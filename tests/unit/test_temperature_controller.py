import json
import pytest
from unittest.mock import Mock
from src.controllers.temperature_controller import TemperatureController
from src.utils.config_manager import SystemConfig

def test_temperature_control():
    mock_gpio = Mock()
    mock_gpio.initialized = True
    mock_config = {
        'optimal': 25, 
        'tolerance': 2,
        'min': 20,
        'max': 30
    }
    
    controller = TemperatureController(mock_gpio, mock_config)
    result = controller.control_temperature()
    
    # Vérifier que le contrôle a été effectué
    assert isinstance(result, bool)

def test_temperature_reading():
    mock_gpio = Mock()
    mock_gpio.initialized = True
    mock_config = {
        'optimal': 25, 
        'tolerance': 2,
        'min': 20,
        'max': 30
    }
    
    controller = TemperatureController(mock_gpio, mock_config)
    temp = controller.read_temperature()
    
    # Vérifier que la température est lue (simulation)
    assert temp is not None
    assert 18 <= temp <= 22  # Plage de simulation

def test_temperature_status():
    mock_gpio = Mock()
    mock_gpio.initialized = True
    mock_config = {
        'optimal': 25, 
        'tolerance': 2,
        'min': 20,
        'max': 30
    }
    
    controller = TemperatureController(mock_gpio, mock_config)
    status = controller.get_status()
    
    # Vérifier la structure du statut
    assert 'current_temperature' in status
    assert 'optimal_temperature' in status
    assert 'heating_active' in status
    assert 'status' in status

def test_from_json_valid(tmp_path):
    config_data = {
        "serial_port": "COM3",
        "baud_rate": 9600,
        "temperature": {"optimal": 25, "tolerance": 2, "min": 20, "max": 30},
        "humidity": {"optimal": 70, "tolerance": 5, "min": 50, "max": 90},
        "location": {"latitude": 48.8566, "longitude": 2.3522},
        "feeding": {"interval_days": 2, "feed_count": 1, "prey_type": "drosophila"}
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))
    config = SystemConfig.from_json(str(config_file))
    assert config.serial_port == "COM3"
    assert config.temperature["optimal"] == 25

def test_from_json_invalid(tmp_path):
    config_file = tmp_path / "bad_config.json"
    config_file.write_text("ce n'est pas un json")
    with pytest.raises(Exception):
        SystemConfig.from_json(str(config_file))