"""
humidity_controller.py
Module pour la gestion de l'humidité via un capteur et un pulvérisateur.
"""

import logging

class HumidityController:
    """
    Classe pour gérer l'humidité.
    """
    def __init__(self, serial_manager, config):
        """
        Initialise le contrôleur d'humidité.

        :param serial_manager: Instance partagée du gestionnaire série.
        :param config: Configuration pour les seuils d'humidité.
        """
        self.serial_manager = serial_manager
        self.optimal_humidity = config['optimal']
        self.tolerance = config['tolerance']

    def read_humidity(self):
        """
        Lit l'humidité actuelle depuis le capteur.

        :return: Humidité actuelle (en %) ou None si la lecture échoue.
        """
        response = self.serial_manager.send_command("READ_HUMIDITY")
        try:
            return float(response) if response else None
        except ValueError:
            logging.error("Erreur : la réponse du capteur d'humidité n'est pas valide.")
            return None

    def control_humidity(self):
        """
        Contrôle l'humidité en activant ou désactivant le pulvérisateur.
        """
        current_humidity = self.read_humidity()

        if current_humidity is None:
            logging.warning("Impossible de lire l'humidité.")
            return

        logging.info(f"Humidité actuelle : {current_humidity}%")

        if current_humidity < self.optimal_humidity - self.tolerance:
            self.activate_sprayer()
        elif current_humidity > self.optimal_humidity + self.tolerance:
            self.deactivate_sprayer()
        else:
            logging.info("Humidité dans la plage optimale.")

    def activate_sprayer(self):
        """
        Active le pulvérisateur.
        """
        response = self.serial_manager.send_command("SPRAYER_ON")
        logging.info("Pulvérisateur activé. Réponse Arduino : %s", response)

    def deactivate_sprayer(self):
        """
        Désactive le pulvérisateur.
        """
        response = self.serial_manager.send_command("SPRAYER_OFF")
        logging.info("Pulvérisateur désactivé. Réponse Arduino : %s", response)
