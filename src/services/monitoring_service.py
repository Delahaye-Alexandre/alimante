"""
Service de monitoring pour Alimante
Surveille les métriques système, la santé des composants et génère des alertes
"""

import logging
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import os

from ..utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory

class MetricType(Enum):
    """Types de métriques"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"

class HealthStatus(Enum):
    """Statuts de santé"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class Metric:
    """Métrique système"""
    name: str
    value: float
    timestamp: datetime
    metric_type: MetricType
    labels: Dict[str, str]
    unit: Optional[str] = None

@dataclass
class HealthCheck:
    """Vérification de santé d'un composant"""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    metrics: Dict[str, float]
    last_error: Optional[str] = None

class MonitoringService:
    """
    Service de monitoring centralisé
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        
        # Métriques en temps réel
        self.metrics: Dict[str, Metric] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        
        # Configuration
        self.update_interval = config.get('update_interval', 5.0)
        self.metrics_retention_hours = config.get('metrics_retention_hours', 24)
        self.health_check_interval = config.get('health_check_interval', 10.0)
        
        # Threads
        self.monitoring_thread: Optional[threading.Thread] = None
        self.health_check_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Callbacks pour les alertes
        self.alert_callbacks: List[Callable] = []
        
        # Seuils d'alerte
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'temperature': 70.0,
            'sensor_accuracy': 95.0,
            'response_time': 5.0
        }
        
        self.logger.info("Service de monitoring initialisé")
    
    def initialize(self) -> bool:
        """Initialise le service de monitoring"""
        try:
            self.logger.info("Initialisation du service de monitoring...")
            
            # Créer le répertoire de données si nécessaire
            os.makedirs('data/monitoring', exist_ok=True)
            
            # Initialiser les métriques de base
            self._initialize_base_metrics()
            
            self.logger.info("Service de monitoring initialisé avec succès")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "initialize",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def start(self) -> bool:
        """Démarre le service de monitoring"""
        try:
            if self.running:
                self.logger.warning("Service de monitoring déjà démarré")
                return True
            
            self.running = True
            
            # Démarrer le thread de monitoring des métriques
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="MonitoringThread",
                daemon=True
            )
            self.monitoring_thread.start()
            
            # Démarrer le thread de vérification de santé
            self.health_check_thread = threading.Thread(
                target=self._health_check_loop,
                name="HealthCheckThread",
                daemon=True
            )
            self.health_check_thread.start()
            
            self.logger.info("Service de monitoring démarré")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "start",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def stop(self) -> bool:
        """Arrête le service de monitoring"""
        try:
            self.running = False
            
            # Attendre que les threads se terminent
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            
            if self.health_check_thread and self.health_check_thread.is_alive():
                self.health_check_thread.join(timeout=5.0)
            
            self.logger.info("Service de monitoring arrêté")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "stop",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
    
    def _initialize_base_metrics(self):
        """Initialise les métriques de base"""
        base_metrics = [
            'cpu_usage', 'memory_usage', 'disk_usage', 'network_io',
            'sensor_accuracy', 'actuator_response_time', 'error_rate',
            'request_count', 'response_time', 'active_connections'
        ]
        
        for metric_name in base_metrics:
            self.metrics[metric_name] = Metric(
                name=metric_name,
                value=0.0,
                timestamp=datetime.now(),
                metric_type=MetricType.GAUGE,
                labels={}
            )
    
    def _monitoring_loop(self):
        """Boucle principale de monitoring"""
        while self.running:
            try:
                self._collect_system_metrics()
                self._collect_application_metrics()
                self._cleanup_old_metrics()
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "MonitoringService", "_monitoring_loop",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                time.sleep(1.0)  # Attendre avant de réessayer
    
    def _health_check_loop(self):
        """Boucle de vérification de santé"""
        while self.running:
            try:
                self._perform_health_checks()
                self._check_alert_thresholds()
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "MonitoringService", "_health_check_loop",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                time.sleep(1.0)
    
    def _collect_system_metrics(self):
        """Collecte les métriques système"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self._update_metric('cpu_usage', cpu_percent)
            
            # Mémoire
            memory = psutil.virtual_memory()
            self._update_metric('memory_usage', memory.percent)
            
            # Disque
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self._update_metric('disk_usage', disk_percent)
            
            # Réseau
            network = psutil.net_io_counters()
            self._update_metric('network_io', network.bytes_sent + network.bytes_recv)
            
            # Température (si disponible)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    cpu_temp = temps.get('cpu_thermal', temps.get('coretemp', []))
                    if cpu_temp:
                        self._update_metric('temperature', cpu_temp[0].current)
            except:
                pass  # Température non disponible sur tous les systèmes
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "_collect_system_metrics",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _collect_application_metrics(self):
        """Collecte les métriques de l'application"""
        try:
            # Statistiques d'erreurs
            error_stats = self.error_handler.get_error_stats()
            self._update_metric('error_rate', error_stats.get('total_errors', 0))
            
            # Santé des composants
            healthy_components = sum(1 for health in error_stats.get('component_health', {}).values() if health)
            total_components = len(error_stats.get('component_health', {}))
            if total_components > 0:
                health_percentage = (healthy_components / total_components) * 100
                self._update_metric('component_health', health_percentage)
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "_collect_application_metrics",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _update_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Met à jour une métrique"""
        self.metrics[name] = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            metric_type=MetricType.GAUGE,
            labels=labels or {}
        )
    
    def _perform_health_checks(self):
        """Effectue les vérifications de santé"""
        try:
            # Vérifier la santé des composants
            error_stats = self.error_handler.get_error_stats()
            component_health = error_stats.get('component_health', {})
            
            for component, is_healthy in component_health.items():
                status = HealthStatus.HEALTHY if is_healthy else HealthStatus.CRITICAL
                message = f"Composant {component} {'opérationnel' if is_healthy else 'défaillant'}"
                
                self.health_checks[component] = HealthCheck(
                    component=component,
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics={},
                    last_error=error_stats.get('recent_errors', [{}])[0].get('message') if error_stats.get('recent_errors') else None
                )
            
            # Vérifier la santé générale du système
            self._check_system_health()
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "_perform_health_checks",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
    
    def _check_system_health(self):
        """Vérifie la santé générale du système"""
        try:
            # Vérifier l'utilisation CPU
            cpu_usage = self.metrics.get('cpu_usage', Metric('cpu_usage', 0, datetime.now(), MetricType.GAUGE, {})).value
            if cpu_usage > self.alert_thresholds['cpu_usage']:
                self._trigger_alert('cpu_usage', f"Utilisation CPU élevée: {cpu_usage:.1f}%")
            
            # Vérifier l'utilisation mémoire
            memory_usage = self.metrics.get('memory_usage', Metric('memory_usage', 0, datetime.now(), MetricType.GAUGE, {})).value
            if memory_usage > self.alert_thresholds['memory_usage']:
                self._trigger_alert('memory_usage', f"Utilisation mémoire élevée: {memory_usage:.1f}%")
            
            # Vérifier l'utilisation disque
            disk_usage = self.metrics.get('disk_usage', Metric('disk_usage', 0, datetime.now(), MetricType.GAUGE, {})).value
            if disk_usage > self.alert_thresholds['disk_usage']:
                self._trigger_alert('disk_usage', f"Utilisation disque élevée: {disk_usage:.1f}%")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "_check_system_health",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _check_alert_thresholds(self):
        """Vérifie les seuils d'alerte"""
        try:
            for metric_name, threshold in self.alert_thresholds.items():
                if metric_name in self.metrics:
                    value = self.metrics[metric_name].value
                    if value > threshold:
                        self._trigger_alert(metric_name, f"Seuil dépassé: {value:.2f} > {threshold}")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "_check_alert_thresholds",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _trigger_alert(self, metric_name: str, message: str):
        """Déclenche une alerte"""
        try:
            alert_data = {
                'metric': metric_name,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'value': self.metrics.get(metric_name, Metric(metric_name, 0, datetime.now(), MetricType.GAUGE, {})).value,
                'threshold': self.alert_thresholds.get(metric_name, 0)
            }
            
            # Appeler les callbacks d'alerte
            for callback in self.alert_callbacks:
                try:
                    callback(alert_data)
                except Exception as e:
                    self.logger.error(f"Erreur dans callback d'alerte: {e}")
            
            # Émettre un événement si le bus d'événements est disponible
            if self.event_bus:
                self.event_bus.emit('alert_triggered', alert_data)
            
            self.logger.warning(f"ALERTE: {message}")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "_trigger_alert",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
    
    def _cleanup_old_metrics(self):
        """Nettoie les métriques anciennes"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.metrics_retention_hours)
            
            # Nettoyer les métriques anciennes
            old_metrics = [
                name for name, metric in self.metrics.items()
                if metric.timestamp < cutoff_time
            ]
            
            for metric_name in old_metrics:
                del self.metrics[metric_name]
            
            if old_metrics:
                self.logger.debug(f"Nettoyé {len(old_metrics)} métriques anciennes")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "_cleanup_old_metrics",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
    
    def add_alert_callback(self, callback: Callable):
        """Ajoute un callback d'alerte"""
        self.alert_callbacks.append(callback)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne toutes les métriques"""
        return {
            name: {
                'value': metric.value,
                'timestamp': metric.timestamp.isoformat(),
                'type': metric.metric_type.value,
                'labels': metric.labels,
                'unit': metric.unit
            }
            for name, metric in self.metrics.items()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retourne le statut de santé"""
        return {
            'overall_status': self._get_overall_health_status(),
            'components': {
                name: {
                    'status': check.status.value,
                    'message': check.message,
                    'timestamp': check.timestamp.isoformat(),
                    'metrics': check.metrics,
                    'last_error': check.last_error
                }
                for name, check in self.health_checks.items()
            },
            'metrics': self.get_metrics()
        }
    
    def _get_overall_health_status(self) -> str:
        """Détermine le statut de santé global"""
        if not self.health_checks:
            return HealthStatus.UNKNOWN.value
        
        statuses = [check.status for check in self.health_checks.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL.value
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING.value
        else:
            return HealthStatus.HEALTHY.value
    
    def export_metrics(self, filepath: str):
        """Exporte les métriques vers un fichier"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': self.get_metrics(),
                'health_status': self.get_health_status()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Métriques exportées vers {filepath}")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "MonitoringService", "export_metrics",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
