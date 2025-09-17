#!/usr/bin/env python3
"""
Test du contrôle des composants via l'API web
"""

import sys
import os
import time
import requests
import json

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_component_control():
    """Test du contrôle des composants"""
    print("🧪 Test du contrôle des composants")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test 1: Vérifier que le serveur est accessible
    print("1. Test de connexion au serveur...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
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
    
    # Test 2: Récupérer l'état des composants
    print("\n2. Test récupération état des composants...")
    try:
        response = requests.get(f"{base_url}/api/components", timeout=5)
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print(f"   ✅ {len(components)} composants trouvés")
            
            for comp_name, comp_data in components.items():
                state = "ON" if comp_data.get('current_state', False) else "OFF"
                mode = comp_data.get('control_mode', 'unknown')
                print(f"      - {comp_name}: {state} (mode: {mode})")
        else:
            print(f"   ❌ Erreur récupération composants (code: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Erreur récupération composants: {e}")
        return False
    
    # Test 3: Contrôle du chauffage
    print("\n3. Test contrôle chauffage...")
    try:
        # Allumer le chauffage
        control_data = {
            "component": "heating",
            "command": {"state": True, "target_temperature": 26.0}
        }
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ Chauffage allumé avec succès")
            else:
                print(f"   ❌ Erreur contrôle chauffage: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API chauffage (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur contrôle chauffage: {e}")
    
    # Test 4: Contrôle de l'éclairage
    print("\n4. Test contrôle éclairage...")
    try:
        control_data = {
            "component": "lighting",
            "command": {"state": True, "brightness": 75}
        }
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ Éclairage contrôlé avec succès")
            else:
                print(f"   ❌ Erreur contrôle éclairage: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API éclairage (code: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur contrôle éclairage: {e}")
    
    # Test 5: Contrôle de l'humidification
    print("\n5. Test contrôle humidification...")
    try:
        control_data = {
            "component": "humidification",
            "command": {"state": True, "target_humidity": 65}
        }
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ Humidification contrôlée avec succès")
            else:
                print(f"   ❌ Erreur contrôle humidification: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API humidification (code: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur contrôle humidification: {e}")
    
    # Test 6: Contrôle de la ventilation
    print("\n6. Test contrôle ventilation...")
    try:
        control_data = {
            "component": "ventilation",
            "command": {"state": True, "fan_speed": 60}
        }
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ Ventilation contrôlée avec succès")
            else:
                print(f"   ❌ Erreur contrôle ventilation: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API ventilation (code: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur contrôle ventilation: {e}")
    
    # Test 7: Contrôle de l'alimentation
    print("\n7. Test contrôle alimentation...")
    try:
        control_data = {
            "component": "feeding",
            "command": {"feed": True}
        }
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ Alimentation contrôlée avec succès")
            else:
                print(f"   ❌ Erreur contrôle alimentation: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API alimentation (code: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur contrôle alimentation: {e}")
    
    # Test 8: Vérifier l'état après les contrôles
    print("\n8. Vérification état final des composants...")
    try:
        response = requests.get(f"{base_url}/api/components", timeout=5)
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print("   📊 État final des composants:")
            
            for comp_name, comp_data in components.items():
                state = "ON" if comp_data.get('current_state', False) else "OFF"
                mode = comp_data.get('control_mode', 'unknown')
                
                # Afficher des détails selon le composant
                if comp_name == 'heating':
                    temp = comp_data.get('target_temperature', 'N/A')
                    print(f"      - {comp_name}: {state} (température cible: {temp}°C)")
                elif comp_name == 'lighting':
                    brightness = comp_data.get('brightness', 'N/A')
                    print(f"      - {comp_name}: {state} (luminosité: {brightness}%)")
                elif comp_name == 'humidification':
                    humidity = comp_data.get('target_humidity', 'N/A')
                    print(f"      - {comp_name}: {state} (humidité cible: {humidity}%)")
                elif comp_name == 'ventilation':
                    speed = comp_data.get('fan_speed', 'N/A')
                    print(f"      - {comp_name}: {state} (vitesse: {speed}%)")
                elif comp_name == 'feeding':
                    feeds = comp_data.get('daily_feeds', 0)
                    max_feeds = comp_data.get('max_daily_feeds', 0)
                    print(f"      - {comp_name}: {state} (alimentations: {feeds}/{max_feeds})")
                else:
                    print(f"      - {comp_name}: {state}")
        else:
            print(f"   ❌ Erreur récupération état final (code: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur vérification état final: {e}")
    
    print("\n🎉 Tests de contrôle des composants terminés!")
    return True

if __name__ == "__main__":
    print("💡 Assurez-vous que 'python main.py' est en cours d'exécution")
    print("   Puis lancez ce test pour vérifier le contrôle des composants\n")
    
    test_component_control()
