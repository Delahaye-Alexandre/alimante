"""
Driver caméra pour Alimante
Gère la capture d'images et le streaming vidéo
"""

import time
import logging
import os
from typing import Dict, Any, Optional, Tuple
from .base_driver import BaseDriver, DriverConfig, DriverState

try:
    import cv2
    import numpy as np
    from PIL import Image
    CAMERA_AVAILABLE = True
except ImportError:
    # Mode simulation pour Windows
    CAMERA_AVAILABLE = False
    cv2 = None
    np = None
    Image = None

class CameraDriver(BaseDriver):
    """
    Driver caméra pour la capture d'images et le streaming
    """
    
    def __init__(self, config: DriverConfig, camera_index: int = 0):
        """
        Initialise le driver caméra
        
        Args:
            config: Configuration du driver
            camera_index: Index de la caméra (0 par défaut)
        """
        super().__init__(config)
        self.camera_index = camera_index
        self.camera = None
        self.is_streaming = False
        self.stream_thread = None
        
        # Configuration de la caméra
        self.width = 640
        self.height = 480
        self.fps = 30
        self.quality = 80  # Qualité JPEG (0-100)
        
        # Configuration de capture
        self.capture_format = 'jpg'
        self.capture_path = 'data/captures'
        self.max_captures = 1000
        self.capture_count = 0
        
        # Configuration de streaming
        self.stream_port = 8080
        self.stream_enabled = False
        self.stream_quality = 60
        
        # Détection de mouvement
        self.motion_detection = False
        self.motion_threshold = 0.1
        self.motion_sensitivity = 0.5
        self.last_frame = None
        self.motion_detected = False
        
        # Statistiques
        self.frames_captured = 0
        self.frames_processed = 0
        self.motion_events = 0
        
    def initialize(self) -> bool:
        """
        Initialise le driver caméra
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not CAMERA_AVAILABLE:
                self.logger.warning("Mode simulation - OpenCV non disponible")
                self.state = DriverState.READY
                return True
            
            # Créer le répertoire de capture
            os.makedirs(self.capture_path, exist_ok=True)
            
            # Initialiser la caméra
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                self.logger.error(f"Impossible d'ouvrir la caméra {self.camera_index}")
                self.state = DriverState.ERROR
                return False
            
            # Configurer la caméra
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Vérifier la configuration
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"Caméra initialisée: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            self.state = DriverState.READY
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation driver caméra: {e}")
            self.state = DriverState.ERROR
            return False
    
    def read(self) -> Dict[str, Any]:
        """
        Lit l'état du driver caméra
        
        Returns:
            Dictionnaire contenant l'état du driver
        """
        try:
            self.read_count += 1
            self.last_update = time.time()
            
            return {
                'driver': 'camera',
                'state': self.state.value,
                'camera_index': self.camera_index,
                'resolution': f"{self.width}x{self.height}",
                'fps': self.fps,
                'is_streaming': self.is_streaming,
                'stream_enabled': self.stream_enabled,
                'motion_detection': self.motion_detection,
                'motion_detected': self.motion_detected,
                'capture_path': self.capture_path,
                'capture_count': self.capture_count,
                'stats': {
                    'read_count': self.read_count,
                    'error_count': self.error_count,
                    'frames_captured': self.frames_captured,
                    'frames_processed': self.frames_processed,
                    'motion_events': self.motion_events,
                    'uptime': time.time() - self.start_time
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lecture driver caméra: {e}")
            self.error_count += 1
            self.last_error = e
            return {'error': str(e)}
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Écrit des données vers le driver caméra
        
        Args:
            data: Données à écrire (capture, stream, etc.)
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        try:
            action = data.get('action', 'capture')
            
            if action == 'capture':
                return self._capture_image(data)
            elif action == 'start_stream':
                return self._start_streaming(data)
            elif action == 'stop_stream':
                return self._stop_streaming()
            elif action == 'set_motion_detection':
                return self._set_motion_detection(data)
            else:
                self.logger.warning(f"Action inconnue: {action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur écriture driver caméra: {e}")
            self.error_count += 1
            self.last_error = e
            return False
    
    def _capture_image(self, data: Dict[str, Any]) -> bool:
        """Capture une image"""
        try:
            if not CAMERA_AVAILABLE or not self.camera:
                self.logger.warning("Mode simulation - capture d'image simulée")
                self.frames_captured += 1
                return True
            
            # Capturer une frame
            ret, frame = self.camera.read()
            if not ret:
                self.logger.error("Échec capture d'image")
                return False
            
            # Traitement de l'image
            frame = self._process_frame(frame, data)
            
            # Sauvegarder l'image
            filename = self._generate_filename(data)
            filepath = os.path.join(self.capture_path, filename)
            
            if self.capture_format.lower() == 'jpg':
                cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
            else:
                cv2.imwrite(filepath, frame)
            
            self.frames_captured += 1
            self.capture_count += 1
            
            self.logger.info(f"Image capturée: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur capture d'image: {e}")
            return False
    
    def _process_frame(self, frame: 'np.ndarray', data: Dict[str, Any]) -> 'np.ndarray':
        """Traite une frame (redimensionnement, filtres, etc.)"""
        try:
            # Redimensionner si nécessaire
            if data.get('resize'):
                width = data.get('width', self.width)
                height = data.get('height', self.height)
                frame = cv2.resize(frame, (width, height))
            
            # Appliquer des filtres
            if data.get('blur'):
                frame = cv2.GaussianBlur(frame, (15, 15), 0)
            
            if data.get('sharpen'):
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                frame = cv2.filter2D(frame, -1, kernel)
            
            # Détection de mouvement
            if self.motion_detection:
                self._detect_motion(frame)
            
            self.frames_processed += 1
            return frame
            
        except Exception as e:
            self.logger.error(f"Erreur traitement frame: {e}")
            return frame
    
    def _detect_motion(self, frame: 'np.ndarray') -> None:
        """Détecte le mouvement dans la frame"""
        try:
            # Convertir en niveaux de gris
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if self.last_frame is not None:
                # Calculer la différence
                frame_delta = cv2.absdiff(self.last_frame, gray)
                thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                
                # Compter les pixels de mouvement
                motion_pixels = cv2.countNonZero(thresh)
                total_pixels = thresh.shape[0] * thresh.shape[1]
                motion_ratio = motion_pixels / total_pixels
                
                # Déclencher l'événement de mouvement
                if motion_ratio > self.motion_threshold:
                    if not self.motion_detected:
                        self.motion_detected = True
                        self.motion_events += 1
                        self.logger.info(f"Mouvement détecté: {motion_ratio:.2%}")
                else:
                    self.motion_detected = False
            
            self.last_frame = gray
            
        except Exception as e:
            self.logger.error(f"Erreur détection mouvement: {e}")
    
    def _generate_filename(self, data: Dict[str, Any]) -> str:
        """Génère un nom de fichier pour la capture"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        prefix = data.get('prefix', 'capture')
        return f"{prefix}_{timestamp}.{self.capture_format}"
    
    def _start_streaming(self, data: Dict[str, Any]) -> bool:
        """Démarre le streaming vidéo"""
        try:
            if self.is_streaming:
                self.logger.warning("Streaming déjà actif")
                return True
            
            self.stream_enabled = True
            self.is_streaming = True
            self.stream_port = data.get('port', self.stream_port)
            self.stream_quality = data.get('quality', self.stream_quality)
            
            self.logger.info(f"Streaming démarré sur le port {self.stream_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage streaming: {e}")
            return False
    
    def _stop_streaming(self) -> bool:
        """Arrête le streaming vidéo"""
        try:
            self.stream_enabled = False
            self.is_streaming = False
            
            self.logger.info("Streaming arrêté")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt streaming: {e}")
            return False
    
    def _set_motion_detection(self, data: Dict[str, Any]) -> bool:
        """Configure la détection de mouvement"""
        try:
            self.motion_detection = data.get('enabled', False)
            self.motion_threshold = data.get('threshold', self.motion_threshold)
            self.motion_sensitivity = data.get('sensitivity', self.motion_sensitivity)
            
            self.logger.info(f"Détection de mouvement: {'activée' if self.motion_detection else 'désactivée'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur configuration détection mouvement: {e}")
            return False
    
    def capture_snapshot(self, prefix: str = "snapshot") -> Optional[str]:
        """
        Capture un instantané
        
        Args:
            prefix: Préfixe du nom de fichier
            
        Returns:
            Chemin du fichier capturé ou None
        """
        try:
            if self.write({'action': 'capture', 'prefix': prefix}):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{prefix}_{timestamp}.{self.capture_format}"
                return os.path.join(self.capture_path, filename)
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur capture instantané: {e}")
            return None
    
    def start_motion_detection(self, threshold: float = 0.1) -> bool:
        """
        Démarre la détection de mouvement
        
        Args:
            threshold: Seuil de détection (0-1)
            
        Returns:
            True si la détection démarre, False sinon
        """
        try:
            return self.write({
                'action': 'set_motion_detection',
                'enabled': True,
                'threshold': threshold
            })
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage détection mouvement: {e}")
            return False
    
    def stop_motion_detection(self) -> bool:
        """
        Arrête la détection de mouvement
        
        Returns:
            True si la détection s'arrête, False sinon
        """
        try:
            return self.write({
                'action': 'set_motion_detection',
                'enabled': False
            })
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt détection mouvement: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du driver caméra
        
        Returns:
            Dictionnaire contenant le statut
        """
        return self.read()
    
    def cleanup(self) -> None:
        """Nettoie le driver caméra"""
        try:
            # Arrêter le streaming
            if self.is_streaming:
                self._stop_streaming()
            
            # Libérer la caméra
            if self.camera:
                self.camera.release()
                self.camera = None
            
            self.state = DriverState.DISABLED
            self.logger.info("Driver caméra nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage driver caméra: {e}")
