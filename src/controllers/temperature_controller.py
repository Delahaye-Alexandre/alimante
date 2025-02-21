"""
temperature_controller.py
Module pour la gestion de la température via un switch relié à une prise.

Fonctionnalités :
- Lecture de la température actuelle depuis un capteur.
- Activation ou désactivation du switch pour maintenir une température optimale.
"""

import logging

class TemperatureController:
    """
    Classe pour gérer la température.
    """
    def __init__(self, serial_manager, config):
        """
        Initialise le contrôleur de température.

        :param serial_manager: Instance partagée du gestionnaire série.
        :param config: Configuration pour les seuils de température.
        """
        self.serial_manager = serial_manager
        self.optimal_temperature = config['optimal']
        self.tolerance = config['tolerance']

    def read_temperature(self):
        """
        Lit la température actuelle depuis le capteur.

        :return: Température actuelle (en °C) ou None si la lecture échoue.
        """
        response = self.serial_manager.send_command("READ_TEMP")
        try:
            return float(response) if response else None
        except ValueError:
            logging.error("Erreur : la réponse du capteur de température n'est pas valide.")
            return None

    def control_temperature(self):
        """
        Contrôle la température en activant ou désactivant le switch.
        """
        current_temperature = self.read_temperature()

        if current_temperature is None:
            logging.warning("Impossible de lire la température.")
            return

        logging.info(f"Température actuelle : {current_temperature}°C")

        if current_temperature < self.optimal_temperature - self.tolerance:
            self.activate_switch()
        elif current_temperature > self.optimal_temperature + self.tolerance:
            self.deactivate_switch()
        else:
            logging.info("Température dans la plage optimale.")

    def activate_switch(self):
        """
        Active le switch pour chauffer.
        """
        response = self.serial_manager.send_command("SWITCH_ON")
        logging.info("Switch activé. Réponse Arduino : %s", response)

    def deactivate_switch(self):
        """
        Désactive le switch pour arrêter le chauffage.
        """
        response = self.serial_manager.send_command("SWITCH_OFF")
        logging.info("Switch désactivé. Réponse Arduino : %s", response)
