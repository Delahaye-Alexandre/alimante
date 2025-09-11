#!/usr/bin/env python3
"""
Test ST7735 basé sur la documentation technique
Utilise les paramètres corrects selon la datasheet
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

class TestST7735Documentation:
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

    def initialize_correct(self):
        """Initialise l'écran selon la documentation ST7735"""
        if not ST7735_AVAILABLE:
            print("❌ ST7735 non disponible")
            return False
        try:
            print("🔧 Initialisation ST7735 selon documentation...")
            
            # Configuration selon la datasheet ST7735
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=270,
                invert=False,  # Pas d'inversion par défaut
                bgr=False      # Format RGB par défaut
            )
            self.display.begin()
            self.is_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            print("   • Format: RGB (pas BGR)")
            print("   • Inversion: Désactivée")
            print("   • Rotation: 270°")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False

    def test_couleurs_documentation(self):
        """Test des couleurs selon la documentation"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test couleurs selon documentation ST7735...")
        
        # Couleurs selon la documentation ST7735
        couleurs_doc = [
            ("Noir", (0, 0, 0), "Doit être noir pur"),
            ("Blanc", (255, 255, 255), "Doit être blanc pur"),
            ("Rouge", (255, 0, 0), "Doit être rouge pur"),
            ("Vert", (0, 255, 0), "Doit être vert pur"),
            ("Bleu", (0, 0, 255), "Doit être bleu pur"),
            ("Jaune", (255, 255, 0), "Doit être jaune pur"),
            ("Cyan", (0, 255, 255), "Doit être cyan pur"),
            ("Magenta", (255, 0, 255), "Doit être magenta pur"),
        ]
        
        try:
            for nom, couleur, description in couleurs_doc:
                print(f"   → {nom} {couleur} - {description}")
                
                # Image plein écran
                image = Image.new("RGB", (self.display.width, self.display.height), couleur)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                # Texte centré
                bbox = draw.textbbox((0, 0), nom, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (self.display.width - text_width) // 2
                y = (self.display.height - text_height) // 2
                
                # Contraste texte
                brightness = sum(couleur) / 3
                text_color = (0,0,0) if brightness > 128 else (255,255,255)
                
                draw.text((x, y), nom, fill=text_color, font=font)
                draw.text((5, 5), f"RGB: {couleur}", fill=text_color, font=font)
                draw.text((5, self.display.height - 25), description, fill=text_color, font=font)
                
                self.display.display(image)
                time.sleep(3)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False

    def test_format_rgb565(self):
        """Test avec format RGB565 selon documentation"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test format RGB565 selon documentation...")
        
        # Couleurs RGB565 selon la documentation
        couleurs_rgb565 = [
            ("Noir", 0x0000),
            ("Blanc", 0xFFFF),
            ("Rouge", 0xF800),
            ("Vert", 0x07E0),
            ("Bleu", 0x001F),
            ("Jaune", 0xFFE0),
            ("Cyan", 0x07FF),
            ("Magenta", 0xF81F),
        ]
        
        try:
            for nom, hex_color in couleurs_rgb565:
                print(f"   → {nom} 0x{hex_color:04X}")
                
                # Conversion RGB565 vers RGB888
                r = (hex_color >> 11) & 0x1F
                g = (hex_color >> 5) & 0x3F
                b = hex_color & 0x1F
                
                # Conversion vers RGB888
                r = (r * 255) // 31
                g = (g * 255) // 63
                b = (b * 255) // 31
                
                rgb_color = (r, g, b)
                print(f"      RGB565: 0x{hex_color:04X} → RGB888: {rgb_color}")
                
                # Image plein écran
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
                text_color = (0,0,0) if brightness > 128 else (255,255,255)
                
                draw.text((x, y), nom, fill=text_color, font=font)
                draw.text((5, 5), f"RGB565: 0x{hex_color:04X}", fill=text_color, font=font)
                draw.text((5, self.display.height - 25), f"RGB888: {rgb_color}", fill=text_color, font=font)
                
                self.display.display(image)
                time.sleep(3)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test RGB565: {e}")
            return False

    def test_parametres_documentation(self):
        """Test des paramètres selon la documentation"""
        if not self.is_initialized:
            return False
            
        print("🔧 Test paramètres selon documentation...")
        
        # Test des paramètres d'initialisation
        parametres = [
            ("Normal", {"invert": False, "bgr": False}),
            ("Invert", {"invert": True, "bgr": False}),
            ("BGR", {"invert": False, "bgr": True}),
            ("Invert+BGR", {"invert": True, "bgr": True}),
        ]
        
        try:
            for nom, params in parametres:
                print(f"   → Test {nom}: {params}")
                
                # Recréer l'écran avec nouveaux paramètres
                self.display = st7735.ST7735(
                    port=0,
                    cs=0,
                    dc=self.a0_pin,
                    rst=self.reset_pin,
                    rotation=270,
                    **params
                )
                self.display.begin()
                
                # Test avec rouge
                image = Image.new("RGB", (self.display.width, self.display.height), (255, 0, 0))
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                draw.text((10, 10), f"Config: {nom}", fill=(255, 255, 255), font=font)
                draw.text((10, 30), "ROUGE (255,0,0)", fill=(255, 255, 255), font=font)
                draw.text((10, 50), f"Params: {params}", fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test paramètres: {e}")
            return False

    def test_rotations_documentation(self):
        """Test des rotations selon la documentation"""
        if not self.is_initialized:
            return False
            
        print("🔄 Test rotations selon documentation...")
        
        rotations = [0, 90, 180, 270]
        couleur_test = (255, 0, 0)  # Rouge
        
        try:
            for rotation in rotations:
                print(f"   → Test rotation {rotation}°")
                
                # Recréer l'écran avec nouvelle rotation
                self.display = st7735.ST7735(
                    port=0,
                    cs=0,
                    dc=self.a0_pin,
                    rst=self.reset_pin,
                    rotation=rotation,
                    invert=False,
                    bgr=False
                )
                self.display.begin()
                
                # Test avec rouge
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_test)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                draw.text((10, 10), f"ROTATION {rotation}°", fill=(255, 255, 255), font=font)
                draw.text((10, 30), "ROUGE (255,0,0)", fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test rotations: {e}")
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
        """Lance les tests selon la documentation"""
        print("🔧 TEST ST7735 SELON DOCUMENTATION")
        if not self.initialize_correct():
            return
        
        print("\n" + "=" * 40)
        print("MENU DE TEST DOCUMENTATION:")
        print("1. Couleurs selon documentation")
        print("2. Format RGB565")
        print("3. Paramètres d'initialisation")
        print("4. Rotations")
        print("5. Tous les tests")
        print("0. Quitter")
        print("=" * 40)
        
        while True:
            choice = input("Votre choix (0-5): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.test_couleurs_documentation()
            elif choice == "2":
                self.test_format_rgb565()
            elif choice == "3":
                self.test_parametres_documentation()
            elif choice == "4":
                self.test_rotations_documentation()
            elif choice == "5":
                print("🚀 Lancement de tous les tests...")
                self.test_couleurs_documentation()
                self.test_format_rgb565()
                self.test_parametres_documentation()
                self.test_rotations_documentation()
            else:
                print("❌ Choix invalide")
        
        self.cleanup()
        print("👋 Tests terminés")

if __name__ == "__main__":
    test = TestST7735Documentation()
    test.run_tests()
