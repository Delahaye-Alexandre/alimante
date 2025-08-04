"""
app.py
API FastAPI pour le système de gestion des mantes
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from src.utils.config_manager import SystemConfig
from src.utils.gpio_manager import GPIOManager
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

# CORS pour l'application mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales
gpio_manager: GPIOManager = None
controllers: Dict[str, Any] = {}
websocket_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialise le système au démarrage"""
    global gpio_manager, controllers
    
    try:
        # Initialisation GPIO
        gpio_manager = GPIOManager()
        
        # Chargement de la configuration
        config = SystemConfig.from_json('config/config.json', 'config/orthopteres/mantidae/mantis_religiosa.json')
        
        # Initialisation des contrôleurs
        controllers = {
            'temperature': TemperatureController(gpio_manager, config.temperature),
            'humidity': HumidityController(gpio_manager, config.humidity),
            'light': LightController(gpio_manager, config.location),
            'feeding': FeedingController(gpio_manager, config.feeding)
        }
        
        logging.info("API Alimante démarrée avec succès")
        
    except Exception as e:
        logging.error(f"Erreur lors du démarrage: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoie les ressources à l'arrêt"""
    global gpio_manager
    if gpio_manager:
        gpio_manager.cleanup()
    logging.info("API arrêtée")

async def broadcast_to_websockets(message: Dict[str, Any]):
    """Envoie un message à tous les clients WebSocket connectés"""
    if websocket_connections:
        message_json = json.dumps(message)
        await asyncio.gather(
            *[ws.send_text(message_json) for ws in websocket_connections],
            return_exceptions=True
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour les mises à jour en temps réel"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Envoi périodique des données
            data = await get_system_status()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(5)  # Mise à jour toutes les 5 secondes
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logging.info("Client WebSocket déconnecté")

@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "Alimante API",
        "version": "1.0.0",
        "status": "running"
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
            if hasattr(controller, 'get_status'):
                status["controllers"][name] = controller.get_status()
            else:
                status["controllers"][name] = {"status": "unknown"}
        
        return status
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération du statut: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

@app.get("/api/metrics")
async def get_metrics():
    """Récupère les métriques des capteurs"""
    try:
        metrics = {}
        
        # Température
        if 'temperature' in controllers:
            temp_status = controllers['temperature'].get_status()
            metrics['temperature'] = {
                'current': temp_status.get('current_temperature'),
                'optimal': temp_status.get('optimal_temperature'),
                'heating_active': temp_status.get('heating_active')
            }
        
        # Humidité
        if 'humidity' in controllers:
            humidity_status = controllers['humidity'].get_status()
            metrics['humidity'] = {
                'current': humidity_status.get('current_humidity'),
                'optimal': humidity_status.get('optimal_humidity'),
                'sprayer_active': humidity_status.get('sprayer_active')
            }
        
        return metrics
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des métriques: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

@app.post("/api/control")
async def control_system(control_data: Dict[str, Any]):
    """Contrôle les systèmes"""
    try:
        results = {}
        
        if 'temperature' in control_data:
            if controllers['temperature'].control_temperature():
                results['temperature'] = "controlled"
            else:
                results['temperature'] = "error"
        
        if 'humidity' in control_data:
            if controllers['humidity'].control_humidity():
                results['humidity'] = "controlled"
            else:
                results['humidity'] = "error"
        
        if 'light' in control_data:
            if controllers['light'].control_lighting():
                results['light'] = "controlled"
            else:
                results['light'] = "error"
        
        if 'feeding' in control_data:
            if controllers['feeding'].control_feeding():
                results['feeding'] = "controlled"
            else:
                results['feeding'] = "error"
        
        # Broadcast aux clients WebSocket
        await broadcast_to_websockets({
            "type": "control_update",
            "data": results,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"status": "success", "results": results}
        
    except Exception as e:
        logging.error(f"Erreur lors du contrôle: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

@app.post("/api/feeding/trigger")
async def trigger_feeding():
    """Déclenche manuellement l'alimentation"""
    try:
        if 'feeding' in controllers:
            success = controllers['feeding'].trigger_feeding()
            
            await broadcast_to_websockets({
                "type": "feeding_triggered",
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
            
            return {"status": "success" if success else "error"}
        else:
            raise HTTPException(status_code=404, detail="Contrôleur d'alimentation non disponible")
            
    except Exception as e:
        logging.error(f"Erreur lors du déclenchement de l'alimentation: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

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
        logging.error(f"Erreur lors de la récupération de la configuration: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)