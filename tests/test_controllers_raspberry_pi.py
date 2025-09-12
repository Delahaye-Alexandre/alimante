#!/usr/bin/env python3
"""
Test des contrôleurs Alimante sur Raspberry Pi
Valide le fonctionnement avec le matériel réel
"""

import sys
import time
import json
import logging
from pathlib import Path

# Ajouter le répertoire parent au path pour accéder à src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.controllers import MainController, ControllerConfig

def load_config_files():
    """Charge tous les fichiers de configuration"""
    config_dir = Path("config")
    config_files = {}
    
    try:
        # Charger gpio_config.json
        with open(config_dir / "gpio_config.json", "r") as f:
            config_files["gpio_config"] = json.load(f)
        
        # Charger safety_limits.json
        with open(config_dir / "safety_limits.json", "r") as f:
            config_files["safety_limits"] = json.load(f)
        
        # Charger les politiques
        policies = {}
        policies_dir = config_dir / "policies"
        for policy_file in policies_dir.glob("*.json"):
            with open(policy_file, "r") as f:
                policies[policy_file.stem] = json.load(f)
        config_files["policies"] = policies
        
        # Charger terrarium_default.json
        with open(config_dir / "terrariums" / "terrarium_default.json", "r") as f:
            config_files["terrarium_config"] = json.load(f)
        
        return config_files
        
    except Exception as e:
        print(f"❌ Erreur chargement configuration: {e}")
        return None

def test_controllers_with_hardware():
    """Test des contrôleurs avec le matériel réel"""
    print("🍓 TEST DES CONTRÔLEURS SUR RASPBERRY PI")
    print("=" * 45)
    
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Charger la configuration
    print("📁 Chargement de la configuration...")
    config_files = load_config_files()
    if not config_files:
        print("❌ Impossible de charger la configuration")
        return False
    
    print("✅ Configuration chargée")
    
    # Créer le contrôleur principal
    print("\n🎛️  Initialisation du contrôleur principal...")
    main_config = ControllerConfig(
        name="main_controller",
        enabled=True,
        update_interval=2.0,
        auto_start=False
    )
    
    try:
        main_controller = MainController(main_config, config_files)
        
        # Initialiser le contrôleur
        if not main_controller.initialize():
            print("❌ Échec initialisation contrôleur principal")
            return False
        
        print("✅ Contrôleur principal initialisé")
        
        # Démarrer le contrôleur
        print("\n🚀 Démarrage du contrôleur principal...")
        if not main_controller.start():
            print("❌ Échec démarrage contrôleur principal")
            return False
        
        print("✅ Contrôleur principal démarré")
        
        # Test de fonctionnement avec affichage en temps réel
        print("\n⏱️  Test de fonctionnement (30 secondes)...")
        print("   • Tournez l'encodeur pour naviguer")
        print("   • Appuyez sur le bouton pour changer d'écran")
        print("   • Observez l'écran ST7735")
        print("   • Vérifiez les LED/actionneurs")
        
        start_time = time.time()
        last_status_time = 0
        
        while time.time() - start_time < 30:
            current_time = time.time()
            
            # Afficher le statut toutes les 5 secondes
            if current_time - last_status_time >= 5:
                status = main_controller.get_system_status()
                
                print(f"\n📊 Statut du système (t+{current_time - start_time:.0f}s):")
                print(f"   • Mode: {status['system_state']['mode']}")
                print(f"   • Uptime: {status['system_state']['system_uptime']:.1f}s")
                
                # Afficher les données des capteurs
                sensor_data = status['system_state']['last_sensor_data']
                if sensor_data:
                    print(f"   • Température: {sensor_data.get('temperature', 'N/A')}°C")
                    print(f"   • Humidité: {sensor_data.get('humidity', 'N/A')}%")
                    print(f"   • Qualité air: {sensor_data.get('air_quality', 'N/A')}")
                    print(f"   • Niveau eau: {sensor_data.get('water_percentage', 'N/A')}%")
                
                # Afficher l'état des actionneurs
                actuator_states = status['system_state']['last_actuator_states']
                if actuator_states:
                    print(f"   • Chauffage: {'ON' if actuator_states.get('heater_on', False) else 'OFF'}")
                    print(f"   • Humidificateur: {'ON' if actuator_states.get('humidifier_on', False) else 'OFF'}")
                    print(f"   • LED: {actuator_states.get('led_intensity', 0)}%")
                    print(f"   • Distributeur: {actuator_states.get('feeder_position', 'N/A')}")
                
                # Afficher les alertes
                alerts = status['system_state']['active_alerts']
                if alerts:
                    print(f"   • Alertes: {len(alerts)}")
                    for alert in alerts[:3]:  # Afficher les 3 premières
                        print(f"     - {alert.get('type', 'Unknown')}: {alert.get('message', 'No message')}")
                else:
                    print("   • Alertes: Aucune")
                
                last_status_time = current_time
            
            time.sleep(1)
        
        # Test des modes
        print("\n🔄 Test des modes de fonctionnement...")
        
        # Mode manuel
        print("   • Activation mode manuel...")
        if main_controller.set_mode("manual"):
            print("   ✅ Mode manuel activé")
        else:
            print("   ❌ Échec activation mode manuel")
        
        time.sleep(3)
        
        # Mode maintenance
        print("   • Activation mode maintenance...")
        if main_controller.set_mode("maintenance"):
            print("   ✅ Mode maintenance activé")
        else:
            print("   ❌ Échec activation mode maintenance")
        
        time.sleep(3)
        
        # Retour au mode auto
        print("   • Retour au mode automatique...")
        if main_controller.set_mode("auto"):
            print("   ✅ Mode automatique activé")
        else:
            print("   ❌ Échec activation mode automatique")
        
        time.sleep(3)
        
        # Test d'arrêt d'urgence
        print("\n🚨 Test d'arrêt d'urgence...")
        print("   • Activation arrêt d'urgence...")
        main_controller.emergency_stop()
        print("   ✅ Arrêt d'urgence activé")
        print("   • Vérifiez que tous les actionneurs sont éteints")
        
        time.sleep(3)
        
        print("   • Désactivation arrêt d'urgence...")
        main_controller.emergency_resume()
        print("   ✅ Arrêt d'urgence désactivé")
        
        # Arrêter le contrôleur
        print("\n🛑 Arrêt du contrôleur principal...")
        if main_controller.stop():
            print("✅ Contrôleur principal arrêté")
        else:
            print("❌ Échec arrêt contrôleur principal")
        
        # Nettoyer
        main_controller.cleanup()
        print("✅ Contrôleur principal nettoyé")
        
        print("\n🎉 TEST TERMINÉ AVEC SUCCÈS")
        print("   • Vérifiez que l'écran s'est éteint")
        print("   • Vérifiez que tous les actionneurs sont éteints")
        print("   • Vérifiez qu'il n'y a pas d'erreurs dans les logs")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test contrôleurs: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🍓 DÉMARRAGE DES TESTS RASPBERRY PI")
    print("=" * 35)
    
    # Test du contrôleur principal avec matériel
    if not test_controllers_with_hardware():
        print("\n❌ Échec test contrôleur principal")
        sys.exit(1)
    
    print("\n🎉 TOUS LES TESTS RÉUSSIS")
    sys.exit(0)
