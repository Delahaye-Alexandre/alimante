"""
Utilitaire pour charger la configuration GPIO
Évite la duplication de code et centralise la gestion des pins GPIO
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class GPIOConfigLoader:
    """
    Chargeur de configuration GPIO centralisé
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._config_cache = None
    
    def load_config(self) -> Dict[str, Any]:
        """
        Charge la configuration GPIO depuis le fichier JSON
        
        Returns:
            Configuration GPIO complète
        """
        if self._config_cache is not None:
            return self._config_cache
        
        try:
            # Chercher le fichier de configuration
            config_paths = [
                Path.cwd() / 'config' / 'gpio_config.json',
                Path(__file__).parent.parent.parent / 'config' / 'gpio_config.json',
                Path(__file__).parent.parent.parent.parent / 'config' / 'gpio_config.json'
            ]
            
            config_path = None
            for path in config_paths:
                if path.exists():
                    config_path = path
                    break
            
            if config_path:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
                self.logger.info(f"Configuration GPIO chargée depuis {config_path}")
            else:
                self.logger.warning("Fichier gpio_config.json non trouvé, utilisation de la configuration par défaut")
                self._config_cache = self._get_default_config()
            
            return self._config_cache
            
        except Exception as e:
            self.logger.error(f"Erreur chargement configuration GPIO: {e}")
            self._config_cache = self._get_default_config()
            return self._config_cache
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration GPIO par défaut
        
        Returns:
            Configuration par défaut
        """
        return {
            'gpio_pins': {
                'sensors': {
                    'dht22_temperature_humidity': {'pin': 4, 'type': 'digital'},
                    'air_quality': {'pin': 5, 'type': 'analog'},
                    'water_level': {'pin': 21, 'type': 'digital'}
                },
                'actuators': {
                    'feeder_servo': {'pwm_pin': 18, 'type': 'pwm', 'frequency': 50},
                    'heater': {'relay_pin': 19, 'type': 'digital'},
                    'humidifier': {'relay_pin': 5, 'type': 'digital'},
                    'lighting': {'pwm_pin': 12, 'type': 'pwm', 'frequency': 1000},
                    'fan_4': {'pwm_pin': 13, 'type': 'pwm', 'frequency': 1000}
                },
                'ui': {
                    'st7735_mosi': {'pin': 10, 'type': 'spi'},
                    'st7735_sclk': {'pin': 11, 'type': 'spi'},
                    'st7735_dc': {'pin': 25, 'type': 'digital'},
                    'st7735_cs': {'pin': 8, 'type': 'digital'},
                    'st7735_rst': {'pin': 24, 'type': 'digital'},
                    'encoder_clk': {'pin': 17, 'type': 'digital'},
                    'encoder_dt': {'pin': 27, 'type': 'digital'},
                    'encoder_sw': {'pin': 22, 'type': 'digital'}
                },
                'safety': {
                    'status_led': {'pin': 25, 'type': 'digital'}
                }
            },
            'i2c': {'enabled': False, 'frequency': 100000},
            'spi': {'enabled': True, 'frequency': 8000000},
            'pwm': {'enabled': True, 'frequency_range': {'min': 1, 'max': 10000}}
        }
    
    def get_sensor_pin(self, sensor_name: str, pin_type: str = 'pin') -> int:
        """
        Récupère le pin d'un capteur
        
        Args:
            sensor_name: Nom du capteur
            pin_type: Type de pin ('pin', 'pwm_pin', 'relay_pin', etc.)
            
        Returns:
            Numéro de pin
        """
        config = self.load_config()
        sensors = config.get('gpio_pins', {}).get('sensors', {})
        sensor_config = sensors.get(sensor_name, {})
        return sensor_config.get(pin_type, 0)
    
    def get_actuator_pin(self, actuator_name: str, pin_type: str = 'pwm_pin') -> int:
        """
        Récupère le pin d'un actionneur
        
        Args:
            actuator_name: Nom de l'actionneur
            pin_type: Type de pin ('pwm_pin', 'relay_pin', etc.)
            
        Returns:
            Numéro de pin
        """
        config = self.load_config()
        actuators = config.get('gpio_pins', {}).get('actuators', {})
        actuator_config = actuators.get(actuator_name, {})
        return actuator_config.get(pin_type, 0)
    
    def get_ui_pin(self, ui_component: str, pin_type: str = 'pin') -> int:
        """
        Récupère le pin d'un composant UI
        
        Args:
            ui_component: Nom du composant UI
            pin_type: Type de pin ('pin', 'pwm_pin', etc.)
            
        Returns:
            Numéro de pin
        """
        config = self.load_config()
        ui_components = config.get('gpio_pins', {}).get('ui', {})
        component_config = ui_components.get(ui_component, {})
        return component_config.get(pin_type, 0)
    
    def get_actuator_frequency(self, actuator_name: str) -> int:
        """
        Récupère la fréquence d'un actionneur PWM
        
        Args:
            actuator_name: Nom de l'actionneur
            
        Returns:
            Fréquence en Hz
        """
        config = self.load_config()
        actuators = config.get('gpio_pins', {}).get('actuators', {})
        actuator_config = actuators.get(actuator_name, {})
        return actuator_config.get('frequency', 1000)

# Instance globale pour éviter de recharger la configuration
_gpio_config_loader = GPIOConfigLoader()

def load_gpio_config() -> Dict[str, Any]:
    """
    Fonction utilitaire pour charger la configuration GPIO
    
    Returns:
        Configuration GPIO
    """
    return _gpio_config_loader.load_config()

def get_sensor_pin(sensor_name: str, pin_type: str = 'pin') -> int:
    """
    Fonction utilitaire pour récupérer le pin d'un capteur
    
    Args:
        sensor_name: Nom du capteur
        pin_type: Type de pin
        
    Returns:
        Numéro de pin
    """
    return _gpio_config_loader.get_sensor_pin(sensor_name, pin_type)

def get_actuator_pin(actuator_name: str, pin_type: str = 'pwm_pin') -> int:
    """
    Fonction utilitaire pour récupérer le pin d'un actionneur
    
    Args:
        actuator_name: Nom de l'actionneur
        pin_type: Type de pin
        
    Returns:
        Numéro de pin
    """
    return _gpio_config_loader.get_actuator_pin(actuator_name, pin_type)

def get_ui_pin(ui_component: str, pin_type: str = 'pin') -> int:
    """
    Fonction utilitaire pour récupérer le pin d'un composant UI
    
    Args:
        ui_component: Nom du composant UI
        pin_type: Type de pin
        
    Returns:
        Numéro de pin
    """
    return _gpio_config_loader.get_ui_pin(ui_component, pin_type)

def get_actuator_frequency(actuator_name: str) -> int:
    """
    Fonction utilitaire pour récupérer la fréquence d'un actionneur
    
    Args:
        actuator_name: Nom de l'actionneur
        
    Returns:
        Fréquence en Hz
    """
    return _gpio_config_loader.get_actuator_frequency(actuator_name)
