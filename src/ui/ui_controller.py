"""
Contrôleur principal de l'interface utilisateur Alimante
Gère l'affichage LCD et l'interface web
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List
from enum import Enum
import json
import os
import sys

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.event_bus import EventBus

class UIMode(Enum):
    """Modes d'affichage de l'interface"""
    LCD = "lcd"
    WEB = "web"
    BOTH = "both"

class UIController:
    """
    Contrôleur principal de l'interface utilisateur
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le contrôleur UI
        
        Args:
            event_bus: Bus d'événements
            config: Configuration de l'interface
        """
        self.event_bus = event_bus or EventBus()
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.config = config or self._load_default_config()
        self.mode = UIMode(self.config.get('mode', 'both'))
        
        # État de l'interface
        self.current_screen = "home"
        self.is_running = False
        self.last_update = 0
        self.update_interval = self.config.get('update_interval', 1.0)
        
        # Données affichées
        self.display_data = {
            'sensors': {},
            'controls': {},
            'alerts': [],
            'system_status': 'initializing',
            'timestamp': time.time()
        }
        
        # Composants UI
        self.lcd_interface = None
        self.web_interface = None
        self.encoder_interface = None
        
        # Threads
        self.update_thread = None
        self.stop_event = threading.Event()
        
        # Statistiques
        self.stats = {
            'updates': 0,
            'lcd_updates': 0,
            'web_updates': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Charger la configuration
        self._load_config()
        
        # Initialiser les composants
        self._initialize_components()
        
        # S'abonner aux événements
        self._subscribe_to_events()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Charge la configuration par défaut"""
        return {
            'mode': 'both',
            'update_interval': 1.0,
            'lcd': {
                'enabled': True,
                'width': 128,
                'height': 160,
                'rotation': 0,
                'brightness': 100
            },
            'web': {
                'enabled': True,
                'port': 8080,
                'host': '0.0.0.0',
                'debug': False
            },
            'encoder': {
                'enabled': True,
                'pin_a': 20,
                'pin_b': 21,
                'pin_btn': 16
            }
        }
    
    def _load_config(self) -> None:
        """Charge la configuration depuis les fichiers"""
        try:
            # Charger la configuration UI
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'ui_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    ui_config = json.load(f)
                    self.config.update(ui_config)
                    self.logger.info("Configuration UI chargée")
            
            # Charger la configuration GPIO
            gpio_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'gpio_config.json')
            if os.path.exists(gpio_path):
                with open(gpio_path, 'r') as f:
                    gpio_config = json.load(f)
                    if 'ui' in gpio_config:
                        self.config['encoder'].update(gpio_config['ui'])
                        self.logger.info("Configuration GPIO UI chargée")
            
        except Exception as e:
            self.logger.warning(f"Erreur chargement configuration UI: {e}")
    
    def _initialize_components(self) -> None:
        """Initialise les composants de l'interface"""
        try:
            # Initialiser l'interface LCD
            if self.mode in [UIMode.LCD, UIMode.BOTH] and self.config['lcd']['enabled']:
                from .lcd_interface import LCDInterface
                self.lcd_interface = LCDInterface(self.config['lcd'], self.event_bus)
                self.logger.info("Interface LCD initialisée")
            
            # Initialiser l'interface web
            if self.mode in [UIMode.WEB, UIMode.BOTH] and self.config['web']['enabled']:
                from .web_interface import WebInterface
                self.web_interface = WebInterface(self.config['web'], self.event_bus)
                self.logger.info("Interface web initialisée")
            
            # Initialiser l'encodeur rotatif
            if self.config['encoder']['enabled']:
                from .encoder_interface import EncoderInterface
                self.encoder_interface = EncoderInterface(self.config['encoder'], self.event_bus)
                self.logger.info("Interface encodeur initialisée")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation composants UI: {e}")
            self.stats['errors'] += 1
    
    def _subscribe_to_events(self) -> None:
        """S'abonne aux événements du système"""
        try:
            # Événements des capteurs
            self.event_bus.subscribe('sensor_data_updated', self._on_sensor_data_updated)
            
            # Événements de contrôle
            self.event_bus.subscribe('control_decision', self._on_control_decision)
            
            # Événements d'alerte
            self.event_bus.subscribe('alert_generated', self._on_alert_generated)
            
            # Événements système
            self.event_bus.subscribe('system_status_changed', self._on_system_status_changed)
            
            # Événements de l'encodeur
            if self.encoder_interface:
                self.event_bus.subscribe('encoder_turned', self._on_encoder_turned)
                self.event_bus.subscribe('encoder_pressed', self._on_encoder_pressed)
            
            self.logger.info("Abonnements aux événements configurés")
            
        except Exception as e:
            self.logger.error(f"Erreur abonnement événements: {e}")
            self.stats['errors'] += 1
    
    def start(self) -> bool:
        """
        Démarre le contrôleur UI
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            self.logger.info("Démarrage du contrôleur UI...")
            
            # Démarrer l'interface LCD
            if self.lcd_interface:
                if not self.lcd_interface.start():
                    self.logger.error("Échec démarrage interface LCD")
                    return False
            
            # Démarrer l'interface web
            if self.web_interface:
                if not self.web_interface.start():
                    self.logger.error("Échec démarrage interface web")
                    return False
            
            # Démarrer l'encodeur
            if self.encoder_interface:
                if not self.encoder_interface.start():
                    self.logger.warning("Échec démarrage encodeur (non critique)")
            
            # Démarrer le thread de mise à jour
            self.is_running = True
            self.stop_event.clear()
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            self.logger.info("Contrôleur UI démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage contrôleur UI: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête le contrôleur UI"""
        try:
            self.logger.info("Arrêt du contrôleur UI...")
            
            # Arrêter le thread de mise à jour
            self.is_running = False
            self.stop_event.set()
            
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=2.0)
            
            # Arrêter les interfaces
            if self.lcd_interface:
                self.lcd_interface.stop()
            
            if self.web_interface:
                self.web_interface.stop()
            
            if self.encoder_interface:
                self.encoder_interface.stop()
            
            self.logger.info("Contrôleur UI arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt contrôleur UI: {e}")
            self.stats['errors'] += 1
    
    def _update_loop(self) -> None:
        """Boucle principale de mise à jour de l'interface"""
        while self.is_running and not self.stop_event.is_set():
            try:
                current_time = time.time()
                
                # Mettre à jour les données d'affichage
                self._update_display_data()
                
                # Mettre à jour l'interface LCD
                if self.lcd_interface and self.lcd_interface.is_running():
                    self.lcd_interface.update(self.display_data)
                    self.stats['lcd_updates'] += 1
                
                # Mettre à jour l'interface web
                if self.web_interface and self.web_interface.is_running():
                    self.web_interface.update(self.display_data)
                    self.stats['web_updates'] += 1
                
                self.stats['updates'] += 1
                self.last_update = current_time
                
                # Attendre la prochaine mise à jour
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Erreur boucle mise à jour UI: {e}")
                self.stats['errors'] += 1
                time.sleep(1.0)
    
    def _update_display_data(self) -> None:
        """Met à jour les données d'affichage"""
        try:
            # Mettre à jour le timestamp
            self.display_data['timestamp'] = time.time()
            
            # Émettre un événement de mise à jour
            self.event_bus.emit('ui_data_updated', {
                'data': self.display_data,
                'timestamp': self.display_data['timestamp']
            })
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données affichage: {e}")
            self.stats['errors'] += 1
    
    def _on_sensor_data_updated(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement : données des capteurs mises à jour"""
        try:
            self.display_data['sensors'] = data.get('data', {})
            self.logger.debug("Données capteurs mises à jour dans l'UI")
        except Exception as e:
            self.logger.error(f"Erreur traitement données capteurs: {e}")
            self.stats['errors'] += 1
    
    def _on_control_decision(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement : décision de contrôle"""
        try:
            self.display_data['controls'] = data
            self.logger.debug(f"Décision de contrôle: {data.get('decision', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Erreur traitement décision contrôle: {e}")
            self.stats['errors'] += 1
    
    def _on_alert_generated(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement : alerte générée"""
        try:
            alert = {
                'type': data.get('type', 'unknown'),
                'message': data.get('message', ''),
                'timestamp': data.get('timestamp', time.time()),
                'level': data.get('level', 'info')
            }
            
            # Ajouter l'alerte à la liste
            self.display_data['alerts'].append(alert)
            
            # Limiter le nombre d'alertes
            max_alerts = 10
            if len(self.display_data['alerts']) > max_alerts:
                self.display_data['alerts'] = self.display_data['alerts'][-max_alerts:]
            
            self.logger.info(f"Alerte UI: {alert['message']}")
            
        except Exception as e:
            self.logger.error(f"Erreur traitement alerte: {e}")
            self.stats['errors'] += 1
    
    def _on_system_status_changed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement : statut système changé"""
        try:
            self.display_data['system_status'] = data.get('status', 'unknown')
            self.logger.debug(f"Statut système: {self.display_data['system_status']}")
        except Exception as e:
            self.logger.error(f"Erreur traitement statut système: {e}")
            self.stats['errors'] += 1
    
    def _on_encoder_turned(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement : encodeur tourné"""
        try:
            direction = data.get('direction', 0)
            self.logger.debug(f"Encodeur tourné: {direction}")
            
            # Changer d'écran selon la direction
            screens = ['home', 'sensors', 'controls', 'config', 'alerts']
            current_index = screens.index(self.current_screen) if self.current_screen in screens else 0
            
            if direction > 0:  # Sens horaire
                current_index = (current_index + 1) % len(screens)
            else:  # Sens anti-horaire
                current_index = (current_index - 1) % len(screens)
            
            self.current_screen = screens[current_index]
            self.logger.info(f"Écran changé: {self.current_screen}")
            
        except Exception as e:
            self.logger.error(f"Erreur traitement encodeur: {e}")
            self.stats['errors'] += 1
    
    def _on_encoder_pressed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement : encodeur pressé"""
        try:
            self.logger.debug("Encodeur pressé")
            
            # Action selon l'écran actuel
            if self.current_screen == 'home':
                # Retourner à l'écran d'accueil
                pass
            elif self.current_screen == 'sensors':
                # Actualiser les données des capteurs
                self.event_bus.emit('refresh_sensor_data', {})
            elif self.current_screen == 'controls':
                # Basculer le mode de contrôle
                self.event_bus.emit('toggle_control_mode', {})
            elif self.current_screen == 'config':
                # Entrer dans le menu de configuration
                self.event_bus.emit('enter_config_menu', {})
            elif self.current_screen == 'alerts':
                # Effacer les alertes
                self.display_data['alerts'].clear()
            
        except Exception as e:
            self.logger.error(f"Erreur traitement pression encodeur: {e}")
            self.stats['errors'] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du contrôleur UI
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_running': self.is_running,
            'mode': self.mode.value,
            'current_screen': self.current_screen,
            'last_update': self.last_update,
            'lcd_enabled': self.lcd_interface is not None,
            'web_enabled': self.web_interface is not None,
            'encoder_enabled': self.encoder_interface is not None,
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie les ressources du contrôleur UI"""
        try:
            self.stop()
            self.logger.info("Contrôleur UI nettoyé")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur UI: {e}")
