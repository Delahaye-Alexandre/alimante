"""
light_controller.py
Module pour la gestion de l'éclairage via GPIO Raspberry Pi.

Fonctionnalités :
- Contrôle de l'éclairage basé sur les heures de lever/coucher du soleil.
- Activation/désactivation automatique des LED.
- Synchronisation avec les cycles naturels.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from astral import LocationInfo
from astral.sun import sun

from src.utils.gpio_manager import GPIOManager, PinAssignments, PinConfig, PinMode

@dataclass
class LightConfig:
    latitude: float
    longitude: float
    day_hours: int  # Nombre d'heures d'éclairage par jour
    uv_required: bool
    intensity: str  # "low", "medium", "high"

class LightController:
    """
    Classe pour gérer l'éclairage avec GPIO.
    """
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        """
        Initialise le contrôleur d'éclairage.

        :param gpio_manager: Instance du gestionnaire GPIO.
        :param config: Configuration pour l'éclairage.
        """
        self.gpio_manager = gpio_manager
        self.config = LightConfig(
            latitude=config['latitude'],
            longitude=config['longitude'],
            day_hours=config.get('day_hours', 12),
            uv_required=config.get('uv_required', True),
            intensity=config.get('intensity', 'medium')
        )
        
        # Configuration des pins
        self._setup_pins()
        
        # Calcul des heures de lever/coucher
        self.location = LocationInfo(
            latitude=self.config.latitude,
            longitude=self.config.longitude
        )
        
    def _setup_pins(self):
        """Configure les pins GPIO nécessaires"""
        # Pin du relais d'éclairage
        light_relay_config = PinConfig(
            pin=PinAssignments.LIGHT_RELAY_PIN,
            mode=PinMode.OUTPUT,
            initial_state=False  # Éclairage désactivé au démarrage
        )
        self.gpio_manager.setup_pin(light_relay_config)
        
        # Pin du capteur de lumière (optionnel)
        light_sensor_config = PinConfig(
            pin=PinAssignments.LIGHT_SENSOR_PIN,
            mode=PinMode.INPUT
        )
        self.gpio_manager.setup_pin(light_sensor_config)

    def get_sunrise_sunset_times(self) -> Dict[str, datetime]:
        """
        Calcule les heures de lever et coucher du soleil.
        
        :return: Dictionnaire avec sunrise et sunset
        """
        try:
            today = datetime.now().date()
            s = sun(self.location.observer, date=today)
            
            return {
                'sunrise': s['sunrise'],
                'sunset': s['sunset']
            }
        except Exception as e:
            logging.error(f"Erreur lors du calcul des heures de soleil: {e}")
            # Heures par défaut si erreur
            return {
                'sunrise': datetime.combine(datetime.now().date(), datetime.min.time().replace(hour=6)),
                'sunset': datetime.combine(datetime.now().date(), datetime.min.time().replace(hour=18))
            }

    def should_light_be_on(self) -> bool:
        """
        Détermine si l'éclairage doit être activé.
        
        :return: True si l'éclairage doit être activé
        """
        try:
            now = datetime.now()
            sun_times = self.get_sunrise_sunset_times()
            
            # Calcul de la durée d'éclairage
            light_start = sun_times['sunrise']
            light_end = light_start + timedelta(hours=self.config.day_hours)
            
            # Vérification si on est dans la période d'éclairage
            is_light_time = light_start <= now <= light_end
            
            logging.debug(f"Période d'éclairage: {light_start.time()} - {light_end.time()}")
            logging.debug(f"Heure actuelle: {now.time()}, Éclairage: {'ON' if is_light_time else 'OFF'}")
            
            return is_light_time
            
        except Exception as e:
            logging.error(f"Erreur lors de la détermination de l'éclairage: {e}")
            return False

    def control_lighting(self) -> bool:
        """
        Contrôle l'éclairage en fonction des heures de lever/coucher.
        
        :return: True si le contrôle a été effectué, False sinon
        """
        try:
            should_be_on = self.should_light_be_on()
            current_state = self.is_light_on()
            
            if should_be_on and not current_state:
                self.activate_light()
                return True
            elif not should_be_on and current_state:
                self.deactivate_light()
                return True
            else:
                logging.debug("État de l'éclairage déjà correct")
                return True
                
        except Exception as e:
            logging.error(f"Erreur lors du contrôle de l'éclairage: {e}")
            return False

    def activate_light(self) -> bool:
        """
        Active l'éclairage.
        
        :return: True si activé avec succès
        """
        success = self.gpio_manager.write_digital(PinAssignments.LIGHT_RELAY_PIN, True)
        if success:
            logging.info("Éclairage activé")
        else:
            logging.error("Échec de l'activation de l'éclairage")
        return success

    def deactivate_light(self) -> bool:
        """
        Désactive l'éclairage.
        
        :return: True si désactivé avec succès
        """
        success = self.gpio_manager.write_digital(PinAssignments.LIGHT_RELAY_PIN, False)
        if success:
            logging.info("Éclairage désactivé")
        else:
            logging.error("Échec de la désactivation de l'éclairage")
        return success

    def is_light_on(self) -> bool:
        """
        Vérifie si l'éclairage est actuellement actif.
        
        :return: True si l'éclairage est actif
        """
        return self.gpio_manager.read_digital(PinAssignments.LIGHT_RELAY_PIN) or False

    def read_light_sensor(self) -> Optional[float]:
        """
        Lit la valeur du capteur de lumière (si disponible).
        
        :return: Valeur de luminosité ou None
        """
        try:
            # Simulation pour le moment
            import random
            light_value = random.uniform(0, 100)  # Simulation 0-100%
            return light_value
        except Exception as e:
            logging.error(f"Erreur lors de la lecture du capteur de lumière: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du contrôleur.
        
        :return: Dictionnaire avec les informations de statut
        """
        sun_times = self.get_sunrise_sunset_times()
        light_on = self.is_light_on()
        should_be_on = self.should_light_be_on()
        light_sensor = self.read_light_sensor()
        
        return {
            "light_on": light_on,
            "should_be_on": should_be_on,
            "sunrise": sun_times['sunrise'].isoformat() if sun_times['sunrise'] else None,
            "sunset": sun_times['sunset'].isoformat() if sun_times['sunset'] else None,
            "day_hours": self.config.day_hours,
            "light_sensor_value": light_sensor,
            "status": "on" if light_on else "off"
        }

    def check_status(self) -> bool:
        """
        Vérifie si le contrôleur est fonctionnel.
        
        :return: True si fonctionnel
        """
        try:
            # Vérification basique - peut-on contrôler l'éclairage
            return self.gpio_manager.initialized
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du statut: {e}")
            return False
