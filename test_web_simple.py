#!/usr/bin/env python3
"""
Test simple du système web sans démarrer de serveur
"""

import sys
import os
import time
import requests

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_web_apis():
    """Test des APIs web sans démarrer de serveur"""
    print("🧪 Test des APIs web (serveur externe)")
    print("=" * 50)
    
    # Test de connexion au serveur existant
    print("1. Test de connexion au serveur...")
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("   ✅ Serveur web accessible")
        else:
            print(f"   ❌ Serveur web inaccessible (code: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter au serveur")
        print("   💡 Assurez-vous que 'python main.py' est en cours d'exécution")
        return False
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False
    
    # Test des APIs
    apis_to_test = [
        ("/api/terrariums", "Terrariums"),
        ("/api/species", "Espèces"),
        ("/api/components", "Composants"),
        ("/api/sensors", "Capteurs"),
        ("/api/controls", "Contrôles"),
        ("/api/status", "Statut")
    ]
    
    for api_path, api_name in apis_to_test:
        print(f"\n2. Test de l'API {api_name}...")
        try:
            response = requests.get(f"http://localhost:8080{api_path}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API {api_name} accessible")
                
                # Afficher quelques données selon l'API
                if api_path == "/api/terrariums":
                    terrariums = data.get('terrariums', [])
                    print(f"   📋 {len(terrariums)} terrariums trouvés")
                    for t in terrariums[:2]:  # Afficher les 2 premiers
                        print(f"      - {t.get('name', 'Sans nom')} ({t.get('status', 'inconnu')})")
                
                elif api_path == "/api/components":
                    components = data.get('components', {})
                    print(f"   🔧 {len(components)} composants trouvés")
                    for comp_name, comp_data in list(components.items())[:3]:  # Afficher les 3 premiers
                        state = "ON" if comp_data.get('current_state', False) else "OFF"
                        print(f"      - {comp_name}: {state}")
                
                elif api_path == "/api/sensors":
                    sensors = data.get('sensors', {})
                    print(f"   🌡️ {len(sensors)} capteurs trouvés")
                    for sensor_name, sensor_data in list(sensors.items())[:3]:  # Afficher les 3 premiers
                        value = sensor_data.get('value', 'N/A')
                        unit = sensor_data.get('unit', '')
                        print(f"      - {sensor_name}: {value} {unit}")
                
            else:
                print(f"   ❌ API {api_name} inaccessible (code: {response.status_code})")
                print(f"   📝 Réponse: {response.text[:200]}...")
        except Exception as e:
            print(f"   ❌ Erreur API {api_name}: {e}")
    
    # Test de contrôle d'un composant
    print(f"\n3. Test de contrôle d'un composant...")
    try:
        control_data = {
            "component": "heating",
            "command": {"state": True, "target_temperature": 26.0}
        }
        response = requests.post(
            "http://localhost:8080/api/control", 
            json=control_data, 
            timeout=5
        )
        if response.status_code == 200:
            print("   ✅ Contrôle de composant fonctionne")
        else:
            print(f"   ❌ Contrôle de composant échoué (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur contrôle composant: {e}")
    
    print("\n🎉 Tests terminés!")
    return True

if __name__ == "__main__":
    print("💡 Assurez-vous que 'python main.py' est en cours d'exécution dans un autre terminal")
    print("   Puis lancez ce test pour vérifier les APIs\n")
    
    test_web_apis()
