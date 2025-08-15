"""
main.py
Point d'entrée du programme pour la gestion des mantes avec Raspberry Pi.
"""

import sys
import asyncio
from typing import Dict, Any

# Imports corrects depuis les packages src
from src.utils.config_manager import SystemConfig
from src.utils.gpio_manager import GPIOManager
from src.utils.logging_config import get_logger, log_system_start, log_system_stop, log_controller_action
from src.utils.exceptions import (
    AlimanteException, 
    ErrorCode, 
    create_exception,
    SystemException,
    GPIOException,
    ControllerException
)
from src.controllers.temperature_controller import TemperatureController
from src.controllers.light_controller import LightController
from src.controllers.humidity_controller import HumidityController
from src.controllers.feeding_controller import FeedingController
from src.controllers.air_quality_controller import AirQualityController
from src.controllers.fan_controller import FanController
from src.utils.select_config import select_config

logger = get_logger("main")

def initialize_system(config: SystemConfig) -> Dict[str, Any]:
    """Initialize all system components with GPIO
    
    Returns:
        dict: Dictionary of controller instances
    Raises:
        SystemException: If initialization fails
    """
    try:
        logger.info("🔧 Initialisation du système Alimante")
        
        # Initialisation GPIO
        gpio_manager = GPIOManager()
        
        if not gpio_manager.initialized:
            raise create_exception(
                ErrorCode.GPIO_INIT_FAILED,
                "Impossible d'initialiser le GPIO",
                {"gpio_status": "failed"}
            )
        
        logger.info("✅ GPIO initialisé avec succès")
        
        # Initialisation des contrôleurs
        controllers = {}
        
        # Préparer la configuration complète avec GPIO pour chaque contrôleur
        temp_config = config.temperature.copy()
        temp_config['gpio_config'] = config.gpio_config
        
        humidity_config = config.humidity.copy()
        humidity_config['gpio_config'] = config.gpio_config
        
        light_config = config.location.copy()
        light_config['gpio_config'] = config.gpio_config
        
        feeding_config = config.feeding.copy()
        feeding_config['gpio_config'] = config.gpio_config
        
        # Configuration pour la qualité de l'air et les ventilateurs
        air_quality_config = {
            "pin": config.gpio_config.pin_assignments.get("AIR_QUALITY_PIN", 27),
            "voltage": "5V",
            "current": 120
        }
        air_quality_config['gpio_config'] = config.gpio_config
        
        fan_config = {
            "count": config.gpio_config.hardware_config.get("fan", {}).get("count", 4),
            "relay_pin": config.gpio_config.pin_assignments.get("FAN_RELAY_PIN", 25),
            "voltage": config.gpio_config.hardware_config.get("fan", {}).get("voltage", "5V"),
            "current_per_fan": config.gpio_config.hardware_config.get("fan", {}).get("current_per_fan", "200mA"),
            "total_current": config.gpio_config.hardware_config.get("fan", {}).get("total_current", "800mA")
        }
        fan_config['gpio_config'] = config.gpio_config
        
        # Contrôleur de température
        try:
            controllers['temperature'] = TemperatureController(gpio_manager, temp_config)
            if not controllers['temperature'].check_status():
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    "Échec d'initialisation du contrôleur de température",
                    {"controller": "temperature"}
                )
            logger.info("✅ Contrôleur de température initialisé")
        except Exception as e:
            logger.exception("❌ Erreur initialisation contrôleur température")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                f"Erreur contrôleur température: {str(e)}",
                {"controller": "temperature", "original_error": str(e)}
            )
        
        # Contrôleur d'humidité
        try:
            controllers['humidity'] = HumidityController(gpio_manager, humidity_config)
            if not controllers['humidity'].check_status():
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    "Échec d'initialisation du contrôleur d'humidité",
                    {"controller": "humidity"}
                )
            logger.info("✅ Contrôleur d'humidité initialisé")
        except Exception as e:
            logger.exception("❌ Erreur initialisation contrôleur humidité")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                f"Erreur contrôleur humidité: {str(e)}",
                {"controller": "humidity", "original_error": str(e)}
            )
        
        # Contrôleur d'éclairage
        try:
            controllers['light'] = LightController(gpio_manager, light_config)
            if not controllers['light'].check_status():
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    "Échec d'initialisation du contrôleur d'éclairage",
                    {"controller": "light"}
                )
            logger.info("✅ Contrôleur d'éclairage initialisé")
        except Exception as e:
            logger.exception("❌ Erreur initialisation contrôleur éclairage")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                f"Erreur contrôleur éclairage: {str(e)}",
                {"controller": "light", "original_error": str(e)}
            )
        
        # Contrôleur d'alimentation
        try:
            controllers['feeding'] = FeedingController(gpio_manager, feeding_config)
            if not controllers['feeding'].check_status():
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    "Échec d'initialisation du contrôleur d'alimentation",
                    {"controller": "feeding"}
                )
            logger.info("✅ Contrôleur d'alimentation initialisé")
        except Exception as e:
            logger.exception("❌ Erreur initialisation contrôleur alimentation")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                f"Erreur contrôleur alimentation: {str(e)}",
                {"controller": "feeding", "original_error": str(e)}
            )
        
        # Contrôleur de qualité de l'air
        try:
            controllers['air_quality'] = AirQualityController(gpio_manager, air_quality_config)
            if not controllers['air_quality'].check_status():
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    "Échec d'initialisation du contrôleur de qualité de l'air",
                    {"controller": "air_quality"}
                )
            logger.info("✅ Contrôleur de qualité de l'air initialisé")
        except Exception as e:
            logger.exception("❌ Erreur initialisation contrôleur qualité de l'air")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                f"Erreur contrôleur qualité de l'air: {str(e)}",
                {"controller": "air_quality", "original_error": str(e)}
            )
        
        # Contrôleur de ventilateurs
        try:
            controllers['fan'] = FanController(gpio_manager, fan_config)
            if not controllers['fan'].check_status():
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    "Échec d'initialisation du contrôleur de ventilateurs",
                    {"controller": "fan"}
                )
            logger.info("✅ Contrôleur de ventilateurs initialisé")
        except Exception as e:
            logger.exception("❌ Erreur initialisation contrôleur ventilateurs")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                f"Erreur contrôleur ventilateurs: {str(e)}",
                {"controller": "fan", "original_error": str(e)}
            )
        
        logger.info("🎉 Tous les contrôleurs initialisés avec succès")
        return controllers
        
    except AlimanteException:
        # Re-raise les exceptions Alimante
        raise
    except Exception as e:
        logger.exception("💥 Erreur inattendue lors de l'initialisation")
        raise create_exception(
            ErrorCode.SYSTEM_INIT_FAILED,
            f"Erreur d'initialisation inattendue: {str(e)}",
            {"original_error": str(e)}
        )

