"""
Interface pour l'encodeur rotatif
Gère la navigation et les interactions utilisateur
"""

import time
import logging
import threading
from typing import Dict, Any, Optional
import os
import sys

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.event_bus import EventBus

try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
except ImportError:
    RASPBERRY_PI = False
    GPIO = None

class EncoderInterface:
    """
    Interface pour l'encodeur rotatif et le bouton
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[EventBus] = None):
        """
        Initialise l'interface encodeur
        
        Args:
            config: Configuration de l'encodeur
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus or EventBus()
        self.logger = logging.getLogger(__name__)
        
        # Charger la configuration GPIO depuis le fichier JSON
        from utils.gpio_config import get_ui_pin
        
        # Configuration GPIO depuis la configuration JSON
        self.pin_a = get_ui_pin('encoder_clk')  # CLK
        self.pin_b = get_ui_pin('encoder_dt')   # DT
        self.pin_btn = get_ui_pin('encoder_sw') # SW (bouton)
        
        # État de l'interface
        self.is_running = False
        self.last_a_state = 0
        self.last_b_state = 0
        self.last_btn_state = 0
        self.encoder_value = 0
        self.btn_pressed = False
        self.btn_press_time = 0
        
        # Thread de surveillance
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Configuration des interruptions
        self.debounce_time = 0.01  # 10ms
        self.last_interrupt = 0
        
        # Statistiques
        self.stats = {
            'rotations': 0,
            'presses': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Initialiser GPIO
        self._initialize_gpio()
    
    
    def _initialize_gpio(self) -> None:
        """Initialise les pins GPIO"""
        try:
            if not RASPBERRY_PI:
                self.logger.warning("Mode simulation: GPIO non disponible")
                return
            
            # Configuration GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Log des pins utilisées
            self.logger.info(f"Configuration encodeur: CLK={self.pin_a}, DT={self.pin_b}, SW={self.pin_btn}")
            
            # Configurer les pins d'entrée avec pull-up
            GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.pin_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Lire l'état initial
            self.last_a_state = GPIO.input(self.pin_a)
            self.last_b_state = GPIO.input(self.pin_b)
            self.last_btn_state = GPIO.input(self.pin_btn)
            
            self.logger.info(f"GPIO encodeur initialisé (A:{self.pin_a}, B:{self.pin_b}, BTN:{self.pin_btn})")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation GPIO encodeur: {e}")
            self.stats['errors'] += 1
    
    def start(self) -> bool:
        """
        Démarre l'interface encodeur
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not RASPBERRY_PI:
                self.logger.warning("Mode simulation: interface encodeur démarrée")
                self.is_running = True
                return True
            
            # Démarrer le thread de surveillance
            self.is_running = True
            self.stop_event.clear()
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            self.logger.info("Interface encodeur démarrée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage interface encodeur: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête l'interface encodeur"""
        try:
            self.is_running = False
            self.stop_event.set()
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2.0)
            
            if RASPBERRY_PI:
                # Nettoyer les pins GPIO
                GPIO.cleanup([self.pin_a, self.pin_b, self.pin_btn])
            
            self.logger.info("Interface encodeur arrêtée")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt interface encodeur: {e}")
            self.stats['errors'] += 1
    
    def _monitor_loop(self) -> None:
        """Boucle de surveillance des pins GPIO"""
        while self.is_running and not self.stop_event.is_set():
            try:
                if not RASPBERRY_PI:
                    time.sleep(0.1)
                    continue
                
                # Lire l'état actuel des pins
                current_a = GPIO.input(self.pin_a)
                current_b = GPIO.input(self.pin_b)
                current_btn = GPIO.input(self.pin_btn)
                
                # Détecter la rotation de l'encodeur
                if current_a != self.last_a_state:
                    if current_a == 0 and self.last_a_state == 1:  # Front descendant sur A
                        if current_b == 1:  # B est haut
                            self._on_encoder_turned(1)  # Sens horaire
                        else:  # B est bas
                            self._on_encoder_turned(-1)  # Sens anti-horaire
                    
                    self.last_a_state = current_a
                
                # Détecter la pression du bouton
                if current_btn != self.last_btn_state:
                    if current_btn == 0 and self.last_btn_state == 1:  # Front descendant
                        self._on_encoder_pressed()
                    
                    self.last_btn_state = current_btn
                
                # Petite pause pour éviter la surcharge CPU
                time.sleep(0.001)  # 1ms
                
            except Exception as e:
                self.logger.error(f"Erreur boucle surveillance encodeur: {e}")
                self.stats['errors'] += 1
                time.sleep(0.1)
    
    def _on_encoder_turned(self, direction: int) -> None:
        """
        Gestionnaire de rotation de l'encodeur
        
        Args:
            direction: 1 pour sens horaire, -1 pour sens anti-horaire
        """
        try:
            current_time = time.time()
            
            # Vérifier le debounce
            if current_time - self.last_interrupt < self.debounce_time:
                return
            
            self.last_interrupt = current_time
            
            # Mettre à jour la valeur de l'encodeur
            self.encoder_value += direction
            self.stats['rotations'] += 1
            
            # Émettre un événement
            self.event_bus.emit('encoder_turned', {
                'direction': direction,
                'value': self.encoder_value,
                'timestamp': current_time
            })
            
            self.logger.debug(f"Encodeur tourné: {direction} (valeur: {self.encoder_value})")
            
        except Exception as e:
            self.logger.error(f"Erreur traitement rotation encodeur: {e}")
            self.stats['errors'] += 1
    
    def _on_encoder_pressed(self) -> None:
        """Gestionnaire de pression du bouton"""
        try:
            current_time = time.time()
            
            # Vérifier le debounce
            if current_time - self.last_interrupt < self.debounce_time:
                return
            
            self.last_interrupt = current_time
            
            # Marquer le bouton comme pressé
            self.btn_pressed = True
            self.btn_press_time = current_time
            self.stats['presses'] += 1
            
            # Émettre un événement
            self.event_bus.emit('encoder_pressed', {
                'pressed': True,
                'timestamp': current_time
            })
            
            self.logger.debug("Bouton encodeur pressé")
            
        except Exception as e:
            self.logger.error(f"Erreur traitement pression bouton: {e}")
            self.stats['errors'] += 1
    
    def get_encoder_value(self) -> int:
        """
        Retourne la valeur actuelle de l'encodeur
        
        Returns:
            Valeur de l'encodeur
        """
        return self.encoder_value
    
    def reset_encoder_value(self) -> None:
        """Remet à zéro la valeur de l'encodeur"""
        self.encoder_value = 0
        self.logger.debug("Valeur encodeur remise à zéro")
    
    def is_button_pressed(self) -> bool:
        """
        Vérifie si le bouton est actuellement pressé
        
        Returns:
            True si pressé, False sinon
        """
        return self.btn_pressed
    
    def is_running(self) -> bool:
        """
        Vérifie si l'interface encodeur est en cours d'exécution
        
        Returns:
            True si en cours d'exécution, False sinon
        """
        return self.is_running
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de l'interface encodeur
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_running': self.is_running,
            'encoder_value': self.encoder_value,
            'button_pressed': self.btn_pressed,
            'pins': {
                'a': self.pin_a,
                'b': self.pin_b,
                'btn': self.pin_btn
            },
            'raspberry_pi': RASPBERRY_PI,
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie les ressources de l'interface encodeur"""
        try:
            self.stop()
            self.logger.info("Interface encodeur nettoyée")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage interface encodeur: {e}")
