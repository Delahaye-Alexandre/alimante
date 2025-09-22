#!/usr/bin/env python3
"""
Alimante - Système de gestion automatique de terrariums
Point d'entrée principal de l'application
"""

import sys
import os
import logging
from pathlib import Path

# Ajouter le répertoire src au path Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.loops.main_loop import MainLoop
from src.utils.event_bus import EventBus
from src.services.safety_service import SafetyService
from src.services.config_service import ConfigService
from src.services.camera_service import CameraService
from src.services.streaming_service import StreamingService
from src.services.snapshot_service import SnapshotService
from src.services.alert_service import AlertService
from src.services.monitoring_service import MonitoringService
from src.services.recovery_service import RecoveryService
from src.services.health_check_service import HealthCheckService
from src.ui.ui_controller import UIController

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('alimante.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Fonction principale"""
    print("🦎 Alimante - Système de gestion de terrariums")
    print("=" * 50)
    
    # Configuration du logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Chargement de la configuration
        import json
        config = {}
        try:
            with open('config/config.json', 'r') as f:
                config = json.load(f)
            logger.info("Configuration chargée")
        except Exception as e:
            logger.warning(f"Erreur chargement configuration: {e}")
            config = {}
        
        # Initialisation du bus d'événements
        event_bus = EventBus()
        logger.info("Bus d'événements initialisé")
        
        # Initialisation du service de configuration
        config_service = ConfigService()
        all_configs = config_service.load_all_configs()
        logger.info("Service de configuration initialisé")
        
        # Initialisation du service de sécurité
        safety_service = SafetyService(event_bus)
        logger.info("Service de sécurité initialisé")
        
        # Initialisation des services de caméra et streaming
        camera_service = CameraService(all_configs.get('main', {}), event_bus)
        if camera_service.initialize():
            logger.info("Service de caméra initialisé")
        else:
            logger.warning("Échec initialisation service de caméra")
        
        streaming_service = StreamingService(all_configs.get('main', {}), event_bus)
        if streaming_service.initialize():
            logger.info("Service de streaming initialisé")
        else:
            logger.warning("Échec initialisation service de streaming")
        
        snapshot_service = SnapshotService(all_configs.get('main', {}), event_bus)
        if snapshot_service.initialize():
            logger.info("Service de snapshots initialisé")
        else:
            logger.warning("Échec initialisation service de snapshots")
        
        alert_service = AlertService(all_configs.get('main', {}), event_bus)
        if alert_service.initialize():
            logger.info("Service d'alertes initialisé")
        else:
            logger.warning("Échec initialisation service d'alertes")
        
        # Initialisation des services de Phase 1 (gestion d'erreurs, monitoring, récupération)
        monitoring_service = MonitoringService(all_configs.get('main', {}), event_bus)
        if monitoring_service.initialize():
            logger.info("Service de monitoring initialisé")
        else:
            logger.warning("Échec initialisation service de monitoring")
        
        recovery_service = RecoveryService(all_configs.get('main', {}), event_bus)
        if recovery_service.initialize():
            logger.info("Service de récupération initialisé")
        else:
            logger.warning("Échec initialisation service de récupération")
        
        health_check_service = HealthCheckService(all_configs.get('main', {}), event_bus)
        if health_check_service.initialize():
            logger.info("Service de vérification de santé initialisé")
        else:
            logger.warning("Échec initialisation service de vérification de santé")
        
        # Initialiser l'interface utilisateur avec la configuration
        ui_controller = UIController(event_bus, config)
        logger.info("Contrôleur UI initialisé")
        
        # Démarrage de la boucle principale
        main_loop = MainLoop(event_bus, safety_service)
        logger.info("Boucle principale initialisée")
        
        # Connecter le service de persistance au MainController
        persistence_service = ui_controller.get_persistence_service()
        if persistence_service and hasattr(main_loop, 'main_controller') and main_loop.main_controller:
            main_loop.main_controller.persistence_service = persistence_service
            logger.info("Service de persistance connecté au MainController")
        
        # Démarrer les services de caméra et streaming
        if camera_service.start():
            logger.info("Service de caméra démarré")
        else:
            logger.warning("Échec démarrage service de caméra")
        
        if streaming_service.start():
            logger.info("Service de streaming démarré")
        else:
            logger.warning("Échec démarrage service de streaming")
        
        if snapshot_service.start():
            logger.info("Service de snapshots démarré")
        else:
            logger.warning("Échec démarrage service de snapshots")
        
        if alert_service.start():
            logger.info("Service d'alertes démarré")
        else:
            logger.warning("Échec démarrage service d'alertes")
        
        # Démarrer les services de Phase 1
        if monitoring_service.start():
            logger.info("Service de monitoring démarré")
        else:
            logger.warning("Échec démarrage service de monitoring")
        
        if recovery_service.start():
            logger.info("Service de récupération démarré")
        else:
            logger.warning("Échec démarrage service de récupération")
        
        if health_check_service.start():
            logger.info("Service de vérification de santé démarré")
        else:
            logger.warning("Échec démarrage service de vérification de santé")
        
        # Démarrer l'interface utilisateur
        if ui_controller.start():
            logger.info("Interface utilisateur démarrée")
        else:
            logger.warning("Échec démarrage interface utilisateur")
        
        print("✅ Système Alimante démarré avec succès")
        print("📊 Surveillance du ou des terrariums en cours...")
        print("🌐 Interface web disponible sur http://localhost:8080")
        print("📷 Services de caméra et streaming actifs")
        print("🛑 Appuyez sur Ctrl+C pour arrêter")
        
        # Lancement de la boucle principale
        main_loop.run()
        
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
        print("\n🛑 Arrêt du système Alimante")
        
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
        print(f"❌ Erreur critique: {e}")
        sys.exit(1)
        
    finally:
        # Arrêter tous les services
        try:
            if 'ui_controller' in locals():
                ui_controller.stop()
                logger.info("Interface utilisateur arrêtée")
        except Exception as e:
            logger.error(f"Erreur arrêt interface utilisateur: {e}")
        
        try:
            if 'camera_service' in locals():
                camera_service.stop()
                logger.info("Service de caméra arrêté")
        except Exception as e:
            logger.error(f"Erreur arrêt service de caméra: {e}")
        
        try:
            if 'streaming_service' in locals():
                streaming_service.stop()
                logger.info("Service de streaming arrêté")
        except Exception as e:
            logger.error(f"Erreur arrêt service de streaming: {e}")
        
        try:
            if 'snapshot_service' in locals():
                snapshot_service.stop()
                logger.info("Service de snapshots arrêté")
        except Exception as e:
            logger.error(f"Erreur arrêt service de snapshots: {e}")
        
        try:
            if 'alert_service' in locals():
                alert_service.stop()
                logger.info("Service d'alertes arrêté")
        except Exception as e:
            logger.error(f"Erreur arrêt service d'alertes: {e}")
        
        # Arrêter les services de Phase 1
        try:
            if 'monitoring_service' in locals():
                monitoring_service.stop()
                logger.info("Service de monitoring arrêté")
        except Exception as e:
            logger.error(f"Erreur arrêt service de monitoring: {e}")
        
        try:
            if 'recovery_service' in locals():
                recovery_service.stop()
                logger.info("Service de récupération arrêté")
        except Exception as e:
            logger.error(f"Erreur arrêt service de récupération: {e}")
        
        try:
            if 'health_check_service' in locals():
                health_check_service.stop()
                logger.info("Service de vérification de santé arrêté")
        except Exception as e:
            logger.error(f"Erreur arrêt service de vérification de santé: {e}")
        
        logger.info("Arrêt du système Alimante")
        print("👋 Au revoir !")

if __name__ == "__main__":
    main()
