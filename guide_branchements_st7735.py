#!/usr/bin/env python3
"""
Guide de vérification des branchements ST7735
Test pour identifier les inversions de connexions
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

class TestBranchements:
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

    def print_guide_branchements(self):
        """Affiche le guide des branchements corrects"""
        print("🔌 GUIDE DES BRANCHEMENTS ST7735")
        print("=" * 50)
        print()
        print("📋 BRANCHEMENTS CORRECTS :")
        print("   ST7735    →    Raspberry Pi")
        print("   -------        --------------")
        print("   VCC       →    3.3V (Pin 1 ou 17)")
        print("   GND       →    GND (Pin 6, 9, 14, 20, 25, 30, 34, 39)")
        print("   CS        →    GPIO 8 (Pin 24) - Chip Select")
        print("   RST       →    GPIO 24 (Pin 18) - Reset")
        print("   A0/DC     →    GPIO 25 (Pin 22) - Data/Command")
        print("   SDA/MOSI  →    GPIO 10 (Pin 19) - Data")
        print("   SCL/SCLK  →    GPIO 11 (Pin 23) - Clock")
        print()
        print("⚠️  ERREURS FRÉQUENTES :")
        print("   • A0/DC et RST inversés")
        print("   • SDA et SCL inversés")
        print("   • CS mal connecté")
        print("   • Alimentation 3.3V vs 5V")
        print()

    def test_initialisation(self):
        """Test d'initialisation avec différents paramètres"""
        if not ST7735_AVAILABLE:
            print("❌ ST7735 non disponible")
            return False

        print("🔧 Test d'initialisation...")
        
        # Test avec rotation 0° d'abord
        try:
            print("   → Test rotation 0°")
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=0
            )
            self.display.begin()
            self.is_initialized = True
            print(f"   ✅ Écran initialisé: {self.display.width}x{self.display.height}")
            return True
        except Exception as e:
            print(f"   ❌ Erreur initialisation: {e}")
            return False

    def test_couleurs_diagnostic(self):
        """Test de diagnostic des couleurs"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        print("🎨 Test diagnostic couleurs...")
        
        # Test avec couleurs très contrastées
        tests = [
            ("ROUGE PUR", (255, 0, 0), "Si vous voyez du BLEU, A0/DC et RST sont inversés"),
            ("VERT PUR", (0, 255, 0), "Si vous voyez du MAGENTA, A0/DC et RST sont inversés"),
            ("BLEU PUR", (0, 0, 255), "Si vous voyez du ROUGE, A0/DC et RST sont inversés"),
            ("BLANC", (255, 255, 255), "Doit être blanc pur"),
            ("NOIR", (0, 0, 0), "Doit être noir pur"),
        ]

        try:
            for nom, couleur, diagnostic in tests:
                print(f"   → {nom} {couleur}")
                print(f"      {diagnostic}")
                
                image = Image.new("RGB", (self.display.width, self.display.height), couleur)
                draw = ImageDraw.Draw(image)

                # Texte centré
                font = ImageFont.load_default()
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

                self.display.display(image)
                time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False

    def test_rotations(self):
        """Test avec différentes rotations"""
        rotations = [0, 90, 180, 270]
        
        print("🔄 Test des rotations...")
        
        for rotation in rotations:
            print(f"   → Test rotation {rotation}°")
            try:
                self.display = st7735.ST7735(
                    port=0,
                    cs=0,
                    dc=self.a0_pin,
                    rst=self.reset_pin,
                    rotation=rotation
                )
                self.display.begin()
                
                # Test rapide avec rouge
                image = Image.new("RGB", (self.display.width, self.display.height), (255, 0, 0))
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                draw.text((10, 10), f"ROTATION {rotation}°", fill=(255, 255, 255), font=font)
                draw.text((10, 30), "ROUGE (255,0,0)", fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            except Exception as e:
                print(f"      ❌ Erreur rotation {rotation}°: {e}")

    def test_pins_alternatives(self):
        """Test avec des configurations de pins alternatives"""
        print("🔧 Test configurations alternatives...")
        
        # Configuration alternative 1: A0 et RST inversés
        print("   → Test A0/RST inversés")
        try:
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.reset_pin,  # A0 et RST inversés
                rst=self.a0_pin,
                rotation=0
            )
            self.display.begin()
            
            image = Image.new("RGB", (self.display.width, self.display.height), (255, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            draw.text((10, 10), "A0/RST INVERSES", fill=(255, 255, 255), font=font)
            draw.text((10, 30), "ROUGE TEST", fill=(255, 255, 255), font=font)
            
            self.display.display(image)
            time.sleep(2)
            
        except Exception as e:
            print(f"      ❌ Erreur A0/RST inversés: {e}")

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

    def run_diagnostic(self):
        """Lance le diagnostic complet"""
        self.print_guide_branchements()
        
        print("🔧 DIAGNOSTIC DES BRANCHEMENTS")
        print("=" * 40)
        
        if self.test_initialisation():
            self.test_couleurs_diagnostic()
            self.test_rotations()
            self.test_pins_alternatives()
        
        self.cleanup()
        
        print("\n📋 RÉSULTATS DU DIAGNOSTIC:")
        print("=" * 40)
        print("1. Vérifiez les couleurs affichées vs attendues")
        print("2. Si ROUGE apparaît en BLEU → A0/DC et RST inversés")
        print("3. Si l'écran est noir → problème d'alimentation ou CS")
        print("4. Si l'écran scintille → problème de clock ou données")
        print("5. Testez différentes rotations pour l'orientation")
        print()
        print("🔧 CORRECTIONS POSSIBLES:")
        print("• Échangez A0/DC et RST si les couleurs sont inversées")
        print("• Vérifiez que CS est bien connecté à GPIO 8")
        print("• Vérifiez l'alimentation 3.3V")
        print("• Testez avec rotation 0° d'abord")

if __name__ == "__main__":
    test = TestBranchements()
    test.run_diagnostic()
