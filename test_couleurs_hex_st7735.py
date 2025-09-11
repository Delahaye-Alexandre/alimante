#!/usr/bin/env python3
"""
Test des couleurs avec valeurs hexadécimales pour ST7735
Utilise les formats natifs du contrôleur
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

class TestCouleursHex:
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

    def rgb_to_hex565(self, rgb):
        """Convertit RGB en RGB565 hex"""
        r, g, b = rgb
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    def test_couleurs_hex_standards(self):
        """Test des couleurs hexadécimales standards"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        # Couleurs hexadécimales standards
        couleurs_hex = [
            ("Noir", 0x0000),
            ("Blanc", 0xFFFF),
            ("Rouge", 0xF800),
            ("Vert", 0x07E0),
            ("Bleu", 0x001F),
            ("Jaune", 0xFFE0),
            ("Cyan", 0x07FF),
            ("Magenta", 0xF81F),
            ("Orange", 0xFC00),
            ("Violet", 0x801F),
            ("Vert clair", 0x07FF),
            ("Rouge foncé", 0x8000),
        ]

        try:
            print("🎨 Test des couleurs hexadécimales standards...")
            
            for nom, hex_color in couleurs_hex:
                print(f"   → {nom}: 0x{hex_color:04X}")
                
                # Conversion hex vers RGB
                rgb_color = self.hex_to_rgb(hex_color)
                print(f"      RGB: {rgb_color}")
                
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
                draw.text((5, 5), f"0x{hex_color:04X}", fill=text_color, font=font)
                draw.text((5, self.display.height - 15), f"RGB: {rgb_color}", fill=text_color, font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs hex: {e}")
            return False

    def test_couleurs_rgb_vers_hex(self):
        """Test conversion RGB vers hex"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        couleurs_rgb = [
            ("Rouge pur", (255, 0, 0)),
            ("Vert pur", (0, 255, 0)),
            ("Bleu pur", (0, 0, 255)),
            ("Jaune pur", (255, 255, 0)),
            ("Cyan pur", (0, 255, 255)),
            ("Magenta pur", (255, 0, 255)),
        ]

        try:
            print("🎨 Test conversion RGB vers hex...")
            
            for nom, rgb_color in couleurs_rgb:
                print(f"   → {nom} {rgb_color}")
                
                # Conversion RGB vers hex
                hex_color = self.rgb_to_hex565(rgb_color)
                print(f"      Hex: 0x{hex_color:04X}")
                
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
                draw.text((5, 5), f"RGB: {rgb_color}", fill=text_color, font=font)
                draw.text((5, self.display.height - 25), f"Hex: 0x{hex_color:04X}", fill=text_color, font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test conversion: {e}")
            return False

    def test_palette_couleurs(self):
        """Test d'une palette de couleurs"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        try:
            print("🎨 Test palette de couleurs...")
            
            # Création d'une palette
            image = Image.new("RGB", (self.display.width, self.display.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            # Titre
            draw.text((10, 5), "PALETTE COULEURS", fill=(255, 255, 255), font=font)
            
            # Barres de couleurs
            couleurs = [
                (0xF800, "Rouge"),
                (0x07E0, "Vert"),
                (0x001F, "Bleu"),
                (0xFFE0, "Jaune"),
                (0x07FF, "Cyan"),
                (0xF81F, "Magenta"),
            ]
            
            y_pos = 25
            for hex_color, nom in couleurs:
                rgb_color = self.hex_to_rgb(hex_color)
                
                # Barre de couleur
                draw.rectangle([10, y_pos, 50, y_pos + 15], fill=rgb_color)
                draw.text((55, y_pos), f"{nom} 0x{hex_color:04X}", fill=(255, 255, 255), font=font)
                y_pos += 20
            
            self.display.display(image)
            time.sleep(5)
            
            return True
        except Exception as e:
            print(f"❌ Erreur test palette: {e}")
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
        print("🔧 TEST COULEURS HEXADÉCIMALES ST7735")
        if not self.initialize():
            return
        
        print("\n" + "=" * 40)
        print("MENU DE TEST COULEURS HEX:")
        print("1. Couleurs hex standards")
        print("2. Conversion RGB vers hex")
        print("3. Palette de couleurs")
        print("4. Tous les tests")
        print("0. Quitter")
        print("=" * 40)
        
        while True:
            choice = input("Votre choix (0-4): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.test_couleurs_hex_standards()
            elif choice == "2":
                self.test_couleurs_rgb_vers_hex()
            elif choice == "3":
                self.test_palette_couleurs()
            elif choice == "4":
                print("🚀 Lancement de tous les tests...")
                self.test_couleurs_hex_standards()
                self.test_couleurs_rgb_vers_hex()
                self.test_palette_couleurs()
            else:
                print("❌ Choix invalide")
        
        self.cleanup()
        print("👋 Tests terminés")

if __name__ == "__main__":
    test = TestCouleursHex()
    test.run_tests()
