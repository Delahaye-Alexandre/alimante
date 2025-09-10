#!/usr/bin/env python3
"""
Script pour activer l'interface SPI sur Raspberry Pi
Nécessite les droits administrateur
"""

import subprocess
import sys
import os

def check_sudo():
    """Vérifie si le script est exécuté avec sudo"""
    if os.geteuid() != 0:
        print("❌ Ce script doit être exécuté avec sudo")
        print("Usage: sudo python3 activate_spi.py")
        return False
    return True

def check_raspi_config():
    """Vérifie si raspi-config est disponible"""
    try:
        result = subprocess.run(['which', 'raspi-config'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ raspi-config trouvé")
            return True
        else:
            print("❌ raspi-config non trouvé")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def activate_spi_raspi_config():
    """Active SPI avec raspi-config"""
    print("🔄 Activation de SPI avec raspi-config...")
    try:
        # Commande pour activer SPI automatiquement
        cmd = ['raspi-config', 'nonint', 'do_spi', '0']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SPI activé avec raspi-config")
            return True
        else:
            print(f"❌ Erreur raspi-config: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def activate_spi_manual():
    """Active SPI manuellement en modifiant /boot/config.txt"""
    print("🔄 Activation manuelle de SPI...")
    
    config_file = '/boot/config.txt'
    backup_file = '/boot/config.txt.backup'
    
    try:
        # Sauvegarde du fichier original
        subprocess.run(['cp', config_file, backup_file], check=True)
        print(f"✅ Sauvegarde créée: {backup_file}")
        
        # Lecture du fichier
        with open(config_file, 'r') as f:
            lines = f.readlines()
        
        # Vérification si SPI est déjà activé
        spi_enabled = False
        for line in lines:
            if 'dtparam=spi=on' in line and not line.strip().startswith('#'):
                spi_enabled = True
                break
        
        if spi_enabled:
            print("✅ SPI déjà activé dans /boot/config.txt")
            return True
        
        # Ajout de la configuration SPI
        spi_config = [
            '\n',
            '# SPI interface activation for PSI display\n',
            'dtparam=spi=on\n',
            'dtoverlay=spi1-1cs\n'
        ]
        
        with open(config_file, 'a') as f:
            f.writelines(spi_config)
        
        print("✅ Configuration SPI ajoutée à /boot/config.txt")
        print("⚠️  Redémarrage nécessaire pour appliquer les changements")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_spi_status():
    """Vérifie le statut de SPI"""
    print("🔍 Vérification du statut SPI...")
    
    # Vérifier /boot/config.txt
    try:
        with open('/boot/config.txt', 'r') as f:
            content = f.read()
            if 'dtparam=spi=on' in content:
                print("✅ SPI activé dans /boot/config.txt")
            else:
                print("❌ SPI non activé dans /boot/config.txt")
                return False
    except Exception as e:
        print(f"❌ Erreur lecture config: {e}")
        return False
    
    # Vérifier les périphériques
    if os.path.exists('/dev/spidev0.0'):
        print("✅ Périphérique SPI trouvé (/dev/spidev0.0)")
    else:
        print("❌ Périphérique SPI non trouvé")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔧 ACTIVATION INTERFACE SPI")
    print("🖥️  Pour écran PSI Alimante")
    print("=" * 60)
    
    # Vérification des droits
    if not check_sudo():
        sys.exit(1)
    
    # Vérification du statut actuel
    if check_spi_status():
        print("✅ SPI déjà activé et fonctionnel!")
        return
    
    print("\n🔄 Activation de SPI...")
    
    # Tentative avec raspi-config
    if check_raspi_config():
        if activate_spi_raspi_config():
            print("\n✅ SPI activé avec raspi-config")
            print("⚠️  Redémarrez le Raspberry Pi pour appliquer les changements")
            print("   sudo reboot")
            return
    
    # Activation manuelle
    print("\n🔄 Tentative d'activation manuelle...")
    if activate_spi_manual():
        print("\n✅ SPI activé manuellement")
        print("⚠️  Redémarrez le Raspberry Pi pour appliquer les changements")
        print("   sudo reboot")
    else:
        print("\n❌ Impossible d'activer SPI automatiquement")
        print("🔧 Activation manuelle requise:")
        print("   1. sudo nano /boot/config.txt")
        print("   2. Ajouter: dtparam=spi=on")
        print("   3. Sauvegarder et redémarrer")

if __name__ == "__main__":
    main()
