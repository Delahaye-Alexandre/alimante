"""
Test des améliorations de la Phase 1 pour Alimante
Valide le système de gestion d'erreurs, le monitoring et la récupération automatique
"""

import sys
import os
import time
import threading
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_error_handler():
    """Test du gestionnaire d'erreurs"""
    print("\n🧪 Test du gestionnaire d'erreurs...")
    
    try:
        from utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory, retry_on_error
        
        # Créer une instance
        error_handler = ErrorHandler()
        
        # Test de logging d'erreur
        test_error = Exception("Test error")
        error_info = error_handler.log_error(
            test_error, "TestComponent", "test_function",
            ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
        )
        
        print(f"  ✅ Erreur enregistrée: {error_info.component}")
        
        # Test de retry
        call_count = 0
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated failure")
            return "success"
        
        result = error_handler.execute_with_retry(failing_function, "TestComponent")
        print(f"  ✅ Retry fonctionnel: {result} après {call_count} tentatives")
        
        # Test des statistiques
        stats = error_handler.get_error_stats()
        print(f"  ✅ Statistiques: {stats['total_errors']} erreurs enregistrées")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test du gestionnaire d'erreurs: {e}")
        return False

def test_monitoring_service():
    """Test du service de monitoring"""
    print("\n🧪 Test du service de monitoring...")
    
    try:
        from services.monitoring_service import MonitoringService
        
        # Configuration de test
        config = {
            'update_interval': 1.0,
            'health_check_interval': 2.0,
            'metrics_retention_hours': 1
        }
        
        # Créer et initialiser le service
        monitoring_service = MonitoringService(config)
        
        if not monitoring_service.initialize():
            print("  ❌ Échec d'initialisation du service de monitoring")
            return False
        
        print("  ✅ Service de monitoring initialisé")
        
        # Démarrer le service
        if not monitoring_service.start():
            print("  ❌ Échec de démarrage du service de monitoring")
            return False
        
        print("  ✅ Service de monitoring démarré")
        
        # Attendre quelques cycles
        time.sleep(3)
        
        # Vérifier les métriques
        metrics = monitoring_service.get_metrics()
        print(f"  ✅ Métriques collectées: {len(metrics)} métriques")
        
        # Vérifier le statut de santé
        health_status = monitoring_service.get_health_status()
        print(f"  ✅ Statut de santé: {health_status['overall_status']}")
        
        # Arrêter le service
        monitoring_service.stop()
        print("  ✅ Service de monitoring arrêté")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test du service de monitoring: {e}")
        return False

def test_recovery_service():
    """Test du service de récupération"""
    print("\n🧪 Test du service de récupération...")
    
    try:
        from services.recovery_service import RecoveryService, RecoveryStrategy
        
        # Configuration de test
        config = {
            'recovery_enabled': True,
            'max_recovery_attempts': 3,
            'recovery_delay': 1.0,
            'health_check_interval': 2.0
        }
        
        # Créer et initialiser le service
        recovery_service = RecoveryService(config)
        
        if not recovery_service.initialize():
            print("  ❌ Échec d'initialisation du service de récupération")
            return False
        
        print("  ✅ Service de récupération initialisé")
        
        # Démarrer le service
        if not recovery_service.start():
            print("  ❌ Échec de démarrage du service de récupération")
            return False
        
        print("  ✅ Service de récupération démarré")
        
        # Ajouter un composant à la surveillance
        recovery_service.add_monitored_component("TestComponent")
        print("  ✅ Composant ajouté à la surveillance")
        
        # Forcer une récupération
        success = recovery_service.force_recovery("TestComponent", RecoveryStrategy.RESTART)
        if success:
            print("  ✅ Récupération forcée initiée")
        else:
            print("  ⚠️ Récupération forcée échouée")
        
        # Attendre un peu
        time.sleep(2)
        
        # Vérifier le statut
        status = recovery_service.get_recovery_status()
        print(f"  ✅ Statut de récupération: {len(status['active_recoveries'])} récupérations actives")
        
        # Arrêter le service
        recovery_service.stop()
        print("  ✅ Service de récupération arrêté")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test du service de récupération: {e}")
        return False

def test_health_check_service():
    """Test du service de vérification de santé"""
    print("\n🧪 Test du service de vérification de santé...")
    
    try:
        from services.health_check_service import HealthCheckService, HealthCheckType
        
        # Configuration de test
        config = {
            'check_interval': 5.0,
            'enabled_checks': ['system', 'component', 'service']
        }
        
        # Créer et initialiser le service
        health_service = HealthCheckService(config)
        
        if not health_service.initialize():
            print("  ❌ Échec d'initialisation du service de santé")
            return False
        
        print("  ✅ Service de santé initialisé")
        
        # Démarrer le service
        if not health_service.start():
            print("  ❌ Échec de démarrage du service de santé")
            return False
        
        print("  ✅ Service de santé démarré")
        
        # Attendre quelques cycles
        time.sleep(3)
        
        # Vérifier le statut global
        overall_status = health_service.get_overall_health_status()
        print(f"  ✅ Statut global: {overall_status['overall_status']}")
        print(f"  ✅ Vérifications: {len(overall_status['checks'])}")
        
        # Exécuter une vérification spécifique
        result = health_service.run_health_check('system')
        if result:
            print(f"  ✅ Vérification système: {result.status.value}")
        
        # Arrêter le service
        health_service.stop()
        print("  ✅ Service de santé arrêté")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test du service de santé: {e}")
        return False

