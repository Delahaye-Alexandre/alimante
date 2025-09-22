"""
Contrôleur de chauffage Alimante
Gère le contrôle du chauffage via relais
"""

import time
import logging
from typing import Dict, Any, Optional
from ..base_controller import BaseController, ControllerConfig, ControllerState, ControllerError
from ..drivers.relay_driver import RelayDriver, DriverConfig

class HeaterController(BaseController):
    """
    Contrôleur du système de chauffage
    """
    
    def __init__(self, config: ControllerConfig, gpio_config: Dict[str, Any], 
                 event_bus: Optional[Any] = None):
        """
        Initialise le contrôleur de chauffage
        
        Args:
            config: Configuration du contrôleur
            gpio_config: Configuration GPIO
            event_bus: Bus d'événements
        """
        super().__init__(config, event_bus)
        self.gpio_config = gpio_config
        
        # Driver de relais pour le chauffage
        self.heater_relay = None
        
        # État du chauffage
        self.is_heating = False
        self.target_temperature = None
        self.current_temperature = None
        self.hysteresis = 1.0  # Hystérésis en degrés
        
        # Configuration de sécurité
        self.max_temperature = 35.0
        self.safety_enabled = True
        
        # Statistiques
        self.heating_time = 0
        self.last_heating_start = None
        self.cycle_count = 0
        
    def initialize(self) -> bool:
        """
        Initialise le contrôleur de chauffage
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du contrôleur de chauffage...")
            
            # Configuration du driver de relais
            relay_config = DriverConfig(
                name="heater_relay",
                pin=self.gpio_config.get('heater_pin', 19),
                active_high=True,
                initial_state=False
            )
            
            # Initialiser le driver de relais
            self.heater_relay = RelayDriver(relay_config)
            
            if not self.heater_relay.initialize():
                self.logger.error("Échec initialisation driver relais chauffage")
                return False
            
            # Charger la configuration de sécurité
            self.max_temperature = self.config.get('max_temperature', 35.0)
            self.hysteresis = self.config.get('hysteresis', 1.0)
            self.safety_enabled = self.config.get('safety_enabled', True)
            
            self.state = ControllerState.READY
            self.logger.info("Contrôleur de chauffage initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation contrôleur chauffage: {e}")
            self.state = ControllerState.ERROR
            return False
    
    def update(self) -> bool:
        """
        Met à jour le contrôleur de chauffage
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            if self.state != ControllerState.RUNNING:
                return True
            
            # Mettre à jour les statistiques de chauffage
            if self.is_heating and self.last_heating_start:
                self.heating_time = time.time() - self.last_heating_start
            
            # Vérifier la sécurité
            if self.safety_enabled and self.current_temperature:
                if self.current_temperature > self.max_temperature:
                    self._emergency_stop()
                    self.logger.warning(f"Arrêt d'urgence chauffage: température {self.current_temperature}°C > {self.max_temperature}°C")
                    return False
            
            self.update_count += 1
            self.last_update = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour contrôleur chauffage: {e}")
            self.error_count += 1
            self.last_error = e
            return False
    
    def set_temperature(self, temperature: float) -> bool:
        """
        Définit la température cible
        
        Args:
            temperature: Température cible en degrés Celsius
            
        Returns:
            True si la commande est acceptée, False sinon
        """
        try:
            if not self.safety_enabled or temperature <= self.max_temperature:
                self.target_temperature = temperature
                self.logger.info(f"Température cible définie: {temperature}°C")
                return True
            else:
                self.logger.warning(f"Température refusée: {temperature}°C > {self.max_temperature}°C")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur définition température: {e}")
            return False
    
    def update_current_temperature(self, temperature: float) -> None:
        """
        Met à jour la température actuelle
        
        Args:
            temperature: Température actuelle en degrés Celsius
        """
        self.current_temperature = temperature
        
        # Logique de contrôle du chauffage
        if self.target_temperature is not None:
            self._control_heating()
    
    def _control_heating(self) -> None:
        """Contrôle la logique de chauffage"""
        try:
            if self.current_temperature is None or self.target_temperature is None:
                return
            
            temp_diff = self.target_temperature - self.current_temperature
            
            # Allumer le chauffage si la température est trop basse
            if temp_diff > self.hysteresis and not self.is_heating:
                self._start_heating()
            
            # Éteindre le chauffage si la température est atteinte
            elif temp_diff <= 0 and self.is_heating:
                self._stop_heating()
                
        except Exception as e:
            self.logger.error(f"Erreur contrôle chauffage: {e}")
    
    def _start_heating(self) -> None:
        """Démarre le chauffage"""
        try:
            if self.heater_relay and not self.is_heating:
                self.heater_relay.set_state(True)
                self.is_heating = True
                self.last_heating_start = time.time()
                self.cycle_count += 1
                
                self.logger.info("Chauffage démarré")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('heater_started', {
                        'target_temperature': self.target_temperature,
                        'current_temperature': self.current_temperature,
                        'timestamp': time.time()
                    })
                
        except Exception as e:
            self.logger.error(f"Erreur démarrage chauffage: {e}")
    
    def _stop_heating(self) -> None:
        """Arrête le chauffage"""
        try:
            if self.heater_relay and self.is_heating:
                self.heater_relay.set_state(False)
                self.is_heating = False
                
                # Calculer le temps de chauffage
                if self.last_heating_start:
                    heating_duration = time.time() - self.last_heating_start
                    self.logger.info(f"Chauffage arrêté après {heating_duration:.1f}s")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('heater_stopped', {
                        'target_temperature': self.target_temperature,
                        'current_temperature': self.current_temperature,
                        'timestamp': time.time()
                    })
                
        except Exception as e:
            self.logger.error(f"Erreur arrêt chauffage: {e}")
    
    def _emergency_stop(self) -> None:
        """Arrêt d'urgence du chauffage"""
        try:
            if self.heater_relay:
                self.heater_relay.set_state(False)
                self.is_heating = False
                self.logger.warning("Arrêt d'urgence du chauffage")
                
                # Émettre un événement d'urgence
                if self.event_bus:
                    self.event_bus.emit('heater_emergency_stop', {
                        'current_temperature': self.current_temperature,
                        'max_temperature': self.max_temperature,
                        'timestamp': time.time()
                    })
                
        except Exception as e:
            self.logger.error(f"Erreur arrêt d'urgence chauffage: {e}")
    
    def force_on(self) -> bool:
        """
        Force l'allumage du chauffage (mode manuel)
        
        Returns:
            True si l'opération réussit, False sinon
        """
        try:
            if not self.safety_enabled or (self.current_temperature and self.current_temperature < self.max_temperature):
                self._start_heating()
                self.logger.info("Chauffage forcé ON")
                return True
            else:
                self.logger.warning("Impossible de forcer le chauffage: sécurité activée")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur forçage chauffage: {e}")
            return False
    
    def force_off(self) -> bool:
        """
        Force l'arrêt du chauffage (mode manuel)
        
        Returns:
            True si l'opération réussit, False sinon
        """
        try:
            self._stop_heating()
            self.logger.info("Chauffage forcé OFF")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur forçage arrêt chauffage: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du contrôleur de chauffage
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'controller': 'heater',
            'state': self.state.value,
            'is_heating': self.is_heating,
            'target_temperature': self.target_temperature,
            'current_temperature': self.current_temperature,
            'hysteresis': self.hysteresis,
            'max_temperature': self.max_temperature,
            'safety_enabled': self.safety_enabled,
            'heating_time': self.heating_time,
            'cycle_count': self.cycle_count,
            'stats': {
                'update_count': self.update_count,
                'error_count': self.error_count,
                'last_update': self.last_update,
                'last_error': str(self.last_error) if self.last_error else None
            }
        }
    
    def cleanup(self) -> None:
        """Nettoie le contrôleur de chauffage"""
        try:
            # Arrêter le chauffage
            if self.is_heating:
                self._stop_heating()
            
            # Nettoyer le driver
            if self.heater_relay:
                self.heater_relay.cleanup()
                self.heater_relay = None
            
            self.state = ControllerState.UNINITIALIZED
            self.logger.info("Contrôleur de chauffage nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur chauffage: {e}")

