"""
Interface web PWA pour Alimante
Serveur web Flask avec interface responsive
"""

import time
import logging
import threading
import json
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.event_bus import EventBus

try:
    from flask import Flask, render_template, jsonify, request, send_from_directory
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    jsonify = None
    render_template = None
    send_from_directory = None
    CORS = None

class WebInterface:
    """
    Interface web PWA pour l'affichage et la configuration
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[EventBus] = None):
        """
        Initialise l'interface web
        
        Args:
            config: Configuration du serveur web
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus or EventBus()
        self.logger = logging.getLogger(__name__)
        
        # État de l'interface
        self.is_running = False
        self.display_data = {}
        self.last_update = 0
        
        # Serveur Flask
        self.app = None
        self.server_thread = None
        self.stop_event = threading.Event()
        
        # Configuration
        self.host = config.get('host', '0.0.0.0')
        self.port = config.get('port', 8080)
        self.debug = config.get('debug', False)
        
        # Données historiques
        self.history_data = {
            'sensors': [],
            'controls': [],
            'alerts': []
        }
        self.max_history = 1000
        
        # Statistiques
        self.stats = {
            'requests': 0,
            'updates': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Initialiser Flask
        self._initialize_flask()
    
    def _initialize_flask(self) -> None:
        """Initialise l'application Flask"""
        try:
            if not FLASK_AVAILABLE:
                self.logger.warning("Flask non disponible - interface web désactivée")
                return
            
            # Créer l'application Flask
            self.app = Flask(__name__, 
                           template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                           static_folder=os.path.join(os.path.dirname(__file__), 'static'))
            
            # Activer CORS
            CORS(self.app)
            
            # Configuration
            self.app.config['SECRET_KEY'] = 'alimante_secret_key_2024'
            self.app.config['JSON_SORT_KEYS'] = False
            
            # Routes
            self._setup_routes()
            
            self.logger.info("Application Flask initialisée")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation Flask: {e}")
            self.stats['errors'] += 1
    
    def _setup_routes(self) -> None:
        """Configure les routes de l'application"""
        try:
            if not self.app:
                return
            
            @self.app.route('/')
            def index():
                """Page d'accueil"""
                return render_template('index.html')
            
            @self.app.route('/api/status')
            def api_status():
                """API : Statut du système"""
                self.stats['requests'] += 1
                return jsonify({
                    'status': 'running',
                    'timestamp': time.time(),
                    'data': self.display_data,
                    'stats': self.stats
                })
            
            @self.app.route('/api/sensors')
            def api_sensors():
                """API : Données des capteurs"""
                self.stats['requests'] += 1
                sensors = self.display_data.get('sensors', {})
                return jsonify({
                    'sensors': sensors,
                    'timestamp': time.time()
                })
            
            @self.app.route('/api/controls')
            def api_controls():
                """API : État des contrôles"""
                self.stats['requests'] += 1
                controls = self.display_data.get('controls', {})
                return jsonify({
                    'controls': controls,
                    'timestamp': time.time()
                })
            
            @self.app.route('/api/alerts')
            def api_alerts():
                """API : Alertes"""
                self.stats['requests'] += 1
                alerts = self.display_data.get('alerts', [])
                return jsonify({
                    'alerts': alerts,
                    'timestamp': time.time()
                })
            
            @self.app.route('/api/history')
            def api_history():
                """API : Historique des données"""
                self.stats['requests'] += 1
                hours = request.args.get('hours', 24, type=int)
                
                # Filtrer l'historique selon les heures demandées
                cutoff_time = time.time() - (hours * 3600)
                filtered_history = {
                    'sensors': [d for d in self.history_data['sensors'] if d['timestamp'] > cutoff_time],
                    'controls': [d for d in self.history_data['controls'] if d['timestamp'] > cutoff_time],
                    'alerts': [d for d in self.history_data['alerts'] if d['timestamp'] > cutoff_time]
                }
                
                return jsonify(filtered_history)
            
            @self.app.route('/api/control', methods=['POST'])
            def api_control():
                """API : Contrôle des actionneurs"""
                self.stats['requests'] += 1
                try:
                    data = request.get_json()
                    
                    # Support des deux formats : ancien et nouveau
                    if 'component' in data and 'command' in data:
                        # Nouveau format (depuis l'interface web)
                        component = data.get('component')
                        command = data.get('command')
                        
                        # Utiliser le service de contrôle des composants s'il est disponible
                        if hasattr(self, 'component_control_service') and self.component_control_service:
                            success = self.component_control_service.control_component(component, command)
                            if success:
                                return jsonify({'success': True, 'message': f'Composant {component} contrôlé'})
                            else:
                                return jsonify({'success': False, 'error': f'Erreur contrôle composant {component}'}), 400
                        else:
                            # Fallback : émettre un événement
                            self.event_bus.emit('component_control', {
                                'component': component,
                                'command': command,
                                'timestamp': time.time()
                            })
                            return jsonify({'success': True, 'message': 'Commande envoyée'})
                    
                    elif 'action' in data and 'value' in data:
                        # Ancien format (compatibilité)
                        action = data.get('action')
                        value = data.get('value')
                        
                        # Émettre un événement de contrôle
                        self.event_bus.emit('manual_control', {
                            'action': action,
                            'value': value,
                            'timestamp': time.time()
                        })
                        
                        return jsonify({'success': True, 'message': 'Commande envoyée'})
                    
                    else:
                        return jsonify({'success': False, 'error': 'Format de données invalide'}), 400
                    
                except Exception as e:
                    self.logger.error(f"Erreur contrôle manuel: {e}")
                    return jsonify({'success': False, 'error': str(e)}), 400
            
            @self.app.route('/api/config', methods=['GET', 'POST'])
            def api_config():
                """API : Configuration"""
                self.stats['requests'] += 1
                
                if request.method == 'GET':
                    # Retourner la configuration actuelle
                    return jsonify(self.config)
                
                elif request.method == 'POST':
                    # Mettre à jour la configuration
                    try:
                        new_config = request.get_json()
                        self.config.update(new_config)
                        
                        # Émettre un événement de mise à jour de configuration
                        self.event_bus.emit('config_updated', {
                            'config': new_config,
                            'timestamp': time.time()
                        })
                        
                        return jsonify({'success': True, 'message': 'Configuration mise à jour'})
                        
                    except Exception as e:
                        self.logger.error(f"Erreur mise à jour configuration: {e}")
                        return jsonify({'success': False, 'error': str(e)}), 400
            
            @self.app.route('/api/terrariums')
            def api_terrariums():
                """API : Liste des terrariums"""
                self.stats['requests'] += 1
                try:
                    # Utiliser le service de terrariums s'il est disponible
                    if hasattr(self, 'terrarium_service') and self.terrarium_service:
                        terrariums = self.terrarium_service.get_terrariums()
                        return jsonify({'terrariums': terrariums})
                    else:
                        # Données par défaut
                        return jsonify({
                            'terrariums': [
                                {
                                    'id': 'terrarium_default',
                                    'name': 'Station de contrôle centrale',
                                    'species': {'common_name': 'Mantis religiosa'},
                                    'status': 'active',
                                    'controller_type': 'raspberry_pi_zero_2w',
                                    'last_update': time.time()
                                }
                            ]
                        })
                except Exception as e:
                    self.logger.error(f"Erreur API terrariums: {e}")
                    return jsonify({'terrariums': []}), 500
            
            @self.app.route('/api/terrariums/<terrarium_id>/select', methods=['POST'])
            def api_select_terrarium(terrarium_id):
                """API : Sélectionner un terrarium"""
                self.stats['requests'] += 1
                try:
                    if hasattr(self, 'terrarium_service') and self.terrarium_service:
                        success = self.terrarium_service.set_current_terrarium(terrarium_id)
                        if success:
                            return jsonify({'success': True, 'message': 'Terrarium sélectionné'})
                        else:
                            return jsonify({'success': False, 'message': 'Terrarium non trouvé'}), 404
                    else:
                        return jsonify({'success': True, 'message': 'Terrarium sélectionné'})
                except Exception as e:
                    self.logger.error(f"Erreur sélection terrarium: {e}")
                    return jsonify({'success': False, 'message': str(e)}), 500
            
            @self.app.route('/api/terrariums/<terrarium_id>', methods=['PUT'])
            def api_update_terrarium(terrarium_id):
                """API : Mettre à jour un terrarium"""
                self.stats['requests'] += 1
                try:
                    if hasattr(self, 'terrarium_service') and self.terrarium_service:
                        config = request.get_json()
                        success = self.terrarium_service.update_terrarium_config(terrarium_id, config)
                        if success:
                            return jsonify({'success': True, 'message': 'Terrarium mis à jour'})
                        else:
                            return jsonify({'success': False, 'message': 'Terrarium non trouvé'}), 404
                    else:
                        return jsonify({'success': True, 'message': 'Terrarium mis à jour'})
                except Exception as e:
                    self.logger.error(f"Erreur mise à jour terrarium: {e}")
                    return jsonify({'success': False, 'message': str(e)}), 500
            
            @self.app.route('/api/species')
            def api_species():
                """API : Liste des espèces"""
                self.stats['requests'] += 1
                try:
                    if hasattr(self, 'terrarium_service') and self.terrarium_service:
                        species = self.terrarium_service.get_species_list()
                        return jsonify({'species': species})
                    else:
                        return jsonify({
                            'species': [
                                {
                                    'id': 'mantis_religiosa',
                                    'name': 'Mantis religiosa',
                                    'scientific_name': 'Mantis religiosa',
                                    'type': 'insect'
                                }
                            ]
                        })
                except Exception as e:
                    self.logger.error(f"Erreur API espèces: {e}")
                    return jsonify({'species': []}), 500
            
            @self.app.route('/api/components')
            def api_components():
                """API : État des composants"""
                self.stats['requests'] += 1
                try:
                    if hasattr(self, 'component_control_service') and self.component_control_service:
                        components = self.component_control_service.get_all_components_status()
                        return jsonify({'components': components})
                    else:
                        return jsonify({
                            'components': {
                                'heating': {
                                    'enabled': True,
                                    'current_state': False,
                                    'target_temperature': 25.0,
                                    'current_temperature': 20.0,
                                    'control_mode': 'automatic'
                                },
                                'lighting': {
                                    'enabled': True,
                                    'current_state': False,
                                    'brightness': 0,
                                    'target_brightness': 80,
                                    'control_mode': 'automatic'
                                },
                                'humidification': {
                                    'enabled': True,
                                    'current_state': False,
                                    'target_humidity': 60.0,
                                    'current_humidity': 45.0,
                                    'control_mode': 'automatic'
                                },
                                'ventilation': {
                                    'enabled': True,
                                    'current_state': False,
                                    'fan_speed': 0,
                                    'target_speed': 50,
                                    'control_mode': 'automatic'
                                },
                                'feeding': {
                                    'enabled': True,
                                    'current_state': False,
                                    'daily_feeds': 0,
                                    'max_daily_feeds': 3,
                                    'control_mode': 'automatic'
                                }
                            }
                        })
                except Exception as e:
                    self.logger.error(f"Erreur API composants: {e}")
                    return jsonify({'components': {}}), 500
            
            @self.app.route('/api/control/global-mode', methods=['POST'])
            def api_global_control_mode():
                """API : Changer le mode de contrôle global"""
                self.stats['requests'] += 1
                try:
                    data = request.get_json()
                    mode = data.get('mode', 'automatic')
                    
                    if hasattr(self, 'component_control_service') and self.component_control_service:
                        # Changer le mode pour tous les composants
                        from services.component_control_service import ComponentType, ControlMode
                        mode_enum = ControlMode(mode)
                        
                        for component_type in ComponentType:
                            self.component_control_service.set_control_mode(component_type, mode_enum)
                    
                    return jsonify({'success': True, 'message': f'Mode global: {mode}'})
                except Exception as e:
                    self.logger.error(f"Erreur changement mode global: {e}")
                    return jsonify({'success': False, 'message': str(e)}), 500
            
            # Route pour les fichiers statiques
            @self.app.route('/static/<path:filename>')
            def static_files(filename):
                return send_from_directory(self.app.static_folder, filename)
            
            # Route pour le service worker
            @self.app.route('/sw.js')
            def service_worker():
                return send_from_directory(self.app.static_folder, 'sw.js')
            
            # Route pour le manifest
            @self.app.route('/manifest.json')
            def manifest():
                return send_from_directory(self.app.static_folder, 'manifest.json')
            
            self.logger.info("Routes Flask configurées")
            
        except Exception as e:
            self.logger.error(f"Erreur configuration routes: {e}")
            self.stats['errors'] += 1
    
    def start(self) -> bool:
        """
        Démarre l'interface web
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            self.logger.info(f"Tentative de démarrage du serveur web sur {self.host}:{self.port}")
            
            if not self.app:
                self.logger.error("Application Flask non disponible - initialisation échouée")
                return False
            
            self.logger.info("Application Flask disponible, démarrage du serveur...")
            
            # Démarrer le serveur dans un thread séparé
            self.is_running = True
            self.stop_event.clear()
            
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            
            # Attendre un peu pour vérifier que le serveur démarre
            import time
            time.sleep(1)
            
            self.logger.info(f"Interface web démarrée sur http://{self.host}:{self.port}")
            self.logger.info(f"Interface web accessible sur http://localhost:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage interface web: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête l'interface web"""
        try:
            self.is_running = False
            self.stop_event.set()
            
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2.0)
            
            self.logger.info("Interface web arrêtée")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt interface web: {e}")
            self.stats['errors'] += 1
    
    def _run_server(self) -> None:
        """Lance le serveur Flask"""
        try:
            self.logger.info(f"Démarrage du serveur Flask sur {self.host}:{self.port}")
            self.app.run(
                host=self.host,
                port=self.port,
                debug=self.debug,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"Erreur serveur Flask: {e}")
            self.stats['errors'] += 1
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Met à jour les données d'affichage
        
        Args:
            data: Données à afficher
        """
        try:
            self.display_data = data
            self.last_update = time.time()
            self.stats['updates'] += 1
            
            # Ajouter à l'historique
            self._add_to_history(data)
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données web: {e}")
            self.stats['errors'] += 1
    
    def _add_to_history(self, data: Dict[str, Any]) -> None:
        """Ajoute les données à l'historique"""
        try:
            current_time = time.time()
            
            # Capteurs
            if 'sensors' in data:
                self.history_data['sensors'].append({
                    'data': data['sensors'],
                    'timestamp': current_time
                })
            
            # Contrôles
            if 'controls' in data:
                self.history_data['controls'].append({
                    'data': data['controls'],
                    'timestamp': current_time
                })
            
            # Alertes
            if 'alerts' in data:
                for alert in data['alerts']:
                    self.history_data['alerts'].append({
                        'data': alert,
                        'timestamp': current_time
                    })
            
            # Limiter la taille de l'historique
            for key in self.history_data:
                if len(self.history_data[key]) > self.max_history:
                    self.history_data[key] = self.history_data[key][-self.max_history:]
            
        except Exception as e:
            self.logger.error(f"Erreur ajout historique: {e}")
            self.stats['errors'] += 1
    
    def is_running(self) -> bool:
        """
        Vérifie si l'interface web est en cours d'exécution
        
        Returns:
            True si en cours d'exécution, False sinon
        """
        return self.is_running
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de l'interface web
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_running': self.is_running,
            'host': self.host,
            'port': self.port,
            'last_update': self.last_update,
            'history_size': {
                'sensors': len(self.history_data['sensors']),
                'controls': len(self.history_data['controls']),
                'alerts': len(self.history_data['alerts'])
            },
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie les ressources de l'interface web"""
        try:
            self.stop()
            self.logger.info("Interface web nettoyée")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage interface web: {e}")
