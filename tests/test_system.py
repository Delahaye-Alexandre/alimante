import pytest
from unittest.mock import Mock, patch
from src.utils.config_manager import SystemConfig
from main import initialize_system

def test_system_initialization():
    """Test complete system initialization"""
    # Mock configuration
    mock_config = SystemConfig(
        serial_port="COM3",
        baud_rate=9600,
        temperature={"target": 25, "tolerance": 2},
        humidity={"target": 70, "tolerance": 5},
        location={"latitude": 48.8566, "longitude": 2.3522},
        feeding={"interval_days": 2}
    )
    
    # Test initialization
    with patch('src.utils.SerialManager') as mock_serial:
        controllers = initialize_system(mock_config)
        
        assert len(controllers) == 4
        assert all(c.check_status() for c in controllers.values())
        
        # Verify serial manager configuration
        mock_serial.assert_called_once_with(
            port="COM3",
            baud_rate=9600,
            retry_attempts=3
        )