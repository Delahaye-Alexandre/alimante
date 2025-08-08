#!/usr/bin/env python3
"""
Script de test GPIO pour Alimante
Teste tous les pins GPIO utilisés par le système
"""

import RPi.GPIO as GPIO
import time
import sys
from typing import Dict, List

# Configuration des pins (identique à gpio_manager.py)
PIN_ASSIGNMENTS = {
    'TEMP_HUMIDITY_PIN': 4,
    'LIGHT_SENSOR_PIN': 17,
    'HEATING_RELAY_PIN': 18,
    'HUMIDITY_RELAY_PIN': 23,
    'FEEDING_SERVO_PIN': 12,
    'LIGHT_RELAY_PIN': 24,
    'STATUS_LED_PIN': 25
}

def test_gpio_initialization():
    """Teste l'initialisation GPIO"""
    print("🔧 Test d'initialisation GPIO...")
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        print("✅ Initialisation GPIO réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur d'initialisation GPIO: {e}")
        return False

def test_pin_output(pin: int, name: str):
    """Teste un pin en sortie"""
    print(f"🔌 Test du pin {pin} ({name})...")
    try:
        GPIO.setup(pin, GPIO.OUT, initial=False)
        
        # Test ON
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.5)
        state = GPIO.input(pin)
        print(f"   ON: {state}")
        
        # Test OFF
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.5)
        state = GPIO.input(pin)
        print(f"   OFF: {state}")
        
        print(f"✅ Pin {pin} ({name}) fonctionne")
        return True
    except Exception as e:
        print(f"❌ Erreur pin {pin} ({name}): {e}")
        return False

def test_pin_input(pin: int, name: str):
    """Teste un pin en entrée"""
    print(f"📡 Test du pin {pin} ({name}) en entrée...")
    try:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        state = GPIO.input(pin)
        print(f"   État actuel: {state}")
        print(f"✅ Pin {pin} ({name}) en entrée OK")
        return True
    except Exception as e:
        print(f"❌ Erreur pin {pin} ({name}): {e}")
        return False

def test_pwm(pin: int, name: str):
    """Teste un pin en PWM (pour servo)"""
    print(f"🎛️  Test PWM du pin {pin} ({name})...")
    try:
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 50)  # 50Hz pour servo
        pwm.start(0)
        
        # Test différentes positions
        for duty in [2.5, 7.5, 12.5]:  # 0°, 90°, 180°
            pwm.ChangeDutyCycle(duty)
            time.sleep(1)
            print(f"   Duty cycle {duty}%")
        
        pwm.stop()
        print(f"✅ PWM pin {pin} ({name}) fonctionne")
        return True
    except Exception as e:
        print(f"❌ Erreur PWM pin {pin} ({name}): {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Tests GPIO pour Alimante")
    print("=" * 40)
    
    if not test_gpio_initialization():
        print("❌ Impossible d'initialiser GPIO")
        sys.exit(1)
    
    results = {}
    
    # Test des pins de sortie (relais)
    output_pins = {
        'HEATING_RELAY_PIN': 'Relais chauffage',
        'HUMIDITY_RELAY_PIN': 'Relais pulvérisateur',
        'LIGHT_RELAY_PIN': 'Relais éclairage',
        'STATUS_LED_PIN': 'LED statut'
    }
    
    print("\n🔌 Tests des pins de sortie:")
    for pin_name, description in output_pins.items():
        pin = PIN_ASSIGNMENTS[pin_name]
        results[pin_name] = test_pin_output(pin, description)
    
    # Test des pins d'entrée (capteurs)
    input_pins = {
        'TEMP_HUMIDITY_PIN': 'Capteur DHT22',
        'LIGHT_SENSOR_PIN': 'Capteur lumière'
    }
    
    print("\n📡 Tests des pins d'entrée:")
    for pin_name, description in input_pins.items():
        pin = PIN_ASSIGNMENTS[pin_name]
        results[pin_name] = test_pin_input(pin, description)
    
    # Test PWM (servo)
    print("\n🎛️  Test PWM (servo):")
    servo_pin = PIN_ASSIGNMENTS['FEEDING_SERVO_PIN']
    results['FEEDING_SERVO_PIN'] = test_pwm(servo_pin, 'Servo alimentation')
    
    # Résumé
    print("\n📊 Résumé des tests:")
    print("=" * 40)
    
    success_count = 0
    total_count = len(results)
    
    for pin_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {pin_name}: {PIN_ASSIGNMENTS[pin_name]}")
        if success:
            success_count += 1
    
    print(f"\n📈 Résultat: {success_count}/{total_count} pins fonctionnels")
    
    if success_count == total_count:
        print("🎉 Tous les tests GPIO sont réussis !")
        print("🚀 Le système Alimante est prêt à fonctionner.")
    else:
        print("⚠️  Certains pins ont des problèmes.")
        print("🔧 Vérifiez les connexions et les permissions GPIO.")
    
    # Nettoyage
    GPIO.cleanup()
    print("\n🧹 GPIO nettoyé")

if __name__ == "__main__":
    main() 