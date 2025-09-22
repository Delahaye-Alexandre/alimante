"""
Driver LCD I2C pour Alimante
Gère l'affichage sur écran LCD I2C (alternative au ST7735)
"""

import time
import logging
from typing import Dict, Any, Optional, List
from .base_driver import BaseDriver, DriverConfig, DriverState

try:
    import smbus
    I2C_AVAILABLE = True
except ImportError:
    # Mode simulation pour Windows
    I2C_AVAILABLE = False
    smbus = None

class I2CLCDDriver(BaseDriver):
    """
    Driver LCD I2C pour l'affichage de données
    Compatible avec les écrans LCD I2C standard (16x2, 20x4, etc.)
    """
    
    def __init__(self, config: DriverConfig, i2c_address: int = 0x27, i2c_bus: int = 1):
        """
        Initialise le driver LCD I2C
        
        Args:
            config: Configuration du driver
            i2c_address: Adresse I2C du LCD (défaut: 0x27)
            i2c_bus: Bus I2C à utiliser (défaut: 1)
        """
        super().__init__(config)
        self.i2c_address = i2c_address
        self.i2c_bus = i2c_bus
        self.bus = None
        
        # Configuration de l'écran
        self.rows = 4
        self.cols = 20
        self.backlight = True
        self.cursor_visible = False
        self.cursor_blink = False
        
        # État de l'écran
        self.current_text = [""] * 4
        self.cursor_row = 0
        self.cursor_col = 0
        
        # Caractères spéciaux
        self.custom_chars = {}
        self.custom_char_count = 0
        
        # Configuration I2C
        self.enable_bit = 0b00000100  # Enable bit
        self.read_write_bit = 0b00000010  # Read/Write bit
        self.register_select_bit = 0b00000001  # Register select bit
        
        # Commandes LCD
        self.LCD_CLEARDISPLAY = 0x01
        self.LCD_RETURNHOME = 0x02
        self.LCD_ENTRYMODESET = 0x04
        self.LCD_DISPLAYCONTROL = 0x08
        self.LCD_CURSORSHIFT = 0x10
        self.LCD_FUNCTIONSET = 0x20
        self.LCD_SETCGRAMADDR = 0x40
        self.LCD_SETDDRAMADDR = 0x80
        
        # Flags pour LCD_DISPLAYCONTROL
        self.LCD_DISPLAYON = 0x04
        self.LCD_DISPLAYOFF = 0x00
        self.LCD_CURSORON = 0x02
        self.LCD_CURSOROFF = 0x00
        self.LCD_BLINKON = 0x01
        self.LCD_BLINKOFF = 0x00
        
        # Flags pour LCD_ENTRYMODESET
        self.LCD_ENTRYRIGHT = 0x00
        self.LCD_ENTRYLEFT = 0x02
        self.LCD_ENTRYSHIFTINCREMENT = 0x01
        self.LCD_ENTRYSHIFTDECREMENT = 0x00
        
        # Flags pour LCD_FUNCTIONSET
        self.LCD_8BITMODE = 0x10
        self.LCD_4BITMODE = 0x00
        self.LCD_2LINE = 0x08
        self.LCD_1LINE = 0x00
        self.LCD_5x10DOTS = 0x04
        self.LCD_5x8DOTS = 0x00
        
    def initialize(self) -> bool:
        """
        Initialise le driver LCD I2C
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not I2C_AVAILABLE:
                self.logger.warning("Mode simulation - I2C non disponible")
                self.state = DriverState.READY
                return True
            
            # Initialiser le bus I2C
            self.bus = smbus.SMBus(self.i2c_bus)
            
            # Initialiser le LCD
            self._lcd_init()
            
            # Configurer l'affichage
            self._lcd_display_control()
            self._lcd_entry_mode_set()
            
            # Effacer l'écran
            self.clear()
            
            self.state = DriverState.READY
            self.logger.info(f"Driver LCD I2C initialisé (adresse: 0x{self.i2c_address:02x})")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation driver LCD I2C: {e}")
            self.state = DriverState.ERROR
            return False
    
    def read(self) -> Dict[str, Any]:
        """
        Lit l'état du driver LCD I2C
        
        Returns:
            Dictionnaire contenant l'état du driver
        """
        try:
            self.read_count += 1
            self.last_update = time.time()
            
            return {
                'driver': 'i2c_lcd',
                'state': self.state.value,
                'i2c_address': f"0x{self.i2c_address:02x}",
                'i2c_bus': self.i2c_bus,
                'rows': self.rows,
                'cols': self.cols,
                'backlight': self.backlight,
                'cursor_visible': self.cursor_visible,
                'cursor_blink': self.cursor_blink,
                'current_text': self.current_text,
                'cursor_position': (self.cursor_row, self.cursor_col),
                'custom_chars': len(self.custom_chars),
                'stats': {
                    'read_count': self.read_count,
                    'error_count': self.error_count,
                    'uptime': time.time() - self.start_time
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lecture driver LCD I2C: {e}")
            self.error_count += 1
            self.last_error = e
            return {'error': str(e)}
    
    def write(self, data: Dict[str, Any]) -> bool:
        """
        Écrit des données vers le driver LCD I2C
        
        Args:
            data: Données à écrire (text, clear, cursor, etc.)
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        try:
            action = data.get('action', 'text')
            
            if action == 'text':
                return self._write_text(data)
            elif action == 'clear':
                return self.clear()
            elif action == 'cursor':
                return self._set_cursor(data)
            elif action == 'backlight':
                return self._set_backlight(data)
            elif action == 'custom_char':
                return self._create_custom_char(data)
            else:
                self.logger.warning(f"Action inconnue: {action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur écriture driver LCD I2C: {e}")
            self.error_count += 1
            self.last_error = e
            return False
    
    def _write_text(self, data: Dict[str, Any]) -> bool:
        """Écrit du texte sur l'écran"""
        try:
            text = data.get('text', '')
            row = data.get('row', 0)
            col = data.get('col', 0)
            clear = data.get('clear', False)
            
            if clear:
                self.clear()
            
            # Positionner le curseur
            self.set_cursor(row, col)
            
            # Écrire le texte
            for char in text:
                self._lcd_write_char(ord(char))
                self.cursor_col += 1
                
                # Gérer le retour à la ligne
                if self.cursor_col >= self.cols:
                    self.cursor_col = 0
                    self.cursor_row += 1
                    if self.cursor_row >= self.rows:
                        self.cursor_row = 0
            
            # Mettre à jour le texte actuel
            if row < self.rows:
                self.current_text[row] = text
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur écriture texte: {e}")
            return False
    
    def _set_cursor(self, data: Dict[str, Any]) -> bool:
        """Configure le curseur"""
        try:
            visible = data.get('visible', self.cursor_visible)
            blink = data.get('blink', self.cursor_blink)
            
            self.cursor_visible = visible
            self.cursor_blink = blink
            
            self._lcd_display_control()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur configuration curseur: {e}")
            return False
    
    def _set_backlight(self, data: Dict[str, Any]) -> bool:
        """Configure le rétroéclairage"""
        try:
            self.backlight = data.get('enabled', True)
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur configuration rétroéclairage: {e}")
            return False
    
    def _create_custom_char(self, data: Dict[str, Any]) -> bool:
        """Crée un caractère personnalisé"""
        try:
            char_code = data.get('char_code', 0)
            pattern = data.get('pattern', [])
            
            if char_code < 0 or char_code > 7:
                self.logger.error("Code de caractère invalide (0-7)")
                return False
            
            if len(pattern) != 8:
                self.logger.error("Pattern invalide (8 bytes requis)")
                return False
            
            # Sauvegarder le caractère personnalisé
            self.custom_chars[char_code] = pattern
            self.custom_char_count += 1
            
            # Envoyer au LCD
            self._lcd_set_cgram_addr(char_code * 8)
            for byte in pattern:
                self._lcd_write_char(byte)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur création caractère personnalisé: {e}")
            return False
    
    def clear(self) -> bool:
        """Efface l'écran"""
        try:
            if not I2C_AVAILABLE:
                self.current_text = [""] * self.rows
                return True
            
            self._lcd_write_command(self.LCD_CLEARDISPLAY)
            time.sleep(0.002)  # Attendre la commande
            
            self.current_text = [""] * self.rows
            self.cursor_row = 0
            self.cursor_col = 0
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur effacement écran: {e}")
            return False
    
    def set_cursor(self, row: int, col: int) -> bool:
        """
        Positionne le curseur
        
        Args:
            row: Ligne (0 à rows-1)
            col: Colonne (0 à cols-1)
            
        Returns:
            True si la position est définie, False sinon
        """
        try:
            if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
                self.logger.error(f"Position curseur invalide: ({row}, {col})")
                return False
            
            self.cursor_row = row
            self.cursor_col = col
            
            if I2C_AVAILABLE:
                self._lcd_set_cursor_position(row, col)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur position curseur: {e}")
            return False
    
    def write_line(self, line: int, text: str, clear_line: bool = True) -> bool:
        """
        Écrit une ligne de texte
        
        Args:
            line: Numéro de ligne (0 à rows-1)
            text: Texte à écrire
            col: Colonne de départ (0 à cols-1)
            
        Returns:
            True si l'écriture réussit, False sinon
        """
        try:
            if line < 0 or line >= self.rows:
                self.logger.error(f"Ligne invalide: {line}")
                return False
            
            # Tronquer le texte si nécessaire
            text = text[:self.cols]
            
            # Effacer la ligne si demandé
            if clear_line:
                self.write({'action': 'text', 'text': ' ' * self.cols, 'row': line, 'col': 0})
            
            # Écrire le texte
            return self.write({'action': 'text', 'text': text, 'row': line, 'col': 0})
            
        except Exception as e:
            self.logger.error(f"Erreur écriture ligne: {e}")
            return False
    
    def display_message(self, lines: List[str], clear: bool = True) -> bool:
        """
        Affiche un message sur plusieurs lignes
        
        Args:
            lines: Liste des lignes à afficher
            clear: Effacer l'écran avant d'afficher
            
        Returns:
            True si l'affichage réussit, False sinon
        """
        try:
            if clear:
                self.clear()
            
            for i, line in enumerate(lines[:self.rows]):
                self.write_line(i, line, clear_line=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur affichage message: {e}")
            return False
    
    def _lcd_init(self) -> None:
        """Initialise le LCD"""
        try:
            # Attendre que le LCD soit prêt
            time.sleep(0.05)
            
            # Initialisation en 4 bits
            self._lcd_write_4bits(0x03)
            time.sleep(0.0045)
            
            self._lcd_write_4bits(0x03)
            time.sleep(0.0045)
            
            self._lcd_write_4bits(0x03)
            time.sleep(0.00015)
            
            self._lcd_write_4bits(0x02)
            
            # Configuration du LCD
            self._lcd_write_command(self.LCD_FUNCTIONSET | self.LCD_4BITMODE | self.LCD_2LINE | self.LCD_5x8DOTS)
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation LCD: {e}")
            raise
    
    def _lcd_display_control(self) -> None:
        """Configure l'affichage du LCD"""
        try:
            display_control = self.LCD_DISPLAYCONTROL | self.LCD_DISPLAYON
            
            if self.cursor_visible:
                display_control |= self.LCD_CURSORON
            
            if self.cursor_blink:
                display_control |= self.LCD_BLINKON
            
            self._lcd_write_command(display_control)
            
        except Exception as e:
            self.logger.error(f"Erreur configuration affichage: {e}")
            raise
    
    def _lcd_entry_mode_set(self) -> None:
        """Configure le mode d'entrée du LCD"""
        try:
            entry_mode = self.LCD_ENTRYMODESET | self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT
            self._lcd_write_command(entry_mode)
            
        except Exception as e:
            self.logger.error(f"Erreur configuration mode entrée: {e}")
            raise
    
    def _lcd_write_command(self, command: int) -> None:
        """Écrit une commande au LCD"""
        try:
            self._lcd_write_4bits(command >> 4)
            self._lcd_write_4bits(command & 0x0F)
            
        except Exception as e:
            self.logger.error(f"Erreur écriture commande: {e}")
            raise
    
    def _lcd_write_char(self, char: int) -> None:
        """Écrit un caractère au LCD"""
        try:
            self._lcd_write_4bits((char >> 4) | 0x08)
            self._lcd_write_4bits((char & 0x0F) | 0x08)
            
        except Exception as e:
            self.logger.error(f"Erreur écriture caractère: {e}")
            raise
    
    def _lcd_write_4bits(self, data: int) -> None:
        """Écrit 4 bits au LCD"""
        try:
            if not I2C_AVAILABLE:
                return
            
            # Préparer les données
            byte = data & 0x0F
            if self.backlight:
                byte |= 0x08
            
            # Envoyer les données
            self.bus.write_byte(self.i2c_address, byte | self.enable_bit)
            time.sleep(0.0001)
            self.bus.write_byte(self.i2c_address, byte & ~self.enable_bit)
            time.sleep(0.0001)
            
        except Exception as e:
            self.logger.error(f"Erreur écriture 4 bits: {e}")
            raise
    
    def _lcd_set_cursor_position(self, row: int, col: int) -> None:
        """Positionne le curseur"""
        try:
            # Adresses DDRAM pour différentes tailles d'écran
            row_offsets = [0x00, 0x40, 0x14, 0x54]
            
            if row < len(row_offsets):
                address = row_offsets[row] + col
                self._lcd_write_command(self.LCD_SETDDRAMADDR | address)
            
        except Exception as e:
            self.logger.error(f"Erreur position curseur: {e}")
            raise
    
    def _lcd_set_cgram_addr(self, address: int) -> None:
        """Définit l'adresse CGRAM"""
        try:
            self._lcd_write_command(self.LCD_SETCGRAMADDR | address)
            
        except Exception as e:
            self.logger.error(f"Erreur adresse CGRAM: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du driver LCD I2C
        
        Returns:
            Dictionnaire contenant le statut
        """
        return self.read()
    
    def cleanup(self) -> None:
        """Nettoie le driver LCD I2C"""
        try:
            # Effacer l'écran
            self.clear()
            
            # Éteindre le rétroéclairage
            self.backlight = False
            
            self.state = DriverState.DISABLED
            self.logger.info("Driver LCD I2C nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage driver LCD I2C: {e}")
