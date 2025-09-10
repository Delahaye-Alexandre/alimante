#!/usr/bin/env python3
"""
Test simple des pins GPIO pour Alimante
Test individuel de chaque pin
"""

import RPi.GPIO as GPIO
import time
import sys
import signal

class SimpleGPIOTest:
    """Test simple des pins GPIO"""
    
    def __init__(self):
        """Initialise le test"""
        # Configuration des pins
        self.pins = {
            'Reset': 24,
            'A0/DC': 25,
            'CS': 8,
            'SDA/MOSI': 10,
            'SCL/SCLK': 11
        }
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Gestionnaire de signal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def cleanup(self):
        """Nettoie les ressources"""
        GPIO.cleanup()
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du test...")
        self.cleanup()
        sys.exit(0)
    
    def test_single_pin(self, name, pin):
        """Test un pin individuel"""
        print(f"🔍 Test du pin {name} (GPIO {pin})...")
        
        try:
            # Nettoyage préalable
            GPIO.cleanup()
            time.sleep(0.1)
            
            # Configuration du pin
            GPIO.setup(pin, GPIO.OUT)
            
            # Test de sortie
            print(f"   État bas...")
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.5)
            
            print(f"   État haut...")
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.5)
            
            print(f"   Retour bas...")
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.5)
            
            print(f"✅ Pin {name} (GPIO {pin}) fonctionne")
            return True
            
        except Exception as e:
            print(f"❌ Erreur pin {name} (GPIO {pin}): {e}")
            return False
        finally:
            GPIO.cleanup()
    
    def test_all_pins(self):
        """Test tous les pins"""
        print("🚀 Test de tous les pins GPIO...")
        print("=" * 50)
        
        results = {}
        
        for name, pin in self.pins.items():
            results[name] = self.test_single_pin(name, pin)
            time.sleep(0.5)  # Pause entre les tests
        
        # Résumé
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 50)
        
        for name, success in results.items():
            status = "✅ OK" if success else "❌ ERREUR"
            pin = self.pins[name]
            print(f"{name:12} (GPIO {pin:2d}): {status}")
        
        # Statistiques
        total = len(results)
        ok = sum(results.values())
        failed = total - ok
        
        print(f"\n📈 Résultats: {ok}/{total} pins fonctionnels")
        
        if failed == 0:
            print("🎉 Tous les pins fonctionnent correctement!")
        else:
            print(f"⚠️  {failed} pin(s) en erreur")
            print("🔧 Vérifiez le câblage et l'alimentation")
    
    def test_pin_sequence(self):
        """Test séquentiel des pins"""
        print("🔄 Test séquentiel des pins...")
        
        try:
            # Nettoyage préalable
            GPIO.cleanup()
            time.sleep(0.1)
            
            # Configuration de tous les pins
            for name, pin in self.pins.items():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            
            print("✅ Tous les pins configurés en sortie")
            
            # Séquence de test
            for i in range(5):
                print(f"\n🔄 Cycle {i+1}/5...")
                
                # Allumer tous les pins
                for name, pin in self.pins.items():
                    GPIO.output(pin, GPIO.HIGH)
                print("   Tous les pins allumés")
                time.sleep(0.5)
                
                # Éteindre tous les pins
                for name, pin in self.pins.items():
                    GPIO.output(pin, GPIO.LOW)
                print("   Tous les pins éteints")
                time.sleep(0.5)
            
            print("✅ Test séquentiel terminé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur test séquentiel: {e}")
            return False
        finally:
            GPIO.cleanup()
    
    def run_interactive_test(self):
        """Lance le test interactif"""
        print("🚀 Test interactif des pins GPIO...")
        
        while True:
            print("\n🎛️  MENU DE TEST:")
            print("1. Test pin individuel")
            print("2. Test tous les pins")
            print("3. Test séquentiel")
            print("4. Afficher configuration")
            print("0. Quitter")
            
            choice = input("\nVotre choix (0-4): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                print("\nPins disponibles:")
                for i, (name, pin) in enumerate(self.pins.items(), 1):
                    print(f"{i}. {name} (GPIO {pin})")
                
                try:
                    pin_choice = int(input("Numéro du pin à tester: ")) - 1
                    pin_names = list(self.pins.keys())
                    if 0 <= pin_choice < len(pin_names):
                        name = pin_names[pin_choice]
                        pin = self.pins[name]
                        self.test_single_pin(name, pin)
                    else:
                        print("❌ Choix invalide")
                except ValueError:
                    print("❌ Entrée invalide")
            elif choice == "2":
                self.test_all_pins()
            elif choice == "3":
                self.test_pin_sequence()
            elif choice == "4":
                self.show_configuration()
            else:
                print("❌ Choix invalide")
    
    def show_configuration(self):
        """Affiche la configuration des pins"""
        print("\n📋 CONFIGURATION DES PINS")
        print("=" * 40)
        print("Fonction        | GPIO | Pin Physique")
        print("-" * 40)
        print(f"Reset           | {self.pins['Reset']:4d} | 18")
        print(f"A0/DC           | {self.pins['A0/DC']:4d} | 22")
        print(f"CS              | {self.pins['CS']:4d} | 24")
        print(f"SDA/MOSI        | {self.pins['SDA/MOSI']:4d} | 19")
        print(f"SCL/SCLK        | {self.pins['SCL/SCLK']:4d} | 23")
        print("=" * 40)

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔧 TEST SIMPLE PINS GPIO")
    print("🔍 Test individuel des pins pour Alimante")
    print("=" * 60)
    
    test = SimpleGPIOTest()
    
    try:
        test.run_interactive_test()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        test.cleanup()
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
