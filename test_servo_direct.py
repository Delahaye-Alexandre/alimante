#!/usr/bin/env python3
"""
Test direct du ServoDriver
"""

import sys
import os
import logging

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_servo_direct():
    """Test direct du ServoDriver"""
    print("🔧 Test direct du ServoDriver")
    print("=" * 50)
    
    try:
        # Import des modules
        print("1. Import des modules...")
        from controllers.drivers.servo_driver import ServoDriver
        from controllers.drivers.base_driver import DriverConfig, DriverError
        print("   ✅ Imports réussis")
        
        # Création de la configuration
        print("2. Création de la configuration...")
        config = DriverConfig(
            name="test_servo",
            enabled=True
        )
        print("   ✅ Configuration créée")
        
        # Initialisation du driver
        print("3. Initialisation du driver...")
        servo = ServoDriver(config, 18, 50)  # pin 18, frequency 50Hz
        print("   ✅ Driver initialisé")
        
        # Test de l'initialisation
        print("4. Test de l'initialisation...")
        if servo.initialize():
            print("   ✅ Driver initialisé avec succès")
        else:
            print("   ❌ Échec de l'initialisation")
            return
        
        # Test de la méthode write
        print("5. Test de la méthode write...")
        try:
            result = servo.write({"angle": 90, "duration": 1.0})
            print(f"   Résultat write: {result}")
        except Exception as e:
            print(f"   ❌ Erreur write: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
        
        # Test de la méthode read
        print("6. Test de la méthode read...")
        try:
            data = servo.read()
            print(f"   Données lues: {data}")
        except Exception as e:
            print(f"   ❌ Erreur read: {e}")
        
        # Nettoyage
        print("7. Nettoyage...")
        servo.cleanup()
        print("   ✅ Nettoyage terminé")
        
    except Exception as e:
        print(f"   ❌ Erreur générale: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_servo_direct()
