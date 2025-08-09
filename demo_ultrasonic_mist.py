#!/usr/bin/env python3
"""
Démonstration du brumisateur ultrasonique
Simulation des différents modes d'humidification
"""

import sys
import time
import json
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.gpio_manager import GPIOManager
from src.controllers.buzzer_controller import UltrasonicMistController
from src.utils.logging_config import get_logger

def demo_ultrasonic_mist():
    """Démonstration complète du brumisateur ultrasonique"""
    logger = get_logger("demo_ultrasonic_mist")
    
    print("🌊 Démonstration du brumisateur ultrasonique")
    print("=" * 50)
    print("💡 Ce script simule l'utilisation du brumisateur ultrasonique")
    print("🔧 En mode réel, il contrôlerait un transducteur ultrasonique")
    print("💧 Pour créer de la brume d'eau pour l'humidification du terrarium")
    print()
    
    try:
        # Configuration
        config = {
            "pin": 22,
            "voltage": "12V",
            "current": 100,
            "power_watts": 24,
            "frequency": 1700000
        }
        
        print("📋 Configuration du transducteur ultrasonique:")
        print(f"  - Pin GPIO: {config['pin']}")
        print(f"  - Tension: {config['voltage']}")
        print(f"  - Courant: {config['current']}mA")
        print(f"  - Puissance: {config['power_watts']}W")
        print(f"  - Fréquence: {config['frequency']:,}Hz (1.7MHz)")
        print()
        
        # Initialisation
        gpio_manager = GPIOManager()
        controller = UltrasonicMistController(gpio_manager, config)
        
        print("🎛️ Modes d'humidification disponibles:")
        for mode_name, mode_config in controller.mist_modes.items():
            print(f"  - {mode_name}: {mode_config['description']}")
            print(f"    Durée: {mode_config['duration']}s, Intensité: {mode_config['intensity']}%")
        print()
        
        # Démonstration 1: Mode léger
        print("🌱 Démonstration 1: Humidification légère")
        print("   Mode 'light' - 30 secondes à 30% d'intensité")
        success = controller.run_mist_mode("light")
        print(f"   Résultat: {'✅ Succès' if success else '❌ Échec'}")
        print()
        
        # Démonstration 2: Mode moyen
        print("💧 Démonstration 2: Humidification moyenne")
        print("   Mode 'medium' - 60 secondes à 60% d'intensité")
        success = controller.run_mist_mode("medium")
        print(f"   Résultat: {'✅ Succès' if success else '❌ Échec'}")
        print()
        
        # Démonstration 3: Contrôle manuel
        print("🎛️ Démonstration 3: Contrôle manuel")
        print("   Activation à 50% d'intensité pendant 3 secondes")
        success = controller.activate_mist(intensity=50, duration=3)
        print(f"   Résultat: {'✅ Succès' if success else '❌ Échec'}")
        print()
        
        # Démonstration 4: Ajustement d'intensité
        print("⚡ Démonstration 4: Ajustement d'intensité")
        print("   Activation à 30%, puis augmentation à 80%")
        controller.activate_mist(intensity=30)
        time.sleep(1)
        controller.set_mist_intensity(80)
        time.sleep(1)
        controller.deactivate_mist()
        print("   ✅ Intensité ajustée avec succès")
        print()
        
        # Démonstration 5: Mode continu
        print("🔄 Démonstration 5: Mode continu")
        print("   Activation continue à 40% d'intensité")
        controller.activate_mist(intensity=40)
        time.sleep(2)
        controller.deactivate_mist()
        print("   ✅ Mode continu testé")
        print()
        
        # Démonstration 6: Sécurité
        print("🔒 Démonstration 6: Fonctionnalités de sécurité")
        print("   - Temps maximum en continu: 5 minutes")
        print("   - Pause de sécurité: 1 minute entre activations")
        print("   - Arrêt d'urgence disponible")
        
        # Test d'arrêt d'urgence
        controller.activate_mist(intensity=100)
        time.sleep(0.5)
        success = controller.emergency_stop()
        print(f"   Arrêt d'urgence: {'✅ Succès' if success else '❌ Échec'}")
        print()
        
        # Démonstration 7: Ajout de mode personnalisé
        print("➕ Démonstration 7: Mode personnalisé")
        custom_mode = {
            "duration": 90,
            "intensity": 70,
            "description": "Humidification tropicale"
        }
        success = controller.add_mist_mode("tropical", custom_mode)
        print(f"   Ajout mode 'tropical': {'✅ Succès' if success else '❌ Échec'}")
        
        # Test du nouveau mode
        success = controller.run_mist_mode("tropical")
        print(f"   Test mode 'tropical': {'✅ Succès' if success else '❌ Échec'}")
        print()
        
        # Statut final
        print("📊 Statut final du contrôleur:")
        status = controller.get_status()
        print(f"   - Actif: {'Oui' if status['mist_active'] else 'Non'}")
        print(f"   - Intensité actuelle: {status['current_intensity']}%")
        print(f"   - Temps total d'utilisation: {status['total_usage_time']:.1f}s")
        print(f"   - Nombre d'erreurs: {status['error_count']}")
        print(f"   - Modes disponibles: {len(status['available_modes'])}")
        print()
        
        # Nettoyage
        controller.cleanup()
        
        print("✅ Démonstration terminée avec succès!")
        print("\n💡 Points clés du brumisateur ultrasonique:")
        print("   - Utilise un transducteur ultrasonique à 1.7MHz")
        print("   - Crée de la brume fine pour l'humidification")
        print("   - Contrôle d'intensité de 0 à 100%")
        print("   - Modes prédéfinis pour différents besoins")
        print("   - Sécurités intégrées (temps max, pauses)")
        print("   - Compatible avec l'API REST")
        
    except Exception as e:
        logger.exception("Erreur lors de la démonstration")
        print(f"\n❌ Erreur: {e}")
        return False
    
    return True

def demo_api_endpoints():
    """Démonstration des endpoints API"""
    print("\n🌐 Endpoints API disponibles:")
    print("=" * 30)
    
    endpoints = [
        ("GET", "/api/ultrasonic-mist/status", "Statut du brumisateur"),
        ("POST", "/api/ultrasonic-mist/activate", "Activer le brumisateur"),
        ("POST", "/api/ultrasonic-mist/deactivate", "Désactiver le brumisateur"),
        ("POST", "/api/ultrasonic-mist/mode/{mode}", "Exécuter un mode"),
        ("POST", "/api/ultrasonic-mist/emergency-stop", "Arrêt d'urgence")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"  {method:6} {endpoint:<35} {description}")
    
    print("\n📝 Exemples d'utilisation:")
    print("  curl -X POST 'http://localhost:8000/api/ultrasonic-mist/activate' \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"intensity\": 60, \"duration\": 30}'")
    print()
    print("  curl -X POST 'http://localhost:8000/api/ultrasonic-mist/mode/medium'")

if __name__ == "__main__":
    print("🌊 Démonstration du brumisateur ultrasonique")
    print("=" * 60)
    
    # Démonstration principale
    success = demo_ultrasonic_mist()
    
    # Démonstration des endpoints API
    demo_api_endpoints()
    
    if success:
        print("\n🎉 Démonstration réussie!")
        sys.exit(0)
    else:
        print("\n💥 Démonstration échouée!")
        sys.exit(1)
