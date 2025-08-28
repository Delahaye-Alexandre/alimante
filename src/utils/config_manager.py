from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
import os
import logging

@dataclass
class SystemConfig:
    """Configuration système pour Alimante"""
    # Configuration système
    system_info: Dict[str, Any]
    hardware: Dict[str, Any]
    communication: Dict[str, Any]
    location: Dict[str, Any]
    species_profiles: Dict[str, Any]
    system_control: Dict[str, Any]
    safety: Dict[str, Any]
    api: Dict[str, Any]
    logging: Dict[str, Any]
    performance: Dict[str, Any]
    
    # Configuration spécifique à l'espèce (optionnelle)
    species_name: Optional[str] = None
    common_name: Optional[str] = None
    classification: Optional[Dict[str, Any]] = None
    temperature: Optional[Dict[str, float]] = None
    humidity: Optional[Dict[str, float]] = None
    feeding: Optional[Dict[str, Any]] = None
    lighting: Optional[Dict[str, Any]] = None
    lifecycle: Optional[Dict[str, Any]] = None
    enclosure: Optional[Dict[str, Any]] = None
    
    # Configuration GPIO (optionnelle)
    gpio_config: Optional[Dict[str, Any]] = None

    @classmethod
    def from_json(cls, common_config_path: str, specific_config_path: str, gpio_config_path: Optional[str] = None) -> 'SystemConfig':
        """Charge la configuration depuis deux fichiers JSON et optionnellement la config GPIO"""
        if not os.path.exists(common_config_path):
            raise FileNotFoundError(f"Common configuration file not found: {common_config_path}")
        if not os.path.exists(specific_config_path):
            raise FileNotFoundError(f"Specific configuration file not found: {specific_config_path}")
        
        try:
            # Charger la configuration commune
            with open(common_config_path, 'r', encoding='utf-8') as f:
                common_data = json.load(f)
            
            # Charger la configuration spécifique à l'espèce
            with open(specific_config_path, 'r', encoding='utf-8') as f:
                specific_data = json.load(f)
            
            # Charger la configuration GPIO si fournie
            gpio_data = {}
            if gpio_config_path and os.path.exists(gpio_config_path):
                with open(gpio_config_path, 'r', encoding='utf-8') as f:
                    gpio_data = json.load(f)
            
            # Combiner les configurations
            # La configuration spécifique a la priorité sur la commune
            combined_data = {**common_data, **specific_data}
            
            # Extraire les sections principales
            config = cls(
                system_info=combined_data.get('system_info', {}),
                hardware=combined_data.get('hardware', {}),
                communication=combined_data.get('communication', {}),
                location=combined_data.get('location', {}),
                species_profiles=combined_data.get('species_profiles', {}),
                system_control=combined_data.get('system_control', {}),
                safety=combined_data.get('safety', {}),
                api=combined_data.get('api', {}),
                logging=combined_data.get('logging', {}),
                performance=combined_data.get('performance', {}),
                
                # Configuration spécifique à l'espèce (extraire des structures imbriquées)
                species_name=specific_data.get('species_info', {}).get('species_name'),
                common_name=specific_data.get('species_info', {}).get('common_name'),
                classification=specific_data.get('species_info', {}).get('taxonomy'),
                temperature=specific_data.get('environmental_requirements', {}).get('temperature'),
                humidity=specific_data.get('environmental_requirements', {}).get('humidity'),
                feeding=specific_data.get('feeding_requirements'),
                lighting=specific_data.get('environmental_requirements', {}).get('lighting'),
                lifecycle=specific_data.get('lifecycle'),
                enclosure=specific_data.get('enclosure_requirements'),
                
                # Configuration GPIO
                gpio_config=gpio_data
            )
            
            logging.info(f"Configuration chargée: {specific_data.get('species_name', 'Unknown')}")
            return config
            
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            raise
    
    def get_temperature_config(self) -> Dict[str, float]:
        """Retourne la configuration de température"""
        return self.temperature or {}
    
    def get_humidity_config(self) -> Dict[str, float]:
        """Retourne la configuration d'humidité"""
        return self.humidity or {}
    
    def get_feeding_config(self) -> Dict[str, Any]:
        """Retourne la configuration d'alimentation"""
        return self.feeding or {}
    
    def get_lighting_config(self) -> Dict[str, Any]:
        """Retourne la configuration d'éclairage"""
        return self.lighting or {}
    
    def get_location_config(self) -> Dict[str, float]:
        """Retourne la configuration de localisation"""
        return self.location or {}
    
    def get_system_control_config(self) -> Dict[str, Any]:
        """Retourne la configuration de contrôle système"""
        return self.system_control or {}
    
    def get_safety_config(self) -> Dict[str, Any]:
        """Retourne la configuration de sécurité"""
        return self.safety or {}
    
    def get_gpio_config(self) -> Dict[str, Any]:
        """Retourne la configuration GPIO"""
        return self.gpio_config or {}
    
    def get_gpio_pins(self) -> Dict[str, Any]:
        """Retourne la configuration des pins GPIO"""
        gpio_config = self.get_gpio_config()
        return gpio_config.get('gpio_pins', {})
    
    def get_pin_assignments(self) -> Dict[str, int]:
        """Retourne les assignations de pins"""
        gpio_config = self.get_gpio_config()
        return gpio_config.get('pin_assignments', {})
    
    def get_hardware_config(self) -> Dict[str, Any]:
        """Retourne la configuration matérielle"""
        gpio_config = self.get_gpio_config()
        return gpio_config.get('hardware_config', {})
    
    def get_controller_config(self, controller_name: str) -> Dict[str, Any]:
        """Retourne la configuration spécifique à un contrôleur"""
        # Configuration par défaut pour chaque contrôleur
        default_configs = {
            'fan': {
                'count': 4,
                'voltage': '5V',
                'current_per_fan': 200,
                'total_current': 800
            },
            'ultrasonic_mist': {
                'pin': 22,
                'voltage': '5V',
                'current': 50,
                'frequency': 1700000,
                'power_watts': 2.5,
                'pwm_frequency': 1000
            },
            'air_quality': {
                'sensor_type': 'MQ2',
                'adc_channel': 0,
                'calibration_points': []
            },
            'lcd_config': {
                'i2c_address': '0x27',
                'rows': 2,
                'columns': 16
            },
            'camera_config': {
                'type': 'CSI',
                'resolution': '1920x1080',
                'framerate': 30
            },
            'water_level_sensor': {
                'type': 'HC-SR04P',
                'voltage': '3.3V',
                'current': 15,
                'trigger_pin': 17,
                'echo_pin': 18
            },
            'radiator_temp_sensor': {
                'type': 'DS18B20',
                'voltage': '3.3V',
                'current': 1
            },
            'watchdog_config': {
                'watchdog_pin': 18,
                'timeout_seconds': 30,
                'max_cpu_temp': 80.0,
                'max_cpu_usage': 90.0,
                'max_memory_usage': 85.0
            }
        }
        
        # Retourner la configuration par défaut pour le contrôleur demandé
        return default_configs.get(controller_name, {})
    
    def validate(self) -> bool:
        """
        Valide la configuration système
        
        :return: True si la configuration est valide, False sinon
        """
        try:
            # Vérifier les configurations obligatoires
            if not self.temperature:
                logging.warning("Configuration de température manquante")
                return False
            
            if not self.humidity:
                logging.warning("Configuration d'humidité manquante")
                return False
            
            if not self.feeding:
                logging.warning("Configuration d'alimentation manquante")
                return False
            
            # Vérifier les valeurs de température
            temp_config = self.get_temperature_config()
            if not all(key in temp_config for key in ['optimal', 'tolerance', 'min', 'max']):
                logging.warning("Configuration de température incomplète")
                return False
            
            # Vérifier les valeurs d'humidité
            hum_config = self.get_humidity_config()
            if not all(key in hum_config for key in ['optimal', 'tolerance', 'min', 'max']):
                logging.warning("Configuration d'humidité incomplète")
                return False
            
            # Vérifier la configuration d'alimentation
            feed_config = self.get_feeding_config()
            if not all(key in feed_config for key in ['interval_days', 'feed_count', 'prey_type']):
                logging.warning("Configuration d'alimentation incomplète")
                return False
            
            # Vérifier la configuration GPIO
            gpio_config = self.get_gpio_config()
            if not gpio_config:
                logging.warning("Configuration GPIO manquante")
                return False
            
            pin_assignments = self.get_pin_assignments()
            if not pin_assignments:
                logging.warning("Assignations de pins GPIO manquantes")
                return False
            
            logging.info("Configuration validée avec succès")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de la validation de la configuration: {e}")
            return False