"""
Driver pour l'écran TFT ST7735 (Azdelivery)
Basé sur l'implémentation fonctionnelle d'alimante_menu.py
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple, List
from .base_driver import BaseDriver, DriverConfig, DriverState

try:
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    RASPBERRY_PI = True
except ImportError:
    # Mode simulation pour Windows
    RASPBERRY_PI = False
    st7735 = None
    Image = None
    ImageDraw = None
    ImageFont = None

class ST7735Driver(BaseDriver):
    """
    Driver pour l'écran TFT ST7735
    Basé sur l'implémentation fonctionnelle d'alimante_menu.py
    """
    
    def __init__(self, config: DriverConfig, dc_pin: int, rst_pin: int, 
                 port: int = 0, cs: int = 0, width: int = 128, height: int = 160):
        """
        Initialise le driver ST7735
        
        Args:
            config: Configuration du driver
            dc_pin: Pin DC (Data/Command)
            rst_pin: Pin RST (Reset)
            port: Port SPI (0)
            cs: Chip Select (0)
            width: Largeur de l'écran
            height: Hauteur de l'écran
        """
        super().__init__(config)
        self.dc_pin = dc_pin
        self.rst_pin = rst_pin
        self.port = port
        self.cs = cs
        self.width = width
        self.height = height
        
        self.display = None
        self.current_rotation = 270  # Rotation par défaut comme dans alimante_menu
        self.current_backlight = True
        self.current_contrast = 50
        
        # Couleurs RGB (comme dans alimante_menu)
        self.colors = {
            "black": (0, 0, 0),
            "white": (255, 255, 255),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
            "orange": (255, 165, 0),
            "pink": (255, 192, 203),
            "gray": (128, 128, 128),
            "dark_gray": (64, 64, 64),
            "light_gray": (192, 192, 192)
        }
        
    def initialize(self) -> bool:
        """
        Initialise le driver ST7735
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.config.enabled:
                self.state = DriverState.DISABLED
                return True
                
            if not RASPBERRY_PI or not st7735:
                self.logger.error("ST7735 nécessite un Raspberry Pi avec st7735 - pas de simulation")
                self.state = DriverState.ERROR
                return False
            
            self._init_display_hardware()
            
            self.state = DriverState.READY
            self.logger.info(f"ST7735 initialisé ({self.width}x{self.height})")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation ST7735: {e}")
            self.state = DriverState.ERROR
            return False
    
    def _init_display_hardware(self) -> None:
        """Initialise l'écran ST7735 avec la bibliothèque st7735"""
        try:
            self.logger.info("Initialisation de l'écran ST7735...")
            self.display = st7735.ST7735(
                port=self.port,
                cs=self.cs,
                dc=self.dc_pin,
                rst=self.rst_pin,
                rotation=self.current_rotation,
                invert=False,  # Pas d'inversion comme dans alimante_menu
                bgr=False      # Format RGB standard
            )
            self.display.begin()
            self.logger.info(f"Écran initialisé: {self.display.width}x{self.display.height}")
            self.logger.info(f"Format: RGB standard, Inversion: Désactivée, Rotation: {self.current_rotation}°")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation écran: {e}")
            raise
    
    
    def read(self) -> Dict[str, Any]:
        """
        Lit l'état actuel de l'écran
        
        Returns:
            Dictionnaire contenant l'état de l'écran
        """
        if not self.is_ready():
            raise DriverError("ST7735 non initialisé")
        
        return {
            "width": self.width,
            "height": self.height,
            "rotation": self.current_rotation,
            "backlight": self.current_backlight,
            "contrast": self.current_contrast,
            "timestamp": time.time(),
            "sensor": "st7735",
            "unit": "pixels"
        }
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Écrit des données vers l'écran
        
        Args:
            data: Données contenant command, text, graphics, etc.
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        if not self.is_ready():
            raise DriverError("ST7735 non initialisé")
        
        try:
            command = data.get("command")
            
            if command == "clear":
                return self.clear_screen(data.get("color", "black"))
            elif command == "text":
                return self._draw_text(data)
            elif command == "image":
                return self._display_image(data)
            elif command == "rotation":
                return self._set_rotation(data.get("rotation", 270))
            elif command == "backlight":
                return self._set_backlight(data.get("state", True))
            elif command == "contrast":
                return self._set_contrast(data.get("value", 50))
            else:
                self.logger.error(f"Commande inconnue: {command}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur écriture ST7735: {e}")
            return False
    
    def clear_screen(self, color: str = "black") -> bool:
        """
        Efface l'écran avec une couleur
        
        Args:
            color: Couleur de fond (nom de couleur)
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not RASPBERRY_PI or not self.display:
                self.logger.info(f"Simulation clear screen: {color}")
                return True
            
            # Créer une image noire comme dans alimante_menu
            image = Image.new("RGB", (self.display.width, self.display.height), self.colors.get(color, (0, 0, 0)))
            self.display.display(image)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur clear screen: {e}")
            return False
    
    def _draw_text(self, data: Dict[str, Any]) -> bool:
        """Dessine du texte sur l'écran comme dans alimante_menu"""
        try:
            text = data.get("text", "")
            x = data.get("x", 0)
            y = data.get("y", 0)
            color = data.get("color", "white")
            font_size = data.get("size", "default")
            
            if not RASPBERRY_PI or not self.display:
                self.logger.info(f"Simulation texte: '{text}' à ({x},{y}) couleur {color}")
                return True
            
            # Créer une image comme dans alimante_menu
            image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Utiliser la police par défaut comme dans alimante_menu
            font = ImageFont.load_default()
            
            # Dessiner le texte
            color_value = self.colors.get(color, (255, 255, 255))
            draw.text((x, y), text, fill=color_value, font=font)
            
            # Afficher l'image
            self.display.display(image)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur dessin texte: {e}")
            return False
    
    def _display_image(self, data: Dict[str, Any]) -> bool:
        """Affiche une image complète comme dans alimante_menu"""
        try:
            image_data = data.get("image_data")
            title = data.get("title", "")
            message = data.get("message", "")
            color = data.get("color", "white")
            
            if not RASPBERRY_PI or not self.display:
                self.logger.info(f"Simulation image: {title} - {message}")
                return True
            
            # Créer une image comme dans alimante_menu
            image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            if title:
                # Centrer le titre comme dans alimante_menu
                bbox = draw.textbbox((0, 0), title, font=font)
                title_width = bbox[2] - bbox[0]
                x_title = (self.display.width - title_width) // 2
                draw.text((x_title, 20), title, fill=self.colors.get(color, (255, 255, 255)), font=font)
            
            if message:
                # Centrer le message
                bbox = draw.textbbox((0, 0), message, font=font)
                msg_width = bbox[2] - bbox[0]
                x_msg = (self.display.width - msg_width) // 2
                draw.text((x_msg, 50), message, fill=(255, 255, 255), font=font)
            
            # Afficher l'image
            self.display.display(image)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur affichage image: {e}")
            return False
    
    def show_message(self, title: str, message: str, color: str = "white") -> bool:
        """
        Affiche un message sur l'écran comme dans alimante_menu
        
        Args:
            title: Titre du message
            message: Contenu du message
            color: Couleur du titre
            
        Returns:
            True si succès, False sinon
        """
        return self._display_image({
            "title": title,
            "message": message,
            "color": color
        })
    
    def _set_rotation(self, rotation: int) -> bool:
        """Définit la rotation de l'écran"""
        try:
            self.current_rotation = rotation % 4
            self.logger.info(f"Rotation écran définie à {self.current_rotation * 90}°")
            return True
        except Exception as e:
            self.logger.error(f"Erreur rotation: {e}")
            return False
    
    def _set_backlight(self, state: bool) -> bool:
        """Définit l'état du rétroéclairage"""
        try:
            self.current_backlight = state
            self.logger.info(f"Rétroéclairage {'activé' if state else 'désactivé'}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur rétroéclairage: {e}")
            return False
    
    def _set_contrast(self, value: int) -> bool:
        """Définit le contraste de l'écran"""
        try:
            self.current_contrast = max(0, min(100, value))
            self.logger.info(f"Contraste défini à {self.current_contrast}%")
            return True
        except Exception as e:
            self.logger.error(f"Erreur contraste: {e}")
            return False
    
    def get_size(self) -> Tuple[int, int]:
        """Retourne la taille de l'écran"""
        if self.display:
            return (self.display.width, self.display.height)
        return (self.width, self.height)
    
    def get_rotation(self) -> int:
        """Retourne la rotation actuelle"""
        return self.current_rotation
    
    def cleanup(self) -> None:
        """Nettoie les ressources de l'écran"""
        if self.display:
            try:
                # Effacer l'écran avant de fermer
                self.clear_screen("black")
            except:
                pass
        
        super().cleanup()
