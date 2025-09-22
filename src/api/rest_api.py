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
        
        @self.app.route('/api/species')
        def api_species():
            """API : Liste des espèces disponibles"""
            self.stats['requests'] += 1
            try:
                # Récupérer les espèces depuis le service de terrariums
                if hasattr(self, 'terrarium_service') and self.terrarium_service:
                    species = self.terrarium_service.get_species_list()
                else:
                    # Fallback : espèces par défaut
                    species = [
                        {'id': 'mantis_religiosa', 'name': 'Mante religieuse', 'scientific_name': 'Mantis religiosa', 'type': 'insect'},
                        {'id': 'template_insect', 'name': 'Template Insect', 'scientific_name': 'Template', 'type': 'insect'},
                        {'id': 'template_reptile', 'name': 'Template Reptile', 'scientific_name': 'Template', 'type': 'reptile'}
                    ]
                
                return jsonify({
                    'species': species,
                    'timestamp': time.time()
                })
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Erreur API espèces: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/species/<species_id>')
        def api_species_details(species_id):
            """API : Détails d'une espèce"""
            self.stats['requests'] += 1
            try:
                if hasattr(self, 'terrarium_service') and self.terrarium_service:
                    species_config = self.terrarium_service.get_species_config(species_id)
                else:
                    species_config = None
                
                if not species_config:
                    return jsonify({'error': 'Espèce non trouvée'}), 404
                
                return jsonify({
                    'species': species_config,
                    'timestamp': time.time()
                })
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Erreur API espèce {species_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/terrariums/current')
        def api_current_terrarium():
            """API : Terrarium actuellement sélectionné"""
            self.stats['requests'] += 1
            try:
                if hasattr(self, 'terrarium_service') and self.terrarium_service:
                    current_terrarium = self.terrarium_service.get_current_terrarium()
                else:
                    current_terrarium = None
                
                return jsonify({
                    'current_terrarium': current_terrarium,
                    'timestamp': time.time()
                })
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Erreur API terrarium actuel: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/terrariums/<terrarium_id>/select', methods=['POST'])
        def api_select_terrarium(terrarium_id):
            """API : Sélectionner un terrarium"""
            self.stats['requests'] += 1
            try:
                if hasattr(self, 'terrarium_service') and self.terrarium_service:
                    success = self.terrarium_service.set_current_terrarium(terrarium_id)
                    
                    if success:
                        return jsonify({
                            'success': True,
                            'message': f'Terrarium {terrarium_id} sélectionné',
                            'terrarium_id': terrarium_id,
                            'timestamp': time.time()
                        })
                    else:
                        return jsonify({'error': 'Échec de la sélection du terrarium'}), 400
                else:
                    return jsonify({'error': 'Service de terrariums non disponible'}), 503
                    
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Erreur API sélection terrarium: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/terrariums/<terrarium_id>/species', methods=['POST'])
        def api_set_terrarium_species(terrarium_id):
            """API : Définir l'espèce d'un terrarium"""
            self.stats['requests'] += 1
            try:
                data = request.get_json()
                if not data or 'species_id' not in data:
                    return jsonify({'error': 'species_id requis'}), 400
                
                species_id = data['species_id']
                
                if hasattr(self, 'terrarium_service') and self.terrarium_service:
                    # Récupérer la configuration de l'espèce
                    species_config = self.terrarium_service.get_species_config(species_id)
                    if not species_config:
                        return jsonify({'error': 'Espèce non trouvée'}), 404
                    
                    # Mettre à jour la configuration du terrarium
                    terrarium_config = self.terrarium_service.get_terrarium_config(terrarium_id)
                    if not terrarium_config:
                        return jsonify({'error': 'Terrarium non trouvé'}), 404
                    
                    # Mettre à jour l'espèce dans la configuration
                    terrarium_config['species'] = {
                        'species_id': species_config['species_id'],
                        'common_name': species_config['common_name'],
                        'scientific_name': species_config['scientific_name'],
                        'type': species_config['category']
                    }
                    
                    # Sauvegarder la configuration
                    success = self.terrarium_service.update_terrarium_config(terrarium_id, terrarium_config)
                    
                    if success:
                        # Émettre un événement de changement d'espèce
                        self.event_bus.emit('species_changed', {
                            'terrarium_id': terrarium_id,
                            'species_id': species_id,
                            'species_config': species_config,
                            'timestamp': time.time()
                        })
                        
                        return jsonify({
                            'success': True,
                            'message': f'Espèce {species_id} définie pour le terrarium {terrarium_id}',
                            'terrarium_id': terrarium_id,
                            'species_id': species_id,
                            'timestamp': time.time()
                        })
                    else:
                        return jsonify({'error': 'Échec de la mise à jour du terrarium'}), 500
                else:
                    return jsonify({'error': 'Service de terrariums non disponible'}), 503
                    
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Erreur API changement espèce: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/terrariums/<terrarium_id>/history/sensors')
        def api_get_sensor_history(terrarium_id):
            """API : Historique des données de capteurs"""
            self.stats['requests'] += 1
            try:
                hours = request.args.get('hours', 24, type=int)
                
                if hasattr(self, 'persistence_service') and self.persistence_service:
                    history = self.persistence_service.get_sensor_history(terrarium_id, hours)
                    return jsonify({
                        'terrarium_id': terrarium_id,
                        'hours': hours,
                        'data_points': len(history),
                        'history': history
                    })
                else:
                    return jsonify({'error': 'Service de persistance non disponible'}), 503
                    
            except Exception as e:
                self.stats['errors'] += 1
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/terrariums/<terrarium_id>/history/feeding')
        def api_get_feeding_history(terrarium_id):
            """API : Historique des alimentations"""
            self.stats['requests'] += 1
            try:
                days = request.args.get('days', 30, type=int)
                
                if hasattr(self, 'persistence_service') and self.persistence_service:
                    history = self.persistence_service.get_feeding_history(terrarium_id, days)
                    return jsonify({
                        'terrarium_id': terrarium_id,
                        'days': days,
                        'feedings': len(history),
                        'history': history
                    })
                else:
                    return jsonify({'error': 'Service de persistance non disponible'}), 503
                    
            except Exception as e:
                self.stats['errors'] += 1
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/terrariums/<terrarium_id>/alerts')
        def api_get_alerts(terrarium_id):
            """API : Alertes d'un terrarium"""
            self.stats['requests'] += 1
            try:
                severity = request.args.get('severity')
                acknowledged = request.args.get('acknowledged', 'false').lower() == 'true'
                
                if hasattr(self, 'persistence_service') and self.persistence_service:
                    alerts = self.persistence_service.get_alerts(
                        terrarium_id=terrarium_id,
                        severity=severity,
                        acknowledged=acknowledged
                    )
                    return jsonify({
                        'terrarium_id': terrarium_id,
                        'alerts_count': len(alerts),
                        'alerts': alerts
                    })
                else:
                    return jsonify({'error': 'Service de persistance non disponible'}), 503
                    
            except Exception as e:
                self.stats['errors'] += 1
                return jsonify({'error': str(e)}), 500
        
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
