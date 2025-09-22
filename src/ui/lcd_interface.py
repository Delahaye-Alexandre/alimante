"""
Interface LCD pour l'affichage des données Alimante
Utilise le driver ST7735 pour l'affichage local
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import os
import sys

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.event_bus import EventBus

try:
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    from controllers.drivers.st7735_driver import ST7735Driver
    from controllers.drivers.base_driver import DriverConfig
    RASPBERRY_PI = True
except ImportError:
    # Mode simulation pour Windows
    RASPBERRY_PI = False
    st7735 = None
    Image = None
    ImageDraw = None
    ImageFont = None
    ST7735Driver = None
    DriverConfig = None

class ScreenType(Enum):
    """Types d'écrans disponibles"""
    HOME = "home"
    SENSORS = "sensors"
    CONTROLS = "controls"
    CONFIG = "config"
    ALERTS = "alerts"
    TERRARIUMS = "terrariums"
    SPECIES = "species"

class LCDInterface:
    """
    Interface LCD pour l'affichage des données
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[EventBus] = None):
        """
        Initialise l'interface LCD
        
        Args:
            config: Configuration de l'écran LCD
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus or EventBus()
        self.logger = logging.getLogger(__name__)
        
        # État de l'interface
        self.is_running = False
        self.current_screen = ScreenType.HOME
        self.display_data = {}
        self.last_update = 0
        
        # Navigation
        self.terrarium_index = 0
        self.species_index = 0
        self.terrariums = []
        self.species = []
        
        # Configuration d'affichage
        self.width = config.get('width', 128)
        self.height = config.get('height', 160)
        self.rotation = config.get('rotation', 0)
        self.brightness = config.get('brightness', 100)
        
        # Statistiques (initialiser avant _initialize_driver)
        self.stats = {
            'updates': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Driver LCD
        self.lcd_driver = None
        self._initialize_driver()
        
        # Thread de mise à jour
        self.update_thread = None
        self.stop_event = threading.Event()
        
        # Couleurs (format RGB565)
        self.colors = {
            'black': 0x0000,
            'white': 0xFFFF,
            'red': 0xF800,
            'green': 0x07E0,
            'blue': 0x001F,
            'yellow': 0xFFE0,
            'cyan': 0x07FF,
            'magenta': 0xF81F,
            'orange': 0xFC00,
            'gray': 0x8410,
            'dark_gray': 0x4208,
            'light_gray': 0xC618
        }
    
    def _initialize_driver(self) -> None:
        """Initialise le driver LCD - Utilise la configuration JSON"""
        try:
            if not RASPBERRY_PI:
                self.logger.warning("Mode simulation: driver ST7735 non disponible")
                return
            
            # Charger la configuration GPIO depuis le fichier JSON
            from utils.gpio_config import get_ui_pin
            
            # Configuration des pins depuis la configuration JSON
            reset_pin = get_ui_pin('st7735_rst')
            a0_pin = get_ui_pin('st7735_dc')
            cs_pin = get_ui_pin('st7735_cs')
            
            # Initialiser directement avec st7735 (comme dans alimante_menu_improved.py)
            self.lcd_driver = st7735.ST7735(
                port=0,
                cs=cs_pin,
                dc=a0_pin,
                rst=reset_pin,
                rotation=90,   # Rotation comme dans alimante_menu_improved.py
                invert=False,   # Inversion de l'affichage
                bgr=False      # Format RGB standard
            )
            self.lcd_driver.begin()
            
            self.logger.info(f"Driver LCD ST7735 initialisé: {self.lcd_driver.width}x{self.lcd_driver.height}")
            self.logger.info("   • Format: RGB standard")
            self.logger.info("   • Inversion: Désactivée") 
            self.logger.info("   • Rotation: 90°")
                
        except Exception as e:
            self.logger.error(f"Erreur initialisation driver LCD: {e}")
            self.stats['errors'] += 1
            self.lcd_driver = None
    
    
    def start(self) -> bool:
        """
        Démarre l'interface LCD
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.lcd_driver:
                self.logger.warning("Driver LCD non disponible - mode simulation")
                self.is_running = True
                return True
            
            # L'objet st7735.ST7735 n'a pas de méthode start()
            # Il est déjà initialisé dans _initialize_driver()
            self.logger.info("Driver LCD ST7735 prêt")
            
            # Démarrer le thread de mise à jour
            self.is_running = True
            self.stop_event.clear()
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            # Afficher l'écran d'accueil
            self._display_home_screen()
            
            self.logger.info("Interface LCD démarrée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage interface LCD: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête l'interface LCD"""
        try:
            self.is_running = False
            self.stop_event.set()
            
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=2.0)
            
            # Nettoyer l'écran avant l'arrêt
            if self.lcd_driver:
                try:
                    # Créer une image noire pour effacer l'écran
                    black_image = Image.new("RGB", (128, 160), (0, 0, 0))
                    self.lcd_driver.display(black_image)
                    self.logger.info("Écran LCD nettoyé")
                except Exception as e:
                    self.logger.warning(f"Erreur nettoyage écran: {e}")
                
                self.logger.info("Driver LCD ST7735 fermé")
            
            self.logger.info("Interface LCD arrêtée")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt interface LCD: {e}")
            self.stats['errors'] += 1
    
    def _update_loop(self) -> None:
        """Boucle de mise à jour de l'affichage"""
        while self.is_running and not self.stop_event.is_set():
            try:
                # Mettre à jour l'affichage selon l'écran actuel
                self._update_display()
                
                # Attendre avant la prochaine mise à jour
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Erreur boucle mise à jour LCD: {e}")
                self.stats['errors'] += 1
                time.sleep(1.0)
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Met à jour les données d'affichage
        
        Args:
            data: Données à afficher
        """
        try:
            self.display_data = data
            self.last_update = time.time()
            self.stats['updates'] += 1
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données LCD: {e}")
            self.stats['errors'] += 1
    
    def set_screen(self, screen: ScreenType) -> None:
        """
        Change l'écran affiché
        
        Args:
            screen: Type d'écran à afficher
        """
        try:
            self.current_screen = screen
            self.logger.debug(f"Écran changé: {screen.value}")
            
        except Exception as e:
            self.logger.error(f"Erreur changement écran: {e}")
            self.stats['errors'] += 1
    
    def navigate_terrarium(self, direction: int) -> None:
        """
        Navigue entre les terrariums
        
        Args:
            direction: 1 pour suivant, -1 pour précédent
        """
        try:
            terrariums = self.display_data.get('terrariums', [])
            if not terrariums:
                return
            
            self.terrarium_index = (self.terrarium_index + direction) % len(terrariums)
            if self.terrarium_index < 0:
                self.terrarium_index = len(terrariums) - 1
            
            self.logger.debug(f"Navigation terrarium: {self.terrarium_index}")
            
        except Exception as e:
            self.logger.error(f"Erreur navigation terrarium: {e}")
            self.stats['errors'] += 1
    
    def navigate_species(self, direction: int) -> None:
        """
        Navigue entre les espèces
        
        Args:
            direction: 1 pour suivant, -1 pour précédent
        """
        try:
            species = self.display_data.get('species', [])
            if not species:
                return
            
            self.species_index = (self.species_index + direction) % len(species)
            if self.species_index < 0:
                self.species_index = len(species) - 1
            
            self.logger.debug(f"Navigation espèce: {self.species_index}")
            
        except Exception as e:
            self.logger.error(f"Erreur navigation espèce: {e}")
            self.stats['errors'] += 1
    
    def select_current_terrarium(self) -> None:
        """Sélectionne le terrarium actuellement affiché"""
        try:
            terrariums = self.display_data.get('terrariums', [])
            if not terrariums or self.terrarium_index >= len(terrariums):
                return
            
            terrarium = terrariums[self.terrarium_index]
            terrarium_id = terrarium.get('id')
            
            if terrarium_id and self.event_bus:
                # Émettre un événement de sélection de terrarium
                self.event_bus.emit('terrarium_select_request', {
                    'terrarium_id': terrarium_id,
                    'timestamp': time.time()
                })
                
                self.logger.info(f"Terrarium sélectionné: {terrarium_id}")
            
        except Exception as e:
            self.logger.error(f"Erreur sélection terrarium: {e}")
            self.stats['errors'] += 1
    
    def select_current_species(self) -> None:
        """Sélectionne l'espèce actuellement affichée"""
        try:
            species = self.display_data.get('species', [])
            if not species or self.species_index >= len(species):
                return
            
            species_item = species[self.species_index]
            species_id = species_item.get('id')
            
            if species_id and self.event_bus:
                # Émettre un événement de sélection d'espèce
                self.event_bus.emit('species_select_request', {
                    'species_id': species_id,
                    'timestamp': time.time()
                })
                
                self.logger.info(f"Espèce sélectionnée: {species_id}")
            
        except Exception as e:
            self.logger.error(f"Erreur sélection espèce: {e}")
            self.stats['errors'] += 1
    
    def _update_display(self) -> None:
        """Met à jour l'affichage selon l'écran actuel"""
        try:
            if not self.lcd_driver:
                return
            
            if self.current_screen == ScreenType.HOME:
                self._display_home_screen()
            elif self.current_screen == ScreenType.SENSORS:
                self._display_sensors_screen()
            elif self.current_screen == ScreenType.CONTROLS:
                self._display_controls_screen()
            elif self.current_screen == ScreenType.CONFIG:
                self._display_config_screen()
            elif self.current_screen == ScreenType.ALERTS:
                self._display_alerts_screen()
            elif self.current_screen == ScreenType.TERRARIUMS:
                self._display_terrariums_screen()
            elif self.current_screen == ScreenType.SPECIES:
                self._display_species_screen()
                
        except Exception as e:
            self.logger.error(f"Erreur mise à jour affichage: {e}")
            self.stats['errors'] += 1
    
    def _display_home_screen(self) -> None:
        """Affiche l'écran d'accueil - Inspiré d'alimante_menu_improved.py"""
        try:
            if not self.lcd_driver:
                return
            
            # Création de l'image (comme dans alimante_menu_improved.py)
            # L'écran fait 128x160 selon la configuration JSON
            image = Image.new("RGB", (128, 160), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Titre centré (comme dans alimante_menu_improved.py)
            title = "ALIMANTE MENU"
            bbox = draw.textbbox((0, 0), title, font=font)
            title_width = bbox[2] - bbox[0]
            x_title = (128 - title_width) // 2
            draw.text((x_title, 5), title, fill=(255, 255, 0), font=font)
            
            # Ligne de séparation
            draw.line([(5, 20), (123, 20)], fill=(128, 128, 128))
            
            # Statut système avec couleur
            status = self.display_data.get('system_status', 'unknown')
            if status == 'running':
                status_color = (0, 255, 0)  # Vert
                status_text = "SYSTEME PRET"
            else:
                status_color = (255, 0, 0)  # Rouge
                status_text = "SYSTEME ARRET"
            
            draw.text((5, 30), status_text, fill=status_color, font=font)
            
            # Données principales des capteurs
            sensors = self.display_data.get('sensors', {})
            dht22_data = sensors.get('dht22', {})
            
            if dht22_data and dht22_data.get('temperature') is not None:
                temp = dht22_data.get('temperature', 0)
                hum = dht22_data.get('humidity', 0)
                
                draw.text((5, 40), f"Temp: {temp:.1f}°C", fill=(255, 255, 255), font=font)
                draw.text((5, 55), f"Hum:  {hum:.1f}%", fill=(255, 255, 255), font=font)
            else:
                draw.text((5, 40), "Capteurs: N/A", fill=(255, 0, 0), font=font)
            
            # Alertes avec indicateur visuel
            alerts = self.display_data.get('alerts', [])
            if alerts:
                draw.text((5, 75), f"Alertes: {len(alerts)}", fill=(255, 165, 0), font=font)
            else:
                draw.text((5, 75), "Aucune alerte", fill=(0, 255, 0), font=font)
            
            # Informations de navigation (adaptées à la taille d'écran)
            draw.text((5, 95), "Tourner: naviguer", fill=(128, 128, 128), font=font)
            draw.text((5, 110), "Appuyer: valider", fill=(128, 128, 128), font=font)
            
            # Indicateur de sélection (adapté à la taille d'écran)
            draw.text((5, 125), "Sel: 1/7", fill=(128, 128, 128), font=font)
            
            # Affichage (comme dans alimante_menu_improved.py)
            self.lcd_driver.display(image)
            self.logger.info("Écran LCD mis à jour avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran accueil: {e}")
            self.stats['errors'] += 1
    
    def _display_sensors_screen(self) -> None:
        """Affiche l'écran des capteurs"""
        try:
            if not self.lcd_driver:
                return
            
            # Effacer l'écran
            self.lcd_driver.fill(self.colors['black'])
            
            # Titre
            self.lcd_driver.text("CAPTEURS", 10, 5, self.colors['white'], size=2)
            
            # Ligne de séparation
            self.lcd_driver.hline(0, 25, self.width, self.colors['gray'])
            
            # Données des capteurs
            sensors = self.display_data.get('sensors', {})
            y_pos = 35
            
            # DHT22
            dht22_data = sensors.get('dht22', {})
            if dht22_data:
                temp = dht22_data.get('temperature', 0)
                hum = dht22_data.get('humidity', 0)
                self.lcd_driver.text(f"DHT22:", 5, y_pos, self.colors['cyan'])
                self.lcd_driver.text(f"  T: {temp:.1f}°C", 5, y_pos + 15, self.colors['white'])
                self.lcd_driver.text(f"  H: {hum:.1f}%", 5, y_pos + 30, self.colors['white'])
                y_pos += 50
            else:
                self.lcd_driver.text("DHT22: N/A", 5, y_pos, self.colors['red'])
                y_pos += 20
            
            # Qualité de l'air
            air_data = sensors.get('air_quality', {})
            if air_data:
                aqi = air_data.get('aqi', 0)
                self.lcd_driver.text(f"Air: AQI {aqi}", 5, y_pos, self.colors['white'])
                y_pos += 20
            else:
                self.lcd_driver.text("Air: N/A", 5, y_pos, self.colors['red'])
                y_pos += 20
            
            # Niveau d'eau
            water_data = sensors.get('water_level', {})
            if water_data:
                level = water_data.get('level', 0)
                self.lcd_driver.text(f"Eau: {level}%", 5, y_pos, self.colors['white'])
            else:
                self.lcd_driver.text("Eau: N/A", 5, y_pos, self.colors['red'])
            
            # Mettre à jour l'affichage
            self.lcd_driver.show()
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran capteurs: {e}")
            self.stats['errors'] += 1
    
    def _display_controls_screen(self) -> None:
        """Affiche l'écran des contrôles"""
        try:
            if not self.lcd_driver:
                return
            
            # Effacer l'écran
            self.lcd_driver.fill(self.colors['black'])
            
            # Titre
            self.lcd_driver.text("CONTROLES", 10, 5, self.colors['white'], size=2)
            
            # Ligne de séparation
            self.lcd_driver.hline(0, 25, self.width, self.colors['gray'])
            
            # État des contrôles
            controls = self.display_data.get('controls', {})
            y_pos = 35
            
            # Chauffage
            heating = controls.get('heating', False)
            heating_color = self.colors['red'] if heating else self.colors['green']
            self.lcd_driver.text(f"Chauffage: {'ON' if heating else 'OFF'}", 5, y_pos, heating_color)
            y_pos += 20
            
            # Éclairage
            lighting = controls.get('lighting', False)
            lighting_color = self.colors['yellow'] if lighting else self.colors['gray']
            self.lcd_driver.text(f"Eclairage: {'ON' if lighting else 'OFF'}", 5, y_pos, lighting_color)
            y_pos += 20
            
            # Humidification
            humidification = controls.get('humidification', False)
            hum_color = self.colors['cyan'] if humidification else self.colors['gray']
            self.lcd_driver.text(f"Humidif: {'ON' if humidification else 'OFF'}", 5, y_pos, hum_color)
            y_pos += 20
            
            # Ventilation
            ventilation = controls.get('ventilation', False)
            vent_color = self.colors['blue'] if ventilation else self.colors['gray']
            self.lcd_driver.text(f"Ventilat: {'ON' if ventilation else 'OFF'}", 5, y_pos, vent_color)
            y_pos += 20
            
            # Alimentation
            feeding = controls.get('feeding', False)
            feed_color = self.colors['magenta'] if feeding else self.colors['gray']
            self.lcd_driver.text(f"Aliment: {'ON' if feeding else 'OFF'}", 5, y_pos, feed_color)
            
            # Mettre à jour l'affichage
            self.lcd_driver.show()
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran contrôles: {e}")
            self.stats['errors'] += 1
    
    def _display_config_screen(self) -> None:
        """Affiche l'écran de configuration"""
        try:
            if not self.lcd_driver:
                return
            
            # Effacer l'écran
            self.lcd_driver.fill(self.colors['black'])
            
            # Titre
            self.lcd_driver.text("CONFIG", 10, 5, self.colors['white'], size=2)
            
            # Ligne de séparation
            self.lcd_driver.hline(0, 25, self.width, self.colors['gray'])
            
            # Options de configuration
            self.lcd_driver.text("1. Terrariums", 5, 35, self.colors['white'])
            self.lcd_driver.text("2. Especes", 5, 55, self.colors['white'])
            self.lcd_driver.text("3. Capteurs", 5, 75, self.colors['white'])
            self.lcd_driver.text("4. Reseau", 5, 95, self.colors['white'])
            self.lcd_driver.text("5. Systeme", 5, 115, self.colors['white'])
            
            # Navigation
            self.lcd_driver.text("Tourner: naviguer", 5, 135, self.colors['gray'], size=1)
            self.lcd_driver.text("Appuyer: selectionner", 5, 150, self.colors['gray'], size=1)
            
            # Mettre à jour l'affichage
            self.lcd_driver.show()
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran config: {e}")
            self.stats['errors'] += 1
    
    def _display_alerts_screen(self) -> None:
        """Affiche l'écran des alertes"""
        try:
            if not self.lcd_driver:
                return
            
            # Effacer l'écran
            self.lcd_driver.fill(self.colors['black'])
            
            # Titre
            self.lcd_driver.text("ALERTES", 10, 5, self.colors['white'], size=2)
            
            # Ligne de séparation
            self.lcd_driver.hline(0, 25, self.width, self.colors['gray'])
            
            # Alertes
            alerts = self.display_data.get('alerts', [])
            y_pos = 35
            
            if not alerts:
                self.lcd_driver.text("Aucune alerte", 5, y_pos, self.colors['green'])
            else:
                # Afficher les 3 dernières alertes
                for i, alert in enumerate(alerts[-3:]):
                    level = alert.get('level', 'info')
                    message = alert.get('message', '')[:20]  # Limiter la longueur
                    
                    if level == 'error':
                        color = self.colors['red']
                    elif level == 'warning':
                        color = self.colors['yellow']
                    else:
                        color = self.colors['white']
                    
                    self.lcd_driver.text(f"{i+1}. {message}", 5, y_pos, color)
                    y_pos += 20
                    
                    if y_pos > self.height - 20:
                        break
            
            # Navigation
            self.lcd_driver.text("Appuyer: effacer", 5, self.height - 15, self.colors['gray'], size=1)
            
            # Mettre à jour l'affichage
            self.lcd_driver.show()
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran alertes: {e}")
            self.stats['errors'] += 1
    
    def _display_terrariums_screen(self) -> None:
        """Affiche l'écran de sélection des terrariums"""
        try:
            if not self.lcd_driver:
                return
            
            # Effacer l'écran
            self.lcd_driver.fill(self.colors['black'])
            
            # Titre
            self.lcd_driver.text("TERRARIUMS", 10, 5, self.colors['white'], size=2)
            
            # Ligne de séparation
            self.lcd_driver.hline(0, 25, self.width, self.colors['gray'])
            
            # Récupérer les terrariums depuis les données d'affichage
            terrariums = self.display_data.get('terrariums', [])
            if not terrariums:
                self.lcd_driver.text("Aucun terrarium", 5, 35, self.colors['red'])
                return
            
            # Afficher le terrarium actuel
            if 0 <= self.terrarium_index < len(terrariums):
                terrarium = terrariums[self.terrarium_index]
                
                # Nom du terrarium
                name = terrarium.get('name', 'Inconnu')[:15]  # Limiter la longueur
                self.lcd_driver.text(f"> {name}", 5, 35, self.colors['yellow'])
                
                # Espèce
                species = terrarium.get('species', {})
                species_name = species.get('common_name', 'Non défini')[:15]
                self.lcd_driver.text(f"  {species_name}", 5, 55, self.colors['white'])
                
                # Statut
                status = terrarium.get('status', 'inactive')
                status_color = self.colors['green'] if status == 'active' else self.colors['red']
                self.lcd_driver.text(f"  {status.upper()}", 5, 75, status_color)
                
                # Indicateur de position
                self.lcd_driver.text(f"{self.terrarium_index + 1}/{len(terrariums)}", 5, 95, self.colors['gray'])
            
            # Navigation
            self.lcd_driver.text("Tourner: naviguer", 5, 115, self.colors['gray'], size=1)
            self.lcd_driver.text("Appuyer: selectionner", 5, 130, self.colors['gray'], size=1)
            
            # Mettre à jour l'affichage
            self.lcd_driver.show()
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran terrariums: {e}")
            self.stats['errors'] += 1
    
    def _display_species_screen(self) -> None:
        """Affiche l'écran de sélection des espèces"""
        try:
            if not self.lcd_driver:
                return
            
            # Effacer l'écran
            self.lcd_driver.fill(self.colors['black'])
            
            # Titre
            self.lcd_driver.text("ESPECES", 10, 5, self.colors['white'], size=2)
            
            # Ligne de séparation
            self.lcd_driver.hline(0, 25, self.width, self.colors['gray'])
            
            # Récupérer les espèces depuis les données d'affichage
            species = self.display_data.get('species', [])
            if not species:
                self.lcd_driver.text("Aucune espece", 5, 35, self.colors['red'])
                return
            
            # Afficher l'espèce actuelle
            if 0 <= self.species_index < len(species):
                species_item = species[self.species_index]
                
                # Nom de l'espèce
                name = species_item.get('name', 'Inconnue')[:15]
                self.lcd_driver.text(f"> {name}", 5, 35, self.colors['yellow'])
                
                # Nom scientifique
                scientific = species_item.get('scientific_name', '')[:15]
                self.lcd_driver.text(f"  {scientific}", 5, 55, self.colors['white'])
                
                # Type
                species_type = species_item.get('type', 'unknown')
                type_color = self.colors['cyan'] if species_type == 'insect' else self.colors['magenta']
                self.lcd_driver.text(f"  {species_type.upper()}", 5, 75, type_color)
                
                # Indicateur de position
                self.lcd_driver.text(f"{self.species_index + 1}/{len(species)}", 5, 95, self.colors['gray'])
            
            # Navigation
            self.lcd_driver.text("Tourner: naviguer", 5, 115, self.colors['gray'], size=1)
            self.lcd_driver.text("Appuyer: selectionner", 5, 130, self.colors['gray'], size=1)
            
            # Mettre à jour l'affichage
            self.lcd_driver.show()
            
        except Exception as e:
            self.logger.error(f"Erreur affichage écran espèces: {e}")
            self.stats['errors'] += 1
    
    def is_running(self) -> bool:
        """
        Vérifie si l'interface LCD est en cours d'exécution
        
        Returns:
            True si en cours d'exécution, False sinon
        """
        return self.is_running
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de l'interface LCD
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'is_running': self.is_running,
            'current_screen': self.current_screen.value,
            'driver_available': self.lcd_driver is not None,
            'last_update': self.last_update,
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie les ressources de l'interface LCD"""
        try:
            self.stop()
            if self.lcd_driver:
                self.lcd_driver.cleanup()
            self.logger.info("Interface LCD nettoyée")
        except Exception as e:
            self.logger.error(f"Erreur nettoyage interface LCD: {e}")
