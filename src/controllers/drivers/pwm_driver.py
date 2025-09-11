"""
Driver PWM pour contrôler les actionneurs (LED, ventilateurs, servo)
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

class PWMDriver(BaseDriver):
    """
    Driver PWM pour contrôler les actionneurs
    """
    
    def __init__(self, config: DriverConfig, gpio_pin: int, frequency: int = 1000):
        """
        Initialise le driver PWM
        
        Args:
            config: Configuration du driver
            gpio_pin: Pin GPIO pour le PWM
            frequency: Fréquence PWM en Hz
        """
        super().__init__(config)
        self.gpio_pin = gpio_pin
        self.frequency = frequency
        self.current_duty_cycle = 0
        self.pwm_object = None
        self.is_running = False
        
        # Configuration PWM
        self.min_duty_cycle = 0
        self.max_duty_cycle = 100
        self.fade_enabled = False
        self.fade_duration = 1.0  # secondes
        self.fade_steps = 50
        
    def initialize(self) -> bool:
        """
        Initialise le driver PWM
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.config.enabled:
                self.state = DriverState.DISABLED
                return True
                
            if not RASPBERRY_PI:
                self.logger.error("PWM nécessite un Raspberry Pi - pas de simulation")
                self.state = DriverState.ERROR
                return False
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            
            # Créer l'objet PWM
            self.pwm_object = GPIO.PWM(self.gpio_pin, self.frequency)
            self.pwm_object.start(0)  # Démarrer à 0%
            self.is_running = True
            
            self.state = DriverState.READY
            self.logger.info(f"PWM initialisé sur pin {self.gpio_pin} à {self.frequency}Hz")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation PWM: {e}")
            self.state = DriverState.ERROR
            return False
    
    def read(self) -> Dict[str, Any]:
        """
        Lit l'état actuel du PWM
        
        Returns:
            Dictionnaire contenant duty_cycle, frequency, status
        """
        if not self.is_ready():
            raise DriverError("PWM non initialisé")
        
        return {
            "duty_cycle": self.current_duty_cycle,
            "frequency": self.frequency,
            "is_running": self.is_running,
            "timestamp": time.time(),
            "sensor": "pwm",
            "unit": "percent"
        }
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Écrit des données vers le PWM
        
        Args:
            data: Données contenant duty_cycle, fade, etc.
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        if not self.is_ready():
            raise DriverError("PWM non initialisé")
        
        try:
            duty_cycle = data.get("duty_cycle", self.current_duty_cycle)
            fade = data.get("fade", self.fade_enabled)
            fade_duration = data.get("fade_duration", self.fade_duration)
            
            # Valider la valeur
            duty_cycle = max(self.min_duty_cycle, min(self.max_duty_cycle, duty_cycle))
            
            if fade and duty_cycle != self.current_duty_cycle:
                return self._fade_to_duty_cycle(duty_cycle, fade_duration)
            else:
                return self._set_duty_cycle(duty_cycle)
                
        except Exception as e:
            self.logger.error(f"Erreur écriture PWM: {e}")
            return False
    
    def _set_duty_cycle(self, duty_cycle: float) -> bool:
        """
        Définit le cycle de service PWM
        
        Args:
            duty_cycle: Cycle de service (0-100)
            
        Returns:
            True si succès, False sinon
        """
        try:
            if RASPBERRY_PI and self.pwm_object:
                self.pwm_object.ChangeDutyCycle(duty_cycle)
            
            self.current_duty_cycle = duty_cycle
            self.logger.debug(f"PWM pin {self.gpio_pin} défini à {duty_cycle}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition duty cycle: {e}")
            return False
    
    def _fade_to_duty_cycle(self, target_duty_cycle: float, duration: float) -> bool:
        """
        Transition douce vers un nouveau cycle de service
        
        Args:
            target_duty_cycle: Cycle de service cible (0-100)
            duration: Durée de la transition en secondes
            
        Returns:
            True si succès, False sinon
        """
        try:
            start_duty_cycle = self.current_duty_cycle
            steps = self.fade_steps
            step_delay = duration / steps
            step_size = (target_duty_cycle - start_duty_cycle) / steps
            
            self.logger.info(f"Fade PWM de {start_duty_cycle}% à {target_duty_cycle}% sur {duration}s")
            
            for i in range(steps + 1):
                current_duty_cycle = start_duty_cycle + (step_size * i)
                self._set_duty_cycle(current_duty_cycle)
                time.sleep(step_delay)
            
            # S'assurer d'atteindre la valeur exacte
            self._set_duty_cycle(target_duty_cycle)
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur fade PWM: {e}")
            return False
    
    def set_frequency(self, frequency: int) -> bool:
        """
        Change la fréquence PWM
        
        Args:
            frequency: Nouvelle fréquence en Hz
            
        Returns:
            True si succès, False sinon
        """
        try:
            if RASPBERRY_PI and self.pwm_object:
                self.pwm_object.ChangeFrequency(frequency)
            
            self.frequency = frequency
            self.logger.info(f"Fréquence PWM changée à {frequency}Hz")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur changement fréquence PWM: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Arrête le PWM
        
        Returns:
            True si succès, False sinon
        """
        try:
            if RASPBERRY_PI and self.pwm_object:
                self.pwm_object.stop()
            
            self.is_running = False
            self.current_duty_cycle = 0
            self.logger.info(f"PWM pin {self.gpio_pin} arrêté")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt PWM: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre le PWM
        
        Returns:
            True si succès, False sinon
        """
        try:
            if RASPBERRY_PI and self.pwm_object:
                self.pwm_object.start(self.current_duty_cycle)
            
            self.is_running = True
            self.logger.info(f"PWM pin {self.gpio_pin} démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage PWM: {e}")
            return False
    
    def get_duty_cycle(self) -> float:
        """
        Retourne le cycle de service actuel
        
        Returns:
            Cycle de service (0-100)
        """
        return self.current_duty_cycle
    
    def get_frequency(self) -> int:
        """
        Retourne la fréquence actuelle
        
        Returns:
            Fréquence en Hz
        """
        return self.frequency
    
    def set_limits(self, min_duty: float, max_duty: float) -> bool:
        """
        Définit les limites du cycle de service
        
        Args:
            min_duty: Cycle de service minimum (0-100)
            max_duty: Cycle de service maximum (0-100)
            
        Returns:
            True si succès, False sinon
        """
        try:
            self.min_duty_cycle = max(0, min(100, min_duty))
            self.max_duty_cycle = max(0, min(100, max_duty))
            
            if self.min_duty_cycle > self.max_duty_cycle:
                self.min_duty_cycle, self.max_duty_cycle = self.max_duty_cycle, self.min_duty_cycle
            
            self.logger.info(f"Limites PWM définies: {self.min_duty_cycle}%-{self.max_duty_cycle}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition limites PWM: {e}")
            return False
    
    def cleanup(self) -> None:
        """
        Nettoie les ressources du PWM
        """
        if self.pwm_object:
            try:
                self.pwm_object.stop()
            except:
                pass
        
        if RASPBERRY_PI and self.gpio_pin:
            try:
                GPIO.setup(self.gpio_pin, GPIO.IN)
            except:
                pass
        
        super().cleanup()
