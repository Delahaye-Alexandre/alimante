#!/usr/bin/env python3
"""
Test pour l'écran SPI ST7735
Configuration basée sur config_alimante.py
Pins: RESET=24, A0/DC=25, CS=8, SDA/MOSI=10, SCL/SCLK=11
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
import threading
from config_alimante import get_gpio_config, get_ui_config
from PIL import Image, ImageDraw, ImageFont
import st7735

class SPIDisplayTest:
    def __init__(self):
        """Initialise le test de l'écran SPI ST7735"""
        self.config = get_gpio_config()
        self.ui_config = get_ui_config()
        
        # Configuration des pins
        self.reset_pin = self.config['DISPLAY']['RESET_PIN']
        self.a0_pin = self.config['DISPLAY']['A0_PIN']
        self.cs_pin = self.config['DISPLAY']['CS_PIN']
        self.sda_pin = self.config['DISPLAY']['SDA_PIN']
        self.scl_pin = self.config['DISPLAY']['SCL_PIN']
        
        # Configuration de l'écran
        self.width = 128
        self.height = 160
        self.display = None
        self.is_initialized = False
        
        # Gestionnaire de signal pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise l'écran SPI ST7735"""
        try:
            print("🔧 Initialisation de l'écran ST7735...")
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=270  # Ajuster selon votre montage
            )
            self.display.begin()
            self.is_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False
    
    def clear_screen(self, color=(0, 0, 0)):
        """Efface l'écran avec une couleur"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        try:
            image = Image.new("RGB", (self.display.width, self.display.height), color)
            self.display.display(image)
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'effacement: {e}")
            return False
    
    def test_colors(self):
        """Test des couleurs de base"""
        print("🎨 Test des couleurs de base...")
        
        colors = [
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
            ("Blanc", (255, 255, 255)),
            ("Noir", (0, 0, 0)),
            ("Jaune", (255, 255, 0)),
            ("Cyan", (0, 255, 255)),
            ("Magenta", (255, 0, 255))
        ]
        
        for name, color in colors:
            print(f"   → {name}")
            # Image plein écran
            image = Image.new("RGB", (self.display.width, self.display.height), color)
            draw = ImageDraw.Draw(image)

            # Texte centré
            font = ImageFont.load_default()
            text_width, text_height = draw.textsize(name, font=font)
            x = (self.display.width - text_width) // 2
            y = (self.display.height - text_height) // 2

            # Contraste texte selon fond
            brightness = sum(color) / 3
            text_color = (0,0,0) if brightness > 128 else (255,255,255)

            draw.text((x, y), name, fill=text_color, font=font)
            self.display.display(image)
            time.sleep(2)
        
        print("✅ Test des couleurs terminé")
    
    def test_gradients(self):
        """Test des dégradés"""
        print("🌈 Test des dégradés...")
        
        # Dégradé horizontal rouge
        print("   → Dégradé horizontal rouge")
        image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        for x in range(self.display.width):
            intensity = int((x / self.display.width) * 255)
            color = (intensity, 0, 0)
            draw.line([(x, 0), (x, self.display.height-1)], fill=color)
        self.display.display(image)
        time.sleep(2)
        
        # Dégradé vertical vert
        print("   → Dégradé vertical vert")
        for y in range(self.height):
            intensity = int((y / self.height) * 255)
            color = (0, intensity, 0)
            for x in range(self.width):
                self.display.set_pixel(x, y, color)
        self.display.display()
        time.sleep(2)
        
        # Dégradé diagonal bleu
        print("   → Dégradé diagonal bleu")
        for x in range(self.width):
            for y in range(self.height):
                intensity = int(((x + y) / (self.width + self.height)) * 255)
                color = (0, 0, intensity)
                self.display.set_pixel(x, y, color)
        self.display.display()
        time.sleep(2)
        
        print("✅ Test des dégradés terminé")
    
    def test_shapes(self):
        """Test des formes géométriques"""
        print("🔷 Test des formes géométriques...")
        
        try:
            image = Image.new("RGB", (self.display.width, self.display.height), (0,0,0))
            draw = ImageDraw.Draw(image)

            # Cadre blanc
            draw.rectangle([0,0,self.display.width-1,self.display.height-1], outline=(255,255,255), width=2)

            # Formes
            draw.rectangle([5,5,45,25], fill=(255,0,0), outline=(255,255,255))  # Rouge
            draw.ellipse([self.display.width-45,5,self.display.width-5,45], fill=(0,255,0), outline=(255,255,255))  # Vert
            draw.polygon([(30,self.display.height-30),(50,self.display.height-10),(10,self.display.height-10)], fill=(255,255,0))  # Jaune
            draw.line([(0,0),(self.display.width-1,self.display.height-1)], fill=(0,255,255), width=2)  # Cyan

            # Texte
            font = ImageFont.load_default()
            draw.text((10, 50), "ALIMANTE", fill=(255, 255, 255), font=font)
            draw.text((10, 70), "Test ST7735", fill=(0, 255, 255), font=font)

            self.display.display(image)
            time.sleep(3)
            print("✅ Test des formes terminé")
            return True
        except Exception as e:
            print(f"❌ Erreur test formes: {e}")
            return False
    
    def test_text(self):
        """Test d'affichage de texte"""
        print("📝 Test d'affichage de texte...")
        
        try:
            # Création d'une image avec texte
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Essai d'utiliser une police système
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
                except:
                    font = ImageFont.load_default()
            
            # Texte de test
            texts = [
                "ALIMANTE",
                "Test SPI",
                "ST7735",
                "128x160",
                "Raspberry Pi"
            ]
            
            y_pos = 10
            for text in texts:
                print(f"   → {text}")
                draw.text((10, y_pos), text, fill=(255, 255, 255), font=font)
                y_pos += 20
            
            self.display.image(image)
            self.display.display()
            time.sleep(3)
            
            print("✅ Test de texte terminé")
            
        except Exception as e:
            print(f"❌ Erreur lors du test de texte: {e}")
    
    def test_animation(self):
        """Test d'animation simple"""
        print("🎬 Test d'animation...")
        
        # Animation de barre de progression
        print("   → Barre de progression")
        for progress in range(0, 101, 5):
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Barre de progression
            bar_width = int((self.width - 20) * progress / 100)
            draw.rectangle([10, 60, 10 + bar_width, 80], fill=(0, 255, 0))
            draw.rectangle([10, 60, self.width - 10, 80], outline=(255, 255, 255))
            
            # Texte de pourcentage
            try:
                font = ImageFont.load_default()
                draw.text((10, 90), f"{progress}%", fill=(255, 255, 255), font=font)
            except:
                pass
            
            self.display.image(image)
            self.display.display()
            time.sleep(0.1)
        
        # Animation de pixels clignotants
        print("   → Pixels clignotants")
        for frame in range(20):
            image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Pixels aléatoires
            import random
            for _ in range(50):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                draw.point((x, y), fill=color)
            
            self.display.image(image)
            self.display.display()
            time.sleep(0.2)
        
        print("✅ Test d'animation terminé")
    
    def test_menu_display(self):
        """Test d'affichage de menu"""
        print("📋 Test d'affichage de menu...")
        
        menu_items = [
            "🏠 Accueil",
            "💡 Test LED",
            "📊 Monitoring",
            "⚙️ Config",
            "🔧 Tests",
            "📈 Stats",
            "ℹ️ À propos"
        ]
        
        try:
            font = ImageFont.load_default()
            
            for i, item in enumerate(menu_items):
                print(f"   → {item}")
                
                image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
                draw = ImageDraw.Draw(image)
                
                # Titre
                draw.text((10, 10), "MENU ALIMANTE", fill=(255, 255, 0), font=font)
                
                # Item sélectionné (simulation)
                y_pos = 30
                for j, menu_item in enumerate(menu_items):
                    if j == i:
                        # Item sélectionné en surbrillance
                        draw.rectangle([5, y_pos - 2, self.width - 5, y_pos + 12], fill=(0, 100, 255))
                        draw.text((10, y_pos), menu_item, fill=(255, 255, 255), font=font)
                    else:
                        draw.text((10, y_pos), menu_item, fill=(128, 128, 128), font=font)
                    y_pos += 15
                
                self.display.image(image)
                self.display.display()
                time.sleep(1)
            
            print("✅ Test de menu terminé")
            
        except Exception as e:
            print(f"❌ Erreur lors du test de menu: {e}")
    
    def test_performance(self):
        """Test de performance de l'écran"""
        print("⚡ Test de performance...")
        
        # Test de rafraîchissement rapide
        print("   → Test de rafraîchissement rapide")
        start_time = time.time()
        
        for i in range(50):
            color = (i * 5 % 255, (i * 7) % 255, (i * 11) % 255)
            self.clear_screen(color)
        
        end_time = time.time()
        fps = 50 / (end_time - start_time)
        print(f"   → FPS moyen: {fps:.1f}")
        
        # Test de pixels individuels
        print("   → Test de pixels individuels")
        start_time = time.time()
        
        for i in range(1000):
            x = i % self.width
            y = (i // self.width) % self.height
            color = (i % 255, (i * 2) % 255, (i * 3) % 255)
            self.display.set_pixel(x, y, color)
        
        self.display.display()
        end_time = time.time()
        print(f"   → 1000 pixels en {end_time - start_time:.3f}s")
        
        print("✅ Test de performance terminé")
    
    def test_sequence(self):
        """Séquence de test complète"""
        print("🚀 Début de la séquence de test complète...")
        
        tests = [
            ("Couleurs de base", self.test_colors),
            ("Dégradés", self.test_gradients),
            ("Formes géométriques", self.test_shapes),
            ("Affichage de texte", self.test_text),
            ("Animation", self.test_animation),
            ("Menu d'affichage", self.test_menu_display),
            ("Performance", self.test_performance)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}...")
            try:
                test_func()
                print(f"✅ {test_name} réussi")
            except Exception as e:
                print(f"❌ {test_name} échoué: {e}")
            
            time.sleep(1)
        
        print("\n🎉 Séquence de test complète terminée!")
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self.display:
            self.clear_screen()
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
    print("🔧 TEST ÉCRAN SPI ST7735 - Alimante")
    print("📍 Configuration basée sur config_alimante.py")
    print("=" * 60)
    
    # Création du testeur
    display_test = SPIDisplayTest()
    
    try:
        # Initialisation
        if not display_test.initialize():
            print("❌ Impossible d'initialiser l'écran")
            return
        
        # Menu interactif
        while True:
            print("\n" + "=" * 40)
            print("MENU DE TEST ÉCRAN SPI:")
            print("1. Test couleurs de base")
            print("2. Test dégradés")
            print("3. Test formes géométriques")
            print("4. Test affichage de texte")
            print("5. Test animation")
            print("6. Test menu d'affichage")
            print("7. Test de performance")
            print("8. Séquence de test complète")
            print("9. Effacer l'écran")
            print("0. Quitter")
            print("=" * 40)
            
            choice = input("Votre choix (0-9): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                display_test.test_colors()
            elif choice == "2":
                display_test.test_gradients()
            elif choice == "3":
                display_test.test_shapes()
            elif choice == "4":
                display_test.test_text()
            elif choice == "5":
                display_test.test_animation()
            elif choice == "6":
                display_test.test_menu_display()
            elif choice == "7":
                display_test.test_performance()
            elif choice == "8":
                display_test.test_sequence()
            elif choice == "9":
                color_choice = input("Couleur (r/g/b/w/k ou r,g,b): ").strip().lower()
                if color_choice == "r":
                    display_test.clear_screen((255, 0, 0))
                elif color_choice == "g":
                    display_test.clear_screen((0, 255, 0))
                elif color_choice == "b":
                    display_test.clear_screen((0, 0, 255))
                elif color_choice == "w":
                    display_test.clear_screen((255, 255, 255))
                elif color_choice == "k":
                    display_test.clear_screen((0, 0, 0))
                else:
                    try:
                        r, g, b = map(int, color_choice.split(','))
                        display_test.clear_screen((r, g, b))
                    except:
                        display_test.clear_screen()
            else:
                print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        # Nettoyage
        display_test.cleanup()
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
