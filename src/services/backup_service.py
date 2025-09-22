"""
Service de sauvegarde automatique et synchronisation cloud pour Alimante
Gère les sauvegardes locales et la synchronisation avec le cloud
"""

import logging
import shutil
import zipfile
import json
import os
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import sqlite3

from ..utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory

class BackupType(Enum):
    """Types de sauvegarde"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    CONFIG = "config"
    DATA = "data"

class BackupStatus(Enum):
    """Statuts de sauvegarde"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"

class SyncStatus(Enum):
    """Statuts de synchronisation"""
    IDLE = "idle"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"

@dataclass
class BackupInfo:
    """Information sur une sauvegarde"""
    id: str
    type: BackupType
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime]
    size: int
    file_path: str
    checksum: str
    description: str
    metadata: Dict[str, Any]

@dataclass
class SyncInfo:
    """Information sur une synchronisation"""
    id: str
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime]
    files_synced: int
    files_failed: int
    bytes_synced: int
    error_message: Optional[str]

class BackupService:
    """
    Service de sauvegarde automatique et synchronisation cloud
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        
        # Configuration de sauvegarde
        self.backup_enabled = config.get('backup_enabled', True)
        self.backup_interval = config.get('backup_interval', 86400)  # 24 heures
        self.retention_days = config.get('retention_days', 30)
        self.max_backups = config.get('max_backups', 10)
        
        # Configuration de synchronisation
        self.sync_enabled = config.get('sync_enabled', False)
        self.sync_interval = config.get('sync_interval', 3600)  # 1 heure
        self.cloud_provider = config.get('cloud_provider', 'local')
        self.cloud_config = config.get('cloud', {})
        
        # Répertoires à sauvegarder
        self.backup_paths = config.get('backup_paths', [
            'config/',
            'data/',
            'logs/',
            'src/'
        ])
        
        # Fichiers à exclure
        self.exclude_patterns = config.get('exclude_patterns', [
            '*.pyc',
            '__pycache__/',
            '*.log',
            '.git/',
            'node_modules/',
            '*.tmp'
        ])
        
        # Stockage des sauvegardes
        self.backups: List[BackupInfo] = []
        self.sync_history: List[SyncInfo] = []
        
        # Threads
        self.backup_thread: Optional[threading.Thread] = None
        self.sync_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Répertoires de travail
        self.backup_dir = 'backups/'
        self.temp_dir = 'temp/backup/'
        
        self.logger.info("Service de sauvegarde initialisé")
    
    def initialize(self) -> bool:
        """Initialise le service de sauvegarde"""
        try:
            self.logger.info("Initialisation du service de sauvegarde...")
            
            # Créer les répertoires nécessaires
            os.makedirs(self.backup_dir, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # Charger l'historique des sauvegardes
            self._load_backup_history()
            
            # Démarrer les threads
            self.running = True
            
            if self.backup_enabled:
                self.backup_thread = threading.Thread(
                    target=self._backup_loop,
                    name="BackupThread",
                    daemon=True
                )
                self.backup_thread.start()
            
            if self.sync_enabled:
                self.sync_thread = threading.Thread(
                    target=self._sync_loop,
                    name="SyncThread",
                    daemon=True
                )
                self.sync_thread.start()
            
            self.logger.info("Service de sauvegarde initialisé avec succès")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "initialize",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def start(self) -> bool:
        """Démarre le service de sauvegarde"""
        return True  # Déjà démarré dans initialize
    
    def stop(self) -> bool:
        """Arrête le service de sauvegarde"""
        try:
            self.running = False
            
            # Attendre que les threads se terminent
            if self.backup_thread and self.backup_thread.is_alive():
                self.backup_thread.join(timeout=10.0)
            
            if self.sync_thread and self.sync_thread.is_alive():
                self.sync_thread.join(timeout=10.0)
            
            # Sauvegarder l'historique
            self._save_backup_history()
            
            self.logger.info("Service de sauvegarde arrêté")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "stop",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
    
    def _load_backup_history(self):
        """Charge l'historique des sauvegardes"""
        try:
            history_file = os.path.join(self.backup_dir, 'backup_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    data = json.load(f)
                
                for backup_data in data.get('backups', []):
                    backup = BackupInfo(
                        id=backup_data['id'],
                        type=BackupType(backup_data['type']),
                        status=BackupStatus(backup_data['status']),
                        created_at=datetime.fromisoformat(backup_data['created_at']),
                        completed_at=datetime.fromisoformat(backup_data['completed_at']) if backup_data['completed_at'] else None,
                        size=backup_data['size'],
                        file_path=backup_data['file_path'],
                        checksum=backup_data['checksum'],
                        description=backup_data['description'],
                        metadata=backup_data['metadata']
                    )
                    self.backups.append(backup)
                
                self.logger.info(f"Chargé {len(self.backups)} sauvegardes")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_load_backup_history",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _save_backup_history(self):
        """Sauvegarde l'historique des sauvegardes"""
        try:
            history_file = os.path.join(self.backup_dir, 'backup_history.json')
            data = {
                'backups': [
                    {
                        'id': backup.id,
                        'type': backup.type.value,
                        'status': backup.status.value,
                        'created_at': backup.created_at.isoformat(),
                        'completed_at': backup.completed_at.isoformat() if backup.completed_at else None,
                        'size': backup.size,
                        'file_path': backup.file_path,
                        'checksum': backup.checksum,
                        'description': backup.description,
                        'metadata': backup.metadata
                    }
                    for backup in self.backups
                ]
            }
            
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_save_backup_history",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _backup_loop(self):
        """Boucle principale de sauvegarde"""
        while self.running:
            try:
                # Vérifier si une sauvegarde est nécessaire
                if self._should_create_backup():
                    self._create_backup(BackupType.FULL, "Sauvegarde automatique")
                
                # Nettoyer les anciennes sauvegardes
                self._cleanup_old_backups()
                
                # Attendre l'intervalle
                time.sleep(self.backup_interval)
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "BackupService", "_backup_loop",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                time.sleep(300)  # Attendre 5 minutes en cas d'erreur
    
    def _sync_loop(self):
        """Boucle principale de synchronisation"""
        while self.running:
            try:
                # Effectuer la synchronisation
                self._sync_to_cloud()
                
                # Attendre l'intervalle
                time.sleep(self.sync_interval)
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "BackupService", "_sync_loop",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                time.sleep(300)
    
    def _should_create_backup(self) -> bool:
        """Détermine si une sauvegarde doit être créée"""
        try:
            if not self.backups:
                return True
            
            # Vérifier la dernière sauvegarde
            last_backup = max(self.backups, key=lambda b: b.created_at)
            time_since_last = datetime.now() - last_backup.created_at
            
            return time_since_last.total_seconds() >= self.backup_interval
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_should_create_backup",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
            return False
    
    def create_backup(self, backup_type: BackupType, description: str = "") -> Tuple[bool, str]:
        """
        Crée une sauvegarde manuelle
        
        Returns:
            Tuple[success, backup_id]
        """
        try:
            return self._create_backup(backup_type, description)
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "create_backup",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False, ""
    
    def _create_backup(self, backup_type: BackupType, description: str) -> Tuple[bool, str]:
        """Crée une sauvegarde"""
        try:
            backup_id = f"backup_{int(time.time())}_{backup_type.value}"
            backup_file = os.path.join(self.backup_dir, f"{backup_id}.zip")
            
            # Créer l'info de sauvegarde
            backup_info = BackupInfo(
                id=backup_id,
                type=backup_type,
                status=BackupStatus.IN_PROGRESS,
                created_at=datetime.now(),
                completed_at=None,
                size=0,
                file_path=backup_file,
                checksum="",
                description=description,
                metadata={}
            )
            
            self.backups.append(backup_info)
            
            # Créer la sauvegarde
            success = self._create_backup_archive(backup_info)
            
            if success:
                backup_info.status = BackupStatus.COMPLETED
                backup_info.completed_at = datetime.now()
                backup_info.size = os.path.getsize(backup_file)
                backup_info.checksum = self._calculate_checksum(backup_file)
                
                self.logger.info(f"Sauvegarde créée: {backup_id} ({backup_info.size} bytes)")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('backup_created', {
                        'backup_id': backup_id,
                        'backup_type': backup_type.value,
                        'size': backup_info.size,
                        'timestamp': backup_info.completed_at.isoformat()
                    })
                
                return True, backup_id
            else:
                backup_info.status = BackupStatus.FAILED
                self.logger.error(f"Échec de la sauvegarde: {backup_id}")
                return False, backup_id
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_create_backup",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False, ""
    
    def _create_backup_archive(self, backup_info: BackupInfo) -> bool:
        """Crée l'archive de sauvegarde"""
        try:
            with zipfile.ZipFile(backup_info.file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for path in self.backup_paths:
                    if os.path.exists(path):
                        if os.path.isfile(path):
                            # Fichier simple
                            if not self._should_exclude(path):
                                zipf.write(path, path)
                        else:
                            # Répertoire
                            for root, dirs, files in os.walk(path):
                                # Filtrer les répertoires à exclure
                                dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d))]
                                
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    if not self._should_exclude(file_path):
                                        arcname = os.path.relpath(file_path)
                                        zipf.write(file_path, arcname)
            
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_create_backup_archive",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
    
    def _should_exclude(self, path: str) -> bool:
        """Vérifie si un chemin doit être exclu"""
        try:
            for pattern in self.exclude_patterns:
                if pattern.endswith('/'):
                    # Répertoire
                    if path.endswith(pattern.rstrip('/')):
                        return True
                else:
                    # Fichier
                    if path.endswith(pattern) or pattern in path:
                        return True
            return False
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_should_exclude",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
            return False
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calcule le checksum d'un fichier"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_calculate_checksum",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
            return ""
    
    def _cleanup_old_backups(self):
        """Nettoie les anciennes sauvegardes"""
        try:
            now = datetime.now()
            cutoff_date = now - timedelta(days=self.retention_days)
            
            # Supprimer les sauvegardes anciennes
            backups_to_remove = []
            for backup in self.backups:
                if backup.created_at < cutoff_date:
                    backups_to_remove.append(backup)
            
            for backup in backups_to_remove:
                try:
                    if os.path.exists(backup.file_path):
                        os.remove(backup.file_path)
                    self.backups.remove(backup)
                    self.logger.info(f"Sauvegarde supprimée: {backup.id}")
                except Exception as e:
                    self.logger.warning(f"Impossible de supprimer la sauvegarde {backup.id}: {e}")
            
            # Limiter le nombre de sauvegardes
            if len(self.backups) > self.max_backups:
                # Trier par date de création et garder les plus récentes
                self.backups.sort(key=lambda b: b.created_at, reverse=True)
                excess_backups = self.backups[self.max_backups:]
                
                for backup in excess_backups:
                    try:
                        if os.path.exists(backup.file_path):
                            os.remove(backup.file_path)
                        self.backups.remove(backup)
                        self.logger.info(f"Sauvegarde supprimée (limite): {backup.id}")
                    except Exception as e:
                        self.logger.warning(f"Impossible de supprimer la sauvegarde {backup.id}: {e}")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_cleanup_old_backups",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _sync_to_cloud(self):
        """Synchronise les sauvegardes avec le cloud"""
        try:
            if not self.sync_enabled:
                return
            
            sync_id = f"sync_{int(time.time())}"
            sync_info = SyncInfo(
                id=sync_id,
                status=SyncStatus.SYNCING,
                started_at=datetime.now(),
                completed_at=None,
                files_synced=0,
                files_failed=0,
                bytes_synced=0,
                error_message=None
            )
            
            self.sync_history.append(sync_info)
            
            try:
                if self.cloud_provider == 'local':
                    success = self._sync_to_local_cloud()
                elif self.cloud_provider == 'aws':
                    success = self._sync_to_aws()
                elif self.cloud_provider == 'google':
                    success = self._sync_to_google()
                else:
                    self.logger.warning(f"Fournisseur cloud non supporté: {self.cloud_provider}")
                    success = False
                
                if success:
                    sync_info.status = SyncStatus.COMPLETED
                    sync_info.completed_at = datetime.now()
                    self.logger.info(f"Synchronisation réussie: {sync_id}")
                else:
                    sync_info.status = SyncStatus.FAILED
                    sync_info.error_message = "Échec de la synchronisation"
                    self.logger.error(f"Échec de la synchronisation: {sync_id}")
                
            except Exception as e:
                sync_info.status = SyncStatus.FAILED
                sync_info.error_message = str(e)
                self.error_handler.log_error(
                    e, "BackupService", "_sync_to_cloud",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_sync_to_cloud",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
    
    def _sync_to_local_cloud(self) -> bool:
        """Synchronise vers un répertoire cloud local"""
        try:
            cloud_dir = self.cloud_config.get('local_path', 'cloud_backups/')
            os.makedirs(cloud_dir, exist_ok=True)
            
            files_synced = 0
            for backup in self.backups:
                if backup.status == BackupStatus.COMPLETED:
                    cloud_file = os.path.join(cloud_dir, os.path.basename(backup.file_path))
                    if not os.path.exists(cloud_file):
                        shutil.copy2(backup.file_path, cloud_file)
                        files_synced += 1
            
            self.logger.info(f"Synchronisation locale: {files_synced} fichiers")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_sync_to_local_cloud",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def _sync_to_aws(self) -> bool:
        """Synchronise vers AWS S3"""
        try:
            # Implémentation AWS S3 (simulation)
            self.logger.info("Synchronisation AWS S3 (simulation)")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_sync_to_aws",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def _sync_to_google(self) -> bool:
        """Synchronise vers Google Cloud Storage"""
        try:
            # Implémentation Google Cloud (simulation)
            self.logger.info("Synchronisation Google Cloud (simulation)")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "_sync_to_google",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def restore_backup(self, backup_id: str, restore_path: str = ".") -> Tuple[bool, str]:
        """
        Restaure une sauvegarde
        
        Returns:
            Tuple[success, message]
        """
        try:
            # Trouver la sauvegarde
            backup = None
            for b in self.backups:
                if b.id == backup_id:
                    backup = b
                    break
            
            if not backup:
                return False, "Sauvegarde non trouvée"
            
            if backup.status != BackupStatus.COMPLETED:
                return False, "Sauvegarde non complète"
            
            if not os.path.exists(backup.file_path):
                return False, "Fichier de sauvegarde introuvable"
            
            # Restaurer l'archive
            with zipfile.ZipFile(backup.file_path, 'r') as zipf:
                zipf.extractall(restore_path)
            
            self.logger.info(f"Sauvegarde restaurée: {backup_id} -> {restore_path}")
            return True, f"Sauvegarde {backup_id} restaurée avec succès"
            
        except Exception as e:
            self.error_handler.log_error(
                e, "BackupService", "restore_backup",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False, f"Erreur lors de la restauration: {str(e)}"
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des sauvegardes"""
        total_size = sum(backup.size for backup in self.backups)
        
        return {
            'total_backups': len(self.backups),
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'by_type': {
                backup_type.value: len([b for b in self.backups if b.type == backup_type])
                for backup_type in BackupType
            },
            'by_status': {
                status.value: len([b for b in self.backups if b.status == status])
                for status in BackupStatus
            },
            'last_backup': max(self.backups, key=lambda b: b.created_at).created_at.isoformat() if self.backups else None,
            'sync_enabled': self.sync_enabled,
            'cloud_provider': self.cloud_provider
        }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Liste toutes les sauvegardes"""
        return [
            {
                'id': backup.id,
                'type': backup.type.value,
                'status': backup.status.value,
                'created_at': backup.created_at.isoformat(),
                'completed_at': backup.completed_at.isoformat() if backup.completed_at else None,
                'size': backup.size,
                'size_mb': backup.size / (1024 * 1024),
                'checksum': backup.checksum,
                'description': backup.description
            }
            for backup in sorted(self.backups, key=lambda b: b.created_at, reverse=True)
        ]
