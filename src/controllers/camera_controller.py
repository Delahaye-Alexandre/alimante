"""
Contrôleur pour caméra CSI Raspberry Pi
Gestion des captures d'images et streaming vidéo pour l'API web
"""

import io
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


class CameraController:
    """Contrôleur pour caméra CSI avec streaming et capture d'images"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("camera_controller")
        self.config = config
        
        # Configuration de la caméra
        self.camera_type = config.get("type", "CSI")
        self.resolution = config.get("resolution", "1920x1080")
        self.framerate = config.get("framerate", 30)
        self.format = config.get("format", "MJPEG")
        self.stream_port = config.get("stream_port", 8080)
        
        # État de la caméra
        self.camera = None
        self.is_initialized = False
        self.is_streaming = False
        self.error_count = 0
        self.last_capture = None
        self.capture_count = 0
        self.is_available = False  # Disponibilité du composant
        
        # Streaming
        self.stream_thread = None
        self.stream_active = False
        
        # Initialisation
        self._initialize_camera()
        
        self.logger.info("Contrôleur caméra CSI initialisé")
    
    def _initialize_camera(self):
        """Initialise la caméra CSI"""
        try:
            # Importer Picamera2 pour Raspberry Pi
            try:
                from picamera2 import Picamera2
                self.camera_library = "picamera2"
                
                self.camera = Picamera2()
                
                # Configuration de base
                width, height = map(int, self.resolution.split('x'))
                config = self.camera.create_still_configuration(
                    main={"size": (width, height), "format": "RGB888"}
                )
                self.camera.configure(config)
                
                self.is_initialized = True
                self.is_available = True
                self.logger.info(f"✅ Caméra initialisée: {self.resolution}@{self.framerate}fps")
                
            except ImportError:
                self.logger.warning("⚠️ Picamera2 non disponible, tentative avec OpenCV")
                # Fallback vers OpenCV
                try:
                    import cv2
                    self.camera_library = "opencv"
                    self.camera = cv2.VideoCapture(0)
                    
                    if not self.camera.isOpened():
                        raise Exception("Impossible d'ouvrir la caméra avec OpenCV")
                    
                    # Configuration OpenCV
                    width, height = map(int, self.resolution.split('x'))
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    self.camera.set(cv2.CAP_PROP_FPS, self.framerate)
                    
                    self.is_initialized = True
                    self.is_available = True
                    self.logger.info(f"✅ Caméra OpenCV initialisée: {self.resolution}")
                    
                except ImportError:
                    self.logger.error("❌ Ni Picamera2 ni OpenCV disponibles")
                    self.is_available = False
                    raise Exception("Ni Picamera2 ni OpenCV disponibles")
                    
        except Exception as e:
            self.is_available = False
            self.logger.exception("❌ Erreur initialisation caméra")
            self.error_count += 1
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible d'initialiser la caméra CSI",
                {"camera_type": self.camera_type, "original_error": str(e)}
            )
    
    def capture_image(self, save_path: Optional[str] = None) -> bytes:
        """Capture une image et la retourne en bytes"""
        if not self.is_available:
            self.logger.warning("⚠️ Tentative de capture avec caméra désactivée - composant non disponible")
            raise create_exception(
                ErrorCode.CONTROLLER_CONTROL_FAILED,
                "Caméra non disponible",
                {"reason": "Composant non détecté"}
            )
        
        try:
            if not self.is_initialized:
                raise Exception("Caméra non initialisée")
            
            image_buffer = io.BytesIO()
            
            if self.camera_library == "picamera2":
                # Démarrer la caméra si nécessaire
                if not self.camera.started:
                    self.camera.start()
                
                # Capturer l'image
                self.camera.capture_file(image_buffer, format='jpeg')
                
                # Arrêter la caméra si pas de streaming actif
                if not self.is_streaming:
                    self.camera.stop()
                    
            elif self.camera_library == "opencv":
                import cv2
                ret, frame = self.camera.read()
                if not ret:
                    raise Exception("Échec de capture avec OpenCV")
                
                # Encoder en JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                image_buffer.write(buffer.tobytes())
            
            # Sauvegarder si chemin spécifié
            if save_path:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(image_buffer.getvalue())
                self.logger.info(f"Image sauvegardée: {save_path}")
            
            self.last_capture = datetime.now()
            self.capture_count += 1
            
            image_buffer.seek(0)
            return image_buffer.getvalue()
            
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur capture image")
            raise create_exception(
                ErrorCode.CONTROLLER_CONTROL_FAILED,
                "Impossible de capturer une image",
                {"original_error": str(e)}
            )
    
    def start_streaming(self) -> bool:
        """Démarre le streaming vidéo"""
        if not self.is_available:
            self.logger.warning("⚠️ Tentative de démarrage streaming avec caméra désactivée - composant non disponible")
            return False
        
        try:
            if self.is_streaming:
                self.logger.debug("Streaming déjà actif")
                return True
            
            if not self.is_initialized:
                raise Exception("Caméra non initialisée")
            
            # Démarrer le thread de streaming
            self.stream_active = True
            self.stream_thread = threading.Thread(target=self._stream_worker)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
            self.is_streaming = True
            self.logger.info("Streaming caméra démarré")
            return True
            
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur démarrage streaming")
            raise create_exception(
                ErrorCode.CONTROLLER_CONTROL_FAILED,
                "Impossible de démarrer le streaming",
                {"original_error": str(e)}
            )
    
    def stop_streaming(self) -> bool:
        """Arrête le streaming vidéo"""
        try:
            if not self.is_streaming:
                self.logger.debug("Streaming déjà arrêté")
                return True
            
            self.stream_active = False
            
            # Attendre la fin du thread
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=5)
            
            self.is_streaming = False
            self.logger.info("Streaming caméra arrêté")
            return True
            
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur arrêt streaming")
            return False
    
    def _stream_worker(self):
        """Worker thread pour le streaming"""
        try:
            if self.camera_library == "picamera2":
                self.camera.start()
                
                while self.stream_active:
                    # Ici on pourrait implémenter un serveur HTTP pour le streaming
                    # Pour l'instant, on simule juste l'activité
                    time.sleep(1.0 / self.framerate)
                    
                self.camera.stop()
                
            elif self.camera_library == "opencv":
                while self.stream_active:
                    ret, frame = self.camera.read()
                    if not ret:
                        break
                    # Traitement du frame pour streaming
                    time.sleep(1.0 / self.framerate)
                    
        except Exception as e:
            self.logger.exception("Erreur dans le worker de streaming")
            self.stream_active = False
    
    def take_snapshot(self) -> str:
        """Prend un snapshot avec timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.jpg"
            save_path = f"logs/camera/{filename}"
            
            self.capture_image(save_path)
            return save_path
            
        except Exception as e:
            self.logger.exception("Erreur prise de snapshot")
            raise create_exception(
                ErrorCode.CONTROLLER_CONTROL_FAILED,
                "Impossible de prendre un snapshot",
                {"original_error": str(e)}
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Récupère le statut du contrôleur caméra"""
        try:
            return {
                "status": "ok" if self.error_count == 0 and self.is_available else "disabled" if not self.is_available else "error",
                "component_available": self.is_available,
                "camera_type": self.camera_type,
                "library": getattr(self, 'camera_library', 'unknown'),
                "resolution": self.resolution,
                "framerate": self.framerate,
                "format": self.format,
                "is_initialized": self.is_initialized,
                "is_streaming": self.is_streaming,
                "capture_count": self.capture_count,
                "error_count": self.error_count,
                "last_capture": self.last_capture.isoformat() if self.last_capture else None,
                "stream_port": self.stream_port,
                "component_info": {
                    "available": self.is_available,
                    "reason_disabled": "Composant non détecté" if not self.is_available else None
                }
            }
            
        except Exception as e:
            self.logger.exception("Erreur récupération statut caméra")
            return {
                "status": "error",
                "error": str(e),
                "is_initialized": False
            }
    
    def check_status(self) -> bool:
        """Vérifie le statut du contrôleur"""
        try:
            return self.is_initialized and self.error_count < 5
            
        except Exception as e:
            self.logger.exception("Erreur vérification statut caméra")
            return False
    
    def cleanup(self):
        """Nettoie les ressources de la caméra"""
        try:
            self.stop_streaming()
            
            if self.camera:
                if self.camera_library == "picamera2":
                    if hasattr(self.camera, 'close'):
                        self.camera.close()
                elif self.camera_library == "opencv":
                    self.camera.release()
                
                self.camera = None
            
            self.is_initialized = False
            self.logger.info("Contrôleur caméra nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage caméra: {e}")
