from dataclasses import dataclass
from typing import Dict, Any
import json
import os
import logging

@dataclass
class SystemConfig:
    """Configuration système pour Mantcare"""
    serial_port: str
    baud_rate: int
    temperature: Dict[str, float]
    humidity: Dict[str, float]
    location: Dict[str, float]
    feeding: Dict[str, int]

    @classmethod
    def from_json(cls, config_path: str) -> 'SystemConfig':
        """Charge la configuration depuis un fichier JSON"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file: {e}")
            raise