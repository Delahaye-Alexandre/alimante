#!/usr/bin/env python3
"""
Test des services Alimante
Vérifie que tous les services fonctionnent correctement
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services import (
    CameraService,
    SchedulerService,
    SyncService,
    UIService,
    TaskType,
    TaskStatus,
    SyncStatus,
    SyncType,
    UIMode,
    UIScreen
)

def test_camera_service():
    """Test du service de caméra"""
    print("📷 TEST DU SERVICE DE CAMÉRA")
    print("=" * 50)
    
    try:
        # Configuration
        config = {
            'camera': {
                'capture_interval': 10,
                'capture_path': 'data/test_captures',
                'max_captures': 10,
                'quality': 80,
                'motion_threshold': 0.1,
                'motion_sensitivity': 0.5
            }
        }
        
        # Initialiser le service
        camera = CameraService(config)
        
        if not camera.initialize():
            print("❌ Échec initialisation service caméra")
            return False
        
        print("✅ Service caméra initialisé")
        
        # Test de démarrage
        if camera.start():
            print("✅ Service caméra démarré")
        else:
            print("❌ Échec démarrage service caméra")
            return False
        
        # Test de capture d'image
        if camera.capture_image("test"):
            print("✅ Capture d'image réussie")
        else:
            print("❌ Échec capture d'image")
            return False
        
        # Test de détection de mouvement
        if camera.start_motion_detection(0.1):
            print("✅ Détection de mouvement activée")
        else:
            print("❌ Échec activation détection mouvement")
            return False
        
        if camera.stop_motion_detection():
            print("✅ Détection de mouvement désactivée")
        else:
            print("❌ Échec désactivation détection mouvement")
            return False
        
        # Test du statut
        status = camera.get_status()
        print(f"✅ Statut: {status['is_running']}")
        print(f"✅ Captures: {status['capture_count']}")
        
        # Nettoyage
        camera.cleanup()
        print("✅ Service caméra nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test service caméra: {e}")
        return False

def test_scheduler_service():
    """Test du service de planification"""
    print("\n⏰ TEST DU SERVICE DE PLANIFICATION")
    print("=" * 50)
    
    try:
        # Configuration
        config = {
            'scheduler': {
                'check_interval': 1.0,
                'max_concurrent_tasks': 3
            }
        }
        
        # Initialiser le service
        scheduler = SchedulerService(config)
        
        if not scheduler.initialize():
            print("❌ Échec initialisation service planification")
            return False
        
        print("✅ Service planification initialisé")
        
        # Test de démarrage
        if scheduler.start():
            print("✅ Service planification démarré")
        else:
            print("❌ Échec démarrage service planification")
            return False
        
        # Test d'ajout de tâche unique
        def test_task():
            print("  → Tâche de test exécutée")
            return "success"
        
        task_id = scheduler.add_task(
            "Test Task",
            TaskType.ONCE,
            test_task,
            args=(),
            kwargs={}
        )
        
        if task_id:
            print(f"✅ Tâche unique ajoutée: {task_id}")
        else:
            print("❌ Échec ajout tâche unique")
            return False
        
        # Test d'ajout de tâche récurrente
        def recurring_task():
            print("  → Tâche récurrente exécutée")
            return "recurring_success"
        
        recurring_task_id = scheduler.add_task(
            "Recurring Task",
            TaskType.INTERVAL,
            recurring_task,
            interval_seconds=5
        )
        
        if recurring_task_id:
            print(f"✅ Tâche récurrente ajoutée: {recurring_task_id}")
        else:
            print("❌ Échec ajout tâche récurrente")
            return False
        
        # Attendre l'exécution des tâches
        time.sleep(6)
        
        # Test de statut des tâches
        task_status = scheduler.get_task_status(task_id)
        if task_status:
            print(f"✅ Statut tâche unique: {task_status['status']}")
        else:
            print("❌ Échec récupération statut tâche")
            return False
        
        # Test d'annulation de tâche
        if scheduler.cancel_task(recurring_task_id):
            print("✅ Tâche récurrente annulée")
        else:
            print("❌ Échec annulation tâche")
            return False
        
        # Test du statut
        status = scheduler.get_status()
        print(f"✅ Statut: {status['is_running']}")
        print(f"✅ Tâches totales: {status['total_tasks']}")
        
        # Nettoyage
        scheduler.cleanup()
        print("✅ Service planification nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test service planification: {e}")
        return False

def test_sync_service():
    """Test du service de synchronisation"""
    print("\n☁️ TEST DU SERVICE DE SYNCHRONISATION")
    print("=" * 50)
    
    try:
        # Configuration
        config = {
            'sync': {
                'enabled': True,
                'sync_interval': 30,
                'retry_interval': 10,
                'max_retries': 2,
                'cloud': {
                    'enabled': False,  # Désactivé pour le test
                    'api_url': 'https://api.example.com',
                    'api_key': 'test_key',
                    'device_id': 'test_device'
                },
                'tunnel': {
                    'enabled': False,  # Désactivé pour le test
                    'url': 'https://tunnel.example.com',
                    'token': 'test_token'
                }
            }
        }
        
        # Initialiser le service
        sync = SyncService(config)
        
        if not sync.initialize():
            print("❌ Échec initialisation service synchronisation")
            return False
        
        print("✅ Service synchronisation initialisé")
        
        # Test de démarrage
        if sync.start():
            print("✅ Service synchronisation démarré")
        else:
            print("❌ Échec démarrage service synchronisation")
            return False
        
        # Test de synchronisation forcée
        if sync.force_sync():
            print("✅ Synchronisation forcée lancée")
        else:
            print("❌ Échec synchronisation forcée")
            return False
        
        # Attendre un peu
        time.sleep(2)
        
        # Test du statut
        status = sync.get_status()
        print(f"✅ Statut: {status['status']}")
        print(f"✅ Activé: {status['enabled']}")
        print(f"✅ En cours: {status['is_running']}")
        
        # Nettoyage
        sync.cleanup()
        print("✅ Service synchronisation nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test service synchronisation: {e}")
        return False

def test_ui_service():
    """Test du service d'interface utilisateur"""
    print("\n🖥️ TEST DU SERVICE D'INTERFACE UTILISATEUR")
    print("=" * 50)
    
    try:
        # Configuration
        config = {
            'ui': {
                'lcd_enabled': True,
                'encoder_enabled': True,
                'auto_refresh': True,
                'refresh_interval': 1.0
            }
        }
        
        # Initialiser le service
        ui = UIService(config)
        
        if not ui.initialize():
            print("❌ Échec initialisation service UI")
            return False
        
        print("✅ Service UI initialisé")
        
        # Test de démarrage
        if ui.start():
            print("✅ Service UI démarré")
        else:
            print("❌ Échec démarrage service UI")
            return False
        
        # Test de changement d'écran
        ui.set_screen(UIScreen.SENSORS)
        print("✅ Écran changé vers SENSORS")
        
        ui.set_screen(UIScreen.CONTROLS)
        print("✅ Écran changé vers CONTROLS")
        
        # Test de changement de mode
        ui.set_mode(UIMode.MANUAL)
        print("✅ Mode changé vers MANUAL")
        
        ui.set_mode(UIMode.AUTO)
        print("✅ Mode changé vers AUTO")
        
        # Test de mise à jour des données
        test_data = {
            'temperature': 25.5,
            'humidity': 60.0,
            'air_quality': 75.0,
            'heating': True,
            'humidifying': False
        }
        
        ui.update_display_data(test_data)
        print("✅ Données d'affichage mises à jour")
        
        # Test du statut
        status = ui.get_status()
        print(f"✅ Statut: {status['is_running']}")
        print(f"✅ Mode actuel: {status['current_mode']}")
        print(f"✅ Écran actuel: {status['current_screen']}")
        
        # Nettoyage
        ui.cleanup()
        print("✅ Service UI nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test service UI: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST DES SERVICES ALIMANTE")
    print("=" * 60)
    
    tests = [
        test_camera_service,
        test_scheduler_service,
        test_sync_service,
        test_ui_service
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
        print("Les services fonctionnent correctement.")
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
