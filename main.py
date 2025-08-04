"""
main.py
Point d'entrée du programme pour la gestion des mantes avec Raspberry Pi.
"""
import logging
import sys
import asyncio
from typing import Dict, Any

# Imports corrects depuis les packages src
from src.utils.config_manager import SystemConfig
from src.utils.gpio_manager import GPIOManager
from src.utils.logging_config import setup_logging
from src.controllers.temperature_controller import TemperatureController
from src.controllers.light_controller import LightController
from src.controllers.humidity_controller import HumidityController
from src.controllers.feeding_controller import FeedingController
from src.utils.select_config import select_config

class SystemInitError(Exception):
    """Custom exception for system initialization errors"""
    pass

def initialize_system(config: SystemConfig) -> Dict[str, Any]:
    """Initialize all system components with GPIO
    
    Returns:
        dict: Dictionary of controller instances
    Raises:
        SystemInitError: If initialization fails
    """
    try:
        # Initialisation GPIO
        gpio_manager = GPIOManager()
        
        if not gpio_manager.initialized:
            raise SystemInitError("Failed to initialize GPIO")
            
        controllers = {
            'temperature': TemperatureController(gpio_manager, config.temperature),
            'humidity': HumidityController(gpio_manager, config.humidity),
            'light': LightController(gpio_manager, config.location),
            'feeding': FeedingController(gpio_manager, config.feeding)
        }
        
        # Validate controllers
        for name, controller in controllers.items():
            if not controller.check_status():
                raise SystemInitError(f"Failed to initialize {name} controller")
                
        return controllers
        
    except Exception as e:
        logging.critical(f"System initialization failed: {str(e)}")
        raise SystemInitError(f"Failed to initialize system: {str(e)}")

async def run_system_loop(controllers: Dict[str, Any]):
    """Boucle principale du système"""
    import time
    
    logging.info("Démarrage de la boucle principale du système")
    
    try:
        while True:
            # Contrôle de la température
            if 'temperature' in controllers:
                controllers['temperature'].control_temperature()
            
            # Contrôle de l'humidité
            if 'humidity' in controllers:
                controllers['humidity'].control_humidity()
            
            # Contrôle de l'éclairage
            if 'light' in controllers:
                controllers['light'].control_lighting()
            
            # Contrôle de l'alimentation
            if 'feeding' in controllers:
                controllers['feeding'].control_feeding()
            
            # Pause entre les cycles
            await asyncio.sleep(30)  # Contrôle toutes les 30 secondes
            
    except KeyboardInterrupt:
        logging.info("Arrêt demandé par l'utilisateur")
    except Exception as e:
        logging.error(f"Erreur dans la boucle principale: {e}")
    finally:
        # Nettoyage
        if 'gpio_manager' in globals():
            gpio_manager.cleanup()

def main():
    """Point d'entrée principal"""
    try:
        setup_logging()
        logging.info("Démarrage du système Alimante")
        
        # Sélection de la configuration
        specific_config_path = select_config()
        if not specific_config_path:
            raise SystemInitError("Configuration non sélectionnée.")
        
        common_config_path = 'config/config.json'
        config = SystemConfig.from_json(common_config_path, specific_config_path)
        
        # Initialisation du système
        controllers = initialize_system(config)
        
        if not controllers:
            raise SystemInitError("Failed to initialize controllers")
            
        logging.info("Système initialisé avec succès")
        
        # Démarrage de la boucle principale
        asyncio.run(run_system_loop(controllers))
        
    except SystemInitError as e:
        logging.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
