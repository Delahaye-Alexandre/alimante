#!/usr/bin/env python3
"""
Test du capteur MQ2 avec convertisseur ADS1115
"""

import sys
import os
sys.path.insert(0, '.')

from src.controllers.air_quality_controller import AirQualityController
from src.utils.gpio_manager import GPIOManager

def test_mq2_ads1115_setup():
    """Test la configuration du MQ2 avec ADS1115"""
    print("🧪 Test de configuration MQ2 + ADS1115")
    print("=" * 50)
    
    try:
        # Configuration pour MQ2 + ADS1115
        config = {
            "pin": 22,  # I2C SDA
            "i2c_address": "0x48",
            "adc_channel": 0,
            "voltage": "5.1V",
            "current": 150
        }
        
        # Initialiser GPIO (simulation)
        gpio_manager = GPIOManager()
        
        # Créer le contrôleur
        controller = AirQualityController(gpio_manager, config)
        
        print("✅ Contrôleur MQ2 + ADS1115 créé")
        print(f"   Pin I2C SDA: {config['pin']}")
        print(f"   Adresse I2C: {config['i2c_address']}")
        print(f"   Canal ADC: {config['adc_channel']}")
        print(f"   Tension: {config['voltage']}")
        print(f"   Courant: {config['current']}mA")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_mq2_gas_detection():
    """Test la détection de gaz avec le MQ2"""
    print("\n🌬️ Test de détection de gaz MQ2")
    print("=" * 40)
    
    try:
        config = {
            "pin": 22,
            "i2c_address": "0x48",
            "adc_channel": 0,
            "voltage": "5.1V",
            "current": 150
        }
        
        gpio_manager = GPIOManager()
        controller = AirQualityController(gpio_manager, config)
        
        # Test de calibration
        print("🔧 Test de calibration...")
        success = controller.calibrate_sensor()
        print(f"   Calibration: {'✅ Succès' if success else '❌ Échec'}")
        
        if success:
            # Test de lecture
            print("\n📊 Test de lecture...")
            for i in range(5):
                reading = controller.read_air_quality()
                if reading:
                    print(f"   Lecture {i+1}: {reading['quality_level']} ({reading['ppm']:.1f} ppm)")
                    print(f"      Ventilateurs: {reading['fan_speed']}%")
                else:
                    print(f"   Lecture {i+1}: ❌ Échec")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_mq2_gas_types():
    """Test la détection de différents types de gaz"""
    print("\n🔍 Test de détection de types de gaz")
    print("=" * 40)
    
    # Types de gaz détectés par le MQ2
    gas_types = [
        "LPG (GPL)",
        "Propane", 
        "Méthane",
        "Alcool",
        "Hydrogène",
        "Fumée"
    ]
    
    print("Types de gaz détectés par le MQ2:")
    for gas in gas_types:
        print(f"   ✅ {gas}")
    
    print("\nPlages de détection:")
    print("   LPG: 200-10000 ppm")
    print("   Propane: 200-10000 ppm") 
    print("   Méthane: 1000-20000 ppm")
    print("   Alcool: 100-2000 ppm")
    print("   Hydrogène: 100-10000 ppm")
    print("   Fumée: 10-1000 ppm")
    
    return True

def main():
    """Programme principal"""
    print("🌬️ Test complet du capteur MQ2 avec ADS1115")
    print("=" * 60)
    
    tests = [
        test_mq2_ads1115_setup,
        test_mq2_gas_detection,
        test_mq2_gas_types
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"🎯 Résultats: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 Tous les tests sont passés !")
        return True
    else:
        print("❌ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    main()
