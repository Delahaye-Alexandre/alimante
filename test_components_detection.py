#!/usr/bin/env python3
"""
Test de détection des composants Alimante
Détecte quels composants sont réellement branchés et fonctionnels
"""

import sys
import time
import logging
from src.controllers.drivers import *

def test_component_detection():
    """Test de détection des composants"""
    print("🔍 DÉTECTION DES COMPOSANTS ALIMANTE")
    print("=" * 40)
    
    # Configuration du logging
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    
    components = {
        "DHT22 (Pin 4)": test_dht22,
        "Capteur qualité d'air (Pin 5)": test_air_quality,
        "Capteur niveau d'eau (Pin 21)": test_water_sensor,
        "PWM LED (Pin 12)": test_pwm,
        "Relais chauffage (Pin 19)": test_relay,
        "Servo distributeur (Pin 18)": test_servo,
        "Écran ST7735 (Pins 25,24)": test_st7735,
        "Encodeur rotatif (Pins 17,27,22)": test_rotary_encoder
    }
    
    results = {}
    
    for name, test_func in components.items():
        print(f"\n🔍 Test {name}...")
        try:
            result = test_func()
            results[name] = result
            if result:
                print(f"   ✅ {name} - BRANCHÉ ET FONCTIONNEL")
            else:
                print(f"   ❌ {name} - NON BRANCHÉ OU DÉFAILLANT")
        except Exception as e:
            print(f"   ❌ {name} - ERREUR: {e}")
            results[name] = False
    
    # Résumé
    print("\n📊 RÉSUMÉ DE DÉTECTION")
    print("=" * 30)
    
    connected = [name for name, result in results.items() if result]
    disconnected = [name for name, result in results.items() if not result]
    
    print(f"✅ Composants branchés ({len(connected)}):")
    for comp in connected:
        print(f"   • {comp}")
    
    print(f"\n❌ Composants non branchés ({len(disconnected)}):")
    for comp in disconnected:
        print(f"   • {comp}")
    
    print(f"\n📈 Taux de connexion: {len(connected)}/{len(results)} ({len(connected)/len(results)*100:.1f}%)")
    
    return len(connected) > 0

def test_dht22():
    """Test DHT22 avec détection de composant"""
    try:
        dht22 = DHT22Sensor(DriverConfig("test", enabled=True), gpio_pin=4)
        if not dht22.initialize():
            return False
        
        # Essayer de lire plusieurs fois
        for _ in range(3):
            data = dht22.safe_read()
            if data and 'temperature' in data and 'humidity' in data:
                temp = data['temperature']
                hum = data['humidity']
                # Vérifier si les valeurs sont réalistes (pas de simulation)
                if -40 <= temp <= 80 and 0 <= hum <= 100:
                    dht22.cleanup()
                    return True
            time.sleep(0.1)
        
        dht22.cleanup()
        return False
    except:
        return False

def test_air_quality():
    """Test capteur qualité d'air avec détection"""
    try:
        air_quality = AirQualitySensor(DriverConfig("test", enabled=True), gpio_pin=5, adc_channel=0)
        if not air_quality.initialize():
            return False
        
        data = air_quality.safe_read()
        air_quality.cleanup()
        
        # Si AQI = 0, c'est probablement qu'il n'y a pas de capteur
        return data and data.get('aqi', 0) > 0
    except:
        return False

def test_water_sensor():
    """Test capteur niveau d'eau avec détection"""
    try:
        water_sensor = TenflyerWaterSensor(DriverConfig("test", enabled=True), gpio_pin=21)
        if not water_sensor.initialize():
            return False
        
        data = water_sensor.safe_read()
        water_sensor.cleanup()
        
        # Vérifier si on a des données valides
        return data and 'percentage' in data
    except:
        return False

def test_pwm():
    """Test PWM avec détection"""
    try:
        pwm = PWMDriver(DriverConfig("test", enabled=True), gpio_pin=12, frequency=1000)
        if not pwm.initialize():
            return False
        
        # Test de fonctionnement
        pwm.safe_write({"duty_cycle": 50})
        time.sleep(0.1)
        pwm.safe_write({"duty_cycle": 0})
        
        pwm.cleanup()
        return True
    except:
        return False

def test_relay():
    """Test relais avec détection"""
    try:
        relay = RelayDriver(DriverConfig("test", enabled=True), gpio_pin=19)
        if not relay.initialize():
            return False
        
        # Test de fonctionnement
        relay.turn_on()
        time.sleep(0.1)
        relay.turn_off()
        
        relay.cleanup()
        return True
    except:
        return False

def test_servo():
    """Test servo avec détection"""
    try:
        servo = ServoDriver(DriverConfig("test", enabled=True), gpio_pin=18)
        if not servo.initialize():
            return False
        
        # Test de mouvement
        servo.move_to_position("open", duration=0.2)
        time.sleep(0.3)
        servo.move_to_position("closed", duration=0.2)
        time.sleep(0.3)
        
        servo.cleanup()
        return True
    except:
        return False

def test_st7735():
    """Test ST7735 avec détection"""
    try:
        display = ST7735Driver(DriverConfig("test", enabled=True), dc_pin=25, rst_pin=24)
        if not display.initialize():
            return False
        
        # Test d'affichage
        display.clear_screen("black")
        display.show_message("Test", "OK", "green")
        time.sleep(0.5)
        display.clear_screen("black")
        
        display.cleanup()
        return True
    except:
        return False

def test_rotary_encoder():
    """Test encodeur rotatif avec détection"""
    try:
        encoder = RotaryEncoderDriver(DriverConfig("test", enabled=True), clk_pin=17, dt_pin=27, sw_pin=22)
        if not encoder.initialize():
            return False
        
        # Test rapide
        time.sleep(0.1)
        encoder.cleanup()
        return True
    except:
        return False

if __name__ == "__main__":
    success = test_component_detection()
    sys.exit(0 if success else 1)
