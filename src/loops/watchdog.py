"""
Watchdog Alimante
Surveille et redémarre les services en cas de problème
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class Watchdog:
    """
    Watchdog pour surveiller et redémarrer les services
    """
    
    def __init__(self, timeout: float = 300.0, check_interval: float = 30.0):
        """
        Initialise le watchdog
        
        Args:
            timeout: Timeout en secondes avant redémarrage
            check_interval: Intervalle de vérification en secondes
        """
        self.timeout = timeout
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)
        
        # Services surveillés
        self.monitored_services = {}
        
        # État du watchdog
        self.is_running = False
        self.watchdog_thread = None
        
        # Statistiques
        self.stats = {
            'restarts_count': 0,
            'last_restart': 0,
            'start_time': 0,
            'checks_count': 0
        }
        
    def add_service(self, name: str, service: Any, timeout: Optional[float] = None) -> None:
        """
        Ajoute un service à surveiller
        
        Args:
            name: Nom du service
            service: Instance du service
            timeout: Timeout spécifique pour ce service
        """
        try:
            self.monitored_services[name] = {
                'service': service,
                'timeout': timeout or self.timeout,
                'last_heartbeat': time.time(),
                'restart_count': 0,
                'max_restarts': 3
            }
            
            self.logger.info(f"Service {name} ajouté au watchdog")
            
        except Exception as e:
            self.logger.error(f"Erreur ajout service {name}: {e}")
    
    def remove_service(self, name: str) -> None:
        """
        Retire un service de la surveillance
        
        Args:
            name: Nom du service
        """
        try:
            if name in self.monitored_services:
                del self.monitored_services[name]
                self.logger.info(f"Service {name} retiré du watchdog")
            
        except Exception as e:
            self.logger.error(f"Erreur retrait service {name}: {e}")
    
    def heartbeat(self, service_name: str) -> None:
        """
        Enregistre un heartbeat pour un service
        
        Args:
            service_name: Nom du service
        """
        try:
            if service_name in self.monitored_services:
                self.monitored_services[service_name]['last_heartbeat'] = time.time()
                self.logger.debug(f"Heartbeat reçu pour {service_name}")
            
        except Exception as e:
            self.logger.error(f"Erreur heartbeat {service_name}: {e}")
    
    def start(self) -> bool:
        """
        Démarre le watchdog
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if self.is_running:
                self.logger.warning("Watchdog déjà en cours d'exécution")
                return True
            
            self.logger.info("Démarrage du watchdog...")
            
            self.is_running = True
            self.stats['start_time'] = time.time()
            
            # Démarrer le thread de surveillance
            self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
            self.watchdog_thread.start()
            
            self.logger.info("Watchdog démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage watchdog: {e}")
            return False
    
    def stop(self) -> None:
        """Arrête le watchdog"""
        try:
            self.logger.info("Arrêt du watchdog...")
            
            self.is_running = False
            
            # Attendre la fin du thread
            if self.watchdog_thread and self.watchdog_thread.is_alive():
                self.watchdog_thread.join(timeout=5.0)
            
            self.logger.info("Watchdog arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt watchdog: {e}")
    
    def _watchdog_loop(self) -> None:
        """Boucle principale du watchdog"""
        try:
            while self.is_running:
                self._check_services()
                self.stats['checks_count'] += 1
                
                # Attendre l'intervalle de vérification
                time.sleep(self.check_interval)
                
        except Exception as e:
            self.logger.error(f"Erreur boucle watchdog: {e}")
    
    def _check_services(self) -> None:
        """Vérifie l'état des services surveillés"""
        try:
            current_time = time.time()
            
            for service_name, service_info in self.monitored_services.items():
                try:
                    # Vérifier le timeout
                    last_heartbeat = service_info['last_heartbeat']
                    timeout = service_info['timeout']
                    
                    if current_time - last_heartbeat > timeout:
                        self.logger.warning(f"Service {service_name} en timeout ({timeout}s)")
                        self._restart_service(service_name, service_info)
                    else:
                        # Vérifier l'état du service
                        if not self._is_service_healthy(service_name, service_info):
                            self.logger.warning(f"Service {service_name} non sain")
                            self._restart_service(service_name, service_info)
                        else:
                            self.logger.debug(f"Service {service_name} OK")
                
                except Exception as e:
                    self.logger.error(f"Erreur vérification service {service_name}: {e}")
            
        except Exception as e:
            self.logger.error(f"Erreur vérification services: {e}")
    
    def _is_service_healthy(self, service_name: str, service_info: Dict[str, Any]) -> bool:
        """
        Vérifie si un service est sain
        
        Args:
            service_name: Nom du service
            service_info: Informations du service
            
        Returns:
            True si le service est sain, False sinon
        """
        try:
            service = service_info['service']
            
            # Vérifier si le service a une méthode get_status
            if hasattr(service, 'get_status'):
                status = service.get_status()
                if status and 'is_running' in status:
                    return status['is_running']
            
            # Vérifier si le service a une méthode is_running
            if hasattr(service, 'is_running'):
                return service.is_running()
            
            # Par défaut, considérer le service comme sain
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur vérification santé service {service_name}: {e}")
            return False
    
    def _restart_service(self, service_name: str, service_info: Dict[str, Any]) -> None:
        """
        Redémarre un service
        
        Args:
            service_name: Nom du service
            service_info: Informations du service
        """
        try:
            service = service_info['service']
            restart_count = service_info['restart_count']
            max_restarts = service_info['max_restarts']
            
            # Vérifier le nombre maximum de redémarrages
            if restart_count >= max_restarts:
                self.logger.error(f"Service {service_name} a atteint le maximum de redémarrages ({max_restarts})")
                return
            
            self.logger.info(f"Redémarrage du service {service_name}...")
            
            # Arrêter le service
            if hasattr(service, 'stop'):
                service.stop()
            
            # Attendre un peu
            time.sleep(2.0)
            
            # Redémarrer le service
            if hasattr(service, 'start'):
                if service.start():
                    self.logger.info(f"Service {service_name} redémarré avec succès")
                    service_info['restart_count'] += 1
                    service_info['last_heartbeat'] = time.time()
                    self.stats['restarts_count'] += 1
                    self.stats['last_restart'] = time.time()
                else:
                    self.logger.error(f"Échec redémarrage service {service_name}")
            else:
                self.logger.warning(f"Service {service_name} n'a pas de méthode start")
            
        except Exception as e:
            self.logger.error(f"Erreur redémarrage service {service_name}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du watchdog
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_running': self.is_running,
            'timeout': self.timeout,
            'check_interval': self.check_interval,
            'monitored_services': list(self.monitored_services.keys()),
            'stats': self.stats.copy()
        }
    
    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Retourne le statut d'un service surveillé
        
        Args:
            service_name: Nom du service
            
        Returns:
            Statut du service ou None
        """
        try:
            if service_name in self.monitored_services:
                service_info = self.monitored_services[service_name]
                return {
                    'name': service_name,
                    'last_heartbeat': service_info['last_heartbeat'],
                    'timeout': service_info['timeout'],
                    'restart_count': service_info['restart_count'],
                    'max_restarts': service_info['max_restarts'],
                    'is_healthy': self._is_service_healthy(service_name, service_info)
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur statut service {service_name}: {e}")
            return None

