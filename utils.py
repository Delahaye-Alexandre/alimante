"""
utils.py
Module utilitaire pour la gestion des tâches partagées.

Fonctionnalités :
- Gestion des horaires (calcul du coucher de soleil UTC).
- Envoi et réception de commandes via la connexion série.
- Configuration de logging.
"""

import logging
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime
import serial
import json

# Configuration du logging
logging.basicConfig(
    filename='system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SerialManager:
    """
    Classe unique pour gérer la connexion série avec l'Arduino.
    """
    def __init__(self, port="COM3", baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.connection = None
        self.initialize_connection()

    def initialize_connection(self):
        try:
            self.connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            logging.info(f"Connexion série initialisée sur {self.port} avec un débit de {self.baud_rate} bauds.")
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation de la connexion série : {e}")

    def send_command(self, command):
        try:
            self.connection.write(f"{command}\n".encode())
            response = self.connection.readline().decode().strip()
            return response
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de la commande '{command}': {e}")
            return None

    def close_connection(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            logging.info("Connexion série fermée.")

def get_sunset_time_utc(latitude, longitude):
    """
    Calcule l'heure précise du coucher de soleil en UTC pour une latitude et une longitude données.

    :param latitude: Latitude du lieu (en degrés).
    :param longitude: Longitude du lieu (en degrés).
    :return: Heure du coucher de soleil en UTC (datetime).
    """
    try:
        # Création d'une localisation fictive
        location = LocationInfo(name="Custom Location", region="World", timezone="UTC",
                                latitude=latitude, longitude=longitude)

        # Calcul des informations sur le soleil pour aujourd'hui
        sun_info = sun(location.observer, date=datetime.utcnow().date())
        sunset_time = sun_info['sunset']

        logging.info(f"Calcul du coucher de soleil pour lat={latitude}, lon={longitude}: {sunset_time}")
        return sunset_time
    except Exception as e:
        logging.error(f"Erreur lors du calcul du coucher de soleil : {e}")
        return None

def load_config():
    """
    Charge les paramètres à partir d'un fichier config.json.

    :return: Dictionnaire contenant les paramètres.
    """
    try:
        with open('config.json', 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)
        logging.info("Configuration chargée avec succès.")
        return config
    except json.JSONDecodeError as e:
        logging.error(f"Erreur lors du décodage du fichier de configuration : {e}")
        return {}
    except FileNotFoundError as e:
        logging.error(f"Fichier de configuration non trouvé : {e}")
        return {}
    except Exception as e:
        logging.error(f"Erreur lors du chargement de la configuration : {e}")
        return {}
