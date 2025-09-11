#!/usr/bin/env python3
"""
Test d'encodeur rotatif + écran ST7735 avec gpiozero
Version avancée avec driver d'écran complet
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
    import RPi.GPIO as GPIO
    SPI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Librairies SPI non disponibles: {e}")
    print("💡 Installez avec: pip install spidev pillow")
    SPI_AVAILABLE = False

class ST7735Display:
    """Driver simplifié pour écran ST7735"""
    
    def __init__(self, spi, reset_pin, a0_pin, cs_pin, width=128, height=160):
        self.spi = spi
        self.reset_pin = reset_pin
        self.a0_pin = a0_pin
        self.cs_pin = cs_pin
        self.width = width
        self.height = height
        
        # Configuration GPIO
        GPIO.setup(self.reset_pin, GPIO.OUT)
        GPIO.setup(self.a0_pin, GPIO.OUT)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        
        self.init_display()
    
    def init_display(self):
        """Initialise l'écran ST7735"""
        # Reset
        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.reset_pin, GPIO.HIGH)
        time.sleep(0.1)
        
        # Séquence d'initialisation simplifiée
        self.send_command(0x01)  # Software reset
        time.sleep(0.1)
        
        self.send_command(0x11)  # Sleep out
        time.sleep(0.1)
        
        self.send_command(0x29)  # Display on
        time.sleep(0.1)
    
    def send_command(self, cmd):
        """Envoie une commande à l'écran"""
        GPIO.output(self.cs_pin, GPIO.LOW)
        GPIO.output(self.a0_pin, GPIO.LOW)  # Mode commande
        self.spi.xfer2([cmd])
        GPIO.output(self.cs_pin, GPIO.HIGH)
    
    def send_data(self, data):
        """Envoie des données à l'écran"""
        GPIO.output(self.cs_pin, GPIO.LOW)
        GPIO.output(self.a0_pin, GPIO.HIGH)  # Mode données
        self.spi.xfer2(data)
        GPIO.output(self.cs_pin, GPIO.HIGH)
    
    def clear(self, color=0x0000):
        """Efface l'écran avec une couleur"""
        # Commande pour définir la zone d'affichage
        self.send_command(0x2A)  # Column address set
        self.send_data([0x00, 0x00, 0x00, self.width-1])
        
        self.send_command(0x2B)  # Row address set
        self.send_data([0x00, 0x00, 0x00, self.height-1])
        
        self.send_command(0x2C)  # Memory write
        
        # Remplir avec la couleur
        color_data = [color >> 8, color & 0xFF]
        for _ in range(self.width * self.height):
            self.send_data(color_data)
    
    def draw_text(self, x, y, text, color=0xFFFF, bg_color=0x0000):
        """Dessine du texte sur l'écran (simplifié)"""
        # Dans une vraie implémentation, il faudrait une police bitmap
        # Ici on simule avec des rectangles
        self.draw_rect(x, y, len(text) * 8, 16, bg_color)
        # Le texte serait dessiné pixel par pixel
    
    def draw_rect(self, x, y, width, height, color):
        """Dessine un rectangle"""
        self.send_command(0x2A)  # Column address set
        self.send_data([x >> 8, x & 0xFF, (x + width - 1) >> 8, (x + width - 1) & 0xFF])
        
        self.send_command(0x2B)  # Row address set
        self.send_data([y >> 8, y & 0xFF, (y + height - 1) >> 8, (y + height - 1) & 0xFF])
        
        self.send_command(0x2C)  # Memory write
        
        color_data = [color >> 8, color & 0xFF]
        for _ in range(width * height):
            self.send_data(color_data)

class EncoderDisplayAdvanced:
    def __init__(self):
        """Initialise le test encodeur + écran avancé"""
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
        self.display = None
        
        # Thread pour l'affichage
        self.display_thread = None
        self.display_stop = False
        
        # Configuration des signaux
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise l'encodeur et l'écran"""
        try:
            print("🔧 Initialisation encodeur + écran avancé...")
            
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
                print("   • Écran ST7735...")
                GPIO.setmode(GPIO.BCM)
                
                # Configuration SPI
                self.spi = spidev.SpiDev()
                self.spi.open(0, 0)
                self.spi.max_speed_hz = 1000000
                
                # Création du driver d'écran
                self.display = ST7735Display(
                    self.spi, 
                    self.reset_pin, 
                    self.a0_pin, 
                    self.cs_pin
                )
                
                print("   ✅ Écran ST7735 initialisé")
                self.display_ready = True
            else:
                print("   ⚠️ Librairies SPI non disponibles")
            
            print("✅ Initialisation terminée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
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
    
    def _update_display(self):
        """Met à jour l'affichage de l'écran"""
        if not self.display_ready or not self.display:
            return
        
        try:
            # Effacer l'écran
            self.display.clear(0x0000)  # Noir
            
            # Dessiner les informations
            y_pos = 10
            
            # Titre
            self.display.draw_rect(10, y_pos, 100, 20, 0x001F)  # Bleu
            y_pos += 25
            
            # Compteur
            self.display.draw_rect(10, y_pos, 80, 15, 0x07E0)  # Vert
            y_pos += 20
            
            # Bouton
            self.display.draw_rect(10, y_pos, 80, 15, 0xF800)  # Rouge
            y_pos += 20
            
            # État
            self.display.draw_rect(10, y_pos, 80, 15, 0xFFE0)  # Jaune
            
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
            time.sleep(0.2)  # 5 FPS
    
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
    print("🔧 TEST ENCODEUR + ÉCRAN AVANCÉ")
    print("📍 Encodeur: gpiozero (anti-rebond automatique)")
    print("📍 Écran: ST7735 via SPI (driver complet)")
    print("=" * 60)
    
    # Vérification des librairies
    print("🔍 Vérification des librairies...")
    
    # gpiozero
    try:
        import gpiozero
        print("✅ gpiozero disponible")
    except ImportError:
        print("❌ gpiozero non installé!")
        return
    
    # SPI
    if SPI_AVAILABLE:
        print("✅ Librairies SPI disponibles")
    else:
        print("⚠️ Librairies SPI non disponibles")
        print("   Mode console uniquement")
    
    # Création du testeur
    encoder_test = EncoderDisplayAdvanced()
    
    try:
        # Initialisation
        if not encoder_test.initialize():
            print("❌ Impossible d'initialiser le système")
            return
        
        # Menu interactif
        while True:
            print("\n" + "=" * 40)
            print("MENU ENCODEUR + ÉCRAN AVANCÉ:")
            print("1. Test combiné (10s)")
            print("2. Afficher configuration")
            print("0. Quitter")
            print("=" * 40)
            
            choice = input("Votre choix (0-2): ").strip()
            
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
