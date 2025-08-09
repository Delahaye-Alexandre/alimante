"""
app.py
API FastAPI pour le système de gestion des mantes
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import asyncio
import io
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
    UserResponse,
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
    ControllerInfo
)
# Import des contrôleurs
from src.controllers.temperature_controller import TemperatureController
from src.controllers.light_controller import LightController
from src.controllers.humidity_controller import HumidityController
from src.controllers.feeding_controller import FeedingController
from src.controllers.fan_controller import FanController
from src.controllers.ultrasonic_mist_controller import UltrasonicMistController
from src.controllers.air_quality_controller import AirQualityController
from src.controllers.lcd_menu_controller import LCDMenuController
from src.controllers.camera_controller import CameraController
from src.controllers.water_level_controller import WaterLevelController
from src.controllers.radiator_temp_controller import RadiatorTempController

# Import des services
from src.services.system_service import system_service
from src.services.control_service import control_service
from src.services.config_service import config_service
from src.services.sensor_service import sensor_service

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
        
        # Chargement de la configuration via le service
        config = config_service.load_system_config()
        
        # Initialisation des contrôleurs
        controllers = {
            'temperature': TemperatureController(gpio_manager, config.temperature),
            'humidity': HumidityController(gpio_manager, config.humidity),
            'light': LightController(gpio_manager, config.location),
            'feeding': FeedingController(gpio_manager, config.feeding),
            'fan': FanController(gpio_manager, config.get("fan", {})),
            'ultrasonic_mist': UltrasonicMistController(gpio_manager, config.get("ultrasonic_mist", {})),
            'air_quality': AirQualityController(gpio_manager, config.get("air_quality", {})),
            'lcd_menu': LCDMenuController(gpio_manager, config.get("lcd_config", {})),
            'camera': CameraController(config.get("camera_config", {})),
            'water_level': WaterLevelController(gpio_manager, config.get("water_level_sensor", {})),
            'radiator_temp': RadiatorTempController(gpio_manager, config.get("radiator_temp_sensor", {}))
        }
        
        # Enregistrer les contrôleurs dans les services
        for name, controller in controllers.items():
            system_service.register_controller(name, controller)
            control_service.register_controller(name, controller)
        
        # Enregistrer les capteurs dans le service de capteurs
        sensor_service.register_sensor("temperature", "temperature", controllers['temperature'])
        sensor_service.register_sensor("humidity", "humidity", controllers['humidity'])
        sensor_service.register_sensor("light", "light", controllers['light'])
        sensor_service.register_sensor("air_quality", "air_quality", controllers['air_quality'])
        sensor_service.register_sensor("water_level", "water_level", controllers['water_level'])
        sensor_service.register_sensor("radiator_temp", "radiator_temp", controllers['radiator_temp'])
        
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
    
    # Nettoyer les services
    system_service.cleanup()
    control_service.cleanup()
    config_service.cleanup()
    sensor_service.cleanup()
    
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
        # Utiliser le service système
        status_data = system_service.get_system_status()
        
        # Convertir en format de réponse API
        status = SystemStatusResponse(
            status="online",
            controllers={}
        )
        
        # Convertir les contrôleurs
        for name, controller_data in status_data["controllers"].items():
            status.controllers[name] = ControllerInfo(
                name=name,
                status=controller_data["status"],
                last_update=datetime.fromisoformat(controller_data["last_update"]),
                error_count=controller_data.get("error_count", 0),
                metadata=controller_data.get("metadata")
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
        # Utiliser le service système pour les métriques
        metrics_data = system_service.get_system_metrics()
        
        # Convertir en format de réponse API
        metrics = SystemMetrics(
            temperature={
                'current': metrics_data.temperature,
                'heating_active': metrics_data.heating_active,
                'cooling_active': metrics_data.cooling_active
            } if metrics_data.temperature is not None else None,
            humidity={
                'current': metrics_data.humidity,
                'humidifier_active': metrics_data.humidifier_active
            } if metrics_data.humidity is not None else None,
            lighting={
                'level': metrics_data.light_level,
                'light_on': metrics_data.light_on
            } if metrics_data.light_level is not None else None,
            feeding={
                'last_feeding': metrics_data.feeding_last.isoformat() if metrics_data.feeding_last else None,
                'next_feeding': metrics_data.feeding_next.isoformat() if metrics_data.feeding_next else None
            } if metrics_data.feeding_last or metrics_data.feeding_next else None
        )
        
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
        # Utiliser le service de contrôle
        action_names = [action.value for action in control_request.actions]
        result = control_service.execute_multiple_actions(action_names, control_request.parameters)
        
        # Broadcast aux clients WebSocket
        control_message = ControlUpdateMessage(
            data=ControlResponse(
                status=result["status"],
                results=result["results"],
                errors=result.get("errors")
            )
        )
        await broadcast_to_websockets(control_message)
        
        logger.info("🎛️ Contrôle système exécuté", {
            "user": current_user.username,
            "actions": action_names,
            "results": result["results"]
        })
        
        return ControlResponse(
            status=result["status"],
            results=result["results"],
            errors=result.get("errors")
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
        # Utiliser le service de contrôle
        result = control_service.execute_control_action("feeding", {
            "quantity": feeding_request.quantity,
            "force": feeding_request.force
        })
        
        feeding_message = FeedingUpdateMessage(
            data=FeedingResponse(
                status="success" if result["status"] == "success" else "error",
                success=result["status"] == "success",
                quantity_dispensed=feeding_request.quantity if result["status"] == "success" else None
            )
        )
        await broadcast_to_websockets(feeding_message)
        
        logger.info("🍽️ Alimentation déclenchée", {
            "user": current_user.username,
            "success": result["status"] == "success",
            "quantity": feeding_request.quantity
        })
        
        return FeedingResponse(
            status="success" if result["status"] == "success" else "error",
            success=result["status"] == "success",
            quantity_dispensed=feeding_request.quantity if result["status"] == "success" else None
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
        # Utiliser le service de configuration
        config = config_service.load_system_config()
        
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
        # Utiliser le service de configuration
        if config_update.temperature:
            config_service.update_config_section("species", "temperature", config_update.temperature)
        
        if config_update.humidity:
            config_service.update_config_section("species", "humidity", config_update.humidity)
        
        if config_update.feeding:
            config_service.update_config_section("species", "feeding", config_update.feeding)
        
        if config_update.lighting:
            config_service.update_config_section("species", "lighting", config_update.lighting)
        
        logger.info("⚙️ Configuration mise à jour", {
            "user": admin_user.username,
            "updates": config_update.dict(exclude_none=True)
        })
        
        # Retourner la configuration actuelle
        config = config_service.load_system_config()
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

# Nouveaux endpoints pour les services
@app.get("/api/system/health")
async def get_system_health(current_user: User = Depends(get_current_user)):
    """Récupère la santé du système"""
    try:
        return system_service.get_system_health()
    except Exception as e:
        logger.exception("💥 Erreur lors de la récupération de la santé du système")
        raise create_api_error(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Impossible de récupérer la santé du système",
            {"original_error": str(e)}
        )

@app.get("/api/sensors/status")
async def get_sensors_status(current_user: User = Depends(get_current_user)):
    """Récupère le statut de tous les capteurs"""
    try:
        sensors_status = {}
        for sensor_id in sensor_service.sensors.keys():
            sensors_status[sensor_id] = sensor_service.get_sensor_status(sensor_id)
        return {"sensors": sensors_status}
    except Exception as e:
        logger.exception("💥 Erreur lors de la récupération du statut des capteurs")
        raise create_api_error(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Impossible de récupérer le statut des capteurs",
            {"original_error": str(e)}
        )

@app.get("/api/sensors/{sensor_id}/statistics")
async def get_sensor_statistics(
    sensor_id: str,
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """Récupère les statistiques d'un capteur"""
    try:
        return sensor_service.get_sensor_statistics(sensor_id, hours)
    except Exception as e:
        logger.exception(f"💥 Erreur lors de la récupération des statistiques du capteur {sensor_id}")
        raise create_api_error(
            ErrorCode.SERVICE_UNAVAILABLE,
            f"Impossible de récupérer les statistiques du capteur {sensor_id}",
            {"original_error": str(e)}
        )

