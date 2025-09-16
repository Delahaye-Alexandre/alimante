"""
Service de contrôle principal
Orchestre tous les services et applique la logique de contrôle automatique
"""

import time
import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from .sensor_service import SensorService
from .heating_service import HeatingService
from .lighting_service import LightingService
from .humidification_service import HumidificationService
from .ventilation_service import VentilationService
from .feeding_service import FeedingService

class ControlService:
    """
    Service de contrôle principal qui orchestre tous les autres services
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de contrôle
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Services
        self.sensor_service = None
        self.heating_service = None
        self.lighting_service = None
        self.humidification_service = None
        self.ventilation_service = None
        self.feeding_service = None
        
        # Configuration
        self.terrarium_config = config.get('terrarium_config', {})
        self.species_config = config.get('species_config', {})
        self.policies = config.get('policies', {})
        self.safety_limits = config.get('safety_limits', {})
        
        # État du système
        self.system_mode = "auto"  # auto, manual, maintenance, emergency
        self.emergency_stop = False
        self.last_control_time = 0
        self.control_interval = 5.0  # Contrôle toutes les 5 secondes
        
        # Historique des décisions
        self.decision_history = []
        self.max_history_size = 1000
        
        # Statistiques
        self.stats = {
            'control_cycles': 0,
            'decisions_made': 0,
            'errors_count': 0,
            'start_time': time.time()
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service de contrôle et tous les sous-services
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du service de contrôle...")
            
            # Initialiser le service de capteurs
            self.sensor_service = SensorService(config, self.event_bus)
            if not self.sensor_service.initialize():
                self.logger.error("Échec initialisation service capteurs")
                return False
            
            # Initialiser le service de chauffage
            self.heating_service = HeatingService(config, self.event_bus)
            if not self.heating_service.initialize():
                self.logger.error("Échec initialisation service chauffage")
                return False
            
            # Initialiser le service d'éclairage
            self.lighting_service = LightingService(config, self.event_bus)
            if not self.lighting_service.initialize():
                self.logger.error("Échec initialisation service éclairage")
                return False
            
            # Initialiser le service d'humidification
            self.humidification_service = HumidificationService(config, self.event_bus)
            if not self.humidification_service.initialize():
                self.logger.error("Échec initialisation service humidification")
                return False
            
            # Initialiser le service de ventilation
            self.ventilation_service = VentilationService(config, self.event_bus)
            if not self.ventilation_service.initialize():
                self.logger.error("Échec initialisation service ventilation")
                return False
            
            # Initialiser le service d'alimentation
            self.feeding_service = FeedingService(config, self.event_bus)
            if not self.feeding_service.initialize():
                self.logger.error("Échec initialisation service alimentation")
                return False
            
            self.logger.info("Service de contrôle initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service contrôle: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre le service de contrôle et tous les sous-services
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            self.logger.info("Démarrage du service de contrôle...")
            
            # Démarrer tous les services
            services = [
                ('sensor', self.sensor_service),
                ('heating', self.heating_service),
                ('lighting', self.lighting_service),
                ('humidification', self.humidification_service),
                ('ventilation', self.ventilation_service),
                ('feeding', self.feeding_service)
            ]
            
            for service_name, service in services:
                if service and service.start():
                    self.logger.info(f"Service {service_name} démarré")
                else:
                    self.logger.error(f"Échec démarrage service {service_name}")
                    return False
            
            self.logger.info("Service de contrôle démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service contrôle: {e}")
            return False
    
    def stop(self) -> None:
        """Arrête le service de contrôle et tous les sous-services"""
        try:
            self.logger.info("Arrêt du service de contrôle...")
            
            # Arrêter tous les services
            services = [
                self.sensor_service,
                self.heating_service,
                self.lighting_service,
                self.humidification_service,
                self.ventilation_service,
                self.feeding_service
            ]
            
            for service in services:
                if service:
                    service.stop()
            
            self.logger.info("Service de contrôle arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service contrôle: {e}")
    
    def update(self) -> bool:
        """
        Met à jour le service de contrôle et applique la logique de contrôle
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            current_time = time.time()
            
            # Vérifier l'intervalle de contrôle
            if current_time - self.last_control_time < self.control_interval:
                return True
            
            # Mettre à jour les capteurs
            if not self.sensor_service.update():
                self.logger.warning("Échec mise à jour service capteurs")
                return False
            
            # Récupérer les données des capteurs
            sensor_data = self.sensor_service.get_current_data()
            
            # Appliquer la logique de contrôle selon le mode
            if self.system_mode == "auto" and not self.emergency_stop:
                self._apply_automatic_control(sensor_data)
            elif self.system_mode == "manual":
                self._apply_manual_control(sensor_data)
            elif self.system_mode == "maintenance":
                self._apply_maintenance_mode(sensor_data)
            elif self.emergency_stop:
                self._apply_emergency_stop()
            
            # Mettre à jour les services
            self._update_services(sensor_data)
            
            # Mettre à jour les statistiques
            self.stats['control_cycles'] += 1
            self.last_control_time = current_time
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour service contrôle: {e}")
            self.stats['errors_count'] += 1
            return False
    
    def _apply_automatic_control(self, sensor_data: Dict[str, Any]) -> None:
        """Applique le contrôle automatique"""
        try:
            # Récupérer le profil de l'espèce active
            active_terrarium = self.terrarium_config.get('active_terrarium', 'default')
            terrarium = self.terrarium_config.get('terrariums', {}).get(active_terrarium, {})
            species_name = terrarium.get('species', 'default')
            species_profile = self.species_config.get(species_name, {})
            
            # Contrôle de température
            self._control_temperature(sensor_data, species_profile)
            
            # Contrôle d'humidité
            self._control_humidity(sensor_data, species_profile)
            
            # Contrôle d'éclairage
            self._control_lighting(sensor_data, species_profile)
            
            # Contrôle de ventilation
            self._control_ventilation(sensor_data, species_profile)
            
            # Contrôle d'alimentation
            self._control_feeding(sensor_data, species_profile)
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle automatique: {e}")
    
    def _control_temperature(self, sensor_data: Dict[str, Any], species_profile: Dict[str, Any]) -> None:
        """Contrôle la température"""
        try:
            if not self.heating_service:
                return
            
            # Récupérer la température actuelle
            dht22_data = sensor_data.get('dht22', {})
            current_temp = dht22_data.get('temperature')
            
            if current_temp is None:
                return
            
            # Récupérer les paramètres de l'espèce
            temp_profile = species_profile.get('temperature', {})
            day_temp = temp_profile.get('day', 25.0)
            night_temp = temp_profile.get('night', 20.0)
            tolerance = temp_profile.get('tolerance', 2.0)
            
            # Déterminer si c'est le jour ou la nuit
            current_hour = time.localtime().tm_hour
            is_day = 6 <= current_hour < 18
            target_temp = day_temp if is_day else night_temp
            
            # Appliquer le contrôle
            if current_temp < target_temp - tolerance:
                self.heating_service.set_heating(True)
                self._log_decision('heating_on', f"Température basse: {current_temp:.1f}°C (cible: {target_temp:.1f}°C)")
            elif current_temp > target_temp + tolerance:
                self.heating_service.set_heating(False)
                self._log_decision('heating_off', f"Température élevée: {current_temp:.1f}°C (cible: {target_temp:.1f}°C)")
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle température: {e}")
    
    def _control_humidity(self, sensor_data: Dict[str, Any], species_profile: Dict[str, Any]) -> None:
        """Contrôle l'humidité"""
        try:
            if not self.humidification_service:
                return
            
            # Récupérer l'humidité actuelle
            dht22_data = sensor_data.get('dht22', {})
            current_humidity = dht22_data.get('humidity')
            
            if current_humidity is None:
                return
            
            # Récupérer les paramètres de l'espèce
            hum_profile = species_profile.get('humidity', {})
            target_humidity = hum_profile.get('target', 60.0)
            tolerance = hum_profile.get('tolerance', 10.0)
            
            # Appliquer le contrôle
            if current_humidity < target_humidity - tolerance:
                self.humidification_service.set_humidification(True)
                self._log_decision('humidification_on', f"Humidité basse: {current_humidity:.1f}% (cible: {target_humidity:.1f}%)")
            elif current_humidity > target_humidity + tolerance:
                self.humidification_service.set_humidification(False)
                self._log_decision('humidification_off', f"Humidité élevée: {current_humidity:.1f}% (cible: {target_humidity:.1f}%)")
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle humidité: {e}")
    
    def _control_lighting(self, sensor_data: Dict[str, Any], species_profile: Dict[str, Any]) -> None:
        """Contrôle l'éclairage"""
        try:
            if not self.lighting_service:
                return
            
            # Récupérer les paramètres d'éclairage de l'espèce
            lighting_profile = species_profile.get('lighting', {})
            if not lighting_profile:
                return
            
            # Appliquer le contrôle d'éclairage
            self.lighting_service.update_lighting(lighting_profile)
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle éclairage: {e}")
    
    def _control_ventilation(self, sensor_data: Dict[str, Any], species_profile: Dict[str, Any]) -> None:
        """Contrôle la ventilation"""
        try:
            if not self.ventilation_service:
                return
            
            # Récupérer la qualité de l'air
            air_quality_data = sensor_data.get('air_quality', {})
            aqi = air_quality_data.get('aqi')
            
            if aqi is None:
                return
            
            # Appliquer le contrôle de ventilation
            self.ventilation_service.update_ventilation(aqi)
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle ventilation: {e}")
    
    def _control_feeding(self, sensor_data: Dict[str, Any], species_profile: Dict[str, Any]) -> None:
        """Contrôle l'alimentation"""
        try:
            if not self.feeding_service:
                return
            
            # Récupérer les paramètres d'alimentation de l'espèce
            feeding_profile = species_profile.get('feeding', {})
            if not feeding_profile:
                return
            
            # Appliquer le contrôle d'alimentation
            self.feeding_service.update_feeding(feeding_profile)
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle alimentation: {e}")
    
    def _apply_manual_control(self, sensor_data: Dict[str, Any]) -> None:
        """Applique le contrôle manuel"""
        try:
            # En mode manuel, les services restent dans leur état actuel
            # L'utilisateur peut les contrôler via l'interface
            pass
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle manuel: {e}")
    
    def _apply_maintenance_mode(self, sensor_data: Dict[str, Any]) -> None:
        """Applique le mode maintenance"""
        try:
            # En mode maintenance, tous les actionneurs sont arrêtés
            if self.heating_service:
                self.heating_service.set_heating(False)
            
            if self.humidification_service:
                self.humidification_service.set_humidification(False)
            
            if self.lighting_service:
                self.lighting_service.set_lighting(False)
            
            if self.ventilation_service:
                self.ventilation_service.set_ventilation(0)
            
        except Exception as e:
            self.logger.error(f"Erreur mode maintenance: {e}")
    
    def _apply_emergency_stop(self) -> None:
        """Applique l'arrêt d'urgence"""
        try:
            # Arrêter tous les actionneurs
            if self.heating_service:
                self.heating_service.set_heating(False)
            
            if self.humidification_service:
                self.humidification_service.set_humidification(False)
            
            if self.lighting_service:
                self.lighting_service.set_lighting(False)
            
            if self.ventilation_service:
                self.ventilation_service.set_ventilation(0)
            
            if self.feeding_service:
                self.feeding_service.stop_feeding()
            
            self.logger.critical("ARRÊT D'URGENCE ACTIVÉ")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt d'urgence: {e}")
    
    def _update_services(self, sensor_data: Dict[str, Any]) -> None:
        """Met à jour tous les services"""
        try:
            # Mettre à jour les services avec les données des capteurs
            if self.heating_service:
                self.heating_service.update(sensor_data)
            
            if self.lighting_service:
                self.lighting_service.update(sensor_data)
            
            if self.humidification_service:
                self.humidification_service.update(sensor_data)
            
            if self.ventilation_service:
                self.ventilation_service.update(sensor_data)
            
            if self.feeding_service:
                self.feeding_service.update(sensor_data)
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour services: {e}")
    
    def _log_decision(self, decision_type: str, reason: str) -> None:
        """Enregistre une décision de contrôle"""
        decision = {
            'type': decision_type,
            'reason': reason,
            'timestamp': time.time(),
            'mode': self.system_mode
        }
        
        self.decision_history.append(decision)
        if len(self.decision_history) > self.max_history_size:
            self.decision_history.pop(0)
        
        self.stats['decisions_made'] += 1
        self.logger.info(f"Décision: {decision_type} - {reason}")
    
    def set_system_mode(self, mode: str) -> bool:
        """
        Définit le mode du système
        
        Args:
            mode: Mode ("auto", "manual", "maintenance", "emergency")
            
        Returns:
            True si succès, False sinon
        """
        try:
            valid_modes = ["auto", "manual", "maintenance", "emergency"]
            if mode not in valid_modes:
                self.logger.warning(f"Mode invalide: {mode}")
                return False
            
            self.system_mode = mode
            self.logger.info(f"Mode système changé: {mode}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur changement mode: {e}")
            return False
    
    def emergency_stop(self) -> None:
        """Active l'arrêt d'urgence"""
        self.emergency_stop = True
        self.system_mode = "emergency"
        self.logger.critical("Arrêt d'urgence activé")
    
    def emergency_resume(self) -> None:
        """Désactive l'arrêt d'urgence"""
        self.emergency_stop = False
        self.system_mode = "auto"
        self.logger.info("Arrêt d'urgence désactivé")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du système
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'system_mode': self.system_mode,
            'emergency_stop': self.emergency_stop,
            'stats': self.stats.copy(),
            'sensor_service': self.sensor_service.get_sensor_status() if self.sensor_service else None,
            'heating_service': self.heating_service.get_status() if self.heating_service else None,
            'lighting_service': self.lighting_service.get_status() if self.lighting_service else None,
            'humidification_service': self.humidification_service.get_status() if self.humidification_service else None,
            'ventilation_service': self.ventilation_service.get_status() if self.ventilation_service else None,
            'feeding_service': self.feeding_service.get_status() if self.feeding_service else None
        }
    
    def get_decision_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Retourne l'historique des décisions
        
        Args:
            hours: Nombre d'heures d'historique
            
        Returns:
            Liste des décisions
        """
        cutoff_time = time.time() - (hours * 3600)
        return [decision for decision in self.decision_history if decision['timestamp'] >= cutoff_time]
    
    def cleanup(self) -> None:
        """Nettoie le service de contrôle"""
        try:
            self.stop()
            
            # Nettoyer tous les services
            services = [
                self.sensor_service,
                self.heating_service,
                self.lighting_service,
                self.humidification_service,
                self.ventilation_service,
                self.feeding_service
            ]
            
            for service in services:
                if service:
                    service.cleanup()
            
            self.logger.info("Service de contrôle nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service contrôle: {e}")

