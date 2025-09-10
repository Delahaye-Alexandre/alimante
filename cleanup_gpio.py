#!/usr/bin/env python3
"""
Script de nettoyage GPIO pour Alimante
Libère tous les pins GPIO et nettoie les ressources
"""

import RPi.GPIO as GPIO
import subprocess
import sys

def cleanup_gpio():
    """Nettoie tous les pins GPIO"""
    try:
        print("🧹 Nettoyage des pins GPIO...")
        GPIO.cleanup()
        print("✅ Pins GPIO nettoyés")
        return True
    except Exception as e:
        print(f"❌ Erreur nettoyage GPIO: {e}")
        return False

def kill_gpio_processes():
    """Tue les processus utilisant GPIO"""
    try:
        print("🔍 Recherche des processus utilisant GPIO...")
        
        # Chercher les processus Python
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        python_processes = []
        
        for line in result.stdout.split('\n'):
            if 'python' in line and 'alimante' in line:
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    python_processes.append(pid)
        
        if python_processes:
            print(f"📋 Processus Python trouvés: {python_processes}")
            for pid in python_processes:
                try:
                    subprocess.run(['kill', '-9', pid], check=True)
                    print(f"✅ Processus {pid} terminé")
                except subprocess.CalledProcessError:
                    print(f"⚠️  Impossible de terminer le processus {pid}")
        else:
            print("✅ Aucun processus Python trouvé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur recherche processus: {e}")
        return False

def reset_gpio_module():
    """Remet à zéro le module GPIO"""
    try:
        print("🔄 Remise à zéro du module GPIO...")
        
        # Nettoyage complet
        GPIO.cleanup()
        
        # Réinitialisation
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        print("✅ Module GPIO réinitialisé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur réinitialisation: {e}")
        return False

def test_gpio_access():
    """Test l'accès aux pins GPIO"""
    try:
        print("🔍 Test d'accès aux pins GPIO...")
        
        # Test avec un pin simple
        test_pin = 18
        GPIO.setup(test_pin, GPIO.OUT)
        GPIO.output(test_pin, GPIO.LOW)
        GPIO.output(test_pin, GPIO.HIGH)
        GPIO.cleanup()
        
        print("✅ Accès GPIO fonctionnel")
        return True
        
    except Exception as e:
        print(f"❌ Erreur accès GPIO: {e}")
        return False

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🧹 NETTOYAGE GPIO - ALIMANTE")
    print("🔧 Libération des pins et nettoyage des ressources")
    print("=" * 60)
    
    # 1. Tuer les processus
    kill_gpio_processes()
    
    # 2. Nettoyer GPIO
    cleanup_gpio()
    
    # 3. Réinitialiser le module
    reset_gpio_module()
    
    # 4. Tester l'accès
    if test_gpio_access():
        print("\n✅ Nettoyage réussi!")
        print("🚀 Vous pouvez maintenant relancer les tests")
    else:
        print("\n❌ Problème persistant")
        print("🔧 Essayez de redémarrer le Raspberry Pi")
        print("   sudo reboot")

if __name__ == "__main__":
    main()
