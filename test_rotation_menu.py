#!/usr/bin/env python3
"""
Test de la rotation dans le menu
Vérifie que la détection de rotation fonctionne correctement
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

class TestRotationMenu:
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
                rotation=270,
                invert=False,
                bgr=False
            )
            self.display.begin()
            self.is_display_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation écran: {e}")
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
            
        # Sauvegarde de l'ancien compteur
        old_counter = self.counter
        
        # Mise à jour du compteur
        self.counter = self.encoder.steps
        
        # Mise à jour de la sélection du menu (INVERSÉ)
        if self.encoder.steps > old_counter:
            # Rotation horaire = menu vers le bas (inversé)
            self.current_selection = (self.current_selection - 1) % len(self.menu_items)
            direction = "HORAIRE"
        else:
            # Rotation anti-horaire = menu vers le haut (inversé)
            self.current_selection = (self.current_selection + 1) % len(self.menu_items)
            direction = "ANTI-HORAIRE"
        
        print(f"🔄 Rotation {direction} | Compteur: {self.counter} | Menu: {self.current_selection + 1}")
        
        # Mise à jour de l'affichage
        self.update_display()

    def _on_button_pressed(self):
        """Callback d'appui du bouton"""
        if not self.is_running:
            return
            
        print(f"🔘 Sélection: {self.menu_items[self.current_selection]}")
        self.show_selection_message()

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
            title = "TEST ROTATION"
            bbox = draw.textbbox((0, 0), title, font=font)
            title_width = bbox[2] - bbox[0]
            x_title = (self.display.width - title_width) // 2
            draw.text((x_title, 5), title, fill=(255, 255, 0), font=font)
            
            # Ligne de séparation
            draw.line([(5, 20), (self.display.width - 5, 20)], fill=(128, 128, 128))
            
            # Items du menu
            y_pos = 25
            for i, item in enumerate(self.menu_items):
                if i == self.current_selection:
                    # Item sélectionné
                    draw.rectangle([2, y_pos - 2, self.display.width - 2, y_pos + 12], 
                                 fill=(0, 100, 255))
                    draw.text((5, y_pos), item, fill=(255, 255, 255), font=font)
                else:
                    # Item normal
                    draw.text((5, y_pos), item, fill=(200, 200, 200), font=font)
                y_pos += 15
            
            # Informations en bas
            info_text = f"Sel: {self.current_selection + 1}/{len(self.menu_items)}"
            draw.text((5, self.display.height - 25), info_text, fill=(128, 128, 128), font=font)
            
            # Compteur
            counter_text = f"Compteur: {self.counter}"
            draw.text((5, self.display.height - 15), counter_text, fill=(128, 128, 128), font=font)
            
            # Affichage
            self.display.display(image)
            
        except Exception as e:
            print(f"❌ Erreur mise à jour affichage: {e}")

    def show_selection_message(self):
        """Affiche un message de sélection"""
        if not self.is_display_initialized:
            return
            
        try:
            image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Message de sélection
            selected_item = self.menu_items[self.current_selection]
            draw.text((10, 20), "SELECTION:", fill=(255, 255, 0), font=font)
            draw.text((10, 40), selected_item, fill=(255, 255, 255), font=font)
            
            # Retour
            draw.text((5, self.display.height - 15), "Appuyez pour continuer", 
                     fill=(128, 128, 128), font=font)
            
            self.display.display(image)
            
            # Attendre l'appui du bouton
            time.sleep(0.5)  # Anti-rebond
            while self.button.is_pressed:
                time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Erreur affichage message: {e}")

    def run_test(self):
        """Lance le test de rotation"""
        print("🚀 Test de rotation dans le menu...")
        
        # Initialisation des composants
        if not self.initialize_display():
            print("❌ Impossible d'initialiser l'écran")
            return
            
        if not self.initialize_encoder():
            print("❌ Impossible d'initialiser l'encodeur")
            return
        
        # Démarrage du test
        self.is_running = True
        self.update_display()
        
        print("\n" + "=" * 50)
        print("🔄 TEST DE ROTATION")
        print("=" * 50)
        print("• Tournez l'encodeur pour naviguer")
        print("• Appuyez sur le bouton pour sélectionner")
        print("• Ctrl+C pour quitter")
        print("=" * 50)
        
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du test")
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
    print("🔄 TEST ROTATION MENU")
    print("📍 Test de la détection de rotation")
    print("=" * 60)
    
    # Vérification des dépendances
    if not ST7735_AVAILABLE:
        print("❌ ST7735 non disponible")
        return
        
    if not GPIOZERO_AVAILABLE:
        print("❌ gpiozero non disponible")
        return
    
    # Création et lancement du test
    test = TestRotationMenu()
    test.run_test()

if __name__ == "__main__":
    main()
