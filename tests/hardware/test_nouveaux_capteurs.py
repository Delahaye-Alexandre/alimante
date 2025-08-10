#!/usr/bin/env python3
"""
Test des nouveaux contrôleurs : niveau d'eau et température radiateur
"""

import sys
import os
import time
sys.path.insert(0, '.')

from src.controllers.water_level_controller import WaterLevelController
from src.controllers.radiator_temp_controller import RadiatorTempController
from src.utils.gpio_manager import GPIOManager

def test_water_level_controller():
    """Test le contrôleur de niveau d'eau"""
    print("💧 Test du contrôleur niveau d'eau")
    print("=" * 50)
    
    try:
        # Configuration de test
        water_config = {
            "type": "HC-SR04P",
            "trigger_pin": 20,
            "echo_pin": 21,
            "voltage": "3.3V",
            "current": 15,
            "min_distance": 5,
            "max_distance": 30,
            "reservoir_height": 25,
            "low_level_threshold": 20,
            "critical_level_threshold": 5
        }
        
        # Initialiser GPIO
        gpio_manager = GPIOManager()
        
        # Créer le contrôleur
        water_controller = WaterLevelController(gpio_manager, water_config)
        print("✅ Contrôleur niveau d'eau créé")
        
        # Test 1: Statut du contrôleur
        print("\n📊 Test du statut...")
        status = water_controller.get_status()
        print(f"   Type de capteur: {status['sensor_type']}")
        print(f"   Initialisé: {status['is_initialized']}")
        print(f"   Hauteur réservoir: {status['config']['reservoir_height']}cm")
        print(f"   Seuil critique: {status['critical_threshold']}%")
        print(f"   Erreurs: {status['error_count']}")
        
        # Test 2: Vérification du statut
        print("\n🔍 Test de vérification du statut...")
        status_ok = water_controller.check_status()
        print(f"   Statut OK: {status_ok}")
        
        if not status_ok:
            print("❌ Capteur niveau d'eau non opérationnel")
            return False
        
        # Test 3: Lecture niveau d'eau
        print("\n📏 Test de lecture niveau d'eau...")
        try:
            for i in range(3):
                level_data = water_controller.read_water_level()
                print(f"   Mesure {i+1}:")
                print(f"     Distance: {level_data['distance_cm']}cm")
                print(f"     Niveau: {level_data['water_level_cm']}cm")
                print(f"     Pourcentage: {level_data['level_percentage']}%")
                print(f"     Statut: {level_data['status']}")
                time.sleep(1)
        except Exception as e:
            print(f"   ❌ Erreur lecture: {e}")
        
        # Test 4: Vérification disponibilité eau
        print("\n💧 Test de disponibilité eau...")
        try:
            is_available = water_controller.is_water_available()
            trend = water_controller.get_level_trend()
            print(f"   Eau disponible: {is_available}")
            print(f"   Tendance: {trend}")
        except Exception as e:
            print(f"   ❌ Erreur vérification: {e}")
        
        # Test 5: Nettoyage
        print("\n🧹 Test de nettoyage...")
        water_controller.cleanup()
        print("   ✅ Nettoyage effectué")
        
        print("\n🎉 Tests niveau d'eau terminés!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur dans les tests niveau d'eau: {e}")
        return False

