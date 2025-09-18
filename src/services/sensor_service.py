"""
Service de gestion des capteurs
Centralise la lecture et le traitement des données des capteurs
"""

import time
import logging
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from controllers.sensor_controller import SensorController
from controllers.drivers.dht22_sensor import DHT22Sensor
from controllers.drivers.air_quality_sensor import AirQualitySensor
from controllers.drivers.tenflyer_water_sensor import TenflyerWaterSensor

class SensorService:
    """
    Service centralisé pour la gestion des capteurs
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de capteurs
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Capteurs
        self.sensors = {}
        self.sensor_data = {}
        self.sensor_alerts = []
        
        # Configuration des capteurs
        self.sensor_configs = config.get('sensors', {})
        self.safety_limits = config.get('safety_limits', {})
        
        # Historique des données
        self.data_history = []
        self.max_history_size = 1000
        
        # État du service
        self.is_running = False
        self.last_update_time = 0
        self.update_interval = 1.0  # Mise à jour toutes les secondes
        
    def initialize(self) -> bool:
        """
        Initialise le service de capteurs
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du service de capteurs...")
            
            # Initialiser le capteur DHT22 (température/humidité)
            if self.sensor_configs.get('temperature', {}).get('enabled', False):
                self._initialize_dht22_sensor()
            
            # Initialiser le capteur de qualité d'air
            if self.sensor_configs.get('air_quality', {}).get('enabled', False):
                self._initialize_air_quality_sensor()
            
            # Initialiser le capteur de niveau d'eau
            if self.sensor_configs.get('water_level', {}).get('enabled', False):
                self._initialize_water_level_sensor()
            
            self.logger.info("Service de capteurs initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service capteurs: {e}")
            return False
    
    def _initialize_dht22_sensor(self) -> None:
        """Initialise le capteur DHT22"""
        try:
            from controllers.drivers.base_driver import DriverConfig, DriverState
            
            config = DriverConfig(
                name="dht22",
                enabled=True,
                timeout=5.0,
                retry_attempts=3,
                retry_delay=1.0
            )
            
            # Récupérer le pin depuis la configuration GPIO
            from utils.gpio_config import get_sensor_pin
            gpio_pin = get_sensor_pin('dht22_temperature_humidity')
            
            self.sensors['dht22'] = DHT22Sensor(config, gpio_pin)
            
            if self.sensors['dht22'].initialize():
                self.logger.info("Capteur DHT22 initialisé")
            else:
                self.logger.error("Échec initialisation capteur DHT22")
                
        except Exception as e:
            self.logger.error(f"Erreur initialisation DHT22: {e}")
    
    def _initialize_air_quality_sensor(self) -> None:
        """Initialise le capteur de qualité d'air"""
        try:
            from controllers.drivers.base_driver import DriverConfig
            
            config = DriverConfig(
                name="air_quality",
                enabled=True,
                timeout=5.0,
                retry_attempts=3,
                retry_delay=1.0
            )
            
            # Récupérer le pin depuis la configuration GPIO
            from utils.gpio_config import get_sensor_pin
            gpio_pin = get_sensor_pin('air_quality')
            
            self.sensors['air_quality'] = AirQualitySensor(config, gpio_pin)
            
            if self.sensors['air_quality'].initialize():
                self.logger.info("Capteur qualité d'air initialisé")
            else:
                self.logger.error("Échec initialisation capteur qualité d'air")
                
        except Exception as e:
            self.logger.error(f"Erreur initialisation capteur qualité d'air: {e}")
    
    def _initialize_water_level_sensor(self) -> None:
        """Initialise le capteur de niveau d'eau"""
        try:
            from controllers.drivers.base_driver import DriverConfig
            
            config = DriverConfig(
                name="water_level",
                enabled=True,
                timeout=5.0,
                retry_attempts=3,
                retry_delay=1.0
            )
            
            # Récupérer le pin depuis la configuration GPIO
            from utils.gpio_config import get_sensor_pin
            gpio_pin = get_sensor_pin('water_level')
            
            self.sensors['water_level'] = TenflyerWaterSensor(config, gpio_pin)
            
            if self.sensors['water_level'].initialize():
                self.logger.info("Capteur niveau d'eau initialisé")
            else:
                self.logger.error("Échec initialisation capteur niveau d'eau")
                
        except Exception as e:
            self.logger.error(f"Erreur initialisation capteur niveau d'eau: {e}")
    
    def start(self) -> bool:
        """
        Démarre le service de capteurs
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            self.logger.info("Démarrage du service de capteurs...")
            
            # Démarrer tous les capteurs
            for sensor_name, sensor in self.sensors.items():
                if sensor.start():
                    self.logger.info(f"Capteur {sensor_name} démarré")
                else:
                    self.logger.warning(f"Échec démarrage capteur {sensor_name}")
            
            self.is_running = True
            self.last_update_time = time.time()
            
            self.logger.info("Service de capteurs démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service capteurs: {e}")
            return False
    
    def stop(self) -> None:
        """Arrête le service de capteurs"""
        try:
            self.logger.info("Arrêt du service de capteurs...")
            
            # Arrêter tous les capteurs
            for sensor_name, sensor in self.sensors.items():
                sensor.stop()
                self.logger.info(f"Capteur {sensor_name} arrêté")
            
            self.is_running = False
            self.logger.info("Service de capteurs arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service capteurs: {e}")
    
    def update(self) -> bool:
        """
        Met à jour les données des capteurs
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            if not self.is_running:
                return False
            
            current_time = time.time()
            if current_time - self.last_update_time < self.update_interval:
                return True
            
            # Lire les données de tous les capteurs
            new_data = {}
            for sensor_name, sensor in self.sensors.items():
                try:
                    sensor_data = sensor.read()
                    if sensor_data:
                        new_data[sensor_name] = sensor_data
                except Exception as e:
                    self.logger.warning(f"Erreur lecture capteur {sensor_name}: {e}")
            
            # Mettre à jour les données
            self.sensor_data.update(new_data)
            
            # Vérifier les alertes
            self._check_alerts()
            
            # Ajouter à l'historique
            self._add_to_history(new_data)
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('sensor_data_updated', {
                    'data': new_data,
                    'timestamp': current_time
                })
            
            self.last_update_time = current_time
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour service capteurs: {e}")
            return False
    
    def _check_alerts(self) -> None:
        """Vérifie les alertes basées sur les données des capteurs"""
        try:
            current_time = time.time()
            
            # Vérifier la température
            if 'dht22' in self.sensor_data:
                temp_data = self.sensor_data['dht22']
                temperature = temp_data.get('temperature')
                humidity = temp_data.get('humidity')
                
                if temperature is not None:
                    self._check_temperature_alert(temperature, current_time)
                
                if humidity is not None:
                    self._check_humidity_alert(humidity, current_time)
            
            # Vérifier la qualité de l'air
            if 'air_quality' in self.sensor_data:
                air_data = self.sensor_data['air_quality']
                aqi = air_data.get('aqi')
                
                if aqi is not None:
                    self._check_air_quality_alert(aqi, current_time)
            
            # Vérifier le niveau d'eau
            if 'water_level' in self.sensor_data:
                water_data = self.sensor_data['water_level']
                level = water_data.get('level')
                
                if level is not None:
                    self._check_water_level_alert(level, current_time)
                    
        except Exception as e:
            self.logger.error(f"Erreur vérification alertes: {e}")
    
    def _check_temperature_alert(self, temperature: float, timestamp: float) -> None:
        """Vérifie les alertes de température"""
        temp_limits = self.safety_limits.get('temperature', {})
        
        # Alerte critique
        critical_max = temp_limits.get('critical_max', 45.0)
        critical_min = temp_limits.get('critical_min', 5.0)
        
        if temperature > critical_max:
            self._add_alert('temperature_critical_high', 
                          f"Température critique élevée: {temperature:.1f}°C", 
                          'critical', timestamp)
        elif temperature < critical_min:
            self._add_alert('temperature_critical_low', 
                          f"Température critique basse: {temperature:.1f}°C", 
                          'critical', timestamp)
        
        # Alerte d'avertissement
        warning_max = temp_limits.get('warning_max', 40.0)
        warning_min = temp_limits.get('warning_min', 10.0)
        
        if temperature > warning_max:
            self._add_alert('temperature_warning_high', 
                          f"Température élevée: {temperature:.1f}°C", 
                          'warning', timestamp)
        elif temperature < warning_min:
            self._add_alert('temperature_warning_low', 
                          f"Température basse: {temperature:.1f}°C", 
                          'warning', timestamp)
    
    def _check_humidity_alert(self, humidity: float, timestamp: float) -> None:
        """Vérifie les alertes d'humidité"""
        hum_limits = self.safety_limits.get('humidity', {})
        
        # Alerte critique
        critical_max = hum_limits.get('critical_max', 99.0)
        critical_min = hum_limits.get('critical_min', 10.0)
        
        if humidity > critical_max:
            self._add_alert('humidity_critical_high', 
                          f"Humidité critique élevée: {humidity:.1f}%", 
                          'critical', timestamp)
        elif humidity < critical_min:
            self._add_alert('humidity_critical_low', 
                          f"Humidité critique basse: {humidity:.1f}%", 
                          'critical', timestamp)
    
    def _check_air_quality_alert(self, aqi: int, timestamp: float) -> None:
        """Vérifie les alertes de qualité d'air"""
        air_limits = self.safety_limits.get('air_quality', {})
        
        hazardous_threshold = air_limits.get('hazardous_threshold', 300)
        unhealthy_threshold = air_limits.get('unhealthy_threshold', 150)
        
        if aqi >= hazardous_threshold:
            self._add_alert('air_quality_hazardous', 
                          f"Qualité d'air dangereuse: AQI {aqi}", 
                          'critical', timestamp)
        elif aqi >= unhealthy_threshold:
            self._add_alert('air_quality_unhealthy', 
                          f"Qualité d'air malsaine: AQI {aqi}", 
                          'warning', timestamp)
    
    def _check_water_level_alert(self, level: float, timestamp: float) -> None:
        """Vérifie les alertes de niveau d'eau"""
        water_limits = self.safety_limits.get('water_level', {})
        
        critical_level = water_limits.get('critical_level', 15.0)
        warning_level = water_limits.get('warning_level', 20.0)
        
        if level <= critical_level:
            self._add_alert('water_level_critical', 
                          f"Niveau d'eau critique: {level:.1f}%", 
                          'critical', timestamp)
        elif level <= warning_level:
            self._add_alert('water_level_warning', 
                          f"Niveau d'eau bas: {level:.1f}%", 
                          'warning', timestamp)
    
    def _add_alert(self, alert_type: str, message: str, level: str, timestamp: float) -> None:
        """Ajoute une alerte"""
        alert = {
            'type': alert_type,
            'message': message,
            'level': level,
            'timestamp': timestamp,
            'acknowledged': False
        }
        
        # Vérifier si l'alerte existe déjà
        for existing_alert in self.sensor_alerts:
            if (existing_alert['type'] == alert_type and 
                not existing_alert['acknowledged'] and
                timestamp - existing_alert['timestamp'] < 300):  # 5 minutes
                return
        
        self.sensor_alerts.append(alert)
        self.logger.warning(f"Alerte {level}: {message}")
        
        # Émettre un événement d'alerte
        if self.event_bus:
            self.event_bus.emit('sensor_alert', alert)
    
    def _add_to_history(self, data: Dict[str, Any]) -> None:
        """Ajoute des données à l'historique"""
        history_entry = {
            'timestamp': time.time(),
            'data': data.copy()
        }
        
        self.data_history.append(history_entry)
        
        # Limiter la taille de l'historique
        if len(self.data_history) > self.max_history_size:
            self.data_history.pop(0)
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Retourne les données actuelles des capteurs
        
        Returns:
            Dictionnaire des données actuelles
        """
        if not self.sensor_data:
            # Si aucun capteur n'est disponible, retourner un dictionnaire vide
            self.logger.warning("Aucun capteur détecté - données manquantes")
            return {}
        return self.sensor_data.copy()
    
    def get_sensor_data(self, sensor_name: str) -> Optional[Dict[str, Any]]:
        """
        Retourne les données d'un capteur spécifique
        
        Args:
            sensor_name: Nom du capteur
            
        Returns:
            Données du capteur ou None
        """
        return self.sensor_data.get(sensor_name)
    
    def get_alerts(self, unacknowledged_only: bool = False) -> List[Dict[str, Any]]:
        """
        Retourne les alertes
        
        Args:
            unacknowledged_only: Si True, retourne seulement les alertes non acquittées
            
        Returns:
            Liste des alertes
        """
        if unacknowledged_only:
            return [alert for alert in self.sensor_alerts if not alert['acknowledged']]
        return self.sensor_alerts.copy()
    
    def acknowledge_alert(self, alert_index: int) -> bool:
        """
        Acquitte une alerte
        
        Args:
            alert_index: Index de l'alerte à acquitter
            
        Returns:
            True si succès, False sinon
        """
        try:
            if 0 <= alert_index < len(self.sensor_alerts):
                self.sensor_alerts[alert_index]['acknowledged'] = True
                self.logger.info(f"Alerte {alert_index} acquittée")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erreur acquittement alerte: {e}")
            return False
    
    def get_data_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Retourne l'historique des données
        
        Args:
            hours: Nombre d'heures d'historique à retourner
            
        Returns:
            Liste des données historiques
        """
        cutoff_time = time.time() - (hours * 3600)
        return [entry for entry in self.data_history if entry['timestamp'] >= cutoff_time]
    
    def get_sensor_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service de capteurs
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_running': self.is_running,
            'sensors_count': len(self.sensors),
            'active_sensors': [name for name, sensor in self.sensors.items() if sensor.is_running()],
            'last_update': self.last_update_time,
            'alerts_count': len([a for a in self.sensor_alerts if not a['acknowledged']]),
            'data_points': len(self.data_history)
        }
    
    def cleanup(self) -> None:
        """Nettoie le service de capteurs"""
        try:
            self.stop()
            
            # Nettoyer tous les capteurs
            for sensor in self.sensors.values():
                sensor.cleanup()
            
            self.sensors.clear()
            self.sensor_data.clear()
            self.sensor_alerts.clear()
            self.data_history.clear()
            
            self.logger.info("Service de capteurs nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service capteurs: {e}")

