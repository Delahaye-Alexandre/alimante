"""
Contrôleur de base pour Alimante
Fournit les fonctionnalités communes et l'interface standard pour tous les contrôleurs
"""

import logging
import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

class ControllerState(Enum):
    """États possibles d'un contrôleur"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"

class ControllerError(Exception):
    """Exception spécifique aux contrôleurs"""
    pass

@dataclass
class ControllerConfig:
    """Configuration de base pour un contrôleur"""
    name: str
    enabled: bool = True
    update_interval: float = 1.0  # Intervalle de mise à jour en secondes
    max_retries: int = 3
    retry_delay: float = 1.0
    auto_start: bool = True
    log_level: str = "INFO"

class BaseController(ABC):
    """
    Classe de base pour tous les contrôleurs
    Fournit les fonctionnalités communes et l'interface standard
    """
    
    def __init__(self, config: ControllerConfig, event_bus: Optional[Any] = None):
        """
        Initialise le contrôleur de base
        
        Args:
            config: Configuration du contrôleur
            event_bus: Bus d'événements pour la communication
        """
        self.config = config
        self.event_bus = event_bus
        self.state = ControllerState.UNINITIALIZED
        self.logger = logging.getLogger(f"alimante.controllers.{config.name}")
        
        # Gestion des threads
        self._thread = None
        self._stop_event = threading.Event()
        self._running = False
        
        # Statistiques
        self.start_time = None
        self.update_count = 0
        self.error_count = 0
        self.last_error = None
        self.last_update = None
        
        # Callbacks
        self._state_change_callbacks: List[Callable[[ControllerState], None]] = []
        self._error_callbacks: List[Callable[[Exception], None]] = []
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialise le contrôleur
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        pass
    
    @abstractmethod
    def update(self) -> bool:
        """
        Met à jour le contrôleur (appelé périodiquement)
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Nettoie les ressources du contrôleur
        """
        pass
    
    def start(self) -> bool:
        """
        Démarre le contrôleur
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.config.enabled:
                self.logger.info(f"Contrôleur {self.config.name} désactivé")
                return True
            
            if self.state == ControllerState.RUNNING:
                self.logger.warning(f"Contrôleur {self.config.name} déjà en cours d'exécution")
                return True
            
            if not self.initialize():
                self.logger.error(f"Échec d'initialisation du contrôleur {self.config.name}")
                return False
            
            self._stop_event.clear()
            self._running = True
            self.start_time = time.time()
            
            # Démarrer le thread de mise à jour
            self._thread = threading.Thread(target=self._update_loop, daemon=True)
            self._thread.start()
            
            self._set_state(ControllerState.RUNNING)
            self.logger.info(f"Contrôleur {self.config.name} démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage contrôleur {self.config.name}: {e}")
            self._set_state(ControllerState.ERROR)
            return False
    
    def stop(self) -> bool:
        """
        Arrête le contrôleur
        
        Returns:
            True si l'arrêt réussit, False sinon
        """
        try:
            if not self._running:
                self.logger.warning(f"Contrôleur {self.config.name} déjà arrêté")
                return True
            
            self._running = False
            self._stop_event.set()
            
            # Attendre que le thread se termine
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)
            
            self.cleanup()
            self._set_state(ControllerState.STOPPED)
            self.logger.info(f"Contrôleur {self.config.name} arrêté")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt contrôleur {self.config.name}: {e}")
            return False
    
    def pause(self) -> bool:
        """
        Met en pause le contrôleur
        
        Returns:
            True si la pause réussit, False sinon
        """
        try:
            if self.state != ControllerState.RUNNING:
                self.logger.warning(f"Contrôleur {self.config.name} pas en cours d'exécution")
                return False
            
            self._set_state(ControllerState.PAUSED)
            self.logger.info(f"Contrôleur {self.config.name} mis en pause")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur pause contrôleur {self.config.name}: {e}")
            return False
    
    def resume(self) -> bool:
        """
        Reprend le contrôleur
        
        Returns:
            True si la reprise réussit, False sinon
        """
        try:
            if self.state != ControllerState.PAUSED:
                self.logger.warning(f"Contrôleur {self.config.name} pas en pause")
                return False
            
            self._set_state(ControllerState.RUNNING)
            self.logger.info(f"Contrôleur {self.config.name} repris")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur reprise contrôleur {self.config.name}: {e}")
            return False
    
    def _update_loop(self) -> None:
        """Boucle de mise à jour du contrôleur"""
        while self._running and not self._stop_event.is_set():
            try:
                if self.state == ControllerState.RUNNING:
                    success = self.update()
                    if success:
                        self.update_count += 1
                        self.last_update = time.time()
                    else:
                        self.error_count += 1
                        self.logger.warning(f"Échec mise à jour contrôleur {self.config.name}")
                
                # Attendre l'intervalle de mise à jour
                self._stop_event.wait(self.config.update_interval)
                
            except Exception as e:
                self.error_count += 1
                self.last_error = str(e)
                self.logger.error(f"Erreur dans la boucle de mise à jour: {e}")
                self._notify_error(e)
                
                # Attendre avant de réessayer
                self._stop_event.wait(self.config.retry_delay)
    
    def _set_state(self, new_state: ControllerState) -> None:
        """Définit l'état du contrôleur et notifie les callbacks"""
        old_state = self.state
        self.state = new_state
        
        if old_state != new_state:
            self.logger.debug(f"État {self.config.name}: {old_state.value} -> {new_state.value}")
            self._notify_state_change(new_state)
    
    def _notify_state_change(self, new_state: ControllerState) -> None:
        """Notifie les callbacks de changement d'état"""
        for callback in self._state_change_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                self.logger.error(f"Erreur callback changement d'état: {e}")
    
    def _notify_error(self, error: Exception) -> None:
        """Notifie les callbacks d'erreur"""
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                self.logger.error(f"Erreur callback erreur: {e}")
    
    def add_state_change_callback(self, callback: Callable[[ControllerState], None]) -> None:
        """Ajoute un callback de changement d'état"""
        self._state_change_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """Ajoute un callback d'erreur"""
        self._error_callbacks.append(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du contrôleur
        
        Returns:
            Dictionnaire contenant le statut
        """
        uptime = 0
        if self.start_time:
            uptime = time.time() - self.start_time
        
        return {
            "name": self.config.name,
            "state": self.state.value,
            "enabled": self.config.enabled,
            "running": self._running,
            "uptime_seconds": uptime,
            "update_count": self.update_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_update": self.last_update,
            "update_interval": self.config.update_interval,
            "error_rate": self.error_count / max(self.update_count, 1)
        }
    
    def is_running(self) -> bool:
        """Vérifie si le contrôleur est en cours d'exécution"""
        return self._running and self.state == ControllerState.RUNNING
    
    def is_ready(self) -> bool:
        """Vérifie si le contrôleur est prêt"""
        return self.state in [ControllerState.READY, ControllerState.RUNNING, ControllerState.PAUSED]
    
    def get_uptime(self) -> float:
        """Retourne le temps de fonctionnement en secondes"""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0
    
    def reset_counters(self) -> None:
        """Remet à zéro les compteurs"""
        self.update_count = 0
        self.error_count = 0
        self.last_error = None
        self.logger.info(f"Compteurs du contrôleur {self.config.name} remis à zéro")

