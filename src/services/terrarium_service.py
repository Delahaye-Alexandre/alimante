"""
Service de gestion des terrariums
Gère la configuration, la sélection et le contrôle des terrariums
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

class TerrariumService:
    """
    Service de gestion des terrariums
    """
    
    def __init__(self, event_bus=None):
        """
        Initialise le service de gestion des terrariums
        
        Args:
            event_bus: Bus d'événements pour la communication
        """
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.config_dir = Path(__file__).parent.parent.parent / 'config'
        self.terrariums_dir = self.config_dir / 'terrariums'
        self.species_dir = self.config_dir / 'species'
        
        # État des terrariums
        self.terrariums = {}
        self.current_terrarium = None
        self.terrarium_configs = {}
        
        # Statistiques
        self.stats = {
            'terrariums_loaded': 0,
            'config_updates': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Charger les terrariums disponibles
        self._load_terrariums()
        
    def _load_terrariums(self) -> None:
        """Charge tous les terrariums disponibles"""
        try:
            self.logger.info("Chargement des terrariums...")
            self.logger.info(f"Répertoire terrariums: {self.terrariums_dir}")
            self.logger.info(f"Répertoire existe: {self.terrariums_dir.exists()}")
            
            # Charger les configurations de terrariums
            if self.terrariums_dir.exists():
                config_files = list(self.terrariums_dir.glob('*.json'))
                self.logger.info(f"Fichiers de configuration trouvés: {len(config_files)}")
                for config_file in config_files:
                    self.logger.info(f"  - {config_file}")
                
                for config_file in config_files:
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            terrarium_config = json.load(f)
                            terrarium_id = terrarium_config.get('terrarium_id')
                            
                            if terrarium_id:
                                self.terrarium_configs[terrarium_id] = terrarium_config
                                self.terrariums[terrarium_id] = {
                                    'id': terrarium_id,
                                    'name': terrarium_config.get('name', terrarium_id),
                                    'description': terrarium_config.get('description', ''),
                                    'species': terrarium_config.get('species', {}),
                                    'status': 'active' if terrarium_config.get('active', False) else 'inactive',
                                    'controller_type': terrarium_config.get('controller_type', 'unknown'),
                                    'last_update': time.time(),
                                    'sensors': {},
                                    'actuators': {},
                                    'alerts': []
                                }
                                self.stats['terrariums_loaded'] += 1
                                self.logger.info(f"Terrarium chargé: {terrarium_id}")
                                
                    except Exception as e:
                        self.logger.error(f"Erreur chargement {config_file}: {e}")
                        self.stats['errors'] += 1
            else:
                self.logger.warning(f"Répertoire terrariums n'existe pas: {self.terrariums_dir}")
            
            # Créer un terrarium principal par défaut si aucun n'existe
            if not self.terrariums:
                self.logger.info("Aucun terrarium trouvé, création du terrarium principal par défaut...")
                self._create_default_terrarium()
            else:
                self.logger.info(f"Terrariums existants trouvés: {len(self.terrariums)}")
            
            # Définir le terrarium par défaut
            if self.terrariums and not self.current_terrarium:
                self.current_terrarium = list(self.terrariums.keys())[0]
                self.logger.info(f"Terrarium par défaut sélectionné: {self.current_terrarium}")
            
            self.logger.info(f"Terrariums chargés: {len(self.terrariums)}")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement terrariums: {e}")
            self.stats['errors'] += 1
    
    def _create_default_terrarium(self) -> None:
        """Crée un terrarium principal par défaut avec l'espèce mantis_religiosa"""
        try:
            self.logger.info("Création du terrarium principal par défaut...")
            
            # Charger la configuration de l'espèce mantis_religiosa
            species_config = self.get_species_config('mantis_religiosa')
            if not species_config:
                self.logger.warning("Configuration mantis_religiosa non trouvée, création d'une configuration par défaut")
                species_config = {
                    'species_id': 'mantis_religiosa',
                    'common_name': 'Mante religieuse',
                    'scientific_name': 'Mantis religiosa',
                    'type': 'insect'
                }
            
            # Créer le terrarium principal en utilisant la configuration de l'espèce
            terrarium_id = 'terrarium_principal'
            
            # Extraire les paramètres environnementaux de la configuration de l'espèce
            env_req = species_config.get('environmental_requirements', {})
            temp_config = env_req.get('temperature', {})
            humidity_config = env_req.get('humidity', {})
            lighting_config = env_req.get('lighting', {})
            ventilation_config = env_req.get('ventilation', {})
            feeding_req = species_config.get('feeding_requirements', {})
            
            terrarium_config = {
                'terrarium_id': terrarium_id,
                'name': 'Terrarium Principal',
                'description': f'Terrarium principal pour {species_config.get("common_name", "la mante religieuse")}',
                'active': True,
                'controller_type': 'raspberry_pi_zero_2w',
                'created_date': time.strftime('%Y-%m-%d'),
                'last_updated': time.strftime('%Y-%m-%d'),
                'species': {
                    'species_id': species_config.get('species_id', 'mantis_religiosa'),
                    'common_name': species_config.get('common_name', 'Mante religieuse'),
                    'scientific_name': species_config.get('scientific_name', 'Mantis religiosa'),
                    'type': species_config.get('category', 'insect')
                },
                'environmental_settings': {
                    'temperature': {
                        'day_target': temp_config.get('day', {}).get('optimal', 25.0),
                        'night_target': temp_config.get('night', {}).get('optimal', 20.0),
                        'min': temp_config.get('day', {}).get('min', 22.0),
                        'max': temp_config.get('day', {}).get('max', 28.0),
                        'hysteresis': 1.0
                    },
                    'humidity': {
                        'target': humidity_config.get('optimal', 65.0),
                        'min': humidity_config.get('min', 50.0),
                        'max': humidity_config.get('max', 80.0),
                        'hysteresis': 5.0
                    },
                    'lighting': {
                        'on_time': lighting_config.get('photoperiod', {}).get('day_start', '08:00'),
                        'off_time': lighting_config.get('photoperiod', {}).get('day_end', '20:00'),
                        'intensity': lighting_config.get('intensity', {}).get('optimal', 60),
                        'fade_enabled': lighting_config.get('fade', {}).get('enabled', True)
                    },
                    'ventilation': {
                        'base_speed': ventilation_config.get('air_circulation', {}).get('base_speed', 25),
                        'max_speed': ventilation_config.get('air_circulation', {}).get('max_speed', 60),
                        'enabled': ventilation_config.get('air_circulation', {}).get('enabled', True)
                    }
                },
                'feeding_schedule': {
                    'enabled': True,
                    'times': feeding_req.get('schedule', {}).get('times', ['10:00', '19:00']),
                    'frequency': feeding_req.get('schedule', {}).get('frequency', 'daily'),
                    'portion_size': feeding_req.get('schedule', {}).get('portion_size', 'small'),
                    'max_daily_feeds': 3
                }
            }
            
            # Sauvegarder la configuration
            self.terrarium_configs[terrarium_id] = terrarium_config
            config_file = self.terrariums_dir / f"{terrarium_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(terrarium_config, f, indent=2, ensure_ascii=False)
            
            # Ajouter au dictionnaire des terrariums
            self.terrariums[terrarium_id] = {
                'id': terrarium_id,
                'name': terrarium_config['name'],
                'description': terrarium_config['description'],
                'species': terrarium_config['species'],
                'status': 'active',
                'controller_type': terrarium_config['controller_type'],
                'last_update': time.time(),
                'sensors': {},
                'actuators': {},
                'alerts': []
            }
            
            self.stats['terrariums_loaded'] += 1
            self.logger.info(f"Terrarium principal créé: {terrarium_id}")
            
        except Exception as e:
            self.logger.error(f"Erreur création terrarium par défaut: {e}")
            self.stats['errors'] += 1
    
    def get_terrariums(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste de tous les terrariums
        
        Returns:
            Liste des terrariums avec leurs informations
        """
        return list(self.terrariums.values())
    
    def get_terrarium(self, terrarium_id: str) -> Optional[Dict[str, Any]]:
        """
        Retourne les informations d'un terrarium spécifique
        
        Args:
            terrarium_id: ID du terrarium
            
        Returns:
            Informations du terrarium ou None si non trouvé
        """
        return self.terrariums.get(terrarium_id)
    
    def get_current_terrarium(self) -> Optional[Dict[str, Any]]:
        """
        Retourne le terrarium actuellement sélectionné
        
        Returns:
            Informations du terrarium actuel
        """
        if self.current_terrarium:
            return self.terrariums.get(self.current_terrarium)
        return None
    
    def set_current_terrarium(self, terrarium_id: str) -> bool:
        """
        Définit le terrarium actuellement sélectionné
        
        Args:
            terrarium_id: ID du terrarium à sélectionner
            
        Returns:
            True si succès, False sinon
        """
        try:
            if terrarium_id in self.terrariums:
                self.current_terrarium = terrarium_id
                self.logger.info(f"Terrarium actuel: {terrarium_id}")
                
                # Émettre un événement de changement de terrarium
                if self.event_bus:
                    self.event_bus.emit('terrarium_changed', {
                        'terrarium_id': terrarium_id,
                        'terrarium': self.terrariums[terrarium_id],
                        'timestamp': time.time()
                    })
                
                return True
            else:
                self.logger.error(f"Terrarium {terrarium_id} non trouvé")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur changement terrarium: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_terrarium_config(self, terrarium_id: str) -> Optional[Dict[str, Any]]:
        """
        Retourne la configuration complète d'un terrarium
        
        Args:
            terrarium_id: ID du terrarium
            
        Returns:
            Configuration du terrarium ou None si non trouvé
        """
        return self.terrarium_configs.get(terrarium_id)
    
    def update_terrarium_config(self, terrarium_id: str, config: Dict[str, Any]) -> bool:
        """
        Met à jour la configuration d'un terrarium
        
        Args:
            terrarium_id: ID du terrarium
            config: Nouvelle configuration
            
        Returns:
            True si succès, False sinon
        """
        try:
            if terrarium_id not in self.terrarium_configs:
                self.logger.error(f"Terrarium {terrarium_id} non trouvé")
                return False
            
            # Mettre à jour la configuration
            self.terrarium_configs[terrarium_id].update(config)
            self.terrarium_configs[terrarium_id]['last_updated'] = time.strftime('%Y-%m-%d')
            
            # Sauvegarder dans le fichier
            config_file = self.terrariums_dir / f"{terrarium_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.terrarium_configs[terrarium_id], f, indent=2, ensure_ascii=False)
            
            # Mettre à jour les informations du terrarium
            if terrarium_id in self.terrariums:
                self.terrariums[terrarium_id].update({
                    'name': config.get('name', self.terrariums[terrarium_id]['name']),
                    'description': config.get('description', self.terrariums[terrarium_id]['description']),
                    'species': config.get('species', self.terrariums[terrarium_id]['species']),
                    'last_update': time.time()
                })
            
            self.stats['config_updates'] += 1
            self.logger.info(f"Configuration terrarium {terrarium_id} mise à jour")
            
            # Émettre un événement de mise à jour
            if self.event_bus:
                self.event_bus.emit('terrarium_config_updated', {
                    'terrarium_id': terrarium_id,
                    'config': config,
                    'timestamp': time.time()
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour configuration terrarium: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_species_list(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des espèces disponibles
        
        Returns:
            Liste des espèces avec leurs informations
        """
        species_list = []
        
        try:
            # Charger les espèces d'insectes
            insects_dir = self.species_dir / 'insects'
            if insects_dir.exists():
                for species_file in insects_dir.glob('*.json'):
                    try:
                        with open(species_file, 'r', encoding='utf-8') as f:
                            species_config = json.load(f)
                            species_list.append({
                                'id': species_config.get('species_id'),
                                'name': species_config.get('common_name'),
                                'scientific_name': species_config.get('scientific_name'),
                                'type': 'insect',
                                'file': species_file.name
                            })
                    except Exception as e:
                        self.logger.warning(f"Erreur chargement espèce {species_file}: {e}")
            
            # Charger les espèces de reptiles
            reptiles_dir = self.species_dir / 'reptiles'
            if reptiles_dir.exists():
                for species_file in reptiles_dir.glob('*.json'):
                    try:
                        with open(species_file, 'r', encoding='utf-8') as f:
                            species_config = json.load(f)
                            species_list.append({
                                'id': species_config.get('species_id'),
                                'name': species_config.get('common_name'),
                                'scientific_name': species_config.get('scientific_name'),
                                'type': 'reptile',
                                'file': species_file.name
                            })
                    except Exception as e:
                        self.logger.warning(f"Erreur chargement espèce {species_file}: {e}")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement espèces: {e}")
            self.stats['errors'] += 1
        
        return species_list
    
    def get_species_config(self, species_id: str) -> Optional[Dict[str, Any]]:
        """
        Retourne la configuration d'une espèce
        
        Args:
            species_id: ID de l'espèce
            
        Returns:
            Configuration de l'espèce ou None si non trouvée
        """
        try:
            # Chercher dans les insectes
            insects_dir = self.species_dir / 'insects'
            if insects_dir.exists():
                for species_file in insects_dir.glob('*.json'):
                    with open(species_file, 'r', encoding='utf-8') as f:
                        species_config = json.load(f)
                        if species_config.get('species_id') == species_id:
                            return species_config
            
            # Chercher dans les reptiles
            reptiles_dir = self.species_dir / 'reptiles'
            if reptiles_dir.exists():
                for species_file in reptiles_dir.glob('*.json'):
                    with open(species_file, 'r', encoding='utf-8') as f:
                        species_config = json.load(f)
                        if species_config.get('species_id') == species_id:
                            return species_config
            
        except Exception as e:
            self.logger.error(f"Erreur chargement espèce {species_id}: {e}")
            self.stats['errors'] += 1
        
        return None
    
    def update_terrarium_sensors(self, terrarium_id: str, sensor_data: Dict[str, Any]) -> None:
        """
        Met à jour les données des capteurs d'un terrarium
        
        Args:
            terrarium_id: ID du terrarium
            sensor_data: Données des capteurs
        """
        if terrarium_id in self.terrariums:
            self.terrariums[terrarium_id]['sensors'] = sensor_data
            self.terrariums[terrarium_id]['last_update'] = time.time()
    
    def update_terrarium_actuators(self, terrarium_id: str, actuator_data: Dict[str, Any]) -> None:
        """
        Met à jour l'état des actionneurs d'un terrarium
        
        Args:
            terrarium_id: ID du terrarium
            actuator_data: État des actionneurs
        """
        if terrarium_id in self.terrariums:
            self.terrariums[terrarium_id]['actuators'] = actuator_data
            self.terrariums[terrarium_id]['last_update'] = time.time()
    
    def add_terrarium_alert(self, terrarium_id: str, alert: Dict[str, Any]) -> None:
        """
        Ajoute une alerte à un terrarium
        
        Args:
            terrarium_id: ID du terrarium
            alert: Données de l'alerte
        """
        if terrarium_id in self.terrariums:
            if 'alerts' not in self.terrariums[terrarium_id]:
                self.terrariums[terrarium_id]['alerts'] = []
            
            alert['timestamp'] = time.time()
            self.terrariums[terrarium_id]['alerts'].append(alert)
            
            # Limiter le nombre d'alertes
            max_alerts = 50
            if len(self.terrariums[terrarium_id]['alerts']) > max_alerts:
                self.terrariums[terrarium_id]['alerts'] = self.terrariums[terrarium_id]['alerts'][-max_alerts:]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du service
        
        Returns:
            Statistiques du service
        """
        return {
            **self.stats,
            'terrariums_count': len(self.terrariums),
            'current_terrarium': self.current_terrarium,
            'uptime': time.time() - self.stats['start_time']
        }
