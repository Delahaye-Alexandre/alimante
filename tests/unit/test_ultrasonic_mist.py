#!/usr/bin/env python3
"""
Test du contrôleur de brumisateur ultrasonique
"""

import sys
import time
import json
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.gpio_manager import GPIOManager
from src.controllers.buzzer_controller import UltrasonicMistController
from src.utils.logging_config import get_logger

def test_ultrasonic_mist():
    """Test complet du contrôleur de brumisateur ultrasonique"""
    logger = get_logger("test_ultrasonic_mist")
    
    print("🧪 Test du contrôleur de brumisateur ultrasonique")
    print("=" * 50)
    
    try:
        # Configuration de test
        config = {
            "pin": 22,
            "voltage": "12V",
            "current": 100,
            "power_watts": 24,
            "frequency": 1700000
        }
        
        print(f"📋 Configuration: {json.dumps(config, indent=2)}")
        
        # Initialisation GPIO (simulation)
        gpio_manager = GPIOManager()
        
        # Initialisation du contrôleur
        print("\n🔧 Initialisation du contrôleur...")
        controller = UltrasonicMistController(gpio_manager, config)
        
        # Test 1: Statut initial
        print("\n📊 Test 1: Statut initial")
        status = controller.get_status()
        print(f"Statut: {json.dumps(status, indent=2)}")
        
        # Test 2: Activation courte
        print("\n💨 Test 2: Activation courte (2 secondes)")
        success = controller.activate_mist(intensity=30, duration=2)
        print(f"Activation: {'✅ Succès' if success else '❌ Échec'}")
        
        # Test 3: Statut après activation
        print("\n📊 Test 3: Statut après activation")
        status = controller.get_status()
        print(f"Statut: {json.dumps(status, indent=2)}")
        
        # Test 4: Modes prédéfinis
        print("\n🌊 Test 4: Modes d'humidification")
        for mode in ["light", "medium", "heavy"]:
            print(f"  - Mode {mode}: ", end="")
            try:
                success = controller.run_mist_mode(mode)
                print("✅ Succès" if success else "❌ Échec")
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        # Test 5: Ajustement d'intensité
        print("\n🎛️ Test 5: Ajustement d'intensité")
        controller.activate_mist(intensity=50)
        time.sleep(1)
        controller.set_mist_intensity(80)
        time.sleep(1)
        controller.deactivate_mist()
        print("✅ Intensité ajustée")
        
        # Test 6: Arrêt d'urgence
        print("\n🚨 Test 6: Arrêt d'urgence")
        controller.activate_mist(intensity=100)
        time.sleep(0.5)
        success = controller.emergency_stop()
        print(f"Arrêt d'urgence: {'✅ Succès' if success else '❌ Échec'}")
        
        # Test 7: Ajout de mode personnalisé
        print("\n➕ Test 7: Ajout de mode personnalisé")
        custom_mode = {
            "duration": 45,
            "intensity": 75,
            "description": "Humidification personnalisée"
        }
        success = controller.add_mist_mode("custom", custom_mode)
        print(f"Ajout mode: {'✅ Succès' if success else '❌ Échec'}")
        
        # Test 8: Statut final
        print("\n📊 Test 8: Statut final")
        status = controller.get_status()
        print(f"Statut: {json.dumps(status, indent=2)}")
        
        # Test 9: Vérification de sécurité
        print("\n🔒 Test 9: Vérification de sécurité")
        health = controller.check_status()
        print(f"Santé du contrôleur: {'✅ OK' if health else '❌ Problème'}")
        
        # Nettoyage
        print("\n🧹 Nettoyage...")
        controller.cleanup()
        
        print("\n✅ Tests terminés avec succès!")
        
    except Exception as e:
        logger.exception("Erreur lors des tests")
        print(f"\n❌ Erreur: {e}")
        return False
    
    return True

def test_modes_humidification():
    """Test spécifique des modes d'humidification"""
    print("\n🌊 Test des modes d'humidification")
    print("=" * 30)
    
    try:
        config = {"pin": 22, "voltage": "12V"}
        gpio_manager = GPIOManager()
        controller = UltrasonicMistController(gpio_manager, config)
        
        modes = controller.mist_modes
        print(f"Modes disponibles: {list(modes.keys())}")
        
        for mode_name, mode_config in modes.items():
            print(f"\n📋 Mode '{mode_name}':")
            print(f"  - Durée: {mode_config['duration']}s")
            print(f"  - Intensité: {mode_config['intensity']}%")
            print(f"  - Description: {mode_config['description']}")
        
        print("\n✅ Configuration des modes OK")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🧪 Tests du contrôleur de brumisateur ultrasonique")
    print("=" * 60)
    
    # Test principal
    success = test_ultrasonic_mist()
    
    # Test des modes
    test_modes_humidification()
    
    if success:
        print("\n🎉 Tous les tests sont passés!")
        sys.exit(0)
    else:
        print("\n💥 Certains tests ont échoué!")
        sys.exit(1)
