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
        # Initialisation du bus d'événements
        event_bus = EventBus()
        logger.info("Bus d'événements initialisé")
        
        # Initialisation du service de sécurité
        safety_service = SafetyService(event_bus)
        logger.info("Service de sécurité initialisé")
        
        # Démarrage de la boucle principale
        main_loop = MainLoop(event_bus, safety_service)
        logger.info("Boucle principale initialisée")
        
        print("✅ Système Alimante démarré avec succès")
        print("📊 Surveillance du ou des terrariums en cours...")
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
        logger.info("Arrêt du système Alimante")
        print("👋 Au revoir !")

if __name__ == "__main__":
    main()
