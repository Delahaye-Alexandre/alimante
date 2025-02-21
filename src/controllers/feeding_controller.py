"""
feeding_controller.py
Module pour la gestion de la distribution alimentaire via une trappe.

Fonctionnalités :
- Libération automatique d'un nombre défini de mouches à intervalles réguliers.
- Commande pour l'ouverture et la fermeture d'une trappe via raspberry.
"""

import logging
from datetime import datetime, timedelta

class FeedingController:
    """
    Classe pour gérer la distribution alimentaire.
    """
    def __init__(self, serial_manager, config):
        """
        Initialise le contrôleur d'alimentation.

        :param serial_manager: Instance partagée du gestionnaire série.
        :param config: Configuration pour la gestion de l'alimentation.
        """
        self.serial_manager = serial_manager
        self.feed_interval_days = config['interval_days']
        self.feed_count = config['feed_count']
        self.last_feed_time = None  # Enregistre la dernière alimentation

    def should_feed(self):
        """
        Vérifie si le moment est venu de distribuer la nourriture.

        :return: True si la distribution doit avoir lieu, sinon False.
        """
        current_time = datetime.now()
        if self.last_feed_time is None or (current_time - self.last_feed_time).days >= self.feed_interval_days:
            return True
        return False

    def control_feeding(self):
        """
        Contrôle la distribution alimentaire.
        Si le moment est venu, libère le nombre défini de mouches.
        """
        if self.should_feed():
            logging.info("Moment venu de distribuer la nourriture.")
            self.release_food()
            self.last_feed_time = datetime.now()
        else:
            logging.info("Pas encore le moment de distribuer la nourriture.")

    def release_food(self):
        """
        Libère les mouches en ouvrant la trappe.
        """
        try:
            response_open = self.serial_manager.send_command(f"OPEN_TRAP:{self.feed_count}")
            logging.info(f"Trappe ouverte pour libérer {self.feed_count} mouches. Réponse Raspberry : %s", response_open)

            # Simulation de la fermeture de la trappe après un court délai
            response_close = self.serial_manager.send_command("CLOSE_TRAP")
            logging.info("Trappe fermée. Réponse Raspberry : %s", response_close)

        except Exception as e:
            logging.error(f"Erreur lors de la gestion de la trappe : {e}")
