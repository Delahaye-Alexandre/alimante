"""
Driver de base pour tous les composants matériels
Fournit les fonctionnalités communes et l'interface standard
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

class DriverState(Enum):
    """États possibles d'un driver"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"

class DriverError(Exception):
    """Exception spécifique aux drivers"""
    pass

@dataclass
class DriverConfig:
    """Configuration de base pour un driver"""
    name: str
    enabled: bool = True
    timeout: float = 5.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    calibration: Optional[Dict[str, Any]] = None

class BaseDriver(ABC):
    """
    Classe de base pour tous les drivers
    Fournit les fonctionnalités communes et l'interface standard
    """
    
    def __init__(self, config: DriverConfig, gpio_config: Optional[Dict] = None):
        """
        Initialise le driver de base
        
        Args:
            config: Configuration du driver
            gpio_config: Configuration GPIO (optionnel)
        """
        self.config = config
        self.gpio_config = gpio_config or {}
        self.state = DriverState.UNINITIALIZED
        self.logger = logging.getLogger(f"alimante.drivers.{config.name}")
        self.last_error = None
        self.error_count = 0
        self.last_update = None
        
        # Statistiques
        self.read_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialise le driver
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        pass
    
    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """
        Lit les données du composant
        
        Returns:
            Dictionnaire contenant les données lues
        """
        pass
    
    @abstractmethod
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Écrit des données vers le composant
        
        Args:
            data: Données à écrire
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        pass
    
    def cleanup(self) -> None:
        """
        Nettoie les ressources du driver
        """
        self.state = DriverState.DISABLED
        self.logger.info(f"Driver {self.config.name} nettoyé")
    
    def is_ready(self) -> bool:
        """
        Vérifie si le driver est prêt
        
        Returns:
            True si le driver est prêt, False sinon
        """
        return self.state == DriverState.READY
    
    def is_enabled(self) -> bool:
        """
        Vérifie si le driver est activé
        
        Returns:
            True si le driver est activé, False sinon
        """
        return self.config.enabled and self.state != DriverState.DISABLED
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du driver
        
        Returns:
            Dictionnaire contenant le statut
        """
        uptime = time.time() - self.start_time
        
        return {
            "name": self.config.name,
            "state": self.state.value,
            "enabled": self.is_enabled(),
            "uptime_seconds": uptime,
            "read_count": self.read_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_update": self.last_update,
            "error_rate": self.error_count / max(self.read_count, 1)
        }
    
    def _handle_error(self, error: Exception, operation: str) -> None:
        """
        Gère les erreurs du driver
        
        Args:
            error: Exception survenue
            operation: Nom de l'opération qui a échoué
        """
        self.error_count += 1
        self.last_error = str(error)
        self.state = DriverState.ERROR
        
        self.logger.error(f"Erreur dans {operation} pour {self.config.name}: {error}")
        
        # Si trop d'erreurs, désactiver le driver
        if self.error_count > 10:
            self.logger.critical(f"Trop d'erreurs pour {self.config.name}, désactivation")
            self.state = DriverState.DISABLED
    
    def _retry_operation(self, operation, *args, **kwargs):
        """
        Exécute une opération avec retry
        
        Args:
            operation: Fonction à exécuter
            *args: Arguments de la fonction
            **kwargs: Arguments nommés de la fonction
            
        Returns:
            Résultat de l'opération ou None si échec
        """
        for attempt in range(self.config.retry_attempts):
            try:
                result = operation(*args, **kwargs)
                self.error_count = 0  # Reset error count on success
                return result
            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    self.logger.warning(f"Tentative {attempt + 1} échouée pour {self.config.name}: {e}")
                    time.sleep(self.config.retry_delay)
                else:
                    self._handle_error(e, operation.__name__)
                    return None
    
    def safe_read(self) -> Optional[Dict[str, Any]]:
        """
        Lecture sécurisée avec retry
        
        Returns:
            Données lues ou None si échec
        """
        if not self.is_enabled():
            return None
            
        result = self._retry_operation(self.read)
        if result:
            self.read_count += 1
            self.last_update = time.time()
            
        return result
    
    def safe_write(self, data: Dict[str, Any]) -> bool:
        """
        Écriture sécurisée avec retry
        
        Args:
            data: Données à écrire
            
        Returns:
            True si succès, False sinon
        """
        if not self.is_enabled():
            return False
            
        return self._retry_operation(self.write, data) is not None
    
    def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """
        Calibre le driver
        
        Args:
            calibration_data: Données de calibration
            
        Returns:
            True si la calibration réussit, False sinon
        """
        try:
            if self.config.calibration:
                self.config.calibration.update(calibration_data)
            else:
                self.config.calibration = calibration_data
                
            self.logger.info(f"Calibration mise à jour pour {self.config.name}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur de calibration pour {self.config.name}: {e}")
            return False
    
    def reset(self) -> bool:
        """
        Remet à zéro le driver
        
        Returns:
            True si le reset réussit, False sinon
        """
        try:
            self.state = DriverState.UNINITIALIZED
            self.error_count = 0
            self.last_error = None
            
            # Réinitialiser le driver
            success = self.initialize()
            if success:
                self.logger.info(f"Reset réussi pour {self.config.name}")
            else:
                self.logger.error(f"Échec du reset pour {self.config.name}")
                
            return success
        except Exception as e:
            self.logger.error(f"Erreur lors du reset de {self.config.name}: {e}")
            return False
