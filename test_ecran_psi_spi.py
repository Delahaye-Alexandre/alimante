#!/usr/bin/env python3
"""
Test avancé pour l'écran PSI avec interface SPI
Utilise spidev pour communiquer avec l'écran
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
import spidev
from datetime import datetime

class PSISpiTest:
    """Test SPI pour l'écran PSI"""
    
    def __init__(self, reset_pin=24, a0_pin=25, spi_bus=0, spi_device=0):
        """
        Initialise le test SPI de l'écran PSI
        
        Args:
            reset_pin (int): Pin Reset de l'écran
            a0_pin (int): Pin A0 de l'écran
            spi_bus (int): Bus SPI (généralement 0)
            spi_device (int): Device SPI (généralement 0)
        """
        self.reset_pin = reset_pin
        self.a0_pin = a0_pin
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
            
            # État initial
            GPIO.output(self.reset_pin, GPIO.HIGH)  # Reset actif bas
            GPIO.output(self.a0_pin, GPIO.LOW)      # A0 bas (mode commande)
            
            # Initialisation SPI
            self.spi = spidev.SpiDev()
            self.spi.open(self.spi_bus, self.spi_device)
            
            # Configuration SPI
            self.spi.max_speed_hz = 1000000  # 1 MHz
            self.spi.mode = 0  # Mode SPI 0
            
            print("✅ Interface SPI initialisée")
            print(f"   • Bus: {self.spi_bus}")
            print(f"   • Device: {self.spi_device}")
            print(f"   • Vitesse: {self.spi.max_speed_hz} Hz")
            print(f"   • Mode: {self.spi.mode}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur initialisation SPI: {e}")
            return False
    
    def reset_display(self):
        """Reset de l'écran"""
        print("🔄 Reset de l'écran...")
        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.reset_pin, GPIO.HIGH)
        time.sleep(0.1)
        print("✅ Reset terminé")
    
    def send_command(self, command):
        """Envoie une commande à l'écran"""
        GPIO.output(self.a0_pin, GPIO.LOW)  # Mode commande
        self.spi.xfer2([command])
        time.sleep(0.001)
    
    def send_data(self, data):
        """Envoie des données à l'écran"""
        GPIO.output(self.a0_pin, GPIO.HIGH)  # Mode données
        if isinstance(data, list):
            self.spi.xfer2(data)
        else:
            self.spi.xfer2([data])
        time.sleep(0.001)
    
    def test_basic_commands(self):
        """Test des commandes de base"""
        print("🔄 Test des commandes de base...")
        
        try:
            # Séquence d'initialisation basique
            self.reset_display()
            
            # Commandes de test (à adapter selon votre écran)
            test_commands = [
                0x01,  # Reset software
                0x11,  # Sortie du mode sommeil
                0x29,  # Allumage de l'écran
            ]
            
            for cmd in test_commands:
                print(f"   Envoi commande: 0x{cmd:02X}")
                self.send_command(cmd)
                time.sleep(0.1)
            
            print("✅ Commandes de base testées")
            return True
            
        except Exception as e:
            print(f"❌ Erreur commandes: {e}")
            return False
    
    def test_data_transmission(self):
        """Test de transmission de données"""
        print("🔄 Test transmission de données...")
        
        try:
            # Test avec des données simples
            test_data = [0x00, 0x55, 0xAA, 0xFF]
            
            for data in test_data:
                print(f"   Envoi données: 0x{data:02X}")
                self.send_data(data)
                time.sleep(0.1)
            
            print("✅ Transmission de données testée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur transmission: {e}")
            return False
    
    def test_spi_communication(self):
        """Test de communication SPI complète"""
        print("🔄 Test communication SPI complète...")
        
        try:
            # Test de lecture/écriture
            test_pattern = [0x01, 0x02, 0x03, 0x04, 0x05]
            
            print("   Envoi pattern de test...")
            self.send_data(test_pattern)
            
            # Test de différentes vitesses
            speeds = [100000, 500000, 1000000, 2000000]
            for speed in speeds:
                print(f"   Test vitesse: {speed} Hz")
                self.spi.max_speed_hz = speed
                self.send_data([0xAA])
                time.sleep(0.1)
            
            # Retour à la vitesse normale
            self.spi.max_speed_hz = 1000000
            
            print("✅ Communication SPI testée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur communication: {e}")
            return False
    
    def run_complete_test(self):
        """Lance le test complet"""
        print("🚀 Démarrage du test SPI écran PSI...")
        
        if not self.initialize():
            return
        
        print("\n" + "="*60)
        print("🖥️  TEST SPI ÉCRAN PSI - ALIMANTE")
        print("="*60)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔌 Reset Pin: {self.reset_pin}")
        print(f"🔌 A0 Pin: {self.a0_pin}")
        print(f"🔌 SPI Bus: {self.spi_bus}, Device: {self.spi_device}")
        print("="*60)
        
        try:
            while True:
                print("\n🎛️  MENU DE TEST SPI:")
                print("1. Reset de l'écran")
                print("2. Test commandes de base")
                print("3. Test transmission de données")
                print("4. Test communication SPI complète")
                print("5. Test complet")
                print("0. Quitter")
                
                choice = input("\nVotre choix (0-5): ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    self.reset_display()
                elif choice == "2":
                    self.test_basic_commands()
                elif choice == "3":
                    self.test_data_transmission()
                elif choice == "4":
                    self.test_spi_communication()
                elif choice == "5":
                    print("🔄 Test complet en cours...")
                    self.reset_display()
                    time.sleep(1)
                    self.test_basic_commands()
                    time.sleep(1)
                    self.test_data_transmission()
                    time.sleep(1)
                    self.test_spi_communication()
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
    print("🖥️  TEST SPI ÉCRAN PSI")
    print("🔧 Test interface SPI pour Alimante")
    print("=" * 70)
    
    # Configuration
    RESET_PIN = 24  # GPIO 24
    A0_PIN = 25     # GPIO 25
    SPI_BUS = 0     # Bus SPI 0
    SPI_DEVICE = 0  # Device SPI 0
    
    print(f"🔌 Configuration:")
    print(f"   • Reset Pin: {RESET_PIN}")
    print(f"   • A0 Pin: {A0_PIN}")
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
    test = PSISpiTest(RESET_PIN, A0_PIN, SPI_BUS, SPI_DEVICE)
    
    try:
        test.run_complete_test()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
