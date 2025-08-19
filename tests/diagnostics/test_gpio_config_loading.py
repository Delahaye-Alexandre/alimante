#!/usr/bin/env python3
"""
Test simple de chargement de la configuration GPIO
"""

import json
import sys
import os

# Ajouter le chemin du projet aux chemins Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_gpio_config_loading():
    """Test de chargement de la configuration GPIO"""
    print("🧪 Test de chargement de la configuration GPIO")
    print("=" * 50)
    
    # Essayer plusieurs chemins possibles
    possible_paths = [
        'config/gpio_config.json',
        '../../config/gpio_config.json',
        '../config/gpio_config.json'
    ]
    
    config = None
    used_path = None
    
    for path in possible_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                used_path = path
                print(f"✅ Configuration chargée depuis: {path}")
                break
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé: {path}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON dans {path}: {e}")
        except Exception as e:
            print(f"❌ Erreur inattendue avec {path}: {e}")
    
    if config is None:
        print("❌ Impossible de charger la configuration GPIO")
        return False
    
    # Vérifier la structure
    print(f"\n📋 Structure de la configuration:")
    print(f"   - gpio_pins: {'✅' if 'gpio_pins' in config else '❌'}")
    print(f"   - pin_assignments: {'✅' if 'pin_assignments' in config else '❌'}")
    print(f"   - power_supply: {'✅' if 'power_supply' in config else '❌'}")
    
    if 'gpio_pins' in config:
        gpio_pins = config['gpio_pins']
        print(f"\n🔌 Sections GPIO:")
        for section in ['sensors', 'actuators', 'interface', 'status', 'led_strip']:
            if section in gpio_pins:
                count = len(gpio_pins[section]) if isinstance(gpio_pins[section], dict) else 0
                print(f"   - {section}: {count} composants")
            else:
                print(f"   - {section}: ❌ manquant")
    
    print(f"\n✅ Test de chargement réussi!")
    return True

if __name__ == '__main__':
    test_gpio_config_loading()
