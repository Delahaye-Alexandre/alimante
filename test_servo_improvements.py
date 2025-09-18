#!/usr/bin/env python3
"""
Script de test pour vérifier les améliorations du servo
"""

import sys
import os
import time
import logging

# Ajouter le répertoire src au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from controllers.drivers.servo_driver import ServoDriver
from controllers.drivers.base_driver import DriverConfig

def test_servo_precision():
    """Test de précision du servo"""
    print("🔧 Test de précision du servo...")
    
    # Configuration du driver
    config = DriverConfig(
        name="test_servo",
        enabled=True,
        type="servo"
    )
    
    # Créer le driver (mode simulation)
    servo = ServoDriver(config, gpio_pin=18, frequency=50)
    
    # Initialiser
    if not servo.initialize():
        print("❌ Échec d'initialisation du servo")
        return False
    
    print("✅ Servo initialisé")
    
    # Test de calibration
    print("\n📐 Test de calibration...")
    servo.calibrate(min_angle=0, max_angle=180, min_pulse=1.0, max_pulse=2.0)
    
    # Test de précision des angles
    test_angles = [0, 45, 90, 135, 180]
    print("\n🎯 Test de précision des angles...")
    
    for angle in test_angles:
        print(f"  Angle {angle}°...")
        servo.write({"angle": angle, "duration": 1.0})
        time.sleep(0.5)
        
        # Vérifier la position
        current_angle = servo.get_angle()
        print(f"    Position actuelle: {current_angle}°")
        
        # Test de maintien de position
        servo.hold_position(0.1)
        time.sleep(0.2)
        
        # Vérifier que la position est maintenue
        final_angle = servo.get_angle()
        print(f"    Position finale: {final_angle}°")
        
        if abs(final_angle - angle) > 2:  # Tolérance de 2°
            print(f"    ⚠️  Dérive détectée: {abs(final_angle - angle)}°")
        else:
            print(f"    ✅ Position stable")
    
    # Test de retour à la position fermée
    print("\n🔒 Test de retour à la position fermée...")
    servo.write({"angle": 0, "duration": 1.0})
    time.sleep(0.5)
    
    final_position = servo.get_angle()
    print(f"Position finale: {final_position}°")
    
    if abs(final_position - 0) <= 2:
        print("✅ Retour à la position fermée réussi")
        return True
    else:
        print(f"❌ Problème de retour à la position: {final_position}°")
        return False

def test_feeding_sequence():
    """Test de la séquence d'alimentation"""
    print("\n🍽️ Test de la séquence d'alimentation...")
    
    # Configuration du driver
    config = DriverConfig(
        name="feeding_servo",
        enabled=True,
        type="servo"
    )
    
    # Créer le driver
    servo = ServoDriver(config, gpio_pin=18, frequency=50)
    
    if not servo.initialize():
        print("❌ Échec d'initialisation")
        return False
    
    # Simuler la séquence d'alimentation
    print("  Ouverture trappe 1...")
    servo.write({"angle": 90, "duration": 1.0})
    servo.hold_position(0.2)
    time.sleep(1)
    
    print("  Fermeture trappe 1...")
    servo.write({"angle": 0, "duration": 1.0})
    servo.hold_position(0.2)
    time.sleep(1)
    
    print("  Ouverture trappe 2...")
    servo.write({"angle": 180, "duration": 1.0})
    servo.hold_position(0.2)
    time.sleep(1)
    
    print("  Fermeture trappe 2...")
    servo.write({"angle": 0, "duration": 1.0})
    servo.hold_position(0.2)
    time.sleep(1)
    
    # Vérifier la position finale
    final_angle = servo.get_angle()
    print(f"  Position finale: {final_angle}°")
    
    if abs(final_angle - 0) <= 2:
        print("✅ Séquence d'alimentation réussie")
        return True
    else:
        print(f"❌ Problème de position finale: {final_angle}°")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test des améliorations du servo Alimante")
    print("=" * 50)
    
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    
    # Tests
    precision_ok = test_servo_precision()
    feeding_ok = test_feeding_sequence()
    
    print("\n" + "=" * 50)
    print("📊 Résultats des tests:")
    print(f"  Précision: {'✅' if precision_ok else '❌'}")
    print(f"  Alimentation: {'✅' if feeding_ok else '❌'}")
    
    if precision_ok and feeding_ok:
        print("\n🎉 Tous les tests sont passés !")
        print("\n💡 Conseils pour améliorer encore plus la précision:")
        print("  1. Calibrez votre servo avec les vraies valeurs min/max")
        print("  2. Utilisez un servo de qualité (MG996R, SG90)")
        print("  3. Vérifiez l'alimentation (5V stable)")
        print("  4. Ajoutez un condensateur de filtrage sur l'alimentation")
        return True
    else:
        print("\n⚠️  Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
