"""
Contrôleur principal Alimante
Orchestre tous les autres contrôleurs et implémente la logique de contrôle
"""

import time
import logging
import json
from typing import Dict, Any, Optional, List
from .base_controller import BaseController, ControllerConfig, ControllerState, ControllerError
from .sensor_controller import SensorController
from .actuator_controller import ActuatorController
from .device_controller import DeviceController

class MainController(BaseController):
    """
    Contrôleur principal qui orchestre tous les autres contrôleurs
    """
    
    def __init__(self, config: ControllerConfig, config_files: Dict[str, Any], 
                 event_bus: Optional[Any] = None):
        """
        Initialise le contrôleur principal
        
        Args:
            config: Configuration du contrôleur
            config_files: Dictionnaire des fichiers de configuration
            event_bus: Bus d'événements
        """
        super().__init__(config, event_bus)
        self.config_files = config_files
        
        # Sous-contrôleurs
        self.sensor_controller = None
        self.actuator_controller = None
        self.device_controller = None
        
        # Configuration
        self.gpio_config = config_files.get("gpio_config", {})
        self.safety_limits = config_files.get("safety_limits", {})
        self.policies = config_files.get("policies", {})
        self.terrarium_config = config_files.get("terrarium_config", {})
        
        # État du système
        self.system_state = {
            "mode": "auto",  # auto, manual, maintenance
            "emergency_stop": False,
            "last_sensor_data": {},
            "last_actuator_states": {},
            "active_alerts": [],
            "system_uptime": 0
        }
        
        # Logique de contrôle
        self.control_logic = {
            "temperature_control": True,
            "humidity_control": True,
            "lighting_control": True,
            "feeding_control": True,
            "ventilation_control": True
        }
        
        # Historique des décisions
        self.decision_history = []
        self.max_history_size = 1000
        
    def initialize(self) -> bool:
        """
        Initialise le contrôleur principal et tous les sous-contrôleurs
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du contrôleur principal...")
            
            # Initialiser le contrôleur des capteurs
            sensor_config = ControllerConfig(
                name="sensor_controller",
                enabled=True,
                update_interval=2.0,  # Lecture toutes les 2 secondes
                auto_start=False
            )
            self.sensor_controller = SensorController(
                sensor_config, 
                self.gpio_config, 
                self.safety_limits, 
                self.event_bus
            )
            
            if not self.sensor_controller.initialize():
                self.logger.error("Échec initialisation contrôleur capteurs")
                return False
            
            # Initialiser le contrôleur des actionneurs
            actuator_config = ControllerConfig(
                name="actuator_controller",
                enabled=True,
                update_interval=5.0,  # Mise à jour toutes les 5 secondes
                auto_start=False
            )
            self.actuator_controller = ActuatorController(
                actuator_config, 
                self.gpio_config, 
                self.policies, 
                self.event_bus
            )
            
            if not self.actuator_controller.initialize():
                self.logger.error("Échec initialisation contrôleur actionneurs")
                return False
            
            # Initialiser le contrôleur des périphériques
            device_config = ControllerConfig(
                name="device_controller",
                enabled=True,
                update_interval=1.0,  # Mise à jour toutes les secondes
                auto_start=False
            )
            self.device_controller = DeviceController(
                device_config, 
                self.gpio_config, 
                self.event_bus
            )
            
            if not self.device_controller.initialize():
                self.logger.error("Échec initialisation contrôleur périphériques")
                return False
            
            # Configurer les callbacks de l'encodeur
            self._setup_encoder_callbacks()
            
            # Démarrer les sous-contrôleurs
            if not self.sensor_controller.start():
                self.logger.error("Échec démarrage contrôleur capteurs")
                return False
            
            if not self.actuator_controller.start():
                self.logger.error("Échec démarrage contrôleur actionneurs")
                return False
            
            if not self.device_controller.start():
                self.logger.error("Échec démarrage contrôleur périphériques")
                return False
            
            self.logger.info("Contrôleur principal initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation contrôleur principal: {e}")
            return False
    
    def _setup_encoder_callbacks(self) -> None:
        """Configure les callbacks de l'encodeur pour la navigation"""
        if not self.device_controller or not self.device_controller.encoder:
            return
        
        def on_rotation(direction: int, position: int, old_position: int) -> None:
            """Callback de rotation de l'encodeur"""
            try:
                # Navigation entre les écrans
                screens = ["main", "sensors", "actuators", "settings", "alerts"]
                current_screen = self.device_controller.current_screen
                
                if current_screen in screens:
                    current_index = screens.index(current_screen)
                    if direction > 0:  # Rotation horaire
                        new_index = (current_index + 1) % len(screens)
                    else:  # Rotation anti-horaire
                        new_index = (current_index - 1) % len(screens)
                    
                    new_screen = screens[new_index]
                    self.device_controller.set_screen(new_screen)
                    self.logger.debug(f"Navigation: {current_screen} -> {new_screen}")
                
            except Exception as e:
                self.logger.error(f"Erreur callback rotation: {e}")
        
        def on_button_press() -> None:
            """Callback d'appui sur le bouton"""
            try:
                current_screen = self.device_controller.current_screen
                
                if current_screen == "main":
                    # Afficher les détails des capteurs
                    self.device_controller.set_screen("sensors")
                elif current_screen == "sensors":
                    # Afficher les actionneurs
                    self.device_controller.set_screen("actuators")
                elif current_screen == "actuators":
                    # Afficher les paramètres
                    self.device_controller.set_screen("settings")
                elif current_screen == "settings":
                    # Afficher les alertes
                    self.device_controller.set_screen("alerts")
                elif current_screen == "alerts":
                    # Retour à l'écran principal
                    self.device_controller.set_screen("main")
                
                self.logger.debug(f"Bouton pressé sur écran: {current_screen}")
                
            except Exception as e:
                self.logger.error(f"Erreur callback bouton: {e}")
        
        def on_button_release() -> None:
            """Callback de relâchement du bouton"""
            try:
                # Pas d'action particulière au relâchement
                pass
            except Exception as e:
                self.logger.error(f"Erreur callback relâchement: {e}")
        
        # Configurer les callbacks
        self.device_controller.set_encoder_callback("rotation", on_rotation)
        self.device_controller.set_encoder_callback("button_press", on_button_press)
        self.device_controller.set_encoder_callback("button_release", on_button_release)
    
    def update(self) -> bool:
        """
        Met à jour le contrôleur principal et applique la logique de contrôle
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            # Vérifier l'arrêt d'urgence
            if self.system_state["emergency_stop"]:
                self._handle_emergency_stop()
                return True
            
            # Récupérer les données des capteurs
            sensor_data = self.sensor_controller.get_current_data()
            self.system_state["last_sensor_data"] = sensor_data
            
            # Mettre à jour l'écran avec les données
            self.device_controller.update_screen_data("sensor_data", sensor_data)
            
            # Récupérer l'état des actionneurs
            actuator_states = self.actuator_controller.get_actuator_states()
            self.system_state["last_actuator_states"] = actuator_states
            
            # Mettre à jour l'écran avec l'état des actionneurs
            self.device_controller.update_screen_data("actuator_data", actuator_states)
            
            # Récupérer les alertes
            alerts = self.sensor_controller.get_alerts(unacknowledged_only=True)
            self.system_state["active_alerts"] = alerts
            
            # Mettre à jour l'écran avec les alertes
            self.device_controller.update_screen_data("alerts", alerts)
            
            # Appliquer la logique de contrôle automatique
            if self.system_state["mode"] == "auto":
                self._apply_control_logic(sensor_data)
            
            # Mettre à jour le temps de fonctionnement
            self.system_state["system_uptime"] = self.get_uptime()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour contrôleur principal: {e}")
            return False
    
    def _apply_control_logic(self, sensor_data: Dict[str, Any]) -> None:
        """Applique la logique de contrôle automatique"""
        try:
            # Contrôle de température
            if self.control_logic["temperature_control"]:
                self._control_temperature(sensor_data)
            
            # Contrôle d'humidité
            if self.control_logic["humidity_control"]:
                self._control_humidity(sensor_data)
            
            # Contrôle d'éclairage
            if self.control_logic["lighting_control"]:
                self._control_lighting(sensor_data)
            
            # Contrôle de ventilation
            if self.control_logic["ventilation_control"]:
                self._control_ventilation(sensor_data)
            
            # Contrôle d'alimentation
            if self.control_logic["feeding_control"]:
                self._control_feeding(sensor_data)
            
        except Exception as e:
            self.logger.error(f"Erreur logique de contrôle: {e}")
    
    def _control_temperature(self, sensor_data: Dict[str, Any]) -> None:
        """Contrôle la température"""
        try:
            temperature = sensor_data.get("temperature")
            if temperature is None:
                return
            
            # Récupérer les limites de sécurité
            temp_limits = self.safety_limits.get("temperature", {})
            min_temp = temp_limits.get("min", 20)
            max_temp = temp_limits.get("max", 30)
            
            # Récupérer les politiques
            temp_policy = self.policies.get("temperature", {})
            target_temp = temp_policy.get("target", 25)
            tolerance = temp_policy.get("tolerance", 2)
            
            # Contrôler le chauffage
            if temperature < target_temp - tolerance:
                if not self.actuator_controller.actuator_states["heater_on"]:
                    self.actuator_controller.set_heater(True)
                    self._log_decision("heater_on", f"Température basse: {temperature}°C")
            elif temperature > target_temp + tolerance:
                if self.actuator_controller.actuator_states["heater_on"]:
                    self.actuator_controller.set_heater(False)
                    self._log_decision("heater_off", f"Température élevée: {temperature}°C")
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle température: {e}")
    
    def _control_humidity(self, sensor_data: Dict[str, Any]) -> None:
        """Contrôle l'humidité"""
        try:
            humidity = sensor_data.get("humidity")
            if humidity is None:
                return
            
            # Récupérer les limites de sécurité
            hum_limits = self.safety_limits.get("humidity", {})
            min_hum = hum_limits.get("min", 40)
            max_hum = hum_limits.get("max", 70)
            
            # Récupérer les politiques
            hum_policy = self.policies.get("humidity", {})
            target_hum = hum_policy.get("target", 60)
            tolerance = hum_policy.get("tolerance", 10)
            
            # Contrôler l'humidificateur
            if humidity < target_hum - tolerance:
                if not self.actuator_controller.actuator_states["humidifier_on"]:
                    self.actuator_controller.set_humidifier(True)
                    self._log_decision("humidifier_on", f"Humidité basse: {humidity}%")
            elif humidity > target_hum + tolerance:
                if self.actuator_controller.actuator_states["humidifier_on"]:
                    self.actuator_controller.set_humidifier(False)
                    self._log_decision("humidifier_off", f"Humidité élevée: {humidity}%")
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle humidité: {e}")
    
    def _control_lighting(self, sensor_data: Dict[str, Any]) -> None:
        """Contrôle l'éclairage"""
        try:
            # Récupérer les politiques d'éclairage
            lighting_policy = self.policies.get("lighting", {})
            if not lighting_policy:
                return
            
            # Calculer l'intensité basée sur l'heure
            current_hour = time.localtime().tm_hour
            intensity = self._calculate_lighting_intensity(current_hour, lighting_policy)
            
            # Appliquer l'intensité
            if intensity != self.actuator_controller.actuator_states["led_intensity"]:
                self.actuator_controller.set_led_intensity(intensity)
                self._log_decision("led_intensity", f"Intensité: {intensity}%")
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle éclairage: {e}")
    
    def _calculate_lighting_intensity(self, hour: int, policy: Dict[str, Any]) -> int:
        """Calcule l'intensité d'éclairage selon l'heure"""
        try:
            # Récupérer les paramètres
            day_start = policy.get("day_start", 6)
            day_end = policy.get("day_end", 18)
            max_intensity = policy.get("max_intensity", 100)
            min_intensity = policy.get("min_intensity", 0)
            
            if day_start <= hour < day_end:
                # Jour : intensité maximale
                return max_intensity
            else:
                # Nuit : intensité minimale
                return min_intensity
                
        except Exception as e:
            self.logger.error(f"Erreur calcul intensité éclairage: {e}")
            return 0
    
    def _control_ventilation(self, sensor_data: Dict[str, Any]) -> None:
        """Contrôle la ventilation"""
        try:
            air_quality = sensor_data.get("air_quality")
            if air_quality is None:
                return
            
            # Récupérer les politiques de ventilation
            ventilation_policy = self.policies.get("ventilation", {})
            if not ventilation_policy:
                return
            
            # Contrôler la ventilation basée sur la qualité de l'air
            aqi_threshold = ventilation_policy.get("aqi_threshold", 100)
            
            if air_quality > aqi_threshold:
                # Qualité d'air dégradée : augmenter la ventilation
                # (implémentation dépendante du matériel disponible)
                pass
            else:
                # Qualité d'air correcte : ventilation normale
                pass
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle ventilation: {e}")
    
    def _control_feeding(self, sensor_data: Dict[str, Any]) -> None:
        """Contrôle l'alimentation"""
        try:
            # Récupérer les politiques d'alimentation
            feeding_policy = self.policies.get("feeding", {})
            if not feeding_policy:
                return
            
            # Vérifier les horaires d'alimentation
            current_hour = time.localtime().tm_hour
            feeding_times = feeding_policy.get("times", [])
            
            if current_hour in feeding_times:
                # Vérifier si l'alimentation a déjà eu lieu aujourd'hui
                today = time.strftime("%Y-%m-%d")
                last_feeding = self._get_last_feeding_date()
                
                if last_feeding != today:
                    # Effectuer l'alimentation avec double trappe
                    fly_count = feeding_policy.get("fly_count", 5)
                    trap_delay = feeding_policy.get("trap_delay", 1.0)
                    
                    if self.actuator_controller.feed_animals_double_trap(fly_count, trap_delay):
                        self._log_decision("feeding", f"Alimentation {fly_count} mouches effectuée à {current_hour}h")
                        self._set_last_feeding_date(today)
                    else:
                        self.logger.warning(f"Échec alimentation à {current_hour}h")
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle alimentation: {e}")
    
    def _handle_emergency_stop(self) -> None:
        """Gère l'arrêt d'urgence"""
        try:
            # Éteindre tous les actionneurs
            self.actuator_controller.set_heater(False)
            self.actuator_controller.set_humidifier(False)
            self.actuator_controller.set_led_intensity(0)
            
            # Afficher l'alerte sur l'écran
            if self.device_controller and self.device_controller.display:
                self.device_controller.display.show_message(
                    "ARRET D'URGENCE",
                    "Systeme arrete",
                    "Verifiez le systeme",
                    "red"
                )
            
            self.logger.critical("ARRÊT D'URGENCE ACTIVÉ")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt d'urgence: {e}")
    
    def emergency_stop(self) -> None:
        """Active l'arrêt d'urgence"""
        self.system_state["emergency_stop"] = True
        self.logger.critical("Arrêt d'urgence activé par l'utilisateur")
    
    def emergency_resume(self) -> None:
        """Désactive l'arrêt d'urgence"""
        self.system_state["emergency_stop"] = False
        self.logger.info("Arrêt d'urgence désactivé")
    
    def set_mode(self, mode: str) -> bool:
        """
        Définit le mode de fonctionnement
        
        Args:
            mode: Mode ("auto", "manual", "maintenance")
            
        Returns:
            True si succès, False sinon
        """
        try:
            valid_modes = ["auto", "manual", "maintenance"]
            if mode not in valid_modes:
                self.logger.warning(f"Mode invalide: {mode}")
                return False
            
            self.system_state["mode"] = mode
            self.logger.info(f"Mode changé: {mode}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur changement mode: {e}")
            return False
    
    def _log_decision(self, decision_type: str, reason: str) -> None:
        """Enregistre une décision de contrôle"""
        decision = {
            "type": decision_type,
            "reason": reason,
            "timestamp": time.time(),
            "mode": self.system_state["mode"]
        }
        
        self.decision_history.append(decision)
        if len(self.decision_history) > self.max_history_size:
            self.decision_history.pop(0)
        
        self.logger.info(f"Décision: {decision_type} - {reason}")
        
        # Stocker la décision dans la base de données
        if hasattr(self, 'persistence_service') and self.persistence_service:
            self.persistence_service.store_control_decision(
                terrarium_id=self.current_terrarium_id,
                decision_type=decision_type,
                component=component,
                action=action,
                value=value,
                reason=reason,
                success=True
            )
    
    def _get_last_feeding_date(self) -> Optional[str]:
        """Récupère la date de la dernière alimentation"""
        try:
            # Utiliser le service de persistance si disponible
            if hasattr(self, 'persistence_service') and self.persistence_service:
                return self.persistence_service.get_last_feeding_date(self.current_terrarium_id)
            return None
        except Exception:
            return None
    
    def _set_last_feeding_date(self, date: str) -> None:
        """Définit la date de la dernière alimentation"""
        try:
            # Utiliser le service de persistance si disponible
            if hasattr(self, 'persistence_service') and self.persistence_service:
                # Récupérer l'espèce actuelle du terrarium
                species_id = getattr(self, 'current_species_id', 'unknown')
                self.persistence_service.set_last_feeding_date(
                    self.current_terrarium_id, 
                    species_id,
                    notes=f"Alimentation automatique - {date}"
                )
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde date alimentation: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retourne le statut complet du système"""
        return {
            "main_controller": self.get_status(),
            "sensor_controller": self.sensor_controller.get_status() if self.sensor_controller else None,
            "actuator_controller": self.actuator_controller.get_status() if self.actuator_controller else None,
            "device_controller": self.device_controller.get_status() if self.device_controller else None,
            "system_state": self.system_state.copy(),
            "control_logic": self.control_logic.copy()
        }
    
    def cleanup(self) -> None:
        """Nettoie le contrôleur principal et tous les sous-contrôleurs"""
        try:
            # Arrêter les sous-contrôleurs
            if self.sensor_controller:
                self.sensor_controller.stop()
                self.sensor_controller.cleanup()
            
            if self.actuator_controller:
                self.actuator_controller.stop()
                self.actuator_controller.cleanup()
            
            if self.device_controller:
                self.device_controller.stop()
                self.device_controller.cleanup()
            
            self.logger.info("Contrôleur principal nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur principal: {e}")

