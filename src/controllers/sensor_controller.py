"""
Contrôleur des capteurs Alimante
Gère la lecture et le traitement des données des capteurs
"""

import time
import logging
from typing import Dict, Any, Optional, List
from .base_controller import BaseController, ControllerConfig, ControllerState, ControllerError
from .drivers import DHT22Sensor, AirQualitySensor, TenflyerWaterSensor, DriverConfig

class SensorController(BaseController):
    """
    Contrôleur des capteurs environnementaux
    """
    
    def __init__(self, config: ControllerConfig, gpio_config: Dict[str, Any], 
                 safety_limits: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le contrôleur des capteurs
        
        Args:
            config: Configuration du contrôleur
            gpio_config: Configuration GPIO
            safety_limits: Limites de sécurité
            event_bus: Bus d'événements
        """
        super().__init__(config, event_bus)
        self.gpio_config = gpio_config
        self.safety_limits = safety_limits
        
        # Capteurs
        self.dht22 = None
        self.air_quality = None
        self.water_sensor = None
        
        # Données actuelles
        self.current_data = {
            "temperature": None,
            "humidity": None,
            "air_quality": None,
            "air_quality_level": None,
            "water_level": None,
            "water_percentage": None,
            "timestamp": None
        }
        
        # Historique des données
        self.data_history = []
        self.max_history_size = 1000
        
        # Alertes
        self.alerts = []
        self.alert_thresholds = {
            "temperature": {"min": 15, "max": 35},
            "humidity": {"min": 30, "max": 80},
            "air_quality": {"max": 150},  # AQI
            "water_level": {"min": 20}    # Pourcentage
        }
        
    def initialize(self) -> bool:
        """
        Initialise les capteurs
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du contrôleur des capteurs...")
            
            # Initialiser DHT22
            if "sensors" in self.gpio_config and "temperature_humidity" in self.gpio_config["sensors"]:
                try:
                    dht22_config = DriverConfig(
                        name="dht22",
                        enabled=True,
                        calibration=self.safety_limits.get("calibration", {}).get("dht22", {})
                    )
                    self.dht22 = DHT22Sensor(dht22_config, self.gpio_config["sensors"]["temperature_humidity"])
                    if self.dht22.initialize():
                        self.logger.info("DHT22 initialisé")
                    else:
                        self.logger.warning("Échec initialisation DHT22")
                        self.dht22 = None
                except Exception as e:
                    self.logger.error(f"Erreur initialisation DHT22: {e}")
                    self.dht22 = None
            
            # Initialiser capteur qualité d'air
            if "sensors" in self.gpio_config and "air_quality" in self.gpio_config["sensors"]:
                try:
                    air_quality_config = DriverConfig(
                        name="air_quality",
                        enabled=True,
                        calibration=self.safety_limits.get("calibration", {}).get("air_quality", {})
                    )
                    self.air_quality = AirQualitySensor(
                        air_quality_config, 
                        self.gpio_config["sensors"]["air_quality"],
                        adc_channel=0
                    )
                    if self.air_quality.initialize():
                        self.logger.info("Capteur qualité d'air initialisé")
                    else:
                        self.logger.warning("Échec initialisation capteur qualité d'air")
                        self.air_quality = None
                except Exception as e:
                    self.logger.error(f"Erreur initialisation capteur qualité d'air: {e}")
                    self.air_quality = None
            
            # Initialiser capteur niveau d'eau
            if "sensors" in self.gpio_config and "water_level" in self.gpio_config["sensors"]:
                try:
                    water_config = DriverConfig(
                        name="water_sensor",
                        enabled=True,
                        calibration=self.safety_limits.get("calibration", {}).get("water_sensor", {})
                    )
                    self.water_sensor = TenflyerWaterSensor(
                        water_config, 
                        self.gpio_config["sensors"]["water_level"]
                    )
                    if self.water_sensor.initialize():
                        self.logger.info("Capteur niveau d'eau initialisé")
                    else:
                        self.logger.warning("Échec initialisation capteur niveau d'eau")
                        self.water_sensor = None
                except Exception as e:
                    self.logger.error(f"Erreur initialisation capteur niveau d'eau: {e}")
                    self.water_sensor = None
            
            # Vérifier qu'au moins un capteur est initialisé
            if not any([self.dht22, self.air_quality, self.water_sensor]):
                self.logger.error("Aucun capteur initialisé")
                return False
            
            self.logger.info("Contrôleur des capteurs initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation contrôleur capteurs: {e}")
            return False
    
    def update(self) -> bool:
        """
        Met à jour les données des capteurs
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            current_time = time.time()
            new_data = {
                "timestamp": current_time,
                "temperature": None,
                "humidity": None,
                "air_quality": None,
                "air_quality_level": None,
                "water_level": None,
                "water_percentage": None
            }
            
            # Lire DHT22
            if self.dht22:
                try:
                    dht22_data = self.dht22.safe_read()
                    if dht22_data:
                        new_data["temperature"] = dht22_data.get("temperature")
                        new_data["humidity"] = dht22_data.get("humidity")
                except Exception as e:
                    self.logger.warning(f"Erreur lecture DHT22: {e}")
            
            # Lire capteur qualité d'air
            if self.air_quality:
                try:
                    air_data = self.air_quality.safe_read()
                    if air_data:
                        new_data["air_quality"] = air_data.get("aqi")
                        new_data["air_quality_level"] = air_data.get("level")
                except Exception as e:
                    self.logger.warning(f"Erreur lecture capteur qualité d'air: {e}")
            
            # Lire capteur niveau d'eau
            if self.water_sensor:
                try:
                    water_data = self.water_sensor.safe_read()
                    if water_data:
                        new_data["water_level"] = water_data.get("level")
                        new_data["water_percentage"] = water_data.get("percentage")
                except Exception as e:
                    self.logger.warning(f"Erreur lecture capteur niveau d'eau: {e}")
            
            # Mettre à jour les données actuelles
            self.current_data.update(new_data)
            
            # Ajouter à l'historique
            self.data_history.append(new_data.copy())
            if len(self.data_history) > self.max_history_size:
                self.data_history.pop(0)
            
            # Vérifier les alertes
            self._check_alerts(new_data)
            
            # Publier les données sur le bus d'événements
            if self.event_bus:
                self.event_bus.publish("sensor_data", new_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour capteurs: {e}")
            return False
    
    def _check_alerts(self, data: Dict[str, Any]) -> None:
        """Vérifie les alertes de sécurité"""
        try:
            current_time = time.time()
            
            # Vérifier température
            if data.get("temperature") is not None:
                temp = data["temperature"]
                if temp < self.alert_thresholds["temperature"]["min"]:
                    self._add_alert("temperature_low", f"Température basse: {temp}°C", current_time)
                elif temp > self.alert_thresholds["temperature"]["max"]:
                    self._add_alert("temperature_high", f"Température élevée: {temp}°C", current_time)
            
            # Vérifier humidité
            if data.get("humidity") is not None:
                hum = data["humidity"]
                if hum < self.alert_thresholds["humidity"]["min"]:
                    self._add_alert("humidity_low", f"Humidité basse: {hum}%", current_time)
                elif hum > self.alert_thresholds["humidity"]["max"]:
                    self._add_alert("humidity_high", f"Humidité élevée: {hum}%", current_time)
            
            # Vérifier qualité d'air
            if data.get("air_quality") is not None:
                aqi = data["air_quality"]
                if aqi > self.alert_thresholds["air_quality"]["max"]:
                    self._add_alert("air_quality_poor", f"Qualité d'air dégradée: AQI {aqi}", current_time)
            
            # Vérifier niveau d'eau
            if data.get("water_percentage") is not None:
                water = data["water_percentage"]
                if water < self.alert_thresholds["water_level"]["min"]:
                    self._add_alert("water_level_low", f"Niveau d'eau bas: {water}%", current_time)
            
        except Exception as e:
            self.logger.error(f"Erreur vérification alertes: {e}")
    
    def _add_alert(self, alert_type: str, message: str, timestamp: float) -> None:
        """Ajoute une alerte"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": timestamp,
            "acknowledged": False
        }
        
        # Éviter les doublons récents
        recent_alerts = [a for a in self.alerts if a["type"] == alert_type and 
                        timestamp - a["timestamp"] < 300]  # 5 minutes
        if not recent_alerts:
            self.alerts.append(alert)
            self.logger.warning(f"ALERTE: {message}")
            
            # Publier l'alerte sur le bus d'événements
            if self.event_bus:
                self.event_bus.publish("alert", alert)
    
    def get_current_data(self) -> Dict[str, Any]:
        """Retourne les données actuelles"""
        return self.current_data.copy()
    
    def get_data_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retourne l'historique des données"""
        if limit:
            return self.data_history[-limit:]
        return self.data_history.copy()
    
    def get_alerts(self, unacknowledged_only: bool = False) -> List[Dict[str, Any]]:
        """Retourne les alertes"""
        if unacknowledged_only:
            return [alert for alert in self.alerts if not alert["acknowledged"]]
        return self.alerts.copy()
    
    def acknowledge_alert(self, alert_index: int) -> bool:
        """Marque une alerte comme acquittée"""
        try:
            if 0 <= alert_index < len(self.alerts):
                self.alerts[alert_index]["acknowledged"] = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erreur acquittement alerte: {e}")
            return False
    
    def clear_alerts(self) -> None:
        """Efface toutes les alertes"""
        self.alerts.clear()
        self.logger.info("Alertes effacées")
    
    def get_sensor_status(self) -> Dict[str, Any]:
        """Retourne le statut des capteurs"""
        return {
            "dht22": {
                "available": self.dht22 is not None,
                "ready": self.dht22.is_ready() if self.dht22 else False,
                "last_temperature": self.current_data.get("temperature"),
                "last_humidity": self.current_data.get("humidity")
            },
            "air_quality": {
                "available": self.air_quality is not None,
                "ready": self.air_quality.is_ready() if self.air_quality else False,
                "last_aqi": self.current_data.get("air_quality"),
                "last_level": self.current_data.get("air_quality_level")
            },
            "water_sensor": {
                "available": self.water_sensor is not None,
                "ready": self.water_sensor.is_ready() if self.water_sensor else False,
                "last_level": self.current_data.get("water_level"),
                "last_percentage": self.current_data.get("water_percentage"),
                "is_empty": self.water_sensor.is_empty() if self.water_sensor else False,
                "is_full": self.water_sensor.is_full() if self.water_sensor else False
            }
        }
    
    def cleanup(self) -> None:
        """Nettoie les ressources des capteurs"""
        try:
            if self.dht22:
                self.dht22.cleanup()
                self.dht22 = None
            
            if self.air_quality:
                self.air_quality.cleanup()
                self.air_quality = None
            
            if self.water_sensor:
                self.water_sensor.cleanup()
                self.water_sensor = None
            
            self.logger.info("Contrôleur des capteurs nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur capteurs: {e}")

