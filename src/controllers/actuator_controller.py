"""
Contrôleur des actionneurs Alimante
Gère le contrôle des actionneurs (PWM, relais, servo)
"""

import time
import logging
from typing import Dict, Any, Optional, List
from .base_controller import BaseController, ControllerConfig, ControllerState, ControllerError
from .drivers import PWMDriver, RelayDriver, ServoDriver, DriverConfig

class ActuatorController(BaseController):
    """
    Contrôleur des actionneurs
    """
    
    def __init__(self, config: ControllerConfig, gpio_config: Dict[str, Any], 
                 policies: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le contrôleur des actionneurs
        
        Args:
            config: Configuration du contrôleur
            gpio_config: Configuration GPIO
            policies: Politiques de contrôle
            event_bus: Bus d'événements
        """
        super().__init__(config, event_bus)
        self.gpio_config = gpio_config
        self.policies = policies
        
        # Actionneurs
        self.pwm_led = None
        self.heater_relay = None
        self.humidifier_relay = None
        self.feeder_servo = None
        
        # État des actionneurs
        self.actuator_states = {
            "led_intensity": 0,
            "heater_on": False,
            "humidifier_on": False,
            "feeder_position": "closed"
        }
        
        # Contrôle automatique
        self.auto_control = True
        self.manual_override = False
        
        # Historique des actions
        self.action_history = []
        self.max_history_size = 500
        
    def initialize(self) -> bool:
        """
        Initialise les actionneurs
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du contrôleur des actionneurs...")
            
            # Initialiser PWM LED
            if "actuators" in self.gpio_config and "pwm_led" in self.gpio_config["actuators"]:
                try:
                    pwm_config = DriverConfig(name="pwm_led", enabled=True)
                    self.pwm_led = PWMDriver(
                        pwm_config, 
                        self.gpio_config["actuators"]["pwm_led"],
                        frequency=1000
                    )
                    if self.pwm_led.initialize():
                        self.logger.info("PWM LED initialisé")
                    else:
                        self.logger.warning("Échec initialisation PWM LED")
                        self.pwm_led = None
                except Exception as e:
                    self.logger.error(f"Erreur initialisation PWM LED: {e}")
                    self.pwm_led = None
            
            # Initialiser relais chauffage
            if "actuators" in self.gpio_config and "heater" in self.gpio_config["actuators"]:
                try:
                    heater_config = DriverConfig(name="heater", enabled=True)
                    self.heater_relay = RelayDriver(
                        heater_config, 
                        self.gpio_config["actuators"]["heater"],
                        active_high=True
                    )
                    if self.heater_relay.initialize():
                        self.logger.info("Relais chauffage initialisé")
                    else:
                        self.logger.warning("Échec initialisation relais chauffage")
                        self.heater_relay = None
                except Exception as e:
                    self.logger.error(f"Erreur initialisation relais chauffage: {e}")
                    self.heater_relay = None
            
            # Initialiser relais humidificateur
            if "actuators" in self.gpio_config and "humidifier" in self.gpio_config["actuators"]:
                try:
                    humidifier_config = DriverConfig(name="humidifier", enabled=True)
                    self.humidifier_relay = RelayDriver(
                        humidifier_config, 
                        self.gpio_config["actuators"]["humidifier"],
                        active_high=True
                    )
                    if self.humidifier_relay.initialize():
                        self.logger.info("Relais humidificateur initialisé")
                    else:
                        self.logger.warning("Échec initialisation relais humidificateur")
                        self.humidifier_relay = None
                except Exception as e:
                    self.logger.error(f"Erreur initialisation relais humidificateur: {e}")
                    self.humidifier_relay = None
            
            # Initialiser servo distributeur
            if "actuators" in self.gpio_config and "feeder_servo" in self.gpio_config["actuators"]:
                try:
                    servo_config = DriverConfig(name="feeder_servo", enabled=True)
                    self.feeder_servo = ServoDriver(
                        servo_config, 
                        self.gpio_config["actuators"]["feeder_servo"],
                        frequency=50
                    )
                    if self.feeder_servo.initialize():
                        self.logger.info("Servo distributeur initialisé")
                    else:
                        self.logger.warning("Échec initialisation servo distributeur")
                        self.feeder_servo = None
                except Exception as e:
                    self.logger.error(f"Erreur initialisation servo distributeur: {e}")
                    self.feeder_servo = None
            
            # Vérifier qu'au moins un actionneur est initialisé
            if not any([self.pwm_led, self.heater_relay, self.humidifier_relay, self.feeder_servo]):
                self.logger.error("Aucun actionneur initialisé")
                return False
            
            self.logger.info("Contrôleur des actionneurs initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation contrôleur actionneurs: {e}")
            return False
    
    def update(self) -> bool:
        """
        Met à jour le contrôle des actionneurs
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            # Si le contrôle automatique est activé et qu'il n'y a pas de surcharge manuelle
            if self.auto_control and not self.manual_override:
                # Le contrôle automatique sera implémenté dans le contrôleur principal
                # qui recevra les données des capteurs et appliquera les politiques
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour actionneurs: {e}")
            return False
    
    def set_led_intensity(self, intensity: float) -> bool:
        """
        Définit l'intensité de la LED
        
        Args:
            intensity: Intensité (0-100)
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.pwm_led:
                self.logger.warning("PWM LED non disponible")
                return False
            
            intensity = max(0, min(100, intensity))
            
            if self.pwm_led.safe_write({"duty_cycle": intensity}):
                self.actuator_states["led_intensity"] = intensity
                self._log_action("led_intensity", intensity)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur définition intensité LED: {e}")
            return False
    
    def set_heater(self, on: bool) -> bool:
        """
        Contrôle le chauffage
        
        Args:
            on: True pour allumer, False pour éteindre
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.heater_relay:
                self.logger.warning("Relais chauffage non disponible")
                return False
            
            if on:
                success = self.heater_relay.turn_on()
            else:
                success = self.heater_relay.turn_off()
            
            if success:
                self.actuator_states["heater_on"] = on
                self._log_action("heater", on)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle chauffage: {e}")
            return False
    
    def set_humidifier(self, on: bool) -> bool:
        """
        Contrôle l'humidificateur
        
        Args:
            on: True pour allumer, False pour éteindre
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.humidifier_relay:
                self.logger.warning("Relais humidificateur non disponible")
                return False
            
            if on:
                success = self.humidifier_relay.turn_on()
            else:
                success = self.humidifier_relay.turn_off()
            
            if success:
                self.actuator_states["humidifier_on"] = on
                self._log_action("humidifier", on)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle humidificateur: {e}")
            return False
    
    def set_feeder_position(self, position: str) -> bool:
        """
        Contrôle la position du distributeur
        
        Args:
            position: Position ("open", "closed", "half", "center")
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.feeder_servo:
                self.logger.warning("Servo distributeur non disponible")
                return False
            
            if self.feeder_servo.move_to_position(position, duration=1.0):
                self.actuator_states["feeder_position"] = position
                self._log_action("feeder_position", position)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle distributeur: {e}")
            return False
    
    def feed_animals_double_trap(self, fly_count: int = 5, trap_delay: float = 1.0) -> bool:
        """
        Distribue des mouches avec double trappe simultanée pour contrôle statistique
        
        Le servomoteur contrôle les deux trappes en opposition :
        - Position 0° : Entrée ouverte, sortie fermée (mouches entrent)
        - Position 90° : Entrée fermée, sortie ouverte (mouches sortent)
        
        Args:
            fly_count: Nombre estimé de mouches souhaitées
            trap_delay: Délai de stabilisation dans le sas (secondes)
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.feeder_servo:
                self.logger.warning("Servo distributeur non disponible")
                return False
            
            # Calculer la durée d'ouverture basée sur le nombre de mouches
            # Estimation : 1 mouche par 0.5 seconde d'ouverture
            duration = max(1.0, min(10.0, fly_count * 0.5))
            
            self.logger.info(f"Début distribution mouches: {fly_count} mouches estimées, durée: {duration}s")
            
            # ÉTAPE 1: Position entrée ouverte (0°) - Les mouches entrent dans le sas
            if not self.set_feeder_position("trap_entrance_open"):
                self.logger.error("Échec position entrée ouverte")
                return False
            
            self.logger.info("Entrée ouverte, sortie fermée - Les mouches entrent dans le sas")
            
            # Attendre la durée calculée pour laisser entrer les mouches
            time.sleep(duration)
            
            # ÉTAPE 2: Position entrée fermée (90°) - Les mouches sortent du sas
            if not self.set_feeder_position("trap_entrance_closed"):
                self.logger.error("Échec position entrée fermée")
                return False
            
            self.logger.info("Entrée fermée, sortie ouverte - Les mouches sortent vers le terrarium")
            
            # Délai pour laisser les mouches s'échapper complètement
            time.sleep(trap_delay)
            
            # ÉTAPE 3: Retour à la position fermée (0°) - Système prêt
            if not self.set_feeder_position("closed"):
                self.logger.warning("Échec retour position fermée")
            
            self.logger.info("Distribution terminée - Système prêt")
            
            self._log_action("feed_animals_double_trap", {
                "fly_count": fly_count,
                "duration": duration,
                "trap_delay": trap_delay
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur distribution mouches double trappe: {e}")
            return False
    
    def calibrate_fly_feeding(self, test_runs: int = 5) -> Dict[str, float]:
        """
        Calibre le système de distribution de mouches
        
        Args:
            test_runs: Nombre de tests à effectuer
            
        Returns:
            Dictionnaire avec les paramètres de calibration
        """
        try:
            if not self.feeder_servo:
                self.logger.warning("Servo distributeur non disponible")
                return {}
            
            self.logger.info(f"Début calibration distribution mouches ({test_runs} tests)")
            
            calibration_data = []
            
            for i in range(test_runs):
                # Test avec différentes durées
                duration = 1.0 + (i * 0.5)  # 1s, 1.5s, 2s, 2.5s, 3s
                
                self.logger.info(f"Test {i+1}/{test_runs}: durée {duration}s")
                
                # Effectuer le test
                start_time = time.time()
                success = self.feed_animals_double_trap(fly_count=int(duration * 2), trap_delay=0.5)
                end_time = time.time()
                
                if success:
                    calibration_data.append({
                        "duration": duration,
                        "actual_time": end_time - start_time,
                        "success": True
                    })
                else:
                    calibration_data.append({
                        "duration": duration,
                        "actual_time": 0,
                        "success": False
                    })
                
                # Attendre entre les tests
                time.sleep(2)
            
            # Analyser les résultats
            successful_tests = [d for d in calibration_data if d["success"]]
            
            if successful_tests:
                avg_duration = sum(d["duration"] for d in successful_tests) / len(successful_tests)
                avg_actual_time = sum(d["actual_time"] for d in successful_tests) / len(successful_tests)
                
                calibration = {
                    "fly_per_second": 2.0,  # Estimation de base
                    "min_duration": 1.0,
                    "max_duration": 5.0,
                    "trap_delay": 0.5,
                    "success_rate": len(successful_tests) / len(calibration_data),
                    "avg_duration": avg_duration,
                    "avg_actual_time": avg_actual_time
                }
                
                self.logger.info(f"Calibration terminée: {calibration}")
                return calibration
            else:
                self.logger.error("Aucun test de calibration réussi")
                return {}
                
        except Exception as e:
            self.logger.error(f"Erreur calibration distribution mouches: {e}")
            return {}
    
    def set_auto_control(self, enabled: bool) -> None:
        """Active/désactive le contrôle automatique"""
        self.auto_control = enabled
        self.logger.info(f"Contrôle automatique {'activé' if enabled else 'désactivé'}")
    
    def set_manual_override(self, enabled: bool) -> None:
        """Active/désactive la surcharge manuelle"""
        self.manual_override = enabled
        self.logger.info(f"Surcharge manuelle {'activée' if enabled else 'désactivée'}")
    
    def get_actuator_states(self) -> Dict[str, Any]:
        """Retourne l'état des actionneurs"""
        return self.actuator_states.copy()
    
    def get_actuator_status(self) -> Dict[str, Any]:
        """Retourne le statut des actionneurs"""
        return {
            "pwm_led": {
                "available": self.pwm_led is not None,
                "ready": self.pwm_led.is_ready() if self.pwm_led else False,
                "intensity": self.actuator_states["led_intensity"]
            },
            "heater": {
                "available": self.heater_relay is not None,
                "ready": self.heater_relay.is_ready() if self.heater_relay else False,
                "on": self.actuator_states["heater_on"]
            },
            "humidifier": {
                "available": self.humidifier_relay is not None,
                "ready": self.humidifier_relay.is_ready() if self.humidifier_relay else False,
                "on": self.actuator_states["humidifier_on"]
            },
            "feeder": {
                "available": self.feeder_servo is not None,
                "ready": self.feeder_servo.is_ready() if self.feeder_servo else False,
                "position": self.actuator_states["feeder_position"]
            }
        }
    
    def get_action_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retourne l'historique des actions"""
        if limit:
            return self.action_history[-limit:]
        return self.action_history.copy()
    
    def _log_action(self, action_type: str, value: Any) -> None:
        """Enregistre une action dans l'historique"""
        action = {
            "type": action_type,
            "value": value,
            "timestamp": time.time()
        }
        
        self.action_history.append(action)
        if len(self.action_history) > self.max_history_size:
            self.action_history.pop(0)
        
        # Publier l'action sur le bus d'événements
        if self.event_bus:
            self.event_bus.emit("actuator_action", action)
    
    def cleanup(self) -> None:
        """Nettoie les ressources des actionneurs"""
        try:
            # Éteindre tous les actionneurs
            if self.pwm_led:
                self.pwm_led.safe_write({"duty_cycle": 0})
                self.pwm_led.cleanup()
                self.pwm_led = None
            
            if self.heater_relay:
                self.heater_relay.turn_off()
                self.heater_relay.cleanup()
                self.heater_relay = None
            
            if self.humidifier_relay:
                self.humidifier_relay.turn_off()
                self.humidifier_relay.cleanup()
                self.humidifier_relay = None
            
            if self.feeder_servo:
                self.feeder_servo.move_to_position("closed")
                self.feeder_servo.cleanup()
                self.feeder_servo = None
            
            self.logger.info("Contrôleur des actionneurs nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur actionneurs: {e}")

