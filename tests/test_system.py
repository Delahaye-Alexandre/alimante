import pytest
from unittest.mock import Mock, patch
from src.utils.config_manager import SystemConfig
from main import initialize_system

def test_system_initialization():
    """Test complete system initialization"""
    # Mock configuration
    mock_config = SystemConfig(
        serial_port="COM3",  # Gardé pour compatibilité
        baud_rate=9600,      # Gardé pour compatibilité
        temperature={"optimal": 25, "tolerance": 2, "min": 20, "max": 30},
        humidity={"optimal": 70, "tolerance": 5, "min": 50, "max": 90},
        location={"latitude": 48.8566, "longitude": 2.3522},
        feeding={"interval_days": 2, "feed_count": 1, "prey_type": "drosophila"}
    )
    
    # Test initialization
    with patch('src.utils.gpio_manager.GPIOManager') as mock_gpio:
        mock_gpio_instance = Mock()
        mock_gpio_instance.initialized = True
        mock_gpio.return_value = mock_gpio_instance
        
        controllers = initialize_system(mock_config)
        
        assert len(controllers) == 4
        assert all(c.check_status() for c in controllers.values())
        
        # Verify GPIO manager configuration
        mock_gpio.assert_called_once()