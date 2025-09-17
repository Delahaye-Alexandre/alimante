#!/usr/bin/env python3
"""
Debug du problème de chargement des terrariums
"""

import sys
import os
from pathlib import Path
import json

def debug_terrarium_loading():
    """Debug du chargement des terrariums"""
    print("🔍 Debug du chargement des terrariums")
    print("=" * 50)
    
    # Vérifier les chemins
    config_dir = Path(__file__).parent / 'config'
    terrariums_dir = config_dir / 'terrariums'
    species_dir = config_dir / 'species'
    
    print(f"1. Vérification des chemins:")
    print(f"   Config dir: {config_dir} (existe: {config_dir.exists()})")
    print(f"   Terrariums dir: {terrariums_dir} (existe: {terrariums_dir.exists()})")
    print(f"   Species dir: {species_dir} (existe: {species_dir.exists()})")
    
    # Vérifier les fichiers de terrariums
    if terrariums_dir.exists():
        config_files = list(terrariums_dir.glob('*.json'))
        print(f"\n2. Fichiers de terrariums trouvés: {len(config_files)}")
        for config_file in config_files:
            print(f"   - {config_file}")
            
            # Vérifier le contenu
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    terrarium_id = data.get('terrarium_id')
                    name = data.get('name', 'Sans nom')
                    species = data.get('species', {})
                    print(f"     → ID: {terrarium_id}")
                    print(f"     → Nom: {name}")
                    print(f"     → Espèce: {species.get('common_name', 'Non définie')}")
            except Exception as e:
                print(f"     → Erreur lecture: {e}")
    else:
        print("\n2. ❌ Répertoire terrariums n'existe pas!")
    
    # Vérifier les fichiers d'espèces
    if species_dir.exists():
        insects_dir = species_dir / 'insects'
        if insects_dir.exists():
            species_files = list(insects_dir.glob('*.json'))
            print(f"\n3. Fichiers d'espèces trouvés: {len(species_files)}")
            for species_file in species_files:
                print(f"   - {species_file}")
                try:
                    with open(species_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        species_id = data.get('species_id')
                        common_name = data.get('common_name')
                        print(f"     → ID: {species_id}")
                        print(f"     → Nom: {common_name}")
                except Exception as e:
                    print(f"     → Erreur lecture: {e}")
        else:
            print("\n3. ❌ Répertoire insects n'existe pas!")
    else:
        print("\n3. ❌ Répertoire species n'existe pas!")

if __name__ == "__main__":
    debug_terrarium_loading()
