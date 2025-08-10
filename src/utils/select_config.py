"""
select_config.py
Module pour la sélection et le chargement de la configuration appropriée.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
from src.utils.config_manager import SystemConfig

def get_available_species() -> Dict[str, Dict[str, Any]]:
    """
    Récupère la liste des espèces disponibles dans le répertoire de configuration.
    
    :return: Dictionnaire des espèces disponibles avec leurs informations
    """
    species = {}
    config_dir = "config"
    
    try:
        # Parcourir les ordres
        for order in os.listdir(config_dir):
            order_path = os.path.join(config_dir, order)
            if os.path.isdir(order_path) and not order.startswith('.'):
                # Parcourir les familles
                for family in os.listdir(order_path):
                    family_path = os.path.join(order_path, family)
                    if os.path.isdir(family_path) and not family.startswith('.'):
                        # Parcourir les espèces
                        for species_file in os.listdir(family_path):
                            if species_file.endswith('.json'):
                                species_name = species_file.replace('.json', '')
                                species_path = os.path.join(family_path, species_file)
                                
                                try:
                                    with open(species_path, 'r', encoding='utf-8') as f:
                                        species_data = json.load(f)
                                    
                                    species[f"{order}/{family}/{species_name}"] = {
                                        'name': species_data.get('species_name', species_name),
                                        'common_name': species_data.get('common_name', ''),
                                        'order': order,
                                        'family': family,
                                        'path': species_path,
                                        'classification': species_data.get('classification', {})
                                    }
                                except Exception as e:
                                    logging.warning(f"Erreur lors du chargement de {species_path}: {e}")
                                    
    except Exception as e:
        logging.error(f"Erreur lors de la recherche des espèces: {e}")
    
    return species

def select_species_config(species_path: str) -> Tuple[str, str]:
    """
    Sélectionne la configuration pour une espèce spécifique.
    
    :param species_path: Chemin vers la configuration de l'espèce (ex: "orthopteres/mantidae/mantis_religiosa")
    :return: Tuple (chemin_config_commune, chemin_config_espece)
    """
    # Configuration commune
    common_config_path = "config/config.json"
    
    # Configuration spécifique à l'espèce
    specific_config_path = f"config/{species_path}.json"
    
    if not os.path.exists(common_config_path):
        raise FileNotFoundError(f"Configuration commune non trouvée: {common_config_path}")
    
    if not os.path.exists(specific_config_path):
        raise FileNotFoundError(f"Configuration de l'espèce non trouvée: {specific_config_path}")
    
    return common_config_path, specific_config_path

def load_species_config(species_name: str) -> 'SystemConfig':
    """
    Charge la configuration pour une espèce spécifique
    
    Args:
        species_name: Nom de l'espèce (ex: 'mantis_religiosa')
        
    Returns:
        SystemConfig: Configuration système complète
        
    Raises:
        FileNotFoundError: Si les fichiers de configuration n'existent pas
        ValueError: Si la configuration est invalide
    """
    try:
        # Chemins des fichiers de configuration
        common_config_path = "config/config.json"
        specific_config_path = f"config/orthopteres/mantidae/{species_name}.json"
        gpio_config_path = "config/gpio_config.json"
        
        # Vérifier que les fichiers existent
        if not os.path.exists(common_config_path):
            raise FileNotFoundError(f"Configuration commune introuvable: {common_config_path}")
        if not os.path.exists(specific_config_path):
            raise FileNotFoundError(f"Configuration espèce introuvable: {specific_config_path}")
        if not os.path.exists(gpio_config_path):
            raise FileNotFoundError(f"Configuration GPIO introuvable: {gpio_config_path}")
        
        # Charger la configuration
        from .config_manager import SystemConfig
        config = SystemConfig.from_json(
            common_config_path=common_config_path,
            specific_config_path=specific_config_path,
            gpio_config_path=gpio_config_path
        )
        
        # Valider la configuration
        validate_species_config(config)
        
        return config
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        raise

def get_default_species() -> str:
    """
    Récupère l'espèce par défaut depuis la configuration.
    
    :return: Chemin de l'espèce par défaut
    """
    try:
        with open("config/config.json", 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        default_profile = config_data.get('species_profiles', {}).get('default_profile', 'mantis_religiosa')
        profiles_dir = config_data.get('species_profiles', {}).get('profiles_directory', 'config/orthopteres/mantidae/')
        
        # Construire le chemin complet
        if profiles_dir.startswith('config/'):
            profiles_dir = profiles_dir[7:]  # Enlever "config/"
        
        return f"{profiles_dir.rstrip('/')}/{default_profile}"
        
    except Exception as e:
        logging.warning(f"Impossible de récupérer l'espèce par défaut: {e}")
        return "orthopteres/mantidae/mantis_religiosa"

def list_species_by_order() -> Dict[str, Dict[str, Any]]:
    """
    Liste les espèces organisées par ordre taxonomique.
    
    :return: Dictionnaire organisé par ordre
    """
    species = get_available_species()
    organized = {}
    
    for path, info in species.items():
        order = info['order']
        if order not in organized:
            organized[order] = {}
        
        family = info['family']
        if family not in organized[order]:
            organized[order][family] = {}
        
        species_name = path.split('/')[-1]
        organized[order][family][species_name] = info
    
    return organized

def validate_species_config(species_path: str) -> bool:
    """
    Valide la configuration d'une espèce.
    
    :param species_path: Chemin vers la configuration de l'espèce
    :return: True si la configuration est valide
    """
    try:
        config = load_species_config(species_path)
        
        # Vérifications de base
        required_fields = ['temperature', 'humidity', 'feeding', 'lighting']
        for field in required_fields:
            if not getattr(config, field):
                logging.warning(f"Champ manquant: {field}")
                return False
        
        # Vérification des valeurs de température
        temp_config = config.get_temperature_config()
        if not temp_config.get('optimal') or not temp_config.get('tolerance'):
            logging.warning("Configuration de température incomplète")
            return False
        
        # Vérification des valeurs d'humidité
        humidity_config = config.get_humidity_config()
        if not humidity_config.get('optimal') or not humidity_config.get('tolerance'):
            logging.warning("Configuration d'humidité incomplète")
            return False
        
        logging.info(f"Configuration de {species_path} validée avec succès")
        return True
        
    except Exception as e:
        logging.error(f"Erreur lors de la validation de {species_path}: {e}")
        return False