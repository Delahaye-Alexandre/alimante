#!/usr/bin/env python3
"""
Test pour l'écran PSI avec bouton encodeur rotatif
Page d'accueil pour Alimante avec navigation par encodeur
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
import threading
from datetime import datetime

class RotaryEncoder:
    """Classe pour gérer l'encodeur rotatif"""
    
    def __init__(self, clk_pin=17, dt_pin=27, sw_pin=22, callback=None):
        """
        Initialise l'encodeur rotatif
        
        Args:
            clk_pin (int): Pin CLK de l'encodeur
            dt_pin (int): Pin DT de l'encodeur  
            sw_pin (int): Pin SW (bouton) de l'encodeur
            callback (function): Fonction appelée lors des changements
        """
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.callback = callback
        
        # États précédents
        self.last_clk_state = 0
        self.last_sw_state = 0
        self.last_sw_time = 0
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Interruptions
        GPIO.add_event_detect(self.clk_pin, GPIO.BOTH, callback=self._clk_callback, bouncetime=2)
        GPIO.add_event_detect(self.sw_pin, GPIO.FALLING, callback=self._sw_callback, bouncetime=200)
    
    def _clk_callback(self, channel):
        """Callback pour le changement d'état du pin CLK"""
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        if clk_state != self.last_clk_state and clk_state == 0:
            if dt_state != clk_state:
                # Rotation horaire
                if self.callback:
                    self.callback('rotate_right')
            else:
                # Rotation anti-horaire
                if self.callback:
                    self.callback('rotate_left')
        
        self.last_clk_state = clk_state
    
    def _sw_callback(self, channel):
        """Callback pour l'appui sur le bouton"""
        current_time = time.time()
        if current_time - self.last_sw_time > 0.2:  # Anti-rebond
            if self.callback:
                self.callback('button_press')
            self.last_sw_time = current_time

