#!/usr/bin/env python3
"""
Diagnostic complet des couleurs ST7735
Teste toutes les conversions possibles pour identifier la bonne
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

class DiagnosticCouleursComplet:
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

    def test_conversions_couleurs(self):
        """Test toutes les conversions de couleurs possibles"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        # Couleurs de test
        couleurs_test = [
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255))
        ]

        # Conversions à tester
        conversions = [
            ("RGB normal", lambda c: c),
            ("BGR", lambda c: (c[2], c[1], c[0])),
            ("GRB", lambda c: (c[1], c[0], c[2])),
            ("RBG", lambda c: (c[0], c[2], c[1])),
            ("GBR", lambda c: (c[1], c[2], c[0])),
            ("BRG", lambda c: (c[2], c[0], c[1])),
        ]

        try:
            print("🎨 Test de toutes les conversions de couleurs...")
            
            for nom_couleur, couleur_rgb in couleurs_test:
                print(f"\n🔍 Test {nom_couleur} {couleur_rgb}:")
                
                for nom_conv, conversion in conversions:
                    print(f"   → {nom_conv}: {conversion(couleur_rgb)}")
                    
                    # Image plein écran
                    couleur_convertie = conversion(couleur_rgb)
                    image = Image.new("RGB", (self.display.width, self.display.height), couleur_convertie)
                    draw = ImageDraw.Draw(image)
                    font = ImageFont.load_default()
                    
                    # Texte
                    draw.text((10, 10), f"{nom_couleur}", fill=(255, 255, 255), font=font)
                    draw.text((10, 30), f"{nom_conv}", fill=(255, 255, 255), font=font)
                    draw.text((10, 50), str(couleur_convertie), fill=(255, 255, 255), font=font)
                    
                    self.display.display(image)
                    time.sleep(2)
                    
                    # Demander à l'utilisateur
                    print(f"      Voyez-vous du {nom_couleur.lower()} ? (o/n)")
                    # Pour l'instant, on continue automatiquement
                    time.sleep(1)
                    
            return True
        except Exception as e:
            print(f"❌ Erreur test conversions: {e}")
            return False

    def test_rotations_couleurs(self):
        """Test avec différentes rotations"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False

        rotations = [0, 90, 180, 270]
        couleur_test = (255, 0, 0)  # Rouge
        
        try:
            print("🔄 Test avec différentes rotations...")
            
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

    def run_diagnostic(self):
        """Lance le diagnostic complet"""
        print("🔧 DIAGNOSTIC COMPLET DES COULEURS")
        print("=" * 50)
        
        if not self.initialize():
            return
        
        print("\n1️⃣ Test des conversions de couleurs")
        self.test_conversions_couleurs()
        
        print("\n2️⃣ Test des rotations")
        self.test_rotations_couleurs()
        
        self.cleanup()
        
        print("\n📋 RÉSULTATS:")
        print("• Notez quelle conversion donne les bonnes couleurs")
        print("• Notez quelle rotation fonctionne le mieux")
        print("• Utilisez ces paramètres dans vos autres scripts")

if __name__ == "__main__":
    diagnostic = DiagnosticCouleursComplet()
    diagnostic.run_diagnostic()
