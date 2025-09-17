#!/usr/bin/env python3
"""
Test final du contrôle des composants via l'interface web
"""

import requests
import json
import time

def test_web_control():
    """Test du contrôle des composants via l'API web"""
    
    print("🌐 Test du contrôle des composants via l'interface web")
    print("=" * 60)
    
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
    
    # Test 2: Test du contrôle de l'humidification
    print("\n2. Test du contrôle de l'humidification...")
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
            print("   ✅ Humidification activée avec succès")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur test humidification: {e}")
        return False
    
    # Test 3: Test du contrôle du chauffage
    print("\n3. Test du contrôle du chauffage...")
    try:
        data = {
            "component": "heating",
            "command": {
                "state": True,
                "target_temperature": 25
            }
        }
        
        print(f"   📤 Envoi: {json.dumps(data, indent=2)}")
        response = requests.post(f"{base_url}/api/control", json=data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            print("   ✅ Chauffage activé avec succès")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur test chauffage: {e}")
    
    # Test 4: Test du contrôle de l'éclairage
    print("\n4. Test du contrôle de l'éclairage...")
    try:
        data = {
            "component": "lighting",
            "command": {
                "state": True,
                "intensity": 80
            }
        }
        
        print(f"   📤 Envoi: {json.dumps(data, indent=2)}")
        response = requests.post(f"{base_url}/api/control", json=data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            print("   ✅ Éclairage activé avec succès")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur test éclairage: {e}")
    
    # Test 5: Test du contrôle de la ventilation
    print("\n5. Test du contrôle de la ventilation...")
    try:
        data = {
            "component": "ventilation",
            "command": {
                "state": True,
                "speed": 60
            }
        }
        
        print(f"   📤 Envoi: {json.dumps(data, indent=2)}")
        response = requests.post(f"{base_url}/api/control", json=data, timeout=5)
        print(f"   📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Résultat: {json.dumps(result, indent=2)}")
            print("   ✅ Ventilation activée avec succès")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur test ventilation: {e}")
    
    # Test 6: Test du contrôle de l'alimentation
    print("\n6. Test du contrôle de l'alimentation...")
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
            print("   ✅ Alimentation activée avec succès")
        else:
            print(f"   ❌ Erreur API (code: {response.status_code})")
            print(f"   📝 Réponse: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur test alimentation: {e}")
    
    # Test 7: Désactivation de tous les composants
    print("\n7. Désactivation de tous les composants...")
    components = ["humidification", "heating", "lighting", "ventilation"]
    
    for component in components:
        try:
            data = {
                "component": component,
                "command": {
                    "state": False
                }
            }
            
            print(f"   📤 Désactivation {component}...")
            response = requests.post(f"{base_url}/api/control", json=data, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ {component} désactivé")
            else:
                print(f"   ❌ Erreur désactivation {component}")
                
        except Exception as e:
            print(f"   ❌ Erreur désactivation {component}: {e}")
    
    print("\n🎯 Résumé des tests:")
    print("   - Interface web: Test d'accessibilité")
    print("   - Humidification: Test d'activation/désactivation")
    print("   - Chauffage: Test d'activation/désactivation")
    print("   - Éclairage: Test d'activation/désactivation")
    print("   - Ventilation: Test d'activation/désactivation")
    print("   - Alimentation: Test d'activation")
    print("   - Désactivation: Test de désactivation de tous les composants")
    
    return True

if __name__ == "__main__":
    test_web_control()
