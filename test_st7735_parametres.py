#!/usr/bin/env python3
"""
Test des paramètres d'initialisation ST7735
Essaie différentes configurations pour corriger les couleurs
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

class TestST7735Parametres:
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

    def initialize_with_params(self, rotation=270, invert=False, bgr=False):
        """Initialise l'écran avec des paramètres spécifiques"""
        if not ST7735_AVAILABLE:
            print("❌ ST7735 non disponible")
            return False
        try:
            print(f"🔧 Initialisation ST7735 (rot={rotation}, inv={invert}, bgr={bgr})...")
            
            # Création de l'écran avec paramètres
            self.display = st7735.ST7735(
                port=0,
                cs=0,
                dc=self.a0_pin,
                rst=self.reset_pin,
                rotation=rotation,
                invert=invert,
                bgr=bgr
            )
            self.display.begin()
            self.is_initialized = True
            print(f"✅ Écran initialisé: {self.display.width}x{self.display.height}")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False

    def test_couleurs_basiques(self):
        """Test des couleurs de base"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test des couleurs de base...")
        
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
                draw.text((5, 5), str(couleur), fill=text_color, font=font)
                
                self.display.display(image)
                time.sleep(2)
                
            return True
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False

    def test_configuration(self, nom, rotation, invert, bgr):
        """Test une configuration spécifique"""
        print(f"\n🔧 Test configuration: {nom}")
        print(f"   Rotation: {rotation}°, Invert: {invert}, BGR: {bgr}")
        
        if self.initialize_with_params(rotation, invert, bgr):
            self.test_couleurs_basiques()
            time.sleep(1)
            return True
        return False

    def test_toutes_configurations(self):
        """Test toutes les configurations possibles"""
        print("🔧 Test de toutes les configurations...")
        
        configurations = [
            ("Normal", 270, False, False),
            ("Invert", 270, True, False),
            ("BGR", 270, False, True),
            ("Invert+BGR", 270, True, True),
            ("Rot0", 0, False, False),
            ("Rot0+Invert", 0, True, False),
            ("Rot0+BGR", 0, False, True),
            ("Rot0+Invert+BGR", 0, True, True),
            ("Rot90", 90, False, False),
            ("Rot90+Invert", 90, True, False),
            ("Rot90+BGR", 90, False, True),
            ("Rot90+Invert+BGR", 90, True, True),
            ("Rot180", 180, False, False),
            ("Rot180+Invert", 180, True, False),
            ("Rot180+BGR", 180, False, True),
            ("Rot180+Invert+BGR", 180, True, True),
        ]
        
        for nom, rotation, invert, bgr in configurations:
            self.test_configuration(nom, rotation, invert, bgr)
            time.sleep(1)

    def test_format_couleur_direct(self):
        """Test avec format de couleur direct"""
        if not self.is_initialized:
            return False
            
        print("🎨 Test format couleur direct...")
        
        # Test avec différentes méthodes de création d'image
        try:
            # Méthode 1: Image.new avec RGB
            print("   → Méthode 1: Image.new RGB")
            image1 = Image.new("RGB", (self.display.width, self.display.height), (255, 0, 0))
            self.display.display(image1)
            time.sleep(2)
            
            # Méthode 2: Image.new avec RGBA
            print("   → Méthode 2: Image.new RGBA")
            image2 = Image.new("RGBA", (self.display.width, self.display.height), (255, 0, 0, 255))
            self.display.display(image2)
            time.sleep(2)
            
            # Méthode 3: Image.new avec L (niveau de gris)
            print("   → Méthode 3: Image.new L")
            image3 = Image.new("L", (self.display.width, self.display.height), 128)
            self.display.display(image3)
            time.sleep(2)
            
            return True
        except Exception as e:
            print(f"❌ Erreur test format direct: {e}")
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
        print("🔧 TEST PARAMÈTRES ST7735")
        
        print("\n" + "=" * 40)
        print("MENU DE TEST PARAMÈTRES:")
        print("1. Configuration normale")
        print("2. Configuration avec invert")
        print("3. Configuration avec BGR")
        print("4. Configuration invert+BGR")
        print("5. Test toutes configurations")
        print("6. Test format couleur direct")
        print("0. Quitter")
        print("=" * 40)
        
        while True:
            choice = input("Votre choix (0-6): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                if self.initialize_with_params(270, False, False):
                    self.test_couleurs_basiques()
            elif choice == "2":
                if self.initialize_with_params(270, True, False):
                    self.test_couleurs_basiques()
            elif choice == "3":
                if self.initialize_with_params(270, False, True):
                    self.test_couleurs_basiques()
            elif choice == "4":
                if self.initialize_with_params(270, True, True):
                    self.test_couleurs_basiques()
            elif choice == "5":
                self.test_toutes_configurations()
            elif choice == "6":
                if self.initialize_with_params(270, False, False):
                    self.test_format_couleur_direct()
            else:
                print("❌ Choix invalide")
        
        self.cleanup()
        print("👋 Tests terminés")

if __name__ == "__main__":
    test = TestST7735Parametres()
    test.run_tests()
