import json
import pytest
from unittest.mock import Mock
from src.controllers.temperature_controller import TemperatureController
from src.utils.config_manager import SystemConfig

def test_temperature_control():
    mock_serial = Mock()
    mock_config = {'target_temp': 25, 'tolerance': 2}
    
    controller = TemperatureController(mock_serial, mock_config)
    controller.control_temperature()
    
    mock_serial.send_command.assert_called_once()

def test_from_json_valid(tmp_path):
    config_data = {
        "serial_port": "COM3",
        "baud_rate": 9600,
        "temperature": {"target": 25, "tolerance": 2},
        "humidity": {"target": 70, "tolerance": 5},
        "location": {"latitude": 48.8566, "longitude": 2.3522},
        "feeding": {"interval_days": 2}
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))
    config = SystemConfig.from_json(str(config_file))
    assert config.serial_port == "COM3"
    assert config.temperature["target"] == 25

def test_from_json_invalid(tmp_path):
    config_file = tmp_path / "bad_config.json"
    config_file.write_text("ce n'est pas un json")
    with pytest.raises(Exception):
        SystemConfig.from_json(str(config_file))