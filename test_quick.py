#!/usr/bin/env python3
"""
Test rapide du TerrariumService
"""

import sys
import os
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_quick():
    """Test rapide"""
    print("🚀 Test rapide du TerrariumService")
    print("=" * 40)
    
    try:
        from services.terrarium_service import TerrariumService
        
        print("Création du service...")
        service = TerrariumService()
        
        print(f"Terrariums trouvés: {len(service.terrariums)}")
        for terrarium_id, terrarium in service.terrariums.items():
            print(f"  - {terrarium.get('name', 'Sans nom')} (ID: {terrarium_id})")
        
        print("✅ Test terminé!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quick()
