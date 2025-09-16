"""
Bus d'événements Alimante
Système de communication entre les composants
"""

import logging
import threading
from typing import Dict, Any, Callable, List, Optional
from collections import defaultdict
import time

class EventBus:
    """
    Bus d'événements pour la communication entre composants
    """
    
    def __init__(self):
        """Initialise le bus d'événements"""
        self.logger = logging.getLogger(__name__)
        
        # Gestionnaires d'événements
        self.handlers = defaultdict(list)
        
        # Verrou pour la thread-safety
        self.lock = threading.RLock()
        
        # Statistiques
        self.stats = {
            'events_emitted': 0,
            'handlers_registered': 0,
            'handlers_called': 0,
            'errors_count': 0,
            'start_time': time.time()
        }
        
    def on(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """
        Enregistre un gestionnaire d'événement
        
        Args:
            event_type: Type d'événement
            handler: Fonction de gestion
        """
        try:
            with self.lock:
                self.handlers[event_type].append(handler)
                self.stats['handlers_registered'] += 1
                self.logger.debug(f"Gestionnaire enregistré pour {event_type}")
                
        except Exception as e:
            self.logger.error(f"Erreur enregistrement gestionnaire {event_type}: {e}")
            self.stats['errors_count'] += 1
    
    def off(self, event_type: str, handler: Optional[Callable[[Any], None]] = None) -> None:
        """
        Désenregistre un gestionnaire d'événement
        
        Args:
            event_type: Type d'événement
            handler: Fonction de gestion (si None, retire tous les gestionnaires)
        """
        try:
            with self.lock:
                if handler is None:
                    # Retirer tous les gestionnaires pour ce type d'événement
                    if event_type in self.handlers:
                        del self.handlers[event_type]
                        self.logger.debug(f"Tous les gestionnaires retirés pour {event_type}")
                else:
                    # Retirer le gestionnaire spécifique
                    if event_type in self.handlers:
                        if handler in self.handlers[event_type]:
                            self.handlers[event_type].remove(handler)
                            self.logger.debug(f"Gestionnaire retiré pour {event_type}")
                
        except Exception as e:
            self.logger.error(f"Erreur désenregistrement gestionnaire {event_type}: {e}")
            self.stats['errors_count'] += 1
    
    def emit(self, event_type: str, data: Any = None) -> None:
        """
        Émet un événement
        
        Args:
            event_type: Type d'événement
            data: Données de l'événement
        """
        try:
            with self.lock:
                self.stats['events_emitted'] += 1
                
                # Notifier tous les gestionnaires
                if event_type in self.handlers:
                    for handler in self.handlers[event_type]:
                        try:
                            handler(data)
                            self.stats['handlers_called'] += 1
                        except Exception as e:
                            self.logger.error(f"Erreur gestionnaire {event_type}: {e}")
                            self.stats['errors_count'] += 1
                
                self.logger.debug(f"Événement émis: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Erreur émission événement {event_type}: {e}")
            self.stats['errors_count'] += 1
    
    def once(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """
        Enregistre un gestionnaire d'événement qui ne sera appelé qu'une fois
        
        Args:
            event_type: Type d'événement
            handler: Fonction de gestion
        """
        try:
            def once_handler(data):
                handler(data)
                self.off(event_type, once_handler)
            
            self.on(event_type, once_handler)
            
        except Exception as e:
            self.logger.error(f"Erreur enregistrement gestionnaire unique {event_type}: {e}")
            self.stats['errors_count'] += 1
    
    def wait_for(self, event_type: str, timeout: Optional[float] = None) -> Any:
        """
        Attend un événement spécifique
        
        Args:
            event_type: Type d'événement à attendre
            timeout: Timeout en secondes (None = infini)
            
        Returns:
            Données de l'événement ou None si timeout
        """
        try:
            event_data = None
            event_received = threading.Event()
            
            def event_handler(data):
                nonlocal event_data
                event_data = data
                event_received.set()
            
            self.once(event_type, event_handler)
            
            if event_received.wait(timeout):
                return event_data
            else:
                self.logger.warning(f"Timeout en attente de l'événement {event_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur attente événement {event_type}: {e}")
            self.stats['errors_count'] += 1
            return None
    
    def get_handlers_count(self, event_type: Optional[str] = None) -> int:
        """
        Retourne le nombre de gestionnaires enregistrés
        
        Args:
            event_type: Type d'événement (None = tous)
            
        Returns:
            Nombre de gestionnaires
        """
        try:
            with self.lock:
                if event_type is None:
                    return sum(len(handlers) for handlers in self.handlers.values())
                else:
                    return len(self.handlers.get(event_type, []))
                    
        except Exception as e:
            self.logger.error(f"Erreur comptage gestionnaires: {e}")
            return 0
    
    def get_registered_events(self) -> List[str]:
        """
        Retourne la liste des types d'événements enregistrés
        
        Returns:
            Liste des types d'événements
        """
        try:
            with self.lock:
                return list(self.handlers.keys())
                
        except Exception as e:
            self.logger.error(f"Erreur récupération événements: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du bus d'événements
        
        Returns:
            Dictionnaire des statistiques
        """
        try:
            with self.lock:
                return {
                    'events_emitted': self.stats['events_emitted'],
                    'handlers_registered': self.stats['handlers_registered'],
                    'handlers_called': self.stats['handlers_called'],
                    'errors_count': self.stats['errors_count'],
                    'uptime': time.time() - self.stats['start_time'],
                    'registered_events': len(self.handlers),
                    'total_handlers': self.get_handlers_count()
                }
                
        except Exception as e:
            self.logger.error(f"Erreur récupération statistiques: {e}")
            return {}
    
    def clear(self) -> None:
        """Efface tous les gestionnaires d'événements"""
        try:
            with self.lock:
                self.handlers.clear()
                self.logger.info("Tous les gestionnaires d'événements effacés")
                
        except Exception as e:
            self.logger.error(f"Erreur effacement gestionnaires: {e}")
            self.stats['errors_count'] += 1

