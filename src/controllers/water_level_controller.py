"""
Contrôleur pour capteur de niveau d'eau
Gestion du niveau d'eau du réservoir pour le brumisateur
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from ..utils.gpio_manager import GPIOManager
from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


class WaterLevelController:
    """Contrôleur pour capteur de niveau d'eau HC-SR04P"""
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        self.logger = get_logger("water_level_controller")
        self.gpio_manager = gpio_manager
        self.config = config
        
        # Configuration du capteur ultrasonique
        self.trigger_pin = config.get("trigger_pin", 20)
        self.echo_pin = config.get("echo_pin", 21)
        self.sensor_type = config.get("type", "HC-SR04P")
        self.voltage = config.get("voltage", "3.3V")
        self.current = config.get("current", 15)  # mA
        
        # Configuration de mesure
        self.min_distance = config.get("min_distance", 5)  # cm - distance minimum fiable
        self.max_distance = config.get("max_distance", 30)  # cm - distance maximum réservoir
        self.reservoir_height = config.get("reservoir_height", 25)  # cm - hauteur totale réservoir
        
        # État du contrôleur
        self.current_distance = None
        self.current_level = None
        self.level_percentage = 0
        self.last_measurement = None
        self.error_count = 0
        self.is_initialized = False
        
        # Seuils d'alerte
        self.low_level_threshold = config.get("low_level_threshold", 20)  # % - niveau bas
        self.critical_level_threshold = config.get("critical_level_threshold", 5)  # % - niveau critique
        
        # Historique et moyennage
        self.measurement_history = []
        self.history_size = 5  # Nombre de mesures pour moyennage
        
        # Initialisation GPIO
        self._setup_gpio()
        
        self.logger.info("Contrôleur niveau d'eau initialisé")
    
    def _setup_gpio(self):
        """Configure les pins GPIO pour le capteur ultrasonique"""
        try:
            # Configuration trigger (sortie)
            self.gpio_manager.setup_pin(self.trigger_pin, "OUT")
            self.gpio_manager.write_pin(self.trigger_pin, False)
            
            # Configuration echo (entrée)
            self.gpio_manager.setup_pin(self.echo_pin, "IN")
            
            self.is_initialized = True
            self.logger.info(f"GPIO capteur niveau configuré: trigger={self.trigger_pin}, echo={self.echo_pin}")
            
        except Exception as e:
            self.logger.exception("Erreur configuration GPIO capteur niveau")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible de configurer le capteur de niveau d'eau",
                {"trigger_pin": self.trigger_pin, "echo_pin": self.echo_pin, "original_error": str(e)}
            )
    
    def _measure_distance(self) -> Optional[float]:
        """Mesure la distance avec le capteur ultrasonique"""
        try:
            import RPi.GPIO as GPIO
            
            # Envoyer impulsion trigger (10µs)
            self.gpio_manager.write_pin(self.trigger_pin, True)
            time.sleep(0.00001)  # 10µs
            self.gpio_manager.write_pin(self.trigger_pin, False)
            
            # Mesurer le temps de l'écho
            start_time = time.time()
            timeout = start_time + 0.1  # Timeout 100ms
            
            # Attendre le début de l'écho (front montant)
            while self.gpio_manager.read_pin(self.echo_pin) == 0:
                start_time = time.time()
                if start_time > timeout:
                    raise Exception("Timeout début écho")
            
            # Attendre la fin de l'écho (front descendant)
            while self.gpio_manager.read_pin(self.echo_pin) == 1:
                end_time = time.time()
                if end_time > timeout:
                    raise Exception("Timeout fin écho")
            
            # Calculer la distance
            pulse_duration = end_time - start_time
            distance = (pulse_duration * 34300) / 2  # Vitesse son = 343 m/s
            
            # Vérifier la validité de la mesure
            if self.min_distance <= distance <= self.max_distance:
                return distance
            else:
                self.logger.warning(f"Distance hors limites: {distance:.2f}cm")
                return None
                
        except Exception as e:
            self.logger.warning(f"Erreur mesure distance: {e}")
            return None
    
    def read_water_level(self) -> Dict[str, Any]:
        """Lit le niveau d'eau et retourne les informations complètes"""
        try:
            if not self.is_initialized:
                raise Exception("Capteur non initialisé")
            
            # Effectuer plusieurs mesures pour moyennage
            distances = []
            for _ in range(3):
                distance = self._measure_distance()
                if distance is not None:
                    distances.append(distance)
                time.sleep(0.1)  # Pause entre mesures
            
            if not distances:
                raise Exception("Aucune mesure valide obtenue")
            
            # Moyenner les mesures
            avg_distance = sum(distances) / len(distances)
            
            # Calculer le niveau d'eau
            water_level = self.reservoir_height - avg_distance
            water_level = max(0, water_level)  # Pas de niveau négatif
            
            # Calculer le pourcentage
            level_percentage = (water_level / self.reservoir_height) * 100
            level_percentage = max(0, min(100, level_percentage))
            
            # Mettre à jour l'état
            self.current_distance = avg_distance
            self.current_level = water_level
            self.level_percentage = level_percentage
            self.last_measurement = datetime.now()
            
            # Ajouter à l'historique
            self.measurement_history.append({
                "timestamp": self.last_measurement,
                "distance": avg_distance,
                "level": water_level,
                "percentage": level_percentage
            })
            
            # Limiter la taille de l'historique
            if len(self.measurement_history) > self.history_size:
                self.measurement_history.pop(0)
            
            # Déterminer le statut
            status = self._determine_status(level_percentage)
            
            result = {
                "distance_cm": round(avg_distance, 2),
                "water_level_cm": round(water_level, 2),
                "level_percentage": round(level_percentage, 1),
                "status": status,
                "measurements_count": len(distances),
                "timestamp": self.last_measurement.isoformat()
            }
            
            self.logger.debug(f"Niveau d'eau: {level_percentage:.1f}% ({water_level:.1f}cm)")
            return result
            
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur lecture niveau d'eau")
            raise create_exception(
                ErrorCode.SENSOR_READ_FAILED,
                "Impossible de lire le niveau d'eau",
                {"original_error": str(e)}
            )
    
    def _determine_status(self, percentage: float) -> str:
        """Détermine le statut selon le niveau d'eau"""
        if percentage <= self.critical_level_threshold:
            return "CRITICAL"
        elif percentage <= self.low_level_threshold:
            return "LOW"
        elif percentage >= 80:
            return "FULL"
        else:
            return "OK"
    
    def is_water_available(self) -> bool:
        """Vérifie si suffisamment d'eau est disponible"""
        try:
            level_info = self.read_water_level()
            return level_info["level_percentage"] > self.critical_level_threshold
        except Exception:
            return False
    
    def get_level_trend(self) -> str:
        """Analyse la tendance du niveau d'eau"""
        if len(self.measurement_history) < 3:
            return "UNKNOWN"
        
        recent_levels = [m["percentage"] for m in self.measurement_history[-3:]]
        
        if recent_levels[-1] > recent_levels[0] + 5:
            return "RISING"
        elif recent_levels[-1] < recent_levels[0] - 5:
            return "FALLING"
        else:
            return "STABLE"
    
    def get_status(self) -> Dict[str, Any]:
        """Récupère le statut complet du contrôleur"""
        try:
            return {
                "status": "ok" if self.error_count < 5 else "error",
                "sensor_type": self.sensor_type,
                "is_initialized": self.is_initialized,
                "current_distance": self.current_distance,
                "current_level": self.current_level,
                "level_percentage": self.level_percentage,
                "last_measurement": self.last_measurement.isoformat() if self.last_measurement else None,
                "error_count": self.error_count,
                "low_threshold": self.low_level_threshold,
                "critical_threshold": self.critical_level_threshold,
                "trend": self.get_level_trend(),
                "config": {
                    "trigger_pin": self.trigger_pin,
                    "echo_pin": self.echo_pin,
                    "reservoir_height": self.reservoir_height,
                    "min_distance": self.min_distance,
                    "max_distance": self.max_distance
                }
            }
            
        except Exception as e:
            self.logger.exception("Erreur récupération statut niveau d'eau")
            return {
                "status": "error",
                "error": str(e),
                "is_initialized": False
            }
    
    def check_status(self) -> bool:
        """Vérifie le statut du contrôleur"""
        try:
            return self.is_initialized and self.error_count < 5
        except Exception as e:
            self.logger.exception("Erreur vérification statut niveau d'eau")
            return False
    
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.is_initialized = False
            self.logger.info("Contrôleur niveau d'eau nettoyé")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage niveau d'eau: {e}")
