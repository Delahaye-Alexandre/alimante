#!/usr/bin/env python3
"""
Tests pour le système de gestion d'erreurs et de logging
Valide le bon fonctionnement des exceptions et du logging
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.exceptions import (
    ErrorCode, 
    AlimanteException, 
    create_exception,
    SystemException,
    SensorException,
    ControllerException,
    APIException
)
from utils.logging_config import get_logger, log_system_start, log_system_stop
from utils.error_handler import create_api_error, create_validation_error


def test_exception_hierarchy():
    """Test la hiérarchie des exceptions"""
    print("🧪 Test de la hiérarchie des exceptions...")
    
    # Test création d'exceptions
    system_exc = create_exception(
        ErrorCode.SYSTEM_INIT_FAILED,
        "Test erreur système",
        {"test": True}
    )
    
    sensor_exc = create_exception(
        ErrorCode.SENSOR_READ_FAILED,
        "Test erreur capteur",
        {"sensor": "temperature"}
    )
    
    api_exc = create_exception(
        ErrorCode.API_INVALID_REQUEST,
        "Test erreur API"
    )
    
    # Vérifier les types
    assert isinstance(system_exc, SystemException)
    assert isinstance(sensor_exc, SensorException)
    assert isinstance(api_exc, APIException)
    
    # Vérifier les codes d'erreur
    assert system_exc.error_code == ErrorCode.SYSTEM_INIT_FAILED
    assert sensor_exc.error_code == ErrorCode.SENSOR_READ_FAILED
    assert api_exc.error_code == ErrorCode.API_INVALID_REQUEST
    
    # Vérifier la conversion en dict
    system_dict = system_exc.to_dict()
    assert system_dict["error_code"] == 1000
    assert system_dict["error_name"] == "SYSTEM_INIT_FAILED"
    assert system_dict["message"] == "Test erreur système"
    assert system_dict["context"]["test"] is True
    
    print("✅ Hiérarchie des exceptions OK")


def test_logging_system():
    """Test le système de logging"""
    print("🧪 Test du système de logging...")
    
    # Créer un dossier temporaire pour les logs
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        # Initialiser le logger
        logger = get_logger("test")
        
        # Tester différents niveaux de log
        logger.debug("Message debug", {"level": "debug"})
        logger.info("Message info", {"level": "info"})
        logger.warning("Message warning", {"level": "warning"})
        logger.error("Message error", {"level": "error"})
        
        # Tester les fonctions utilitaires
        log_system_start()
        log_system_stop()
        
        # Vérifier que les fichiers de log ont été créés
        log_files = list(Path("logs").glob("*.log"))
        assert len(log_files) > 0, "Aucun fichier de log créé"
        
        # Vérifier le contenu du log principal
        main_log = Path("logs/alimante.log")
        assert main_log.exists(), "Fichier de log principal manquant"
        
        with open(main_log, 'r') as f:
            log_content = f.read()
            assert "Message info" in log_content
            assert "Message error" in log_content
        
        print("✅ Système de logging OK")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)


def test_error_handler():
    """Test le gestionnaire d'erreurs"""
    print("🧪 Test du gestionnaire d'erreurs...")
    
    # Test création d'erreurs API
    api_error = create_api_error(
        ErrorCode.API_INVALID_REQUEST,
        "Test erreur API",
        {"field": "test"}
    )
    
    validation_error = create_validation_error("email", "Format invalide")
    
    # Vérifier les types
    assert isinstance(api_error, APIException)
    assert isinstance(validation_error, APIException)
    
    # Vérifier les messages
    assert "Test erreur API" in str(api_error)
    assert "email" in str(validation_error)
    assert "Format invalide" in str(validation_error)
    
    print("✅ Gestionnaire d'erreurs OK")


def test_error_codes():
    """Test les codes d'erreur"""
    print("🧪 Test des codes d'erreur...")
    
    # Vérifier que tous les codes sont uniques
    codes = [code.value for code in ErrorCode]
    assert len(codes) == len(set(codes)), "Codes d'erreur dupliqués"
    
    # Vérifier les plages de codes
    for code in ErrorCode:
        if "SYSTEM" in code.name:
            assert 1000 <= code.value < 2000
        elif "SENSOR" in code.name:
            assert 2000 <= code.value < 3000
        elif "CONTROLLER" in code.name:
            assert 3000 <= code.value < 4000
        elif "API" in code.name:
            assert 4000 <= code.value < 5000
        elif "DATA" in code.name:
            assert 5000 <= code.value < 6000
        elif "NETWORK" in code.name:
            assert 6000 <= code.value < 7000
    
    print("✅ Codes d'erreur OK")


def test_exception_context():
    """Test le contexte des exceptions"""
    print("🧪 Test du contexte des exceptions...")
    
    # Créer une exception avec contexte complexe
    context = {
        "user_id": "123",
        "action": "temperature_control",
        "parameters": {
            "target": 25.0,
            "tolerance": 2.0
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    exc = create_exception(
        ErrorCode.TEMPERATURE_OUT_OF_RANGE,
        "Température hors limites",
        context
    )
    
    # Vérifier le contexte
    assert exc.context["user_id"] == "123"
    assert exc.context["action"] == "temperature_control"
    assert exc.context["parameters"]["target"] == 25.0
    
    # Vérifier la conversion en dict
    exc_dict = exc.to_dict()
    assert exc_dict["context"]["user_id"] == "123"
    
    print("✅ Contexte des exceptions OK")


def test_logging_with_context():
    """Test le logging avec contexte"""
    print("🧪 Test du logging avec contexte...")
    
    # Créer un dossier temporaire
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        logger = get_logger("test_context")
        
        # Tester le logging avec contexte
        context = {
            "user_id": "test_user",
            "action": "test_action",
            "parameters": {"param1": "value1"}
        }
        
        logger.info("Test avec contexte", context)
        logger.error("Test erreur avec contexte", context, "TEST_ERROR")
        
        # Vérifier que le contexte est dans les logs
        log_file = Path("logs/alimante.log")
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_content = f.read()
                # Vérifier que le JSON contient le contexte
                log_entries = [json.loads(line) for line in log_content.strip().split('\n') if line]
                
                context_found = False
                for entry in log_entries:
                    if "context" in entry and entry["context"].get("user_id") == "test_user":
                        context_found = True
                        break
                
                assert context_found, "Contexte non trouvé dans les logs"
        
        print("✅ Logging avec contexte OK")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)


def main():
    """Exécute tous les tests"""
    print("🧪 Tests du système de gestion d'erreurs et de logging")
    print("=" * 60)
    
    tests = [
        ("Hiérarchie des exceptions", test_exception_hierarchy),
        ("Système de logging", test_logging_system),
        ("Gestionnaire d'erreurs", test_error_handler),
        ("Codes d'erreur", test_error_codes),
        ("Contexte des exceptions", test_exception_context),
        ("Logging avec contexte", test_logging_with_context),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        try:
            test_func()
            print(f"✅ {test_name} - PASSÉ")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} - ÉCHOUÉ: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 Tous les tests sont passés !")
        print("✅ Le système de gestion d'erreurs et de logging fonctionne correctement.")
    else:
        print("⚠️ Certains tests ont échoué.")
        print("🔧 Vérifiez les erreurs ci-dessus.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 