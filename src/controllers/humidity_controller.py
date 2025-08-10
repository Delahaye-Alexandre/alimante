"""
humidity_controller.py
Module pour la gestion de l'humidité via GPIO Raspberry Pi.

Fonctionnalités :
- Lecture de l'humidité actuelle depuis un capteur DHT22.
- Activation ou désactivation du pulvérisateur pour maintenir une humidité optimale.
"""

import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from src.controllers.base_controller import BaseController
from src.utils.gpio_manager import GPIOManager, PinAssignments, PinConfig, PinMode

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
        
        self.humidity_config = HumidityConfig(
            optimal=config['optimal'],
            tolerance=config['tolerance'],
            min_humidity=config.get('min', 30.0),
            max_humidity=config.get('max', 90.0),
            spray_duration=config.get('spray_duration', 3)
        )
        
        # Configuration des pins
        self._setup_pins()
        self.initialized = True
        
    def _setup_pins(self):
        """Configure les pins GPIO nécessaires"""
        # Pin du capteur DHT22 (partagé avec température)
        humidity_sensor_config = PinConfig(
            pin=PinAssignments.TEMP_HUMIDITY_PIN,
            mode=PinMode.INPUT
        )
        self.gpio_manager.setup_pin(humidity_sensor_config)
        
        # Pin du relais de pulvérisation
        spray_relay_config = PinConfig(
            pin=PinAssignments.HUMIDITY_RELAY_PIN,
            mode=PinMode.OUTPUT,
            initial_state=False  # Relais désactivé au démarrage
        )
        self.gpio_manager.setup_pin(spray_relay_config)

    def read_humidity(self) -> Optional[float]:
        """
        Lit l'humidité actuelle depuis le capteur DHT22.

        :return: Humidité actuelle (en %) ou None si la lecture échoue.
        """
        try:
            # Lecture réelle du capteur DHT22
            import adafruit_dht
            import board
            
            # Initialiser le capteur DHT22 sur le pin configuré
            dht = adafruit_dht.DHT22(board.D4)  # Pin 4 pour DHT22
            
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
        Contrôle l'humidité en activant ou désactivant le pulvérisateur.

        :return: True si le contrôle a été effectué, False sinon
        """
        current_humidity = self.read_humidity()

        if current_humidity is None:
            self.logger.warning("Impossible de lire l'humidité.")
            return False

        self.logger.info(f"Humidité actuelle: {current_humidity:.1f}% (optimal: {self.humidity_config.optimal}%)")

        # Logique de contrôle
        if current_humidity < self.humidity_config.optimal - self.humidity_config.tolerance:
            self.activate_sprayer()
            return True
        elif current_humidity > self.humidity_config.optimal + self.humidity_config.tolerance:
            self.deactivate_sprayer()
            return True
        else:
            self.logger.info("Humidité dans la plage optimale.")
            return True

    def control(self) -> bool:
        """Méthode principale de contrôle - alias pour control_humidity"""
        return self.control_humidity()

    def activate_sprayer(self) -> bool:
        """
        Active le pulvérisateur pour augmenter l'humidité.
        
        :return: True si activé avec succès
        """
        success = self.gpio_manager.write_digital(PinAssignments.HUMIDITY_RELAY_PIN, True)
        if success:
            self.logger.info(f"Pulvérisateur activé pour {self.humidity_config.spray_duration} secondes")
            # Désactivation automatique après la durée configurée
            time.sleep(self.humidity_config.spray_duration)
            self.deactivate_sprayer()
        else:
            self.logger.error("Échec de l'activation du pulvérisateur")
        return success

    def deactivate_sprayer(self) -> bool:
        """
        Désactive le pulvérisateur.
        
        :return: True si désactivé avec succès
        """
        success = self.gpio_manager.write_digital(PinAssignments.HUMIDITY_RELAY_PIN, False)
        if success:
            self.logger.info("Pulvérisateur désactivé")
        else:
            self.logger.error("Échec de la désactivation du pulvérisateur")
        return success

    def is_sprayer_active(self) -> bool:
        """
        Vérifie si le pulvérisateur est actuellement actif.
        
        :return: True si le pulvérisateur est actif
        """
        return self.gpio_manager.read_digital(PinAssignments.HUMIDITY_RELAY_PIN) or False

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du contrôleur.
        
        :return: Dictionnaire avec les informations de statut
        """
        current_humidity = self.read_humidity()
        sprayer_active = self.is_sprayer_active()
        
        return {
            "current_humidity": current_humidity,
            "optimal_humidity": self.humidity_config.optimal,
            "tolerance": self.humidity_config.tolerance,
            "sprayer_active": sprayer_active,
            "status": "optimal" if current_humidity and abs(current_humidity - self.humidity_config.optimal) <= self.humidity_config.tolerance else "adjusting"
        }

    def check_status(self) -> bool:
        """
        Vérifie si le contrôleur est fonctionnel.
        
        :return: True si fonctionnel
        """
        try:
            humidity = self.read_humidity()
            return humidity is not None
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du statut: {e}")
            return False
