from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
import os
import logging

@dataclass
class SystemConfig:
    """Configuration système pour Alimante"""
    serial_port: str
    baud_rate: int
    temperature: Dict[str, float]
    humidity: Dict[str, float]
    location: Dict[str, float]
    feeding: Dict[str, int]
    species_name: Optional[str] = None
    common_name: Optional[str] = None
    classification: Optional[Dict[str, Any]] = None
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
            with open(common_config_path, 'r', encoding='utf-8') as f:
                common_data = json.load(f)
            with open(specific_config_path, 'r', encoding='utf-8') as f:
                specific_data = json.load(f)
            
            # Combine common and specific configurations
            combined_data = {**common_data, **specific_data}
            return cls(**combined_data)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file: {e}")
            raise