"""
Service de gestion de l'alimentation
Contrôle l'alimentation automatique avec système de double trappe
"""

import time
import logging
from typing import Dict, Any, Optional, List
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from controllers.drivers.servo_driver import ServoDriver
from controllers.drivers.base_driver import DriverConfig

class FeedingService:
    """
    Service de gestion de l'alimentation
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service d'alimentation
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Driver d'alimentation
        self.servo_driver = None
        
        # Configuration
        self.gpio_config = config.get('gpio_config', {})
        self.safety_limits = config.get('safety_limits', {})
        self.feeding_config = config.get('actuators', {}).get('feeding', {})
        
        # État de l'alimentation
        self.is_feeding = False
        self.feeding_schedule = []
        self.last_feeding_time = 0
        self.feeding_count = 0
        self.today_feeding_count = 0  # Compteur pour aujourd'hui
        
        # Système de double trappe avec un seul servomoteur
        # Les deux trappes sont actionnées simultanément par le même servo
        self.trap1_open_angle = 0     # Position 0° : Trappe 1 ouverte (entrée SAS), Trappe 2 fermée (sortie terrarium)
        self.trap2_open_angle = 100   # Position 100° : Trappe 1 fermée (entrée SAS), Trappe 2 ouverte (sortie terrarium)
        self.trap_delay = 1.0         # Délai entre les phases d'alimentation
        
        # Statistiques
        self.stats = {
            'total_feedings': 0,
            'successful_feedings': 0,
            'failed_feedings': 0,
            'last_feeding_time': 0,
            'flies_delivered': 0,
            'today_feeding_count': 0
        }
        
        # S'abonner aux événements de contrôle
        if self.event_bus:
            self.event_bus.on('manual_feeding_request', self._on_manual_feeding_request)
            self.event_bus.on('servo_position_request', self._on_servo_position_request)
        
    def initialize(self) -> bool:
        """
        Initialise le service d'alimentation
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du service d'alimentation...")
            
            # Vérifier si un driver a déjà été passé (par ComponentControlService)
            if hasattr(self, '_external_servo_driver') and self._external_servo_driver:
                self.servo_driver = self._external_servo_driver
                self.logger.info("Utilisation du driver servomoteur externe")
            else:
                # Initialiser un nouveau driver
                self.logger.info("Initialisation du driver servomoteur interne...")
                
                # Récupérer la configuration GPIO
                gpio_pins = self.gpio_config.get('gpio_pins', {})
                actuators = gpio_pins.get('actuators', {})
                servo_config = actuators.get('feeder_servo', {})
                
                if not servo_config:
                    self.logger.error("Configuration servo alimentation non trouvée")
                    return False
                
                # Créer le driver servo pour l'alimentation
                driver_config = DriverConfig(
                    name="feeding_servo",
                    enabled=self.feeding_config.get('enabled', True),
                    timeout=5.0,
                    retry_attempts=3,
                    retry_delay=1.0
                )
                
                from utils.gpio_config import get_actuator_pin
                pwm_pin = get_actuator_pin('feeder_servo', 'pwm_pin')
                frequency = servo_config.get('frequency', 50)
                
                self.servo_driver = ServoDriver(driver_config, pwm_pin, frequency)
                
                if not self.servo_driver.initialize():
                    self.logger.error("Échec initialisation driver alimentation")
                    return False
            
            # Récupérer les paramètres d'alimentation
            self.trap_delay = self.feeding_config.get('trap_delay', 1.0)
            
            self.logger.info("Service d'alimentation initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service alimentation: {e}")
            return False
    
    def start(self) -> bool:
        """
        Démarre le service d'alimentation
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.servo_driver:
                return False
            
            if self.servo_driver.start():
                self.logger.info("Service d'alimentation démarré")
                return True
            else:
                self.logger.error("Échec démarrage service alimentation")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur démarrage service alimentation: {e}")
            return False
    
    def stop(self) -> None:
        """Arrête le service d'alimentation"""
        try:
            # Arrêter l'alimentation en cours
            self.stop_feeding()
            
            # Arrêter le driver
            if self.servo_driver:
                self.servo_driver.stop()
            
            self.logger.info("Service d'alimentation arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service alimentation: {e}")
    
    def update(self, sensor_data: Dict[str, Any]) -> None:
        """
        Met à jour le service d'alimentation
        
        Args:
            sensor_data: Données des capteurs
        """
        try:
            # Vérifier les horaires d'alimentation
            self._check_feeding_schedule()
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour service alimentation: {e}")
    
    def update_feeding(self, feeding_profile: Dict[str, Any]) -> None:
        """
        Met à jour l'alimentation selon le profil d'espèce
        
        Args:
            feeding_profile: Profil d'alimentation de l'espèce
        """
        try:
            # Récupérer les paramètres du profil
            self.feeding_schedule = feeding_profile.get('schedule', [])
            self.trap_delay = feeding_profile.get('trap_delay', 1.0)
            
            self.logger.info(f"Profil d'alimentation mis à jour: {len(self.feeding_schedule)} horaires")
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour alimentation: {e}")
    
    def _check_feeding_schedule(self) -> None:
        """Vérifie les horaires d'alimentation"""
        try:
            current_time = time.time()
            current_hour = time.localtime().tm_hour
            
            # Vérifier si c'est l'heure d'alimentation
            for schedule in self.feeding_schedule:
                feeding_hour = schedule.get('hour')
                feeding_count = schedule.get('count', 1)
                
                if feeding_hour == current_hour:
                    # Vérifier si l'alimentation a déjà eu lieu aujourd'hui
                    if self._should_feed_today(feeding_hour):
                        self.feed_animals_double_trap(feeding_count, self.trap_delay)
                        break
            
        except Exception as e:
            self.logger.error(f"Erreur vérification horaires: {e}")
    
    def _should_feed_today(self, feeding_hour: int) -> bool:
        """
        Vérifie si l'alimentation doit avoir lieu aujourd'hui
        
        Args:
            feeding_hour: Heure d'alimentation
            
        Returns:
            True si l'alimentation doit avoir lieu
        """
        try:
            current_time = time.time()
            today = time.strftime("%Y-%m-%d")
            
            # Vérifier si l'alimentation a déjà eu lieu aujourd'hui
            if self.stats['last_feeding_time'] > 0:
                last_feeding_date = time.strftime("%Y-%m-%d", time.localtime(self.stats['last_feeding_time']))
                if last_feeding_date == today:
                    return False
            
            # Vérifier si c'est l'heure d'alimentation
            current_hour = time.localtime().tm_hour
            if current_hour != feeding_hour:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur vérification alimentation: {e}")
            return False
    
    def feed_animals_double_trap(self, fly_count: int, trap_delay: float = 1.0) -> bool:
        """
        Effectue l'alimentation avec le système de double trappe
        
        Args:
            fly_count: Nombre de mouches à distribuer
            trap_delay: Délai entre l'ouverture des trappes
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.servo_driver:
                self.logger.error("Driver servo non disponible")
                return False
            
            if self.is_feeding:
                self.logger.warning("Alimentation déjà en cours")
                return False
            
            self.logger.info(f"Début alimentation: {fly_count} mouches")
            self.is_feeding = True
            self.stats['total_feedings'] += 1
            
            # Phase 1: Position 0° - SAS ouvert (entrée des mouches)
            # Trappe 1 ouverte (entrée SAS), Trappe 2 fermée (sortie terrarium)
            self.logger.info("Phase 1: Ouverture SAS pour entrée des mouches...")
            if not self._set_servo_position(self.trap1_open_angle):
                self.logger.error("Échec positionnement servo phase 1")
                self.is_feeding = False
                return False
            
            # Attendre que les mouches entrent dans le SAS
            self.logger.info(f"Attente entrée des mouches ({trap_delay}s)...")
            time.sleep(trap_delay)
            
            # Phase 2: Position 100° - SAS fermé (sortie vers terrarium)
            # Trappe 1 fermée (entrée SAS), Trappe 2 ouverte (sortie terrarium)
            self.logger.info("Phase 2: Fermeture SAS et ouverture sortie terrarium...")
            if not self._set_servo_position(self.trap2_open_angle):
                self.logger.error("Échec positionnement servo phase 2")
                self.is_feeding = False
                return False
            
            # Attendre que les mouches sortent vers le terrarium
            self.logger.info("Attente sortie des mouches vers terrarium...")
            time.sleep(2.0)
            
            # Phase 3: Retour position 0° - SAS fermé (repos)
            # Trappe 1 fermée (entrée SAS), Trappe 2 fermée (sortie terrarium)
            self.logger.info("Phase 3: Retour position repos...")
            if not self._set_servo_position(0):
                self.logger.error("Échec retour position repos")
            
            # Mettre à jour les statistiques
            current_time = time.time()
            self.stats['successful_feedings'] += 1
            self.stats['last_feeding_time'] = current_time
            self.stats['flies_delivered'] += fly_count
            self.stats['today_feeding_count'] += 1
            self.last_feeding_time = current_time
            self.feeding_count += 1
            self.today_feeding_count += 1
            
            self.is_feeding = False
            
            self.logger.info(f"Alimentation terminée: {fly_count} mouches distribuées")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('feeding_completed', {
                    'fly_count': fly_count,
                    'timestamp': time.time(),
                    'success': True
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur alimentation: {e}")
            self.stats['failed_feedings'] += 1
            self.is_feeding = False
            
            # Émettre un événement d'erreur
            if self.event_bus:
                self.event_bus.emit('feeding_failed', {
                    'fly_count': fly_count,
                    'error': str(e),
                    'timestamp': time.time()
                })
            
            return False
    
    def _set_servo_position(self, angle: float) -> bool:
        """
        Positionne le servomoteur à l'angle spécifié
        
        Args:
            angle: Angle en degrés (0° ou 100°)
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not self.servo_driver:
                return False
            
            # Positionner le servo à l'angle spécifié
            success = self.servo_driver.write({"angle": angle, "duration": 1.0})
            if success:
                if angle == self.trap1_open_angle:
                    self.logger.info("Position 0°: Trappe 1 ouverte (entrée SAS), Trappe 2 fermée (sortie terrarium)")
                elif angle == self.trap2_open_angle:
                    self.logger.info("Position 100°: Trappe 1 fermée (entrée SAS), Trappe 2 ouverte (sortie terrarium)")
                else:
                    self.logger.info(f"Position {angle}°: Système en position de repos")
            return success
        except Exception as e:
            self.logger.error(f"Erreur positionnement servo à {angle}°: {e}")
            return False
    
    def stop_feeding(self) -> None:
        """Arrête l'alimentation en cours"""
        try:
            if self.is_feeding:
                self.logger.info("Arrêt alimentation en cours...")
                
                # Retourner le servo en position de repos (0°)
                self._set_servo_position(0)
                
                self.is_feeding = False
                self.logger.info("Alimentation arrêtée")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt alimentation: {e}")
    
    def get_feeding_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de l'alimentation
        
        Returns:
            Dictionnaire du statut
        """
        # Vérifier si c'est un nouveau jour et réinitialiser le compteur
        self._check_daily_reset()
        
        return {
            'is_feeding': self.is_feeding,
            'feeding_schedule': self.feeding_schedule.copy(),
            'last_feeding_time': self.last_feeding_time,
            'feeding_count': self.feeding_count,
            'today_feeding_count': self.today_feeding_count,
            'trap_delay': self.trap_delay,
            'stats': self.stats.copy()
        }
    
    def _check_daily_reset(self) -> None:
        """
        Vérifie si c'est un nouveau jour et réinitialise le compteur quotidien
        """
        try:
            current_time = time.time()
            current_date = time.strftime("%Y-%m-%d", time.localtime(current_time))
            
            # Vérifier si la dernière alimentation était d'un jour différent
            if self.last_feeding_time > 0:
                last_feeding_date = time.strftime("%Y-%m-%d", time.localtime(self.last_feeding_time))
                if last_feeding_date != current_date:
                    # Nouveau jour, réinitialiser le compteur
                    self.today_feeding_count = 0
                    self.stats['today_feeding_count'] = 0
                    self.logger.info("Nouveau jour détecté, compteur d'alimentation réinitialisé")
        except Exception as e:
            self.logger.error(f"Erreur vérification réinitialisation quotidienne: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du service
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'service_name': 'feeding_service',
            'enabled': self.feeding_config.get('enabled', True),
            'feeding_status': self.get_feeding_status(),
            'driver_status': self.servo_driver.get_status() if self.servo_driver else None
        }
    
    def _on_manual_feeding_request(self, event_data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement pour une demande d'alimentation manuelle"""
        try:
            self.logger.info(f"Demande d'alimentation manuelle reçue: {event_data}")
            
            # Exécuter l'alimentation
            if self.feed_animals_double_trap(fly_count=1, trap_delay=1.0):
                self.logger.info("Alimentation exécutée avec succès")
            else:
                self.logger.error("Échec de l'alimentation")
                
        except Exception as e:
            self.logger.error(f"Erreur gestion événement alimentation: {e}")
    
    def _on_servo_position_request(self, event_data: Dict[str, Any]) -> None:
        """Gestionnaire d'événement pour une demande de positionnement du servo"""
        try:
            angle = event_data.get('angle', 0)
            duration = event_data.get('duration', 1.0)
            self.logger.info(f"Demande de positionnement servo reçue: angle={angle}, duration={duration}")
            
            # Positionner le servo
            if self.set_servo_angle(angle, duration):
                self.logger.info(f"Servo positionné à {angle}°")
            else:
                self.logger.error(f"Échec positionnement servo à {angle}°")
                
        except Exception as e:
            self.logger.error(f"Erreur gestion événement servo: {e}")
    
    def cleanup(self) -> None:
        """Nettoie le service d'alimentation"""
        try:
            self.stop()
            
            if self.servo_driver:
                self.servo_driver.cleanup()
                self.servo_driver = None
            
            self.logger.info("Service d'alimentation nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service alimentation: {e}")

