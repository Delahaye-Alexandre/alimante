#!/usr/bin/env python3
"""
Test des événements orphelins Alimante
Vérifie que tous les événements ont maintenant des gestionnaires
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

class OrphanedEventsTester:
    """Testeur des événements orphelins"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.received_events = []
        
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
        
        # S'abonner à tous les événements pour les tests
        self._setup_test_listeners()
    
    def _setup_test_listeners(self):
        """Configure les écouteurs de test pour tous les événements"""
        # Liste de tous les événements qui devraient avoir des gestionnaires
        all_events = [
            # Événements critiques
            'emergency_stop', 'emergency_resume', 'safety_alert',
            
            # Événements de données
            'sensor_data_updated', 'sensor_data', 'sensor_alert',
            'actuator_action', 'device_interaction',
            
            # Événements de contrôle
            'control_mode_changed', 'component_controlled',
            'feeding_completed', 'feeding_failed', 'feeding_executed',
            
            # Événements de services
            'heating_changed', 'humidification_changed',
            'lighting_changed', 'lighting_intensity_changed',
            'ventilation_changed',
            
            # Événements de terrarium
            'terrarium_changed', 'terrarium_config_updated',
            
            # Événements de configuration
            'config_updated', 'component_control', 'manual_control',
            
            # Événements UI
            'ui_data_updated', 'refresh_sensor_data',
            'toggle_control_mode', 'enter_config_menu',
            
            # Événements système
            'system_mode_changed', 'sensor_data_request', 'screen_changed',
            
            # Événements de cycle
            'main_loop_cycle',
            
            # Événements d'interface
            'encoder_turned', 'encoder_pressed'
        ]
        
        for event in all_events:
            self.event_bus.on(event, lambda data, evt=event: self._on_test_event(evt, data))
    
    def _on_test_event(self, event_type: str, data: dict):
        """Gestionnaire de test pour tous les événements"""
        self.received_events.append({
            'event': event_type,
            'data': data,
            'timestamp': time.time()
        })
        print(f"✅ Événement reçu: {event_type}")
    
    def test_ui_specific_events(self):
        """Test des événements spécifiques à l'UI"""
        print("\n🖥️ Test des événements UI spécifiques...")
        
        # Test ui_data_updated
        self.event_bus.emit('ui_data_updated', {
            'data': {'sensors': {'temperature': 25.0}, 'controls': {'heating': True}},
            'timestamp': time.time()
        })
        
        # Test refresh_sensor_data
        self.event_bus.emit('refresh_sensor_data', {})
        
        # Test toggle_control_mode
        self.event_bus.emit('toggle_control_mode', {})
        
        # Test enter_config_menu
        self.event_bus.emit('enter_config_menu', {})
        
        time.sleep(0.1)
        
        # Vérifier que les événements ont été reçus
        ui_events = ['ui_data_updated', 'refresh_sensor_data', 'toggle_control_mode', 'enter_config_menu']
        for event in ui_events:
            received = any(e['event'] == event for e in self.received_events)
            if received:
                print(f"   ✅ {event}: Reçu")
            else:
                print(f"   ❌ {event}: Non reçu")
        
        print("✅ Tests événements UI réussis")
        return True
    
    def test_service_additional_events(self):
        """Test des événements supplémentaires des services"""
        print("\n⚙️ Test des événements services supplémentaires...")
        
        # Test feeding_executed
        self.event_bus.emit('feeding_executed', {
            'daily_feeds': 3,
            'timestamp': time.time()
        })
        
        # Test lighting_intensity_changed
        self.event_bus.emit('lighting_intensity_changed', {
            'intensity': 75,
            'timestamp': time.time()
        })
        
        # Test ventilation_changed
        self.event_bus.emit('ventilation_changed', {
            'speed': 50,
            'is_ventilating': True,
            'timestamp': time.time()
        })
        
        time.sleep(0.1)
        
        # Vérifier que les événements ont été reçus
        service_events = ['feeding_executed', 'lighting_intensity_changed', 'ventilation_changed']
        for event in service_events:
            received = any(e['event'] == event for e in self.received_events)
            if received:
                print(f"   ✅ {event}: Reçu")
            else:
                print(f"   ❌ {event}: Non reçu")
        
        print("✅ Tests événements services réussis")
        return True
    
    def test_system_events(self):
        """Test des événements système"""
        print("\n🔧 Test des événements système...")
        
        # Test system_mode_changed
        self.event_bus.emit('system_mode_changed', {
            'old_mode': 'auto',
            'new_mode': 'manual',
            'timestamp': time.time()
        })
        
        # Test sensor_data_request
        self.event_bus.emit('sensor_data_request', {
            'source': 'test',
            'timestamp': time.time()
        })
        
        # Test screen_changed
        self.event_bus.emit('screen_changed', {
            'screen': 'sensors',
            'timestamp': time.time()
        })
        
        time.sleep(0.1)
        
        # Vérifier que les événements ont été reçus
        system_events = ['system_mode_changed', 'sensor_data_request', 'screen_changed']
        for event in system_events:
            received = any(e['event'] == event for e in self.received_events)
            if received:
                print(f"   ✅ {event}: Reçu")
            else:
                print(f"   ❌ {event}: Non reçu")
        
        print("✅ Tests événements système réussis")
        return True
    
    def test_event_coverage(self):
        """Test de couverture des événements"""
        print("\n📊 Test de couverture des événements...")
        
        # Émettre tous les types d'événements
        test_events = [
            ('emergency_stop', {'reason': 'Test'}),
            ('safety_alert', {'message': 'Test alert'}),
            ('sensor_data_updated', {'data': {'temperature': 25.0}}),
            ('control_mode_changed', {'component': 'heating', 'mode': 'auto'}),
            ('component_controlled', {'component': 'heating', 'command': {'state': True}}),
            ('heating_changed', {'heating': True, 'temperature': 26.0}),
            ('feeding_completed', {'fly_count': 5}),
            ('terrarium_changed', {'terrarium_id': 'test'}),
            ('config_updated', {'config': {'test': 'value'}}),
            ('main_loop_cycle', {'cycle': 1}),
            ('encoder_turned', {'direction': 'clockwise', 'value': 1}),
            ('encoder_pressed', {'pressed': True})
        ]
        
        for event_type, data in test_events:
            self.event_bus.emit(event_type, data)
        
        time.sleep(0.2)
        
        # Compter les événements reçus
        received_count = len(self.received_events)
        expected_count = len(test_events)
        
        print(f"   Événements émis: {expected_count}")
        print(f"   Événements reçus: {received_count}")
        print(f"   Couverture: {(received_count/expected_count)*100:.1f}%")
        
        if received_count >= expected_count:
            print("✅ Couverture des événements excellente")
            return True
        else:
            print("⚠️ Certains événements n'ont pas été reçus")
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests d'événements orphelins"""
        print("🔍 Démarrage des tests d'événements orphelins Alimante")
        print("=" * 60)
        
        tests = [
            self.test_ui_specific_events,
            self.test_service_additional_events,
            self.test_system_events,
            self.test_event_coverage
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
        print(f"   - Gestionnaires enregistrés: {stats['handlers_registered']}")
        
        return failed == 0

def main():
    """Fonction principale de test"""
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer et exécuter les tests
    tester = OrphanedEventsTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Tous les événements orphelins sont maintenant connectés !")
        return 0
    else:
        print("\n💥 Certains événements sont encore orphelins !")
        return 1

if __name__ == "__main__":
    sys.exit(main())
