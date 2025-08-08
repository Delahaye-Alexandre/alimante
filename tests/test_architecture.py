#!/usr/bin/env python3
"""
Tests pour l'architecture Alimante
Valide la séparation des couches et les services
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.services.system_service import system_service, SystemMetrics
from src.services.control_service import control_service, ControlResult
from src.services.config_service import config_service
from src.services.sensor_service import sensor_service, SensorReading
from src.utils.exceptions import ErrorCode, create_exception


class MockController:
    """Contrôleur simulé pour les tests"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "ok"
        self.error_count = 0
    
    def get_status(self):
        return {
            "status": self.status,
            "error_count": self.error_count,
            "current_temperature": 25.0,
            "current_humidity": 60.0,
            "heating_active": False,
            "sprayer_active": False
        }
    
    def check_status(self):
        return self.status == "ok"
    
    def control_temperature(self):
        return True
    
    def control_humidity(self):
        return True
    
    def control_lighting(self):
        return True
    
    def control_feeding(self):
        return True
    
    def cleanup(self):
        pass


class MockSensor:
    """Capteur simulé pour les tests"""
    
    def __init__(self, sensor_type: str):
        self.sensor_type = sensor_type
        self.value = 25.0
    
    def read(self):
        return self.value
    
    def get_temperature(self):
        return self.value
    
    def get_humidity(self):
        return 60.0
    
    def cleanup(self):
        pass


def test_system_service():
    """Test le service système"""
    print("🧪 Test service système...")
    
    # Réinitialiser le service
    system_service.controllers.clear()
    system_service.metrics_history.clear()
    system_service.error_history.clear()
    
    # Enregistrer des contrôleurs simulés
    mock_temp = MockController("temperature")
    mock_humidity = MockController("humidity")
    
    system_service.register_controller("temperature", mock_temp)
    system_service.register_controller("humidity", mock_humidity)
    
    # Test récupération statut
    status = system_service.get_system_status()
    assert "controllers" in status
    assert "temperature" in status["controllers"]
    assert "humidity" in status["controllers"]
    
    # Test métriques
    metrics = system_service.get_system_metrics()
    assert isinstance(metrics, SystemMetrics)
    assert metrics.temperature is not None
    assert metrics.humidity is not None
    
    # Test santé système
    health = system_service.get_system_health()
    assert "status" in health
    assert "checks" in health
    
    print("✅ Service système OK")


def test_control_service():
    """Test le service de contrôle"""
    print("🧪 Test service de contrôle...")
    
    # Réinitialiser le service
    control_service.controllers.clear()
    control_service.action_history.clear()
    
    # Enregistrer des contrôleurs simulés
    mock_temp = MockController("temperature")
    mock_humidity = MockController("humidity")
    
    control_service.register_controller("temperature", mock_temp)
    control_service.register_controller("humidity", mock_humidity)
    
    # Test action simple
    result = control_service.execute_control_action("temperature")
    assert "status" in result
    assert result["status"] == "success"
    
    # Test actions multiples
    result = control_service.execute_multiple_actions(["temperature", "humidity"])
    assert "status" in result
    assert "results" in result
    assert "temperature" in result["results"]
    assert "humidity" in result["results"]
    
    # Test statut contrôleurs
    status = control_service.get_all_controllers_status()
    assert "temperature" in status
    assert "humidity" in status
    
    print("✅ Service de contrôle OK")


def test_config_service():
    """Test le service de configuration"""
    print("🧪 Test service de configuration...")
    
    # Créer un dossier temporaire
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        # Créer des fichiers de configuration de test
        os.makedirs("config/orthopteres/mantidae", exist_ok=True)
        
        # Configuration système
        system_config = {
            "serial_port": "/dev/ttyUSB0",
            "baud_rate": 9600,
            "location": {
                "latitude": 48.8566,
                "longitude": 2.3522
            }
        }
        
        with open("config/config.json", "w") as f:
            import json
            json.dump(system_config, f)
        
        # Configuration espèce
        species_config = {
            "temperature": {
                "optimal": 25.0,
                "tolerance": 2.0
            },
            "humidity": {
                "optimal": 60.0,
                "tolerance": 5.0
            },
            "feeding": {
                "interval_hours": 24
            }
        }
        
        with open("config/orthopteres/mantidae/mantis_religiosa.json", "w") as f:
            json.dump(species_config, f)
        
        # Test chargement configuration
        config = config_service.load_config("system")
        assert "serial_port" in config
        assert config["serial_port"] == "/dev/ttyUSB0"
        
        # Test validation configuration
        validation = config_service.validate_config(species_config, "species")
        assert validation["valid"] is True
        
        # Test informations configuration
        info = config_service.get_config_info("system")
        assert info["exists"] is True
        assert info["type"] == "system"
        
        print("✅ Service de configuration OK")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)


