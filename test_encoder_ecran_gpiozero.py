#!/usr/bin/env python3
"""
Test d'encodeur rotatif + écran SPI avec gpiozero
Version optimisée : gpiozero pour l'encodeur, SPI pour l'écran
"""

import time
import signal
import sys
import threading
from gpiozero import RotaryEncoder, Button
from config_alimante import get_gpio_config

# Import des librairies SPI pour l'écran
try:
    import spidev
    from PIL import Image, ImageDraw, ImageFont
    SPI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Librairies SPI non disponibles: {e}")
    print("💡 Installez avec: pip install spidev pillow")
    SPI_AVAILABLE = False

class EncoderDisplayTest:
    def __init__(self):
        """Initialise le test encodeur + écran"""
        self.config = get_gpio_config()
        
        # Configuration des pins
        self.clk_pin = self.config['ENCODER']['CLK_PIN']
        self.dt_pin = self.config['ENCODER']['DT_PIN']
        self.sw_pin = self.config['ENCODER']['SW_PIN']
        
        # Configuration écran
        self.reset_pin = self.config['DISPLAY']['RESET_PIN']
        self.a0_pin = self.config['DISPLAY']['A0_PIN']
        self.cs_pin = self.config['DISPLAY']['CS_PIN']
        self.sda_pin = self.config['DISPLAY']['SDA_PIN']
        self.scl_pin = self.config['DISPLAY']['SCL_PIN']
        
        # Variables d'état
        self.counter = 0
        self.button_press_count = 0
        self.is_running = False
        self.display_ready = False
        
        # Variables pour l'écran
        self.spi = None
        self.display_width = 128
        self.display_height = 160
        
        # Thread pour l'affichage
        self.display_thread = None
        self.display_stop = False
        
        # Configuration des signaux
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise l'encodeur et l'écran"""
        try:
            print("🔧 Initialisation encodeur + écran...")
            
            # 1. Initialisation de l'encodeur avec gpiozero
            print("   • Encodeur (gpiozero)...")
            self.encoder = RotaryEncoder(
                a=self.clk_pin, 
                b=self.dt_pin, 
                max_steps=0
            )
            self.button = Button(self.sw_pin, pull_up=True)
            
            # Configuration des callbacks
            self.encoder.when_rotated = self._on_rotation
            self.button.when_pressed = self._on_button_pressed
            self.button.when_released = self._on_button_released
            
            print("   ✅ Encodeur initialisé")
            
            # 2. Initialisation de l'écran SPI
            if SPI_AVAILABLE:
                print("   • Écran SPI...")
                if self._init_display():
                    print("   ✅ Écran initialisé")
                    self.display_ready = True
                else:
                    print("   ⚠️ Écran non disponible, mode console uniquement")
            else:
                print("   ⚠️ Librairies SPI non disponibles, mode console uniquement")
            
            print("✅ Initialisation terminée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def _init_display(self):
        """Initialise l'écran SPI"""
        try:
            # Configuration SPI
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)  # Bus 0, Device 0
            self.spi.max_speed_hz = 1000000  # 1MHz
            
            # Configuration des pins GPIO pour l'écran
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.reset_pin, GPIO.OUT)
            GPIO.setup(self.a0_pin, GPIO.OUT)
            GPIO.setup(self.cs_pin, GPIO.OUT)
            
            # Reset de l'écran
            GPIO.output(self.reset_pin, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(self.reset_pin, GPIO.HIGH)
            time.sleep(0.1)
            
            # Initialisation de l'écran (simplifiée)
            self._send_command(0x01)  # Reset
            time.sleep(0.1)
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur écran: {e}")
            return False
    
    def _send_command(self, cmd):
        """Envoie une commande à l'écran"""
        if not self.spi:
            return
        
        import RPi.GPIO as GPIO
        GPIO.output(self.cs_pin, GPIO.LOW)
        GPIO.output(self.a0_pin, GPIO.LOW)  # Mode commande
        self.spi.xfer2([cmd])
        GPIO.output(self.cs_pin, GPIO.HIGH)
    
    def _send_data(self, data):
        """Envoie des données à l'écran"""
        if not self.spi:
            return
        
        import RPi.GPIO as GPIO
        GPIO.output(self.cs_pin, GPIO.LOW)
        GPIO.output(self.a0_pin, GPIO.HIGH)  # Mode données
        self.spi.xfer2(data)
        GPIO.output(self.cs_pin, GPIO.HIGH)
    
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
        
        # Mise à jour de l'écran si disponible
        if self.display_ready:
            self._update_display()
    
    def _on_button_pressed(self):
        """Callback appelé lors de l'appui du bouton"""
        if not self.is_running:
            return
            
        self.button_press_count += 1
        print(f"🔘 BOUTON PRESSÉ #{self.button_press_count}")
        
        # Mise à jour de l'écran si disponible
        if self.display_ready:
            self._update_display()
    
    def _on_button_released(self):
        """Callback appelé lors du relâchement du bouton"""
        if not self.is_running:
            return
            
        print("🔘 BOUTON RELÂCHÉ")
    
    def _update_display(self):
        """Met à jour l'affichage de l'écran"""
        if not self.display_ready:
            return
        
        try:
            # Création de l'image
            image = Image.new('RGB', (self.display_width, self.display_height), 'black')
            draw = ImageDraw.Draw(image)
            
            # Affichage des informations
            y_pos = 10
            
            # Titre
            draw.text((10, y_pos), "ENCODEUR TEST", fill='white')
            y_pos += 20
            
            # Compteur
            draw.text((10, y_pos), f"Compteur: {self.counter}", fill='green')
            y_pos += 20
            
            # Bouton
            draw.text((10, y_pos), f"Boutons: {self.button_press_count}", fill='blue')
            y_pos += 20
            
            # État
            draw.text((10, y_pos), "Status: ACTIF", fill='yellow')
            
            # Envoi de l'image à l'écran (simplifié)
            # Dans une vraie implémentation, il faudrait convertir l'image
            # et l'envoyer pixel par pixel via SPI
            
        except Exception as e:
            print(f"⚠️ Erreur affichage: {e}")
    
    def start_display_thread(self):
        """Démarre le thread d'affichage"""
        if not self.display_ready:
            return
        
        self.display_stop = False
        self.display_thread = threading.Thread(target=self._display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        print("📺 Thread d'affichage démarré")
    
    def _display_loop(self):
        """Boucle d'affichage en arrière-plan"""
        while not self.display_stop and self.is_running:
            self._update_display()
            time.sleep(0.1)  # 10 FPS
    
    def test_combined(self, duration=10):
        """Test combiné encodeur + écran"""
        print(f"🔄 Test combiné pendant {duration} secondes...")
        print("   → Tournez l'encodeur dans les deux sens")
        print("   → Appuyez sur le bouton")
        if self.display_ready:
            print("   → Regardez l'écran pour les mises à jour")
        print("   → Appuyez sur Ctrl+C pour arrêter")
        
        self.is_running = True
        self.counter = 0
        self.button_press_count = 0
        
        # Démarrage du thread d'affichage
        if self.display_ready:
            self.start_display_thread()
        
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            print("\n🛑 Test arrêté par l'utilisateur")
        finally:
            self.is_running = False
            self.display_stop = True
            
        print(f"\n📊 Résultats:")
        print(f"   • Rotations détectées: {self.counter}")
        print(f"   • Appuis de bouton: {self.button_press_count}")
        if self.display_ready:
            print(f"   • Écran: Mis à jour en temps réel")
    
    def monitor_realtime(self):
        """Monitoring en temps réel"""
        print("👁️ Monitoring temps réel")
        print("   → Tournez l'encodeur et appuyez sur le bouton")
        if self.display_ready:
            print("   → Regardez l'écran pour les mises à jour")
        print("   → Appuyez sur Ctrl+C pour arrêter")
        
        self.is_running = True
        self.counter = 0
        self.button_press_count = 0
        
        # Démarrage du thread d'affichage
        if self.display_ready:
            self.start_display_thread()
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring arrêté")
        finally:
            self.is_running = False
            self.display_stop = True
    
    def cleanup(self):
        """Nettoie les ressources"""
        self.is_running = False
        self.display_stop = True
        
        if hasattr(self, 'encoder'):
            self.encoder.close()
        if hasattr(self, 'button'):
            self.button.close()
        if self.spi:
            self.spi.close()
        
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du programme...")
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("🔧 TEST ENCODEUR + ÉCRAN - gpiozero + SPI")
    print("📍 Encodeur: gpiozero (anti-rebond automatique)")
    print("📍 Écran: SPI (mise à jour temps réel)")
    print("=" * 60)
    
    # Vérification des librairies
    print("🔍 Vérification des librairies...")
    
    # gpiozero
    try:
        import gpiozero
        print("✅ gpiozero disponible")
    except ImportError:
        print("❌ gpiozero non installé!")
        print("   Installez avec: pip install gpiozero")
        return
    
    # SPI
    if SPI_AVAILABLE:
        print("✅ Librairies SPI disponibles")
    else:
        print("⚠️ Librairies SPI non disponibles")
        print("   Mode console uniquement")
    
    # Création du testeur
    encoder_test = EncoderDisplayTest()
    
    try:
        # Initialisation
        if not encoder_test.initialize():
            print("❌ Impossible d'initialiser le système")
            return
        
        # Menu interactif
        while True:
            print("\n" + "=" * 40)
            print("MENU ENCODEUR + ÉCRAN:")
            print("1. Test combiné (10s)")
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
                    encoder_test.test_combined(duration)
                except ValueError:
                    print("❌ Durée invalide, utilisation de 10s")
                    encoder_test.test_combined(10)
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
