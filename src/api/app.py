"""
app.py
API FastAPI pour le système de gestion des mantes
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from src.utils.config_manager import SystemConfig
from src.utils.gpio_manager import GPIOManager
from src.utils.logging_config import get_logger, log_system_start, log_system_stop
from src.utils.error_handler import register_error_handlers, create_api_error
from src.utils.exceptions import ErrorCode, AlimanteException
from src.utils.auth import (
    auth_manager, 
    get_current_user, 
    require_admin, 
    User, 
    UserLogin, 
    Token, 
    create_user_token,
    log_auth_event
)
from src.api.models import (
    ControlRequest,
    FeedingTriggerRequest,
    ConfigUpdateRequest,
    SystemStatusResponse,
    SystemMetrics,
    ControlResponse,
    FeedingResponse,
    ConfigResponse,
    WebSocketMessage,
    StatusUpdateMessage,
    ControlUpdateMessage,
    FeedingUpdateMessage,
    UserResponse,
    ControllerInfo
)
from src.controllers.temperature_controller import TemperatureController
from src.controllers.light_controller import LightController
from src.controllers.humidity_controller import HumidityController
from src.controllers.feeding_controller import FeedingController

# Configuration de l'application
app = FastAPI(
    title="Alimante API",
    description="API sécurisée pour la gestion automatisée des mantes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enregistrement des gestionnaires d'erreurs
register_error_handlers(app)

# CORS pour l'application mobile (sécurisé)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Développement local
        "http://192.168.1.100:3000",  # IP locale
        "https://votre-app-mobile.com"  # Production (à remplacer)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Variables globales
gpio_manager: GPIOManager = None
controllers: Dict[str, Any] = {}
websocket_connections: List[WebSocket] = []
logger = get_logger("api")

@app.on_event("startup")
async def startup_event():
    """Initialise le système au démarrage"""
    global gpio_manager, controllers
    
    try:
        logger.info("🚀 Démarrage de l'API Alimante")
        
        # Initialisation GPIO
        gpio_manager = GPIOManager()
        if not gpio_manager.initialized:
            raise create_api_error(
                ErrorCode.GPIO_INIT_FAILED,
                "Impossible d'initialiser le GPIO",
                {"gpio_status": "failed"}
            )
        
        # Chargement de la configuration
        config = SystemConfig.from_json('config/config.json', 'config/orthopteres/mantidae/mantis_religiosa.json')
        
        # Initialisation des contrôleurs
        controllers = {
            'temperature': TemperatureController(gpio_manager, config.temperature),
            'humidity': HumidityController(gpio_manager, config.humidity),
            'light': LightController(gpio_manager, config.location),
            'feeding': FeedingController(gpio_manager, config.feeding)
        }
        
        # Validation des contrôleurs
        for name, controller in controllers.items():
            if not controller.check_status():
                raise create_api_error(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    f"Échec d'initialisation du contrôleur {name}",
                    {"controller": name, "status": "failed"}
                )
        
        log_system_start()
        logger.info("✅ API Alimante démarrée avec succès")
        
    except AlimanteException:
        # Re-raise les exceptions Alimante
        raise
    except Exception as e:
        logger.exception("💥 Erreur lors du démarrage de l'API")
        raise create_api_error(
            ErrorCode.SYSTEM_INIT_FAILED,
            f"Erreur lors du démarrage: {str(e)}",
            {"original_error": str(e)}
        )

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoie les ressources à l'arrêt"""
    global gpio_manager
    
    logger.info("🛑 Arrêt de l'API Alimante")
    
    # Fermer les connexions WebSocket
    for websocket in websocket_connections:
        try:
            await websocket.close()
        except Exception as e:
            logger.warning(f"Erreur lors de la fermeture WebSocket: {e}")
    
    # Nettoyer GPIO
    if gpio_manager:
        try:
            gpio_manager.cleanup()
            logger.info("✅ GPIO nettoyé")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage GPIO: {e}")
    
    log_system_stop()

async def broadcast_to_websockets(message: WebSocketMessage):
    """Envoie un message à tous les clients WebSocket connectés"""
    if not websocket_connections:
        return
        
    message_json = message.json()
    disconnected = []
    
    for websocket in websocket_connections:
        try:
            await websocket.send_text(message_json)
        except Exception as e:
            logger.warning(f"Erreur WebSocket: {e}")
            disconnected.append(websocket)
    
    # Nettoyer les connexions déconnectées
    for websocket in disconnected:
        websocket_connections.remove(websocket)
    
    if disconnected:
        logger.info(f"🧹 {len(disconnected)} connexions WebSocket nettoyées")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour les mises à jour en temps réel"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    logger.info("🔌 Nouvelle connexion WebSocket", {
        "total_connections": len(websocket_connections)
    })
    
    try:
        while True:
            # Envoi périodique des données
            status_data = await get_system_status()
            status_message = StatusUpdateMessage(
                data=status_data
            )
            await websocket.send_text(status_message.json())
            await asyncio.sleep(5)  # Mise à jour toutes les 5 secondes
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("🔌 Client WebSocket déconnecté", {
            "remaining_connections": len(websocket_connections)
        })
    except Exception as e:
        logger.exception("💥 Erreur WebSocket")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# Endpoints d'authentification
