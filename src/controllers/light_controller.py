"""
light_controller.py
Module pour la gestion de la lumière en fonction des horaires de coucher de soleil.

Fonctionnalités :
- Activation et désactivation des lumières via l'Arduino.
"""

import logging
from src.utils.utils import get_sunset_time_utc
from datetime import datetime

class LightController:
    """
    Classe pour gérer l'éclairage.
    """
    def __init__(self, serial_manager, location_config):
        """
        Initialise le contrôleur de lumière.

        :param serial_manager: Instance partagée du gestionnaire série.
        :param location_config: Coordonnées du lieu (latitude, longitude).
        """
        self.serial_manager = serial_manager
        self.latitude = location_config['latitude']
        self.longitude = location_config['longitude']

    def control_lighting(self):
        """
        Contrôle les lumières en fonction de l'heure actuelle et de l'heure du coucher de soleil.
        """
        sunset_time = get_sunset_time_utc(self.latitude, self.longitude)
        current_time = datetime.utcnow()

        logging.info(f"Heure actuelle (UTC) : {current_time}")
        logging.info(f"Heure du coucher de soleil (UTC) : {sunset_time}")

        if current_time >= sunset_time:
            self.activate_lights()
        else:
            self.deactivate_lights()

    def activate_lights(self):
        """
        Active les lumières.
        """
        response = self.serial_manager.send_command("LIGHT_ON")
        logging.info("Lumières activées. Réponse Arduino : %s", response)

    def deactivate_lights(self):
        """
        Désactive les lumières.
        """
        response = self.serial_manager.send_command("LIGHT_OFF")
        logging.info("Lumières désactivées. Réponse Arduino : %s", response)
