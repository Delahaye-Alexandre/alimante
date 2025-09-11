#!/usr/bin/env python3
"""
Test de résolution pour trouver la configuration optimale de l'écran ST7735
"""

import time
import sys
import signal
from config_alimante import get_gpio_config

# Import pour l'écran ST7735
try:
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    ST7735_AVAILABLE = True
    print("✅ Librairies ST7735 et PIL importées avec succès")
except Exception as e:
    ST7735_AVAILABLE = False
    print(f"⚠️  Erreur lors de l'import: {e}")

def test_configuration(config_name, **kwargs):
    """Test une configuration spécifique"""
    print(f"\n🔧 Test configuration: {config_name}")
    print(f"   Paramètres: {kwargs}")
    
    try:
        config = get_gpio_config()
        reset_pin = config['DISPLAY']['RESET_PIN']
        a0_pin = config['DISPLAY']['A0_PIN']
        
        # Configuration par défaut
        default_params = {
            'port': 0,
            'cs': 0,
            'dc': a0_pin,
            'rst': reset_pin,
            'spi_speed_hz': 2000000,
            'rotation': 270,
            'bgr': False  # Ordre RGB
        }
        
        # Fusionner avec les paramètres de test
        params = {**default_params, **kwargs}
        
        # Créer l'écran
        display = st7735.ST7735(**params)
        display.begin()
        
        print(f"   ✅ Résolution détectée: {display.width}x{display.height}")
        
        # Test d'affichage - remplir tout l'écran
        image = Image.new('RGB', (display.width, display.height), color=(255, 0, 0))  # Rouge RGB
        draw = ImageDraw.Draw(image)
        
        # Cadre blanc pour voir les bords
        draw.rectangle([0, 0, display.width-1, display.height-1], outline=(255, 255, 255), width=2)
        
        # Texte au centre
        try:
            font = ImageFont.load_default()
            text = f"{display.width}x{display.height}"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (display.width - text_width) // 2
            y = (display.height - text_height) // 2
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
        except:
            x = (display.width - len(text) * 6) // 2
            y = (display.height - 20) // 2
            draw.text((x, y), text, fill=(255, 255, 255))
        
        display.display(image)
        
        print(f"   📐 Zone utilisable: {display.width}x{display.height}")
        print(f"   🎨 Image affichée - regardez l'écran")
        
        # Attendre 3 secondes
        time.sleep(3)
        
        # Nettoyage
        del display
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    """Test différentes configurations"""
    if not ST7735_AVAILABLE:
        print("❌ Librairie ST7735 non disponible")
        return
    
    print("🔧 TEST DE RÉSOLUTION ÉCRAN ST7735")
    print("=" * 50)
    print("Ce test va essayer différentes configurations pour optimiser l'utilisation de l'écran")
    print("Regardez l'écran pendant chaque test pour voir quelle configuration utilise le mieux l'espace")
    
    # Gestionnaire de signal
    def signal_handler(signum, frame):
        print("\n🛑 Arrêt du test...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configurations à tester
    configurations = [
        ("Défaut", {}),
        ("Largeur 160", {"width": 160}),
        ("Hauteur 128", {"height": 128}),
        ("160x128", {"width": 160, "height": 128}),
        ("128x160", {"width": 128, "height": 160}),
        ("Avec offset", {"width": 160, "height": 128, "x_offset": 0, "y_offset": 0}),
        ("Rotation 0°", {"rotation": 0}),
        ("Rotation 90°", {"rotation": 90}),
        ("Rotation 180°", {"rotation": 180}),
    ]
    
    results = []
    
    for config_name, params in configurations:
        try:
            result = test_configuration(config_name, **params)
            results.append((config_name, result))
            
            if result:
                print(f"✅ {config_name}: RÉUSSI")
            else:
                print(f"❌ {config_name}: ÉCHEC")
            
            # Pause entre les tests
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n🛑 Test interrompu par l'utilisateur")
            break
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append((config_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    for config_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"   {config_name}: {status}")
    
    print("\n💡 Choisissez la configuration qui utilise le mieux votre écran!")
    print("   Vous pouvez ensuite modifier vos scripts avec ces paramètres.")

if __name__ == "__main__":
    main()
