"""
app.py
API FastAPI pour le système de gestion des mantes
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
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
from src.controllers.temperature_controller import TemperatureController
from src.controllers.light_controller import LightController
from src.controllers.humidity_controller import HumidityController
from src.controllers.feeding_controller import FeedingController

# Configuration de l'application
app = FastAPI(
    title="Alimante API",
    description="API pour la gestion automatisée des mantes",
    version="1.0.0"
)

# Enregistrement des gestionnaires d'erreurs
register_error_handlers(app)

# CORS pour l'application mobile (plus sécurisé)
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

async def broadcast_to_websockets(message: Dict[str, Any]):
    """Envoie un message à tous les clients WebSocket connectés"""
    if not websocket_connections:
        return
        
    message_json = json.dumps(message)
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
            data = await get_system_status()
            await websocket.send_text(json.dumps(data))
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

@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "Alimante API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def get_system_status():
    """Retourne le statut complet du système"""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "system": "online",
            "controllers": {}
        }
        
        # Statut de chaque contrôleur
        for name, controller in controllers.items():
            try:
                if hasattr(controller, 'get_status'):
                    status["controllers"][name] = controller.get_status()
                else:
                    status["controllers"][name] = {"status": "unknown"}
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération du statut {name}: {e}")
                status["controllers"][name] = {"status": "error", "error": str(e)}
        
        return status
        
    except Exception as e:
        logger.exception("💥 Erreur lors de la récupération du statut")
        raise create_api_error(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Impossible de récupérer le statut du système",
            {"original_error": str(e)}
        )

@app.get("/api/metrics")
async def get_metrics():
    """Récupère les métriques des capteurs"""
    try:
        metrics = {}
        
        # Température
        if 'temperature' in controllers:
            try:
                temp_status = controllers['temperature'].get_status()
                metrics['temperature'] = {
                    'current': temp_status.get('current_temperature'),
                    'optimal': temp_status.get('optimal_temperature'),
                    'heating_active': temp_status.get('heating_active')
                }
            except Exception as e:
                logger.warning(f"Erreur métriques température: {e}")
                metrics['temperature'] = {"error": str(e)}
        
        # Humidité
        if 'humidity' in controllers:
            try:
                humidity_status = controllers['humidity'].get_status()
                metrics['humidity'] = {
                    'current': humidity_status.get('current_humidity'),
                    'optimal': humidity_status.get('optimal_humidity'),
                    'sprayer_active': humidity_status.get('sprayer_active')
                }
            except Exception as e:
                logger.warning(f"Erreur métriques humidité: {e}")
                metrics['humidity'] = {"error": str(e)}
        
        return metrics
        
    except Exception as e:
        logger.exception("💥 Erreur lors de la récupération des métriques")
        raise create_api_error(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Impossible de récupérer les métriques",
            {"original_error": str(e)}
        )

@app.post("/api/control")
async def control_system(control_data: Dict[str, Any]):
    """Contrôle les systèmes"""
    try:
        if not control_data:
            raise create_api_error(
                ErrorCode.API_INVALID_REQUEST,
                "Données de contrôle manquantes"
            )
        
        results = {}
        
        # Contrôle température
        if 'temperature' in control_data:
            try:
                if controllers['temperature'].control_temperature():
                    results['temperature'] = "controlled"
                else:
                    results['temperature'] = "error"
            except Exception as e:
                logger.error(f"Erreur contrôle température: {e}")
                results['temperature'] = "error"
        
        # Contrôle humidité
        if 'humidity' in control_data:
            try:
                if controllers['humidity'].control_humidity():
                    results['humidity'] = "controlled"
                else:
                    results['humidity'] = "error"
            except Exception as e:
                logger.error(f"Erreur contrôle humidité: {e}")
                results['humidity'] = "error"
        
        # Contrôle éclairage
        if 'light' in control_data:
            try:
                if controllers['light'].control_lighting():
                    results['light'] = "controlled"
                else:
                    results['light'] = "error"
            except Exception as e:
                logger.error(f"Erreur contrôle éclairage: {e}")
                results['light'] = "error"
        
        # Contrôle alimentation
        if 'feeding' in control_data:
            try:
                if controllers['feeding'].control_feeding():
                    results['feeding'] = "controlled"
                else:
                    results['feeding'] = "error"
            except Exception as e:
                logger.error(f"Erreur contrôle alimentation: {e}")
                results['feeding'] = "error"
        
        # Broadcast aux clients WebSocket
        await broadcast_to_websockets({
            "type": "control_update",
            "data": results,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info("🎛️ Contrôle système exécuté", {"results": results})
        return {"status": "success", "results": results}
        
    except AlimanteException:
        raise
    except Exception as e:
        logger.exception("💥 Erreur lors du contrôle système")
        raise create_api_error(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Erreur lors du contrôle système",
            {"original_error": str(e)}
        )

@app.post("/api/feeding/trigger")
async def trigger_feeding():
    """Déclenche manuellement l'alimentation"""
    try:
        if 'feeding' not in controllers:
            raise create_api_error(
                ErrorCode.API_NOT_FOUND,
                "Contrôleur d'alimentation non disponible"
            )
        
        success = controllers['feeding'].trigger_feeding()
        
        await broadcast_to_websockets({
            "type": "feeding_triggered",
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info("🍽️ Alimentation déclenchée", {"success": success})
        return {"status": "success" if success else "error"}
        
    except AlimanteException:
        raise
    except Exception as e:
        logger.exception("💥 Erreur lors du déclenchement de l'alimentation")
        raise create_api_error(
            ErrorCode.FEEDING_FAILED,
            "Erreur lors du déclenchement de l'alimentation",
            {"original_error": str(e)}
        )

@app.get("/api/config")
async def get_config():
    """Retourne la configuration actuelle"""
    try:
        config = SystemConfig.from_json('config/config.json', 'config/orthopteres/mantidae/mantis_religiosa.json')
        return {
            "serial_port": config.serial_port,
            "baud_rate": config.baud_rate,
            "temperature": config.temperature,
            "humidity": config.humidity,
            "location": config.location,
            "feeding": config.feeding
        }
    except Exception as e:
        logger.exception("💥 Erreur lors de la récupération de la configuration")
        raise create_api_error(
            ErrorCode.CONFIGURATION_INVALID,
            "Impossible de récupérer la configuration",
            {"original_error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)