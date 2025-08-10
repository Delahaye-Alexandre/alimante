#!/usr/bin/env python3
"""
Test rapide des composants Alimante
Permet de tester les composants individuellement
"""

import sys
import time
import json
import os

# Ajouter le répertoire src au path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from component_test import ComponentTester, TestStatus

def test_single_component(component_name: str):
    """Teste un composant spécifique"""
    tester = ComponentTester()
    
    # Mapping des noms de composants vers les méthodes de test
    test_methods = {
        "gpio": tester.test_gpio_setup,
        "dht22": tester.test_dht22,
        "mq2": tester.test_mq2_sensor,
        "servo": tester.test_servo,
        "transducer": tester.test_transducers,
        "camera": tester.test_camera,
        "display": tester.test_display,
        "mosfet": tester.test_mosfet,
        "fans": tester.test_fans,
        "adc": tester.test_adc
    }
    
    if component_name not in test_methods:
        print(f"❌ Composant '{component_name}' non reconnu")
        print("Composants disponibles:", list(test_methods.keys()))
        return
    
    print(f"🔧 Test du composant: {component_name}")
    print("=" * 40)
    
    try:
        result = test_methods[component_name]()
        status_icon = "✅" if result.status == TestStatus.PASSED else "❌"
        print(f"{status_icon} {result.component}: {result.message}")
        
        if result.data:
            print("📊 Données:", json.dumps(result.data, indent=2))
        
        print(f"⏱️  Durée: {result.duration:.2f}s")
        
    except Exception as e:
        print(f"💥 Erreur lors du test: {e}")
    finally:
        tester.cleanup()

def list_components():
    """Liste tous les composants disponibles"""
    components = [
        "gpio - Configuration GPIO",
        "dht22 - Capteur température/humidité",
        "mq2 - Capteur qualité air",
        "servo - Servomoteur",
        "transducer - Transducteur brume",
        "camera - Caméra CSI",
        "display - Écran TFT",
        "mosfet - MOSFET",
        "fans - Ventilateurs (4x)",
        "adc - Convertisseur ADC"
    ]
    
    print("📋 Composants disponibles:")
    for comp in components:
        print(f"  {comp}")

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("🔧 Test rapide des composants Alimante")
        print("=" * 50)
        print("Usage:")
        print("  python3 quick_test.py <composant>")
        print("  python3 quick_test.py list")
        print("  python3 quick_test.py all")
        print()
        list_components()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_components()
    elif command == "all":
        print("🔧 Test de tous les composants")
        print("=" * 50)
        tester = ComponentTester()
        try:
            summary = tester.run_all_tests()
            tester.save_results("quick_test_results.json")
        finally:
            tester.cleanup()
    else:
        test_single_component(command)

if __name__ == "__main__":
    main() 