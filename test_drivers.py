#!/usr/bin/env python3
"""
Test des drivers Alimante
Vérifie que tous les drivers fonctionnent correctement
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from controllers.drivers import (
    MosfetDriver,
    CameraDriver,
    I2CLCDDriver
)
from controllers.drivers.base_driver import DriverConfig

def test_mosfet_driver():
    """Test du driver MOSFET"""
    print("🔌 TEST DU DRIVER MOSFET")
    print("=" * 50)
    
    try:
        # Configuration
        config = DriverConfig(
            name="mosfet_test",
            min_duty_cycle=0,
            max_duty_cycle=100,
            fade_enabled=True
        )
        
        # Initialiser le driver
        mosfet = MosfetDriver(config, gpio_pin=18, frequency=1000)
        
        if not mosfet.initialize():
            print("❌ Échec initialisation driver MOSFET")
            return False
        
        print("✅ Driver MOSFET initialisé")
        
        # Test de lecture
        status = mosfet.read()
        print(f"✅ État lu: {status['state']}")
        
        # Test d'écriture (intensité)
        if mosfet.write({'duty_cycle': 50, 'fade': True}):
            print("✅ Intensité définie: 50%")
        else:
            print("❌ Échec définition intensité")
            return False
        
        # Test de fondu
        if mosfet.fade_in(1.0):
            print("✅ Fondu entrée réussi")
        else:
            print("❌ Échec fondu entrée")
            return False
        
        time.sleep(1)
        
        if mosfet.fade_out(1.0):
            print("✅ Fondu sortie réussi")
        else:
            print("❌ Échec fondu sortie")
            return False
        
        # Test de protection thermique
        mosfet.set_temperature(85.0)
        print("✅ Protection thermique testée")
        
        # Test du statut
        status = mosfet.get_status()
        print(f"✅ Statut: {status['state']}")
        
        # Nettoyage
        mosfet.cleanup()
        print("✅ Driver MOSFET nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test driver MOSFET: {e}")
        return False

def test_camera_driver():
    """Test du driver caméra"""
    print("\n📷 TEST DU DRIVER CAMÉRA")
    print("=" * 50)
    
    try:
        # Configuration
        config = DriverConfig(
            name="camera_test",
            capture_format='jpg',
            quality=80
        )
        
        # Initialiser le driver
        camera = CameraDriver(config, camera_index=0)
        
        if not camera.initialize():
            print("❌ Échec initialisation driver caméra")
            return False
        
        print("✅ Driver caméra initialisé")
        
        # Test de lecture
        status = camera.read()
        print(f"✅ État lu: {status['state']}")
        
        # Test de capture d'image
        if camera.write({'action': 'capture', 'prefix': 'test'}):
            print("✅ Capture d'image réussie")
        else:
            print("❌ Échec capture d'image")
            return False
        
        # Test de capture d'instantané
        snapshot_path = camera.capture_snapshot("snapshot_test")
        if snapshot_path:
            print(f"✅ Instantané capturé: {snapshot_path}")
        else:
            print("❌ Échec capture instantané")
            return False
        
        # Test de détection de mouvement
        if camera.start_motion_detection(0.1):
            print("✅ Détection de mouvement activée")
        else:
            print("❌ Échec activation détection mouvement")
            return False
        
        if camera.stop_motion_detection():
            print("✅ Détection de mouvement désactivée")
        else:
            print("❌ Échec désactivation détection mouvement")
            return False
        
        # Test du statut
        status = camera.get_status()
        print(f"✅ Statut: {status['state']}")
        print(f"✅ Images capturées: {status['stats']['frames_captured']}")
        
        # Nettoyage
        camera.cleanup()
        print("✅ Driver caméra nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test driver caméra: {e}")
        return False

def test_i2c_lcd_driver():
    """Test du driver LCD I2C"""
    print("\n📺 TEST DU DRIVER LCD I2C")
    print("=" * 50)
    
    try:
        # Configuration
        config = DriverConfig(
            name="i2c_lcd_test",
            rows=4,
            cols=20
        )
        
        # Initialiser le driver
        lcd = I2CLCDDriver(config, i2c_address=0x27, i2c_bus=1)
        
        if not lcd.initialize():
            print("❌ Échec initialisation driver LCD I2C")
            return False
        
        print("✅ Driver LCD I2C initialisé")
        
        # Test de lecture
        status = lcd.read()
        print(f"✅ État lu: {status['state']}")
        
        # Test d'effacement
        if lcd.clear():
            print("✅ Écran effacé")
        else:
            print("❌ Échec effacement écran")
            return False
        
        # Test d'écriture de texte
        if lcd.write({'action': 'text', 'text': 'Test Alimante', 'row': 0, 'col': 0}):
            print("✅ Texte écrit")
        else:
            print("❌ Échec écriture texte")
            return False
        
        # Test d'écriture de ligne
        if lcd.write_line(1, "Ligne 2 - Test"):
            print("✅ Ligne écrite")
        else:
            print("❌ Échec écriture ligne")
            return False
        
        # Test d'affichage de message
        message = [
            "=== ALIMANTE ===",
            "Temp: 25.5°C",
            "Hum: 60%",
            "Status: OK"
        ]
        
        if lcd.display_message(message):
            print("✅ Message affiché")
        else:
            print("❌ Échec affichage message")
            return False
        
        # Test de positionnement curseur
        if lcd.set_cursor(2, 5):
            print("✅ Curseur positionné")
        else:
            print("❌ Échec positionnement curseur")
            return False
        
        # Test de configuration curseur
        if lcd.write({'action': 'cursor', 'visible': True, 'blink': True}):
            print("✅ Curseur configuré")
        else:
            print("❌ Échec configuration curseur")
            return False
        
        # Test de rétroéclairage
        if lcd.write({'action': 'backlight', 'enabled': True}):
            print("✅ Rétroéclairage activé")
        else:
            print("❌ Échec rétroéclairage")
            return False
        
        # Test du statut
        status = lcd.get_status()
        print(f"✅ Statut: {status['state']}")
        print(f"✅ Résolution: {status['resolution']}")
        
        # Nettoyage
        lcd.cleanup()
        print("✅ Driver LCD I2C nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test driver LCD I2C: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST DES DRIVERS ALIMANTE")
    print("=" * 60)
    
    tests = [
        test_mosfet_driver,
        test_camera_driver,
        test_i2c_lcd_driver
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Ligne vide entre les tests
    
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 30)
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 TOUS LES TESTS RÉUSSIS !")
        print("Les drivers fonctionnent correctement.")
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
