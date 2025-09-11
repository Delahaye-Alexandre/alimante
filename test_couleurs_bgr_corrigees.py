#!/usr/bin/env python3
"""
Test des couleurs BGR corrigées pour ST7735
Corrige le problème RVB → BGR
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

class TestCouleursBGR:
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

    def rgb_to_bgr(self, rgb_color):
        """Convertit RGB en BGR pour corriger l'affichage"""
        if len(rgb_color) == 3:
            return (rgb_color[2], rgb_color[1], rgb_color[0])  # BGR
        return rgb_color

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

    def test_couleurs_comparaison(self):
        """Test de comparaison RGB vs BGR"""
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
            print("🎨 Test de comparaison RGB vs BGR...")
            
            for nom, couleur_rgb in couleurs:
                print(f"   → {nom} RGB: {couleur_rgb}")
                
                # Test RGB (probablement incorrect)
                print("      Test RGB (probablement incorrect)...")
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_rgb)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                # Texte
                draw.text((10, 10), f"{nom} RGB", fill=(255, 255, 255), font=font)
                draw.text((10, 30), str(couleur_rgb), fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
                # Test BGR (corrigé)
                print("      Test BGR (corrigé)...")
                couleur_bgr = self.rgb_to_bgr(couleur_rgb)
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_bgr)
                draw = ImageDraw.Draw(image)
                
                # Texte
                draw.text((10, 10), f"{nom} BGR", fill=(255, 255, 255), font=font)
                draw.text((10, 30), str(couleur_bgr), fill=(255, 255, 255), font=font)
                draw.text((10, 50), "CORRIGE", fill=(0, 255, 0), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False

    def test_couleurs_corrigees(self):
        """Test des couleurs avec correction BGR"""
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
            print("🎨 Test des couleurs corrigées BGR...")
            
            for nom, couleur_rgb in couleurs:
                print(f"   → {nom} {couleur_rgb}")
                
                # Conversion BGR
                couleur_bgr = self.rgb_to_bgr(couleur_rgb)
                
                # Image plein écran
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_bgr)
                draw = ImageDraw.Draw(image)

                # Texte centré
                font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), nom, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (self.display.width - text_width) // 2
                y = (self.display.height - text_height) // 2

                # Contraste texte
                brightness = sum(couleur_rgb) / 3
                text_color = (0,0,0) if brightness > 128 else (255,255,255)
                text_color_bgr = self.rgb_to_bgr(text_color)

                draw.text((x, y), nom, fill=text_color_bgr, font=font)
                draw.text((5, 5), f"RGB: {couleur_rgb}", fill=text_color_bgr, font=font)
                draw.text((5, self.display.height - 15), "BGR CORRIGE", fill=text_color_bgr, font=font)

                self.display.display(image)
                time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False

    def test_formes_corrigees(self):
        """Test des formes avec couleurs corrigées"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        try:
            print("🔷 Test des formes avec couleurs corrigées...")
            image = Image.new("RGB", (self.display.width, self.display.height), (0,0,0))
            draw = ImageDraw.Draw(image)

            # Cadre blanc
            draw.rectangle([0,0,self.display.width-1,self.display.height-1], 
                         outline=self.rgb_to_bgr((255,255,255)), width=2)

            # Formes avec couleurs corrigées
            draw.rectangle([5,5,45,25], fill=self.rgb_to_bgr((255,0,0)), 
                         outline=self.rgb_to_bgr((255,255,255)))  # Rouge
            draw.ellipse([self.display.width-45,5,self.display.width-5,45], 
                        fill=self.rgb_to_bgr((0,255,0)), 
                        outline=self.rgb_to_bgr((255,255,255)))  # Vert
            draw.polygon([(30,self.display.height-30),(50,self.display.height-10),(10,self.display.height-10)], 
                        fill=self.rgb_to_bgr((255,255,0)))  # Jaune
            draw.line([(0,0),(self.display.width-1,self.display.height-1)], 
                    fill=self.rgb_to_bgr((0,255,255)), width=2)  # Cyan

            # Texte
            font = ImageFont.load_default()
            draw.text((10, 50), "ALIMANTE", fill=self.rgb_to_bgr((255, 255, 255)), font=font)
            draw.text((10, 70), "BGR CORRIGE", fill=self.rgb_to_bgr((0, 255, 255)), font=font)

            self.display.display(image)
            time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Erreur test formes: {e}")
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
        """Lance tous les tests"""
        print("🔧 DÉBUT TESTS COULEURS BGR")
        if not self.initialize():
            return
        
        print("\n" + "=" * 40)
        print("MENU DE TEST COULEURS BGR:")
        print("1. Comparaison RGB vs BGR")
        print("2. Couleurs corrigées BGR")
        print("3. Formes corrigées")
        print("4. Tous les tests")
        print("0. Quitter")
        print("=" * 40)
        
        while True:
            choice = input("Votre choix (0-4): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.test_couleurs_comparaison()
            elif choice == "2":
                self.test_couleurs_corrigees()
            elif choice == "3":
                self.test_formes_corrigees()
            elif choice == "4":
                print("🚀 Lancement de tous les tests...")
                self.test_couleurs_comparaison()
                self.test_couleurs_corrigees()
                self.test_formes_corrigees()
            else:
                print("❌ Choix invalide")
        
        self.cleanup()
        print("👋 Tests terminés")

if __name__ == "__main__":
    test = TestCouleursBGR()
    test.run_tests()
