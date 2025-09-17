#!/usr/bin/env python3
"""
Test spécifique du brumisateur et du servomoteur d'alimentation
"""

import sys
import os
import requests
import json
import time

def test_humidification_feeding():
    """Test du brumisateur et du servomoteur"""
    print("💧🍽️ Test du brumisateur et du servomoteur d'alimentation")
    print("=" * 60)
    
    base_url = "http://localhost:8080"
    
    # Test 1: Brumisateur (humidification)
    print("1. Test du brumisateur (humidification)...")
    try:
        control_data = {
            "component": "humidification",
            "command": {"state": True, "target_humidity": 70}
        }
        print(f"   📤 Envoi: {json.dumps(control_data, indent=2)}")
        
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("   ✅ Brumisateur activé avec succès")
                
                # Vérifier l'état après contrôle
                time.sleep(1)
                response = requests.get(f"{base_url}/api/components", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    components = data.get('components', {})
                    humidification = components.get('humidification', {})
                    state = "ON" if humidification.get('current_state', False) else "OFF"
                    target = humidification.get('target_humidity', 'N/A')
                    print(f"   💧 État brumisateur: {state} (cible: {target}%)")
            else:
                print(f"   ❌ Erreur brumisateur: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur brumisateur: {e}")
    
    # Test 2: Servomoteur d'alimentation
    print("\n2. Test du servomoteur d'alimentation...")
    try:
        control_data = {
            "component": "feeding",
            "command": {"state": True, "servo_angle": 90, "feed": True}
        }
        print(f"   📤 Envoi: {json.dumps(control_data, indent=2)}")
        
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("   ✅ Servomoteur d'alimentation activé avec succès")
                
                # Vérifier l'état après contrôle
                time.sleep(1)
                response = requests.get(f"{base_url}/api/components", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    components = data.get('components', {})
                    feeding = components.get('feeding', {})
                    state = "ON" if feeding.get('current_state', False) else "OFF"
                    angle = feeding.get('servo_angle', 'N/A')
                    daily_feeds = feeding.get('daily_feeds', 0)
                    print(f"   🍽️ État servomoteur: {state} (angle: {angle}°, repas: {daily_feeds})")
            else:
                print(f"   ❌ Erreur servomoteur: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur servomoteur: {e}")
    
    # Test 3: Test de l'action "Alimenter maintenant" (bouton feed)
    print("\n3. Test de l'action 'Alimenter maintenant'...")
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
                print("   ✅ Action 'Alimenter maintenant' réussie")
            else:
                print(f"   ❌ Erreur action: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur action: {e}")
    
    # Test 4: Désactivation du brumisateur
    print("\n4. Test de désactivation du brumisateur...")
    try:
        control_data = {
            "component": "humidification",
            "command": {"state": False}
        }
        print(f"   📤 Envoi: {json.dumps(control_data, indent=2)}")
        
        response = requests.post(f"{base_url}/api/control", json=control_data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("   ✅ Brumisateur désactivé avec succès")
                
                # Vérifier l'état après contrôle
                time.sleep(1)
                response = requests.get(f"{base_url}/api/components", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    components = data.get('components', {})
                    humidification = components.get('humidification', {})
                    state = "ON" if humidification.get('current_state', False) else "OFF"
                    print(f"   💧 État brumisateur après désactivation: {state}")
            else:
                print(f"   ❌ Erreur désactivation: {result.get('error', 'Inconnu')}")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur désactivation: {e}")
    
    print("\n🎯 Résumé des tests:")
    print("   - Brumisateur (humidification): Test d'activation/désactivation")
    print("   - Servomoteur (feeding): Test d'activation et d'angle")
    print("   - Action 'Alimenter maintenant': Test du bouton feed")
    
    return True

if __name__ == "__main__":
    test_humidification_feeding()
