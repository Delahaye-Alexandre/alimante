"""
Service de capteurs pour Alimante
Gestion des lectures de capteurs et calibrations
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from statistics import mean, stdev

from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


@dataclass
class SensorReading:
    """Lecture d'un capteur"""
    sensor_id: str
    value: float
    unit: str
    timestamp: datetime
    quality: float = 1.0  # 0.0 à 1.0
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SensorCalibration:
    """Calibration d'un capteur"""
    sensor_id: str
    offset: float = 0.0
    scale: float = 1.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    last_calibration: Optional[datetime] = None
    calibration_points: List[Tuple[float, float]] = None
    
    def __post_init__(self):
        if self.calibration_points is None:
            self.calibration_points = []


class SensorService:
    """Service de gestion des capteurs"""
    
    def __init__(self):
        self.logger = get_logger("sensor_service")
        self.sensors: Dict[str, Any] = {}
        self.readings_history: Dict[str, List[SensorReading]] = {}
        self.calibrations: Dict[str, SensorCalibration] = {}
        self.max_history_size = 1000
        
        # Configuration des capteurs
        self.sensor_configs = {
            "temperature": {
                "unit": "°C",
                "min_value": -10.0,
                "max_value": 50.0,
                "calibration_required": True,
                "reading_interval": 30,  # secondes
                "quality_threshold": 0.8
            },
            "humidity": {
                "unit": "%",
                "min_value": 0.0,
                "max_value": 100.0,
                "calibration_required": True,
                "reading_interval": 30,
                "quality_threshold": 0.8
            },
            "light": {
                "unit": "lux",
                "min_value": 0.0,
                "max_value": 100000.0,
                "calibration_required": False,
                "reading_interval": 60,
                "quality_threshold": 0.7
            }
        }
    
    def register_sensor(self, sensor_id: str, sensor_type: str, sensor_instance: Any) -> None:
        """Enregistre un capteur"""
        if sensor_type not in self.sensor_configs:
            raise create_exception(
                ErrorCode.SENSOR_INIT_FAILED,
                f"Type de capteur non reconnu: {sensor_type}",
                {"available_types": list(self.sensor_configs.keys())}
            )
        
        self.sensors[sensor_id] = {
            "type": sensor_type,
            "instance": sensor_instance,
            "config": self.sensor_configs[sensor_type].copy(),
            "last_reading": None,
            "error_count": 0
        }
        
        # Initialiser l'historique
        self.readings_history[sensor_id] = []
        
        # Initialiser la calibration
        if self.sensor_configs[sensor_type]["calibration_required"]:
            self.calibrations[sensor_id] = SensorCalibration(sensor_id=sensor_id)
        
        self.logger.info(f"Capteur enregistré: {sensor_id} ({sensor_type})")
    
    def read_sensor(self, sensor_id: str) -> SensorReading:
        """Lit un capteur"""
        try:
            if sensor_id not in self.sensors:
                raise create_exception(
                    ErrorCode.SENSOR_INIT_FAILED,
                    f"Capteur non trouvé: {sensor_id}",
                    {"available_sensors": list(self.sensors.keys())}
                )
            
            sensor_info = self.sensors[sensor_id]
            sensor_instance = sensor_info["instance"]
            config = sensor_info["config"]
            
            # Lire le capteur
            start_time = time.time()
            
            if hasattr(sensor_instance, 'read'):
                raw_value = sensor_instance.read()
            elif hasattr(sensor_instance, 'get_temperature'):
                raw_value = sensor_instance.get_temperature()
            elif hasattr(sensor_instance, 'get_humidity'):
                raw_value = sensor_instance.get_humidity()
            else:
                raise create_exception(
                    ErrorCode.SENSOR_READ_FAILED,
                    f"Méthode de lecture non disponible pour le capteur {sensor_id}",
                    {"sensor_id": sensor_id}
                )
            
            reading_time = time.time() - start_time
            
            # Appliquer la calibration si nécessaire
            calibrated_value = self._apply_calibration(sensor_id, raw_value)
            
            # Vérifier les limites
            if config["min_value"] is not None and calibrated_value < config["min_value"]:
                self.logger.warning(f"Valeur capteur {sensor_id} sous la limite minimale: {calibrated_value}")
            
            if config["max_value"] is not None and calibrated_value > config["max_value"]:
                self.logger.warning(f"Valeur capteur {sensor_id} au-dessus de la limite maximale: {calibrated_value}")
            
            # Calculer la qualité de la lecture
            quality = self._calculate_reading_quality(sensor_id, calibrated_value, reading_time)
            
            # Créer l'objet de lecture
            reading = SensorReading(
                sensor_id=sensor_id,
                value=calibrated_value,
                unit=config["unit"],
                timestamp=datetime.now(),
                quality=quality,
                metadata={
                    "raw_value": raw_value,
                    "reading_time": reading_time,
                    "sensor_type": sensor_info["type"]
                }
            )
            
            # Mettre à jour les informations du capteur
            sensor_info["last_reading"] = reading
            sensor_info["error_count"] = 0
            
            # Ajouter à l'historique
            self._add_to_history(sensor_id, reading)
            
            self.logger.debug(f"Lecture capteur {sensor_id}: {calibrated_value}{config['unit']} (qualité: {quality:.2f})")
            
            return reading
            
        except Exception as e:
            # Incrémenter le compteur d'erreurs
            if sensor_id in self.sensors:
                self.sensors[sensor_id]["error_count"] += 1
            
            self.logger.exception(f"Erreur lecture capteur {sensor_id}")
            
            if isinstance(e, create_exception):
                raise
            else:
                raise create_exception(
                    ErrorCode.SENSOR_READ_FAILED,
                    f"Erreur lors de la lecture du capteur {sensor_id}",
                    {"original_error": str(e)}
                )
    
    def read_all_sensors(self) -> Dict[str, SensorReading]:
        """Lit tous les capteurs"""
        try:
            readings = {}
            
            for sensor_id in self.sensors.keys():
                try:
                    readings[sensor_id] = self.read_sensor(sensor_id)
                except Exception as e:
                    self.logger.error(f"Erreur lecture capteur {sensor_id}: {e}")
                    # Créer une lecture d'erreur
                    readings[sensor_id] = SensorReading(
                        sensor_id=sensor_id,
                        value=0.0,
                        unit="error",
                        timestamp=datetime.now(),
                        quality=0.0,
                        metadata={"error": str(e)}
                    )
            
            return readings
            
        except Exception as e:
            self.logger.exception("Erreur lecture de tous les capteurs")
            raise create_exception(
                ErrorCode.SENSOR_READ_FAILED,
                "Erreur lors de la lecture de tous les capteurs",
                {"original_error": str(e)}
            )
    
    def calibrate_sensor(self, sensor_id: str, reference_values: List[Tuple[float, float]]) -> bool:
        """Calibre un capteur"""
        try:
            if sensor_id not in self.sensors:
                raise create_exception(
                    ErrorCode.SENSOR_INIT_FAILED,
                    f"Capteur non trouvé: {sensor_id}",
                    {"available_sensors": list(self.sensors.keys())}
                )
            
            sensor_info = self.sensors[sensor_id]
            config = sensor_info["config"]
            
            if not config["calibration_required"]:
                raise create_exception(
                    ErrorCode.SENSOR_CALIBRATION_FAILED,
                    f"Calibration non requise pour le capteur {sensor_id}",
                    {"sensor_id": sensor_id}
                )
            
            if len(reference_values) < 2:
                raise create_exception(
                    ErrorCode.SENSOR_CALIBRATION_FAILED,
                    "Au moins 2 points de référence sont nécessaires pour la calibration",
                    {"points_provided": len(reference_values)}
                )
            
            # Calculer les paramètres de calibration
            raw_values = [point[0] for point in reference_values]
            expected_values = [point[1] for point in reference_values]
            
            # Régression linéaire simple
            n = len(raw_values)
            sum_x = sum(raw_values)
            sum_y = sum(expected_values)
            sum_xy = sum(x * y for x, y in zip(raw_values, expected_values))
            sum_x2 = sum(x * x for x in raw_values)
            
            # Calculer offset et scale
            scale = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            offset = (sum_y - scale * sum_x) / n
            
            # Créer ou mettre à jour la calibration
            if sensor_id not in self.calibrations:
                self.calibrations[sensor_id] = SensorCalibration(sensor_id=sensor_id)
            
            calibration = self.calibrations[sensor_id]
            calibration.offset = offset
            calibration.scale = scale
            calibration.calibration_points = reference_values
            calibration.last_calibration = datetime.now()
            
            # Définir les limites min/max
            calibration.min_value = min(expected_values)
            calibration.max_value = max(expected_values)
            
            self.logger.info(f"Capteur calibré: {sensor_id} (offset: {offset:.3f}, scale: {scale:.3f})")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Erreur calibration capteur {sensor_id}")
            if isinstance(e, create_exception):
                raise
            else:
                raise create_exception(
                    ErrorCode.SENSOR_CALIBRATION_FAILED,
                    f"Erreur lors de la calibration du capteur {sensor_id}",
                    {"original_error": str(e)}
                )
    
    def get_sensor_status(self, sensor_id: str) -> Dict[str, Any]:
        """Récupère le statut d'un capteur"""
        try:
            if sensor_id not in self.sensors:
                raise create_exception(
                    ErrorCode.SENSOR_INIT_FAILED,
                    f"Capteur non trouvé: {sensor_id}",
                    {"available_sensors": list(self.sensors.keys())}
                )
            
            sensor_info = self.sensors[sensor_id]
            last_reading = sensor_info["last_reading"]
            
            status = {
                "sensor_id": sensor_id,
                "type": sensor_info["type"],
                "config": sensor_info["config"],
                "error_count": sensor_info["error_count"],
                "last_reading": last_reading.to_dict() if last_reading else None,
                "calibration": None
            }
            
            # Ajouter les informations de calibration
            if sensor_id in self.calibrations:
                calibration = self.calibrations[sensor_id]
                status["calibration"] = {
                    "offset": calibration.offset,
                    "scale": calibration.scale,
                    "min_value": calibration.min_value,
                    "max_value": calibration.max_value,
                    "last_calibration": calibration.last_calibration.isoformat() if calibration.last_calibration else None,
                    "calibration_points_count": len(calibration.calibration_points)
                }
            
            return status
            
        except Exception as e:
            self.logger.exception(f"Erreur récupération statut capteur {sensor_id}")
            raise create_exception(
                ErrorCode.SENSOR_READ_FAILED,
                f"Impossible de récupérer le statut du capteur {sensor_id}",
                {"original_error": str(e)}
            )
    
    def get_readings_history(self, sensor_id: str, hours: int = 24) -> List[SensorReading]:
        """Récupère l'historique des lectures d'un capteur"""
        if sensor_id not in self.readings_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [reading for reading in self.readings_history[sensor_id] if reading.timestamp > cutoff_time]
    
    def get_sensor_statistics(self, sensor_id: str, hours: int = 24) -> Dict[str, Any]:
        """Récupère les statistiques d'un capteur"""
        try:
            readings = self.get_readings_history(sensor_id, hours)
            
            if not readings:
                return {
                    "sensor_id": sensor_id,
                    "period_hours": hours,
                    "readings_count": 0,
                    "statistics": None
                }
            
            values = [reading.value for reading in readings if reading.quality > 0.5]
            
            if not values:
                return {
                    "sensor_id": sensor_id,
                    "period_hours": hours,
                    "readings_count": len(readings),
                    "valid_readings_count": 0,
                    "statistics": None
                }
            
            return {
                "sensor_id": sensor_id,
                "period_hours": hours,
                "readings_count": len(readings),
                "valid_readings_count": len(values),
                "statistics": {
                    "mean": mean(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": stdev(values) if len(values) > 1 else 0.0,
                    "quality_avg": mean([r.quality for r in readings])
                }
            }
            
        except Exception as e:
            self.logger.exception(f"Erreur calcul statistiques capteur {sensor_id}")
            raise create_exception(
                ErrorCode.SENSOR_READ_FAILED,
                f"Impossible de calculer les statistiques du capteur {sensor_id}",
                {"original_error": str(e)}
            )
    
    def _apply_calibration(self, sensor_id: str, raw_value: float) -> float:
        """Applique la calibration à une valeur brute"""
        if sensor_id not in self.calibrations:
            return raw_value
        
        calibration = self.calibrations[sensor_id]
        return raw_value * calibration.scale + calibration.offset
    
    def _calculate_reading_quality(self, sensor_id: str, value: float, reading_time: float) -> float:
        """Calcule la qualité d'une lecture"""
        sensor_info = self.sensors[sensor_id]
        config = sensor_info["config"]
        
        quality = 1.0
        
        # Facteur temps de lecture
        if reading_time > 5.0:  # Plus de 5 secondes
            quality *= 0.8
        elif reading_time > 2.0:  # Plus de 2 secondes
            quality *= 0.9
        
        # Facteur limites
        if config["min_value"] is not None and value < config["min_value"]:
            quality *= 0.5
        if config["max_value"] is not None and value > config["max_value"]:
            quality *= 0.5
        
        # Facteur historique (stabilité)
        recent_readings = self.get_readings_history(sensor_id, hours=1)
        if len(recent_readings) > 2:
            recent_values = [r.value for r in recent_readings[-3:]]
            if max(recent_values) - min(recent_values) > 10:  # Variation importante
                quality *= 0.8
        
        return max(0.0, min(1.0, quality))
    
    def _add_to_history(self, sensor_id: str, reading: SensorReading) -> None:
        """Ajoute une lecture à l'historique"""
        if sensor_id not in self.readings_history:
            self.readings_history[sensor_id] = []
        
        self.readings_history[sensor_id].append(reading)
        
        # Limiter la taille de l'historique
        if len(self.readings_history[sensor_id]) > self.max_history_size:
            self.readings_history[sensor_id] = self.readings_history[sensor_id][-self.max_history_size:]
    
    def cleanup(self) -> None:
        """Nettoie les ressources du service"""
        self.logger.info("Nettoyage du service de capteurs")
        
        # Nettoyer les capteurs
        for sensor_id, sensor_info in self.sensors.items():
            try:
                sensor_instance = sensor_info["instance"]
                if hasattr(sensor_instance, 'cleanup'):
                    sensor_instance.cleanup()
                    self.logger.info(f"Capteur nettoyé: {sensor_id}")
            except Exception as e:
                self.logger.error(f"Erreur nettoyage capteur {sensor_id}: {e}")
        
        # Vider les historiques
        self.readings_history.clear()
        
        self.logger.info("Service de capteurs nettoyé")


# Instance globale du service de capteurs
sensor_service = SensorService() 