async def run_system_loop(controllers: Dict[str, Any]):
    """Boucle principale du système avec gestion d'erreurs robuste"""
    logger.info("🔄 Démarrage de la boucle principale du système")
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            logger.debug(f"🔄 Cycle système #{cycle_count}")
            
            # Contrôle de la température
            if 'temperature' in controllers:
                try:
                    success = controllers['temperature'].control()
                    log_controller_action("temperature", "control", success)
                except Exception as e:
                    logger.error(f"❌ Erreur contrôle température: {e}")
                    log_controller_action("temperature", "control", False, {"error": str(e)})
            
            # Contrôle de l'humidité
            if 'humidity' in controllers:
                try:
                    success = controllers['humidity'].control()
                    log_controller_action("humidity", "control", success)
                except Exception as e:
                    logger.error(f"❌ Erreur contrôle humidité: {e}")
                    log_controller_action("humidity", "control", False, {"error": str(e)})
            
            # Contrôle de l'éclairage
            if 'light' in controllers:
                try:
                    success = controllers['light'].control()
                    log_controller_action("light", "control", success)
                except Exception as e:
                    logger.error(f"❌ Erreur contrôle éclairage: {e}")
                    log_controller_action("light", "control", False, {"error": str(e)})
            
            # Contrôle de l'alimentation
            if 'feeding' in controllers:
                try:
                    success = controllers['feeding'].control()
                    log_controller_action("feeding", "control", success)
                except Exception as e:
                    logger.error(f"❌ Erreur contrôle alimentation: {e}")
                    log_controller_action("feeding", "control", False, {"error": str(e)})
            
            # Contrôle de la qualité de l'air et ventilation
            if 'air_quality' in controllers and 'fan' in controllers:
                try:
                    # Lire la qualité de l'air et ajuster automatiquement les ventilateurs
                    success = controllers['air_quality'].control_ventilation(controllers['fan'])
                    log_controller_action("air_quality", "control_ventilation", success)
                    
                    if success:
                        # Obtenir le statut pour le logging
                        air_status = controllers['air_quality'].get_status()
                        fan_status = controllers['fan'].get_status()
                        logger.debug(f"Qualité air: {air_status.get('current_quality', 'unknown')} - Ventilateurs: {fan_status.get('current_speed', 0)}%")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur contrôle qualité air/ventilation: {e}")
                    log_controller_action("air_quality", "control_ventilation", False, {"error": str(e)})
            
            # Contrôle autonome des ventilateurs (température et humidité)
            elif 'fan' in controllers:
                try:
                    # Obtenir les valeurs actuelles depuis les autres contrôleurs
                    temp_value = None
                    humidity_value = None
                    
                    if 'temperature' in controllers:
                        temp_status = controllers['temperature'].get_status()
                        temp_value = temp_status.get('current_temperature', None)
                    
                    if 'humidity' in controllers:
                        humidity_status = controllers['humidity'].get_status()
                        humidity_value = humidity_status.get('current_humidity', None)
                    
                    # Contrôle automatique des ventilateurs basé sur température/humidité
                    if temp_value is not None or humidity_value is not None:
                        success = controllers['fan'].control_ventilation(
                            temperature=temp_value or 25.0,
                            humidity=humidity_value or 60.0
                        )
                        log_controller_action("fan", "control_ventilation", success)
                        
                        if success:
                            fan_status = controllers['fan'].get_status()
                            logger.debug(f"Ventilateurs: {fan_status.get('fans_active', False)} - Vitesse: {fan_status.get('current_speed', 0)}%")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur contrôle ventilateurs: {e}")
                    log_controller_action("fan", "control_ventilation", False, {"error": str(e)})
            
            # Pause entre les cycles
            await asyncio.sleep(30)  # Contrôle toutes les 30 secondes
            
    except KeyboardInterrupt:
        logger.info("⏹️ Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.exception("💥 Erreur critique dans la boucle principale")
        raise create_exception(
            ErrorCode.SYSTEM_INIT_FAILED,
            f"Erreur dans la boucle principale: {str(e)}",
            {"cycle_count": cycle_count, "original_error": str(e)}
        )
    finally:
        # Nettoyage
        logger.info("🧹 Nettoyage des ressources")
        try:
            # Nettoyer les contrôleurs
            for controller_name, controller in controllers.items():
                try:
                    if hasattr(controller, 'cleanup'):
                        controller.cleanup()
                        logger.debug(f"✅ Contrôleur {controller_name} nettoyé")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur lors du nettoyage du contrôleur {controller_name}: {e}")
            
            # Nettoyer GPIO
            if 'gpio_manager' in globals():
                gpio_manager.cleanup()
                logger.info("✅ GPIO nettoyé")
        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage: {e}")

def main():
    """Point d'entrée principal avec gestion d'erreurs complète"""
    try:
        # Initialisation du logging
        logger = get_logger()
        log_system_start()
        
        logger.info("🚀 Démarrage du système Alimante")
        
        # Sélection de la configuration
        specific_config_path = select_config()
        if not specific_config_path:
            raise create_exception(
                ErrorCode.CONFIGURATION_INVALID,
                "Configuration non sélectionnée"
            )
        
        logger.info(f"📋 Configuration sélectionnée: {specific_config_path}")
        
        # Chargement de la configuration
        common_config_path = 'config/config.json'
        gpio_config_path = 'config/gpio_config.json'
        config = SystemConfig.from_json(common_config_path, specific_config_path, gpio_config_path)
        
        logger.info("✅ Configuration chargée avec succès")
        
        # Initialisation du système
        controllers = initialize_system(config)
        
        if not controllers:
            raise create_exception(
                ErrorCode.SYSTEM_INIT_FAILED,
                "Aucun contrôleur initialisé"
            )
            
        logger.info(f"✅ Système initialisé avec {len(controllers)} contrôleurs")
        
        # Démarrage de la boucle principale
        asyncio.run(run_system_loop(controllers))
        
    except AlimanteException as e:
        logger.critical(f"💥 Erreur système: {e.message}", {
            "error_code": e.error_code.value,
            "error_name": e.error_code.name,
            "context": e.context
        })
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⏹️ Arrêt demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"💥 Erreur inattendue: {str(e)}")
        sys.exit(1)
    finally:
        log_system_stop()
        logger.info("🛑 Arrêt du système Alimante")

if __name__ == "__main__":
    main()
