import pytest
from unittest.mock import Mock
from main import initialize_system, SystemInitError
from src.utils.config_manager import SystemConfig

# Objets factices pour les contrôleurs
class DummyController:
    def check_status(self):
        return True

# Objets fictifs pour remplacer GPIO
class DummyGPIOManager:
    def __init__(self, *args, **kwargs):
        self.initialized = True
    def is_connected(self):
        return self.initialized

# Fonctions factices pour simuler les contrôleurs
def dummy_temperature_controller(gpio_manager, config):
    return DummyController()
def dummy_humidity_controller(gpio_manager, config):
    return DummyController()
def dummy_light_controller(gpio_manager, config):
    return DummyController()
def dummy_feeding_controller(gpio_manager, config):
    return DummyController()

@pytest.fixture(autouse=True)
def patch_controllers(monkeypatch):
    monkeypatch.setattr("main.TemperatureController", dummy_temperature_controller)
    monkeypatch.setattr("main.HumidityController", dummy_humidity_controller)
    monkeypatch.setattr("main.LightController", dummy_light_controller)
    monkeypatch.setattr("main.FeedingController", dummy_feeding_controller)
    # Simuler une connexion GPIO réussie
    monkeypatch.setattr("main.GPIOManager", lambda: DummyGPIOManager())

def test_initialize_system_success():
    config = SystemConfig(
        serial_port="COM3",  # Gardé pour compatibilité
        baud_rate=9600,      # Gardé pour compatibilité
        temperature={"optimal": 25, "tolerance": 2, "min": 20, "max": 30},
        humidity={"optimal": 70, "tolerance": 5, "min": 50, "max": 90},
        location={"latitude": 48.8566, "longitude": 2.3522},
        feeding={"interval_days": 2, "feed_count": 1, "prey_type": "drosophila"}
    )
    controllers = initialize_system(config)
    assert "temperature" in controllers
    assert "humidity" in controllers
    assert "light" in controllers
    assert "feeding" in controllers
    for ctrl in controllers.values():
        assert ctrl.check_status()

def test_initialize_system_failure(monkeypatch):
    # Simuler échec de connexion GPIO
    dummy_manager = DummyGPIOManager()
    dummy_manager.initialized = False
    monkeypatch.setattr("main.GPIOManager", lambda: dummy_manager)
    
    config = SystemConfig(
        serial_port="COM3",
        baud_rate=9600,
        temperature={"optimal": 25, "tolerance": 2, "min": 20, "max": 30},
        humidity={"optimal": 70, "tolerance": 5, "min": 50, "max": 90},
        location={"latitude": 48.8566, "longitude": 2.3522},
        feeding={"interval_days": 2, "feed_count": 1, "prey_type": "drosophila"}
    )
    with pytest.raises(SystemInitError):
        initialize_system(config)