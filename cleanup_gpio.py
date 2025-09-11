#!/usr/bin/env python3
"""
Script de nettoyage des pins GPIO
Utilisez ce script si vous avez des erreurs "Device or resource busy"
"""

import RPi.GPIO as GPIO
import time

def cleanup_gpio():
    """Nettoie toutes les pins GPIO"""
    try:
        print("🧹 Nettoyage des pins GPIO...")
        GPIO.cleanup()
        print("✅ Pins GPIO nettoyées")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False

def main():
    print("🔧 NETTOYAGE PINS GPIO")
    print("=" * 30)
    
    # Nettoyage multiple pour être sûr
    for i in range(3):
        print(f"Tentative {i+1}/3...")
        cleanup_gpio()
        time.sleep(1)
    
    print("\n✅ Nettoyage terminé!")
    print("Vous pouvez maintenant relancer votre script principal.")

if __name__ == "__main__":
    main()
