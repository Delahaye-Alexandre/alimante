#!/usr/bin/env python3
"""
Tests du système d'événements Alimante
Vérifie que tous les événements sont correctement émis et traités
"""

import sys
import os
import time
import logging
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.event_bus import EventBus
from services.control_service import ControlService
from ui.ui_controller import UIController

class EventSystemTester:
    """Testeur du système d'événements"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.received_events = []
        self.test_results = {}
        
        # Configuration de base
        self.config = {
            'terrarium_config': {},
            'species_config': {},
            'policies': {},
            'safety_limits': {
                'temperature': {'min': 15, 'max': 35},
                'humidity': {'min': 30, 'max': 80},
                'air_quality': {'hazardous_threshold': 300}
            }
        }
        
        # Initialiser les services
        self.control_service = ControlService(self.config, self.event_bus)
        self.ui_controller = UIController(self.event_bus)
        
        # S'abonner aux événements de test
        self._setup_test_listeners()
        
    def _setup_test_listeners(self):
        """Configure les écouteurs de test"""
        # Écouter tous les événements pour les tests
        test_events = [
            'emergency_stop', 'emergency_resume', 'safety_alert',
            'sensor_data_updated', 'control_mode_changed', 'component_controlled',
            'heating_changed', 'humidification_changed', 'lighting_changed',
            'ventilation_changed', 'feeding_completed', 'feeding_failed',
            'terrarium_changed', 'config_updated', 'main_loop_cycle'
        ]
        
        for event in test_events:
            self.event_bus.on(event, lambda data, evt=event: self._on_test_event(evt, data))
    
    def _on_test_event(self, event_type: str, data: dict):
        """Gestionnaire de test pour tous les événements"""
        self.received_events.append({
            'event': event_type,
            'data': data,
            'timestamp': time.time()
        })
        print(f"✅ Événement reçu: {event_type}")
    
    def test_emergency_events(self):
        """Test des événements d'urgence"""
        print("\n🚨 Test des événements d'urgence...")
        
        # Simuler un arrêt d'urgence
        self.event_bus.emit('emergency_stop', {
            'reason': 'Test d\'arrêt d\'urgence',
            'timestamp': time.time(),
            'violation': {'message': 'Test violation'}
        })
        
        time.sleep(0.1)  # Laisser le temps de traitement
        
        # Vérifier que l'événement a été reçu
        emergency_events = [e for e in self.received_events if e['event'] == 'emergency_stop']
        assert len(emergency_events) > 0, "Événement emergency_stop non reçu"
        
        # Simuler une reprise
        self.event_bus.emit('emergency_resume', {
            'timestamp': time.time()
        })
        
        time.sleep(0.1)
        
        resume_events = [e for e in self.received_events if e['event'] == 'emergency_resume']
        assert len(resume_events) > 0, "Événement emergency_resume non reçu"
        
        print("✅ Tests d'urgence réussis")
        return True
    
    def test_sensor_events(self):
        """Test des événements de capteurs"""
        print("\n📊 Test des événements de capteurs...")
        
        # Simuler des données de capteurs
        sensor_data = {
            'temperature': 25.5,
            'humidity': 60.0,
            'air_quality': 45,
            'water_level': 80.0,
            'timestamp': time.time()
        }
        
        self.event_bus.emit('sensor_data_updated', {
            'data': sensor_data,
            'timestamp': time.time()
        })
        
        time.sleep(0.1)
        
        # Vérifier que l'événement a été reçu
        sensor_events = [e for e in self.received_events if e['event'] == 'sensor_data_updated']
        assert len(sensor_events) > 0, "Événement sensor_data_updated non reçu"
        
        print("✅ Tests de capteurs réussis")
        return True
    
    def test_control_events(self):
        """Test des événements de contrôle"""
        print("\n🎛️ Test des événements de contrôle...")
        
        # Test changement de mode
        self.event_bus.emit('control_mode_changed', {
            'component': 'heating',
            'mode': 'automatic',
            'timestamp': time.time()
        })
        
        # Test contrôle de composant
        self.event_bus.emit('component_controlled', {
            'component': 'heating',
            'command': {'state': True, 'temperature': 25},
            'timestamp': time.time()
        })
        
        time.sleep(0.1)
        
        # Vérifier les événements
        mode_events = [e for e in self.received_events if e['event'] == 'control_mode_changed']
        control_events = [e for e in self.received_events if e['event'] == 'component_controlled']
        
        assert len(mode_events) > 0, "Événement control_mode_changed non reçu"
        assert len(control_events) > 0, "Événement component_controlled non reçu"
        
        print("✅ Tests de contrôle réussis")
        return True
    
    def test_service_events(self):
        """Test des événements de services"""
        print("\n⚙️ Test des événements de services...")
        
        # Test chauffage
        self.event_bus.emit('heating_changed', {
            'heating': True,
            'temperature': 26.0,
            'timestamp': time.time()
        })
        
        # Test humidification
        self.event_bus.emit('humidification_changed', {
            'humidifying': True,
            'humidity': 65.0,
            'timestamp': time.time()
        })
        
        # Test éclairage
        self.event_bus.emit('lighting_changed', {
            'lighting': True,
            'intensity': 80,
            'timestamp': time.time()
        })
        
        time.sleep(0.1)
        
        # Vérifier les événements
        heating_events = [e for e in self.received_events if e['event'] == 'heating_changed']
        humid_events = [e for e in self.received_events if e['event'] == 'humidification_changed']
        lighting_events = [e for e in self.received_events if e['event'] == 'lighting_changed']
        
        assert len(heating_events) > 0, "Événement heating_changed non reçu"
        assert len(humid_events) > 0, "Événement humidification_changed non reçu"
        assert len(lighting_events) > 0, "Événement lighting_changed non reçu"
        
        print("✅ Tests de services réussis")
        return True
    
    def test_feeding_events(self):
        """Test des événements d'alimentation"""
        print("\n🍽️ Test des événements d'alimentation...")
        
        # Test alimentation réussie
        self.event_bus.emit('feeding_completed', {
            'fly_count': 5,
            'timestamp': time.time()
        })
        
        # Test échec alimentation
        self.event_bus.emit('feeding_failed', {
            'fly_count': 0,
            'error': 'Test d\'erreur',
            'timestamp': time.time()
        })
        
        time.sleep(0.1)
        
        # Vérifier les événements
        completed_events = [e for e in self.received_events if e['event'] == 'feeding_completed']
        failed_events = [e for e in self.received_events if e['event'] == 'feeding_failed']
        
        assert len(completed_events) > 0, "Événement feeding_completed non reçu"
        assert len(failed_events) > 0, "Événement feeding_failed non reçu"
        
        print("✅ Tests d'alimentation réussis")
        return True
    
    def test_event_performance(self):
        """Test de performance du système d'événements"""
        print("\n⚡ Test de performance des événements...")
        
        start_time = time.time()
        
        # Émettre 100 événements rapidement
        for i in range(100):
            self.event_bus.emit('sensor_data_updated', {
                'data': {'temperature': 25 + i * 0.1},
                'timestamp': time.time()
            })
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ 100 événements émis en {duration:.3f}s")
        print(f"📊 Performance: {100/duration:.1f} événements/seconde")
        
        # Vérifier que tous les événements ont été reçus
        sensor_events = [e for e in self.received_events if e['event'] == 'sensor_data_updated']
        assert len(sensor_events) >= 100, f"Seulement {len(sensor_events)}/100 événements reçus"
        
        print("✅ Test de performance réussi")
        return True
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🧪 Démarrage des tests du système d'événements Alimante")
        print("=" * 60)
        
        tests = [
            self.test_emergency_events,
            self.test_sensor_events,
            self.test_control_events,
            self.test_service_events,
            self.test_feeding_events,
            self.test_event_performance
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test échoué: {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Résultats: {passed} réussis, {failed} échoués")
        print(f"📈 Total événements reçus: {len(self.received_events)}")
        
        # Afficher les statistiques du bus d'événements
        stats = self.event_bus.get_stats()
        print(f"📊 Statistiques du bus d'événements:")
        print(f"   - Événements émis: {stats['events_emitted']}")
        print(f"   - Gestionnaires appelés: {stats['handlers_called']}")
        print(f"   - Erreurs: {stats['errors_count']}")
        
        return failed == 0

def main():
    """Fonction principale de test"""
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer et exécuter les tests
    tester = EventSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Tous les tests sont passés avec succès !")
        return 0
    else:
        print("\n💥 Certains tests ont échoué !")
        return 1

if __name__ == "__main__":
    sys.exit(main())
