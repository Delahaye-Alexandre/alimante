"""
Contrôleur de distributeur d'alimentation Alimante
Gère le distributeur d'alimentation via servo et SAS (Système d'Alimentation Sécurisé)
"""

import time
import logging
from typing import Dict, Any, Optional
from ..base_controller import BaseController, ControllerConfig, ControllerState, ControllerError
from ..drivers.servo_driver import ServoDriver, DriverConfig
from ..drivers.relay_driver import RelayDriver

class FeederSASController(BaseController):
    """
    Contrôleur du système de distributeur d'alimentation
    Utilise un servo-moteur pour contrôler l'ouverture/fermeture du distributeur
    et un relais pour le SAS (Système d'Alimentation Sécurisé)
    """
    
    def __init__(self, config: ControllerConfig, gpio_config: Dict[str, Any], 
                 event_bus: Optional[Any] = None):
        """
        Initialise le contrôleur de distributeur d'alimentation
        
        Args:
            config: Configuration du contrôleur
            gpio_config: Configuration GPIO
            event_bus: Bus d'événements
        """
        super().__init__(config, event_bus)
        self.gpio_config = gpio_config
        
        # Drivers pour le distributeur
        self.servo_driver = None
        self.sas_relay = None
        
        # État du distributeur
        self.is_open = False
        self.is_feeding = False
        self.current_position = 0  # Position du servo (0-180°)
        self.target_position = 0
        
        # Positions prédéfinies
        self.positions = {
            'closed': 0,      # Fermé
            'half_open': 45,  # Semi-ouvert
            'open': 90,       # Ouvert
            'full_open': 135  # Complètement ouvert
        }
        
        # Configuration de sécurité
        self.safety_lock = True
        self.max_daily_feeds = 3
        self.min_feeding_interval = 3600  # 1 heure minimum entre les repas
        self.feeding_duration = 5.0  # Durée d'ouverture en secondes
        self.max_feeding_duration = 30.0  # Durée maximale de sécurité
        
        # Statistiques
        self.daily_feeds = 0
        self.total_feeds = 0
        self.last_feeding_time = None
        self.feeding_start_time = None
        self.feeding_errors = 0
        
    def initialize(self) -> bool:
        """
        Initialise le contrôleur de distributeur d'alimentation
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du contrôleur de distributeur d'alimentation...")
            
            # Configuration du driver servo
            servo_config = DriverConfig(
                name="feeder_servo",
                pin=self.gpio_config.get('feeder_servo_pin', 18),
                min_pulse_width=500,  # 0.5ms
                max_pulse_width=2500,  # 2.5ms
                frequency=50  # 50Hz
            )
            
            # Configuration du driver relais SAS
            sas_config = DriverConfig(
                name="sas_relay",
                pin=self.gpio_config.get('sas_pin', 20),
                active_high=True,
                initial_state=False
            )
            
            # Initialiser les drivers
            self.servo_driver = ServoDriver(servo_config)
            self.sas_relay = RelayDriver(sas_config)
            
            if not self.servo_driver.initialize():
                self.logger.error("Échec initialisation driver servo distributeur")
                return False
            
            if not self.sas_relay.initialize():
                self.logger.error("Échec initialisation driver relais SAS")
                return False
            
            # Charger la configuration de sécurité
            self.safety_lock = self.config.get('safety_lock', True)
            self.max_daily_feeds = self.config.get('max_daily_feeds', 3)
            self.min_feeding_interval = self.config.get('min_feeding_interval', 3600)
            self.feeding_duration = self.config.get('feeding_duration', 5.0)
            self.max_feeding_duration = self.config.get('max_feeding_duration', 30.0)
            
            # Positionner le servo en position fermée
            self._set_servo_position(self.positions['closed'])
            
            self.state = ControllerState.READY
            self.logger.info("Contrôleur de distributeur d'alimentation initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation contrôleur distributeur: {e}")
            self.state = ControllerState.ERROR
            return False
    
    def update(self) -> bool:
        """
        Met à jour le contrôleur de distributeur d'alimentation
        
        Returns:
            True si la mise à jour réussit, False sinon
        """
        try:
            if self.state != ControllerState.RUNNING:
                return True
            
            # Gérer l'alimentation en cours
            if self.is_feeding and self.feeding_start_time:
                elapsed = time.time() - self.feeding_start_time
                
                # Vérifier la durée maximale de sécurité
                if elapsed > self.max_feeding_duration:
                    self._emergency_stop_feeding()
                    self.logger.warning(f"Arrêt d'urgence alimentation: durée maximale dépassée ({self.max_feeding_duration}s)")
                    return False
                
                # Fermer automatiquement après la durée prévue
                elif elapsed >= self.feeding_duration:
                    self._stop_feeding()
            
            self.update_count += 1
            self.last_update = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour contrôleur distributeur: {e}")
            self.error_count += 1
            self.last_error = e
            return False
    
    def start_feeding(self, food_type: str = "default", quantity: float = 1.0) -> bool:
        """
        Démarre une séquence d'alimentation
        
        Args:
            food_type: Type de nourriture
            quantity: Quantité à distribuer
            
        Returns:
            True si l'alimentation peut démarrer, False sinon
        """
        try:
            # Vérifier les conditions de sécurité
            if not self._can_feed():
                return False
            
            # Vérifier le verrouillage de sécurité
            if self.safety_lock and not self._check_safety_conditions():
                self.logger.warning("Alimentation refusée: conditions de sécurité non remplies")
                return False
            
            # Démarrer l'alimentation
            self._open_feeder()
            self.is_feeding = True
            self.feeding_start_time = time.time()
            self.last_feeding_time = time.time()
            self.daily_feeds += 1
            self.total_feeds += 1
            
            self.logger.info(f"Alimentation démarrée: {food_type} (quantité: {quantity})")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('feeding_started', {
                    'food_type': food_type,
                    'quantity': quantity,
                    'timestamp': time.time()
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage alimentation: {e}")
            self.feeding_errors += 1
            return False
    
    def stop_feeding(self) -> bool:
        """
        Arrête la séquence d'alimentation
        
        Returns:
            True si l'arrêt réussit, False sinon
        """
        try:
            if self.is_feeding:
                self._stop_feeding()
                return True
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt alimentation: {e}")
            return False
    
    def _can_feed(self) -> bool:
        """Vérifie si l'alimentation est possible"""
        try:
            # Vérifier la limite quotidienne
            if self.daily_feeds >= self.max_daily_feeds:
                self.logger.warning(f"Limite quotidienne d'alimentation atteinte: {self.daily_feeds}/{self.max_daily_feeds}")
                return False
            
            # Vérifier l'intervalle minimum
            if self.last_feeding_time:
                time_since_last = time.time() - self.last_feeding_time
                if time_since_last < self.min_feeding_interval:
                    remaining = self.min_feeding_interval - time_since_last
                    self.logger.warning(f"Intervalle minimum non respecté: {remaining:.0f}s restantes")
                    return False
            
            # Vérifier qu'aucune alimentation n'est en cours
            if self.is_feeding:
                self.logger.warning("Alimentation déjà en cours")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur vérification conditions alimentation: {e}")
            return False
    
    def _check_safety_conditions(self) -> bool:
        """Vérifie les conditions de sécurité pour l'alimentation"""
        try:
            # Vérifier que le SAS est activé
            if self.sas_relay and not self.sas_relay.get_state():
                self.logger.warning("SAS non activé - alimentation refusée")
                return False
            
            # Vérifier que le servo est en position fermée
            if self.current_position != self.positions['closed']:
                self.logger.warning("Distributeur pas en position fermée - alimentation refusée")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur vérification sécurité: {e}")
            return False
    
    def _open_feeder(self) -> None:
        """Ouvre le distributeur d'alimentation"""
        try:
            # Activer le SAS
            if self.sas_relay:
                self.sas_relay.set_state(True)
                time.sleep(0.1)  # Attendre l'activation
            
            # Ouvrir le servo
            self._set_servo_position(self.positions['open'])
            self.is_open = True
            
            self.logger.info("Distributeur d'alimentation ouvert")
            
        except Exception as e:
            self.logger.error(f"Erreur ouverture distributeur: {e}")
    
    def _close_feeder(self) -> None:
        """Ferme le distributeur d'alimentation"""
        try:
            # Fermer le servo
            self._set_servo_position(self.positions['closed'])
            self.is_open = False
            
            # Désactiver le SAS après un délai
            if self.sas_relay:
                time.sleep(0.5)  # Attendre la fermeture complète
                self.sas_relay.set_state(False)
            
            self.logger.info("Distributeur d'alimentation fermé")
            
        except Exception as e:
            self.logger.error(f"Erreur fermeture distributeur: {e}")
    
    def _stop_feeding(self) -> None:
        """Arrête l'alimentation"""
        try:
            self._close_feeder()
            self.is_feeding = False
            self.feeding_start_time = None
            
            # Calculer la durée d'alimentation
            if self.last_feeding_time:
                duration = time.time() - self.last_feeding_time
                self.logger.info(f"Alimentation terminée après {duration:.1f}s")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('feeding_stopped', {
                    'daily_feeds': self.daily_feeds,
                    'total_feeds': self.total_feeds,
                    'timestamp': time.time()
                })
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt alimentation: {e}")
    
    def _emergency_stop_feeding(self) -> None:
        """Arrêt d'urgence de l'alimentation"""
        try:
            self._close_feeder()
            self.is_feeding = False
            self.feeding_start_time = None
            self.feeding_errors += 1
            
            self.logger.warning("Arrêt d'urgence de l'alimentation")
            
            # Émettre un événement d'urgence
            if self.event_bus:
                self.event_bus.emit('feeding_emergency_stop', {
                    'timestamp': time.time()
                })
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt d'urgence alimentation: {e}")
    
    def _set_servo_position(self, position: int) -> None:
        """Définit la position du servo"""
        try:
            if self.servo_driver:
                self.servo_driver.set_angle(position)
                self.current_position = position
                self.target_position = position
                
        except Exception as e:
            self.logger.error(f"Erreur positionnement servo: {e}")
    
    def set_position(self, position_name: str) -> bool:
        """
        Définit la position du distributeur
        
        Args:
            position_name: Nom de la position ('closed', 'half_open', 'open', 'full_open')
            
        Returns:
            True si la position est définie, False sinon
        """
        try:
            if position_name not in self.positions:
                self.logger.error(f"Position invalide: {position_name}")
                return False
            
            if self.is_feeding:
                self.logger.warning("Impossible de changer la position pendant l'alimentation")
                return False
            
            self._set_servo_position(self.positions[position_name])
            self.logger.info(f"Position distributeur: {position_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur définition position: {e}")
            return False
    
    def reset_daily_count(self) -> None:
        """Remet à zéro le compteur quotidien d'alimentations"""
        self.daily_feeds = 0
        self.logger.info("Compteur quotidien d'alimentations remis à zéro")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du contrôleur de distributeur d'alimentation
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'controller': 'feeder_sas',
            'state': self.state.value,
            'is_open': self.is_open,
            'is_feeding': self.is_feeding,
            'current_position': self.current_position,
            'target_position': self.target_position,
            'safety_lock': self.safety_lock,
            'max_daily_feeds': self.max_daily_feeds,
            'daily_feeds': self.daily_feeds,
            'total_feeds': self.total_feeds,
            'min_feeding_interval': self.min_feeding_interval,
            'feeding_duration': self.feeding_duration,
            'last_feeding_time': self.last_feeding_time,
            'feeding_errors': self.feeding_errors,
            'positions': self.positions,
            'stats': {
                'update_count': self.update_count,
                'error_count': self.error_count,
                'last_update': self.last_update,
                'last_error': str(self.last_error) if self.last_error else None
            }
        }
    
    def cleanup(self) -> None:
        """Nettoie le contrôleur de distributeur d'alimentation"""
        try:
            # Arrêter toute alimentation en cours
            if self.is_feeding:
                self._stop_feeding()
            
            # Fermer le distributeur
            self._close_feeder()
            
            # Nettoyer les drivers
            if self.servo_driver:
                self.servo_driver.cleanup()
                self.servo_driver = None
            
            if self.sas_relay:
                self.sas_relay.cleanup()
                self.sas_relay = None
            
            self.state = ControllerState.UNINITIALIZED
            self.logger.info("Contrôleur de distributeur d'alimentation nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage contrôleur distributeur: {e}")

