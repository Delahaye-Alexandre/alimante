"""
Service de récupération automatique pour Alimante
Gère la récupération automatique des composants défaillants et la restauration du système
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from src.utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory

class RecoveryStrategy(Enum):
    """Stratégies de récupération"""
    RESTART = "restart"
    RESET = "reset"
    FALLBACK = "fallback"
    MANUAL = "manual"

class RecoveryStatus(Enum):
    """Statuts de récupération"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class RecoveryAction:
    """Action de récupération"""
    component: str
    strategy: RecoveryStrategy
    status: RecoveryStatus
    timestamp: datetime
    attempts: int
    max_attempts: int
    last_error: Optional[str] = None
    recovery_data: Optional[Dict[str, Any]] = None

class RecoveryService:
    """
    Service de récupération automatique
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        
        # Configuration
        self.recovery_enabled = config.get('recovery_enabled', True)
        self.max_recovery_attempts = config.get('max_recovery_attempts', 3)
        self.recovery_delay = config.get('recovery_delay', 5.0)
        self.health_check_interval = config.get('health_check_interval', 10.0)
        
        # État du service
        self.running = False
        self.recovery_thread: Optional[threading.Thread] = None
        self.active_recoveries: Dict[str, RecoveryAction] = {}
        self.recovery_history: List[RecoveryAction] = []
        
        # Callbacks de récupération
        self.recovery_callbacks: Dict[str, Callable] = {}
        
        # Composants surveillés
        self.monitored_components = set()
        
        self.logger.info("Service de récupération initialisé")
    
    def initialize(self) -> bool:
        """Initialise le service de récupération"""
        try:
            self.logger.info("Initialisation du service de récupération...")
            
            # Enregistrer les callbacks de récupération par défaut
            self._register_default_callbacks()
            
            self.logger.info("Service de récupération initialisé avec succès")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "initialize",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def start(self) -> bool:
        """Démarre le service de récupération"""
        try:
            if self.running:
                self.logger.warning("Service de récupération déjà démarré")
                return True
            
            if not self.recovery_enabled:
                self.logger.info("Service de récupération désactivé")
                return True
            
            self.running = True
            
            # Démarrer le thread de surveillance
            self.recovery_thread = threading.Thread(
                target=self._recovery_loop,
                name="RecoveryThread",
                daemon=True
            )
            self.recovery_thread.start()
            
            self.logger.info("Service de récupération démarré")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "start",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def stop(self) -> bool:
        """Arrête le service de récupération"""
        try:
            self.running = False
            
            # Attendre que le thread se termine
            if self.recovery_thread and self.recovery_thread.is_alive():
                self.recovery_thread.join(timeout=5.0)
            
            self.logger.info("Service de récupération arrêté")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "stop",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
    
    def _register_default_callbacks(self):
        """Enregistre les callbacks de récupération par défaut"""
        
        def restart_component(component: str, recovery_data: Dict[str, Any]) -> bool:
            """Redémarre un composant"""
            try:
                self.logger.info(f"Redémarrage du composant {component}")
                
                # Simuler le redémarrage
                time.sleep(1.0)
                
                # Marquer le composant comme sain
                self.error_handler.reset_component_health(component)
                
                return True
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "RecoveryService", "restart_component",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                return False
        
        def reset_component(component: str, recovery_data: Dict[str, Any]) -> bool:
            """Remet à zéro un composant"""
            try:
                self.logger.info(f"Remise à zéro du composant {component}")
                
                # Simuler la remise à zéro
                time.sleep(2.0)
                
                # Marquer le composant comme sain
                self.error_handler.reset_component_health(component)
                
                return True
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "RecoveryService", "reset_component",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                return False
        
        def fallback_component(component: str, recovery_data: Dict[str, Any]) -> bool:
            """Active le mode de secours pour un composant"""
            try:
                self.logger.info(f"Activation du mode de secours pour {component}")
                
                # Simuler l'activation du mode de secours
                time.sleep(0.5)
                
                return True
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "RecoveryService", "fallback_component",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                return False
        
        # Enregistrer les callbacks
        self.recovery_callbacks[RecoveryStrategy.RESTART.value] = restart_component
        self.recovery_callbacks[RecoveryStrategy.RESET.value] = reset_component
        self.recovery_callbacks[RecoveryStrategy.FALLBACK.value] = fallback_component
    
    def _recovery_loop(self):
        """Boucle principale de récupération"""
        while self.running:
            try:
                self._check_component_health()
                self._process_active_recoveries()
                self._cleanup_old_recoveries()
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "RecoveryService", "_recovery_loop",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                time.sleep(1.0)
    
    def _check_component_health(self):
        """Vérifie la santé des composants surveillés"""
        try:
            error_stats = self.error_handler.get_error_stats()
            component_health = error_stats.get('component_health', {})
            
            for component, is_healthy in component_health.items():
                if not is_healthy and component not in self.active_recoveries:
                    # Composant défaillant, initier la récupération
                    self._initiate_recovery(component)
                
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "_check_component_health",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _initiate_recovery(self, component: str):
        """Initie la récupération d'un composant"""
        try:
            self.logger.info(f"Initiation de la récupération pour {component}")
            
            # Déterminer la stratégie de récupération
            strategy = self._determine_recovery_strategy(component)
            
            # Créer l'action de récupération
            recovery_action = RecoveryAction(
                component=component,
                strategy=strategy,
                status=RecoveryStatus.PENDING,
                timestamp=datetime.now(),
                attempts=0,
                max_attempts=self.max_recovery_attempts
            )
            
            self.active_recoveries[component] = recovery_action
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('recovery_initiated', {
                    'component': component,
                    'strategy': strategy.value,
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "_initiate_recovery",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
    
    def _determine_recovery_strategy(self, component: str) -> RecoveryStrategy:
        """Détermine la stratégie de récupération pour un composant"""
        try:
            # Récupérer l'historique des erreurs pour ce composant
            error_stats = self.error_handler.get_error_stats()
            recent_errors = error_stats.get('recent_errors', [])
            
            component_errors = [
                error for error in recent_errors
                if error.get('component') == component
            ]
            
            # Déterminer la stratégie basée sur le type d'erreur
            if not component_errors:
                return RecoveryStrategy.RESTART
            
            last_error = component_errors[0]
            error_message = last_error.get('message', '').lower()
            
            if 'sensor' in error_message or 'hardware' in error_message:
                return RecoveryStrategy.RESET
            elif 'network' in error_message or 'connection' in error_message:
                return RecoveryStrategy.RESTART
            elif 'critical' in error_message or 'fatal' in error_message:
                return RecoveryStrategy.FALLBACK
            else:
                return RecoveryStrategy.RESTART
                
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "_determine_recovery_strategy",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return RecoveryStrategy.RESTART
    
    def _process_active_recoveries(self):
        """Traite les récupérations actives"""
        try:
            for component, recovery in list(self.active_recoveries.items()):
                if recovery.status == RecoveryStatus.PENDING:
                    self._execute_recovery(recovery)
                elif recovery.status == RecoveryStatus.IN_PROGRESS:
                    # Vérifier si la récupération est terminée
                    if self._is_recovery_complete(recovery):
                        self._finalize_recovery(recovery)
                
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "_process_active_recoveries",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
    
    def _execute_recovery(self, recovery: RecoveryAction):
        """Exécute une action de récupération"""
        try:
            self.logger.info(f"Exécution de la récupération {recovery.strategy.value} pour {recovery.component}")
            
            recovery.status = RecoveryStatus.IN_PROGRESS
            recovery.attempts += 1
            
            # Récupérer le callback de récupération
            callback = self.recovery_callbacks.get(recovery.strategy.value)
            if not callback:
                self.logger.error(f"Callback de récupération non trouvé pour {recovery.strategy.value}")
                recovery.status = RecoveryStatus.FAILED
                recovery.last_error = "Callback non trouvé"
                return
            
            # Exécuter la récupération
            success = callback(recovery.component, recovery.recovery_data or {})
            
            if success:
                recovery.status = RecoveryStatus.SUCCESS
                self.logger.info(f"Récupération réussie pour {recovery.component}")
            else:
                if recovery.attempts >= recovery.max_attempts:
                    recovery.status = RecoveryStatus.FAILED
                    recovery.last_error = "Nombre maximum de tentatives atteint"
                    self.logger.error(f"Échec de la récupération pour {recovery.component}")
                else:
                    recovery.status = RecoveryStatus.PENDING
                    self.logger.warning(f"Tentative de récupération échouée pour {recovery.component}, retry dans {self.recovery_delay}s")
                    time.sleep(self.recovery_delay)
            
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "_execute_recovery",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            recovery.status = RecoveryStatus.FAILED
            recovery.last_error = str(e)
    
    def _is_recovery_complete(self, recovery: RecoveryAction) -> bool:
        """Vérifie si une récupération est terminée"""
        try:
            # Vérifier la santé du composant
            is_healthy = self.error_handler.get_component_health(recovery.component)
            
            if is_healthy:
                recovery.status = RecoveryStatus.SUCCESS
                return True
            
            # Vérifier le timeout
            timeout = timedelta(minutes=5)  # 5 minutes de timeout
            if datetime.now() - recovery.timestamp > timeout:
                recovery.status = RecoveryStatus.FAILED
                recovery.last_error = "Timeout de récupération"
                return True
            
            return False
            
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "_is_recovery_complete",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def _finalize_recovery(self, recovery: RecoveryAction):
        """Finalise une récupération"""
        try:
            # Ajouter à l'historique
            self.recovery_history.append(recovery)
            
            # Retirer des récupérations actives
            if recovery.component in self.active_recoveries:
                del self.active_recoveries[recovery.component]
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('recovery_completed', {
                    'component': recovery.component,
                    'strategy': recovery.strategy.value,
                    'status': recovery.status.value,
                    'attempts': recovery.attempts,
                    'timestamp': datetime.now().isoformat()
                })
            
            self.logger.info(f"Récupération finalisée pour {recovery.component}: {recovery.status.value}")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "_finalize_recovery",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _cleanup_old_recoveries(self):
        """Nettoie les anciennes récupérations"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            # Nettoyer l'historique
            self.recovery_history = [
                recovery for recovery in self.recovery_history
                if recovery.timestamp > cutoff_time
            ]
            
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "_cleanup_old_recoveries",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
    
    def add_monitored_component(self, component: str):
        """Ajoute un composant à la surveillance"""
        self.monitored_components.add(component)
        self.logger.info(f"Composant {component} ajouté à la surveillance")
    
    def remove_monitored_component(self, component: str):
        """Retire un composant de la surveillance"""
        self.monitored_components.discard(component)
        if component in self.active_recoveries:
            del self.active_recoveries[component]
        self.logger.info(f"Composant {component} retiré de la surveillance")
    
    def register_recovery_callback(self, strategy: RecoveryStrategy, callback: Callable):
        """Enregistre un callback de récupération personnalisé"""
        self.recovery_callbacks[strategy.value] = callback
        self.logger.info(f"Callback de récupération enregistré pour {strategy.value}")
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Retourne le statut des récupérations"""
        return {
            'active_recoveries': {
                component: {
                    'strategy': recovery.strategy.value,
                    'status': recovery.status.value,
                    'attempts': recovery.attempts,
                    'max_attempts': recovery.max_attempts,
                    'timestamp': recovery.timestamp.isoformat(),
                    'last_error': recovery.last_error
                }
                for component, recovery in self.active_recoveries.items()
            },
            'recovery_history': [
                {
                    'component': recovery.component,
                    'strategy': recovery.strategy.value,
                    'status': recovery.status.value,
                    'attempts': recovery.attempts,
                    'timestamp': recovery.timestamp.isoformat(),
                    'last_error': recovery.last_error
                }
                for recovery in self.recovery_history[-10:]  # 10 dernières récupérations
            ],
            'monitored_components': list(self.monitored_components),
            'recovery_enabled': self.recovery_enabled
        }
    
    def force_recovery(self, component: str, strategy: Optional[RecoveryStrategy] = None) -> bool:
        """Force la récupération d'un composant"""
        try:
            if component in self.active_recoveries:
                self.logger.warning(f"Récupération déjà en cours pour {component}")
                return False
            
            if strategy is None:
                strategy = self._determine_recovery_strategy(component)
            
            recovery_action = RecoveryAction(
                component=component,
                strategy=strategy,
                status=RecoveryStatus.PENDING,
                timestamp=datetime.now(),
                attempts=0,
                max_attempts=self.max_recovery_attempts
            )
            
            self.active_recoveries[component] = recovery_action
            
            self.logger.info(f"Récupération forcée initiée pour {component} avec stratégie {strategy.value}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "RecoveryService", "force_recovery",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
