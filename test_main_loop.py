#!/usr/bin/env python3
"""
Test du MainLoop pour vérifier s'il démarre correctement
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.event_bus import EventBus
from src.services.safety_service import SafetyService
from src.loops.main_loop import MainLoop

def test_main_loop():
    """Test du MainLoop"""
    
    print("🔄 Test du MainLoop")
    print("=" * 30)
    
    try:
        # Initialisation du bus d'événements
        event_bus = EventBus()
        print("✅ Bus d'événements initialisé")
        
        # Initialisation du service de sécurité
        safety_service = SafetyService(event_bus)
        print("✅ Service de sécurité initialisé")
        
        # Initialisation de la boucle principale
        main_loop = MainLoop(event_bus, safety_service)
        print("✅ MainLoop initialisé")
        
        # Test d'initialisation
        if main_loop.initialize():
            print("✅ MainLoop initialisé avec succès")
        else:
            print("❌ Échec initialisation MainLoop")
            return False
        
        # Test de démarrage
        if main_loop.start():
            print("✅ MainLoop démarré avec succès")
            
            # Arrêter le MainLoop
            main_loop.stop()
            print("✅ MainLoop arrêté")
            return True
        else:
            print("❌ Échec démarrage MainLoop")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_main_loop()
