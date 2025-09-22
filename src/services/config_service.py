"""
Service de configuration centralisé Alimante
Gère le chargement et la validation de toutes les configurations
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime

class ConfigService:
    """
    Service de configuration centralisé
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialise le service de configuration
        
        Args:
            config_dir: Répertoire des fichiers de configuration
        """
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
        
        # Cache des configurations
        self._config_cache = {}
        self._hardcoded_values = None
        
        # Fichiers de configuration
        self.config_files = {
            'main': 'config.json',
            'gpio': 'gpio_config.json',
            'network': 'network.json',
            'safety': 'safety_limits.json',
            'hardcoded': 'hardcoded_values.json',
            'terrariums': 'terrariums/',
            'species': 'species/',
            'policies': 'policies/'
        }
        
    def load_all_configs(self) -> Dict[str, Any]:
        """
        Charge toutes les configurations
        
        Returns:
            Dictionnaire contenant toutes les configurations
        """
        try:
            configs = {}
            
            # Charger la configuration principale
            configs['main'] = self.load_config('main')
            
            # Charger les configurations spécialisées
            configs['gpio'] = self.load_config('gpio')
            configs['network'] = self.load_config('network')
            configs['safety'] = self.load_config('safety')
            configs['hardcoded'] = self.load_config('hardcoded')
            
            # Charger les configurations des terrariums
            configs['terrariums'] = self.load_terrarium_configs()
            
            # Charger les configurations des espèces
            configs['species'] = self.load_species_configs()
            
            # Charger les politiques
            configs['policies'] = self.load_policy_configs()
            
            self.logger.info("Toutes les configurations chargées avec succès")
            return configs
            
        except Exception as e:
            self.logger.error(f"Erreur chargement configurations: {e}")
            return {}
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        Charge une configuration spécifique
        
        Args:
            config_name: Nom de la configuration
            
        Returns:
            Dictionnaire de configuration
        """
        try:
            if config_name in self._config_cache:
                return self._config_cache[config_name]
            
            config_file = self.config_files.get(config_name)
            if not config_file:
                self.logger.error(f"Configuration inconnue: {config_name}")
                return {}
            
            config_path = self.config_dir / config_file
            
            if not config_path.exists():
                self.logger.warning(f"Fichier de configuration non trouvé: {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self._config_cache[config_name] = config
            self.logger.debug(f"Configuration {config_name} chargée")
            return config
            
        except Exception as e:
            self.logger.error(f"Erreur chargement configuration {config_name}: {e}")
            return {}
    
    def load_terrarium_configs(self) -> Dict[str, Any]:
        """
        Charge toutes les configurations de terrariums
        
        Returns:
            Dictionnaire des configurations de terrariums
        """
        try:
            terrarium_dir = self.config_dir / 'terrariums'
            configs = {}
            
            if not terrarium_dir.exists():
                self.logger.warning("Répertoire terrariums non trouvé")
                return configs
            
            for config_file in terrarium_dir.glob('*.json'):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        terrarium_config = json.load(f)
                    
                    terrarium_id = terrarium_config.get('terrarium_id', config_file.stem)
                    configs[terrarium_id] = terrarium_config
                    
                except Exception as e:
                    self.logger.error(f"Erreur chargement terrarium {config_file}: {e}")
            
            self.logger.info(f"{len(configs)} configurations de terrariums chargées")
            return configs
            
        except Exception as e:
            self.logger.error(f"Erreur chargement configurations terrariums: {e}")
            return {}
    
    def load_species_configs(self) -> Dict[str, Any]:
        """
        Charge toutes les configurations d'espèces
        
        Returns:
            Dictionnaire des configurations d'espèces
        """
        try:
            species_dir = self.config_dir / 'species'
            configs = {}
            
            if not species_dir.exists():
                self.logger.warning("Répertoire species non trouvé")
                return configs
            
            # Charger les insectes
            insects_dir = species_dir / 'insects'
            if insects_dir.exists():
                for config_file in insects_dir.glob('*.json'):
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            species_config = json.load(f)
                        
                        species_id = species_config.get('species_id', config_file.stem)
                        configs[species_id] = species_config
                        
                    except Exception as e:
                        self.logger.error(f"Erreur chargement espèce {config_file}: {e}")
            
            # Charger les reptiles
            reptiles_dir = species_dir / 'reptiles'
            if reptiles_dir.exists():
                for config_file in reptiles_dir.glob('*.json'):
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            species_config = json.load(f)
                        
                        species_id = species_config.get('species_id', config_file.stem)
                        configs[species_id] = species_config
                        
                    except Exception as e:
                        self.logger.error(f"Erreur chargement espèce {config_file}: {e}")
            
            self.logger.info(f"{len(configs)} configurations d'espèces chargées")
            return configs
            
        except Exception as e:
            self.logger.error(f"Erreur chargement configurations espèces: {e}")
            return {}
    
    def load_policy_configs(self) -> Dict[str, Any]:
        """
        Charge toutes les configurations de politiques
        
        Returns:
            Dictionnaire des configurations de politiques
        """
        try:
            policy_dir = self.config_dir / 'policies'
            configs = {}
            
            if not policy_dir.exists():
                self.logger.warning("Répertoire policies non trouvé")
                return configs
            
            for config_file in policy_dir.glob('*.json'):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        policy_config = json.load(f)
                    
                    policy_name = config_file.stem
                    configs[policy_name] = policy_config
                    
                except Exception as e:
                    self.logger.error(f"Erreur chargement politique {config_file}: {e}")
            
            self.logger.info(f"{len(configs)} configurations de politiques chargées")
            return configs
            
        except Exception as e:
            self.logger.error(f"Erreur chargement configurations politiques: {e}")
            return {}
    
    def get_hardcoded_value(self, path: str, default: Any = None) -> Any:
        """
        Récupère une valeur hardcodée par chemin
        
        Args:
            path: Chemin vers la valeur (ex: "services.camera.quality")
            default: Valeur par défaut
            
        Returns:
            Valeur de configuration ou valeur par défaut
        """
        try:
            if not self._hardcoded_values:
                self._hardcoded_values = self.load_config('hardcoded')
            
            if not self._hardcoded_values:
                return default
            
            # Naviguer dans le chemin
            keys = path.split('.')
            value = self._hardcoded_values
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"Erreur récupération valeur hardcodée {path}: {e}")
            return default
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Récupère la configuration d'un service
        
        Args:
            service_name: Nom du service
            
        Returns:
            Configuration du service
        """
        try:
            hardcoded_config = self.get_hardcoded_value(f"services.{service_name}", {})
            main_config = self.load_config('main')
            
            # Fusionner les configurations (hardcoded en priorité)
            service_config = {}
            
            # Ajouter la configuration principale
            if service_name in main_config:
                service_config.update(main_config[service_name])
            
            # Ajouter la configuration hardcodée
            service_config.update(hardcoded_config)
            
            return service_config
            
        except Exception as e:
            self.logger.error(f"Erreur récupération configuration service {service_name}: {e}")
            return {}
    
    def get_controller_config(self, controller_name: str) -> Dict[str, Any]:
        """
        Récupère la configuration d'un contrôleur
        
        Args:
            controller_name: Nom du contrôleur
            
        Returns:
            Configuration du contrôleur
        """
        try:
            return self.get_hardcoded_value(f"controllers.{controller_name}", {})
            
        except Exception as e:
            self.logger.error(f"Erreur récupération configuration contrôleur {controller_name}: {e}")
            return {}
    
    def get_driver_config(self, driver_name: str) -> Dict[str, Any]:
        """
        Récupère la configuration d'un driver
        
        Args:
            driver_name: Nom du driver
            
        Returns:
            Configuration du driver
        """
        try:
            return self.get_hardcoded_value(f"drivers.{driver_name}", {})
            
        except Exception as e:
            self.logger.error(f"Erreur récupération configuration driver {driver_name}: {e}")
            return {}
    
    def get_timeout(self, timeout_name: str, default: float = 5.0) -> float:
        """
        Récupère un timeout par nom
        
        Args:
            timeout_name: Nom du timeout
            default: Valeur par défaut
            
        Returns:
            Valeur du timeout
        """
        try:
            return self.get_hardcoded_value(f"timeouts.{timeout_name}", default)
            
        except Exception as e:
            self.logger.error(f"Erreur récupération timeout {timeout_name}: {e}")
            return default
    
    def get_interval(self, interval_name: str, default: float = 1.0) -> float:
        """
        Récupère un intervalle par nom
        
        Args:
            interval_name: Nom de l'intervalle
            default: Valeur par défaut
            
        Returns:
            Valeur de l'intervalle
        """
        try:
            return self.get_hardcoded_value(f"intervals.{interval_name}", default)
            
        except Exception as e:
            self.logger.error(f"Erreur récupération intervalle {interval_name}: {e}")
            return default
    
    def get_path(self, path_name: str, default: str = "") -> str:
        """
        Récupère un chemin par nom
        
        Args:
            path_name: Nom du chemin
            default: Valeur par défaut
            
        Returns:
            Chemin
        """
        try:
            return self.get_hardcoded_value(f"paths.{path_name}", default)
            
        except Exception as e:
            self.logger.error(f"Erreur récupération chemin {path_name}: {e}")
            return default
    
    def get_hardware_config(self, hardware_name: str) -> Dict[str, Any]:
        """
        Récupère la configuration matérielle
        
        Args:
            hardware_name: Nom du composant matériel
            
        Returns:
            Configuration matérielle
        """
        try:
            return self.get_hardcoded_value(f"hardware.{hardware_name}", {})
            
        except Exception as e:
            self.logger.error(f"Erreur récupération configuration matérielle {hardware_name}: {e}")
            return {}
    
    def validate_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Valide une configuration selon un schéma
        
        Args:
            config: Configuration à valider
            schema: Schéma de validation
            
        Returns:
            True si la configuration est valide, False sinon
        """
        try:
            # Implémentation basique de validation
            # Pour une implémentation complète, utiliser jsonschema
            for key, value in schema.items():
                if key not in config:
                    self.logger.warning(f"Clé manquante dans la configuration: {key}")
                    return False
                
                if isinstance(value, dict) and isinstance(config[key], dict):
                    if not self.validate_config(config[key], value):
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur validation configuration: {e}")
            return False
    
    def save_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """
        Sauvegarde une configuration
        
        Args:
            config_name: Nom de la configuration
            config: Configuration à sauvegarder
            
        Returns:
            True si la sauvegarde réussit, False sinon
        """
        try:
            config_file = self.config_files.get(config_name)
            if not config_file:
                self.logger.error(f"Configuration inconnue: {config_name}")
                return False
            
            config_path = self.config_dir / config_file
            
            # Créer le répertoire si nécessaire
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Ajouter la date de modification
            config['last_updated'] = datetime.now().isoformat()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Mettre à jour le cache
            self._config_cache[config_name] = config
            
            self.logger.info(f"Configuration {config_name} sauvegardée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde configuration {config_name}: {e}")
            return False
    
    def reload_config(self, config_name: str) -> bool:
        """
        Recharge une configuration depuis le fichier
        
        Args:
            config_name: Nom de la configuration
            
        Returns:
            True si le rechargement réussit, False sinon
        """
        try:
            # Supprimer du cache
            if config_name in self._config_cache:
                del self._config_cache[config_name]
            
            # Recharger
            config = self.load_config(config_name)
            return bool(config)
            
        except Exception as e:
            self.logger.error(f"Erreur rechargement configuration {config_name}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service de configuration
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'service': 'config',
            'config_dir': str(self.config_dir),
            'cached_configs': list(self._config_cache.keys()),
            'available_configs': list(self.config_files.keys()),
            'hardcoded_loaded': self._hardcoded_values is not None
        }
