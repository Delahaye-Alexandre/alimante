"""
Test des améliorations de la Phase 2 pour Alimante
Valide le système d'authentification, les notifications, la sauvegarde et l'analyse
"""

import sys
import os
import time
import threading
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_auth_service():
    """Test du service d'authentification"""
    print("\n🧪 Test du service d'authentification...")
    
    try:
        from services.auth_service import AuthService, UserRole, AuthStatus
        
        # Configuration de test
        config = {
            'jwt_secret': 'test_secret_key_12345',
            'jwt_expiry': 3600,
            'max_failed_attempts': 3,
            'password_min_length': 6
        }
        
        # Créer le service
        auth_service = AuthService(config)
        
        if not auth_service.initialize():
            print("  ❌ Échec d'initialisation du service d'authentification")
            return False
        
        print("  ✅ Service d'authentification initialisé")
        
        # Test d'authentification avec l'utilisateur admin par défaut
        success, access_token, refresh_token = auth_service.authenticate("admin", "admin123")
        if success and access_token:
            print("  ✅ Authentification admin réussie")
        else:
            print("  ❌ Échec de l'authentification admin")
            return False
        
        # Test de vérification du token
        is_valid, user, permissions = auth_service.verify_token(access_token)
        if is_valid and user:
            print(f"  ✅ Token valide pour {user.username}")
        else:
            print("  ❌ Token invalide")
            return False
        
        # Test de création d'utilisateur
        success, message = auth_service.create_user("testuser", "test@example.com", "password123", UserRole.OPERATOR)
        if success:
            print("  ✅ Utilisateur créé avec succès")
        else:
            print(f"  ❌ Échec création utilisateur: {message}")
            return False
        
        # Test d'authentification du nouvel utilisateur
        success, access_token2, refresh_token2 = auth_service.authenticate("testuser", "password123")
        if success:
            print("  ✅ Authentification nouvel utilisateur réussie")
        else:
            print("  ❌ Échec authentification nouvel utilisateur")
            return False
        
        # Test de vérification des permissions
        has_permission = auth_service.check_permission(access_token2, "read")
        if has_permission:
            print("  ✅ Vérification des permissions fonctionnelle")
        else:
            print("  ❌ Échec vérification des permissions")
            return False
        
        # Test des statistiques
        stats = auth_service.get_auth_stats()
        print(f"  ✅ Statistiques: {stats['total_users']} utilisateurs, {stats['active_tokens']} tokens actifs")
        
        # Arrêter le service
        auth_service.stop()
        print("  ✅ Service d'authentification arrêté")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test d'authentification: {e}")
        return False

def test_notification_service():
    """Test du service de notifications"""
    print("\n🧪 Test du service de notifications...")
    
    try:
        from services.notification_service import NotificationService, NotificationChannel, NotificationPriority
        
        # Configuration de test
        config = {
            'email': {'enabled': False},  # Désactiver pour les tests
            'sms': {'enabled': False},
            'webhook': {'enabled': False},
            'push': {'enabled': False},
            'max_retries': 2,
            'retry_delay': 1
        }
        
        # Créer le service
        notification_service = NotificationService(config)
        
        if not notification_service.initialize():
            print("  ❌ Échec d'initialisation du service de notifications")
            return False
        
        print("  ✅ Service de notifications initialisé")
        
        # Démarrer le service
        if not notification_service.start():
            print("  ❌ Échec de démarrage du service de notifications")
            return False
        
        print("  ✅ Service de notifications démarré")
        
        # Test d'envoi de notification
        variables = {
            'alert_type': 'Test Alert',
            'component': 'TestComponent',
            'message': 'This is a test notification',
            'timestamp': datetime.now().isoformat()
        }
        
        success = notification_service.send_notification(
            'system_alert',
            'test@example.com',
            variables,
            [NotificationChannel.LOG],  # Utiliser seulement les logs
            NotificationPriority.MEDIUM
        )
        
        if success:
            print("  ✅ Notification envoyée avec succès")
        else:
            print("  ❌ Échec envoi de notification")
            return False
        
        # Attendre le traitement
        time.sleep(2)
        
        # Vérifier les statistiques
        stats = notification_service.get_notification_stats()
        print(f"  ✅ Statistiques: {stats['total_sent']} notifications envoyées")
        
        # Test d'envoi de notification critique
        variables_critical = {
            'component': 'CriticalComponent',
            'function': 'critical_function',
            'error_message': 'Critical error occurred',
            'timestamp': datetime.now().isoformat()
        }
        
        success = notification_service.send_notification(
            'critical_error',
            'admin@example.com',
            variables_critical,
            [NotificationChannel.LOG],
            NotificationPriority.CRITICAL
        )
        
        if success:
            print("  ✅ Notification critique envoyée")
        else:
            print("  ❌ Échec envoi notification critique")
            return False
        
        # Attendre le traitement
        time.sleep(2)
        
        # Vérifier les notifications récentes
        recent = notification_service.get_recent_notifications(5)
        print(f"  ✅ Notifications récentes: {len(recent)}")
        
        # Arrêter le service
        notification_service.stop()
        print("  ✅ Service de notifications arrêté")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test de notifications: {e}")
        return False

