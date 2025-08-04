"""
temperature_controller.py
Module pour la gestion de la température via GPIO Raspberry Pi.

Fonctionnalités :
- Lecture de la température actuelle depuis un capteur DHT22.
- Activation ou désactivation du relais pour maintenir une température optimale.
"""

import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from src.utils.gpio_manager import GPIOManager, PinAssignments, PinConfig, PinMode

@dataclass
class TemperatureConfig:
    optimal: float
    tolerance: float
    min_temp: float
    max_temp: float

class TemperatureController:
    """
    Classe pour gérer la température avec GPIO.
    """
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        """
        Initialise le contrôleur de température.

        :param gpio_manager: Instance du gestionnaire GPIO.
        :param config: Configuration pour les seuils de température.
        """
        self.gpio_manager = gpio_manager
        self.config = TemperatureConfig(
            optimal=config['optimal'],
            tolerance=config['tolerance'],
            min_temp=config.get('min', 15.0),
            max_temp=config.get('max', 35.0)
        )
        
        # Configuration des pins
        self._setup_pins()
        
    def _setup_pins(self):
        """Configure les pins GPIO nécessaires"""
        # Pin du capteur DHT22
        temp_sensor_config = PinConfig(
            pin=PinAssignments.TEMP_HUMIDITY_PIN,
            mode=PinMode.INPUT
        )
        self.gpio_manager.setup_pin(temp_sensor_config)
        
        # Pin du relais de chauffage
        heating_relay_config = PinConfig(
            pin=PinAssignments.HEATING_RELAY_PIN,
            mode=PinMode.OUTPUT,
            initial_state=False  # Relais désactivé au démarrage
        )
        self.gpio_manager.setup_pin(heating_relay_config)

    def read_temperature(self) -> Optional[float]:
        """
        Lit la température actuelle depuis le capteur DHT22.

        :return: Température actuelle (en °C) ou None si la lecture échoue.
        """
        try:
            # Simulation pour le moment - à remplacer par la vraie lecture DHT22
            # import adafruit_dht
            # dht = adafruit_dht.DHT22(PinAssignments.TEMP_HUMIDITY_PIN)
            # temp = dht.temperature
            
            # Simulation temporaire
            import random
            temp = 20 + random.uniform(-2, 2)  # Simulation 18-22°C
            
            if temp is not None and self.config.min_temp <= temp <= self.config.max_temp:
                logging.info(f"Température lue: {temp:.1f}°C")
                return temp
            else:
                logging.warning(f"Température hors limites: {temp}°C")
                return None
                
        except Exception as e:
            logging.error(f"Erreur lors de la lecture de la température: {e}")
            return None

    def control_temperature(self) -> bool:
        """
        Contrôle la température en activant ou désactivant le relais.

        :return: True si le contrôle a été effectué, False sinon
        """
        current_temperature = self.read_temperature()

        if current_temperature is None:
            logging.warning("Impossible de lire la température.")
            return False

        logging.info(f"Température actuelle: {current_temperature:.1f}°C (optimal: {self.config.optimal}°C)")

        # Logique de contrôle
        if current_temperature < self.config.optimal - self.config.tolerance:
            self.activate_heating()
            return True
        elif current_temperature > self.config.optimal + self.config.tolerance:
            self.deactivate_heating()
            return True
        else:
            logging.info("Température dans la plage optimale.")
            return True

    def activate_heating(self) -> bool:
        """
        Active le relais de chauffage.
        
        :return: True si activé avec succès
        """
        success = self.gpio_manager.write_digital(PinAssignments.HEATING_RELAY_PIN, True)
        if success:
            logging.info("Relais de chauffage activé")
        else:
            logging.error("Échec de l'activation du relais de chauffage")
        return success

    def deactivate_heating(self) -> bool:
        """
        Désactive le relais de chauffage.
        
        :return: True si désactivé avec succès
        """
        success = self.gpio_manager.write_digital(PinAssignments.HEATING_RELAY_PIN, False)
        if success:
            logging.info("Relais de chauffage désactivé")
        else:
            logging.error("Échec de la désactivation du relais de chauffage")
        return success

    def is_heating_active(self) -> bool:
        """
        Vérifie si le chauffage est actuellement actif.
        
        :return: True si le chauffage est actif
        """
        return self.gpio_manager.read_digital(PinAssignments.HEATING_RELAY_PIN) or False

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du contrôleur.
        
        :return: Dictionnaire avec les informations de statut
        """
        current_temp = self.read_temperature()
        heating_active = self.is_heating_active()
        
        return {
            "current_temperature": current_temp,
            "optimal_temperature": self.config.optimal,
            "tolerance": self.config.tolerance,
            "heating_active": heating_active,
            "status": "optimal" if current_temp and abs(current_temp - self.config.optimal) <= self.config.tolerance else "adjusting"
        }

    def check_status(self) -> bool:
        """
        Vérifie si le contrôleur est fonctionnel.
        
        :return: True si fonctionnel
        """
        try:
            temp = self.read_temperature()
            return temp is not None
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du statut: {e}")
            return False
