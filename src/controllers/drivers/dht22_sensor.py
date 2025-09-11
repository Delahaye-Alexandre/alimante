"""
Driver pour le capteur de température et d'humidité DHT22
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

class DHT22Sensor(BaseDriver):
    """
    Driver pour le capteur DHT22 (température et humidité)
    """
    
    def __init__(self, config: DriverConfig, gpio_pin: int):
        """
        Initialise le capteur DHT22
        
        Args:
            config: Configuration du driver
            gpio_pin: Pin GPIO connecté au capteur
        """
        super().__init__(config)
        self.gpio_pin = gpio_pin
        self.last_temperature = None
        self.last_humidity = None
        self.last_read_time = None
        
        # Configuration DHT22
        self.read_timeout = 0.1  # 100ms timeout
        self.retry_delay = 2.0   # 2s entre les lectures
        
    def initialize(self) -> bool:
        """
        Initialise le capteur DHT22
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.config.enabled:
                self.state = DriverState.DISABLED
                return True
            
            if not RASPBERRY_PI:
                self.logger.error("DHT22 nécessite un Raspberry Pi - pas de simulation")
                self.state = DriverState.ERROR
                return False
                
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            GPIO.output(self.gpio_pin, GPIO.HIGH)
            time.sleep(0.1)
            
            self.state = DriverState.READY
            self.logger.info(f"DHT22 initialisé sur pin {self.gpio_pin}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation DHT22: {e}")
            self.state = DriverState.ERROR
            return False
    
    def read(self) -> Dict[str, Any]:
        """
        Lit la température et l'humidité du DHT22
        
        Returns:
            Dictionnaire contenant temperature, humidity, timestamp
        """
        if not self.is_ready():
            raise DriverError("DHT22 non initialisé")
        
        # Vérifier le délai minimum entre les lectures
        if self.last_read_time and (time.time() - self.last_read_time) < self.retry_delay:
            return {
                "temperature": self.last_temperature,
                "humidity": self.last_humidity,
                "timestamp": self.last_read_time,
                "cached": True
            }
        
        if not RASPBERRY_PI:
            raise DriverError("DHT22 nécessite un Raspberry Pi - pas de simulation")
        
        temperature, humidity = self._read_dht22_hardware()
        
        # Appliquer la calibration
        if self.config.calibration:
            temp_offset = self.config.calibration.get("temperature_offset", 0.0)
            hum_offset = self.config.calibration.get("humidity_offset", 0.0)
            temperature += temp_offset
            humidity += hum_offset
        
        # Valider les valeurs
        if not self._validate_values(temperature, humidity):
            raise DriverError(f"Valeurs invalides: T={temperature}°C, H={humidity}%")
        
        # Mettre à jour les valeurs
        self.last_temperature = temperature
        self.last_humidity = humidity
        self.last_read_time = time.time()
        
        return {
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": self.last_read_time,
            "cached": False,
            "sensor": "dht22",
            "unit_temperature": "celsius",
            "unit_humidity": "percent"
        }
    
    def _read_dht22_hardware(self) -> tuple[float, float]:
        """
        Lecture réelle du DHT22 sur Raspberry Pi
        
        Returns:
            Tuple (temperature, humidity)
        """
        try:
            # Signal de démarrage
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            GPIO.output(self.gpio_pin, GPIO.LOW)
            time.sleep(0.018)  # 18ms
            
            # Passage en mode lecture
            GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Attendre la réponse du capteur
            timeout_start = time.time()
            while GPIO.input(self.gpio_pin) == GPIO.HIGH:
                if time.time() - timeout_start > self.read_timeout:
                    raise DriverError("Timeout DHT22")
            
            # Lire les 40 bits de données
            data = []
            for _ in range(40):
                # Attendre le front montant
                timeout_start = time.time()
                while GPIO.input(self.gpio_pin) == GPIO.LOW:
                    if time.time() - timeout_start > self.read_timeout:
                        raise DriverError("Timeout DHT22 front montant")
                
                # Mesurer la durée du niveau haut
                high_start = time.time()
                while GPIO.input(self.gpio_pin) == GPIO.HIGH:
                    if time.time() - timeout_start > self.read_timeout:
                        raise DriverError("Timeout DHT22 niveau haut")
                
                high_duration = time.time() - high_start
                data.append(1 if high_duration > 0.00005 else 0)  # 50µs seuil
            
            # Vérifier le checksum
            if not self._verify_checksum(data):
                raise DriverError("Checksum DHT22 invalide")
            
            # Convertir les données
            humidity = self._bits_to_value(data[0:16]) / 10.0
            temperature = self._bits_to_value(data[16:32]) / 10.0
            
            # Gérer le bit de signe pour la température
            if data[16] == 1:
                temperature = -temperature
            
            return temperature, humidity
            
        except Exception as e:
            raise DriverError(f"Erreur lecture DHT22: {e}")
    
    
    def _bits_to_value(self, bits: list) -> int:
        """
        Convertit une liste de bits en valeur entière
        
        Args:
            bits: Liste de bits (0 ou 1)
            
        Returns:
            Valeur entière
        """
        value = 0
        for bit in bits:
            value = (value << 1) | bit
        return value
    
    def _verify_checksum(self, data: list) -> bool:
        """
        Vérifie le checksum des données DHT22
        
        Args:
            data: Liste de 40 bits
            
        Returns:
            True si le checksum est valide, False sinon
        """
        if len(data) != 40:
            return False
        
        # Calculer le checksum (8 premiers bits des 5 octets)
        checksum = 0
        for i in range(0, 32, 8):
            byte_value = self._bits_to_value(data[i:i+8])
            checksum += byte_value
        
        # Vérifier avec le checksum reçu
        received_checksum = self._bits_to_value(data[32:40])
        return (checksum & 0xFF) == received_checksum
    
    def _validate_values(self, temperature: float, humidity: float) -> bool:
        """
        Valide les valeurs lues du DHT22
        
        Args:
            temperature: Température en °C
            humidity: Humidité en %
            
        Returns:
            True si les valeurs sont valides, False sinon
        """
        # Plages de validité DHT22
        temp_min, temp_max = -40.0, 80.0
        hum_min, hum_max = 0.0, 100.0
        
        return (temp_min <= temperature <= temp_max and 
                hum_min <= humidity <= hum_max)
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Le DHT22 est un capteur en lecture seule
        
        Args:
            data: Données à écrire (ignorées)
            
        Returns:
            False (capteur en lecture seule)
        """
        self.logger.warning("DHT22 est un capteur en lecture seule")
        return False
    
    def get_temperature(self) -> Optional[float]:
        """
        Retourne la dernière température lue
        
        Returns:
            Température en °C ou None
        """
        return self.last_temperature
    
    def get_humidity(self) -> Optional[float]:
        """
        Retourne la dernière humidité lue
        
        Returns:
            Humidité en % ou None
        """
        return self.last_humidity
    
    def cleanup(self) -> None:
        """
        Nettoie les ressources du DHT22
        """
        if RASPBERRY_PI and self.gpio_pin:
            try:
                GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
            except:
                pass
        
        super().cleanup()
