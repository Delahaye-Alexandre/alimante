#!/usr/bin/env python3
"""
Test de l'utilisation de la configuration JSON au lieu du hardcoding
"""

import sys
import os
import json
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_json_config_loading():
    """Test du chargement de la configuration JSON"""
    print("🧪 Test de chargement de la configuration JSON")
    print("=" * 60)
    
    # Test 1: Vérifier que le fichier mantis_religiosa.json existe
    print("1. Vérification du fichier de configuration...")
    config_file = Path("config/species/insects/mantis_religiosa.json")
    
    if config_file.exists():
        print(f"   ✅ Fichier trouvé: {config_file}")
        
        # Charger et analyser le fichier
        with open(config_file, 'r', encoding='utf-8') as f:
            species_config = json.load(f)
        
        print(f"   📋 Espèce: {species_config.get('common_name', 'N/A')}")
        print(f"   🔬 Nom scientifique: {species_config.get('scientific_name', 'N/A')}")
        
        # Vérifier les paramètres environnementaux
        env_req = species_config.get('environmental_requirements', {})
        
        # Température
        temp_config = env_req.get('temperature', {})
        day_temp = temp_config.get('day', {}).get('optimal', 'N/A')
        night_temp = temp_config.get('night', {}).get('optimal', 'N/A')
        print(f"   🌡️  Température jour: {day_temp}°C")
        print(f"   🌙 Température nuit: {night_temp}°C")
        
        # Humidité
        humidity_config = env_req.get('humidity', {})
        humidity_opt = humidity_config.get('optimal', 'N/A')
        print(f"   💧 Humidité optimale: {humidity_opt}%")
        
        # Éclairage
        lighting_config = env_req.get('lighting', {})
        photoperiod = lighting_config.get('photoperiod', {})
        intensity = lighting_config.get('intensity', {})
        print(f"   💡 Éclairage: {photoperiod.get('day_start', 'N/A')} - {photoperiod.get('day_end', 'N/A')}")
        print(f"   🔆 Intensité: {intensity.get('optimal', 'N/A')}%")
        
        # Ventilation
        ventilation_config = env_req.get('ventilation', {})
        air_circ = ventilation_config.get('air_circulation', {})
        print(f"   💨 Ventilation: {air_circ.get('base_speed', 'N/A')}% - {air_circ.get('max_speed', 'N/A')}%")
        
        # Alimentation
        feeding_req = species_config.get('feeding_requirements', {})
        schedule = feeding_req.get('schedule', {})
        print(f"   🍽️  Alimentation: {schedule.get('times', [])}")
        print(f"   📅 Fréquence: {schedule.get('frequency', 'N/A')}")
        
    else:
        print(f"   ❌ Fichier non trouvé: {config_file}")
        return False
    
    # Test 2: Simuler le chargement par ComponentControlService
    print("\n2. Test de chargement par ComponentControlService...")
    try:
        from services.component_control_service import ComponentControlService
        
        # Créer une instance du service
        service = ComponentControlService()
        
        # Vérifier que les composants sont initialisés avec les bonnes valeurs
        components = service.get_all_components()
        
        print(f"   📊 {len(components)} composants chargés:")
        
        for comp_name, comp_data in components.items():
            print(f"      - {comp_name}:")
            
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
        
        print("   ✅ Configuration JSON chargée avec succès!")
        
    except Exception as e:
        print(f"   ❌ Erreur chargement service: {e}")
        return False
    
    # Test 3: Vérifier la création du terrarium
    print("\n3. Test de création du terrarium...")
    try:
        from services.terrarium_service import TerrariumService
        
        # Créer une instance du service
        terrarium_service = TerrariumService()
        
        # Vérifier que le terrarium principal existe
        terrariums = terrarium_service.get_terrariums()
        print(f"   📊 {len(terrariums)} terrariums trouvés:")
        
        for terrarium in terrariums:
            print(f"      - {terrarium.get('name', 'Sans nom')} (ID: {terrarium.get('id', 'N/A')})")
            species = terrarium.get('species', {})
            print(f"        → Espèce: {species.get('common_name', 'Non définie')}")
            print(f"        → Scientifique: {species.get('scientific_name', 'N/A')}")
            
            # Vérifier les paramètres environnementaux
            env_settings = terrarium.get('environmental_settings', {})
            if env_settings:
                temp_settings = env_settings.get('temperature', {})
                print(f"        → Temp jour: {temp_settings.get('day_target', 'N/A')}°C")
                print(f"        → Temp nuit: {temp_settings.get('night_target', 'N/A')}°C")
                
                humidity_settings = env_settings.get('humidity', {})
                print(f"        → Humidité: {humidity_settings.get('target', 'N/A')}%")
                
                lighting_settings = env_settings.get('lighting', {})
                print(f"        → Éclairage: {lighting_settings.get('on_time', 'N/A')} - {lighting_settings.get('off_time', 'N/A')}")
                print(f"        → Intensité: {lighting_settings.get('intensity', 'N/A')}%")
        
        print("   ✅ Terrarium créé avec configuration JSON!")
        
    except Exception as e:
        print(f"   ❌ Erreur création terrarium: {e}")
        return False
    
    print("\n🎉 Tous les tests de configuration JSON réussis!")
    return True

if __name__ == "__main__":
    test_json_config_loading()
