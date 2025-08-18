"""
gpio_manager.py
Gestionnaire GPIO pour Raspberry Pi - remplace SerialManager
"""

import RPi.GPIO as GPIO
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class PinMode(Enum):
    INPUT = "input"
    OUTPUT = "output"
    PWM = "pwm"

@dataclass
class PinConfig:
    pin: int
    mode: PinMode
    initial_state: Optional[bool] = None
    pwm_frequency: Optional[int] = None

class GPIOManager:
    """Gestionnaire GPIO pour Raspberry Pi"""
    
    def __init__(self):
        self.pins: Dict[int, Any] = {}
        self.pwm_channels: Dict[int, Any] = {}
        self.initialized = False
        self.setup_gpio()
    
    def setup_gpio(self) -> bool:
        """Initialise le système GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)  # Utilise les numéros BCM
            GPIO.setwarnings(False)  # Désactive les warnings
            self.initialized = True
            logging.info("GPIO initialisé avec succès")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation GPIO: {e}")
            return False
    
    def setup_pin(self, pin_config: PinConfig) -> bool:
        """Configure un pin GPIO"""
        try:
            pin = pin_config.pin
            mode = pin_config.mode
            
            if mode == PinMode.INPUT:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            elif mode == PinMode.OUTPUT:
                GPIO.setup(pin, GPIO.OUT, initial=pin_config.initial_state or False)
            elif mode == PinMode.PWM:
                GPIO.setup(pin, GPIO.OUT)
                pwm = GPIO.PWM(pin, pin_config.pwm_frequency or 1000)
                pwm.start(0)
                self.pwm_channels[pin] = pwm
            
            self.pins[pin] = pin_config
            logging.info(f"Pin {pin} configuré en mode {mode.value}")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de la configuration du pin {pin_config.pin}: {e}")
            return False
    
    def read_digital(self, pin: int) -> Optional[bool]:
        """Lit l'état d'un pin digital"""
        if not self.initialized or pin not in self.pins:
            logging.error(f"Pin {pin} non configuré")
            return None
        
        try:
            return GPIO.input(pin) == GPIO.HIGH
        except Exception as e:
            logging.error(f"Erreur lors de la lecture du pin {pin}: {e}")
            return None
    
    def write_digital(self, pin: int, state: bool) -> bool:
        """Écrit l'état d'un pin digital"""
        if not self.initialized or pin not in self.pins:
            logging.error(f"Pin {pin} non configuré")
            return False
        
        try:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            logging.debug(f"Pin {pin} mis à {state}")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'écriture du pin {pin}: {e}")
            return False
    
    def set_pin_state(self, pin: int, state: bool) -> bool:
        """Alias pour write_digital - compatibilité avec les contrôleurs existants"""
        return self.write_digital(pin, state)
    
    def get_pin_state(self, pin: int) -> Optional[bool]:
        """Alias pour read_digital - compatibilité avec les contrôleurs existants"""
        return self.read_digital(pin)
    
    def read_analog(self, pin: int) -> Optional[float]:
        """Lit la valeur analogique d'un pin (simulation pour Raspberry Pi)"""
        if not self.initialized or pin not in self.pins:
            logging.error(f"Pin {pin} non configuré")
            return None
        
        try:
            # Note: Raspberry Pi n'a pas de pins analogiques natifs
            # Cette méthode simule une lecture analogique pour compatibilité
            # En production, utiliser un ADC externe (MCP3008, PCF8591, etc.)
            
            # Simulation temporaire - retourne une valeur entre 0 et 1
            import random
            analog_value = random.uniform(0.0, 1.0)
            
            logging.debug(f"Lecture analogique simulée pin {pin}: {analog_value:.3f}")
            return analog_value
            
        except Exception as e:
            logging.error(f"Erreur lors de la lecture analogique du pin {pin}: {e}")
            return None
    
    def set_pwm_duty_cycle(self, pin: int, duty_cycle: float) -> bool:
        """Définit le cycle de travail PWM (0-100)"""
        if pin not in self.pwm_channels:
            logging.error(f"Pin {pin} n'est pas configuré en PWM")
            return False
        
        try:
            duty_cycle = max(0, min(100, duty_cycle))  # Clamp entre 0 et 100
            self.pwm_channels[pin].ChangeDutyCycle(duty_cycle)
            logging.debug(f"PWM pin {pin} à {duty_cycle}%")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la définition du cycle PWM: {e}")
            return False
    
    def set_servo_position(self, pin: int, pulse_width: int) -> bool:
        """
        Définit la position d'un servomoteur via PWM
        
        :param pin: Pin GPIO du servo
        :param pulse_width: Largeur d'impulsion en microsecondes (500-2500)
        :return: True si réussi, False sinon
        """
        try:
            if pin not in self.pwm_channels:
                logging.error(f"Pin {pin} n'est pas configuré en PWM")
                return False
            
            # Convertir la largeur d'impulsion en cycle de travail
            # Fréquence typique: 50Hz (20ms période)
            # Cycle de travail = (pulse_width / 20000) * 100
            duty_cycle = (pulse_width / 20000.0) * 100
            
            # Limiter le cycle de travail à 0-100%
            duty_cycle = max(0.0, min(100.0, duty_cycle))
            
            # Appliquer le cycle de travail
            pwm = self.pwm_channels[pin]
            pwm.ChangeDutyCycle(duty_cycle)
            
            logging.debug(f"Servo pin {pin} positionné à {pulse_width}μs ({duty_cycle:.1f}%)")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors du positionnement du servo: {e}")
            return False
    
    def cleanup(self):
        """Nettoie les ressources GPIO"""
        try:
            for pwm in self.pwm_channels.values():
                pwm.stop()
            GPIO.cleanup()
            logging.info("GPIO nettoyé")
        except Exception as e:
            logging.error(f"Erreur lors du nettoyage GPIO: {e}")

# Configuration des pins pour le projet
class PinAssignments:
    # Capteurs
    TEMP_HUMIDITY_PIN = 4  # DHT22
    LIGHT_SENSOR_PIN = 17  # Capteur de lumière
    
    # Actionneurs
    HEATING_RELAY_PIN = 18  # Relais chauffage
    HUMIDITY_RELAY_PIN = 23  # Relais ultrasonic mist
    FEEDING_SERVO_PIN = 12  # Servo trappe
    LIGHT_RELAY_PIN = 24   # Relais éclairage
    
    # LED de statut
    STATUS_LED_PIN = 25 