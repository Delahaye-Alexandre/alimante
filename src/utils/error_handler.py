"""
Middleware de gestion d'erreurs pour FastAPI
Gestion centralisée des erreurs avec logging structuré
"""

import time
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import (
    AlimanteException, 
    ErrorCode, 
    create_exception,
    APIException,
    ValidationException,
    AuthenticationException
)
from .logging_config import get_logger, log_api_request, log_error_with_context


class ErrorHandler:
    """Gestionnaire d'erreurs centralisé pour l'API"""
    
    def __init__(self):
        self.logger = get_logger("api.errors")
    
    async def handle_request(self, request: Request, call_next):
        """Middleware pour gérer les requêtes et mesurer les performances"""
        start_time = time.time()
        
        try:
            # Traitement de la requête
            response = await call_next(request)
            
            # Calcul du temps de réponse
            duration_ms = (time.time() - start_time) * 1000
            
            # Log de la requête
            log_api_request(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            return response
            
        except Exception as e:
            # Calcul du temps avant l'erreur
            duration_ms = (time.time() - start_time) * 1000
            
            # Log de l'erreur
            self.logger.exception(
                f"Erreur API {request.method} {request.url.path}",
                {
                    "method": request.method,
                    "path": str(request.url.path),
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            
            # Retourner une réponse d'erreur appropriée
            return await self.handle_exception(e, request)
    
    async def handle_exception(self, exc: Exception, request: Request) -> JSONResponse:
        """Gère les exceptions et retourne une réponse JSON appropriée"""
        
        # Déterminer le type d'erreur et créer la réponse
        if isinstance(exc, AlimanteException):
            return self._handle_alimante_exception(exc)
        elif isinstance(exc, RequestValidationError):
            return self._handle_validation_error(exc)
        elif isinstance(exc, StarletteHTTPException):
            return self._handle_http_exception(exc)
        else:
            return self._handle_unexpected_error(exc)
    
    def _handle_alimante_exception(self, exc: AlimanteException) -> JSONResponse:
        """Gère les exceptions Alimante personnalisées"""
        error_data = exc.to_dict()
        
        # Déterminer le code HTTP approprié
        http_status = self._get_http_status_from_error_code(exc.error_code)
        
        self.logger.error(
            f"Exception Alimante: {exc.message}",
            {
                "error_code": exc.error_code.value,
                "error_name": exc.error_code.name,
                "context": exc.context,
                "http_status": http_status
            }
        )
        
        return JSONResponse(
            status_code=http_status,
            content={
                "error": error_data,
                "timestamp": time.time()
            }
        )
    
    def _handle_validation_error(self, exc: RequestValidationError) -> JSONResponse:
        """Gère les erreurs de validation Pydantic"""
        validation_exc = create_exception(
            ErrorCode.API_INVALID_REQUEST,
            "Données de requête invalides",
            {"validation_errors": exc.errors()}
        )
        
        self.logger.warning(
            "Erreur de validation des données",
            {
                "validation_errors": exc.errors(),
                "error_code": ErrorCode.API_INVALID_REQUEST.value
            }
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": validation_exc.to_dict(),
                "timestamp": time.time()
            }
        )
    
    def _handle_http_exception(self, exc: StarletteHTTPException) -> JSONResponse:
        """Gère les exceptions HTTP FastAPI"""
        error_data = {
            "error_code": exc.status_code,
            "error_name": "HTTP_EXCEPTION",
            "message": exc.detail,
            "context": {}
        }
        
        self.logger.warning(
            f"Exception HTTP {exc.status_code}: {exc.detail}",
            {
                "status_code": exc.status_code,
                "detail": exc.detail
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": error_data,
                "timestamp": time.time()
            }
        )
    
    def _handle_unexpected_error(self, exc: Exception) -> JSONResponse:
        """Gère les erreurs inattendues"""
        error_data = {
            "error_code": 500,
            "error_name": "INTERNAL_SERVER_ERROR",
            "message": "Erreur interne du serveur",
            "context": {}
        }
        
        self.logger.critical(
            f"Erreur inattendue: {str(exc)}",
            {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc()
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": error_data,
                "timestamp": time.time()
            }
        )
    
    def _get_http_status_from_error_code(self, error_code: ErrorCode) -> int:
        """Mappe les codes d'erreur Alimante vers les codes HTTP"""
        error_code_mapping = {
            # Erreurs système
            ErrorCode.SYSTEM_INIT_FAILED: 500,
            ErrorCode.CONFIGURATION_INVALID: 500,
            ErrorCode.GPIO_INIT_FAILED: 500,
            ErrorCode.SERVICE_UNAVAILABLE: 503,
            
            # Erreurs capteurs
            ErrorCode.SENSOR_READ_FAILED: 500,
            ErrorCode.SENSOR_NOT_FOUND: 404,
            ErrorCode.SENSOR_CALIBRATION_ERROR: 500,
            ErrorCode.TEMPERATURE_OUT_OF_RANGE: 400,
            ErrorCode.HUMIDITY_OUT_OF_RANGE: 400,
            
            # Erreurs contrôleurs
            ErrorCode.CONTROLLER_INIT_FAILED: 500,
            ErrorCode.HEATING_FAILED: 500,
            ErrorCode.COOLING_FAILED: 500,
            ErrorCode.HUMIDITY_CONTROL_FAILED: 500,
            ErrorCode.LIGHTING_CONTROL_FAILED: 500,
            ErrorCode.FEEDING_FAILED: 500,
            
            # Erreurs API
            ErrorCode.API_INVALID_REQUEST: 400,
            ErrorCode.API_UNAUTHORIZED: 401,
            ErrorCode.API_FORBIDDEN: 403,
            ErrorCode.API_NOT_FOUND: 404,
            ErrorCode.API_RATE_LIMIT_EXCEEDED: 429,
            
            # Erreurs données
            ErrorCode.DATA_VALIDATION_FAILED: 400,
            ErrorCode.DATA_NOT_FOUND: 404,
            ErrorCode.DATA_CORRUPTED: 500,
            
            # Erreurs réseau
            ErrorCode.NETWORK_TIMEOUT: 408,
            ErrorCode.NETWORK_CONNECTION_FAILED: 503,
            ErrorCode.WEBSOCKET_CONNECTION_FAILED: 503,
        }
        
        return error_code_mapping.get(error_code, 500)


# Instance globale du gestionnaire d'erreurs
error_handler = ErrorHandler()


def create_error_middleware():
    """Crée le middleware de gestion d'erreurs pour FastAPI"""
    async def error_middleware(request: Request, call_next):
        return await error_handler.handle_request(request, call_next)
    
    return error_middleware


def register_error_handlers(app):
    """Enregistre les gestionnaires d'erreurs sur l'application FastAPI"""
    
    # Gestionnaire pour les exceptions Alimante
    @app.exception_handler(AlimanteException)
    async def alimante_exception_handler(request: Request, exc: AlimanteException):
        return await error_handler.handle_exception(exc, request)
    
    # Gestionnaire pour les erreurs de validation
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await error_handler.handle_exception(exc, request)
    
    # Gestionnaire pour les exceptions HTTP
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return await error_handler.handle_exception(exc, request)
    
    # Gestionnaire pour les exceptions générales
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return await error_handler.handle_exception(exc, request)


# Fonctions utilitaires pour créer des erreurs
def create_api_error(
    error_code: ErrorCode,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> AlimanteException:
    """Crée une exception API avec le bon type"""
    return create_exception(error_code, message, context)


def create_validation_error(field: str, message: str) -> ValidationException:
    """Crée une erreur de validation"""
    return create_exception(
        ErrorCode.API_INVALID_REQUEST,
        f"Erreur de validation pour le champ '{field}': {message}",
        {"field": field, "message": message}
    )


def create_authentication_error(message: str = "Authentification requise") -> AuthenticationException:
    """Crée une erreur d'authentification"""
    return create_exception(
        ErrorCode.API_UNAUTHORIZED,
        message,
        {"auth_required": True}
    ) 