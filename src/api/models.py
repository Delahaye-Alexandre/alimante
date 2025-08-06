"""
Modèles Pydantic pour l'API Alimante
Validation des données d'entrée et de sortie
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ControlAction(str, Enum):
    """Actions de contrôle disponibles"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    LIGHT = "light"
    FEEDING = "feeding"


class SystemStatus(str, Enum):
    """Statuts du système"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ControllerStatus(str, Enum):
    """Statuts des contrôleurs"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNKNOWN = "unknown"


# Modèles pour les requêtes API
class ControlRequest(BaseModel):
    """Requête de contrôle système"""
    actions: List[ControlAction] = Field(
        ..., 
        description="Actions à exécuter",
        min_items=1,
        max_items=10
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Paramètres optionnels pour les actions"
    )
    
    @validator('actions')
    def validate_actions(cls, v):
        """Valide que les actions sont uniques"""
        if len(set(v)) != len(v):
            raise ValueError("Les actions doivent être uniques")
        return v


class FeedingTriggerRequest(BaseModel):
    """Requête de déclenchement d'alimentation"""
    quantity: Optional[float] = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Quantité d'alimentation (1-10)"
    )
    force: bool = Field(
        default=False,
        description="Forcer l'alimentation même si pas prévue"
    )


class ConfigUpdateRequest(BaseModel):
    """Requête de mise à jour de configuration"""
    temperature: Optional[Dict[str, float]] = Field(
        default=None,
        description="Configuration température"
    )
    humidity: Optional[Dict[str, float]] = Field(
        default=None,
        description="Configuration humidité"
    )
    feeding: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration alimentation"
    )
    lighting: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration éclairage"
    )
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Valide la configuration température"""
        if v is not None:
            required_keys = ['optimal', 'tolerance']
            if not all(key in v for key in required_keys):
                raise ValueError("Configuration température incomplète")
            if v['optimal'] < 10 or v['optimal'] > 40:
                raise ValueError("Température optimale doit être entre 10 et 40°C")
            if v['tolerance'] < 0.5 or v['tolerance'] > 10:
                raise ValueError("Tolérance doit être entre 0.5 et 10°C")
        return v
    
    @validator('humidity')
    def validate_humidity(cls, v):
        """Valide la configuration humidité"""
        if v is not None:
            required_keys = ['optimal', 'tolerance']
            if not all(key in v for key in required_keys):
                raise ValueError("Configuration humidité incomplète")
            if v['optimal'] < 20 or v['optimal'] > 90:
                raise ValueError("Humidité optimale doit être entre 20 et 90%")
            if v['tolerance'] < 1 or v['tolerance'] > 20:
                raise ValueError("Tolérance doit être entre 1 et 20%")
        return v


# Modèles pour les réponses API
class SystemMetrics(BaseModel):
    """Métriques du système"""
    temperature: Optional[Dict[str, float]] = Field(
        default=None,
        description="Métriques température"
    )
    humidity: Optional[Dict[str, float]] = Field(
        default=None,
        description="Métriques humidité"
    )
    lighting: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métriques éclairage"
    )
    feeding: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métriques alimentation"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp des métriques"
    )


class ControllerInfo(BaseModel):
    """Informations d'un contrôleur"""
    name: str = Field(..., description="Nom du contrôleur")
    status: ControllerStatus = Field(..., description="Statut du contrôleur")
    last_update: datetime = Field(..., description="Dernière mise à jour")
    error_count: int = Field(
        default=0,
        ge=0,
        description="Nombre d'erreurs"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métadonnées du contrôleur"
    )


class SystemStatusResponse(BaseModel):
    """Réponse de statut système"""
    status: SystemStatus = Field(..., description="Statut du système")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp du statut"
    )
    controllers: Dict[str, ControllerInfo] = Field(
        default_factory=dict,
        description="Statut des contrôleurs"
    )
    uptime: Optional[float] = Field(
        default=None,
        description="Temps de fonctionnement en secondes"
    )
    version: str = Field(
        default="1.0.0",
        description="Version du système"
    )


class ControlResponse(BaseModel):
    """Réponse de contrôle système"""
    status: str = Field(..., description="Statut de l'opération")
    results: Dict[str, str] = Field(
        default_factory=dict,
        description="Résultats par action"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de l'opération"
    )
    errors: Optional[List[str]] = Field(
        default=None,
        description="Erreurs éventuelles"
    )


class FeedingResponse(BaseModel):
    """Réponse de déclenchement d'alimentation"""
    status: str = Field(..., description="Statut de l'alimentation")
    success: bool = Field(..., description="Succès de l'opération")
    quantity_dispensed: Optional[float] = Field(
        default=None,
        description="Quantité distribuée"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de l'alimentation"
    )
    next_feeding: Optional[datetime] = Field(
        default=None,
        description="Prochaine alimentation prévue"
    )


class ConfigResponse(BaseModel):
    """Réponse de configuration"""
    temperature: Dict[str, float] = Field(..., description="Configuration température")
    humidity: Dict[str, float] = Field(..., description="Configuration humidité")
    feeding: Dict[str, Any] = Field(..., description="Configuration alimentation")
    lighting: Dict[str, Any] = Field(..., description="Configuration éclairage")
    location: Dict[str, float] = Field(..., description="Configuration localisation")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de la configuration"
    )


# Modèles pour les WebSocket
class WebSocketMessage(BaseModel):
    """Message WebSocket générique"""
    type: str = Field(..., description="Type de message")
    data: Dict[str, Any] = Field(..., description="Données du message")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp du message"
    )


class StatusUpdateMessage(WebSocketMessage):
    """Message de mise à jour de statut"""
    type: str = Field(default="status_update", description="Type de message")
    data: SystemStatusResponse = Field(..., description="Données de statut")


class ControlUpdateMessage(WebSocketMessage):
    """Message de mise à jour de contrôle"""
    type: str = Field(default="control_update", description="Type de message")
    data: ControlResponse = Field(..., description="Données de contrôle")


class FeedingUpdateMessage(WebSocketMessage):
    """Message de mise à jour d'alimentation"""
    type: str = Field(default="feeding_update", description="Type de message")
    data: FeedingResponse = Field(..., description="Données d'alimentation")


# Modèles pour les erreurs
class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée"""
    error_code: int = Field(..., description="Code d'erreur")
    error_name: str = Field(..., description="Nom de l'erreur")
    message: str = Field(..., description="Message d'erreur")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Contexte de l'erreur"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de l'erreur"
    )


# Modèles pour les métriques
class MetricData(BaseModel):
    """Données de métrique"""
    name: str = Field(..., description="Nom de la métrique")
    value: float = Field(..., description="Valeur de la métrique")
    unit: str = Field(..., description="Unité de mesure")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de la métrique"
    )
    tags: Optional[Dict[str, str]] = Field(
        default=None,
        description="Tags de la métrique"
    )


class MetricsResponse(BaseModel):
    """Réponse de métriques"""
    metrics: List[MetricData] = Field(..., description="Liste des métriques")
    summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Résumé des métriques"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de la réponse"
    )


# Validateurs personnalisés
def validate_temperature_range(value: float) -> float:
    """Valide une température"""
    if value < -10 or value > 50:
        raise ValueError("Température doit être entre -10 et 50°C")
    return value


def validate_humidity_range(value: float) -> float:
    """Valide une humidité"""
    if value < 0 or value > 100:
        raise ValueError("Humidité doit être entre 0 et 100%")
    return value


def validate_positive_float(value: float) -> float:
    """Valide un nombre positif"""
    if value <= 0:
        raise ValueError("La valeur doit être positive")
    return value 