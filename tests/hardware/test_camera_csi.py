#!/usr/bin/env python3
"""
Test du contrôleur de caméra CSI
"""

import sys
import os
import time
sys.path.insert(0, '.')

from src.controllers.camera_controller import CameraController

def test_camera_controller():
    """Test le contrôleur de caméra CSI"""
    print("📸 Test du contrôleur caméra CSI")
    print("=" * 50)
    
    try:
        # Configuration de test
        camera_config = {
            "type": "CSI",
            "resolution": "1920x1080",
            "framerate": 30,
            "format": "MJPEG",
            "stream_port": 8080
        }
        
        # Créer le contrôleur
        camera_controller = CameraController(camera_config)
        print("✅ Contrôleur caméra créé")
        
        # Test 1: Statut du contrôleur
        print("\n📊 Test du statut...")
        status = camera_controller.get_status()
        print(f"   Type de caméra: {status['camera_type']}")
        print(f"   Bibliothèque: {status['library']}")
        print(f"   Résolution: {status['resolution']}")
        print(f"   Framerate: {status['framerate']}fps")
        print(f"   Initialisée: {status['is_initialized']}")
        print(f"   Streaming: {status['is_streaming']}")
        print(f"   Captures: {status['capture_count']}")
        
        # Test 2: Vérification du statut
        print("\n🔍 Test de vérification du statut...")
        status_ok = camera_controller.check_status()
        print(f"   Statut OK: {status_ok}")
        
        if not status_ok:
            print("❌ Caméra non opérationnelle")
            return False
        
        # Test 3: Capture d'image
        print("\n📷 Test de capture d'image...")
        try:
            image_data = camera_controller.capture_image()
            print(f"   ✅ Image capturée: {len(image_data)} bytes")
        except Exception as e:
            print(f"   ❌ Erreur capture: {e}")
        
        # Test 4: Snapshot avec sauvegarde
        print("\n💾 Test de snapshot...")
        try:
            snapshot_path = camera_controller.take_snapshot()
            print(f"   ✅ Snapshot sauvegardé: {snapshot_path}")
        except Exception as e:
            print(f"   ❌ Erreur snapshot: {e}")
        
        # Test 5: Streaming
        print("\n🎬 Test de streaming...")
        try:
            # Démarrer streaming
            success = camera_controller.start_streaming()
            print(f"   Démarrage streaming: {'✅' if success else '❌'}")
            
            if success:
                time.sleep(3)  # Laisser tourner 3 secondes
                
                # Arrêter streaming
                success = camera_controller.stop_streaming()
                print(f"   Arrêt streaming: {'✅' if success else '❌'}")
        except Exception as e:
            print(f"   ❌ Erreur streaming: {e}")
        
        # Test 6: Nettoyage
        print("\n🧹 Test de nettoyage...")
        camera_controller.cleanup()
        print("   ✅ Nettoyage effectué")
        
        print("\n🎉 Tous les tests de caméra terminés avec succès!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur dans les tests de caméra: {e}")
        return False

def test_camera_compatibility():
    """Test de compatibilité des bibliothèques de caméra"""
    print("\n🔧 Test de compatibilité des bibliothèques...")
    
    # Test Picamera2
    try:
        import picamera2
        print("   ✅ Picamera2 disponible")
        picamera2_available = True
    except ImportError:
        print("   ❌ Picamera2 non disponible")
        picamera2_available = False
    
    # Test OpenCV
    try:
        import cv2
        print("   ✅ OpenCV disponible")
        opencv_available = True
    except ImportError:
        print("   ❌ OpenCV non disponible")
        opencv_available = False
    
    if not picamera2_available and not opencv_available:
        print("   ⚠️  Aucune bibliothèque de caméra disponible")
        print("   📝 Installation recommandée:")
        print("      sudo apt install python3-picamera2")
        print("      pip install opencv-python")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Tests du système de caméra CSI")
    print("=" * 60)
    
    # Test de compatibilité
    if not test_camera_compatibility():
        print("\n❌ Tests annulés - problèmes de compatibilité")
        sys.exit(1)
    
    # Test du contrôleur
    success = test_camera_controller()
    
    if success:
        print("\n🎉 Tous les tests réussis!")
        sys.exit(0)
    else:
        print("\n❌ Certains tests ont échoué")
        sys.exit(1)
