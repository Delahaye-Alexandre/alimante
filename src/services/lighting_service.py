"""
Service de gestion de l'éclairage
Contrôle les bandeaux LED selon les profils d'espèces et la photopériode
"""

import time
import logging
from typing import Dict, Any, Optional
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from controllers.drivers.pwm_driver import PWMDriver
from controllers.drivers.base_driver import DriverConfig

class LightingService:
    """
    Service de gestion de l'éclairage
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service d'éclairage
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Driver d'éclairage
        self.lighting_driver = None
        
        # Configuration
        self.gpio_config = config.get('gpio_config', {})
        self.lighting_config = config.get('actuators', {}).get('lighting', {})
        
        # État de l'éclairage
        self.current_intensity = 0
        self.target_intensity = 0
        self.is_lighting = False
        self.fade_duration = 30.0  # Durée de transition en secondes
        
        # Photopériode
        self.day_start_hour = 6
        self.day_end_hour = 18
        self.max_intensity = 100
        self.min_intensity = 0
        
        # Statistiques
        self.stats = {
            'total_lighting_time': 0,
            'fade_cycles': 0,
            'last_fade_start': 0,
            'last_fade_end': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service d'éclairage
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du service d'éclairage...")
            
            # Récupérer la configuration GPIO
            gpio_pins = self.gpio_config.get('gpio_pins', {})
            actuators = gpio_pins.get('actuators', {})
            lighting_config = actuators.get('lighting', {})
            
            if not lighting_config:
                self.logger.error("Configuration éclairage non trouvée")
                return False
            
            # Créer le driver PWM pour l'éclairage
            driver_config = DriverConfig(
                name="lighting",
                enabled=self.lighting_config.get('enabled', True),
                timeout=5.0,
                retry_attempts=3,
                retry_delay=1.0
            )
            
            from utils.gpio_config import get_actuator_pin
            pwm_pin = get_actuator_pin('lighting', 'pwm_pin')
            frequency = lighting_config.get('frequency', 1000)
            
            self.lighting_driver = PWMDriver(driver_config, pwm_pin, frequency)
            
            if not self.lighting_driver.initialize():
                self.logger.error("Échec initialisation driver éclairage")
                return False
            
            # Récupérer les paramètres d'éclairage
            self.fade_duration = self.lighting_config.get('fade_duration', 30)
            self.max_intensity = self.lighting_config.get('max_brightness', 100)
            
            self.logger.info("Service d'éclairage initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service éclairage: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre le service d'éclairage
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.lighting_driver:
                return False
            
            if self.lighting_driver.start():
                self.logger.info("Service d'éclairage démarré")
                return True
            else:
                self.logger.error("Échec démarrage service éclairage")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur démarrage service éclairage: {e}")
            return False
    
    def stop(self) -> None:
        """Arrête le service d'éclairage"""
        try:
            # Éteindre l'éclairage
            self.set_lighting(False)
            
            # Arrêter le driver
            if self.lighting_driver:
                self.lighting_driver.stop()
            
            self.logger.info("Service d'éclairage arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service éclairage: {e}")
    
    def update(self, sensor_data: Dict[str, Any]) -> None:
        """
        Met à jour le service d'éclairage
        
        Args:
            sensor_data: Données des capteurs
        """
        try:
            # Mettre à jour les statistiques
            if self.is_lighting:
                current_time = time.time()
                if self.stats['last_fade_start'] > 0:
                    self.stats['total_lighting_time'] += current_time - self.stats['last_fade_start']
                self.stats['last_fade_start'] = current_time
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour service éclairage: {e}")
    
    def update_lighting(self, lighting_profile: Dict[str, Any]) -> None:
        """
        Met à jour l'éclairage selon le profil d'espèce
        
        Args:
            lighting_profile: Profil d'éclairage de l'espèce
        """
        try:
            # Récupérer les paramètres du profil
            self.day_start_hour = lighting_profile.get('day_start', 6)
            self.day_end_hour = lighting_profile.get('day_end', 18)
            self.max_intensity = lighting_profile.get('max_intensity', 100)
            self.min_intensity = lighting_profile.get('min_intensity', 0)
            
            # Calculer l'intensité cible selon l'heure
            current_hour = time.localtime().tm_hour
            target_intensity = self._calculate_target_intensity(current_hour)
            
            # Appliquer l'intensité
            if target_intensity != self.target_intensity:
                self.set_intensity(target_intensity)
                self.target_intensity = target_intensity
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour éclairage: {e}")
    
    def _calculate_target_intensity(self, hour: int) -> int:
        """
        Calcule l'intensité cible selon l'heure
        
        Args:
            hour: Heure actuelle (0-23)
            
        Returns:
            Intensité cible (0-100)
        """
        try:
            if self.day_start_hour <= hour < self.day_end_hour:
                # Période de jour : intensité maximale
                return self.max_intensity
            else:
                # Période de nuit : intensité minimale
                return self.min_intensity
                
        except Exception as e:
            self.logger.error(f"Erreur calcul intensité: {e}")
            return 0
    
    def set_lighting(self, lighting: bool) -> bool:
        """
        Active ou désactive l'éclairage
        
        Args:
            lighting: True pour activer, False pour désactiver
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.lighting_driver:
                return False
            
            target_intensity = self.max_intensity if lighting else self.min_intensity
            
            if lighting != self.is_lighting:
                self.is_lighting = lighting
                self.target_intensity = target_intensity
                
                if lighting:
                    self.logger.info("Éclairage activé")
                else:
                    self.logger.info("Éclairage désactivé")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('lighting_changed', {
                        'lighting': lighting,
                        'intensity': target_intensity,
                        'timestamp': time.time()
                    })
            
            return self.set_intensity(target_intensity)
            
        except Exception as e:
            self.logger.error(f"Erreur commande éclairage: {e}")
            return False
    
    def set_intensity(self, intensity: int) -> bool:
        """
        Définit l'intensité de l'éclairage
        
        Args:
            intensity: Intensité (0-100)
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.lighting_driver:
                return False
            
            # Limiter l'intensité
            intensity = max(0, min(100, intensity))
            
            # Appliquer l'intensité avec transition douce
            if intensity != self.current_intensity:
                self._fade_to_intensity(intensity)
                self.current_intensity = intensity
                
                self.logger.debug(f"Intensité éclairage: {intensity}%")
                
                # Émettre un événement
                if self.event_bus:
                    self.event_bus.emit('lighting_intensity_changed', {
                        'intensity': intensity,
                        'timestamp': time.time()
                    })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition intensité: {e}")
            return False
    
    def _fade_to_intensity(self, target_intensity: int) -> None:
        """
        Transition douce vers une intensité cible
        
        Args:
            target_intensity: Intensité cible
        """
        try:
            if not self.lighting_driver:
                return
            
            start_intensity = self.current_intensity
            fade_steps = 50  # Nombre d'étapes pour la transition
            step_duration = self.fade_duration / fade_steps
            
            self.stats['fade_cycles'] += 1
            self.stats['last_fade_start'] = time.time()
            
            for step in range(fade_steps + 1):
                # Calculer l'intensité intermédiaire
                progress = step / fade_steps
                intermediate_intensity = int(start_intensity + (target_intensity - start_intensity) * progress)
                
                # Appliquer l'intensité
                duty_cycle = intermediate_intensity / 100.0
                self.lighting_driver.set_duty_cycle(duty_cycle)
                
                # Attendre avant la prochaine étape
                time.sleep(step_duration)
            
            self.stats['last_fade_end'] = time.time()
            
        except Exception as e:
            self.logger.error(f"Erreur transition éclairage: {e}")
    
    def get_lighting_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de l'éclairage
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_lighting': self.is_lighting,
            'current_intensity': self.current_intensity,
            'target_intensity': self.target_intensity,
            'day_start_hour': self.day_start_hour,
            'day_end_hour': self.day_end_hour,
            'max_intensity': self.max_intensity,
            'min_intensity': self.min_intensity,
            'stats': self.stats.copy()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du service
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'service_name': 'lighting_service',
            'enabled': self.lighting_config.get('enabled', True),
            'lighting_status': self.get_lighting_status(),
            'driver_status': self.lighting_driver.get_status() if self.lighting_driver else None
        }
    
    def cleanup(self) -> None:
        """Nettoie le service d'éclairage"""
        try:
            self.stop()
            
            if self.lighting_driver:
                self.lighting_driver.cleanup()
                self.lighting_driver = None
            
            self.logger.info("Service d'éclairage nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service éclairage: {e}")