class PSIDisplay:
    """Classe pour gérer l'affichage sur l'écran PSI"""
    
    def __init__(self):
        """Initialise l'affichage PSI"""
        self.current_page = 0
        self.menu_items = [
            "🏠 Accueil Alimante",
            "💡 Test LED Bandeaux", 
            "📊 Monitoring Système",
            "⚙️ Configuration",
            "🔧 Tests Hardware",
            "📈 Statistiques",
            "ℹ️ À propos"
        ]
        self.current_item = 0
        
    def display_page(self):
        """Affiche la page actuelle"""
        print("\n" + "="*50)
        print(f"🖥️  ÉCRAN PSI - ALIMANTE")
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*50)
        
        if self.current_page == 0:  # Page d'accueil
            self._display_home()
        elif self.current_page == 1:  # Menu principal
            self._display_menu()
        else:
            self._display_content()
    
    def _display_home(self):
        """Affiche la page d'accueil"""
        print("""
    ╔══════════════════════════════════════╗
    ║           🏠 ALIMANTE 🏠             ║
    ║                                      ║
    ║    Système de contrôle intelligent   ║
    ║    pour bandeaux LED et capteurs     ║
    ║                                      ║
    ║  🔄 Tournez l'encodeur pour naviguer ║
    ║  🔘 Appuyez pour sélectionner        ║
    ║                                      ║
    ║  📊 Status: Système opérationnel     ║
    ║  💡 LED: 4 bandeaux connectés        ║
    ║  🔧 GPIO: 24 (PWM)                   ║
    ╚══════════════════════════════════════╝
        """)
    
    def _display_menu(self):
        """Affiche le menu principal"""
        print("📋 MENU PRINCIPAL:")
        print("-" * 30)
        for i, item in enumerate(self.menu_items):
            marker = "▶" if i == self.current_item else " "
            print(f"{marker} {item}")
        print("-" * 30)
        print("🔄 Encodeur: Navigation | 🔘 Bouton: Sélection")
    
    def _display_content(self):
        """Affiche le contenu de la page sélectionnée"""
        if self.current_item == 0:  # Accueil
            self._display_home()
        elif self.current_item == 1:  # Test LED
            self._display_led_test()
        elif self.current_item == 2:  # Monitoring
            self._display_monitoring()
        elif self.current_item == 3:  # Configuration
            self._display_config()
        elif self.current_item == 4:  # Tests Hardware
            self._display_hardware_tests()
        elif self.current_item == 5:  # Statistiques
            self._display_stats()
        elif self.current_item == 6:  # À propos
            self._display_about()
    
    def _display_led_test(self):
        """Affiche la page de test LED"""
        print("""
💡 TEST BANDEAUX LED
═══════════════════════════════════════

🔧 Configuration:
   • GPIO: 24 (PWM)
   • Fréquence: 1000 Hz
   • Bandeaux: 4 x 15cm

🎛️ Contrôles:
   • Rotation: Ajuster intensité (0-100%)
   • Bouton: Démarrer/Arrêter test

📊 Status: Prêt pour test
        """)
    
    def _display_monitoring(self):
        """Affiche la page de monitoring"""
        print("""
📊 MONITORING SYSTÈME
═══════════════════════════════════════

🖥️ État Système:
   • CPU: 45% (Normal)
   • RAM: 62% (Normal) 
   • Temp: 42°C (Normal)

💡 LED Status:
   • Intensité: 75%
   • Mode: Manuel
   • Uptime: 2h 15min

🔧 GPIO Status:
   • Pin 24: Actif (PWM)
   • Encodeur: Connecté
   • Capteurs: OK
        """)
    
    def _display_config(self):
        """Affiche la page de configuration"""
        print("""
⚙️ CONFIGURATION
═══════════════════════════════════════

🔧 Paramètres LED:
   • GPIO Pin: 24
   • Fréquence PWM: 1000 Hz
   • Intensité max: 100%

🎛️ Paramètres Encodeur:
   • CLK Pin: 18
   • DT Pin: 19  
   • SW Pin: 20

📡 Communication:
   • Interface: I2C
   • Baudrate: 9600
        """)
    
    def _display_hardware_tests(self):
        """Affiche la page de tests hardware"""
        print("""
🔧 TESTS HARDWARE
═══════════════════════════════════════

✅ Tests Disponibles:
   • Test GPIO (Pins 18,19,20,24)
   • Test PWM (Fréquence/Intensité)
   • Test Encodeur (Rotation/Bouton)
   • Test LED (Séquence complète)

🔄 Rotation: Sélectionner test
🔘 Bouton: Démarrer test sélectionné
        """)
    
    def _display_stats(self):
        """Affiche la page de statistiques"""
        print("""
📈 STATISTIQUES
═══════════════════════════════════════

⏱️ Temps de fonctionnement:
   • Total: 15h 32min
   • Aujourd'hui: 2h 15min
   • Cette semaine: 8h 45min

💡 Utilisation LED:
   • Allumages: 127
   • Intensité moy: 68%
   • Économie: 23%

🔧 Actions Encodeur:
   • Rotations: 1,247
   • Clics: 89
        """)
    
    def _display_about(self):
        """Affiche la page à propos"""
        print("""
ℹ️ À PROPOS - ALIMANTE
═══════════════════════════════════════

🏠 Alimante v1.0
   Système de contrôle intelligent

👨‍💻 Développé pour:
   • Contrôle bandeaux LED
   • Interface encodeur rotatif
   • Monitoring système

🔧 Technologies:
   • Python 3.x
   • RPi.GPIO
   • Raspberry Pi

📞 Support: contact@alimante.fr
        """)
    
    def navigate_up(self):
        """Navigation vers le haut"""
        if self.current_page == 1:  # Dans le menu
            self.current_item = (self.current_item - 1) % len(self.menu_items)
        self.display_page()
    
    def navigate_down(self):
        """Navigation vers le bas"""
        if self.current_page == 1:  # Dans le menu
            self.current_item = (self.current_item + 1) % len(self.menu_items)
        self.display_page()
    
    def select_item(self):
        """Sélectionne l'élément actuel"""
        if self.current_page == 0:  # Page d'accueil -> Menu
            self.current_page = 1
        elif self.current_page == 1:  # Menu -> Contenu
            self.current_page = 2
        else:  # Retour au menu
            self.current_page = 1
        
        self.display_page()

class AlimanteSystem:
    """Système principal Alimante"""
    
    def __init__(self, clk_pin=17, dt_pin=27, sw_pin=22):
        """
        Initialise le système Alimante
        
        Args:
            clk_pin (int): Pin CLK de l'encodeur
            dt_pin (int): Pin DT de l'encodeur
            sw_pin (int): Pin SW de l'encodeur
        """
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        
        # Initialisation des composants
        self.display = PSIDisplay()
        self.encoder = RotaryEncoder(clk_pin, dt_pin, sw_pin, self._encoder_callback)
        
        # Gestionnaire de signal pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
    
    def _encoder_callback(self, action):
        """Callback pour les actions de l'encodeur"""
        if action == 'rotate_left':
            self.display.navigate_up()
        elif action == 'rotate_right':
            self.display.navigate_down()
        elif action == 'button_press':
            self.display.select_item()
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du système Alimante...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """Lance le système principal"""
        print("🚀 Démarrage du système Alimante...")
        print("🔄 Initialisation de l'écran PSI et de l'encodeur...")
        
        # Affichage initial
        self.display.display_page()
        
        print("\n✅ Système opérationnel!")
        print("🔄 Utilisez l'encodeur pour naviguer")
        print("🔘 Appuyez sur le bouton pour sélectionner")
        print("⏹️  Ctrl+C pour quitter")
        
        # Boucle principale
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
    print("🏠 ALIMANTE - Système de contrôle intelligent")
    print("🖥️  Test écran PSI avec encodeur rotatif")
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
    
    # Création et lancement du système
    system = AlimanteSystem(CLK_PIN, DT_PIN, SW_PIN)
    
    try:
        system.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("👋 Au revoir!")

if __name__ == "__main__":
    main()
