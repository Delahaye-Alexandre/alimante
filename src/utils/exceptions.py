class MantcareException(Exception):
    """Base exception class for Mantcare"""
    pass

class SensorException(MantcareException):
    """Raised when sensor readings fail"""
    pass

class ConfigurationException(MantcareException):
    """Raised when configuration is invalid"""
    pass