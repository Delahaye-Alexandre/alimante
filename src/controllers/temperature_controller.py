"""
temperature_controller.py
Module pour la gestion de la température via GPIO Raspberry Pi.

Fonctionnalités :
- Lecture de la température actuelle depuis un capteur DHT22.
- Activation ou désactivation du relais pour maintenir une température optimale.
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from .base_controller import BaseController
from ..utils.gpio_manager import GPIOManager, PinAssignments, PinConfig, PinMode

@dataclass
class TemperatureConfig:
    optimal: float
    tolerance: float
    min_temp: float
    max_temp: float

class TemperatureController(BaseController):
    """
    Classe pour gérer la température avec GPIO.
    """
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        """
        Initialise le contrôleur de température.

        :param gpio_manager: Instance du gestionnaire GPIO.
        :param config: Configuration pour les seuils de température.
        """
        super().__init__(gpio_manager, config)
        
        # Extraire la configuration de température depuis la config système
        temp_config = config.get('temperature', {})
        self.temp_config = TemperatureConfig(
            optimal=temp_config.get('optimal', 25.0),
            tolerance=temp_config.get('tolerance', 2.0),
            min_temp=temp_config.get('min', 15.0),
            max_temp=temp_config.get('max', 35.0)
        )
        
        # Configuration des pins depuis la config GPIO
        self._setup_pins()
        self.initialized = True
        
    def _setup_pins(self):
        """Configure les pins GPIO nécessaires"""
        try:
            # Utiliser le service de configuration GPIO
            from ..services.gpio_config_service import GPIOConfigService
            gpio_service = GPIOConfigService()
            
            # Pin du capteur DHT22
            temp_sensor_pin = gpio_service.get_sensor_pin('temp_humidity')
            if temp_sensor_pin is None:
                temp_sensor_pin = gpio_service.get_pin_assignment('TEMP_HUMIDITY_PIN')
            
            temp_sensor_config = PinConfig(
                pin=temp_sensor_pin,
                mode=PinMode.INPUT
            )
            self.gpio_manager.setup_pin(temp_sensor_config)
            
            # Pin du relais de chauffage
            heating_relay_pin = gpio_service.get_actuator_pin('heating_relay')
            if heating_relay_pin is None:
                heating_relay_pin = gpio_service.get_pin_assignment('HEATING_RELAY_PIN')
            
            heating_relay_config = PinConfig(
                pin=heating_relay_pin,
                mode=PinMode.OUTPUT,
                initial_state=False  # Relais désactivé au démarrage
            )
            self.gpio_manager.setup_pin(heating_relay_config)
            
            self.logger.info(f"Pins configurés - Capteur: {temp_sensor_pin}, Relais: {heating_relay_pin}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la configuration des pins: {e}")
            self.record_error(e)
            raise

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
            
            if temp is not None and self.temp_config.min_temp <= temp <= self.temp_config.max_temp:
                self.logger.info(f"Température lue: {temp:.1f}°C")
                return temp
            else:
                self.logger.warning(f"Température hors limites: {temp}°C")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture de la température: {e}")
            self.record_error(e)
            return None

    def control(self) -> bool:
        """
        Méthode de contrôle principale (implémentation de l'abstraction)
        
        :return: True si le contrôle a été effectué, False sinon
        """
        return self.control_temperature()

    def control_temperature(self) -> bool:
        """
        Contrôle la température en activant ou désactivant le relais.

        :return: True si le contrôle a été effectué, False sinon
        """
        current_temperature = self.read_temperature()
        
        if current_temperature is None:
            return False
        
        try:
            # Vérifier si le chauffage est nécessaire
            if current_temperature < (self.temp_config.optimal - self.temp_config.tolerance):
                if not self.is_heating_active():
                    self.activate_heating()
                    return True
            elif current_temperature > (self.temp_config.optimal + self.temp_config.tolerance):
                if self.is_heating_active():
                    self.deactivate_heating()
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors du contrôle de la température: {e}")
            self.record_error(e)
            return False

    def activate_heating(self) -> bool:
        """
        Active le relais de chauffage.

        :return: True si l'activation a réussi, False sinon.
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            heating_pin = pin_assignments.get('HEATING_RELAY_PIN', 18)
            
            self.gpio_manager.set_pin_state(heating_pin, True)
            self.logger.info("Chauffage activé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'activation du chauffage: {e}")
            self.record_error(e)
            return False

    def deactivate_heating(self) -> bool:
        """
        Désactive le relais de chauffage.

        :return: True si la désactivation a réussi, False sinon.
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            heating_pin = pin_assignments.get('HEATING_RELAY_PIN', 18)
            
            self.gpio_manager.set_pin_state(heating_pin, False)
            self.logger.info("Chauffage désactivé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la désactivation du chauffage: {e}")
            self.record_error(e)
            return False

    def is_heating_active(self) -> bool:
        """
        Vérifie si le chauffage est actuellement actif.

        :return: True si le chauffage est actif, False sinon.
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            heating_pin = pin_assignments.get('HEATING_RELAY_PIN', 18)
            
            return self.gpio_manager.get_pin_state(heating_pin)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du chauffage: {e}")
            self.record_error(e)
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du contrôleur (implémentation de l'abstraction)
        
        :return: Dictionnaire contenant le statut
        """
        try:
            current_temp = self.read_temperature()
            heating_active = self.is_heating_active()
            
            return {
                "controller": "temperature",
                "initialized": self.initialized,
                "current_temperature": current_temp,
                "heating_active": heating_active,
                "target_temperature": self.temp_config.optimal,
                "tolerance": self.temp_config.tolerance,
                "min_temp": self.temp_config.min_temp,
                "max_temp": self.temp_config.max_temp,
                "error_count": self.error_count,
                "last_error": str(self.last_error) if self.last_error else None
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du statut: {e}")
            self.record_error(e)
            return {
                "controller": "temperature",
                "initialized": self.initialized,
                "error": str(e),
                "error_count": self.error_count
            }

    def check_status(self) -> bool:
        """
        Vérifie le statut du contrôleur.

        :return: True si tout fonctionne correctement, False sinon.
        """
        try:
            # Vérifier que le capteur fonctionne
            temp = self.read_temperature()
            if temp is None:
                return False
            
            # Vérifier que le relais répond
            heating_state = self.is_heating_active()
            
            self.logger.info(f"Statut vérifié - Temp: {temp}°C, Chauffage: {heating_state}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du statut: {e}")
            self.record_error(e)
            return False
