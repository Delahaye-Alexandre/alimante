#!/usr/bin/env python3
"""
Script pour tester et afficher les logs de l'interface web
"""

import sys
import os
import time
import requests
import json

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_web_logs():
    """Test des logs de l'interface web"""
    print("🔍 Test des logs de l'interface web")
    print("=" * 60)
    
    base_url = "http://localhost:8080"
    
    print("1. Test de connexion au serveur...")
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
    
    print("\n2. Test de l'API terrariums...")
    try:
        response = requests.get(f"{base_url}/api/terrariums", timeout=5)
        print(f"   📡 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            terrariums = data.get('terrariums', [])
            print(f"   📊 {len(terrariums)} terrariums trouvés:")
            
            for terrarium in terrariums:
                print(f"      - {terrarium.get('name', 'Sans nom')} (ID: {terrarium.get('id', 'N/A')})")
                species = terrarium.get('species', {})
                print(f"        → Espèce: {species.get('common_name', 'Non définie')}")
                
                # Vérifier si c'est le terrarium principal
                if terrarium.get('id') == 'terrarium_principal':
                    print("        → ✅ Terrarium principal trouvé!")
                    env_settings = terrarium.get('environmental_settings', {})
                    if env_settings:
                        temp_settings = env_settings.get('temperature', {})
                        print(f"        → Température jour: {temp_settings.get('day_target', 'N/A')}°C")
                        print(f"        → Température nuit: {temp_settings.get('night_target', 'N/A')}°C")
                        
                        humidity_settings = env_settings.get('humidity', {})
                        print(f"        → Humidité: {humidity_settings.get('target', 'N/A')}%")
                        
                        lighting_settings = env_settings.get('lighting', {})
                        print(f"        → Éclairage: {lighting_settings.get('on_time', 'N/A')} - {lighting_settings.get('off_time', 'N/A')}")
                        print(f"        → Intensité: {lighting_settings.get('intensity', 'N/A')}%")
        else:
            print(f"   ❌ Erreur API terrariums: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur test terrariums: {e}")
    
    print("\n3. Test de l'API composants...")
    try:
        response = requests.get(f"{base_url}/api/components", timeout=5)
        print(f"   📡 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            components = data.get('components', {})
            print(f"   📊 {len(components)} composants trouvés:")
            
            for comp_name, comp_data in components.items():
                print(f"      - {comp_name}:")
                print(f"        → Mode: {comp_data.get('control_mode', 'N/A')}")
                print(f"        → Activé: {comp_data.get('enabled', 'N/A')}")
                
                if comp_name == 'heating':
                    target_temp = comp_data.get('target_temperature', 'N/A')
                    night_temp = comp_data.get('night_temperature', 'N/A')
                    print(f"        → Température jour: {target_temp}°C (attendu: 25.0°C)")
                    print(f"        → Température nuit: {night_temp}°C (attendu: 20.0°C)")
                    
                elif comp_name == 'lighting':
                    brightness = comp_data.get('target_brightness', 'N/A')
                    schedule = comp_data.get('schedule', {})
                    print(f"        → Luminosité: {brightness}% (attendu: 60%)")
                    print(f"        → Horaires: {schedule.get('on_time', 'N/A')} - {schedule.get('off_time', 'N/A')} (attendu: 10:00 - 22:00)")
                    
                elif comp_name == 'humidification':
                    humidity = comp_data.get('target_humidity', 'N/A')
                    print(f"        → Humidité: {humidity}% (attendu: 65%)")
                    
                elif comp_name == 'ventilation':
                    base_speed = comp_data.get('target_speed', 'N/A')
                    max_speed = comp_data.get('max_speed', 'N/A')
                    print(f"        → Vitesse base: {base_speed}% (attendu: 25%)")
                    print(f"        → Vitesse max: {max_speed}% (attendu: 60%)")
                    
                elif comp_name == 'feeding':
                    schedule = comp_data.get('feeding_schedule', [])
                    portion = comp_data.get('portion_size', 'N/A')
                    print(f"        → Horaires: {schedule} (attendu: ['10:00', '19:00'])")
                    print(f"        → Portion: {portion} (attendu: small)")
        else:
            print(f"   ❌ Erreur API composants: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur test composants: {e}")
    
    print("\n4. Test de l'API espèces...")
    try:
        response = requests.get(f"{base_url}/api/species", timeout=5)
        print(f"   📡 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            species = data.get('species', [])
            print(f"   📊 {len(species)} espèces trouvées:")
            
            for specie in species:
                print(f"      - {specie.get('name', 'Sans nom')} ({specie.get('scientific_name', 'N/A')})")
                if specie.get('id') == 'mantis_religiosa':
                    print("        → ✅ Mante religieuse trouvée!")
        else:
            print(f"   ❌ Erreur API espèces: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur test espèces: {e}")
    
    print("\n🎯 Instructions pour consulter les logs:")
    print("   1. Dans le terminal où vous lancez 'python main.py', vous devriez voir:")
    print("      - Les logs d'initialisation des services")
    print("      - Les logs de chargement de la configuration JSON")
    print("      - Les logs des appels API")
    print("   2. Copiez-collez ces logs ici pour que je puisse diagnostiquer le problème")
    
    return True

if __name__ == "__main__":
    test_web_logs()
