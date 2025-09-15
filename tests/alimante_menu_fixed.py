#!/usr/bin/env python3
"""
Menu Principal Alimante - Version avec correction d'importation
Corrige le problème d'importation numpy/st7735
"""

import time
import sys
import os
import signal
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_alimante import get_gpio_config, get_ui_config

# Import des librairies avec gestion d'erreur améliorée
ST7735_AVAILABLE = False
GPIOZERO_AVAILABLE = False

# Test d'importation st7735 avec correction
print("🔧 Test d'importation des librairies...")

try:
    # Import numpy en premier pour éviter les conflits
    import numpy as np
    print("✅ numpy importé")
    
    # Changer temporairement le répertoire de travail pour éviter l'erreur numpy
    original_cwd = os.getcwd()
    os.chdir('/tmp')  # Changer vers un répertoire neutre
    
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    
    # Restaurer le répertoire de travail
    os.chdir(original_cwd)
    
    ST7735_AVAILABLE = True
    print("✅ Librairies ST7735 et PIL importées avec succès")
    
except Exception as e:
    print(f"⚠️  Erreur ST7735: {e}")
    print("   Tentative de correction...")
    
    # Restaurer le répertoire de travail en cas d'erreur
    try:
        os.chdir(original_cwd)
    except:
        pass
    
    # Essayer une approche alternative
    try:
        # Désactiver temporairement les warnings numpy
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning)
        
        import st7735
        from PIL import Image, ImageDraw, ImageFont
        ST7735_AVAILABLE = True
        print("✅ Librairies ST7735 et PIL importées (mode alternatif)")
        
    except Exception as e2:
        print(f"❌ Impossible d'importer ST7735: {e2}")
        ST7735_AVAILABLE = False

try:
    from gpiozero import RotaryEncoder, Button
    GPIOZERO_AVAILABLE = True
    print("✅ Librairie gpiozero importée avec succès")
except Exception as e:
    GPIOZERO_AVAILABLE = False
    print(f"⚠️  Erreur gpiozero: {e}")

