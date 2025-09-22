#!/usr/bin/env python3
"""
Test des contrôleurs d'actionneurs Alimante
Vérifie que tous les contrôleurs d'actionneurs fonctionnent correctement
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from controllers.actuators import (
    HeaterController,
    HumidifierController, 
    FanController,
    FeederSASController
)
from controllers.base_controller import ControllerConfig

def test_heater_controller():
    """Test du contrôleur de chauffage"""
    print("🔥 TEST DU CONTRÔLEUR DE CHAUFFAGE")
    print("=" * 50)
    
    try:
        # Configuration
        config = ControllerConfig(
            name="heater_test",
            max_temperature=35.0,
            hysteresis=1.0,
            safety_enabled=True
        )
        
        gpio_config = {'heater_pin': 19}
        
        # Initialiser le contrôleur
        heater = HeaterController(config, gpio_config)
        
        if not heater.initialize():
            print("❌ Échec initialisation contrôleur chauffage")
            return False
        
        print("✅ Contrôleur chauffage initialisé")
        
        # Test de définition de température
        if heater.set_temperature(25.0):
            print("✅ Température définie: 25°C")
        else:
            print("❌ Échec définition température")
            return False
        
        # Test de mise à jour de température
        heater.update_current_temperature(20.0)
        print("✅ Température actuelle mise à jour: 20°C")
        
        # Test de forçage
        if heater.force_on():
            print("✅ Chauffage forcé ON")
        else:
            print("❌ Échec forçage chauffage")
            return False
        
        # Test d'arrêt
        if heater.force_off():
            print("✅ Chauffage forcé OFF")
        else:
            print("❌ Échec arrêt chauffage")
            return False
        
        # Test du statut
        status = heater.get_status()
        print(f"✅ Statut: {status['state']}")
        
        # Nettoyage
        heater.cleanup()
        print("✅ Contrôleur chauffage nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test contrôleur chauffage: {e}")
        return False

def test_humidifier_controller():
    """Test du contrôleur d'humidification"""
    print("\n💧 TEST DU CONTRÔLEUR D'HUMIDIFICATION")
    print("=" * 50)
    
    try:
        # Configuration
        config = ControllerConfig(
            name="humidifier_test",
            max_humidity=95.0,
            hysteresis=5.0,
            min_cycle_time=60,
            max_cycle_duration=300,
            safety_enabled=True
        )
        
        gpio_config = {'humidifier_pin': 5, 'mister_pin': 6}
        
        # Initialiser le contrôleur
        humidifier = HumidifierController(config, gpio_config)
        
        if not humidifier.initialize():
            print("❌ Échec initialisation contrôleur humidification")
            return False
        
        print("✅ Contrôleur humidification initialisé")
        
        # Test de définition d'humidité
        if humidifier.set_humidity(60.0):
            print("✅ Humidité définie: 60%")
        else:
            print("❌ Échec définition humidité")
            return False
        
        # Test de mise à jour d'humidité
        humidifier.update_current_humidity(40.0)
        print("✅ Humidité actuelle mise à jour: 40%")
        
        # Test de forçage
        if humidifier.force_on():
            print("✅ Humidification forcée ON")
        else:
            print("❌ Échec forçage humidification")
            return False
        
        # Test d'arrêt
        if humidifier.force_off():
            print("✅ Humidification forcée OFF")
        else:
            print("❌ Échec arrêt humidification")
            return False
        
        # Test du statut
        status = humidifier.get_status()
        print(f"✅ Statut: {status['state']}")
        
        # Nettoyage
        humidifier.cleanup()
        print("✅ Contrôleur humidification nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test contrôleur humidification: {e}")
        return False

def test_fan_controller():
    """Test du contrôleur de ventilation"""
    print("\n🌪️ TEST DU CONTRÔLEUR DE VENTILATION")
    print("=" * 50)
    
    try:
        # Configuration
        config = ControllerConfig(
            name="fan_test",
            min_speed=20,
            max_speed=100,
            ramp_time=2.0,
            auto_mode=True
        )
        
        gpio_config = {'fan_pin': 12}
        
        # Initialiser le contrôleur
        fan = FanController(config, gpio_config)
        
        if not fan.initialize():
            print("❌ Échec initialisation contrôleur ventilation")
            return False
        
        print("✅ Contrôleur ventilation initialisé")
        
        # Test de définition de vitesse
        if fan.set_speed(50):
            print("✅ Vitesse définie: 50%")
        else:
            print("❌ Échec définition vitesse")
            return False
        
        # Test de mode automatique
        fan.set_auto_mode(True)
        print("✅ Mode automatique activé")
        
        # Test de contrôle basé sur la qualité de l'air
        fan.update_air_quality(75.0)  # Qualité modérée
        print("✅ Contrôle basé sur qualité d'air: 75 AQI")
        
        # Test de forçage
        if fan.force_on(80):
            print("✅ Ventilateur forcé ON à 80%")
        else:
            print("❌ Échec forçage ventilateur")
            return False
        
        # Test d'arrêt
        if fan.force_off():
            print("✅ Ventilateur forcé OFF")
        else:
            print("❌ Échec arrêt ventilateur")
            return False
        
        # Test du statut
        status = fan.get_status()
        print(f"✅ Statut: {status['state']}")
        
        # Nettoyage
        fan.cleanup()
        print("✅ Contrôleur ventilation nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test contrôleur ventilation: {e}")
        return False

def test_feeder_controller():
    """Test du contrôleur de distributeur d'alimentation"""
    print("\n🍽️ TEST DU CONTRÔLEUR DE DISTRIBUTEUR D'ALIMENTATION")
    print("=" * 50)
    
    try:
        # Configuration
        config = ControllerConfig(
            name="feeder_test",
            safety_lock=True,
            max_daily_feeds=3,
            min_feeding_interval=60,  # 1 minute pour le test
            feeding_duration=3.0,    # 3 secondes pour le test
            max_feeding_duration=10.0
        )
        
        gpio_config = {'feeder_servo_pin': 18, 'sas_pin': 20}
        
        # Initialiser le contrôleur
        feeder = FeederSASController(config, gpio_config)
        
        if not feeder.initialize():
            print("❌ Échec initialisation contrôleur distributeur")
            return False
        
        print("✅ Contrôleur distributeur initialisé")
        
        # Test de position
        if feeder.set_position('closed'):
            print("✅ Position fermée définie")
        else:
            print("❌ Échec définition position fermée")
            return False
        
        # Test d'alimentation (simulation)
        if feeder.start_feeding("cricket", 2.0):
            print("✅ Alimentation démarrée: cricket (2.0g)")
            
            # Attendre la fin de l'alimentation
            time.sleep(4)
            
            if feeder.stop_feeding():
                print("✅ Alimentation arrêtée")
            else:
                print("❌ Échec arrêt alimentation")
                return False
        else:
            print("❌ Échec démarrage alimentation")
            return False
        
        # Test du statut
        status = feeder.get_status()
        print(f"✅ Statut: {status['state']}")
        print(f"✅ Alimentations quotidiennes: {status['daily_feeds']}")
        
        # Nettoyage
        feeder.cleanup()
        print("✅ Contrôleur distributeur nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test contrôleur distributeur: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST DES CONTRÔLEURS D'ACTIONNEURS ALIMANTE")
    print("=" * 60)
    
    tests = [
        test_heater_controller,
        test_humidifier_controller,
        test_fan_controller,
        test_feeder_controller
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Ligne vide entre les tests
    
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 30)
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 TOUS LES TESTS RÉUSSIS !")
        print("Les contrôleurs d'actionneurs fonctionnent correctement.")
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

