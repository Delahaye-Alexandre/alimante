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
        
        # Récupérer la configuration depuis le service GPIO
        from ..services.gpio_config_service import GPIOConfigService
        gpio_service = GPIOConfigService()
        
        # Pins SPI pour ST7735
        lcd_interface_config = gpio_service.get_interface_config('lcd_st7735')
        if lcd_interface_config:
            spi_pins = lcd_interface_config.get('spi_gpios', {})
            self.dc_pin = spi_pins.get('dc', 8)
            self.cs_pin = spi_pins.get('cs', 7)
            self.rst_pin = spi_pins.get('rst', 9)
            self.backlight_pin = lcd_interface_config.get('backlight_gpio', 10)
        else:
            # Fallback vers la configuration locale
            self.dc_pin = self.lcd_config.get("spi_pins", {}).get("dc", 8)
            self.cs_pin = self.lcd_config.get("spi_pins", {}).get("cs", 7)
            self.rst_pin = self.lcd_config.get("spi_pins", {}).get("rst", 9)
            self.backlight_pin = self.lcd_config.get("backlight_pin", 10)
        
        # Configuration encodeur rotatif
        rotary_interface_config = gpio_service.get_interface_config('rotary_encoder')
        if rotary_interface_config:
            self.clk_pin = rotary_interface_config.get('clk_gpio', 5)
            self.dt_pin = rotary_interface_config.get('dt_gpio', 6)
            self.sw_pin = rotary_interface_config.get('sw_gpio', 13)
        else:
            # Fallback vers la configuration locale
            self.rotary_config = self.menu_config.get("rotary_encoder", {})
            self.clk_pin = self.rotary_config.get("clk_pin", 5)
            self.dt_pin = self.rotary_config.get("dt_pin", 6)
            self.sw_pin = self.rotary_config.get("sw_pin", 13)
        self.rotation_sensitivity = self.menu_config.get("rotation_sensitivity", 1)
        
        # État de l'encodeur rotatif
        self.last_clk_state = None
        self.encoder_position = 0
        self.last_encoder_position = 0
        
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
        
        # Disponibilité du composant
        self.is_available = False
        
        # Initialisation GPIO
        self._setup_gpio()
        
        # Gestion de l'encodeur rotatif
        self.encoder_states = {}
        self.debounce_time = self.menu_config.get("debounce_time", 50)
        self.long_press_time = self.menu_config.get("long_press_time", 1000)
        self.last_encoder_action = {}
        
        # Thread pour la gestion de l'encodeur
        self.encoder_thread = None
        self.running = False
        
        # État du contrôleur
        self.is_initialized = False
        self.error_count = 0
        
        # Initialisation
        self._setup_gpio()
        self._create_main_menu()
        self._start_encoder_monitoring()
        
        self.logger.info("Contrôleur LCD menu initialisé")
    
    def _setup_gpio(self):
        """Configure les GPIO pour l'écran et l'encodeur rotatif"""
        try:
            from ..utils.gpio_manager import PinConfig, PinMode
            
            # Vérifier que les pins essentiels sont définis
            if self.clk_pin is None or self.dt_pin is None:
                self.logger.warning("❌ Composant encodeur rotatif non détecté - Pins CLK/DT manquants")
                self.is_available = False
                return
            
            # Configuration des pins SPI (sera géré par la bibliothèque ST7735)
            
            # Configuration de l'encodeur rotatif
            encoder_pins = [self.clk_pin, self.dt_pin, self.sw_pin]
            encoder_success = True
            
            for pin in encoder_pins:
                if pin is not None:  # Vérifier que le pin est défini
                    encoder_config = PinConfig(
                        pin=pin,
                        mode=PinMode.INPUT,
                        component_name=f"Encodeur rotatif (pin {pin})",
                        required=(pin in [self.clk_pin, self.dt_pin])  # CLK et DT sont requis
                    )
                    if not self.gpio_manager.setup_pin(encoder_config):
                        if pin in [self.clk_pin, self.dt_pin]:
                            encoder_success = False
                            self.logger.error(f"❌ Échec configuration encodeur rotatif - pin {pin}")
            
            # Configuration du backlight (optionnel)
            backlight_success = True
            if self.backlight_pin is not None:
                backlight_config = PinConfig(
                    pin=self.backlight_pin,
                    mode=PinMode.OUTPUT,
                    initial_state=True,
                    component_name="Backlight LCD",
                    required=False  # Optionnel
                )
                backlight_success = self.gpio_manager.setup_pin(backlight_config)
                if backlight_success:
                    self.logger.info("✅ Backlight LCD activé")
                else:
                    self.logger.warning("⚠️ Backlight LCD non configuré (optionnel)")
            
            # Définir la disponibilité globale
            if encoder_success:
                self.is_available = True
                self.logger.info("✅ Composant LCD et encodeur rotatif configuré")
                
                # Initialiser l'état CLK pour détecter les rotations
                self.last_clk_state = self.gpio_manager.read_digital(self.clk_pin)
            else:
                self.is_available = False
                self.logger.error("❌ Échec configuration encodeur rotatif")
                raise Exception("Impossible de configurer l'encodeur rotatif")
            
        except Exception as e:
            self.is_available = False
            self.logger.error(f"❌ Erreur configuration GPIO LCD: {e}")
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
                MenuItem("🌫️ Test Brumisateur", MenuItemType.ACTION, action=self._test_brumisateur)
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
    
    def _start_encoder_monitoring(self):
        """Démarre la surveillance de l'encodeur rotatif dans un thread séparé"""
        self.running = True
        self.encoder_thread = threading.Thread(target=self._encoder_monitor_loop, daemon=True)
        self.encoder_thread.start()
        self.logger.info("Surveillance encodeur rotatif démarrée")
    
    def _encoder_monitor_loop(self):
        """Boucle de surveillance de l'encodeur rotatif"""
        while self.running:
            try:
                self._check_encoder_rotation()
                self._check_encoder_button()
                time.sleep(0.01)  # 10ms de délai pour réactivité encodeur
            except Exception as e:
                self.logger.error(f"Erreur surveillance encodeur: {e}")
                time.sleep(0.05)
    
    def _check_encoder_rotation(self):
        """Vérifie la rotation de l'encodeur rotatif"""
        try:
            current_clk = self.gpio_manager.read_digital(self.clk_pin)
            
            # Détecter changement d'état sur CLK
            if current_clk != self.last_clk_state:
                dt_state = self.gpio_manager.read_digital(self.dt_pin)
                
                # Déterminer le sens de rotation
                if current_clk == 0:  # Front descendant CLK
                    if dt_state == 0:
                        # Rotation horaire
                        self.encoder_position += self.rotation_sensitivity
                        self._navigate_down()
                        self.logger.debug("Encodeur: rotation horaire")
                    else:
                        # Rotation anti-horaire
                        self.encoder_position -= self.rotation_sensitivity
                        self._navigate_up()
                        self.logger.debug("Encodeur: rotation anti-horaire")
                
                self.last_clk_state = current_clk
                
        except Exception as e:
            self.logger.error(f"Erreur lecture rotation encodeur: {e}")
    
    def _check_encoder_button(self):
        """Vérifie l'état du bouton de l'encodeur"""
        try:
            current_time = time.time()
            
            # Lire l'état du bouton (inversé car pull-up)
            button_pressed = not self.gpio_manager.read_digital(self.sw_pin)
            
            if button_pressed and not self.encoder_states.get(self.sw_pin, False):
                # Bouton pressé
                self.encoder_states[self.sw_pin] = True
                self.last_encoder_action[self.sw_pin] = current_time
                self.logger.debug("Bouton encodeur pressé")
                
            elif not button_pressed and self.encoder_states.get(self.sw_pin, False):
                # Bouton relâché
                self.encoder_states[self.sw_pin] = False
                press_duration = current_time - self.last_encoder_action.get(self.sw_pin, current_time)
                
                if press_duration > (self.long_press_time / 1000.0):  # Conversion ms en s
                    self._handle_long_press("ENCODER")
                else:
                    self._handle_encoder_press()
                    
        except Exception as e:
            self.logger.error(f"Erreur lecture bouton encodeur: {e}")
    
    def _handle_encoder_press(self):
        """Gère un appui court sur le bouton de l'encodeur"""
        try:
            # Appui court = sélection
            self._select_item()
        except Exception as e:
            self.logger.error(f"Erreur gestion bouton encodeur: {e}")
    
    def _handle_long_press(self, button_name: str):
        """Gère un appui long sur le bouton de l'encodeur"""
        try:
            if button_name == "ENCODER":
                # Appui long = retour au menu principal ou action spéciale
                if self.menu_stack:
                    self._go_to_main_menu()
                else:
                    self._handle_long_select()
                
        except Exception as e:
            self.logger.error(f"Erreur gestion appui long encodeur: {e}")
    
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
    
    def _test_brumisateur(self):
        """Teste le brumisateur ultrasonique"""
        # Simulation - à connecter avec le contrôleur de brumisateur ultrasonique
        self.logger.info("Test brumisateur ultrasonique")
        self._show_info_screen("🌫️ Brumisateur", "Test en cours...")
    
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
            "status": "ok" if self.error_count == 0 and self.is_available else "disabled" if not self.is_available else "error",
            "component_available": self.is_available,
            "display_type": "ST7735",
            "resolution": f"{self.width}x{self.height}",
            "current_menu_depth": len(self.menu_stack),
            "selected_index": self.selected_index,
            "is_initialized": self.is_initialized,
            "error_count": self.error_count,
            "button_states": self.button_states,
            "running": self.running,
            "component_info": {
                "available": self.is_available,
                "reason_disabled": "Composant non détecté" if not self.is_available else None
            }
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
                    self.gpio_manager.read_digital(pin)
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
