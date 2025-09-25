"""
Service de gestion des snapshots Alimante
Gère la capture, le stockage et la gestion des images
"""

import time
import logging
import threading
import shutil
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    SNAPSHOT_AVAILABLE = True
except ImportError:
    # Mode simulation pour Windows
    SNAPSHOT_AVAILABLE = False
    cv2 = None
    np = None
    Image = None
    ImageDraw = None
    ImageFont = None

class SnapshotType(Enum):
    """Types de snapshots"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    MOTION = "motion"
    ALERT = "alert"
    DAILY = "daily"

class SnapshotService:
    """
    Service de gestion des snapshots
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de snapshots
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Configuration des snapshots
        self.snapshot_config = config.get('snapshots', {})
        self.enabled = self.snapshot_config.get('enabled', True)
        self.storage_path = Path(self.snapshot_config.get('storage_path', 'data/snapshots'))
        self.max_snapshots = self.snapshot_config.get('max_snapshots', 1000)
        self.retention_days = self.snapshot_config.get('retention_days', 30)
        
        # Configuration de capture
        self.width = self.snapshot_config.get('width', 1280)
        self.height = self.snapshot_config.get('height', 720)
        self.quality = self.snapshot_config.get('quality', 90)
        self.format = self.snapshot_config.get('format', 'jpg')
        
        # Configuration des annotations
        self.annotate_enabled = self.snapshot_config.get('annotate', True)
        self.show_timestamp = self.snapshot_config.get('show_timestamp', True)
        self.show_sensors = self.snapshot_config.get('show_sensors', True)
        self.show_terrarium = self.snapshot_config.get('show_terrarium', True)
        
        # État du service
        self.is_running = False
        self.camera = None
        self.snapshot_count = 0
        
        # Threads
        self.cleanup_thread = None
        self.stop_event = threading.Event()
        
        # Callbacks
        self.snapshot_callbacks = []
        
        # Statistiques
        self.stats = {
            'snapshots_taken': 0,
            'snapshots_deleted': 0,
            'storage_used': 0,
            'errors': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service de snapshots
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.enabled:
                self.logger.info("Service de snapshots désactivé")
                return True
            
            if not SNAPSHOT_AVAILABLE:
                self.logger.warning("Service de snapshots non disponible - OpenCV manquant")
                return True
            
            # Créer le répertoire de stockage
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # Initialiser la caméra
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.logger.error("Impossible d'ouvrir la caméra pour les snapshots")
                return False
            
            # Configurer la caméra
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            self.logger.info(f"Service de snapshots initialisé ({self.width}x{self.height})")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service snapshots: {e}")
            self.stats['errors'] += 1
            return False
    
    def start(self) -> bool:
        """
        Démarre le service de snapshots
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.enabled:
                self.logger.info("Service de snapshots désactivé")
                return True
            
            if self.is_running:
                self.logger.warning("Service de snapshots déjà en cours d'exécution")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Démarrer le thread de nettoyage
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            
            self.logger.info("Service de snapshots démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service snapshots: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête le service de snapshots"""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            self.stop_event.set()
            
            # Attendre que le thread se termine
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)
            
            # Libérer la caméra
            if self.camera:
                self.camera.release()
                self.camera = None
            
            self.logger.info("Service de snapshots arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service snapshots: {e}")
            self.stats['errors'] += 1
    
    def _cleanup_loop(self) -> None:
        """Boucle de nettoyage des anciens snapshots"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Nettoyer les anciens snapshots
                    self._cleanup_old_snapshots()
                    
                    # Attendre 1 heure avant le prochain nettoyage
                    self.stop_event.wait(3600)
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle de nettoyage: {e}")
                    self.stats['errors'] += 1
                    time.sleep(60)
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle de nettoyage: {e}")
            self.stats['errors'] += 1
    
    def _cleanup_old_snapshots(self) -> None:
        """Nettoie les anciens snapshots"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            
            for snapshot_file in self.storage_path.glob(f"*.{self.format}"):
                try:
                    # Vérifier l'âge du fichier
                    file_time = datetime.fromtimestamp(snapshot_file.stat().st_mtime)
                    
                    if file_time < cutoff_date:
                        snapshot_file.unlink()
                        deleted_count += 1
                        self.stats['snapshots_deleted'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Erreur suppression snapshot {snapshot_file}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"{deleted_count} anciens snapshots supprimés")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage anciens snapshots: {e}")
            self.stats['errors'] += 1
    
    def take_snapshot(self, snapshot_type: SnapshotType = SnapshotType.MANUAL, 
                     annotate: bool = None, metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Prend un snapshot
        
        Args:
            snapshot_type: Type de snapshot
            annotate: Annoter l'image (None = utiliser la config)
            metadata: Métadonnées à afficher
            
        Returns:
            Chemin du fichier créé ou None
        """
        try:
            if not self.enabled or not self.camera:
                self.logger.warning("Service de snapshots non disponible")
                return None
            
            # Capturer une frame
            ret, frame = self.camera.read()
            if not ret:
                self.logger.error("Échec capture frame pour snapshot")
                return None
            
            # Redimensionner si nécessaire
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height))
            
            # Annoter l'image si demandé
            if annotate is None:
                annotate = self.annotate_enabled
            
            if annotate:
                frame = self._annotate_image(frame, snapshot_type, metadata)
            
            # Générer le nom de fichier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{snapshot_type.value}_{timestamp}.{self.format}"
            filepath = self.storage_path / filename
            
            # Sauvegarder l'image
            if self.format.lower() == 'jpg':
                cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
            else:
                cv2.imwrite(str(filepath), frame)
            
            self.snapshot_count += 1
            self.stats['snapshots_taken'] += 1
            
            self.logger.info(f"Snapshot pris: {filename}")
            
            # Appeler les callbacks
            for callback in self.snapshot_callbacks:
                try:
                    callback(filepath, snapshot_type, metadata)
                except Exception as e:
                    self.logger.error(f"Erreur callback snapshot: {e}")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('snapshot_taken', {
                    'filepath': str(filepath),
                    'type': snapshot_type.value,
                    'metadata': metadata or {},
                    'timestamp': time.time()
                })
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Erreur prise snapshot: {e}")
            self.stats['errors'] += 1
            return None
    
    def _annotate_image(self, frame: 'np.ndarray', snapshot_type: SnapshotType, 
                       metadata: Dict[str, Any] = None) -> 'np.ndarray':
        """Annote une image avec des informations"""
        try:
            if not SNAPSHOT_AVAILABLE:
                return frame
            
            # Convertir en PIL pour l'annotation
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            draw = ImageDraw.Draw(pil_image)
            
            # Charger une police
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Couleurs
            white = (255, 255, 255)
            black = (0, 0, 0)
            red = (255, 0, 0)
            green = (0, 255, 0)
            
            y_offset = 10
            
            # Timestamp
            if self.show_timestamp:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                draw.text((10, y_offset), f"Timestamp: {timestamp}", fill=white, font=font)
                y_offset += 25
            
            # Type de snapshot
            draw.text((10, y_offset), f"Type: {snapshot_type.value.upper()}", fill=white, font=font)
            y_offset += 25
            
            # Terrarium
            if self.show_terrarium and metadata:
                terrarium = metadata.get('terrarium', 'Unknown')
                draw.text((10, y_offset), f"Terrarium: {terrarium}", fill=white, font=font)
                y_offset += 25
            
            # Données des capteurs
            if self.show_sensors and metadata:
                sensors = metadata.get('sensors', {})
                if sensors:
                    temp = sensors.get('temperature', 0)
                    hum = sensors.get('humidity', 0)
                    draw.text((10, y_offset), f"Temp: {temp:.1f}°C", fill=white, font=font)
                    y_offset += 25
                    draw.text((10, y_offset), f"Humidity: {hum:.0f}%", fill=white, font=font)
                    y_offset += 25
            
            # Statut des systèmes
            if metadata:
                systems = metadata.get('systems', {})
                if systems:
                    heating = "ON" if systems.get('heating', False) else "OFF"
                    lighting = "ON" if systems.get('lighting', False) else "OFF"
                    draw.text((10, y_offset), f"Heating: {heating}", 
                            fill=green if systems.get('heating', False) else red, font=font)
                    y_offset += 25
                    draw.text((10, y_offset), f"Lighting: {lighting}", 
                            fill=green if systems.get('lighting', False) else red, font=font)
                    y_offset += 25
            
            # Convertir de nouveau en OpenCV
            frame_annotated = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return frame_annotated
            
        except Exception as e:
            self.logger.error(f"Erreur annotation image: {e}")
            return frame
    
    def get_latest_snapshots(self, count: int = 10, snapshot_type: SnapshotType = None) -> List[Dict[str, Any]]:
        """
        Récupère les derniers snapshots
        
        Args:
            count: Nombre de snapshots à récupérer
            snapshot_type: Type de snapshot (None = tous)
            
        Returns:
            Liste des informations des snapshots
        """
        try:
            snapshots = []
            
            # Lister tous les fichiers
            pattern = f"*.{self.format}"
            if snapshot_type:
                pattern = f"{snapshot_type.value}_*.{self.format}"
            
            files = list(self.storage_path.glob(pattern))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file_path in files[:count]:
                try:
                    stat = file_path.stat()
                    snapshots.append({
                        'filename': file_path.name,
                        'filepath': str(file_path),
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'type': self._extract_snapshot_type(file_path.name)
                    })
                except Exception as e:
                    self.logger.error(f"Erreur traitement fichier {file_path}: {e}")
            
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Erreur récupération snapshots: {e}")
            return []
    
    def _extract_snapshot_type(self, filename: str) -> str:
        """Extrait le type de snapshot du nom de fichier"""
        try:
            parts = filename.split('_')
            if parts:
                return parts[0]
            return 'unknown'
        except:
            return 'unknown'
    
    def delete_snapshot(self, filename: str) -> bool:
        """
        Supprime un snapshot
        
        Args:
            filename: Nom du fichier à supprimer
            
        Returns:
            True si la suppression réussit, False sinon
        """
        try:
            file_path = self.storage_path / filename
            
            if not file_path.exists():
                self.logger.warning(f"Snapshot {filename} non trouvé")
                return False
            
            file_path.unlink()
            self.stats['snapshots_deleted'] += 1
            
            self.logger.info(f"Snapshot supprimé: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur suppression snapshot {filename}: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Récupère les informations de stockage
        
        Returns:
            Dictionnaire contenant les informations de stockage
        """
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.storage_path.glob(f"*.{self.format}"):
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except:
                    pass
            
            return {
                'total_files': file_count,
                'total_size': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'max_snapshots': self.max_snapshots,
                'retention_days': self.retention_days,
                'storage_path': str(self.storage_path)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur récupération info stockage: {e}")
            return {}
    
    def add_snapshot_callback(self, callback: Callable) -> None:
        """
        Ajoute un callback pour les snapshots
        
        Args:
            callback: Fonction à appeler lors de la prise d'un snapshot
        """
        self.snapshot_callbacks.append(callback)
        self.logger.info("Callback snapshot ajouté")
    
    def remove_snapshot_callback(self, callback: Callable) -> None:
        """
        Supprime un callback de snapshot
        
        Args:
            callback: Fonction à supprimer
        """
        if callback in self.snapshot_callbacks:
            self.snapshot_callbacks.remove(callback)
            self.logger.info("Callback snapshot supprimé")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service de snapshots
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'service': 'snapshots',
            'enabled': self.enabled,
            'is_running': self.is_running,
            'storage_path': str(self.storage_path),
            'max_snapshots': self.max_snapshots,
            'retention_days': self.retention_days,
            'snapshot_count': self.snapshot_count,
            'storage_info': self.get_storage_info(),
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie le service de snapshots"""
        try:
            # Arrêter le service
            self.stop()
            
            self.logger.info("Service de snapshots nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service snapshots: {e}")
            self.stats['errors'] += 1