def test_sensor_service():
    """Test le service de capteurs"""
    print("🧪 Test service de capteurs...")
    
    # Réinitialiser le service
    sensor_service.sensors.clear()
    sensor_service.readings_history.clear()
    sensor_service.calibrations.clear()
    
    # Enregistrer des capteurs simulés
    mock_temp_sensor = MockSensor("temperature")
    mock_humidity_sensor = MockSensor("humidity")
    
    sensor_service.register_sensor("temp_sensor", "temperature", mock_temp_sensor)
    sensor_service.register_sensor("humidity_sensor", "humidity", mock_humidity_sensor)
    
    # Test lecture capteur
    reading = sensor_service.read_sensor("temp_sensor")
    assert isinstance(reading, SensorReading)
    assert reading.sensor_id == "temp_sensor"
    assert reading.value == 25.0
    assert reading.unit == "°C"
    
    # Test lecture tous les capteurs
    readings = sensor_service.read_all_sensors()
    assert "temp_sensor" in readings
    assert "humidity_sensor" in readings
    
    # Test statut capteur
    status = sensor_service.get_sensor_status("temp_sensor")
    assert "sensor_id" in status
    assert status["sensor_id"] == "temp_sensor"
    
    # Test calibration
    reference_values = [(20.0, 20.0), (30.0, 30.0)]
    success = sensor_service.calibrate_sensor("temp_sensor", reference_values)
    assert success is True
    
    # Test statistiques
    stats = sensor_service.get_sensor_statistics("temp_sensor", hours=1)
    assert "sensor_id" in stats
    assert "statistics" in stats
    
    print("✅ Service de capteurs OK")


def test_service_integration():
    """Test l'intégration des services"""
    print("🧪 Test intégration des services...")
    
    # Réinitialiser tous les services
    system_service.controllers.clear()
    control_service.controllers.clear()
    sensor_service.sensors.clear()
    
    # Créer des contrôleurs/capteurs simulés
    mock_temp = MockController("temperature")
    mock_humidity = MockController("humidity")
    mock_temp_sensor = MockSensor("temperature")
    mock_humidity_sensor = MockSensor("humidity")
    
    # Enregistrer dans les services
    system_service.register_controller("temperature", mock_temp)
    system_service.register_controller("humidity", mock_humidity)
    
    control_service.register_controller("temperature", mock_temp)
    control_service.register_controller("humidity", mock_humidity)
    
    sensor_service.register_sensor("temp_sensor", "temperature", mock_temp_sensor)
    sensor_service.register_sensor("humidity_sensor", "humidity", mock_humidity_sensor)
    
    # Test flux complet
    # 1. Lire les capteurs
    readings = sensor_service.read_all_sensors()
    assert len(readings) == 2
    
    # 2. Récupérer les métriques système
    metrics = system_service.get_system_metrics()
    assert metrics.temperature is not None
    
    # 3. Exécuter des actions de contrôle
    result = control_service.execute_multiple_actions(["temperature", "humidity"])
    assert result["status"] == "success"
    
    # 4. Vérifier le statut système
    status = system_service.get_system_status()
    assert "controllers" in status
    
    print("✅ Intégration des services OK")


def test_error_handling():
    """Test la gestion d'erreurs dans les services"""
    print("🧪 Test gestion d'erreurs...")
    
    # Test service système avec erreur
    try:
        system_service.get_system_status()
    except Exception as e:
        assert isinstance(e, create_exception)
        assert e.error_code == ErrorCode.SERVICE_UNAVAILABLE
    
    # Test service de contrôle avec action inexistante
    try:
        control_service.execute_control_action("inexistant")
    except Exception as e:
        assert isinstance(e, create_exception)
        assert e.error_code == ErrorCode.API_INVALID_REQUEST
    
    # Test service de capteurs avec capteur inexistant
    try:
        sensor_service.read_sensor("inexistant")
    except Exception as e:
        assert isinstance(e, create_exception)
        assert e.error_code == ErrorCode.SENSOR_INIT_FAILED
    
    print("✅ Gestion d'erreurs OK")


def test_service_cleanup():
    """Test le nettoyage des services"""
    print("🧪 Test nettoyage des services...")
    
    # Ajouter des données de test
    mock_controller = MockController("test")
    system_service.register_controller("test", mock_controller)
    control_service.register_controller("test", mock_controller)
    
    mock_sensor = MockSensor("temperature")
    sensor_service.register_sensor("test_sensor", "temperature", mock_sensor)
    
    # Vérifier que les données sont présentes
    assert len(system_service.controllers) > 0
    assert len(control_service.controllers) > 0
    assert len(sensor_service.sensors) > 0
    
    # Nettoyer les services
    system_service.cleanup()
    control_service.cleanup()
    sensor_service.cleanup()
    
    # Vérifier que les données sont vidées
    assert len(system_service.controllers) == 0
    assert len(control_service.controllers) == 0
    assert len(sensor_service.sensors) == 0
    
    print("✅ Nettoyage des services OK")


def main():
    """Exécute tous les tests d'architecture"""
    print("🧪 Tests de l'architecture Alimante")
    print("=" * 60)
    
    tests = [
        ("Service système", test_system_service),
        ("Service de contrôle", test_control_service),
        ("Service de configuration", test_config_service),
        ("Service de capteurs", test_sensor_service),
        ("Intégration des services", test_service_integration),
        ("Gestion d'erreurs", test_error_handling),
        ("Nettoyage des services", test_service_cleanup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        try:
            test_func()
            print(f"✅ {test_name} - PASSÉ")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} - ÉCHOUÉ: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 Tous les tests d'architecture sont passés !")
        print("✅ L'architecture avec services fonctionne correctement.")
        print("\n🏗️ Architecture implémentée:")
        print("   - Service système (métriques, statut, santé)")
        print("   - Service de contrôle (actions, historique)")
        print("   - Service de configuration (chargement, validation)")
        print("   - Service de capteurs (lectures, calibration)")
    else:
        print("⚠️ Certains tests d'architecture ont échoué.")
        print("🔧 Vérifiez les erreurs ci-dessus.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 