"""
Gestionnaire d'erreurs centralisé pour Alimante
Fournit un système de retry intelligent, de logging d'erreurs et de récupération automatique
"""

import logging
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import threading
from datetime import datetime, timedelta

class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Catégories d'erreurs"""
    HARDWARE = "hardware"
    NETWORK = "network"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    SERVICE = "service"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    """Information sur une erreur"""
    timestamp: datetime
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    function: str
    line_number: int
    traceback: str
    context: Dict[str, Any]
    retry_count: int = 0
    resolved: bool = False

class RetryConfig:
    """Configuration pour le système de retry"""
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

class ErrorHandler:
    """
    Gestionnaire d'erreurs centralisé
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_history: List[ErrorInfo] = []
        self.error_stats: Dict[str, int] = {}
        self.component_health: Dict[str, bool] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.lock = threading.Lock()
        
        # Configuration par défaut
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Configure les paramètres de retry par défaut"""
        # Configuration pour les capteurs
        self.retry_configs['sensor'] = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=10.0,
            backoff_factor=1.5
        )
        
        # Configuration pour les actionneurs
        self.retry_configs['actuator'] = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0
        )
        
        # Configuration pour les services
        self.retry_configs['service'] = RetryConfig(
            max_retries=3,
            base_delay=2.0,
            max_delay=60.0,
            backoff_factor=2.0
        )
        
        # Configuration pour la base de données
        self.retry_configs['database'] = RetryConfig(
            max_retries=5,
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=1.8
        )
    
    def log_error(self, 
                  error: Exception,
                  component: str,
                  function: str,
                  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                  category: ErrorCategory = ErrorCategory.UNKNOWN,
                  context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """
        Enregistre une erreur dans le système
        
        Args:
            error: Exception à enregistrer
            component: Nom du composant
            function: Nom de la fonction
            severity: Niveau de sévérité
            category: Catégorie d'erreur
            context: Contexte supplémentaire
            
        Returns:
            ErrorInfo: Information sur l'erreur
        """
        with self.lock:
            error_info = ErrorInfo(
                timestamp=datetime.now(),
                error_type=type(error).__name__,
                error_message=str(error),
                severity=severity,
                category=category,
                component=component,
                function=function,
                line_number=error.__traceback__.tb_lineno if error.__traceback__ else 0,
                traceback=traceback.format_exc(),
                context=context or {}
            )
            
            self.error_history.append(error_info)
            
            # Mettre à jour les statistiques
            error_key = f"{component}.{function}"
            self.error_stats[error_key] = self.error_stats.get(error_key, 0) + 1
            
            # Marquer le composant comme défaillant si erreur critique
            if severity == ErrorSeverity.CRITICAL:
                self.component_health[component] = False
            
            # Logging selon la sévérité
            if severity == ErrorSeverity.CRITICAL:
                self.logger.critical(f"ERREUR CRITIQUE dans {component}.{function}: {error}")
            elif severity == ErrorSeverity.HIGH:
                self.logger.error(f"ERREUR HAUTE dans {component}.{function}: {error}")
            elif severity == ErrorSeverity.MEDIUM:
                self.logger.warning(f"ERREUR MOYENNE dans {component}.{function}: {error}")
            else:
                self.logger.info(f"ERREUR FAIBLE dans {component}.{function}: {error}")
            
            return error_info
    
    def execute_with_retry(self, 
                          func: Callable,
                          component: str,
                          *args,
                          retry_config: Optional[RetryConfig] = None,
                          **kwargs) -> Any:
        """
        Exécute une fonction avec retry automatique
        
        Args:
            func: Fonction à exécuter
            component: Nom du composant
            *args: Arguments de la fonction
            retry_config: Configuration de retry
            **kwargs: Arguments nommés de la fonction
            
        Returns:
            Résultat de la fonction
            
        Raises:
            Exception: Si tous les retry échouent
        """
        if retry_config is None:
            retry_config = self.retry_configs.get(component, self.retry_configs['service'])
        
        last_error = None
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # Marquer le composant comme sain si succès
                if attempt > 0:
                    self.component_health[component] = True
                    self.logger.info(f"Récupération réussie pour {component} après {attempt} tentatives")
                
                return result
                
            except Exception as e:
                last_error = e
                
                # Déterminer la sévérité basée sur le nombre de tentatives
                if attempt == retry_config.max_retries:
                    severity = ErrorSeverity.CRITICAL
                elif attempt >= retry_config.max_retries // 2:
                    severity = ErrorSeverity.HIGH
                else:
                    severity = ErrorSeverity.MEDIUM
                
                # Enregistrer l'erreur
                self.log_error(
                    error=e,
                    component=component,
                    function=func.__name__,
                    severity=severity,
                    context={
                        'attempt': attempt + 1,
                        'max_retries': retry_config.max_retries,
                        'args': str(args)[:100],  # Limiter la taille
                        'kwargs': str(kwargs)[:100]
                    }
                )
                
                # Si c'est la dernière tentative, lever l'erreur
                if attempt == retry_config.max_retries:
                    break
                
                # Calculer le délai d'attente
                delay = min(
                    retry_config.base_delay * (retry_config.backoff_factor ** attempt),
                    retry_config.max_delay
                )
                
                # Ajouter du jitter pour éviter les collisions
                if retry_config.jitter:
                    import random
                    delay *= (0.5 + random.random() * 0.5)
                
                self.logger.warning(f"Tentative {attempt + 1} échouée pour {component}.{func.__name__}, retry dans {delay:.2f}s")
                time.sleep(delay)
        
        # Si on arrive ici, toutes les tentatives ont échoué
        raise last_error
    
    def get_component_health(self, component: str) -> bool:
        """Vérifie la santé d'un composant"""
        return self.component_health.get(component, True)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'erreurs"""
        with self.lock:
            return {
                'total_errors': len(self.error_history),
                'error_stats': self.error_stats.copy(),
                'component_health': self.component_health.copy(),
                'recent_errors': [
                    {
                        'timestamp': error.timestamp.isoformat(),
                        'component': error.component,
                        'function': error.function,
                        'severity': error.severity.value,
                        'message': error.error_message
                    }
                    for error in self.error_history[-10:]  # 10 dernières erreurs
                ]
            }
    
    def clear_old_errors(self, max_age_hours: int = 24):
        """Nettoie les erreurs anciennes"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with self.lock:
            self.error_history = [
                error for error in self.error_history 
                if error.timestamp > cutoff_time
            ]
    
    def reset_component_health(self, component: str):
        """Remet à zéro la santé d'un composant"""
        with self.lock:
            self.component_health[component] = True

def retry_on_error(component: str, 
                  retry_config: Optional[RetryConfig] = None,
                  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                  category: ErrorCategory = ErrorCategory.UNKNOWN):
    """
    Décorateur pour ajouter automatiquement le retry à une fonction
    
    Args:
        component: Nom du composant
        retry_config: Configuration de retry
        severity: Niveau de sévérité par défaut
        category: Catégorie d'erreur par défaut
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Récupérer l'instance d'ErrorHandler depuis les arguments ou créer une nouvelle
            error_handler = None
            if args and hasattr(args[0], 'error_handler'):
                error_handler = args[0].error_handler
            else:
                error_handler = ErrorHandler()
            
            return error_handler.execute_with_retry(
                func, component, *args, retry_config=retry_config, **kwargs
            )
        return wrapper
    return decorator

# Instance globale pour l'application
error_handler = ErrorHandler()

# Fonctions utilitaires
def log_error(error: Exception, component: str, function: str, **kwargs):
    """Fonction utilitaire pour logger une erreur"""
    return error_handler.log_error(error, component, function, **kwargs)

def execute_with_retry(func: Callable, component: str, *args, **kwargs):
    """Fonction utilitaire pour exécuter avec retry"""
    return error_handler.execute_with_retry(func, component, *args, **kwargs)

def get_component_health(component: str) -> bool:
    """Fonction utilitaire pour vérifier la santé d'un composant"""
    return error_handler.get_component_health(component)

def get_error_stats() -> Dict[str, Any]:
    """Fonction utilitaire pour obtenir les statistiques d'erreurs"""
    return error_handler.get_error_stats()
