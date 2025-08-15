"""
light_controller.py
Module pour la gestion de l'éclairage via GPIO Raspberry Pi.

Fonctionnalités :
- Contrôle automatique de l'éclairage basé sur les heures de lever/coucher du soleil.
- Activation ou désactivation du relais d'éclairage.
- Support pour différents types d'éclairage (UV, LED, etc.).
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from .base_controller import BaseController
from ..utils.gpio_manager import GPIOManager, PinConfig, PinMode

# Import pour le calcul des heures de soleil
try:
    from astral import LocationInfo
    from astral.sun import sun
    SUN_CALCULATION_AVAILABLE = True
except ImportError:
    SUN_CALCULATION_AVAILABLE = False
    # Note: logging sera géré par BaseController

@dataclass
class LightConfig:
    latitude: float
    longitude: float
    day_hours: int  # Nombre d'heures d'éclairage par jour
    uv_required: bool
    intensity: str  # "low", "medium", "high"

class LightController(BaseController):
    """
    Classe pour gérer l'éclairage avec GPIO.
    """
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        """
        Initialise le contrôleur d'éclairage.

        :param gpio_manager: Instance du gestionnaire GPIO.
        :param config: Configuration pour l'éclairage.
        """
        super().__init__(gpio_manager, config)
        
        # Extraire la configuration d'éclairage depuis la config système
        lighting_config = config.get('lighting', {})
        self.light_config = LightConfig(
            latitude=lighting_config.get('latitude', 48.8566),
            longitude=lighting_config.get('longitude', 2.3522),
            day_hours=lighting_config.get('day_hours', 12),
            uv_required=lighting_config.get('uv_required', True),
            intensity=lighting_config.get('intensity', 'medium')
        )
        
        # Configuration des pins
        self._setup_pins()
        
        # Calcul des heures de lever/coucher
        if SUN_CALCULATION_AVAILABLE:
            self.location = LocationInfo(
                latitude=self.light_config.latitude,
                longitude=self.light_config.longitude
            )
        else:
            self.location = None
            self.logger.warning("Module astral non disponible, utilisation des heures par défaut")
            
        self.initialized = True
        
    def _setup_pins(self):
        """Configure les pins GPIO nécessaires"""
        try:
            # Récupérer la configuration GPIO depuis la config système
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            
            # Pin du relais d'éclairage
            light_relay_pin = pin_assignments.get('LIGHT_RELAY_PIN', 24)
            light_relay_config = PinConfig(
                pin=light_relay_pin,
                mode=PinMode.OUTPUT,
                initial_state=False  # Éclairage désactivé au démarrage
            )
            self.gpio_manager.setup_pin(light_relay_config)
            
            # Pin du capteur de lumière (optionnel)
            light_sensor_pin = pin_assignments.get('LIGHT_SENSOR_PIN', 17)
            light_sensor_config = PinConfig(
                pin=light_sensor_pin,
                mode=PinMode.INPUT
            )
            self.gpio_manager.setup_pin(light_sensor_config)
            
            self.logger.info(f"Pins configurés - Relais: {light_relay_pin}, Capteur: {light_sensor_pin}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la configuration des pins: {e}")
            self.record_error(e)
            raise

    def get_sunrise_sunset_times(self) -> Dict[str, datetime]:
        """
        Calcule les heures de lever et coucher du soleil.
        
        :return: Dictionnaire avec sunrise et sunset
        """
        try:
            if SUN_CALCULATION_AVAILABLE and self.location:
                today = datetime.now().date()
                s = sun(self.location.observer, date=today)
                
                return {
                    'sunrise': s['sunrise'],
                    'sunset': s['sunset']
                }
            else:
                # Heures par défaut si le module astral n'est pas disponible
                now = datetime.now()
                sunrise = now.replace(hour=6, minute=0, second=0, microsecond=0)
                sunset = sunrise + timedelta(hours=self.light_config.day_hours)
                
                return {
                    'sunrise': sunrise,
                    'sunset': sunset
                }
                
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul des heures de soleil: {e}")
            self.record_error(e)
            # Heures par défaut en cas d'erreur
            now = datetime.now()
            sunrise = now.replace(hour=6, minute=0, second=0, microsecond=0)
            sunset = sunrise + timedelta(hours=self.light_config.day_hours)
            
            return {
                'sunrise': sunrise,
                'sunset': sunset
            }

    def should_light_be_on(self) -> bool:
        """
        Détermine si l'éclairage doit être allumé.
        
        :return: True si l'éclairage doit être allumé
        """
        try:
            if SUN_CALCULATION_AVAILABLE and self.location:
                # Utiliser les vraies heures de lever/coucher
                times = self.get_sunrise_sunset_times()
                now = datetime.now()
                
                return times['sunrise'] <= now <= times['sunset']
            else:
                # Utiliser des heures fixes
                now = datetime.now()
                start_hour = 6  # 6h00
                end_hour = start_hour + self.light_config.day_hours
                
                return start_hour <= now.hour < end_hour
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la détermination de l'état d'éclairage: {e}")
            self.record_error(e)
            return False

    def control_lighting(self) -> bool:
        """
        Contrôle l'éclairage automatique.
        
        :return: True si le contrôle a été effectué, False sinon
        """
        try:
            should_be_on = self.should_light_be_on()
            currently_on = self.is_light_on()
            
            if should_be_on and not currently_on:
                self.activate_light()
                return True
            elif not should_be_on and currently_on:
                self.deactivate_light()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors du contrôle de l'éclairage: {e}")
            self.record_error(e)
            return False

    def control(self) -> bool:
        """
        Méthode de contrôle principale (implémentation de l'abstraction)
        
        :return: True si le contrôle a été effectué, False sinon
        """
        return self.control_lighting()

    def activate_light(self) -> bool:
        """
        Active l'éclairage.
        
        :return: True si l'activation a réussi, False sinon
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            light_pin = pin_assignments.get('LIGHT_RELAY_PIN', 24)
            
            self.gpio_manager.set_pin_state(light_pin, True)
            self.logger.info("Éclairage activé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'activation de l'éclairage: {e}")
            self.record_error(e)
            return False

    def deactivate_light(self) -> bool:
        """
        Désactive l'éclairage.
        
        :return: True si la désactivation a réussi, False sinon
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            light_pin = pin_assignments.get('LIGHT_RELAY_PIN', 24)
            
            self.gpio_manager.set_pin_state(light_pin, False)
            self.logger.info("Éclairage désactivé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la désactivation de l'éclairage: {e}")
            self.record_error(e)
            return False

    def is_light_on(self) -> bool:
        """
        Vérifie si l'éclairage est actuellement allumé.
        
        :return: True si l'éclairage est allumé, False sinon
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            light_pin = pin_assignments.get('LIGHT_RELAY_PIN', 24)
            
            return self.gpio_manager.get_pin_state(light_pin)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de l'éclairage: {e}")
            self.record_error(e)
            return False

    def read_light_sensor(self) -> Optional[float]:
        """
        Lit la valeur du capteur de lumière.
        
        :return: Valeur de luminosité ou None si la lecture échoue
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            light_sensor_pin = pin_assignments.get('LIGHT_SENSOR_PIN', 17)
            
            # Lecture analogique du capteur LDR
            # Note: Cette implémentation dépend du type de capteur utilisé
            light_value = self.gpio_manager.read_analog(light_sensor_pin)
            
            if light_value is not None:
                self.logger.info(f"Luminosité lue: {light_value}")
                return light_value
            else:
                self.logger.warning("Impossible de lire la luminosité")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture du capteur de lumière: {e}")
            self.record_error(e)
            return None

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du contrôleur (implémentation de l'abstraction)
        
        :return: Dictionnaire contenant le statut
        """
        try:
            light_on = self.is_light_on()
            should_be_on = self.should_light_be_on()
            light_sensor_value = self.read_light_sensor()
            
            return {
                "controller": "light",
                "initialized": self.initialized,
                "light_on": light_on,
                "should_be_on": should_be_on,
                "light_sensor_value": light_sensor_value,
                "latitude": self.light_config.latitude,
                "longitude": self.light_config.longitude,
                "day_hours": self.light_config.day_hours,
                "uv_required": self.light_config.uv_required,
                "intensity": self.light_config.intensity,
                "sun_calculation_available": SUN_CALCULATION_AVAILABLE,
                "error_count": self.error_count,
                "last_error": str(self.last_error) if self.last_error else None
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du statut: {e}")
            self.record_error(e)
            return {
                "controller": "light",
                "initialized": self.initialized,
                "error": str(e),
                "error_count": self.error_count
            }

    def check_status(self) -> bool:
        """
        Vérifie le statut du contrôleur.
        
        :return: True si tout fonctionne correctement, False sinon
        """
        try:
            # Vérifier que le relais répond
            light_state = self.is_light_on()
            
            # Vérifier que le capteur fonctionne (optionnel)
            light_sensor_value = self.read_light_sensor()
            
            self.logger.info(f"Statut vérifié - Éclairage: {light_state}, Capteur: {light_sensor_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du statut: {e}")
            self.record_error(e)
            return False
