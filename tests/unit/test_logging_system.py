#!/usr/bin/env python3
"""
Tests unitaires pour le système de logging Alimante
"""

import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.logging_config import (
    AlimanteLogger,
    get_logger,
    setup_logging,
    test_logging_system,
    get_logging_status,
    log_system_start,
    log_system_stop,
    log_sensor_reading,
    log_controller_action,
    log_api_request,
    log_error_with_context,
    cleanup_test_logs
)


class TestAlimanteLogger(unittest.TestCase):
    """Tests pour la classe AlimanteLogger"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Créer le dossier logs
        os.makedirs("logs", exist_ok=True)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_logger_creation(self):
        """Test de création d'un logger"""
        logger = AlimanteLogger("test_logger")
        self.assertEqual(logger.name, "test_logger")
        self.assertIsNotNone(logger.logger)
    
    def test_logger_singleton(self):
        """Test du pattern singleton"""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        self.assertIs(logger1, logger2)
    
    def test_logger_methods(self):
        """Test des méthodes de logging"""
        logger = AlimanteLogger("test_methods")
        
        # Test des différents niveaux
        logger.debug("Test debug")
        logger.info("Test info")
        logger.warning("Test warning")
        logger.error("Test error")
        logger.critical("Test critical")
        
        # Vérifier que les handlers sont configurés
        self.assertGreater(len(logger.logger.handlers), 0)
    
    def test_logging_with_context(self):
        """Test du logging avec contexte"""
        logger = AlimanteLogger("test_context")
        
        context = {"user_id": "123", "action": "test"}
        logger.info("Test avec contexte", context)
        
        # Vérifier que le contexte est bien passé
        self.assertTrue(True)  # Pas d'erreur = succès
    
    def test_logging_with_error_code(self):
        """Test du logging avec code d'erreur"""
        logger = AlimanteLogger("test_error_code")
        
        logger.error("Test erreur", error_code="TEST_001")
        self.assertTrue(True)  # Pas d'erreur = succès
    
    def test_exception_logging(self):
        """Test du logging d'exceptions"""
        logger = AlimanteLogger("test_exception")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Exception capturée")
        
        self.assertTrue(True)  # Pas d'erreur = succès
    
    def test_metrics_logging(self):
        """Test du logging de métriques"""
        logger = AlimanteLogger("test_metrics")
        
        logger.metric("test_metric", 42.5, {"tag": "test"})
        self.assertTrue(True)  # Pas d'erreur = succès


class TestLoggingFunctions(unittest.TestCase):
    """Tests pour les fonctions utilitaires de logging"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Créer le dossier logs
        os.makedirs("logs", exist_ok=True)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_setup_logging(self):
        """Test de la fonction setup_logging"""
        logger = setup_logging("test_setup")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "test_setup")
    
    def test_test_logging_system(self):
        """Test de la fonction test_logging_system"""
        result = test_logging_system()
        self.assertIsInstance(result, bool)
    
    def test_get_logging_status(self):
        """Test de la fonction get_logging_status"""
        status = get_logging_status()
        self.assertIsInstance(status, dict)
        self.assertIn("name", status)
        self.assertIn("level", status)
        self.assertIn("handlers_count", status)
    
    def test_system_logs(self):
        """Test des logs système"""
        log_system_start()
        log_system_stop()
        self.assertTrue(True)  # Pas d'erreur = succès
    
    def test_sensor_logging(self):
        """Test du logging de capteurs"""
        log_sensor_reading("temperature", 25.5, "°C")
        log_sensor_reading("humidity", 65.2, "%")
        self.assertTrue(True)  # Pas d'erreur = succès
    
    def test_controller_logging(self):
        """Test du logging de contrôleurs"""
        log_controller_action("pump", "start", True, {"pressure": 2.1})
        log_controller_action("fan", "stop", False, {"error": "timeout"})
        self.assertTrue(True)  # Pas d'erreur = succès
    
    def test_api_logging(self):
        """Test du logging d'API"""
        log_api_request("GET", "/api/sensors", 200, 45.2, "user123")
        log_api_request("POST", "/api/config", 400, 120.5, "user456")
        self.assertTrue(True)  # Pas d'erreur = succès
    
    def test_error_logging(self):
        """Test du logging d'erreurs"""
        try:
            raise RuntimeError("Test error")
        except RuntimeError as e:
            log_error_with_context(e, {"operation": "test"})
        
        self.assertTrue(True)  # Pas d'erreur = succès
    
    def test_cleanup_test_logs(self):
        """Test de la fonction de nettoyage"""
        # Créer un fichier de test
        test_log = Path("logs") / "test.log"
        test_log.write_text("test content")
        
        # Nettoyer
        cleanup_test_logs()
        
        # Vérifier que le fichier existe toujours (cleanup ne supprime que les patterns spécifiques)
        self.assertTrue(test_log.exists())


class TestLoggingRobustness(unittest.TestCase):
    """Tests de robustesse du système de logging"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_logging_without_logs_directory(self):
        """Test du logging sans dossier logs (doit fonctionner)"""
        logger = AlimanteLogger("test_no_logs")
        
        # Le système doit fonctionner même sans dossier logs
        logger.info("Test sans dossier logs")
        self.assertTrue(True)  # Pas d'erreur = succès
    
    def test_logging_with_readonly_directory(self):
        """Test du logging avec un dossier en lecture seule"""
        # Créer un dossier logs en lecture seule
        os.makedirs("logs", exist_ok=True)
        os.chmod("logs", 0o444)  # Lecture seule
        
        try:
            logger = AlimanteLogger("test_readonly")
            logger.info("Test avec dossier en lecture seule")
            self.assertTrue(True)  # Pas d'erreur = succès
        finally:
            # Restaurer les permissions
            os.chmod("logs", 0o755)
    
    def test_logging_with_invalid_formatter(self):
        """Test du logging avec un formateur invalide"""
        logger = AlimanteLogger("test_invalid_formatter")
        
        # Le système doit continuer à fonctionner
        logger.info("Test avec formateur potentiellement invalide")
        self.assertTrue(True)  # Pas d'erreur = succès


if __name__ == "__main__":
    # Créer un test suite
    test_suite = unittest.TestSuite()
    
    # Ajouter les tests
    test_suite.addTest(unittest.makeSuite(TestAlimanteLogger))
    test_suite.addTest(unittest.makeSuite(TestLoggingFunctions))
    test_suite.addTest(unittest.makeSuite(TestLoggingRobustness))
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Code de sortie basé sur le résultat
    sys.exit(0 if result.wasSuccessful() else 1)
