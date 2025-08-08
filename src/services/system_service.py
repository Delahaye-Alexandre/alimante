"""
Service système pour Alimante
Gestion de l'état global, des métriques et du monitoring
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode
from ..controllers.temperature_controller import TemperatureController
from ..controllers.humidity_controller import HumidityController
from ..controllers.light_controller import LightController
from ..controllers.feeding_controller import FeedingController


@dataclass
class SystemMetrics:
    """Métriques système"""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light_level: Optional[float] = None
    heating_active: bool = False
    cooling_active: bool = False
    humidifier_active: bool = False
    light_on: bool = False
    feeding_last: Optional[datetime] = None
    feeding_next: Optional[datetime] = None
    uptime_seconds: float = 0.0
    error_count: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ControllerStatus:
    """Statut d'un contrôleur"""
    name: str
    status: str  # "active", "inactive", "error"
    last_update: datetime
    error_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SystemService:
    """Service de gestion du système"""
    
    def __init__(self):
        self.logger = get_logger("system_service")
        self.start_time = datetime.now()
        self.controllers: Dict[str, Any] = {}
        self.metrics_history: List[SystemMetrics] = []
        self.error_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # Configuration par défaut
        self.config = {
            'metrics_interval': 30,  # secondes
            'max_history_size': 1000,
            'error_threshold': 5
        }
    
    def register_controller(self, name: str, controller: Any) -> None:
        """Enregistre un contrôleur"""
        self.controllers[name] = controller
        self.logger.info(f"Contrôleur enregistré: {name}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Récupère le statut complet du système"""
        try:
            status = {
                "status": "online",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "version": "1.0.0",
                "controllers": {}
            }
            
            # Statut des contrôleurs
            for name, controller in self.controllers.items():
                try:
                    if hasattr(controller, 'get_status'):
                        controller_status = controller.get_status()
                        status["controllers"][name] = {
                            "name": name,
                            "status": "active" if controller_status.get("status") == "ok" else "error",
                            "last_update": datetime.now().isoformat(),
                            "error_count": controller_status.get("error_count", 0),
                            "metadata": controller_status
                        }
                    else:
                        status["controllers"][name] = {
                            "name": name,
                            "status": "unknown",
                            "last_update": datetime.now().isoformat(),
                            "error_count": 0
                        }
                except Exception as e:
                    self.logger.error(f"Erreur statut contrôleur {name}: {e}")
                    status["controllers"][name] = {
                        "name": name,
                        "status": "error",
                        "last_update": datetime.now().isoformat(),
                        "error_count": 1,
                        "error": str(e)
                    }
            
            return status
            
        except Exception as e:
            self.logger.exception("Erreur récupération statut système")
            raise create_exception(
                ErrorCode.SERVICE_UNAVAILABLE,
                "Impossible de récupérer le statut système",
                {"original_error": str(e)}
            )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Récupère les métriques actuelles du système"""
        try:
            metrics = SystemMetrics()
            
            # Température
            if 'temperature' in self.controllers:
                try:
                    temp_status = self.controllers['temperature'].get_status()
                    metrics.temperature = temp_status.get('current_temperature')
                    metrics.heating_active = temp_status.get('heating_active', False)
                    metrics.cooling_active = temp_status.get('cooling_active', False)
                except Exception as e:
                    self.logger.warning(f"Erreur métriques température: {e}")
            
            # Humidité
            if 'humidity' in self.controllers:
                try:
                    humidity_status = self.controllers['humidity'].get_status()
                    metrics.humidity = humidity_status.get('current_humidity')
                    metrics.humidifier_active = humidity_status.get('sprayer_active', False)
                except Exception as e:
                    self.logger.warning(f"Erreur métriques humidité: {e}")
            
            # Éclairage
            if 'light' in self.controllers:
                try:
                    light_status = self.controllers['light'].get_status()
                    metrics.light_level = light_status.get('light_level')
                    metrics.light_on = light_status.get('light_on', False)
                except Exception as e:
                    self.logger.warning(f"Erreur métriques éclairage: {e}")
            
            # Alimentation
            if 'feeding' in self.controllers:
                try:
                    feeding_status = self.controllers['feeding'].get_status()
                    metrics.feeding_last = feeding_status.get('last_feeding')
                    metrics.feeding_next = feeding_status.get('next_feeding')
                except Exception as e:
                    self.logger.warning(f"Erreur métriques alimentation: {e}")
            
            # Métriques système
            metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            metrics.error_count = len(self.error_history)
            
            # Ajouter aux historiques
            self._add_to_history(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.exception("Erreur récupération métriques système")
            raise create_exception(
                ErrorCode.SERVICE_UNAVAILABLE,
                "Impossible de récupérer les métriques système",
                {"original_error": str(e)}
            )
    
    def get_metrics_history(self, hours: int = 24) -> List[SystemMetrics]:
        """Récupère l'historique des métriques"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp > cutoff_time]
    
    def get_error_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Récupère l'historique des erreurs"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [e for e in self.error_history if e.get('timestamp', datetime.now()) > cutoff_time]
    
    def record_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Enregistre une erreur"""
        error_record = {
            "timestamp": datetime.now(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        self.error_history.append(error_record)
        self.logger.error(f"Erreur système enregistrée: {error}", context)
        
        # Limiter la taille de l'historique
        if len(self.error_history) > self.config['max_history_size']:
            self.error_history = self.error_history[-self.config['max_history_size']:]
    
    def get_system_health(self) -> Dict[str, Any]:
        """Évalue la santé du système"""
        try:
            health = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "checks": {}
            }
            
            # Vérifier les contrôleurs
            for name, controller in self.controllers.items():
                try:
                    if hasattr(controller, 'check_status'):
                        is_healthy = controller.check_status()
                        health["checks"][name] = {
                            "status": "healthy" if is_healthy else "unhealthy",
                            "last_check": datetime.now().isoformat()
                        }
                    else:
                        health["checks"][name] = {
                            "status": "unknown",
                            "last_check": datetime.now().isoformat()
                        }
                except Exception as e:
                    health["checks"][name] = {
                        "status": "error",
                        "error": str(e),
                        "last_check": datetime.now().isoformat()
                    }
            
            # Déterminer le statut global
            unhealthy_count = sum(
                1 for check in health["checks"].values() 
                if check["status"] in ["unhealthy", "error"]
            )
            
            if unhealthy_count > self.config['error_threshold']:
                health["status"] = "unhealthy"
            elif unhealthy_count > 0:
                health["status"] = "degraded"
            
            return health
            
        except Exception as e:
            self.logger.exception("Erreur évaluation santé système")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _add_to_history(self, metrics: SystemMetrics) -> None:
        """Ajoute des métriques à l'historique"""
        self.metrics_history.append(metrics)
        
        # Limiter la taille de l'historique
        if len(self.metrics_history) > self.config['max_history_size']:
            self.metrics_history = self.metrics_history[-self.config['max_history_size']:]
    
    def cleanup(self) -> None:
        """Nettoie les ressources du service"""
        self.logger.info("Nettoyage du service système")
        
        # Nettoyer les contrôleurs
        for name, controller in self.controllers.items():
            try:
                if hasattr(controller, 'cleanup'):
                    controller.cleanup()
                    self.logger.info(f"Contrôleur nettoyé: {name}")
            except Exception as e:
                self.logger.error(f"Erreur nettoyage contrôleur {name}: {e}")
        
        # Vider les historiques
        self.metrics_history.clear()
        self.error_history.clear()
        
        self.logger.info("Service système nettoyé")


# Instance globale du service système
system_service = SystemService() 