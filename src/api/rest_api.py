"""
API REST pour Alimante
Gestion des endpoints et communication avec l'interface web
"""

import time
import logging
from typing import Dict, Any, Optional
from flask import Flask, jsonify, request
from flask_cors import CORS

class AlimanteAPI:
    """
    API REST pour l'application Alimante
    """
    
    def __init__(self, event_bus, config: Optional[Dict[str, Any]] = None):
        """
        Initialise l'API REST
        
        Args:
            event_bus: Bus d'événements
            config: Configuration de l'API
        """
        self.event_bus = event_bus
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Données partagées
        self.display_data = {
            'sensors': {},
            'controls': {},
            'alerts': [],
            'system_status': 'initializing',
            'timestamp': time.time()
        }
        
        # Statistiques de l'API
        self.stats = {
            'requests': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Initialiser Flask
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Enregistrer les routes
        self._register_routes()
    
    def _register_routes(self):
        """Enregistre toutes les routes de l'API"""
        
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
            """API : Alertes système"""
            self.stats['requests'] += 1
            alerts = self.display_data.get('alerts', [])
            return jsonify({
                'alerts': alerts,
                'timestamp': time.time()
            })
        
        @self.app.route('/api/feeding')
        def api_feeding():
            """API : Données d'alimentation"""
            self.stats['requests'] += 1
            feeding_data = self.display_data.get('controls', {}).get('feeding', {})
            return jsonify({
                'feeding': feeding_data,
                'timestamp': time.time()
            })
        
        @self.app.route('/api/control', methods=['POST'])
        def api_control():
            """API : Contrôle des composants"""
            try:
                self.stats['requests'] += 1
                data = request.get_json()
                
                if not data:
                    return jsonify({'error': 'Données JSON requises'}), 400
                
                component = data.get('component')
                command = data.get('command', {})
                
                if not component:
                    return jsonify({'error': 'Composant non spécifié'}), 400
                
                # Émettre un événement de contrôle
                self.event_bus.emit('component_control', {
                    'component': component,
                    'command': command,
                    'timestamp': time.time()
                })
                
                return jsonify({
                    'success': True,
                    'message': f'Commande envoyée au composant {component}',
                    'timestamp': time.time()
                })
                
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Erreur API contrôle: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/feeding/feed', methods=['POST'])
        def api_feed_now():
            """API : Alimentation immédiate"""
            try:
                self.stats['requests'] += 1
                
                # Émettre un événement d'alimentation manuelle
                self.event_bus.emit('manual_feeding_request', {
                    'timestamp': time.time(),
                    'source': 'api'
                })
                
                return jsonify({
                    'success': True,
                    'message': 'Demande d\'alimentation envoyée',
                    'timestamp': time.time()
                })
                
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Erreur API alimentation: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/terrariums')
        def api_terrariums():
            """API : Liste des terrariums"""
            self.stats['requests'] += 1
            terrariums = self.display_data.get('terrariums', [])
            return jsonify({
                'terrariums': terrariums,
                'timestamp': time.time()
            })
        
        @self.app.route('/api/terrariums/<terrarium_id>')
        def api_terrarium_details(terrarium_id):
            """API : Détails d'un terrarium"""
            self.stats['requests'] += 1
            terrariums = self.display_data.get('terrariums', [])
            terrarium = next((t for t in terrariums if t.get('id') == terrarium_id), None)
            
            if not terrarium:
                return jsonify({'error': 'Terrarium non trouvé'}), 404
            
            return jsonify({
                'terrarium': terrarium,
                'timestamp': time.time()
            })
        
        @self.app.route('/api/health')
        def api_health():
            """API : Santé du système"""
            uptime = time.time() - self.stats['start_time']
            return jsonify({
                'status': 'healthy',
                'uptime': uptime,
                'requests': self.stats['requests'],
                'errors': self.stats['errors'],
                'timestamp': time.time()
            })
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Met à jour les données partagées
        
        Args:
            data: Nouvelles données à partager
        """
        try:
            self.display_data.update(data)
            self.logger.debug("Données API mises à jour")
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données API: {e}")
            self.stats['errors'] += 1
    
    def get_app(self) -> Flask:
        """
        Retourne l'application Flask
        
        Returns:
            Application Flask configurée
        """
        return self.app
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de l'API
        
        Returns:
            Dictionnaire des statistiques
        """
        return self.stats.copy()
