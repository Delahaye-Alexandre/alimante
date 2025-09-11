#!/usr/bin/env python3
"""
Script de diagnostic des pins GPIO
Pour identifier les conflits et les processus qui utilisent les pins
"""

import subprocess
import os
import time

def check_gpio_usage():
    """Vérifie l'utilisation des pins GPIO"""
    print("🔍 DIAGNOSTIC PINS GPIO")
    print("=" * 40)
    
    # 1. Vérifier les processus utilisant GPIO
    print("1. Processus utilisant GPIO:")
    try:
        result = subprocess.run(['sudo', 'lsof', '/dev/gpiochip*'], 
                              capture_output=True, text=True, timeout=10)
        if result.stdout:
            print(result.stdout)
        else:
            print("   Aucun processus détecté")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # 2. Vérifier l'état des pins GPIO
    print("\n2. État des pins GPIO:")
    try:
        result = subprocess.run(['sudo', 'cat', '/sys/kernel/debug/gpio'], 
                              capture_output=True, text=True, timeout=10)
        if result.stdout:
            print(result.stdout)
        else:
            print("   Impossible de lire l'état des pins")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # 3. Vérifier les périphériques SPI
    print("\n3. Périphériques SPI:")
    try:
        result = subprocess.run(['ls', '-la', '/dev/spi*'], 
                              capture_output=True, text=True, timeout=5)
        if result.stdout:
            print(result.stdout)
        else:
            print("   Aucun périphérique SPI trouvé")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # 4. Vérifier les modules chargés
    print("\n4. Modules GPIO chargés:")
    try:
        result = subprocess.run(['lsmod'], capture_output=True, text=True, timeout=5)
        if result.stdout:
            gpio_modules = [line for line in result.stdout.split('\n') if 'gpio' in line.lower()]
            for module in gpio_modules:
                print(f"   {module}")
        else:
            print("   Impossible de lister les modules")
    except Exception as e:
        print(f"   Erreur: {e}")

def force_cleanup():
    """Force le nettoyage des pins GPIO"""
    print("\n🧹 NETTOYAGE FORCÉ")
    print("=" * 40)
    
    # 1. Tuer tous les processus Python
    print("1. Arrêt des processus Python...")
    try:
        subprocess.run(['sudo', 'pkill', '-f', 'python'], timeout=5)
        time.sleep(1)
        print("   ✅ Processus Python arrêtés")
    except Exception as e:
        print(f"   ⚠️  Erreur: {e}")
    
    # 2. Libérer les pins GPIO
    print("2. Libération des pins GPIO...")
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
        print("   ✅ Pins GPIO libérées")
    except Exception as e:
        print(f"   ⚠️  Erreur: {e}")
    
    # 3. Attendre un peu
    print("3. Attente...")
    time.sleep(2)
    
    # 4. Vérifier à nouveau
    print("4. Vérification post-nettoyage...")
    check_gpio_usage()

def main():
    """Fonction principale"""
    print("🔧 DIAGNOSTIC ET NETTOYAGE GPIO")
    print("=" * 50)
    
    # Diagnostic initial
    check_gpio_usage()
    
    # Demander si on veut nettoyer
    print("\n" + "=" * 50)
    response = input("Voulez-vous forcer le nettoyage ? (y/N): ").strip().lower()
    
    if response in ['y', 'yes', 'oui']:
        force_cleanup()
        print("\n✅ Nettoyage terminé!")
        print("Vous pouvez maintenant relancer votre script principal.")
    else:
        print("\nℹ️  Nettoyage annulé.")
        print("Pour nettoyer manuellement, exécutez:")
        print("   sudo pkill -f python")
        print("   python3 cleanup_gpio.py")

if __name__ == "__main__":
    main()
