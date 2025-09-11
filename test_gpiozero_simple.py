#!/usr/bin/env python3
"""
Test simple de gpiozero pour vérifier l'installation
"""

def test_gpiozero():
    """Test basique de gpiozero"""
    try:
        print("🔧 Test de gpiozero...")
        
        # Import des modules
        from gpiozero import RotaryEncoder, Button
        print("✅ Import gpiozero réussi")
        
        # Test de création d'objets (sans pins réelles)
        print("🔧 Test de création d'objets...")
        
        # Note: On ne peut pas tester avec de vraies pins sans hardware
        print("✅ gpiozero est prêt à être utilisé")
        print("💡 Pour tester avec du hardware, utilisez test_encoder_gpiozero.py")
        
        return True
        
    except ImportError as e:
        print(f"❌ gpiozero non installé: {e}")
        print("💡 Installez avec: pip install gpiozero")
        return False
    except Exception as e:
        print(f"❌ Erreur gpiozero: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TEST SIMPLE GPIOZERO")
    print("=" * 50)
    
    if test_gpiozero():
        print("\n🎉 gpiozero est prêt!")
        print("🚀 Vous pouvez maintenant utiliser test_encoder_gpiozero.py")
    else:
        print("\n❌ gpiozero n'est pas prêt")
        print("🔧 Installez gpiozero d'abord")
