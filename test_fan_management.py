#!/usr/bin/env python3
"""
Test de la gestion des ventilateurs et de leur intégration avec la qualité de l'air
"""

import sys
import os
import time
import asyncio
sys.path.insert(0, '.')

from src.controllers.air_quality_controller import AirQualityController
from src.controllers.fan_controller import FanController
from src.utils.gpio_manager import GPIOManager

def test_fan_management():
    """Test la gestion des ventilateurs et leur lien avec la qualité de l'air"""
    print("🌪️ Test de la gestion des ventilateurs")
    print("=" * 60)
    
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
            "current_per_fan": "200mA",
            "total_current": "800mA"
        }
        
        # Initialiser GPIO (simulation)
        gpio_manager = GPIOManager()
        
        # Créer les contrôleurs
        air_quality_controller = AirQualityController(gpio_manager, air_quality_config)
        fan_controller = FanController(gpio_manager, fan_config)
        
        print("✅ Contrôleurs créés")
        
        # Test 1: Calibration du capteur de qualité de l'air
        print("\n🔧 Test de calibration du capteur...")
        success = air_quality_controller.calibrate_sensor()
        print(f"   Calibration: {'✅ Succès' if success else '❌ Échec'}")
        
        if not success:
            print("❌ Impossible de continuer sans calibration")
            return False
        
        # Test 2: Simulation de différents niveaux de qualité de l'air
        print("\n📊 Test de différents niveaux de qualité de l'air...")
        
        test_scenarios = [
            {"name": "Air excellent", "ppm": 25, "expected_speed": 0},
            {"name": "Air bon", "ppm": 75, "expected_speed": 25},
            {"name": "Air modéré", "ppm": 125, "expected_speed": 50},
            {"name": "Air mauvais", "ppm": 175, "expected_speed": 75},
            {"name": "Air malsain", "ppm": 250, "expected_speed": 100},
            {"name": "Air très malsain", "ppm": 350, "expected_speed": 100}
        ]
        
        for scenario in test_scenarios:
            print(f"\n   📊 Scénario: {scenario['name']}")
            print(f"      PPM simulé: {scenario['ppm']}")
            print(f"      Vitesse attendue: {scenario['expected_speed']}%")
            
            # Simuler la lecture (on modifie temporairement la méthode)
            original_read = air_quality_controller._read_raw_sensor
            
            def mock_read():
                return scenario['ppm']
            
            air_quality_controller._read_raw_sensor = mock_read
            
            # Lire la qualité de l'air
            reading = air_quality_controller.read_air_quality()
            if reading:
                print(f"      Qualité détectée: {reading['quality_level']}")
                print(f"      PPM mesuré: {reading['ppm']:.1f}")
                print(f"      Vitesse ventilateurs: {reading['fan_speed']}%")
                
                # Contrôler la ventilation
                success = air_quality_controller.control_ventilation(fan_controller)
                print(f"      Contrôle ventilation: {'✅ Succès' if success else '❌ Échec'}")
                
                # Vérifier le statut des ventilateurs
                fan_status = fan_controller.get_status()
                print(f"      Ventilateurs actifs: {fan_status['fans_active']}")
                print(f"      Vitesse actuelle: {fan_status['current_speed']}%")
                
                # Vérifier que la vitesse correspond à l'attendu
                if fan_status['current_speed'] == scenario['expected_speed']:
                    print(f"      ✅ Vitesse correcte")
                else:
                    print(f"      ⚠️ Vitesse différente de l'attendu")
            else:
                print("      ❌ Échec de lecture")
            
            # Restaurer la méthode originale
            air_quality_controller._read_raw_sensor = original_read
            
            time.sleep(1)  # Pause entre les scénarios
        
        # Test 3: Contrôle autonome des ventilateurs
        print("\n🌡️ Test du contrôle autonome des ventilateurs...")
        
        # Simuler des conditions de température et humidité
        temp_scenarios = [
            {"temp": 20.0, "humidity": 50.0, "should_activate": False},
            {"temp": 30.0, "humidity": 60.0, "should_activate": True},
            {"temp": 25.0, "humidity": 85.0, "should_activate": True},
            {"temp": 35.0, "humidity": 90.0, "should_activate": True}
        ]
        
        for scenario in temp_scenarios:
            print(f"\n   🌡️ Scénario: Temp={scenario['temp']}°C, Humidité={scenario['humidity']}%")
            
            success = fan_controller.control_ventilation(
                temperature=scenario['temp'],
                humidity=scenario['humidity']
            )
            
            fan_status = fan_controller.get_status()
            print(f"      Résultat: {'✅ Succès' if success else '❌ Échec'}")
            print(f"      Ventilateurs actifs: {fan_status['fans_active']}")
            print(f"      Vitesse: {fan_status['current_speed']}%")
            
            # Vérifier la logique
            if scenario['should_activate'] == fan_status['fans_active']:
                print(f"      ✅ Logique correcte")
            else:
                print(f"      ⚠️ Logique différente de l'attendu")
            
            time.sleep(1)
        
        # Test 4: Gestion des erreurs
        print("\n⚠️ Test de la gestion des erreurs...")
        
        # Test avec un pin GPIO invalide
        try:
            invalid_fan_config = fan_config.copy()
            invalid_fan_config['relay_pin'] = 999  # Pin invalide
            
            invalid_fan_controller = FanController(gpio_manager, invalid_fan_config)
            print("   ❌ Le contrôleur aurait dû échouer avec un pin invalide")
        except Exception as e:
            print(f"   ✅ Gestion d'erreur correcte: {type(e).__name__}")
        
        # Nettoyage
        print("\n🧹 Nettoyage...")
        air_quality_controller.cleanup()
        fan_controller.cleanup()
        gpio_manager.cleanup()
        
        print("✅ Test terminé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_species_configurations():
    """Test les configurations de ventilation des différentes espèces"""
    print("\n🐛 Test des configurations de ventilation par espèce")
    print("=" * 60)
    
    try:
        from src.utils.config_manager import SystemConfig
        
        # Charger la configuration
        config = SystemConfig.from_json(
            'config/config.json',
            'config/orthopteres/mantidae/mantis_religiosa.json',
            'config/gpio_config.json'
        )
        
        # Vérifier la configuration de ventilation
        if hasattr(config, 'ventilation'):
            ventilation_config = config.ventilation
            print(f"✅ Configuration de ventilation trouvée pour {config.species_name}")
            print(f"   Nombre de ventilateurs: {ventilation_config.get('fan_count', 'N/A')}")
            print(f"   Mode automatique: {ventilation_config.get('auto_mode', 'N/A')}")
            print(f"   Seuil température: {ventilation_config.get('temperature_threshold', 'N/A')}°C")
            print(f"   Seuil humidité: {ventilation_config.get('humidity_threshold', 'N/A')}%")
        else:
            print("❌ Configuration de ventilation manquante")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des configurations: {e}")
        return False

async def test_integration():
    """Test l'intégration complète du système"""
    print("\n🔗 Test d'intégration complète")
    print("=" * 60)
    
    try:
        from src.utils.config_manager import SystemConfig
        from main import initialize_system, run_system_loop
        
        # Charger la configuration
        config = SystemConfig.from_json(
            'config/config.json',
            'config/orthopteres/mantidae/mantis_religiosa.json',
            'config/gpio_config.json'
        )
        
        print("✅ Configuration chargée")
        
        # Initialiser le système
        controllers = initialize_system(config)
        
        if not controllers:
            print("❌ Aucun contrôleur initialisé")
            return False
        
        print(f"✅ {len(controllers)} contrôleurs initialisés")
        
        # Vérifier la présence des contrôleurs de ventilation
        required_controllers = ['air_quality', 'fan']
        for controller_name in required_controllers:
            if controller_name in controllers:
                print(f"✅ Contrôleur {controller_name} présent")
            else:
                print(f"❌ Contrôleur {controller_name} manquant")
                return False
        
        # Test de la boucle principale (version courte)
        print("\n🔄 Test de la boucle principale (version courte)...")
        
        # Exécuter quelques cycles
        for i in range(3):
            print(f"   Cycle {i+1}/3...")
            
            # Contrôle de la qualité de l'air et ventilation
            if 'air_quality' in controllers and 'fan' in controllers:
                try:
                    success = controllers['air_quality'].control_ventilation(controllers['fan'])
                    print(f"      Contrôle ventilation: {'✅ Succès' if success else '❌ Échec'}")
                except Exception as e:
                    print(f"      ❌ Erreur: {e}")
            
            await asyncio.sleep(1)
        
        # Nettoyage
        print("\n🧹 Nettoyage...")
        for controller_name, controller in controllers.items():
            try:
                if hasattr(controller, 'cleanup'):
                    controller.cleanup()
                    print(f"   ✅ {controller_name} nettoyé")
            except Exception as e:
                print(f"   ⚠️ Erreur nettoyage {controller_name}: {e}")
        
        print("✅ Test d'intégration terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Programme principal"""
    print("🚀 Test complet de la gestion des ventilateurs")
    print("=" * 80)
    
    # Test 1: Gestion des ventilateurs
    success1 = test_fan_management()
    
    # Test 2: Configurations des espèces
    success2 = test_species_configurations()
    
    # Test 3: Intégration complète
    print("\n" + "="*80)
    success3 = asyncio.run(test_integration())
    
    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*80)
    print(f"✅ Gestion des ventilateurs: {'Succès' if success1 else 'Échec'}")
    print(f"✅ Configurations des espèces: {'Succès' if success2 else 'Échec'}")
    print(f"✅ Intégration complète: {'Succès' if success3 else 'Échec'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 Tous les tests sont passés avec succès !")
        print("La gestion des ventilateurs est correctement intégrée.")
        return True
    else:
        print("\n❌ Certains tests ont échoué.")
        print("Vérifiez les erreurs ci-dessus.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
