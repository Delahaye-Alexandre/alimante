"""
Package des drivers pour Alimante
Contient tous les drivers pour l'interaction avec le matériel
"""

from .base_driver import BaseDriver, DriverConfig, DriverState, DriverError
from .dht22_sensor import DHT22Sensor
from .air_quality_sensor import AirQualitySensor
from .tenflyer_water_sensor import TenflyerWaterSensor
from .pwm_driver import PWMDriver
from .relay_driver import RelayDriver
from .servo_driver import ServoDriver
from .st7735_driver import ST7735Driver
from .rotary_encoder_driver import RotaryEncoderDriver
from .mosfet_driver import MosfetDriver
from .camera_driver import CameraDriver
from .i2c_lcd_driver import I2CLCDDriver
# from .test_drivers import DriverTester  # Fichier non existant

__all__ = [
    'BaseDriver',
    'DriverConfig', 
    'DriverState',
    'DriverError',
    'DHT22Sensor',
    'AirQualitySensor',
    'TenflyerWaterSensor',
    'PWMDriver',
    'RelayDriver',
    'ServoDriver',
    'ST7735Driver',
    'RotaryEncoderDriver',
    'MosfetDriver',
    'CameraDriver',
    'I2CLCDDriver',
    # 'DriverTester'  # Fichier non existant
]

# Version du package
__version__ = "1.0.0"