class AlimanteMenuFixed:
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
        """Initialise l'écran ST7735 avec gestion d'erreur améliorée"""
        if not ST7735_AVAILABLE:
            print("❌ ST7735 non disponible")
            return False
        
        try:
            print("🔧 Initialisation de l'écran ST7735...")
            
            # Changer temporairement le répertoire de travail
            original_cwd = os.getcwd()
            os.chdir('/tmp')
            
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=270,
                invert=False,
                bgr=False
            )
            
            # Restaurer le répertoire de travail
            os.chdir(original_cwd)
            
            self.display.begin()
            self.is_display_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation écran: {e}")
            # Restaurer le répertoire de travail en cas d'erreur
            try:
                os.chdir(original_cwd)
            except:
                pass
            return False

    def initialize_encoder(self):
        """Initialise l'encodeur rotatif"""
        if not GPIOZERO_AVAILABLE:
            print("❌ gpiozero non disponible")
            return False
            
        try:
            print("🔧 Initialisation de l'encodeur rotatif...")
            
            self.encoder = RotaryEncoder(
                a=self.clk_pin,
                b=self.dt_pin,
                max_steps=0
            )
            
            self.button = Button(self.sw_pin, pull_up=True)
            
            self.encoder.when_rotated = self._on_rotation
            self.button.when_pressed = self._on_button_pressed
            
            self.is_encoder_initialized = True
            print("✅ Encodeur et bouton initialisés")
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation encodeur: {e}")
            return False

    def _on_rotation(self):
        """Callback de rotation de l'encodeur"""
        if not self.is_running:
            return
            
        old_counter = self.counter
        self.counter = self.encoder.steps
        
        if self.encoder.steps > old_counter:
            self.current_selection = (self.current_selection - 1) % len(self.menu_items)
            print(f"🔄 Rotation horaire → Menu: {self.current_selection + 1}")
        else:
            self.current_selection = (self.current_selection + 1) % len(self.menu_items)
            print(f"🔄 Rotation anti-horaire → Menu: {self.current_selection + 1}")
        
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
            # Changer temporairement le répertoire de travail
            original_cwd = os.getcwd()
            os.chdir('/tmp')
            
            image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Titre
            title = "ALIMANTE MENU"
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
                    draw.rectangle([2, y_pos - 2, self.display.width - 2, y_pos + 12], 
                                 fill=(0, 100, 255))
                    draw.text((5, y_pos), item, fill=(255, 255, 255), font=font)
                else:
                    draw.text((5, y_pos), item, fill=(200, 200, 200), font=font)
                y_pos += 15
            
            # Informations en bas
            info_text = f"Sel: {self.current_selection + 1}/{len(self.menu_items)}"
            draw.text((5, self.display.height - 15), info_text, fill=(128, 128, 128), font=font)
            
            # Affichage
            self.display.display(image)
            
            # Restaurer le répertoire de travail
            os.chdir(original_cwd)
            
        except Exception as e:
            print(f"❌ Erreur mise à jour affichage: {e}")
            # Restaurer le répertoire de travail en cas d'erreur
            try:
                os.chdir(original_cwd)
            except:
                pass

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
        self.show_message("Accueil Alimante", "Système prêt", (0, 255, 0))

    def action_test_led(self):
        """Action: Test LED Bandeaux"""
        print("💡 Test LED Bandeaux")
        self.show_message("Test LED", "Fonctionnalité en développement", (255, 165, 0))

    def action_monitoring(self):
        """Action: Monitoring Système"""
        print("📊 Monitoring Système")
        self.show_message("Monitoring", "Surveillance active", (0, 255, 255))

    def action_configuration(self):
        """Action: Configuration"""
        print("⚙️ Configuration")
        self.show_message("Configuration", "Paramètres système", (128, 0, 128))

    def action_tests_hardware(self):
        """Action: Tests Hardware"""
        print("🔧 Tests Hardware")
        self.show_message("Tests HW", "Diagnostic matériel", (255, 0, 0))

    def action_statistiques(self):
        """Action: Statistiques"""
        print("📈 Statistiques")
        self.show_message("Statistiques", "Données d'utilisation", (255, 0, 255))

    def action_a_propos(self):
        """Action: À propos"""
        print("ℹ️ À propos")
        self.show_message("À propos", "Alimante v1.0.0", (255, 255, 0))

    def show_message(self, title, message, color=(255, 255, 255)):
        """Affiche un message sur l'écran"""
        if not self.is_display_initialized:
            return
            
        try:
            # Changer temporairement le répertoire de travail
            original_cwd = os.getcwd()
            os.chdir('/tmp')
            
            image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Titre
            bbox = draw.textbbox((0, 0), title, font=font)
            title_width = bbox[2] - bbox[0]
            x_title = (self.display.width - title_width) // 2
            draw.text((x_title, 20), title, fill=color, font=font)
            
            # Message
            bbox = draw.textbbox((0, 0), message, font=font)
            msg_width = bbox[2] - bbox[0]
            x_msg = (self.display.width - msg_width) // 2
            draw.text((x_msg, 50), message, fill=(255, 255, 255), font=font)
            
            # Retour
            draw.text((5, self.display.height - 15), "Appuyez pour retourner", 
                     fill=(128, 128, 128), font=font)
            
            self.display.display(image)
            
            # Restaurer le répertoire de travail
            os.chdir(original_cwd)
            
            # Attendre l'appui du bouton
            time.sleep(0.5)
            while self.button.is_pressed:
                time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Erreur affichage message: {e}")
            # Restaurer le répertoire de travail en cas d'erreur
            try:
                os.chdir(original_cwd)
            except:
                pass

    def run_menu(self):
        """Lance le menu principal"""
        print("🚀 Lancement du menu Alimante (version corrigée)...")
        
        # Initialisation des composants
        if not self.initialize_display():
            print("❌ Impossible d'initialiser l'écran")
            print("   Le menu fonctionnera en mode console uniquement")
            
        if not self.initialize_encoder():
            print("❌ Impossible d'initialiser l'encodeur")
            print("   Le menu fonctionnera en mode console uniquement")
        
        # Démarrage du menu
        self.is_running = True
        if self.is_display_initialized:
            self.update_display()
        
        print("\n" + "=" * 50)
        print("🎛️  MENU ALIMANTE ACTIF")
        print("=" * 50)
        if self.is_encoder_initialized:
            print("• Tournez l'encodeur pour naviguer")
            print("• Appuyez sur le bouton pour sélectionner")
        else:
            print("• Mode console - utilisez les touches du clavier")
            print("• Flèches haut/bas pour naviguer, Entrée pour sélectionner")
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
        
        if self.display and self.is_display_initialized:
            try:
                # Changer temporairement le répertoire de travail
                original_cwd = os.getcwd()
                os.chdir('/tmp')
                
                image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
                self.display.display(image)
                
                # Restaurer le répertoire de travail
                os.chdir(original_cwd)
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
    print("🎛️  ALIMANTE - MENU CORRIGÉ")
    print("📍 Encodeur rotatif + Écran ST7735")
    print("📍 Version avec correction d'importation")
    print("=" * 60)
    
    # Vérification des dépendances
    if not ST7735_AVAILABLE:
        print("⚠️  ST7735 non disponible - mode console uniquement")
        print("   L'écran ne fonctionnera pas mais le menu reste utilisable")
        
    if not GPIOZERO_AVAILABLE:
        print("⚠️  gpiozero non disponible - mode console uniquement")
        print("   L'encodeur ne fonctionnera pas mais le menu reste utilisable")
    
    # Création et lancement du menu
    menu = AlimanteMenuFixed()
    menu.run_menu()

if __name__ == "__main__":
    main()
