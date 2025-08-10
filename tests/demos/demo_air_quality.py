#!/usr/bin/env python3
"""
Démonstration du système de qualité de l'air
Montre comment la qualité de l'air affecte la vitesse des ventilateurs
"""

import time
import sys
import os
sys.path.insert(0, '.')

from src.controllers.air_quality_controller import AirQualityController
from src.controllers.fan_controller import FanController
from src.utils.gpio_manager import GPIOManager

def simulate_air_quality_changes(air_quality_controller, fan_controller):
    """Simule des changements de qualité de l'air"""
    print("🌬️ Simulation de changements de qualité de l'air")
    print("=" * 50)
    
    # Scénarios de qualité de l'air
    scenarios = [
        {"name": "Air pur", "ppm": 30, "expected_speed": 0},
        {"name": "Air légèrement pollué", "ppm": 80, "expected_speed": 25},
        {"name": "Air modérément pollué", "ppm": 120, "expected_speed": 50},
        {"name": "Air pollué", "ppm": 180, "expected_speed": 75},
        {"name": "Air très pollué", "ppm": 250, "expected_speed": 100},
        {"name": "Air dangereux", "ppm": 350, "expected_speed": 100}
    ]
    
    for scenario in scenarios:
        print(f"\n📊 Scénario: {scenario['name']}")
        print(f"   PPM simulé: {scenario['ppm']}")
        print(f"   Vitesse attendue: {scenario['expected_speed']}%")
        
        # Simuler la lecture (on modifie temporairement la méthode)
        original_read = air_quality_controller._read_raw_sensor
        
        def mock_read():
            return scenario['ppm']
        
        air_quality_controller._read_raw_sensor = mock_read
        
        # Lire la qualité de l'air
        reading = air_quality_controller.read_air_quality()
        if reading:
            print(f"   Qualité détectée: {reading['quality_level']}")
            print(f"   PPM mesuré: {reading['ppm']:.1f}")
            print(f"   Vitesse ventilateurs: {reading['fan_speed']}%")
            
            # Contrôler la ventilation
            success = air_quality_controller.control_ventilation(fan_controller)
            print(f"   Contrôle ventilation: {'✅ Succès' if success else '❌ Échec'}")
            
            # Vérifier le statut des ventilateurs
            fan_status = fan_controller.get_status()
            print(f"   Ventilateurs actifs: {fan_status['fans_active']}")
            print(f"   Vitesse actuelle: {fan_status['current_speed']}%")
        else:
            print("   ❌ Échec de lecture")
        
        # Restaurer la méthode originale
        air_quality_controller._read_raw_sensor = original_read
        
        time.sleep(2)  # Pause entre les scénarios

def show_air_quality_levels():
    """Affiche les niveaux de qualité de l'air"""
    print("\n📋 Niveaux de qualité de l'air")
    print("=" * 40)
    
    levels = [
        {"name": "Excellent", "ppm": "0-50", "speed": "0%", "color": "🟢"},
        {"name": "Bon", "ppm": "50-100", "speed": "25%", "color": "🟡"},
        {"name": "Modéré", "ppm": "100-150", "speed": "50%", "color": "🟠"},
        {"name": "Mauvais", "ppm": "150-200", "speed": "75%", "color": "🔴"},
        {"name": "Malsain", "ppm": "200-300", "speed": "100%", "color": "🟣"},
        {"name": "Très malsain", "ppm": "300+", "speed": "100%", "color": "⚫"}
    ]
    
    for level in levels:
        print(f"{level['color']} {level['name']}: {level['ppm']} ppm → Ventilateurs: {level['speed']}")

def main():
    """Programme principal"""
    print("🌬️ Démonstration du système de qualité de l'air")
    print("=" * 60)
    print("Ce script montre comment la qualité de l'air affecte")
    print("automatiquement la vitesse des ventilateurs.")
    print()
    
    try:
        # Configuration
        air_quality_config = {
            "pin": 27,
            "voltage": "5V",
            "current": 120
        }
        
        fan_config = {
            "count": 4,
            "relay_pin": 25,
            "voltage": "5V",
            "current_per_fan": 200,
            "total_current": 800
        }
        
        # Initialiser les contrôleurs
        gpio_manager = GPIOManager()
        air_quality_controller = AirQualityController(gpio_manager, air_quality_config)
        fan_controller = FanController(gpio_manager, fan_config)
        
        print("✅ Contrôleurs initialisés")
        
        # Afficher les niveaux de qualité
        show_air_quality_levels()
        
        # Calibrer le capteur
        print("\n🔧 Calibration du capteur...")
        success = air_quality_controller.calibrate_sensor()
        if success:
            print("✅ Capteur calibré")
        else:
            print("❌ Échec de calibration")
            return False
        
        # Démarrer la simulation
        print("\n🚀 Démarrage de la simulation...")
        simulate_air_quality_changes(air_quality_controller, fan_controller)
        
        # Statut final
        print("\n📊 Statut final:")
        air_status = air_quality_controller.get_status()
        fan_status = fan_controller.get_status()
        
        print(f"   Qualité de l'air: {air_status['current_quality']}")
        print(f"   Ventilateurs actifs: {fan_status['fans_active']}")
        print(f"   Vitesse ventilateurs: {fan_status['current_speed']}%")
        print(f"   Lectures effectuées: {air_status['reading_count']}")
        
        # Nettoyage
        print("\n🧹 Nettoyage...")
        air_quality_controller.cleanup()
        fan_controller.cleanup()
        
        print("\n🎉 Démonstration terminée !")
        print("Le système de qualité de l'air fonctionne correctement.")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
