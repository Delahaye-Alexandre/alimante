#!/usr/bin/env python3
"""
Test de diagnostic des couleurs pour l'écran ST7735
Teste différentes rotations et configurations pour identifier le problème de couleurs
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

class DiagnosticCouleurs:
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

    def initialize(self, rotation=0):
        if not ST7735_AVAILABLE:
            print("❌ ST7735 non disponible")
            return False
        try:
            print(f"🔧 Initialisation de l'écran ST7735 (rotation: {rotation}°)...")
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=rotation
            )
            self.display.begin()
            self.is_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False

    def test_couleurs_pures(self):
        """Test des couleurs pures RGB"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        couleurs = [
            ("Rouge pur", (255, 0, 0)),
            ("Vert pur", (0, 255, 0)),
            ("Bleu pur", (0, 0, 255)),
            ("Blanc pur", (255, 255, 255)),
            ("Noir pur", (0, 0, 0))
        ]

        try:
            for nom, couleur in couleurs:
                print(f"   → {nom} {couleur}")
                # Image plein écran
                image = Image.new("RGB", (self.display.width, self.display.height), couleur)
                draw = ImageDraw.Draw(image)

                # Texte centré
                font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), nom, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (self.display.width - text_width) // 2
                y = (self.display.height - text_height) // 2

                # Contraste texte selon fond
                brightness = sum(couleur) / 3
                text_color = (0,0,0) if brightness > 128 else (255,255,255)

                draw.text((x, y), nom, fill=text_color, font=font)

                self.display.display(image)
                time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False

    def test_couleurs_inversees(self):
        """Test avec couleurs inversées pour diagnostiquer"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        # Test avec différentes inversions possibles
        tests = [
            ("Rouge normal", (255, 0, 0)),
            ("Rouge inversé BGR", (0, 0, 255)),  # BGR au lieu de RGB
            ("Rouge inversé GRB", (0, 255, 0)),  # GRB au lieu de RGB
            ("Vert normal", (0, 255, 0)),
            ("Vert inversé BGR", (255, 0, 0)),   # BGR au lieu de RGB
            ("Vert inversé GRB", (0, 0, 255)),   # GRB au lieu de RGB
            ("Bleu normal", (0, 0, 255)),
            ("Bleu inversé BGR", (0, 255, 0)),   # BGR au lieu de RGB
            ("Bleu inversé GRB", (255, 0, 0)),   # GRB au lieu de RGB
        ]

        try:
            for nom, couleur in tests:
                print(f"   → {nom} {couleur}")
                image = Image.new("RGB", (self.display.width, self.display.height), couleur)
                draw = ImageDraw.Draw(image)

                # Texte
                font = ImageFont.load_default()
                draw.text((10, 10), nom, fill=(255, 255, 255), font=font)
                draw.text((10, 30), str(couleur), fill=(255, 255, 255), font=font)

                self.display.display(image)
                time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs inversées: {e}")
            return False

    def test_rotations(self):
        """Test avec différentes rotations"""
        rotations = [0, 90, 180, 270]
        
        for rotation in rotations:
            print(f"\n🔄 Test avec rotation {rotation}°")
            if self.initialize(rotation):
                self.test_couleurs_pures()
                time.sleep(1)
            else:
                print(f"❌ Impossible d'initialiser avec rotation {rotation}°")

    def test_format_couleur(self):
        """Test avec différents formats de couleur"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        print("🎨 Test formats de couleur...")
        
        # Test avec format RGB vs BGR
        formats = [
            ("RGB", (255, 0, 0)),      # Rouge en RGB
            ("BGR", (0, 0, 255)),      # Rouge en BGR
            ("GRB", (0, 255, 0)),      # Rouge en GRB
        ]

        try:
            for format_name, couleur in formats:
                print(f"   → Format {format_name}: {couleur}")
                image = Image.new("RGB", (self.display.width, self.display.height), couleur)
                draw = ImageDraw.Draw(image)

                # Texte
                font = ImageFont.load_default()
                draw.text((10, 10), f"Format {format_name}", fill=(255, 255, 255), font=font)
                draw.text((10, 30), str(couleur), fill=(255, 255, 255), font=font)

                self.display.display(image)
                time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Erreur test format couleur: {e}")
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

    def run_diagnostic(self):
        """Lance le diagnostic complet"""
        print("🔧 DIAGNOSTIC COULEURS ST7735")
        print("=" * 50)
        
        print("\n1️⃣ Test avec rotation actuelle (270°)")
        if self.initialize(270):
            self.test_couleurs_pures()
            print("\n2️⃣ Test couleurs inversées")
            self.test_couleurs_inversees()
            print("\n3️⃣ Test formats de couleur")
            self.test_format_couleur()
        
        print("\n4️⃣ Test avec différentes rotations")
        self.test_rotations()
        
        self.cleanup()
        print("\n✅ Diagnostic terminé")
        print("\n📋 Instructions:")
        print("   • Observez quelle couleur apparaît quand vous testez le rouge")
        print("   • Notez si les couleurs correspondent aux valeurs RGB attendues")
        print("   • Identifiez la rotation qui donne les bonnes couleurs")

if __name__ == "__main__":
    diagnostic = DiagnosticCouleurs()
    diagnostic.run_diagnostic()
