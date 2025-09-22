#!/usr/bin/env python3
"""
Test des fonctionnalités de caméra et streaming Alimante
Vérifie que tous les services de caméra fonctionnent correctement
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services import (
    CameraService,
    StreamingService,
    SnapshotService,
    AlertService,
    StreamFormat,
    StreamQuality,
    SnapshotType,
    AlertSeverity,
    AlertStatus
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

def test_streaming_service():
    """Test du service de streaming"""
    print("\n📺 TEST DU SERVICE DE STREAMING")
    print("=" * 50)
    
    try:
        # Configuration
        config = {
            'streaming': {
                'enabled': True,
                'port': 8081,  # Port différent pour éviter les conflits
                'host': '127.0.0.1',
                'max_clients': 5,
                'width': 640,
                'height': 480,
                'fps': 30,
                'quality': 80,
                'format': 'mjpeg',
                'recording_path': 'data/test_recordings',
                'recording_duration': 60
            }
        }
        
        # Initialiser le service
        streaming = StreamingService(config)
        
        if not streaming.initialize():
            print("❌ Échec initialisation service streaming")
            return False
        
        print("✅ Service streaming initialisé")
        
        # Test de démarrage
        if streaming.start():
            print("✅ Service streaming démarré")
        else:
            print("❌ Échec démarrage service streaming")
            return False
        
        # Test d'enregistrement
        if streaming.start_recording():
            print("✅ Enregistrement démarré")
        else:
            print("❌ Échec démarrage enregistrement")
            return False
        
        # Attendre un peu
        time.sleep(2)
        
        if streaming.stop_recording():
            print("✅ Enregistrement arrêté")
        else:
            print("❌ Échec arrêt enregistrement")
            return False
        
        # Test du statut
        status = streaming.get_status()
        print(f"✅ Statut: {status['is_running']}")
        print(f"✅ URL: {status['stream_url']}")
        print(f"✅ Clients: {status['clients_connected']}")
        
        # Nettoyage
        streaming.cleanup()
        print("✅ Service streaming nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test service streaming: {e}")
        return False

def test_snapshot_service():
    """Test du service de snapshots"""
    print("\n📸 TEST DU SERVICE DE SNAPSHOTS")
    print("=" * 50)
    
    try:
        # Configuration
        config = {
            'snapshots': {
                'enabled': True,
                'storage_path': 'data/test_snapshots',
                'max_snapshots': 10,
                'retention_days': 7,
                'width': 640,
                'height': 480,
                'quality': 90,
                'format': 'jpg',
                'annotate': True,
                'show_timestamp': True,
                'show_sensors': True,
                'show_terrarium': True
            }
        }
        
        # Initialiser le service
        snapshots = SnapshotService(config)
        
        if not snapshots.initialize():
            print("❌ Échec initialisation service snapshots")
            return False
        
        print("✅ Service snapshots initialisé")
        
        # Test de démarrage
        if snapshots.start():
            print("✅ Service snapshots démarré")
        else:
            print("❌ Échec démarrage service snapshots")
            return False
        
        # Test de prise de snapshot manuel
        metadata = {
            'terrarium': 'test_terrarium',
            'sensors': {
                'temperature': 25.5,
                'humidity': 60.0
            },
            'systems': {
                'heating': True,
                'lighting': False
            }
        }
        
        snapshot_path = snapshots.take_snapshot(
            SnapshotType.MANUAL,
            annotate=True,
            metadata=metadata
        )
        
        if snapshot_path:
            print(f"✅ Snapshot manuel pris: {snapshot_path}")
        else:
            print("❌ Échec prise snapshot manuel")
            return False
        
        # Test de prise de snapshot de mouvement
        snapshot_path = snapshots.take_snapshot(
            SnapshotType.MOTION,
            annotate=True,
            metadata=metadata
        )
        
        if snapshot_path:
            print(f"✅ Snapshot mouvement pris: {snapshot_path}")
        else:
            print("❌ Échec prise snapshot mouvement")
            return False
        
        # Test de récupération des snapshots
        latest_snapshots = snapshots.get_latest_snapshots(5)
        print(f"✅ Snapshots récupérés: {len(latest_snapshots)}")
        
        # Test des informations de stockage
        storage_info = snapshots.get_storage_info()
        print(f"✅ Fichiers stockés: {storage_info['total_files']}")
        print(f"✅ Taille: {storage_info['total_size_mb']:.2f} MB")
        
        # Test du statut
        status = snapshots.get_status()
        print(f"✅ Statut: {status['is_running']}")
        print(f"✅ Snapshots: {status['snapshot_count']}")
        
        # Nettoyage
        snapshots.cleanup()
        print("✅ Service snapshots nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test service snapshots: {e}")
        return False

def test_alert_service():
    """Test du service d'alertes"""
    print("\n🚨 TEST DU SERVICE D'ALERTES")
    print("=" * 50)
    
    try:
        # Configuration
        config = {
            'alerts': {
                'enabled': True,
                'max_alerts': 100,
                'retention_days': 7,
                'auto_acknowledge_delay': 300,
                'notifications_enabled': True,
                'email_enabled': False,
                'sms_enabled': False,
                'webhook_enabled': False
            }
        }
        
        # Initialiser le service
        alerts = AlertService(config)
        
        if not alerts.initialize():
            print("❌ Échec initialisation service alertes")
            return False
        
        print("✅ Service alertes initialisé")
        
        # Test de démarrage
        if alerts.start():
            print("✅ Service alertes démarré")
        else:
            print("❌ Échec démarrage service alertes")
            return False
        
        # Test de création d'alerte info
        alert_id = alerts.create_alert(
            "TEMP_HIGH",
            "Température élevée détectée",
            AlertSeverity.INFO,
            terrarium_id="test_terrarium",
            component="heating",
            value=30.5,
            threshold=30.0
        )
        
        if alert_id:
            print(f"✅ Alerte info créée: {alert_id}")
        else:
            print("❌ Échec création alerte info")
            return False
        
        # Test de création d'alerte critique
        alert_id_critical = alerts.create_alert(
            "SENSOR_FAIL",
            "Capteur de température défaillant",
            AlertSeverity.CRITICAL,
            terrarium_id="test_terrarium",
            component="temperature_sensor"
        )
        
        if alert_id_critical:
            print(f"✅ Alerte critique créée: {alert_id_critical}")
        else:
            print("❌ Échec création alerte critique")
            return False
        
        # Test d'accusé réception
        if alerts.acknowledge_alert(alert_id, "test_user"):
            print("✅ Alerte accusée")
        else:
            print("❌ Échec accusé réception alerte")
            return False
        
        # Test de résolution
        if alerts.resolve_alert(alert_id, "test_user"):
            print("✅ Alerte résolue")
        else:
            print("❌ Échec résolution alerte")
            return False
        
        # Test de récupération des alertes
        active_alerts = alerts.get_alerts(AlertStatus.ACTIVE)
        print(f"✅ Alertes actives: {len(active_alerts)}")
        
        critical_alerts = alerts.get_alerts(severity=AlertSeverity.CRITICAL)
        print(f"✅ Alertes critiques: {len(critical_alerts)}")
        
        # Test du statut
        status = alerts.get_status()
        print(f"✅ Statut: {status['is_running']}")
        print(f"✅ Total alertes: {status['total_alerts']}")
        print(f"✅ Alertes actives: {status['active_alerts']}")
        print(f"✅ Alertes critiques: {status['critical_alerts']}")
        
        # Nettoyage
        alerts.cleanup()
        print("✅ Service alertes nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test service alertes: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST DES FONCTIONNALITÉS DE CAMÉRA ET STREAMING")
    print("=" * 70)
    
    tests = [
        test_camera_service,
        test_streaming_service,
        test_snapshot_service,
        test_alert_service
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
        print("Les fonctionnalités de caméra et streaming fonctionnent correctement.")
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
