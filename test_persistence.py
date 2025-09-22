#!/usr/bin/env python3
"""
Test du service de persistance Alimante
Vérifie que la base de données SQLite fonctionne correctement
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.persistence_service import PersistenceService

def test_persistence_service():
    """Test du service de persistance"""
    print("🧪 TEST DU SERVICE DE PERSISTANCE")
    print("=" * 50)
    
    # Configuration de test
    config = {
        'terrariums': {
            'data_retention_days': 7
        }
    }
    
    try:
        # Initialiser le service
        print("1. Initialisation du service...")
        persistence = PersistenceService(config)
        
        if not persistence.initialize():
            print("❌ Échec initialisation du service")
            return False
        
        print("✅ Service initialisé")
        
        # Test de stockage de données de capteurs
        print("\n2. Test stockage données capteurs...")
        sensor_data = {
            'timestamp': time.time(),
            'temperature': 25.5,
            'humidity': 60.0,
            'air_quality': 45.0,
            'air_quality_level': 'good',
            'water_level': 80.0,
            'water_percentage': 80.0
        }
        
        success = persistence.store_sensor_data('terrarium_test', sensor_data)
        if success:
            print("✅ Données capteurs stockées")
        else:
            print("❌ Échec stockage données capteurs")
            return False
        
        # Test de stockage d'alimentation
        print("\n3. Test stockage alimentation...")
        success = persistence.set_last_feeding_date(
            'terrarium_test', 
            'mantis_religiosa',
            'cricket',
            2.0,
            'Test alimentation automatique'
        )
        if success:
            print("✅ Alimentation stockée")
        else:
            print("❌ Échec stockage alimentation")
            return False
        
        # Test de récupération de la dernière alimentation
        print("\n4. Test récupération dernière alimentation...")
        last_feeding = persistence.get_last_feeding_date('terrarium_test')
        if last_feeding:
            print(f"✅ Dernière alimentation: {last_feeding}")
        else:
            print("❌ Aucune alimentation trouvée")
            return False
        
        # Test de stockage d'alerte
        print("\n5. Test stockage alerte...")
        success = persistence.store_alert(
            'terrarium_test',
            'temperature',
            'warning',
            'Température élevée détectée',
            30.5,
            30.0
        )
        if success:
            print("✅ Alerte stockée")
        else:
            print("❌ Échec stockage alerte")
            return False
        
        # Test de stockage de décision de contrôle
        print("\n6. Test stockage décision contrôle...")
        success = persistence.store_control_decision(
            'terrarium_test',
            'heating',
            'heater',
            'turn_on',
            75.0,
            'Température trop basse'
        )
        if success:
            print("✅ Décision contrôle stockée")
        else:
            print("❌ Échec stockage décision contrôle")
            return False
        
        # Test de récupération de l'historique
        print("\n7. Test récupération historique...")
        history = persistence.get_sensor_history('terrarium_test', 1)
        if history:
            print(f"✅ Historique récupéré: {len(history)} points")
        else:
            print("❌ Aucun historique trouvé")
            return False
        
        # Test de récupération des alertes
        print("\n8. Test récupération alertes...")
        alerts = persistence.get_alerts('terrarium_test')
        if alerts:
            print(f"✅ Alertes récupérées: {len(alerts)} alertes")
        else:
            print("❌ Aucune alerte trouvée")
            return False
        
        # Test des statistiques
        print("\n9. Test statistiques...")
        stats = persistence.get_stats()
        print(f"✅ Statistiques: {stats['stats']}")
        
        # Nettoyage
        print("\n10. Nettoyage...")
        persistence.cleanup()
        print("✅ Service nettoyé")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("Le service de persistance fonctionne correctement.")
        return True
        
    except Exception as e:
        print(f"❌ Erreur durant les tests: {e}")
        return False

if __name__ == "__main__":
    success = test_persistence_service()
    sys.exit(0 if success else 1)
