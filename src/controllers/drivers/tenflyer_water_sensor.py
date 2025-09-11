"""
Driver pour le capteur de niveau d'eau Tenflyer
"""

import time
import logging
from typing import Dict, Any, Optional
from .base_driver import BaseDriver, DriverConfig, DriverState, DriverError

try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
except ImportError:
    # Mode simulation pour Windows
    RASPBERRY_PI = False
    GPIO = None

class TenflyerWaterSensor(BaseDriver):
    """
    Driver pour le capteur de niveau d'eau Tenflyer
    """
    
    def __init__(self, config: DriverConfig, gpio_pin: int):
        """
        Initialise le capteur de niveau d'eau Tenflyer
        
        Args:
            config: Configuration du driver
            gpio_pin: Pin GPIO connecté au capteur
        """
        super().__init__(config)
        self.gpio_pin = gpio_pin
        self.last_level = None
        self.last_percentage = None
        self.last_read_time = None
        
        # Configuration Tenflyer
        self.read_timeout = 0.1  # 100ms timeout
        self.retry_delay = 1.0   # 1s entre les lectures
        
        # Seuils de niveau (configurables)
        self.empty_level = 0
        self.full_level = 100
        
    def initialize(self) -> bool:
        """
        Initialise le capteur de niveau d'eau Tenflyer
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.config.enabled:
                self.state = DriverState.DISABLED
                return True
                
            if not RASPBERRY_PI:
                self.logger.error("Capteur Tenflyer nécessite un Raspberry Pi - pas de simulation")
                self.state = DriverState.ERROR
                return False
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            self.state = DriverState.READY
            self.logger.info(f"Capteur Tenflyer initialisé sur pin {self.gpio_pin}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation Tenflyer: {e}")
            self.state = DriverState.ERROR
            return False
    
    def read(self) -> Dict[str, Any]:
        """
        Lit le niveau d'eau du capteur Tenflyer
        
        Returns:
            Dictionnaire contenant level, percentage, timestamp
        """
        if not self.is_ready():
            raise DriverError("Capteur Tenflyer non initialisé")
        
        # Vérifier le délai minimum entre les lectures
        if self.last_read_time and (time.time() - self.last_read_time) < self.retry_delay:
            return {
                "level": self.last_level,
                "percentage": self.last_percentage,
                "timestamp": self.last_read_time,
                "cached": True
            }
        
        if not RASPBERRY_PI:
            raise DriverError("Capteur Tenflyer nécessite un Raspberry Pi - pas de simulation")
        
        level = self._read_tenflyer_hardware()
        
        # Appliquer la calibration
        if self.config.calibration:
            empty_level = self.config.calibration.get("empty_level", self.empty_level)
            full_level = self.config.calibration.get("full_level", self.full_level)
        else:
            empty_level = self.empty_level
            full_level = self.full_level
        
        # Convertir en pourcentage
        percentage = self._level_to_percentage(level, empty_level, full_level)
        
        # Valider les valeurs
        if not self._validate_values(level, percentage):
            raise DriverError(f"Valeurs invalides: Level={level}, Percentage={percentage}%")
        
        # Mettre à jour les valeurs
        self.last_level = level
        self.last_percentage = percentage
        self.last_read_time = time.time()
        
        return {
            "level": level,
            "percentage": percentage,
            "timestamp": self.last_read_time,
            "cached": False,
            "sensor": "tenflyer_water",
            "unit": "percent",
            "empty_level": empty_level,
            "full_level": full_level
        }
    
    def _read_tenflyer_hardware(self) -> int:
        """
        Lecture réelle du capteur Tenflyer sur Raspberry Pi
        
        Returns:
            Niveau d'eau (0-100)
        """
        try:
            # Le capteur Tenflyer utilise un signal PWM
            # Mesurer la durée du signal haut
            high_durations = []
            
            for _ in range(10):  # 10 mesures pour moyenne
                # Attendre le front montant
                timeout_start = time.time()
                while GPIO.input(self.gpio_pin) == GPIO.LOW:
                    if time.time() - timeout_start > self.read_timeout:
                        raise DriverError("Timeout Tenflyer front montant")
                
                # Mesurer la durée du niveau haut
                high_start = time.time()
                while GPIO.input(self.gpio_pin) == GPIO.HIGH:
                    if time.time() - timeout_start > self.read_timeout:
                        raise DriverError("Timeout Tenflyer niveau haut")
                
                high_duration = time.time() - high_start
                high_durations.append(high_duration)
                
                # Petite pause entre les mesures
                time.sleep(0.01)
            
            # Calculer la durée moyenne
            avg_duration = sum(high_durations) / len(high_durations)
            
            # Convertir en niveau (0-100)
            # Durée typique: 1ms = 0%, 2ms = 100%
            level = int((avg_duration - 0.001) / 0.001 * 100)
            level = max(0, min(100, level))
            
            return level
            
        except Exception as e:
            raise DriverError(f"Erreur lecture Tenflyer: {e}")
    
    
    def _level_to_percentage(self, level: int, empty_level: int, full_level: int) -> float:
        """
        Convertit le niveau brut en pourcentage
        
        Args:
            level: Niveau brut (0-100)
            empty_level: Niveau vide
            full_level: Niveau plein
            
        Returns:
            Pourcentage (0.0-100.0)
        """
        if full_level <= empty_level:
            return 0.0
        
        percentage = ((level - empty_level) / (full_level - empty_level)) * 100.0
        return max(0.0, min(100.0, percentage))
    
    def _validate_values(self, level: int, percentage: float) -> bool:
        """
        Valide les valeurs lues du capteur
        
        Args:
            level: Niveau brut (0-100)
            percentage: Pourcentage (0.0-100.0)
            
        Returns:
            True si les valeurs sont valides, False sinon
        """
        return (0 <= level <= 100 and 
                0.0 <= percentage <= 100.0)
    
    def is_empty(self) -> bool:
        """
        Vérifie si le réservoir est vide
        
        Returns:
            True si vide, False sinon
        """
        if self.last_percentage is None:
            return False
        
        empty_threshold = 10.0  # Seuil de vide
        return self.last_percentage <= empty_threshold
    
    def is_low(self) -> bool:
        """
        Vérifie si le niveau est bas
        
        Returns:
            True si bas, False sinon
        """
        if self.last_percentage is None:
            return False
        
        low_threshold = 25.0  # Seuil de niveau bas
        return self.last_percentage <= low_threshold
    
    def is_full(self) -> bool:
        """
        Vérifie si le réservoir est plein
        
        Returns:
            True si plein, False sinon
        """
        if self.last_percentage is None:
            return False
        
        full_threshold = 90.0  # Seuil de plein
        return self.last_percentage >= full_threshold
    
    def get_level(self) -> Optional[int]:
        """
        Retourne le dernier niveau lu
        
        Returns:
            Niveau (0-100) ou None
        """
        return self.last_level
    
    def get_percentage(self) -> Optional[float]:
        """
        Retourne le dernier pourcentage lu
        
        Returns:
            Pourcentage (0.0-100.0) ou None
        """
        return self.last_percentage
    
    def calibrate_empty(self) -> bool:
        """
        Calibre le niveau vide
        
        Returns:
            True si la calibration réussit, False sinon
        """
        try:
            if not self.is_ready():
                return False
            
            # Lire le niveau actuel
            data = self.read()
            if data and "level" in data:
                self.empty_level = data["level"]
                self.logger.info(f"Niveau vide calibré à {self.empty_level}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Erreur calibration niveau vide: {e}")
            return False
    
    def calibrate_full(self) -> bool:
        """
        Calibre le niveau plein
        
        Returns:
            True si la calibration réussit, False sinon
        """
        try:
            if not self.is_ready():
                return False
            
            # Lire le niveau actuel
            data = self.read()
            if data and "level" in data:
                self.full_level = data["level"]
                self.logger.info(f"Niveau plein calibré à {self.full_level}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Erreur calibration niveau plein: {e}")
            return False
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Le capteur de niveau d'eau est en lecture seule
        
        Args:
            data: Données à écrire (ignorées)
            
        Returns:
            False (capteur en lecture seule)
        """
        self.logger.warning("Capteur Tenflyer est en lecture seule")
        return False
    
    def cleanup(self) -> None:
        """
        Nettoie les ressources du capteur
        """
        if RASPBERRY_PI and self.gpio_pin:
            try:
                GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
            except:
                pass
        
        super().cleanup()
