"""
feeding_controller.py
Module pour la gestion de l'alimentation automatique via GPIO Raspberry Pi.

Fonctionnalités :
- Contrôle automatique de l'alimentation selon un planning configuré.
- Utilisation d'un servo-moteur pour ouvrir/fermer une trappe.
- Gestion des intervalles et quantités d'alimentation.
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from src.controllers.base_controller import BaseController
from src.utils.gpio_manager import GPIOManager, PinConfig, PinMode

@dataclass
class FeedingConfig:
    interval_days: int  # Intervalle entre les repas en jours
    feed_count: int     # Nombre de repas par cycle
    prey_type: str      # Type de proie
    servo_open_angle: int = 90   # Angle d'ouverture du servo
    servo_close_angle: int = 0   # Angle de fermeture du servo
    trap_open_duration: int = 5  # Durée d'ouverture en secondes

class FeedingController(BaseController):
    """
    Classe pour gérer l'alimentation avec GPIO.
    """
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        """
        Initialise le contrôleur d'alimentation.

        :param gpio_manager: Instance du gestionnaire GPIO.
        :param config: Configuration pour l'alimentation.
        """
        super().__init__(gpio_manager, config)
        
        # Extraire la configuration d'alimentation depuis la config système
        feeding_config = config.get('feeding', {})
        self.feeding_config = FeedingConfig(
            interval_days=feeding_config.get('interval_days', 3),
            feed_count=feeding_config.get('feed_count', 2),
            prey_type=feeding_config.get('prey_type', 'Drosophiles'),
            servo_open_angle=feeding_config.get('servo_open_angle', 90),
            servo_close_angle=feeding_config.get('servo_close_angle', 0),
            trap_open_duration=feeding_config.get('trap_open_duration', 5)
        )
        
        # Configuration des pins
        self._setup_pins()
        
        # Historique des repas
        self.last_feeding_time: Optional[datetime] = None
        self.feeding_count = 0
        
        self.initialized = True
        
    def _setup_pins(self):
        """Configure les pins GPIO nécessaires"""
        try:
            # Récupérer la configuration GPIO depuis la config système
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            
            # Pin du servo pour la trappe
            feeding_servo_pin = pin_assignments.get('FEEDING_SERVO_PIN', 12)
            servo_config = PinConfig(
                pin=feeding_servo_pin,
                mode=PinMode.PWM,
                pwm_frequency=50  # 50Hz pour servo standard
            )
            self.gpio_manager.setup_pin(servo_config)
            
            self.logger.info(f"Pin servo configuré: {feeding_servo_pin}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la configuration des pins: {e}")
            self.record_error(e)
            raise

    def should_feed_now(self) -> bool:
        """
        Détermine si il est temps de nourrir.
        
        :return: True si il faut nourrir maintenant
        """
        try:
            if self.last_feeding_time is None:
                # Premier repas
                return True
            
            # Calcul du temps écoulé depuis le dernier repas
            time_since_last = datetime.now() - self.last_feeding_time
            days_since_last = time_since_last.days
            
            # Vérification de l'intervalle
            if days_since_last >= self.feeding_config.interval_days:
                # Vérification du nombre de repas par cycle
                if self.feeding_count < self.feeding_config.feed_count:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du timing d'alimentation: {e}")
            self.record_error(e)
            return False

    def control_feeding(self) -> bool:
        """
        Contrôle l'alimentation automatique.
        
        :return: True si l'alimentation a été déclenchée, False sinon
        """
        try:
            if self.should_feed_now():
                self.logger.info("Déclenchement de l'alimentation automatique")
                return self.trigger_feeding()
            else:
                self.logger.debug("Pas encore le moment de nourrir")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur lors du contrôle de l'alimentation: {e}")
            self.record_error(e)
            return False

    def control(self) -> bool:
        """
        Méthode de contrôle principale (implémentation de l'abstraction)
        
        :return: True si le contrôle a été effectué, False sinon
        """
        return self.control_feeding()

    def trigger_feeding(self) -> bool:
        """
        Déclenche l'alimentation en ouvrant la trappe.
        
        :return: True si l'alimentation a réussi, False sinon
        """
        try:
            self.logger.info(f"Alimentation en cours - Type: {self.feeding_config.prey_type}")
            
            # Ouvrir la trappe
            if self.open_trap():
                # Attendre la durée configurée
                time.sleep(self.feeding_config.trap_open_duration)
                
                # Fermer la trappe
                if self.close_trap():
                    # Mettre à jour l'historique
                    self.last_feeding_time = datetime.now()
                    self.feeding_count += 1
                    
                    self.logger.info(f"Alimentation terminée - Repas #{self.feeding_count}")
                    return True
                else:
                    self.logger.error("Impossible de fermer la trappe")
                    return False
            else:
                self.logger.error("Impossible d'ouvrir la trappe")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'alimentation: {e}")
            self.record_error(e)
            return False

    def open_trap(self) -> bool:
        """
        Ouvre la trappe d'alimentation.
        
        :return: True si l'ouverture a réussi, False sinon
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            feeding_servo_pin = pin_assignments.get('FEEDING_SERVO_PIN', 12)
            
            # Récupérer la configuration matérielle
            hardware_config = gpio_config.get('hardware_config', {})
            servo_config = hardware_config.get('servo', {}).get('feeding_trap', {})
            
            open_angle = servo_config.get('open_angle', self.feeding_config.servo_open_angle)
            min_pulse = servo_config.get('min_pulse', 500)
            max_pulse = servo_config.get('max_pulse', 2500)
            
            # Calculer la position PWM
            pulse_width = min_pulse + (max_pulse - min_pulse) * (open_angle / 180.0)
            
            # Activer le servo
            self.gpio_manager.set_servo_position(feeding_servo_pin, pulse_width)
            
            self.logger.info(f"Trappe ouverte à {open_angle}°")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ouverture de la trappe: {e}")
            self.record_error(e)
            return False

    def close_trap(self) -> bool:
        """
        Ferme la trappe d'alimentation.
        
        :return: True si la fermeture a réussi, False sinon
        """
        try:
            # Récupérer le pin depuis la config GPIO
            gpio_config = self.config.get('gpio_config', {})
            pin_assignments = gpio_config.get('pin_assignments', {})
            feeding_servo_pin = pin_assignments.get('FEEDING_SERVO_PIN', 12)
            
            # Récupérer la configuration matérielle
            hardware_config = gpio_config.get('hardware_config', {})
            servo_config = hardware_config.get('servo', {}).get('feeding_trap', {})
            
            close_angle = servo_config.get('close_angle', self.feeding_config.servo_close_angle)
            min_pulse = servo_config.get('min_pulse', 500)
            max_pulse = servo_config.get('max_pulse', 2500)
            
            # Calculer la position PWM
            pulse_width = min_pulse + (max_pulse - min_pulse) * (close_angle / 180.0)
            
            # Activer le servo
            self.gpio_manager.set_servo_position(feeding_servo_pin, pulse_width)
            
            self.logger.info(f"Trappe fermée à {close_angle}°")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la fermeture de la trappe: {e}")
            self.record_error(e)
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du contrôleur (implémentation de l'abstraction)
        
        :return: Dictionnaire contenant le statut
        """
        try:
            return {
                "controller": "feeding",
                "initialized": self.initialized,
                "last_feeding_time": self.last_feeding_time.isoformat() if self.last_feeding_time else None,
                "feeding_count": self.feeding_count,
                "interval_days": self.feeding_config.interval_days,
                "feed_count": self.feeding_config.feed_count,
                "prey_type": self.feeding_config.prey_type,
                "servo_open_angle": self.feeding_config.servo_open_angle,
                "servo_close_angle": self.feeding_config.servo_close_angle,
                "trap_open_duration": self.feeding_config.trap_open_duration,
                "should_feed_now": self.should_feed_now(),
                "error_count": self.error_count,
                "last_error": str(self.last_error) if self.last_error else None
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du statut: {e}")
            self.record_error(e)
            return {
                "controller": "feeding",
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
            # Vérifier que le servo répond
            # Note: Pour un test complet, on pourrait essayer de bouger le servo
            # mais ici on se contente de vérifier que la configuration est valide
            
            if not self.initialized:
                return False
            
            # Vérifier la configuration
            if (self.feeding_config.interval_days <= 0 or 
                self.feeding_config.feed_count <= 0 or
                self.feeding_config.trap_open_duration <= 0):
                return False
            
            self.logger.info("Statut du contrôleur d'alimentation vérifié")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du statut: {e}")
            self.record_error(e)
            return False

    def reset_feeding_count(self):
        """Remet à zéro le compteur de repas"""
        try:
            self.feeding_count = 0
            self.last_feeding_time = None
            self.logger.info("Compteur de repas remis à zéro")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la remise à zéro du compteur: {e}")
            self.record_error(e)
