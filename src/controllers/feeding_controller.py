"""
feeding_controller.py
Module pour la gestion de l'alimentation via GPIO Raspberry Pi.

Fonctionnalités :
- Contrôle automatique de l'alimentation selon un planning.
- Déclenchement manuel de l'alimentation.
- Gestion du servo pour ouvrir/fermer la trappe.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

from src.utils.gpio_manager import GPIOManager, PinAssignments, PinConfig, PinMode

@dataclass
class FeedingConfig:
    interval_days: int  # Intervalle entre les repas en jours
    feed_count: int     # Nombre de repas par cycle
    prey_type: str      # Type de proie
    servo_open_angle: int = 90   # Angle d'ouverture du servo
    servo_close_angle: int = 0   # Angle de fermeture du servo
    trap_open_duration: int = 5  # Durée d'ouverture en secondes

class FeedingController:
    """
    Classe pour gérer l'alimentation avec GPIO.
    """
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        """
        Initialise le contrôleur d'alimentation.

        :param gpio_manager: Instance du gestionnaire GPIO.
        :param config: Configuration pour l'alimentation.
        """
        self.gpio_manager = gpio_manager
        self.config = FeedingConfig(
            interval_days=config['interval_days'],
            feed_count=config['feed_count'],
            prey_type=config['prey_type'],
            servo_open_angle=config.get('servo_open_angle', 90),
            servo_close_angle=config.get('servo_close_angle', 0),
            trap_open_duration=config.get('trap_open_duration', 5)
        )
        
        # Configuration des pins
        self._setup_pins()
        
        # Historique des repas
        self.last_feeding_time: Optional[datetime] = None
        self.feeding_count = 0
        
    def _setup_pins(self):
        """Configure les pins GPIO nécessaires"""
        # Pin du servo pour la trappe
        servo_config = PinConfig(
            pin=PinAssignments.FEEDING_SERVO_PIN,
            mode=PinMode.PWM,
            pwm_frequency=50  # 50Hz pour servo standard
        )
        self.gpio_manager.setup_pin(servo_config)

    def should_feed_now(self) -> bool:
        """
        Détermine si il est temps de nourrir.
        
        :return: True si il faut nourrir maintenant
        """
        if self.last_feeding_time is None:
            # Premier repas
            return True
        
        # Calcul du temps écoulé depuis le dernier repas
        time_since_last = datetime.now() - self.last_feeding_time
        days_since_last = time_since_last.days
        
        # Vérification de l'intervalle
        if days_since_last >= self.config.interval_days:
            # Vérification du nombre de repas par cycle
            if self.feeding_count < self.config.feed_count:
                return True
        
        return False

    def control_feeding(self) -> bool:
        """
        Contrôle l'alimentation automatique.
        
        :return: True si l'alimentation a été déclenchée, False sinon
        """
        try:
            if self.should_feed_now():
                logging.info("Déclenchement de l'alimentation automatique")
                return self.trigger_feeding()
            else:
                logging.debug("Pas encore l'heure de nourrir")
                return False
                
        except Exception as e:
            logging.error(f"Erreur lors du contrôle de l'alimentation: {e}")
            return False

    def trigger_feeding(self) -> bool:
        """
        Déclenche manuellement l'alimentation.
        
        :return: True si l'alimentation a réussi
        """
        try:
            logging.info("Ouverture de la trappe d'alimentation")
            
            # Ouverture de la trappe
            if not self.open_trap():
                logging.error("Échec de l'ouverture de la trappe")
                return False
            
            # Attente de la durée configurée
            time.sleep(self.config.trap_open_duration)
            
            # Fermeture de la trappe
            if not self.close_trap():
                logging.error("Échec de la fermeture de la trappe")
                return False
            
            # Mise à jour de l'historique
            self.last_feeding_time = datetime.now()
            self.feeding_count += 1
            
            logging.info(f"Alimentation terminée. Repas #{self.feeding_count}")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors du déclenchement de l'alimentation: {e}")
            return False

    def open_trap(self) -> bool:
        """
        Ouvre la trappe d'alimentation.
        
        :return: True si l'ouverture a réussi
        """
        try:
            # Conversion de l'angle en duty cycle PWM (0-100%)
            # Servo standard: 0° = 2.5%, 90° = 7.5%, 180° = 12.5%
            duty_cycle = 2.5 + (self.config.servo_open_angle / 180.0) * 10.0
            
            success = self.gpio_manager.set_pwm_duty_cycle(
                PinAssignments.FEEDING_SERVO_PIN, 
                duty_cycle
            )
            
            if success:
                logging.info(f"Trappe ouverte à {self.config.servo_open_angle}°")
            else:
                logging.error("Échec de l'ouverture de la trappe")
            
            return success
            
        except Exception as e:
            logging.error(f"Erreur lors de l'ouverture de la trappe: {e}")
            return False

    def close_trap(self) -> bool:
        """
        Ferme la trappe d'alimentation.
        
        :return: True si la fermeture a réussi
        """
        try:
            # Conversion de l'angle en duty cycle PWM
            duty_cycle = 2.5 + (self.config.servo_close_angle / 180.0) * 10.0
            
            success = self.gpio_manager.set_pwm_duty_cycle(
                PinAssignments.FEEDING_SERVO_PIN, 
                duty_cycle
            )
            
            if success:
                logging.info(f"Trappe fermée à {self.config.servo_close_angle}°")
            else:
                logging.error("Échec de la fermeture de la trappe")
            
            return success
            
        except Exception as e:
            logging.error(f"Erreur lors de la fermeture de la trappe: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du contrôleur.
        
        :return: Dictionnaire avec les informations de statut
        """
        time_since_last = None
        if self.last_feeding_time:
            time_since_last = (datetime.now() - self.last_feeding_time).days
        
        return {
            "last_feeding_time": self.last_feeding_time.isoformat() if self.last_feeding_time else None,
            "days_since_last_feeding": time_since_last,
            "feeding_count": self.feeding_count,
            "interval_days": self.config.interval_days,
            "feed_count": self.config.feed_count,
            "prey_type": self.config.prey_type,
            "should_feed_now": self.should_feed_now(),
            "status": "ready" if self.should_feed_now() else "waiting"
        }

    def check_status(self) -> bool:
        """
        Vérifie si le contrôleur est fonctionnel.
        
        :return: True si fonctionnel
        """
        try:
            # Test basique du servo
            return self.gpio_manager.initialized
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du statut: {e}")
            return False

    def reset_feeding_count(self):
        """Réinitialise le compteur de repas (pour un nouveau cycle)"""
        self.feeding_count = 0
        logging.info("Compteur de repas réinitialisé")
