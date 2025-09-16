"""
Driver pour les relais (chauffage, humidificateur, etc.)
"""

import time
import logging
from typing import Dict, Any, Optional
from .base_driver import BaseDriver, DriverConfig, DriverState

try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
except ImportError:
    # Mode simulation pour Windows
    RASPBERRY_PI = False
    GPIO = None

class RelayDriver(BaseDriver):
    """
    Driver pour contrôler les relais
    """
    
    def __init__(self, config: DriverConfig, gpio_pin: int, active_high: bool = True):
        """
        Initialise le driver de relais
        
        Args:
            config: Configuration du driver
            gpio_pin: Pin GPIO connecté au relais
            active_high: True si le relais s'active sur niveau haut
        """
        super().__init__(config)
        self.gpio_pin = gpio_pin
        self.active_high = active_high
        self.current_state = False
        self.last_switch_time = None
        self.switch_count = 0
        
        # Configuration de sécurité
        self.min_cycle_time = 0.1  # Temps minimum entre les commutations (100ms)
        self.max_cycle_time = 3600  # Temps maximum de fonctionnement continu
        self.cycle_start_time = None
        
    def initialize(self) -> bool:
        """
        Initialise le driver de relais
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.config.enabled:
                self.state = DriverState.DISABLED
                return True
                
            if not RASPBERRY_PI:
                self.logger.error("Relais nécessite un Raspberry Pi - pas de simulation")
                self.state = DriverState.ERROR
                return False
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            
            # État initial : relais fermé
            self._set_relay_state(False)
            
            self.state = DriverState.READY
            self.logger.info(f"Relais initialisé sur pin {self.gpio_pin} (active_high={self.active_high})")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation relais: {e}")
            self.state = DriverState.ERROR
            return False
    
    def read(self) -> Dict[str, Any]:
        """
        Lit l'état actuel du relais
        
        Returns:
            Dictionnaire contenant state, switch_count, uptime
        """
        if not self.is_ready():
            raise DriverError("Relais non initialisé")
        
        uptime = 0
        if self.cycle_start_time and self.current_state:
            uptime = time.time() - self.cycle_start_time
        
        return {
            "state": self.current_state,
            "switch_count": self.switch_count,
            "uptime_seconds": uptime,
            "timestamp": time.time(),
            "sensor": "relay",
            "unit": "boolean"
        }
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Écrit des données vers le relais
        
        Args:
            data: Données contenant state, duration, etc.
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        if not self.is_ready():
            raise DriverError("Relais non initialisé")
        
        try:
            state = data.get("state", False)
            duration = data.get("duration", None)  # Durée en secondes
            force = data.get("force", False)  # Forcer la commutation
            
            # Vérifier le délai minimum entre les commutations
            if not force and not self._can_switch():
                self.logger.warning("Délai minimum entre commutations non respecté")
                return False
            
            # Vérifier la durée de fonctionnement continu
            if self.current_state and not force and self._is_max_cycle_reached():
                self.logger.warning("Durée maximale de fonctionnement atteinte")
                return False
            
            # Changer l'état du relais
            if self._set_relay_state(state):
                if duration:
                    # Programmer l'arrêt automatique
                    self._schedule_turn_off(duration)
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur écriture relais: {e}")
            return False
    
    def _set_relay_state(self, state: bool) -> bool:
        """
        Définit l'état du relais
        
        Args:
            state: True pour activer, False pour désactiver
            
        Returns:
            True si succès, False sinon
        """
        try:
            if RASPBERRY_PI:
                # Inverser la logique si active_low
                gpio_state = state if self.active_high else not state
                GPIO.output(self.gpio_pin, gpio_state)
            else:
                # Mode simulation
                pass
            
            # Mettre à jour l'état
            old_state = self.current_state
            self.current_state = state
            
            # Compter les commutations
            if old_state != state:
                self.switch_count += 1
                self.last_switch_time = time.time()
                
                # Gérer le temps de cycle
                if state:
                    self.cycle_start_time = time.time()
                else:
                    self.cycle_start_time = None
                
                action = "activé" if state else "désactivé"
                self.logger.info(f"Relais pin {self.gpio_pin} {action}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur changement état relais: {e}")
            return False
    
    def _can_switch(self) -> bool:
        """
        Vérifie si le relais peut être commuté
        
        Returns:
            True si la commutation est autorisée, False sinon
        """
        if not self.last_switch_time:
            return True
        
        time_since_last_switch = time.time() - self.last_switch_time
        return time_since_last_switch >= self.min_cycle_time
    
    def _is_max_cycle_reached(self) -> bool:
        """
        Vérifie si la durée maximale de fonctionnement est atteinte
        
        Returns:
            True si la durée max est atteinte, False sinon
        """
        if not self.cycle_start_time or not self.current_state:
            return False
        
        uptime = time.time() - self.cycle_start_time
        return uptime >= self.max_cycle_time
    
    def _schedule_turn_off(self, duration: float) -> None:
        """
        Programme l'arrêt automatique du relais
        
        Args:
            duration: Durée en secondes
        """
        def turn_off():
            time.sleep(duration)
            if self.current_state:
                self._set_relay_state(False)
                self.logger.info(f"Relais pin {self.gpio_pin} arrêté automatiquement après {duration}s")
        
        import threading
        thread = threading.Thread(target=turn_off, daemon=True)
        thread.start()
    
    def turn_on(self) -> bool:
        """
        Active le relais
        
        Returns:
            True si succès, False sinon
        """
        return self.write({"state": True})
    
    def turn_off(self) -> bool:
        """
        Désactive le relais
        
        Returns:
            True si succès, False sinon
        """
        return self.write({"state": False})
    
    def toggle(self) -> bool:
        """
        Inverse l'état du relais
        
        Returns:
            True si succès, False sinon
        """
        return self.write({"state": not self.current_state})
    
    def is_on(self) -> bool:
        """
        Vérifie si le relais est activé
        
        Returns:
            True si activé, False sinon
        """
        return self.current_state
    
    def get_uptime(self) -> float:
        """
        Retourne le temps de fonctionnement actuel
        
        Returns:
            Temps en secondes
        """
        if not self.current_state or not self.cycle_start_time:
            return 0.0
        
        return time.time() - self.cycle_start_time
    
    def get_switch_count(self) -> int:
        """
        Retourne le nombre de commutations
        
        Returns:
            Nombre de commutations
        """
        return self.switch_count
    
    def set_cycle_limits(self, min_time: float, max_time: float) -> bool:
        """
        Définit les limites de cycle
        
        Args:
            min_time: Temps minimum entre commutations (s)
            max_time: Temps maximum de fonctionnement (s)
            
        Returns:
            True si succès, False sinon
        """
        try:
            self.min_cycle_time = max(0.1, min_time)
            self.max_cycle_time = max(1.0, max_time)
            
            self.logger.info(f"Limites de cycle définies: min={self.min_cycle_time}s, max={self.max_cycle_time}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition limites cycle: {e}")
            return False
    
    def reset_counters(self) -> bool:
        """
        Remet à zéro les compteurs
        
        Returns:
            True si succès, False sinon
        """
        try:
            self.switch_count = 0
            self.cycle_start_time = None
            self.last_switch_time = None
            
            self.logger.info("Compteurs relais remis à zéro")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur reset compteurs: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre le driver de relais
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.is_ready():
                self.logger.error("Relais non initialisé")
                return False
            
            self.logger.info(f"Driver relais {self.config.name} démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage relais: {e}")
            return False
    
    def stop(self) -> None:
        """
        Arrête le driver de relais
        """
        try:
            # Éteindre le relais
            self._set_relay_state(False)
            self.logger.info(f"Driver relais {self.config.name} arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt relais: {e}")
    
    def set_state(self, state: bool) -> bool:
        """
        Définit l'état du relais (méthode de compatibilité)
        
        Args:
            state: True pour activer, False pour désactiver
            
        Returns:
            True si succès, False sinon
        """
        try:
            return self.write({"state": state})
            
        except Exception as e:
            self.logger.error(f"Erreur set_state relais: {e}")
            return False
    
    def is_running(self) -> bool:
        """
        Vérifie si le driver est en cours d'exécution
        
        Returns:
            True si en cours d'exécution, False sinon
        """
        return self.is_ready()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du driver
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'name': self.config.name,
            'enabled': self.config.enabled,
            'state': self.state.value,
            'is_ready': self.is_ready(),
            'is_running': self.is_running(),
            'current_state': self.current_state,
            'switch_count': self.switch_count,
            'uptime': self.get_uptime()
        }
    
    def cleanup(self) -> None:
        """
        Nettoie les ressources du relais
        """
        if self.current_state:
            self._set_relay_state(False)
        
        if RASPBERRY_PI and self.gpio_pin:
            try:
                GPIO.setup(self.gpio_pin, GPIO.IN)
            except:
                pass
        
        super().cleanup()
