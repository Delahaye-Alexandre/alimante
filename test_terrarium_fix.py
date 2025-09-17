#!/usr/bin/env python3
"""
Test rapide pour vérifier que le terrarium est maintenant chargé
"""

import sys
import os
import requests
import json

def test_terrarium_fix():
    """Test rapide du terrarium"""
    print("🔧 Test de correction du terrarium")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    try:
        # Test terrariums
        print("1. Test API terrariums...")
        response = requests.get(f"{base_url}/api/terrariums", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            terrariums = data.get('terrariums', [])
            print(f"   📊 {len(terrariums)} terrariums trouvés:")
            
            for terrarium in terrariums:
                print(f"      - {terrarium.get('name', 'Sans nom')} (ID: {terrarium.get('id', 'N/A')})")
                species = terrarium.get('species', {})
                print(f"        → Espèce: {species.get('common_name', 'Non définie')}")
                
                if terrarium.get('id') == 'terrarium_default':
                    print("        → ✅ Terrarium par défaut trouvé!")
                    env_settings = terrarium.get('environmental_settings', {})
                    if env_settings:
                        temp_settings = env_settings.get('temperature', {})
                        print(f"        → Température jour: {temp_settings.get('day_target', 'N/A')}°C")
                        print(f"        → Température nuit: {temp_settings.get('night_target', 'N/A')}°C")
                        
                        humidity_settings = env_settings.get('humidity', {})
                        print(f"        → Humidité: {humidity_settings.get('target', 'N/A')}%")
                        
                        lighting_settings = env_settings.get('lighting', {})
                        print(f"        → Éclairage: {lighting_settings.get('photoperiod', {}).get('day_start', 'N/A')} - {lighting_settings.get('photoperiod', {}).get('day_end', 'N/A')}")
                        print(f"        → Intensité: {lighting_settings.get('intensity', {}).get('optimal', 'N/A')}%")
        else:
            print(f"   ❌ Erreur: {response.text}")
        
        # Test composants
        print("\n2. Test API composants...")
        response = requests.get(f"{base_url}/api/components", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print(f"   📊 {len(components)} composants trouvés:")
            
            for comp_name, comp_data in components.items():
                print(f"      - {comp_name}:")
                if comp_name == 'heating':
                    target_temp = comp_data.get('target_temperature', 'N/A')
                    print(f"        → Température cible: {target_temp}°C")
                elif comp_name == 'lighting':
                    brightness = comp_data.get('target_brightness', 'N/A')
                    print(f"        → Luminosité cible: {brightness}%")
                elif comp_name == 'humidification':
                    humidity = comp_data.get('target_humidity', 'N/A')
                    print(f"        → Humidité cible: {humidity}%")
                elif comp_name == 'ventilation':
                    base_speed = comp_data.get('target_speed', 'N/A')
                    print(f"        → Vitesse cible: {base_speed}%")
                elif comp_name == 'feeding':
                    schedule = comp_data.get('feeding_schedule', [])
                    print(f"        → Horaires: {schedule}")
        else:
            print(f"   ❌ Erreur: {response.text}")
        
        print("\n✅ Test terminé!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_terrarium_fix()
