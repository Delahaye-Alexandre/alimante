"""
Tests unitaires pour le service de configuration GPIO
"""

import unittest
from unittest.mock import patch, mock_open
import json
import sys
import os

# Ajouter le chemin du projet aux chemins Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.gpio_config_service import GPIOConfigService, GPIOPinConfig


class TestGPIOConfigService(unittest.TestCase):
    """Tests pour le service de configuration GPIO"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        # Configuration GPIO de test
        self.test_gpio_config = {
            "gpio_pins": {
                "sensors": {
                    "temp_humidity": {
                        "gpio_pin": 4,
                        "type": "DHT22",
                        "voltage": "3.3V",
                        "current": "5mA",
                        "power_connection": "3v3_power_rail",
                        "description": "Capteur température et humidité DHT22"
                    },
                    "light": {
                        "gpio_pin": 17,
                        "type": "LDR",
                        "voltage": "3.3V",
                        "current": "1mA",
                        "power_connection": "3v3_power_rail",
                        "description": "Capteur de lumière LDR"
                    }
                },
                "actuators": {
                    "heating_relay": {
                        "gpio_pin": 18,
                        "type": "relay",
                        "voltage": "5.1V",
                        "current": "30mA",
                        "power_connection": "5v1_power_rail",
                        "description": "Relais chauffage"
                    },
                    "fan_relay": {
                        "gpio_pin": 25,
                        "type": "relay",
                        "voltage": "5.1V",
                        "current": "30mA",
                        "power_connection": "5v1_power_rail",
                        "description": "Relais ventilateurs"
                    }
                },
                "interface": {
                    "rotary_encoder": {
                        "clk_gpio": 5,
                        "dt_gpio": 6,
                        "sw_gpio": 13,
                        "type": "rotary_encoder",
                        "voltage": "3.3V",
                        "current": "negligible",
                        "power_connection": "3v3_power_rail",
                        "pull_up": True,
                        "description": "Encodeur rotatif"
                    }
                }
            },
            "pin_assignments": {
                "TEMP_HUMIDITY_PIN": 4,
                "LIGHT_SENSOR_PIN": 17,
                "HEATING_RELAY_PIN": 18,
                "FAN_RELAY_PIN": 25,
                "ROTARY_ENCODER_CLK_PIN": 5,
                "ROTARY_ENCODER_DT_PIN": 6,
                "ROTARY_ENCODER_SW_PIN": 13
            }
        }
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_load_gpio_config_success(self, mock_exists, mock_file):
        """Test du chargement réussi de la configuration GPIO"""
        mock_exists.return_value = True
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.test_gpio_config)
        
        service = GPIOConfigService("test_config.json")
        
        # Vérifier que la configuration a été chargée
        self.assertEqual(len(service.sensors_config), 2)
        self.assertEqual(len(service.actuators_config), 2)
        self.assertEqual(len(service.interface_config), 1)
        self.assertEqual(len(service.pin_assignments), 7)
    
    @patch('pathlib.Path.exists')
    def test_load_gpio_config_file_not_found(self, mock_exists):
        """Test de la gestion d'erreur quand le fichier n'existe pas"""
        mock_exists.return_value = False
        
        with self.assertRaises(Exception):
            GPIOConfigService("nonexistent_config.json")
    
    def test_get_sensor_pin(self):
        """Test de la récupération du pin d'un capteur"""
        with patch.object(GPIOConfigService, 'load_gpio_config') as mock_load:
            mock_load.return_value = self.test_gpio_config
            service = GPIOConfigService()
            
            # Simuler le chargement des configurations
            service._extract_sensors_config()
            service._extract_actuators_config()
            service._extract_interface_config()
            service._extract_pin_assignments()
            
            # Tester la récupération des pins
            temp_pin = service.get_sensor_pin('temp_humidity')
            self.assertEqual(temp_pin, 4)
            
            light_pin = service.get_sensor_pin('light')
            self.assertEqual(light_pin, 17)
            
            # Test avec un capteur inexistant
            unknown_pin = service.get_sensor_pin('unknown_sensor')
            self.assertIsNone(unknown_pin)
    
    def test_get_actuator_pin(self):
        """Test de la récupération du pin d'un actionneur"""
        with patch.object(GPIOConfigService, 'load_gpio_config') as mock_load:
            mock_load.return_value = self.test_gpio_config
            service = GPIOConfigService()
            
            # Simuler le chargement des configurations
            service._extract_sensors_config()
            service._extract_actuators_config()
            service._extract_interface_config()
            service._extract_pin_assignments()
            
            # Tester la récupération des pins
            heating_pin = service.get_actuator_pin('heating_relay')
            self.assertEqual(heating_pin, 18)
            
            fan_pin = service.get_actuator_pin('fan_relay')
            self.assertEqual(fan_pin, 25)
    
    def test_get_pin_assignment(self):
        """Test de la récupération des assignations de pins"""
        with patch.object(GPIOConfigService, 'load_gpio_config') as mock_load:
            mock_load.return_value = self.test_gpio_config
            service = GPIOConfigService()
            
            # Simuler le chargement des configurations
            service._extract_pin_assignments()
            
            # Tester la récupération des assignations
            temp_pin = service.get_pin_assignment('TEMP_HUMIDITY_PIN')
            self.assertEqual(temp_pin, 4)
            
            fan_pin = service.get_pin_assignment('FAN_RELAY_PIN')
            self.assertEqual(fan_pin, 25)
    
    def test_get_interface_config(self):
        """Test de la récupération de la configuration d'interface"""
        with patch.object(GPIOConfigService, 'load_gpio_config') as mock_load:
            mock_load.return_value = self.test_gpio_config
            service = GPIOConfigService()
            
            # Simuler le chargement des configurations
            service._extract_interface_config()
            
            # Tester la récupération de la configuration d'interface
            rotary_config = service.get_interface_config('rotary_encoder')
            self.assertIsNotNone(rotary_config)
            self.assertEqual(rotary_config['clk_gpio'], 5)
            self.assertEqual(rotary_config['dt_gpio'], 6)
            self.assertEqual(rotary_config['sw_gpio'], 13)
    
    def test_validate_pin_config(self):
        """Test de la validation de la configuration des pins"""
        with patch.object(GPIOConfigService, 'load_gpio_config') as mock_load:
            mock_load.return_value = self.test_gpio_config
            service = GPIOConfigService()
            
            # Simuler le chargement des configurations
            service._extract_sensors_config()
            service._extract_actuators_config()
            service._extract_interface_config()
            service._extract_pin_assignments()
            
            # Tester la validation des pins
            self.assertTrue(service.validate_pin_config(4))   # Capteur temp/humidité
            self.assertTrue(service.validate_pin_config(18))  # Relais chauffage
            self.assertTrue(service.validate_pin_config(5))   # Encodeur rotatif CLK
            
            # Test avec un pin non configuré
            self.assertFalse(service.validate_pin_config(99))
    
    def test_get_config_summary(self):
        """Test de la récupération du résumé de configuration"""
        with patch.object(GPIOConfigService, 'load_gpio_config') as mock_load:
            mock_load.return_value = self.test_gpio_config
            service = GPIOConfigService()
            
            # Simuler le chargement des configurations
            service._extract_sensors_config()
            service._extract_actuators_config()
            service._extract_interface_config()
            service._extract_pin_assignments()
            
            # Tester le résumé de configuration
            summary = service.get_config_summary()
            
            self.assertEqual(summary['total_sensors'], 2)
            self.assertEqual(summary['total_actuators'], 2)
            self.assertEqual(summary['total_interface_components'], 1)
            self.assertIn('power_rails', summary)
            self.assertIn('communication_protocols', summary)


