#!/usr/bin/env python3
"""
Test de présence physique des composants Alimante
Vérifie la présence des composants par test de résistance/continuité
"""

import sys
import time
import logging
from pathlib import Path

# Ajouter le répertoire parent au path pour accéder à src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.controllers.drivers import *

def test_physical_components():
    """Test de présence physique des composants"""
    print("🔌 TEST DE PRÉSENCE PHYSIQUE DES COMPOSANTS")
    print("=" * 50)
    
    # Configuration du logging
    logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
    
    print("📋 INSTRUCTIONS POUR L'UTILISATEUR :")
    print("=" * 40)
    print("Ce test vous demande de vérifier manuellement quels composants sont branchés.")
    print("Répondez 'o' pour oui, 'n' pour non, ou '?' si vous n'êtes pas sûr.")
    print()
    
    components = {
        "DHT22 (température/humidité) - Pin 4": "Capteur avec 3 fils (VCC, GND, DATA)",
        "Capteur qualité d'air - Pin 5 + ADC": "Capteur avec 4 fils (VCC, GND, A0, D0)",
        "Capteur niveau d'eau Tenflyer - Pin 21": "Capteur avec 3 fils (VCC, GND, SIG)",
        "LED/ventilateur PWM - Pin 12": "LED ou ventilateur connecté",
        "Relais chauffage - Pin 19": "Relais avec charge (résistance chauffante)",
        "Relais humidificateur - Pin 5": "Relais avec charge (humidificateur)",
        "Servo distributeur - Pin 18": "Servo-moteur avec bras mécanique",
        "Brumisateur - Pin 5": "Relais pour brumisateur/humidificateur",
        "Écran ST7735 - Pins 25,24 + SPI": "Écran TFT avec 7 fils",
        "Encodeur rotatif - Pins 17,27,22": "Encodeur avec bouton intégré"
    }
    
    connected = []
    disconnected = []
    unsure = []
    
    for component, description in components.items():
        print(f"\n🔍 {component}")
        print(f"   Description: {description}")
        
        while True:
            response = input("   Branché ? (o/n/?): ").lower().strip()
            if response in ['o', 'oui', 'y', 'yes']:
                connected.append(component)
                break
            elif response in ['n', 'non', 'no']:
                disconnected.append(component)
                break
            elif response in ['?', 's', 'sure']:
                unsure.append(component)
                break
            else:
                print("   Réponse invalide. Utilisez 'o', 'n', ou '?'")
    
    # Résumé
    print("\n📊 RÉSUMÉ DE PRÉSENCE PHYSIQUE")
    print("=" * 35)
    
    print(f"✅ Composants branchés ({len(connected)}):")
    for comp in connected:
        print(f"   • {comp}")
    
    if unsure:
        print(f"\n❓ Composants incertains ({len(unsure)}):")
        for comp in unsure:
            print(f"   • {comp}")
    
    print(f"\n❌ Composants non branchés ({len(disconnected)}):")
    for comp in disconnected:
        print(f"   • {comp}")
    
    total = len(components)
    connected_count = len(connected)
    print(f"\n📈 Taux de branchement: {connected_count}/{total} ({connected_count/total*100:.1f}%)")
    
    # Test fonctionnel des composants branchés
    if connected:
        print(f"\n🔧 TEST FONCTIONNEL DES COMPOSANTS BRANCHÉS")
        print("=" * 45)
        
        for component in connected:
            if "DHT22" in component:
                test_dht22_functional()
            elif "qualité d'air" in component:
                test_air_quality_functional()
            elif "niveau d'eau" in component:
                test_water_sensor_functional()
            elif "PWM" in component:
                test_pwm_functional()
            elif "Relais" in component:
                test_relay_functional()
            elif "Servo" in component:
                test_servo_functional()
            elif "Brumisateur" in component:
                test_brumisateur_functional()
            elif "ST7735" in component:
                test_st7735_functional()
            elif "Encodeur" in component:
                test_encoder_functional()
    
    return len(connected) > 0

