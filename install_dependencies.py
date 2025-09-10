#!/usr/bin/env python3
"""
Script d'installation des dépendances pour Alimante
Installe les modules Python nécessaires
"""

import subprocess
import sys
import os

def check_python_version():
    """Vérifie la version de Python"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("❌ Python 3.6+ requis")
        return False
    
    print("✅ Version Python compatible")
    return True

def install_package(package):
    """Installe un package Python"""
    try:
        print(f"📦 Installation de {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur installation {package}: {e}")
        return False

def check_package(package):
    """Vérifie si un package est installé"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def install_system_packages():
    """Installe les packages système nécessaires"""
    packages = [
        "python3-dev",
        "python3-pip",
        "i2c-tools",
        "spi-tools"
    ]
    
    print("🔧 Installation des packages système...")
    
    for package in packages:
        try:
            print(f"📦 Installation de {package}...")
            subprocess.check_call(["sudo", "apt", "update"])
            subprocess.check_call(["sudo", "apt", "install", "-y", package])
            print(f"✅ {package} installé")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Erreur installation {package}: {e}")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔧 INSTALLATION DÉPENDANCES ALIMANTE")
    print("📦 Installation des modules Python nécessaires")
    print("=" * 60)
    
    # Vérification Python
    if not check_python_version():
        return
    
    # Packages Python requis
    python_packages = [
        "RPi.GPIO",
        "spidev",
        "Pillow"  # Pour les images si nécessaire
    ]
    
    print("\n📋 Vérification des packages Python...")
    
    # Vérifier et installer les packages
    for package in python_packages:
        if check_package(package.replace("-", "_")):
            print(f"✅ {package} déjà installé")
        else:
            if not install_package(package):
                print(f"❌ Impossible d'installer {package}")
    
    # Installation des packages système
    print("\n🔧 Installation des packages système...")
    try:
        install_system_packages()
    except Exception as e:
        print(f"⚠️  Erreur packages système: {e}")
    
    # Vérification finale
    print("\n🔍 Vérification finale...")
    all_ok = True
    
    for package in python_packages:
        if check_package(package.replace("-", "_")):
            print(f"✅ {package}: OK")
        else:
            print(f"❌ {package}: MANQUANT")
            all_ok = False
    
    if all_ok:
        print("\n🎉 Toutes les dépendances sont installées!")
        print("🚀 Vous pouvez maintenant utiliser les scripts Alimante")
    else:
        print("\n⚠️  Certaines dépendances manquent")
        print("🔧 Relancez ce script ou installez manuellement")
    
    print("\n📚 Scripts disponibles:")
    print("   • python3 diagnostic_ecran_psi.py")
    print("   • python3 test_st7735_azdelivery.py")
    print("   • python3 alimante_main.py")

if __name__ == "__main__":
    main()