@app.post("/api/sensors/{sensor_id}/calibrate")
async def calibrate_sensor(
    sensor_id: str,
    reference_values: List[Dict[str, float]],
    current_user: User = Depends(require_admin)
):
    """Calibre un capteur (admin uniquement)"""
    try:
        # Convertir les données en tuples
        calibration_points = [(point["raw"], point["expected"]) for point in reference_values]
        
        success = sensor_service.calibrate_sensor(sensor_id, calibration_points)
        
        logger.info(f"🔧 Capteur calibré: {sensor_id}", {
            "user": current_user.username,
            "points_count": len(calibration_points)
        })
        
        return {"success": success, "sensor_id": sensor_id}
        
    except Exception as e:
        logger.exception(f"💥 Erreur lors de la calibration du capteur {sensor_id}")
        raise create_api_error(
            ErrorCode.SENSOR_CALIBRATION_FAILED,
            f"Erreur lors de la calibration du capteur {sensor_id}",
            {"original_error": str(e)}
        )

@app.get("/api/config/info")
async def get_config_info(current_user: User = Depends(get_current_user)):
    """Récupère les informations sur toutes les configurations"""
    try:
        return config_service.get_all_configs_info()
    except Exception as e:
        logger.exception("💥 Erreur lors de la récupération des informations de configuration")
        raise create_api_error(
            ErrorCode.CONFIGURATION_INVALID,
            "Impossible de récupérer les informations de configuration",
            {"original_error": str(e)}
        )

