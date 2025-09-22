#!/usr/bin/env python3
"""
Test du service de configuration Alimante
Vérifie que le ConfigService fonctionne correctement
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services import ConfigService

def test_config_service():
    """Test du service de configuration"""
    print("⚙️ TEST DU SERVICE DE CONFIGURATION")
    print("=" * 50)
    
    try:
        # Initialiser le service
        config_service = ConfigService()
        
        # Test de chargement de la configuration principale
        main_config = config_service.load_config('main')
        if main_config:
            print("✅ Configuration principale chargée")
            print(f"   Application: {main_config.get('application', {}).get('name', 'N/A')}")
            print(f"   Version: {main_config.get('application', {}).get('version', 'N/A')}")
        else:
            print("❌ Échec chargement configuration principale")
            return False
        
        # Test de chargement des valeurs hardcodées
        hardcoded_config = config_service.load_config('hardcoded')
        if hardcoded_config:
            print("✅ Configuration hardcodée chargée")
            print(f"   Services configurés: {len(hardcoded_config.get('services', {}))}")
            print(f"   Contrôleurs configurés: {len(hardcoded_config.get('controllers', {}))}")
            print(f"   Drivers configurés: {len(hardcoded_config.get('drivers', {}))}")
        else:
            print("❌ Échec chargement configuration hardcodée")
            return False
        
        # Test de récupération de valeurs hardcodées
        camera_quality = config_service.get_hardcoded_value("services.camera.quality", 80)
        print(f"✅ Qualité caméra: {camera_quality}")
        
        streaming_port = config_service.get_hardcoded_value("services.streaming.port", 8080)
        print(f"✅ Port streaming: {streaming_port}")
        
        max_alerts = config_service.get_hardcoded_value("services.alerts.max_alerts", 1000)
        print(f"✅ Max alertes: {max_alerts}")
        
        # Test de récupération de configuration de service
        camera_config = config_service.get_service_config('camera')
        if camera_config:
            print("✅ Configuration service caméra récupérée")
            print(f"   Intervalle capture: {camera_config.get('capture_interval', 'N/A')}")
            print(f"   Qualité: {camera_config.get('quality', 'N/A')}")
        else:
            print("❌ Échec récupération configuration service caméra")
            return False
        
        # Test de récupération de configuration de contrôleur
        heater_config = config_service.get_controller_config('heater')
        if heater_config:
            print("✅ Configuration contrôleur chauffage récupérée")
            print(f"   Température max: {heater_config.get('max_temperature', 'N/A')}")
            print(f"   Hystérésis: {heater_config.get('hysteresis', 'N/A')}")
        else:
            print("❌ Échec récupération configuration contrôleur chauffage")
            return False
        
        # Test de récupération de configuration de driver
        camera_driver_config = config_service.get_driver_config('camera')
        if camera_driver_config:
            print("✅ Configuration driver caméra récupérée")
            print(f"   Largeur: {camera_driver_config.get('width', 'N/A')}")
            print(f"   Hauteur: {camera_driver_config.get('height', 'N/A')}")
        else:
            print("❌ Échec récupération configuration driver caméra")
            return False
        
        # Test de récupération de timeouts
        thread_join_timeout = config_service.get_timeout('thread_join', 5.0)
        print(f"✅ Timeout join thread: {thread_join_timeout}")
        
        # Test de récupération d'intervalles
        cleanup_interval = config_service.get_interval('cleanup_wait', 3600)
        print(f"✅ Intervalle nettoyage: {cleanup_interval}")
        
        # Test de récupération de chemins
        captures_path = config_service.get_path('captures', 'data/captures')
        print(f"✅ Chemin captures: {captures_path}")
        
        # Test de récupération de configuration matérielle
        servo_positions = config_service.get_hardware_config('servo_positions')
        if servo_positions:
            print("✅ Configuration matérielle servo récupérée")
            print(f"   Position fermée: {servo_positions.get('closed', 'N/A')}")
            print(f"   Position ouverte: {servo_positions.get('open', 'N/A')}")
        else:
            print("❌ Échec récupération configuration matérielle servo")
            return False
        
        # Test du statut
        status = config_service.get_status()
        print("✅ Statut du service:")
        print(f"   Répertoire config: {status['config_dir']}")
        print(f"   Configurations en cache: {len(status['cached_configs'])}")
        print(f"   Configurations disponibles: {len(status['available_configs'])}")
        print(f"   Valeurs hardcodées chargées: {status['hardcoded_loaded']}")
        
        print("\\n🎉 Tous les tests du service de configuration ont réussi!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test service configuration: {e}")
        return False

def test_config_validation():
    """Test de validation des configurations"""
    print("\\n🔍 TEST DE VALIDATION DES CONFIGURATIONS")
    print("=" * 50)
    
    try:
        config_service = ConfigService()
        
        # Test de validation d'une configuration valide
        valid_config = {
            'application': {
                'name': 'Alimante',
                'version': '0.1.0'
            },
            'system': {
                'platform': 'raspberry_pi'
            }
        }
        
        schema = {
            'application': {
                'name': str,
                'version': str
            },
            'system': {
                'platform': str
            }
        }
        
        if config_service.validate_config(valid_config, schema):
            print("✅ Validation configuration valide réussie")
        else:
            print("❌ Échec validation configuration valide")
            return False
        
        # Test de validation d'une configuration invalide
        invalid_config = {
            'application': {
                'name': 'Alimante'
                # version manquante
            }
        }
        
        if not config_service.validate_config(invalid_config, schema):
            print("✅ Validation configuration invalide détectée")
        else:
            print("❌ Échec détection configuration invalide")
            return False
        
        print("\\n🎉 Tests de validation réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test validation: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST DU SERVICE DE CONFIGURATION")
    print("=" * 70)
    
    tests = [
        test_config_service,
        test_config_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Ligne vide entre les tests
    
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 30)
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 TOUS LES TESTS RÉUSSIS !")
        print("Le service de configuration fonctionne correctement.")
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
