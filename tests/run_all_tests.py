#!/usr/bin/env python3
"""
Script principal pour exécuter tous les tests Alimante
"""

import sys
import os
import time
import subprocess
from pathlib import Path

def run_test_script(script_path, test_name):
    """Exécute un script de test et retourne le résultat"""
    print(f"\n{'='*60}")
    print(f"🧪 Exécution: {test_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, 
                              text=True, 
                              timeout=300)  # 5 minutes max
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: {test_name} a pris trop de temps")
        return False
    except Exception as e:
        print(f"❌ Erreur exécution {test_name}: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Démarrage de la suite de tests Alimante")
    print("=" * 60)
    
    # Liste des tests à exécuter
    tests = [
        ("test_event_system.py", "Tests du système d'événements"),
        ("test_safety_system.py", "Tests du système de sécurité"),
        ("test_system_integration.py", "Tests d'intégration système")
    ]
    
    # Vérifier que les fichiers de test existent
    test_dir = Path(__file__).parent
    missing_tests = []
    
    for script, name in tests:
        if not (test_dir / script).exists():
            missing_tests.append(script)
    
    if missing_tests:
        print(f"❌ Tests manquants: {', '.join(missing_tests)}")
        return 1
    
    # Exécuter les tests
    results = {}
    start_time = time.time()
    
    for script, name in tests:
        script_path = test_dir / script
        success = run_test_script(str(script_path), name)
        results[name] = success
        
        if success:
            print(f"✅ {name}: RÉUSSI")
        else:
            print(f"❌ {name}: ÉCHOUÉ")
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Résumé final
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ FINAL")
    print(f"{'='*60}")
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for name, success in results.items():
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"   {name}: {status}")
    
    print(f"\n📈 Résultat global: {passed}/{total} tests réussis")
    print(f"⏱️ Durée totale: {duration:.1f} secondes")
    
    if passed == total:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ Votre système Alimante est prêt pour la production !")
        return 0
    else:
        print(f"\n💥 {total - passed} TEST(S) ONT ÉCHOUÉ !")
        print("🔧 Veuillez corriger les problèmes avant de continuer.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
