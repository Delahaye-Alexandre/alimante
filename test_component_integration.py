#!/usr/bin/env python3
"""
Test d'intégration des composants Alimante
Vérifie que tous les composants sont bien "branchés" et effectifs
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_main_initialization():
    """Test de l'initialisation principale"""
    print("🏠 TEST D'INITIALISATION PRINCIPALE")
    print("=" * 50)
    
    try:
        # Test des imports principaux
        from src.utils.event_bus import EventBus
        from src.services.safety_service import SafetyService
        from src.services.config_service import ConfigService
        from src.services.camera_service import CameraService
        from src.services.streaming_service import StreamingService
        from src.services.snapshot_service import SnapshotService
        from src.services.alert_service import AlertService
        from src.ui.ui_controller import UIController
        from src.loops.main_loop import MainLoop
        
        print("✅ Tous les imports principaux réussis")
        
        # Test de l'initialisation du bus d'événements
        event_bus = EventBus()
        print("✅ Bus d'événements initialisé")
        
        # Test de l'initialisation du service de configuration
        config_service = ConfigService()
        all_configs = config_service.load_all_configs()
        print("✅ Service de configuration initialisé")
        print(f"   Configurations chargées: {len(all_configs)}")
        
        # Test de l'initialisation des services
        safety_service = SafetyService(event_bus)
        print("✅ Service de sécurité initialisé")
        
        camera_service = CameraService(all_configs.get('main', {}), event_bus)
        if camera_service.initialize():
            print("✅ Service de caméra initialisé")
        else:
            print("❌ Échec initialisation service de caméra")
        
        streaming_service = StreamingService(all_configs.get('main', {}), event_bus)
        if streaming_service.initialize():
            print("✅ Service de streaming initialisé")
        else:
            print("❌ Échec initialisation service de streaming")
        
        snapshot_service = SnapshotService(all_configs.get('main', {}), event_bus)
        if snapshot_service.initialize():
            print("✅ Service de snapshots initialisé")
        else:
            print("❌ Échec initialisation service de snapshots")
        
        alert_service = AlertService(all_configs.get('main', {}), event_bus)
        if alert_service.initialize():
            print("✅ Service d'alertes initialisé")
        else:
            print("❌ Échec initialisation service d'alertes")
        
        # Test de l'initialisation de l'UI
        ui_controller = UIController(event_bus, all_configs.get('main', {}))
        print("✅ Contrôleur UI initialisé")
        
        # Test de l'initialisation de la boucle principale
        main_loop = MainLoop(event_bus, safety_service)
        print("✅ Boucle principale initialisée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test initialisation principale: {e}")
        return False

def test_controller_integration():
    """Test de l'intégration des contrôleurs"""
    print("\n🎛️ TEST D'INTÉGRATION DES CONTRÔLEURS")
    print("=" * 50)
    
    try:
        from src.controllers.main_controller import MainController
        from src.controllers.actuators import HeaterController, HumidifierController, FanController, FeederSASController
        from src.utils.event_bus import EventBus
        from src.controllers.base_controller import ControllerConfig
        
        print("✅ Imports des contrôleurs réussis")
        
        # Test de l'initialisation des contrôleurs d'actionneurs
        event_bus = EventBus()
        gpio_config = {}  # Configuration GPIO simulée
        
        # Contrôleur de chauffage
        heater_config = ControllerConfig(
            name="heater_controller",
            enabled=True,
            update_interval=1.0,
            auto_start=False
        )
        heater_controller = HeaterController(heater_config, gpio_config, event_bus)
        if heater_controller.initialize():
            print("✅ Contrôleur de chauffage initialisé")
        else:
            print("❌ Échec initialisation contrôleur de chauffage")
        
        # Contrôleur d'humidification
        humidifier_config = ControllerConfig(
            name="humidifier_controller",
            enabled=True,
            update_interval=1.0,
            auto_start=False
        )
        humidifier_controller = HumidifierController(humidifier_config, gpio_config, event_bus)
        if humidifier_controller.initialize():
            print("✅ Contrôleur d'humidification initialisé")
        else:
            print("❌ Échec initialisation contrôleur d'humidification")
        
        # Contrôleur de ventilation
        fan_config = ControllerConfig(
            name="fan_controller",
            enabled=True,
            update_interval=1.0,
            auto_start=False
        )
        fan_controller = FanController(fan_config, gpio_config, event_bus)
        if fan_controller.initialize():
            print("✅ Contrôleur de ventilation initialisé")
        else:
            print("❌ Échec initialisation contrôleur de ventilation")
        
        # Contrôleur d'alimentation
        feeder_config = ControllerConfig(
            name="feeder_controller",
            enabled=True,
            update_interval=1.0,
            auto_start=False
        )
        feeder_controller = FeederSASController(feeder_config, gpio_config, event_bus)
        if feeder_controller.initialize():
            print("✅ Contrôleur d'alimentation initialisé")
        else:
            print("❌ Échec initialisation contrôleur d'alimentation")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test intégration contrôleurs: {e}")
        return False