@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authentification utilisateur"""
    try:
        user = auth_manager.authenticate_user(user_credentials.username, user_credentials.password)
        if not user:
            log_auth_event("login_failed", user_credentials.username, False)
            raise create_api_error(
                ErrorCode.API_UNAUTHORIZED,
                "Nom d'utilisateur ou mot de passe incorrect"
            )
        
        token = create_user_token(user)
        log_auth_event("login_success", user.username, True)
        
        return token
        
    except AlimanteException:
        raise
    except Exception as e:
        logger.exception("💥 Erreur lors de l'authentification")
        raise create_api_error(
            ErrorCode.API_UNAUTHORIZED,
            "Erreur lors de l'authentification",
            {"original_error": str(e)}
        )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur connecté"""
    return UserResponse(
        username=current_user.username,
        email=current_user.email,
        is_admin=current_user.is_admin,
        is_active=current_user.is_active
    )

# Endpoints publics (sans authentification)
@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "Alimante API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs"
    }

@app.get("/api/health")
async def health_check():
    """Vérification de santé du système"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Endpoints protégés (avec authentification)
@app.get("/api/status", response_model=SystemStatusResponse)
async def get_system_status(current_user: User = Depends(get_current_user)):
    """Retourne le statut complet du système"""
    try:
        status = SystemStatusResponse(
            status="online",
            controllers={}
        )
        
        # Statut de chaque contrôleur
        for name, controller in controllers.items():
            try:
                if hasattr(controller, 'get_status'):
                    controller_status = controller.get_status()
                    status.controllers[name] = ControllerInfo(
                        name=name,
                        status="active" if controller_status.get("status") == "ok" else "error",
                        last_update=datetime.now(),
                        error_count=controller_status.get("error_count", 0),
                        metadata=controller_status
                    )
                else:
                    status.controllers[name] = ControllerInfo(
                        name=name,
                        status="unknown",
                        last_update=datetime.now()
                    )
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération du statut {name}: {e}")
                status.controllers[name] = ControllerInfo(
                    name=name,
                    status="error",
                    last_update=datetime.now(),
                    error_count=1
                )
        
        return status
        
    except Exception as e:
        logger.exception("💥 Erreur lors de la récupération du statut")
        raise create_api_error(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Impossible de récupérer le statut du système",
            {"original_error": str(e)}
        )

@app.get("/api/metrics", response_model=SystemMetrics)
async def get_metrics(current_user: User = Depends(get_current_user)):
    """Récupère les métriques des capteurs"""
    try:
        metrics = SystemMetrics()
        
        # Température
        if 'temperature' in controllers:
            try:
                temp_status = controllers['temperature'].get_status()
                metrics.temperature = {
                    'current': temp_status.get('current_temperature'),
                    'optimal': temp_status.get('optimal_temperature'),
                    'heating_active': temp_status.get('heating_active')
                }
            except Exception as e:
                logger.warning(f"Erreur métriques température: {e}")
                metrics.temperature = {"error": str(e)}
        
        # Humidité
        if 'humidity' in controllers:
            try:
                humidity_status = controllers['humidity'].get_status()
                metrics.humidity = {
                    'current': humidity_status.get('current_humidity'),
                    'optimal': humidity_status.get('optimal_humidity'),
                    'sprayer_active': humidity_status.get('sprayer_active')
                }
            except Exception as e:
                logger.warning(f"Erreur métriques humidité: {e}")
                metrics.humidity = {"error": str(e)}
        
        return metrics
        
    except Exception as e:
        logger.exception("💥 Erreur lors de la récupération des métriques")
        raise create_api_error(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Impossible de récupérer les métriques",
            {"original_error": str(e)}
        )

@app.post("/api/control", response_model=ControlResponse)
async def control_system(
    control_request: ControlRequest,
    current_user: User = Depends(get_current_user)
):
    """Contrôle les systèmes"""
    try:
        results = {}
        errors = []
        
        # Contrôle température
        if "temperature" in control_request.actions:
            try:
                if controllers['temperature'].control_temperature():
                    results['temperature'] = "controlled"
                else:
                    results['temperature'] = "error"
                    errors.append("Échec contrôle température")
            except Exception as e:
                logger.error(f"Erreur contrôle température: {e}")
                results['temperature'] = "error"
                errors.append(f"Erreur contrôle température: {str(e)}")
        
        # Contrôle humidité
        if "humidity" in control_request.actions:
            try:
                if controllers['humidity'].control_humidity():
                    results['humidity'] = "controlled"
                else:
                    results['humidity'] = "error"
                    errors.append("Échec contrôle humidité")
            except Exception as e:
                logger.error(f"Erreur contrôle humidité: {e}")
                results['humidity'] = "error"
                errors.append(f"Erreur contrôle humidité: {str(e)}")
        
        # Contrôle éclairage
        if "light" in control_request.actions:
            try:
                if controllers['light'].control_lighting():
                    results['light'] = "controlled"
                else:
                    results['light'] = "error"
                    errors.append("Échec contrôle éclairage")
            except Exception as e:
                logger.error(f"Erreur contrôle éclairage: {e}")
                results['light'] = "error"
                errors.append(f"Erreur contrôle éclairage: {str(e)}")
        
        # Contrôle alimentation
        if "feeding" in control_request.actions:
            try:
                if controllers['feeding'].control_feeding():
                    results['feeding'] = "controlled"
                else:
                    results['feeding'] = "error"
                    errors.append("Échec contrôle alimentation")
            except Exception as e:
                logger.error(f"Erreur contrôle alimentation: {e}")
                results['feeding'] = "error"
                errors.append(f"Erreur contrôle alimentation: {str(e)}")
        
        # Broadcast aux clients WebSocket
        control_message = ControlUpdateMessage(
            data=ControlResponse(
                status="success" if not errors else "partial_success",
                results=results,
                errors=errors if errors else None
            )
        )
        await broadcast_to_websockets(control_message)
        
        logger.info("🎛️ Contrôle système exécuté", {
            "user": current_user.username,
            "actions": control_request.actions,
            "results": results
        })
        
        return ControlResponse(
            status="success" if not errors else "partial_success",
            results=results,
            errors=errors if errors else None
        )
        
    except AlimanteException:
        raise
    except Exception as e:
        logger.exception("💥 Erreur lors du contrôle système")
        raise create_api_error(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Erreur lors du contrôle système",
            {"original_error": str(e)}
        )

@app.post("/api/feeding/trigger", response_model=FeedingResponse)
async def trigger_feeding(
    feeding_request: FeedingTriggerRequest,
    current_user: User = Depends(get_current_user)
):
    """Déclenche manuellement l'alimentation"""
    try:
        if 'feeding' not in controllers:
            raise create_api_error(
                ErrorCode.API_NOT_FOUND,
                "Contrôleur d'alimentation non disponible"
            )
        
        success = controllers['feeding'].trigger_feeding()
        
        feeding_message = FeedingUpdateMessage(
            data=FeedingResponse(
                status="success" if success else "error",
                success=success,
                quantity_dispensed=feeding_request.quantity if success else None
            )
        )
        await broadcast_to_websockets(feeding_message)
        
        logger.info("🍽️ Alimentation déclenchée", {
            "user": current_user.username,
            "success": success,
            "quantity": feeding_request.quantity
        })
        
        return FeedingResponse(
            status="success" if success else "error",
            success=success,
            quantity_dispensed=feeding_request.quantity if success else None
        )
        
    except AlimanteException:
        raise
    except Exception as e:
        logger.exception("💥 Erreur lors du déclenchement de l'alimentation")
        raise create_api_error(
            ErrorCode.FEEDING_FAILED,
            "Erreur lors du déclenchement de l'alimentation",
            {"original_error": str(e)}
        )

