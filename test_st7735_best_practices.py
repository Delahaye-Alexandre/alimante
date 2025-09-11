#!/usr/bin/env python3
"""
Test ST7735 avec les meilleures pratiques
Basé sur la documentation technique et les exemples officiels
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

class TestST7735BestPractices:
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

    def initialize_best_practice(self):
        """Initialise l'écran selon les meilleures pratiques"""
        if not ST7735_AVAILABLE:
            print("❌ ST7735 non disponible")
            return False
        try:
            print("🔧 Initialisation ST7735 selon meilleures pratiques...")
            
            # Configuration recommandée selon la documentation
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=270,
                invert=False,  # Pas d'inversion
                bgr=False      # Format RGB standard
            )
            
            # Initialisation avec paramètres par défaut
            self.display.begin()
            
            # Configuration des paramètres d'affichage
            self.display.set_remap(0x00)  # Configuration standard
            self.display.set_display_start_line(0x00)  # Ligne de début
            self.display.set_display_offset(0x00)  # Pas d'offset
            
            self.is_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            print("   • Format: RGB standard")
            print("   • Inversion: Désactivée")
            print("   • Rotation: 270°")
            print("   • Configuration: Standard")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False

    def test_couleurs_standard(self):
        """Test des couleurs avec format standard"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test couleurs format standard...")
        
        # Couleurs standard RGB
        couleurs_standard = [
            ("Noir", (0, 0, 0)),
            ("Blanc", (255, 255, 255)),
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
            ("Jaune", (255, 255, 0)),
            ("Cyan", (0, 255, 255)),
            ("Magenta", (255, 0, 255)),
        ]
        
        try:
            for nom, couleur in couleurs_standard:
                print(f"   → {nom} {couleur}")
                
                # Création de l'image avec format standard
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
                
                # Affichage avec méthode standard
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False

    def test_format_rgb565_direct(self):
        """Test avec format RGB565 direct"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test format RGB565 direct...")
        
        # Couleurs RGB565
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
                
                # Création de l'image
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
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test RGB565: {e}")
            return False

    def test_initialisation_alternative(self):
        """Test avec initialisation alternative"""
        if not ST7735_AVAILABLE:
            return False
            
        print("🔧 Test initialisation alternative...")
        
        try:
            # Méthode alternative d'initialisation
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=270
            )
            
            # Initialisation manuelle
            self.display.begin()
            
            # Configuration manuelle des registres
            self.display.set_remap(0x00)
            self.display.set_display_start_line(0x00)
            self.display.set_display_offset(0x00)
            
            self.is_initialized = True
            print("✅ Initialisation alternative réussie")
            
            # Test avec rouge
            image = Image.new("RGB", (self.display.width, self.display.height), (255, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            draw.text((10, 10), "INIT ALTERNATIVE", fill=(255, 255, 255), font=font)
            draw.text((10, 30), "ROUGE (255,0,0)", fill=(255, 255, 255), font=font)
            
            self.display.display(image)
            time.sleep(3)
            
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation alternative: {e}")
            return False

    def test_diagnostic_complet(self):
        """Diagnostic complet selon la documentation"""
        if not self.is_initialized:
            return False
            
        print("🔍 Diagnostic complet...")
        
        try:
            # Test de diagnostic
            print("   → Test 1: Couleurs de base")
            self.test_couleurs_standard()
            
            print("   → Test 2: Format RGB565")
            self.test_format_rgb565_direct()
            
            print("   → Test 3: Initialisation alternative")
            self.test_initialisation_alternative()
            
            return True
        except Exception as e:
            print(f"❌ Erreur diagnostic: {e}")
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
        """Lance les tests selon les meilleures pratiques"""
        print("🔧 TEST ST7735 MEILLEURES PRATIQUES")
        if not self.initialize_best_practice():
            return
        
        print("\n" + "=" * 40)
        print("MENU DE TEST MEILLEURES PRATIQUES:")
        print("1. Couleurs format standard")
        print("2. Format RGB565 direct")
        print("3. Initialisation alternative")
        print("4. Diagnostic complet")
        print("0. Quitter")
        print("=" * 40)
        
        while True:
            choice = input("Votre choix (0-4): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.test_couleurs_standard()
            elif choice == "2":
                self.test_format_rgb565_direct()
            elif choice == "3":
                self.test_initialisation_alternative()
            elif choice == "4":
                self.test_diagnostic_complet()
            else:
                print("❌ Choix invalide")
        
        self.cleanup()
        print("👋 Tests terminés")

if __name__ == "__main__":
    test = TestST7735BestPractices()
    test.run_tests()