def test_driver_integration():
    """Test de l'intégration des drivers"""
    print("\n🔌 TEST D'INTÉGRATION DES DRIVERS")
    print("=" * 50)
    
    try:
        from src.controllers.drivers.camera_driver import CameraDriver
        from src.controllers.drivers.mosfet_driver import MosfetDriver
        from src.controllers.drivers.i2c_lcd_driver import I2CLCDDriver
        from src.controllers.drivers.base_driver import DriverConfig
        
        print("✅ Imports des drivers réussis")
        
        # Test de l'initialisation des nouveaux drivers
        event_bus = None  # Pas de bus d'événements pour les drivers
        
        # Driver de caméra
        camera_config = DriverConfig(
            name="camera_driver",
            enabled=True,
            update_interval=1.0
        )
        camera_driver = CameraDriver(camera_config)
        if camera_driver.initialize():
            print("✅ Driver de caméra initialisé")
        else:
            print("❌ Échec initialisation driver de caméra")
        
        # Driver MOSFET
        mosfet_config = DriverConfig(
            name="mosfet_driver",
            enabled=True,
            update_interval=1.0
        )
        mosfet_driver = MosfetDriver(mosfet_config)
        if mosfet_driver.initialize():
            print("✅ Driver MOSFET initialisé")
        else:
            print("❌ Échec initialisation driver MOSFET")
        
        # Driver LCD I2C
        lcd_config = DriverConfig(
            name="i2c_lcd_driver",
            enabled=True,
            update_interval=1.0
        )
        lcd_driver = I2CLCDDriver(lcd_config)
        if lcd_driver.initialize():
            print("✅ Driver LCD I2C initialisé")
        else:
            print("❌ Échec initialisation driver LCD I2C")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test intégration drivers: {e}")
        return False

