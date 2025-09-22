"""
Driver MOSFET pour contrôler les LED et actionneurs haute puissance
Utilise PWM pour contrôler l'intensité des LED et autres composants
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

class MosfetDriver(BaseDriver):
    """
    Driver MOSFET pour contrôler les LED et actionneurs haute puissance
    Utilise PWM pour contrôler l'intensité
    """
    
    def __init__(self, config: DriverConfig, gpio_pin: int, frequency: int = 1000):
        """
        Initialise le driver MOSFET
        
        Args:
            config: Configuration du driver
            gpio_pin: Pin GPIO pour le MOSFET
            frequency: Fréquence PWM en Hz
        """
        super().__init__(config)
        self.gpio_pin = gpio_pin
        self.frequency = frequency
        self.current_duty_cycle = 0
        self.pwm_object = None
        self.is_running = False
        
        # Configuration MOSFET
        self.min_duty_cycle = 0
        self.max_duty_cycle = 100
        self.fade_enabled = True
        self.fade_duration = 2.0  # secondes
        self.fade_steps = 100
        
        # Protection thermique
        self.thermal_protection = True
        self.max_temperature = 80.0  # °C
        self.current_temperature = 25.0
        self.thermal_shutdown = False
        
        # Limitation de courant
        self.current_limit = 2.0  # A
        self.current_monitoring = False
        
    def initialize(self) -> bool:
        """
        Initialise le driver MOSFET
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not RASPBERRY_PI:
                self.logger.warning("Mode simulation - Raspberry Pi non détecté")
                self.state = DriverState.READY
                return True
            
            # Configuration GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            
            # Initialiser PWM
            self.pwm_object = GPIO.PWM(self.gpio_pin, self.frequency)
            self.pwm_object.start(0)  # Commencer à 0%
            
            self.state = DriverState.READY
            self.logger.info(f"Driver MOSFET initialisé sur pin {self.gpio_pin}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation driver MOSFET: {e}")
            self.state = DriverState.ERROR
            return False
    
    def read(self) -> Dict[str, Any]:
        """
        Lit l'état du driver MOSFET
        
        Returns:
            Dictionnaire contenant l'état du driver
        """
        try:
            self.read_count += 1
            self.last_update = time.time()
            
            return {
                'driver': 'mosfet',
                'state': self.state.value,
                'gpio_pin': self.gpio_pin,
                'frequency': self.frequency,
                'current_duty_cycle': self.current_duty_cycle,
                'is_running': self.is_running,
                'thermal_protection': self.thermal_protection,
                'current_temperature': self.current_temperature,
                'thermal_shutdown': self.thermal_shutdown,
                'current_limit': self.current_limit,
                'fade_enabled': self.fade_enabled,
                'stats': {
                    'read_count': self.read_count,
                    'error_count': self.error_count,
                    'uptime': time.time() - self.start_time
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lecture driver MOSFET: {e}")
            self.error_count += 1
            self.last_error = e
            return {'error': str(e)}
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Écrit des données vers le driver MOSFET
        
        Args:
            data: Données à écrire (duty_cycle, fade, etc.)
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        try:
            # Vérifier la protection thermique
            if self.thermal_protection and self.thermal_shutdown:
                self.logger.warning("Écriture refusée: protection thermique active")
                return False
            
            # Extraire les paramètres
            duty_cycle = data.get('duty_cycle', self.current_duty_cycle)
            fade = data.get('fade', self.fade_enabled)
            fade_duration = data.get('fade_duration', self.fade_duration)
            
            # Limiter le duty cycle
            duty_cycle = max(self.min_duty_cycle, min(duty_cycle, self.max_duty_cycle))
            
            # Appliquer le changement
            if fade and self.fade_enabled:
                self._fade_to_duty_cycle(duty_cycle, fade_duration)
            else:
                self._set_duty_cycle(duty_cycle)
            
            self.logger.debug(f"Duty cycle MOSFET: {duty_cycle}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur écriture driver MOSFET: {e}")
            self.error_count += 1
            self.last_error = e
            return False
    
    def _set_duty_cycle(self, duty_cycle: float) -> None:
        """Définit le duty cycle du PWM"""
        try:
            if not RASPBERRY_PI:
                self.current_duty_cycle = duty_cycle
                self.is_running = duty_cycle > 0
                return
            
            if self.pwm_object:
                self.pwm_object.ChangeDutyCycle(duty_cycle)
                self.current_duty_cycle = duty_cycle
                self.is_running = duty_cycle > 0
                
        except Exception as e:
            self.logger.error(f"Erreur définition duty cycle: {e}")
            raise
    
    def _fade_to_duty_cycle(self, target_duty_cycle: float, duration: float) -> None:
        """Fait un fondu vers le duty cycle cible"""
        try:
            if not RASPBERRY_PI:
                self.current_duty_cycle = target_duty_cycle
                self.is_running = target_duty_cycle > 0
                return
            
            start_duty_cycle = self.current_duty_cycle
            steps = self.fade_steps
            step_duration = duration / steps
            
            for i in range(steps + 1):
                # Calculer le duty cycle intermédiaire
                progress = i / steps
                current_duty = start_duty_cycle + (target_duty_cycle - start_duty_cycle) * progress
                
                # Appliquer le duty cycle
                self._set_duty_cycle(current_duty)
                
                # Attendre
                time.sleep(step_duration)
                
        except Exception as e:
            self.logger.error(f"Erreur fondu duty cycle: {e}")
            raise
    
    def set_intensity(self, intensity: float) -> bool:
        """
        Définit l'intensité des LED (0-100%)
        
        Args:
            intensity: Intensité en pourcentage
            
        Returns:
            True si la commande réussit, False sinon
        """
        try:
            return self.write({'duty_cycle': intensity, 'fade': True})
            
        except Exception as e:
            self.logger.error(f"Erreur définition intensité: {e}")
            return False
    
    def fade_in(self, duration: float = 2.0) -> bool:
        """
        Fait un fondu d'entrée
        
        Args:
            duration: Durée du fondu en secondes
            
        Returns:
            True si la commande réussit, False sinon
        """
        try:
            return self.write({'duty_cycle': self.max_duty_cycle, 'fade': True, 'fade_duration': duration})
            
        except Exception as e:
            self.logger.error(f"Erreur fondu entrée: {e}")
            return False
    
    def fade_out(self, duration: float = 2.0) -> bool:
        """
        Fait un fondu de sortie
        
        Args:
            duration: Durée du fondu en secondes
            
        Returns:
            True si la commande réussit, False sinon
        """
        try:
            return self.write({'duty_cycle': 0, 'fade': True, 'fade_duration': duration})
            
        except Exception as e:
            self.logger.error(f"Erreur fondu sortie: {e}")
            return False
    
    def set_temperature(self, temperature: float) -> None:
        """
        Met à jour la température pour la protection thermique
        
        Args:
            temperature: Température en degrés Celsius
        """
        self.current_temperature = temperature
        
        # Vérifier la protection thermique
        if self.thermal_protection and temperature > self.max_temperature:
            if not self.thermal_shutdown:
                self.logger.warning(f"Protection thermique activée: {temperature}°C > {self.max_temperature}°C")
                self.thermal_shutdown = True
                self._emergency_shutdown()
        elif self.thermal_shutdown and temperature <= self.max_temperature - 10:
            # Réactiver après refroidissement
            self.logger.info("Protection thermique désactivée")
            self.thermal_shutdown = False
    
    def _emergency_shutdown(self) -> None:
        """Arrêt d'urgence du MOSFET"""
        try:
            self._set_duty_cycle(0)
            self.logger.warning("Arrêt d'urgence MOSFET activé")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt d'urgence MOSFET: {e}")
    
    def enable_thermal_protection(self, enabled: bool) -> None:
        """
        Active/désactive la protection thermique
        
        Args:
            enabled: True pour activer la protection
        """
        self.thermal_protection = enabled
        self.logger.info(f"Protection thermique: {'activée' if enabled else 'désactivée'}")
    
    def set_current_limit(self, limit: float) -> None:
        """
        Définit la limite de courant
        
        Args:
            limit: Limite de courant en ampères
        """
        self.current_limit = limit
        self.logger.info(f"Limite de courant définie: {limit}A")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du driver MOSFET
        
        Returns:
            Dictionnaire contenant le statut
        """
        return self.read()
    
    def cleanup(self) -> None:
        """Nettoie le driver MOSFET"""
        try:
            # Arrêter le PWM
            if self.pwm_object:
                self.pwm_object.stop()
                self.pwm_object = None
            
            # Nettoyer GPIO
            if RASPBERRY_PI:
                GPIO.cleanup(self.gpio_pin)
            
            self.state = DriverState.DISABLED
            self.logger.info("Driver MOSFET nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage driver MOSFET: {e}")
