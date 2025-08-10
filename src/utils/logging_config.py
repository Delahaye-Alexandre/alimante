"""
Configuration centralisée du logging pour Alimante
Système de logging structuré avec différents niveaux et handlers
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Formateur JSON structuré pour les logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formate un record en JSON structuré"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Ajouter les attributs personnalisés
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        if hasattr(record, 'error_code'):
            log_entry['error_code'] = record.error_code
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
            
        # Ajouter l'exception si présente
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Formateur coloré pour la console"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Formate avec couleurs pour la console"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format: [TIMESTAMP] LEVEL | MODULE:FUNCTION:LINE | MESSAGE
        formatted = (
            f"{color}[{self.formatTime(record)}] {record.levelname}{reset} | "
            f"{record.module}:{record.funcName}:{record.lineno} | "
            f"{record.getMessage()}"
        )
        
        # Ajouter l'exception si présente
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
            
        return formatted


class AlimanteLogger:
    """Logger centralisé pour Alimante"""
    
    def __init__(self, name: str = "alimante"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure le logger avec tous les handlers"""
        try:
            self.logger.setLevel(logging.DEBUG)
            
            # Éviter les logs dupliqués
            if self.logger.handlers:
                return
                
            # Handler console avec couleurs
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(ColoredFormatter())
            self.logger.addHandler(console_handler)
            
            # Handler fichier principal (JSON structuré)
            self._setup_file_handlers()
            
            # Handler pour les erreurs critiques
            self._setup_error_handler()
            
            # Handler pour les métriques
            self._setup_metrics_handler()
            
        except Exception as e:
            # En cas d'erreur, on configure au minimum un handler console
            fallback_handler = logging.StreamHandler(sys.stderr)
            fallback_handler.setLevel(logging.ERROR)
            fallback_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            self.logger.addHandler(fallback_handler)
            self.logger.error(f"Erreur lors de la configuration du logging: {e}")
    
    def _setup_file_handlers(self):
        """Configure les handlers de fichiers"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Log principal (JSON structuré)
            main_handler = logging.handlers.RotatingFileHandler(
                log_dir / "alimante.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            main_handler.setLevel(logging.DEBUG)
            main_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(main_handler)
            
            # Log des erreurs séparé
            error_handler = logging.handlers.RotatingFileHandler(
                log_dir / "errors.log",
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(error_handler)
            
        except Exception as e:
            # En cas d'erreur, on continue sans les handlers de fichiers
            self.logger.warning(f"Impossible de configurer les handlers de fichiers: {e}")
    
    def _setup_error_handler(self):
        """Handler spécial pour les erreurs critiques"""
        try:
            critical_handler = logging.handlers.RotatingFileHandler(
                Path("logs") / "critical.log",
                maxBytes=2*1024*1024,  # 2MB
                backupCount=2
            )
            critical_handler.setLevel(logging.CRITICAL)
            critical_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(critical_handler)
            
        except Exception as e:
            # En cas d'erreur, on continue sans le handler critique
            self.logger.warning(f"Impossible de configurer le handler critique: {e}")
    
    def _setup_metrics_handler(self):
        """Handler pour les métriques système"""
        try:
            metrics_handler = logging.handlers.RotatingFileHandler(
                Path("logs") / "metrics.log",
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3
            )
            metrics_handler.setLevel(logging.INFO)
            metrics_handler.setFormatter(StructuredFormatter())
            
            # Créer un logger séparé pour les métriques
            metrics_logger = logging.getLogger(f"{self.name}.metrics")
            metrics_logger.addHandler(metrics_handler)
            metrics_logger.setLevel(logging.INFO)
            metrics_logger.propagate = False  # Éviter la duplication
            
        except Exception as e:
            # En cas d'erreur, on continue sans le handler de métriques
            self.logger.warning(f"Impossible de configurer le handler de métriques: {e}")
    
    def log_with_context(
        self, 
        level: int, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Log avec contexte structuré"""
        extra = {}
        if context:
            extra['context'] = context
        if error_code:
            extra['error_code'] = error_code
        if user_id:
            extra['user_id'] = user_id
            
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug avec contexte"""
        self.log_with_context(logging.DEBUG, message, context)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info avec contexte"""
        self.log_with_context(logging.INFO, message, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning avec contexte"""
        self.log_with_context(logging.WARNING, message, context)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, error_code: Optional[str] = None):
        """Log error avec contexte et code d'erreur"""
        self.log_with_context(logging.ERROR, message, context, error_code)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, error_code: Optional[str] = None):
        """Log critical avec contexte et code d'erreur"""
        self.log_with_context(logging.CRITICAL, message, context, error_code)
    
    def exception(self, message: str, context: Optional[Dict[str, Any]] = None, error_code: Optional[str] = None):
        """Log exception avec traceback"""
        extra = {}
        if context:
            extra['context'] = context
        if error_code:
            extra['error_code'] = error_code
            
        self.logger.exception(message, extra=extra)
    
    def metric(self, metric_name: str, value: Any, tags: Optional[Dict[str, Any]] = None):
        """Log une métrique système"""
        metrics_logger = logging.getLogger(f"{self.name}.metrics")
        metric_data = {
            "metric": metric_name,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        if tags:
            metric_data["tags"] = tags
            
        metrics_logger.info(f"METRIC: {json.dumps(metric_data)}")


# Instance globale du logger
_logger_instance: Optional[AlimanteLogger] = None


def get_logger(name: str = "alimante") -> AlimanteLogger:
    """Retourne l'instance du logger (singleton)"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AlimanteLogger(name)
    return _logger_instance


def setup_logging(name: str = "alimante") -> AlimanteLogger:
    """Fonction de compatibilité pour l'ancien système - retourne le logger configuré"""
    return get_logger(name)


def test_logging_system() -> bool:
    """Teste le système de logging et retourne True si tout fonctionne"""
    try:
        logger = get_logger("test")
        
        # Tester les différents niveaux
        logger.debug("Test debug")
        logger.info("Test info")
        logger.warning("Test warning")
        logger.error("Test error")
        
        # Vérifier que les handlers sont configurés
        if not logger.logger.handlers:
            return False
            
        # Vérifier que le niveau est correct
        if logger.logger.level > logging.DEBUG:
            return False
            
        return True
        
    except Exception as e:
        # En cas d'erreur, on ne peut pas logger, donc on retourne False
        return False


def get_logging_status() -> Dict[str, Any]:
    """Retourne l'état actuel du système de logging"""
    try:
        logger = get_logger()
        status = {
            "name": logger.name,
            "level": logging.getLevelName(logger.logger.level),
            "handlers_count": len(logger.logger.handlers),
            "handlers_info": []
        }
        
        for handler in logger.logger.handlers:
            handler_info = {
                "type": handler.__class__.__name__,
                "level": logging.getLevelName(handler.level),
                "formatter": handler.formatter.__class__.__name__ if handler.formatter else "None"
            }
            status["handlers_info"].append(handler_info)
            
        return status
        
    except Exception as e:
        return {"error": str(e)}


def cleanup_test_logs():
    """Nettoie les logs de test pour éviter l'accumulation"""
    try:
        log_dir = Path("logs")
        if not log_dir.exists():
            return
            
        # Supprimer les fichiers de test temporaires
        test_patterns = ["*test*", "*temp*"]
        for pattern in test_patterns:
            for log_file in log_dir.glob(pattern):
                try:
                    log_file.unlink()
                except Exception:
                    pass
                    
    except Exception:
        # Ignorer les erreurs de nettoyage
        pass


# Fonctions utilitaires pour le logging
def log_system_start():
    """Log le démarrage du système"""
    logger = get_logger()
    logger.info("🚀 Démarrage du système Alimante", {
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    })


def log_system_stop():
    """Log l'arrêt du système"""
    logger = get_logger()
    logger.info("🛑 Arrêt du système Alimante")


def log_sensor_reading(sensor_type: str, value: float, unit: str):
    """Log une lecture de capteur"""
    logger = get_logger()
    logger.debug(f"📊 Lecture capteur {sensor_type}", {
        "sensor_type": sensor_type,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now().isoformat()
    })


def log_controller_action(controller: str, action: str, success: bool, context: Optional[Dict[str, Any]] = None):
    """Log une action de contrôleur"""
    logger = get_logger()
    level = logging.INFO if success else logging.ERROR
    emoji = "✅" if success else "❌"
    
    log_context = {
        "controller": controller,
        "action": action,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    if context:
        log_context.update(context)
    
    logger.log(level, f"{emoji} Action {controller}: {action}", log_context)


def log_api_request(method: str, path: str, status_code: int, duration_ms: float, user_id: Optional[str] = None):
    """Log une requête API"""
    logger = get_logger()
    level = logging.INFO if status_code < 400 else logging.WARNING
    
    logger.log(level, f"🌐 API {method} {path}", {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "user_id": user_id
    })


def log_error_with_context(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log une erreur avec contexte"""
    logger = get_logger()
    logger.exception(f"💥 Erreur: {str(error)}", context)