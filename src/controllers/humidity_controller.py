"""
humidity_controller.py
Module pour la gestion de l'humidité via GPIO Raspberry Pi.

Fonctionnalités :
- Lecture de l'humidité actuelle depuis un capteur DHT22.
- Activation ou désactivation de l'ultrasonic mist pour maintenir une humidité optimale.
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from src.controllers.base_controller import BaseController
from src.utils.gpio_manager import GPIOManager, PinConfig, PinMode

@dataclass
class HumidityConfig:
    optimal: float
    tolerance: float
    min_humidity: float
    max_humidity: float
    spray_duration: int  # Durée de pulvérisation en secondes

class HumidityController(BaseController):
    """
    Classe pour gérer l'humidité avec GPIO.
    """
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        """
        Initialise le contrôleur d'humidité.

        :param gpio_manager: Instance du gestionnaire GPIO.
        :param config: Configuration pour les seuils d'humidité.
        """
        super().__init__(gpio_manager, config)
        
        # Extraire la configuration d'humidité depuis la config système
        humidity_config = config.get('humidity', {})
        self.humidity_config = HumidityConfig(
            optimal=humidity_config.get('optimal', 60.0),
            tolerance=humidity_config.get('tolerance', 10.0),
            min_humidity=humidity_config.get('min', 30.0),
            max_humidity=humidity_config.get('max', 90.0),
            spray_duration=humidity_config.get('spray_duration', 3)
        )
        
        # Configuration des pins
        self._setup_pins()
        self.initialized = True
        
    def _setup_pins(self):
        """Configure les pins GPIO nécessaires"""
        try:
            # Récupérer la configuration GPIO depuis la config système
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            
            # Pin du capteur DHT22 (partagé avec température)
            temp_humidity_pin = pin_assignments.get('TEMP_HUMIDITY_PIN', 4)
            humidity_sensor_config = PinConfig(
                pin=temp_humidity_pin,
                mode=PinMode.INPUT
            )
            self.gpio_manager.setup_pin(humidity_sensor_config)
            
            # Pin du relais de pulvérisation
            humidity_relay_pin = pin_assignments.get('HUMIDITY_RELAY_PIN', 23)
            spray_relay_config = PinConfig(
                pin=humidity_relay_pin,
                mode=PinMode.OUTPUT,
                initial_state=False  # Relais désactivé au démarrage
            )
            self.gpio_manager.setup_pin(spray_relay_config)
            
            self.logger.info(f"Pins configurés - Capteur: {temp_humidity_pin}, Relais: {humidity_relay_pin}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la configuration des pins: {e}")
            self.record_error(e)
            raise

    def read_humidity(self) -> Optional[float]:
        """
        Lit l'humidité actuelle depuis le capteur DHT22.

        :return: Humidité actuelle (en %) ou None si la lecture échoue.
        """
        try:
            # Lecture réelle du capteur DHT22
            import adafruit_dht
            import board
            
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            temp_humidity_pin = pin_assignments.get('TEMP_HUMIDITY_PIN', 4)
            
            # Initialiser le capteur DHT22 sur le pin configuré
            dht = adafruit_dht.DHT22(getattr(board, f'D{temp_humidity_pin}'))
            
            # Lire l'humidité
            humidity = dht.humidity
            
            if humidity is not None and self.humidity_config.min_humidity <= humidity <= self.humidity_config.max_humidity:
                self.logger.info(f"Humidité lue: {humidity:.1f}%")
                return humidity
            else:
                self.logger.warning(f"Humidité hors limites: {humidity}%")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture de l'humidité: {e}")
            self.record_error(e)
            return None

    def control_humidity(self) -> bool:
        """
        Contrôle l'humidité en activant ou désactivant l'ultrasonic mist.

        :return: True si le contrôle a été effectué, False sinon
        """
        current_humidity = self.read_humidity()
        
        if current_humidity is None:
            return False
        
        try:
            # Vérifier si la pulvérisation est nécessaire
            if current_humidity < (self.humidity_config.optimal - self.humidity_config.tolerance):
                if not self.is_sprayer_active():
                    self.activate_sprayer()
                    return True
            elif current_humidity > (self.humidity_config.optimal + self.humidity_config.tolerance):
                if self.is_sprayer_active():
                    self.deactivate_sprayer()
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors du contrôle de l'humidité: {e}")
            self.record_error(e)
            return False

    def control(self) -> bool:
        """
        Méthode de contrôle principale (implémentation de l'abstraction)
        
        :return: True si le contrôle a été effectué, False sinon
        """
        return self.control_humidity()

    def activate_sprayer(self) -> bool:
        """
        Active l'ultrasonic mist d'humidité.
        
        :return: True si l'activation a réussi, False sinon
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            humidity_pin = pin_assignments.get('HUMIDITY_RELAY_PIN', 23)
            
            self.gpio_manager.set_pin_state(humidity_pin, True)
            self.logger.info("Ultrasonic mist activé")
            
            # Désactiver après la durée configurée
            time.sleep(self.humidity_config.spray_duration)
            self.deactivate_sprayer()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'activation de l'ultrasonic mist: {e}")
            self.record_error(e)
            return False

    def deactivate_sprayer(self) -> bool:
        """
        Désactive l'ultrasonic mist d'humidité.
        
        :return: True si la désactivation a réussi, False sinon
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            humidity_pin = pin_assignments.get('HUMIDITY_RELAY_PIN', 23)
            
            self.gpio_manager.set_pin_state(humidity_pin, False)
            self.logger.info("Ultrasonic mist désactivé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la désactivation de l'ultrasonic mist: {e}")
            self.record_error(e)
            return False

    def is_sprayer_active(self) -> bool:
        """
        Vérifie si l'ultrasonic mist est actuellement actif.
        
        :return: True si l'ultrasonic mist est actif, False sinon
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            humidity_pin = pin_assignments.get('HUMIDITY_RELAY_PIN', 23)
            
            return self.gpio_manager.get_pin_state(humidity_pin)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de l'ultrasonic mist: {e}")
            self.record_error(e)
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du contrôleur (implémentation de l'abstraction)
        
        :return: Dictionnaire contenant le statut
        """
        try:
            current_humidity = self.read_humidity()
            sprayer_active = self.is_sprayer_active()
            
            return {
                "controller": "humidity",
                "initialized": self.initialized,
                "current_humidity": current_humidity,
                "sprayer_active": sprayer_active,
                "target_humidity": self.humidity_config.optimal,
                "tolerance": self.humidity_config.tolerance,
                "min_humidity": self.humidity_config.min_humidity,
                "max_humidity": self.humidity_config.max_humidity,
                "spray_duration": self.humidity_config.spray_duration,
                "error_count": self.error_count,
                "last_error": str(self.last_error) if self.last_error else None
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du statut: {e}")
            self.record_error(e)
            return {
                "controller": "humidity",
                "initialized": self.initialized,
                "error": str(e),
                "error_count": self.error_count
            }

    def check_status(self) -> bool:
        """
        Vérifie le statut du contrôleur.
        
        :return: True si tout fonctionne correctement, False sinon
        """
        try:
            # Vérifier que le capteur fonctionne
            humidity = self.read_humidity()
            if humidity is None:
                return False
            
            # Vérifier que le relais répond
            sprayer_state = self.is_sprayer_active()
            
            self.logger.info(f"Statut vérifié - Humidité: {humidity}%, Ultrasonic mist: {sprayer_state}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du statut: {e}")
            self.record_error(e)
            return False
