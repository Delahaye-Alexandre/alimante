#!/usr/bin/env python3
"""
Test des couleurs pour déterminer l'ordre correct (RGB ou BGR)
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

def test_couleurs_bgr(bgr_mode):
    """Test des couleurs avec un mode BGR spécifique"""
    if not ST7735_AVAILABLE:
        print("❌ Librairie ST7735 non disponible")
        return False
    
    try:
        config = get_gpio_config()
        reset_pin = config['DISPLAY']['RESET_PIN']
        a0_pin = config['DISPLAY']['A0_PIN']
        
        print(f"\n🔧 Test avec bgr={bgr_mode}")
        print(f"   RST={reset_pin}, A0={a0_pin}")
        
        # Initialisation de l'écran
        display = st7735.ST7735(
            port=0,
            cs=0,
            dc=a0_pin,
            rst=reset_pin,
            spi_speed_hz=2000000,
            rotation=270,
            bgr=bgr_mode
        )
        
        display.begin()
        print(f"   ✅ Résolution: {display.width}x{display.height}")
        
        # Test des couleurs de base
        couleurs = [
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255))
        ]
        
        for nom, couleur in couleurs:
            print(f"   🎨 Affichage {nom}...")
            image = Image.new('RGB', (display.width, display.height), color=couleur)
            
            # Ajouter un cadre blanc
            draw = ImageDraw.Draw(image)
            draw.rectangle([0, 0, display.width-1, display.height-1], outline=(255, 255, 255), width=2)
            
            # Ajouter le nom de la couleur
            try:
                font = ImageFont.load_default()
                text_bbox = draw.textbbox((0, 0), nom, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                x = (display.width - text_width) // 2
                y = (display.height - 20) // 2
                draw.text((x, y), nom, fill=(255, 255, 255), font=font)
            except:
                x = (display.width - len(nom) * 6) // 2
                y = (display.height - 20) // 2
                draw.text((x, y), nom, fill=(255, 255, 255))
            
            display.display(image)
            time.sleep(2)
        
        # Nettoyage
        del display
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    """Test des deux modes BGR"""
    if not ST7735_AVAILABLE:
        print("❌ Librairie ST7735 non disponible")
        return
    
    print("🔧 TEST COULEURS RGB vs BGR")
    print("=" * 50)
    print("Ce test va essayer les deux modes pour déterminer le bon ordre de couleurs")
    print("Regardez l'écran et dites-moi quel mode affiche les bonnes couleurs")
    
    # Gestionnaire de signal
    def signal_handler(signum, frame):
        print("\n🛑 Arrêt du test...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Test des deux modes
    modes = [
        (False, "RGB"),
        (True, "BGR")
    ]
    
    for bgr_mode, nom_mode in modes:
        print(f"\n{'='*20} MODE {nom_mode} {'='*20}")
        print(f"Configuration: bgr={bgr_mode}")
        print("Regardez l'écran - les couleurs sont-elles correctes ?")
        print("(Rouge=rouge, Vert=vert, Bleu=bleu)")
        
        try:
            success = test_couleurs_bgr(bgr_mode)
            if success:
                print(f"✅ Mode {nom_mode} testé avec succès")
            else:
                print(f"❌ Mode {nom_mode} a échoué")
        except KeyboardInterrupt:
            print("\n🛑 Test interrompu")
            break
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
        
        # Pause entre les modes
        if bgr_mode == False:  # Après le premier mode
            print("\n⏸️  Pause de 3 secondes avant le mode suivant...")
            time.sleep(3)
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ")
    print("=" * 50)
    print("1. Mode RGB (bgr=False): Rouge=rouge, Vert=vert, Bleu=bleu ?")
    print("2. Mode BGR (bgr=True): Rouge=rouge, Vert=vert, Bleu=bleu ?")
    print("\n💡 Choisissez le mode qui affiche les bonnes couleurs!")
    print("   Utilisez ce mode dans vos scripts avec le paramètre bgr=...")

if __name__ == "__main__":
    main()
