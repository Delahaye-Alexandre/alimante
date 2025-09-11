#!/usr/bin/env python3
"""
Test complet de l'écran ST7735 pour Raspberry Pi
Affiche les couleurs et les formes en remplissant correctement l'écran
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
    print("⚠️  Librairie ST7735 non disponible. Installation requise:")
    print("   pip install st7735 Pillow")

class EcranST7735:
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
                rotation=270  # Ajuster selon ton montage
            )
            self.display.begin()
            self.is_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False

    def test_couleurs(self):
        if not self.is_initialized:
            print("❌ Écran non initialisé")
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
            for nom, couleur in couleurs:
                # Image plein écran
                image = Image.new("RGB", (self.display.width, self.display.height), couleur)
                draw = ImageDraw.Draw(image)

                # Texte centré
                font = ImageFont.load_default()
                text_width, text_height = draw.textsize(nom, font=font)
                x = (self.display.width - text_width) // 2
                y = (self.display.height - text_height) // 2

                # Contraste texte selon fond
                brightness = sum(couleur) / 3
                text_color = (0,0,0) if brightness > 128 else (255,255,255)

                draw.text((x, y), nom, fill=text_color, font=font)

                self.display.display(image)
                time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False

    def test_formes(self):
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
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

            self.display.display(image)
            time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Erreur test formes: {e}")
            return False

    def cleanup(self):
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

    def run(self):
        print("🔧 DÉBUT TESTS ST7735")
        if not self.initialize():
            return
        self.test_couleurs()
        self.test_formes()
        self.cleanup()
        print("👋 Tests terminés")

if __name__ == "__main__":
    ecran = EcranST7735()
    ecran.run()
