#!/usr/bin/env python3
"""
Test de débogage du contrôle web - trace complète du flux
"""

import sys
import os
import time
import requests
import json

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_web_control_flow():
    """Test complet du flux de contrôle web"""
    print("🔍 Test de débogage du contrôle web")
    print("=" * 60)
    
    base_url = "http://localhost:8080"
    
    # Test 1: Vérifier la connexion
    print("1. Test de connexion...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            print("   ✅ Serveur accessible")
        else:
            print(f"   ❌ Serveur inaccessible (code: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
        return False
    
    # Test 2: Vérifier l'état initial des composants
    print("\n2. État initial des composants...")
    try:
        response = requests.get(f"{base_url}/api/components", timeout=5)
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print(f"   📊 {len(components)} composants trouvés:")
            
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
    
    # Test 3: Test de contrôle du chauffage (toggle ON)
    print("\n3. Test contrôle chauffage (ON)...")
    try:
        control_data = {
            "component": "heating",
            "command": {"state": True}
        }
        print(f"   📤 Envoi: {json.dumps(control_data, indent=2)}")
        
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("   ✅ Chauffage allumé avec succès")
            else:
                print(f"   ❌ Erreur contrôle chauffage: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur contrôle chauffage: {e}")
    
    # Test 4: Vérifier l'état après contrôle
    print("\n4. Vérification état après contrôle...")
    try:
        response = requests.get(f"{base_url}/api/components", timeout=5)
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print("   📊 État des composants après contrôle:")
            
            for comp_name, comp_data in components.items():
                state = "ON" if comp_data.get('current_state', False) else "OFF"
                mode = comp_data.get('control_mode', 'unknown')
                print(f"      - {comp_name}: {state} (mode: {mode})")
                
                # Détails spécifiques
                if comp_name == 'heating':
                    temp = comp_data.get('target_temperature', 'N/A')
                    print(f"        → Température cible: {temp}°C")
        else:
            print(f"   ❌ Erreur récupération état final (code: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur vérification état final: {e}")
    
    # Test 5: Test de contrôle de l'éclairage (brightness)
    print("\n5. Test contrôle éclairage (brightness)...")
    try:
        control_data = {
            "component": "lighting",
            "command": {"state": True, "brightness": 75}
        }
        print(f"   📤 Envoi: {json.dumps(control_data, indent=2)}")
        
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("   ✅ Éclairage contrôlé avec succès")
            else:
                print(f"   ❌ Erreur contrôle éclairage: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur contrôle éclairage: {e}")
    
    # Test 6: Test de contrôle de l'alimentation
    print("\n6. Test contrôle alimentation...")
    try:
        control_data = {
            "component": "feeding",
            "command": {"feed": True}
        }
        print(f"   📤 Envoi: {json.dumps(control_data, indent=2)}")
        
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("   ✅ Alimentation contrôlée avec succès")
            else:
                print(f"   ❌ Erreur contrôle alimentation: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur contrôle alimentation: {e}")
    
    # Test 7: État final complet
    print("\n7. État final complet...")
    try:
        response = requests.get(f"{base_url}/api/components", timeout=5)
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print("   📊 État final de tous les composants:")
            
            for comp_name, comp_data in components.items():
                state = "ON" if comp_data.get('current_state', False) else "OFF"
                mode = comp_data.get('control_mode', 'unknown')
                print(f"      - {comp_name}: {state} (mode: {mode})")
                
                # Détails spécifiques
                if comp_name == 'heating':
                    temp = comp_data.get('target_temperature', 'N/A')
                    print(f"        → Température cible: {temp}°C")
                elif comp_name == 'lighting':
                    brightness = comp_data.get('brightness', 'N/A')
                    print(f"        → Luminosité: {brightness}%")
                elif comp_name == 'feeding':
                    feeds = comp_data.get('daily_feeds', 0)
                    max_feeds = comp_data.get('max_daily_feeds', 0)
                    print(f"        → Alimentations: {feeds}/{max_feeds}")
        else:
            print(f"   ❌ Erreur récupération état final (code: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur vérification état final: {e}")
    
    print("\n🎉 Test de débogage terminé!")
    return True

if __name__ == "__main__":
    print("💡 Assurez-vous que 'python main.py' est en cours d'exécution")
    print("   Puis lancez ce test pour déboguer le contrôle des composants\n")
    
    test_web_control_flow()
