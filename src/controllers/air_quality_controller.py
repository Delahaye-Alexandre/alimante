"""
Contrôleur pour la qualité de l'air
Gestion du capteur MQ2 avec convertisseur ADS1115 et contrôle des ventilateurs
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from ..utils.gpio_manager import GPIOManager
from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


class AirQualityController:
    """Contrôleur pour la qualité de l'air avec capteur MQ2 et ADS1115"""
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        self.logger = get_logger("air_quality_controller")
        self.gpio_manager = gpio_manager
        self.config = config
        
        # Configuration du capteur MQ2 avec ADS1115
        self.mq2_pin = config.get("pin", 22)  # I2C SDA
        self.i2c_address = config.get("i2c_address", "0x48")
        self.adc_channel = config.get("adc_channel", 0)
        self.voltage = config.get("voltage", "5.1V")
        self.current = config.get("current", 150)  # mA
        
        # Seuils de qualité de l'air (ppm)
        self.air_quality_thresholds = {
            "excellent": 0,      # 0-50 ppm
            "good": 50,          # 50-100 ppm
            "moderate": 100,     # 100-150 ppm
            "poor": 150,         # 150-200 ppm
            "unhealthy": 200,    # 200-300 ppm
            "very_unhealthy": 300 # 300+ ppm
        }
        
        # Configuration des ventilateurs
        self.fan_speed_levels = {
            "excellent": 0,      # Ventilateurs éteints
            "good": 25,          # 25% de vitesse
            "moderate": 50,      # 50% de vitesse
            "poor": 75,          # 75% de vitesse
            "unhealthy": 100,    # 100% de vitesse
            "very_unhealthy": 100 # 100% de vitesse + alerte
        }
        
        # État du contrôleur
        self.current_quality = "unknown"
        self.last_reading = None
        self.last_reading_time = None
        self.reading_count = 0
        self.error_count = 0
        
        # Configuration de lecture
        self.reading_interval = 30  # secondes
        self.calibration_time = 20  # secondes pour calibration
        self.is_calibrated = False
        self.baseline_value = None
        
        # Initialisation GPIO
        self._setup_gpio()
        
        self.logger.info("Contrôleur qualité de l'air initialisé")
    
    def _setup_gpio(self):
        """Configure le GPIO pour le capteur MQ2 avec ADS1115"""
        try:
            # Le MQ2 utilise l'ADS1115 via I2C, donc on configure les pins I2C
            # SDA (GPIO 22) et SCL (GPIO 3) sont configurés automatiquement par le système
            self.logger.info(f"Configuration I2C pour MQ2 + ADS1115 sur adresse {self.i2c_address}")
            self.logger.info(f"Pins I2C: SDA={self.mq2_pin}, SCL=3, Canal ADC={self.adc_channel}")
        except Exception as e:
            self.logger.error(f"Erreur configuration I2C MQ2: {e}")
            raise create_exception(
                ErrorCode.GPIO_SETUP_FAILED,
                f"Impossible de configurer l'I2C pour MQ2: {e}",
                {"i2c_address": self.i2c_address, "original_error": str(e)}
            )
    
    def calibrate_sensor(self) -> bool:
        """Calibre le capteur MQ2"""
        try:
            self.logger.info("Début de la calibration du capteur MQ2...")
            self.logger.info("Veuillez vous assurer que l'air ambiant est propre")
            
            readings = []
            start_time = time.time()
            
            # Lecture pendant 20 secondes pour établir une baseline
            while time.time() - start_time < self.calibration_time:
                reading = self._read_raw_sensor()
                if reading is not None:
                    readings.append(reading)
                time.sleep(1)
            
            if readings:
                self.baseline_value = sum(readings) / len(readings)
                self.is_calibrated = True
                self.logger.info(f"Calibration terminée. Baseline: {self.baseline_value:.2f}")
                return True
            else:
                self.logger.error("Aucune lecture valide pendant la calibration")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la calibration: {e}")
            return False
    
    def _read_raw_sensor(self) -> Optional[float]:
        """Lit la valeur brute du capteur MQ2 via ADS1115"""
        try:
            # Lecture via ADS1115 via I2C
            # import board
            # import adafruit_ads1x15.ads1115 as ADS
            # from adafruit_ads1x15.analog_in import AnalogIn
            
            # i2c = board.I2C()
            # ads = ADS.ADS1115(i2c, address=int(self.i2c_address, 16))
            # channel = AnalogIn(ads, getattr(ADS, f"P{self.adc_channel}"))
            # value = channel.value
            
            # Simulation temporaire pour MQ2 (détection LPG, propane, méthane, etc.)
            import random
            value = 200 + random.uniform(-50, 100)  # Simulation 150-300 ppm
            
            return value
            
        except Exception as e:
            self.logger.error(f"Erreur lecture capteur MQ2: {e}")
            return None
    
    def read_air_quality(self) -> Optional[Dict[str, Any]]:
        """Lit la qualité de l'air actuelle"""
        try:
            if not self.is_calibrated:
                self.logger.warning("Capteur non calibré, calibration automatique...")
                if not self.calibrate_sensor():
                    return None
            
            raw_value = self._read_raw_sensor()
            if raw_value is None:
                return None
            
            # Calculer la concentration en ppm (formule simplifiée)
            # ppm = (raw_value / baseline_value) * 100
            ppm = raw_value  # Simulation pour le moment
            
            # Déterminer la qualité de l'air
            quality_level = self._determine_quality_level(ppm)
            
            # Calculer la vitesse des ventilateurs
            fan_speed = self.fan_speed_levels.get(quality_level, 0)
            
            reading = {
                "ppm": ppm,
                "quality_level": quality_level,
                "fan_speed": fan_speed,
                "timestamp": datetime.now(),
                "raw_value": raw_value,
                "baseline": self.baseline_value
            }
            
            self.last_reading = reading
            self.last_reading_time = datetime.now()
            self.reading_count += 1
            
            self.logger.info(f"Qualité de l'air: {quality_level} ({ppm:.1f} ppm) - Ventilateurs: {fan_speed}%")
            
            return reading
            
        except Exception as e:
            self.logger.error(f"Erreur lecture qualité de l'air: {e}")
            self.error_count += 1
            return None
    
    def _determine_quality_level(self, ppm: float) -> str:
        """Détermine le niveau de qualité de l'air basé sur les ppm"""
        if ppm <= self.air_quality_thresholds["good"]:
            return "excellent"
        elif ppm <= self.air_quality_thresholds["moderate"]:
            return "good"
        elif ppm <= self.air_quality_thresholds["poor"]:
            return "moderate"
        elif ppm <= self.air_quality_thresholds["unhealthy"]:
            return "poor"
        elif ppm <= self.air_quality_thresholds["very_unhealthy"]:
            return "unhealthy"
        else:
            return "very_unhealthy"
    
    def control_ventilation(self, fan_controller=None) -> bool:
        """Contrôle la ventilation basée sur la qualité de l'air"""
        try:
            reading = self.read_air_quality()
            if reading is None:
                return False
            
            quality_level = reading["quality_level"]
            fan_speed = reading["fan_speed"]
            
            # Si on a un contrôleur de ventilateurs, ajuster la vitesse
            if fan_controller and hasattr(fan_controller, 'set_fan_speed'):
                success = fan_controller.set_fan_speed(fan_speed)
                if success:
                    self.logger.info(f"Ventilation ajustée: {fan_speed}% (qualité: {quality_level})")
                else:
                    self.logger.error("Échec de l'ajustement de la ventilation")
                    return False
            
            # Mettre à jour l'état
            self.current_quality = quality_level
            
            # Alerte si qualité très mauvaise
            if quality_level in ["unhealthy", "very_unhealthy"]:
                self.logger.warning(f"⚠️ Qualité de l'air dégradée: {quality_level} ({reading['ppm']:.1f} ppm)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle ventilation: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du contrôleur"""
        return {
            "controller": "air_quality",
            "sensor_type": "MQ2",
            "pin": self.mq2_pin,
            "voltage": self.voltage,
            "current_quality": self.current_quality,
            "is_calibrated": self.is_calibrated,
            "baseline_value": self.baseline_value,
            "last_reading": self.last_reading,
            "reading_count": self.reading_count,
            "error_count": self.error_count,
            "fan_speed_levels": self.fan_speed_levels,
            "air_quality_thresholds": self.air_quality_thresholds
        }
    
    def check_status(self) -> bool:
        """Vérifie le statut du contrôleur"""
        try:
            # Test de lecture
            reading = self.read_air_quality()
            if reading is None:
                return False
            
            # Vérifier que les valeurs sont dans des plages raisonnables
            ppm = reading.get("ppm", 0)
                    if ppm < 0 or ppm > 5000:  # Plage raisonnable pour MQ2 (LPG, propane, etc.)
            self.logger.warning(f"Valeur MQ2 suspecte: {ppm} ppm")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur vérification statut: {e}")
            return False
    
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.logger.info("Nettoyage du contrôleur qualité de l'air")
            # Pas de GPIO à nettoyer pour ce capteur
        except Exception as e:
            self.logger.error(f"Erreur nettoyage: {e}")
