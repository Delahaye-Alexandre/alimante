"""
Contrôleur de ventilation Alimante
Gère le contrôle des ventilateurs via PWM
"""

import time
import logging
from typing import Dict, Any, Optional
from ..base_controller import BaseController, ControllerConfig, ControllerState, ControllerError
from ..drivers.pwm_driver import PWMDriver, DriverConfig

class FanController(BaseController):
    """
    Contrôleur du système de ventilation
    """
    
    def __init__(self, config: ControllerConfig, gpio_config: Dict[str, Any], 
                 event_bus: Optional[Any] = None):
        """
        Initialise le contrôleur de ventilation
        
        Args:
            config: Configuration du contrôleur
            gpio_config: Configuration GPIO
            event_bus: Bus d'événements
        """
        super().__init__(config, event_bus)
        self.gpio_config = gpio_config
        
        # Drivers PWM pour les ventilateurs
        self.fan_pwm = None
        
        # État de la ventilation
        self.is_running = False
        self.current_speed = 0  # 0-100%
        self.target_speed = 0
        self.auto_mode = True
        
        # Configuration de ventilation
        self.min_speed = 20  # Vitesse minimale en %
        self.max_speed = 100  # Vitesse maximale en %
        self.ramp_time = 5.0  # Temps de montée/descente en secondes
        
        # Contrôle automatique basé sur la qualité de l'air
        self.air_quality_thresholds = {
            'excellent': 0,      # Pas de ventilation
            'good': 30,          # Ventilation faible
            'moderate': 60,      # Ventilation modérée
            'poor': 80,          # Ventilation forte
            'hazardous': 100     # Ventilation maximale
        }
        
        # Statistiques
        self.total_runtime = 0
        self.last_speed_change = None
        self.speed_changes = 0
        
    def initialize(self) -> bool:
        """
        Initialise le contrôleur de ventilation
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du contrôleur de ventilation...")
            
            # Configuration du driver PWM
            pwm_config = DriverConfig(
                name="fan_pwm",
                pin=self.gpio_config.get('fan_pin', 12),
                frequency=1000,  # 1kHz pour les ventilateurs
                duty_cycle=0
            )
            
            # Initialiser le driver PWM
            self.fan_pwm = PWMDriver(pwm_config)
            
            if not self.fan_pwm.initialize():
                self.logger.error("Échec initialisation driver PWM ventilateur")
                return False
            
            # Charger la configuration
            self.min_speed = self.config.get('min_speed', 20)
            self.max_speed = self.config.get('max_speed', 100)
            self.ramp_time = self.config.get('ramp_time', 5.0)
            self.auto_mode = self.config.get('auto_mode', True)
            
            # Charger les seuils de qualité d'air
            thresholds = self.config.get('air_quality_thresholds', {})
            self.air_quality_thresholds.update(thresholds)
            
            self.state = ControllerState.READY
            self.logger.info("Contrôleur de ventilation initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation contrôleur ventilation: {e}")
            self.state = ControllerState.ERROR
            return False
    
    def update(self) -> bool:
        """
        Met à jour le contrôleur de ventilation
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            if self.state != ControllerState.RUNNING:
                return True
            
            # Mettre à jour les statistiques de fonctionnement
            if self.is_running:
                self.total_runtime += 0.1  # Mise à jour toutes les 100ms
            
            # Gérer la rampe de vitesse
            self._update_speed_ramp()
            
            self.update_count += 1
            self.last_update = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour contrôleur ventilation: {e}")
            self.error_count += 1
            self.last_error = e
            return False
    
    def set_speed(self, speed: int) -> bool:
        """
        Définit la vitesse du ventilateur
        
        Args:
            speed: Vitesse en pourcentage (0-100)
            
        Returns:
            True si la commande est acceptée, False sinon
        """
        try:
            # Limiter la vitesse dans la plage autorisée
            speed = max(self.min_speed, min(speed, self.max_speed))
            
            if speed != self.target_speed:
                self.target_speed = speed
                self.last_speed_change = time.time()
                self.speed_changes += 1
                
                self.logger.info(f"Vitesse ventilateur définie: {speed}%")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('fan_speed_changed', {
                        'target_speed': speed,
                        'current_speed': self.current_speed,
                        'timestamp': time.time()
                    })
            
            return True
                
        except Exception as e:
            self.logger.error(f"Erreur définition vitesse ventilateur: {e}")
            return False
    
    def set_auto_mode(self, enabled: bool) -> None:
        """
        Active/désactive le mode automatique
        
        Args:
            enabled: True pour activer le mode automatique
        """
        self.auto_mode = enabled
        self.logger.info(f"Mode automatique ventilation: {'activé' if enabled else 'désactivé'}")
    
    def update_air_quality(self, air_quality: float) -> None:
        """
        Met à jour la qualité de l'air pour le contrôle automatique
        
        Args:
            air_quality: Valeur de qualité de l'air (0-500 AQI)
        """
        if not self.auto_mode:
            return
        
        # Déterminer la vitesse basée sur la qualité de l'air
        if air_quality <= 50:
            target_speed = self.air_quality_thresholds['excellent']
        elif air_quality <= 100:
            target_speed = self.air_quality_thresholds['good']
        elif air_quality <= 150:
            target_speed = self.air_quality_thresholds['moderate']
        elif air_quality <= 200:
            target_speed = self.air_quality_thresholds['poor']
        else:
            target_speed = self.air_quality_thresholds['hazardous']
        
        self.set_speed(target_speed)
    
    def _update_speed_ramp(self) -> None:
        """Met à jour la rampe de vitesse"""
        try:
            if self.current_speed == self.target_speed:
                return
            
            if not self.last_speed_change:
                self.last_speed_change = time.time()
                return
            
            # Calculer le temps écoulé depuis le dernier changement
            elapsed = time.time() - self.last_speed_change
            
            if elapsed >= self.ramp_time:
                # Rampe terminée, définir la vitesse cible
                self._set_fan_speed(self.target_speed)
            else:
                # Calculer la vitesse intermédiaire
                progress = elapsed / self.ramp_time
                speed_diff = self.target_speed - self.current_speed
                intermediate_speed = self.current_speed + (speed_diff * progress)
                self._set_fan_speed(int(intermediate_speed))
                
        except Exception as e:
            self.logger.error(f"Erreur mise à jour rampe vitesse: {e}")
    
    def _set_fan_speed(self, speed: int) -> None:
        """Définit la vitesse réelle du ventilateur"""
        try:
            if self.fan_pwm:
                # Convertir le pourcentage en duty cycle (0-100)
                duty_cycle = max(0, min(100, speed))
                self.fan_pwm.set_duty_cycle(duty_cycle)
                
                # Mettre à jour l'état
                self.current_speed = speed
                self.is_running = speed > 0
                
                if speed > 0 and not self.is_running:
                    self.logger.info("Ventilateur démarré")
                elif speed == 0 and self.is_running:
                    self.logger.info("Ventilateur arrêté")
                
        except Exception as e:
            self.logger.error(f"Erreur définition vitesse ventilateur: {e}")
    
    def start(self) -> bool:
        """
        Démarre le contrôleur de ventilation
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not super().start():
                return False
            
            # Démarrer avec la vitesse minimale
            self.set_speed(self.min_speed)
            self.logger.info("Contrôleur de ventilation démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage contrôleur ventilation: {e}")
            return False
    
    def stop(self) -> None:
        """Arrête le contrôleur de ventilation"""
        try:
            # Arrêter le ventilateur
            self.set_speed(0)
            
            # Appeler la méthode parent
            super().stop()
            
            self.logger.info("Contrôleur de ventilation arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt contrôleur ventilation: {e}")
    
    def force_on(self, speed: int = 100) -> bool:
        """
        Force l'allumage du ventilateur (mode manuel)
        
        Args:
            speed: Vitesse forcée en pourcentage
            
        Returns:
            True si l'opération réussit, False sinon
        """
        try:
            self.set_auto_mode(False)
            self.set_speed(speed)
            self.logger.info(f"Ventilateur forcé ON à {speed}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur forçage ventilateur: {e}")
            return False
    
    def force_off(self) -> bool:
        """
        Force l'arrêt du ventilateur (mode manuel)
        
        Returns:
            True si l'opération réussit, False sinon
        """
        try:
            self.set_speed(0)
            self.logger.info("Ventilateur forcé OFF")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur forçage arrêt ventilateur: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du contrôleur de ventilation
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'controller': 'fan',
            'state': self.state.value,
            'is_running': self.is_running,
            'current_speed': self.current_speed,
            'target_speed': self.target_speed,
            'auto_mode': self.auto_mode,
            'min_speed': self.min_speed,
            'max_speed': self.max_speed,
            'ramp_time': self.ramp_time,
            'air_quality_thresholds': self.air_quality_thresholds,
            'total_runtime': self.total_runtime,
            'speed_changes': self.speed_changes,
            'stats': {
                'update_count': self.update_count,
                'error_count': self.error_count,
                'last_update': self.last_update,
                'last_error': str(self.last_error) if self.last_error else None
            }
        }
    
    def cleanup(self) -> None:
        """Nettoie le contrôleur de ventilation"""
        try:
            # Arrêter le ventilateur
            self.set_speed(0)
            
            # Nettoyer le driver
            if self.fan_pwm:
                self.fan_pwm.cleanup()
                self.fan_pwm = None
            
            self.state = ControllerState.UNINITIALIZED
            self.logger.info("Contrôleur de ventilation nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur ventilation: {e}")

