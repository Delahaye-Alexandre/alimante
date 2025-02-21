"""
main.py - Point d'entrée pour la gestion des mantes feuilles.
"""
import logging
import schedule
import time
import sys

from utils.config_manager import SystemConfig
from utils.serial_manager import SerialManager
from utils.logging_config import setup_logging
from controllers.temperature_controller import TemperatureController
from controllers.light_controller import LightController
from controllers.humidity_controller import HumidityController
from controllers.feeding_controller import FeedingController

class SystemInitError(Exception):
    """Exception personnalisée pour l'initialisation du système"""
    pass

def initialize_system(config: SystemConfig) -> dict:
    try:
        serial_manager = SerialManager(
            config.serial_port, 
            config.baud_rate,
            retry_attempts=3
        )
        if not serial_manager.is_connected():
            raise SystemInitError("Impossible d'établir une connexion série")
        controllers = {
            'temperature': TemperatureController(serial_manager, config.temperature),
            'humidity': HumidityController(serial_manager, config.humidity),
            'light': LightController(serial_manager, config.location),
            'feeding': FeedingController(serial_manager, config.feeding)
        }
        for name, controller in controllers.items():
            if not controller.check_status():
                raise SystemInitError(f"Échec de l'initialisation du contrôleur {name}")
        return controllers
    except Exception as e:
        logging.critical(f"Erreur lors de l'initialisation système: {e}")
        raise SystemInitError(f"Échec de l'initialisation: {e}")

def main():
    try:
        setup_logging()
        config = SystemConfig.from_json('config/config.json')
        controllers = initialize_system(config)
        if not controllers:
            raise SystemInitError("Contrôleurs non initialisés correctement")
        logging.info("Système initialisé avec succès")
        # Lancer les tâches ou la boucle principale
        # Par exemple : while True: schedule.run_pending(); time.sleep(1)
    except SystemInitError as e:
        logging.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

from setuptools import setup, find_packages

setup(
    name="mantcare",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'pyserial>=3.5',
        'schedule>=1.1.0',
        'astral>=3.2',  # Si vous utilisez cette lib pour le calcul de la lumière
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'mantcare=mantcare.main:main',
        ],
    },
    author="Votre Nom",
    author_email="votre.email@example.com",
    description="Système de gestion automatisé pour l'élevage de mantes feuilles",
    long_description=open('README.md', encoding='utf-8').read() if open('README.md', encoding='utf-8').read() else "",
    long_description_content_type="text/markdown",
)