#!/usr/bin/env python3
"""
Test simple pour l'encodeur rotatif sans interruptions
Utilise une approche de polling pour éviter les conflits GPIO
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
from config_alimante import get_gpio_config, get_test_config

class EncoderTestSimple:
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
        self.last_dt_state = 0
        self.last_sw_state = 0
        self.sw_pressed = False
        self.sw_press_time = 0
        self.is_running = False
        
        # Paramètres d'anti-rebond améliorés
        self.encoder_debounce_ms = 5  # 5ms pour l'encodeur
        self.button_debounce_ms = 10  # 10ms pour le bouton
        
        # Variables d'anti-rebond non-bloquant
        self.clk_debounce_time = 0
        self.sw_debounce_time = 0
        self.clk_pending_state = None
        self.sw_pending_state = None
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Gestionnaire de signal pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise les pins GPIO de l'encodeur"""
        try:
            # Nettoyage préalable
            GPIO.cleanup()
            time.sleep(0.1)
            
            # Configuration des pins d'entrée avec pull-up interne
            GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Lecture de l'état initial
            self.last_clk_state = GPIO.input(self.clk_pin)
            self.last_sw_state = GPIO.input(self.sw_pin)
            
            self.is_running = True
            print("✅ Encodeur rotatif initialisé (mode polling)")
            print(f"   📌 CLK: GPIO {self.clk_pin}")
            print(f"   📌 DT:  GPIO {self.dt_pin}")
            print(f"   📌 SW:  GPIO {self.sw_pin}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def check_rotation(self):
        """Vérifie la rotation de l'encodeur (polling + anti-rebond non-bloquant)"""
        if not self.is_running:
            return
            
        current_time = time.time()
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        # Détection du changement d'état sur CLK
        if clk_state != self.last_clk_state:
            # Si pas de changement en attente, démarrer l'anti-rebond
            if self.clk_pending_state is None:
                self.clk_pending_state = clk_state
                self.clk_debounce_time = current_time
            # Si changement différent en attente, réinitialiser
            elif self.clk_pending_state != clk_state:
                self.clk_pending_state = clk_state
                self.clk_debounce_time = current_time
        
        # Vérifier si l'anti-rebond est terminé
        if (self.clk_pending_state is not None and 
            current_time - self.clk_debounce_time >= self.encoder_debounce_ms / 1000.0):
            
            # Relire l'état actuel pour vérifier la stabilité
            clk_state_now = GPIO.input(self.clk_pin)
            dt_state_now = GPIO.input(self.dt_pin)
            
            # Si l'état est stable et différent du dernier état enregistré
            if (clk_state_now == self.clk_pending_state and 
                clk_state_now != self.last_clk_state):
                
                # Détection de la direction
                if dt_state_now != clk_state_now:
                    self.counter += 1
                    direction = "🔄 HORAIRE"
                else:
                    self.counter -= 1
                    direction = "🔄 ANTI-HORAIRE"
                
                print(f"{direction} | Compteur: {self.counter}")
                self.last_clk_state = clk_state_now
            
            # Réinitialiser l'anti-rebond
            self.clk_pending_state = None

    def check_button(self):
        """Vérifie l'état du bouton (polling + anti-rebond non-bloquant)"""
        if not self.is_running:
            return
            
        current_time = time.time()
        sw_state = GPIO.input(self.sw_pin)
        
        # Détection de l'appui (transition HIGH -> LOW)
        if sw_state == 0 and self.last_sw_state == 1:
            # Si pas de changement en attente, démarrer l'anti-rebond
            if self.sw_pending_state is None:
                self.sw_pending_state = 0
                self.sw_debounce_time = current_time
        
        # Détection du relâchement (transition LOW -> HIGH)
        elif sw_state == 1 and self.last_sw_state == 0:
            # Si pas de changement en attente, démarrer l'anti-rebond
            if self.sw_pending_state is None:
                self.sw_pending_state = 1
                self.sw_debounce_time = current_time
        
        # Vérifier si l'anti-rebond est terminé
        if (self.sw_pending_state is not None and 
            current_time - self.sw_debounce_time >= self.button_debounce_ms / 1000.0):
            
            # Relire l'état actuel pour vérifier la stabilité
            sw_state_now = GPIO.input(self.sw_pin)
            
            # Si l'état est stable et différent du dernier état enregistré
            if (sw_state_now == self.sw_pending_state and 
                sw_state_now != self.last_sw_state):
                
                if sw_state_now == 0:  # Appui confirmé
                    self.sw_pressed = True
                    self.sw_press_time = current_time
                    print("🔘 BOUTON APPUYÉ")
                elif sw_state_now == 1 and self.sw_pressed:  # Relâchement confirmé
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
                
                self.last_sw_state = sw_state_now
            
            # Réinitialiser l'anti-rebond
            self.sw_pending_state = None
    
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
                self.check_rotation()
                self.check_button()
                time.sleep(0.01)  # Polling à 100Hz
                
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
                self.check_button()
                if self.sw_pressed:
                    clics_detected += 1
                    print(f"   Clic {clics_detected}/{count} détecté")
                    # Attendre le relâchement
                    while self.sw_pressed:
                        self.check_button()
                        time.sleep(0.01)
                    time.sleep(0.1)  # Petite pause entre les clics
                time.sleep(0.01)
            
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
                self.check_rotation()
                self.check_button()
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring arrêté")
    
    def reset_debounce_states(self):
        """Réinitialise les états d'anti-rebond"""
        self.clk_pending_state = None
        self.sw_pending_state = None
        self.clk_debounce_time = 0
        self.sw_debounce_time = 0

    def adjust_debounce(self):
        """Ajuste les paramètres d'anti-rebond"""
        print("\n🔧 AJUSTEMENT ANTI-REBOND")
        print("=" * 40)
        print(f"Paramètres actuels:")
        print(f"  • Encodeur: {self.encoder_debounce_ms}ms")
        print(f"  • Bouton: {self.button_debounce_ms}ms")
        print()
        print("Valeurs recommandées:")
        print("  • Encodeur: 5-20ms (plus bas = plus sensible)")
        print("  • Bouton: 10-30ms (plus bas = plus sensible)")
        print()
        print("💡 Si problème de rebond persiste:")
        print("  • Augmentez les valeurs (plus stable)")
        print("  • Vérifiez les connexions")
        print("  • Testez avec option 4 (monitoring)")
        print()
        
        try:
            # Ajuster l'anti-rebond de l'encodeur
            new_encoder_ms = input(f"Anti-rebond encodeur en ms (actuel: {self.encoder_debounce_ms}): ").strip()
            if new_encoder_ms:
                self.encoder_debounce_ms = max(5, min(100, int(new_encoder_ms)))
                print(f"✅ Encodeur: {self.encoder_debounce_ms}ms")
            
            # Ajuster l'anti-rebond du bouton
            new_button_ms = input(f"Anti-rebond bouton en ms (actuel: {self.button_debounce_ms}): ").strip()
            if new_button_ms:
                self.button_debounce_ms = max(5, min(200, int(new_button_ms)))
                print(f"✅ Bouton: {self.button_debounce_ms}ms")
            
            # Réinitialiser les états d'anti-rebond
            self.reset_debounce_states()
            
            print(f"\n📊 Nouveaux paramètres:")
            print(f"  • Encodeur: {self.encoder_debounce_ms}ms")
            print(f"  • Bouton: {self.button_debounce_ms}ms")
            print("✅ États d'anti-rebond réinitialisés")
            print("Les nouveaux paramètres sont actifs immédiatement!")
            
        except ValueError:
            print("❌ Valeur invalide, paramètres inchangés")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    def diagnostic_debounce(self):
        """Diagnostic en temps réel de l'anti-rebond"""
        print("\n🔍 DIAGNOSTIC ANTI-REBOND")
        print("=" * 50)
        print("Affichage des états bruts et de l'anti-rebond")
        print("Appuyez sur Ctrl+C pour arrêter")
        print()
        
        # Réinitialiser les états
        self.reset_debounce_states()
        self.last_clk_state = GPIO.input(self.clk_pin)
        self.last_sw_state = GPIO.input(self.sw_pin)
        
        try:
            while True:
                current_time = time.time()
                clk_state = GPIO.input(self.clk_pin)
                dt_state = GPIO.input(self.dt_pin)
                sw_state = GPIO.input(self.sw_pin)
                
                # Affichage des états bruts
                clk_change = "🔴" if clk_state != self.last_clk_state else "⚪"
                dt_change = "🔴" if dt_state != self.last_dt_state else "⚪"
                sw_change = "🔴" if sw_state != self.last_sw_state else "⚪"
                
                # Affichage des états d'anti-rebond
                clk_pending = "⏳" if self.clk_pending_state is not None else "⚪"
                sw_pending = "⏳" if self.sw_pending_state is not None else "⚪"
                
                print(f"\rCLK:{clk_state}{clk_change} DT:{dt_state}{dt_change} SW:{sw_state}{sw_change} | "
                      f"CLK_P:{clk_pending} SW_P:{sw_pending} | C:{self.counter}", end="", flush=True)
                
                # Vérifier la rotation
                self.check_rotation()
                self.check_button()
                
                # Mettre à jour les états de référence
                self.last_dt_state = dt_state
                
                time.sleep(0.001)  # 1ms pour diagnostic précis
                
        except KeyboardInterrupt:
            print("\n🛑 Diagnostic arrêté")
        except Exception as e:
            print(f"\n❌ Erreur diagnostic: {e}")

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
    print("🔧 TEST ENCODEUR ROTATIF SIMPLE - Alimante")
    print("📍 Configuration basée sur config_alimante.py")
    print("📍 Mode polling (sans interruptions)")
    print("=" * 60)
    
    # Création du testeur
    encoder_test = EncoderTestSimple()
    
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
            print("7. Ajuster anti-rebond")
            print("8. Diagnostic anti-rebond")
            print("0. Quitter")
            print("=" * 40)
            
            choice = input("Votre choix (0-8): ").strip()
            
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
            elif choice == "7":
                encoder_test.adjust_debounce()
            elif choice == "8":
                encoder_test.diagnostic_debounce()
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
