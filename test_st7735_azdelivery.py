#!/usr/bin/env python3
"""
Test spécifique pour l'écran ST7735 d'AZdelivery
Écran TFT couleur 1.8" avec interface SPI
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
import spidev
from datetime import datetime

class ST7735Test:
    """Test pour l'écran ST7735 d'AZdelivery"""
    
    def __init__(self, reset_pin=24, a0_pin=25, cs_pin=8, spi_bus=0, spi_device=0):
        """
        Initialise le test pour ST7735
        
        Args:
            reset_pin (int): Pin Reset de l'écran
            a0_pin (int): Pin A0/DC de l'écran
            cs_pin (int): Pin CS (Chip Select) de l'écran
            spi_bus (int): Bus SPI (généralement 0)
            spi_device (int): Device SPI (généralement 0)
        """
        self.reset_pin = reset_pin
        self.a0_pin = a0_pin
        self.cs_pin = cs_pin
        self.spi_bus = spi_bus
        self.spi_device = spi_device
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Interface SPI
        self.spi = None
        
        # Gestionnaire de signal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise l'interface SPI et les pins"""
        try:
            # Configuration des pins
            GPIO.setup(self.reset_pin, GPIO.OUT)
            GPIO.setup(self.a0_pin, GPIO.OUT)
            GPIO.setup(self.cs_pin, GPIO.OUT)
            
            # État initial
            GPIO.output(self.reset_pin, GPIO.HIGH)  # Reset actif bas
            GPIO.output(self.a0_pin, GPIO.LOW)      # A0 bas (mode commande)
            GPIO.output(self.cs_pin, GPIO.HIGH)     # CS actif bas
            
            # Initialisation SPI
            self.spi = spidev.SpiDev()
            self.spi.open(self.spi_bus, self.spi_device)
            
            # Configuration SPI pour ST7735
            self.spi.max_speed_hz = 8000000  # 8 MHz (max pour ST7735)
            self.spi.mode = 0  # Mode SPI 0
            
            print("✅ Interface SPI initialisée pour ST7735")
            print(f"   • Reset Pin: {self.reset_pin}")
            print(f"   • A0/DC Pin: {self.a0_pin}")
            print(f"   • CS Pin: {self.cs_pin}")
            print(f"   • Bus: {self.spi_bus}")
            print(f"   • Device: {self.spi_device}")
            print(f"   • Vitesse: {self.spi.max_speed_hz} Hz")
            print(f"   • Mode: {self.spi.mode}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation SPI: {e}")
            return False
    
    def reset_display(self):
        """Reset de l'écran ST7735"""
        print("🔄 Reset de l'écran ST7735...")
        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self.reset_pin, GPIO.HIGH)
        time.sleep(0.12)  # Attendre 120ms après reset
        print("✅ Reset terminé")
    
    def send_command(self, command):
        """Envoie une commande à l'écran"""
        GPIO.output(self.cs_pin, GPIO.LOW)   # Sélectionner l'écran
        GPIO.output(self.a0_pin, GPIO.LOW)   # Mode commande
        self.spi.xfer2([command])
        GPIO.output(self.cs_pin, GPIO.HIGH)  # Désélectionner l'écran
        time.sleep(0.001)
    
    def send_data(self, data):
        """Envoie des données à l'écran"""
        GPIO.output(self.cs_pin, GPIO.LOW)   # Sélectionner l'écran
        GPIO.output(self.a0_pin, GPIO.HIGH)  # Mode données
        if isinstance(data, list):
            self.spi.xfer2(data)
        else:
            self.spi.xfer2([data])
        GPIO.output(self.cs_pin, GPIO.HIGH)  # Désélectionner l'écran
        time.sleep(0.001)
    
    def init_st7735(self):
        """Initialise l'écran ST7735 avec les bonnes commandes"""
        print("🔄 Initialisation ST7735...")
        
        try:
            # Séquence d'initialisation ST7735
            init_commands = [
                # Software Reset
                (0x01, []),
                # Sleep Out
                (0x11, []),
                # Frame Rate Control
                (0xB1, [0x01, 0x2C, 0x2D]),
                # Frame Rate Control
                (0xB2, [0x01, 0x2C, 0x2D]),
                # Frame Rate Control
                (0xB3, [0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D]),
                # Display Inversion Control
                (0xB4, [0x07]),
                # Power Control 1
                (0xC0, [0xA2, 0x02, 0x84]),
                # Power Control 2
                (0xC1, [0xC5]),
                # Power Control 3
                (0xC2, [0x0A, 0x00]),
                # Power Control 4
                (0xC3, [0x8A, 0x2A]),
                # Power Control 5
                (0xC4, [0x8A, 0xEE]),
                # VCOM Control
                (0xC5, [0x0E]),
                # Memory Access Control
                (0x36, [0xC8]),
                # Column Address Set
                (0x2A, [0x00, 0x01, 0x00, 0x80]),
                # Row Address Set
                (0x2B, [0x00, 0x02, 0x00, 0x80]),
                # Gamma Set
                (0x26, [0x01]),
                # Positive Gamma Correction
                (0xE0, [0x0F, 0x1A, 0x0F, 0x18, 0x2F, 0x28, 0x20, 0x22, 0x1F, 0x1B, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10]),
                # Negative Gamma Correction
                (0xE1, [0x0F, 0x1B, 0x0F, 0x17, 0x33, 0x2C, 0x29, 0x2E, 0x30, 0x30, 0x39, 0x3F, 0x00, 0x07, 0x03, 0x10]),
                # Display On
                (0x29, []),
                # Memory Write
                (0x2C, [])
            ]
            
            for cmd, data in init_commands:
                print(f"   Commande: 0x{cmd:02X}, Données: {len(data)} bytes")
                self.send_command(cmd)
                if data:
                    self.send_data(data)
                time.sleep(0.01)
            
            print("✅ Initialisation ST7735 terminée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False
    
    def clear_screen(self, color=0x0000):
        """Efface l'écran avec une couleur"""
        print(f"🔄 Effacement écran couleur: 0x{color:04X}")
        
        try:
            # Set Column Address
            self.send_command(0x2A)
            self.send_data([0x00, 0x00, 0x00, 0x9F])  # 0-159
            
            # Set Row Address
            self.send_command(0x2B)
            self.send_data([0x00, 0x00, 0x00, 0x9F])  # 0-159
            
            # Memory Write
            self.send_command(0x2C)
            
            # Envoyer la couleur pour tous les pixels (160x128 = 20480 pixels)
            color_bytes = [(color >> 8) & 0xFF, color & 0xFF]
            for i in range(160 * 128):
                self.send_data(color_bytes)
            
            print("✅ Écran effacé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur effacement: {e}")
            return False
    
    def test_colors(self):
        """Test des couleurs de base"""
        print("🔄 Test des couleurs...")
        
        colors = [
            (0x0000, "Noir"),
            (0xFFFF, "Blanc"),
            (0xF800, "Rouge"),
            (0x07E0, "Vert"),
            (0x001F, "Bleu"),
            (0xFFE0, "Jaune"),
            (0xF81F, "Magenta"),
            (0x07FF, "Cyan")
        ]
        
        try:
            for color, name in colors:
                print(f"   Couleur: {name} (0x{color:04X})")
                self.clear_screen(color)
                time.sleep(1)
            
            print("✅ Test des couleurs terminé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur test couleurs: {e}")
            return False
    
    def test_patterns(self):
        """Test de motifs"""
        print("🔄 Test de motifs...")
        
        try:
            # Motif rayures verticales
            print("   Rayures verticales...")
            for x in range(0, 160, 10):
                color = 0xF800 if (x // 10) % 2 == 0 else 0x0000
                self.send_command(0x2A)  # Column Address
                self.send_data([x >> 8, x & 0xFF, (x + 9) >> 8, (x + 9) & 0xFF])
                self.send_command(0x2B)  # Row Address
                self.send_data([0x00, 0x00, 0x00, 0x9F])
                self.send_command(0x2C)  # Memory Write
                
                color_bytes = [(color >> 8) & 0xFF, color & 0xFF]
                for y in range(128):
                    for w in range(10):
                        self.send_data(color_bytes)
            
            time.sleep(2)
            
            # Motif rayures horizontales
            print("   Rayures horizontales...")
            for y in range(0, 128, 10):
                color = 0x07E0 if (y // 10) % 2 == 0 else 0x0000
                self.send_command(0x2A)  # Column Address
                self.send_data([0x00, 0x00, 0x00, 0x9F])
                self.send_command(0x2B)  # Row Address
                self.send_data([y >> 8, y & 0xFF, (y + 9) >> 8, (y + 9) & 0xFF])
                self.send_command(0x2C)  # Memory Write
                
                color_bytes = [(color >> 8) & 0xFF, color & 0xFF]
                for x in range(160):
                    for h in range(10):
                        self.send_data(color_bytes)
            
            print("✅ Test de motifs terminé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur test motifs: {e}")
            return False
    
    def run_complete_test(self):
        """Lance le test complet"""
        print("🚀 Démarrage du test ST7735 AZdelivery...")
        
        if not self.initialize():
            return
        
        print("\n" + "="*60)
        print("🖥️  TEST ST7735 AZDELIVERY - ALIMANTE")
        print("="*60)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔌 Reset Pin: {self.reset_pin}")
        print(f"🔌 A0/DC Pin: {self.a0_pin}")
        print(f"🔌 CS Pin: {self.cs_pin}")
        print(f"🔌 SPI Bus: {self.spi_bus}, Device: {self.spi_device}")
        print("="*60)
        
        try:
            while True:
                print("\n🎛️  MENU DE TEST ST7735:")
                print("1. Reset de l'écran")
                print("2. Initialisation ST7735")
                print("3. Effacer écran (noir)")
                print("4. Test des couleurs")
                print("5. Test de motifs")
                print("6. Test complet")
                print("0. Quitter")
                
                choice = input("\nVotre choix (0-6): ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    self.reset_display()
                elif choice == "2":
                    self.init_st7735()
                elif choice == "3":
                    self.clear_screen(0x0000)
                elif choice == "4":
                    self.test_colors()
                elif choice == "5":
                    self.test_patterns()
                elif choice == "6":
                    print("🔄 Test complet en cours...")
                    self.reset_display()
                    time.sleep(1)
                    self.init_st7735()
                    time.sleep(1)
                    self.test_colors()
                    time.sleep(1)
                    self.test_patterns()
                    print("✅ Test complet terminé!")
                else:
                    print("❌ Choix invalide")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Arrêt par l'utilisateur")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self.spi:
            self.spi.close()
        GPIO.cleanup()
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du test...")
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🖥️  TEST ST7735 AZDELIVERY")
    print("🔧 Test écran TFT couleur 1.8\" pour Alimante")
    print("=" * 70)
    
    # Configuration
    RESET_PIN = 24  # GPIO 24
    A0_PIN = 25     # GPIO 25 (DC/A0)
    CS_PIN = 8      # GPIO 8 (CS)
    SPI_BUS = 0     # Bus SPI 0
    SPI_DEVICE = 0  # Device SPI 0
    
    print(f"🔌 Configuration:")
    print(f"   • Reset Pin: {RESET_PIN}")
    print(f"   • A0/DC Pin: {A0_PIN}")
    print(f"   • CS Pin: {CS_PIN}")
    print(f"   • SPI Bus: {SPI_BUS}")
    print(f"   • SPI Device: {SPI_DEVICE}")
    print()
    
    # Vérification de spidev
    try:
        import spidev
        print("✅ Module spidev disponible")
    except ImportError:
        print("❌ Module spidev non trouvé")
        print("   Installez avec: pip install spidev")
        return
    
    # Création et lancement du test
    test = ST7735Test(RESET_PIN, A0_PIN, CS_PIN, SPI_BUS, SPI_DEVICE)
    
    try:
        test.run_complete_test()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
