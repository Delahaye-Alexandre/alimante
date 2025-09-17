#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les problèmes web
"""

import sys
import os
import traceback

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_web_issue():
    """Diagnostic des problèmes web"""
    print("🔍 Diagnostic des problèmes web Alimante")
    print("=" * 50)
    
    # Test 1: Vérifier les imports de base
    print("1. Test des imports de base...")
    try:
        from utils.event_bus import EventBus
        print("   ✅ EventBus importé")
    except Exception as e:
        print(f"   ❌ Erreur EventBus: {e}")
        traceback.print_exc()
        return False
    
    # Test 2: Vérifier les services
    print("\n2. Test des services...")
    try:
        from services.terrarium_service import TerrariumService
        print("   ✅ TerrariumService importé")
        
        from services.component_control_service import ComponentControlService
        print("   ✅ ComponentControlService importé")
    except Exception as e:
        print(f"   ❌ Erreur services: {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Vérifier l'UI
    print("\n3. Test de l'interface utilisateur...")
    try:
        from ui.ui_controller import UIController
        print("   ✅ UIController importé")
        
        from ui.web_interface import WebInterface
        print("   ✅ WebInterface importé")
    except Exception as e:
        print(f"   ❌ Erreur UI: {e}")
        traceback.print_exc()
        return False
    
    # Test 4: Créer les instances
    print("\n4. Test de création des instances...")
    try:
        event_bus = EventBus()
        print("   ✅ EventBus créé")
        
        terrarium_service = TerrariumService(event_bus)
        print("   ✅ TerrariumService créé")
        
        component_service = ComponentControlService(event_bus)
        print("   ✅ ComponentControlService créé")
        
        ui_controller = UIController(event_bus)
        print("   ✅ UIController créé")
        
    except Exception as e:
        print(f"   ❌ Erreur création instances: {e}")
        traceback.print_exc()
        return False
    
    # Test 5: Vérifier les services dans l'UI
    print("\n5. Test des services dans l'UI...")
    try:
        if hasattr(ui_controller, 'terrarium_service'):
            print("   ✅ terrarium_service présent dans UIController")
        else:
            print("   ❌ terrarium_service manquant dans UIController")
        
        if hasattr(ui_controller, 'component_control_service'):
            print("   ✅ component_control_service présent dans UIController")
        else:
            print("   ❌ component_control_service manquant dans UIController")
        
        if hasattr(ui_controller, 'web_interface'):
            print("   ✅ web_interface présent dans UIController")
            
            if hasattr(ui_controller.web_interface, 'terrarium_service'):
                print("   ✅ terrarium_service présent dans WebInterface")
            else:
                print("   ❌ terrarium_service manquant dans WebInterface")
                
            if hasattr(ui_controller.web_interface, 'component_control_service'):
                print("   ✅ component_control_service présent dans WebInterface")
            else:
                print("   ❌ component_control_service manquant dans WebInterface")
        else:
            print("   ❌ web_interface manquant dans UIController")
            
    except Exception as e:
        print(f"   ❌ Erreur vérification services: {e}")
        traceback.print_exc()
        return False
    
    print("\n🎉 Diagnostic terminé!")
    return True

if __name__ == "__main__":
    debug_web_issue()