class TestGPIOPinConfig(unittest.TestCase):
    """Tests pour la classe GPIOPinConfig"""
    
    def test_gpio_pin_config_creation(self):
        """Test de la création d'une configuration de pin GPIO"""
        pin_config = GPIOPinConfig(
            pin=4,
            type="DHT22",
            voltage="3.3V",
            current="5mA",
            power_connection="3v3_power_rail",
            description="Capteur température et humidité",
            mode="input",
            initial_state=None,
            pull_up=True
        )
        
        self.assertEqual(pin_config.pin, 4)
        self.assertEqual(pin_config.type, "DHT22")
        self.assertEqual(pin_config.voltage, "3.3V")
        self.assertEqual(pin_config.current, "5mA")
        self.assertEqual(pin_config.power_connection, "3v3_power_rail")
        self.assertEqual(pin_config.description, "Capteur température et humidité")
        self.assertEqual(pin_config.mode, "input")
        self.assertIsNone(pin_config.initial_state)
        self.assertTrue(pin_config.pull_up)
    
    def test_gpio_pin_config_defaults(self):
        """Test des valeurs par défaut de GPIOPinConfig"""
        pin_config = GPIOPinConfig(
            pin=18,
            type="relay",
            voltage="5.1V",
            current="30mA",
            power_connection="5v1_power_rail",
            description="Relais chauffage"
        )
        
        self.assertEqual(pin_config.mode, "input")  # Valeur par défaut
        self.assertIsNone(pin_config.initial_state)
        self.assertIsNone(pin_config.pull_up)
        self.assertIsNone(pin_config.frequency)
        self.assertIsNone(pin_config.adc_channel)
        self.assertIsNone(pin_config.i2c_address)


if __name__ == '__main__':
    unittest.main()
