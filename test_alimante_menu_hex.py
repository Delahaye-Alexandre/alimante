#!/usr/bin/env python3
"""
Menu Alimante avec couleurs hexadécimales
Utilise les formats natifs du ST7735
"""

import time
import sys
import signal
from config_alimante import get_gpio_config, get_ui_config

# Import des librairies
try:
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    ST7735_AVAILABLE = True
    print("✅ Librairies ST7735 et PIL importées avec succès")
except Exception as e:
    ST7735_AVAILABLE = False
    print(f"⚠️  Erreur ST7735: {e}")

try:
    from gpiozero import RotaryEncoder, Button
    GPIOZERO_AVAILABLE = True
    print("✅ Librairie gpiozero importée avec succès")
except Exception as e:
    GPIOZERO_AVAILABLE = False
    print(f"⚠️  Erreur gpiozero: {e}")

class AlimanteMenuHex:
    def __init__(self):
        self.config = get_gpio_config()
        self.ui_config = get_ui_config()
        
        # Configuration écran
        self.display = None
        self.is_display_initialized = False
        self.reset_pin = self.config['DISPLAY']['RESET_PIN']
        self.a0_pin = self.config['DISPLAY']['A0_PIN']
        
        # Configuration encodeur
        self.encoder = None
        self.button = None
        self.is_encoder_initialized = False
        self.clk_pin = self.config['ENCODER']['CLK_PIN']
        self.dt_pin = self.config['ENCODER']['DT_PIN']
        self.sw_pin = self.config['ENCODER']['SW_PIN']
        
        # État du menu
        self.menu_items = self.ui_config['MENU']['ITEMS']
        self.current_selection = 0
        self.counter = 0
        self.is_running = False
        
        # Palette de couleurs hexadécimales
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
            'purple': 0x801F,
            'dark_red': 0x8000,
            'dark_green': 0x0400,
            'dark_blue': 0x0010,
            'light_gray': 0xC618,
            'dark_gray': 0x4208,
        }
        
        # Gestionnaire d'arrêt
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def hex_to_rgb(self, hex_color):
        """Convertit hex en RGB"""
        if isinstance(hex_color, str):
            hex_color = int(hex_color, 16)
        
        # RGB565 format
        r = (hex_color >> 11) & 0x1F
        g = (hex_color >> 5) & 0x3F
        b = hex_color & 0x1F
        
        # Conversion vers RGB888
        r = (r * 255) // 31
        g = (g * 255) // 63
        b = (b * 255) // 31
        
        return (r, g, b)

    def get_color(self, color_name):
        """Récupère une couleur par nom"""
        return self.hex_to_rgb(self.colors.get(color_name, self.colors['white']))

    def initialize_display(self):
        """Initialise l'écran ST7735"""
        if not ST7735_AVAILABLE:
            print("❌ ST7735 non disponible")
            return False
        
        try:
            print("🔧 Initialisation de l'écran ST7735...")
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=270
            )
            self.display.begin()
            self.is_display_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            
            # Test des couleurs hex
            self.test_couleurs_hex()
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation écran: {e}")
            return False

    def test_couleurs_hex(self):
        """Test des couleurs hexadécimales"""
        if not self.is_display_initialized:
            return False
            
        print("🎨 Test des couleurs hexadécimales...")
        
        couleurs_test = [
            ("Rouge", 'red'),
            ("Vert", 'green'),
            ("Bleu", 'blue'),
        ]
        
        try:
            for nom, color_name in couleurs_test:
                print(f"   → {nom} (0x{self.colors[color_name]:04X})")
                
                # Image plein écran
                rgb_color = self.get_color(color_name)
                image = Image.new("RGB", (self.display.width, self.display.height), rgb_color)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                # Texte centré
                bbox = draw.textbbox((0, 0), nom, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (self.display.width - text_width) // 2
                y = (self.display.height - text_height) // 2
                
                # Contraste texte
                brightness = sum(rgb_color) / 3
                text_color = self.get_color('black') if brightness > 128 else self.get_color('white')
                
                draw.text((x, y), nom, fill=text_color, font=font)
                draw.text((5, 5), f"0x{self.colors[color_name]:04X}", fill=text_color, font=font)
                
                self.display.display(image)
                time.sleep(1)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False

    def initialize_encoder(self):
        """Initialise l'encodeur rotatif"""
        if not GPIOZERO_AVAILABLE:
            print("❌ gpiozero non disponible")
            return False
            
        try:
            print("🔧 Initialisation de l'encodeur rotatif...")
            
            # Création de l'encodeur
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
            
            self.is_encoder_initialized = True
            print("✅ Encodeur et bouton initialisés")
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation encodeur: {e}")
            return False

    def _on_rotation(self):
        """Callback de rotation de l'encodeur (INVERSÉ)"""
        if not self.is_running:
            return
            
        # Mise à jour du compteur
        old_counter = self.counter
        self.counter = self.encoder.steps
        
        # Mise à jour de la sélection du menu (INVERSÉ)
        if self.encoder.steps > old_counter:
            # Rotation horaire = menu vers le bas (inversé)
            self.current_selection = (self.current_selection - 1) % len(self.menu_items)
        else:
            # Rotation anti-horaire = menu vers le haut (inversé)
            self.current_selection = (self.current_selection + 1) % len(self.menu_items)
        
        # Mise à jour de l'affichage
        self.update_display()

    def _on_button_pressed(self):
        """Callback d'appui du bouton"""
        if not self.is_running:
            return
            
        print(f"🔘 Sélection: {self.menu_items[self.current_selection]}")
        self.execute_menu_action(self.current_selection)

    def update_display(self):
        """Met à jour l'affichage du menu"""
        if not self.is_display_initialized:
            return
            
        try:
            # Création de l'image
            image = Image.new("RGB", (self.display.width, self.display.height), self.get_color('black'))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Titre
            title = "ALIMANTE MENU"
            bbox = draw.textbbox((0, 0), title, font=font)
            title_width = bbox[2] - bbox[0]
            x_title = (self.display.width - title_width) // 2
            draw.text((x_title, 5), title, fill=self.get_color('yellow'), font=font)
            
            # Ligne de séparation
            draw.line([(5, 20), (self.display.width - 5, 20)], fill=self.get_color('light_gray'))
            
            # Items du menu
            y_pos = 25
            for i, item in enumerate(self.menu_items):
                if i == self.current_selection:
                    # Item sélectionné
                    draw.rectangle([2, y_pos - 2, self.display.width - 2, y_pos + 12], 
                                 fill=self.get_color('blue'))
                    draw.text((5, y_pos), item, fill=self.get_color('white'), font=font)
                else:
                    # Item normal
                    draw.text((5, y_pos), item, fill=self.get_color('light_gray'), font=font)
                y_pos += 15
            
            # Informations en bas
            info_text = f"Sel: {self.current_selection + 1}/{len(self.menu_items)}"
            draw.text((5, self.display.height - 15), info_text, fill=self.get_color('dark_gray'), font=font)
            
            # Affichage
            self.display.display(image)
            
        except Exception as e:
            print(f"❌ Erreur mise à jour affichage: {e}")

    def execute_menu_action(self, selection):
        """Exécute l'action du menu sélectionné"""
        actions = {
            0: self.action_accueil,
            1: self.action_test_led,
            2: self.action_monitoring,
            3: self.action_configuration,
            4: self.action_tests_hardware,
            5: self.action_statistiques,
            6: self.action_a_propos
        }
        
        if selection in actions:
            actions[selection]()

    def action_accueil(self):
        """Action: Accueil Alimante"""
        print("🏠 Accueil Alimante")
        self.show_message("Accueil Alimante", "Système prêt", 'green')

    def action_test_led(self):
        """Action: Test LED Bandeaux"""
        print("💡 Test LED Bandeaux")
        self.show_message("Test LED", "Fonctionnalité en développement", 'orange')

    def action_monitoring(self):
        """Action: Monitoring Système"""
        print("📊 Monitoring Système")
        self.show_message("Monitoring", "Surveillance active", 'cyan')

    def action_configuration(self):
        """Action: Configuration"""
        print("⚙️ Configuration")
        self.show_message("Configuration", "Paramètres système", 'purple')

    def action_tests_hardware(self):
        """Action: Tests Hardware"""
        print("🔧 Tests Hardware")
        self.show_message("Tests HW", "Diagnostic matériel", 'red')

    def action_statistiques(self):
        """Action: Statistiques"""
        print("📈 Statistiques")
        self.show_message("Statistiques", "Données d'utilisation", 'magenta')

    def action_a_propos(self):
        """Action: À propos"""
        print("ℹ️ À propos")
        self.show_message("À propos", "Alimante v1.0.0", 'yellow')

    def show_message(self, title, message, color='white'):
        """Affiche un message sur l'écran"""
        if not self.is_display_initialized:
            return
            
        try:
            image = Image.new("RGB", (self.display.width, self.display.height), self.get_color('black'))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Titre
            bbox = draw.textbbox((0, 0), title, font=font)
            title_width = bbox[2] - bbox[0]
            x_title = (self.display.width - title_width) // 2
            draw.text((x_title, 20), title, fill=self.get_color(color), font=font)
            
            # Message
            bbox = draw.textbbox((0, 0), message, font=font)
            msg_width = bbox[2] - bbox[0]
            x_msg = (self.display.width - msg_width) // 2
            draw.text((x_msg, 50), message, fill=self.get_color('white'), font=font)
            
            # Retour
            draw.text((5, self.display.height - 15), "Appuyez pour retourner", 
                     fill=self.get_color('dark_gray'), font=font)
            
            self.display.display(image)
            
            # Attendre l'appui du bouton
            time.sleep(0.5)  # Anti-rebond
            while self.button.is_pressed:
                time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Erreur affichage message: {e}")

    def run_menu(self):
        """Lance le menu principal"""
        print("🚀 Lancement du menu Alimante (couleurs hex)...")
        
        # Initialisation des composants
        if not self.initialize_display():
            print("❌ Impossible d'initialiser l'écran")
            return
            
        if not self.initialize_encoder():
            print("❌ Impossible d'initialiser l'encodeur")
            return
        
        # Démarrage du menu
        self.is_running = True
        self.update_display()
        
        print("\n" + "=" * 50)
        print("🎛️  MENU ALIMANTE ACTIF (HEX)")
        print("=" * 50)
        print("• Tournez l'encodeur pour naviguer")
        print("• Appuyez sur le bouton pour sélectionner")
        print("• Ctrl+C pour quitter")
        print("=" * 50)
        
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du menu")
        finally:
            self.cleanup()

    def cleanup(self):
        """Nettoie les ressources"""
        self.is_running = False
        
        if self.display:
            try:
                image = Image.new("RGB", (self.display.width, self.display.height), self.get_color('black'))
                self.display.display(image)
            except:
                pass
                
        if self.encoder:
            self.encoder.close()
        if self.button:
            self.button.close()
            
        print("🧹 Ressources nettoyées")

    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du programme...")
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🎛️  ALIMANTE - MENU HEX")
    print("📍 Encodeur rotatif + Écran ST7735")
    print("📍 Couleurs hexadécimales natives")
    print("=" * 60)
    
    # Vérification des dépendances
    if not ST7735_AVAILABLE:
        print("❌ ST7735 non disponible")
        print("   Installez avec: pip install st7735 Pillow")
        return
        
    if not GPIOZERO_AVAILABLE:
        print("❌ gpiozero non disponible")
        print("   Installez avec: pip install gpiozero")
        return
    
    # Création et lancement du menu
    menu = AlimanteMenuHex()
    menu.run_menu()

if __name__ == "__main__":
    main()
