#!/usr/bin/env python3
"""
Test pour l'encodeur rotatif avec bouton
Configuration basée sur config_alimante.py
Pins: CLK=17, DT=27, SW=22
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
import threading
from config_alimante import get_gpio_config, get_test_config

class EncoderTest:
    def __init__(self):
        """Initialise le test de l'encodeur rotatif"""
        self.config = get_gpio_config()
        self.test_config = get_test_config()
        
        # Configuration des pins
        self.clk_pin = self.config['ENCODER']['CLK_PIN']
        self.dt_pin = self.config['ENCODER']['DT_PIN']
        self.sw_pin = self.config['ENCODER']['SW_PIN']
        
        # Variables d'état
        self.counter = 0
        self.last_clk_state = 0
        self.last_sw_state = 0
        self.sw_pressed = False
        self.sw_press_time = 0
        self.is_running = False
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Gestionnaire de signal pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise les pins GPIO de l'encodeur"""
        try:
            # Nettoyage préalable des GPIO
            GPIO.cleanup()
            
            # Configuration des pins d'entrée avec pull-up interne
            GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Lecture de l'état initial AVANT de configurer les interruptions
            self.last_clk_state = GPIO.input(self.clk_pin)
            self.last_sw_state = GPIO.input(self.sw_pin)
            
            # Configuration des interruptions avec gestion d'erreur
            try:
                GPIO.add_event_detect(self.clk_pin, GPIO.BOTH, callback=self._clk_callback, bouncetime=2)
                print(f"✅ Interruption CLK configurée sur GPIO {self.clk_pin}")
            except Exception as e:
                print(f"❌ Erreur configuration interruption CLK: {e}")
                return False
                
            try:
                GPIO.add_event_detect(self.sw_pin, GPIO.BOTH, callback=self._sw_callback, bouncetime=2)
                print(f"✅ Interruption SW configurée sur GPIO {self.sw_pin}")
            except Exception as e:
                print(f"❌ Erreur configuration interruption SW: {e}")
                return False
            
            self.is_running = True
            print("✅ Encodeur rotatif initialisé")
            print(f"   📌 CLK: GPIO {self.clk_pin}")
            print(f"   📌 DT:  GPIO {self.dt_pin}")
            print(f"   📌 SW:  GPIO {self.sw_pin}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def _clk_callback(self, channel):
        """Callback pour la détection de rotation"""
        if not self.is_running:
            return
            
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        # Détection du changement d'état sur CLK
        if clk_state != self.last_clk_state:
            # Détection de la direction de rotation
            if dt_state != clk_state:
                # Rotation horaire
                self.counter += 1
                direction = "🔄 HORAIRE"
            else:
                # Rotation anti-horaire
                self.counter -= 1
                direction = "🔄 ANTI-HORAIRE"
            
            print(f"{direction} | Compteur: {self.counter}")
            self.last_clk_state = clk_state
    
    def _sw_callback(self, channel):
        """Callback pour la détection du bouton"""
        if not self.is_running:
            return
            
        sw_state = GPIO.input(self.sw_pin)
        current_time = time.time()
        
        # Détection de l'appui (transition HIGH -> LOW)
        if sw_state == 0 and self.last_sw_state == 1:
            self.sw_pressed = True
            self.sw_press_time = current_time
            print("🔘 BOUTON APPUYÉ")
        
        # Détection du relâchement (transition LOW -> HIGH)
        elif sw_state == 1 and self.last_sw_state == 0:
            if self.sw_pressed:
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
        
        start_time = time.time()
        initial_counter = self.counter
        
        try:
            while time.time() - start_time < duration:
                time.sleep(0.1)
                
                # Affichage périodique du compteur
                if int(time.time()) % 2 == 0:
                    print(f"   Compteur actuel: {self.counter}")
                
        except KeyboardInterrupt:
            print("\n🛑 Test interrompu par l'utilisateur")
        
        final_counter = self.counter
        total_rotations = final_counter - initial_counter
        print(f"✅ Test terminé")
        print(f"   → Rotations totales: {total_rotations}")
        print(f"   → Compteur final: {self.counter}")
    
    def test_button_sequence(self):
        """Test de séquence de boutons"""
        print("🔘 Test de séquence de boutons...")
        print("   → Appuyez sur le bouton selon les instructions")
        print("   → Appuyez sur Ctrl+C pour arrêter")
        
        sequences = [
            ("1 clic court", 1, 0.5),
            ("1 clic long", 1, 1.5),
            ("2 clics courts", 2, 0.3),
            ("3 clics rapides", 3, 0.2)
        ]
        
        for description, count, max_duration in sequences:
            print(f"\n📋 {description} (max {max_duration}s par clic)")
            input("   → Appuyez sur Entrée quand prêt...")
            
            clics_detected = 0
            start_time = time.time()
            
            while clics_detected < count and (time.time() - start_time) < 10:
                if self.sw_pressed:
                    clics_detected += 1
                    print(f"   Clic {clics_detected}/{count} détecté")
                    # Attendre le relâchement
                    while self.sw_pressed:
                        time.sleep(0.01)
                    time.sleep(0.1)  # Petite pause entre les clics
            
            if clics_detected == count:
                print(f"   ✅ {description} réussi!")
            else:
                print(f"   ❌ {description} échoué ({clics_detected}/{count})")
    
    def test_encoder_precision(self, rotations=10):
        """Test de précision de l'encodeur"""
        print(f"🎯 Test de précision ({rotations} rotations)...")
        print("   → Effectuez exactement 10 rotations horaires")
        print("   → Puis 10 rotations anti-horaires")
        print("   → Appuyez sur Entrée pour commencer...")
        input()
        
        initial_counter = self.counter
        print(f"   Compteur initial: {initial_counter}")
        
        # Test rotations horaires
        print("\n   🔄 Rotations horaires (10 tours)...")
        input("   → Appuyez sur Entrée quand terminé...")
        horaire_counter = self.counter
        
        # Test rotations anti-horaires
        print("\n   🔄 Rotations anti-horaires (10 tours)...")
        input("   → Appuyez sur Entrée quand terminé...")
        final_counter = self.counter
        
        # Calcul des résultats
        horaire_rotations = horaire_counter - initial_counter
        anti_horaire_rotations = final_counter - horaire_counter
        total_rotations = final_counter - initial_counter
        
        print(f"\n📊 Résultats du test de précision:")
        print(f"   → Rotations horaires: {horaire_rotations}")
        print(f"   → Rotations anti-horaires: {anti_horaire_rotations}")
        print(f"   → Total: {total_rotations}")
        print(f"   → Précision: {abs(total_rotations)} rotations détectées")
        
        if abs(total_rotations) <= 2:  # Tolérance de ±2
            print("   ✅ Précision excellente!")
        elif abs(total_rotations) <= 5:
            print("   ⚠️  Précision correcte")
        else:
            print("   ❌ Problème de précision détecté")
    
    def monitor_realtime(self):
        """Monitoring en temps réel"""
        print("📊 Monitoring en temps réel")
        print("   → Tournez l'encodeur et appuyez sur le bouton")
        print("   → Appuyez sur Ctrl+C pour arrêter")
        
        try:
            while True:
                time.sleep(0.1)
                # Le monitoring se fait via les callbacks
        except KeyboardInterrupt:
            print("\n🛑 Monitoring arrêté")
    
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
    print("🔧 TEST ENCODEUR ROTATIF - Alimante")
    print("📍 Configuration basée sur config_alimante.py")
    print("=" * 60)
    
    # Création du testeur
    encoder_test = EncoderTest()
    
    try:
        # Initialisation
        if not encoder_test.initialize():
            print("❌ Impossible d'initialiser l'encodeur")
            return
        
        # Menu interactif
        while True:
            print("\n" + "=" * 40)
            print("MENU DE TEST ENCODEUR:")
            print("1. Test de rotation (10s)")
            print("2. Test de séquence de boutons")
            print("3. Test de précision")
            print("4. Monitoring temps réel")
            print("5. Test personnalisé")
            print("6. Afficher configuration")
            print("0. Quitter")
            print("=" * 40)
            
            choice = input("Votre choix (0-6): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                try:
                    duration = int(input("Durée du test en secondes (défaut 10): ") or "10")
                    encoder_test.test_rotation(duration)
                except ValueError:
                    encoder_test.test_rotation()
            elif choice == "2":
                encoder_test.test_button_sequence()
            elif choice == "3":
                try:
                    rotations = int(input("Nombre de rotations (défaut 10): ") or "10")
                    encoder_test.test_encoder_precision(rotations)
                except ValueError:
                    encoder_test.test_encoder_precision()
            elif choice == "4":
                encoder_test.monitor_realtime()
            elif choice == "5":
                print("Test personnalisé - monitoring continu")
                print("Appuyez sur Ctrl+C pour arrêter")
                encoder_test.monitor_realtime()
            elif choice == "6":
                from config_alimante import print_config
                print_config()
            else:
                print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        # Nettoyage
        encoder_test.cleanup()
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
