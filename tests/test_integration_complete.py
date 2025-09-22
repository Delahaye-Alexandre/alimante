"""
Tests d'intégration complets pour Alimante
Teste le fonctionnement end-to-end de l'application avec simulation du matériel
"""

import unittest
import time
import threading
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory, retry_on_error
from services.monitoring_service import MonitoringService
from services.config_service import ConfigService
from utils.event_bus import EventBus

class MockHardware:
    """Simulation du matériel pour les tests"""
    
    def __init__(self):
        self.sensors = {
            'temperature': 25.0,
            'humidity': 60.0,
            'air_quality': 80.0,
            'water_level': 75.0
        }
        self.actuators = {
            'heater': False,
            'humidifier': False,
            'fan': False,
            'light': False
        }
        self.camera_available = True
        self.lcd_available = True
    
    def read_sensor(self, sensor_name: str) -> float:
        """Simule la lecture d'un capteur"""
        if sensor_name in self.sensors:
            # Ajouter une petite variation pour simuler la réalité
            import random
            base_value = self.sensors[sensor_name]
            variation = random.uniform(-0.5, 0.5)
            return max(0, min(100, base_value + variation))
        return 0.0
    
    def set_actuator(self, actuator_name: str, state: bool) -> bool:
        """Simule le contrôle d'un actionneur"""
        if actuator_name in self.actuators:
            self.actuators[actuator_name] = state
            return True
        return False
    
    def get_actuator_state(self, actuator_name: str) -> bool:
        """Récupère l'état d'un actionneur"""
        return self.actuators.get(actuator_name, False)

