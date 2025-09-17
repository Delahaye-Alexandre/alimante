"""
Contrôleur des périphériques Alimante
Gère l'écran ST7735 et l'encodeur rotatif
"""

import time
import logging
from typing import Dict, Any, Optional, List, Callable
from .base_controller import BaseController, ControllerConfig, ControllerState, ControllerError
from .drivers import ST7735Driver, RotaryEncoderDriver, DriverConfig

class DeviceController(BaseController):
    """
    Contrôleur des périphériques (écran et encodeur)
    """
    
    def __init__(self, config: ControllerConfig, gpio_config: Dict[str, Any], 
                 event_bus: Optional[Any] = None):
        """
        Initialise le contrôleur des périphériques
        
        Args:
            config: Configuration du contrôleur
            gpio_config: Configuration GPIO
            event_bus: Bus d'événements
        """
        super().__init__(config, event_bus)
        self.gpio_config = gpio_config
        
        # Périphériques
        self.display = None
        self.encoder = None
        
        # État de l'écran
        self.current_screen = "main"
        self.screen_data = {}
        self.display_brightness = 100
        
        # État de l'encodeur
        self.encoder_position = 0
        self.encoder_pressed = False
        self.encoder_callbacks = {
            "rotation": None,
            "button_press": None,
            "button_release": None
        }
        
        # Historique des interactions
        self.interaction_history = []
        self.max_history_size = 200
        
    def initialize(self) -> bool:
        """
        Initialise les périphériques
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du contrôleur des périphériques...")
            
            # Initialiser écran ST7735
            if "ui" in self.gpio_config and "display" in self.gpio_config["ui"]:
                try:
                    display_config = DriverConfig(name="st7735", enabled=True)
                    display_pins = self.gpio_config["ui"]["display"]
                    self.display = ST7735Driver(
                        display_config,
                        dc_pin=display_pins["dc"],
                        rst_pin=display_pins["rst"]
                    )
                    if self.display.initialize():
                        self.logger.info("Écran ST7735 initialisé")
                        self._show_startup_screen()
                    else:
                        self.logger.warning("Échec initialisation écran ST7735")
                        self.display = None
                except Exception as e:
                    self.logger.error(f"Erreur initialisation écran ST7735: {e}")
                    self.display = None
            
            # Initialiser encodeur rotatif
            if "ui" in self.gpio_config and "encoder" in self.gpio_config["ui"]:
                try:
                    encoder_config = DriverConfig(name="rotary_encoder", enabled=True)
                    encoder_pins = self.gpio_config["ui"]["encoder"]
                    self.encoder = RotaryEncoderDriver(
                        encoder_config,
                        clk_pin=encoder_pins["clk"],
                        dt_pin=encoder_pins["dt"],
                        sw_pin=encoder_pins["sw"]
                    )
                    if self.encoder.initialize():
                        self.logger.info("Encodeur rotatif initialisé")
                        self._setup_encoder_callbacks()
                    else:
                        self.logger.warning("Échec initialisation encodeur rotatif")
                        self.encoder = None
                except Exception as e:
                    self.logger.error(f"Erreur initialisation encodeur rotatif: {e}")
                    self.encoder = None
            
            # Vérifier qu'au moins un périphérique est initialisé
            if not any([self.display, self.encoder]):
                self.logger.error("Aucun périphérique initialisé")
                return False
            
            self.logger.info("Contrôleur des périphériques initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation contrôleur périphériques: {e}")
            return False
    
    def _setup_encoder_callbacks(self) -> None:
        """Configure les callbacks de l'encodeur"""
        if not self.encoder:
            return
        
        def on_rotation(direction: int, position: int, old_position: int) -> None:
            self.encoder_position = position
            self._log_interaction("rotation", {"direction": direction, "position": position})
            
            # Appeler le callback personnalisé
            if self.encoder_callbacks["rotation"]:
                try:
                    self.encoder_callbacks["rotation"](direction, position, old_position)
                except Exception as e:
                    self.logger.error(f"Erreur callback rotation: {e}")
        
        def on_button_press() -> None:
            self.encoder_pressed = True
            self._log_interaction("button_press", {})
            
            # Appeler le callback personnalisé
            if self.encoder_callbacks["button_press"]:
                try:
                    self.encoder_callbacks["button_press"]()
                except Exception as e:
                    self.logger.error(f"Erreur callback bouton pressé: {e}")
        
        def on_button_release() -> None:
            self.encoder_pressed = False
            self._log_interaction("button_release", {})
            
            # Appeler le callback personnalisé
            if self.encoder_callbacks["button_release"]:
                try:
                    self.encoder_callbacks["button_release"]()
                except Exception as e:
                    self.logger.error(f"Erreur callback bouton relâché: {e}")
        
        # Configurer les callbacks
        self.encoder.set_rotation_callback(on_rotation)
        self.encoder.set_button_callback(on_button_press, on_button_release)
    
    def update(self) -> bool:
        """
        Met à jour les périphériques
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            # Mise à jour de l'écran si nécessaire
            if self.display and self.current_screen:
                self._update_display()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour périphériques: {e}")
            return False
    
    def _show_startup_screen(self) -> None:
        """Affiche l'écran de démarrage"""
        if not self.display:
            return
        
        try:
            self.display.show_message(
                "ALIMANTE",
                "Systeme de controle",
                "Terrarium automatique",
                "green"
            )
            time.sleep(2)
        except Exception as e:
            self.logger.error(f"Erreur écran de démarrage: {e}")
    
    def _update_display(self) -> None:
        """Met à jour l'affichage selon l'écran actuel"""
        if not self.display:
            return
        
        try:
            if self.current_screen == "main":
                self._show_main_screen()
            elif self.current_screen == "sensors":
                self._show_sensors_screen()
            elif self.current_screen == "actuators":
                self._show_actuators_screen()
            elif self.current_screen == "settings":
                self._show_settings_screen()
            elif self.current_screen == "alerts":
                self._show_alerts_screen()
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour affichage: {e}")
    
    def _show_main_screen(self) -> None:
        """Affiche l'écran principal"""
        if not self.display:
            return
        
        try:
            # Récupérer les données des capteurs depuis le bus d'événements
            sensor_data = self.screen_data.get("sensor_data", {})
            
            temp = sensor_data.get("temperature", "N/A")
            hum = sensor_data.get("humidity", "N/A")
            aqi = sensor_data.get("air_quality", "N/A")
            water = sensor_data.get("water_percentage", "N/A")
            
            # Afficher les données
            self.display.show_message(
                f"T: {temp}°C H: {hum}%",
                f"AQI: {aqi} Eau: {water}%",
                "Tournez pour naviguer",
                "white"
            )
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran principal: {e}")
    
    def _show_sensors_screen(self) -> None:
        """Affiche l'écran des capteurs"""
        if not self.display:
            return
        
        try:
            sensor_data = self.screen_data.get("sensor_data", {})
            
            self.display.show_message(
                "CAPTEURS",
                f"T: {sensor_data.get('temperature', 'N/A')}°C",
                f"H: {sensor_data.get('humidity', 'N/A')}%",
                "blue"
            )
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran capteurs: {e}")
    
    def _show_actuators_screen(self) -> None:
        """Affiche l'écran des actionneurs"""
        if not self.display:
            return
        
        try:
            actuator_data = self.screen_data.get("actuator_data", {})
            
            heater = "ON" if actuator_data.get("heater_on", False) else "OFF"
            humidifier = "ON" if actuator_data.get("humidifier_on", False) else "OFF"
            led = f"{actuator_data.get('led_intensity', 0)}%"
            
            self.display.show_message(
                "ACTIONNEURS",
                f"Chauffage: {heater}",
                f"Humidif: {humidifier} LED: {led}",
                "yellow"
            )
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran actionneurs: {e}")
    
    def _show_settings_screen(self) -> None:
        """Affiche l'écran des paramètres"""
        if not self.display:
            return
        
        try:
            self.display.show_message(
                "PARAMETRES",
                "Controle auto: ON",
                "Mode: Normal",
                "cyan"
            )
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran paramètres: {e}")
    
    def _show_alerts_screen(self) -> None:
        """Affiche l'écran des alertes"""
        if not self.display:
            return
        
        try:
            alerts = self.screen_data.get("alerts", [])
            
            if alerts:
                alert = alerts[0]  # Afficher la première alerte
                self.display.show_message(
                    "ALERTE",
                    alert.get("type", "Unknown"),
                    alert.get("message", "No message"),
                    "red"
                )
            else:
                self.display.show_message(
                    "ALERTES",
                    "Aucune alerte",
                    "Systeme OK",
                    "green"
                )
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran alertes: {e}")
    
    def set_screen(self, screen_name: str) -> bool:
        """
        Change l'écran affiché
        
        Args:
            screen_name: Nom de l'écran ("main", "sensors", "actuators", "settings", "alerts")
            
        Returns:
            True si succès, False sinon
        """
        try:
            valid_screens = ["main", "sensors", "actuators", "settings", "alerts"]
            if screen_name not in valid_screens:
                self.logger.warning(f"Écran invalide: {screen_name}")
                return False
            
            self.current_screen = screen_name
            self._log_interaction("screen_change", {"screen": screen_name})
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur changement écran: {e}")
            return False
    
    def update_screen_data(self, data_type: str, data: Dict[str, Any]) -> None:
        """
        Met à jour les données d'affichage
        
        Args:
            data_type: Type de données ("sensor_data", "actuator_data", "alerts")
            data: Données à afficher
        """
        try:
            self.screen_data[data_type] = data
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données écran: {e}")
    
    def set_encoder_callback(self, callback_type: str, callback: Callable) -> None:
        """
        Définit un callback pour l'encodeur
        
        Args:
            callback_type: Type de callback ("rotation", "button_press", "button_release")
            callback: Fonction de callback
        """
        try:
            if callback_type in self.encoder_callbacks:
                self.encoder_callbacks[callback_type] = callback
            else:
                self.logger.warning(f"Type de callback invalide: {callback_type}")
        except Exception as e:
            self.logger.error(f"Erreur définition callback: {e}")
    
    def get_encoder_state(self) -> Dict[str, Any]:
        """Retourne l'état de l'encodeur"""
        return {
            "position": self.encoder_position,
            "pressed": self.encoder_pressed,
            "available": self.encoder is not None,
            "ready": self.encoder.is_ready() if self.encoder else False
        }
    
    def get_display_state(self) -> Dict[str, Any]:
        """Retourne l'état de l'écran"""
        return {
            "current_screen": self.current_screen,
            "brightness": self.display_brightness,
            "available": self.display is not None,
            "ready": self.display.is_ready() if self.display else False
        }
    
    def get_interaction_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retourne l'historique des interactions"""
        if limit:
            return self.interaction_history[-limit:]
        return self.interaction_history.copy()
    
    def _log_interaction(self, interaction_type: str, data: Dict[str, Any]) -> None:
        """Enregistre une interaction dans l'historique"""
        interaction = {
            "type": interaction_type,
            "data": data,
            "timestamp": time.time()
        }
        
        self.interaction_history.append(interaction)
        if len(self.interaction_history) > self.max_history_size:
            self.interaction_history.pop(0)
        
        # Publier l'interaction sur le bus d'événements
        if self.event_bus:
            self.event_bus.emit("device_interaction", interaction)
    
    def cleanup(self) -> None:
        """Nettoie les ressources des périphériques"""
        try:
            if self.display:
                self.display.clear_screen("black")
                self.display.cleanup()
                self.display = None
            
            if self.encoder:
                self.encoder.cleanup()
                self.encoder = None
            
            self.logger.info("Contrôleur des périphériques nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur périphériques: {e}")

