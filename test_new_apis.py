#!/usr/bin/env python3
"""
Test spécifique des nouvelles APIs (terrariums, composants, contrôle)
"""

import sys
import os
import time
import requests
import json

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_new_apis():
    """Test des nouvelles APIs"""
    print("🧪 Test des nouvelles APIs Alimante")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test 1: API Terrariums
    print("1. Test API Terrariums...")
    try:
        response = requests.get(f"{base_url}/api/terrariums", timeout=5)
        if response.status_code == 200:
            data = response.json()
            terrariums = data.get('terrariums', [])
            print(f"   ✅ API terrariums accessible ({len(terrariums)} terrariums)")
            
            for terrarium in terrariums:
                print(f"   📋 {terrarium.get('name', 'Sans nom')} (ID: {terrarium.get('id', 'N/A')})")
                print(f"      - Espèce: {terrarium.get('species', {}).get('common_name', 'Non définie')}")
                print(f"      - Statut: {terrarium.get('status', 'inconnu')}")
                print(f"      - Type: {terrarium.get('controller_type', 'inconnu')}")
        else:
            print(f"   ❌ API terrariums échoué (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur API terrariums: {e}")
    
    # Test 2: API Espèces
    print("\n2. Test API Espèces...")
    try:
        response = requests.get(f"{base_url}/api/species", timeout=5)
        if response.status_code == 200:
            data = response.json()
            species = data.get('species', [])
            print(f"   ✅ API espèces accessible ({len(species)} espèces)")
            
            for specie in species:
                print(f"   🐛 {specie.get('name', 'Sans nom')} ({specie.get('scientific_name', 'N/A')})")
        else:
            print(f"   ❌ API espèces échoué (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur API espèces: {e}")
    
    # Test 3: API Composants
    print("\n3. Test API Composants...")
    try:
        response = requests.get(f"{base_url}/api/components", timeout=5)
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print(f"   ✅ API composants accessible ({len(components)} composants)")
            
            for comp_name, comp_data in components.items():
                state = "ON" if comp_data.get('current_state', False) else "OFF"
                mode = comp_data.get('control_mode', 'unknown')
                print(f"   🔧 {comp_name}: {state} (mode: {mode})")
                
                # Afficher des détails selon le composant
                if comp_name == 'heating':
                    temp = comp_data.get('current_temperature', 'N/A')
                    target = comp_data.get('target_temperature', 'N/A')
                    print(f"      - Température: {temp}°C (cible: {target}°C)")
                elif comp_name == 'lighting':
                    brightness = comp_data.get('brightness', 'N/A')
                    target = comp_data.get('target_brightness', 'N/A')
                    print(f"      - Luminosité: {brightness}% (cible: {target}%)")
                elif comp_name == 'humidification':
                    humidity = comp_data.get('current_humidity', 'N/A')
                    target = comp_data.get('target_humidity', 'N/A')
                    print(f"      - Humidité: {humidity}% (cible: {target}%)")
                elif comp_name == 'ventilation':
                    speed = comp_data.get('fan_speed', 'N/A')
                    target = comp_data.get('target_speed', 'N/A')
                    print(f"      - Vitesse: {speed}% (cible: {target}%)")
                elif comp_name == 'feeding':
                    daily_feeds = comp_data.get('daily_feeds', 0)
                    max_feeds = comp_data.get('max_daily_feeds', 0)
                    print(f"      - Alimentations: {daily_feeds}/{max_feeds}")
        else:
            print(f"   ❌ API composants échoué (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur API composants: {e}")
    
    # Test 4: Contrôle de composants
    print("\n4. Test de contrôle des composants...")
    
    # Test chauffage
    print("   🔥 Test contrôle chauffage...")
    try:
        control_data = {
            "component": "heating",
            "command": {"state": True, "target_temperature": 26.0}
        }
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        if response.status_code == 200:
            print("      ✅ Contrôle chauffage réussi")
        else:
            print(f"      ❌ Contrôle chauffage échoué (code: {response.status_code})")
            print(f"      📝 Réponse: {response.text}")
    except Exception as e:
        print(f"      ❌ Erreur contrôle chauffage: {e}")
    
    # Test éclairage
    print("   💡 Test contrôle éclairage...")
    try:
        control_data = {
            "component": "lighting",
            "command": {"state": True, "brightness": 75}
        }
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        if response.status_code == 200:
            print("      ✅ Contrôle éclairage réussi")
        else:
            print(f"      ❌ Contrôle éclairage échoué (code: {response.status_code})")
            print(f"      📝 Réponse: {response.text}")
    except Exception as e:
        print(f"      ❌ Erreur contrôle éclairage: {e}")
    
    # Test alimentation
    print("   🍽️ Test contrôle alimentation...")
    try:
        control_data = {
            "component": "feeding",
            "command": {"feed": True}
        }
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        if response.status_code == 200:
            print("      ✅ Contrôle alimentation réussi")
        else:
            print(f"      ❌ Contrôle alimentation échoué (code: {response.status_code})")
            print(f"      📝 Réponse: {response.text}")
    except Exception as e:
        print(f"      ❌ Erreur contrôle alimentation: {e}")
    
    # Test 5: Mode de contrôle global
    print("\n5. Test mode de contrôle global...")
    try:
        mode_data = {"mode": "manual"}
        response = requests.post(f"{base_url}/api/control/global-mode", json=mode_data, timeout=5)
        if response.status_code == 200:
            print("   ✅ Mode global changé en 'manual'")
        else:
            print(f"   ❌ Changement mode global échoué (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur mode global: {e}")
    
    print("\n🎉 Tests des nouvelles APIs terminés!")
    return True

if __name__ == "__main__":
    print("💡 Assurez-vous que 'python main.py' est en cours d'exécution")
    print("   Puis lancez ce test pour vérifier les nouvelles APIs\n")
    
    test_new_apis()
