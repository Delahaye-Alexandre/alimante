"""
Contrôleur pour les ventilateurs de ventilation
Gestion de la ventilation et du refroidissement
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from ..utils.gpio_manager import GPIOManager
from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


class FanController:
    """Contrôleur pour les ventilateurs de ventilation"""
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        self.logger = get_logger("fan_controller")
        self.gpio_manager = gpio_manager
        self.config = config
        
        # Configuration des ventilateurs
        self.fan_count = config.get("count", 4)
        self.voltage = config.get("voltage", "5V")
        self.current_per_fan = config.get("current_per_fan", 200)  # mA
        self.total_current = config.get("total_current", 800)  # mA
        
        # Récupérer le pin depuis la configuration GPIO
        from ..services.gpio_config_service import GPIOConfigService
        gpio_service = GPIOConfigService()
        self.fan_relay_pin = gpio_service.get_actuator_pin('fan_relay')
        if self.fan_relay_pin is None:
            self.fan_relay_pin = gpio_service.get_pin_assignment('FAN_RELAY_PIN')
        
        # État des ventilateurs
        self.fans_active = False
        self.last_activation = None
        self.total_runtime = 0
        self.error_count = 0
        
        # Configuration de contrôle
        self.auto_mode = True
        self.temperature_threshold = 28.0  # °C
        self.humidity_threshold = 80.0  # %
        self.min_runtime = 30  # secondes
        self.max_runtime = 3600  # secondes (1 heure)
        
        # Configuration de vitesse des ventilateurs
        self.current_speed = 0  # 0-100%
        self.speed_levels = {
            "low": 25,      # 25% de vitesse
            "medium": 50,   # 50% de vitesse
            "high": 75,     # 75% de vitesse
            "max": 100      # 100% de vitesse
        }
        
        # Initialisation GPIO
        self._setup_gpio()
        
        self.logger.info(f"Contrôleur ventilateurs initialisé: {self.fan_count} ventilateurs")
    
    def _setup_gpio(self):
        """Configure les pins GPIO"""
        try:
            # Configurer le pin du relais des ventilateurs
            self.gpio_manager.setup_pin(self.fan_relay_pin, "OUT")
            self.gpio_manager.write_pin(self.fan_relay_pin, False)  # Éteint par défaut
            
            self.logger.info(f"GPIO ventilateurs configuré: pin {self.fan_relay_pin}")
            
        except Exception as e:
            self.logger.exception("Erreur configuration GPIO ventilateurs")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible de configurer les ventilateurs",
                {"relay_pin": self.fan_relay_pin, "original_error": str(e)}
            )
    
    def activate_fans(self) -> bool:
        """Active tous les ventilateurs"""
        try:
            if not self.fans_active:
                self.gpio_manager.write_pin(self.fan_relay_pin, True)
                self.fans_active = True
                self.last_activation = datetime.now()
                
                self.logger.info("Ventilateurs activés", {
                    "fan_count": self.fan_count,
                    "total_current": f"{self.total_current}mA",
                    "voltage": self.voltage,
                    "speed": f"{self.current_speed}%"
                })
                
                return True
            else:
                self.logger.debug("Ventilateurs déjà actifs")
                return True
                
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur activation ventilateurs")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible d'activer les ventilateurs",
                {"original_error": str(e)}
            )
    
    def deactivate_fans(self) -> bool:
        """Désactive tous les ventilateurs"""
        try:
            if self.fans_active:
                self.gpio_manager.write_pin(self.fan_relay_pin, False)
                self.fans_active = False
                self.current_speed = 0
                
                # Calculer le temps de fonctionnement
                if self.last_activation:
                    runtime = (datetime.now() - self.last_activation).total_seconds()
                    self.total_runtime += runtime
                
                self.logger.info("Ventilateurs désactivés", {
                    "runtime_seconds": runtime if self.last_activation else 0,
                    "total_runtime_hours": self.total_runtime / 3600
                })
                
                return True
            else:
                self.logger.debug("Ventilateurs déjà inactifs")
                return True
                
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur désactivation ventilateurs")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible de désactiver les ventilateurs",
                {"original_error": str(e)}
            )
    
    def control_ventilation(self, temperature: float, humidity: float) -> bool:
        """Contrôle automatique de la ventilation"""
        try:
            if not self.auto_mode:
                self.logger.debug("Mode automatique désactivé")
                return True
            
            # Logique de contrôle
            should_activate = False
            
            # Activation basée sur la température
            if temperature > self.temperature_threshold:
                should_activate = True
                self.logger.info(f"Activation ventilateurs: température élevée ({temperature}°C)")
            
            # Activation basée sur l'humidité
            if humidity > self.humidity_threshold:
                should_activate = True
                self.logger.info(f"Activation ventilateurs: humidité élevée ({humidity}%)")
            
            # Vérifier le temps de fonctionnement minimum
            if self.fans_active and self.last_activation:
                runtime = (datetime.now() - self.last_activation).total_seconds()
                if runtime < self.min_runtime:
                    should_activate = True
                    self.logger.debug(f"Ventilateurs maintenus actifs: temps minimum ({runtime}s)")
            
            # Vérifier le temps de fonctionnement maximum
            if self.fans_active and self.last_activation:
                runtime = (datetime.now() - self.last_activation).total_seconds()
                if runtime > self.max_runtime:
                    should_activate = False
                    self.logger.info(f"Désactivation ventilateurs: temps maximum atteint ({runtime}s)")
            
            # Appliquer la décision
            if should_activate and not self.fans_active:
                return self.activate_fans()
            elif not should_activate and self.fans_active:
                return self.deactivate_fans()
            else:
                return True
                
        except Exception as e:
            self.logger.exception("Erreur contrôle automatique ventilation")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Erreur contrôle automatique ventilation",
                {"original_error": str(e)}
            )
    
    def set_auto_mode(self, enabled: bool) -> bool:
        """Active/désactive le mode automatique"""
        self.auto_mode = enabled
        self.logger.info(f"Mode automatique ventilateurs: {'activé' if enabled else 'désactivé'}")
        return True
    
    def set_temperature_threshold(self, threshold: float) -> bool:
        """Définit le seuil de température"""
        if 15.0 <= threshold <= 40.0:
            self.temperature_threshold = threshold
            self.logger.info(f"Seuil température ventilateurs: {threshold}°C")
            return True
        else:
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Seuil de température invalide",
                {"threshold": threshold, "valid_range": "15.0-40.0"}
            )
    
    def set_humidity_threshold(self, threshold: float) -> bool:
        """Définit le seuil d'humidité"""
        if 30.0 <= threshold <= 95.0:
            self.humidity_threshold = threshold
            self.logger.info(f"Seuil humidité ventilateurs: {threshold}%")
            return True
        else:
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Seuil d'humidité invalide",
                {"threshold": threshold, "valid_range": "30.0-95.0"}
            )
    
    def set_fan_speed(self, speed_percent: int) -> bool:
        """Définit la vitesse des ventilateurs (0-100%)"""
        try:
            if not 0 <= speed_percent <= 100:
                self.logger.error(f"Vitesse invalide: {speed_percent}%")
                return False
            
            self.current_speed = speed_percent
            
            # Activer/désactiver selon la vitesse
            if speed_percent > 0:
                if not self.fans_active:
                    self.activate_fans()
                self.logger.info(f"Vitesse ventilateurs: {speed_percent}%")
            else:
                if self.fans_active:
                    self.deactivate_fans()
                self.logger.info("Ventilateurs éteints")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour vitesse ventilateurs: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Récupère le statut du contrôleur"""
        try:
            runtime = 0
            if self.fans_active and self.last_activation:
                runtime = (datetime.now() - self.last_activation).total_seconds()
            
            return {
                "status": "ok" if self.error_count == 0 else "error",
                "fans_active": self.fans_active,
                "auto_mode": self.auto_mode,
                "fan_count": self.fan_count,
                "current_runtime": runtime,
                "total_runtime": self.total_runtime,
                "temperature_threshold": self.temperature_threshold,
                "humidity_threshold": self.humidity_threshold,
                "current_speed": self.current_speed,
                "error_count": self.error_count,
                "voltage": self.voltage,
                "total_current_ma": self.total_current,
                "last_activation": self.last_activation.isoformat() if self.last_activation else None
            }
            
        except Exception as e:
            self.logger.exception("Erreur récupération statut ventilateurs")
            return {
                "status": "error",
                "error": str(e),
                "fans_active": False
            }
    
    def check_status(self) -> bool:
        """Vérifie le statut du contrôleur"""
        try:
            # Vérifier que le GPIO fonctionne
            current_state = self.gpio_manager.read_pin(self.fan_relay_pin)
            
            # Vérifier la cohérence
            if self.fans_active != current_state:
                self.logger.warning("Incohérence état ventilateurs détectée")
                return False
            
            return self.error_count < 5
            
        except Exception as e:
            self.logger.exception("Erreur vérification statut ventilateurs")
            return False
    
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.deactivate_fans()
            self.logger.info("Contrôleur ventilateurs nettoyé")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage ventilateurs: {e}")
