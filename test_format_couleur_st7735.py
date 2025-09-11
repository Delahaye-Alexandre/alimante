#!/usr/bin/env python3
"""
Test des formats de couleur pour ST7735
Identifie le bon format de couleur du contrôleur
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

class TestFormatCouleur:
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

    def test_format_rgb(self):
        """Test avec format RGB normal"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test format RGB normal...")
        
        couleurs = [
            ("Noir", (0, 0, 0)),
            ("Blanc", (255, 255, 255)),
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
        ]
        
        try:
            for nom, couleur in couleurs:
                print(f"   → {nom} {couleur}")
                
                image = Image.new("RGB", (self.display.width, self.display.height), couleur)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                draw.text((10, 10), f"RGB: {nom}", fill=(255, 255, 255), font=font)
                draw.text((10, 30), str(couleur), fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test RGB: {e}")
            return False

    def test_format_bgr(self):
        """Test avec format BGR"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test format BGR...")
        
        couleurs_rgb = [
            ("Noir", (0, 0, 0)),
            ("Blanc", (255, 255, 255)),
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
        ]
        
        try:
            for nom, couleur_rgb in couleurs_rgb:
                # Conversion BGR
                couleur_bgr = (couleur_rgb[2], couleur_rgb[1], couleur_rgb[0])
                print(f"   → {nom} RGB: {couleur_rgb} → BGR: {couleur_bgr}")
                
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_bgr)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                draw.text((10, 10), f"BGR: {nom}", fill=(255, 255, 255), font=font)
                draw.text((10, 30), f"RGB: {couleur_rgb}", fill=(255, 255, 255), font=font)
                draw.text((10, 50), f"BGR: {couleur_bgr}", fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test BGR: {e}")
            return False

    def test_format_grb(self):
        """Test avec format GRB"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test format GRB...")
        
        couleurs_rgb = [
            ("Noir", (0, 0, 0)),
            ("Blanc", (255, 255, 255)),
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
        ]
        
        try:
            for nom, couleur_rgb in couleurs_rgb:
                # Conversion GRB
                couleur_grb = (couleur_rgb[1], couleur_rgb[0], couleur_rgb[2])
                print(f"   → {nom} RGB: {couleur_rgb} → GRB: {couleur_grb}")
                
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_grb)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                draw.text((10, 10), f"GRB: {nom}", fill=(255, 255, 255), font=font)
                draw.text((10, 30), f"RGB: {couleur_rgb}", fill=(255, 255, 255), font=font)
                draw.text((10, 50), f"GRB: {couleur_grb}", fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test GRB: {e}")
            return False

    def test_format_rbg(self):
        """Test avec format RBG"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test format RBG...")
        
        couleurs_rgb = [
            ("Noir", (0, 0, 0)),
            ("Blanc", (255, 255, 255)),
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
        ]
        
        try:
            for nom, couleur_rgb in couleurs_rgb:
                # Conversion RBG
                couleur_rbg = (couleur_rgb[0], couleur_rgb[2], couleur_rgb[1])
                print(f"   → {nom} RGB: {couleur_rgb} → RBG: {couleur_rbg}")
                
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_rbg)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                draw.text((10, 10), f"RBG: {nom}", fill=(255, 255, 255), font=font)
                draw.text((10, 30), f"RGB: {couleur_rgb}", fill=(255, 255, 255), font=font)
                draw.text((10, 50), f"RBG: {couleur_rbg}", fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test RBG: {e}")
            return False

    def test_format_gbr(self):
        """Test avec format GBR"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test format GBR...")
        
        couleurs_rgb = [
            ("Noir", (0, 0, 0)),
            ("Blanc", (255, 255, 255)),
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
        ]
        
        try:
            for nom, couleur_rgb in couleurs_rgb:
                # Conversion GBR
                couleur_gbr = (couleur_rgb[1], couleur_rgb[2], couleur_rgb[0])
                print(f"   → {nom} RGB: {couleur_rgb} → GBR: {couleur_gbr}")
                
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_gbr)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                draw.text((10, 10), f"GBR: {nom}", fill=(255, 255, 255), font=font)
                draw.text((10, 30), f"RGB: {couleur_rgb}", fill=(255, 255, 255), font=font)
                draw.text((10, 50), f"GBR: {couleur_gbr}", fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test GBR: {e}")
            return False

    def test_format_brg(self):
        """Test avec format BRG"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test format BRG...")
        
        couleurs_rgb = [
            ("Noir", (0, 0, 0)),
            ("Blanc", (255, 255, 255)),
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
        ]
        
        try:
            for nom, couleur_rgb in couleurs_rgb:
                # Conversion BRG
                couleur_brg = (couleur_rgb[2], couleur_rgb[0], couleur_rgb[1])
                print(f"   → {nom} RGB: {couleur_rgb} → BRG: {couleur_brg}")
                
                image = Image.new("RGB", (self.display.width, self.display.height), couleur_brg)
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default()
                
                draw.text((10, 10), f"BRG: {nom}", fill=(255, 255, 255), font=font)
                draw.text((10, 30), f"RGB: {couleur_rgb}", fill=(255, 255, 255), font=font)
                draw.text((10, 50), f"BRG: {couleur_brg}", fill=(255, 255, 255), font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test BRG: {e}")
            return False

    def test_rotations(self):
        """Test avec différentes rotations"""
        if not self.is_initialized:
            return False
            
        print("🔄 Test avec différentes rotations...")
        
        rotations = [0, 90, 180, 270]
        couleur_test = (255, 0, 0)  # Rouge
        
        try:
            for rotation in rotations:
                print(f"   → Test rotation {rotation}°")
                try:
                    # Recréer l'écran avec nouvelle rotation
                    self.display = st7735.ST7735(
                        port=0,
                        cs=0,
                        dc=self.a0_pin,
                        rst=self.reset_pin,
                        rotation=rotation
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
                    
                except Exception as e:
                    print(f"      ❌ Erreur rotation {rotation}°: {e}")
                    
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
        """Lance tous les tests"""
        print("🔧 TEST FORMAT COULEUR ST7735")
        if not self.initialize():
            return
        
        print("\n" + "=" * 40)
        print("MENU DE TEST FORMAT COULEUR:")
        print("1. Format RGB normal")
        print("2. Format BGR")
        print("3. Format GRB")
        print("4. Format RBG")
        print("5. Format GBR")
        print("6. Format BRG")
        print("7. Test rotations")
        print("8. Tous les tests")
        print("0. Quitter")
        print("=" * 40)
        
        while True:
            choice = input("Votre choix (0-8): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.test_format_rgb()
            elif choice == "2":
                self.test_format_bgr()
            elif choice == "3":
                self.test_format_grb()
            elif choice == "4":
                self.test_format_rbg()
            elif choice == "5":
                self.test_format_gbr()
            elif choice == "6":
                self.test_format_brg()
            elif choice == "7":
                self.test_rotations()
            elif choice == "8":
                print("🚀 Lancement de tous les tests...")
                self.test_format_rgb()
                self.test_format_bgr()
                self.test_format_grb()
                self.test_format_rbg()
                self.test_format_gbr()
                self.test_format_brg()
                self.test_rotations()
            else:
                print("❌ Choix invalide")
        
        self.cleanup()
        print("👋 Tests terminés")

if __name__ == "__main__":
    test = TestFormatCouleur()
    test.run_tests()
