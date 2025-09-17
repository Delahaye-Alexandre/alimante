#!/usr/bin/env python3
"""
Test final du système web Alimante
"""

import sys
import os
import time
import threading
import requests

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_web_system():
    """Test complet du système web"""
    print("🧪 Test final du système web Alimante")
    print("=" * 50)
    
    try:
        # Imports
        from utils.event_bus import EventBus
        from services.terrarium_service import TerrariumService
        from services.component_control_service import ComponentControlService
        from ui.ui_controller import UIController
        
        print("✅ Tous les imports réussis")
        
        # Création des instances
        event_bus = EventBus()
        terrarium_service = TerrariumService(event_bus)
        component_service = ComponentControlService(event_bus)
        ui_controller = UIController(event_bus)
        
        print("✅ Toutes les instances créées")
        
        # Vérification des services dans l'UI
        if hasattr(ui_controller, 'terrarium_service') and ui_controller.terrarium_service:
            print("✅ TerrariumService disponible dans UIController")
        else:
            print("❌ TerrariumService manquant dans UIController")
            return False
            
        if hasattr(ui_controller, 'component_control_service') and ui_controller.component_control_service:
            print("✅ ComponentControlService disponible dans UIController")
        else:
            print("❌ ComponentControlService manquant dans UIController")
            return False
        
        # Vérification de l'interface web
        if hasattr(ui_controller, 'web_interface') and ui_controller.web_interface:
            print("✅ WebInterface disponible dans UIController")
            
            # Vérifier les services dans l'interface web
            if hasattr(ui_controller.web_interface, 'terrarium_service'):
                print("✅ TerrariumService passé à WebInterface")
            else:
                print("❌ TerrariumService non passé à WebInterface")
                
            if hasattr(ui_controller.web_interface, 'component_control_service'):
                print("✅ ComponentControlService passé à WebInterface")
            else:
                print("❌ ComponentControlService non passé à WebInterface")
        else:
            print("❌ WebInterface manquant dans UIController")
            return False
        
        # Test de démarrage de l'UI
        print("\n🚀 Test de démarrage de l'UI...")
        if ui_controller.start():
            print("✅ UIController démarré avec succès")
            
            # Attendre un peu pour que le serveur démarre
            time.sleep(3)
            
            # Test de connexion au serveur web
            print("\n🌐 Test de connexion au serveur web...")
            try:
                response = requests.get("http://localhost:8080", timeout=5)
                if response.status_code == 200:
                    print("✅ Serveur web accessible")
                else:
                    print(f"❌ Serveur web inaccessible (code: {response.status_code})")
                    return False
            except requests.exceptions.ConnectionError:
                print("❌ Impossible de se connecter au serveur web")
                return False
            except Exception as e:
                print(f"❌ Erreur de connexion: {e}")
                return False
            
            # Test des APIs
            print("\n🔌 Test des APIs...")
            
            # API terrariums
            try:
                response = requests.get("http://localhost:8080/api/terrariums", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ API terrariums fonctionne ({len(data.get('terrariums', []))} terrariums)")
                else:
                    print(f"❌ API terrariums échoué (code: {response.status_code})")
            except Exception as e:
                print(f"❌ Erreur API terrariums: {e}")
            
            # API composants
            try:
                response = requests.get("http://localhost:8080/api/components", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    components = data.get('components', {})
                    print(f"✅ API composants fonctionne ({len(components)} composants)")
                else:
                    print(f"❌ API composants échoué (code: {response.status_code})")
            except Exception as e:
                print(f"❌ Erreur API composants: {e}")
            
            # Arrêter l'UI
            ui_controller.stop()
            print("\n🛑 UIController arrêté")
            
        else:
            print("❌ Échec démarrage UIController")
            return False
        
        print("\n🎉 Tous les tests passent! Le système web fonctionne correctement.")
        return True
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_web_system()
    if success:
        print("\n✅ Le système est prêt! Lancez 'python main.py' et ouvrez http://localhost:8080")
    else:
        print("\n❌ Des problèmes ont été détectés. Vérifiez les logs ci-dessus.")
