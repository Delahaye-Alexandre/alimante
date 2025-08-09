"""
Contrôleur pour le brumisateur à ultrasons
Gestion de l'humidification par transducteur ultrasonique
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from ..utils.gpio_manager import GPIOManager
from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


class UltrasonicMistController:
    """Contrôleur pour le brumisateur à ultrasons"""
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        self.logger = get_logger("ultrasonic_mist_controller")
        self.gpio_manager = gpio_manager
        self.config = config
        
        # Configuration du transducteur ultrasonique
        self.mist_pin = config.get("pin", 22)
        self.voltage = config.get("voltage", "12V")  # Transducteurs ultrasoniques fonctionnent souvent en 12V
        self.current = config.get("current", 100)  # mA - plus élevé que buzzer
        self.frequency = config.get("frequency", 1700000)  # 1.7MHz typique pour brumisateur
        self.power_watts = config.get("power_watts", 24)  # Puissance typique
        
        # État du brumisateur
        self.mist_active = False
        self.last_activation = None
        self.total_usage_time = 0
        self.error_count = 0
        self.mist_intensity = 50  # 0-100%
        
        # Configuration des modes d'humidification
        self.mist_modes = {
            "light": {"duration": 30, "intensity": 30, "description": "Humidification légère"},
            "medium": {"duration": 60, "intensity": 60, "description": "Humidification moyenne"},
            "heavy": {"duration": 120, "intensity": 100, "description": "Humidification forte"},
            "continuous": {"duration": 0, "intensity": 50, "description": "Humidification continue"}
        }
        
        # Sécurité
        self.max_continuous_time = 300  # 5 minutes max en continu
        self.cooldown_time = 60  # 1 minute de pause entre activations
        
        # Initialisation GPIO
        self._setup_gpio()
        
        self.logger.info("Contrôleur brumisateur ultrasonique initialisé")
    
    def _setup_gpio(self):
        """Configure les pins GPIO"""
        try:
            # Configurer le pin du transducteur ultrasonique
            self.gpio_manager.setup_pin(self.mist_pin, "OUT")
            self.gpio_manager.write_pin(self.mist_pin, False)  # Éteint par défaut
            
            self.logger.info(f"GPIO brumisateur configuré: pin {self.mist_pin}")
            
        except Exception as e:
            self.logger.exception("Erreur configuration GPIO brumisateur")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible de configurer le brumisateur ultrasonique",
                {"mist_pin": self.mist_pin, "original_error": str(e)}
            )
    
    def activate_mist(self, intensity: int = 50, duration: Optional[float] = None) -> bool:
        """Active le brumisateur ultrasonique"""
        try:
            if self.mist_active:
                self.logger.debug("Brumisateur déjà actif")
                return True
            
            # Vérifier l'intensité
            intensity = max(0, min(100, intensity))
            
            # Vérifier le temps de pause si nécessaire
            if self.last_activation:
                time_since_last = (datetime.now() - self.last_activation).total_seconds()
                if time_since_last < self.cooldown_time:
                    remaining = self.cooldown_time - time_since_last
                    self.logger.warning(f"Pause de sécurité requise: {remaining:.1f}s restantes")
                    return False
            
            # Activer le transducteur
            self.gpio_manager.write_pin(self.mist_pin, True)
            self.mist_active = True
            self.mist_intensity = intensity
            self.last_activation = datetime.now()
            
            self.logger.info("Brumisateur ultrasonique activé", {
                "intensity": f"{intensity}%",
                "duration": f"{duration}s" if duration else "continue",
                "voltage": self.voltage,
                "power_watts": self.power_watts
            })
            
            # Si une durée est spécifiée, arrêter après
            if duration and duration > 0:
                time.sleep(duration)
                return self.deactivate_mist()
            
            return True
                
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur activation brumisateur")
            raise create_exception(
                ErrorCode.CONTROLLER_CONTROL_FAILED,
                "Impossible d'activer le brumisateur ultrasonique",
                {"original_error": str(e)}
            )
    
    def deactivate_mist(self) -> bool:
        """Désactive le brumisateur ultrasonique"""
        try:
            if not self.mist_active:
                self.logger.debug("Brumisateur déjà inactif")
                return True
            
            self.gpio_manager.write_pin(self.mist_pin, False)
            self.mist_active = False
            
            # Calculer le temps d'utilisation
            if self.last_activation:
                usage_time = (datetime.now() - self.last_activation).total_seconds()
                self.total_usage_time += usage_time
                
                self.logger.info("Brumisateur désactivé", {
                    "usage_time": usage_time,
                    "total_usage_hours": self.total_usage_time / 3600,
                    "last_intensity": self.mist_intensity
                })
            
            return True
                
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur désactivation brumisateur")
            raise create_exception(
                ErrorCode.CONTROLLER_CONTROL_FAILED,
                "Impossible de désactiver le brumisateur ultrasonique",
                {"original_error": str(e)}
            )
    
    def set_mist_intensity(self, intensity: int) -> bool:
        """Ajuste l'intensité du brumisateur (0-100%)"""
        try:
            intensity = max(0, min(100, intensity))
            
            if self.mist_active:
                self.mist_intensity = intensity
                self.logger.info(f"Intensité brumisateur ajustée: {intensity}%")
                return True
            else:
                self.logger.warning("Brumisateur inactif, impossible d'ajuster l'intensité")
                return False
                
        except Exception as e:
            self.logger.exception("Erreur ajustement intensité")
            raise create_exception(
                ErrorCode.CONTROLLER_CONTROL_FAILED,
                "Impossible d'ajuster l'intensité du brumisateur",
                {"original_error": str(e)}
            )
    
    def run_mist_mode(self, mode: str) -> bool:
        """Exécute un mode d'humidification prédéfini"""
        try:
            if mode not in self.mist_modes:
                raise create_exception(
                    ErrorCode.CONTROLLER_CONTROL_FAILED,
                    f"Mode d'humidification inconnu: {mode}",
                    {"available_modes": list(self.mist_modes.keys())}
                )
            
            config = self.mist_modes[mode]
            
            self.logger.info(f"Exécution mode humidification: {mode}", config)
            
            # Activer avec les paramètres du mode
            return self.activate_mist(
                intensity=config["intensity"],
                duration=config["duration"] if config["duration"] > 0 else None
            )
            
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Erreur mode humidification {mode}")
            raise create_exception(
                ErrorCode.CONTROLLER_CONTROL_FAILED,
                f"Impossible d'exécuter le mode {mode}",
                {"original_error": str(e)}
            )
    
    def emergency_stop(self) -> bool:
        """Arrêt d'urgence du brumisateur"""
        try:
            self.logger.warning("Arrêt d'urgence du brumisateur ultrasonique")
            return self.deactivate_mist()
            
        except Exception as e:
            self.logger.exception("Erreur arrêt d'urgence")
            return False
    
    def add_mist_mode(self, name: str, config: Dict[str, Any]) -> bool:
        """Ajoute un nouveau mode d'humidification"""
        try:
            required_keys = ["duration", "intensity", "description"]
            if not all(key in config for key in required_keys):
                raise create_exception(
                    ErrorCode.CONTROLLER_CONTROL_FAILED,
                    "Configuration de mode incomplète",
                    {"required_keys": required_keys, "provided_keys": list(config.keys())}
                )
            
            self.mist_modes[name] = config
            self.logger.info(f"Nouveau mode d'humidification ajouté: {name}")
            return True
            
        except Exception as e:
            self.logger.exception(f"Erreur ajout mode {name}")
            raise create_exception(
                ErrorCode.CONTROLLER_CONTROL_FAILED,
                f"Impossible d'ajouter le mode {name}",
                {"original_error": str(e)}
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Récupère le statut du contrôleur"""
        try:
            usage_time = 0
            if self.mist_active and self.last_activation:
                usage_time = (datetime.now() - self.last_activation).total_seconds()
            
            return {
                "status": "ok" if self.error_count == 0 else "error",
                "mist_active": self.mist_active,
                "current_intensity": self.mist_intensity,
                "current_usage_time": usage_time,
                "total_usage_time": self.total_usage_time,
                "error_count": self.error_count,
                "voltage": self.voltage,
                "power_watts": self.power_watts,
                "frequency_hz": self.frequency,
                "available_modes": list(self.mist_modes.keys()),
                "last_activation": self.last_activation.isoformat() if self.last_activation else None,
                "safety": {
                    "max_continuous_time": self.max_continuous_time,
                    "cooldown_time": self.cooldown_time
                }
            }
            
        except Exception as e:
            self.logger.exception("Erreur récupération statut brumisateur")
            return {
                "status": "error",
                "error": str(e),
                "mist_active": False
            }
    
    def check_status(self) -> bool:
        """Vérifie le statut du contrôleur"""
        try:
            # Vérifier que le GPIO fonctionne
            current_state = self.gpio_manager.read_pin(self.mist_pin)
            
            # Vérifier la cohérence
            if self.mist_active != current_state:
                self.logger.warning("Incohérence état brumisateur détectée")
                return False
            
            # Vérifier le temps d'utilisation en continu
            if self.mist_active and self.last_activation:
                usage_time = (datetime.now() - self.last_activation).total_seconds()
                if usage_time > self.max_continuous_time:
                    self.logger.warning("Temps d'utilisation continu dépassé, arrêt automatique")
                    self.deactivate_mist()
                    return False
            
            return self.error_count < 5
            
        except Exception as e:
            self.logger.exception("Erreur vérification statut brumisateur")
            return False
    
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.deactivate_mist()
            self.logger.info("Contrôleur brumisateur ultrasonique nettoyé")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage brumisateur: {e}")


# Alias pour compatibilité
BuzzerController = UltrasonicMistController
