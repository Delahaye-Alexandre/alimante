#!/usr/bin/env python3
"""
Test rapide des couleurs pour identifier la bonne conversion
"""

import time
import sys
import signal
from config_alimante import get_gpio_config

# Import ST7735 et PIL
try:
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    ST7735_AVAILABLE = True
    print("✅ Librairies ST7735 et PIL importées avec succès")
except Exception as e:
    ST7735_AVAILABLE = False
    print(f"⚠️  Erreur lors de l'import: {e}")

class TestCouleursRapide:
    def __init__(self):
        self.config = get_gpio_config()
        self.display = None
        self.is_initialized = False

        # Pins du display
        self.reset_pin = self.config['DISPLAY']['RESET_PIN']
        self.a0_pin = self.config['DISPLAY']['A0_PIN']

        # Gestionnaire d'arrêt
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize(self):
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
            self.is_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False

    def test_conversion(self, nom, couleur_rgb, conversion_func, conversion_name):
        """Test une conversion spécifique"""
        if not self.is_initialized:
            return False
            
        try:
            print(f"   → {nom} {conversion_name}: {conversion_func(couleur_rgb)}")
            
            # Image plein écran
            couleur_convertie = conversion_func(couleur_rgb)
            image = Image.new("RGB", (self.display.width, self.display.height), couleur_convertie)
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Texte
            draw.text((10, 10), nom, fill=(255, 255, 255), font=font)
            draw.text((10, 30), conversion_name, fill=(255, 255, 255), font=font)
            draw.text((10, 50), str(couleur_convertie), fill=(255, 255, 255), font=font)
            
            self.display.display(image)
            time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Erreur test {conversion_name}: {e}")
            return False

    def test_toutes_conversions(self):
        """Test toutes les conversions possibles"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        # Couleurs de test
        couleurs = [
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255))
        ]

        # Conversions à tester
        conversions = [
            ("RGB", lambda c: c),
            ("BGR", lambda c: (c[2], c[1], c[0])),
            ("GRB", lambda c: (c[1], c[0], c[2])),
            ("RBG", lambda c: (c[0], c[2], c[1])),
            ("GBR", lambda c: (c[1], c[2], c[0])),
            ("BRG", lambda c: (c[2], c[0], c[1])),
        ]

        try:
            print("🎨 Test de toutes les conversions...")
            print("👀 Observez quelle conversion donne les bonnes couleurs!")
            
            for nom, couleur_rgb in couleurs:
                print(f"\n🔍 Test {nom} {couleur_rgb}:")
                
                for conv_name, conv_func in conversions:
                    self.test_conversion(nom, couleur_rgb, conv_func, conv_name)
                    
            return True
        except Exception as e:
            print(f"❌ Erreur test conversions: {e}")
            return False

    def test_conversion_specifique(self, method="bgr"):
        """Test une conversion spécifique"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        conversions = {
            "rgb": lambda c: c,
            "bgr": lambda c: (c[2], c[1], c[0]),
            "grb": lambda c: (c[1], c[0], c[2]),
            "rbg": lambda c: (c[0], c[2], c[1]),
            "gbr": lambda c: (c[1], c[2], c[0]),
            "brg": lambda c: (c[2], c[0], c[1]),
        }

        if method not in conversions:
            print(f"❌ Méthode {method} non reconnue")
            return False

        couleurs = [
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
            ("Jaune", (255, 255, 0)),
            ("Cyan", (0, 255, 255)),
            ("Magenta", (255, 0, 255)),
            ("Blanc", (255, 255, 255)),
            ("Noir", (0, 0, 0))
        ]

        try:
            print(f"🎨 Test avec conversion {method.upper()}...")
            
            for nom, couleur_rgb in couleurs:
                print(f"   → {nom} {couleur_rgb}")
                
                # Conversion
                couleur_convertie = conversions[method](couleur_rgb)
                
                # Image plein écran
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_convertie)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                # Texte centré
                bbox = draw.textbbox((0, 0), nom, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (self.display.width - text_width) // 2
                y = (self.display.height - text_height) // 2
                
                # Contraste texte
                brightness = sum(couleur_rgb) / 3
                text_color = (0,0,0) if brightness > 128 else (255,255,255)
                text_color_conv = conversions[method](text_color)
                
                draw.text((x, y), nom, fill=text_color_conv, font=font)
                draw.text((5, 5), f"{method.upper()}: {couleur_convertie}", fill=text_color_conv, font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test {method}: {e}")
            return False

    def cleanup(self):
        """Nettoie l'écran"""
        if self.display:
            try:
                image = Image.new("RGB", (self.display.width, self.display.height), (0,0,0))
                self.display.display(image)
            except:
                pass
        self.is_initialized = False
        print("🧹 Écran nettoyé")

    def _signal_handler(self, signum, frame):
        print("\n🛑 Arrêt du programme")
        self.cleanup()
        sys.exit(0)

    def run_tests(self):
        """Lance les tests"""
        print("🔧 TEST RAPIDE DES COULEURS")
        if not self.initialize():
            return
        
        print("\n" + "=" * 40)
        print("MENU DE TEST COULEURS:")
        print("1. Toutes les conversions")
        print("2. Test BGR")
        print("3. Test GRB")
        print("4. Test RBG")
        print("5. Test GBR")
        print("6. Test BRG")
        print("0. Quitter")
        print("=" * 40)
        
        while True:
            choice = input("Votre choix (0-6): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.test_toutes_conversions()
            elif choice == "2":
                self.test_conversion_specifique("bgr")
            elif choice == "3":
                self.test_conversion_specifique("grb")
            elif choice == "4":
                self.test_conversion_specifique("rbg")
            elif choice == "5":
                self.test_conversion_specifique("gbr")
            elif choice == "6":
                self.test_conversion_specifique("brg")
            else:
                print("❌ Choix invalide")
        
        self.cleanup()
        print("👋 Tests terminés")

if __name__ == "__main__":
    test = TestCouleursRapide()
    test.run_tests()
