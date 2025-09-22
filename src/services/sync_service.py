"""
Service de synchronisation Alimante
Gère la synchronisation des données avec le cloud et les tunnels
"""

import time
import logging
import threading
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

class SyncStatus(Enum):
    """Statuts de synchronisation"""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    FAILED = "failed"
    DISABLED = "disabled"

class SyncType(Enum):
    """Types de synchronisation"""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    BIDIRECTIONAL = "bidirectional"

class SyncService:
    """
    Service de synchronisation des données
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de synchronisation
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Configuration de synchronisation
        self.sync_config = config.get('sync', {})
        self.enabled = self.sync_config.get('enabled', False)
        self.sync_interval = self.sync_config.get('sync_interval', 3600)  # 1 heure
        self.retry_interval = self.sync_config.get('retry_interval', 300)  # 5 minutes
        self.max_retries = self.sync_config.get('max_retries', 3)
        
        # Configuration cloud
        self.cloud_config = self.sync_config.get('cloud', {})
        self.api_url = self.cloud_config.get('api_url')
        self.api_key = self.cloud_config.get('api_key')
        self.device_id = self.cloud_config.get('device_id')
        
        # Configuration tunnel
        self.tunnel_config = self.sync_config.get('tunnel', {})
        self.tunnel_enabled = self.tunnel_config.get('enabled', False)
        self.tunnel_url = self.tunnel_config.get('url')
        self.tunnel_token = self.tunnel_config.get('token')
        
        # État du service
        self.status = SyncStatus.IDLE
        self.is_running = False
        self.last_sync = None
        self.next_sync = None
        self.retry_count = 0
        self.current_sync_type = None
        
        # Threads
        self.sync_thread = None
        self.stop_event = threading.Event()
        
        # Données à synchroniser
        self.pending_uploads = []
        self.pending_downloads = []
        
        # Statistiques
        self.stats = {
            'syncs_successful': 0,
            'syncs_failed': 0,
            'data_uploaded': 0,
            'data_downloaded': 0,
            'errors': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service de synchronisation
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.enabled:
                self.status = SyncStatus.DISABLED
                self.logger.info("Service de synchronisation désactivé")
                return True
            
            # Vérifier la configuration
            if not self._validate_config():
                self.logger.error("Configuration de synchronisation invalide")
                return False
            
            # Créer les répertoires nécessaires
            self._create_directories()
            
            # Planifier la première synchronisation
            self.next_sync = datetime.now() + timedelta(seconds=30)
            
            self.logger.info("Service de synchronisation initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service synchronisation: {e}")
            self.stats['errors'] += 1
            return False
    
    def start(self) -> bool:
        """
        Démarre le service de synchronisation
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.enabled:
                self.logger.info("Service de synchronisation désactivé")
                return True
            
            if self.is_running:
                self.logger.warning("Service de synchronisation déjà en cours d'exécution")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Démarrer le thread de synchronisation
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            
            self.logger.info("Service de synchronisation démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service synchronisation: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête le service de synchronisation"""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            self.stop_event.set()
            
            # Attendre que le thread se termine
            if self.sync_thread and self.sync_thread.is_alive():
                self.sync_thread.join(timeout=10)
            
            self.logger.info("Service de synchronisation arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service synchronisation: {e}")
            self.stats['errors'] += 1
    
    def _sync_loop(self) -> None:
        """Boucle principale de synchronisation"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    current_time = datetime.now()
                    
                    # Vérifier si c'est le moment de synchroniser
                    if (self.next_sync and 
                        current_time >= self.next_sync and 
                        self.status == SyncStatus.IDLE):
                        
                        self._perform_sync()
                    
                    # Attendre avant la prochaine vérification
                    self.stop_event.wait(60)  # Vérifier toutes les minutes
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle de synchronisation: {e}")
                    self.stats['errors'] += 1
                    time.sleep(30)
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle de synchronisation: {e}")
            self.stats['errors'] += 1
    
    def _perform_sync(self) -> None:
        """Effectue une synchronisation"""
        try:
            self.status = SyncStatus.SYNCING
            self.logger.info("Début de la synchronisation")
            
            # Synchroniser les données
            success = True
            
            # Upload des données locales
            if self._upload_data():
                self.logger.info("Upload des données réussi")
            else:
                success = False
                self.logger.error("Échec upload des données")
            
            # Download des données distantes
            if self._download_data():
                self.logger.info("Download des données réussi")
            else:
                success = False
                self.logger.error("Échec download des données")
            
            # Mettre à jour le statut
            if success:
                self.status = SyncStatus.SUCCESS
                self.last_sync = datetime.now()
                self.next_sync = self.last_sync + timedelta(seconds=self.sync_interval)
                self.retry_count = 0
                self.stats['syncs_successful'] += 1
                
                self.logger.info("Synchronisation réussie")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('sync_completed', {
                        'timestamp': time.time(),
                        'success': True
                    })
            else:
                self.status = SyncStatus.FAILED
                self.retry_count += 1
                self.stats['syncs_failed'] += 1
                
                # Planifier une nouvelle tentative
                if self.retry_count < self.max_retries:
                    self.next_sync = datetime.now() + timedelta(seconds=self.retry_interval)
                    self.logger.info(f"Nouvelle tentative dans {self.retry_interval} secondes")
                else:
                    self.next_sync = datetime.now() + timedelta(seconds=self.sync_interval)
                    self.retry_count = 0
                    self.logger.error("Nombre maximum de tentatives atteint")
                
                # Émettre un événement d'erreur
                if self.event_bus:
                    self.event_bus.emit('sync_failed', {
                        'timestamp': time.time(),
                        'retry_count': self.retry_count
                    })
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la synchronisation: {e}")
            self.status = SyncStatus.FAILED
            self.stats['errors'] += 1
            self.stats['syncs_failed'] += 1
        
        finally:
            # Retourner à l'état inactif après un délai
            threading.Timer(10.0, lambda: setattr(self, 'status', SyncStatus.IDLE)).start()
    
    def _upload_data(self) -> bool:
        """Upload les données locales vers le cloud"""
        try:
            if not self.api_url or not self.api_key:
                self.logger.warning("Configuration cloud manquante pour l'upload")
                return True
            
            # Préparer les données à uploader
            upload_data = self._prepare_upload_data()
            
            if not upload_data:
                self.logger.info("Aucune donnée à uploader")
                return True
            
            # Envoyer les données
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.api_url}/api/devices/{self.device_id}/data",
                json=upload_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                self.stats['data_uploaded'] += len(upload_data)
                self.logger.info(f"Upload réussi: {len(upload_data)} éléments")
                return True
            else:
                self.logger.error(f"Échec upload: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur upload des données: {e}")
            return False
    
    def _download_data(self) -> bool:
        """Download les données du cloud vers le local"""
        try:
            if not self.api_url or not self.api_key:
                self.logger.warning("Configuration cloud manquante pour le download")
                return True
            
            # Récupérer les données
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_url}/api/devices/{self.device_id}/data",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self._process_downloaded_data(data)
                self.stats['data_downloaded'] += len(data.get('data', []))
                self.logger.info(f"Download réussi: {len(data.get('data', []))} éléments")
                return True
            else:
                self.logger.error(f"Échec download: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur download des données: {e}")
            return False
    
    def _prepare_upload_data(self) -> List[Dict[str, Any]]:
        """Prépare les données à uploader"""
        try:
            upload_data = []
            
            # Récupérer les données des capteurs
            sensor_data = self._get_sensor_data()
            if sensor_data:
                upload_data.extend(sensor_data)
            
            # Récupérer les logs d'alimentation
            feeding_data = self._get_feeding_data()
            if feeding_data:
                upload_data.extend(feeding_data)
            
            # Récupérer les alertes
            alerts_data = self._get_alerts_data()
            if alerts_data:
                upload_data.extend(alerts_data)
            
            return upload_data
            
        except Exception as e:
            self.logger.error(f"Erreur préparation données upload: {e}")
            return []
    
    def _get_sensor_data(self) -> List[Dict[str, Any]]:
        """Récupère les données des capteurs"""
        try:
            # Cette méthode devrait interroger le service de persistance
            # Pour l'instant, on simule
            return []
            
        except Exception as e:
            self.logger.error(f"Erreur récupération données capteurs: {e}")
            return []
    
    def _get_feeding_data(self) -> List[Dict[str, Any]]:
        """Récupère les données d'alimentation"""
        try:
            # Cette méthode devrait interroger le service de persistance
            # Pour l'instant, on simule
            return []
            
        except Exception as e:
            self.logger.error(f"Erreur récupération données alimentation: {e}")
            return []
    
    def _get_alerts_data(self) -> List[Dict[str, Any]]:
        """Récupère les données d'alertes"""
        try:
            # Cette méthode devrait interroger le service de persistance
            # Pour l'instant, on simule
            return []
            
        except Exception as e:
            self.logger.error(f"Erreur récupération données alertes: {e}")
            return []
    
    def _process_downloaded_data(self, data: Dict[str, Any]) -> None:
        """Traite les données téléchargées"""
        try:
            # Traiter les données téléchargées
            # Cette méthode devrait sauvegarder les données localement
            self.logger.info("Données téléchargées traitées")
            
        except Exception as e:
            self.logger.error(f"Erreur traitement données téléchargées: {e}")
    
    def _validate_config(self) -> bool:
        """Valide la configuration de synchronisation"""
        try:
            if not self.enabled:
                return True
            
            # Vérifier la configuration cloud
            if self.cloud_config.get('enabled', False):
                if not self.api_url or not self.api_key or not self.device_id:
                    self.logger.error("Configuration cloud incomplète")
                    return False
            
            # Vérifier la configuration tunnel
            if self.tunnel_enabled:
                if not self.tunnel_url or not self.tunnel_token:
                    self.logger.error("Configuration tunnel incomplète")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur validation configuration: {e}")
            return False
    
    def _create_directories(self) -> None:
        """Crée les répertoires nécessaires"""
        try:
            # Créer le répertoire de synchronisation
            sync_dir = Path("data/sync")
            sync_dir.mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            self.logger.error(f"Erreur création répertoires: {e}")
    
    def force_sync(self) -> bool:
        """
        Force une synchronisation immédiate
        
        Returns:
            True si la synchronisation est lancée, False sinon
        """
        try:
            if not self.enabled:
                self.logger.warning("Service de synchronisation désactivé")
                return False
            
            if self.status == SyncStatus.SYNCING:
                self.logger.warning("Synchronisation déjà en cours")
                return False
            
            # Planifier une synchronisation immédiate
            self.next_sync = datetime.now()
            self.logger.info("Synchronisation forcée planifiée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur synchronisation forcée: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service de synchronisation
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'service': 'sync',
            'enabled': self.enabled,
            'is_running': self.is_running,
            'status': self.status.value,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'next_sync': self.next_sync.isoformat() if self.next_sync else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'sync_interval': self.sync_interval,
            'cloud_enabled': bool(self.cloud_config.get('enabled', False)),
            'tunnel_enabled': self.tunnel_enabled,
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie le service de synchronisation"""
        try:
            # Arrêter le service
            self.stop()
            
            self.logger.info("Service de synchronisation nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service synchronisation: {e}")
            self.stats['errors'] += 1
