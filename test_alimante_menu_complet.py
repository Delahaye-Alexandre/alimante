#!/usr/bin/env python3
"""
Test combiné Alimante - Encodeur rotatif + Écran ST7735
Menu contrôlable avec correction des couleurs BGR
"""

import time
import sys
import signal
import threading
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

class AlimanteMenuComplet:
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
        
        # Gestionnaire d'arrêt
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def convert_color(self, rgb_color, method="bgr"):
        """Convertit RGB selon la méthode spécifiée"""
        if len(rgb_color) != 3:
            return rgb_color
            
        conversions = {
            "rgb": lambda c: c,                                    # RGB normal
            "bgr": lambda c: (c[2], c[1], c[0]),                  # BGR
            "grb": lambda c: (c[1], c[0], c[2]),                  # GRB
            "rbg": lambda c: (c[0], c[2], c[1]),                  # RBG
            "gbr": lambda c: (c[1], c[2], c[0]),                  # GBR
            "brg": lambda c: (c[2], c[0], c[1]),                  # BRG
        }
        
        if method in conversions:
            return conversions[method](rgb_color)
        else:
            return rgb_color

    def initialize_display(self):
        """Initialise l'écran ST7735 avec correction BGR"""
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
            
            # Test des couleurs corrigées
            self.test_couleurs_corrigees()
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation écran: {e}")
            return False

    def test_couleurs_corrigees(self):
        """Test des couleurs avec correction BGR"""
        if not self.is_display_initialized:
            return False
            
        print("🎨 Test des couleurs corrigées...")
        
        couleurs_test = [
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
        ]
        
        try:
            for nom, couleur_rgb in couleurs_test:
                print(f"   → {nom} {couleur_rgb}")
                
                # Conversion BGR
                couleur_bgr = self.convert_color(couleur_rgb, "bgr")
                
                # Image plein écran
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_bgr)
                draw = ImageDraw.Draw(image)
                
                # Texte centré
                font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), nom, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (self.display.width - text_width) // 2
                y = (self.display.height - text_height) // 2
                
                # Contraste texte
                brightness = sum(couleur_rgb) / 3
                text_color = (0,0,0) if brightness > 128 else (255,255,255)
                text_color_bgr = self.convert_color(text_color, "bgr")
                
                draw.text((x, y), nom, fill=text_color_bgr, font=font)
                draw.text((5, 5), f"RGB: {couleur_rgb}", fill=text_color_bgr, font=font)
                
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
            image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Titre
            title = "ALIMANTE MENU"
            bbox = draw.textbbox((0, 0), title, font=font)
            title_width = bbox[2] - bbox[0]
            x_title = (self.display.width - title_width) // 2
            draw.text((x_title, 5), title, fill=self.rgb_to_bgr((255, 255, 0)), font=font)
            
            # Ligne de séparation
            draw.line([(5, 20), (self.display.width - 5, 20)], fill=self.rgb_to_bgr((128, 128, 128)))
            
            # Items du menu
            y_pos = 25
            for i, item in enumerate(self.menu_items):
                if i == self.current_selection:
                    # Item sélectionné
                    draw.rectangle([2, y_pos - 2, self.display.width - 2, y_pos + 12], 
                                 fill=self.rgb_to_bgr((0, 100, 255)))
                    draw.text((5, y_pos), item, fill=self.rgb_to_bgr((255, 255, 255)), font=font)
                else:
                    # Item normal
                    draw.text((5, y_pos), item, fill=self.rgb_to_bgr((200, 200, 200)), font=font)
                y_pos += 15
            
            # Informations en bas
            info_text = f"Sel: {self.current_selection + 1}/{len(self.menu_items)}"
            draw.text((5, self.display.height - 15), info_text, fill=self.rgb_to_bgr((128, 128, 128)), font=font)
            
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
        self.show_message("Accueil Alimante", "Système prêt")

    def action_test_led(self):
        """Action: Test LED Bandeaux"""
        print("💡 Test LED Bandeaux")
        self.show_message("Test LED", "Fonctionnalité en développement")

    def action_monitoring(self):
        """Action: Monitoring Système"""
        print("📊 Monitoring Système")
        self.show_message("Monitoring", "Surveillance active")

    def action_configuration(self):
        """Action: Configuration"""
        print("⚙️ Configuration")
        self.show_message("Configuration", "Paramètres système")

    def action_tests_hardware(self):
        """Action: Tests Hardware"""
        print("🔧 Tests Hardware")
        self.show_message("Tests HW", "Diagnostic matériel")

    def action_statistiques(self):
        """Action: Statistiques"""
        print("📈 Statistiques")
        self.show_message("Statistiques", "Données d'utilisation")

    def action_a_propos(self):
        """Action: À propos"""
        print("ℹ️ À propos")
        self.show_message("À propos", "Alimante v1.0.0")

    def show_message(self, title, message):
        """Affiche un message sur l'écran"""
        if not self.is_display_initialized:
            return
            
        try:
            image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Titre
            bbox = draw.textbbox((0, 0), title, font=font)
            title_width = bbox[2] - bbox[0]
            x_title = (self.display.width - title_width) // 2
            draw.text((x_title, 20), title, fill=self.rgb_to_bgr((255, 255, 0)), font=font)
            
            # Message
            bbox = draw.textbbox((0, 0), message, font=font)
            msg_width = bbox[2] - bbox[0]
            x_msg = (self.display.width - msg_width) // 2
            draw.text((x_msg, 50), message, fill=self.rgb_to_bgr((255, 255, 255)), font=font)
            
            # Retour
            draw.text((5, self.display.height - 15), "Appuyez pour retourner", 
                     fill=self.rgb_to_bgr((128, 128, 128)), font=font)
            
            self.display.display(image)
            
            # Attendre l'appui du bouton
            time.sleep(0.5)  # Anti-rebond
            while self.button.is_pressed:
                time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Erreur affichage message: {e}")

    def run_menu(self):
        """Lance le menu principal"""
        print("🚀 Lancement du menu Alimante...")
        
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
        print("🎛️  MENU ALIMANTE ACTIF")
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
                image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
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
    print("🎛️  ALIMANTE - MENU COMBINÉ")
    print("📍 Encodeur rotatif + Écran ST7735")
    print("📍 Correction des couleurs BGR")
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
    menu = AlimanteMenuComplet()
    menu.run_menu()

if __name__ == "__main__":
    main()
