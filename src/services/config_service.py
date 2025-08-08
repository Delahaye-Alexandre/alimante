"""
Service de configuration pour Alimante
Gestion centralisée de la configuration système
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..utils.logging_config import get_logger
from ..utils.exceptions import create_exception, ErrorCode
from ..utils.config_manager import SystemConfig


class ConfigService:
    """Service de gestion de la configuration"""
    
    def __init__(self):
        self.logger = get_logger("config_service")
        self.config_dir = Path("config")
        self.config_cache: Dict[str, Any] = {}
        self.config_history: List[Dict[str, Any]] = []
        self.max_history_size = 50
        
        # Fichiers de configuration par défaut
        self.default_configs = {
            "system": "config/config.json",
            "species": "config/orthopteres/mantidae/mantis_religiosa.json",
            "gpio": "config/gpio_config.json"
        }
        
        # Validation des configurations
        self.config_validators = {
            "temperature": self._validate_temperature_config,
            "humidity": self._validate_humidity_config,
            "feeding": self._validate_feeding_config,
            "lighting": self._validate_lighting_config
        }
    
    def load_config(self, config_type: str = "system") -> Dict[str, Any]:
        """Charge une configuration"""
        try:
            if config_type not in self.default_configs:
                raise create_exception(
                    ErrorCode.CONFIGURATION_INVALID,
                    f"Type de configuration non reconnu: {config_type}",
                    {"available_types": list(self.default_configs.keys())}
                )
            
            config_path = self.default_configs[config_type]
            
            if not os.path.exists(config_path):
                raise create_exception(
                    ErrorCode.CONFIGURATION_INVALID,
                    f"Fichier de configuration non trouvé: {config_path}",
                    {"config_type": config_type, "path": config_path}
                )
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Valider la configuration
            self._validate_config(config, config_type)
            
            # Mettre en cache
            self.config_cache[config_type] = {
                "data": config,
                "timestamp": datetime.now(),
                "path": config_path
            }
            
            self.logger.info(f"Configuration chargée: {config_type}")
            return config
            
        except Exception as e:
            self.logger.exception(f"Erreur chargement configuration {config_type}")
            if isinstance(e, create_exception):
                raise
            else:
                raise create_exception(
                    ErrorCode.CONFIGURATION_INVALID,
                    f"Erreur lors du chargement de la configuration {config_type}",
                    {"original_error": str(e)}
                )
    
    def load_system_config(self) -> SystemConfig:
        """Charge la configuration système complète"""
        try:
            # Charger les configurations de base
            system_config = self.load_config("system")
            species_config = self.load_config("species")
            
            # Créer la configuration système
            config = SystemConfig.from_json(
                self.default_configs["system"],
                self.default_configs["species"]
            )
            
            self.logger.info("Configuration système chargée avec succès")
            return config
            
        except Exception as e:
            self.logger.exception("Erreur chargement configuration système")
            raise create_exception(
                ErrorCode.CONFIGURATION_INVALID,
                "Impossible de charger la configuration système",
                {"original_error": str(e)}
            )
    
    def save_config(self, config_type: str, config_data: Dict[str, Any]) -> bool:
        """Sauvegarde une configuration"""
        try:
            if config_type not in self.default_configs:
                raise create_exception(
                    ErrorCode.CONFIGURATION_INVALID,
                    f"Type de configuration non reconnu: {config_type}",
                    {"available_types": list(self.default_configs.keys())}
                )
            
            config_path = self.default_configs[config_type]
            
            # Valider la configuration avant sauvegarde
            self._validate_config(config_data, config_type)
            
            # Créer une sauvegarde
            backup_path = f"{config_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(config_path):
                import shutil
                shutil.copy2(config_path, backup_path)
                self.logger.info(f"Sauvegarde créée: {backup_path}")
            
            # Sauvegarder la nouvelle configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Mettre à jour le cache
            self.config_cache[config_type] = {
                "data": config_data,
                "timestamp": datetime.now(),
                "path": config_path
            }
            
            # Enregistrer dans l'historique
            self._add_to_history({
                "action": "save_config",
                "config_type": config_type,
                "timestamp": datetime.now(),
                "backup_path": backup_path if os.path.exists(config_path) else None
            })
            
            self.logger.info(f"Configuration sauvegardée: {config_type}")
            return True
            
        except Exception as e:
            self.logger.exception(f"Erreur sauvegarde configuration {config_type}")
            if isinstance(e, create_exception):
                raise
            else:
                raise create_exception(
                    ErrorCode.CONFIGURATION_INVALID,
                    f"Erreur lors de la sauvegarde de la configuration {config_type}",
                    {"original_error": str(e)}
                )
    
    def update_config_section(self, config_type: str, section: str, data: Dict[str, Any]) -> bool:
        """Met à jour une section de configuration"""
        try:
            # Charger la configuration actuelle
            current_config = self.load_config(config_type)
            
            # Mettre à jour la section
            if section not in current_config:
                current_config[section] = {}
            
            current_config[section].update(data)
            
            # Valider la configuration mise à jour
            self._validate_config(current_config, config_type)
            
            # Sauvegarder
            return self.save_config(config_type, current_config)
            
        except Exception as e:
            self.logger.exception(f"Erreur mise à jour section {section} de {config_type}")
            raise create_exception(
                ErrorCode.CONFIGURATION_INVALID,
                f"Erreur lors de la mise à jour de la section {section}",
                {"original_error": str(e)}
            )
    
    def get_config_info(self, config_type: str) -> Dict[str, Any]:
        """Récupère les informations sur une configuration"""
        try:
            if config_type not in self.default_configs:
                raise create_exception(
                    ErrorCode.CONFIGURATION_INVALID,
                    f"Type de configuration non reconnu: {config_type}",
                    {"available_types": list(self.default_configs.keys())}
                )
            
            config_path = self.default_configs[config_type]
            
            info = {
                "type": config_type,
                "path": config_path,
                "exists": os.path.exists(config_path),
                "cached": config_type in self.config_cache
            }
            
            if info["exists"]:
                stat = os.stat(config_path)
                info.update({
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
            
            if info["cached"]:
                cache_info = self.config_cache[config_type]
                info["cached_timestamp"] = cache_info["timestamp"].isoformat()
            
            return info
            
        except Exception as e:
            self.logger.exception(f"Erreur récupération infos configuration {config_type}")
            raise create_exception(
                ErrorCode.CONFIGURATION_INVALID,
                f"Impossible de récupérer les informations de la configuration {config_type}",
                {"original_error": str(e)}
            )
    
    def get_all_configs_info(self) -> Dict[str, Any]:
        """Récupère les informations sur toutes les configurations"""
        try:
            configs_info = {}
            
            for config_type in self.default_configs.keys():
                try:
                    configs_info[config_type] = self.get_config_info(config_type)
                except Exception as e:
                    self.logger.error(f"Erreur infos configuration {config_type}: {e}")
                    configs_info[config_type] = {
                        "type": config_type,
                        "error": str(e)
                    }
            
            return {
                "configs": configs_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.exception("Erreur récupération infos de toutes les configurations")
            raise create_exception(
                ErrorCode.CONFIGURATION_INVALID,
                "Impossible de récupérer les informations des configurations",
                {"original_error": str(e)}
            )
    
    def validate_config(self, config_data: Dict[str, Any], config_type: str) -> Dict[str, Any]:
        """Valide une configuration"""
        try:
            errors = []
            warnings = []
            
            # Validation de base
            if not isinstance(config_data, dict):
                errors.append("La configuration doit être un objet JSON")
                return {"valid": False, "errors": errors, "warnings": warnings}
            
            # Validation spécifique au type
            if config_type in self.config_validators:
                validator_result = self.config_validators[config_type](config_data)
                errors.extend(validator_result.get("errors", []))
                warnings.extend(validator_result.get("warnings", []))
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.exception(f"Erreur validation configuration {config_type}")
            return {
                "valid": False,
                "errors": [f"Erreur de validation: {str(e)}"],
                "warnings": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_config(self, config_data: Dict[str, Any], config_type: str) -> None:
        """Valide une configuration et lève une exception si invalide"""
        validation_result = self.validate_config(config_data, config_type)
        
        if not validation_result["valid"]:
            raise create_exception(
                ErrorCode.CONFIGURATION_INVALID,
                f"Configuration {config_type} invalide",
                {"errors": validation_result["errors"]}
            )
    
    def _validate_temperature_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Valide la configuration de température"""
        errors = []
        warnings = []
        
        if "temperature" in config:
            temp_config = config["temperature"]
            
            if "optimal" not in temp_config:
                errors.append("Température optimale manquante")
            elif not isinstance(temp_config["optimal"], (int, float)):
                errors.append("Température optimale doit être un nombre")
            elif temp_config["optimal"] < 10 or temp_config["optimal"] > 40:
                errors.append("Température optimale doit être entre 10 et 40°C")
            
            if "tolerance" not in temp_config:
                errors.append("Tolérance de température manquante")
            elif not isinstance(temp_config["tolerance"], (int, float)):
                errors.append("Tolérance de température doit être un nombre")
            elif temp_config["tolerance"] < 0.5 or temp_config["tolerance"] > 10:
                errors.append("Tolérance de température doit être entre 0.5 et 10°C")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_humidity_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Valide la configuration d'humidité"""
        errors = []
        warnings = []
        
        if "humidity" in config:
            humidity_config = config["humidity"]
            
            if "optimal" not in humidity_config:
                errors.append("Humidité optimale manquante")
            elif not isinstance(humidity_config["optimal"], (int, float)):
                errors.append("Humidité optimale doit être un nombre")
            elif humidity_config["optimal"] < 20 or humidity_config["optimal"] > 90:
                errors.append("Humidité optimale doit être entre 20 et 90%")
            
            if "tolerance" not in humidity_config:
                errors.append("Tolérance d'humidité manquante")
            elif not isinstance(humidity_config["tolerance"], (int, float)):
                errors.append("Tolérance d'humidité doit être un nombre")
            elif humidity_config["tolerance"] < 1 or humidity_config["tolerance"] > 20:
                errors.append("Tolérance d'humidité doit être entre 1 et 20%")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_feeding_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Valide la configuration d'alimentation"""
        errors = []
        warnings = []
        
        if "feeding" in config:
            feeding_config = config["feeding"]
            
            if "interval_hours" not in feeding_config:
                errors.append("Intervalle d'alimentation manquant")
            elif not isinstance(feeding_config["interval_hours"], (int, float)):
                errors.append("Intervalle d'alimentation doit être un nombre")
            elif feeding_config["interval_hours"] < 1 or feeding_config["interval_hours"] > 168:
                errors.append("Intervalle d'alimentation doit être entre 1 et 168 heures")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_lighting_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Valide la configuration d'éclairage"""
        errors = []
        warnings = []
        
        if "lighting" in config:
            lighting_config = config["lighting"]
            
            if "auto_mode" not in lighting_config:
                warnings.append("Mode automatique d'éclairage non défini")
        
        return {"errors": errors, "warnings": warnings}
    
    def _add_to_history(self, record: Dict[str, Any]) -> None:
        """Ajoute un enregistrement à l'historique"""
        self.config_history.append(record)
        
        # Limiter la taille de l'historique
        if len(self.config_history) > self.max_history_size:
            self.config_history = self.config_history[-self.max_history_size:]
    
    def get_config_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Récupère l'historique des modifications de configuration"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [record for record in self.config_history if record.get('timestamp', datetime.now()) > cutoff_time]
    
    def cleanup(self) -> None:
        """Nettoie les ressources du service"""
        self.logger.info("Nettoyage du service de configuration")
        
        # Vider le cache
        self.config_cache.clear()
        
        # Vider l'historique
        self.config_history.clear()
        
        self.logger.info("Service de configuration nettoyé")


# Instance globale du service de configuration
config_service = ConfigService() 