#!/usr/bin/env python3
"""
Test pour contrôler 4 bandeaux LED de 15cm
Connectés au même MOSFET sur le GPIO 24
Contrôle de l'intensité lumineuse en pourcentage via PWM
"""

import RPi.GPIO as GPIO
import time
import sys
import signal

class LEDBandeauxController:
    def __init__(self, gpio_pin=18, frequency=1000):
        """
        Initialise le contrôleur pour les bandeaux LED
        
        Args:
            gpio_pin (int): Numéro du GPIO (défaut: 24)
            frequency (int): Fréquence PWM en Hz (défaut: 1000)
        """
        self.gpio_pin = gpio_pin
        self.frequency = frequency
        self.pwm = None
        self.is_initialized = False
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Gestionnaire de signal pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise le GPIO et le PWM"""
        try:
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            self.pwm = GPIO.PWM(self.gpio_pin, self.frequency)
            self.pwm.start(0)  # Commence avec 0% d'intensité
            self.is_initialized = True
            print(f"✅ Bandeaux LED initialisés sur GPIO {self.gpio_pin}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def set_intensity(self, percentage):
        """
        Définit l'intensité lumineuse des bandeaux LED
        
        Args:
            percentage (float): Intensité en pourcentage (0-100)
        """
        if not self.is_initialized:
            print("❌ Contrôleur non initialisé. Appelez initialize() d'abord.")
            return False
        
        # Validation de la plage
        if percentage < 0:
            percentage = 0
        elif percentage > 100:
            percentage = 100
        
        try:
            self.pwm.ChangeDutyCycle(percentage)
            print(f"💡 Intensité des bandeaux LED: {percentage:.1f}%")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du changement d'intensité: {e}")
            return False
    
    def fade_in(self, duration=2.0, steps=50):
        """
        Fonction de fondu progressif (0% à 100%)
        
        Args:
            duration (float): Durée du fondu en secondes
            steps (int): Nombre d'étapes pour le fondu
        """
        if not self.is_initialized:
            print("❌ Contrôleur non initialisé.")
            return
        
        print(f"🌅 Fondu progressif sur {duration}s...")
        step_duration = duration / steps
        
        for i in range(steps + 1):
            intensity = (i / steps) * 100
            self.set_intensity(intensity)
            time.sleep(step_duration)
    
    def fade_out(self, duration=2.0, steps=50):
        """
        Fonction de fondu progressif (100% à 0%)
        
        Args:
            duration (float): Durée du fondu en secondes
            steps (int): Nombre d'étapes pour le fondu
        """
        if not self.is_initialized:
            print("❌ Contrôleur non initialisé.")
            return
        
        print(f"🌆 Fondu progressif sur {duration}s...")
        step_duration = duration / steps
        
        for i in range(steps, -1, -1):
            intensity = (i / steps) * 100
            self.set_intensity(intensity)
            time.sleep(step_duration)
    
    def blink(self, times=5, on_duration=0.5, off_duration=0.5):
        """
        Fait clignoter les bandeaux LED
        
        Args:
            times (int): Nombre de clignotements
            on_duration (float): Durée allumée en secondes
            off_duration (float): Durée éteinte en secondes
        """
        if not self.is_initialized:
            print("❌ Contrôleur non initialisé.")
            return
        
        print(f"⚡ Clignotement {times} fois...")
        for i in range(times):
            self.set_intensity(100)
            time.sleep(on_duration)
            self.set_intensity(0)
            time.sleep(off_duration)
    
    def test_sequence(self):
        """Séquence de test complète"""
        if not self.is_initialized:
            print("❌ Contrôleur non initialisé.")
            return
        
        print("🚀 Début de la séquence de test...")
        
        # Test 1: Fondu progressif
        self.fade_in(3.0)
        time.sleep(1)
        
        # Test 2: Différentes intensités
        intensities = [25, 50, 75, 100]
        for intensity in intensities:
            print(f"Test intensité {intensity}%")
            self.set_intensity(intensity)
            time.sleep(1)
        
        # Test 3: Clignotement
        self.blink(3, 0.3, 0.3)
        
        # Test 4: Fondu progressif sortant
        self.fade_out(3.0)
        
        print("✅ Séquence de test terminée!")
    
    def cleanup(self):
        """Nettoie les ressources GPIO"""
        if self.pwm:
            self.pwm.stop()
        GPIO.cleanup()
        self.is_initialized = False
        print("🧹 Ressources GPIO nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du programme...")
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale de test"""
    print("=" * 50)
    print("🔧 TEST BANDEAUX LED - 4 bandeaux de 15cm")
    print("📍 GPIO 18 - Contrôle PWM")
    print("=" * 50)
    
    # Création du contrôleur
    led_controller = LEDBandeauxController(gpio_pin=18)
    
    try:
        # Initialisation
        if not led_controller.initialize():
            print("❌ Impossible d'initialiser le contrôleur")
            return
        
        # Menu interactif
        while True:
            print("\n" + "=" * 30)
            print("MENU DE TEST:")
            print("1. Définir intensité (0-100%)")
            print("2. Fondu progressif (0% → 100%)")
            print("3. Fondu progressif (100% → 0%)")
            print("4. Clignotement")
            print("5. Séquence de test complète")
            print("6. Test intensités multiples")
            print("0. Quitter")
            print("=" * 30)
            
            choice = input("Votre choix (0-6): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                try:
                    intensity = float(input("Intensité (0-100%): "))
                    led_controller.set_intensity(intensity)
                except ValueError:
                    print("❌ Valeur invalide")
            elif choice == "2":
                led_controller.fade_in()
            elif choice == "3":
                led_controller.fade_out()
            elif choice == "4":
                try:
                    times = int(input("Nombre de clignotements (défaut 5): ") or "5")
                    led_controller.blink(times)
                except ValueError:
                    led_controller.blink()
            elif choice == "5":
                led_controller.test_sequence()
            elif choice == "6":
                print("Test de différentes intensités...")
                for intensity in [10, 25, 50, 75, 90, 100]:
                    print(f"Intensité: {intensity}%")
                    led_controller.set_intensity(intensity)
                    time.sleep(1)
            else:
                print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        # Nettoyage
        led_controller.cleanup()
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
