"""
Service de streaming vidéo Alimante
Gère le streaming en temps réel et l'enregistrement vidéo
"""

import time
import logging
import threading
import socket
import struct
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image
    import base64
    STREAMING_AVAILABLE = True
except ImportError:
    # Essayer d'utiliser l'OpenCV système
    try:
        import sys
        sys.path.append('/usr/lib/python3/dist-packages')
        import cv2
        import numpy as np
        from PIL import Image
        import base64
        STREAMING_AVAILABLE = True
        print("Using system OpenCV for streaming")
    except ImportError:
        # Mode simulation pour Windows
        STREAMING_AVAILABLE = False
        cv2 = None
        np = None
        Image = None
        base64 = None

class StreamFormat(Enum):
    """Formats de streaming"""
    MJPEG = "mjpeg"
    H264 = "h264"
    WEBRTC = "webrtc"

class StreamQuality(Enum):
    """Qualités de streaming"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

class StreamingService:
    """
    Service de streaming vidéo
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de streaming
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Configuration du streaming
        self.streaming_config = config.get('streaming', {})
        self.enabled = self.streaming_config.get('enabled', False)
        self.port = self.streaming_config.get('port', 8080)
        self.host = self.streaming_config.get('host', '0.0.0.0')
        self.max_clients = self.streaming_config.get('max_clients', 10)
        
        # Configuration vidéo
        self.width = self.streaming_config.get('width', 640)
        self.height = self.streaming_config.get('height', 480)
        self.fps = self.streaming_config.get('fps', 30)
        self.quality = self.streaming_config.get('quality', 80)
        self.format = StreamFormat(self.streaming_config.get('format', 'mjpeg'))
        
        # État du service
        self.is_running = False
        self.is_streaming = False
        self.server_socket = None
        self.clients = []
        self.camera = None
        
        # Threads
        self.server_thread = None
        self.streaming_thread = None
        self.stop_event = threading.Event()
        
        # Enregistrement vidéo
        self.recording_enabled = False
        self.recording_path = Path(self.streaming_config.get('recording_path', 'data/recordings'))
        self.recording_duration = self.streaming_config.get('recording_duration', 3600)  # 1 heure
        self.video_writer = None
        self.recording_start_time = None
        
        # Statistiques
        self.stats = {
            'clients_connected': 0,
            'frames_sent': 0,
            'bytes_sent': 0,
            'recording_time': 0,
            'errors': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service de streaming
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.enabled:
                self.logger.info("Service de streaming désactivé")
                return True
            
            if not STREAMING_AVAILABLE:
                self.logger.warning("Service de streaming non disponible - OpenCV manquant")
                return True
            
            # Créer le répertoire d'enregistrement
            self.recording_path.mkdir(parents=True, exist_ok=True)
            
            # Initialiser la caméra
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.logger.error("Impossible d'ouvrir la caméra pour le streaming")
                return False
            
            # Configurer la caméra
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            self.logger.info(f"Service de streaming initialisé ({self.width}x{self.height} @ {self.fps}fps)")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service streaming: {e}")
            self.stats['errors'] += 1
            return False
    
    def start(self) -> bool:
        """
        Démarre le service de streaming
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.enabled:
                self.logger.info("Service de streaming désactivé")
                return True
            
            if self.is_running:
                self.logger.warning("Service de streaming déjà en cours d'exécution")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Démarrer le serveur de streaming
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            # Démarrer le thread de streaming
            self.streaming_thread = threading.Thread(target=self._streaming_loop, daemon=True)
            self.streaming_thread.start()
            
            self.logger.info(f"Service de streaming démarré sur {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service streaming: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête le service de streaming"""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            self.is_streaming = False
            self.stop_event.set()
            
            # Fermer toutes les connexions clients
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
            
            # Fermer le serveur
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            
            # Arrêter l'enregistrement
            if self.recording_enabled:
                self.stop_recording()
            
            # Attendre que les threads se terminent
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5)
            
            if self.streaming_thread and self.streaming_thread.is_alive():
                self.streaming_thread.join(timeout=5)
            
            # Libérer la caméra
            if self.camera:
                self.camera.release()
                self.camera = None
            
            self.logger.info("Service de streaming arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service streaming: {e}")
            self.stats['errors'] += 1
    
    def _server_loop(self) -> None:
        """Boucle principale du serveur de streaming"""
        try:
            # Créer le socket serveur
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            
            self.logger.info(f"Serveur de streaming en écoute sur {self.host}:{self.port}")
            
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Accepter les connexions
                    client_socket, address = self.server_socket.accept()
                    
                    if len(self.clients) < self.max_clients:
                        # Ajouter le client
                        self.clients.append(client_socket)
                        self.stats['clients_connected'] = len(self.clients)
                        
                        self.logger.info(f"Client connecté: {address}")
                        
                        # Émettre un événement
                        if self.event_bus:
                            self.event_bus.emit('streaming_client_connected', {
                                'address': address,
                                'total_clients': len(self.clients),
                                'timestamp': time.time()
                            })
                    else:
                        # Trop de clients
                        client_socket.close()
                        self.logger.warning(f"Connexion refusée - trop de clients: {address}")
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        self.logger.error(f"Erreur acceptation connexion: {e}")
                        self.stats['errors'] += 1
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle serveur: {e}")
            self.stats['errors'] += 1
    
    def _streaming_loop(self) -> None:
        """Boucle de streaming vidéo"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    if not self.camera or not self.clients:
                        time.sleep(0.1)
                        continue
                    
                    # Capturer une frame
                    ret, frame = self.camera.read()
                    if not ret:
                        self.logger.error("Échec capture frame pour streaming")
                        time.sleep(0.1)
                        continue
                    
                    # Traiter la frame
                    processed_frame = self._process_frame(frame)
                    
                    # Encoder la frame
                    encoded_frame = self._encode_frame(processed_frame)
                    
                    if encoded_frame:
                        # Envoyer à tous les clients
                        self._send_to_clients(encoded_frame)
                        
                        # Enregistrer si activé
                        if self.recording_enabled:
                            self._record_frame(processed_frame)
                    
                    # Contrôler le FPS
                    time.sleep(1.0 / self.fps)
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle de streaming: {e}")
                    self.stats['errors'] += 1
                    time.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle de streaming: {e}")
            self.stats['errors'] += 1
    
    def _process_frame(self, frame: 'np.ndarray') -> 'np.ndarray':
        """Traite une frame pour le streaming"""
        try:
            # Redimensionner si nécessaire
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height))
            
            # Appliquer des filtres selon la qualité
            if self.quality < 50:
                # Qualité faible - flou
                frame = cv2.GaussianBlur(frame, (5, 5), 0)
            elif self.quality > 80:
                # Qualité élevée - netteté
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                frame = cv2.filter2D(frame, -1, kernel)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Erreur traitement frame: {e}")
            return frame
    
    def _encode_frame(self, frame: 'np.ndarray') -> Optional[bytes]:
        """Encode une frame selon le format"""
        try:
            if self.format == StreamFormat.MJPEG:
                # Encoder en MJPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
                ret, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                if ret:
                    # Créer l'en-tête HTTP
                    header = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: image/jpeg\r\n"
                        f"Content-Length: {len(buffer)}\r\n"
                        f"Cache-Control: no-cache\r\n"
                        f"Connection: close\r\n\r\n"
                    )
                    return header.encode() + buffer.tobytes()
            
            elif self.format == StreamFormat.H264:
                # Encoder en H264 (nécessite un encodeur H264)
                # Pour l'instant, on utilise MJPEG
                return self._encode_frame(frame)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur encodage frame: {e}")
            return None
    
    def _send_to_clients(self, data: bytes) -> None:
        """Envoie les données à tous les clients"""
        try:
            clients_to_remove = []
            
            for client in self.clients:
                try:
                    client.send(data)
                    self.stats['frames_sent'] += 1
                    self.stats['bytes_sent'] += len(data)
                except Exception as e:
                    self.logger.warning(f"Erreur envoi client: {e}")
                    clients_to_remove.append(client)
            
            # Supprimer les clients déconnectés
            for client in clients_to_remove:
                self.clients.remove(client)
                self.stats['clients_connected'] = len(self.clients)
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('streaming_client_disconnected', {
                        'total_clients': len(self.clients),
                        'timestamp': time.time()
                    })
            
        except Exception as e:
            self.logger.error(f"Erreur envoi clients: {e}")
            self.stats['errors'] += 1
    
    def _record_frame(self, frame: 'np.ndarray') -> None:
        """Enregistre une frame pour l'enregistrement vidéo"""
        try:
            if not self.video_writer:
                # Créer le writer vidéo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.recording_path / f"recording_{timestamp}.mp4"
                
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(
                    str(filename),
                    fourcc,
                    self.fps,
                    (self.width, self.height)
                )
                
                self.recording_start_time = time.time()
                self.logger.info(f"Enregistrement démarré: {filename}")
            
            # Écrire la frame
            self.video_writer.write(frame)
            self.stats['recording_time'] = time.time() - self.recording_start_time
            
            # Vérifier la durée d'enregistrement
            if self.stats['recording_time'] >= self.recording_duration:
                self.stop_recording()
            
        except Exception as e:
            self.logger.error(f"Erreur enregistrement frame: {e}")
            self.stats['errors'] += 1
    
    def start_recording(self) -> bool:
        """
        Démarre l'enregistrement vidéo
        
        Returns:
            True si l'enregistrement démarre, False sinon
        """
        try:
            if self.recording_enabled:
                self.logger.warning("Enregistrement déjà en cours")
                return True
            
            self.recording_enabled = True
            self.logger.info("Enregistrement vidéo démarré")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('recording_started', {
                    'timestamp': time.time()
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage enregistrement: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop_recording(self) -> bool:
        """
        Arrête l'enregistrement vidéo
        
        Returns:
            True si l'enregistrement s'arrête, False sinon
        """
        try:
            if not self.recording_enabled:
                return True
            
            self.recording_enabled = False
            
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            self.logger.info("Enregistrement vidéo arrêté")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('recording_stopped', {
                    'duration': self.stats['recording_time'],
                    'timestamp': time.time()
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt enregistrement: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_stream_url(self) -> str:
        """
        Retourne l'URL du stream
        
        Returns:
            URL du stream
        """
        return f"http://{self.host}:{self.port}/stream"
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service de streaming
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'service': 'streaming',
            'enabled': self.enabled,
            'is_running': self.is_running,
            'is_streaming': self.is_streaming,
            'host': self.host,
            'port': self.port,
            'format': self.format.value,
            'quality': self.quality,
            'resolution': f"{self.width}x{self.height}",
            'fps': self.fps,
            'clients_connected': len(self.clients),
            'max_clients': self.max_clients,
            'recording_enabled': self.recording_enabled,
            'recording_time': self.stats['recording_time'],
            'stream_url': self.get_stream_url(),
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie le service de streaming"""
        try:
            # Arrêter le service
            self.stop()
            
            self.logger.info("Service de streaming nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service streaming: {e}")
            self.stats['errors'] += 1
