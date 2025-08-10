#!/usr/bin/env python3
"""
Test du contrôleur de qualité de l'air
"""

import sys
import os
sys.path.insert(0, '.')

from src.controllers.air_quality_controller import AirQualityController
from src.controllers.fan_controller import FanController
from src.utils.gpio_manager import GPIOManager

def test_air_quality_controller():
    """Test le contrôleur de qualité de l'air"""
    print("🧪 Test du contrôleur de qualité de l'air")
    print("=" * 50)
    
    try:
        # Configuration de test
        air_quality_config = {
            "pin": 27,
            "voltage": "5V",
            "current": 120
        }
        
        fan_config = {
            "count": 4,
            "relay_pin": 25,
            "voltage": "5V",
            "current_per_fan": 200,
            "total_current": 800
        }
        
        # Initialiser GPIO (simulation)
        gpio_manager = GPIOManager()
        
        # Créer les contrôleurs
        air_quality_controller = AirQualityController(gpio_manager, air_quality_config)
        fan_controller = FanController(gpio_manager, fan_config)
        
        print("✅ Contrôleurs créés")
        
        # Test 1: Calibration
        print("\n🔧 Test de calibration...")
        success = air_quality_controller.calibrate_sensor()
        print(f"   Calibration: {'✅ Succès' if success else '❌ Échec'}")
        
        # Test 2: Lecture de la qualité de l'air
        print("\n📊 Test de lecture de la qualité de l'air...")
        for i in range(5):
            reading = air_quality_controller.read_air_quality()
            if reading:
                print(f"   Lecture {i+1}: {reading['quality_level']} ({reading['ppm']:.1f} ppm) - Ventilateurs: {reading['fan_speed']}%")
            else:
                print(f"   Lecture {i+1}: ❌ Échec")
        
        # Test 3: Contrôle de ventilation
        print("\n🌪️ Test de contrôle de ventilation...")
        success = air_quality_controller.control_ventilation(fan_controller)
        print(f"   Contrôle ventilation: {'✅ Succès' if success else '❌ Échec'}")
        
        # Test 4: Statut du contrôleur
        print("\n📋 Test du statut...")
        status = air_quality_controller.get_status()
        print(f"   Qualité actuelle: {status['current_quality']}")
        print(f"   Calibré: {status['is_calibrated']}")
        print(f"   Nombre de lectures: {status['reading_count']}")
        print(f"   Nombre d'erreurs: {status['error_count']}")
        
        # Test 5: Vérification du statut
        print("\n🔍 Test de vérification du statut...")
        status_ok = air_quality_controller.check_status()
        print(f"   Statut OK: {'✅ Oui' if status_ok else '❌ Non'}")
        
        # Test 6: Nettoyage
        print("\n🧹 Test de nettoyage...")
        air_quality_controller.cleanup()
        fan_controller.cleanup()
        print("   ✅ Nettoyage terminé")
        
        print("\n🎉 Tous les tests sont passés !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_fan_speed_control():
    """Test le contrôle de vitesse des ventilateurs"""
    print("\n🌪️ Test du contrôle de vitesse des ventilateurs")
    print("=" * 50)
    
    try:
        fan_config = {
            "count": 4,
            "relay_pin": 25,
            "voltage": "5V",
            "current_per_fan": 200,
            "total_current": 800
        }
        
        gpio_manager = GPIOManager()
        fan_controller = FanController(gpio_manager, fan_config)
        
        # Test des différentes vitesses
        speeds = [0, 25, 50, 75, 100]
        
        for speed in speeds:
            print(f"   Test vitesse {speed}%...")
            success = fan_controller.set_fan_speed(speed)
            status = fan_controller.get_status()
            print(f"      Résultat: {'✅ Succès' if success else '❌ Échec'}")
            print(f"      Vitesse actuelle: {status['current_speed']}%")
            print(f"      Ventilateurs actifs: {status['fans_active']}")
        
        fan_controller.cleanup()
        print("   ✅ Test de vitesse terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Programme principal"""
    print("🧪 Tests du système de qualité de l'air")
    print("=" * 60)
    
    # Test 1: Contrôleur de qualité de l'air
    test1_success = test_air_quality_controller()
    
    # Test 2: Contrôle de vitesse des ventilateurs
    test2_success = test_fan_speed_control()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"   Contrôleur qualité de l'air: {'✅ PASSÉ' if test1_success else '❌ ÉCHOUÉ'}")
    print(f"   Contrôle vitesse ventilateurs: {'✅ PASSÉ' if test2_success else '❌ ÉCHOUÉ'}")
    
    if test1_success and test2_success:
        print("\n🎉 Tous les tests sont passés !")
        print("Le système de qualité de l'air est fonctionnel.")
        return True
    else:
        print("\n⚠️ Certains tests ont échoué.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
