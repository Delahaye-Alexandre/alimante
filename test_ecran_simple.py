#!/usr/bin/env python3
"""
Test simple de l'écran ST7735 sans encodeur
Pour isoler les problèmes de conflit GPIO
"""

import RPi.GPIO as GPIO
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
    print("⚠️  Librairie ST7735 non disponible. Installation requise:")
    print("   pip install st7735 Pillow")

def cleanup_gpio():
    """Nettoie les pins GPIO"""
    try:
        print("🧹 Nettoyage des pins GPIO...")
        GPIO.cleanup()
        time.sleep(0.5)
    except:
        pass

def test_ecran_simple():
    """Test simple de l'écran"""
    if not ST7735_AVAILABLE:
        print("❌ Librairie ST7735 non disponible")
        return False
    
    # Nettoyage préventif
    cleanup_gpio()
    
    # Configuration GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Configuration depuis config
    config = get_gpio_config()
    reset_pin = config['DISPLAY']['RESET_PIN']
    a0_pin = config['DISPLAY']['A0_PIN']
    
    try:
        print("🔧 Initialisation de l'écran ST7735...")
        print(f"   RST={reset_pin}, A0={a0_pin}")
        
        # Initialisation de l'écran
        display = st7735.ST7735(
            port=0,
            cs=0,
            dc=a0_pin,
            rst=reset_pin,
            spi_speed_hz=4000000,
            rotation=270
        )
        
        print("🔧 Démarrage de l'écran...")
        display.begin()
        
        print("✅ Écran initialisé avec succès!")
        print(f"   📐 Résolution: {display.width}x{display.height}")
        
        # Test simple - affichage d'une couleur
        print("🎨 Test d'affichage...")
        image = Image.new('RGB', (display.width, display.height), color=(0, 0, 255))  # Rouge BGR
        display.display(image)
        
        print("✅ Test réussi! L'écran fonctionne.")
        print("   Appuyez sur Ctrl+C pour quitter...")
        
        # Attendre l'interruption
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du test...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Nettoyage
        try:
            if 'display' in locals():
                image = Image.new('RGB', (display.width, display.height), color=(0, 0, 0))
                display.display(image)
        except:
            pass
        
        cleanup_gpio()
        print("🧹 Nettoyage terminé")

def main():
    """Fonction principale"""
    print("🔧 TEST SIMPLE ÉCRAN ST7735")
    print("=" * 40)
    
    # Gestionnaire de signal
    def signal_handler(signum, frame):
        print("\n🛑 Arrêt du programme...")
        cleanup_gpio()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    success = test_ecran_simple()
    
    if success:
        print("🎉 Test terminé avec succès!")
    else:
        print("❌ Test échoué")

if __name__ == "__main__":
    main()
