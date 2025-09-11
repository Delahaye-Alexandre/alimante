#!/usr/bin/env python3
"""
Script d'installation des librairies pour encodeur rotatif + écran
"""

import subprocess
import sys
import os

def install_package(package):
    """Installe un package avec pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation de {package}: {e}")
        return False

def check_package(package):
    """Vérifie si un package est installé"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    """Fonction principale d'installation"""
    print("=" * 60)
    print("🔧 INSTALLATION DES LIBRAIRIES ENCODEUR + ÉCRAN")
    print("=" * 60)
    
    # Liste des packages à installer
    packages = [
        ("gpiozero", "gpiozero"),
        ("RPi.GPIO", "RPi.GPIO"),
        ("spidev", "spidev"),
        ("Pillow", "PIL"),
    ]
    
    print("📦 Vérification des packages...")
    
    all_installed = True
    for package_name, import_name in packages:
        if check_package(import_name):
            print(f"✅ {package_name} déjà installé")
        else:
            print(f"❌ {package_name} non installé")
            all_installed = False
    
    if all_installed:
        print("\n🎉 Tous les packages sont déjà installés!")
        return
    
    print("\n📥 Installation des packages manquants...")
    
    for package_name, import_name in packages:
        if not check_package(import_name):
            print(f"\n🔄 Installation de {package_name}...")
            if install_package(package_name):
                print(f"✅ {package_name} installé avec succès")
            else:
                print(f"❌ Échec de l'installation de {package_name}")
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES SOLUTIONS DISPONIBLES:")
    print("=" * 60)
    print("1. test_encoder_gpiozero.py")
    print("   • Encodeur uniquement avec gpiozero")
    print("   • Anti-rebond automatique")
    print("   • Recommandé pour débuter")
    print()
    print("2. test_encoder_ecran_gpiozero.py")
    print("   • Encodeur + écran avec gpiozero + SPI")
    print("   • Version combinée simple")
    print("   • Mise à jour temps réel")
    print()
    print("3. test_encoder_ecran_avance.py")
    print("   • Encodeur + écran avec driver ST7735")
    print("   • Version avancée avec driver complet")
    print("   • Pour utilisation professionnelle")
    print()
    print("4. test_encoder_interrupts.py")
    print("   • Encodeur avec interruptions RPi.GPIO")
    print("   • Anti-rebond par bouncetime")
    print("   • Alternative à gpiozero")
    print()
    print("5. test_encoder_simple.py")
    print("   • Version manuelle avec polling")
    print("   • Anti-rebond personnalisé")
    print("   • Pour cas complexes")
    print()
    print("🚀 Testez les solutions dans cet ordre!")

if __name__ == "__main__":
    main()
