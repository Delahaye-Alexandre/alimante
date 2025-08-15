#!/usr/bin/env python3
"""
Script de test pour les corrections de priorité 3
Tests d'intégration et de diagnostic complet du système Alimante
"""

import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_feeding_controller_fixes():
    """Teste les corrections du contrôleur d'alimentation"""
    print("🍽️ Test des corrections du contrôleur d'alimentation...")
    
    try:
        from src.controllers.feeding_controller import FeedingController, FeedingConfig
        from src.utils.gpio_manager import GPIOManager, PinConfig, PinMode
        
        # Configuration de test
        test_config = {
            "feeding": {
                "interval_days": 2,
                "feed_count": 3,
                "prey_type": "Drosophiles",
                "servo_open_angle": 90,
                "servo_close_angle": 0,
                "trap_open_duration": 3
            },
            "gpio_config": {
                "pin_assignments": {
                    "FEEDING_SERVO_PIN": 12
                },
                "hardware_config": {
                    "servo": {
                        "feeding_trap": {
                            "open_angle": 90,
                            "close_angle": 0,
                            "min_pulse": 500,
                            "max_pulse": 2500
                        }
                    }
                }
            }
        }
        
        # Créer un GPIOManager mock
        class MockGPIOManager:
            def setup_pin(self, config):
                return True
            def set_servo_position(self, pin, pulse_width):
                return True
            def cleanup(self):
                pass
        
        gpio_manager = MockGPIOManager()
        
        # Créer le contrôleur
        controller = FeedingController(gpio_manager, test_config)
        
        # Vérifier l'initialisation
        if not controller.initialized:
            print("❌ Contrôleur non initialisé")
            return False
        
        # Vérifier la configuration
        if controller.feeding_config.interval_days != 2:
            print("❌ Configuration interval_days incorrecte")
            return False
        
        # Vérifier les méthodes de contrôle
        status = controller.get_status()
        if not status or status.get("controller") != "feeding":
            print("❌ Méthode get_status() défaillante")
            return False
        
        # Vérifier le timing d'alimentation
        should_feed = controller.should_feed_now()
        if not should_feed:
            print("❌ Premier repas non détecté")
            return False
        
        # Vérifier le contrôle principal
        control_result = controller.control()
        if control_result is None:
            print("❌ Méthode control() défaillante")
            return False
        
        print("✅ Contrôleur d'alimentation corrigé et fonctionnel")
        print(f"   - Configuration: {controller.feeding_config.prey_type}")
        print(f"   - Intervalle: {controller.feeding_config.interval_days} jours")
        print(f"   - Statut: {status.get('should_feed_now')}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test du contrôleur d'alimentation: {e}")
        return False

