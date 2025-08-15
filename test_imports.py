#!/usr/bin/env python3
"""
Test simple des imports Alimante
Vérifie que les corrections d'imports fonctionnent
"""

import sys
import os

def test_basic_imports():
    """Test des imports de base"""
    print("🧪 Test des imports de base...")
    
    try:
        # Test import du package principal
        from src import __version__
        print(f"✅ Package principal: version {__version__}")
        
        # Test import des utilitaires
        from src.utils.config_manager import SystemConfig
        print("✅ Config manager importé")
        
        from src.utils.gpio_manager import GPIOManager
        print("✅ GPIO manager importé")
        
        from src.utils.logging_config import get_logger
        print("✅ Logging config importé")
        
        # Test import des contrôleurs
        from src.controllers.base_controller import BaseController
        print("✅ Base controller importé")
        
        from src.controllers.temperature_controller import TemperatureController
        print("✅ Temperature controller importé")
        
        # Test import des services
        from src.services.system_service import system_service
        print("✅ System service importé")
        
        from src.services.control_service import control_service
        print("✅ Control service importé")
        
        # Test import de l'API
        from src.api.models import SystemStatusResponse
        print("✅ API models importés")
        
        print("✅ Tous les imports de base fonctionnent !")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def test_relative_imports():
    """Test des imports relatifs dans les modules"""
    print("\n🧪 Test des imports relatifs...")
    
    try:
        # Test que les contrôleurs peuvent importer leurs dépendances
        from src.controllers.temperature_controller import TemperatureController
        controller = TemperatureController()
        print("✅ Temperature controller créé avec succès")
        
        from src.controllers.humidity_controller import HumidityController
        controller = HumidityController()
        print("✅ Humidity controller créé avec succès")
        
        from src.controllers.feeding_controller import FeedingController
        controller = FeedingController()
        print("✅ Feeding controller créé avec succès")
        
        print("✅ Tous les imports relatifs fonctionnent !")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import relatif: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def test_package_structure():
    """Test de la structure du package"""
    print("\n🧪 Test de la structure du package...")
    
    try:
        # Vérifier que src est un package
        import src
        assert hasattr(src, '__version__')
        print(f"✅ Package src: {src.__version__}")
        
        # Vérifier les sous-packages
        import src.utils
        import src.controllers
        import src.services
        import src.api
        print("✅ Tous les sous-packages sont accessibles")
        
        # Vérifier les modules principaux
        from src.utils import config_manager, gpio_manager, logging_config
        print("✅ Modules utils accessibles")
        
        from src.controllers import base_controller, temperature_controller
        print("✅ Modules controllers accessibles")
        
        from src.services import system_service, control_service
        print("✅ Modules services accessibles")
        
        print("✅ Structure du package correcte !")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur de structure: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def main():
    """Exécute tous les tests d'imports"""
    print("🧪 Tests des imports Alimante")
    print("=" * 50)
    
    tests = [
        ("Imports de base", test_basic_imports),
        ("Imports relatifs", test_relative_imports),
        ("Structure du package", test_package_structure),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name} - PASSÉ")
                passed += 1
            else:
                print(f"❌ {test_name} - ÉCHOUÉ")
        except Exception as e:
            print(f"❌ {test_name} - ERREUR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Résultats: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 Tous les tests d'imports sont passés !")
        print("✅ Les corrections d'architecture et d'imports fonctionnent.")
        print("\n🔧 Prochaines étapes:")
        print("   - Tester l'API FastAPI")
        print("   - Vérifier les contrôleurs GPIO")
        print("   - Lancer l'application complète")
    else:
        print("⚠️ Certains tests d'imports ont échoué.")
        print("🔧 Vérifiez les erreurs ci-dessus.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
