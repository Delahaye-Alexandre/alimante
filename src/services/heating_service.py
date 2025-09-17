"""
Service de gestion du chauffage
Contrôle les éléments chauffants selon les profils d'espèces
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

class HeatingService:
    """
    Service de gestion du chauffage
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de chauffage
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Driver de chauffage
        self.heater_driver = None
        
        # Configuration
        self.gpio_config = config.get('gpio_config', {})
        self.safety_limits = config.get('safety_limits', {})
        self.heating_config = config.get('actuators', {}).get('heating', {})
        
        # État du chauffage
        self.is_heating = False
        self.target_temperature = 25.0
        self.current_temperature = None
        self.hysteresis = 1.0
        
        # Statistiques
        self.stats = {
            'heating_time': 0,
            'cycles_count': 0,
            'last_heating_start': 0,
            'last_heating_stop': 0
        }
        
        # S'abonner aux événements de contrôle
        if self.event_bus:
            self.event_bus.subscribe('heating_control_request', self._on_heating_control_request)
        
    def initialize(self) -> bool:
        """
        Initialise le service de chauffage
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du service de chauffage...")
            
            # Récupérer la configuration GPIO
            gpio_pins = self.gpio_config.get('gpio_pins', {})
            actuators = gpio_pins.get('actuators', {})
            heater_config = actuators.get('heater', {})
            
            if not heater_config:
                self.logger.error("Configuration chauffage non trouvée")
                return False
            
            # Créer le driver de relais pour le chauffage
            driver_config = DriverConfig(
                name="heater",
                enabled=self.heating_config.get('enabled', True),
                timeout=5.0,
                retry_attempts=3,
                retry_delay=1.0
            )
            
            relay_pin = heater_config.get('relay_pin', 19)
            self.heater_driver = RelayDriver(driver_config, relay_pin)
            
            if not self.heater_driver.initialize():
                self.logger.error("Échec initialisation driver chauffage")
                return False
            
            # Récupérer les paramètres de sécurité
            temp_limits = self.safety_limits.get('temperature', {})
            self.hysteresis = temp_limits.get('hysteresis', 1.0)
            
            self.logger.info("Service de chauffage initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service chauffage: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre le service de chauffage
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.heater_driver:
                return False
            
            if self.heater_driver.start():
                self.logger.info("Service de chauffage démarré")
                return True
            else:
                self.logger.error("Échec démarrage service chauffage")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur démarrage service chauffage: {e}")
            return False
    
    def stop(self) -> None:
        """Arrête le service de chauffage"""
        try:
            # Arrêter le chauffage
            self.set_heating(False)
            
            # Arrêter le driver
            if self.heater_driver:
                self.heater_driver.stop()
            
            self.logger.info("Service de chauffage arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service chauffage: {e}")
    
    def update(self, sensor_data: Dict[str, Any]) -> None:
        """
        Met à jour le service de chauffage
        
        Args:
            sensor_data: Données des capteurs
        """
        try:
            # Récupérer la température actuelle
            dht22_data = sensor_data.get('dht22', {})
            self.current_temperature = dht22_data.get('temperature')
            
            if self.current_temperature is None:
                self.logger.warning("Capteur DHT22 non disponible - service chauffage en attente")
                return
            
            # Mettre à jour les statistiques
            if self.is_heating:
                current_time = time.time()
                if self.stats['last_heating_start'] > 0:
                    self.stats['heating_time'] += current_time - self.stats['last_heating_start']
                self.stats['last_heating_start'] = current_time
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour service chauffage: {e}")
    
    def set_heating(self, heating: bool) -> bool:
        """
        Active ou désactive le chauffage
        
        Args:
            heating: True pour activer, False pour désactiver
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.heater_driver:
                return False
            
            # Vérifier les limites de sécurité
            if heating and self.current_temperature is not None:
                temp_limits = self.safety_limits.get('temperature', {})
                max_temp = temp_limits.get('critical_max', 45.0)
                
                if self.current_temperature >= max_temp:
                    self.logger.warning(f"Chauffage refusé: température trop élevée ({self.current_temperature:.1f}°C)")
                    return False
            
            # Appliquer la commande
            if self.heater_driver.set_state(heating):
                if heating != self.is_heating:
                    self.is_heating = heating
                    
                    if heating:
                        self.stats['last_heating_start'] = time.time()
                        self.stats['cycles_count'] += 1
                        self.logger.info("Chauffage activé")
                    else:
                        self.stats['last_heating_stop'] = time.time()
                        self.logger.info("Chauffage désactivé")
                    
                    # Émettre un événement
                    if self.event_bus:
                        self.event_bus.emit('heating_changed', {
                            'heating': heating,
                            'temperature': self.current_temperature,
                            'timestamp': time.time()
                        })
                
                return True
            else:
                self.logger.error("Échec commande chauffage")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur commande chauffage: {e}")
            return False
    
    def set_target_temperature(self, temperature: float) -> bool:
        """
        Définit la température cible
        
        Args:
            temperature: Température cible en °C
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Vérifier les limites de sécurité
            temp_limits = self.safety_limits.get('temperature', {})
            min_temp = temp_limits.get('warning_min', 10.0)
            max_temp = temp_limits.get('warning_max', 40.0)
            
            if temperature < min_temp or temperature > max_temp:
                self.logger.warning(f"Température cible hors limites: {temperature:.1f}°C")
                return False
            
            self.target_temperature = temperature
            self.logger.info(f"Température cible définie: {temperature:.1f}°C")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition température cible: {e}")
            return False
    
    def get_heating_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du chauffage
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_heating': self.is_heating,
            'target_temperature': self.target_temperature,
            'current_temperature': self.current_temperature,
            'hysteresis': self.hysteresis,
            'stats': self.stats.copy()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du service
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'service_name': 'heating_service',
            'enabled': self.heating_config.get('enabled', True),
            'heating_status': self.get_heating_status(),
            'driver_status': self.heater_driver.get_status() if self.heater_driver else None
        }
    
    def _on_heating_control_request(self, event_data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement pour une demande de contrôle du chauffage"""
        try:
            self.logger.info(f"Demande de contrôle chauffage reçue: {event_data}")
            
            state = event_data.get('state', False)
            target_temp = event_data.get('target_temperature', 25.0)
            power_level = event_data.get('power_level', 100)
            
            # Mettre à jour la température cible
            self.target_temperature = target_temp
            
            # Contrôler le chauffage
            if state:
                self.start()
                self.logger.info(f"Chauffage activé - Température cible: {target_temp}°C")
            else:
                self.stop()
                self.logger.info("Chauffage désactivé")
                
        except Exception as e:
            self.logger.error(f"Erreur gestion événement chauffage: {e}")
    
    def cleanup(self) -> None:
        """Nettoie le service de chauffage"""
        try:
            self.stop()
            
            if self.heater_driver:
                self.heater_driver.cleanup()
                self.heater_driver = None
            
            self.logger.info("Service de chauffage nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service chauffage: {e}")

