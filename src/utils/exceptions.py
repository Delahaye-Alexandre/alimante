"""
Exceptions centralisées pour Alimante
Système d'exceptions hiérarchisé avec codes d'erreur
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(Enum):
    """Codes d'erreur standardisés"""
    # Erreurs système (1000-1999)
    SYSTEM_INIT_FAILED = 1000
    CONFIGURATION_INVALID = 1001
    GPIO_INIT_FAILED = 1002
    SERVICE_UNAVAILABLE = 1003
    
    # Erreurs capteurs (2000-2999)
    SENSOR_READ_FAILED = 2000
    SENSOR_NOT_FOUND = 2001
    SENSOR_CALIBRATION_ERROR = 2002
    TEMPERATURE_OUT_OF_RANGE = 2003
    HUMIDITY_OUT_OF_RANGE = 2004
    
    # Erreurs contrôleurs (3000-3999)
    CONTROLLER_INIT_FAILED = 3000
    HEATING_FAILED = 3001
    COOLING_FAILED = 3002
    HUMIDITY_CONTROL_FAILED = 3003
    LIGHTING_CONTROL_FAILED = 3004
    FEEDING_FAILED = 3005
    GPIO_SETUP_FAILED = 3006
    
    # Erreurs API (4000-4999)
    API_INVALID_REQUEST = 4000
    API_UNAUTHORIZED = 4001
    API_FORBIDDEN = 4002
    API_NOT_FOUND = 4003
    API_RATE_LIMIT_EXCEEDED = 4004
    
    # Erreurs données (5000-5999)
    DATA_VALIDATION_FAILED = 5000
    DATA_NOT_FOUND = 5001
    DATA_CORRUPTED = 5002
    
    # Erreurs réseau (6000-6999)
    NETWORK_TIMEOUT = 6000
    NETWORK_CONNECTION_FAILED = 6001
    WEBSOCKET_CONNECTION_FAILED = 6002


class AlimanteException(Exception):
    """Exception de base pour Alimante avec code d'erreur et contexte"""
    
    def __init__(
        self, 
        message: str, 
        error_code: ErrorCode,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.original_exception = original_exception
        
        # Message d'erreur complet
        full_message = f"[{error_code.name}] {message}"
        if context:
            full_message += f" | Context: {context}"
        if original_exception:
            full_message += f" | Original: {str(original_exception)}"
            
        super().__init__(full_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'exception en dictionnaire pour l'API"""
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": self.message,
            "context": self.context
        }


# Exceptions système
class SystemException(AlimanteException):
    """Erreurs liées au système"""
    pass


class ConfigurationException(SystemException):
    """Erreurs de configuration"""
    pass


class GPIOException(SystemException):
    """Erreurs GPIO"""
    pass


# Exceptions capteurs
class SensorException(AlimanteException):
    """Erreurs de capteurs"""
    pass


class TemperatureSensorException(SensorException):
    """Erreurs spécifiques au capteur de température"""
    pass


class HumiditySensorException(SensorException):
    """Erreurs spécifiques au capteur d'humidité"""
    pass


# Exceptions contrôleurs
class ControllerException(AlimanteException):
    """Erreurs de contrôleurs"""
    pass


class TemperatureControllerException(ControllerException):
    """Erreurs du contrôleur de température"""
    pass


class HumidityControllerException(ControllerException):
    """Erreurs du contrôleur d'humidité"""
    pass


class LightControllerException(ControllerException):
    """Erreurs du contrôleur d'éclairage"""
    pass


class FeedingControllerException(ControllerException):
    """Erreurs du contrôleur d'alimentation"""
    pass


# Exceptions API
class APIException(AlimanteException):
    """Erreurs API"""
    pass


class ValidationException(APIException):
    """Erreurs de validation des données"""
    pass


class AuthenticationException(APIException):
    """Erreurs d'authentification"""
    pass


# Exceptions données
class DataException(AlimanteException):
    """Erreurs de données"""
    pass


class DatabaseException(DataException):
    """Erreurs de base de données"""
    pass


# Exceptions réseau
class NetworkException(AlimanteException):
    """Erreurs réseau"""
    pass


class WebSocketException(NetworkException):
    """Erreurs WebSocket"""
    pass


def create_exception(
    error_code: ErrorCode,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    original_exception: Optional[Exception] = None
) -> AlimanteException:
    """Factory pour créer des exceptions avec le bon type selon le code d'erreur"""
    
    exception_map = {
        # Système
        ErrorCode.SYSTEM_INIT_FAILED: SystemException,
        ErrorCode.CONFIGURATION_INVALID: ConfigurationException,
        ErrorCode.GPIO_INIT_FAILED: GPIOException,
        
        # Capteurs
        ErrorCode.SENSOR_READ_FAILED: SensorException,
        ErrorCode.TEMPERATURE_OUT_OF_RANGE: TemperatureSensorException,
        ErrorCode.HUMIDITY_OUT_OF_RANGE: HumiditySensorException,
        
        # Contrôleurs
        ErrorCode.CONTROLLER_INIT_FAILED: ControllerException,
        ErrorCode.HEATING_FAILED: TemperatureControllerException,
        ErrorCode.HUMIDITY_CONTROL_FAILED: HumidityControllerException,
        ErrorCode.LIGHTING_CONTROL_FAILED: LightControllerException,
        ErrorCode.FEEDING_FAILED: FeedingControllerException,
        
        # API
        ErrorCode.API_INVALID_REQUEST: ValidationException,
        ErrorCode.API_UNAUTHORIZED: AuthenticationException,
        
        # Données
        ErrorCode.DATA_VALIDATION_FAILED: DataException,
        ErrorCode.DATA_CORRUPTED: DatabaseException,
        
        # Réseau
        ErrorCode.NETWORK_TIMEOUT: NetworkException,
        ErrorCode.WEBSOCKET_CONNECTION_FAILED: WebSocketException,
    }
    
    exception_class = exception_map.get(error_code, AlimanteException)
    return exception_class(message, error_code, context, original_exception)