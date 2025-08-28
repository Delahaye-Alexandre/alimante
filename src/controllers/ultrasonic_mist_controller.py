"""
Contrôleur pour le brumisateur à ultrasons ANGEEK
Gestion de l'humidification par transducteur ultrasonique avec contrôle PWM
Compatible avec transducteurs ANGEEK 1/2 pour contrôle précis de l'intensité
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from ..utils.gpio_manager import GPIOManager
from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


class UltrasonicMistController:
    """Contrôleur pour le brumisateur à ultrasons ANGEEK avec contrôle PWM"""
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        self.logger = get_logger("ultrasonic_mist_controller")
        self.gpio_manager = gpio_manager
        self.config = config
        
        # Configuration du transducteur ultrasonique ANGEEK
        self.mist_pin = config.get("pin", 22)
        self.voltage = config.get("voltage", "5V")  # ANGEEK peut fonctionner en 5V
        self.current = config.get("current", 50)  # mA - ANGEEK 1/2 plus efficace
        self.frequency = config.get("frequency", 1700000)  # 1.7MHz pour ANGEEK
        self.power_watts = config.get("power_watts", 2.5)  # ANGEEK 1/2 consomme moins
        self.pwm_frequency = config.get("pwm_frequency", 1000)  # 1kHz pour contrôle PWM
        
        # Support PWM pour contrôle précis de l'intensité
        self.pwm_instance = None
        self.current_duty_cycle = 0
        
        # État du brumisateur
        self.mist_active = False
        self.last_activation = None
        self.total_usage_time = 0
        self.error_count = 0
        self.mist_intensity = 50  # 0-100%
        self.is_available = False  # Disponibilité du composant
        
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
        """Configure les pins GPIO avec support PWM pour transducteur ANGEEK"""
        try:
            # Vérifier que le pin est défini
            if self.mist_pin is None:
                self.logger.warning("❌ Composant brumisateur ultrasonique non détecté - PIN manquant")
                self.is_available = False
                return
            
            from ..utils.gpio_manager import PinConfig, PinMode
            
            # Configurer le pin du transducteur ultrasonique en mode PWM
            mist_config = PinConfig(
                pin=self.mist_pin,
                mode=PinMode.OUTPUT,
                initial_state=False,
                component_name="Brumisateur ultrasonique",
                required=True
            )
            
            if self.gpio_manager.setup_pin(mist_config):
                # Initialiser PWM pour contrôle précis de l'intensité ANGEEK
                try:
                    import RPi.GPIO as GPIO
                    self.pwm_instance = GPIO.PWM(self.mist_pin, self.pwm_frequency)
                    self.pwm_instance.start(0)  # Démarrer avec 0% duty cycle
                    self.logger.info(f"✅ PWM initialisé: pin {self.mist_pin}, fréquence {self.pwm_frequency}Hz")
                except Exception as pwm_error:
                    self.logger.warning(f"⚠️ Impossible d'initialiser PWM: {pwm_error}")
                    # Fallback sur contrôle digital simple
                    self.gpio_manager.write_pin(self.mist_pin, False)
                
                self.is_available = True
                self.logger.info(f"✅ Composant brumisateur ultrasonique configuré: pin {self.mist_pin}")
            else:
                self.is_available = False
                self.logger.error("❌ Échec configuration brumisateur ultrasonique")
                raise create_exception(
                    ErrorCode.GPIO_SETUP_FAILED,
                    "Impossible de configurer le brumisateur ultrasonique",
                    {"mist_pin": self.mist_pin}
                )
            
        except Exception as e:
            self.is_available = False
            self.logger.exception("❌ Erreur configuration GPIO brumisateur ultrasonique")
            raise create_exception(
                ErrorCode.GPIO_SETUP_FAILED,
                "Impossible de configurer le brumisateur ultrasonique",
                {"mist_pin": self.mist_pin, "original_error": str(e)}
            )
    
    def activate_mist(self, intensity: int = 50, duration: Optional[float] = None) -> bool:
        """Active le brumisateur ultrasonique"""
        if not self.is_available:
            self.logger.warning("⚠️ Tentative d'activation brumisateur désactivé - composant non disponible")
            return False
        
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
            
            # Activer le transducteur avec contrôle PWM pour ANGEEK
            if self.pwm_instance:
                # Utiliser PWM pour contrôle précis de l'intensité
                duty_cycle = intensity  # 0-100%
                self.pwm_instance.ChangeDutyCycle(duty_cycle)
                self.current_duty_cycle = duty_cycle
                self.logger.debug(f"PWM activé: {duty_cycle}% duty cycle")
            else:
                # Fallback: contrôle digital simple
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
            
            # Désactiver le transducteur (PWM ou digital)
            if self.pwm_instance:
                self.pwm_instance.ChangeDutyCycle(0)  # 0% duty cycle = arrêt
                self.current_duty_cycle = 0
                self.logger.debug("PWM désactivé: 0% duty cycle")
            else:
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
                # Ajuster l'intensité en temps réel avec PWM
                if self.pwm_instance:
                    self.pwm_instance.ChangeDutyCycle(intensity)
                    self.current_duty_cycle = intensity
                    self.logger.debug(f"PWM ajusté: {intensity}% duty cycle")
                
                self.mist_intensity = intensity
                self.logger.info(f"Intensité brumisateur ANGEEK ajustée: {intensity}%")
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
        """Nettoie les ressources PWM et GPIO"""
        try:
            self.deactivate_mist()
            
            # Nettoyer PWM
            if self.pwm_instance:
                try:
                    self.pwm_instance.stop()
                    self.pwm_instance = None
                    self.logger.debug("PWM nettoyé")
                except Exception as pwm_error:
                    self.logger.warning(f"Erreur nettoyage PWM: {pwm_error}")
            
            self.logger.info("Contrôleur brumisateur ultrasonique ANGEEK nettoyé")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage brumisateur: {e}")
