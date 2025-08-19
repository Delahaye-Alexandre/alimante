"""
Service de configuration GPIO pour Alimante
Gestion centralisée des pins GPIO depuis gpio_config.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode, AlimanteException


@dataclass
class GPIOPinConfig:
    """Configuration d'un pin GPIO"""
    pin: int
    type: str
    voltage: str
    current: str
    power_connection: str
    description: str
    mode: str = "input"  # input, output, pwm, i2c, spi, onewire
    initial_state: Optional[bool] = None
    pull_up: Optional[bool] = None
    frequency: Optional[int] = None
    adc_channel: Optional[int] = None
    i2c_address: Optional[str] = None


class GPIOConfigService:
    """Service de gestion de la configuration GPIO"""
    
    def __init__(self, config_path: str = None):
        self.logger = get_logger("gpio_config_service")
        
        # Déterminer le chemin de configuration par défaut
        if config_path is None:
            # Essayer de trouver le fichier de configuration depuis différents emplacements
            possible_paths = [
                "config/gpio_config.json",
                "../../config/gpio_config.json",
                "../config/gpio_config.json"
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    config_path = path
                    break
            else:
                # Si aucun chemin ne fonctionne, utiliser le chemin par défaut
                config_path = "config/gpio_config.json"
        
        self.config_path = Path(config_path)
        self.gpio_config: Dict[str, Any] = {}
        self.pin_assignments: Dict[str, int] = {}
        self.sensors_config: Dict[str, GPIOPinConfig] = {}
        self.actuators_config: Dict[str, GPIOPinConfig] = {}
        self.interface_config: Dict[str, Any] = {}
        
        # Charger la configuration au démarrage
        self.load_gpio_config()
    
    def load_gpio_config(self) -> Dict[str, Any]:
        """Charge la configuration GPIO depuis le fichier JSON"""
        try:
            if not self.config_path.exists():
                raise create_exception(
                    ErrorCode.CONFIGURATION_INVALID,
                    f"Fichier de configuration GPIO non trouvé: {self.config_path}",
                    {"path": str(self.config_path)}
                )
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.gpio_config = json.load(f)
            
            # Extraire les différentes sections
            self._extract_pin_assignments()
            self._extract_sensors_config()
            self._extract_actuators_config()
            self._extract_interface_config()
            
            self.logger.info("Configuration GPIO chargée avec succès")
            return self.gpio_config
            
        except Exception as e:
            self.logger.exception("Erreur lors du chargement de la configuration GPIO")
            if isinstance(e, AlimanteException):
                raise
            else:
                raise create_exception(
                    ErrorCode.CONFIGURATION_INVALID,
                    "Erreur lors du chargement de la configuration GPIO",
                    {"original_error": str(e)}
                )
    
    def _extract_pin_assignments(self):
        """Extrait les assignations de pins"""
        self.pin_assignments = self.gpio_config.get('pin_assignments', {})
        self.logger.debug(f"Assignations de pins extraites: {len(self.pin_assignments)} pins")
    
    def _extract_sensors_config(self):
        """Extrait la configuration des capteurs"""
        sensors = self.gpio_config.get('gpio_pins', {}).get('sensors', {})
        
        for sensor_name, sensor_config in sensors.items():
            # Gérer les capteurs spéciaux (ultrasonique, etc.)
            if 'trigger_gpio' in sensor_config:
                # Capteur ultrasonique avec trigger et echo
                trigger_pin_config = GPIOPinConfig(
                    pin=sensor_config['trigger_gpio'],
                    type=sensor_config.get('type', 'unknown'),
                    voltage=sensor_config.get('voltage', '3.3V'),
                    current=sensor_config.get('current', '1mA'),
                    power_connection=sensor_config.get('power_connection', '3v3_power_rail'),
                    description=f"{sensor_config.get('description', '')} - Trigger",
                    mode='output',
                    adc_channel=sensor_config.get('adc_channel'),
                    i2c_address=sensor_config.get('i2c_address')
                )
                
                echo_pin_config = GPIOPinConfig(
                    pin=sensor_config['echo_gpio'],
                    type=sensor_config.get('type', 'unknown'),
                    voltage=sensor_config.get('voltage', '3.3V'),
                    current=sensor_config.get('current', '1mA'),
                    power_connection=sensor_config.get('power_connection', '3v3_power_rail'),
                    description=f"{sensor_config.get('description', '')} - Echo",
                    mode='input',
                    adc_channel=sensor_config.get('adc_channel'),
                    i2c_address=sensor_config.get('i2c_address')
                )
                
                # Stocker les deux configurations avec des noms distincts
                self.sensors_config[f"{sensor_name}_trigger"] = trigger_pin_config
                self.sensors_config[f"{sensor_name}_echo"] = echo_pin_config
                
            else:
                # Capteur standard avec un seul pin
                pin_config = GPIOPinConfig(
                    pin=sensor_config.get('gpio_pin', 0),
                    type=sensor_config.get('type', 'unknown'),
                    voltage=sensor_config.get('voltage', '3.3V'),
                    current=sensor_config.get('current', '1mA'),
                    power_connection=sensor_config.get('power_connection', '3v3_power_rail'),
                    description=sensor_config.get('description', ''),
                    mode='input',
                    adc_channel=sensor_config.get('adc_channel'),
                    i2c_address=sensor_config.get('i2c_address')
                )
                
                self.sensors_config[sensor_name] = pin_config
        
        self.logger.debug(f"Configuration des capteurs extraite: {len(self.sensors_config)} capteurs")
    
    def _extract_actuators_config(self):
        """Extrait la configuration des actionneurs"""
        actuators = self.gpio_config.get('gpio_pins', {}).get('actuators', {})
        
        for actuator_name, actuator_config in actuators.items():
            pin_config = GPIOPinConfig(
                pin=actuator_config.get('gpio_pin', 0),
                type=actuator_config.get('type', 'unknown'),
                voltage=actuator_config.get('voltage', '5.1V'),
                current=actuator_config.get('current', '30mA'),
                power_connection=actuator_config.get('power_connection', '5v1_power_rail'),
                description=actuator_config.get('description', ''),
                mode='output',
                initial_state=False,
                frequency=actuator_config.get('frequency')
            )
            
            self.actuators_config[actuator_name] = pin_config
        
        self.logger.debug(f"Configuration des actionneurs extraite: {len(self.actuators_config)} actionneurs")
    
    def _extract_interface_config(self):
        """Extrait la configuration de l'interface"""
        self.interface_config = self.gpio_config.get('gpio_pins', {}).get('interface', {})
        self.logger.debug(f"Configuration de l'interface extraite")
    
    def get_sensor_pin(self, sensor_name: str) -> Optional[int]:
        """Récupère le pin d'un capteur"""
        if sensor_name in self.sensors_config:
            return self.sensors_config[sensor_name].pin
        
        # Gérer les capteurs spéciaux avec des noms spécifiques
        if sensor_name == 'water_level':
            # Pour la compatibilité, retourner le pin trigger par défaut
            trigger_config = self.sensors_config.get('water_level_trigger')
            if trigger_config:
                return trigger_config.pin
        
        return None
    
    def get_water_level_pins(self) -> Optional[Dict[str, int]]:
        """Récupère les pins du capteur de niveau d'eau (trigger et echo)"""
        trigger_config = self.sensors_config.get('water_level_trigger')
        echo_config = self.sensors_config.get('water_level_echo')
        
        if trigger_config and echo_config:
            return {
                'trigger': trigger_config.pin,
                'echo': echo_config.pin
            }
        return None
    
    def get_actuator_pin(self, actuator_name: str) -> Optional[int]:
        """Récupère le pin d'un actionneur"""
        if actuator_name in self.actuators_config:
            return self.actuators_config[actuator_name].pin
        return None
    
    def get_pin_assignment(self, pin_name: str) -> Optional[int]:
        """Récupère l'assignation d'un pin par son nom"""
        return self.pin_assignments.get(pin_name)
    
    def get_sensor_config(self, sensor_name: str) -> Optional[GPIOPinConfig]:
        """Récupère la configuration complète d'un capteur"""
        return self.sensors_config.get(sensor_name)
    
    def get_actuator_config(self, actuator_name: str) -> Optional[GPIOPinConfig]:
        """Récupère la configuration complète d'un actionneur"""
        return self.actuators_config.get(actuator_name)
    
    def get_interface_config(self, interface_name: str) -> Optional[Dict[str, Any]]:
        """Récupère la configuration d'une interface"""
        return self.interface_config.get(interface_name)
    
    def get_all_sensors(self) -> Dict[str, GPIOPinConfig]:
        """Récupère tous les capteurs"""
        return self.sensors_config.copy()
    
    def get_all_actuators(self) -> Dict[str, GPIOPinConfig]:
        """Récupère tous les actionneurs"""
        return self.actuators_config.copy()
    
    def get_power_rail_info(self, rail_name: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un rail d'alimentation"""
        power_connections = self.gpio_config.get('gpio_pins', {}).get('power_connections', {})
        return power_connections.get(rail_name)
    
    def validate_pin_config(self, pin: int) -> bool:
        """Valide qu'un pin est configuré et disponible"""
        # Vérifier que le pin n'est pas utilisé par plusieurs composants
        used_pins = set()
        
        for sensor in self.sensors_config.values():
            used_pins.add(sensor.pin)
        
        for actuator in self.actuators_config.values():
            used_pins.add(actuator.pin)
        
        # Vérifier les pins d'interface
        for interface_name, interface_config in self.interface_config.items():
            if interface_name == 'rotary_encoder':
                used_pins.add(interface_config.get('clk_gpio', 0))
                used_pins.add(interface_config.get('dt_gpio', 0))
                used_pins.add(interface_config.get('sw_gpio', 0))
            elif interface_name == 'lcd_st7735':
                spi_pins = interface_config.get('spi_gpios', {})
                used_pins.add(spi_pins.get('dc', 0))
                used_pins.add(spi_pins.get('cs', 0))
                used_pins.add(spi_pins.get('rst', 0))
                used_pins.add(interface_config.get('backlight_gpio', 0))
        
        return pin in used_pins
    
    def reload_config(self) -> Dict[str, Any]:
        """Recharge la configuration GPIO"""
        self.logger.info("Rechargement de la configuration GPIO")
        return self.load_gpio_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Récupère un résumé de la configuration GPIO"""
        return {
            "total_sensors": len(self.sensors_config),
            "total_actuators": len(self.actuators_config),
            "total_interface_components": len(self.interface_config),
            "power_rails": list(self.gpio_config.get('gpio_pins', {}).get('power_connections', {}).keys()),
            "communication_protocols": list(self.gpio_config.get('communication', {}).keys())
        }
