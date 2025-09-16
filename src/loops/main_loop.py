"""
Boucle principale Alimante
Orchestre le fonctionnement continu du système
"""

import time
import logging
import signal
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.control_service import ControlService
from utils.event_bus import EventBus

class MainLoop:
    """
    Boucle principale du système Alimante
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None, safety_service: Optional[Any] = None):
        """
        Initialise la boucle principale
        
        Args:
            event_bus: Bus d'événements
            safety_service: Service de sécurité
        """
        self.event_bus = event_bus or EventBus()
        self.safety_service = safety_service
        self.logger = logging.getLogger(__name__)
        
        # Service de contrôle principal
        self.control_service = None
        
        # Configuration
        self.config = self._load_config()
        
        # État de la boucle
        self.is_running = False
        self.loop_interval = 1.0  # Boucle toutes les secondes
        self.last_loop_time = 0
        
        # Statistiques
        self.stats = {
            'loop_cycles': 0,
            'start_time': 0,
            'last_update': 0,
            'errors_count': 0
        }
        
        # Gestionnaire de signaux
        self._setup_signal_handlers()
        
    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration du système"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'config'
            
            # Charger la configuration principale
            main_config = {}
            config_file = config_path / 'config.json'
            if config_file.exists():
                import json
                with open(config_file, 'r') as f:
                    main_config = json.load(f)
            
            # Charger la configuration GPIO
            gpio_config = {}
            gpio_file = config_path / 'gpio_config.json'
            if gpio_file.exists():
                import json
                with open(gpio_file, 'r') as f:
                    gpio_config = json.load(f)
            
            # Charger les limites de sécurité
            safety_limits = {}
            safety_file = config_path / 'safety_limits.json'
            if safety_file.exists():
                import json
                with open(safety_file, 'r') as f:
                    safety_limits = json.load(f)
            
            # Charger les politiques
            policies = {}
            policies_dir = config_path / 'policies'
            if policies_dir.exists():
                for policy_file in policies_dir.glob('*.json'):
                    policy_name = policy_file.stem
                    import json
                    with open(policy_file, 'r') as f:
                        policies[policy_name] = json.load(f)
            
            # Charger la configuration des espèces
            species_config = {}
            species_dir = config_path / 'species'
            if species_dir.exists():
                for species_file in species_dir.rglob('*.json'):
                    species_name = species_file.stem
                    import json
                    with open(species_file, 'r') as f:
                        species_config[species_name] = json.load(f)
            
            # Charger la configuration des terrariums
            terrarium_config = {}
            terrarium_dir = config_path / 'terrariums'
            if terrarium_dir.exists():
                for terrarium_file in terrarium_dir.glob('*.json'):
                    terrarium_name = terrarium_file.stem
                    import json
                    with open(terrarium_file, 'r') as f:
                        terrarium_config[terrarium_name] = json.load(f)
            
            return {
                'main_config': main_config,
                'gpio_config': gpio_config,
                'safety_limits': safety_limits,
                'policies': policies,
                'species_config': species_config,
                'terrarium_config': terrarium_config
            }
            
        except Exception as e:
            self.logger.error(f"Erreur chargement configuration: {e}")
            return {}
    
    def _setup_signal_handlers(self) -> None:
        """Configure les gestionnaires de signaux"""
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception as e:
            self.logger.error(f"Erreur configuration signaux: {e}")
    
    def _signal_handler(self, signum, frame) -> None:
        """Gestionnaire de signaux pour arrêt propre"""
        try:
            self.logger.info(f"Signal reçu: {signum}")
            self.stop()
        except Exception as e:
            self.logger.error(f"Erreur gestionnaire signal: {e}")
    
    def initialize(self) -> bool:
        """
        Initialise la boucle principale
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation de la boucle principale...")
            
            # Initialiser le service de contrôle
            self.control_service = ControlService(self.config, self.event_bus)
            
            if not self.control_service.initialize():
                self.logger.error("Échec initialisation service de contrôle")
                return False
            
            self.logger.info("Boucle principale initialisée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation boucle principale: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre la boucle principale
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.initialize():
                return False
            
            self.logger.info("Démarrage de la boucle principale...")
            
            # Démarrer le service de contrôle
            if not self.control_service.start():
                self.logger.error("Échec démarrage service de contrôle")
                return False
            
            self.is_running = True
            self.stats['start_time'] = time.time()
            
            self.logger.info("Boucle principale démarrée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage boucle principale: {e}")
            return False
    
    def run(self) -> None:
        """Lance la boucle principale"""
        try:
            if not self.start():
                self.logger.error("Impossible de démarrer la boucle principale")
                return
            
            self.logger.info("🦎 Alimante - Surveillance des terrariums en cours...")
            
            while self.is_running:
                try:
                    current_time = time.time()
                    
                    # Vérifier l'intervalle de boucle
                    if current_time - self.last_loop_time >= self.loop_interval:
                        self._loop_cycle()
                        self.last_loop_time = current_time
                        self.stats['loop_cycles'] += 1
                        self.stats['last_update'] = current_time
                    
                    # Petite pause pour éviter la surcharge CPU
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    self.logger.info("Arrêt demandé par l'utilisateur")
                    break
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle principale: {e}")
                    self.stats['errors_count'] += 1
                    time.sleep(1)  # Pause en cas d'erreur
            
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle principale: {e}")
        finally:
            self.stop()
    
    def _loop_cycle(self) -> None:
        """Exécute un cycle de la boucle principale"""
        try:
            # Mettre à jour le service de contrôle
            if self.control_service:
                self.control_service.update()
            
            # Vérifier les alertes de sécurité
            if self.safety_service and self.control_service:
                # Récupérer les données des capteurs depuis le service de contrôle
                sensor_data = self.control_service.get_sensor_data()
                self.safety_service.check_safety_limits(sensor_data)
            
            # Émettre un événement de cycle
            self.event_bus.emit('main_loop_cycle', {
                'cycle': self.stats['loop_cycles'],
                'timestamp': time.time()
            })
            
        except Exception as e:
            self.logger.error(f"Erreur cycle boucle principale: {e}")
            self.stats['errors_count'] += 1
    
    def stop(self) -> None:
        """Arrête la boucle principale"""
        try:
            self.logger.info("Arrêt de la boucle principale...")
            
            self.is_running = False
            
            # Arrêter le service de contrôle
            if self.control_service:
                self.control_service.stop()
            
            self.logger.info("Boucle principale arrêtée")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt boucle principale: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de la boucle principale
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_running': self.is_running,
            'loop_interval': self.loop_interval,
            'stats': self.stats.copy(),
            'control_service': self.control_service.get_system_status() if self.control_service else None
        }
    
    def cleanup(self) -> None:
        """Nettoie la boucle principale"""
        try:
            self.stop()
            
            if self.control_service:
                self.control_service.cleanup()
                self.control_service = None
            
            self.logger.info("Boucle principale nettoyée")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage boucle principale: {e}")

