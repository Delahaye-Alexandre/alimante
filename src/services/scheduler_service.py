"""
Service de planification des tâches Alimante
Gère l'exécution de tâches planifiées et récurrentes
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

class TaskType(Enum):
    """Types de tâches"""
    ONCE = "once"           # Exécution unique
    DAILY = "daily"         # Quotidienne
    WEEKLY = "weekly"       # Hebdomadaire
    MONTHLY = "monthly"     # Mensuelle
    INTERVAL = "interval"   # Par intervalle de temps

class TaskStatus(Enum):
    """Statuts des tâches"""
    PENDING = "pending"     # En attente
    RUNNING = "running"     # En cours d'exécution
    COMPLETED = "completed" # Terminée
    FAILED = "failed"       # Échouée
    CANCELLED = "cancelled" # Annulée

@dataclass
class ScheduledTask:
    """Tâche planifiée"""
    id: str
    name: str
    task_type: TaskType
    callback: Callable
    args: tuple = ()
    kwargs: dict = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    enabled: bool = True
    max_retries: int = 3
    retry_count: int = 0
    error_message: Optional[str] = None
    
    # Configuration spécifique au type
    interval_seconds: Optional[int] = None  # Pour INTERVAL
    hour: Optional[int] = None              # Pour DAILY
    minute: Optional[int] = None            # Pour DAILY
    weekday: Optional[int] = None           # Pour WEEKLY (0=lundi, 6=dimanche)
    day: Optional[int] = None               # Pour MONTHLY

class SchedulerService:
    """
    Service de planification des tâches
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de planification
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Configuration du service
        self.scheduler_config = config.get('scheduler', {})
        self.check_interval = self.scheduler_config.get('check_interval', 1.0)  # secondes
        self.max_concurrent_tasks = self.scheduler_config.get('max_concurrent_tasks', 5)
        
        # État du service
        self.is_running = False
        self.tasks = {}  # id -> ScheduledTask
        self.running_tasks = {}  # id -> thread
        self.task_counter = 0
        
        # Thread principal
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        
        # Statistiques
        self.stats = {
            'tasks_created': 0,
            'tasks_executed': 0,
            'tasks_failed': 0,
            'tasks_cancelled': 0,
            'errors': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service de planification
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Service de planification initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service planification: {e}")
            self.stats['errors'] += 1
            return False
    
    def start(self) -> bool:
        """
        Démarre le service de planification
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if self.is_running:
                self.logger.warning("Service de planification déjà en cours d'exécution")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Démarrer le thread principal
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            self.logger.info("Service de planification démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service planification: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête le service de planification"""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            self.stop_event.set()
            
            # Annuler toutes les tâches en cours
            for task_id in list(self.running_tasks.keys()):
                self.cancel_task(task_id)
            
            # Attendre que le thread principal se termine
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            self.logger.info("Service de planification arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service planification: {e}")
            self.stats['errors'] += 1
    
    def _scheduler_loop(self) -> None:
        """Boucle principale du planificateur"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    current_time = datetime.now()
                    
                    # Vérifier les tâches à exécuter
                    self._check_pending_tasks(current_time)
                    
                    # Nettoyer les tâches terminées
                    self._cleanup_completed_tasks()
                    
                    # Attendre avant la prochaine vérification
                    self.stop_event.wait(self.check_interval)
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle du planificateur: {e}")
                    self.stats['errors'] += 1
                    time.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle du planificateur: {e}")
            self.stats['errors'] += 1
    
    def _check_pending_tasks(self, current_time: datetime) -> None:
        """Vérifie les tâches en attente"""
        try:
            for task_id, task in self.tasks.items():
                if (task.status == TaskStatus.PENDING and 
                    task.enabled and 
                    task.next_run and 
                    current_time >= task.next_run):
                    
                    # Vérifier si on peut exécuter la tâche
                    if len(self.running_tasks) < self.max_concurrent_tasks:
                        self._execute_task(task)
                    else:
                        self.logger.warning(f"Trop de tâches en cours, report de {task.name}")
                        
        except Exception as e:
            self.logger.error(f"Erreur vérification tâches en attente: {e}")
            self.stats['errors'] += 1
    
    def _execute_task(self, task: ScheduledTask) -> None:
        """Exécute une tâche"""
        try:
            # Marquer la tâche comme en cours
            task.status = TaskStatus.RUNNING
            task.last_run = datetime.now()
            
            # Créer un thread pour exécuter la tâche
            thread = threading.Thread(
                target=self._run_task,
                args=(task,),
                daemon=True
            )
            
            self.running_tasks[task.id] = thread
            thread.start()
            
            self.logger.info(f"Tâche '{task.name}' démarrée")
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage tâche {task.name}: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            self.stats['errors'] += 1
    
    def _run_task(self, task: ScheduledTask) -> None:
        """Exécute une tâche dans un thread séparé"""
        try:
            # Exécuter la tâche
            result = task.callback(*task.args, **(task.kwargs or {}))
            
            # Marquer comme terminée
            task.status = TaskStatus.COMPLETED
            task.retry_count = 0
            task.error_message = None
            
            self.stats['tasks_executed'] += 1
            
            # Planifier la prochaine exécution
            self._schedule_next_run(task)
            
            self.logger.info(f"Tâche '{task.name}' terminée avec succès")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('task_completed', {
                    'task_id': task.id,
                    'task_name': task.name,
                    'result': result,
                    'timestamp': time.time()
                })
            
        except Exception as e:
            self.logger.error(f"Erreur exécution tâche {task.name}: {e}")
            
            # Gérer les tentatives
            task.retry_count += 1
            task.error_message = str(e)
            
            if task.retry_count < task.max_retries:
                # Réessayer plus tard
                task.status = TaskStatus.PENDING
                task.next_run = datetime.now() + timedelta(minutes=5)  # Attendre 5 minutes
                self.logger.info(f"Tâche '{task.name}' sera réessayée dans 5 minutes")
            else:
                # Abandonner
                task.status = TaskStatus.FAILED
                self.stats['tasks_failed'] += 1
                self.logger.error(f"Tâche '{task.name}' abandonnée après {task.max_retries} tentatives")
            
            # Émettre un événement d'erreur
            if self.event_bus:
                self.event_bus.emit('task_failed', {
                    'task_id': task.id,
                    'task_name': task.name,
                    'error': str(e),
                    'retry_count': task.retry_count,
                    'timestamp': time.time()
                })
        
        finally:
            # Nettoyer
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    def _schedule_next_run(self, task: ScheduledTask) -> None:
        """Planifie la prochaine exécution d'une tâche"""
        try:
            if task.task_type == TaskType.ONCE:
                # Tâche unique, pas de prochaine exécution
                task.next_run = None
                return
            
            current_time = datetime.now()
            
            if task.task_type == TaskType.INTERVAL:
                # Tâche par intervalle
                if task.interval_seconds:
                    task.next_run = current_time + timedelta(seconds=task.interval_seconds)
                else:
                    task.next_run = None
            
            elif task.task_type == TaskType.DAILY:
                # Tâche quotidienne
                next_run = current_time.replace(
                    hour=task.hour or 0,
                    minute=task.minute or 0,
                    second=0,
                    microsecond=0
                )
                
                if next_run <= current_time:
                    next_run += timedelta(days=1)
                
                task.next_run = next_run
            
            elif task.task_type == TaskType.WEEKLY:
                # Tâche hebdomadaire
                days_ahead = (task.weekday or 0) - current_time.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                
                next_run = current_time + timedelta(days=days_ahead)
                next_run = next_run.replace(
                    hour=task.hour or 0,
                    minute=task.minute or 0,
                    second=0,
                    microsecond=0
                )
                
                task.next_run = next_run
            
            elif task.task_type == TaskType.MONTHLY:
                # Tâche mensuelle
                next_month = current_time.replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)
                
                next_run = next_month.replace(
                    day=task.day or 1,
                    hour=task.hour or 0,
                    minute=task.minute or 0,
                    second=0,
                    microsecond=0
                )
                
                task.next_run = next_run
            
            # Réactiver la tâche
            task.status = TaskStatus.PENDING
            
        except Exception as e:
            self.logger.error(f"Erreur planification prochaine exécution: {e}")
            self.stats['errors'] += 1
    
    def _cleanup_completed_tasks(self) -> None:
        """Nettoie les tâches terminées"""
        try:
            # Supprimer les tâches uniques terminées
            tasks_to_remove = []
            for task_id, task in self.tasks.items():
                if (task.task_type == TaskType.ONCE and 
                    task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
                self.logger.debug(f"Tâche unique supprimée: {task_id}")
                
        except Exception as e:
            self.logger.error(f"Erreur nettoyage tâches terminées: {e}")
            self.stats['errors'] += 1
    
    def add_task(self, name: str, task_type: TaskType, callback: Callable, 
                 args: tuple = (), kwargs: dict = None, **task_config) -> str:
        """
        Ajoute une tâche planifiée
        
        Args:
            name: Nom de la tâche
            task_type: Type de tâche
            callback: Fonction à exécuter
            args: Arguments positionnels
            kwargs: Arguments nommés
            **task_config: Configuration spécifique au type
            
        Returns:
            ID de la tâche créée
        """
        try:
            task_id = f"task_{self.task_counter}"
            self.task_counter += 1
            
            # Créer la tâche
            task = ScheduledTask(
                id=task_id,
                name=name,
                task_type=task_type,
                callback=callback,
                args=args,
                kwargs=kwargs or {},
                **task_config
            )
            
            # Planifier la première exécution
            self._schedule_next_run(task)
            
            # Ajouter à la liste
            self.tasks[task_id] = task
            self.stats['tasks_created'] += 1
            
            self.logger.info(f"Tâche '{name}' ajoutée (ID: {task_id})")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Erreur ajout tâche {name}: {e}")
            self.stats['errors'] += 1
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Annule une tâche
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            True si la tâche est annulée, False sinon
        """
        try:
            if task_id not in self.tasks:
                self.logger.warning(f"Tâche {task_id} non trouvée")
                return False
            
            task = self.tasks[task_id]
            
            if task.status == TaskStatus.RUNNING:
                # La tâche est en cours, on ne peut pas l'annuler directement
                self.logger.warning(f"Tâche {task.name} en cours d'exécution, annulation différée")
                task.status = TaskStatus.CANCELLED
            else:
                # Annuler la tâche
                task.status = TaskStatus.CANCELLED
                task.next_run = None
            
            self.stats['tasks_cancelled'] += 1
            self.logger.info(f"Tâche '{task.name}' annulée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur annulation tâche {task_id}: {e}")
            self.stats['errors'] += 1
            return False
    
    def enable_task(self, task_id: str) -> bool:
        """
        Active une tâche
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            True si la tâche est activée, False sinon
        """
        try:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.enabled = True
            
            # Replanifier si nécessaire
            if task.status == TaskStatus.PENDING and not task.next_run:
                self._schedule_next_run(task)
            
            self.logger.info(f"Tâche '{task.name}' activée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur activation tâche {task_id}: {e}")
            return False
    
    def disable_task(self, task_id: str) -> bool:
        """
        Désactive une tâche
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            True si la tâche est désactivée, False sinon
        """
        try:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.enabled = False
            
            self.logger.info(f"Tâche '{task.name}' désactivée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur désactivation tâche {task_id}: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le statut d'une tâche
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            Dictionnaire contenant le statut ou None
        """
        try:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            return {
                'id': task.id,
                'name': task.name,
                'type': task.task_type.value,
                'status': task.status.value,
                'enabled': task.enabled,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'retry_count': task.retry_count,
                'max_retries': task.max_retries,
                'error_message': task.error_message
            }
            
        except Exception as e:
            self.logger.error(f"Erreur récupération statut tâche {task_id}: {e}")
            return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les tâches
        
        Returns:
            Liste des statuts de toutes les tâches
        """
        try:
            return [self.get_task_status(task_id) for task_id in self.tasks.keys()]
            
        except Exception as e:
            self.logger.error(f"Erreur récupération toutes les tâches: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service de planification
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'service': 'scheduler',
            'is_running': self.is_running,
            'check_interval': self.check_interval,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'total_tasks': len(self.tasks),
            'running_tasks': len(self.running_tasks),
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie le service de planification"""
        try:
            # Arrêter le service
            self.stop()
            
            # Nettoyer toutes les tâches
            self.tasks.clear()
            self.running_tasks.clear()
            
            self.logger.info("Service de planification nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service planification: {e}")
            self.stats['errors'] += 1
