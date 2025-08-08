"""
Service de contrôle pour Alimante
Gestion des actions de contrôle sur les différents systèmes
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode
from ..api.models import ControlAction


class ControlResult(str, Enum):
    """Résultats possibles d'une action de contrôle"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ControlAction:
    """Action de contrôle"""
    name: str
    controller: str
    parameters: Optional[Dict[str, Any]] = None
    timeout: float = 30.0  # secondes
    retry_count: int = 3


class ControlService:
    """Service de contrôle des systèmes"""
    
    def __init__(self):
        self.logger = get_logger("control_service")
        self.controllers: Dict[str, Any] = {}
        self.action_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
        # Configuration des actions disponibles
        self.available_actions = {
            "temperature": {
                "controller": "temperature",
                "methods": ["control_temperature", "activate_heating", "deactivate_heating"],
                "timeout": 30.0
            },
            "humidity": {
                "controller": "humidity", 
                "methods": ["control_humidity", "activate_sprayer", "deactivate_sprayer"],
                "timeout": 30.0
            },
            "light": {
                "controller": "light",
                "methods": ["control_lighting", "turn_on_light", "turn_off_light"],
                "timeout": 15.0
            },
            "feeding": {
                "controller": "feeding",
                "methods": ["control_feeding", "trigger_feeding"],
                "timeout": 60.0
            }
        }
    
    def register_controller(self, name: str, controller: Any) -> None:
        """Enregistre un contrôleur"""
        self.controllers[name] = controller
        self.logger.info(f"Contrôleur enregistré dans le service de contrôle: {name}")
    
    def execute_control_action(self, action_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Exécute une action de contrôle"""
        try:
            if action_name not in self.available_actions:
                raise create_exception(
                    ErrorCode.API_INVALID_REQUEST,
                    f"Action de contrôle non reconnue: {action_name}",
                    {"available_actions": list(self.available_actions.keys())}
                )
            
            action_config = self.available_actions[action_name]
            controller_name = action_config["controller"]
            
            if controller_name not in self.controllers:
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    f"Contrôleur non disponible: {controller_name}",
                    {"required_controller": controller_name}
                )
            
            controller = self.controllers[controller_name]
            method_name = action_config["methods"][0]  # Méthode principale
            
            if not hasattr(controller, method_name):
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    f"Méthode non disponible: {method_name}",
                    {"controller": controller_name, "method": method_name}
                )
            
            # Exécuter l'action
            start_time = datetime.now()
            method = getattr(controller, method_name)
            
            if parameters:
                result = method(**parameters)
            else:
                result = method()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Enregistrer l'action
            action_record = {
                "action": action_name,
                "controller": controller_name,
                "parameters": parameters,
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now(),
                "status": ControlResult.SUCCESS if result else ControlResult.ERROR
            }
            
            self._add_to_history(action_record)
            
            self.logger.info(f"Action de contrôle exécutée: {action_name}", {
                "controller": controller_name,
                "result": result,
                "execution_time": execution_time
            })
            
            return {
                "action": action_name,
                "status": "success" if result else "error",
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.exception(f"Erreur lors de l'exécution de l'action {action_name}")
            
            # Enregistrer l'erreur
            action_config = self.available_actions.get(action_name)
            error_record = {
                "action": action_name,
                "controller": action_config.get("controller") if action_name in self.available_actions else None,
                "parameters": parameters,
                "error": str(e),
                "timestamp": datetime.now(),
                "status": ControlResult.ERROR
            }
            
            self._add_to_history(error_record)
            
            if isinstance(e, create_exception):
                raise
            else:
                raise create_exception(
                    ErrorCode.SERVICE_UNAVAILABLE,
                    f"Erreur lors de l'exécution de l'action {action_name}",
                    {"original_error": str(e)}
                )
    
    def execute_multiple_actions(self, actions: List[str], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Exécute plusieurs actions de contrôle"""
        try:
            results = {}
            errors = []
            total_execution_time = 0
            
            for action in actions:
                try:
                    action_params = parameters.get(action) if parameters else None
                    result = self.execute_control_action(action, action_params)
                    results[action] = result
                    total_execution_time += result.get("execution_time", 0)
                except Exception as e:
                    errors.append(f"Erreur action {action}: {str(e)}")
                    results[action] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return {
                "actions": actions,
                "results": results,
                "errors": errors if errors else None,
                "total_execution_time": total_execution_time,
                "status": "success" if not errors else "partial_success" if len(errors) < len(actions) else "error",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.exception("Erreur lors de l'exécution de multiples actions")
            raise create_exception(
                ErrorCode.SERVICE_UNAVAILABLE,
                "Erreur lors de l'exécution de multiples actions",
                {"original_error": str(e)}
            )
    
    def get_controller_status(self, controller_name: str) -> Dict[str, Any]:
        """Récupère le statut d'un contrôleur"""
        try:
            if controller_name not in self.controllers:
                raise create_exception(
                    ErrorCode.CONTROLLER_INIT_FAILED,
                    f"Contrôleur non trouvé: {controller_name}",
                    {"available_controllers": list(self.controllers.keys())}
                )
            
            controller = self.controllers[controller_name]
            
            if hasattr(controller, 'get_status'):
                status = controller.get_status()
                return {
                    "controller": controller_name,
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "controller": controller_name,
                    "status": "unknown",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.exception(f"Erreur récupération statut contrôleur {controller_name}")
            raise create_exception(
                ErrorCode.SERVICE_UNAVAILABLE,
                f"Impossible de récupérer le statut du contrôleur {controller_name}",
                {"original_error": str(e)}
            )
    
    def get_all_controllers_status(self) -> Dict[str, Any]:
        """Récupère le statut de tous les contrôleurs"""
        try:
            status = {}
            
            for controller_name, controller in self.controllers.items():
                try:
                    status[controller_name] = self.get_controller_status(controller_name)
                except Exception as e:
                    self.logger.error(f"Erreur statut contrôleur {controller_name}: {e}")
                    status[controller_name] = {
                        "controller": controller_name,
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            
            return status
            
        except Exception as e:
            self.logger.exception("Erreur récupération statut de tous les contrôleurs")
            raise create_exception(
                ErrorCode.SERVICE_UNAVAILABLE,
                "Impossible de récupérer le statut des contrôleurs",
                {"original_error": str(e)}
            )
    
    def get_action_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Récupère l'historique des actions"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [action for action in self.action_history if action.get('timestamp', datetime.now()) > cutoff_time]
    
    def get_available_actions(self) -> Dict[str, Any]:
        """Récupère les actions disponibles"""
        return {
            "actions": self.available_actions,
            "controllers": list(self.controllers.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    def _add_to_history(self, action_record: Dict[str, Any]) -> None:
        """Ajoute une action à l'historique"""
        self.action_history.append(action_record)
        
        # Limiter la taille de l'historique
        if len(self.action_history) > self.max_history_size:
            self.action_history = self.action_history[-self.max_history_size:]
    
    def cleanup(self) -> None:
        """Nettoie les ressources du service"""
        self.logger.info("Nettoyage du service de contrôle")
        
        # Nettoyer les contrôleurs
        for name, controller in self.controllers.items():
            try:
                if hasattr(controller, 'cleanup'):
                    controller.cleanup()
                    self.logger.info(f"Contrôleur nettoyé: {name}")
            except Exception as e:
                self.logger.error(f"Erreur nettoyage contrôleur {name}: {e}")
        
        # Vider l'historique
        self.action_history.clear()
        
        self.logger.info("Service de contrôle nettoyé")


# Instance globale du service de contrôle
control_service = ControlService() 