class TestIntegrationComplete(unittest.TestCase):
    """Tests d'intégration complets"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.hardware = MockHardware()
        self.event_bus = EventBus()
        self.error_handler = ErrorHandler()
        
        # Configuration de test
        self.test_config = {
            'update_interval': 1.0,
            'health_check_interval': 2.0,
            'metrics_retention_hours': 1
        }
        
        # Services
        self.monitoring_service = None
        self.config_service = None
        
        # Données de test
        self.test_data = {
            'temperature': 25.0,
            'humidity': 60.0,
            'air_quality': 80.0,
            'water_level': 75.0
        }
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if self.monitoring_service:
            self.monitoring_service.stop()
    
    def test_error_handler_integration(self):
        """Test l'intégration du gestionnaire d'erreurs"""
        print("\n🧪 Test du gestionnaire d'erreurs...")
        
        # Test de logging d'erreur
        test_error = Exception("Test error")
        error_info = self.error_handler.log_error(
            test_error, "TestComponent", "test_function",
            ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
        )
        
        self.assertIsNotNone(error_info)
        self.assertEqual(error_info.component, "TestComponent")
        self.assertEqual(error_info.severity, ErrorSeverity.MEDIUM)
        
        # Test de retry
        call_count = 0
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated failure")
            return "success"
        
        result = self.error_handler.execute_with_retry(
            failing_function, "TestComponent"
        )
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
        
        # Test des statistiques
        stats = self.error_handler.get_error_stats()
        self.assertIn('total_errors', stats)
        self.assertGreater(stats['total_errors'], 0)
        
        print("✅ Gestionnaire d'erreurs fonctionnel")
    
    def test_monitoring_service_integration(self):
        """Test l'intégration du service de monitoring"""
        print("\n🧪 Test du service de monitoring...")
        
        self.monitoring_service = MonitoringService(self.test_config, self.event_bus)
        
        # Test d'initialisation
        self.assertTrue(self.monitoring_service.initialize())
        
        # Test de démarrage
        self.assertTrue(self.monitoring_service.start())
        
        # Attendre quelques cycles de monitoring
        time.sleep(3)
        
        # Test des métriques
        metrics = self.monitoring_service.get_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('cpu_usage', metrics)
        self.assertIn('memory_usage', metrics)
        
        # Test du statut de santé
        health_status = self.monitoring_service.get_health_status()
        self.assertIn('overall_status', health_status)
        self.assertIn('components', health_status)
        
        print("✅ Service de monitoring fonctionnel")
    
    def test_config_service_integration(self):
        """Test l'intégration du service de configuration"""
        print("\n🧪 Test du service de configuration...")
        
        self.config_service = ConfigService()
        
        # Test de chargement des configurations
        configs = self.config_service.load_all_configs()
        self.assertIsInstance(configs, dict)
        
        # Test de récupération de configuration spécifique
        main_config = self.config_service.load_config('main')
        self.assertIsInstance(main_config, dict)
        
        # Test de récupération de valeur hardcodée
        hardcoded_value = self.config_service.get_hardcoded_value('services.monitoring.update_interval')
        self.assertIsNotNone(hardcoded_value)
        
        print("✅ Service de configuration fonctionnel")
    
    def test_hardware_simulation(self):
        """Test la simulation du matériel"""
        print("\n🧪 Test de simulation du matériel...")
        
        # Test de lecture des capteurs
        for sensor_name in self.hardware.sensors:
            value = self.hardware.read_sensor(sensor_name)
            self.assertIsInstance(value, float)
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)
        
        # Test de contrôle des actionneurs
        for actuator_name in self.hardware.actuators:
            # Test d'activation
            result = self.hardware.set_actuator(actuator_name, True)
            self.assertTrue(result)
            self.assertTrue(self.hardware.get_actuator_state(actuator_name))
            
            # Test de désactivation
            result = self.hardware.set_actuator(actuator_name, False)
            self.assertTrue(result)
            self.assertFalse(self.hardware.get_actuator_state(actuator_name))
        
        print("✅ Simulation du matériel fonctionnelle")
    
    def test_error_recovery_simulation(self):
        """Test la simulation de récupération d'erreurs"""
        print("\n🧪 Test de récupération d'erreurs...")
        
        # Simuler une défaillance temporaire
        original_read_sensor = self.hardware.read_sensor
        failure_count = 0
        
        def failing_read_sensor(sensor_name):
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 2:
                raise Exception("Sensor temporarily unavailable")
            return original_read_sensor(sensor_name)
        
        self.hardware.read_sensor = failing_read_sensor
        
        # Test avec retry
        def read_temperature():
            return self.hardware.read_sensor('temperature')
        
        result = self.error_handler.execute_with_retry(
            read_temperature, "SensorController"
        )
        
        self.assertIsInstance(result, float)
        self.assertEqual(failure_count, 3)  # 2 échecs + 1 succès
        
        print("✅ Récupération d'erreurs fonctionnelle")
    
    def test_performance_under_load(self):
        """Test de performance sous charge"""
        print("\n🧪 Test de performance sous charge...")
        
        self.monitoring_service = MonitoringService(self.test_config, self.event_bus)
        self.monitoring_service.initialize()
        self.monitoring_service.start()
        
        # Simuler une charge élevée
        start_time = time.time()
        operations_count = 0
        
        def simulate_operation():
            nonlocal operations_count
            operations_count += 1
            # Simuler une opération
            self.hardware.read_sensor('temperature')
            time.sleep(0.01)  # 10ms d'opération
        
        # Exécuter plusieurs opérations en parallèle
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=simulate_operation)
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Vérifier que les opérations se sont bien exécutées
        self.assertGreater(operations_count, 0)
        self.assertLess(duration, 5.0)  # Doit se terminer en moins de 5 secondes
        
        print(f"✅ Performance sous charge: {operations_count} opérations en {duration:.2f}s")
    
    def test_system_health_monitoring(self):
        """Test du monitoring de santé du système"""
        print("\n🧪 Test du monitoring de santé...")
        
        self.monitoring_service = MonitoringService(self.test_config, self.event_bus)
        self.monitoring_service.initialize()
        self.monitoring_service.start()
        
        # Attendre quelques cycles
        time.sleep(3)
        
        # Vérifier le statut de santé
        health_status = self.monitoring_service.get_health_status()
        
        self.assertIn('overall_status', health_status)
        self.assertIn('components', health_status)
        self.assertIn('metrics', health_status)
        
        # Le statut doit être 'healthy' ou 'warning' (pas 'critical')
        self.assertIn(health_status['overall_status'], ['healthy', 'warning', 'unknown'])
        
        print("✅ Monitoring de santé fonctionnel")
    
    def test_alert_system(self):
        """Test du système d'alertes"""
        print("\n🧪 Test du système d'alertes...")
        
        self.monitoring_service = MonitoringService(self.test_config, self.event_bus)
        self.monitoring_service.initialize()
        self.monitoring_service.start()
        
        # Callback pour capturer les alertes
        alerts_received = []
        
        def alert_callback(alert_data):
            alerts_received.append(alert_data)
        
        self.monitoring_service.add_alert_callback(alert_callback)
        
        # Simuler une condition d'alerte (CPU élevé)
        self.monitoring_service._update_metric('cpu_usage', 95.0)
        
        # Attendre la vérification des seuils
        time.sleep(3)
        
        # Vérifier qu'une alerte a été générée
        self.assertGreater(len(alerts_received), 0)
        
        print("✅ Système d'alertes fonctionnel")
    
    def test_data_persistence(self):
        """Test de la persistance des données"""
        print("\n🧪 Test de persistance des données...")
        
        self.monitoring_service = MonitoringService(self.test_config, self.event_bus)
        self.monitoring_service.initialize()
        self.monitoring_service.start()
        
        # Attendre quelques cycles
        time.sleep(3)
        
        # Exporter les métriques
        export_file = 'test_metrics_export.json'
        self.monitoring_service.export_metrics(export_file)
        
        # Vérifier que le fichier a été créé
        self.assertTrue(os.path.exists(export_file))
        
        # Vérifier le contenu
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('timestamp', data)
        self.assertIn('metrics', data)
        self.assertIn('health_status', data)
        
        # Nettoyer
        os.remove(export_file)
        
        print("✅ Persistance des données fonctionnelle")
    
    def test_full_system_workflow(self):
        """Test du workflow complet du système"""
        print("\n🧪 Test du workflow complet...")
        
        # Initialiser tous les services
        self.monitoring_service = MonitoringService(self.test_config, self.event_bus)
        self.config_service = ConfigService()
        
        # Démarrer les services
        self.assertTrue(self.monitoring_service.initialize())
        self.assertTrue(self.monitoring_service.start())
        
        # Simuler le fonctionnement normal
        for i in range(5):
            # Lire les capteurs
            temperature = self.hardware.read_sensor('temperature')
            humidity = self.hardware.read_sensor('humidity')
            
            # Simuler la logique de contrôle
            if temperature < 20:
                self.hardware.set_actuator('heater', True)
            else:
                self.hardware.set_actuator('heater', False)
            
            if humidity < 50:
                self.hardware.set_actuator('humidifier', True)
            else:
                self.hardware.set_actuator('humidifier', False)
            
            # Attendre un cycle
            time.sleep(1)
        
        # Vérifier que le système fonctionne
        health_status = self.monitoring_service.get_health_status()
        self.assertIn('overall_status', health_status)
        
        print("✅ Workflow complet fonctionnel")
    
    def test_error_handling_robustness(self):
        """Test de la robustesse de la gestion d'erreurs"""
        print("\n🧪 Test de robustesse de la gestion d'erreurs...")
        
        # Test avec des erreurs multiples
        error_count = 0
        
        def error_prone_function():
            nonlocal error_count
            error_count += 1
            if error_count <= 5:
                raise Exception(f"Error {error_count}")
            return "success"
        
        # Exécuter avec retry
        result = self.error_handler.execute_with_retry(
            error_prone_function, "TestComponent",
            retry_config=self.error_handler.retry_configs['service']
        )
        
        self.assertEqual(result, "success")
        self.assertEqual(error_count, 6)  # 5 échecs + 1 succès
        
        # Vérifier que les erreurs ont été enregistrées
        stats = self.error_handler.get_error_stats()
        self.assertGreater(stats['total_errors'], 0)
        
        print("✅ Gestion d'erreurs robuste")
    
    def test_component_health_tracking(self):
        """Test du suivi de santé des composants"""
        print("\n🧪 Test du suivi de santé des composants...")
        
        # Marquer un composant comme défaillant
        self.error_handler.log_error(
            Exception("Component failure"), "TestComponent", "test_function",
            ErrorSeverity.CRITICAL, ErrorCategory.HARDWARE
        )
        
        # Vérifier que le composant est marqué comme défaillant
        self.assertFalse(self.error_handler.get_component_health("TestComponent"))
        
        # Réinitialiser la santé
        self.error_handler.reset_component_health("TestComponent")
        self.assertTrue(self.error_handler.get_component_health("TestComponent"))
        
        print("✅ Suivi de santé des composants fonctionnel")

def run_integration_tests():
    """Lance tous les tests d'intégration"""
    print("🚀 Démarrage des tests d'intégration complets...")
    print("=" * 60)
    
    # Créer la suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegrationComplete)
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Afficher le résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS D'INTÉGRATION")
    print("=" * 60)
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")
    print(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    
    if result.failures:
        print("\n❌ ÉCHECS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 ERREURS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ TOUS LES TESTS D'INTÉGRATION ONT RÉUSSI!")
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