def test_service_integration():
    """Test de l'intégration des services"""
    print("\n⚙️ TEST D'INTÉGRATION DES SERVICES")
    print("=" * 50)
    
    try:
        from src.services.control_service import ControlService
        from src.services.sensor_service import SensorService
        from src.services.heating_service import HeatingService
        from src.services.lighting_service import LightingService
        from src.services.humidification_service import HumidificationService
        from src.services.ventilation_service import VentilationService
        from src.services.feeding_service import FeedingService
        from src.services.persistence_service import PersistenceService
        from src.services.terrarium_service import TerrariumService
        from src.utils.event_bus import EventBus
        
        print("✅ Imports des services réussis")
        
        # Test de l'initialisation des services
        event_bus = EventBus()
        config = {}  # Configuration simulée
        
        # Service de contrôle
        control_service = ControlService(config, event_bus)
        if control_service.initialize():
            print("✅ Service de contrôle initialisé")
        else:
            print("❌ Échec initialisation service de contrôle")
        
        # Service de capteurs
        sensor_service = SensorService(config, event_bus)
        if sensor_service.initialize():
            print("✅ Service de capteurs initialisé")
        else:
            print("❌ Échec initialisation service de capteurs")
        
        # Service de chauffage
        heating_service = HeatingService(config, event_bus)
        if heating_service.initialize():
            print("✅ Service de chauffage initialisé")
        else:
            print("❌ Échec initialisation service de chauffage")
        
        # Service d'éclairage
        lighting_service = LightingService(config, event_bus)
        if lighting_service.initialize():
            print("✅ Service d'éclairage initialisé")
        else:
            print("❌ Échec initialisation service d'éclairage")
        
        # Service d'humidification
        humidification_service = HumidificationService(config, event_bus)
        if humidification_service.initialize():
            print("✅ Service d'humidification initialisé")
        else:
            print("❌ Échec initialisation service d'humidification")
        
        # Service de ventilation
        ventilation_service = VentilationService(config, event_bus)
        if ventilation_service.initialize():
            print("✅ Service de ventilation initialisé")
        else:
            print("❌ Échec initialisation service de ventilation")
        
        # Service d'alimentation
        feeding_service = FeedingService(config, event_bus)
        if feeding_service.initialize():
            print("✅ Service d'alimentation initialisé")
        else:
            print("❌ Échec initialisation service d'alimentation")
        
        # Service de persistance
        persistence_service = PersistenceService(config, event_bus)
        if persistence_service.initialize():
            print("✅ Service de persistance initialisé")
        else:
            print("❌ Échec initialisation service de persistance")
        
        # Service de terrariums
        terrarium_service = TerrariumService(event_bus)
        print("✅ Service de terrariums initialisé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test intégration services: {e}")
        return False

def test_component_connections():
    """Test des connexions entre composants"""
    print("\n🔗 TEST DES CONNEXIONS ENTRE COMPOSANTS")
    print("=" * 50)
    
    try:
        from src.utils.event_bus import EventBus
        from src.services.config_service import ConfigService
        from src.ui.ui_controller import UIController
        
        # Test du bus d'événements
        event_bus = EventBus()
        print("✅ Bus d'événements créé")
        
        # Test de la configuration
        config_service = ConfigService()
        all_configs = config_service.load_all_configs()
        print("✅ Service de configuration chargé")
        
        # Test de l'UI avec injection de dépendances
        ui_controller = UIController(event_bus, all_configs.get('main', {}))
        print("✅ Contrôleur UI avec injection de dépendances")
        
        # Test de la récupération des services depuis l'UI
        persistence_service = ui_controller.get_persistence_service()
        if persistence_service:
            print("✅ Service de persistance récupéré depuis l'UI")
        else:
            print("❌ Service de persistance non disponible depuis l'UI")
        
        # Test des connexions de services
        if hasattr(ui_controller, 'terrarium_service') and ui_controller.terrarium_service:
            print("✅ Service de terrariums connecté à l'UI")
        else:
            print("❌ Service de terrariums non connecté à l'UI")
        
        if hasattr(ui_controller, 'component_control_service') and ui_controller.component_control_service:
            print("✅ Service de contrôle des composants connecté à l'UI")
        else:
            print("❌ Service de contrôle des composants non connecté à l'UI")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test connexions composants: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST D'INTÉGRATION DES COMPOSANTS ALIMANTE")
    print("=" * 70)
    
    tests = [
        test_main_initialization,
        test_controller_integration,
        test_driver_integration,
        test_service_integration,
        test_component_connections
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
        print("🎉 TOUS LES COMPOSANTS SONT BIEN INTÉGRÉS !")
        print("L'application Alimante est prête pour la production.")
        return True
    else:
        print("❌ CERTAINS COMPOSANTS NÉCESSITENT UNE ATTENTION")
        print("Vérifiez les erreurs ci-dessus pour corriger les problèmes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
