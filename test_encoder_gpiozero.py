#!/usr/bin/env python3
"""
Test d'encodeur rotatif avec gpiozero (anti-rebond intégré)
Version simplifiée avec librairie spécialisée
"""

import time
import signal
import sys
from gpiozero import RotaryEncoder, Button
from config_alimante import get_gpio_config

class EncoderTestGPIOZero:
    def __init__(self):
        """Initialise le test avec gpiozero"""
        self.config = get_gpio_config()
        
        # Configuration des pins
        self.clk_pin = self.config['ENCODER']['CLK_PIN']
        self.dt_pin = self.config['ENCODER']['DT_PIN']
        self.sw_pin = self.config['ENCODER']['SW_PIN']
        
        # Variables d'état
        self.counter = 0
        self.button_press_count = 0
        self.is_running = False
        
        # Configuration des signaux
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise l'encodeur et le bouton avec gpiozero"""
        try:
            print("🔧 Initialisation avec gpiozero...")
            
            # Création de l'encodeur (anti-rebond intégré)
            self.encoder = RotaryEncoder(
                a=self.clk_pin, 
                b=self.dt_pin, 
                max_steps=0  # Pas de limite
            )
            
            # Création du bouton (anti-rebond intégré)
            self.button = Button(self.sw_pin, pull_up=True)
            
            # Configuration des callbacks
            self.encoder.when_rotated = self._on_rotation
            self.button.when_pressed = self._on_button_pressed
            self.button.when_released = self._on_button_released
            
            print("✅ Encodeur et bouton initialisés avec gpiozero")
            print(f"   • CLK: GPIO {self.clk_pin}")
            print(f"   • DT:  GPIO {self.dt_pin}")
            print(f"   • SW:  GPIO {self.sw_pin}")
            print("   • Anti-rebond: Intégré dans gpiozero")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            print("💡 Vérifiez que les pins GPIO sont correctes dans config_alimante.py")
            print("💡 Assurez-vous que gpiozero est installé: pip install gpiozero")
            return False
    
    def _on_rotation(self):
        """Callback appelé lors de la rotation"""
        if not self.is_running:
            return
            
        # Direction de rotation
        if self.encoder.steps > self.counter:
            direction = "🔄 HORAIRE"
            self.counter = self.encoder.steps
        else:
            direction = "🔄 ANTI-HORAIRE"
            self.counter = self.encoder.steps
        
        print(f"{direction} | Compteur: {self.counter}")
    
    def _on_button_pressed(self):
        """Callback appelé lors de l'appui du bouton"""
        if not self.is_running:
            return
            
        self.button_press_count += 1
        print(f"🔘 BOUTON PRESSÉ #{self.button_press_count}")
    
    def _on_button_released(self):
        """Callback appelé lors du relâchement du bouton"""
        if not self.is_running:
            return
            
        print("🔘 BOUTON RELÂCHÉ")
    
    def test_rotation(self, duration=10):
        """Test de rotation pendant une durée donnée"""
        print(f"🔄 Test de rotation pendant {duration} secondes...")
        print("   → Tournez l'encodeur dans les deux sens")
        print("   → Appuyez sur le bouton")
        print("   → Appuyez sur Ctrl+C pour arrêter")
        
        self.is_running = True
        self.counter = 0
        self.button_press_count = 0
        
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            print("\n🛑 Test arrêté par l'utilisateur")
        finally:
            self.is_running = False
            
        print(f"\n📊 Résultats:")
        print(f"   • Rotations détectées: {self.counter}")
        print(f"   • Appuis de bouton: {self.button_press_count}")
    
    def monitor_realtime(self):
        """Monitoring en temps réel"""
        print("👁️ Monitoring en temps réel")
        print("   → Tournez l'encodeur et appuyez sur le bouton")
        print("   → Appuyez sur Ctrl+C pour arrêter")
        
        self.is_running = True
        self.counter = 0
        self.button_press_count = 0
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring arrêté")
        finally:
            self.is_running = False
    
    def cleanup(self):
        """Nettoie les ressources"""
        self.is_running = False
        if hasattr(self, 'encoder'):
            self.encoder.close()
        if hasattr(self, 'button'):
            self.button.close()
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du programme...")
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("🔧 TEST ENCODEUR ROTATIF - gpiozero")
    print("📍 Anti-rebond intégré dans la librairie")
    print("📍 Configuration basée sur config_alimante.py")
    print("=" * 60)
    
    # Vérification de l'installation de gpiozero
    try:
        import gpiozero
        # gpiozero n'a pas toujours __version__, on vérifie juste l'import
        print("✅ gpiozero disponible")
    except ImportError:
        print("❌ gpiozero non installé!")
        print("   Installez avec: pip install gpiozero")
        return
    
    # Création du testeur
    encoder_test = EncoderTestGPIOZero()
    
    try:
        # Initialisation
        if not encoder_test.initialize():
            print("❌ Impossible d'initialiser l'encodeur")
            return
        
        # Menu interactif
        while True:
            print("\n" + "=" * 40)
            print("MENU DE TEST ENCODEUR (gpiozero):")
            print("1. Test de rotation (10s)")
            print("2. Monitoring temps réel")
            print("3. Afficher configuration")
            print("0. Quitter")
            print("=" * 40)
            
            choice = input("Votre choix (0-3): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                try:
                    duration = int(input("Durée du test en secondes (défaut 10): ") or "10")
                    encoder_test.test_rotation(duration)
                except ValueError:
                    print("❌ Durée invalide, utilisation de 10s")
                    encoder_test.test_rotation(10)
            elif choice == "2":
                encoder_test.monitor_realtime()
            elif choice == "3":
                from config_alimante import print_config
                print_config()
            else:
                print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        encoder_test.cleanup()

if __name__ == "__main__":
    main()
