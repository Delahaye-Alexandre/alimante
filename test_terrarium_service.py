#!/usr/bin/env python3
"""
Test direct du TerrariumService
"""

import sys
import os
import logging

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_terrarium_service():
    """Test direct du TerrariumService"""
    print("🧪 Test direct du TerrariumService")
    print("=" * 50)
    
    try:
        from services.terrarium_service import TerrariumService
        
        print("1. Création du service...")
        service = TerrariumService()
        
        print("2. Test des méthodes...")
        terrariums = service.get_terrariums()
        print(f"   📊 Terrariums trouvés: {len(terrariums)}")
        
        for terrarium in terrariums:
            print(f"      - {terrarium.get('name', 'Sans nom')} (ID: {terrarium.get('id', 'N/A')})")
            species = terrarium.get('species', {})
            print(f"        → Espèce: {species.get('common_name', 'Non définie')}")
        
        current = service.get_current_terrarium()
        if current:
            print(f"   🎯 Terrarium actuel: {current.get('name', 'Sans nom')}")
        else:
            print("   ❌ Aucun terrarium actuel")
        
        species_list = service.get_species_list()
        print(f"   🐛 Espèces disponibles: {len(species_list)}")
        for specie in species_list:
            print(f"      - {specie.get('name', 'Sans nom')} ({specie.get('scientific_name', 'N/A')})")
        
        print("\n✅ Test terminé!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_terrarium_service()
