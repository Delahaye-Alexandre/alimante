#!/usr/bin/env python3
"""
Test rapide pour identifier les inversions de pins ST7735
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

class TestPinsInverses:
    def __init__(self):
        self.config = get_gpio_config()
        self.reset_pin = self.config['DISPLAY']['RESET_PIN']
        self.a0_pin = self.config['DISPLAY']['A0_PIN']
        
        # Gestionnaire d'arrêt
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def test_configuration(self, dc_pin, rst_pin, rotation=0, nom="Configuration normale"):
        """Test une configuration spécifique"""
        if not ST7735_AVAILABLE:
            return False
            
        try:
            print(f"🔧 Test {nom} (DC={dc_pin}, RST={rst_pin}, ROT={rotation}°)")
            
            display = st7735.ST7735(
                port=0,
                cs=0,
                dc=dc_pin,
                rst=rst_pin,
                rotation=rotation
            )
            display.begin()
            
            # Test avec rouge pur
            image = Image.new("RGB", (display.width, display.height), (255, 0, 0))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            
            draw.text((10, 10), nom, fill=(255, 255, 255), font=font)
            draw.text((10, 30), "ROUGE (255,0,0)", fill=(255, 255, 255), font=font)
            draw.text((10, 50), f"DC={dc_pin} RST={rst_pin}", fill=(255, 255, 255), font=font)
            
            display.display(image)
            time.sleep(3)
            
            # Nettoyage
            image = Image.new("RGB", (display.width, display.height), (0, 0, 0))
            display.display(image)
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return False

    def run_tests(self):
        """Lance tous les tests de configurations"""
        print("🔧 TEST DES CONFIGURATIONS ST7735")
        print("=" * 50)
        print()
        print("📋 Tests à effectuer:")
        print("1. Configuration normale")
        print("2. A0/DC et RST inversés")
        print("3. Différentes rotations")
        print()
        print("👀 OBSERVEZ:")
        print("• Quand vous voyez du ROUGE, c'est correct")
        print("• Si vous voyez du BLEU, les pins sont inversés")
        print("• Si l'écran est noir, vérifiez l'alimentation")
        print()
        
        input("Appuyez sur Entrée pour commencer...")
        
        # Test 1: Configuration normale
        print("\n1️⃣ CONFIGURATION NORMALE")
        self.test_configuration(
            dc_pin=self.a0_pin,
            rst_pin=self.reset_pin,
            rotation=0,
            nom="NORMALE"
        )
        
        # Test 2: A0/DC et RST inversés
        print("\n2️⃣ A0/DC ET RST INVERSÉS")
        self.test_configuration(
            dc_pin=self.reset_pin,
            rst_pin=self.a0_pin,
            rotation=0,
            nom="INVERSE"
        )
        
        # Test 3: Configuration normale avec rotation 270°
        print("\n3️⃣ NORMALE + ROTATION 270°")
        self.test_configuration(
            dc_pin=self.a0_pin,
            rst_pin=self.reset_pin,
            rotation=270,
            nom="NORMALE+270°"
        )
        
        # Test 4: Inversée avec rotation 270°
        print("\n4️⃣ INVERSÉE + ROTATION 270°")
        self.test_configuration(
            dc_pin=self.reset_pin,
            rst_pin=self.a0_pin,
            rotation=270,
            nom="INVERSE+270°"
        )
        
        print("\n✅ Tests terminés!")
        print("\n📋 RÉSULTATS:")
        print("• Notez quelle configuration affiche du ROUGE")
        print("• C'est la configuration correcte à utiliser")
        print("• Si aucune ne fonctionne, vérifiez les branchements")

    def _signal_handler(self, signum, frame):
        print("\n🛑 Arrêt du programme")
        sys.exit(0)

if __name__ == "__main__":
    test = TestPinsInverses()
    test.run_tests()
