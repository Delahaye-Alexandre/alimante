#!/usr/bin/env python3
"""
Test de l'initialisation automatique du terrarium principal
"""

import sys
import os
import time
import requests
import json

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_terrarium_initialization():
    """Test de l'initialisation automatique du terrarium"""
    print("🧪 Test d'initialisation automatique du terrarium")
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
    
    # Test 2: Vérifier les terrariums
    print("\n2. Test des terrariums...")
    try:
        response = requests.get(f"{base_url}/api/terrariums", timeout=5)
        if response.status_code == 200:
            data = response.json()
            terrariums = data.get('terrariums', [])
            print(f"   📊 {len(terrariums)} terrariums trouvés:")
            
            for terrarium in terrariums:
                print(f"      - {terrarium.get('name', 'Sans nom')} (ID: {terrarium.get('id', 'N/A')})")
                print(f"        → Espèce: {terrarium.get('species', {}).get('common_name', 'Non définie')}")
                print(f"        → Statut: {terrarium.get('status', 'inconnu')}")
                print(f"        → Type: {terrarium.get('controller_type', 'inconnu')}")
        else:
            print(f"   ❌ Erreur récupération terrariums (code: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Erreur récupération terrariums: {e}")
        return False
    
    # Test 3: Vérifier les espèces
    print("\n3. Test des espèces...")
    try:
        response = requests.get(f"{base_url}/api/species", timeout=5)
        if response.status_code == 200:
            data = response.json()
            species = data.get('species', [])
            print(f"   🐛 {len(species)} espèces trouvées:")
            
            for specie in species:
                print(f"      - {specie.get('name', 'Sans nom')} ({specie.get('scientific_name', 'N/A')})")
                if specie.get('id') == 'mantis_religiosa':
                    print(f"        → ✅ Mante religieuse trouvée!")
        else:
            print(f"   ❌ Erreur récupération espèces (code: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Erreur récupération espèces: {e}")
        return False
    
    # Test 4: Vérifier les composants avec paramètres par défaut
    print("\n4. Test des composants avec paramètres par défaut...")
    try:
        response = requests.get(f"{base_url}/api/components", timeout=5)
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print(f"   🔧 {len(components)} composants trouvés:")
            
            for comp_name, comp_data in components.items():
                state = "ON" if comp_data.get('current_state', False) else "OFF"
                mode = comp_data.get('control_mode', 'unknown')
                print(f"      - {comp_name}: {state} (mode: {mode})")
                
                # Vérifier les paramètres spécifiques
                if comp_name == 'heating':
                    temp = comp_data.get('target_temperature', 'N/A')
                    print(f"        → Température cible: {temp}°C (attendu: 25.0°C)")
                elif comp_name == 'lighting':
                    brightness = comp_data.get('target_brightness', 'N/A')
                    print(f"        → Luminosité cible: {brightness}% (attendu: 60%)")
                elif comp_name == 'humidification':
                    humidity = comp_data.get('target_humidity', 'N/A')
                    print(f"        → Humidité cible: {humidity}% (attendu: 65%)")
                elif comp_name == 'ventilation':
                    speed = comp_data.get('target_speed', 'N/A')
                    print(f"        → Vitesse cible: {speed}% (attendu: 25%)")
                elif comp_name == 'feeding':
                    feeds = comp_data.get('daily_feeds', 0)
                    max_feeds = comp_data.get('max_daily_feeds', 0)
                    schedule = comp_data.get('feeding_schedule', [])
                    print(f"        → Alimentations: {feeds}/{max_feeds} (max: 3)")
                    print(f"        → Horaires: {schedule} (attendu: ['10:00', '19:00'])")
        else:
            print(f"   ❌ Erreur récupération composants (code: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Erreur récupération composants: {e}")
        return False
    
    # Test 5: Test de contrôle d'un composant
    print("\n5. Test de contrôle d'un composant...")
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
            else:
                print(f"   ❌ Erreur contrôle: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur contrôle: {e}")
    
    print("\n🎉 Test d'initialisation terminé!")
    return True

if __name__ == "__main__":
    print("💡 Assurez-vous que 'python main.py' est en cours d'exécution")
    print("   Puis lancez ce test pour vérifier l'initialisation automatique\n")
    
    test_terrarium_initialization()
