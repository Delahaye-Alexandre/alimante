class AlimanteException(Exception):
    """Base exception class for Alimante"""
    pass

class SensorException(AlimanteException):
    """Raised when sensor readings fail"""
    pass

class ConfigurationException(AlimanteException):
    """Raised when configuration is invalid"""
    pass