#!/usr/bin/env python3
"""
Tests de performance Alimante
Mesure les performances du système d'événements et des services
"""

import sys
import os
import time
import threading
import psutil
import logging
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.event_bus import EventBus
from services.control_service import ControlService
from services.safety_service import SafetyService
from ui.ui_controller import UIController

class PerformanceTester:
    """Testeur de performance"""
    
    def __init__(self):
        self.event_bus = EventBus()
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
        self.safety_service = SafetyService(self.event_bus)
        self.ui_controller = UIController(self.event_bus)
        
        # Métriques
        self.event_count = 0
        self.start_time = None
        self.end_time = None
    
    def _event_counter(self, data):
        """Compteur d'événements pour les tests"""
        self.event_count += 1
    
    def test_event_bus_performance(self):
        """Test de performance du bus d'événements"""
        print("\n⚡ Test de performance du bus d'événements...")
        
        # S'abonner à un événement
        self.event_bus.on('test_event', self._event_counter)
        
        # Test avec différents volumes d'événements
        test_cases = [100, 500, 1000, 2000]
        
        for count in test_cases:
            self.event_count = 0
            start_time = time.time()
            
            # Émettre les événements
            for i in range(count):
                self.event_bus.emit('test_event', {'id': i, 'data': f'test_{i}'})
            
            end_time = time.time()
            duration = end_time - start_time
            
            events_per_second = count / duration if duration > 0 else 0
            
            print(f"   {count:4d} événements: {duration:.3f}s ({events_per_second:.0f} evt/s)")
            
            # Vérifier que tous les événements ont été traités
            assert self.event_count == count, f"Seulement {self.event_count}/{count} événements traités"
        
        print("✅ Test de performance du bus d'événements réussi")
        return True
    
    def test_memory_usage(self):
        """Test d'utilisation mémoire"""
        print("\n💾 Test d'utilisation mémoire...")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"   Mémoire initiale: {initial_memory:.1f} MB")
        
        # Créer beaucoup d'événements et de données
        events_data = []
        for i in range(1000):
            events_data.append({
                'id': i,
                'sensor_data': {
                    'temperature': 25.0 + i * 0.01,
                    'humidity': 60.0 + i * 0.02,
                    'air_quality': 50 + i,
                    'timestamp': time.time()
                }
            })
        
        # Émettre tous les événements
        for data in events_data:
            self.event_bus.emit('sensor_data_updated', data)
        
        time.sleep(1)  # Laisser le temps au traitement
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"   Mémoire finale: {final_memory:.1f} MB")
        print(f"   Augmentation: {memory_increase:.1f} MB")
        
        # Vérifier que l'augmentation mémoire est raisonnable (< 50 MB)
        if memory_increase < 50:
            print("✅ Utilisation mémoire acceptable")
            return True
        else:
            print(f"⚠️ Utilisation mémoire élevée: {memory_increase:.1f} MB")
            return False
    
    def test_concurrent_events(self):
        """Test d'événements concurrents"""
        print("\n🔄 Test d'événements concurrents...")
        
        self.event_count = 0
        self.start_time = time.time()
        
        def emit_events(thread_id, count):
            """Fonction pour émettre des événements dans un thread"""
            for i in range(count):
                self.event_bus.emit('test_event', {
                    'thread_id': thread_id,
                    'event_id': i,
                    'timestamp': time.time()
                })
        
        # Créer plusieurs threads qui émettent des événements
        threads = []
        events_per_thread = 200
        num_threads = 5
        
        for i in range(num_threads):
            thread = threading.Thread(target=emit_events, args=(i, events_per_thread))
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        total_events = num_threads * events_per_thread
        events_per_second = total_events / duration if duration > 0 else 0
        
        print(f"   {num_threads} threads, {events_per_thread} événements/thread")
        print(f"   Total: {total_events} événements en {duration:.3f}s")
        print(f"   Performance: {events_per_second:.0f} événements/seconde")
        
        # Vérifier que tous les événements ont été traités
        assert self.event_count == total_events, f"Seulement {self.event_count}/{total_events} événements traités"
        
        print("✅ Test d'événements concurrents réussi")
        return True
    
    def test_service_performance(self):
        """Test de performance des services"""
        print("\n⚙️ Test de performance des services...")
        
        # Test du service de sécurité
        start_time = time.time()
        
        for i in range(100):
            sensor_data = {
                'temperature': 25.0 + (i % 20) * 0.5,
                'humidity': 60.0 + (i % 10) * 2.0,
                'air_quality': 50 + (i % 50),
                'water_level': 80.0 - (i % 20) * 2.0,
                'timestamp': time.time()
            }
            
            self.safety_service.check_safety_limits(sensor_data)
        
        end_time = time.time()
        duration = end_time - start_time
        checks_per_second = 100 / duration if duration > 0 else 0
        
        print(f"   Service de sécurité: 100 vérifications en {duration:.3f}s ({checks_per_second:.0f} vérif/s)")
        
        # Test du service de contrôle
        start_time = time.time()
        
        for i in range(50):
            sensor_data = {
                'temperature': 25.0,
                'humidity': 60.0,
                'air_quality': 50,
                'timestamp': time.time()
            }
            
            self.event_bus.emit('sensor_data_updated', {'data': sensor_data})
        
        time.sleep(1)  # Laisser le temps au traitement
        end_time = time.time()
        
        print(f"   Service de contrôle: 50 cycles en {end_time - start_time:.3f}s")
        
        print("✅ Test de performance des services réussi")
        return True
    
    def test_ui_responsiveness(self):
        """Test de réactivité de l'interface"""
        print("\n🖥️ Test de réactivité de l'interface...")
        
        # Démarrer l'UI
        ui_started = self.ui_controller.start()
        if not ui_started:
            print("❌ Impossible de démarrer l'UI")
            return False
        
        # Test de réactivité avec des événements rapides
        start_time = time.time()
        
        for i in range(50):
            self.event_bus.emit('sensor_data_updated', {
                'data': {
                    'temperature': 25.0 + i * 0.1,
                    'humidity': 60.0 + i * 0.2,
                    'timestamp': time.time()
                }
            })
            time.sleep(0.01)  # 10ms entre les événements
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   50 mises à jour UI en {duration:.3f}s")
        
        # Arrêter l'UI
        self.ui_controller.stop()
        
        print("✅ Test de réactivité UI réussi")
        return True
    
    def run_all_tests(self):
        """Exécute tous les tests de performance"""
        print("⚡ Démarrage des tests de performance Alimante")
        print("=" * 60)
        
        tests = [
            self.test_event_bus_performance,
            self.test_memory_usage,
            self.test_concurrent_events,
            self.test_service_performance,
            self.test_ui_responsiveness
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
        
        return failed == 0

def main():
    """Fonction principale de test"""
    # Configuration du logging
    logging.basicConfig(
        level=logging.WARNING,  # Réduire les logs pour les tests de performance
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer et exécuter les tests
    tester = PerformanceTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Tous les tests de performance sont passés !")
        return 0
    else:
        print("\n💥 Certains tests de performance ont échoué !")
        return 1

if __name__ == "__main__":
    sys.exit(main())
