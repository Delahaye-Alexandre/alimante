#!/usr/bin/env python3
"""
Test complet du système Alimante
Vérifie que tous les composants fonctionnent ensemble
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Teste que tous les imports fonctionnent"""
    print("🔍 Test des imports...")
    
    try:
        from utils.config_manager import SystemConfig
        from utils.gpio_manager import GPIOManager, PinAssignments
        from controllers.temperature_controller import TemperatureController
        from controllers.humidity_controller import HumidityController
        from controllers.light_controller import LightController
        from controllers.feeding_controller import FeedingController
        from api.app import app
        print("✅ Tous les imports fonctionnent")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def test_config_manager():
    """Teste le gestionnaire de configuration"""
    print("⚙️  Test du gestionnaire de configuration...")
    
    try:
        from utils.config_manager import SystemConfig
        
        # Test avec des données valides
        config_data = {
            "serial_port": "/dev/ttyAMA0",
            "baud_rate": 9600,
            "temperature": {"optimal": 25, "tolerance": 2, "min": 20, "max": 30},
            "humidity": {"optimal": 70, "tolerance": 5, "min": 50, "max": 90},
            "location": {"latitude": 48.8566, "longitude": 2.3522},
            "feeding": {"interval_days": 2, "feed_count": 1, "prey_type": "drosophila"}
        }
        
        # Créer des fichiers temporaires
        with open('temp_common.json', 'w') as f:
            json.dump({"serial_port": "/dev/ttyAMA0", "baud_rate": 9600}, f)
        
        with open('temp_specific.json', 'w') as f:
            json.dump(config_data, f)
        
        config = SystemConfig.from_json('temp_common.json', 'temp_specific.json')
        
        # Nettoyer
        os.remove('temp_common.json')
        os.remove('temp_specific.json')
        
        print("✅ Gestionnaire de configuration fonctionne")
        return True
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return False

def test_gpio_manager():
    """Teste le gestionnaire GPIO (simulation)"""
    print("🔌 Test du gestionnaire GPIO...")
    
    try:
        from utils.gpio_manager import GPIOManager, PinAssignments, PinConfig, PinMode
        
        # Test avec mock
        with patch('utils.gpio_manager.GPIO') as mock_gpio:
            manager = GPIOManager()
            
            # Test configuration pin
            pin_config = PinConfig(pin=18, mode=PinMode.OUTPUT, initial_state=False)
            result = manager.setup_pin(pin_config)
            
            print("✅ Gestionnaire GPIO fonctionne (simulation)")
            return True
    except Exception as e:
        print(f"❌ Erreur GPIO: {e}")
        return False

def test_controllers():
    """Teste tous les contrôleurs"""
    print("🎛️  Test des contrôleurs...")
    
    try:
        from utils.gpio_manager import GPIOManager
        from controllers.temperature_controller import TemperatureController
        from controllers.humidity_controller import HumidityController
        from controllers.light_controller import LightController
        from controllers.feeding_controller import FeedingController
        
        # Mock GPIO
        mock_gpio = Mock()
        mock_gpio.initialized = True
        mock_gpio.setup_pin.return_value = True
        mock_gpio.write_digital.return_value = True
        mock_gpio.read_digital.return_value = False
        mock_gpio.set_pwm_duty_cycle.return_value = True
        
        # Test température
        temp_config = {"optimal": 25, "tolerance": 2, "min": 20, "max": 30}
        temp_controller = TemperatureController(mock_gpio, temp_config)
        assert temp_controller.check_status()
        
        # Test humidité
        humidity_config = {"optimal": 70, "tolerance": 5, "min": 50, "max": 90}
        humidity_controller = HumidityController(mock_gpio, humidity_config)
        assert humidity_controller.check_status()
        
        # Test éclairage
        light_config = {"latitude": 48.8566, "longitude": 2.3522, "day_hours": 12}
        light_controller = LightController(mock_gpio, light_config)
        assert light_controller.check_status()
        
        # Test alimentation
        feeding_config = {"interval_days": 2, "feed_count": 1, "prey_type": "drosophila"}
        feeding_controller = FeedingController(mock_gpio, feeding_config)
        assert feeding_controller.check_status()
        
        print("✅ Tous les contrôleurs fonctionnent")
        return True
    except Exception as e:
        print(f"❌ Erreur contrôleurs: {e}")
        return False

def test_api():
    """Teste l'API FastAPI"""
    print("🌐 Test de l'API...")
    
    try:
        from api.app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test endpoint racine
        response = client.get("/")
        assert response.status_code == 200
        assert "Alimante API" in response.json()["message"]
        
        print("✅ API fonctionne")
        return True
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return False

def main():
    """Test complet du système"""
    print("🧪 Test complet du système Alimante")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config_manager),
        ("GPIO Manager", test_gpio_manager),
        ("Contrôleurs", test_controllers),
        ("API", test_api)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 Résumé des tests:")
    
    success_count = 0
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if result:
            success_count += 1
    
    print(f"\n📈 Résultat: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("🎉 Tous les tests sont réussis !")
        print("🚀 Le système Alimante est prêt à fonctionner.")
    else:
        print("⚠️  Certains tests ont échoué.")
        print("🔧 Vérifiez les erreurs ci-dessus.")
    
    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 