# Endpoints pour la qualité de l'air
@app.get("/api/air-quality/status")
async def get_air_quality_status(current_user: User = Depends(get_current_user)):
    """Récupère le statut de la qualité de l'air"""
    try:
        if 'air_quality' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur de qualité de l'air non disponible",
                {"controller": "air_quality"}
            )
        
        status = controllers['air_quality'].get_status()
        return {"air_quality": status}
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_READ_FAILED,
            "Impossible de récupérer le statut de la qualité de l'air",
            {"original_error": str(e)}
        )

@app.post("/api/air-quality/control-ventilation")
async def control_ventilation_with_air_quality(current_user: User = Depends(require_admin)):
    """Contrôle la ventilation basée sur la qualité de l'air"""
    try:
        if 'air_quality' not in controllers or 'fan' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleurs air_quality ou fan non disponibles",
                {"controllers": ["air_quality", "fan"]}
            )
        
        success = controllers['air_quality'].control_ventilation(controllers['fan'])
        return {"success": success, "message": "Contrôle ventilation basé sur la qualité de l'air"}
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible de contrôler la ventilation basée sur la qualité de l'air",
            {"original_error": str(e)}
        )

@app.post("/api/air-quality/calibrate")
async def calibrate_air_quality_sensor(current_user: User = Depends(require_admin)):
    """Calibre le capteur de qualité de l'air"""
    try:
        if 'air_quality' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur de qualité de l'air non disponible",
                {"controller": "air_quality"}
            )
        
        success = controllers['air_quality'].calibrate_sensor()
        return {"calibrated": success, "message": "Calibration du capteur de qualité de l'air"}
    except Exception as e:
        raise create_api_error(
            ErrorCode.SENSOR_CALIBRATION_FAILED,
            "Impossible de calibrer le capteur de qualité de l'air",
            {"original_error": str(e)}
        )

# Endpoints pour le contrôleur LCD Menu
@app.get("/api/lcd-menu/status")
async def get_lcd_menu_status(current_user: User = Depends(get_current_user)):
    """Récupère le statut du contrôleur LCD menu"""
    try:
        if 'lcd_menu' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur LCD menu non disponible",
                {"controller": "lcd_menu"}
            )
        
        status = controllers['lcd_menu'].get_status()
        return {"lcd_menu": status}
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_READ_FAILED,
            "Impossible de récupérer le statut du contrôleur LCD menu",
            {"original_error": str(e)}
        )

