#!/usr/bin/env python3
"""
Test simple de l'écran ST7735
Basé sur alimante_menu_improved.py
"""

import time
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    print("✅ Modules st7735 et PIL importés avec succès")
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    sys.exit(1)

def test_lcd():
    """Test simple de l'écran ST7735"""
    try:
        print("🔧 Initialisation de l'écran ST7735...")
        
        # Charger la configuration GPIO depuis le fichier JSON
        import json
        with open('config/gpio_config.json', 'r', encoding='utf-8') as f:
            gpio_config = json.load(f)
        
        ui_pins = gpio_config.get('gpio_pins', {}).get('ui', {})
        reset_pin = ui_pins.get('st7735_rst', {}).get('pin', 24)
        a0_pin = ui_pins.get('st7735_dc', {}).get('pin', 25)
        cs_pin = ui_pins.get('st7735_cs', {}).get('pin', 8)
        
        print(f"📌 Pins configurées: RST={reset_pin}, DC={a0_pin}, CS={cs_pin}")
        
        # Initialiser l'écran
        display = st7735.ST7735(
            port=0,
            cs=cs_pin,
            dc=a0_pin,
            rst=reset_pin,
            rotation=90,   # Rotation comme dans alimante_menu_improved.py
            invert=False,   # Inversion de l'affichage
            bgr=False      # Format RGB standard
        )
        display.begin()
        
        print(f"✅ Écran initialisé: {display.width}x{display.height}")
        
        # Créer une image de test
        image = Image.new("RGB", (display.width, display.height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        
        # Titre
        title = "TEST ALIMANTE"
        bbox = draw.textbbox((0, 0), title, font=font)
        title_width = bbox[2] - bbox[0]
        x_title = (display.width - title_width) // 2
        draw.text((x_title, 10), title, fill=(255, 255, 0), font=font)
        
        # Ligne de séparation
        draw.line([(5, 30), (display.width - 5, 30)], fill=(128, 128, 128))
        
        # Message de test
        draw.text((10, 50), "Ecran fonctionnel!", fill=(0, 255, 0), font=font)
        draw.text((10, 70), f"Resolution: {display.width}x{display.height}", fill=(255, 255, 255), font=font)
        draw.text((10, 90), "Test reussi!", fill=(0, 255, 0), font=font)
        
        # Affichage
        print("📺 Affichage de l'image de test...")
        display.display(image)
        print("✅ Image affichée avec succès!")
        
        # Attendre un peu
        time.sleep(3)
        
        # Test avec une image colorée
        print("🎨 Test avec image colorée...")
        for i in range(5):
            # Créer une image avec une couleur différente
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
            image = Image.new("RGB", (display.width, display.height), colors[i])
            display.display(image)
            print(f"  Couleur {i+1}/5: {colors[i]}")
            time.sleep(1)
        
        # Image finale
        image = Image.new("RGB", (display.width, display.height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.text((10, 50), "Test termine!", fill=(255, 255, 255), font=font)
        display.display(image)
        
        print("✅ Test de l'écran ST7735 terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur test écran: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🦎 Test de l'écran ST7735 Alimante")
    print("=" * 40)
    
    if test_lcd():
        print("🎉 Test réussi!")
    else:
        print("💥 Test échoué!")
        sys.exit(1)
