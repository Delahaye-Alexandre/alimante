#!/usr/bin/env python3
"""
Script de test pour le contrôleur d'humidité
"""

import sys
import os
sys.path.insert(0, '.')

from src.utils.gpio_manager import GPIOManager
from src.controllers.humidity_controller import HumidityController
from src.utils.config_manager import SystemConfig

def test_humidity_controller():
    """Test le contrôleur d'humidité"""
    print("🧪 Test du contrôleur d'humidité")
    print("=" * 40)
    
    try:
        # Charger la configuration
        config = SystemConfig.from_json(
            "config/config.json",
            "config/lepidopteres/saturniidae/saturnia_pyri.json"
        )
        
        print(f"✅ Configuration chargée:")
        print(f"   - Espèce: {config.species_name}")
        print(f"   - Humidité min: {config.humidity.get('min', 'N/A')}%")
        print(f"   - Humidité max: {config.humidity.get('max', 'N/A')}%")
        print(f"   - Humidité optimale: {config.humidity.get('optimal', 'N/A')}%")
        
        # Initialiser GPIO (simulation)
        gpio_manager = GPIOManager()
        
        # Créer le contrôleur
        humidity_controller = HumidityController(gpio_manager, config.humidity)
        print("✅ Contrôleur d'humidité créé")
        
        # Test de lecture
        print("\n📊 Test de lecture d'humidité:")
        for i in range(5):
            humidity = humidity_controller.read_humidity()
            if humidity is not None:
                print(f"   Lecture {i+1}: {humidity:.1f}%")
            else:
                print(f"   Lecture {i+1}: ÉCHEC")
        
        # Test de contrôle
        print("\n🎛️ Test de contrôle d'humidité:")
        result = humidity_controller.control_humidity()
        print(f"   Contrôle: {'✅ Succès' if result else '❌ Échec'}")
        
        # Test de statut
        print("\n📋 Statut du contrôleur:")
        status = humidity_controller.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Test terminé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_humidity_controller()
    sys.exit(0 if success else 1)
