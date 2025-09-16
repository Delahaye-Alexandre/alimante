#!/usr/bin/env python3
"""
Test simple de l'encodeur rotatif
Utilise la configuration JSON
"""

import time
import sys
import os
import json

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import RPi.GPIO as GPIO
    print("✅ Module RPi.GPIO importé avec succès")
except ImportError as e:
    print(f"❌ Erreur import RPi.GPIO: {e}")
    sys.exit(1)

def test_encoder():
    """Test simple de l'encodeur rotatif"""
    try:
        print("🔧 Initialisation de l'encodeur rotatif...")
        
        # Charger la configuration GPIO depuis le fichier JSON
        with open('config/gpio_config.json', 'r', encoding='utf-8') as f:
            gpio_config = json.load(f)
        
        ui_pins = gpio_config.get('gpio_pins', {}).get('ui', {})
        pin_clk = ui_pins.get('encoder_clk', {}).get('pin', 17)
        pin_dt = ui_pins.get('encoder_dt', {}).get('pin', 27)
        pin_sw = ui_pins.get('encoder_sw', {}).get('pin', 22)
        
        print(f"📌 Pins configurées: CLK={pin_clk}, DT={pin_dt}, SW={pin_sw}")
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Configurer les pins d'entrée avec pull-up
        GPIO.setup(pin_clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(pin_dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(pin_sw, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        print("✅ Pins GPIO configurées")
        
        # Variables de suivi
        last_clk_state = GPIO.input(pin_clk)
        last_dt_state = GPIO.input(pin_dt)
        last_sw_state = GPIO.input(pin_sw)
        
        rotation_count = 0
        press_count = 0
        
        print("\n🔄 Test de l'encodeur rotatif...")
        print("   • Tournez l'encodeur pour tester la rotation")
        print("   • Appuyez sur le bouton pour tester la pression")
        print("   • Appuyez sur Ctrl+C pour arrêter")
        print("=" * 50)
        
        try:
            while True:
                # Lire l'état actuel des pins
                clk_state = GPIO.input(pin_clk)
                dt_state = GPIO.input(pin_dt)
                sw_state = GPIO.input(pin_sw)
                
                # Détecter la rotation
                if clk_state != last_clk_state:
                    if dt_state != clk_state:
                        # Rotation dans le sens horaire
                        rotation_count += 1
                        print(f"🔄 Rotation horaire: {rotation_count}")
                    else:
                        # Rotation dans le sens anti-horaire
                        rotation_count -= 1
                        print(f"🔄 Rotation anti-horaire: {rotation_count}")
                    last_clk_state = clk_state
                
                # Détecter la pression du bouton
                if sw_state != last_sw_state:
                    if sw_state == GPIO.LOW:  # Bouton pressé (pull-up, donc LOW = pressé)
                        press_count += 1
                        print(f"🔘 Bouton pressé: {press_count}")
                    last_sw_state = sw_state
                
                # Petite pause pour éviter la surcharge CPU
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n🛑 Test interrompu par l'utilisateur")
        
        print(f"\n📊 Résultats du test:")
        print(f"   • Rotations détectées: {rotation_count}")
        print(f"   • Pressions détectées: {press_count}")
        
        # Nettoyer GPIO
        GPIO.cleanup()
        print("✅ GPIO nettoyé")
        
        print("✅ Test de l'encodeur terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur test encodeur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Test de l'encodeur rotatif Alimante")
    print("=" * 40)
    
    if test_encoder():
        print("🎉 Test réussi!")
    else:
        print("💥 Test échoué!")
        sys.exit(1)
