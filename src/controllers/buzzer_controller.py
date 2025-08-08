"""
Contrôleur pour le buzzer/transducteur sonore
Gestion des alertes sonores et notifications
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from ..utils.gpio_manager import GPIOManager
from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


class BuzzerController:
    """Contrôleur pour le buzzer/transducteur sonore"""
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        self.logger = get_logger("buzzer_controller")
        self.gpio_manager = gpio_manager
        self.config = config
        
        # Configuration du buzzer
        self.buzzer_pin = config.get("pin", 22)
        self.voltage = config.get("voltage", "3.3V")
        self.current = config.get("current", 30)  # mA
        self.frequency_range = config.get("frequency_range", "2000-4000Hz")
        
        # État du buzzer
        self.buzzer_active = False
        self.last_activation = None
        self.total_usage_time = 0
        self.error_count = 0
        
        # Configuration des alertes
        self.alert_patterns = {
            "emergency": {"duration": 5, "frequency": 4000, "repeats": 3},
            "warning": {"duration": 2, "frequency": 2000, "repeats": 2},
            "info": {"duration": 1, "frequency": 3000, "repeats": 1},
            "success": {"duration": 0.5, "frequency": 3500, "repeats": 1}
        }
        
        # Initialisation GPIO
        self._setup_gpio()
        
        self.logger.info("Contrôleur buzzer initialisé")
    
    def _setup_gpio(self):
        """Configure les pins GPIO"""
        try:
            # Configurer le pin du buzzer
            self.gpio_manager.setup_pin(self.buzzer_pin, "OUT")
            self.gpio_manager.write_pin(self.buzzer_pin, False)  # Éteint par défaut
            
            self.logger.info(f"GPIO buzzer configuré: pin {self.buzzer_pin}")
            
        except Exception as e:
            self.logger.exception("Erreur configuration GPIO buzzer")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible de configurer le buzzer",
                {"buzzer_pin": self.buzzer_pin, "original_error": str(e)}
            )
    
    def activate_buzzer(self, duration: float = 1.0) -> bool:
        """Active le buzzer pour une durée donnée"""
        try:
            if not self.buzzer_active:
                self.gpio_manager.write_pin(self.buzzer_pin, True)
                self.buzzer_active = True
                self.last_activation = datetime.now()
                
                self.logger.info("Buzzer activé", {
                    "duration": duration,
                    "voltage": self.voltage,
                    "current": f"{self.current}mA"
                })
                
                # Attendre la durée spécifiée
                time.sleep(duration)
                
                # Désactiver
                return self.deactivate_buzzer()
            else:
                self.logger.debug("Buzzer déjà actif")
                return True
                
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur activation buzzer")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible d'activer le buzzer",
                {"original_error": str(e)}
            )
    
    def deactivate_buzzer(self) -> bool:
        """Désactive le buzzer"""
        try:
            if self.buzzer_active:
                self.gpio_manager.write_pin(self.buzzer_pin, False)
                self.buzzer_active = False
                
                # Calculer le temps d'utilisation
                if self.last_activation:
                    usage_time = (datetime.now() - self.last_activation).total_seconds()
                    self.total_usage_time += usage_time
                
                self.logger.info("Buzzer désactivé", {
                    "usage_time": usage_time if self.last_activation else 0,
                    "total_usage_hours": self.total_usage_time / 3600
                })
                
                return True
            else:
                self.logger.debug("Buzzer déjà inactif")
                return True
                
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur désactivation buzzer")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible de désactiver le buzzer",
                {"original_error": str(e)}
            )
    
    def play_alert(self, alert_type: str) -> bool:
        """Joue une alerte prédéfinie"""
        try:
            if alert_type not in self.alert_patterns:
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    f"Type d'alerte inconnu: {alert_type}",
                    {"available_types": list(self.alert_patterns.keys())}
                )
            
            pattern = self.alert_patterns[alert_type]
            
            self.logger.info(f"Jouer alerte: {alert_type}", pattern)
            
            # Jouer le pattern
            for i in range(pattern["repeats"]):
                if i > 0:
                    time.sleep(0.5)  # Pause entre les répétitions
                
                # Activer le buzzer
                self.gpio_manager.write_pin(self.buzzer_pin, True)
                time.sleep(pattern["duration"])
                self.gpio_manager.write_pin(self.buzzer_pin, False)
            
            return True
            
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Erreur alerte {alert_type}")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                f"Impossible de jouer l'alerte {alert_type}",
                {"original_error": str(e)}
            )
    
    def play_custom_pattern(self, pattern: Dict[str, Any]) -> bool:
        """Joue un pattern personnalisé"""
        try:
            duration = pattern.get("duration", 1.0)
            repeats = pattern.get("repeats", 1)
            pause = pattern.get("pause", 0.5)
            
            self.logger.info("Jouer pattern personnalisé", pattern)
            
            for i in range(repeats):
                if i > 0:
                    time.sleep(pause)
                
                self.gpio_manager.write_pin(self.buzzer_pin, True)
                time.sleep(duration)
                self.gpio_manager.write_pin(self.buzzer_pin, False)
            
            return True
            
        except Exception as e:
            self.error_count += 1
            self.logger.exception("Erreur pattern personnalisé")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                "Impossible de jouer le pattern personnalisé",
                {"original_error": str(e)}
            )
    
    def emergency_alert(self) -> bool:
        """Alerte d'urgence"""
        return self.play_alert("emergency")
    
    def warning_alert(self) -> bool:
        """Alerte d'avertissement"""
        return self.play_alert("warning")
    
    def info_alert(self) -> bool:
        """Alerte d'information"""
        return self.play_alert("info")
    
    def success_alert(self) -> bool:
        """Alerte de succès"""
        return self.play_alert("success")
    
    def add_alert_pattern(self, name: str, pattern: Dict[str, Any]) -> bool:
        """Ajoute un nouveau pattern d'alerte"""
        try:
            required_keys = ["duration", "frequency", "repeats"]
            if not all(key in pattern for key in required_keys):
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    "Pattern d'alerte incomplet",
                    {"required_keys": required_keys, "provided_keys": list(pattern.keys())}
                )
            
            self.alert_patterns[name] = pattern
            self.logger.info(f"Nouveau pattern d'alerte ajouté: {name}")
            return True
            
        except Exception as e:
            self.logger.exception(f"Erreur ajout pattern {name}")
            raise create_exception(
                ErrorCode.CONTROLLER_INIT_FAILED,
                f"Impossible d'ajouter le pattern {name}",
                {"original_error": str(e)}
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Récupère le statut du contrôleur"""
        try:
            usage_time = 0
            if self.buzzer_active and self.last_activation:
                usage_time = (datetime.now() - self.last_activation).total_seconds()
            
            return {
                "status": "ok" if self.error_count == 0 else "error",
                "buzzer_active": self.buzzer_active,
                "current_usage_time": usage_time,
                "total_usage_time": self.total_usage_time,
                "error_count": self.error_count,
                "voltage": self.voltage,
                "current_ma": self.current,
                "frequency_range": self.frequency_range,
                "available_patterns": list(self.alert_patterns.keys()),
                "last_activation": self.last_activation.isoformat() if self.last_activation else None
            }
            
        except Exception as e:
            self.logger.exception("Erreur récupération statut buzzer")
            return {
                "status": "error",
                "error": str(e),
                "buzzer_active": False
            }
    
    def check_status(self) -> bool:
        """Vérifie le statut du contrôleur"""
        try:
            # Vérifier que le GPIO fonctionne
            current_state = self.gpio_manager.read_pin(self.buzzer_pin)
            
            # Vérifier la cohérence
            if self.buzzer_active != current_state:
                self.logger.warning("Incohérence état buzzer détectée")
                return False
            
            return self.error_count < 5
            
        except Exception as e:
            self.logger.exception("Erreur vérification statut buzzer")
            return False
    
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.deactivate_buzzer()
            self.logger.info("Contrôleur buzzer nettoyé")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage buzzer: {e}")
