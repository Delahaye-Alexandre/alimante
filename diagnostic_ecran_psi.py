#!/usr/bin/env python3
"""
Diagnostic pour l'écran PSI
Vérification de la configuration GPIO et SPI
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
import subprocess
import os
from datetime import datetime

class PSIDiagnostic:
    """Diagnostic pour l'écran PSI"""
    
    def __init__(self):
        """Initialise le diagnostic"""
        # Configuration GPIO selon vos spécifications
        self.reset_pin = 24  # GPIO 24
        self.a0_pin = 25     # GPIO 25
        self.cs_pin = 8      # GPIO 8 (CS)
        self.sda_pin = 10    # GPIO 10 (MOSI)
        self.scl_pin = 11    # GPIO 11 (SCLK)
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Gestionnaire de signal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def check_spi_interface(self):
        """Vérifie si l'interface SPI est activée"""
        print("🔍 Vérification de l'interface SPI...")
        
        try:
            # Vérifier si le module SPI est chargé
            result = subprocess.run(['lsmod'], capture_output=True, text=True)
            if 'spi_bcm2835' in result.stdout:
                print("✅ Module SPI chargé (spi_bcm2835)")
            else:
                print("❌ Module SPI non chargé")
                return False
            
            # Vérifier les périphériques SPI
            if os.path.exists('/dev/spidev0.0'):
                print("✅ Périphérique SPI trouvé (/dev/spidev0.0)")
            else:
                print("❌ Périphérique SPI non trouvé")
                return False
            
            # Vérifier la configuration dans /boot/firmware/config.txt (nouveau) ou /boot/config.txt (ancien)
            config_files = ['/boot/firmware/config.txt', '/boot/config.txt']
            config_found = False
            
            for config_file in config_files:
                try:
                    with open(config_file, 'r') as f:
                        config_content = f.read()
                        # Chercher dtparam=spi=on sans commentaire
                        lines = config_content.split('\n')
                        spi_found = False
                        for line in lines:
                            line = line.strip()
                            if line == 'dtparam=spi=on' or line.startswith('dtparam=spi=on '):
                                spi_found = True
                                break
                            elif line.startswith('#dtparam=spi=on'):
                                print(f"⚠️  SPI commenté dans {config_file}")
                                return False
                        
                        if spi_found:
                            print(f"✅ SPI activé dans {config_file}")
                            config_found = True
                            break
                        else:
                            print(f"❌ SPI non trouvé dans {config_file}")
                            print("   Contenu trouvé:")
                            for line in lines:
                                if 'spi' in line.lower():
                                    print(f"   {line}")
                except FileNotFoundError:
                    print(f"⚠️  Fichier {config_file} non trouvé")
                    continue
            
            if not config_found:
                print("❌ Aucun fichier de configuration trouvé")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification SPI: {e}")
            return False
    
    def test_gpio_pins(self):
        """Test des pins GPIO"""
        print("🔍 Test des pins GPIO...")
        
        try:
            # Nettoyage préalable
            GPIO.cleanup()
            time.sleep(0.1)
            
            # Configuration des pins
            GPIO.setup(self.reset_pin, GPIO.OUT)
            GPIO.setup(self.a0_pin, GPIO.OUT)
            GPIO.setup(self.cs_pin, GPIO.OUT)
            GPIO.setup(self.sda_pin, GPIO.OUT)
            GPIO.setup(self.scl_pin, GPIO.OUT)
            
            print(f"✅ Pins configurés:")
            print(f"   • Reset (GPIO {self.reset_pin})")
            print(f"   • A0/DC (GPIO {self.a0_pin})")
            print(f"   • CS (GPIO {self.cs_pin})")
            print(f"   • SDA/MOSI (GPIO {self.sda_pin})")
            print(f"   • SCL/SCLK (GPIO {self.scl_pin})")
            
            # Test de sortie
            print("\n🔄 Test de sortie des pins...")
            
            # Test Reset
            GPIO.output(self.reset_pin, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(self.reset_pin, GPIO.HIGH)
            print("   ✅ Reset testé")
            
            # Test A0/DC
            GPIO.output(self.a0_pin, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(self.a0_pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(self.a0_pin, GPIO.LOW)
            print("   ✅ A0/DC testé")
            
            # Test CS
            GPIO.output(self.cs_pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(self.cs_pin, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(self.cs_pin, GPIO.HIGH)
            print("   ✅ CS testé")
            
            # Test SDA/MOSI
            GPIO.output(self.sda_pin, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(self.sda_pin, GPIO.HIGH)
            print("   ✅ SDA/MOSI testé")
            
            # Test SCL/SCLK
            GPIO.output(self.scl_pin, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(self.scl_pin, GPIO.HIGH)
            print("   ✅ SCL/SCLK testé")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test GPIO: {e}")
            return False
    
    def check_pin_mapping(self):
        """Affiche le mapping des pins"""
        print("📋 Mapping des pins GPIO:")
        print("=" * 50)
        print("Fonction        | GPIO | Pin Physique")
        print("-" * 50)
        print(f"Reset           | {self.reset_pin:4d} | 18")
        print(f"A0/DC           | {self.a0_pin:4d} | 22")
        print(f"CS              | {self.cs_pin:4d} | 24")
        print(f"SDA/MOSI        | {self.sda_pin:4d} | 19")
        print(f"SCL/SCLK        | {self.scl_pin:4d} | 23")
        print("=" * 50)
        print()
        print("🔌 Câblage recommandé:")
        print("   ST7735 AZdelivery → Raspberry Pi")
        print(f"   Reset  → Pin 18 (GPIO {self.reset_pin})")
        print(f"   A0/DC  → Pin 22 (GPIO {self.a0_pin})")
        print(f"   CS     → Pin 24 (GPIO {self.cs_pin})")
        print(f"   SDA    → Pin 19 (GPIO {self.sda_pin})")
        print(f"   SCL    → Pin 23 (GPIO {self.scl_pin})")
        print("   VCC    → 3.3V")
        print("   GND    → GND")
    
    def check_i2c_interface(self):
        """Vérifie l'interface I2C (alternative)"""
        print("🔍 Vérification de l'interface I2C...")
        
        try:
            # Vérifier si I2C est activé
            result = subprocess.run(['i2cdetect', '-y', '1'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Interface I2C disponible")
                print("📊 Périphériques I2C détectés:")
                print(result.stdout)
            else:
                print("❌ Interface I2C non disponible")
                return False
            
            return True
            
        except FileNotFoundError:
            print("❌ i2cdetect non trouvé (installez i2c-tools)")
            return False
        except Exception as e:
            print(f"❌ Erreur I2C: {e}")
            return False
    
    def run_diagnostic(self):
        """Lance le diagnostic complet"""
        print("🚀 DIAGNOSTIC ÉCRAN PSI - ALIMANTE")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        
        # 1. Mapping des pins
        self.check_pin_mapping()
        
        # 2. Vérification SPI
        spi_ok = self.check_spi_interface()
        
        # 3. Test GPIO
        gpio_ok = self.test_gpio_pins()
        
        # 4. Vérification I2C (alternative)
        i2c_ok = self.check_i2c_interface()
        
        # Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DU DIAGNOSTIC")
        print("=" * 60)
        print(f"SPI Interface: {'✅ OK' if spi_ok else '❌ PROBLÈME'}")
        print(f"GPIO Pins:     {'✅ OK' if gpio_ok else '❌ PROBLÈME'}")
        print(f"I2C Interface: {'✅ OK' if i2c_ok else '❌ PROBLÈME'}")
        
        if not spi_ok:
            print("\n🔧 ACTIONS RECOMMANDÉES:")
            print("1. Activer SPI avec: sudo raspi-config")
            print("2. Aller dans 'Interfacing Options' > 'SPI' > 'Enable'")
            print("3. Redémarrer le Raspberry Pi")
            print("4. Vérifier que dtparam=spi=on est dans /boot/config.txt")
        
        if not gpio_ok:
            print("\n🔧 VÉRIFIER LE CÂBLAGE:")
            print("   • Vérifiez les connexions physiques")
            print("   • Vérifiez l'alimentation 3.3V")
            print("   • Vérifiez la masse (GND)")
        
        print("\n" + "=" * 60)
    
    def cleanup(self):
        """Nettoie les ressources"""
        GPIO.cleanup()
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du diagnostic...")
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🔍 DIAGNOSTIC ÉCRAN PSI")
    print("🔧 Vérification configuration GPIO et SPI")
    print("=" * 70)
    
    # Création et lancement du diagnostic
    diagnostic = PSIDiagnostic()
    
    try:
        diagnostic.run_diagnostic()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        diagnostic.cleanup()
        print("👋 Diagnostic terminé!")

if __name__ == "__main__":
    main()
