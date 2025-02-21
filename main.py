"""
main.py
Point d'entrée du programme pour la gestion des mantes feuilles.
"""
import logging
import sys

# Imports corrects depuis les packages src
from src.utils.config_manager import SystemConfig
from src.utils.serial_manager import SerialManager
from src.utils.logging_config import setup_logging
from src.controllers.temperature_controller import TemperatureController
from src.controllers.light_controller import LightController
from src.controllers.humidity_controller import HumidityController
from src.controllers.feeding_controller import FeedingController

class SystemInitError(Exception):
    """Custom exception for system initialization errors"""
    pass

def initialize_system(config: SystemConfig) -> dict:
    """Initialize all system components with error handling
    
    Returns:
        dict: Dictionary of controller instances
    Raises:
        SystemInitError: If initialization fails
    """
    try:
        serial_manager = SerialManager(
            config.serial_port, 
            config.baud_rate,
            retry_attempts=3  # Add retry logic
        )
        
        if not serial_manager.is_connected():
            raise SystemInitError("Failed to establish serial connection")
            
        controllers = {
            'temperature': TemperatureController(serial_manager, config.temperature),
            'humidity': HumidityController(serial_manager, config.humidity),
            'light': LightController(serial_manager, config.location),
            'feeding': FeedingController(serial_manager, config.feeding)
        }
        
        # Validate controllers
        for name, controller in controllers.items():
            if not controller.check_status():
                raise SystemInitError(f"Failed to initialize {name} controller")
                
        return controllers
        
    except Exception as e:
        logging.critical(f"System initialization failed: {str(e)}")
        raise SystemInitError(f"Failed to initialize system: {str(e)}")

def main():
    try:
        setup_logging()
        config = SystemConfig.from_json('config/config.json')
        controllers = initialize_system(config)
        
        if not controllers:
            raise SystemInitError("Failed to initialize controllers")
            
        logging.info("System initialized successfully")
        
    except SystemInitError as e:
        logging.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
h