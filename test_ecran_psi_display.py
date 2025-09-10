#!/usr/bin/env python3
"""
Test spécifique pour l'écran PSI
Test des pins Reset, A0, SDA, SCL
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
from datetime import datetime

class PSIDisplayTest:
    """Test pour l'écran PSI"""
    
    def __init__(self, reset_pin=24, a0_pin=25, sda_pin=10, scl_pin=11):
        """
        Initialise le test de l'écran PSI
        
        Args:
            reset_pin (int): Pin Reset de l'écran
            a0_pin (int): Pin A0 de l'écran
            sda_pin (int): Pin SDA (I2C) de l'écran
            scl_pin (int): Pin SCL (I2C) de l'écran
        """
        self.reset_pin = reset_pin
        self.a0_pin = a0_pin
        self.sda_pin = sda_pin
        self.scl_pin = scl_pin
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Gestionnaire de signal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
    
    def initialize(self):
        """Initialise les pins de l'écran PSI"""
        try:
            # Configuration des pins en sortie
            GPIO.setup(self.reset_pin, GPIO.OUT)
            GPIO.setup(self.a0_pin, GPIO.OUT)
            GPIO.setup(self.sda_pin, GPIO.OUT)
            GPIO.setup(self.scl_pin, GPIO.OUT)
            
            # État initial
            GPIO.output(self.reset_pin, GPIO.HIGH)  # Reset actif bas
            GPIO.output(self.a0_pin, GPIO.LOW)      # A0 bas
            GPIO.output(self.sda_pin, GPIO.HIGH)    # SDA haut
            GPIO.output(self.scl_pin, GPIO.HIGH)    # SCL haut
            
            print("✅ Pins écran PSI initialisés")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False
    
    def test_reset_sequence(self):
        """Test de la séquence de reset"""
        print("🔄 Test séquence de reset...")
        
        # Reset (actif bas)
        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.reset_pin, GPIO.HIGH)
        time.sleep(0.1)
        
        print("✅ Séquence de reset terminée")
    
    def test_a0_control(self):
        """Test du contrôle A0"""
        print("🔄 Test contrôle A0...")
        
        # A0 = 0 (commande)
        GPIO.output(self.a0_pin, GPIO.LOW)
        print("   A0 = 0 (mode commande)")
        time.sleep(0.5)
        
        # A0 = 1 (données)
        GPIO.output(self.a0_pin, GPIO.HIGH)
        print("   A0 = 1 (mode données)")
        time.sleep(0.5)
        
        # Retour à 0
        GPIO.output(self.a0_pin, GPIO.LOW)
        print("✅ Test contrôle A0 terminé")
    
    def test_i2c_pins(self):
        """Test des pins I2C"""
        print("🔄 Test pins I2C...")
        
        # Test SDA
        print("   Test SDA...")
        GPIO.output(self.sda_pin, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(self.sda_pin, GPIO.HIGH)
        time.sleep(0.2)
        
        # Test SCL
        print("   Test SCL...")
        GPIO.output(self.scl_pin, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(self.scl_pin, GPIO.HIGH)
        time.sleep(0.2)
        
        print("✅ Test pins I2C terminé")
    
    def test_i2c_sequence(self):
        """Test d'une séquence I2C simple"""
        print("🔄 Test séquence I2C...")
        
        # Start condition
        GPIO.output(self.sda_pin, GPIO.HIGH)
        GPIO.output(self.scl_pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.sda_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.scl_pin, GPIO.LOW)
        time.sleep(0.1)
        
        # Quelques cycles de clock
        for i in range(8):
            GPIO.output(self.scl_pin, GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(self.scl_pin, GPIO.LOW)
            time.sleep(0.05)
        
        # Stop condition
        GPIO.output(self.sda_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.scl_pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.sda_pin, GPIO.HIGH)
        time.sleep(0.1)
        
        print("✅ Séquence I2C terminée")
    
    def run_complete_test(self):
        """Lance le test complet"""
        print("🚀 Démarrage du test écran PSI...")
        
        if not self.initialize():
            return
        
        print("\n" + "="*60)
        print("🖥️  TEST ÉCRAN PSI - ALIMANTE")
        print("="*60)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔌 Reset Pin: {self.reset_pin}")
        print(f"🔌 A0 Pin: {self.a0_pin}")
        print(f"🔌 SDA Pin: {self.sda_pin}")
        print(f"🔌 SCL Pin: {self.scl_pin}")
        print("="*60)
        
        try:
            while self.running:
                print("\n🎛️  MENU DE TEST:")
                print("1. Test séquence de reset")
                print("2. Test contrôle A0")
                print("3. Test pins I2C")
                print("4. Test séquence I2C")
                print("5. Test complet")
                print("0. Quitter")
                
                choice = input("\nVotre choix (0-5): ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    self.test_reset_sequence()
                elif choice == "2":
                    self.test_a0_control()
                elif choice == "3":
                    self.test_i2c_pins()
                elif choice == "4":
                    self.test_i2c_sequence()
                elif choice == "5":
                    print("🔄 Test complet en cours...")
                    self.test_reset_sequence()
                    time.sleep(1)
                    self.test_a0_control()
                    time.sleep(1)
                    self.test_i2c_pins()
                    time.sleep(1)
                    self.test_i2c_sequence()
                    print("✅ Test complet terminé!")
                else:
                    print("❌ Choix invalide")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Arrêt par l'utilisateur")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Nettoie les ressources"""
        GPIO.cleanup()
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du test...")
        self.running = False
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🖥️  TEST ÉCRAN PSI")
    print("🔧 Test pins Reset, A0, SDA, SCL pour Alimante")
    print("=" * 70)
    
    # Configuration des pins (selon votre câblage)
    RESET_PIN = 24  # Pin Reset de l'écran
    A0_PIN = 25     # Pin A0 de l'écran
    SDA_PIN = 10    # Pin SDA (I2C) de l'écran
    SCL_PIN = 11    # Pin SCL (I2C) de l'écran
    
    print(f"🔌 Configuration GPIO:")
    print(f"   • Reset Pin: {RESET_PIN}")
    print(f"   • A0 Pin: {A0_PIN}")
    print(f"   • SDA Pin: {SDA_PIN}")
    print(f"   • SCL Pin: {SCL_PIN}")
    print()
    
    # Création et lancement du test
    test = PSIDisplayTest(RESET_PIN, A0_PIN, SDA_PIN, SCL_PIN)
    
    try:
        test.run_complete_test()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
