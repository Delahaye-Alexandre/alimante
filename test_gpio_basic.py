#!/usr/bin/env python3
"""
Test basique GPIO pour Alimante
Test simple d'un seul pin
"""

import RPi.GPIO as GPIO
import time

def test_basic_gpio():
    """Test basique d'un pin GPIO"""
    print("🔧 Test basique GPIO...")
    
    try:
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Test avec le pin 18 (LED)
        test_pin = 18
        print(f"🔍 Test du pin GPIO {test_pin}...")
        
        # Configuration du pin
        GPIO.setup(test_pin, GPIO.OUT)
        
        # Test de sortie
        print("   État bas...")
        GPIO.output(test_pin, GPIO.LOW)
        time.sleep(1)
        
        print("   État haut...")
        GPIO.output(test_pin, GPIO.HIGH)
        time.sleep(1)
        
        print("   Retour bas...")
        GPIO.output(test_pin, GPIO.LOW)
        time.sleep(1)
        
        print("✅ Test GPIO basique réussi!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test GPIO: {e}")
        return False
    finally:
        GPIO.cleanup()

def test_all_pins():
    """Test de tous les pins d'Alimante"""
    print("🔧 Test de tous les pins Alimante...")
    
    pins = [24, 25, 8, 10, 11]  # Reset, A0/DC, CS, SDA, SCL
    results = []
    
    for pin in pins:
        try:
            print(f"🔍 Test du pin GPIO {pin}...")
            
            # Configuration GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Configuration du pin
            GPIO.setup(pin, GPIO.OUT)
            
            # Test rapide
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(pin, GPIO.LOW)
            
            print(f"✅ Pin GPIO {pin} OK")
            results.append(True)
            
        except Exception as e:
            print(f"❌ Pin GPIO {pin} ERREUR: {e}")
            results.append(False)
        finally:
            GPIO.cleanup()
            time.sleep(0.1)
    
    # Résumé
    print("\n📊 RÉSUMÉ:")
    for i, pin in enumerate(pins):
        status = "✅ OK" if results[i] else "❌ ERREUR"
        print(f"GPIO {pin:2d}: {status}")
    
    success = sum(results)
    total = len(results)
    print(f"\n📈 Résultat: {success}/{total} pins fonctionnels")
    
    return success == total

def main():
    """Fonction principale"""
    print("=" * 50)
    print("🔧 TEST BASIQUE GPIO - ALIMANTE")
    print("=" * 50)
    
    print("\n1. Test basique (pin 18)...")
    if test_basic_gpio():
        print("✅ GPIO fonctionne correctement")
        
        print("\n2. Test de tous les pins Alimante...")
        if test_all_pins():
            print("\n🎉 Tous les pins fonctionnent!")
            print("🚀 Vous pouvez maintenant tester l'écran ST7735")
        else:
            print("\n⚠️  Certains pins ont des problèmes")
            print("🔧 Vérifiez le câblage")
    else:
        print("\n❌ Problème avec GPIO")
        print("🔧 Vérifiez les permissions et le câblage")

if __name__ == "__main__":
    main()
