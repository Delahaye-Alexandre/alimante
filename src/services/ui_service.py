"""
Service de gestion de l'interface utilisateur Alimante
Gère l'affichage LCD et l'encodeur rotatif
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime

class UIMode(Enum):
    """Modes d'interface utilisateur"""
    AUTO = "auto"           # Mode automatique
    MANUAL = "manual"       # Mode manuel
    CONFIG = "config"       # Mode configuration
    ALERT = "alert"         # Mode alerte

class UIScreen(Enum):
    """Écrans de l'interface"""
    HOME = "home"
    SENSORS = "sensors"
    CONTROLS = "controls"
    CONFIG = "config"
    ALERTS = "alerts"
    TERRARIUMS = "terrariums"
    SPECIES = "species"

class UIService:
    """
    Service de gestion de l'interface utilisateur
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service d'interface utilisateur
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Configuration de l'interface
        self.ui_config = config.get('ui', {})
        self.lcd_enabled = self.ui_config.get('lcd_enabled', True)
        self.encoder_enabled = self.ui_config.get('encoder_enabled', True)
        self.auto_refresh = self.ui_config.get('auto_refresh', True)
        self.refresh_interval = self.ui_config.get('refresh_interval', 1.0)  # secondes
        
        # État de l'interface
        self.current_mode = UIMode.AUTO
        self.current_screen = UIScreen.HOME
        self.is_running = False
        self.last_update = None
        
        # Données d'affichage
        self.display_data = {
            'temperature': 0.0,
            'humidity': 0.0,
            'air_quality': 0.0,
            'water_level': 0.0,
            'heating': False,
            'humidifying': False,
            'lighting': False,
            'ventilation': False,
            'alerts': [],
            'terrarium': 'default',
            'species': 'unknown'
        }
        
        # Interface LCD
        self.lcd_interface = None
        self.lcd_thread = None
        
        # Interface encodeur
        self.encoder_interface = None
        self.encoder_thread = None
        
        # Threads
        self.ui_thread = None
        self.stop_event = threading.Event()
        
        # Callbacks
        self.screen_callbacks = {}
        self.mode_callbacks = {}
        
        # Statistiques
        self.stats = {
            'screen_changes': 0,
            'mode_changes': 0,
            'encoder_events': 0,
            'lcd_updates': 0,
            'errors': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service d'interface utilisateur
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            # Initialiser l'interface LCD
            if self.lcd_enabled:
                self._initialize_lcd()
            
            # Initialiser l'interface encodeur
            if self.encoder_enabled:
                self._initialize_encoder()
            
            self.logger.info("Service d'interface utilisateur initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service UI: {e}")
            self.stats['errors'] += 1
            return False
    
    def start(self) -> bool:
        """
        Démarre le service d'interface utilisateur
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if self.is_running:
                self.logger.warning("Service UI déjà en cours d'exécution")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Démarrer le thread principal
            self.ui_thread = threading.Thread(target=self._ui_loop, daemon=True)
            self.ui_thread.start()
            
            # Démarrer l'interface LCD
            if self.lcd_interface:
                self.lcd_thread = threading.Thread(target=self._lcd_loop, daemon=True)
                self.lcd_thread.start()
            
            # Démarrer l'interface encodeur
            if self.encoder_interface:
                self.encoder_thread = threading.Thread(target=self._encoder_loop, daemon=True)
                self.encoder_thread.start()
            
            self.logger.info("Service d'interface utilisateur démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service UI: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête le service d'interface utilisateur"""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            self.stop_event.set()
            
            # Attendre que les threads se terminent
            if self.ui_thread and self.ui_thread.is_alive():
                self.ui_thread.join(timeout=5)
            
            if self.lcd_thread and self.lcd_thread.is_alive():
                self.lcd_thread.join(timeout=5)
            
            if self.encoder_thread and self.encoder_thread.is_alive():
                self.encoder_thread.join(timeout=5)
            
            self.logger.info("Service d'interface utilisateur arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service UI: {e}")
            self.stats['errors'] += 1
    
    def _initialize_lcd(self) -> None:
        """Initialise l'interface LCD"""
        try:
            from ui.lcd_interface import LCDInterface
            from utils.event_bus import EventBus
            
            # Créer l'interface LCD
            self.lcd_interface = LCDInterface(self.config, self.event_bus)
            
            if not self.lcd_interface.initialize():
                self.logger.error("Échec initialisation interface LCD")
                self.lcd_interface = None
                return
            
            self.logger.info("Interface LCD initialisée")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation interface LCD: {e}")
            self.lcd_interface = None
    
    def _initialize_encoder(self) -> None:
        """Initialise l'interface encodeur"""
        try:
            from ui.encoder_interface import EncoderInterface
            
            # Créer l'interface encodeur
            self.encoder_interface = EncoderInterface(self.config, self.event_bus)
            
            if not self.encoder_interface.initialize():
                self.logger.error("Échec initialisation interface encodeur")
                self.encoder_interface = None
                return
            
            # Configurer les callbacks
            self.encoder_interface.set_rotation_callback(self._handle_encoder_rotation)
            self.encoder_interface.set_button_callback(self._handle_encoder_button)
            
            self.logger.info("Interface encodeur initialisée")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation interface encodeur: {e}")
            self.encoder_interface = None
    
    def _ui_loop(self) -> None:
        """Boucle principale de l'interface utilisateur"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Mettre à jour l'affichage
                    self._update_display()
                    
                    # Attendre avant la prochaine mise à jour
                    self.stop_event.wait(self.refresh_interval)
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle UI: {e}")
                    self.stats['errors'] += 1
                    time.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle UI: {e}")
            self.stats['errors'] += 1
    
    def _lcd_loop(self) -> None:
        """Boucle de l'interface LCD"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    if self.lcd_interface:
                        # Mettre à jour l'affichage LCD
                        self.lcd_interface.update()
                        self.stats['lcd_updates'] += 1
                    
                    # Attendre avant la prochaine mise à jour
                    self.stop_event.wait(0.1)  # Mise à jour rapide pour l'encodeur
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle LCD: {e}")
                    self.stats['errors'] += 1
                    time.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle LCD: {e}")
            self.stats['errors'] += 1
    
    def _encoder_loop(self) -> None:
        """Boucle de l'interface encodeur"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    if self.encoder_interface:
                        # Mettre à jour l'encodeur
                        self.encoder_interface.update()
                    
                    # Attendre avant la prochaine mise à jour
                    self.stop_event.wait(0.01)  # Mise à jour très rapide pour l'encodeur
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle encodeur: {e}")
                    self.stats['errors'] += 1
                    time.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle encodeur: {e}")
            self.stats['errors'] += 1
    
    def _update_display(self) -> None:
        """Met à jour l'affichage"""
        try:
            # Mettre à jour les données d'affichage
            self._refresh_display_data()
            
            # Mettre à jour l'écran LCD
            if self.lcd_interface:
                self._update_lcd_display()
            
            self.last_update = time.time()
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour affichage: {e}")
            self.stats['errors'] += 1
    
    def _refresh_display_data(self) -> None:
        """Rafraîchit les données d'affichage"""
        try:
            # Cette méthode devrait interroger les services pour récupérer les données
            # Pour l'instant, on simule
            pass
            
        except Exception as e:
            self.logger.error(f"Erreur rafraîchissement données: {e}")
            self.stats['errors'] += 1
    
    def _update_lcd_display(self) -> None:
        """Met à jour l'affichage LCD"""
        try:
            if not self.lcd_interface:
                return
            
            # Mettre à jour l'affichage selon l'écran actuel
            if self.current_screen == UIScreen.HOME:
                self._display_home_screen()
            elif self.current_screen == UIScreen.SENSORS:
                self._display_sensors_screen()
            elif self.current_screen == UIScreen.CONTROLS:
                self._display_controls_screen()
            elif self.current_screen == UIScreen.ALERTS:
                self._display_alerts_screen()
            elif self.current_screen == UIScreen.TERRARIUMS:
                self._display_terrariums_screen()
            elif self.current_screen == UIScreen.SPECIES:
                self._display_species_screen()
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour affichage LCD: {e}")
            self.stats['errors'] += 1
    
    def _display_home_screen(self) -> None:
        """Affiche l'écran d'accueil"""
        try:
            if not self.lcd_interface:
                return
            
            # Afficher les informations principales
            lines = [
                "=== ALIMANTE ===",
                f"Temp: {self.display_data['temperature']:.1f}°C",
                f"Hum: {self.display_data['humidity']:.0f}%",
                f"Terr: {self.display_data['terrarium']}"
            ]
            
            self.lcd_interface.display_message(lines)
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran d'accueil: {e}")
    
    def _display_sensors_screen(self) -> None:
        """Affiche l'écran des capteurs"""
        try:
            if not self.lcd_interface:
                return
            
            lines = [
                "=== CAPTEURS ===",
                f"Temp: {self.display_data['temperature']:.1f}°C",
                f"Hum: {self.display_data['humidity']:.0f}%",
                f"Air: {self.display_data['air_quality']:.0f} AQI"
            ]
            
            self.lcd_interface.display_message(lines)
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran capteurs: {e}")
    
    def _display_controls_screen(self) -> None:
        """Affiche l'écran des contrôles"""
        try:
            if not self.lcd_interface:
                return
            
            lines = [
                "=== CONTRÔLES ===",
                f"Chauffage: {'ON' if self.display_data['heating'] else 'OFF'}",
                f"Humidif: {'ON' if self.display_data['humidifying'] else 'OFF'}",
                f"Éclairage: {'ON' if self.display_data['lighting'] else 'OFF'}"
            ]
            
            self.lcd_interface.display_message(lines)
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran contrôles: {e}")
    
    def _display_alerts_screen(self) -> None:
        """Affiche l'écran des alertes"""
        try:
            if not self.lcd_interface:
                return
            
            alerts = self.display_data.get('alerts', [])
            if not alerts:
                lines = [
                    "=== ALERTES ===",
                    "Aucune alerte",
                    "",
                    ""
                ]
            else:
                lines = [
                    "=== ALERTES ===",
                    f"Total: {len(alerts)}",
                    alerts[0][:20] if alerts else "",
                    alerts[1][:20] if len(alerts) > 1 else ""
                ]
            
            self.lcd_interface.display_message(lines)
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran alertes: {e}")
    
    def _display_terrariums_screen(self) -> None:
        """Affiche l'écran des terrariums"""
        try:
            if not self.lcd_interface:
                return
            
            lines = [
                "=== TERRARIUMS ===",
                f"Actuel: {self.display_data['terrarium']}",
                "Utilisez l'encodeur",
                "pour naviguer"
            ]
            
            self.lcd_interface.display_message(lines)
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran terrariums: {e}")
    
    def _display_species_screen(self) -> None:
        """Affiche l'écran des espèces"""
        try:
            if not self.lcd_interface:
                return
            
            lines = [
                "=== ESPÈCES ===",
                f"Actuelle: {self.display_data['species']}",
                "Utilisez l'encodeur",
                "pour naviguer"
            ]
            
            self.lcd_interface.display_message(lines)
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran espèces: {e}")
    
    def _handle_encoder_rotation(self, direction: int) -> None:
        """Gère la rotation de l'encodeur"""
        try:
            self.stats['encoder_events'] += 1
            
            # Navigation entre les écrans
            if self.current_mode == UIMode.AUTO:
                self._navigate_screens(direction)
            elif self.current_mode == UIMode.MANUAL:
                self._navigate_manual_controls(direction)
            elif self.current_mode == UIMode.CONFIG:
                self._navigate_config(direction)
            
            # Appeler les callbacks
            if self.current_screen in self.screen_callbacks:
                for callback in self.screen_callbacks[self.current_screen]:
                    callback('rotation', direction)
            
        except Exception as e:
            self.logger.error(f"Erreur gestion rotation encodeur: {e}")
            self.stats['errors'] += 1
    
    def _handle_encoder_button(self, pressed: bool) -> None:
        """Gère l'appui sur le bouton de l'encodeur"""
        try:
            self.stats['encoder_events'] += 1
            
            if pressed:
                # Sélectionner l'élément actuel
                self._select_current_item()
            
            # Appeler les callbacks
            if self.current_screen in self.screen_callbacks:
                for callback in self.screen_callbacks[self.current_screen]:
                    callback('button', pressed)
            
        except Exception as e:
            self.logger.error(f"Erreur gestion bouton encodeur: {e}")
            self.stats['errors'] += 1
    
    def _navigate_screens(self, direction: int) -> None:
        """Navigue entre les écrans"""
        try:
            screens = list(UIScreen)
            current_index = screens.index(self.current_screen)
            
            if direction > 0:
                next_index = (current_index + 1) % len(screens)
            else:
                next_index = (current_index - 1) % len(screens)
            
            self.set_screen(screens[next_index])
            
        except Exception as e:
            self.logger.error(f"Erreur navigation écrans: {e}")
    
    def _navigate_manual_controls(self, direction: int) -> None:
        """Navigue dans les contrôles manuels"""
        try:
            # Implémentation de la navigation dans les contrôles manuels
            pass
            
        except Exception as e:
            self.logger.error(f"Erreur navigation contrôles manuels: {e}")
    
    def _navigate_config(self, direction: int) -> None:
        """Navigue dans la configuration"""
        try:
            # Implémentation de la navigation dans la configuration
            pass
            
        except Exception as e:
            self.logger.error(f"Erreur navigation configuration: {e}")
    
    def _select_current_item(self) -> None:
        """Sélectionne l'élément actuel"""
        try:
            # Implémentation de la sélection d'élément
            pass
            
        except Exception as e:
            self.logger.error(f"Erreur sélection élément: {e}")
    
    def set_screen(self, screen: UIScreen) -> None:
        """
        Change l'écran affiché
        
        Args:
            screen: Nouvel écran à afficher
        """
        try:
            if screen != self.current_screen:
                self.current_screen = screen
                self.stats['screen_changes'] += 1
                
                self.logger.info(f"Écran changé: {screen.value}")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('ui_screen_changed', {
                        'screen': screen.value,
                        'timestamp': time.time()
                    })
            
        except Exception as e:
            self.logger.error(f"Erreur changement écran: {e}")
            self.stats['errors'] += 1
    
    def set_mode(self, mode: UIMode) -> None:
        """
        Change le mode de l'interface
        
        Args:
            mode: Nouveau mode
        """
        try:
            if mode != self.current_mode:
                self.current_mode = mode
                self.stats['mode_changes'] += 1
                
                self.logger.info(f"Mode changé: {mode.value}")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('ui_mode_changed', {
                        'mode': mode.value,
                        'timestamp': time.time()
                    })
            
        except Exception as e:
            self.logger.error(f"Erreur changement mode: {e}")
            self.stats['errors'] += 1
    
    def update_display_data(self, data: Dict[str, Any]) -> None:
        """
        Met à jour les données d'affichage
        
        Args:
            data: Nouvelles données à afficher
        """
        try:
            self.display_data.update(data)
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données affichage: {e}")
            self.stats['errors'] += 1
    
    def add_screen_callback(self, screen: UIScreen, callback: Callable) -> None:
        """
        Ajoute un callback pour un écran
        
        Args:
            screen: Écran concerné
            callback: Fonction à appeler
        """
        try:
            if screen not in self.screen_callbacks:
                self.screen_callbacks[screen] = []
            
            self.screen_callbacks[screen].append(callback)
            
        except Exception as e:
            self.logger.error(f"Erreur ajout callback écran: {e}")
    
    def remove_screen_callback(self, screen: UIScreen, callback: Callable) -> None:
        """
        Supprime un callback d'écran
        
        Args:
            screen: Écran concerné
            callback: Fonction à supprimer
        """
        try:
            if screen in self.screen_callbacks and callback in self.screen_callbacks[screen]:
                self.screen_callbacks[screen].remove(callback)
            
        except Exception as e:
            self.logger.error(f"Erreur suppression callback écran: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service d'interface utilisateur
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'service': 'ui',
            'is_running': self.is_running,
            'current_mode': self.current_mode.value,
            'current_screen': self.current_screen.value,
            'lcd_enabled': self.lcd_enabled,
            'encoder_enabled': self.encoder_enabled,
            'auto_refresh': self.auto_refresh,
            'refresh_interval': self.refresh_interval,
            'last_update': self.last_update,
            'display_data': self.display_data,
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie le service d'interface utilisateur"""
        try:
            # Arrêter le service
            self.stop()
            
            # Nettoyer les interfaces
            if self.lcd_interface:
                self.lcd_interface.cleanup()
                self.lcd_interface = None
            
            if self.encoder_interface:
                self.encoder_interface.cleanup()
                self.encoder_interface = None
            
            self.logger.info("Service d'interface utilisateur nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service UI: {e}")
            self.stats['errors'] += 1
