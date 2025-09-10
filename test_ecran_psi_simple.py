#!/usr/bin/env python3
"""
Test simple pour l'écran PSI avec encodeur rotatif
Version simplifiée pour tests rapides
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
from datetime import datetime

class SimplePSITest:
    """Test simple pour l'écran PSI"""
    
    def __init__(self, clk_pin=17, dt_pin=27, sw_pin=22):
        """
        Initialise le test PSI
        
        Args:
            clk_pin (int): Pin CLK de l'encodeur
            dt_pin (int): Pin DT de l'encodeur
            sw_pin (int): Pin SW (bouton) de l'encodeur
        """
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # États
        self.last_clk_state = 0
        self.last_sw_state = 0
        self.last_sw_time = 0
        self.counter = 0
        self.running = True
        
        # Gestionnaire de signal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise les pins GPIO"""
        try:
            GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Interruptions
            GPIO.add_event_detect(self.clk_pin, GPIO.BOTH, callback=self._clk_callback, bouncetime=2)
            GPIO.add_event_detect(self.sw_pin, GPIO.FALLING, callback=self._sw_callback, bouncetime=200)
            
            print("✅ Pins GPIO initialisés")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False
    
    def _clk_callback(self, channel):
        """Callback pour le changement d'état du pin CLK"""
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        if clk_state != self.last_clk_state and clk_state == 0:
            if dt_state != clk_state:
                # Rotation horaire
                self.counter += 1
                print(f"🔄 Rotation droite: {self.counter}")
            else:
                # Rotation anti-horaire
                self.counter -= 1
                print(f"🔄 Rotation gauche: {self.counter}")
        
        self.last_clk_state = clk_state
    
    def _sw_callback(self, channel):
        """Callback pour l'appui sur le bouton"""
        current_time = time.time()
        if current_time - self.last_sw_time > 0.2:  # Anti-rebond
            print(f"🔘 Bouton pressé! Compteur: {self.counter}")
            self.last_sw_time = current_time
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du test...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def run_test(self):
        """Lance le test"""
        print("🚀 Démarrage du test PSI...")
        
        if not self.initialize():
            return
        
        print("\n" + "="*50)
        print("🖥️  TEST ÉCRAN PSI - ALIMANTE")
        print("="*50)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔌 CLK Pin: {self.clk_pin}")
        print(f"🔌 DT Pin: {self.dt_pin}")
        print(f"🔌 SW Pin: {self.sw_pin}")
        print("="*50)
        print()
        print("🎛️  INSTRUCTIONS:")
        print("   • Tournez l'encodeur pour incrémenter/décrémenter")
        print("   • Appuyez sur le bouton pour afficher le compteur")
        print("   • Ctrl+C pour quitter")
        print()
        print("🔄 Test en cours...")
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt par l'utilisateur")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Nettoie les ressources"""
        GPIO.cleanup()
        print("🧹 Ressources nettoyées")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🖥️  TEST SIMPLE ÉCRAN PSI")
    print("🔧 Test encodeur rotatif pour Alimante")
    print("=" * 60)
    
    # Configuration des pins (modifiez selon votre câblage)
    CLK_PIN = 17  # Pin CLK de l'encodeur
    DT_PIN = 27   # Pin DT de l'encodeur
    SW_PIN = 22   # Pin SW (bouton) de l'encodeur
    
    print(f"🔌 Configuration GPIO:")
    print(f"   • CLK Pin: {CLK_PIN}")
    print(f"   • DT Pin: {DT_PIN}")
    print(f"   • SW Pin: {SW_PIN}")
    print()
    
    # Création et lancement du test
    test = SimplePSITest(CLK_PIN, DT_PIN, SW_PIN)
    
    try:
        test.run_test()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