def test_radiator_temp_controller():
    """Test le contrôleur de température radiateur"""
    print("\n🌡️ Test du contrôleur température radiateur")
    print("=" * 50)
    
    try:
        # Configuration de test
        temp_config = {
            "type": "DS18B20",
            "pin": 26,
            "voltage": "3.3V",
            "current": 1,
            "address": "auto",
            "max_safe_temp": 80.0,
            "warning_temp": 70.0,
            "min_temp": -10.0,
            "max_temp": 125.0
        }
        
        # Initialiser GPIO
        gpio_manager = GPIOManager()
        
        # Créer le contrôleur
        temp_controller = RadiatorTempController(gpio_manager, temp_config)
        print("✅ Contrôleur température radiateur créé")
        
        # Test 1: Statut du contrôleur
        print("\n📊 Test du statut...")
        status = temp_controller.get_status()
        print(f"   Type de capteur: {status['sensor_type']}")
        print(f"   Initialisé: {status['is_initialized']}")
        print(f"   Seuil alerte: {status['safety_thresholds']['warning']}°C")
        print(f"   Seuil critique: {status['safety_thresholds']['critical']}°C")
        print(f"   Chemin capteur: {status.get('device_path', 'Non trouvé')}")
        print(f"   Erreurs: {status['error_count']}")
        
        # Test 2: Vérification du statut
        print("\n🔍 Test de vérification du statut...")
        status_ok = temp_controller.check_status()
        print(f"   Statut OK: {status_ok}")
        
        if not status_ok:
            print("❌ Capteur température radiateur non opérationnel")
            return False
        
        # Test 3: Lecture température
        print("\n🌡️ Test de lecture température...")
        try:
            for i in range(3):
                temp_data = temp_controller.read_temperature()
                print(f"   Mesure {i+1}:")
                print(f"     Température: {temp_data['temperature']}°C")
                print(f"     Statut sécurité: {temp_data['safety_status']}")
                print(f"     Seuil alerte: {temp_data['thresholds']['warning']}°C")
                print(f"     Seuil critique: {temp_data['thresholds']['critical']}°C")
                time.sleep(2)
        except Exception as e:
            print(f"   ❌ Erreur lecture: {e}")
        
        # Test 4: Vérification sécurité
        print("\n🛡️ Test de sécurité...")
        try:
            is_safe = temp_controller.is_safe_temperature()
            trend = temp_controller.get_temperature_trend()
            emergency = temp_controller.emergency_check()
            print(f"   Température sûre: {is_safe}")
            print(f"   Tendance: {trend}")
            print(f"   Vérification urgence: {emergency}")
        except Exception as e:
            print(f"   ❌ Erreur vérification: {e}")
        
        # Test 5: Nettoyage
        print("\n🧹 Test de nettoyage...")
        temp_controller.cleanup()
        print("   ✅ Nettoyage effectué")
        
        print("\n🎉 Tests température radiateur terminés!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur dans les tests température radiateur: {e}")
        return False

def test_compatibility():
    """Test de compatibilité des modules"""
    print("🔧 Test de compatibilité des modules...")
    
    # Test module OneWire pour DS18B20
    try:
        import os
        onewire_path = "/sys/bus/w1/devices/"
        if os.path.exists(onewire_path):
            print("   ✅ Bus OneWire disponible")
        else:
            print("   ❌ Bus OneWire non disponible")
            print("      Chargez les modules: sudo modprobe w1-gpio w1-therm")
    except Exception as e:
        print(f"   ❌ Erreur OneWire: {e}")
    
    # Test GPIO
    try:
        import RPi.GPIO as GPIO
        print("   ✅ RPi.GPIO disponible")
    except ImportError:
        print("   ❌ RPi.GPIO non disponible")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Tests des nouveaux capteurs Alimante")
    print("=" * 60)
    
    # Test de compatibilité
    if not test_compatibility():
        print("\n❌ Tests annulés - problèmes de compatibilité")
        sys.exit(1)
    
    # Tests des contrôleurs
    water_success = test_water_level_controller()
    temp_success = test_radiator_temp_controller()
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"💧 Niveau d'eau: {'✅ OK' if water_success else '❌ ÉCHEC'}")
    print(f"🌡️ Température radiateur: {'✅ OK' if temp_success else '❌ ÉCHEC'}")
    
    if water_success and temp_success:
        print("\n🎉 Tous les tests réussis!")
        print("\n📝 Prochaines étapes:")
        print("   1. Vérifier le câblage physique")
        print("   2. Calibrer les capteurs")
        print("   3. Tester l'intégration avec l'API")
        sys.exit(0)
    else:
        print("\n❌ Certains tests ont échoué")
        print("\n🔧 Actions recommandées:")
        print("   1. Vérifier les connexions GPIO")
        print("   2. Charger les modules kernel nécessaires")
        print("   3. Tester les capteurs individuellement")
        sys.exit(1)
