#!/usr/bin/env python3
"""
Script de test pour vérifier les imports des modules web
"""

import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test des imports"""
    print("🧪 Test des imports des modules web")
    print("=" * 40)
    
    try:
        # Test 1: Imports des services
        print("1. Test des services...")
        from services.terrarium_service import TerrariumService
        from services.component_control_service import ComponentControlService, ComponentType, ControlMode
        print("   ✅ Services importés avec succès")
        
        # Test 2: Imports de l'UI
        print("\n2. Test de l'interface utilisateur...")
        from ui.ui_controller import UIController
        from ui.web_interface import WebInterface
        print("   ✅ Interface utilisateur importée avec succès")
        
        # Test 3: Création des instances
        print("\n3. Test de création des instances...")
        from utils.event_bus import EventBus
        
        event_bus = EventBus()
        terrarium_service = TerrariumService(event_bus)
        component_service = ComponentControlService(event_bus)
        print("   ✅ Instances créées avec succès")
        
        # Test 4: Vérification des méthodes
        print("\n4. Test des méthodes...")
        terrariums = terrarium_service.get_terrariums()
        components = component_service.get_all_components_status()
        print(f"   ✅ Méthodes fonctionnent (terrariums: {len(terrariums)}, composants: {len(components)})")
        
        print("\n🎉 Tous les imports et tests passent!")
        return True
        
    except ImportError as e:
        print(f"   ❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_imports()