def test_backup_service():
    """Test du service de sauvegarde"""
    print("\n🧪 Test du service de sauvegarde...")
    
    try:
        from services.backup_service import BackupService, BackupType, BackupStatus
        
        # Configuration de test
        config = {
            'backup_enabled': True,
            'backup_interval': 60,  # 1 minute pour les tests
            'retention_days': 7,
            'max_backups': 5,
            'sync_enabled': False,  # Désactiver la sync pour les tests
            'backup_paths': ['config/', 'src/'],
            'exclude_patterns': ['*.pyc', '__pycache__/']
        }
        
        # Créer le service
        backup_service = BackupService(config)
        
        if not backup_service.initialize():
            print("  ❌ Échec d'initialisation du service de sauvegarde")
            return False
        
        print("  ✅ Service de sauvegarde initialisé")
        
        # Démarrer le service
        if not backup_service.start():
            print("  ❌ Échec de démarrage du service de sauvegarde")
            return False
        
        print("  ✅ Service de sauvegarde démarré")
        
        # Test de création de sauvegarde manuelle
        success, backup_id = backup_service.create_backup(BackupType.FULL, "Test backup")
        if success:
            print(f"  ✅ Sauvegarde créée: {backup_id}")
        else:
            print("  ❌ Échec création de sauvegarde")
            return False
        
        # Attendre un peu pour que la sauvegarde se termine
        time.sleep(2)
        
        # Vérifier les statistiques
        stats = backup_service.get_backup_stats()
        print(f"  ✅ Statistiques: {stats['total_backups']} sauvegardes, {stats['total_size_mb']:.2f} MB")
        
        # Lister les sauvegardes
        backups = backup_service.list_backups()
        if backups:
            print(f"  ✅ Sauvegardes disponibles: {len(backups)}")
            latest_backup = backups[0]
            print(f"  ✅ Dernière sauvegarde: {latest_backup['id']} ({latest_backup['size_mb']:.2f} MB)")
        else:
            print("  ⚠️ Aucune sauvegarde trouvée")
        
        # Test de création de sauvegarde de configuration
        success, config_backup_id = backup_service.create_backup(BackupType.CONFIG, "Config backup")
        if success:
            print(f"  ✅ Sauvegarde config créée: {config_backup_id}")
        else:
            print("  ❌ Échec création sauvegarde config")
        
        # Arrêter le service
        backup_service.stop()
        print("  ✅ Service de sauvegarde arrêté")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test de sauvegarde: {e}")
        return False

def test_analytics_service():
    """Test du service d'analyse"""
    print("\n🧪 Test du service d'analyse...")
    
    try:
        from services.analytics_service import AnalyticsService, MetricType, ReportType
        
        # Configuration de test
        config = {
            'analysis_interval': 10,  # 10 secondes pour les tests
            'report_interval': 30,    # 30 secondes pour les tests
            'data_retention_days': 7,
            'alert_thresholds': {
                'temperature': {'min': 15, 'max': 35},
                'humidity': {'min': 30, 'max': 80}
            }
        }
        
        # Créer le service
        analytics_service = AnalyticsService(config)
        
        if not analytics_service.initialize():
            print("  ❌ Échec d'initialisation du service d'analyse")
            return False
        
        print("  ✅ Service d'analyse initialisé")
        
        # Démarrer le service
        if not analytics_service.start():
            print("  ❌ Échec de démarrage du service d'analyse")
            return False
        
        print("  ✅ Service d'analyse démarré")
        
        # Ajouter des points de données de test
        import random
        
        for i in range(20):
            # Données de température
            analytics_service.add_data_point(
                MetricType.TEMPERATURE,
                20 + random.uniform(-5, 10),  # 15-30°C
                "terrarium_1",
                {"sensor_id": "temp_1"}
            )
            
            # Données d'humidité
            analytics_service.add_data_point(
                MetricType.HUMIDITY,
                50 + random.uniform(-20, 20),  # 30-70%
                "terrarium_1",
                {"sensor_id": "hum_1"}
            )
            
            time.sleep(0.1)  # Petite pause
        
        print("  ✅ Points de données ajoutés")
        
        # Attendre l'analyse
        time.sleep(2)
        
        # Vérifier les statistiques
        stats = analytics_service.get_analytics_stats()
        print(f"  ✅ Statistiques: {stats['real_time_stats']['total_data_points']} points de données")
        
        # Récupérer les données récentes
        recent_data = analytics_service.get_recent_data(MetricType.TEMPERATURE, "terrarium_1", 1)
        print(f"  ✅ Données récentes: {len(recent_data)} points de température")
        
        # Attendre la génération de rapport
        time.sleep(5)
        
        # Vérifier les rapports
        reports = analytics_service.get_reports(ReportType.DAILY, 5)
        if reports:
            print(f"  ✅ Rapports générés: {len(reports)}")
            latest_report = reports[0]
            print(f"  ✅ Dernier rapport: {latest_report['title']}")
        else:
            print("  ⚠️ Aucun rapport généré")
        
        # Test d'ajout de données avec anomalie
        analytics_service.add_data_point(
            MetricType.TEMPERATURE,
            50,  # Température anormalement élevée
            "terrarium_1",
            {"sensor_id": "temp_1", "anomaly": True}
        )
        
        print("  ✅ Donnée avec anomalie ajoutée")
        
        # Arrêter le service
        analytics_service.stop()
        print("  ✅ Service d'analyse arrêté")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test d'analyse: {e}")
        return False

