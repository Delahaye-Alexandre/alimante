from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.utils.gpio_manager import GPIOManager
from src.utils.logging_config import get_logger

class BaseController(ABC):
    """Classe de base pour tous les contrôleurs Alimante"""
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        self.gpio_manager = gpio_manager
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.initialized = False
        self.error_count = 0
        self.last_error = None
        
    @abstractmethod
    def check_status(self) -> bool:
        """Vérifie le statut du contrôleur"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut complet du contrôleur"""
        pass
    
    @abstractmethod
    def control(self) -> bool:
        """Méthode principale de contrôle"""
        pass
    
    def is_initialized(self) -> bool:
        """Vérifie si le contrôleur est initialisé"""
        return self.initialized
    
    def get_error_count(self) -> int:
        """Retourne le nombre d'erreurs"""
        return self.error_count
    
    def get_last_error(self) -> Optional[str]:
        """Retourne la dernière erreur"""
        return self.last_error
    
    def record_error(self, error: Exception) -> None:
        """Enregistre une erreur"""
        self.error_count += 1
        self.last_error = str(error)
        self.logger.error(f"Erreur enregistrée: {error}")
    
    def reset_errors(self) -> None:
        """Réinitialise le compteur d'erreurs"""
        self.error_count = 0
        self.last_error = None
        self.logger.info("Compteur d'erreurs réinitialisé")