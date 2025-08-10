from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
import os
import logging

@dataclass
class SystemConfig:
    """Configuration système pour Alimante"""
    # Configuration système
    system_info: Dict[str, Any]
    hardware: Dict[str, Any]
    communication: Dict[str, Any]
    location: Dict[str, Any]
    species_profiles: Dict[str, Any]
    system_control: Dict[str, Any]
    safety: Dict[str, Any]
    api: Dict[str, Any]
    logging: Dict[str, Any]
    performance: Dict[str, Any]
    
    # Configuration spécifique à l'espèce (optionnelle)
    species_name: Optional[str] = None
    common_name: Optional[str] = None
    classification: Optional[Dict[str, Any]] = None
    temperature: Optional[Dict[str, float]] = None
    humidity: Optional[Dict[str, float]] = None
    feeding: Optional[Dict[str, Any]] = None
    lighting: Optional[Dict[str, Any]] = None
    lifecycle: Optional[Dict[str, Any]] = None
    enclosure: Optional[Dict[str, Any]] = None

    @classmethod
    def from_json(cls, common_config_path: str, specific_config_path: str) -> 'SystemConfig':
        """Charge la configuration depuis deux fichiers JSON"""
        if not os.path.exists(common_config_path):
            raise FileNotFoundError(f"Common configuration file not found: {common_config_path}")
        if not os.path.exists(specific_config_path):
            raise FileNotFoundError(f"Specific configuration file not found: {specific_config_path}")
        
        try:
            # Charger la configuration commune
            with open(common_config_path, 'r', encoding='utf-8') as f:
                common_data = json.load(f)
            
            # Charger la configuration spécifique à l'espèce
            with open(specific_config_path, 'r', encoding='utf-8') as f:
                specific_data = json.load(f)
            
            # Combiner les configurations
            # La configuration spécifique a la priorité sur la commune
            combined_data = {**common_data, **specific_data}
            
            # Extraire les sections principales
            config = cls(
                system_info=combined_data.get('system_info', {}),
                hardware=combined_data.get('hardware', {}),
                communication=combined_data.get('communication', {}),
                location=combined_data.get('location', {}),
                species_profiles=combined_data.get('species_profiles', {}),
                system_control=combined_data.get('system_control', {}),
                safety=combined_data.get('safety', {}),
                api=combined_data.get('api', {}),
                logging=combined_data.get('logging', {}),
                performance=combined_data.get('performance', {}),
                
                # Configuration spécifique à l'espèce
                species_name=specific_data.get('species_name'),
                common_name=specific_data.get('common_name'),
                classification=specific_data.get('classification'),
                temperature=specific_data.get('temperature'),
                humidity=specific_data.get('humidity'),
                feeding=specific_data.get('feeding'),
                lighting=specific_data.get('lighting'),
                lifecycle=specific_data.get('lifecycle'),
                enclosure=specific_data.get('enclosure')
            )
            
            logging.info(f"Configuration chargée: {specific_data.get('species_name', 'Unknown')}")
            return config
            
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            raise
    
    def get_temperature_config(self) -> Dict[str, float]:
        """Retourne la configuration de température"""
        return self.temperature or {}
    
    def get_humidity_config(self) -> Dict[str, float]:
        """Retourne la configuration d'humidité"""
        return self.humidity or {}
    
    def get_feeding_config(self) -> Dict[str, Any]:
        """Retourne la configuration d'alimentation"""
        return self.feeding or {}
    
    def get_lighting_config(self) -> Dict[str, Any]:
        """Retourne la configuration d'éclairage"""
        return self.lighting or {}
    
    def get_location_config(self) -> Dict[str, float]:
        """Retourne la configuration de localisation"""
        return self.location or {}
    
    def get_system_control_config(self) -> Dict[str, Any]:
        """Retourne la configuration de contrôle système"""
        return self.system_control or {}
    
    def get_safety_config(self) -> Dict[str, Any]:
        """Retourne la configuration de sécurité"""
        return self.safety or {}