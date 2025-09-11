"""
Driver pour l'encodeur rotatif (navigation menu)
Basé sur l'implémentation fonctionnelle d'alimante_menu.py
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from .base_driver import BaseDriver, DriverConfig, DriverState

try:
    from gpiozero import RotaryEncoder, Button
    RASPBERRY_PI = True
except ImportError:
    # Mode simulation pour Windows
    RASPBERRY_PI = False
    RotaryEncoder = None
    Button = None

class RotaryEncoderDriver(BaseDriver):
    """
    Driver pour l'encodeur rotatif KY-040
    Basé sur l'implémentation fonctionnelle d'alimante_menu.py
    """
    
    def __init__(self, config: DriverConfig, clk_pin: int, dt_pin: int, sw_pin: int):
        """
        Initialise le driver d'encodeur rotatif
        
        Args:
            config: Configuration du driver
            clk_pin: Pin CLK (Clock)
            dt_pin: Pin DT (Data)
            sw_pin: Pin SW (Switch/Button)
        """
        super().__init__(config)
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        
        # Objets gpiozero
        self.encoder = None
        self.button = None
        
        # État de l'encodeur
        self.position = 0
        self.counter = 0
        
        # Callbacks
        self.rotation_callback = None
        self.button_callback = None
        
        # Configuration
        self.step_size = 1
        self.min_position = -1000
        self.max_position = 1000
        
    def initialize(self) -> bool:
        """
        Initialise le driver d'encodeur rotatif
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.config.enabled:
                self.state = DriverState.DISABLED
                return True
                
            if not RASPBERRY_PI or not RotaryEncoder or not Button:
                self.logger.error("Encodeur rotatif nécessite un Raspberry Pi avec gpiozero - pas de simulation")
                self.state = DriverState.ERROR
                return False
            
            self._init_gpiozero()
            
            self.state = DriverState.READY
            self.logger.info(f"Encodeur rotatif initialisé (CLK:{self.clk_pin}, DT:{self.dt_pin}, SW:{self.sw_pin})")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation encodeur: {e}")
            self.state = DriverState.ERROR
            return False
    
    def _init_gpiozero(self) -> None:
        """Initialise l'encodeur avec gpiozero comme dans alimante_menu"""
        try:
            self.logger.info("Initialisation de l'encodeur rotatif avec gpiozero...")
            
            # Création de l'encodeur comme dans alimante_menu
            self.encoder = RotaryEncoder(
                a=self.clk_pin,
                b=self.dt_pin,
                max_steps=0
            )
            
            # Création du bouton
            self.button = Button(self.sw_pin, pull_up=True)
            
            # Configuration des callbacks
            self.encoder.when_rotated = self._on_rotation
            self.button.when_pressed = self._on_button_pressed
            
            self.logger.info("Encodeur et bouton initialisés avec gpiozero")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation gpiozero: {e}")
            raise
    
    
    def _on_rotation(self) -> None:
        """Callback de rotation de l'encodeur (comme dans alimante_menu)"""
        try:
            # Sauvegarde de l'ancien compteur
            old_counter = self.counter
            
            # Mise à jour du compteur
            self.counter = self.encoder.steps
            
            # Mise à jour de la position (INVERSÉ comme dans alimante_menu)
            if self.encoder.steps > old_counter:
                # Rotation horaire = position vers le bas (inversé)
                self.position = max(self.min_position, self.position - self.step_size)
            else:
                # Rotation anti-horaire = position vers le haut (inversé)
                self.position = min(self.max_position, self.position + self.step_size)
            
            # Appeler le callback si défini
            if self.rotation_callback:
                try:
                    direction = 1 if self.encoder.steps > old_counter else -1
                    self.rotation_callback(direction, self.position, old_counter)
                except Exception as e:
                    self.logger.error(f"Erreur callback rotation: {e}")
            
            self.logger.debug(f"Rotation encodeur: {direction}, position: {self.position}")
            
        except Exception as e:
            self.logger.error(f"Erreur callback rotation: {e}")
    
    def _on_button_pressed(self) -> None:
        """Callback d'appui du bouton (comme dans alimante_menu)"""
        try:
            # Appeler le callback si défini
            if self.button_callback:
                try:
                    self.button_callback(self.position)
                except Exception as e:
                    self.logger.error(f"Erreur callback bouton: {e}")
            
            self.logger.debug(f"Bouton encodeur pressé, position: {self.position}")
            
        except Exception as e:
            self.logger.error(f"Erreur callback bouton: {e}")
    
    def read(self) -> Dict[str, Any]:
        """
        Lit l'état actuel de l'encodeur
        
        Returns:
            Dictionnaire contenant position, button_state
        """
        if not self.is_ready():
            raise DriverError("Encodeur non initialisé")
        
        button_pressed = False
        if self.button:
            button_pressed = self.button.is_pressed
        
        return {
            "position": self.position,
            "button_pressed": button_pressed,
            "timestamp": time.time(),
            "sensor": "rotary_encoder",
            "unit": "steps"
        }
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Écrit des données vers l'encodeur (configuration)
        
        Args:
            data: Données contenant callbacks, limits, etc.
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        if not self.is_ready():
            raise DriverError("Encodeur non initialisé")
        
        try:
            # Configuration des callbacks
            if "rotation_callback" in data:
                self.rotation_callback = data["rotation_callback"]
            
            if "button_callback" in data:
                self.button_callback = data["button_callback"]
            
            # Configuration des limites
            if "min_position" in data:
                self.min_position = data["min_position"]
            
            if "max_position" in data:
                self.max_position = data["max_position"]
            
            # Configuration du pas
            if "step_size" in data:
                self.step_size = max(1, data["step_size"])
            
            # Reset de position
            if "reset_position" in data and data["reset_position"]:
                self.position = 0
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur écriture encodeur: {e}")
            return False
    
    def set_rotation_callback(self, callback: Callable[[int, int, int], None]) -> None:
        """
        Définit le callback de rotation
        
        Args:
            callback: Fonction appelée lors de la rotation
                     Signature: callback(direction, new_position, old_position)
        """
        self.rotation_callback = callback
    
    def set_button_callback(self, callback: Callable[[int], None]) -> None:
        """
        Définit le callback de bouton
        
        Args:
            callback: Fonction appelée lors de la pression
                     Signature: callback(position)
        """
        self.button_callback = callback
    
    def get_position(self) -> int:
        """
        Retourne la position actuelle
        
        Returns:
            Position actuelle
        """
        return self.position
    
    def set_position(self, position: int) -> bool:
        """
        Définit la position de l'encodeur
        
        Args:
            position: Nouvelle position
            
        Returns:
            True si succès, False sinon
        """
        try:
            self.position = max(self.min_position, min(self.max_position, position))
            self.logger.info(f"Position encodeur définie à {self.position}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur définition position: {e}")
            return False
    
    def reset_position(self) -> bool:
        """
        Remet la position à zéro
        
        Returns:
            True si succès, False sinon
        """
        return self.set_position(0)
    
    def is_button_pressed(self) -> bool:
        """
        Vérifie si le bouton est pressé
        
        Returns:
            True si pressé, False sinon
        """
        if self.button:
            return self.button.is_pressed
        return False
    
    def cleanup(self) -> None:
        """Nettoie les ressources de l'encodeur"""
        if self.encoder:
            try:
                self.encoder.close()
            except:
                pass
        
        if self.button:
            try:
                self.button.close()
            except:
                pass
        
        super().cleanup()