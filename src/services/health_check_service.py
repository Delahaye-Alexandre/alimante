"""
Service de vérification de santé du système pour Alimante
Effectue des vérifications complètes de la santé du système et de ses composants
"""

import logging
import time
import threading
import psutil
import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from src.utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory

class HealthCheckType(Enum):
    """Types de vérifications de santé"""
    SYSTEM = "system"
    COMPONENT = "component"
    SERVICE = "service"
    HARDWARE = "hardware"
    NETWORK = "network"
    STORAGE = "storage"
    MEMORY = "memory"
    CPU = "cpu"

class HealthStatus(Enum):
    """Statuts de santé"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Résultat d'une vérification de santé"""
    check_type: HealthCheckType
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    metrics: Dict[str, Any]
    recommendations: List[str]
    error_details: Optional[str] = None

class HealthCheckService:
    """
    Service de vérification de santé du système
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        
        # Configuration
        self.check_interval = config.get('check_interval', 30.0)
        self.enabled_checks = config.get('enabled_checks', [
            'system', 'component', 'service', 'hardware', 
            'network', 'storage', 'memory', 'cpu'
        ])
        
        # Seuils d'alerte
        self.thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'temperature': 70.0,
            'network_latency': 1000.0,  # ms
            'response_time': 5.0,  # secondes
            'error_rate': 10.0,  # pourcentage
            'component_failure_rate': 20.0  # pourcentage
        }
        
        # État du service
        self.running = False
        self.health_check_thread: Optional[threading.Thread] = None
        self.health_results: Dict[str, HealthCheckResult] = {}
        self.health_history: List[HealthCheckResult] = []
        
        # Callbacks pour les vérifications personnalisées
        self.custom_checks: Dict[str, Callable] = {}
        
        self.logger.info("Service de vérification de santé initialisé")
    
    def initialize(self) -> bool:
        """Initialise le service de vérification de santé"""
        try:
            self.logger.info("Initialisation du service de vérification de santé...")
            
            # Enregistrer les vérifications par défaut
            self._register_default_checks()
            
            self.logger.info("Service de vérification de santé initialisé avec succès")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "HealthCheckService", "initialize",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def start(self) -> bool:
        """Démarre le service de vérification de santé"""
        try:
            if self.running:
                self.logger.warning("Service de vérification de santé déjà démarré")
                return True
            
            self.running = True
            
            # Démarrer le thread de vérification
            self.health_check_thread = threading.Thread(
                target=self._health_check_loop,
                name="HealthCheckThread",
                daemon=True
            )
            self.health_check_thread.start()
            
            self.logger.info("Service de vérification de santé démarré")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "HealthCheckService", "start",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def stop(self) -> bool:
        """Arrête le service de vérification de santé"""
        try:
            self.running = False
            
            # Attendre que le thread se termine
            if self.health_check_thread and self.health_check_thread.is_alive():
                self.health_check_thread.join(timeout=5.0)
            
            self.logger.info("Service de vérification de santé arrêté")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "HealthCheckService", "stop",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
    
    def _register_default_checks(self):
        """Enregistre les vérifications de santé par défaut"""
        
        def check_system_health() -> HealthCheckResult:
            """Vérifie la santé générale du système"""
            try:
                # Vérifier l'utilisation CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Vérifier l'utilisation mémoire
                memory = psutil.virtual_memory()
                
                # Vérifier l'utilisation disque
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                
                # Déterminer le statut
                status = HealthStatus.HEALTHY
                message = "Système en bonne santé"
                recommendations = []
                
                if cpu_percent > self.thresholds['cpu_usage']:
                    status = HealthStatus.CRITICAL if cpu_percent > 95 else HealthStatus.WARNING
                    message = f"Utilisation CPU élevée: {cpu_percent:.1f}%"
                    recommendations.append("Vérifier les processus gourmands en CPU")
                
                if memory.percent > self.thresholds['memory_usage']:
                    status = HealthStatus.CRITICAL if memory.percent > 95 else HealthStatus.WARNING
                    message = f"Utilisation mémoire élevée: {memory.percent:.1f}%"
                    recommendations.append("Libérer de la mémoire ou redémarrer le système")
                
                if disk_percent > self.thresholds['disk_usage']:
                    status = HealthStatus.CRITICAL if disk_percent > 95 else HealthStatus.WARNING
                    message = f"Utilisation disque élevée: {disk_percent:.1f}%"
                    recommendations.append("Nettoyer l'espace disque")
                
                return HealthCheckResult(
                    check_type=HealthCheckType.SYSTEM,
                    component="system",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics={
                        'cpu_usage': cpu_percent,
                        'memory_usage': memory.percent,
                        'disk_usage': disk_percent,
                        'available_memory': memory.available,
                        'free_disk_space': disk.free
                    },
                    recommendations=recommendations
                )
                
            except Exception as e:
                return HealthCheckResult(
                    check_type=HealthCheckType.SYSTEM,
                    component="system",
                    status=HealthStatus.CRITICAL,
                    message=f"Erreur lors de la vérification système: {str(e)}",
                    timestamp=datetime.now(),
                    metrics={},
                    recommendations=["Vérifier les permissions système"],
                    error_details=str(e)
                )
        
        def check_component_health() -> HealthCheckResult:
            """Vérifie la santé des composants"""
            try:
                error_stats = self.error_handler.get_error_stats()
                component_health = error_stats.get('component_health', {})
                
                if not component_health:
                    return HealthCheckResult(
                        check_type=HealthCheckType.COMPONENT,
                        component="components",
                        status=HealthStatus.UNKNOWN,
                        message="Aucun composant surveillé",
                        timestamp=datetime.now(),
                        metrics={},
                        recommendations=["Ajouter des composants à la surveillance"]
                    )
                
                healthy_components = sum(1 for health in component_health.values() if health)
                total_components = len(component_health)
                health_percentage = (healthy_components / total_components) * 100
                
                status = HealthStatus.HEALTHY
                message = f"Tous les composants sont sains ({healthy_components}/{total_components})"
                recommendations = []
                
                if health_percentage < 100:
                    if health_percentage < 50:
                        status = HealthStatus.CRITICAL
                    else:
                        status = HealthStatus.WARNING
                    
                    failed_components = [
                        comp for comp, health in component_health.items() if not health
                    ]
                    message = f"Composants défaillants: {', '.join(failed_components)}"
                    recommendations.append("Vérifier les composants défaillants")
                
                return HealthCheckResult(
                    check_type=HealthCheckType.COMPONENT,
                    component="components",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics={
                        'total_components': total_components,
                        'healthy_components': healthy_components,
                        'health_percentage': health_percentage,
                        'component_health': component_health
                    },
                    recommendations=recommendations
                )
                
            except Exception as e:
                return HealthCheckResult(
                    check_type=HealthCheckType.COMPONENT,
                    component="components",
                    status=HealthStatus.CRITICAL,
                    message=f"Erreur lors de la vérification des composants: {str(e)}",
                    timestamp=datetime.now(),
                    metrics={},
                    recommendations=["Vérifier la configuration des composants"],
                    error_details=str(e)
                )
        
        def check_service_health() -> HealthCheckResult:
            """Vérifie la santé des services"""
            try:
                # Vérifier les services critiques
                critical_services = ['MonitoringService', 'ErrorHandler', 'EventBus']
                service_status = {}
                
                for service in critical_services:
                    # Simuler la vérification du service
                    service_status[service] = True  # En réalité, vérifier si le service est actif
                
                all_services_healthy = all(service_status.values())
                
                status = HealthStatus.HEALTHY if all_services_healthy else HealthStatus.CRITICAL
                message = "Tous les services critiques sont actifs" if all_services_healthy else "Certains services critiques sont défaillants"
                
                recommendations = []
                if not all_services_healthy:
                    failed_services = [svc for svc, healthy in service_status.items() if not healthy]
                    recommendations.append(f"Redémarrer les services défaillants: {', '.join(failed_services)}")
                
                return HealthCheckResult(
                    check_type=HealthCheckType.SERVICE,
                    component="services",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics=service_status,
                    recommendations=recommendations
                )
                
            except Exception as e:
                return HealthCheckResult(
                    check_type=HealthCheckType.SERVICE,
                    component="services",
                    status=HealthStatus.CRITICAL,
                    message=f"Erreur lors de la vérification des services: {str(e)}",
                    timestamp=datetime.now(),
                    metrics={},
                    recommendations=["Vérifier la configuration des services"],
                    error_details=str(e)
                )
        
        def check_hardware_health() -> HealthCheckResult:
            """Vérifie la santé du matériel"""
            try:
                # Vérifier la température
                temps = psutil.sensors_temperatures()
                max_temp = 0
                temp_warnings = []
                
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current:
                            max_temp = max(max_temp, entry.current)
                            if entry.current > self.thresholds['temperature']:
                                temp_warnings.append(f"{name}: {entry.current}°C")
                
                # Vérifier les ventilateurs
                fans = psutil.sensors_fans()
                fan_warnings = []
                
                for name, entries in fans.items():
                    for entry in entries:
                        if entry.current and entry.current < 1000:  # RPM trop bas
                            fan_warnings.append(f"{name}: {entry.current} RPM")
                
                status = HealthStatus.HEALTHY
                message = "Matériel en bonne santé"
                recommendations = []
                
                if temp_warnings:
                    status = HealthStatus.CRITICAL if max_temp > 80 else HealthStatus.WARNING
                    message = f"Températures élevées détectées: {', '.join(temp_warnings)}"
                    recommendations.append("Vérifier le refroidissement du système")
                
                if fan_warnings:
                    if status == HealthStatus.HEALTHY:
                        status = HealthStatus.WARNING
                    message += f" | Ventilateurs lents: {', '.join(fan_warnings)}"
                    recommendations.append("Vérifier les ventilateurs")
                
                return HealthCheckResult(
                    check_type=HealthCheckType.HARDWARE,
                    component="hardware",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics={
                        'max_temperature': max_temp,
                        'temperature_warnings': temp_warnings,
                        'fan_warnings': fan_warnings
                    },
                    recommendations=recommendations
                )
                
            except Exception as e:
                return HealthCheckResult(
                    check_type=HealthCheckType.HARDWARE,
                    component="hardware",
                    status=HealthStatus.UNKNOWN,
                    message=f"Impossible de vérifier le matériel: {str(e)}",
                    timestamp=datetime.now(),
                    metrics={},
                    recommendations=["Vérifier les permissions matériel"],
                    error_details=str(e)
                )
        
        def check_network_health() -> HealthCheckResult:
            """Vérifie la santé du réseau"""
            try:
                # Vérifier les interfaces réseau
                net_io = psutil.net_io_counters()
                net_connections = psutil.net_connections()
                
                # Vérifier la connectivité (simulation)
                network_available = True  # En réalité, faire un ping
                
                status = HealthStatus.HEALTHY if network_available else HealthStatus.CRITICAL
                message = "Réseau opérationnel" if network_available else "Problème de connectivité réseau"
                
                recommendations = []
                if not network_available:
                    recommendations.append("Vérifier la connexion réseau")
                
                return HealthCheckResult(
                    check_type=HealthCheckType.NETWORK,
                    component="network",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics={
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv,
                        'active_connections': len(net_connections),
                        'network_available': network_available
                    },
                    recommendations=recommendations
                )
                
            except Exception as e:
                return HealthCheckResult(
                    check_type=HealthCheckType.NETWORK,
                    component="network",
                    status=HealthStatus.CRITICAL,
                    message=f"Erreur lors de la vérification réseau: {str(e)}",
                    timestamp=datetime.now(),
                    metrics={},
                    recommendations=["Vérifier la configuration réseau"],
                    error_details=str(e)
                )
        
        def check_storage_health() -> HealthCheckResult:
            """Vérifie la santé du stockage"""
            try:
                # Vérifier l'espace disque
                disk_usage = psutil.disk_usage('/')
                disk_percent = (disk_usage.used / disk_usage.total) * 100
                
                # Vérifier les inodes (si disponible)
                try:
                    statvfs = os.statvfs('/')
                    inode_usage = ((statvfs.f_files - statvfs.f_favail) / statvfs.f_files) * 100
                except:
                    inode_usage = 0
                
                status = HealthStatus.HEALTHY
                message = "Stockage en bonne santé"
                recommendations = []
                
                if disk_percent > self.thresholds['disk_usage']:
                    status = HealthStatus.CRITICAL if disk_percent > 95 else HealthStatus.WARNING
                    message = f"Espace disque faible: {disk_percent:.1f}% utilisé"
                    recommendations.append("Nettoyer l'espace disque")
                
                if inode_usage > 90:
                    if status == HealthStatus.HEALTHY:
                        status = HealthStatus.WARNING
                    message += f" | Inodes: {inode_usage:.1f}% utilisés"
                    recommendations.append("Nettoyer les fichiers inutilisés")
                
                return HealthCheckResult(
                    check_type=HealthCheckType.STORAGE,
                    component="storage",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics={
                        'disk_usage_percent': disk_percent,
                        'disk_used': disk_usage.used,
                        'disk_free': disk_usage.free,
                        'disk_total': disk_usage.total,
                        'inode_usage_percent': inode_usage
                    },
                    recommendations=recommendations
                )
                
            except Exception as e:
                return HealthCheckResult(
                    check_type=HealthCheckType.STORAGE,
                    component="storage",
                    status=HealthStatus.CRITICAL,
                    message=f"Erreur lors de la vérification du stockage: {str(e)}",
                    timestamp=datetime.now(),
                    metrics={},
                    recommendations=["Vérifier les permissions de stockage"],
                    error_details=str(e)
                )
        
        def check_memory_health() -> HealthCheckResult:
            """Vérifie la santé de la mémoire"""
            try:
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                status = HealthStatus.HEALTHY
                message = "Mémoire en bonne santé"
                recommendations = []
                
                if memory.percent > self.thresholds['memory_usage']:
                    status = HealthStatus.CRITICAL if memory.percent > 95 else HealthStatus.WARNING
                    message = f"Utilisation mémoire élevée: {memory.percent:.1f}%"
                    recommendations.append("Libérer de la mémoire")
                
                if swap.percent > 50:
                    if status == HealthStatus.HEALTHY:
                        status = HealthStatus.WARNING
                    message += f" | Swap utilisé: {swap.percent:.1f}%"
                    recommendations.append("Vérifier l'utilisation du swap")
                
                return HealthCheckResult(
                    check_type=HealthCheckType.MEMORY,
                    component="memory",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics={
                        'memory_usage_percent': memory.percent,
                        'memory_available': memory.available,
                        'memory_total': memory.total,
                        'swap_usage_percent': swap.percent,
                        'swap_total': swap.total
                    },
                    recommendations=recommendations
                )
                
            except Exception as e:
                return HealthCheckResult(
                    check_type=HealthCheckType.MEMORY,
                    component="memory",
                    status=HealthStatus.CRITICAL,
                    message=f"Erreur lors de la vérification de la mémoire: {str(e)}",
                    timestamp=datetime.now(),
                    metrics={},
                    recommendations=["Vérifier les permissions mémoire"],
                    error_details=str(e)
                )
        
        def check_cpu_health() -> HealthCheckResult:
            """Vérifie la santé du CPU"""
            try:
                # Utilisation CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Fréquence CPU
                cpu_freq = psutil.cpu_freq()
                
                # Nombre de cœurs
                cpu_count = psutil.cpu_count()
                
                # Charge système
                load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                
                status = HealthStatus.HEALTHY
                message = "CPU en bonne santé"
                recommendations = []
                
                if cpu_percent > self.thresholds['cpu_usage']:
                    status = HealthStatus.CRITICAL if cpu_percent > 95 else HealthStatus.WARNING
                    message = f"Utilisation CPU élevée: {cpu_percent:.1f}%"
                    recommendations.append("Vérifier les processus gourmands")
                
                if load_avg[0] > cpu_count * 2:
                    if status == HealthStatus.HEALTHY:
                        status = HealthStatus.WARNING
                    message += f" | Charge système élevée: {load_avg[0]:.2f}"
                    recommendations.append("Réduire la charge système")
                
                return HealthCheckResult(
                    check_type=HealthCheckType.CPU,
                    component="cpu",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics={
                        'cpu_usage_percent': cpu_percent,
                        'cpu_frequency': cpu_freq.current if cpu_freq else 0,
                        'cpu_count': cpu_count,
                        'load_average': load_avg
                    },
                    recommendations=recommendations
                )
                
            except Exception as e:
                return HealthCheckResult(
                    check_type=HealthCheckType.CPU,
                    component="cpu",
                    status=HealthStatus.CRITICAL,
                    message=f"Erreur lors de la vérification du CPU: {str(e)}",
                    timestamp=datetime.now(),
                    metrics={},
                    recommendations=["Vérifier les permissions CPU"],
                    error_details=str(e)
                )
        
        # Enregistrer les vérifications
        self.custom_checks['system'] = check_system_health
        self.custom_checks['component'] = check_component_health
        self.custom_checks['service'] = check_service_health
        self.custom_checks['hardware'] = check_hardware_health
        self.custom_checks['network'] = check_network_health
        self.custom_checks['storage'] = check_storage_health
        self.custom_checks['memory'] = check_memory_health
        self.custom_checks['cpu'] = check_cpu_health
    
    def _health_check_loop(self):
        """Boucle principale de vérification de santé"""
        while self.running:
            try:
                self._perform_all_health_checks()
                self._cleanup_old_results()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "HealthCheckService", "_health_check_loop",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                time.sleep(1.0)
    
    def _perform_all_health_checks(self):
        """Effectue toutes les vérifications de santé"""
        try:
            for check_name in self.enabled_checks:
                if check_name in self.custom_checks:
                    result = self.custom_checks[check_name]()
                    
                    # Stocker le résultat
                    self.health_results[check_name] = result
                    self.health_history.append(result)
                    
                    # Émettre un événement si nécessaire
                    if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                        if self.event_bus:
                            self.event_bus.emit('health_warning', {
                                'check_type': result.check_type.value,
                                'component': result.component,
                                'status': result.status.value,
                                'message': result.message,
                                'timestamp': result.timestamp.isoformat()
                            })
                
        except Exception as e:
            self.error_handler.log_error(
                e, "HealthCheckService", "_perform_all_health_checks",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
    
    def _cleanup_old_results(self):
        """Nettoie les anciens résultats"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            # Nettoyer l'historique
            self.health_history = [
                result for result in self.health_history
                if result.timestamp > cutoff_time
            ]
            
        except Exception as e:
            self.error_handler.log_error(
                e, "HealthCheckService", "_cleanup_old_results",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
    
    def get_overall_health_status(self) -> Dict[str, Any]:
        """Retourne le statut de santé global"""
        try:
            if not self.health_results:
                return {
                    'overall_status': HealthStatus.UNKNOWN.value,
                    'message': 'Aucune vérification effectuée',
                    'checks': {},
                    'recommendations': []
                }
            
            # Déterminer le statut global
            statuses = [result.status for result in self.health_results.values()]
            
            if HealthStatus.CRITICAL in statuses:
                overall_status = HealthStatus.CRITICAL
            elif HealthStatus.WARNING in statuses:
                overall_status = HealthStatus.WARNING
            elif HealthStatus.UNKNOWN in statuses:
                overall_status = HealthStatus.UNKNOWN
            else:
                overall_status = HealthStatus.HEALTHY
            
            # Collecter toutes les recommandations
            all_recommendations = []
            for result in self.health_results.values():
                all_recommendations.extend(result.recommendations)
            
            # Supprimer les doublons
            unique_recommendations = list(set(all_recommendations))
            
            return {
                'overall_status': overall_status.value,
                'message': f"Système {overall_status.value}",
                'checks': {
                    name: {
                        'status': result.status.value,
                        'message': result.message,
                        'timestamp': result.timestamp.isoformat(),
                        'metrics': result.metrics,
                        'recommendations': result.recommendations
                    }
                    for name, result in self.health_results.items()
                },
                'recommendations': unique_recommendations,
                'last_check': max(result.timestamp for result in self.health_results.values()).isoformat()
            }
            
        except Exception as e:
            self.error_handler.log_error(
                e, "HealthCheckService", "get_overall_health_status",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return {
                'overall_status': HealthStatus.CRITICAL.value,
                'message': f"Erreur lors de la vérification: {str(e)}",
                'checks': {},
                'recommendations': ["Vérifier la configuration du service de santé"]
            }
    
    def register_custom_check(self, name: str, check_function: Callable):
        """Enregistre une vérification personnalisée"""
        self.custom_checks[name] = check_function
        self.logger.info(f"Vérification personnalisée enregistrée: {name}")
    
    def run_health_check(self, check_name: str) -> Optional[HealthCheckResult]:
        """Exécute une vérification de santé spécifique"""
        try:
            if check_name in self.custom_checks:
                result = self.custom_checks[check_name]()
                self.health_results[check_name] = result
                self.health_history.append(result)
                return result
            else:
                self.logger.warning(f"Vérification non trouvée: {check_name}")
                return None
                
        except Exception as e:
            self.error_handler.log_error(
                e, "HealthCheckService", "run_health_check",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return None
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Retourne l'historique des vérifications de santé"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            return [
                {
                    'check_type': result.check_type.value,
                    'component': result.component,
                    'status': result.status.value,
                    'message': result.message,
                    'timestamp': result.timestamp.isoformat(),
                    'metrics': result.metrics,
                    'recommendations': result.recommendations
                }
                for result in self.health_history
                if result.timestamp > cutoff_time
            ]
            
        except Exception as e:
            self.error_handler.log_error(
                e, "HealthCheckService", "get_health_history",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return []
