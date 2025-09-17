"""
Service de gestion de l'humidification
Contrôle l'humidificateur selon les profils d'espèces
"""

import time
import logging
from typing import Dict, Any, Optional
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from controllers.drivers.relay_driver import RelayDriver
from controllers.drivers.base_driver import DriverConfig

class HumidificationService:
    """
    Service de gestion de l'humidification
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service d'humidification
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Driver d'humidification
        self.humidifier_driver = None
        
        # Configuration
        self.gpio_config = config.get('gpio_config', {})
        self.safety_limits = config.get('safety_limits', {})
        self.humidification_config = config.get('actuators', {}).get('humidification', {})
        
        # État de l'humidification
        self.is_humidifying = False
        self.target_humidity = 60.0
        self.current_humidity = None
        self.hysteresis = 5.0
        
        # Contrôle cyclique
        self.min_cycle_time = 300  # 5 minutes minimum entre les cycles
        self.last_humidification_stop = 0
        
        # Statistiques
        self.stats = {
            'humidification_time': 0,
            'cycles_count': 0,
            'last_humidification_start': 0,
            'last_humidification_stop': 0
        }
        
        # S'abonner aux événements de contrôle
        if self.event_bus:
            self.event_bus.subscribe('humidification_control_request', self._on_humidification_control_request)
        
    def initialize(self) -> bool:
        """
        Initialise le service d'humidification
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du service d'humidification...")
            
            # Récupérer la configuration GPIO
            gpio_pins = self.gpio_config.get('gpio_pins', {})
            actuators = gpio_pins.get('actuators', {})
            humidifier_config = actuators.get('humidifier', {})
            
            if not humidifier_config:
                self.logger.error("Configuration humidificateur non trouvée")
                return False
            
            # Créer le driver de relais pour l'humidificateur
            driver_config = DriverConfig(
                name="humidifier",
                enabled=self.humidification_config.get('enabled', True),
                timeout=5.0,
                retry_attempts=3,
                retry_delay=1.0
            )
            
            relay_pin = humidifier_config.get('relay_pin', 5)
            self.humidifier_driver = RelayDriver(driver_config, relay_pin)
            
            if not self.humidifier_driver.initialize():
                self.logger.error("Échec initialisation driver humidificateur")
                return False
            
            # Récupérer les paramètres de sécurité
            hum_limits = self.safety_limits.get('humidity', {})
            self.hysteresis = hum_limits.get('hysteresis', 5.0)
            
            # Récupérer les paramètres d'humidification
            self.min_cycle_time = self.humidification_config.get('min_cycle_time', 300)
            
            self.logger.info("Service d'humidification initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service humidification: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre le service d'humidification
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.humidifier_driver:
                return False
            
            if self.humidifier_driver.start():
                self.logger.info("Service d'humidification démarré")
                return True
            else:
                self.logger.error("Échec démarrage service humidification")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur démarrage service humidification: {e}")
            return False
    
    def stop(self) -> None:
        """Arrête le service d'humidification"""
        try:
            # Arrêter l'humidification
            self.set_humidification(False)
            
            # Arrêter le driver
            if self.humidifier_driver:
                self.humidifier_driver.stop()
            
            self.logger.info("Service d'humidification arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service humidification: {e}")
    
    def update(self, sensor_data: Dict[str, Any]) -> None:
        """
        Met à jour le service d'humidification
        
        Args:
            sensor_data: Données des capteurs
        """
        try:
            # Récupérer l'humidité actuelle
            dht22_data = sensor_data.get('dht22', {})
            self.current_humidity = dht22_data.get('humidity')
            
            # Mettre à jour les statistiques
            if self.is_humidifying:
                current_time = time.time()
                if self.stats['last_humidification_start'] > 0:
                    self.stats['humidification_time'] += current_time - self.stats['last_humidification_start']
                self.stats['last_humidification_start'] = current_time
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour service humidification: {e}")
    
    def set_humidification(self, humidifying: bool) -> bool:
        """
        Active ou désactive l'humidification
        
        Args:
            humidifying: True pour activer, False pour désactiver
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.humidifier_driver:
                return False
            
            # Vérifier les limites de sécurité
            if humidifying and self.current_humidity is not None:
                hum_limits = self.safety_limits.get('humidity', {})
                max_humidity = hum_limits.get('critical_max', 99.0)
                
                if self.current_humidity >= max_humidity:
                    self.logger.warning(f"Humidification refusée: humidité trop élevée ({self.current_humidity:.1f}%)")
                    return False
            
            # Vérifier le temps minimum entre les cycles
            if humidifying and not self.is_humidifying:
                current_time = time.time()
                if current_time - self.last_humidification_stop < self.min_cycle_time:
                    self.logger.debug("Humidification refusée: cycle trop récent")
                    return False
            
            # Appliquer la commande
            if self.humidifier_driver.set_state(humidifying):
                if humidifying != self.is_humidifying:
                    self.is_humidifying = humidifying
                    
                    if humidifying:
                        self.stats['last_humidification_start'] = time.time()
                        self.stats['cycles_count'] += 1
                        self.logger.info("Humidification activée")
                    else:
                        self.stats['last_humidification_stop'] = time.time()
                        self.last_humidification_stop = time.time()
                        self.logger.info("Humidification désactivée")
                    
                    # Émettre un événement
                    if self.event_bus:
                        self.event_bus.emit('humidification_changed', {
                            'humidifying': humidifying,
                            'humidity': self.current_humidity,
                            'timestamp': time.time()
                        })
                
                return True
            else:
                self.logger.error("Échec commande humidification")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur commande humidification: {e}")
            return False
    
    def set_target_humidity(self, humidity: float) -> bool:
        """
        Définit l'humidité cible
        
        Args:
            humidity: Humidité cible en %
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Vérifier les limites de sécurité
            hum_limits = self.safety_limits.get('humidity', {})
            min_humidity = hum_limits.get('warning_min', 20.0)
            max_humidity = hum_limits.get('warning_max', 90.0)
            
            if humidity < min_humidity or humidity > max_humidity:
                self.logger.warning(f"Humidité cible hors limites: {humidity:.1f}%")
                return False
            
            self.target_humidity = humidity
            self.logger.info(f"Humidité cible définie: {humidity:.1f}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition humidité cible: {e}")
            return False
    
    def get_humidification_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de l'humidification
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_humidifying': self.is_humidifying,
            'target_humidity': self.target_humidity,
            'current_humidity': self.current_humidity,
            'hysteresis': self.hysteresis,
            'min_cycle_time': self.min_cycle_time,
            'stats': self.stats.copy()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du service
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'service_name': 'humidification_service',
            'enabled': self.humidification_config.get('enabled', True),
            'humidification_status': self.get_humidification_status(),
            'driver_status': self.humidifier_driver.get_status() if self.humidifier_driver else None
        }
    
    def _on_humidification_control_request(self, event_data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement pour une demande de contrôle de l'humidification"""
        try:
            self.logger.info(f"Demande de contrôle humidification reçue: {event_data}")
            
            state = event_data.get('state', False)
            target_humidity = event_data.get('target_humidity', 60.0)
            intensity = event_data.get('intensity', 80)
            
            # Mettre à jour l'humidité cible
            self.target_humidity = target_humidity
            
            # Contrôler l'humidification
            if state:
                self.start()
                self.logger.info(f"Humidification activée - Humidité cible: {target_humidity}%")
            else:
                self.stop()
                self.logger.info("Humidification désactivée")
                
        except Exception as e:
            self.logger.error(f"Erreur gestion événement humidification: {e}")
    
    def cleanup(self) -> None:
        """Nettoie le service d'humidification"""
        try:
            self.stop()
            
            if self.humidifier_driver:
                self.humidifier_driver.cleanup()
                self.humidifier_driver = None
            
            self.logger.info("Service d'humidification nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service humidification: {e}")