@app.post("/api/lcd-menu/navigate")
async def navigate_lcd_menu(
    direction: str,
    current_user: User = Depends(get_current_user)
):
    """Navigation dans le menu LCD"""
    try:
        if 'lcd_menu' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur LCD menu non disponible",
                {"controller": "lcd_menu"}
            )
        
        # Simulation de navigation (les boutons physiques gèrent déjà la navigation)
        return {"success": True, "message": f"Navigation {direction} simulée"}
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible de naviguer dans le menu LCD",
            {"original_error": str(e)}
        )

@app.post("/api/lcd-menu/select")
async def select_lcd_menu_item(current_user: User = Depends(get_current_user)):
    """Sélectionne l'élément actuel du menu LCD"""
    try:
        if 'lcd_menu' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur LCD menu non disponible",
                {"controller": "lcd_menu"}
            )
        
        # Simulation de sélection (les boutons physiques gèrent déjà la sélection)
        return {"success": True, "message": "Sélection simulée"}
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible de sélectionner l'élément du menu LCD",
            {"original_error": str(e)}
        )

# Endpoints pour le contrôleur de brumisateur ultrasonique
@app.get("/api/ultrasonic-mist/status")
async def get_ultrasonic_mist_status(current_user: User = Depends(get_current_user)):
    """Récupère le statut du brumisateur ultrasonique"""
    try:
        if 'ultrasonic_mist' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur brumisateur ultrasonique non disponible",
                {"controller": "ultrasonic_mist"}
            )
        
        status = controllers['ultrasonic_mist'].get_status()
        return {"ultrasonic_mist": status}
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_READ_FAILED,
            "Impossible de récupérer le statut du brumisateur ultrasonique",
            {"original_error": str(e)}
        )

@app.post("/api/ultrasonic-mist/activate")
async def activate_ultrasonic_mist(
    intensity: int = 50,
    duration: Optional[float] = None,
    current_user: User = Depends(get_current_user)
):
    """Active le brumisateur ultrasonique"""
    try:
        if 'ultrasonic_mist' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur brumisateur ultrasonique non disponible",
                {"controller": "ultrasonic_mist"}
            )
        
        success = controllers['ultrasonic_mist'].activate_mist(intensity, duration)
        return {
            "success": success,
            "message": f"Brumisateur activé avec intensité {intensity}%",
            "duration": duration
        }
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible d'activer le brumisateur ultrasonique",
            {"original_error": str(e)}
        )

@app.post("/api/ultrasonic-mist/deactivate")
async def deactivate_ultrasonic_mist(current_user: User = Depends(get_current_user)):
    """Désactive le brumisateur ultrasonique"""
    try:
        if 'ultrasonic_mist' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur brumisateur ultrasonique non disponible",
                {"controller": "ultrasonic_mist"}
            )
        
        success = controllers['ultrasonic_mist'].deactivate_mist()
        return {
            "success": success,
            "message": "Brumisateur désactivé"
        }
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible de désactiver le brumisateur ultrasonique",
            {"original_error": str(e)}
        )

@app.post("/api/ultrasonic-mist/mode/{mode_name}")
async def run_mist_mode(
    mode_name: str,
    current_user: User = Depends(get_current_user)
):
    """Exécute un mode d'humidification prédéfini"""
    try:
        if 'ultrasonic_mist' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur brumisateur ultrasonique non disponible",
                {"controller": "ultrasonic_mist"}
            )
        
        success = controllers['ultrasonic_mist'].run_mist_mode(mode_name)
        return {
            "success": success,
            "message": f"Mode {mode_name} exécuté",
            "mode": mode_name
        }
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            f"Impossible d'exécuter le mode {mode_name}",
            {"original_error": str(e)}
        )

