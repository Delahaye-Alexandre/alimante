"""
Service de gestion de la caméra Alimante
Gère la capture d'images, le streaming et la détection de mouvement
"""

import time
import logging
import os
import threading
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from datetime import datetime, timedelta

try:
    from controllers.drivers.camera_driver import CameraDriver
    from controllers.drivers.base_driver import DriverConfig
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    CameraDriver = None
    DriverConfig = None

class CameraService:
    """
    Service de gestion de la caméra
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de caméra
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Configuration de la caméra
        self.camera_config = config.get('camera', {})
        self.camera_driver = None
        self.is_initialized = False
        
        # Configuration de capture
        self.capture_enabled = True
        self.capture_interval = self.camera_config.get('capture_interval', 300)  # 5 minutes
        self.capture_path = Path(self.camera_config.get('capture_path', 'data/captures'))
        self.max_captures = self.camera_config.get('max_captures', 1000)
        self.capture_quality = self.camera_config.get('quality', 80)
        
        # Configuration de streaming
        self.streaming_enabled = False
        self.streaming_port = self.camera_config.get('streaming_port', 8080)
        self.streaming_quality = self.camera_config.get('streaming_quality', 60)
        
        # Configuration de détection de mouvement
        self.motion_detection_enabled = False
        self.motion_threshold = self.camera_config.get('motion_threshold', 0.1)
        self.motion_sensitivity = self.camera_config.get('motion_sensitivity', 0.5)
        self.motion_cooldown = self.camera_config.get('motion_cooldown', 30)  # secondes
        
        # État du service
        self.is_running = False
        self.last_capture = None
        self.last_motion = None
        self.capture_count = 0
        self.motion_events = 0
        
        # Threads
        self.capture_thread = None
        self.streaming_thread = None
        self.stop_event = threading.Event()
        
        # Callbacks
        self.motion_callbacks = []
        
        # Statistiques
        self.stats = {
            'captures': 0,
            'motion_events': 0,
            'errors': 0,
            'uptime': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service de caméra
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not CAMERA_AVAILABLE:
                self.logger.warning("Service de caméra non disponible - OpenCV manquant")
                self.is_initialized = True
                return True
            
            # Créer le répertoire de capture
            self.capture_path.mkdir(parents=True, exist_ok=True)
            
            # Configuration du driver caméra
            driver_config = DriverConfig(
                name="camera_service",
                capture_format='jpg',
                quality=self.capture_quality
            )
            
            # Initialiser le driver caméra
            self.camera_driver = CameraDriver(driver_config, camera_index=0)
            
            if not self.camera_driver.initialize():
                self.logger.error("Échec initialisation driver caméra")
                return False
            
            # Configurer la détection de mouvement
            if self.motion_detection_enabled:
                self.camera_driver.start_motion_detection(self.motion_threshold)
            
            self.is_initialized = True
            self.logger.info("Service de caméra initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service caméra: {e}")
            self.stats['errors'] += 1
            return False
    
    def start(self) -> bool:
        """
        Démarre le service de caméra
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return False
            
            if self.is_running:
                self.logger.warning("Service de caméra déjà en cours d'exécution")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Démarrer le thread de capture
            if self.capture_enabled:
                self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
                self.capture_thread.start()
                self.logger.info("Thread de capture démarré")
            
            # Démarrer le streaming si activé
            if self.streaming_enabled:
                self.streaming_thread = threading.Thread(target=self._streaming_loop, daemon=True)
                self.streaming_thread.start()
                self.logger.info("Thread de streaming démarré")
            
            self.logger.info("Service de caméra démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service caméra: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête le service de caméra"""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            self.stop_event.set()
            
            # Attendre que les threads se terminent
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=5)
            
            if self.streaming_thread and self.streaming_thread.is_alive():
                self.streaming_thread.join(timeout=5)
            
            # Arrêter la détection de mouvement
            if self.camera_driver and self.motion_detection_enabled:
                self.camera_driver.stop_motion_detection()
            
            self.logger.info("Service de caméra arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service caméra: {e}")
            self.stats['errors'] += 1
    
    def _capture_loop(self) -> None:
        """Boucle de capture d'images"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Capturer une image
                    if self.capture_image():
                        self.stats['captures'] += 1
                        self.last_capture = time.time()
                    
                    # Attendre l'intervalle de capture
                    self.stop_event.wait(self.capture_interval)
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle de capture: {e}")
                    self.stats['errors'] += 1
                    time.sleep(5)  # Attendre avant de réessayer
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle de capture: {e}")
            self.stats['errors'] += 1
    
    def _streaming_loop(self) -> None:
        """Boucle de streaming vidéo"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Implémentation du streaming (à développer)
                    # Pour l'instant, on simule
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle de streaming: {e}")
                    self.stats['errors'] += 1
                    time.sleep(5)
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle de streaming: {e}")
            self.stats['errors'] += 1
    
    def capture_image(self, prefix: str = "capture") -> bool:
        """
        Capture une image
        
        Args:
            prefix: Préfixe du nom de fichier
            
        Returns:
            True si la capture réussit, False sinon
        """
        try:
            if not self.camera_driver:
                self.logger.warning("Driver caméra non disponible")
                return False
            
            # Capturer l'image
            filepath = self.camera_driver.capture_snapshot(prefix)
            
            if filepath:
                self.capture_count += 1
                self.logger.info(f"Image capturée: {filepath}")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('camera_capture', {
                        'filepath': filepath,
                        'timestamp': time.time(),
                        'count': self.capture_count
                    })
                
                # Nettoyer les anciennes captures si nécessaire
                self._cleanup_old_captures()
                
                return True
            else:
                self.logger.error("Échec capture d'image")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur capture d'image: {e}")
            self.stats['errors'] += 1
            return False
    
    def start_motion_detection(self, threshold: float = None) -> bool:
        """
        Démarre la détection de mouvement
        
        Args:
            threshold: Seuil de détection (optionnel)
            
        Returns:
            True si la détection démarre, False sinon
        """
        try:
            if not self.camera_driver:
                self.logger.warning("Driver caméra non disponible")
                return False
            
            if threshold is not None:
                self.motion_threshold = threshold
            
            if self.camera_driver.start_motion_detection(self.motion_threshold):
                self.motion_detection_enabled = True
                self.logger.info(f"Détection de mouvement activée (seuil: {self.motion_threshold})")
                return True
            else:
                self.logger.error("Échec activation détection de mouvement")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur activation détection mouvement: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop_motion_detection(self) -> bool:
        """
        Arrête la détection de mouvement
        
        Returns:
            True si la détection s'arrête, False sinon
        """
        try:
            if not self.camera_driver:
                return True
            
            if self.camera_driver.stop_motion_detection():
                self.motion_detection_enabled = False
                self.logger.info("Détection de mouvement désactivée")
                return True
            else:
                self.logger.error("Échec désactivation détection de mouvement")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur désactivation détection mouvement: {e}")
            self.stats['errors'] += 1
            return False
    
    def add_motion_callback(self, callback: Callable) -> None:
        """
        Ajoute un callback pour les événements de mouvement
        
        Args:
            callback: Fonction à appeler lors de la détection de mouvement
        """
        self.motion_callbacks.append(callback)
        self.logger.info("Callback de mouvement ajouté")
    
    def remove_motion_callback(self, callback: Callable) -> None:
        """
        Supprime un callback de mouvement
        
        Args:
            callback: Fonction à supprimer
        """
        if callback in self.motion_callbacks:
            self.motion_callbacks.remove(callback)
            self.logger.info("Callback de mouvement supprimé")
    
    def _handle_motion_detected(self) -> None:
        """Gère la détection de mouvement"""
        try:
            current_time = time.time()
            
            # Vérifier le cooldown
            if self.last_motion and (current_time - self.last_motion) < self.motion_cooldown:
                return
            
            self.last_motion = current_time
            self.motion_events += 1
            self.stats['motion_events'] += 1
            
            self.logger.info(f"Mouvement détecté (événement #{self.motion_events})")
            
            # Appeler les callbacks
            for callback in self.motion_callbacks:
                try:
                    callback({
                        'timestamp': current_time,
                        'event_count': self.motion_events,
                        'threshold': self.motion_threshold
                    })
                except Exception as e:
                    self.logger.error(f"Erreur callback mouvement: {e}")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('motion_detected', {
                    'timestamp': current_time,
                    'event_count': self.motion_events,
                    'threshold': self.motion_threshold
                })
            
        except Exception as e:
            self.logger.error(f"Erreur gestion mouvement détecté: {e}")
            self.stats['errors'] += 1
    
    def _cleanup_old_captures(self) -> None:
        """Nettoie les anciennes captures"""
        try:
            if self.capture_count <= self.max_captures:
                return
            
            # Lister tous les fichiers de capture
            capture_files = list(self.capture_path.glob("*.jpg"))
            capture_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Supprimer les plus anciens
            files_to_remove = capture_files[:-self.max_captures]
            for file_path in files_to_remove:
                try:
                    file_path.unlink()
                    self.logger.debug(f"Ancienne capture supprimée: {file_path}")
                except Exception as e:
                    self.logger.error(f"Erreur suppression fichier {file_path}: {e}")
            
            self.logger.info(f"{len(files_to_remove)} anciennes captures supprimées")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage captures: {e}")
            self.stats['errors'] += 1
    
    def get_latest_captures(self, count: int = 10) -> List[str]:
        """
        Récupère les dernières captures
        
        Args:
            count: Nombre de captures à récupérer
            
        Returns:
            Liste des chemins des fichiers
        """
        try:
            capture_files = list(self.capture_path.glob("*.jpg"))
            capture_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return [str(f) for f in capture_files[:count]]
            
        except Exception as e:
            self.logger.error(f"Erreur récupération captures: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service de caméra
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'service': 'camera',
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'capture_enabled': self.capture_enabled,
            'capture_interval': self.capture_interval,
            'capture_count': self.capture_count,
            'last_capture': self.last_capture,
            'motion_detection_enabled': self.motion_detection_enabled,
            'motion_threshold': self.motion_threshold,
            'motion_events': self.motion_events,
            'last_motion': self.last_motion,
            'streaming_enabled': self.streaming_enabled,
            'capture_path': str(self.capture_path),
            'max_captures': self.max_captures,
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie le service de caméra"""
        try:
            # Arrêter le service
            self.stop()
            
            # Nettoyer le driver
            if self.camera_driver:
                self.camera_driver.cleanup()
                self.camera_driver = None
            
            self.is_initialized = False
            self.logger.info("Service de caméra nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service caméra: {e}")
            self.stats['errors'] += 1
