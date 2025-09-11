#!/usr/bin/env python3
"""
Test complet sur Raspberry Pi pour Alimante
À exécuter sur le Raspberry Pi pour vérifier que tous les drivers fonctionnent
"""

import sys
import time
import logging
from src.controllers.drivers import *

def test_raspberry_pi():
    """Test complet sur Raspberry Pi"""
    print("🍓 TEST COMPLET SUR RASPBERRY PI")
    print("=" * 40)
    
    # Configuration du logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Test des capteurs
    print("\n📊 TEST DES CAPTEURS")
    print("-" * 20)
    
    # DHT22
    print("🌡️  Test DHT22...")
    try:
        dht22 = DHT22Sensor(DriverConfig("dht22", enabled=True), gpio_pin=4)
        if dht22.initialize():
            data = dht22.safe_read()
            if data:
                print(f"   ✅ Température: {data.get('temperature', 'N/A')}°C")
                print(f"   ✅ Humidité: {data.get('humidity', 'N/A')}%")
            else:
                print("   ❌ Échec de lecture")
        else:
            print("   ❌ Échec d'initialisation")
        dht22.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Capteur qualité d'air
    print("\n🌬️  Test capteur qualité d'air...")
    try:
        air_quality = AirQualitySensor(DriverConfig("air_quality", enabled=True), gpio_pin=5, adc_channel=0)
        if air_quality.initialize():
            data = air_quality.safe_read()
            if data:
                print(f"   ✅ AQI: {data.get('aqi', 'N/A')}")
                print(f"   ✅ Niveau: {data.get('level', 'N/A')}")
            else:
                print("   ❌ Échec de lecture")
        else:
            print("   ❌ Échec d'initialisation")
        air_quality.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Capteur niveau d'eau
    print("\n💧 Test capteur niveau d'eau...")
    try:
        water_sensor = TenflyerWaterSensor(DriverConfig("water_sensor", enabled=True), gpio_pin=21)
        if water_sensor.initialize():
            data = water_sensor.safe_read()
            if data:
                print(f"   ✅ Niveau: {data.get('percentage', 'N/A')}%")
                print(f"   ✅ Vide: {water_sensor.is_empty()}")
                print(f"   ✅ Plein: {water_sensor.is_full()}")
            else:
                print("   ❌ Échec de lecture")
        else:
            print("   ❌ Échec d'initialisation")
        water_sensor.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test des actionneurs
    print("\n🔧 TEST DES ACTIONNEURS")
    print("-" * 25)
    
    # PWM
    print("⚡ Test PWM...")
    try:
        pwm = PWMDriver(DriverConfig("pwm", enabled=True), gpio_pin=12, frequency=1000)
        if pwm.initialize():
            pwm.safe_write({"duty_cycle": 50})
            time.sleep(0.1)
            pwm.safe_write({"duty_cycle": 0})
            print("   ✅ PWM fonctionnel")
        else:
            print("   ❌ Échec d'initialisation")
        pwm.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Relais
    print("\n🔌 Test relais...")
    try:
        relay = RelayDriver(DriverConfig("relay", enabled=True), gpio_pin=19)
        if relay.initialize():
            relay.turn_on()
            time.sleep(0.1)
            relay.turn_off()
            print("   ✅ Relais fonctionnel")
        else:
            print("   ❌ Échec d'initialisation")
        relay.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Servo
    print("\n🎛️  Test servo...")
    try:
        servo = ServoDriver(DriverConfig("servo", enabled=True), gpio_pin=18)
        if servo.initialize():
            servo.move_to_position("open", duration=0.5)
            time.sleep(0.6)
            servo.move_to_position("closed", duration=0.5)
            time.sleep(0.6)
            print("   ✅ Servo fonctionnel")
        else:
            print("   ❌ Échec d'initialisation")
        servo.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test des périphériques
    print("\n🖥️  TEST DES PÉRIPHÉRIQUES")
    print("-" * 30)
    
    # ST7735
    print("📺 Test écran ST7735...")
    try:
        display = ST7735Driver(DriverConfig("st7735", enabled=True), dc_pin=25, rst_pin=24)
        if display.initialize():
            display.clear_screen("black")
            display.show_message("Test", "Alimante OK", "green")
            time.sleep(1)
            display.clear_screen("black")
            print("   ✅ Écran ST7735 fonctionnel")
        else:
            print("   ❌ Échec d'initialisation")
        display.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Encodeur rotatif
    print("\n🔄 Test encodeur rotatif...")
    try:
        encoder = RotaryEncoderDriver(DriverConfig("encoder", enabled=True), clk_pin=17, dt_pin=27, sw_pin=22)
        if encoder.initialize():
            print("   ✅ Encodeur rotatif fonctionnel")
            print("   ℹ️  Tournez l'encodeur et appuyez sur le bouton pour tester")
            time.sleep(2)
        else:
            print("   ❌ Échec d'initialisation")
        encoder.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n🎉 TEST TERMINÉ")
    print("=" * 20)
    print("Vérifiez les résultats ci-dessus pour confirmer que tout fonctionne")

if __name__ == "__main__":
    test_raspberry_pi()
