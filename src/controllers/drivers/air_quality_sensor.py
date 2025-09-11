"""
Driver pour le capteur de qualité d'air générique
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

class AirQualitySensor(BaseDriver):
    """
    Driver pour capteur de qualité d'air générique (ADC)
    """
    
    def __init__(self, config: DriverConfig, gpio_pin: int, adc_channel: int = 0):
        """
        Initialise le capteur de qualité d'air
        
        Args:
            config: Configuration du driver
            gpio_pin: Pin GPIO (non utilisé pour ADC)
            adc_channel: Canal ADC (0-7)
        """
        super().__init__(config)
        self.gpio_pin = gpio_pin
        self.adc_channel = adc_channel
        self.last_value = None
        self.last_aqi = None
        self.last_read_time = None
        
        # Configuration ADC
        self.adc_resolution = 12  # 12 bits
        self.reference_voltage = 3.3  # 3.3V
        self.max_value = (2 ** self.adc_resolution) - 1
        
        # Seuils de qualité d'air (configurables)
        self.aqi_thresholds = {
            "excellent": 0,
            "good": 50,
            "moderate": 100,
            "unhealthy": 150,
            "hazardous": 300
        }
        
    def initialize(self) -> bool:
        """
        Initialise le capteur de qualité d'air
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.config.enabled:
                self.state = DriverState.DISABLED
                return True
            
            if not RASPBERRY_PI:
                self.logger.error("Capteur qualité d'air nécessite un Raspberry Pi - pas de simulation")
                self.state = DriverState.ERROR
                return False
            
            # Initialiser l'ADC (MCP3008 ou similaire)
            self._init_adc_hardware()
            
            self.state = DriverState.READY
            self.logger.info(f"Capteur qualité d'air initialisé (ADC channel {self.adc_channel})")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation capteur qualité d'air: {e}")
            self.state = DriverState.ERROR
            return False
    
    def read(self) -> Dict[str, Any]:
        """
        Lit la qualité d'air
        
        Returns:
            Dictionnaire contenant raw_value, aqi, level, timestamp
        """
        if not self.is_ready():
            raise DriverError("Capteur qualité d'air non initialisé")
        
        if not RASPBERRY_PI:
            raise DriverError("Capteur qualité d'air nécessite un Raspberry Pi - pas de simulation")
        
        raw_value = self._read_adc_hardware()
        
        # Appliquer la calibration
        if self.config.calibration:
            baseline = self.config.calibration.get("baseline", 0)
            sensitivity = self.config.calibration.get("sensitivity", 1.0)
            raw_value = (raw_value - baseline) * sensitivity + baseline
        
        # Convertir en AQI
        aqi = self._raw_to_aqi(raw_value)
        level = self._aqi_to_level(aqi)
        
        # Mettre à jour les valeurs
        self.last_value = raw_value
        self.last_aqi = aqi
        self.last_read_time = time.time()
        
        return {
            "raw_value": raw_value,
            "aqi": aqi,
            "level": level,
            "timestamp": self.last_read_time,
            "sensor": "air_quality",
            "unit": "aqi",
            "adc_channel": self.adc_channel
        }
    
    def _init_adc_hardware(self) -> None:
        """
        Initialise l'ADC hardware (MCP3008)
        """
        try:
            import spidev
            
            # Configuration SPI pour MCP3008
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)  # Bus 0, Device 0
            self.spi.max_speed_hz = 1000000  # 1MHz
            
            self.logger.info("ADC MCP3008 initialisé")
            
        except ImportError:
            self.logger.warning("spidev non disponible, utilisation de la simulation")
            self.spi = None
        except Exception as e:
            self.logger.error(f"Erreur initialisation ADC: {e}")
            raise
    
    def _read_adc_hardware(self) -> int:
        """
        Lecture réelle de l'ADC sur Raspberry Pi
        
        Returns:
            Valeur ADC brute (0-4095)
        """
        try:
            if not hasattr(self, 'spi') or self.spi is None:
                return self._read_adc_simulation()
            
            # Configuration pour MCP3008
            # Channel 0-7, single-ended mode
            adc_command = 0x80 | (self.adc_channel << 4)
            
            # Envoyer la commande et lire la réponse
            response = self.spi.xfer2([1, adc_command, 0])
            
            # Extraire la valeur (10 bits)
            adc_value = ((response[1] & 0x03) << 8) | response[2]
            
            # Convertir en 12 bits pour cohérence
            adc_value = adc_value << 2
            
            return adc_value
            
        except Exception as e:
            raise DriverError(f"Erreur lecture ADC: {e}")
    
    
    def _raw_to_aqi(self, raw_value: int) -> int:
        """
        Convertit la valeur ADC brute en AQI
        
        Args:
            raw_value: Valeur ADC brute (0-4095)
            
        Returns:
            Valeur AQI (0-500)
        """
        # Conversion simple : mapping linéaire
        # 0-4095 ADC -> 0-500 AQI
        aqi = int((raw_value / self.max_value) * 500)
        return max(0, min(500, aqi))
    
    def _aqi_to_level(self, aqi: int) -> str:
        """
        Convertit l'AQI en niveau de qualité
        
        Args:
            aqi: Valeur AQI (0-500)
            
        Returns:
            Niveau de qualité d'air
        """
        if aqi <= self.aqi_thresholds["excellent"]:
            return "excellent"
        elif aqi <= self.aqi_thresholds["good"]:
            return "good"
        elif aqi <= self.aqi_thresholds["moderate"]:
            return "moderate"
        elif aqi <= self.aqi_thresholds["unhealthy"]:
            return "unhealthy"
        else:
            return "hazardous"
    
    def get_aqi(self) -> Optional[int]:
        """
        Retourne la dernière valeur AQI lue
        
        Returns:
            AQI ou None
        """
        return self.last_aqi
    
    def get_level(self) -> Optional[str]:
        """
        Retourne le dernier niveau de qualité lue
        
        Returns:
            Niveau de qualité ou None
        """
        if self.last_aqi is not None:
            return self._aqi_to_level(self.last_aqi)
        return None
    
    def set_thresholds(self, thresholds: Dict[str, int]) -> bool:
        """
        Met à jour les seuils de qualité d'air
        
        Args:
            thresholds: Nouveaux seuils
            
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            self.aqi_thresholds.update(thresholds)
            self.logger.info(f"Seuils qualité d'air mis à jour: {thresholds}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur mise à jour seuils: {e}")
            return False
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Le capteur de qualité d'air est en lecture seule
        
        Args:
            data: Données à écrire (ignorées)
            
        Returns:
            False (capteur en lecture seule)
        """
        self.logger.warning("Capteur qualité d'air est en lecture seule")
        return False
    
    def cleanup(self) -> None:
        """
        Nettoie les ressources du capteur
        """
        if hasattr(self, 'spi') and self.spi:
            try:
                self.spi.close()
            except:
                pass
        
        super().cleanup()
