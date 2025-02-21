import pytest
from unittest.mock import Mock
from main import initialize_system, SystemInitError
from src.utils.config_manager import SystemConfig

# Objets factices pour les contrôleurs
class DummyController:
    def check_status(self):
        return True

# Objets fictifs pour remplacer la connexion série
class DummySerialManager:
    def __init__(self, *args, **kwargs):
        self.connected = True
    def is_connected(self):
        return self.connected

# Fonctions factices pour simuler les contrôleurs
def dummy_temperature_controller(serial_manager, config):
    return DummyController()
def dummy_humidity_controller(serial_manager, config):
    return DummyController()
def dummy_light_controller(serial_manager, config):
    return DummyController()
def dummy_feeding_controller(serial_manager, config):
    return DummyController()

@pytest.fixture(autouse=True)
def patch_controllers(monkeypatch):
    monkeypatch.setattr("mantcare.main.TemperatureController", dummy_temperature_controller)
    monkeypatch.setattr("mantcare.main.HumidityController", dummy_humidity_controller)
    monkeypatch.setattr("mantcare.main.LightController", dummy_light_controller)
    monkeypatch.setattr("mantcare.main.FeedingController", dummy_feeding_controller)
    # Simuler une connexion série réussie
    monkeypatch.setattr("mantcare.main.SerialManager", lambda port, baud_rate, retry_attempts: DummySerialManager())

def test_initialize_system_success():
    config = SystemConfig(
        serial_port="COM3",
        baud_rate=9600,
        temperature={"target": 25, "tolerance": 2},
        humidity={"target": 70, "tolerance": 5},
        location={"latitude": 48.8566, "longitude": 2.3522},
        feeding={"interval_days": 2}
    )
    controllers = initialize_system(config)
    assert "temperature" in controllers
    for ctrl in controllers.values():
        assert ctrl.check_status()

def test_initialize_system_failure(monkeypatch):
    # Simuler échec de connexion série
    dummy_manager = DummySerialManager()
    dummy_manager.connected = False
    monkeypatch.setattr("mantcare.main.SerialManager", lambda port, baud_rate, retry_attempts: dummy_manager)
    
    config = SystemConfig(
        serial_port="COM3",
        baud_rate=9600,
        temperature={"target": 25, "tolerance": 2},
        humidity={"target": 70, "tolerance": 5},
        location={"latitude": 48.8566, "longitude": 2.3522},
        feeding={"interval_days": 2}
    )
    with pytest.raises(SystemInitError):
        initialize_system(config)