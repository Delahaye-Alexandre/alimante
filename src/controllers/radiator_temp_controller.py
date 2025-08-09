"""
Contrôleur pour capteur de température du radiateur
Surveillance de sécurité pour éviter la surchauffe
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from ..utils.gpio_manager import GPIOManager
from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


class RadiatorTempController:
    """Contrôleur pour capteur de température DS18B20 du radiateur"""
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        self.logger = get_logger("radiator_temp_controller")
        self.gpio_manager = gpio_manager
        self.config = config
        
        # Configuration du capteur DS18B20
        self.sensor_pin = config.get("pin", 26)
        self.sensor_type = config.get("type", "DS18B20")
        self.sensor_address = config.get("address", "auto")
        self.voltage = config.get("voltage", "3.3V")
        self.current = config.get("current", 1)  # mA
        
        # État du contrôleur
        self.current_temperature = None
        self.last_measurement = None
        self.error_count = 0
        self.is_initialized = False
        self.device_path = None
        
        # Seuils de sécurité
        self.max_safe_temp = config.get("max_safe_temp", 80.0)  # °C - seuil critique
        self.warning_temp = config.get("warning_temp", 70.0)   # °C - seuil d'alerte
        self.min_temp = config.get("min_temp", -10.0)          # °C - température minimum valide
        self.max_temp = config.get("max_temp", 125.0)          # °C - température maximum valide
        
        # Historique et moyennage
        self.temperature_history = []
        self.history_size = 10
        
        # Configuration OneWire
        self.onewire_path = "/sys/bus/w1/devices/"
        
        # Initialisation
        self._setup_sensor()
        
        self.logger.info("Contrôleur température radiateur initialisé")
    
    def _setup_sensor(self):
        """Configure le capteur DS18B20"""
        try:
            # Activer le module OneWire si nécessaire
            self._enable_onewire()
            
            # Rechercher le capteur
            self._find_sensor()
            
            # Test de lecture
            test_temp = self._read_raw_temperature()
            if test_temp is not None:
                self.is_initialized = True
                self.logger.info(f"Capteur DS18B20 initialisé: {self.device_path}")
                self.logger.info(f"Température test: {test_temp:.2f}°C")
            else:
                raise Exception("Impossible de lire la température de test")
                
        except Exception as e:
            self.logger.exception("Erreur initialisation capteur DS18B20")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible d'initialiser le capteur de température radiateur",
                {"sensor_pin": self.sensor_pin, "original_error": str(e)}
            )
    
    def _enable_onewire(self):
        """Active le module OneWire"""
        try:
            import os
            
            # Charger les modules kernel si nécessaire
            os.system("sudo modprobe w1-gpio")
            os.system("sudo modprobe w1-therm")
            
            time.sleep(2)  # Attendre que les modules se chargent
            
        except Exception as e:
            self.logger.warning(f"Impossible de charger les modules OneWire: {e}")
    
    def _find_sensor(self):
        """Recherche le capteur DS18B20 sur le bus OneWire"""
        try:
            import os
            import glob
            
            if not os.path.exists(self.onewire_path):
                raise Exception("Bus OneWire non disponible")
            
            # Rechercher les capteurs DS18B20 (famille 28-*)
            sensor_paths = glob.glob(self.onewire_path + "28-*")
            
            if not sensor_paths:
                raise Exception("Aucun capteur DS18B20 trouvé")
            
            if self.sensor_address == "auto":
                # Prendre le premier capteur trouvé
                self.device_path = sensor_paths[0] + "/w1_slave"
                device_id = os.path.basename(sensor_paths[0])
                self.logger.info(f"Capteur DS18B20 auto-détecté: {device_id}")
            else:
                # Rechercher l'adresse spécifique
                target_path = self.onewire_path + self.sensor_address + "/w1_slave"
                if os.path.exists(target_path):
                    self.device_path = target_path
                    self.logger.info(f"Capteur DS18B20 trouvé: {self.sensor_address}")
                else:
                    raise Exception(f"Capteur {self.sensor_address} non trouvé")
                    
        except Exception as e:
            self.logger.error(f"Erreur recherche capteur DS18B20: {e}")
            raise
    
    def _read_raw_temperature(self) -> Optional[float]:
        """Lit la température brute du capteur DS18B20"""
        try:
            if not self.device_path:
                raise Exception("Capteur non configuré")
            
            # Lire le fichier du capteur
            with open(self.device_path, 'r') as f:
                lines = f.readlines()
            
            # Vérifier la validité de la lecture
            if len(lines) < 2:
                raise Exception("Données capteur incomplètes")
            
            if "YES" not in lines[0]:
                raise Exception("CRC invalide")
            
            # Extraire la température
            temp_line = lines[1]
            temp_index = temp_line.find("t=")
            if temp_index == -1:
                raise Exception("Format température invalide")
            
            temp_raw = temp_line[temp_index + 2:]
            temperature = float(temp_raw) / 1000.0  # Conversion millidegrés -> degrés
            
            # Vérifier la plage valide
            if not (self.min_temp <= temperature <= self.max_temp):
                raise Exception(f"Température hors limites: {temperature:.2f}°C")
            
            return temperature
            
        except Exception as e:
            self.logger.warning(f"Erreur lecture température: {e}")
            return None
    
    def read_temperature(self) -> Dict[str, Any]:
        """Lit la température du radiateur avec analyse de sécurité"""
        try:
            if not self.is_initialized:
                raise Exception("Capteur non initialisé")
            
            # Effectuer plusieurs lectures pour fiabilité
            temperatures = []
            for _ in range(3):
                temp = self._read_raw_temperature()
                if temp is not None:
                    temperatures.append(temp)
                time.sleep(0.2)
            
            if not temperatures:
                raise Exception("Aucune lecture valide obtenue")
            
            # Moyenner les lectures
            avg_temperature = sum(temperatures) / len(temperatures)
            
            # Mettre à jour l'état
            self.current_temperature = avg_temperature
            self.last_measurement = datetime.now()
            
            # Ajouter à l'historique
            self.temperature_history.append({
                "timestamp": self.last_measurement,
                "temperature": avg_temperature
            })
            
            # Limiter la taille de l'historique
            if len(self.temperature_history) > self.history_size:
                self.temperature_history.pop(0)
            
            # Analyser la sécurité
            safety_status = self._analyze_safety(avg_temperature)
            
            result = {
                "temperature": round(avg_temperature, 2),
                "safety_status": safety_status,
                "measurements_count": len(temperatures),
                "timestamp": self.last_measurement.isoformat(),
                "thresholds": {
                    "warning": self.warning_temp,
                    "critical": self.max_safe_temp
                }
            }
            
            # Log selon le niveau de criticité
            if safety_status == "CRITICAL":
                self.logger.error(f"TEMPÉRATURE RADIATEUR CRITIQUE: {avg_temperature:.2f}°C")
            elif safety_status == "WARNING":
                self.logger.warning(f"Température radiateur élevée: {avg_temperature:.2f}°C")
            else:
                self.logger.debug(f"Température radiateur: {avg_temperature:.2f}°C")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur lecture température radiateur")
            raise create_exception(
                ErrorCode.SENSOR_READ_FAILED,
                "Impossible de lire la température du radiateur",
                {"original_error": str(e)}
            )
    
    def _analyze_safety(self, temperature: float) -> str:
        """Analyse la sécurité selon la température"""
        if temperature >= self.max_safe_temp:
            return "CRITICAL"
        elif temperature >= self.warning_temp:
            return "WARNING"
        else:
            return "SAFE"
    
    def is_safe_temperature(self) -> bool:
        """Vérifie si la température est dans une plage sûre"""
        try:
            temp_info = self.read_temperature()
            return temp_info["safety_status"] != "CRITICAL"
        except Exception:
            return False
    
    def get_temperature_trend(self) -> str:
        """Analyse la tendance de température"""
        if len(self.temperature_history) < 3:
            return "UNKNOWN"
        
        recent_temps = [m["temperature"] for m in self.temperature_history[-3:]]
        
        if recent_temps[-1] > recent_temps[0] + 2:
            return "RISING"
        elif recent_temps[-1] < recent_temps[0] - 2:
            return "FALLING"
        else:
            return "STABLE"
    
    def emergency_check(self) -> Dict[str, Any]:
        """Vérification d'urgence rapide"""
        try:
            temp = self._read_raw_temperature()
            if temp is None:
                return {"status": "ERROR", "action": "SENSOR_FAULT"}
            
            if temp >= self.max_safe_temp:
                return {
                    "status": "CRITICAL", 
                    "temperature": temp,
                    "action": "SHUTDOWN_RADIATOR"
                }
            
            return {"status": "OK", "temperature": temp}
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e), "action": "SENSOR_FAULT"}
    
    def get_status(self) -> Dict[str, Any]:
        """Récupère le statut complet du contrôleur"""
        try:
            return {
                "status": "ok" if self.error_count < 5 else "error",
                "sensor_type": self.sensor_type,
                "is_initialized": self.is_initialized,
                "current_temperature": self.current_temperature,
                "last_measurement": self.last_measurement.isoformat() if self.last_measurement else None,
                "error_count": self.error_count,
                "safety_thresholds": {
                    "warning": self.warning_temp,
                    "critical": self.max_safe_temp
                },
                "trend": self.get_temperature_trend(),
                "device_path": self.device_path,
                "config": {
                    "sensor_pin": self.sensor_pin,
                    "sensor_address": self.sensor_address
                }
            }
            
        except Exception as e:
            self.logger.exception("Erreur récupération statut température radiateur")
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
            self.logger.exception("Erreur vérification statut température radiateur")
            return False
    
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.is_initialized = False
            self.logger.info("Contrôleur température radiateur nettoyé")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage température radiateur: {e}")
