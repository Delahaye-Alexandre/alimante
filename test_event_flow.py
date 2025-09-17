#!/usr/bin/env python3
"""
Test du flux d'événements entre ComponentControlService et les services
"""

import requests
import json
import time

def test_event_flow():
    """Test du flux d'événements"""
    
    print("🔄 Test du flux d'événements")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test 1: Vérifier que le serveur web est accessible
    print("1. Vérification de l'accessibilité du serveur web...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Serveur web accessible")
        else:
            print(f"   ❌ Erreur serveur web (code: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Impossible de se connecter au serveur web: {e}")
        return False
    
    # Test 2: Test du contrôle du chauffage
    print("\n2. Test du contrôle du chauffage...")
    try:
        data = {
            "component": "heating",
            "command": {
                "state": True,
                "target_temperature": 26
            }
        }
        
        print(f"   📤 Envoi: {json.dumps(data, indent=2)}")
        response = requests.post(f"{base_url}/api/control", json=data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            print("   ✅ API chauffage répond")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur test chauffage: {e}")
        return False
    
    # Test 3: Test du contrôle de l'humidification
    print("\n3. Test du contrôle de l'humidification...")
    try:
        data = {
            "component": "humidification",
            "command": {
                "state": True,
                "target_humidity": 70
            }
        }
        
        print(f"   📤 Envoi: {json.dumps(data, indent=2)}")
        response = requests.post(f"{base_url}/api/control", json=data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            print("   ✅ API humidification répond")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur test humidification: {e}")
    
    # Test 4: Vérifier l'état des composants
    print("\n4. Vérification de l'état des composants...")
    try:
        response = requests.get(f"{base_url}/api/controls", timeout=5)
        if response.status_code == 200:
            controls = response.json()
            print(f"   📊 État des composants:")
            for component, state in controls.items():
                print(f"      - {component}: {state}")
        else:
            print(f"   ❌ Erreur récupération état (code: {response.status_code})")
            
    except Exception as e:
        print(f"   ❌ Erreur vérification état: {e}")
    
    print("\n🎯 Instructions pour diagnostiquer:")
    print("   1. Vérifiez les logs du serveur principal (main.py)")
    print("   2. Regardez s'il y a des messages d'événements émis/reçus")
    print("   3. Vérifiez que les services sont bien démarrés")
    print("   4. Testez manuellement les composants physiques")
    
    return True

if __name__ == "__main__":
    test_event_flow()
