"""
Serveur web pour Alimante
Utilise l'API REST et sert l'interface web
"""

import time
import logging
import threading
from typing import Dict, Any, Optional
from flask import Flask, render_template, send_from_directory

from .rest_api import AlimanteAPI

class WebServer:
    """
    Serveur web principal pour Alimante
    """
    
    def __init__(self, event_bus, config: Dict[str, Any]):
        """
        Initialise le serveur web
        
        Args:
            event_bus: Bus d'événements
            config: Configuration du serveur
        """
        self.event_bus = event_bus
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration du serveur
        self.host = config.get('ui', {}).get('web', {}).get('host', '0.0.0.0')
        self.port = config.get('ui', {}).get('web', {}).get('port', 8080)
        self.debug = config.get('application', {}).get('debug', False)
        
        # État du serveur
        self.is_running = False
        self.server_thread = None
        
        # Initialiser l'API
        self.api = AlimanteAPI(event_bus, config)
        self.app = self.api.get_app()
        
        # Configurer les chemins des templates et fichiers statiques
        self._configure_paths()
        
        # Ajouter la route principale
        self._add_main_routes()
        
        # Statistiques
        self.stats = {
            'start_time': time.time(),
            'requests': 0,
            'updates': 0,
            'errors': 0
        }
    
    def _configure_paths(self):
        """Configure les chemins des templates et fichiers statiques"""
        import os
        
        # Chemin vers les templates
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'ui', 'templates')
        self.app.template_folder = template_dir
        
        # Chemin vers les fichiers statiques
        static_dir = os.path.join(os.path.dirname(__file__), '..', 'ui', 'static')
        self.app.static_folder = static_dir
        
        self.logger.info(f"Templates: {template_dir}")
        self.logger.info(f"Statiques: {static_dir}")
    
    def _add_main_routes(self):
        """Ajoute les routes principales de l'interface web"""
        
        @self.app.route('/')
        def index():
            """Page principale"""
            self.stats['requests'] += 1
            return render_template('index.html')
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Fichiers statiques"""
            import os
            static_dir = os.path.join(os.path.dirname(__file__), '..', 'ui', 'static')
            return send_from_directory(static_dir, filename)
        
        @self.app.route('/favicon.ico')
        def favicon():
            """Favicon"""
            import os
            static_dir = os.path.join(os.path.dirname(__file__), '..', 'ui', 'static')
            return send_from_directory(static_dir, 'favicon.ico')
    
    def start(self) -> bool:
        """
        Démarre le serveur web
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if self.is_running:
                self.logger.warning("Serveur web déjà en cours d'exécution")
                return True
            
            self.logger.info(f"Démarrage du serveur web sur {self.host}:{self.port}")
            
            # Démarrer le serveur dans un thread séparé
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            
            # Attendre un peu pour vérifier que le serveur démarre
            time.sleep(1)
            
            self.is_running = True
            self.logger.info("Serveur web démarré avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage serveur web: {e}")
            self.stats['errors'] += 1
            return False
    
    def _run_server(self):
        """Lance le serveur Flask"""
        try:
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
    
    def stop(self) -> None:
        """
        Arrête le serveur web
        """
        try:
            if not self.is_running:
                return
            
            self.logger.info("Arrêt du serveur web...")
            self.is_running = False
            
            # Note: Flask ne fournit pas de méthode stop() simple
            # Le serveur s'arrêtera quand le thread principal se termine
            
            self.logger.info("Serveur web arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt serveur web: {e}")
            self.stats['errors'] += 1
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Met à jour les données partagées
        
        Args:
            data: Nouvelles données à partager
        """
        try:
            self.api.update_data(data)
            self.stats['updates'] += 1
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données serveur: {e}")
            self.stats['errors'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du serveur
        
        Returns:
            Dictionnaire des statistiques
        """
        api_stats = self.api.get_stats()
        return {
            'server': self.stats.copy(),
            'api': api_stats,
            'is_running': self.is_running
        }
