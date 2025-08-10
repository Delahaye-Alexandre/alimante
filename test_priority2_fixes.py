#!/usr/bin/env python3
"""
Script de test pour les corrections de priorité 2
Vérifie la cohérence de la configuration et des contrôleurs
"""

import sys
import os
import json
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gpio_config_structure():
    """Teste la structure de la configuration GPIO"""
    print("🔌 Test de la structure de configuration GPIO...")
    
    try:
        with open("config/gpio_config.json", "r") as f:
            gpio_config = json.load(f)
        
        # Vérifier la structure
        required_sections = ["gpio_pins", "pin_assignments", "power_supply", "hardware_config", "communication"]
        for section in required_sections:
            if section not in gpio_config:
                print(f"❌ Section manquante: {section}")
                return False
        
        # Vérifier les pins
        pins = gpio_config.get("gpio_pins", {})
        if not pins:
            print("❌ Aucun pin configuré")
            return False
        
        # Vérifier les assignations
        assignments = gpio_config.get("pin_assignments", {})
        if not assignments:
            print("❌ Aucune assignation de pin")
            return False
        
        print("✅ Structure de configuration GPIO valide")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de la configuration GPIO: {e}")
        return False

def test_system_config_integration():
    """Teste l'intégration de SystemConfig avec la configuration GPIO"""
    print("\n📊 Test de l'intégration SystemConfig...")
    
    try:
        from src.utils.config_manager import SystemConfig
        
        # Charger la configuration
        config = SystemConfig.from_json(
            "config/config.json",
            "config/orthopteres/mantidae/mantis_religiosa.json",
            "config/gpio_config.json"
        )
        
        # Vérifier que la config GPIO est chargée
        gpio_config = config.get_gpio_config()
        if not gpio_config:
            print("❌ Configuration GPIO non chargée")
            return False
        
        # Vérifier les pins
        pins = config.get_gpio_pins()
        if not pins:
            print("❌ Pins GPIO non récupérés")
            return False
        
        # Vérifier les assignations
        assignments = config.get_pin_assignments()
        if not assignments:
            print("❌ Assignations de pins non récupérées")
            return False
        
        print("✅ Intégration SystemConfig réussie")
        print(f"   - Pins configurés: {len(pins)}")
        print(f"   - Assignations: {len(assignments)}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test SystemConfig: {e}")
        return False

def test_temperature_controller():
    """Teste le contrôleur de température"""
    print("\n🌡️ Test du contrôleur de température...")
    
    try:
        from src.controllers.temperature_controller import TemperatureController
        from src.utils.gpio_manager import GPIOManager
        
        # Configuration de test
        test_config = {
            "temperature": {
                "optimal": 25.0,
                "tolerance": 2.0,
                "min": 15.0,
                "max": 35.0
            },
            "gpio_config": {
                "pin_assignments": {
                    "TEMP_HUMIDITY_PIN": 4,
                    "HEATING_RELAY_PIN": 18
                }
            }
        }
        
        # Créer un GPIOManager mock
        class MockGPIOManager:
            def setup_pin(self, config):
                pass
            def set_pin_state(self, pin, state):
                pass
            def get_pin_state(self, pin):
                return False
        
        gpio_manager = MockGPIOManager()
        
        # Créer le contrôleur
        controller = TemperatureController(gpio_manager, test_config)
        
        # Vérifier l'initialisation
        if not controller.is_initialized():
            print("❌ Contrôleur non initialisé")
            return False
        
        # Vérifier les méthodes abstraites
        status = controller.get_status()
        if not status or "controller" not in status:
            print("❌ Méthode get_status() défaillante")
            return False
        
        # Vérifier le contrôle
        control_result = controller.control()
        if control_result is None:
            print("❌ Méthode control() défaillante")
            return False
        
        print("✅ Contrôleur de température fonctionnel")
        print(f"   - Statut: {status.get('controller')}")
        print(f"   - Température cible: {status.get('target_temperature')}°C")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test du contrôleur: {e}")
        return False

def test_config_loading():
    """Teste le chargement de configuration via select_config"""
    print("\n📁 Test du chargement de configuration...")
    
    try:
        from src.utils.select_config import load_species_config
        
        # Charger la configuration
        config = load_species_config("mantis_religiosa")
        
        # Vérifier la structure
        if not hasattr(config, 'gpio_config'):
            print("❌ Configuration GPIO non présente")
            return False
        
        if not hasattr(config, 'temperature'):
            print("❌ Configuration température non présente")
            return False
        
        print("✅ Chargement de configuration réussi")
        print(f"   - Espèce: {config.species_name}")
        print(f"   - Config GPIO: {'✅' if config.gpio_config else '❌'}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement de configuration: {e}")
        return False

def main():
    """Programme principal de test"""
    print("🧪 Test des corrections de priorité 2")
    print("=" * 50)
    
    tests = [
        ("Structure GPIO", test_gpio_config_structure),
        ("Intégration SystemConfig", test_system_config_integration),
        ("Contrôleur température", test_temperature_controller),
        ("Chargement config", test_config_loading)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' a échoué avec une exception: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    success_count = 0
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if result:
            success_count += 1
    
    print(f"\n📈 Résultat: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("🎉 Toutes les corrections de priorité 2 sont fonctionnelles !")
        print("\n📋 Prochaines étapes:")
        print("1. Tester les autres contrôleurs")
        print("2. Vérifier la documentation")
        print("3. Passer aux tests d'intégration")
    else:
        print("⚠️ Certaines corrections nécessitent encore du travail.")
        print("🔧 Vérifiez les erreurs ci-dessus.")
    
    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
