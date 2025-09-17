#!/usr/bin/env python3
"""
Test du ComponentControlService pour diagnostiquer les erreurs
"""

import sys
import os
import logging

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_component_service():
    """Test du ComponentControlService"""
    print("🔧 Test du ComponentControlService")
    print("=" * 50)
    
    try:
        # Import du service
        print("1. Import du ComponentControlService...")
        from services.component_control_service import ComponentControlService, ComponentType
        print("   ✅ Import réussi")
        
        # Initialisation du service
        print("2. Initialisation du service...")
        service = ComponentControlService()
        print("   ✅ Service initialisé")
        
        # Vérification des composants
        print("3. Vérification des composants...")
        print(f"   Composants disponibles: {list(service.components.keys())}")
        print(f"   Drivers disponibles: {list(service.drivers.keys())}")
        
        # Test du contrôle du servomoteur
        print("4. Test du contrôle du servomoteur...")
        if ComponentType.FEEDING in service.drivers and service.drivers[ComponentType.FEEDING]:
            print("   ✅ Driver servomoteur disponible")
            
            # Test de la commande feed
            print("5. Test de la commande 'feed'...")
            result = service.control_component("feeding", {"feed": True})
            print(f"   Résultat: {result}")
        else:
            print("   ❌ Driver servomoteur non disponible")
            print(f"   Drivers: {service.drivers}")
        
        # Test du contrôle de l'humidification
        print("6. Test du contrôle de l'humidification...")
        result = service.control_component("humidification", {"state": True, "target_humidity": 70})
        print(f"   Résultat: {result}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_component_service()
