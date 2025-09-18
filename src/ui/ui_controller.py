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
        
        # Initialiser les services (après les composants)
        self._initialize_services()
        
        # S'abonner aux événements
        self._subscribe_to_events()
        
        # Passer les services à l'interface web après initialisation
        self._pass_services_to_web()
    
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
    
    def _initialize_services(self) -> None:
        """Initialise les services de gestion"""
        try:
            # Service de gestion des terrariums
            from services.terrarium_service import TerrariumService
            self.terrarium_service = TerrariumService(self.event_bus)
            self.logger.info("Service de terrariums initialisé")
            
            # Service de contrôle des composants
            from services.component_control_service import ComponentControlService
            self.component_control_service = ComponentControlService(self.event_bus)
            self.logger.info("Service de contrôle des composants initialisé")
            
            # Service d'alimentation
            from services.feeding_service import FeedingService
            # Charger la configuration GPIO
            import json
            try:
                with open('config/gpio_config.json', 'r') as f:
                    gpio_config = json.load(f)
                # Ajouter la configuration GPIO à la config principale
                feeding_config = self.config.copy()
                feeding_config['gpio_config'] = gpio_config
                feeding_config['safety_limits'] = self.config.get('safety', {})
            except Exception as e:
                self.logger.warning(f"Erreur chargement config GPIO: {e}")
                feeding_config = self.config
            
            self.feeding_service = FeedingService(feeding_config, self.event_bus)
            if self.feeding_service.initialize():
                self.logger.info("Service d'alimentation initialisé")
            else:
                self.logger.warning("Échec initialisation service d'alimentation")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation services: {e}")
            self.stats['errors'] += 1
    
    def _pass_services_to_web(self) -> None:
        """Passe les services à l'interface web"""
        try:
            if hasattr(self, 'web_interface') and self.web_interface:
                if hasattr(self, 'terrarium_service') and self.terrarium_service:
                    self.web_interface.terrarium_service = self.terrarium_service
                    self.logger.info("Service de terrariums passé à l'interface web")
                
                if hasattr(self, 'component_control_service') and self.component_control_service:
                    self.web_interface.component_control_service = self.component_control_service
                    self.logger.info("Service de contrôle des composants passé à l'interface web")
        except Exception as e:
            self.logger.error(f"Erreur passage services à l'interface web: {e}")
            self.stats['errors'] += 1
    
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
            self.event_bus.on('sensor_data_updated', self._on_sensor_data_updated)
            
            # Événements de contrôle
            self.event_bus.on('control_decision', self._on_control_decision)
            
            # Événements d'alerte
            self.event_bus.on('alert_generated', self._on_alert_generated)
            
            # Événements système
            self.event_bus.on('system_status_changed', self._on_system_status_changed)
            
            # Événements de l'encodeur
            if self.encoder_interface:
                self.event_bus.on('encoder_turned', self._on_encoder_turned)
                self.event_bus.on('encoder_pressed', self._on_encoder_pressed)
            
            # Événements de sécurité
            self.event_bus.on('emergency_stop', self._on_emergency_stop)
            self.event_bus.on('emergency_resume', self._on_emergency_resume)
            self.event_bus.on('safety_alert', self._on_safety_alert)
            
            # Événements de données
            self.event_bus.on('sensor_data', self._on_sensor_data)
            self.event_bus.on('sensor_alert', self._on_sensor_alert)
            self.event_bus.on('actuator_action', self._on_actuator_action)
            self.event_bus.on('device_interaction', self._on_device_interaction)
            
            # Événements de contrôle
            self.event_bus.on('control_mode_changed', self._on_control_mode_changed)
            self.event_bus.on('component_controlled', self._on_component_controlled)
            self.event_bus.on('feeding_completed', self._on_feeding_completed)
            self.event_bus.on('feeding_failed', self._on_feeding_failed)
            
            # Événements de services
            self.event_bus.on('heating_changed', self._on_heating_changed)
            self.event_bus.on('humidification_changed', self._on_humidification_changed)
            self.event_bus.on('lighting_changed', self._on_lighting_changed)
            self.event_bus.on('ventilation_changed', self._on_ventilation_changed)
            
            # Événements de terrarium
            self.event_bus.on('terrarium_changed', self._on_terrarium_changed)
            self.event_bus.on('terrarium_config_updated', self._on_terrarium_config_updated)
            
            # Événements de configuration
            self.event_bus.on('config_updated', self._on_config_updated)
            self.event_bus.on('component_control', self._on_component_control)
            self.event_bus.on('manual_control', self._on_manual_control)
            
            # Événements de cycle
            self.event_bus.on('main_loop_cycle', self._on_main_loop_cycle)
            
            # Événements UI spécifiques
            self.event_bus.on('ui_data_updated', self._on_ui_data_updated)
            self.event_bus.on('refresh_sensor_data', self._on_refresh_sensor_data)
            self.event_bus.on('toggle_control_mode', self._on_toggle_control_mode)
            self.event_bus.on('enter_config_menu', self._on_enter_config_menu)
            
            # Événements de services supplémentaires
            self.event_bus.on('feeding_executed', self._on_feeding_executed)
            self.event_bus.on('lighting_intensity_changed', self._on_lighting_intensity_changed)
            self.event_bus.on('ventilation_changed', self._on_ventilation_changed)
            
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
                if self.lcd_interface and self.lcd_interface.is_running:
                    self.lcd_interface.update(self.display_data)
                    self.stats['lcd_updates'] += 1
                
                # Mettre à jour l'interface web
                if self.web_interface and self.web_interface.is_running:
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
            
            # Données des terrariums
            if hasattr(self, 'terrarium_service') and self.terrarium_service:
                self.display_data['terrariums'] = self.terrarium_service.get_terrariums()
                self.display_data['current_terrarium'] = self.terrarium_service.get_current_terrarium()
            
            # Données des composants
            if hasattr(self, 'component_control_service') and self.component_control_service:
                self.display_data['components'] = self.component_control_service.get_all_components_status()
            
            # Mettre à jour les données d'alimentation
            self._update_feeding_data()
            
            # Émettre un événement de mise à jour
            self.event_bus.emit('ui_data_updated', {
                'data': self.display_data,
                'timestamp': self.display_data['timestamp']
            })
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données affichage: {e}")
            self.stats['errors'] += 1
    
    def _update_feeding_data(self) -> None:
        """Met à jour les données d'alimentation depuis le service"""
        try:
            # Demander les données d'alimentation au service
            if hasattr(self, 'feeding_service') and self.feeding_service:
                feeding_status = self.feeding_service.get_feeding_status()
                
                # Mettre à jour les données d'affichage
                if 'feeding' not in self.display_data['controls']:
                    self.display_data['controls']['feeding'] = {}
                
                self.display_data['controls']['feeding'].update({
                    'today_feeding_count': feeding_status.get('today_feeding_count', 0),
                    'last_feeding_time': feeding_status.get('last_feeding_time', 0),
                    'is_feeding': feeding_status.get('is_feeding', False)
                })
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données alimentation: {e}")
    
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
    
    # Gestionnaires d'événements de sécurité
    def _on_emergency_stop(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement emergency_stop"""
        try:
            reason = data.get('reason', 'Raison inconnue')
            self.logger.critical(f"ARRÊT D'URGENCE: {reason}")
            
            # Mettre à jour l'affichage
            self.display_data['system_status'] = 'emergency'
            self.display_data['alerts'].append({
                'type': 'emergency',
                'message': f"ARRÊT D'URGENCE: {reason}",
                'timestamp': time.time(),
                'severity': 'critical'
            })
            
            # Forcer la mise à jour de l'affichage
            self._update_display_data()
            
        except Exception as e:
            self.logger.error(f"Erreur gestion emergency_stop: {e}")
    
    def _on_emergency_resume(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement emergency_resume"""
        try:
            self.logger.info("Reprise normale du système")
            self.display_data['system_status'] = 'normal'
            self._update_display_data()
            
        except Exception as e:
            self.logger.error(f"Erreur gestion emergency_resume: {e}")
    
    def _on_safety_alert(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement safety_alert"""
        try:
            message = data.get('message', 'Alerte inconnue')
            self.logger.warning(f"Alerte sécurité: {message}")
            
            # Ajouter à la liste des alertes
            self.display_data['alerts'].append({
                'type': 'safety',
                'message': message,
                'timestamp': time.time(),
                'severity': 'warning'
            })
            
        except Exception as e:
            self.logger.error(f"Erreur gestion safety_alert: {e}")
    
    # Gestionnaires d'événements de données
    def _on_sensor_data(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement sensor_data"""
        try:
            self.logger.debug(f"Données capteurs reçues: {data}")
            # Les données sont déjà traitées par _on_sensor_data_updated
        except Exception as e:
            self.logger.error(f"Erreur gestion sensor_data: {e}")
    
    def _on_sensor_alert(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement sensor_alert"""
        try:
            message = data.get('message', 'Alerte capteur inconnue')
            self.logger.warning(f"Alerte capteur: {message}")
            
            self.display_data['alerts'].append({
                'type': 'sensor',
                'message': message,
                'timestamp': time.time(),
                'severity': 'warning'
            })
            
        except Exception as e:
            self.logger.error(f"Erreur gestion sensor_alert: {e}")
    
    def _on_actuator_action(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement actuator_action"""
        try:
            self.logger.debug(f"Action actionneur: {data}")
            # Mettre à jour l'état des actionneurs dans l'affichage
            if 'actuator' in data:
                self.display_data['controls'][data['actuator']] = data.get('state', False)
            
        except Exception as e:
            self.logger.error(f"Erreur gestion actuator_action: {e}")
    
    def _on_device_interaction(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement device_interaction"""
        try:
            self.logger.debug(f"Interaction périphérique: {data}")
            # Loguer l'interaction pour debugging
        except Exception as e:
            self.logger.error(f"Erreur gestion device_interaction: {e}")
    
    # Gestionnaires d'événements de contrôle
    def _on_control_mode_changed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement control_mode_changed"""
        try:
            component = data.get('component', 'unknown')
            mode = data.get('mode', 'unknown')
            self.logger.info(f"Mode contrôle changé: {component} -> {mode}")
            
            # Mettre à jour l'affichage
            self.display_data['controls'][f"{component}_mode"] = mode
            
        except Exception as e:
            self.logger.error(f"Erreur gestion control_mode_changed: {e}")
    
    def _on_component_controlled(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement component_controlled"""
        try:
            component = data.get('component', 'unknown')
            command = data.get('command', {})
            self.logger.debug(f"Composant contrôlé: {component} - {command}")
            
        except Exception as e:
            self.logger.error(f"Erreur gestion component_controlled: {e}")
    
    def _on_feeding_completed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement feeding_completed"""
        try:
            fly_count = data.get('fly_count', 0)
            self.logger.info(f"Alimentation terminée: {fly_count} mouches")
            
            self.display_data['alerts'].append({
                'type': 'feeding',
                'message': f"Alimentation terminée: {fly_count} mouches",
                'timestamp': time.time(),
                'severity': 'info'
            })
            
        except Exception as e:
            self.logger.error(f"Erreur gestion feeding_completed: {e}")
    
    def _on_feeding_failed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement feeding_failed"""
        try:
            error = data.get('error', 'Erreur inconnue')
            self.logger.error(f"Échec alimentation: {error}")
            
            self.display_data['alerts'].append({
                'type': 'feeding',
                'message': f"Échec alimentation: {error}",
                'timestamp': time.time(),
                'severity': 'error'
            })
            
        except Exception as e:
            self.logger.error(f"Erreur gestion feeding_failed: {e}")
    
    # Gestionnaires d'événements de services
    def _on_heating_changed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement heating_changed"""
        try:
            heating = data.get('heating', False)
            temperature = data.get('temperature', 0)
            self.logger.debug(f"Chauffage: {heating}, Température: {temperature}°C")
            
            self.display_data['controls']['heating'] = heating
            self.display_data['sensors']['temperature'] = temperature
            
        except Exception as e:
            self.logger.error(f"Erreur gestion heating_changed: {e}")
    
    def _on_humidification_changed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement humidification_changed"""
        try:
            humidifying = data.get('humidifying', False)
            humidity = data.get('humidity', 0)
            self.logger.debug(f"Humidification: {humidifying}, Humidité: {humidity}%")
            
            self.display_data['controls']['humidification'] = humidifying
            self.display_data['sensors']['humidity'] = humidity
            
        except Exception as e:
            self.logger.error(f"Erreur gestion humidification_changed: {e}")
    
    def _on_lighting_changed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement lighting_changed"""
        try:
            lighting = data.get('lighting', False)
            intensity = data.get('intensity', 0)
            self.logger.debug(f"Éclairage: {lighting}, Intensité: {intensity}%")
            
            self.display_data['controls']['lighting'] = lighting
            self.display_data['controls']['lighting_intensity'] = intensity
            
        except Exception as e:
            self.logger.error(f"Erreur gestion lighting_changed: {e}")
    
    def _on_ventilation_changed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement ventilation_changed"""
        try:
            speed = data.get('speed', 0)
            is_ventilating = data.get('is_ventilating', False)
            self.logger.debug(f"Ventilation: {is_ventilating}, Vitesse: {speed}%")
            
            self.display_data['controls']['ventilation'] = is_ventilating
            self.display_data['controls']['ventilation_speed'] = speed
            
        except Exception as e:
            self.logger.error(f"Erreur gestion ventilation_changed: {e}")
    
    # Gestionnaires d'événements de terrarium
    def _on_terrarium_changed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement terrarium_changed"""
        try:
            terrarium_id = data.get('terrarium_id', 'unknown')
            self.logger.info(f"Terrarium changé: {terrarium_id}")
            
        except Exception as e:
            self.logger.error(f"Erreur gestion terrarium_changed: {e}")
    
    def _on_terrarium_config_updated(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement terrarium_config_updated"""
        try:
            terrarium_id = data.get('terrarium_id', 'unknown')
            self.logger.info(f"Configuration terrarium mise à jour: {terrarium_id}")
            
        except Exception as e:
            self.logger.error(f"Erreur gestion terrarium_config_updated: {e}")
    
    # Gestionnaires d'événements de configuration
    def _on_config_updated(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement config_updated"""
        try:
            config = data.get('config', {})
            self.logger.info("Configuration mise à jour")
            
        except Exception as e:
            self.logger.error(f"Erreur gestion config_updated: {e}")
    
    def _on_component_control(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement component_control"""
        try:
            component = data.get('component', 'unknown')
            command = data.get('command', {})
            self.logger.debug(f"Contrôle composant: {component} - {command}")
            
        except Exception as e:
            self.logger.error(f"Erreur gestion component_control: {e}")
    
    def _on_manual_control(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement manual_control"""
        try:
            action = data.get('action', 'unknown')
            value = data.get('value', None)
            self.logger.debug(f"Contrôle manuel: {action} = {value}")
            
        except Exception as e:
            self.logger.error(f"Erreur gestion manual_control: {e}")
    
    # Gestionnaire d'événement de cycle
    def _on_main_loop_cycle(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement main_loop_cycle"""
        try:
            cycle = data.get('cycle', 0)
            self.logger.debug(f"Cycle principal: {cycle}")
            
        except Exception as e:
            self.logger.error(f"Erreur gestion main_loop_cycle: {e}")
    
    # Gestionnaires d'événements UI spécifiques
    def _on_ui_data_updated(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement ui_data_updated"""
        try:
            ui_data = data.get('data', {})
            timestamp = data.get('timestamp', time.time())
            self.logger.debug(f"Données UI mises à jour: {ui_data}")
            
            # Mettre à jour les données d'affichage
            if 'sensors' in ui_data:
                self.display_data['sensors'].update(ui_data['sensors'])
            if 'controls' in ui_data:
                self.display_data['controls'].update(ui_data['controls'])
            if 'alerts' in ui_data:
                self.display_data['alerts'] = ui_data['alerts']
            
            self.display_data['timestamp'] = timestamp
            
        except Exception as e:
            self.logger.error(f"Erreur gestion ui_data_updated: {e}")
    
    def _on_refresh_sensor_data(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement refresh_sensor_data"""
        try:
            self.logger.info("Actualisation des données capteurs demandée")
            
            # Émettre une demande de rafraîchissement
            self.event_bus.emit('sensor_data_request', {
                'timestamp': time.time(),
                'source': 'ui_refresh'
            })
            
        except Exception as e:
            self.logger.error(f"Erreur gestion refresh_sensor_data: {e}")
    
    def _on_toggle_control_mode(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement toggle_control_mode"""
        try:
            self.logger.info("Basculement du mode de contrôle demandé")
            
            # Basculer entre les modes
            current_mode = self.display_data.get('system_status', 'auto')
            if current_mode == 'auto':
                new_mode = 'manual'
            elif current_mode == 'manual':
                new_mode = 'maintenance'
            else:
                new_mode = 'auto'
            
            self.display_data['system_status'] = new_mode
            
            # Émettre un événement de changement de mode
            self.event_bus.emit('system_mode_changed', {
                'old_mode': current_mode,
                'new_mode': new_mode,
                'timestamp': time.time()
            })
            
            self.logger.info(f"Mode de contrôle basculé: {current_mode} -> {new_mode}")
            
        except Exception as e:
            self.logger.error(f"Erreur gestion toggle_control_mode: {e}")
    
    def _on_enter_config_menu(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement enter_config_menu"""
        try:
            self.logger.info("Entrée dans le menu de configuration")
            
            # Changer l'écran vers la configuration
            self.current_screen = 'config'
            
            # Émettre un événement de changement d'écran
            self.event_bus.emit('screen_changed', {
                'screen': 'config',
                'timestamp': time.time()
            })
            
        except Exception as e:
            self.logger.error(f"Erreur gestion enter_config_menu: {e}")
    
    # Gestionnaires d'événements de services supplémentaires
    def _on_feeding_executed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement feeding_executed"""
        try:
            daily_feeds = data.get('daily_feeds', 0)
            timestamp = data.get('timestamp', time.time())
            self.logger.info(f"Alimentation exécutée: {daily_feeds} repas quotidiens")
            
            # Mettre à jour l'affichage
            self.display_data['controls']['feeding'] = {
                'today_feeding_count': daily_feeds,
                'last_feeding_time': timestamp
            }
            
            # Ajouter une notification
            self.display_data['alerts'].append({
                'type': 'feeding',
                'message': f"Alimentation exécutée: {daily_feeds} repas",
                'timestamp': timestamp,
                'severity': 'info'
            })
            
        except Exception as e:
            self.logger.error(f"Erreur gestion feeding_executed: {e}")
    
    def _on_lighting_intensity_changed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement lighting_intensity_changed"""
        try:
            intensity = data.get('intensity', 0)
            timestamp = data.get('timestamp', time.time())
            self.logger.debug(f"Intensité éclairage changée: {intensity}%")
            
            # Mettre à jour l'affichage
            self.display_data['controls']['lighting_intensity'] = intensity
            self.display_data['controls']['lighting_intensity_timestamp'] = timestamp
            
        except Exception as e:
            self.logger.error(f"Erreur gestion lighting_intensity_changed: {e}")
    
    def _on_ventilation_changed(self, data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement ventilation_changed"""
        try:
            speed = data.get('speed', 0)
            is_ventilating = data.get('is_ventilating', False)
            timestamp = data.get('timestamp', time.time())
            self.logger.debug(f"Ventilation changée: {is_ventilating}, vitesse: {speed}%")
            
            # Mettre à jour l'affichage
            self.display_data['controls']['ventilation'] = is_ventilating
            self.display_data['controls']['ventilation_speed'] = speed
            self.display_data['controls']['ventilation_timestamp'] = timestamp
            
        except Exception as e:
            self.logger.error(f"Erreur gestion ventilation_changed: {e}")
    
    def cleanup(self) -> None:
        """Nettoie les ressources du contrôleur UI"""
        try:
            self.stop()
            self.logger.info("Contrôleur UI nettoyé")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur UI: {e}")