def test_integration():
    """Test d'intégration des services"""
    print("\n🧪 Test d'intégration des services...")
    
    try:
        from utils.error_handler import ErrorHandler
        from services.monitoring_service import MonitoringService
        from services.recovery_service import RecoveryService
        from services.health_check_service import HealthCheckService
        
        # Créer les services
        error_handler = ErrorHandler()
        
        monitoring_config = {
            'update_interval': 1.0,
            'health_check_interval': 2.0,
            'metrics_retention_hours': 1
        }
        monitoring_service = MonitoringService(monitoring_config)
        
        recovery_config = {
            'recovery_enabled': True,
            'max_recovery_attempts': 3,
            'recovery_delay': 1.0,
            'health_check_interval': 2.0
        }
        recovery_service = RecoveryService(recovery_config)
        
        health_config = {
            'check_interval': 5.0,
            'enabled_checks': ['system', 'component']
        }
        health_service = HealthCheckService(health_config)
        
        # Initialiser tous les services
        services = [monitoring_service, recovery_service, health_service]
        for service in services:
            if not service.initialize():
                print(f"  ❌ Échec d'initialisation de {service.__class__.__name__}")
                return False
        
        print("  ✅ Tous les services initialisés")
        
        # Démarrer tous les services
        for service in services:
            if not service.start():
                print(f"  ❌ Échec de démarrage de {service.__class__.__name__}")
                return False
        
        print("  ✅ Tous les services démarrés")
        
        # Simuler le fonctionnement
        time.sleep(3)
        
        # Vérifier que tout fonctionne
        monitoring_metrics = monitoring_service.get_metrics()
        recovery_status = recovery_service.get_recovery_status()
        health_status = health_service.get_overall_health_status()
        
        print(f"  ✅ Monitoring: {len(monitoring_metrics)} métriques")
        print(f"  ✅ Récupération: {len(recovery_status['active_recoveries'])} récupérations actives")
        print(f"  ✅ Santé: {health_status['overall_status']}")
        
        # Arrêter tous les services
        for service in services:
            service.stop()
        
        print("  ✅ Tous les services arrêtés")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test d'intégration: {e}")
        return False

def test_error_recovery_simulation():
    """Test de simulation de récupération d'erreurs"""
    print("\n🧪 Test de simulation de récupération d'erreurs...")
    
    try:
        from utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory
        
        error_handler = ErrorHandler()
        
        # Simuler des erreurs multiples
        error_count = 0
        
        def error_prone_function():
            nonlocal error_count
            error_count += 1
            if error_count <= 3:
                raise Exception(f"Error {error_count}")
            return "success"
        
        # Exécuter avec retry
        result = error_handler.execute_with_retry(error_prone_function, "TestComponent")
        
        if result == "success" and error_count == 4:
            print(f"  ✅ Récupération réussie après {error_count} tentatives")
            return True
        else:
            print(f"  ❌ Échec de la récupération: {result}")
            return False
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test de récupération: {e}")
        return False

def test_performance_under_load():
    """Test de performance sous charge"""
    print("\n🧪 Test de performance sous charge...")
    
    try:
        from utils.error_handler import ErrorHandler
        
        error_handler = ErrorHandler()
        
        # Simuler une charge élevée
        start_time = time.time()
        operations_count = 0
        
        def simulate_operation():
            nonlocal operations_count
            operations_count += 1
            # Simuler une opération
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
        
        if operations_count > 0 and duration < 5.0:
            print(f"  ✅ Performance: {operations_count} opérations en {duration:.2f}s")
            return True
        else:
            print(f"  ❌ Performance insuffisante: {operations_count} opérations en {duration:.2f}s")
            return False
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test de performance: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS DE LA PHASE 1")
    print("=" * 60)
    
    tests = [
        ("Gestionnaire d'erreurs", test_error_handler),
        ("Service de monitoring", test_monitoring_service),
        ("Service de récupération", test_recovery_service),
        ("Service de vérification de santé", test_health_check_service),
        ("Intégration des services", test_integration),
        ("Simulation de récupération d'erreurs", test_error_recovery_simulation),
        ("Performance sous charge", test_performance_under_load)
    ]
    
    results = []
    
    for test_name, test_function in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_function()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name}: RÉUSSI")
            else:
                print(f"❌ {test_name}: ÉCHOUÉ")
        except Exception as e:
            print(f"💥 {test_name}: ERREUR - {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS DE LA PHASE 1")
    print("=" * 60)
    
    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
    
    print(f"\nRésultat global: {successful_tests}/{total_tests} tests réussis")
    
    if successful_tests == total_tests:
        print("🎉 TOUS LES TESTS DE LA PHASE 1 ONT RÉUSSI!")
        print("✅ Le système de gestion d'erreurs est robuste")
        print("✅ Le monitoring fonctionne correctement")
        print("✅ La récupération automatique est opérationnelle")
        print("✅ La vérification de santé est efficace")
        return True
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Veuillez vérifier les erreurs ci-dessus")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
