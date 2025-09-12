#!/usr/bin/env python3
"""
Test des contrôleurs Alimante
Valide le fonctionnement de tous les contrôleurs
"""

import sys
import time
import json
import logging
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from controllers import MainController, ControllerConfig

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

def test_controllers():
    """Test des contrôleurs"""
    print("🧪 TEST DES CONTRÔLEURS ALIMANTE")
    print("=" * 40)
    
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
        update_interval=1.0,
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
        
        # Test de fonctionnement
        print("\n⏱️  Test de fonctionnement (10 secondes)...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            # Vérifier le statut
            status = main_controller.get_system_status()
            
            # Afficher les informations
            if time.time() - start_time > 5:  # Afficher après 5 secondes
                print(f"\n📊 Statut du système:")
                print(f"   • Mode: {status['system_state']['mode']}")
                print(f"   • Uptime: {status['system_state']['system_uptime']:.1f}s")
                print(f"   • Capteurs: {len([k for k, v in status['sensor_controller'].items() if v]) if status['sensor_controller'] else 0}")
                print(f"   • Actionneurs: {len([k for k, v in status['actuator_controller'].items() if v]) if status['actuator_controller'] else 0}")
                print(f"   • Périphériques: {len([k for k, v in status['device_controller'].items() if v]) if status['device_controller'] else 0}")
                break
            
            time.sleep(1)
        
        # Test des modes
        print("\n🔄 Test des modes de fonctionnement...")
        
        # Mode manuel
        if main_controller.set_mode("manual"):
            print("✅ Mode manuel activé")
        else:
            print("❌ Échec activation mode manuel")
        
        time.sleep(2)
        
        # Mode maintenance
        if main_controller.set_mode("maintenance"):
            print("✅ Mode maintenance activé")
        else:
            print("❌ Échec activation mode maintenance")
        
        time.sleep(2)
        
        # Retour au mode auto
        if main_controller.set_mode("auto"):
            print("✅ Mode automatique activé")
        else:
            print("❌ Échec activation mode automatique")
        
        # Test d'arrêt d'urgence
        print("\n🚨 Test d'arrêt d'urgence...")
        main_controller.emergency_stop()
        print("✅ Arrêt d'urgence activé")
        
        time.sleep(2)
        
        main_controller.emergency_resume()
        print("✅ Arrêt d'urgence désactivé")
        
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
        return True
        
    except Exception as e:
        print(f"❌ Erreur test contrôleurs: {e}")
        return False

def test_individual_controllers():
    """Test des contrôleurs individuels"""
    print("\n🔍 TEST DES CONTRÔLEURS INDIVIDUELS")
    print("=" * 40)
    
    # Charger la configuration
    config_files = load_config_files()
    if not config_files:
        return False
    
    # Test du contrôleur de base
    print("\n📋 Test contrôleur de base...")
    try:
        from controllers import BaseController, ControllerConfig
        
        class TestController(BaseController):
            def initialize(self):
                return True
            
            def update(self):
                return True
            
            def cleanup(self):
                pass
        
        config = ControllerConfig("test_controller", enabled=True)
        controller = TestController(config)
        
        if controller.initialize():
            print("✅ Contrôleur de base initialisé")
        else:
            print("❌ Échec initialisation contrôleur de base")
            return False
        
        if controller.start():
            print("✅ Contrôleur de base démarré")
        else:
            print("❌ Échec démarrage contrôleur de base")
            return False
        
        time.sleep(1)
        
        if controller.stop():
            print("✅ Contrôleur de base arrêté")
        else:
            print("❌ Échec arrêt contrôleur de base")
            return False
        
        controller.cleanup()
        print("✅ Contrôleur de base nettoyé")
        
    except Exception as e:
        print(f"❌ Erreur test contrôleur de base: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 DÉMARRAGE DES TESTS")
    print("=" * 30)
    
    # Test des contrôleurs individuels
    if not test_individual_controllers():
        print("\n❌ Échec test contrôleurs individuels")
        sys.exit(1)
    
    # Test du contrôleur principal
    if not test_controllers():
        print("\n❌ Échec test contrôleur principal")
        sys.exit(1)
    
    print("\n🎉 TOUS LES TESTS RÉUSSIS")
    sys.exit(0)

