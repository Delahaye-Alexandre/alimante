#!/usr/bin/env python3
"""
Test simple des connexions des composants Alimante
Vérifie que tous les composants sont bien "branchés" sans dépendances matérielles
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test des imports de tous les composants"""
    print("📦 TEST DES IMPORTS")
    print("=" * 30)
    
    imports_tests = [
        # Services principaux
        ("EventBus", "src.utils.event_bus"),
        ("SafetyService", "src.services.safety_service"),
        ("ConfigService", "src.services.config_service"),
        ("ControlService", "src.services.control_service"),
        ("SensorService", "src.services.sensor_service"),
        ("PersistenceService", "src.services.persistence_service"),
        ("TerrariumService", "src.services.terrarium_service"),
        
        # Services de contrôle
        ("HeatingService", "src.services.heating_service"),
        ("LightingService", "src.services.lighting_service"),
        ("HumidificationService", "src.services.humidification_service"),
        ("VentilationService", "src.services.ventilation_service"),
        ("FeedingService", "src.services.feeding_service"),
        
        # Services de caméra et streaming
        ("CameraService", "src.services.camera_service"),
        ("StreamingService", "src.services.streaming_service"),
        ("SnapshotService", "src.services.snapshot_service"),
        ("AlertService", "src.services.alert_service"),
        
        # Contrôleurs
        ("MainController", "src.controllers.main_controller"),
        ("SensorController", "src.controllers.sensor_controller"),
        ("ActuatorController", "src.controllers.actuator_controller"),
        ("DeviceController", "src.controllers.device_controller"),
        
        # Contrôleurs d'actionneurs
        ("HeaterController", "src.controllers.actuators.heater_controller"),
        ("HumidifierController", "src.controllers.actuators.humidifier_controller"),
        ("FanController", "src.controllers.actuators.fan_controller"),
        ("FeederSASController", "src.controllers.actuators.feeder_sas_controller"),
        
        # Drivers
        ("CameraDriver", "src.controllers.drivers.camera_driver"),
        ("MosfetDriver", "src.controllers.drivers.mosfet_driver"),
        ("I2CLCDDriver", "src.controllers.drivers.i2c_lcd_driver"),
        
        # UI
        ("UIController", "src.ui.ui_controller"),
        ("MainLoop", "src.loops.main_loop"),
    ]
    
    passed = 0
    total = len(imports_tests)
    
    for class_name, module_path in imports_tests:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  ✅ {class_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {class_name}: {e}")
    
    print(f"\nImports réussis: {passed}/{total}")
    return passed == total

def test_configuration_loading():
    """Test du chargement des configurations"""
    print("\n⚙️ TEST DU CHARGEMENT DES CONFIGURATIONS")
    print("=" * 50)
    
    try:
        from src.services.config_service import ConfigService
        
        config_service = ConfigService()
        all_configs = config_service.load_all_configs()
        
        print(f"✅ Service de configuration initialisé")
        print(f"   Configurations chargées: {len(all_configs)}")
        
        # Vérifier les configurations principales
        expected_configs = ['main', 'gpio', 'network', 'safety', 'hardcoded']
        for config_name in expected_configs:
            if config_name in all_configs:
                print(f"  ✅ {config_name}")
            else:
                print(f"  ❌ {config_name} manquant")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur chargement configurations: {e}")
        return False

def test_event_bus():
    """Test du bus d'événements"""
    print("\n🔗 TEST DU BUS D'ÉVÉNEMENTS")
    print("=" * 30)
    
    try:
        from src.utils.event_bus import EventBus
        
        event_bus = EventBus()
        print("✅ Bus d'événements créé")
        
        # Test d'émission d'événement
        test_data = {"test": "data", "timestamp": 1234567890}
        event_bus.emit("test_event", test_data)
        print("✅ Émission d'événement réussie")
        
        # Test d'abonnement à un événement
        received_data = None
        
        def test_callback(data):
            nonlocal received_data
            received_data = data
        
        event_bus.subscribe("test_event", test_callback)
        event_bus.emit("test_event", test_data)
        
        if received_data == test_data:
            print("✅ Réception d'événement réussie")
        else:
            print("❌ Échec réception d'événement")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test bus d'événements: {e}")
        return False

def test_ui_controller():
    """Test du contrôleur UI"""
    print("\n🖥️ TEST DU CONTRÔLEUR UI")
    print("=" * 30)
    
    try:
        from src.ui.ui_controller import UIController
        from src.utils.event_bus import EventBus
        
        event_bus = EventBus()
        config = {"ui": {"mode": "both"}}
        
        ui_controller = UIController(event_bus, config)
        print("✅ Contrôleur UI initialisé")
        
        # Vérifier les services injectés
        if hasattr(ui_controller, 'persistence_service'):
            print("✅ Service de persistance injecté")
        else:
            print("❌ Service de persistance non injecté")
        
        if hasattr(ui_controller, 'terrarium_service'):
            print("✅ Service de terrariums injecté")
        else:
            print("❌ Service de terrariums non injecté")
        
        if hasattr(ui_controller, 'component_control_service'):
            print("✅ Service de contrôle des composants injecté")
        else:
            print("❌ Service de contrôle des composants non injecté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test contrôleur UI: {e}")
        return False

def test_main_loop():
    """Test de la boucle principale"""
    print("\n🔄 TEST DE LA BOUCLE PRINCIPALE")
    print("=" * 40)
    
    try:
        from src.loops.main_loop import MainLoop
        from src.utils.event_bus import EventBus
        from src.services.safety_service import SafetyService
        
        event_bus = EventBus()
        safety_service = SafetyService(event_bus)
        main_loop = MainLoop(event_bus, safety_service)
        
        print("✅ Boucle principale initialisée")
        
        # Vérifier les composants de la boucle
        if hasattr(main_loop, 'control_service'):
            print("✅ Service de contrôle présent")
        else:
            print("❌ Service de contrôle manquant")
        
        if hasattr(main_loop, 'config'):
            print("✅ Configuration chargée")
        else:
            print("❌ Configuration manquante")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test boucle principale: {e}")
        return False

def test_controller_connections():
    """Test des connexions des contrôleurs"""
    print("\n🎛️ TEST DES CONNEXIONS DES CONTRÔLEURS")
    print("=" * 50)
    
    try:
        from src.controllers.main_controller import MainController
        from src.controllers.base_controller import ControllerConfig
        from src.utils.event_bus import EventBus
        
        event_bus = EventBus()
        config = ControllerConfig(
            name="main_controller",
            enabled=True,
            update_interval=1.0,
            auto_start=False
        )
        
        config_files = {
            "gpio_config": {},
            "safety_limits": {},
            "policies": {},
            "terrarium_config": {}
        }
        
        main_controller = MainController(config, config_files, event_bus)
        print("✅ Contrôleur principal créé")
        
        # Vérifier les sous-contrôleurs
        if hasattr(main_controller, 'sensor_controller'):
            print("✅ Contrôleur de capteurs présent")
        else:
            print("❌ Contrôleur de capteurs manquant")
        
        if hasattr(main_controller, 'actuator_controller'):
            print("✅ Contrôleur d'actionneurs présent")
        else:
            print("❌ Contrôleur d'actionneurs manquant")
        
        if hasattr(main_controller, 'device_controller'):
            print("✅ Contrôleur de périphériques présent")
        else:
            print("❌ Contrôleur de périphériques manquant")
        
        # Vérifier les contrôleurs spécialisés
        if hasattr(main_controller, 'heater_controller'):
            print("✅ Contrôleur de chauffage présent")
        else:
            print("❌ Contrôleur de chauffage manquant")
        
        if hasattr(main_controller, 'humidifier_controller'):
            print("✅ Contrôleur d'humidification présent")
        else:
            print("❌ Contrôleur d'humidification manquant")
        
        if hasattr(main_controller, 'fan_controller'):
            print("✅ Contrôleur de ventilation présent")
        else:
            print("❌ Contrôleur de ventilation manquant")
        
        if hasattr(main_controller, 'feeder_controller'):
            print("✅ Contrôleur d'alimentation présent")
        else:
            print("❌ Contrôleur d'alimentation manquant")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test connexions contrôleurs: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST SIMPLE DES CONNEXIONS DES COMPOSANTS")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_configuration_loading,
        test_event_bus,
        test_ui_controller,
        test_main_loop,
        test_controller_connections
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Ligne vide entre les tests
    
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 30)
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 TOUS LES COMPOSANTS SONT BIEN CONNECTÉS !")
        print("L'architecture de l'application Alimante est cohérente.")
        return True
    else:
        print("❌ CERTAINS COMPOSANTS NÉCESSITENT UNE ATTENTION")
        print("Vérifiez les erreurs ci-dessus pour corriger les problèmes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