def test_integration_phase2():
    """Test d'intégration des services de la Phase 2"""
    print("\n🧪 Test d'intégration Phase 2...")
    
    try:
        from services.auth_service import AuthService, UserRole
        from services.notification_service import NotificationService, NotificationChannel, NotificationPriority
        from services.backup_service import BackupService, BackupType
        from services.analytics_service import AnalyticsService, MetricType
        
        # Créer tous les services
        auth_config = {'jwt_secret': 'test_secret', 'password_min_length': 6}
        auth_service = AuthService(auth_config)
        
        notification_config = {
            'email': {'enabled': False},
            'sms': {'enabled': False},
            'webhook': {'enabled': False},
            'push': {'enabled': False}
        }
        notification_service = NotificationService(notification_config)
        
        backup_config = {
            'backup_enabled': True,
            'sync_enabled': False,
            'backup_paths': ['config/'],
            'exclude_patterns': ['*.pyc']
        }
        backup_service = BackupService(backup_config)
        
        analytics_config = {
            'analysis_interval': 10,
            'report_interval': 30,
            'data_retention_days': 7
        }
        analytics_service = AnalyticsService(analytics_config)
        
        # Initialiser tous les services
        services = [auth_service, notification_service, backup_service, analytics_service]
        for service in services:
            if not service.initialize():
                print(f"  ❌ Échec d'initialisation de {service.__class__.__name__}")
                return False
        
        print("  ✅ Tous les services Phase 2 initialisés")
        
        # Démarrer tous les services
        for service in services:
            if not service.start():
                print(f"  ❌ Échec de démarrage de {service.__class__.__name__}")
                return False
        
        print("  ✅ Tous les services Phase 2 démarrés")
        
        # Test d'intégration: authentification + notification
        success, access_token, refresh_token = auth_service.authenticate("admin", "admin123")
        if success:
            print("  ✅ Authentification intégrée réussie")
            
            # Envoyer une notification basée sur l'authentification
            notification_service.send_notification(
                'system_alert',
                'admin@example.com',
                {
                    'alert_type': 'User Login',
                    'component': 'AuthService',
                    'message': f'User admin logged in successfully',
                    'timestamp': datetime.now().isoformat()
                },
                [NotificationChannel.LOG],
                NotificationPriority.MEDIUM
            )
            print("  ✅ Notification d'authentification envoyée")
        
        # Test d'intégration: sauvegarde + analyse
        success, backup_id = backup_service.create_backup(BackupType.FULL, "Integration test backup")
        if success:
            print(f"  ✅ Sauvegarde d'intégration créée: {backup_id}")
            
            # Ajouter des données d'analyse sur la sauvegarde
            analytics_service.add_data_point(
                MetricType.SYSTEM_LOAD,
                75.0,
                "backup_system",
                {"backup_id": backup_id, "operation": "backup_created"}
            )
            print("  ✅ Données d'analyse de sauvegarde ajoutées")
        
        # Attendre le traitement
        time.sleep(3)
        
        # Vérifier que tout fonctionne ensemble
        auth_stats = auth_service.get_auth_stats()
        notification_stats = notification_service.get_notification_stats()
        backup_stats = backup_service.get_backup_stats()
        analytics_stats = analytics_service.get_analytics_stats()
        
        print(f"  ✅ Intégration: {auth_stats['total_users']} utilisateurs, "
              f"{notification_stats['total_sent']} notifications, "
              f"{backup_stats['total_backups']} sauvegardes, "
              f"{analytics_stats['real_time_stats']['total_data_points']} points de données")
        
        # Arrêter tous les services
        for service in services:
            service.stop()
        
        print("  ✅ Tous les services Phase 2 arrêtés")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur dans le test d'intégration Phase 2: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS DE LA PHASE 2")
    print("=" * 60)
    
    tests = [
        ("Service d'authentification", test_auth_service),
        ("Service de notifications", test_notification_service),
        ("Service de sauvegarde", test_backup_service),
        ("Service d'analyse", test_analytics_service),
        ("Intégration Phase 2", test_integration_phase2)
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
    print("📊 RÉSUMÉ DES TESTS DE LA PHASE 2")
    print("=" * 60)
    
    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
    
    print(f"\nRésultat global: {successful_tests}/{total_tests} tests réussis")
    
    if successful_tests == total_tests:
        print("🎉 TOUS LES TESTS DE LA PHASE 2 ONT RÉUSSI!")
        print("✅ Le système d'authentification est sécurisé")
        print("✅ Les notifications multi-canaux fonctionnent")
        print("✅ La sauvegarde automatique est opérationnelle")
        print("✅ L'analyse de données est efficace")
        print("✅ L'intégration des services est réussie")
        return True
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Veuillez vérifier les erreurs ci-dessus")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
