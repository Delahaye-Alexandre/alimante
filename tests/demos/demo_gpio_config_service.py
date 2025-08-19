#!/usr/bin/env python3
"""
Démonstration du service de configuration GPIO
Montre comment utiliser le service pour récupérer les pins GPIO
"""

import sys
import os

# Ajouter le chemin du projet aux chemins Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.gpio_config_service import GPIOConfigService


def demo_gpio_config_service():
    """Démonstration du service de configuration GPIO"""
    print("=== Démonstration du Service de Configuration GPIO ===\n")
    
    try:
        # Initialiser le service
        print("1. Initialisation du service de configuration GPIO...")
        gpio_service = GPIOConfigService()
        print("✅ Service initialisé avec succès\n")
        
        # Afficher le résumé de la configuration
        print("2. Résumé de la configuration GPIO:")
        summary = gpio_service.get_config_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
        print()
        
        # Afficher tous les capteurs
        print("3. Configuration des capteurs:")
        sensors = gpio_service.get_all_sensors()
        for sensor_name, sensor_config in sensors.items():
            print(f"   {sensor_name}:")
            print(f"     - Pin: {sensor_config.pin}")
            print(f"     - Type: {sensor_config.type}")
            print(f"     - Tension: {sensor_config.voltage}")
            print(f"     - Courant: {sensor_config.current}")
            print(f"     - Mode: {sensor_config.mode}")
            if sensor_config.adc_channel is not None:
                print(f"     - Canal ADC: {sensor_config.adc_channel}")
            if sensor_config.i2c_address is not None:
                print(f"     - Adresse I2C: {sensor_config.i2c_address}")
            print()
        
        # Afficher tous les actionneurs
        print("4. Configuration des actionneurs:")
        actuators = gpio_service.get_all_actuators()
        for actuator_name, actuator_config in actuators.items():
            print(f"   {actuator_name}:")
            print(f"     - Pin: {actuator_config.pin}")
            print(f"     - Type: {actuator_config.type}")
            print(f"     - Tension: {actuator_config.voltage}")
            print(f"     - Courant: {actuator_config.current}")
            print(f"     - Mode: {actuator_config.mode}")
            if actuator_config.frequency is not None:
                print(f"     - Fréquence: {actuator_config.frequency}Hz")
            print()
        
        # Afficher la configuration des interfaces
        print("5. Configuration des interfaces:")
        interfaces = ['rotary_encoder', 'lcd_st7735']
        for interface_name in interfaces:
            interface_config = gpio_service.get_interface_config(interface_name)
            if interface_config:
                print(f"   {interface_name}:")
                if interface_name == 'rotary_encoder':
                    print(f"     - CLK: GPIO {interface_config.get('clk_gpio')}")
                    print(f"     - DT: GPIO {interface_config.get('dt_gpio')}")
                    print(f"     - SW: GPIO {interface_config.get('sw_gpio')}")
                elif interface_name == 'lcd_st7735':
                    spi_pins = interface_config.get('spi_gpios', {})
                    print(f"     - DC: GPIO {spi_pins.get('dc')}")
                    print(f"     - CS: GPIO {spi_pins.get('cs')}")
                    print(f"     - RST: GPIO {spi_pins.get('rst')}")
                    print(f"     - Backlight: GPIO {interface_config.get('backlight_gpio')}")
                print()
        
        # Exemples d'utilisation pratique
        print("6. Exemples d'utilisation pratique:")
        
        # Récupérer le pin du capteur de température
        temp_pin = gpio_service.get_sensor_pin('temp_humidity')
        if temp_pin is not None:
            print(f"   - Pin capteur température/humidité: GPIO {temp_pin}")
        
        # Récupérer les pins du capteur de niveau d'eau
        water_pins = gpio_service.get_water_level_pins()
        if water_pins is not None:
            print(f"   - Pins capteur niveau d'eau: Trigger GPIO {water_pins['trigger']}, Echo GPIO {water_pins['echo']}")
        
        # Récupérer le pin du relais de chauffage
        heating_pin = gpio_service.get_actuator_pin('heating_relay')
        if heating_pin is not None:
            print(f"   - Pin relais chauffage: GPIO {heating_pin}")
        
        # Récupérer le pin du relais des ventilateurs
        fan_pin = gpio_service.get_actuator_pin('fan_relay')
        if fan_pin is not None:
            print(f"   - Pin relais ventilateurs: GPIO {fan_pin}")
        
        # Récupérer le pin de la bande LED
        led_pin = gpio_service.get_actuator_pin('led_strip')
        if led_pin is not None:
            print(f"   - Pin bande LED: GPIO {led_pin}")
        
        print()
        
        # Validation des pins
        print("7. Validation des pins:")
        test_pins = [4, 18, 25, 24, 99]  # Pins valides et invalides
        for pin in test_pins:
            is_valid = gpio_service.validate_pin_config(pin)
            status = "✅ Valide" if is_valid else "❌ Invalide"
            print(f"   - GPIO {pin}: {status}")
        
        print("\n=== Démonstration terminée ===")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()


def demo_pin_assignments():
    """Démonstration des assignations de pins"""
    print("\n=== Démonstration des Assignations de Pins ===\n")
    
    try:
        gpio_service = GPIOConfigService()
        
        # Liste des assignations de pins courantes
        pin_names = [
            'TEMP_HUMIDITY_PIN',
            'LIGHT_SENSOR_PIN',
            'HEATING_RELAY_PIN',
            'HUMIDITY_RELAY_PIN',
            'FEEDING_SERVO_PIN',
            'FAN_RELAY_PIN',
            'LED_STRIP_PIN',
            'STATUS_LED_PIN',
            'WATER_LEVEL_TRIGGER_PIN',
            'WATER_LEVEL_ECHO_PIN',
            'RADIATOR_TEMP_PIN',
            'MQ2_GAS_PIN'
        ]
        
        print("Assignations de pins:")
        for pin_name in pin_names:
            pin_number = gpio_service.get_pin_assignment(pin_name)
            if pin_number is not None:
                print(f"   {pin_name}: GPIO {pin_number}")
            else:
                print(f"   {pin_name}: Non configuré")
        
        print("\n=== Fin des assignations de pins ===")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration des assignations: {e}")


if __name__ == '__main__':
    print("Démonstration du Service de Configuration GPIO pour Alimante\n")
    
    # Démonstration principale
    demo_gpio_config_service()
    
    # Démonstration des assignations de pins
    demo_pin_assignments()
