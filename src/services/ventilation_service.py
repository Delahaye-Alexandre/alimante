"""
Service de gestion de la ventilation
Contrôle les ventilateurs selon la qualité de l'air
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

class VentilationService:
    """
    Service de gestion de la ventilation
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de ventilation
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Driver de ventilation
        self.fan_driver = None
        
        # Configuration
        self.gpio_config = config.get('gpio_config', {})
        self.safety_limits = config.get('safety_limits', {})
        self.ventilation_config = config.get('actuators', {}).get('ventilation', {})
        
        # État de la ventilation
        self.current_speed = 0
        self.target_speed = 0
        self.is_ventilating = False
        
        # Contrôle basé sur la qualité de l'air
        self.aqi_thresholds = {
            'good': 50,
            'moderate': 100,
            'unhealthy': 150,
            'hazardous': 300
        }
        
        # Vitesses de ventilation
        self.speed_levels = {
            'off': 0,
            'low': 25,
            'medium': 50,
            'high': 75,
            'max': 100
        }
        
        # Statistiques
        self.stats = {
            'total_ventilation_time': 0,
            'speed_changes': 0,
            'last_speed_change': 0,
            'current_aqi': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service de ventilation
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du service de ventilation...")
            
            # Récupérer la configuration GPIO
            gpio_pins = self.gpio_config.get('gpio_pins', {})
            actuators = gpio_pins.get('actuators', {})
            fan_config = actuators.get('fan_4', {})
            
            if not fan_config:
                self.logger.error("Configuration ventilateur non trouvée")
                return False
            
            # Créer le driver PWM pour le ventilateur
            driver_config = DriverConfig(
                name="ventilation",
                enabled=self.ventilation_config.get('enabled', True),
                timeout=5.0,
                retry_attempts=3,
                retry_delay=1.0
            )
            
            from utils.gpio_config import get_actuator_pin
            pwm_pin = get_actuator_pin('fan_4', 'pwm_pin')
            frequency = fan_config.get('frequency', 1000)
            
            self.fan_driver = PWMDriver(driver_config, pwm_pin, frequency)
            
            if not self.fan_driver.initialize():
                self.logger.error("Échec initialisation driver ventilation")
                return False
            
            # Récupérer les paramètres de ventilation
            self.aqi_thresholds = self.safety_limits.get('air_quality', self.aqi_thresholds)
            
            self.logger.info("Service de ventilation initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service ventilation: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre le service de ventilation
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.fan_driver:
                return False
            
            if self.fan_driver.start():
                self.logger.info("Service de ventilation démarré")
                return True
            else:
                self.logger.error("Échec démarrage service ventilation")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur démarrage service ventilation: {e}")
            return False
    
    def stop(self) -> None:
        """Arrête le service de ventilation"""
        try:
            # Arrêter la ventilation
            self.set_ventilation(0)
            
            # Arrêter le driver
            if self.fan_driver:
                self.fan_driver.stop()
            
            self.logger.info("Service de ventilation arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service ventilation: {e}")
    
    def update(self, sensor_data: Dict[str, Any]) -> None:
        """
        Met à jour le service de ventilation
        
        Args:
            sensor_data: Données des capteurs
        """
        try:
            # Récupérer la qualité de l'air
            air_quality_data = sensor_data.get('air_quality', {})
            aqi = air_quality_data.get('aqi')
            
            if aqi is not None:
                self.stats['current_aqi'] = aqi
                
                # Mettre à jour la ventilation selon la qualité de l'air
                self.update_ventilation(aqi)
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour service ventilation: {e}")
    
    def update_ventilation(self, aqi: int) -> None:
        """
        Met à jour la ventilation selon la qualité de l'air
        
        Args:
            aqi: Indice de qualité de l'air (AQI)
        """
        try:
            # Déterminer la vitesse de ventilation selon l'AQI
            if aqi >= self.aqi_thresholds['hazardous']:
                target_speed = self.speed_levels['max']
                level = "max"
            elif aqi >= self.aqi_thresholds['unhealthy']:
                target_speed = self.speed_levels['high']
                level = "high"
            elif aqi >= self.aqi_thresholds['moderate']:
                target_speed = self.speed_levels['medium']
                level = "medium"
            elif aqi >= self.aqi_thresholds['good']:
                target_speed = self.speed_levels['low']
                level = "low"
            else:
                target_speed = self.speed_levels['off']
                level = "off"
            
            # Appliquer la vitesse
            if target_speed != self.target_speed:
                self.set_ventilation(target_speed)
                self.logger.info(f"Ventilation ajustée: {level} (AQI: {aqi}, vitesse: {target_speed}%)")
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour ventilation: {e}")
    
    def set_ventilation(self, speed: int) -> bool:
        """
        Définit la vitesse de ventilation
        
        Args:
            speed: Vitesse (0-100)
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.fan_driver:
                return False
            
            # Limiter la vitesse
            speed = max(0, min(100, speed))
            
            # Appliquer la vitesse
            if speed != self.current_speed:
                duty_cycle = speed / 100.0
                
                if self.fan_driver.set_duty_cycle(duty_cycle):
                    self.current_speed = speed
                    self.target_speed = speed
                    self.is_ventilating = speed > 0
                    
                    # Mettre à jour les statistiques
                    self.stats['speed_changes'] += 1
                    self.stats['last_speed_change'] = time.time()
                    
                    if self.is_ventilating:
                        self.stats['total_ventilation_time'] += 1
                    
                    self.logger.debug(f"Vitesse ventilation: {speed}%")
                    
                    # Émettre un événement
                    if self.event_bus:
                        self.event_bus.emit('ventilation_changed', {
                            'speed': speed,
                            'is_ventilating': self.is_ventilating,
                            'aqi': self.stats['current_aqi'],
                            'timestamp': time.time()
                        })
                    
                    return True
                else:
                    self.logger.error("Échec commande ventilation")
                    return False
            else:
                return True
                
        except Exception as e:
            self.logger.error(f"Erreur commande ventilation: {e}")
            return False
    
    def set_ventilation_level(self, level: str) -> bool:
        """
        Définit le niveau de ventilation
        
        Args:
            level: Niveau ("off", "low", "medium", "high", "max")
            
        Returns:
            True si succès, False sinon
        """
        try:
            if level not in self.speed_levels:
                self.logger.warning(f"Niveau de ventilation invalide: {level}")
                return False
            
            speed = self.speed_levels[level]
            return self.set_ventilation(speed)
            
        except Exception as e:
            self.logger.error(f"Erreur définition niveau ventilation: {e}")
            return False
    
    def get_ventilation_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de la ventilation
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_ventilating': self.is_ventilating,
            'current_speed': self.current_speed,
            'target_speed': self.target_speed,
            'current_aqi': self.stats['current_aqi'],
            'aqi_thresholds': self.aqi_thresholds.copy(),
            'speed_levels': self.speed_levels.copy(),
            'stats': self.stats.copy()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du service
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'service_name': 'ventilation_service',
            'enabled': self.ventilation_config.get('enabled', True),
            'ventilation_status': self.get_ventilation_status(),
            'driver_status': self.fan_driver.get_status() if self.fan_driver else None
        }
    
    def cleanup(self) -> None:
        """Nettoie le service de ventilation"""
        try:
            self.stop()
            
            if self.fan_driver:
                self.fan_driver.cleanup()
                self.fan_driver = None
            
            self.logger.info("Service de ventilation nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service ventilation: {e}")

