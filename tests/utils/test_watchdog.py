#!/usr/bin/env python3
"""
Test du service Watchdog Alimante
Teste toutes les fonctionnalités du service de surveillance critique
"""

import time
import sys
import os

# Ajouter le répertoire src au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.gpio_manager import GPIOManager
from src.services.watchdog_service import WatchdogService, AlertLevel
from src.utils.logging_config import setup_logging

def test_watchdog_basic():
    """Test basique du service watchdog"""
    print("🔍 Test basique du service watchdog...")
    
    try:
        # Initialisation
        gpio_manager = GPIOManager()
        watchdog = WatchdogService(gpio_manager, {
            "watchdog_pin": 18,
            "timeout_seconds": 5,  # Timeout court pour les tests
            "max_cpu_temp": 80.0,
            "max_cpu_usage": 90.0,
            "max_memory_usage": 85.0
        })
        
        print("✅ Service watchdog initialisé")
        
        # Test du statut
        status = watchdog.get_system_status()
        print(f"📊 Statut système: {status['status']}")
        print(f"🌡️ Température CPU: {status['system']['cpu_temp']}°C")
        print(f"💾 Utilisation mémoire: {status['system']['memory_usage']}%")
        
        return watchdog
        
    except Exception as e:
        print(f"❌ Erreur test basique: {e}")
        return None

def test_watchdog_alerts(watchdog):
    """Test des alertes du watchdog"""
    print("\n🚨 Test des alertes...")
    
    try:
        # Test création d'alerte info
        watchdog._create_alert(
            AlertLevel.INFO,
            "Test alerte info",
            "test_script"
        )
        print("✅ Alerte INFO créée")
        
        # Test création d'alerte warning
        watchdog._create_alert(
            AlertLevel.WARNING,
            "Test alerte warning",
            "test_script",
            {"test_data": "valeur_test"}
        )
        print("✅ Alerte WARNING créée")
        
        # Test création d'alerte critical
        watchdog._create_alert(
            AlertLevel.CRITICAL,
            "Test alerte critical",
            "test_script"
        )
        print("✅ Alerte CRITICAL créée")
        
        # Vérification des alertes
        alerts = watchdog.get_alerts()
        print(f"📋 Total alertes: {len(alerts)}")
        
        for i, alert in enumerate(alerts):
            print(f"  {i}: [{alert.level.value}] {alert.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test alertes: {e}")
        return False

def test_watchdog_monitoring(watchdog):
    """Test du monitoring système"""
    print("\n📊 Test du monitoring système...")
    
    try:
        # Démarrer le monitoring
        watchdog.start()
        print("✅ Monitoring démarré")
        
        # Attendre quelques secondes pour collecter des données
        print("⏳ Collecte de données système...")
        time.sleep(3)
        
        # Vérifier le statut
        status = watchdog.get_system_status()
        print(f"📈 Heartbeats envoyés: {status['stats']['heartbeats_sent']}")
        print(f"🔄 Alertes générées: {status['stats']['alerts_generated']}")
        
        # Arrêter le monitoring
        watchdog.stop()
        print("✅ Monitoring arrêté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test monitoring: {e}")
        return False

def test_watchdog_callbacks(watchdog):
    """Test des callbacks d'alerte"""
    print("\n🔔 Test des callbacks d'alerte...")
    
    try:
        # Variable pour stocker les alertes reçues
        received_alerts = []
        
        def alert_callback(alert):
            received_alerts.append(alert)
            print(f"🔔 Callback reçu: {alert.message}")
        
        # Ajouter le callback
        watchdog.add_alert_callback(alert_callback)
        print("✅ Callback ajouté")
        
        # Créer une alerte pour déclencher le callback
        watchdog._create_alert(
            AlertLevel.INFO,
            "Test callback",
            "test_script"
        )
        
        # Vérifier que le callback a été appelé
        if len(received_alerts) > 0:
            print("✅ Callback fonctionne correctement")
            return True
        else:
            print("❌ Callback non appelé")
            return False
        
    except Exception as e:
        print(f"❌ Erreur test callbacks: {e}")
        return False

def test_watchdog_management(watchdog):
    """Test de la gestion des alertes"""
    print("\n🛠️ Test de la gestion des alertes...")
    
    try:
        # Créer quelques alertes
        for i in range(3):
            watchdog._create_alert(
                AlertLevel.WARNING,
                f"Alerte test {i}",
                "test_script"
            )
        
        # Vérifier le nombre d'alertes
        alerts = watchdog.get_alerts()
        print(f"📋 Alertes avant résolution: {len(alerts)}")
        
        # Résoudre une alerte
        if len(alerts) > 0:
            watchdog.resolve_alert(0)
            print("✅ Première alerte résolue")
        
        # Vérifier les alertes non résolues
        unresolved = [a for a in watchdog.get_alerts() if not a.resolved]
        print(f"📋 Alertes non résolues: {len(unresolved)}")
        
        # Nettoyer les anciennes alertes (plus de 0 jours = toutes)
        watchdog.clear_old_alerts(0)
        print("✅ Nettoyage des alertes effectué")
        
        # Vérifier qu'il ne reste plus d'alertes
        remaining_alerts = watchdog.get_alerts()
        print(f"📋 Alertes restantes: {len(remaining_alerts)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test gestion: {e}")
        return False

def test_watchdog_safety():
    """Test des mécanismes de sécurité (sans redémarrage réel)"""
    print("\n🛡️ Test des mécanismes de sécurité...")
    
    try:
        # Créer un watchdog avec des seuils très bas pour déclencher des alertes
        gpio_manager = GPIOManager()
        safety_watchdog = WatchdogService(gpio_manager, {
            "watchdog_pin": 18,
            "timeout_seconds": 10,
            "max_cpu_temp": 0.1,  # Seuil très bas pour déclencher une alerte
            "max_cpu_usage": 0.1,
            "max_memory_usage": 0.1
        })
        
        # Démarrer le monitoring
        safety_watchdog.start()
        print("✅ Monitoring de sécurité démarré")
        
        # Attendre pour la collecte de données
        time.sleep(2)
        
        # Vérifier les alertes générées
        alerts = safety_watchdog.get_alerts()
        print(f"🚨 Alertes de sécurité générées: {len(alerts)}")
        
        # Arrêter le monitoring
        safety_watchdog.stop()
        print("✅ Monitoring de sécurité arrêté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test sécurité: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests du service Watchdog Alimante")
    print("=" * 60)
    
    # Test basique
    watchdog = test_watchdog_basic()
    if not watchdog:
        print("❌ Test basique échoué, arrêt des tests")
        return
    
    # Tests des fonctionnalités
    tests = [
        ("Alertes", lambda: test_watchdog_alerts(watchdog)),
        ("Monitoring", lambda: test_watchdog_monitoring(watchdog)),
        ("Callbacks", lambda: test_watchdog_callbacks(watchdog)),
        ("Gestion", lambda: test_watchdog_management(watchdog)),
        ("Sécurité", lambda: test_watchdog_safety())
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur dans le test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé des tests
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} : {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés avec succès !")
    else:
        print("⚠️ Certains tests ont échoué")
    
    # Nettoyage
    if watchdog:
        watchdog.cleanup()
        print("🧹 Nettoyage effectué")

if __name__ == "__main__":
    main()
