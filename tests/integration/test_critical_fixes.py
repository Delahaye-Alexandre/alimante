#!/usr/bin/env python3
"""
test_critical_fixes.py
Script de test pour vérifier que les corrections critiques fonctionnent
"""

import sys
import os
import json
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_gpio_manager_methods():
    """Test des méthodes GPIO manquantes"""
    print("🧪 Test des méthodes GPIO manquantes...")
    
    try:
        from src.utils.gpio_manager import GPIOManager
        
        # Créer une instance (sans initialisation GPIO réelle)
        gpio_manager = GPIOManager()
        
        # Tester les méthodes ajoutées
        assert hasattr(gpio_manager, 'set_pin_state'), "set_pin_state manquante"
        assert hasattr(gpio_manager, 'get_pin_state'), "get_pin_state manquante"
        assert hasattr(gpio_manager, 'read_analog'), "read_analog manquante"
        
        print("✅ Toutes les méthodes GPIO sont présentes")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test GPIO: {e}")
        return False

def test_controller_methods():
    """Test des méthodes des contrôleurs"""
    print("🧪 Test des méthodes des contrôleurs...")
    
    try:
        from src.controllers.temperature_controller import TemperatureController
        from src.controllers.humidity_controller import HumidityController
        from src.controllers.light_controller import LightController
        from src.controllers.feeding_controller import FeedingController
        
        # Vérifier que tous les contrôleurs ont la méthode control()
        controllers = [
            TemperatureController,
            HumidityController,
            LightController,
            FeedingController
        ]
        
        for controller_class in controllers:
            assert hasattr(controller_class, 'control'), f"control() manquante dans {controller_class.__name__}"
        
        print("✅ Tous les contrôleurs ont la méthode control()")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des contrôleurs: {e}")
        return False

def test_config_loading():
    """Test du chargement de la configuration"""
    print("🧪 Test du chargement de la configuration...")
    
    try:
        # Vérifier que les fichiers de configuration existent
        config_files = [
            'config/config.json',
            'config/gpio_config.json'
        ]
        
        for config_file in config_files:
            assert Path(config_file).exists(), f"Fichier de configuration manquant: {config_file}"
        
        # Vérifier que gpio_config.json est valide
        with open('config/gpio_config.json', 'r') as f:
            gpio_config = json.load(f)
        
        assert 'pin_assignments' in gpio_config, "pin_assignments manquant dans gpio_config.json"
        assert 'gpio_pins' in gpio_config, "gpio_pins manquant dans gpio_config.json"
        
        print("✅ Configuration GPIO valide")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de configuration: {e}")
        return False

def test_base_controller_interface():
    """Test de l'interface BaseController"""
    print("🧪 Test de l'interface BaseController...")
    
    try:
        from src.controllers.base_controller import BaseController
        
        # Vérifier que BaseController a les méthodes abstraites
        assert hasattr(BaseController, 'check_status'), "check_status manquante"
        assert hasattr(BaseController, 'get_status'), "get_status manquante"
        assert hasattr(BaseController, 'control'), "control manquante"
        
        print("✅ Interface BaseController complète")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test BaseController: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests des corrections critiques")
    print("=" * 50)
    
    tests = [
        test_gpio_manager_methods,
        test_controller_methods,
        test_config_loading,
        test_base_controller_interface
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Toutes les corrections critiques sont fonctionnelles !")
        return 0
    else:
        print("⚠️ Certaines corrections nécessitent encore des ajustements")
        return 1

if __name__ == "__main__":
    sys.exit(main())
