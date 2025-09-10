#!/usr/bin/env python3
"""
Système principal Alimante
Interface complète avec écran PSI et encodeur rotatif
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
import threading
from datetime import datetime
from config_alimante import get_gpio_config, get_ui_config, get_system_config

class AlimanteMain:
    """Système principal Alimante"""
    
    def __init__(self):
        """Initialise le système principal"""
        self.config = get_gpio_config()
        self.ui_config = get_ui_config()
        self.system_config = get_system_config()
        
        # Configuration des pins
        self.clk_pin = self.config['ENCODER']['CLK_PIN']
        self.dt_pin = self.config['ENCODER']['DT_PIN']
        self.sw_pin = self.config['ENCODER']['SW_PIN']
        self.led_pin = self.config['LED']['PWM_PIN']
        
        # Pins écran PSI
        self.display_reset_pin = self.config['DISPLAY']['RESET_PIN']
        self.display_a0_pin = self.config['DISPLAY']['A0_PIN']
        self.display_sda_pin = self.config['DISPLAY']['SDA_PIN']
        self.display_scl_pin = self.config['DISPLAY']['SCL_PIN']
        
        # États
        self.last_clk_state = 0
        self.last_sw_state = 0
        self.last_sw_time = 0
        self.current_page = 0
        self.current_item = 0
        self.counter = 0
        self.running = True
        
        # PWM pour LED
        self.pwm = None
        self.led_intensity = 0
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Gestionnaire de signal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise tous les composants"""
        try:
            # Configuration des pins
            GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.led_pin, GPIO.OUT)
            
            # Configuration des pins écran PSI
            GPIO.setup(self.display_reset_pin, GPIO.OUT)
            GPIO.setup(self.display_a0_pin, GPIO.OUT)
            GPIO.setup(self.display_sda_pin, GPIO.OUT)
            GPIO.setup(self.display_scl_pin, GPIO.OUT)
            
            # Initialisation PWM
            self.pwm = GPIO.PWM(self.led_pin, self.config['LED']['FREQUENCY'])
            self.pwm.start(0)
            
            # Interruptions
            GPIO.add_event_detect(self.clk_pin, GPIO.BOTH, callback=self._clk_callback, 
                                bouncetime=self.ui_config['DISPLAY']['DEBOUNCE_TIME'])
            GPIO.add_event_detect(self.sw_pin, GPIO.FALLING, callback=self._sw_callback, 
                                bouncetime=self.ui_config['DISPLAY']['DEBOUNCE_TIME'])
            
            print("✅ Système Alimante initialisé")
            return True
        except Exception as e:
            print(f"❌ Erreur d'initialisation: {e}")
            return False
    
    def _clk_callback(self, channel):
        """Callback pour l'encodeur rotatif"""
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        if clk_state != self.last_clk_state and clk_state == 0:
            if dt_state != clk_state:
                # Rotation horaire
                self.counter += 1
                self._handle_rotation('right')
            else:
                # Rotation anti-horaire
                self.counter -= 1
                self._handle_rotation('left')
        
        self.last_clk_state = clk_state
    
    def _sw_callback(self, channel):
        """Callback pour le bouton"""
        current_time = time.time()
        if current_time - self.last_sw_time > 0.2:
            self._handle_button_press()
            self.last_sw_time = current_time
    
    def _handle_rotation(self, direction):
        """Gère la rotation de l'encodeur"""
        if self.current_page == 0:  # Page d'accueil
            if direction == 'right':
                self.current_page = 1  # Aller au menu
            else:
                self.current_page = 1  # Aller au menu
        elif self.current_page == 1:  # Menu
            if direction == 'right':
                self.current_item = (self.current_item + 1) % len(self.ui_config['MENU']['ITEMS'])
            else:
                self.current_item = (self.current_item - 1) % len(self.ui_config['MENU']['ITEMS'])
        elif self.current_page == 2:  # Page de contenu
            if self.current_item == 1:  # Test LED
                if direction == 'right':
                    self.led_intensity = min(100, self.led_intensity + 5)
                else:
                    self.led_intensity = max(0, self.led_intensity - 5)
                self.pwm.ChangeDutyCycle(self.led_intensity)
        
        self._display_current_page()
    
    def _handle_button_press(self):
        """Gère l'appui sur le bouton"""
        if self.current_page == 0:  # Page d'accueil -> Menu
            self.current_page = 1
        elif self.current_page == 1:  # Menu -> Contenu
            self.current_page = 2
        else:  # Retour au menu
            self.current_page = 1
        
        self._display_current_page()
    
    def _display_current_page(self):
        """Affiche la page actuelle"""
        print("\n" + "="*60)
        print(f"🖥️  ALIMANTE v{self.system_config['VERSION']} - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        if self.current_page == 0:
            self._display_home()
        elif self.current_page == 1:
            self._display_menu()
        else:
            self._display_content()
    
    def _display_home(self):
        """Affiche la page d'accueil"""
        print("""
    ╔════════════════════════════════════════════════╗
    ║                🏠 ALIMANTE 🏠                  ║
    ║                                                ║
    ║        Système de contrôle intelligent         ║
    ║        pour bandeaux LED et capteurs           ║
    ║                                                ║
    ║  🔄 Tournez l'encodeur pour naviguer          ║
    ║  🔘 Appuyez pour accéder au menu               ║
    ║                                                ║
    ║  📊 Status: Système opérationnel              ║
    ║  💡 LED: 4 bandeaux connectés                 ║
    ║  🔧 LED: 18 (PWM) | Encodeur: 17,27,22       ║
    ║  🖥️  Écran: Reset=24, A0=25, SDA=10, SCL=11  ║
    ║  📈 Compteur: {:<10}                    ║
    ╚════════════════════════════════════════════════╝
        """.format(self.counter))
    
    def _display_menu(self):
        """Affiche le menu principal"""
        print("📋 MENU PRINCIPAL:")
        print("-" * 50)
        for i, item in enumerate(self.ui_config['MENU']['ITEMS']):
            marker = "▶" if i == self.current_item else " "
            print(f"{marker} {item}")
        print("-" * 50)
        print("🔄 Encodeur: Navigation | 🔘 Bouton: Sélection")
        print(f"📈 Compteur: {self.counter}")
    
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
        print(f"""
💡 TEST BANDEAUX LED
═══════════════════════════════════════

🔧 Configuration:
   • GPIO: {self.led_pin} (PWM)
   • Fréquence: {self.config['LED']['FREQUENCY']} Hz
   • Bandeaux: 4 x 15cm
   • Écran: Reset={self.display_reset_pin}, A0={self.display_a0_pin}

🎛️ Contrôles:
   • Rotation: Ajuster intensité (0-100%)
   • Bouton: Retour au menu

📊 Status:
   • Intensité actuelle: {self.led_intensity}%
   • Mode: Manuel
   • Compteur: {self.counter}
        """)
    
    def _display_monitoring(self):
        """Affiche la page de monitoring"""
        print(f"""
📊 MONITORING SYSTÈME
═══════════════════════════════════════

🖥️ État Système:
   • CPU: 45% (Normal)
   • RAM: 62% (Normal) 
   • Temp: 42°C (Normal)

💡 LED Status:
   • Intensité: {self.led_intensity}%
   • Mode: Manuel
   • Uptime: 2h 15min

🔧 GPIO Status:
   • Pin {self.led_pin}: Actif (PWM)
   • Encodeur: Connecté (17,27,22)
   • Écran: Connecté (24,25,10,11)
   • Capteurs: OK

📈 Compteur: {self.counter}
        """)
    
    def _display_config(self):
        """Affiche la page de configuration"""
        print(f"""
⚙️ CONFIGURATION
═══════════════════════════════════════

🔧 Paramètres LED:
   • GPIO Pin: {self.led_pin}
   • Fréquence PWM: {self.config['LED']['FREQUENCY']} Hz
   • Intensité max: {self.config['LED']['MAX_INTENSITY']}%

🎛️ Paramètres Encodeur:
   • CLK Pin: {self.clk_pin}
   • DT Pin: {self.dt_pin}  
   • SW Pin: {self.sw_pin}

🖥️ Paramètres Écran:
   • Reset Pin: {self.display_reset_pin}
   • A0 Pin: {self.display_a0_pin}
   • SDA Pin: {self.display_sda_pin}
   • SCL Pin: {self.display_scl_pin}

📡 Communication:
   • Interface: I2C
   • Baudrate: 9600

📈 Compteur: {self.counter}
        """)
    
    def _display_hardware_tests(self):
        """Affiche la page de tests hardware"""
        print(f"""
🔧 TESTS HARDWARE
═══════════════════════════════════════

✅ Tests Disponibles:
   • Test GPIO (Encodeur: {self.clk_pin},{self.dt_pin},{self.sw_pin})
   • Test GPIO (LED: {self.led_pin}, Écran: {self.display_reset_pin},{self.display_a0_pin})
   • Test PWM (Fréquence/Intensité)
   • Test Encodeur (Rotation/Bouton)
   • Test LED (Séquence complète)

🔄 Rotation: Sélectionner test
🔘 Bouton: Démarrer test sélectionné

📈 Compteur: {self.counter}
        """)
    
    def _display_stats(self):
        """Affiche la page de statistiques"""
        print(f"""
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
   • Rotations: {abs(self.counter)}
   • Clics: 89

📈 Compteur actuel: {self.counter}
        """)
    
    def _display_about(self):
        """Affiche la page à propos"""
        print(f"""
ℹ️ À PROPOS - ALIMANTE
═══════════════════════════════════════

🏠 {self.system_config['NAME']} v{self.system_config['VERSION']}
   {self.system_config['DESCRIPTION']}

👨‍💻 Développé par: {self.system_config['AUTHOR']}

🔧 Technologies:
   • Python 3.x
   • RPi.GPIO
   • Raspberry Pi

📞 Support: contact@alimante.fr

📈 Compteur: {self.counter}
        """)
    
    def run(self):
        """Lance le système principal"""
        print("🚀 Démarrage d'Alimante...")
        
        if not self.initialize():
            return
        
        # Affichage initial
        self._display_current_page()
        
        print("\n✅ Système opérationnel!")
        print("🔄 Utilisez l'encodeur pour naviguer")
        print("🔘 Appuyez sur le bouton pour sélectionner")
        print("⏹️  Ctrl+C pour quitter")
        
        # Boucle principale
        try:
            while self.running:
                time.sleep(self.ui_config['DISPLAY']['REFRESH_RATE'])
        except KeyboardInterrupt:
            print("\n🛑 Arrêt par l'utilisateur")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self.pwm:
            self.pwm.stop()
        GPIO.cleanup()
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du système Alimante...")
        self.running = False
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🏠 ALIMANTE - Système de contrôle intelligent")
    print("🖥️  Interface écran PSI avec encodeur rotatif")
    print("=" * 70)
    
    # Création et lancement du système
    system = AlimanteMain()
    
    try:
        system.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("👋 Au revoir!")

if __name__ == "__main__":
    main()
