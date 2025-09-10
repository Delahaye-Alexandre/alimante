#!/usr/bin/env python3
"""
Test de pins alternatifs pour CS
Trouve un pin de remplacement pour le CS
"""

import RPi.GPIO as GPIO
import time

def test_pin_for_cs(pin):
    """Test si un pin peut être utilisé pour CS"""
    try:
        GPIO.cleanup()
        time.sleep(0.1)
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(pin, GPIO.LOW)
        
        return True
    except Exception as e:
        print(f"   ❌ GPIO {pin}: {e}")
        return False
    finally:
        GPIO.cleanup()

def find_alternative_cs():
    """Trouve des pins alternatifs pour CS"""
    print("🔍 Recherche de pins alternatifs pour CS...")
    
    # Pins disponibles (éviter ceux déjà utilisés)
    used_pins = [24, 25, 10, 11, 17, 27, 22, 18]  # Pins déjà utilisés
    available_pins = []
    
    for pin in range(1, 28):  # Tester tous les GPIO
        if pin not in used_pins:
            print(f"🔍 Test GPIO {pin}...")
            if test_pin_for_cs(pin):
                available_pins.append(pin)
                print(f"   ✅ GPIO {pin} disponible")
            else:
                print(f"   ❌ GPIO {pin} non disponible")
    
    return available_pins

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔍 RECHERCHE PIN ALTERNATIF POUR CS")
    print("🔧 Trouve un remplacement pour GPIO 8")
    print("=" * 60)
    
    available_pins = find_alternative_cs()
    
    print("\n" + "=" * 60)
    print("📋 PINS DISPONIBLES POUR CS:")
    print("=" * 60)
    
    if available_pins:
        for pin in available_pins:
            print(f"✅ GPIO {pin} - Pin physique {pin_to_physical(pin)}")
        
        print(f"\n🎯 RECOMMANDATIONS:")
        print(f"   • GPIO {available_pins[0]} (Pin {pin_to_physical(available_pins[0])}) - Premier choix")
        if len(available_pins) > 1:
            print(f"   • GPIO {available_pins[1]} (Pin {pin_to_physical(available_pins[1])}) - Deuxième choix")
        
        print(f"\n🔧 Pour utiliser GPIO {available_pins[0]} comme CS:")
        print(f"   1. Modifiez le câblage: CS → Pin {pin_to_physical(available_pins[0])}")
        print(f"   2. Modifiez config_alimante.py: 'CS_PIN': {available_pins[0]}")
    else:
        print("❌ Aucun pin alternatif trouvé")
        print("🔧 Vérifiez le câblage du GPIO 8")

def pin_to_physical(gpio):
    """Convertit GPIO en pin physique"""
    # Mapping simplifié des pins les plus courants
    mapping = {
        2: 3, 3: 5, 4: 7, 5: 29, 6: 31, 7: 26, 8: 24, 9: 21, 10: 19, 11: 23,
        12: 32, 13: 33, 14: 8, 15: 10, 16: 36, 17: 11, 18: 12, 19: 35, 20: 38,
        21: 40, 22: 15, 23: 16, 24: 18, 25: 22, 26: 37, 27: 13
    }
    return mapping.get(gpio, "?")

if __name__ == "__main__":
    main()