@app.post("/api/ultrasonic-mist/emergency-stop")
async def emergency_stop_mist(current_user: User = Depends(get_current_user)):
    """Arrêt d'urgence du brumisateur ultrasonique"""
    try:
        if 'ultrasonic_mist' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur brumisateur ultrasonique non disponible",
                {"controller": "ultrasonic_mist"}
            )
        
        success = controllers['ultrasonic_mist'].emergency_stop()
        return {
            "success": success,
            "message": "Arrêt d'urgence du brumisateur effectué"
        }
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible d'arrêter le brumisateur en urgence",
            {"original_error": str(e)}
        )

# Endpoints pour le niveau d'eau
@app.get("/api/water-level/status")
async def get_water_level_status(current_user: User = Depends(get_current_user)):
    """Récupère le statut du capteur de niveau d'eau"""
    try:
        if 'water_level' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur niveau d'eau non disponible",
                {"controller": "water_level"}
            )
        
        status = controllers['water_level'].get_status()
        return {"water_level": status}
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_READ_FAILED,
            "Impossible de récupérer le statut du niveau d'eau",
            {"original_error": str(e)}
        )

@app.get("/api/water-level/read")
async def read_water_level(current_user: User = Depends(get_current_user)):
    """Lit le niveau d'eau actuel"""
    try:
        if 'water_level' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur niveau d'eau non disponible",
                {"controller": "water_level"}
            )
        
        level_data = controllers['water_level'].read_water_level()
        return {"water_level_data": level_data}
    except Exception as e:
        raise create_api_error(
            ErrorCode.SENSOR_READ_FAILED,
            "Impossible de lire le niveau d'eau",
            {"original_error": str(e)}
        )

@app.get("/api/water-level/check-availability")
async def check_water_availability(current_user: User = Depends(get_current_user)):
    """Vérifie si suffisamment d'eau est disponible"""
    try:
        if 'water_level' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur niveau d'eau non disponible",
                {"controller": "water_level"}
            )
        
        is_available = controllers['water_level'].is_water_available()
        trend = controllers['water_level'].get_level_trend()
        
        return {
            "water_available": is_available,
            "trend": trend,
            "message": "Eau disponible" if is_available else "Niveau d'eau critique"
        }
    except Exception as e:
        raise create_api_error(
            ErrorCode.SENSOR_READ_FAILED,
            "Impossible de vérifier la disponibilité de l'eau",
            {"original_error": str(e)}
        )

# Endpoints pour la température du radiateur
@app.get("/api/radiator-temp/status")
async def get_radiator_temp_status(current_user: User = Depends(get_current_user)):
    """Récupère le statut du capteur de température radiateur"""
    try:
        if 'radiator_temp' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur température radiateur non disponible",
                {"controller": "radiator_temp"}
            )
        
        status = controllers['radiator_temp'].get_status()
        return {"radiator_temp": status}
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_READ_FAILED,
            "Impossible de récupérer le statut de la température radiateur",
            {"original_error": str(e)}
        )

@app.get("/api/radiator-temp/read")
async def read_radiator_temperature(current_user: User = Depends(get_current_user)):
    """Lit la température du radiateur"""
    try:
        if 'radiator_temp' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur température radiateur non disponible",
                {"controller": "radiator_temp"}
            )
        
        temp_data = controllers['radiator_temp'].read_temperature()
        return {"radiator_temperature": temp_data}
    except Exception as e:
        raise create_api_error(
            ErrorCode.SENSOR_READ_FAILED,
            "Impossible de lire la température du radiateur",
            {"original_error": str(e)}
        )

@app.get("/api/radiator-temp/safety-check")
async def radiator_safety_check(current_user: User = Depends(get_current_user)):
    """Vérification de sécurité rapide du radiateur"""
    try:
        if 'radiator_temp' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur température radiateur non disponible",
                {"controller": "radiator_temp"}
            )
        
        safety_result = controllers['radiator_temp'].emergency_check()
        return {"safety_check": safety_result}
    except Exception as e:
        raise create_api_error(
            ErrorCode.SENSOR_READ_FAILED,
            "Impossible d'effectuer la vérification de sécurité",
            {"original_error": str(e)}
        )

