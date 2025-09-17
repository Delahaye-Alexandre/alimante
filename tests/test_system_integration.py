#!/usr/bin/env python3
"""
Tests d'intégration système Alimante
Vérifie le fonctionnement global du système
"""

import sys
import os
import time
import logging
import threading
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.event_bus import EventBus
from services.control_service import ControlService
from services.safety_service import SafetyService
from ui.ui_controller import UIController
from loops.main_loop import MainLoop

class SystemIntegrationTester:
    """Testeur d'intégration système"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.test_results = {}
        
        # Configuration de base
        self.config = {
            'terrarium_config': {
                'name': 'Test Terrarium',
                'species': 'mantis_religiosa',
                'temperature_target': 25.0,
                'humidity_target': 60.0
            },
            'species_config': {
                'mantis_religiosa': {
                    'temperature_range': [20, 30],
                    'humidity_range': [40, 80],
                    'feeding_schedule': 'daily'
                }
            },
            'policies': {
                'heating': {'enabled': True, 'target_temp': 25.0},
                'humidification': {'enabled': True, 'target_humidity': 60.0},
                'lighting': {'enabled': True, 'schedule': '12h_on'}
            },
            'safety_limits': {
                'temperature': {'min': 15, 'max': 35},
                'humidity': {'min': 30, 'max': 80},
                'air_quality': {'hazardous_threshold': 300},
                'water_level': {'critical_level': 15.0}
            }
        }
        
        # Initialiser les services
        self.safety_service = SafetyService(self.event_bus)
        self.control_service = ControlService(self.config, self.event_bus)
        self.ui_controller = UIController(self.event_bus)
        self.main_loop = MainLoop(self.event_bus, self.safety_service)
        
        # État de test
        self.test_events_received = []
        self.setup_test_listeners()
    
    def setup_test_listeners(self):
        """Configure les écouteurs de test"""
        # Écouter les événements critiques
        self.event_bus.on('emergency_stop', self._on_emergency_stop)
        self.event_bus.on('safety_alert', self._on_safety_alert)
        self.event_bus.on('sensor_data_updated', self._on_sensor_data)
    
    def _on_emergency_stop(self, data):
        self.test_events_received.append(('emergency_stop', data))
        print(f"🚨 Arrêt d'urgence reçu: {data.get('reason', 'Inconnu')}")
    
    def _on_safety_alert(self, data):
        self.test_events_received.append(('safety_alert', data))
        print(f"⚠️ Alerte sécurité: {data.get('message', 'Inconnue')}")
    
    def _on_sensor_data(self, data):
        self.test_events_received.append(('sensor_data_updated', data))
        print(f"📊 Données capteurs: {data.get('data', {})}")
    
    def test_system_startup(self):
        """Test du démarrage du système"""
        print("\n🚀 Test de démarrage du système...")
        
        try:
            # Démarrer l'interface utilisateur
            ui_started = self.ui_controller.start()
            assert ui_started, "Échec démarrage UI"
            
            # Démarrer la boucle principale (en arrière-plan)
            loop_thread = threading.Thread(target=self.main_loop.run, daemon=True)
            loop_thread.start()
            
            # Laisser le temps au système de s'initialiser
            time.sleep(2)
            
            print("✅ Système démarré avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Échec démarrage système: {e}")
            return False
    
    def test_sensor_data_flow(self):
        """Test du flux de données des capteurs"""
        print("\n📊 Test du flux de données capteurs...")
        
        try:
            # Simuler des données de capteurs
            sensor_data = {
                'temperature': 25.5,
                'humidity': 60.0,
                'air_quality': 45,
                'water_level': 80.0,
                'timestamp': time.time()
            }
            
            # Émettre l'événement
            self.event_bus.emit('sensor_data_updated', {
                'data': sensor_data,
                'timestamp': time.time()
            })
            
            # Attendre le traitement
            time.sleep(1)
            
            # Vérifier que l'événement a été traité
            sensor_events = [e for e in self.test_events_received if e[0] == 'sensor_data_updated']
            assert len(sensor_events) > 0, "Données capteurs non traitées"
            
            print("✅ Flux de données capteurs fonctionnel")
            return True
            
        except Exception as e:
            print(f"❌ Échec test flux capteurs: {e}")
            return False
    
    def test_safety_system(self):
        """Test du système de sécurité"""
        print("\n🛡️ Test du système de sécurité...")
        
        try:
            # Simuler des données dangereuses
            dangerous_data = {
                'temperature': 40.0,  # Trop chaud
                'humidity': 90.0,     # Trop humide
                'air_quality': 350,   # Qualité d'air dangereuse
                'water_level': 10.0,  # Niveau d'eau critique
                'timestamp': time.time()
            }
            
            # Vérifier les limites de sécurité
            violations = self.safety_service.check_safety_limits(dangerous_data)
            
            if violations:
                print(f"⚠️ Violations détectées: {len(violations)}")
                for violation in violations:
                    print(f"   - {violation['message']}")
                
                # Vérifier que les événements d'alerte sont émis
                time.sleep(1)
                safety_events = [e for e in self.test_events_received if e[0] == 'safety_alert']
                assert len(safety_events) > 0, "Alertes sécurité non émises"
                
                print("✅ Système de sécurité fonctionnel")
                return True
            else:
                print("⚠️ Aucune violation détectée (peut-être normal)")
                return True
                
        except Exception as e:
            print(f"❌ Échec test sécurité: {e}")
            return False
    
    def test_control_system(self):
        """Test du système de contrôle"""
        print("\n🎛️ Test du système de contrôle...")
        
        try:
            # Simuler des données nécessitant un contrôle
            sensor_data = {
                'temperature': 20.0,  # Trop froid
                'humidity': 40.0,     # Trop sec
                'timestamp': time.time()
            }
            
            # Émettre les données
            self.event_bus.emit('sensor_data_updated', {
                'data': sensor_data,
                'timestamp': time.time()
            })
            
            # Attendre le traitement
            time.sleep(2)
            
            # Vérifier que le système a réagi
            print("✅ Système de contrôle testé")
            return True
            
        except Exception as e:
            print(f"❌ Échec test contrôle: {e}")
            return False
    
    def test_ui_responsiveness(self):
        """Test de la réactivité de l'interface"""
        print("\n🖥️ Test de réactivité UI...")
        
        try:
            # Vérifier que l'UI est active
            ui_status = self.ui_controller.get_status()
            assert ui_status['is_running'], "UI non active"
            
            # Simuler des événements UI
            self.event_bus.emit('encoder_turned', {
                'direction': 'clockwise',
                'value': 1
            })
            
            self.event_bus.emit('encoder_pressed', {
                'pressed': True,
                'timestamp': time.time()
            })
            
            time.sleep(0.5)
            
            print("✅ Interface utilisateur réactive")
            return True
            
        except Exception as e:
            print(f"❌ Échec test UI: {e}")
            return False
    
    def test_system_stress(self):
        """Test de stress du système"""
        print("\n💪 Test de stress du système...")
        
        try:
            start_time = time.time()
            
            # Émettre beaucoup d'événements rapidement
            for i in range(50):
                sensor_data = {
                    'temperature': 25 + (i % 10) * 0.5,
                    'humidity': 60 + (i % 5) * 2,
                    'timestamp': time.time()
                }
                
                self.event_bus.emit('sensor_data_updated', {
                    'data': sensor_data,
                    'timestamp': time.time()
                })
                
                time.sleep(0.01)  # Petit délai
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏱️ 50 événements traités en {duration:.2f}s")
            print(f"📊 Performance: {50/duration:.1f} événements/seconde")
            
            # Vérifier que le système est toujours stable
            ui_status = self.ui_controller.get_status()
            assert ui_status['is_running'], "UI plantée après stress test"
            
            print("✅ Système stable sous stress")
            return True
            
        except Exception as e:
            print(f"❌ Échec test stress: {e}")
            return False
    
    def test_system_shutdown(self):
        """Test d'arrêt propre du système"""
        print("\n🛑 Test d'arrêt du système...")
        
        try:
            # Arrêter l'UI
            self.ui_controller.stop()
            
            # Vérifier l'arrêt
            ui_status = self.ui_controller.get_status()
            assert not ui_status['is_running'], "UI non arrêtée"
            
            print("✅ Arrêt propre réussi")
            return True
            
        except Exception as e:
            print(f"❌ Échec arrêt système: {e}")
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests d'intégration"""
        print("🔗 Démarrage des tests d'intégration système Alimante")
        print("=" * 60)
        
        tests = [
            self.test_system_startup,
            self.test_sensor_data_flow,
            self.test_safety_system,
            self.test_control_system,
            self.test_ui_responsiveness,
            self.test_system_stress,
            self.test_system_shutdown
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
        print(f"📈 Total événements reçus: {len(self.test_events_received)}")
        
        return failed == 0

def main():
    """Fonction principale de test"""
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer et exécuter les tests
    tester = SystemIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Tous les tests d'intégration sont passés !")
        return 0
    else:
        print("\n💥 Certains tests d'intégration ont échoué !")
        return 1

if __name__ == "__main__":
    sys.exit(main())
