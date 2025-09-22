"""
Contrôleur d'humidification Alimante
Gère le contrôle de l'humidification via relais
"""

import time
import logging
from typing import Dict, Any, Optional
from ..base_controller import BaseController, ControllerConfig, ControllerState, ControllerError
from ..drivers.relay_driver import RelayDriver, DriverConfig

class HumidifierController(BaseController):
    """
    Contrôleur du système d'humidification
    """
    
    def __init__(self, config: ControllerConfig, gpio_config: Dict[str, Any], 
                 event_bus: Optional[Any] = None):
        """
        Initialise le contrôleur d'humidification
        
        Args:
            config: Configuration du contrôleur
            gpio_config: Configuration GPIO
            event_bus: Bus d'événements
        """
        super().__init__(config, event_bus)
        self.gpio_config = gpio_config
        
        # Drivers de relais pour l'humidification
        self.humidifier_relay = None
        self.mister_relay = None
        
        # État de l'humidification
        self.is_humidifying = False
        self.target_humidity = None
        self.current_humidity = None
        self.hysteresis = 5.0  # Hystérésis en pourcentage
        
        # Configuration de sécurité
        self.max_humidity = 95.0
        self.min_cycle_time = 300  # 5 minutes minimum entre les cycles
        self.max_cycle_duration = 1800  # 30 minutes maximum par cycle
        self.safety_enabled = True
        
        # Statistiques
        self.humidifying_time = 0
        self.last_humidifying_start = None
        self.last_cycle_end = None
        self.cycle_count = 0
        
    def initialize(self) -> bool:
        """
        Initialise le contrôleur d'humidification
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du contrôleur d'humidification...")
            
            # Configuration du driver de relais principal
            humidifier_config = DriverConfig(
                name="humidifier_relay",
                pin=self.gpio_config.get('humidifier_pin', 5),
                active_high=True,
                initial_state=False
            )
            
            # Configuration du driver de relais brumisateur
            mister_config = DriverConfig(
                name="mister_relay",
                pin=self.gpio_config.get('mister_pin', 6),
                active_high=True,
                initial_state=False
            )
            
            # Initialiser les drivers de relais
            self.humidifier_relay = RelayDriver(humidifier_config)
            self.mister_relay = RelayDriver(mister_config)
            
            if not self.humidifier_relay.initialize():
                self.logger.error("Échec initialisation driver relais humidificateur")
                return False
            
            if not self.mister_relay.initialize():
                self.logger.error("Échec initialisation driver relais brumisateur")
                return False
            
            # Charger la configuration de sécurité
            self.max_humidity = self.config.get('max_humidity', 95.0)
            self.hysteresis = self.config.get('hysteresis', 5.0)
            self.min_cycle_time = self.config.get('min_cycle_time', 300)
            self.max_cycle_duration = self.config.get('max_cycle_duration', 1800)
            self.safety_enabled = self.config.get('safety_enabled', True)
            
            self.state = ControllerState.READY
            self.logger.info("Contrôleur d'humidification initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation contrôleur humidification: {e}")
            self.state = ControllerState.ERROR
            return False
    
    def update(self) -> bool:
        """
        Met à jour le contrôleur d'humidification
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            if self.state != ControllerState.RUNNING:
                return True
            
            # Mettre à jour les statistiques d'humidification
            if self.is_humidifying and self.last_humidifying_start:
                self.humidifying_time = time.time() - self.last_humidifying_start
                
                # Vérifier la durée maximale du cycle
                if self.humidifying_time > self.max_cycle_duration:
                    self._stop_humidifying()
                    self.logger.warning(f"Arrêt humidification: durée maximale atteinte ({self.max_cycle_duration}s)")
            
            # Vérifier la sécurité
            if self.safety_enabled and self.current_humidity:
                if self.current_humidity > self.max_humidity:
                    self._emergency_stop()
                    self.logger.warning(f"Arrêt d'urgence humidification: humidité {self.current_humidity}% > {self.max_humidity}%")
                    return False
            
            self.update_count += 1
            self.last_update = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour contrôleur humidification: {e}")
            self.error_count += 1
            self.last_error = e
            return False
    
    def set_humidity(self, humidity: float) -> bool:
        """
        Définit l'humidité cible
        
        Args:
            humidity: Humidité cible en pourcentage
            
        Returns:
            True si la commande est acceptée, False sinon
        """
        try:
            if not self.safety_enabled or humidity <= self.max_humidity:
                self.target_humidity = humidity
                self.logger.info(f"Humidité cible définie: {humidity}%")
                return True
            else:
                self.logger.warning(f"Humidité refusée: {humidity}% > {self.max_humidity}%")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur définition humidité: {e}")
            return False
    
    def update_current_humidity(self, humidity: float) -> None:
        """
        Met à jour l'humidité actuelle
        
        Args:
            humidity: Humidité actuelle en pourcentage
        """
        self.current_humidity = humidity
        
        # Logique de contrôle de l'humidification
        if self.target_humidity is not None:
            self._control_humidification()
    
    def _control_humidification(self) -> None:
        """Contrôle la logique d'humidification"""
        try:
            if self.current_humidity is None or self.target_humidity is None:
                return
            
            # Vérifier le temps minimum entre les cycles
            if self.last_cycle_end and (time.time() - self.last_cycle_end) < self.min_cycle_time:
                return
            
            humidity_diff = self.target_humidity - self.current_humidity
            
            # Démarrer l'humidification si l'humidité est trop basse
            if humidity_diff > self.hysteresis and not self.is_humidifying:
                self._start_humidifying()
            
            # Arrêter l'humidification si l'humidité est atteinte
            elif humidity_diff <= 0 and self.is_humidifying:
                self._stop_humidifying()
                
        except Exception as e:
            self.logger.error(f"Erreur contrôle humidification: {e}")
    
    def _start_humidifying(self) -> None:
        """Démarre l'humidification"""
        try:
            if (self.humidifier_relay and self.mister_relay and 
                not self.is_humidifying):
                
                # Démarrer l'humidificateur principal
                self.humidifier_relay.set_state(True)
                
                # Démarrer le brumisateur pour un effet plus rapide
                self.mister_relay.set_state(True)
                
                self.is_humidifying = True
                self.last_humidifying_start = time.time()
                self.cycle_count += 1
                
                self.logger.info("Humidification démarrée")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('humidification_started', {
                        'target_humidity': self.target_humidity,
                        'current_humidity': self.current_humidity,
                        'timestamp': time.time()
                    })
                
        except Exception as e:
            self.logger.error(f"Erreur démarrage humidification: {e}")
    
    def _stop_humidifying(self) -> None:
        """Arrête l'humidification"""
        try:
            if self.humidifier_relay and self.mister_relay and self.is_humidifying:
                # Arrêter l'humidificateur principal
                self.humidifier_relay.set_state(False)
                
                # Arrêter le brumisateur
                self.mister_relay.set_state(False)
                
                self.is_humidifying = False
                self.last_cycle_end = time.time()
                
                # Calculer le temps d'humidification
                if self.last_humidifying_start:
                    humidifying_duration = time.time() - self.last_humidifying_start
                    self.logger.info(f"Humidification arrêtée après {humidifying_duration:.1f}s")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('humidification_stopped', {
                        'target_humidity': self.target_humidity,
                        'current_humidity': self.current_humidity,
                        'timestamp': time.time()
                    })
                
        except Exception as e:
            self.logger.error(f"Erreur arrêt humidification: {e}")
    
    def _emergency_stop(self) -> None:
        """Arrêt d'urgence de l'humidification"""
        try:
            if self.humidifier_relay and self.mister_relay:
                self.humidifier_relay.set_state(False)
                self.mister_relay.set_state(False)
                self.is_humidifying = False
                self.last_cycle_end = time.time()
                self.logger.warning("Arrêt d'urgence de l'humidification")
                
                # Émettre un événement d'urgence
                if self.event_bus:
                    self.event_bus.emit('humidification_emergency_stop', {
                        'current_humidity': self.current_humidity,
                        'max_humidity': self.max_humidity,
                        'timestamp': time.time()
                    })
                
        except Exception as e:
            self.logger.error(f"Erreur arrêt d'urgence humidification: {e}")
    
    def force_on(self) -> bool:
        """
        Force l'allumage de l'humidification (mode manuel)
        
        Returns:
            True si l'opération réussit, False sinon
        """
        try:
            if not self.safety_enabled or (self.current_humidity and self.current_humidity < self.max_humidity):
                self._start_humidifying()
                self.logger.info("Humidification forcée ON")
                return True
            else:
                self.logger.warning("Impossible de forcer l'humidification: sécurité activée")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur forçage humidification: {e}")
            return False
    
    def force_off(self) -> bool:
        """
        Force l'arrêt de l'humidification (mode manuel)
        
        Returns:
            True si l'opération réussit, False sinon
        """
        try:
            self._stop_humidifying()
            self.logger.info("Humidification forcée OFF")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur forçage arrêt humidification: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du contrôleur d'humidification
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'controller': 'humidifier',
            'state': self.state.value,
            'is_humidifying': self.is_humidifying,
            'target_humidity': self.target_humidity,
            'current_humidity': self.current_humidity,
            'hysteresis': self.hysteresis,
            'max_humidity': self.max_humidity,
            'min_cycle_time': self.min_cycle_time,
            'max_cycle_duration': self.max_cycle_duration,
            'safety_enabled': self.safety_enabled,
            'humidifying_time': self.humidifying_time,
            'cycle_count': self.cycle_count,
            'stats': {
                'update_count': self.update_count,
                'error_count': self.error_count,
                'last_update': self.last_update,
                'last_error': str(self.last_error) if self.last_error else None
            }
        }
    
    def cleanup(self) -> None:
        """Nettoie le contrôleur d'humidification"""
        try:
            # Arrêter l'humidification
            if self.is_humidifying:
                self._stop_humidifying()
            
            # Nettoyer les drivers
            if self.humidifier_relay:
                self.humidifier_relay.cleanup()
                self.humidifier_relay = None
            
            if self.mister_relay:
                self.mister_relay.cleanup()
                self.mister_relay = None
            
            self.state = ControllerState.UNINITIALIZED
            self.logger.info("Contrôleur d'humidification nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur humidification: {e}")

