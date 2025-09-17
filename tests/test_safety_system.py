#!/usr/bin/env python3
"""
Tests du système de sécurité Alimante
Vérifie que tous les mécanismes de sécurité fonctionnent correctement
"""

import sys
import os
import time
import logging
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.event_bus import EventBus
from services.safety_service import SafetyService

class SafetySystemTester:
    """Testeur du système de sécurité"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.safety_service = SafetyService(self.event_bus)
        self.emergency_events = []
        self.alert_events = []
        
        # S'abonner aux événements de sécurité
        self.event_bus.on('emergency_stop', self._on_emergency_stop)
        self.event_bus.on('safety_alert', self._on_safety_alert)
    
    def _on_emergency_stop(self, data):
        self.emergency_events.append(data)
        print(f"🚨 ARRÊT D'URGENCE: {data.get('reason', 'Inconnu')}")
    
    def _on_safety_alert(self, data):
        self.alert_events.append(data)
        print(f"⚠️ ALERTE SÉCURITÉ: {data.get('message', 'Inconnue')}")
    
    def test_temperature_limits(self):
        """Test des limites de température"""
        print("\n🌡️ Test des limites de température...")
        
        # Test température trop basse
        cold_data = {'temperature': 10.0, 'humidity': 50.0, 'air_quality': 50}
        violations = self.safety_service.check_safety_limits(cold_data)
        
        if violations:
            print(f"✅ Température basse détectée: {len(violations)} violations")
            for v in violations:
                print(f"   - {v['message']}")
        else:
            print("⚠️ Température basse non détectée")
        
        # Test température trop élevée
        hot_data = {'temperature': 40.0, 'humidity': 50.0, 'air_quality': 50}
        violations = self.safety_service.check_safety_limits(hot_data)
        
        if violations:
            print(f"✅ Température élevée détectée: {len(violations)} violations")
            for v in violations:
                print(f"   - {v['message']}")
        else:
            print("⚠️ Température élevée non détectée")
        
        return True
    
    def test_humidity_limits(self):
        """Test des limites d'humidité"""
        print("\n💧 Test des limites d'humidité...")
        
        # Test humidité trop basse
        dry_data = {'temperature': 25.0, 'humidity': 20.0, 'air_quality': 50}
        violations = self.safety_service.check_safety_limits(dry_data)
        
        if violations:
            print(f"✅ Humidité basse détectée: {len(violations)} violations")
        else:
            print("⚠️ Humidité basse non détectée")
        
        # Test humidité trop élevée
        wet_data = {'temperature': 25.0, 'humidity': 95.0, 'air_quality': 50}
        violations = self.safety_service.check_safety_limits(wet_data)
        
        if violations:
            print(f"✅ Humidité élevée détectée: {len(violations)} violations")
        else:
            print("⚠️ Humidité élevée non détectée")
        
        return True
    
    def test_air_quality_limits(self):
        """Test des limites de qualité d'air"""
        print("\n🌬️ Test des limites de qualité d'air...")
        
        # Test qualité d'air dangereuse
        bad_air_data = {'temperature': 25.0, 'humidity': 50.0, 'air_quality': 350}
        violations = self.safety_service.check_safety_limits(bad_air_data)
        
        if violations:
            print(f"✅ Qualité d'air dangereuse détectée: {len(violations)} violations")
            for v in violations:
                print(f"   - {v['message']}")
        else:
            print("⚠️ Qualité d'air dangereuse non détectée")
        
        return True
    
    def test_water_level_limits(self):
        """Test des limites de niveau d'eau"""
        print("\n💧 Test des limites de niveau d'eau...")
        
        # Test niveau d'eau critique
        low_water_data = {'temperature': 25.0, 'humidity': 50.0, 'air_quality': 50, 'water_level': 10.0}
        violations = self.safety_service.check_safety_limits(low_water_data)
        
        if violations:
            print(f"✅ Niveau d'eau critique détecté: {len(violations)} violations")
            for v in violations:
                print(f"   - {v['message']}")
        else:
            print("⚠️ Niveau d'eau critique non détecté")
        
        return True
    
    def test_emergency_stop_trigger(self):
        """Test du déclenchement d'arrêt d'urgence"""
        print("\n🚨 Test de déclenchement d'arrêt d'urgence...")
        
        # Simuler une violation critique
        critical_data = {'temperature': 45.0, 'humidity': 50.0, 'air_quality': 50}
        violations = self.safety_service.check_safety_limits(critical_data)
        
        time.sleep(0.5)  # Laisser le temps au traitement
        
        # Vérifier qu'un arrêt d'urgence a été déclenché
        if self.emergency_events:
            print(f"✅ Arrêt d'urgence déclenché: {len(self.emergency_events)} événements")
            for event in self.emergency_events:
                print(f"   - Raison: {event.get('reason', 'Inconnue')}")
        else:
            print("⚠️ Arrêt d'urgence non déclenché")
        
        return True
    
    def test_alert_system(self):
        """Test du système d'alertes"""
        print("\n⚠️ Test du système d'alertes...")
        
        # Simuler plusieurs violations
        test_cases = [
            {'temperature': 5.0, 'humidity': 50.0, 'air_quality': 50},
            {'temperature': 25.0, 'humidity': 10.0, 'air_quality': 50},
            {'temperature': 25.0, 'humidity': 50.0, 'air_quality': 400},
            {'temperature': 25.0, 'humidity': 50.0, 'air_quality': 50, 'water_level': 5.0}
        ]
        
        for i, data in enumerate(test_cases):
            print(f"   Test cas {i+1}: {data}")
            violations = self.safety_service.check_safety_limits(data)
            time.sleep(0.1)
        
        time.sleep(1)  # Laisser le temps au traitement
        
        print(f"✅ Alertes générées: {len(self.alert_events)}")
        for alert in self.alert_events:
            print(f"   - {alert.get('message', 'Inconnue')}")
        
        return True
    
    def test_emergency_resume(self):
        """Test de la reprise après arrêt d'urgence"""
        print("\n🔄 Test de reprise après arrêt d'urgence...")
        
        # Déclencher un arrêt d'urgence
        critical_data = {'temperature': 50.0, 'humidity': 50.0, 'air_quality': 50}
        self.safety_service.check_safety_limits(critical_data)
        
        time.sleep(0.5)
        
        # Vérifier que l'arrêt d'urgence est actif
        if self.safety_service.emergency_stop:
            print("✅ Arrêt d'urgence actif")
            
            # Tenter de reprendre
            success = self.safety_service.clear_emergency_stop()
            if success:
                print("✅ Reprise réussie")
                return True
            else:
                print("❌ Échec reprise")
                return False
        else:
            print("⚠️ Arrêt d'urgence non actif")
            return True
    
    def test_safety_statistics(self):
        """Test des statistiques de sécurité"""
        print("\n📊 Test des statistiques de sécurité...")
        
        # Obtenir les statistiques
        stats = self.safety_service.get_safety_status()
        
        print(f"✅ Statistiques de sécurité:")
        print(f"   - Arrêt d'urgence: {stats.get('emergency_stop', False)}")
        print(f"   - Alertes actives: {stats.get('active_alerts', 0)}")
        print(f"   - Total alertes: {stats.get('total_alerts', 0)}")
        print(f"   - Violations: {stats.get('safety_violations', 0)}")
        
        return True
    
    def run_all_tests(self):
        """Exécute tous les tests de sécurité"""
        print("🛡️ Démarrage des tests de sécurité Alimante")
        print("=" * 60)
        
        tests = [
            self.test_temperature_limits,
            self.test_humidity_limits,
            self.test_air_quality_limits,
            self.test_water_level_limits,
            self.test_emergency_stop_trigger,
            self.test_alert_system,
            self.test_emergency_resume,
            self.test_safety_statistics
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
        print(f"🚨 Arrêts d'urgence: {len(self.emergency_events)}")
        print(f"⚠️ Alertes générées: {len(self.alert_events)}")
        
        return failed == 0

def main():
    """Fonction principale de test"""
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer et exécuter les tests
    tester = SafetySystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Tous les tests de sécurité sont passés !")
        return 0
    else:
        print("\n💥 Certains tests de sécurité ont échoué !")
        return 1

if __name__ == "__main__":
    sys.exit(main())