@app.get("/api/radiator-temp/is-safe")
async def is_radiator_safe(current_user: User = Depends(get_current_user)):
    """Vérifie si la température du radiateur est sûre"""
    try:
        if 'radiator_temp' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur température radiateur non disponible",
                {"controller": "radiator_temp"}
            )
        
        is_safe = controllers['radiator_temp'].is_safe_temperature()
        trend = controllers['radiator_temp'].get_temperature_trend()
        
        return {
            "is_safe": is_safe,
            "trend": trend,
            "message": "Température sûre" if is_safe else "Température dangereuse"
        }
    except Exception as e:
        raise create_api_error(
            ErrorCode.SENSOR_READ_FAILED,
            "Impossible de vérifier la sécurité de la température",
            {"original_error": str(e)}
        )

# Endpoints pour la caméra CSI
@app.get("/api/camera/status")
async def get_camera_status(current_user: User = Depends(get_current_user)):
    """Récupère le statut de la caméra"""
    try:
        if 'camera' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur caméra non disponible",
                {"controller": "camera"}
            )
        
        status = controllers['camera'].get_status()
        return {"camera": status}
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_READ_FAILED,
            "Impossible de récupérer le statut de la caméra",
            {"original_error": str(e)}
        )

@app.get("/api/camera/capture")
async def capture_image(current_user: User = Depends(get_current_user)):
    """Capture une image depuis la caméra"""
    try:
        if 'camera' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur caméra non disponible",
                {"controller": "camera"}
            )
        
        image_data = controllers['camera'].capture_image()
        
        logger.info("Image capturée via API", {
            "user": current_user.username,
            "size_bytes": len(image_data)
        })
        
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type="image/jpeg",
            headers={"Content-Disposition": "inline; filename=capture.jpg"}
        )
        
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible de capturer une image",
            {"original_error": str(e)}
        )

@app.post("/api/camera/snapshot")
async def take_snapshot(current_user: User = Depends(get_current_user)):
    """Prend un snapshot et le sauvegarde"""
    try:
        if 'camera' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur caméra non disponible",
                {"controller": "camera"}
            )
        
        snapshot_path = controllers['camera'].take_snapshot()
        
        logger.info("Snapshot pris via API", {
            "user": current_user.username,
            "path": snapshot_path
        })
        
        return {
            "success": True,
            "snapshot_path": snapshot_path,
            "message": "Snapshot sauvegardé avec succès"
        }
        
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible de prendre un snapshot",
            {"original_error": str(e)}
        )

@app.post("/api/camera/streaming/start")
async def start_camera_streaming(current_user: User = Depends(get_current_user)):
    """Démarre le streaming vidéo"""
    try:
        if 'camera' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur caméra non disponible",
                {"controller": "camera"}
            )
        
        success = controllers['camera'].start_streaming()
        
        logger.info("Streaming caméra démarré via API", {
            "user": current_user.username,
            "success": success
        })
        
        return {
            "success": success,
            "message": "Streaming démarré" if success else "Échec démarrage streaming"
        }
        
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible de démarrer le streaming",
            {"original_error": str(e)}
        )

@app.post("/api/camera/streaming/stop")
async def stop_camera_streaming(current_user: User = Depends(get_current_user)):
    """Arrête le streaming vidéo"""
    try:
        if 'camera' not in controllers:
            raise create_api_error(
                ErrorCode.CONTROLLER_NOT_FOUND,
                "Contrôleur caméra non disponible",
                {"controller": "camera"}
            )
        
        success = controllers['camera'].stop_streaming()
        
        logger.info("Streaming caméra arrêté via API", {
            "user": current_user.username,
            "success": success
        })
        
        return {
            "success": success,
            "message": "Streaming arrêté" if success else "Échec arrêt streaming"
        }
        
    except Exception as e:
        raise create_api_error(
            ErrorCode.CONTROLLER_CONTROL_FAILED,
            "Impossible d'arrêter le streaming",
            {"original_error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)