@app.get("/api/config", response_model=ConfigResponse)
async def get_config(current_user: User = Depends(get_current_user)):
    """Retourne la configuration actuelle"""
    try:
        config = SystemConfig.from_json('config/config.json', 'config/orthopteres/mantidae/mantis_religiosa.json')
        return ConfigResponse(
            temperature=config.temperature,
            humidity=config.humidity,
            feeding=config.feeding,
            lighting={},  # À implémenter
            location=config.location
        )
    except Exception as e:
        logger.exception("💥 Erreur lors de la récupération de la configuration")
        raise create_api_error(
            ErrorCode.CONFIGURATION_INVALID,
            "Impossible de récupérer la configuration",
            {"original_error": str(e)}
        )

# Endpoints administrateur
@app.put("/api/config", response_model=ConfigResponse)
async def update_config(
    config_update: ConfigUpdateRequest,
    admin_user: User = Depends(require_admin)
):
    """Met à jour la configuration (admin uniquement)"""
    try:
        # Ici on pourrait sauvegarder la configuration
        logger.info("⚙️ Configuration mise à jour", {
            "user": admin_user.username,
            "updates": config_update.dict(exclude_none=True)
        })
        
        # Retourner la configuration actuelle
        config = SystemConfig.from_json('config/config.json', 'config/orthopteres/mantidae/mantis_religiosa.json')
        return ConfigResponse(
            temperature=config.temperature,
            humidity=config.humidity,
            feeding=config.feeding,
            lighting={},
            location=config.location
        )
        
    except Exception as e:
        logger.exception("💥 Erreur lors de la mise à jour de la configuration")
        raise create_api_error(
            ErrorCode.CONFIGURATION_INVALID,
            "Erreur lors de la mise à jour de la configuration",
            {"original_error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)