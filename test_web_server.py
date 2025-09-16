#!/usr/bin/env python3
"""
Test simple du serveur web Flask
"""

import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_flask_import():
    """Test l'import de Flask"""
    try:
        from flask import Flask
        print("✅ Flask importé avec succès")
        return True
    except ImportError as e:
        print(f"❌ Erreur import Flask: {e}")
        return False

def test_web_interface():
    """Test l'interface web"""
    try:
        from ui.web_interface import WebInterface
        print("✅ WebInterface importé avec succès")
        
        # Configuration de test
        config = {
            'host': '0.0.0.0',
            'port': 8080,
            'debug': False
        }
        
        # Créer l'interface
        web_interface = WebInterface(config)
        print("✅ WebInterface créé avec succès")
        
        # Tester le démarrage
        if web_interface.start():
            print("✅ Serveur web démarré avec succès")
            print(f"🌐 Serveur accessible sur http://localhost:{config['port']}")
            print("🛑 Appuyez sur Ctrl+C pour arrêter")
            
            try:
                # Garder le serveur en vie
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Arrêt du serveur...")
                web_interface.stop()
                print("✅ Serveur arrêté")
        else:
            print("❌ Échec démarrage serveur web")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test interface web: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🌐 Test du serveur web Alimante")
    print("=" * 40)
    
    if not test_flask_import():
        print("💥 Flask non disponible - installez avec: pip install flask flask-cors")
        sys.exit(1)
    
    if test_web_interface():
        print("🎉 Test du serveur web réussi!")
    else:
        print("💥 Test du serveur web échoué!")
        sys.exit(1)
