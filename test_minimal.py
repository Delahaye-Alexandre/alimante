#!/usr/bin/env python3
"""
Test minimal pour identifier la bonne configuration de l'écran ST7735
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

def test_configuration_simple():
    """Test avec la configuration la plus simple possible"""
    if not ST7735_AVAILABLE:
        print("❌ Librairie ST7735 non disponible")
        return False
    
    try:
        config = get_gpio_config()
        reset_pin = config['DISPLAY']['RESET_PIN']
        a0_pin = config['DISPLAY']['A0_PIN']
        
        print("🔧 Test configuration simple...")
        print(f"   RST={reset_pin}, A0={a0_pin}")
        
        # Configuration la plus simple possible
        display = st7735.ST7735(
            port=0,
            cs=0,
            dc=a0_pin,
            rst=reset_pin
        )
        
        display.begin()
        print(f"   ✅ Résolution détectée: {display.width}x{display.height}")
        
        # Test simple - rouge pur
        print("   🎨 Test rouge pur...")
        image = Image.new('RGB', (display.width, display.height), color=(255, 0, 0))
        display.display(image)
        
        print("   Regardez l'écran - voyez-vous du ROUGE ?")
        print("   (Appuyez sur Entrée pour continuer)")
        input()
        
        # Test vert pur
        print("   🎨 Test vert pur...")
        image = Image.new('RGB', (display.width, display.height), color=(0, 255, 0))
        display.display(image)
        
        print("   Regardez l'écran - voyez-vous du VERT ?")
        print("   (Appuyez sur Entrée pour continuer)")
        input()
        
        # Test bleu pur
        print("   🎨 Test bleu pur...")
        image = Image.new('RGB', (display.width, display.height), color=(0, 0, 255))
        display.display(image)
        
        print("   Regardez l'écran - voyez-vous du BLEU ?")
        print("   (Appuyez sur Entrée pour continuer)")
        input()
        
        # Nettoyage
        del display
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_avec_rotation(rotation):
    """Test avec une rotation spécifique"""
    if not ST7735_AVAILABLE:
        return False
    
    try:
        config = get_gpio_config()
        reset_pin = config['DISPLAY']['RESET_PIN']
        a0_pin = config['DISPLAY']['A0_PIN']
        
        print(f"🔧 Test avec rotation {rotation}°...")
        
        display = st7735.ST7735(
            port=0,
            cs=0,
            dc=a0_pin,
            rst=reset_pin,
            rotation=rotation
        )
        
        display.begin()
        print(f"   ✅ Résolution: {display.width}x{display.height}")
        
        # Test rouge
        image = Image.new('RGB', (display.width, display.height), color=(255, 0, 0))
        display.display(image)
        
        print(f"   Rotation {rotation}° - Rouge visible ? (Entrée pour continuer)")
        input()
        
        del display
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_avec_bgr(bgr_mode):
    """Test avec un mode BGR spécifique"""
    if not ST7735_AVAILABLE:
        return False
    
    try:
        config = get_gpio_config()
        reset_pin = config['DISPLAY']['RESET_PIN']
        a0_pin = config['DISPLAY']['A0_PIN']
        
        print(f"🔧 Test avec bgr={bgr_mode}...")
        
        display = st7735.ST7735(
            port=0,
            cs=0,
            dc=a0_pin,
            rst=reset_pin,
            rotation=0,  # Pas de rotation d'abord
            bgr=bgr_mode
        )
        
        display.begin()
        print(f"   ✅ Résolution: {display.width}x{display.height}")
        
        # Test rouge
        image = Image.new('RGB', (display.width, display.height), color=(255, 0, 0))
        display.display(image)
        
        print(f"   bgr={bgr_mode} - Rouge visible ? (Entrée pour continuer)")
        input()
        
        del display
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    """Test progressif pour trouver la bonne configuration"""
    if not ST7735_AVAILABLE:
        print("❌ Librairie ST7735 non disponible")
        return
    
    print("🔧 TEST MINIMAL ÉCRAN ST7735")
    print("=" * 50)
    print("Ce test va identifier la bonne configuration étape par étape")
    print("Répondez aux questions pour chaque test")
    
    # Gestionnaire de signal
    def signal_handler(signum, frame):
        print("\n🛑 Arrêt du test...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Test 1: Configuration de base
    print("\n" + "="*30)
    print("TEST 1: Configuration de base")
    print("="*30)
    test_configuration_simple()
    
    # Test 2: Différentes rotations
    print("\n" + "="*30)
    print("TEST 2: Différentes rotations")
    print("="*30)
    for rotation in [0, 90, 180, 270]:
        test_avec_rotation(rotation)
    
    # Test 3: Modes BGR
    print("\n" + "="*30)
    print("TEST 3: Modes BGR")
    print("="*30)
    for bgr_mode in [False, True]:
        test_avec_bgr(bgr_mode)
    
    print("\n" + "="*50)
    print("📊 RÉSUMÉ")
    print("="*50)
    print("Maintenant vous savez quelle configuration fonctionne le mieux!")
    print("Utilisez ces paramètres dans vos scripts principaux.")

if __name__ == "__main__":
    main()
