#!/usr/bin/env python3
"""
Contrôleur pour l'écran LCD ST7735 avec système de menu
Gestion de l'affichage et navigation par boutons
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

from ..utils.gpio_manager import GPIOManager
from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode


class MenuItemType(Enum):
    """Types d'éléments de menu"""
    SUBMENU = "submenu"
    ACTION = "action"
    TOGGLE = "toggle"
    VALUE = "value"


class MenuItem:
    """Élément de menu"""
    
    def __init__(self, name: str, item_type: MenuItemType, action: Optional[Callable] = None, 
                 submenu: Optional[List['MenuItem']] = None, value: Any = None):
        self.name = name
        self.type = item_type
        self.action = action
        self.submenu = submenu or []
        self.value = value


class LCDMenuController:
    """Contrôleur pour l'écran LCD ST7735 avec système de menu"""
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict[str, Any]):
        self.logger = get_logger("lcd_menu_controller")
        self.gpio_manager = gpio_manager
        self.config = config
        
        # Configuration de l'écran ST7735
        self.lcd_config = config.get("lcd_config", {})
        self.menu_config = config.get("menu_config", {})
        
        # Pins SPI pour ST7735
        self.dc_pin = self.lcd_config.get("spi_pins", {}).get("dc", 8)
        self.cs_pin = self.lcd_config.get("spi_pins", {}).get("cs", 7)
        self.rst_pin = self.lcd_config.get("spi_pins", {}).get("rst", 9)
        self.backlight_pin = self.lcd_config.get("backlight_pin", 10)
        
        # Pins des boutons
        self.button_pins = self.menu_config.get("buttons", {})
        self.up_pin = self.button_pins.get("up", 5)
        self.down_pin = self.button_pins.get("down", 6)
        self.select_pin = self.button_pins.get("select", 13)
        self.back_pin = self.button_pins.get("back", 19)
        
        # Configuration de l'écran
        self.width = 128
        self.height = 160
        self.current_screen = None
        self.display = None
        
        # État du menu
        self.current_menu = []
        self.menu_stack = []
        self.selected_index = 0
        self.display_start = 0
        self.items_per_page = 6
        
        # Gestion des boutons
        self.button_states = {}
        self.debounce_time = self.menu_config.get("debounce_time", 200)
        self.long_press_time = self.menu_config.get("long_press_time", 1000)
        self.last_button_press = {}
        
        # Thread pour la gestion des boutons
        self.button_thread = None
        self.running = False
        
        # État du contrôleur
        self.is_initialized = False
        self.error_count = 0
        
        # Initialisation
        self._setup_gpio()
        self._create_main_menu()
        self._start_button_monitoring()
        
        self.logger.info("Contrôleur LCD menu initialisé")
    
    def _setup_gpio(self):
        """Configure les GPIO pour l'écran et les boutons"""
        try:
            # Configuration des pins SPI (sera géré par la bibliothèque ST7735)
            # Configuration des boutons
            button_pins = [self.up_pin, self.down_pin, self.select_pin, self.back_pin]
            
            for pin in button_pins:
                pin_config = {
                    "pin": pin,
                    "mode": "input",
                    "pull_up_down": "up"
                }
                self.gpio_manager.setup_pin(pin_config)
                self.button_states[pin] = False
            
            # Configuration du backlight
            backlight_config = {
                "pin": self.backlight_pin,
                "mode": "output"
            }
            self.gpio_manager.setup_pin(backlight_config)
            self.gpio_manager.write_pin(self.backlight_pin, True)  # Allumer le backlight
            
            self.logger.info("GPIO configuré pour LCD et boutons")
            
        except Exception as e:
            self.logger.error(f"Erreur configuration GPIO LCD: {e}")
            raise create_exception(
                ErrorCode.GPIO_SETUP_FAILED,
                f"Impossible de configurer le GPIO pour LCD: {e}",
                {"original_error": str(e)}
            )
    
    def _create_main_menu(self):
        """Crée le menu principal"""
        self.current_menu = [
            MenuItem("📊 Statut Système", MenuItemType.SUBMENU, submenu=[
                MenuItem("🌡️ Température", MenuItemType.ACTION, action=self._show_temperature),
                MenuItem("💧 Humidité", MenuItemType.ACTION, action=self._show_humidity),
                MenuItem("💡 Éclairage", MenuItemType.ACTION, action=self._show_lighting),
                MenuItem("🌪️ Ventilation", MenuItemType.ACTION, action=self._show_ventilation),
                MenuItem("🍽️ Alimentation", MenuItemType.ACTION, action=self._show_feeding),
                MenuItem("🌬️ Qualité Air", MenuItemType.ACTION, action=self._show_air_quality)
            ]),
            MenuItem("⚙️ Configuration", MenuItemType.SUBMENU, submenu=[
                MenuItem("🔧 Paramètres", MenuItemType.ACTION, action=self._show_settings),
                MenuItem("📋 Espèce", MenuItemType.ACTION, action=self._show_species),
                MenuItem("🔄 Calibration", MenuItemType.ACTION, action=self._show_calibration)
            ]),
            MenuItem("🎛️ Contrôles", MenuItemType.SUBMENU, submenu=[
                MenuItem("💡 Éclairage ON/OFF", MenuItemType.TOGGLE, action=self._toggle_lighting),
                MenuItem("🌪️ Ventilation ON/OFF", MenuItemType.TOGGLE, action=self._toggle_ventilation),
                MenuItem("🍽️ Alimentation Manuelle", MenuItemType.ACTION, action=self._manual_feed),
                MenuItem("🔊 Test Buzzer", MenuItemType.ACTION, action=self._test_buzzer)
            ]),
            MenuItem("📈 Métriques", MenuItemType.SUBMENU, submenu=[
                MenuItem("📊 Historique", MenuItemType.ACTION, action=self._show_history),
                MenuItem("📋 Logs", MenuItemType.ACTION, action=self._show_logs),
                MenuItem("⚡ Consommation", MenuItemType.ACTION, action=self._show_power_usage)
            ]),
            MenuItem("🔧 Système", MenuItemType.SUBMENU, submenu=[
                MenuItem("🔄 Redémarrage", MenuItemType.ACTION, action=self._restart_system),
                MenuItem("⏹️ Arrêt", MenuItemType.ACTION, action=self._shutdown_system),
                MenuItem("📱 API Status", MenuItemType.ACTION, action=self._show_api_status)
            ])
        ]
    
    def _start_button_monitoring(self):
        """Démarre la surveillance des boutons dans un thread séparé"""
        self.running = True
        self.button_thread = threading.Thread(target=self._button_monitor_loop, daemon=True)
        self.button_thread.start()
        self.logger.info("Surveillance des boutons démarrée")
    
    def _button_monitor_loop(self):
        """Boucle de surveillance des boutons"""
        while self.running:
            try:
                self._check_buttons()
                time.sleep(0.05)  # 50ms de délai
            except Exception as e:
                self.logger.error(f"Erreur surveillance boutons: {e}")
                time.sleep(0.1)
    
    def _check_buttons(self):
        """Vérifie l'état des boutons"""
        current_time = time.time()
        
        for pin, button_name in [
            (self.up_pin, "UP"),
            (self.down_pin, "DOWN"),
            (self.select_pin, "SELECT"),
            (self.back_pin, "BACK")
        ]:
            try:
                # Lire l'état du bouton (inversé car pull-up)
                button_pressed = not self.gpio_manager.read_pin(pin)
                
                if button_pressed and not self.button_states[pin]:
                    # Bouton pressé
                    self.button_states[pin] = True
                    self.last_button_press[pin] = current_time
                    self.logger.debug(f"Bouton {button_name} pressé")
                    
                elif not button_pressed and self.button_states[pin]:
                    # Bouton relâché
                    self.button_states[pin] = False
                    press_duration = current_time - self.last_button_press.get(pin, current_time)
                    
                    if press_duration > self.long_press_time:
                        self._handle_long_press(button_name)
                    else:
                        self._handle_button_press(button_name)
                    
            except Exception as e:
                self.logger.error(f"Erreur lecture bouton {button_name}: {e}")
    
    def _handle_button_press(self, button_name: str):
        """Gère un appui court sur un bouton"""
        try:
            if button_name == "UP":
                self._navigate_up()
            elif button_name == "DOWN":
                self._navigate_down()
            elif button_name == "SELECT":
                self._select_item()
            elif button_name == "BACK":
                self._go_back()
                
        except Exception as e:
            self.logger.error(f"Erreur gestion bouton {button_name}: {e}")
    
    def _handle_long_press(self, button_name: str):
        """Gère un appui long sur un bouton"""
        try:
            if button_name == "BACK":
                # Retour au menu principal
                self._go_to_main_menu()
            elif button_name == "SELECT":
                # Action spéciale selon le contexte
                self._handle_long_select()
                
        except Exception as e:
            self.logger.error(f"Erreur gestion appui long {button_name}: {e}")
    
    def _navigate_up(self):
        """Navigation vers le haut"""
        if self.selected_index > 0:
            self.selected_index -= 1
            if self.selected_index < self.display_start:
                self.display_start = max(0, self.display_start - 1)
            self._update_display()
    
    def _navigate_down(self):
        """Navigation vers le bas"""
        if self.selected_index < len(self.current_menu) - 1:
            self.selected_index += 1
            if self.selected_index >= self.display_start + self.items_per_page:
                self.display_start = min(
                    len(self.current_menu) - self.items_per_page,
                    self.display_start + 1
                )
            self._update_display()
    
    def _select_item(self):
        """Sélectionne l'élément actuel"""
        if 0 <= self.selected_index < len(self.current_menu):
            item = self.current_menu[self.selected_index]
            
            if item.type == MenuItemType.SUBMENU:
                self._enter_submenu(item)
            elif item.type == MenuItemType.ACTION and item.action:
                self._execute_action(item.action)
            elif item.type == MenuItemType.TOGGLE:
                self._toggle_item(item)
    
    def _enter_submenu(self, item: MenuItem):
        """Entre dans un sous-menu"""
        if item.submenu:
            self.menu_stack.append((self.current_menu, self.selected_index))
            self.current_menu = item.submenu
            self.selected_index = 0
            self.display_start = 0
            self._update_display()
            self.logger.info(f"Entrée dans le sous-menu: {item.name}")
    
    def _go_back(self):
        """Retourne au menu précédent"""
        if self.menu_stack:
            self.current_menu, self.selected_index = self.menu_stack.pop()
            self.display_start = 0
            self._update_display()
            self.logger.info("Retour au menu précédent")
        else:
            # Retour au menu principal
            self._go_to_main_menu()
    
    def _go_to_main_menu(self):
        """Retourne au menu principal"""
        self.menu_stack.clear()
        self._create_main_menu()
        self.selected_index = 0
        self.display_start = 0
        self._update_display()
        self.logger.info("Retour au menu principal")
    
    def _execute_action(self, action: Callable):
        """Exécute une action"""
        try:
            action()
        except Exception as e:
            self.logger.error(f"Erreur exécution action: {e}")
            self._show_error(f"Erreur: {str(e)}")
    
    def _toggle_item(self, item: MenuItem):
        """Bascule un élément toggle"""
        try:
            if item.action:
                item.action()
            # Inverser la valeur
            if isinstance(item.value, bool):
                item.value = not item.value
            self._update_display()
        except Exception as e:
            self.logger.error(f"Erreur toggle: {e}")
    
    def _update_display(self):
        """Met à jour l'affichage"""
        try:
            if not self.display:
                return
            
            # Effacer l'écran
            self.display.fill((0, 0, 0))
            
            # Afficher le titre
            title = "ALIMANTE"
            if self.menu_stack:
                title = self.menu_stack[-1][0][self.menu_stack[-1][1]].name
            
            # Afficher les éléments du menu
            for i in range(self.items_per_page):
                menu_index = self.display_start + i
                if menu_index < len(self.current_menu):
                    item = self.current_menu[menu_index]
                    is_selected = (menu_index == self.selected_index)
                    
                    # Couleur selon la sélection
                    color = (255, 255, 255) if is_selected else (128, 128, 128)
                    bg_color = (0, 100, 200) if is_selected else (0, 0, 0)
                    
                    # Afficher l'élément
                    text = f"{'▶ ' if is_selected else '  '}{item.name}"
                    if item.type == MenuItemType.TOGGLE and isinstance(item.value, bool):
                        text += f" {'ON' if item.value else 'OFF'}"
                    
                    # Ici on utiliserait la bibliothèque ST7735 pour afficher le texte
                    # self.display.text(text, 5, 10 + i * 20, color, bg_color)
            
            # Afficher les informations de navigation
            nav_text = f"↑↓:Naviguer  OK:Select  ←:Retour"
            # self.display.text(nav_text, 5, self.height - 20, (64, 64, 64))
            
            # Rafraîchir l'affichage
            # self.display.show()
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour affichage: {e}")
    
    def _show_error(self, message: str):
        """Affiche un message d'erreur"""
        try:
            if self.display:
                # self.display.fill((255, 0, 0))
                # self.display.text("ERREUR", 5, 10, (255, 255, 255))
                # self.display.text(message, 5, 30, (255, 255, 255))
                # self.display.show()
                self.logger.error(f"Erreur affichée: {message}")
        except Exception as e:
            self.logger.error(f"Erreur affichage erreur: {e}")
    
    # Actions du menu
    def _show_temperature(self):
        """Affiche les informations de température"""
        # Simulation - à connecter avec le contrôleur de température
        temp = "22.5°C"
        self._show_info_screen("🌡️ Température", f"Actuelle: {temp}")
    
    def _show_humidity(self):
        """Affiche les informations d'humidité"""
        # Simulation - à connecter avec le contrôleur d'humidité
        humidity = "65%"
        self._show_info_screen("💧 Humidité", f"Actuelle: {humidity}")
    
    def _show_lighting(self):
        """Affiche les informations d'éclairage"""
        # Simulation - à connecter avec le contrôleur d'éclairage
        status = "ON"
        self._show_info_screen("💡 Éclairage", f"Statut: {status}")
    
    def _show_ventilation(self):
        """Affiche les informations de ventilation"""
        # Simulation - à connecter avec le contrôleur de ventilation
        status = "ON"
        speed = "50%"
        self._show_info_screen("🌪️ Ventilation", f"Statut: {status}\nVitesse: {speed}")
    
    def _show_feeding(self):
        """Affiche les informations d'alimentation"""
        # Simulation - à connecter avec le contrôleur d'alimentation
        last_feed = "2h ago"
        self._show_info_screen("🍽️ Alimentation", f"Dernier repas: {last_feed}")
    
    def _show_air_quality(self):
        """Affiche les informations de qualité de l'air"""
        # Simulation - à connecter avec le contrôleur de qualité de l'air
        quality = "Bon"
        ppm = "85 ppm"
        self._show_info_screen("🌬️ Qualité Air", f"Qualité: {quality}\nPPM: {ppm}")
    
    def _show_settings(self):
        """Affiche les paramètres"""
        self._show_info_screen("⚙️ Paramètres", "Configuration système")
    
    def _show_species(self):
        """Affiche les informations sur l'espèce"""
        species = "Saturnia pyri"
        self._show_info_screen("📋 Espèce", f"Actuelle: {species}")
    
    def _show_calibration(self):
        """Affiche les options de calibration"""
        self._show_info_screen("🔄 Calibration", "Options de calibration")
    
    def _toggle_lighting(self):
        """Bascule l'éclairage"""
        # Simulation - à connecter avec le contrôleur d'éclairage
        self.logger.info("Basculement éclairage")
        self._show_info_screen("💡 Éclairage", "Basculement...")
    
    def _toggle_ventilation(self):
        """Bascule la ventilation"""
        # Simulation - à connecter avec le contrôleur de ventilation
        self.logger.info("Basculement ventilation")
        self._show_info_screen("🌪️ Ventilation", "Basculement...")
    
    def _manual_feed(self):
        """Déclenche une alimentation manuelle"""
        # Simulation - à connecter avec le contrôleur d'alimentation
        self.logger.info("Alimentation manuelle déclenchée")
        self._show_info_screen("🍽️ Alimentation", "Alimentation manuelle...")
    
    def _test_buzzer(self):
        """Teste le buzzer"""
        # Simulation - à connecter avec le contrôleur de buzzer
        self.logger.info("Test buzzer")
        self._show_info_screen("🔊 Buzzer", "Test en cours...")
    
    def _show_history(self):
        """Affiche l'historique"""
        self._show_info_screen("📈 Historique", "Historique des données")
    
    def _show_logs(self):
        """Affiche les logs"""
        self._show_info_screen("📋 Logs", "Logs système")
    
    def _show_power_usage(self):
        """Affiche la consommation électrique"""
        self._show_info_screen("⚡ Consommation", "Consommation électrique")
    
    def _restart_system(self):
        """Redémarre le système"""
        self.logger.warning("Redémarrage système demandé")
        self._show_info_screen("🔄 Redémarrage", "Redémarrage en cours...")
    
    def _shutdown_system(self):
        """Arrête le système"""
        self.logger.warning("Arrêt système demandé")
        self._show_info_screen("⏹️ Arrêt", "Arrêt en cours...")
    
    def _show_api_status(self):
        """Affiche le statut de l'API"""
        status = "ON"
        self._show_info_screen("📱 API Status", f"Statut: {status}")
    
    def _show_info_screen(self, title: str, content: str):
        """Affiche un écran d'information"""
        try:
            if self.display:
                # self.display.fill((0, 0, 0))
                # self.display.text(title, 5, 10, (255, 255, 255))
                # self.display.text(content, 5, 40, (200, 200, 200))
                # self.display.show()
                self.logger.info(f"Écran info: {title} - {content}")
        except Exception as e:
            self.logger.error(f"Erreur affichage info: {e}")
    
    def _handle_long_select(self):
        """Gère un appui long sur SELECT"""
        # Action spéciale selon le contexte
        self.logger.info("Appui long sur SELECT")
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du contrôleur"""
        return {
            "controller": "lcd_menu",
            "display_type": "ST7735",
            "resolution": f"{self.width}x{self.height}",
            "current_menu_depth": len(self.menu_stack),
            "selected_index": self.selected_index,
            "is_initialized": self.is_initialized,
            "error_count": self.error_count,
            "button_states": self.button_states,
            "running": self.running
        }
    
    def check_status(self) -> bool:
        """Vérifie le statut du contrôleur"""
        try:
            # Vérifier que le thread de surveillance fonctionne
            if not self.running:
                return False
            
            # Vérifier les boutons
            for pin in [self.up_pin, self.down_pin, self.select_pin, self.back_pin]:
                try:
                    self.gpio_manager.read_pin(pin)
                except Exception as e:
                    self.logger.error(f"Erreur lecture bouton {pin}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur vérification statut: {e}")
            return False
    
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.logger.info("Nettoyage du contrôleur LCD menu")
            
            # Arrêter le thread de surveillance
            self.running = False
            if self.button_thread and self.button_thread.is_alive():
                self.button_thread.join(timeout=1)
            
            # Éteindre le backlight
            self.gpio_manager.write_pin(self.backlight_pin, False)
            
            # Nettoyer l'écran
            if self.display:
                # self.display.fill((0, 0, 0))
                # self.display.show()
                pass
                
        except Exception as e:
            self.logger.error(f"Erreur nettoyage: {e}")