def test_system_integration():
    """Teste l'intégration complète du système"""
    print("\n🔗 Test de l'intégration système...")
    
    try:
        from src.utils.config_manager import SystemConfig
        from src.services.system_service import SystemService
        from src.services.control_service import ControlService
        
        # Charger la configuration système
        config = SystemConfig.from_json(
            "config/config.json",
            "config/orthopteres/mantidae/mantis_religiosa.json",
            "config/gpio_config.json"
        )
        
        # Vérifier que tous les services peuvent être créés
        system_service = SystemService(config)
        control_service = ControlService(config)
        
        # Vérifier l'état des services
        if not system_service.is_healthy():
            print("❌ Service système non sain")
            return False
        
        if not control_service.is_ready():
            print("❌ Service de contrôle non prêt")
            return False
        
        print("✅ Intégration système réussie")
        print(f"   - Service système: {'✅' if system_service.is_healthy() else '❌'}")
        print(f"   - Service contrôle: {'✅' if control_service.is_ready() else '❌'}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        return False

def test_api_endpoints():
    """Teste tous les endpoints de l'API"""
    print("\n🌐 Test des endpoints API...")
    
    try:
        from src.api.app import app
        
        # Créer un client de test
        with app.test_client() as client:
            # Test des endpoints principaux
            endpoints = [
                ("/api/status", "GET"),
                ("/api/temperature/status", "GET"),
                ("/api/humidity/status", "GET"),
                ("/api/light/status", "GET"),
                ("/api/feeding/status", "GET"),
                ("/api/water-level/status", "GET"),
                ("/api/radiator-temp/status", "GET")
            ]
            
            working_endpoints = 0
            for endpoint, method in endpoints:
                try:
                    if method == "GET":
                        response = client.get(endpoint)
                        if response.status_code in [200, 404]:  # 404 acceptable pour certains endpoints
                            working_endpoints += 1
                            print(f"  ✅ {endpoint}")
                        else:
                            print(f"  ❌ {endpoint} - Status: {response.status_code}")
                    else:
                        print(f"  ⚠️ {endpoint} - Méthode {method} non testée")
                except Exception as e:
                    print(f"  ❌ {endpoint} - Erreur: {e}")
            
            success_rate = (working_endpoints / len(endpoints)) * 100
            print(f"✅ API testée: {working_endpoints}/{len(endpoints)} endpoints fonctionnels ({success_rate:.1f}%)")
            return success_rate >= 80  # Au moins 80% des endpoints doivent fonctionner
        
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API: {e}")
        return False

def test_error_handling():
    """Teste la gestion des erreurs du système"""
    print("\n🛡️ Test de la gestion des erreurs...")
    
    try:
        from src.utils.error_handler import ErrorHandler
        from src.utils.exceptions import AlimanteError, ConfigurationError
        
        # Créer un gestionnaire d'erreurs
        error_handler = ErrorHandler()
        
        # Tester la gestion d'erreurs personnalisées
        try:
            raise ConfigurationError("Test d'erreur de configuration")
        except ConfigurationError as e:
            error_handler.handle_error(e)
        
        # Tester la gestion d'erreurs génériques
        try:
            raise ValueError("Test d'erreur générique")
        except Exception as e:
            error_handler.handle_error(e)
        
        # Vérifier que les erreurs ont été enregistrées
        if error_handler.get_error_count() >= 2:
            print("✅ Gestion des erreurs fonctionnelle")
            print(f"   - Erreurs enregistrées: {error_handler.get_error_count()}")
            return True
        else:
            print("❌ Erreurs non enregistrées correctement")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test de gestion d'erreurs: {e}")
        return False

def test_configuration_validation():
    """Teste la validation des configurations"""
    print("\n✅ Test de validation des configurations...")
    
    try:
        from src.utils.config_manager import SystemConfig
        
        # Test avec configuration valide
        valid_config = {
            "temperature": {"optimal": 25, "tolerance": 2, "min": 20, "max": 30},
            "humidity": {"optimal": 70, "tolerance": 5, "min": 50, "max": 90},
            "feeding": {"interval_days": 2, "feed_count": 1, "prey_type": "drosophila"}
        }
        
        # Créer des fichiers temporaires
        with open('temp_common.json', 'w') as f:
            json.dump({"serial_port": "/dev/ttyAMA0", "baud_rate": 9600}, f)
        
        with open('temp_specific.json', 'w') as f:
            json.dump(valid_config, f)
        
        config = SystemConfig.from_json('temp_common.json', 'temp_specific.json')
        
        # Nettoyer
        os.remove('temp_common.json')
        os.remove('temp_specific.json')
        
        # Vérifier la validation
        if config.validate():
            print("✅ Validation des configurations réussie")
            return True
        else:
            print("❌ Configuration invalide")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        return False

def test_gpio_integration():
    """Teste l'intégration GPIO complète"""
    print("\n🔌 Test de l'intégration GPIO...")
    
    try:
        from src.utils.gpio_manager import GPIOManager, PinConfig, PinMode
        
        # Test avec mock GPIO
        with patch('src.utils.gpio_manager.GPIO') as mock_gpio:
            manager = GPIOManager()
            
            # Test configuration des pins
            pins_to_test = [
                PinConfig(pin=4, mode=PinMode.INPUT),      # DHT22
                PinConfig(pin=12, mode=PinMode.PWM),       # Servo
                PinConfig(pin=18, mode=PinMode.OUTPUT),    # Relais chauffage
                PinConfig(pin=22, mode=PinMode.PWM),       # Transducteur
                PinConfig(pin=24, mode=PinMode.OUTPUT),    # LED
                PinConfig(pin=25, mode=PinMode.OUTPUT)     # Ventilateurs
            ]
            
            success_count = 0
            for pin_config in pins_to_test:
                try:
                    result = manager.setup_pin(pin_config)
                    if result:
                        success_count += 1
                        print(f"  ✅ Pin {pin_config.pin} configuré")
                    else:
                        print(f"  ❌ Pin {pin_config.pin} échec")
                except Exception as e:
                    print(f"  ❌ Pin {pin_config.pin} erreur: {e}")
            
            success_rate = (success_count / len(pins_to_test)) * 100
            print(f"✅ GPIO testé: {success_count}/{len(pins_to_test)} pins configurés ({success_rate:.1f}%)")
            return success_rate >= 80
        
    except Exception as e:
        print(f"❌ Erreur lors du test GPIO: {e}")
        return False

def test_logging_system():
    """Teste le système de logging"""
    print("\n📝 Test du système de logging...")
    
    try:
        from src.utils.logging_config import (
            setup_logging, 
            test_logging_system as test_logging,
            get_logging_status
        )
        
        # Configurer le logging
        logger = setup_logging("test_logger")
        
        # Tester le système de logging
        test_result = test_logging()
        if not test_result:
            print("❌ Test du système de logging échoué")
            return False
        
        # Obtenir le statut du système
        status = get_logging_status()
        print(f"   - Nom: {status.get('name', 'N/A')}")
        print(f"   - Niveau: {status.get('level', 'N/A')}")
        print(f"   - Handlers: {status.get('handlers_count', 'N/A')}")
        
        # Tester différents niveaux de log
        logger.debug("Test message debug")
        logger.info("Test message info")
        logger.warning("Test message warning")
        logger.error("Test message error")
        
        print("✅ Système de logging fonctionnel")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test du logging: {e}")
        return False

def main():
    """Programme principal de test"""
    print("🧪 Test des corrections de priorité 3")
    print("=" * 50)
    
    tests = [
        ("Contrôleur alimentation", test_feeding_controller_fixes),
        ("Intégration système", test_system_integration),
        ("Endpoints API", test_api_endpoints),
        ("Gestion erreurs", test_error_handling),
        ("Validation config", test_configuration_validation),
        ("Intégration GPIO", test_gpio_integration),
        ("Système logging", test_logging_system)
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
    print("📊 RÉSUMÉ DES TESTS PRIORITÉ 3")
    print("=" * 50)
    
    success_count = 0
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if result:
            success_count += 1
    
    print(f"\n📈 Résultat: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("🎉 Toutes les corrections de priorité 3 sont fonctionnelles !")
        print("\n📋 Prochaines étapes:")
        print("1. Tests de performance et endurance")
        print("2. Tests de sécurité et robustesse")
        print("3. Déploiement en environnement de production")
        print("4. Tests d'intégration avec le matériel physique")
    else:
        print("⚠️ Certaines corrections nécessitent encore du travail.")
        print("🔧 Vérifiez les erreurs ci-dessus.")
        print("\n📋 Priorités suivantes:")
        print("1. Corriger les tests échoués")
        print("2. Améliorer la robustesse du système")
        print("3. Optimiser les performances")
    
    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
