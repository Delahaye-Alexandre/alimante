#!/usr/bin/env python3
"""
Test GPIO simple pour vérifier le pin 4
"""

import RPi.GPIO as GPIO
import time

def test_pin_4():
    """Test le pin 4"""
    print("🔧 Test du pin GPIO 4")
    print("=" * 30)
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    try:
        # Test 1: Configuration en sortie
        print("📌 Test 1: Configuration en sortie")
        GPIO.setup(4, GPIO.OUT)
        print("✅ Pin 4 configuré en sortie")
        
        # Test 2: Écriture HIGH
        GPIO.output(4, GPIO.HIGH)
        print("✅ Pin 4 HIGH")
        time.sleep(0.5)
        
        # Test 3: Écriture LOW
        GPIO.output(4, GPIO.LOW)
        print("✅ Pin 4 LOW")
        time.sleep(0.5)
        
        # Test 4: Configuration en entrée
        print("📌 Test 2: Configuration en entrée")
        GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print("✅ Pin 4 configuré en entrée avec pull-up")
        
        # Test 5: Lecture
        state = GPIO.input(4)
        print(f"📊 État du pin 4: {'HIGH' if state else 'LOW'}")
        
        print("\n✅ Pin GPIO 4 fonctionne correctement")
        return True
        
    except Exception as e:
        print(f"❌ Erreur pin 4: {e}")
        return False
        
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    success = test_pin_4()
    exit(0 if success else 1)
