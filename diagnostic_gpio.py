#!/usr/bin/env python3
"""
Diagnostic GPIO pour DHT22
"""

import RPi.GPIO as GPIO
import time

def test_gpio_pins():
    """Test les pins GPIO"""
    print("🔧 Diagnostic GPIO pour DHT22")
    print("=" * 40)
    
    # Configuration GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Pin DHT22 (GPIO 4)
    DHT_PIN = 4
    
    print(f"📌 Test du pin GPIO {DHT_PIN} (Pin physique 7)")
    
    try:
        # Configurer le pin en sortie pour tester
        GPIO.setup(DHT_PIN, GPIO.OUT)
        print("✅ Pin configuré en sortie")
        
        # Test d'écriture
        GPIO.output(DHT_PIN, GPIO.HIGH)
        print("✅ Pin HIGH")
        time.sleep(0.1)
        
        GPIO.output(DHT_PIN, GPIO.LOW)
        print("✅ Pin LOW")
        time.sleep(0.1)
        
        # Configurer en entrée avec pull-up
        GPIO.setup(DHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print("✅ Pin configuré en entrée avec pull-up")
        
        # Lire l'état
        state = GPIO.input(DHT_PIN)
        print(f"📊 État du pin: {'HIGH' if state else 'LOW'}")
        
        print("\n✅ Test GPIO réussi")
        return True
        
    except Exception as e:
        print(f"❌ Erreur GPIO: {e}")
        return False
        
    finally:
        GPIO.cleanup()

def test_dht22_manual():
    """Test manuel du protocole DHT22"""
    print("\n🔧 Test manuel du protocole DHT22")
    print("=" * 40)
    
    import RPi.GPIO as GPIO
    
    DHT_PIN = 4
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    try:
        # Signal de démarrage
        GPIO.setup(DHT_PIN, GPIO.OUT)
        GPIO.output(DHT_PIN, GPIO.LOW)
        time.sleep(0.02)  # 20ms
        
        # Configurer en entrée
        GPIO.setup(DHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Attendre la réponse du capteur
        time.sleep(0.001)  # 1ms
        
        # Lire les données
        data = []
        for i in range(40):
            # Attendre le front descendant
            while GPIO.input(DHT_PIN) == GPIO.HIGH:
                pass
            
            # Mesurer la durée du pulse
            start = time.time()
            while GPIO.input(DHT_PIN) == GPIO.LOW:
                pass
            end = time.time()
            
            duration = end - start
            data.append(1 if duration > 0.00005 else 0)  # 50μs seuil
        
        print(f"📊 Données brutes: {data[:8]}...")  # Premiers 8 bits
        print("✅ Communication DHT22 détectée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur protocole DHT22: {e}")
        return False
        
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    print("🔍 Diagnostic complet GPIO/DHT22")
    print("=" * 50)
    
    # Test 1: GPIO de base
    gpio_ok = test_gpio_pins()
    
    # Test 2: Protocole DHT22
    dht_ok = test_dht22_manual()
    
    print("\n📊 RÉSUMÉ:")
    print(f"   GPIO: {'✅ OK' if gpio_ok else '❌ ÉCHEC'}")
    print(f"   DHT22: {'✅ OK' if dht_ok else '❌ ÉCHEC'}")
    
    if gpio_ok and dht_ok:
        print("\n🎉 Tous les tests sont passés !")
        print("Le capteur DHT22 devrait fonctionner.")
    else:
        print("\n⚠️ Problèmes détectés:")
        if not gpio_ok:
            print("   - Vérifiez le câblage")
            print("   - Vérifiez les permissions GPIO")
        if not dht_ok:
            print("   - Vérifiez la résistance pull-up")
            print("   - Vérifiez l'alimentation 3.3V")
