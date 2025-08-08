#!/usr/bin/env python3
"""
Test simple du capteur DHT22
"""

import time
import board
import adafruit_dht

def test_dht22():
    """Test le capteur DHT22"""
    print("🧪 Test du capteur DHT22")
    print("=" * 30)
    
    try:
        # Initialiser le capteur
        dht = adafruit_dht.DHT22(board.D4)
        print("✅ Capteur DHT22 initialisé sur pin D4")
        
        # Lire plusieurs fois pour vérifier la stabilité
        for i in range(5):
            try:
                temperature = dht.temperature
                humidity = dht.humidity
                
                print(f"Lecture {i+1}:")
                print(f"  🌡️  Température: {temperature:.1f}°C")
                print(f"  💧 Humidité: {humidity:.1f}%")
                print()
                
                time.sleep(2)  # Attendre 2 secondes entre les lectures
                
            except RuntimeError as e:
                print(f"❌ Erreur lecture {i+1}: {e}")
                time.sleep(2)
                
    except Exception as e:
        print(f"❌ Erreur initialisation DHT22: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_dht22()
    exit(0 if success else 1)
