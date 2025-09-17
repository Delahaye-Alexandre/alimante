#!/usr/bin/env python3
"""
Script de test pour vérifier que les modules web fonctionnent
"""

import sys
import os
import time
import requests
import json

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_web_modules():
    """Test des modules web"""
    print("🧪 Test des modules web Alimante")
    print("=" * 40)
    
    try:
        # Test 1: Vérifier que le serveur répond
        print("1. Test de connexion au serveur...")
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("   ✅ Serveur web accessible")
        else:
            print(f"   ❌ Serveur web inaccessible (code: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter au serveur")
        print("   💡 Assurez-vous que main.py est en cours d'exécution")
        return False
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False
    
    # Test 2: Vérifier l'API des terrariums
    print("\n2. Test de l'API des terrariums...")
    try:
        response = requests.get("http://localhost:8080/api/terrariums", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API terrariums accessible ({len(data.get('terrariums', []))} terrariums)")
            print(f"   📋 Terrariums: {[t.get('name', 'Sans nom') for t in data.get('terrariums', [])]}")
        else:
            print(f"   ❌ API terrariums inaccessible (code: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Erreur API terrariums: {e}")
        return False
    
    # Test 3: Vérifier l'API des espèces
    print("\n3. Test de l'API des espèces...")
    try:
        response = requests.get("http://localhost:8080/api/species", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API espèces accessible ({len(data.get('species', []))} espèces)")
            print(f"   🐛 Espèces: {[s.get('name', 'Sans nom') for s in data.get('species', [])]}")
        else:
            print(f"   ❌ API espèces inaccessible (code: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Erreur API espèces: {e}")
        return False
    
    # Test 4: Vérifier l'API des composants
    print("\n4. Test de l'API des composants...")
    try:
        response = requests.get("http://localhost:8080/api/components", timeout=5)
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print(f"   ✅ API composants accessible ({len(components)} composants)")
            for comp_name, comp_data in components.items():
                state = "ON" if comp_data.get('current_state', False) else "OFF"
                print(f"   🔧 {comp_name}: {state}")
        else:
            print(f"   ❌ API composants inaccessible (code: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Erreur API composants: {e}")
        return False
    
    # Test 5: Test de contrôle d'un composant
    print("\n5. Test de contrôle d'un composant...")
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
    test_web_modules()
