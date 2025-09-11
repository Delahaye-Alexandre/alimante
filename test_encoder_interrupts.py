#!/usr/bin/env python3
"""
Test d'encodeur rotatif avec RPi.GPIO et interruptions
Version avec anti-rebond par interruptions (plus efficace)
"""

import RPi.GPIO as GPIO
import time
import signal
import sys
import threading
from config_alimante import get_gpio_config

class EncoderTestInterrupts:
    def __init__(self):
        """Initialise le test avec interruptions"""
        self.config = get_gpio_config()
        
        # Configuration des pins
        self.clk_pin = self.config['ENCODER']['CLK_PIN']
        self.dt_pin = self.config['ENCODER']['DT_PIN']
        self.sw_pin = self.config['ENCODER']['SW_PIN']
        
        # Variables d'état
        self.counter = 0
        self.button_press_count = 0
        self.is_running = False
        
        # Variables d'anti-rebond
        self.last_clk_state = 0
        self.last_sw_state = 0
        self.sw_pressed = False
        self.sw_press_time = 0
        
        # Verrous pour la sécurité des threads
        self.counter_lock = threading.Lock()
        self.button_lock = threading.Lock()
        
        # Configuration des signaux
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise les pins GPIO avec interruptions"""
        try:
            print("🔧 Initialisation avec interruptions...")
            
            # Configuration GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Configuration des pins
            GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Lecture des états initiaux
            self.last_clk_state = GPIO.input(self.clk_pin)
            self.last_sw_state = GPIO.input(self.sw_pin)
            
            # Configuration des interruptions avec anti-rebond
            GPIO.add_event_detect(
                self.clk_pin, 
                GPIO.BOTH, 
                callback=self._clk_callback,
                bouncetime=5  # 5ms d'anti-rebond intégré
            )
            
            GPIO.add_event_detect(
                self.sw_pin, 
                GPIO.BOTH, 
                callback=self._sw_callback,
                bouncetime=10  # 10ms d'anti-rebond intégré
            )
            
            print("✅ Interruptions configurées")
            print(f"   • CLK: GPIO {self.clk_pin} (interruption + 5ms anti-rebond)")
            print(f"   • DT:  GPIO {self.dt_pin}")
            print(f"   • SW:  GPIO {self.sw_pin} (interruption + 10ms anti-rebond)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def _clk_callback(self, channel):
        """Callback pour la pin CLK (interruption)"""
        if not self.is_running:
            return
            
        # Lecture des états actuels
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        # Détection du changement d'état
        if clk_state != self.last_clk_state:
            # Détection de la direction
            if dt_state != clk_state:
                with self.counter_lock:
                    self.counter += 1
                    direction = "🔄 HORAIRE"
            else:
                with self.counter_lock:
                    self.counter -= 1
                    direction = "🔄 ANTI-HORAIRE"
            
            print(f"{direction} | Compteur: {self.counter}")
            self.last_clk_state = clk_state
    
    def _sw_callback(self, channel):
        """Callback pour la pin SW (interruption)"""
        if not self.is_running:
            return
            
        sw_state = GPIO.input(self.sw_pin)
        current_time = time.time()
        
        # Détection de l'appui (transition HIGH -> LOW)
        if sw_state == 0 and self.last_sw_state == 1:
            with self.button_lock:
                self.sw_pressed = True
                self.sw_press_time = current_time
                self.button_press_count += 1
                print(f"🔘 BOUTON PRESSÉ #{self.button_press_count}")
        
        # Détection du relâchement (transition LOW -> HIGH)
        elif sw_state == 1 and self.last_sw_state == 0:
            if self.sw_pressed:
                with self.button_lock:
                    press_duration = current_time - self.sw_press_time
                    print(f"🔘 BOUTON RELÂCHÉ (durée: {press_duration:.2f}s)")
                    
                    # Classification du type d'appui
                    if press_duration < 0.5:
                        print("   → Clic court")
                    elif press_duration < 2.0:
                        print("   → Clic long")
                    else:
                        print("   → Appui très long")
                    
                    self.sw_pressed = False
        
        self.last_sw_state = sw_state
    
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
        """Nettoie les ressources GPIO"""
        self.is_running = False
        GPIO.cleanup()
        print("🧹 Ressources GPIO nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du programme...")
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("🔧 TEST ENCODEUR ROTATIF - Interruptions")
    print("📍 Anti-rebond par interruptions RPi.GPIO")
    print("📍 Configuration basée sur config_alimante.py")
    print("=" * 60)
    
    # Création du testeur
    encoder_test = EncoderTestInterrupts()
    
    try:
        # Initialisation
        if not encoder_test.initialize():
            print("❌ Impossible d'initialiser l'encodeur")
            return
        
        # Menu interactif
        while True:
            print("\n" + "=" * 40)
            print("MENU DE TEST ENCODEUR (Interruptions):")
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