def test_dht22_functional():
    """Test fonctionnel DHT22"""
    print("\n🌡️  Test DHT22...")
    try:
        dht22 = DHT22Sensor(DriverConfig("test", enabled=True), gpio_pin=4)
        if dht22.initialize():
            data = dht22.safe_read()
            if data:
                print(f"   ✅ Température: {data.get('temperature', 'N/A')}°C")
                print(f"   ✅ Humidité: {data.get('humidity', 'N/A')}%")
            else:
                print("   ⚠️  Capteur branché mais lecture échouée")
        dht22.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_air_quality_functional():
    """Test fonctionnel capteur qualité d'air"""
    print("\n🌬️  Test capteur qualité d'air...")
    try:
        air_quality = AirQualitySensor(DriverConfig("test", enabled=True), gpio_pin=5, adc_channel=0)
        if air_quality.initialize():
            data = air_quality.safe_read()
            if data:
                print(f"   ✅ AQI: {data.get('aqi', 'N/A')}")
                print(f"   ✅ Niveau: {data.get('level', 'N/A')}")
            else:
                print("   ⚠️  Capteur branché mais lecture échouée")
        air_quality.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_water_sensor_functional():
    """Test fonctionnel capteur niveau d'eau"""
    print("\n💧 Test capteur niveau d'eau...")
    try:
        water_sensor = TenflyerWaterSensor(DriverConfig("test", enabled=True), gpio_pin=21)
        if water_sensor.initialize():
            data = water_sensor.safe_read()
            if data:
                print(f"   ✅ Niveau: {data.get('percentage', 'N/A')}%")
            else:
                print("   ⚠️  Capteur branché mais lecture échouée")
        water_sensor.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_pwm_functional():
    """Test fonctionnel PWM"""
    print("\n⚡ Test PWM...")
    try:
        pwm = PWMDriver(DriverConfig("test", enabled=True), gpio_pin=12, frequency=1000)
        if pwm.initialize():
            print("   ✅ PWM initialisé - LED/ventilateur devrait s'allumer")
            pwm.safe_write({"duty_cycle": 50})
            time.sleep(1)
            pwm.safe_write({"duty_cycle": 0})
            print("   ✅ Test PWM terminé")
        pwm.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_relay_functional():
    """Test fonctionnel relais"""
    print("\n🔌 Test relais...")
    try:
        relay = RelayDriver(DriverConfig("test", enabled=True), gpio_pin=19)
        if relay.initialize():
            print("   ✅ Relais initialisé - charge devrait s'activer")
            relay.turn_on()
            time.sleep(1)
            relay.turn_off()
            print("   ✅ Test relais terminé")
        relay.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_servo_functional():
    """Test fonctionnel servo - VERSION SÉCURISÉE"""
    print("\n🎛️  Test servo (SÉCURISÉ)...")
    try:
        servo = ServoDriver(DriverConfig("test", enabled=True), gpio_pin=18)
        if servo.initialize():
            print("   ⚠️  ATTENTION: Mouvements très limités pour la sécurité")
            print("   • Plage de mouvement: ±5° autour de 90°")
            
            # Définir des limites très restrictives
            servo.set_limits(85, 95)  # Seulement 10 degrés de mouvement
            
            print("   ✅ Servo initialisé avec limites de sécurité")
            
            # Test de mouvement sécurisé
            print("   🔄 Test mouvement sécurisé...")
            servo.write({"angle": 90, "duration": 0.5})  # Centre
            time.sleep(0.5)
            servo.write({"angle": 92, "duration": 0.5})  # +2°
            time.sleep(0.5)
            servo.write({"angle": 90, "duration": 0.5})  # Retour centre
            time.sleep(0.5)
            servo.write({"angle": 88, "duration": 0.5})  # -2°
            time.sleep(0.5)
            servo.write({"angle": 90, "duration": 0.5})  # Retour centre
            
            print("   ✅ Test servo sécurisé terminé")
        servo.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_brumisateur_functional():
    """Test fonctionnel brumisateur (humidificateur)"""
    print("\n💨 Test brumisateur...")
    try:
        import RPi.GPIO as GPIO
        
        # Configuration du brumisateur (pin 5 selon gpio_config.json)
        brumisateur_pin = 5
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(brumisateur_pin, GPIO.OUT)
        
        print("   ⚠️  ATTENTION: Le brumisateur va s'activer pendant 3 secondes")
        print("   ⚠️  Assurez-vous qu'il n'y a pas d'eau à proximité")
        
        # Confirmation de sécurité
        response = input("   Continuer le test du brumisateur? (o/n): ").lower().strip()
        if response not in ['o', 'oui', 'y', 'yes']:
            print("   ❌ Test brumisateur annulé")
            GPIO.setup(brumisateur_pin, GPIO.IN)
            return
        
        print("   ✅ Brumisateur activé - relais ON")
        GPIO.output(brumisateur_pin, GPIO.HIGH)
        
        # Test de 3 secondes
        for i in range(3):
            print(f"   ⏱️  Temps restant: {3-i} secondes...")
            time.sleep(1)
        
        # Désactivation
        GPIO.output(brumisateur_pin, GPIO.LOW)
        print("   ✅ Brumisateur désactivé - relais OFF")
        
        # Vérification de l'état
        current_state = GPIO.input(brumisateur_pin)
        print(f"   • État relais: {'HIGH' if current_state else 'LOW'}")
        print(f"   • Statut: {'✅ Relais fonctionnel' if not current_state else '⚠️  Relais encore actif'}")
        
        # Nettoyage
        GPIO.setup(brumisateur_pin, GPIO.IN)
        print("   ✅ Test brumisateur terminé")
        
    except ImportError:
        print("   ⚠️  RPi.GPIO non disponible - mode simulation")
        print("   ℹ️  Simulation du contrôle du brumisateur:")
        print("   • Activation relais pendant 3 secondes")
        print("   • Vérification de l'état du relais")
        print("   • Désactivation du relais")
        time.sleep(2)
        print("   ✅ Simulation brumisateur terminée")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_st7735_functional():
    """Test fonctionnel ST7735"""
    print("\n📺 Test écran ST7735...")
    try:
        display = ST7735Driver(DriverConfig("test", enabled=True), dc_pin=25, rst_pin=24)
        if display.initialize():
            print("   ✅ Écran initialisé - texte devrait apparaître")
            display.show_message("Test", "Alimante OK", "green")
            time.sleep(2)
            display.clear_screen("black")
            print("   ✅ Test écran terminé")
        display.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_encoder_functional():
    """Test fonctionnel encodeur"""
    print("\n🔄 Test encodeur rotatif...")
    try:
        encoder = RotaryEncoderDriver(DriverConfig("test", enabled=True), clk_pin=17, dt_pin=27, sw_pin=22)
        if encoder.initialize():
            print("   ✅ Encodeur initialisé - tournez et appuyez pour tester")
            print("   ℹ️  Appuyez sur Entrée quand vous avez testé...")
            input()
            print("   ✅ Test encodeur terminé")
        encoder.cleanup()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    success = test_physical_components()
    sys.exit(0 if success else 1)
