#!/usr/bin/env python3
"""
Test du contrôle via l'interface web
"""

import sys
import os
import requests
import json
import time

def test_web_control():
    """Test du contrôle via l'interface web"""
    print("🔧 Test du contrôle via l'interface web")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test 1: Vérifier que le serveur répond
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
        print("   💡 Assurez-vous que 'python main.py' est en cours d'exécution")
        return False
    
    # Test 2: Vérifier les terrariums
    print("\n2. Test des terrariums...")
    try:
        response = requests.get(f"{base_url}/api/terrariums", timeout=5)
        if response.status_code == 200:
            data = response.json()
            terrariums = data.get('terrariums', [])
            print(f"   📊 {len(terrariums)} terrariums trouvés")
            for terrarium in terrariums:
                print(f"      - {terrarium.get('name', 'Sans nom')} (ID: {terrarium.get('id', 'N/A')})")
        else:
            print(f"   ❌ Erreur terrariums: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur terrariums: {e}")
    
    # Test 3: Vérifier les composants
    print("\n3. Test des composants...")
    try:
        response = requests.get(f"{base_url}/api/components", timeout=5)
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print(f"   📊 {len(components)} composants trouvés")
            for comp_name, comp_data in components.items():
                state = "ON" if comp_data.get('current_state', False) else "OFF"
                enabled = "✅" if comp_data.get('enabled', False) else "❌"
                print(f"      - {comp_name}: {state} (enabled: {enabled})")
        else:
            print(f"   ❌ Erreur composants: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur composants: {e}")
    
    # Test 4: Test de contrôle du chauffage
    print("\n4. Test de contrôle du chauffage...")
    try:
        control_data = {
            "component": "heating",
            "command": {"state": True, "target_temperature": 26.0}
        }
        print(f"   📤 Envoi: {json.dumps(control_data, indent=2)}")
        
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("   ✅ Contrôle du chauffage réussi")
                
                # Vérifier l'état après contrôle
                time.sleep(1)
                response = requests.get(f"{base_url}/api/components", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    components = data.get('components', {})
                    heating = components.get('heating', {})
                    state = "ON" if heating.get('current_state', False) else "OFF"
                    print(f"   🔥 État chauffage après contrôle: {state}")
            else:
                print(f"   ❌ Erreur contrôle: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur contrôle: {e}")
    
    # Test 5: Test de contrôle de l'éclairage
    print("\n5. Test de contrôle de l'éclairage...")
    try:
        control_data = {
            "component": "lighting",
            "command": {"state": True, "brightness": 80}
        }
        print(f"   📤 Envoi: {json.dumps(control_data, indent=2)}")
        
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("   ✅ Contrôle de l'éclairage réussi")
            else:
                print(f"   ❌ Erreur contrôle: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur contrôle: {e}")
    
    print("\n🎯 Instructions pour diagnostiquer:")
    print("   1. Vérifiez les logs du serveur principal (main.py)")
    print("   2. Regardez s'il y a des erreurs dans les services")
    print("   3. Vérifiez que les drivers sont bien initialisés")
    
    return True

if __name__ == "__main__":
    test_web_control()
