#!/usr/bin/env python3
"""
Test des boutons de l'interface web pour diagnostiquer le problème
"""

import requests
import json
import time

def test_web_buttons():
    """Test des boutons de l'interface web"""
    
    print("🖱️ Test des boutons de l'interface web")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test 1: Vérifier l'état initial des composants
    print("1. État initial des composants...")
    try:
        response = requests.get(f"{base_url}/api/controls", timeout=5)
        if response.status_code == 200:
            controls = response.json()
            print(f"   📊 État initial: {json.dumps(controls, indent=2)}")
        else:
            print(f"   ❌ Erreur récupération état (code: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: Test du bouton chauffage ON
    print("\n2. Test bouton chauffage ON...")
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
            
    except Exception as e:
        print(f"   ❌ Erreur test chauffage: {e}")
    
    # Attendre un peu pour voir les logs
    print("\n   ⏳ Attente de 3 secondes pour voir les logs...")
    time.sleep(3)
    
    # Test 3: Vérifier l'état après activation
    print("\n3. État après activation du chauffage...")
    try:
        response = requests.get(f"{base_url}/api/controls", timeout=5)
        if response.status_code == 200:
            controls = response.json()
            print(f"   📊 État après: {json.dumps(controls, indent=2)}")
        else:
            print(f"   ❌ Erreur récupération état (code: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 4: Test du bouton humidification ON
    print("\n4. Test bouton humidification ON...")
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
    
    # Attendre un peu pour voir les logs
    print("\n   ⏳ Attente de 3 secondes pour voir les logs...")
    time.sleep(3)
    
    # Test 5: Test du bouton alimentation
    print("\n5. Test bouton alimentation...")
    try:
        data = {
            "component": "feeding",
            "command": {
                "feed": True
            }
        }
        
        print(f"   📤 Envoi: {json.dumps(data, indent=2)}")
        response = requests.post(f"{base_url}/api/control", json=data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            print("   ✅ API alimentation répond")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur test alimentation: {e}")
    
    print("\n🎯 Instructions pour diagnostiquer:")
    print("   1. Regardez les logs du serveur principal (main.py)")
    print("   2. Cherchez les messages d'événements émis/reçus")
    print("   3. Vérifiez si les drivers physiques sont activés")
    print("   4. Testez manuellement les composants physiques")
    
    return True

if __name__ == "__main__":
    test_web_buttons()
