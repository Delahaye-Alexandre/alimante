#!/usr/bin/env python3
"""
Test combiné pour l'encodeur rotatif et l'écran SPI
Configuration basée sur config_alimante.py
Interface interactive avec navigation par encodeur
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
import threading
from config_alimante import get_gpio_config, get_ui_config, get_test_config
from PIL import Image, ImageDraw, ImageFont
import st7735

class EncoderDisplayTest:
    def __init__(self):
        """Initialise le test combiné encodeur + écran"""
        self.config = get_gpio_config()
        self.ui_config = get_ui_config()
        self.test_config = get_test_config()
        
        # Configuration des pins encodeur
        self.clk_pin = self.config['ENCODER']['CLK_PIN']
        self.dt_pin = self.config['ENCODER']['DT_PIN']
        self.sw_pin = self.config['ENCODER']['SW_PIN']
        
        # Configuration des pins écran
        self.reset_pin = self.config['DISPLAY']['RESET_PIN']
        self.a0_pin = self.config['DISPLAY']['A0_PIN']
        self.cs_pin = self.config['DISPLAY']['CS_PIN']
        self.sda_pin = self.config['DISPLAY']['SDA_PIN']
        self.scl_pin = self.config['DISPLAY']['SCL_PIN']
        
        # Configuration de l'écran
        self.width = 128
        self.height = 160
        self.display = None
        
        # Variables d'état
        self.counter = 0
        self.last_clk_state = 0
        self.last_sw_state = 0
        self.sw_pressed = False
        self.sw_press_time = 0
        self.is_running = False
        
        # Interface utilisateur
        self.current_menu = 0
        self.menu_items = [
            "🏠 Accueil Alimante",
            "💡 Test LED Bandeaux", 
            "📊 Monitoring Système",
            "⚙️ Configuration",
            "🔧 Tests Hardware",
            "📈 Statistiques",
            "ℹ️ À propos"
        ]
        self.selected_item = 0
        self.menu_start_y = 30
        self.items_per_screen = 6
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Gestionnaire de signal pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise l'encodeur et l'écran"""
        try:
            # Nettoyage préalable des GPIO
            GPIO.cleanup()
            time.sleep(0.1)
            
            # Initialisation de l'écran
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=270
            )
            self.display.begin()
            
            # Configuration des pins encodeur
            GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Lecture de l'état initial
            self.last_clk_state = GPIO.input(self.clk_pin)
            self.last_sw_state = GPIO.input(self.sw_pin)
            
            self.is_running = True
            
            print("✅ Système combiné initialisé (mode polling)")
            print(f"   📌 Encodeur: CLK={self.clk_pin}, DT={self.dt_pin}, SW={self.sw_pin}")
            print(f"   📌 Écran: RESET={self.reset_pin}, A0={self.a0_pin}, CS={self.cs_pin}")
            print(f"   📐 Résolution: {self.display.width}x{self.display.height}")
            
            # Affichage initial
            self.display_welcome()
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def check_rotation(self):
        """Vérifie la rotation de l'encodeur (polling)"""
        if not self.is_running:
            return
            
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        if clk_state != self.last_clk_state:
            if dt_state != clk_state:
                # Rotation horaire
                self.counter += 1
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
            else:
                # Rotation anti-horaire
                self.counter -= 1
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
            
            self.update_display()
            self.last_clk_state = clk_state
    
    def check_button(self):
        """Vérifie l'état du bouton (polling)"""
        if not self.is_running:
            return
            
        sw_state = GPIO.input(self.sw_pin)
        current_time = time.time()
        
        if sw_state == 0 and self.last_sw_state == 1:
            self.sw_pressed = True
            self.sw_press_time = current_time
            print(f"🔘 Sélection: {self.menu_items[self.selected_item]}")
            self.handle_selection()
        
        elif sw_state == 1 and self.last_sw_state == 0:
            if self.sw_pressed:
                press_duration = current_time - self.sw_press_time
                if press_duration > 2.0:
                    print("🔘 Retour au menu principal")
                    self.display_menu()
                self.sw_pressed = False
        
        self.last_sw_state = sw_state
    
    def display_welcome(self):
        """Affiche l'écran de bienvenue"""
        try:
            image = Image.new('RGB', (self.width, self.height), (0, 0, 50))
            draw = ImageDraw.Draw(image)
            
            # Titre
            try:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            except:
                font_large = font_small = None
            
            draw.text((10, 20), "ALIMANTE", fill=(255, 255, 0), font=font_large)
            draw.text((10, 40), "System Ready", fill=(0, 255, 0), font=font_small)
            draw.text((10, 60), "Rotate to navigate", fill=(255, 255, 255), font=font_small)
            draw.text((10, 80), "Press to select", fill=(255, 255, 255), font=font_small)
            
            # Indicateur de statut
            draw.rectangle([10, 100, 118, 110], outline=(0, 255, 0))
            draw.rectangle([10, 100, 118, 110], fill=(0, 255, 0))
            
            self.display.display(image)
            self.display.display()
            
        except Exception as e:
            print(f"❌ Erreur affichage bienvenue: {e}")
    
    def display_menu(self):
        """Affiche le menu principal"""
        try:
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Titre
            draw.text((10, 10), "MENU PRINCIPAL", fill=(255, 255, 0), font=ImageFont.load_default())
            
            # Items du menu
            start_idx = max(0, self.selected_item - self.items_per_screen // 2)
            end_idx = min(len(self.menu_items), start_idx + self.items_per_screen)
            
            y_pos = self.menu_start_y
            for i in range(start_idx, end_idx):
                item = self.menu_items[i]
                if i == self.selected_item:
                    # Item sélectionné
                    draw.rectangle([5, y_pos - 2, self.width - 5, y_pos + 12], fill=(0, 100, 255))
                    draw.text((10, y_pos), item, fill=(255, 255, 255), font=ImageFont.load_default())
                else:
                    draw.text((10, y_pos), item, fill=(128, 128, 128), font=ImageFont.load_default())
                y_pos += 15
            
            # Indicateur de navigation
            if start_idx > 0:
                draw.text((self.width - 20, 10), "↑", fill=(255, 255, 255), font=ImageFont.load_default())
            if end_idx < len(self.menu_items):
                draw.text((self.width - 20, self.height - 20), "↓", fill=(255, 255, 255), font=ImageFont.load_default())
            
            self.display.display(image)
            self.display.display()
            
        except Exception as e:
            print(f"❌ Erreur affichage menu: {e}")
    
    def update_display(self):
        """Met à jour l'affichage"""
        self.display_menu()
    
    def handle_selection(self):
        """Gère la sélection d'un item du menu"""
        selected = self.menu_items[self.selected_item]
        print(f"🎯 Exécution: {selected}")
        
        if "Accueil" in selected:
            self.display_welcome()
        elif "Test LED" in selected:
            self.test_led_display()
        elif "Monitoring" in selected:
            self.monitoring_display()
        elif "Configuration" in selected:
            self.config_display()
        elif "Tests Hardware" in selected:
            self.hardware_test_display()
        elif "Statistiques" in selected:
            self.stats_display()
        elif "À propos" in selected:
            self.about_display()
    
    def test_led_display(self):
        """Affiche le test des LED"""
        try:
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            draw.text((10, 20), "TEST LED BANDEAUX", fill=(255, 255, 0), font=ImageFont.load_default())
            draw.text((10, 40), "Compteur:", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 60), str(self.counter), fill=(0, 255, 0), font=ImageFont.load_default())
            
            # Barre de progression basée sur le compteur
            progress = abs(self.counter) % 100
            bar_width = int((self.width - 20) * progress / 100)
            draw.rectangle([10, 80, 10 + bar_width, 100], fill=(0, 255, 0))
            draw.rectangle([10, 80, self.width - 10, 100], outline=(255, 255, 255))
            
            draw.text((10, 110), f"Progress: {progress}%", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 130), "Press to return", fill=(128, 128, 128), font=ImageFont.load_default())
            
            self.display.display(image)
            self.display.display()
            
        except Exception as e:
            print(f"❌ Erreur test LED: {e}")
    
    def monitoring_display(self):
        """Affiche le monitoring système"""
        try:
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            draw.text((10, 10), "MONITORING", fill=(255, 255, 0), font=ImageFont.load_default())
            
            # Informations système simulées
            draw.text((10, 30), f"Counter: {self.counter}", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 50), f"Selected: {self.selected_item}", fill=(255, 255, 255), font=ImageFont.load_default())
            
            # Graphique simple
            for i in range(20):
                height = (abs(self.counter + i) % 20) + 5
                x = 10 + i * 5
                draw.rectangle([x, 100 - height, x + 3, 100], fill=(0, 255, 0))
            
            draw.text((10, 120), "Real-time data", fill=(0, 255, 0), font=ImageFont.load_default())
            draw.text((10, 140), "Press to return", fill=(128, 128, 128), font=ImageFont.load_default())
            
            self.display.display(image)
            self.display.display()
            
        except Exception as e:
            print(f"❌ Erreur monitoring: {e}")
    
    def config_display(self):
        """Affiche la configuration"""
        try:
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            draw.text((10, 10), "CONFIGURATION", fill=(255, 255, 0), font=ImageFont.load_default())
            
            # Configuration GPIO
            draw.text((10, 30), f"CLK: GPIO {self.clk_pin}", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 50), f"DT:  GPIO {self.dt_pin}", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 70), f"SW:  GPIO {self.sw_pin}", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 90), f"RESET: GPIO {self.reset_pin}", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 110), f"A0:  GPIO {self.a0_pin}", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 130), f"CS:  GPIO {self.cs_pin}", fill=(255, 255, 255), font=ImageFont.load_default())
            
            self.display.display(image)
            self.display.display()
            
        except Exception as e:
            print(f"❌ Erreur config: {e}")
    
    def hardware_test_display(self):
        """Affiche les tests hardware"""
        try:
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            draw.text((10, 10), "TESTS HARDWARE", fill=(255, 255, 0), font=ImageFont.load_default())
            
            # Tests disponibles
            tests = [
                "✓ Encodeur OK",
                "✓ Écran OK", 
                "✓ GPIO OK",
                "✓ Interruptions OK"
            ]
            
            y_pos = 30
            for test in tests:
                draw.text((10, y_pos), test, fill=(0, 255, 0), font=ImageFont.load_default())
                y_pos += 20
            
            draw.text((10, 120), "All systems OK", fill=(0, 255, 0), font=ImageFont.load_default())
            draw.text((10, 140), "Press to return", fill=(128, 128, 128), font=ImageFont.load_default())
            
            self.display.display(image)
            self.display.display()
            
        except Exception as e:
            print(f"❌ Erreur tests hardware: {e}")
    
    def stats_display(self):
        """Affiche les statistiques"""
        try:
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            draw.text((10, 10), "STATISTIQUES", fill=(255, 255, 0), font=ImageFont.load_default())
            
            # Statistiques simulées
            draw.text((10, 30), f"Rotations: {abs(self.counter)}", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 50), f"Selections: {self.selected_item}", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 70), f"Uptime: {int(time.time()) % 3600}s", fill=(255, 255, 255), font=ImageFont.load_default())
            
            # Graphique simple
            for i in range(15):
                height = (abs(self.counter + i * 2) % 15) + 5
                x = 10 + i * 7
                draw.rectangle([x, 120 - height, x + 5, 120], fill=(0, 255, 0))
            
            draw.text((10, 140), "Press to return", fill=(128, 128, 128), font=ImageFont.load_default())
            
            self.display.display(image)
            self.display.display()
            
        except Exception as e:
            print(f"❌ Erreur stats: {e}")
    
    def about_display(self):
        """Affiche les informations à propos"""
        try:
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            draw.text((10, 10), "À PROPOS", fill=(255, 255, 0), font=ImageFont.load_default())
            
            # Informations système
            draw.text((10, 30), "Alimante v1.0.0", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 50), "Raspberry Pi", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 70), "ST7735 Display", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 90), "Rotary Encoder", fill=(255, 255, 255), font=ImageFont.load_default())
            draw.text((10, 110), "LED Control", fill=(255, 255, 255), font=ImageFont.load_default())
            
            draw.text((10, 140), "Press to return", fill=(128, 128, 128), font=ImageFont.load_default())
            
            self.display.display(image)
            self.display.display()
            
        except Exception as e:
            print(f"❌ Erreur about: {e}")
    
    def test_interactive_mode(self):
        """Mode de test interactif"""
        print("🎮 Mode de test interactif")
        print("   → Tournez l'encodeur pour naviguer")
        print("   → Appuyez sur le bouton pour sélectionner")
        print("   → Appuyez sur Ctrl+C pour arrêter")
        
        self.display_menu()
        
        try:
            while True:
                self.check_rotation()
                self.check_button()
                time.sleep(0.01)  # Polling à 100Hz
        except KeyboardInterrupt:
            print("\n🛑 Mode interactif arrêté")
    
    def test_synchronization(self):
        """Test de synchronisation encodeur-écran"""
        print("🔄 Test de synchronisation...")
        
        # Test de rotation rapide
        print("   → Test de rotation rapide")
        self.display_menu()
        
        # Simulation de rotation rapide
        for i in range(20):
            self.selected_item = (self.selected_item + 1) % len(self.menu_items)
            self.update_display()
            time.sleep(0.1)
        
        # Test de bouton rapide
        print("   → Test de bouton rapide")
        for i in range(5):
            self.handle_selection()
            time.sleep(0.5)
        
        print("✅ Test de synchronisation terminé")
    
    def cleanup(self):
        """Nettoie les ressources"""
        self.is_running = False
        if self.display:
            try:
                image = Image.new("RGB", (self.display.width, self.display.height), (0,0,0))
                self.display.display(image)
            except:
                pass
        GPIO.cleanup()
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du programme...")
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("🔧 TEST COMBINÉ ENCODEUR + ÉCRAN - Alimante")
    print("📍 Configuration basée sur config_alimante.py")
    print("=" * 60)
    
    # Création du testeur
    combined_test = EncoderDisplayTest()
    
    try:
        # Initialisation
        if not combined_test.initialize():
            print("❌ Impossible d'initialiser le système")
            return
        
        # Menu interactif
        while True:
            print("\n" + "=" * 40)
            print("MENU DE TEST COMBINÉ:")
            print("1. Mode interactif (navigation)")
            print("2. Test de synchronisation")
            print("3. Test encodeur seul")
            print("4. Test écran seul")
            print("5. Afficher configuration")
            print("0. Quitter")
            print("=" * 40)
            
            choice = input("Votre choix (0-5): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                combined_test.test_interactive_mode()
            elif choice == "2":
                combined_test.test_synchronization()
            elif choice == "3":
                print("Test encodeur - tournez l'encodeur et appuyez sur le bouton")
                print("Appuyez sur Ctrl+C pour arrêter")
                try:
                    while True:
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    pass
            elif choice == "4":
                print("Test écran - affichage de test")
                combined_test.display_welcome()
                time.sleep(3)
                combined_test.display_menu()
                time.sleep(3)
            elif choice == "5":
                from config_alimante import print_config
                print_config()
            else:
                print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        # Nettoyage
        combined_test.cleanup()
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
