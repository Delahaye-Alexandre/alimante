"""
Driver pour les servo-moteurs (distributeur de nourriture)
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

class ServoDriver(BaseDriver):
    """
    Driver pour contrôler les servo-moteurs
    """
    
    def __init__(self, config: DriverConfig, gpio_pin: int, frequency: int = 50):
        """
        Initialise le driver de servo-moteur
        
        Args:
            config: Configuration du driver
            gpio_pin: Pin GPIO pour le PWM
            frequency: Fréquence PWM en Hz (50Hz standard)
        """
        super().__init__(config)
        self.gpio_pin = gpio_pin
        self.frequency = frequency
        self.current_angle = 0
        self.pwm_object = None
        self._is_running = False
        
        # Configuration servo
        self.min_angle = 0
        self.max_angle = 180
        self.min_pulse_width = 1.0  # ms
        self.max_pulse_width = 2.0  # ms
        self.center_pulse_width = 1.5  # ms
        
        # Positions prédéfinies
        self.positions = {
            "closed": 0,           # Fermé
            "open": 90,            # Ouvert (déprécié)
            "half": 45,            # Demi-ouvert
            "center": 90,          # Centre
            # Positions double trappe simultanée
            "trap_entrance_open": 0,    # Entrée ouverte, sortie fermée
            "trap_entrance_closed": 90  # Entrée fermée, sortie ouverte
        }
        
    def initialize(self) -> bool:
        """
        Initialise le driver de servo-moteur
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.config.enabled:
                self.state = DriverState.DISABLED
                return True
                
            if not RASPBERRY_PI:
                self.logger.error("Servo nécessite un Raspberry Pi - pas de simulation")
                self.state = DriverState.ERROR
                return False
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            
            # Créer l'objet PWM
            self.pwm_object = GPIO.PWM(self.gpio_pin, self.frequency)
            self.pwm_object.start(0)
            self._is_running = True
            
            # Position initiale : fermé
            self._set_angle(0)
            
            self.state = DriverState.READY
            self.logger.info(f"Servo initialisé sur pin {self.gpio_pin} à {self.frequency}Hz")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation servo: {e}")
            self.state = DriverState.ERROR
            return False
    
    def read(self) -> Dict[str, Any]:
        """
        Lit l'état actuel du servo
        
        Returns:
            Dictionnaire contenant angle, position, status
        """
        if not self.is_ready():
            raise DriverError("Servo non initialisé")
        
        return {
            "angle": self.current_angle,
            "position": self._angle_to_position(self.current_angle),
            "is_running": self.is_running,
            "timestamp": time.time(),
            "sensor": "servo",
            "unit": "degrees"
        }
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Écrit des données vers le servo
        
        Args:
            data: Données contenant angle, position, duration, etc.
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        if not self.is_ready():
            raise DriverError("Servo non initialisé")
        
        try:
            angle = data.get("angle", None)
            position = data.get("position", None)
            duration = data.get("duration", 1.0)  # Durée de la rotation
            smooth = data.get("smooth", True)  # Rotation douce
            
            # Déterminer l'angle cible
            target_angle = None
            if angle is not None:
                target_angle = angle
            elif position is not None:
                target_angle = self._position_to_angle(position)
            
            if target_angle is None:
                self.logger.error("Angle ou position non spécifié")
                return False
            
            # Valider l'angle
            target_angle = max(self.min_angle, min(self.max_angle, target_angle))
            
            if smooth and target_angle != self.current_angle:
                return self._smooth_move_to_angle(target_angle, duration)
            else:
                return self._set_angle(target_angle)
                
        except Exception as e:
            self.logger.error(f"Erreur écriture servo: {e}")
            return False
    
    def _set_angle(self, angle: float) -> bool:
        """
        Définit l'angle du servo
        
        Args:
            angle: Angle en degrés (0-180)
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Convertir l'angle en largeur d'impulsion
            pulse_width = self._angle_to_pulse_width(angle)
            duty_cycle = self._pulse_width_to_duty_cycle(pulse_width)
            
            if RASPBERRY_PI and self.pwm_object:
                self.pwm_object.ChangeDutyCycle(duty_cycle)
            
            self.current_angle = angle
            self.logger.debug(f"Servo pin {self.gpio_pin} défini à {angle}°")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition angle servo: {e}")
            return False
    
    def _smooth_move_to_angle(self, target_angle: float, duration: float) -> bool:
        """
        Rotation douce vers un angle
        
        Args:
            target_angle: Angle cible en degrés
            duration: Durée de la rotation en secondes
            
        Returns:
            True si succès, False sinon
        """
        try:
            start_angle = self.current_angle
            steps = 20  # Nombre d'étapes
            step_delay = duration / steps
            step_size = (target_angle - start_angle) / steps
            
            self.logger.info(f"Rotation servo de {start_angle}° à {target_angle}° sur {duration}s")
            
            for i in range(steps + 1):
                current_angle = start_angle + (step_size * i)
                self._set_angle(current_angle)
                time.sleep(step_delay)
            
            # S'assurer d'atteindre l'angle exact
            self._set_angle(target_angle)
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur rotation douce servo: {e}")
            return False
    
    def _angle_to_pulse_width(self, angle: float) -> float:
        """
        Convertit un angle en largeur d'impulsion
        
        Args:
            angle: Angle en degrés (0-180)
            
        Returns:
            Largeur d'impulsion en ms
        """
        # Interpolation linéaire entre min et max
        ratio = angle / (self.max_angle - self.min_angle)
        pulse_width = self.min_pulse_width + ratio * (self.max_pulse_width - self.min_pulse_width)
        return pulse_width
    
    def _pulse_width_to_duty_cycle(self, pulse_width: float) -> float:
        """
        Convertit une largeur d'impulsion en cycle de service
        
        Args:
            pulse_width: Largeur d'impulsion en ms
            
        Returns:
            Cycle de service en %
        """
        # Cycle de service = (largeur_impulsion / période) * 100
        period_ms = 1000 / self.frequency  # Période en ms
        duty_cycle = (pulse_width / period_ms) * 100
        return duty_cycle
    
    def _angle_to_position(self, angle: float) -> str:
        """
        Convertit un angle en position nommée
        
        Args:
            angle: Angle en degrés
            
        Returns:
            Position nommée
        """
        if angle <= 10:
            return "closed"
        elif angle >= 170:
            return "open"
        elif 40 <= angle <= 50:
            return "half"
        elif 85 <= angle <= 95:
            return "center"
        else:
            return f"{angle:.0f}°"
    
    def _position_to_angle(self, position: str) -> Optional[float]:
        """
        Convertit une position nommée en angle
        
        Args:
            position: Position nommée
            
        Returns:
            Angle en degrés ou None
        """
        return self.positions.get(position.lower())
    
    def move_to_position(self, position: str, duration: float = 1.0) -> bool:
        """
        Déplace le servo vers une position nommée
        
        Args:
            position: Position nommée
            duration: Durée de la rotation
            
        Returns:
            True si succès, False sinon
        """
        angle = self._position_to_angle(position)
        if angle is None:
            self.logger.error(f"Position inconnue: {position}")
            return False
        
        return self.write({"angle": angle, "duration": duration})
    
    def open(self, duration: float = 1.0) -> bool:
        """
        Ouvre le servo (position ouverte)
        
        Args:
            duration: Durée de la rotation
            
        Returns:
            True si succès, False sinon
        """
        return self.move_to_position("open", duration)
    
    def close(self, duration: float = 1.0) -> bool:
        """
        Ferme le servo (position fermée)
        
        Args:
            duration: Durée de la rotation
            
        Returns:
            True si succès, False sinon
        """
        return self.move_to_position("closed", duration)
    
    def center(self, duration: float = 1.0) -> bool:
        """
        Centre le servo
        
        Args:
            duration: Durée de la rotation
            
        Returns:
            True si succès, False sinon
        """
        return self.move_to_position("center", duration)
    
    def get_angle(self) -> float:
        """
        Retourne l'angle actuel
        
        Returns:
            Angle en degrés
        """
        return self.current_angle
    
    def get_position(self) -> str:
        """
        Retourne la position actuelle
        
        Returns:
            Position nommée
        """
        return self._angle_to_position(self.current_angle)
    
    def set_limits(self, min_angle: float, max_angle: float) -> bool:
        """
        Définit les limites d'angle
        
        Args:
            min_angle: Angle minimum en degrés
            max_angle: Angle maximum en degrés
            
        Returns:
            True si succès, False sinon
        """
        try:
            self.min_angle = max(0, min(180, min_angle))
            self.max_angle = max(0, min(180, max_angle))
            
            if self.min_angle > self.max_angle:
                self.min_angle, self.max_angle = self.max_angle, self.min_angle
            
            self.logger.info(f"Limites servo définies: {self.min_angle}°-{self.max_angle}°")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition limites servo: {e}")
            return False
    
    def set_pulse_limits(self, min_pulse: float, max_pulse: float) -> bool:
        """
        Définit les limites de largeur d'impulsion
        
        Args:
            min_pulse: Largeur minimum en ms
            max_pulse: Largeur maximum en ms
            
        Returns:
            True si succès, False sinon
        """
        try:
            self.min_pulse_width = max(0.5, min(2.5, min_pulse))
            self.max_pulse_width = max(0.5, min(2.5, max_pulse))
            
            if self.min_pulse_width > self.max_pulse_width:
                self.min_pulse_width, self.max_pulse_width = self.max_pulse_width, self.min_pulse_width
            
            self.logger.info(f"Limites impulsion définies: {self.min_pulse_width}-{self.max_pulse_width}ms")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition limites impulsion: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre le servo (démarre le PWM)
        
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.is_ready():
                self.logger.error("Servo non initialisé")
                return False
            
            if RASPBERRY_PI and self.pwm_object:
                # Démarrer le PWM à 0% pour position neutre (pas de mouvement)
                self.pwm_object.start(0)
                self.current_angle = 0
            
            self._is_running = True
            self.logger.info(f"Servo pin {self.gpio_pin} démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage servo: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Arrête le servo (arrête le PWM)
        
        Returns:
            True si succès, False sinon
        """
        try:
            if RASPBERRY_PI and self.pwm_object:
                self.pwm_object.stop()
            
            self._is_running = False
            self.logger.info(f"Servo pin {self.gpio_pin} arrêté")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt servo: {e}")
            return False
    
    def is_running(self) -> bool:
        """
        Vérifie si le servo est en cours d'exécution
        
        Returns:
            True si en cours d'exécution, False sinon
        """
        return self._is_running and self.is_ready()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du servo
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'name': self.config.name,
            'enabled': self.config.enabled,
            'state': self.state.value,
            'is_ready': self.is_ready(),
            'is_running': self.is_running(),
            'current_angle': self.current_angle,
            'frequency': self.frequency,
            'min_angle': self.min_angle,
            'max_angle': self.max_angle
        }
    
    def cleanup(self) -> None:
        """
        Nettoie les ressources du servo
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
