#!/usr/bin/env python3
"""
Script de test pour vérifier les corrections des problèmes critiques.
"""

import sys
import os
import logging

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_base_controller():
    """Test de la classe BaseController"""
    print("🔍 Test de BaseController...")
    
    try:
        from controllers.base_controller import BaseController
        from utils.gpio_manager import GPIOManager
        
        # Créer un mock GPIOManager
        class MockGPIOManager:
            def __init__(self):
                self.initialized = True
        
        # Test de création
        config = {'test': 'value'}
        controller = BaseController(MockGPIOManager(), config)
        
        # Vérifier les attributs
        assert hasattr(controller, 'gpio_manager')
        assert hasattr(controller, 'config')
        assert hasattr(controller, 'logger')
        assert hasattr(controller, 'initialized')
        assert hasattr(controller, 'error_count')
        assert hasattr(controller, 'last_error')
        
        print("✅ BaseController: OK")
        return True
        
    except Exception as e:
        print(f"❌ BaseController: ERREUR - {e}")
        return False

def test_temperature_controller():
    """Test de TemperatureController"""
    print("🔍 Test de TemperatureController...")
    
    try:
        from controllers.temperature_controller import TemperatureController
        from utils.gpio_manager import GPIOManager
        
        # Créer un mock GPIOManager
        class MockGPIOManager:
            def __init__(self):
                self.initialized = True
            
            def setup_pin(self, config):
                pass
            
            def write_digital(self, pin, state):
                return True
        
        # Test de création
        config = {
            'optimal': 25.0,
            'tolerance': 2.0,
            'min': 18.0,
            'max': 32.0
        }
        
        controller = TemperatureController(MockGPIOManager(), config)
        
        # Vérifier l'héritage
        assert isinstance(controller, TemperatureController)
        
        # Vérifier les méthodes abstraites
        assert hasattr(controller, 'check_status')
        assert hasattr(controller, 'get_status')
        assert hasattr(controller, 'control')
        
        # Vérifier l'initialisation
        assert controller.initialized == True
        
        print("✅ TemperatureController: OK")
        return True
        
    except Exception as e:
        print(f"❌ TemperatureController: ERREUR - {e}")
        return False

def test_config_manager():
    """Test de SystemConfig"""
    print("🔍 Test de SystemConfig...")
    
    try:
        from utils.config_manager import SystemConfig
        
        # Test de création avec des données minimales
        config = SystemConfig(
            system_info={},
            hardware={},
            communication={},
            location={},
            species_profiles={},
            system_control={},
            safety={},
            api={},
            logging={},
            performance={}
        )
        
        # Vérifier les attributs
        assert hasattr(config, 'system_info')
        assert hasattr(config, 'hardware')
        assert hasattr(config, 'communication')
        assert hasattr(config, 'location')
        assert hasattr(config, 'species_profiles')
        assert hasattr(config, 'system_control')
        assert hasattr(config, 'safety')
        assert hasattr(config, 'api')
        assert hasattr(config, 'logging')
        assert hasattr(config, 'performance')
        
        # Vérifier les méthodes
        assert hasattr(config, 'get_temperature_config')
        assert hasattr(config, 'get_humidity_config')
        assert hasattr(config, 'get_feeding_config')
        assert hasattr(config, 'get_lighting_config')
        
        print("✅ SystemConfig: OK")
        return True
        
    except Exception as e:
        print(f"❌ SystemConfig: ERREUR - {e}")
        return False

def test_select_config():
    """Test de select_config"""
    print("🔍 Test de select_config...")
    
    try:
        from utils.select_config import (
            get_available_species,
            select_species_config,
            get_default_species,
            list_species_by_order
        )
        
        # Test des fonctions
        species = get_available_species()
        assert isinstance(species, dict)
        
        default = get_default_species()
        assert isinstance(default, str)
        
        organized = list_species_by_order()
        assert isinstance(organized, dict)
        
        print("✅ select_config: OK")
        return True
        
    except Exception as e:
        print(f"❌ select_config: ERREUR - {e}")
        return False

def test_config_files():
    """Test des fichiers de configuration"""
    print("🔍 Test des fichiers de configuration...")
    
    try:
        import json
        
        # Test config.json principal
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        required_sections = [
            'system_info', 'hardware', 'communication', 'location',
            'species_profiles', 'system_control', 'safety', 'api',
            'logging', 'performance'
        ]
        
        for section in required_sections:
            assert section in config_data, f"Section manquante: {section}"
        
        # Test mantis_religiosa.json
        with open('config/orthopteres/mantidae/mantis_religiosa.json', 'r', encoding='utf-8') as f:
            species_data = json.load(f)
        
        required_fields = ['species_name', 'temperature', 'humidity', 'feeding', 'lighting']
        for field in required_fields:
            assert field in species_data, f"Champ manquant: {field}"
        
        print("✅ Fichiers de configuration: OK")
        return True
        
    except Exception as e:
        print(f"❌ Fichiers de configuration: ERREUR - {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests d'intégration...")
    print("=" * 50)
    
    tests = [
        test_base_controller,
        test_temperature_controller,
        test_config_manager,
        test_select_config,
        test_config_files
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} a échoué: {e}")
            results.append(False)
    
    print("=" * 50)
    print("📊 Résultats des tests:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1:2d}. {test.__name__:25s} - {status}")
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Les corrections critiques ont fonctionné.")
        return 0
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1

if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    
    # Exécution des tests
    exit_code = main()
    sys.exit(exit_code)
