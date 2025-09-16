"""
Système de calibration pour Alimante
Calibration des capteurs et actionneurs
"""

import time
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import statistics

class CalibrationManager:
    """
    Gestionnaire de calibration pour les capteurs et actionneurs
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le gestionnaire de calibration
        
        Args:
            config_path: Chemin vers le fichier de configuration de calibration
        """
        self.logger = logging.getLogger(__name__)
        
        # Chemin de configuration
        self.config_path = Path(config_path) if config_path else Path(__file__).parent.parent.parent / 'config' / 'calibration.json'
        
        # Données de calibration
        self.calibration_data = {}
        
        # État de calibration
        self.is_calibrating = False
        self.current_sensor = None
        self.calibration_samples = []
        
        # Charger la configuration existante
        self._load_calibration_data()
        
    def _load_calibration_data(self) -> None:
        """Charge les données de calibration existantes"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.calibration_data = json.load(f)
                self.logger.info("Données de calibration chargées")
            else:
                self.calibration_data = {}
                self.logger.info("Aucune donnée de calibration existante")
                
        except Exception as e:
            self.logger.error(f"Erreur chargement calibration: {e}")
            self.calibration_data = {}
    
    def _save_calibration_data(self) -> None:
        """Sauvegarde les données de calibration"""
        try:
            # Créer le répertoire si nécessaire
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            
            self.logger.info("Données de calibration sauvegardées")
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde calibration: {e}")
    
    def start_calibration(self, sensor_name: str, calibration_type: str, 
                         duration: float = 60.0) -> bool:
        """
        Démarre une calibration
        
        Args:
            sensor_name: Nom du capteur
            calibration_type: Type de calibration ('offset', 'scale', 'linear')
            duration: Durée de calibration en secondes
            
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if self.is_calibrating:
                self.logger.warning("Calibration déjà en cours")
                return False
            
            self.logger.info(f"Démarrage calibration {sensor_name} ({calibration_type})")
            
            self.is_calibrating = True
            self.current_sensor = sensor_name
            self.calibration_samples = []
            
            # Créer l'entrée de calibration
            if sensor_name not in self.calibration_data:
                self.calibration_data[sensor_name] = {}
            
            self.calibration_data[sensor_name][calibration_type] = {
                'status': 'in_progress',
                'start_time': time.time(),
                'duration': duration,
                'samples': []
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage calibration: {e}")
            return False
    
    def add_calibration_sample(self, sensor_name: str, value: float, 
                              reference_value: Optional[float] = None) -> None:
        """
        Ajoute un échantillon de calibration
        
        Args:
            sensor_name: Nom du capteur
            value: Valeur mesurée
            reference_value: Valeur de référence (optionnelle)
        """
        try:
            if not self.is_calibrating or self.current_sensor != sensor_name:
                self.logger.warning(f"Pas de calibration en cours pour {sensor_name}")
                return
            
            sample = {
                'timestamp': time.time(),
                'value': value,
                'reference': reference_value
            }
            
            self.calibration_samples.append(sample)
            
            # Mettre à jour les données de calibration
            if sensor_name in self.calibration_data:
                for calib_type in self.calibration_data[sensor_name]:
                    if self.calibration_data[sensor_name][calib_type].get('status') == 'in_progress':
                        self.calibration_data[sensor_name][calib_type]['samples'].append(sample)
            
            self.logger.debug(f"Échantillon ajouté pour {sensor_name}: {value}")
            
        except Exception as e:
            self.logger.error(f"Erreur ajout échantillon: {e}")
    
    def finish_calibration(self, sensor_name: str, calibration_type: str) -> bool:
        """
        Termine une calibration et calcule les paramètres
        
        Args:
            sensor_name: Nom du capteur
            calibration_type: Type de calibration
            
        Returns:
            True si la calibration réussit, False sinon
        """
        try:
            if not self.is_calibrating or self.current_sensor != sensor_name:
                self.logger.warning(f"Pas de calibration en cours pour {sensor_name}")
                return False
            
            if len(self.calibration_samples) < 10:
                self.logger.warning(f"Pas assez d'échantillons pour {sensor_name} ({len(self.calibration_samples)})")
                return False
            
            self.logger.info(f"Finalisation calibration {sensor_name} ({calibration_type})")
            
            # Calculer les paramètres selon le type
            if calibration_type == 'offset':
                params = self._calculate_offset_calibration()
            elif calibration_type == 'scale':
                params = self._calculate_scale_calibration()
            elif calibration_type == 'linear':
                params = self._calculate_linear_calibration()
            else:
                self.logger.error(f"Type de calibration inconnu: {calibration_type}")
                return False
            
            # Mettre à jour les données de calibration
            self.calibration_data[sensor_name][calibration_type].update({
                'status': 'completed',
                'end_time': time.time(),
                'samples_count': len(self.calibration_samples),
                'parameters': params
            })
            
            # Sauvegarder
            self._save_calibration_data()
            
            # Réinitialiser l'état
            self.is_calibrating = False
            self.current_sensor = None
            self.calibration_samples = []
            
            self.logger.info(f"Calibration {sensor_name} terminée avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur finalisation calibration: {e}")
            return False
    
    def _calculate_offset_calibration(self) -> Dict[str, float]:
        """Calcule la calibration d'offset"""
        try:
            values = [sample['value'] for sample in self.calibration_samples]
            reference_values = [sample['reference'] for sample in self.calibration_samples if sample['reference'] is not None]
            
            if not reference_values:
                # Pas de valeur de référence, utiliser la moyenne
                offset = -statistics.mean(values)
            else:
                # Calculer l'offset moyen
                offsets = [ref - val for val, ref in zip(values, reference_values)]
                offset = statistics.mean(offsets)
            
            return {
                'offset': offset,
                'mean_value': statistics.mean(values),
                'std_value': statistics.stdev(values) if len(values) > 1 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul offset: {e}")
            return {'offset': 0.0, 'mean_value': 0.0, 'std_value': 0.0}
    
    def _calculate_scale_calibration(self) -> Dict[str, float]:
        """Calcule la calibration d'échelle"""
        try:
            values = [sample['value'] for sample in self.calibration_samples]
            reference_values = [sample['reference'] for sample in self.calibration_samples if sample['reference'] is not None]
            
            if not reference_values:
                self.logger.warning("Pas de valeurs de référence pour la calibration d'échelle")
                return {'scale': 1.0, 'offset': 0.0}
            
            # Régression linéaire simple
            n = len(values)
            sum_x = sum(values)
            sum_y = sum(reference_values)
            sum_xy = sum(x * y for x, y in zip(values, reference_values))
            sum_x2 = sum(x * x for x in values)
            
            if n * sum_x2 - sum_x * sum_x == 0:
                self.logger.warning("Division par zéro dans le calcul d'échelle")
                return {'scale': 1.0, 'offset': 0.0}
            
            scale = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            offset = (sum_y - scale * sum_x) / n
            
            return {
                'scale': scale,
                'offset': offset,
                'r_squared': self._calculate_r_squared(values, reference_values, scale, offset)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul échelle: {e}")
            return {'scale': 1.0, 'offset': 0.0, 'r_squared': 0.0}
    
    def _calculate_linear_calibration(self) -> Dict[str, float]:
        """Calcule la calibration linéaire complète"""
        try:
            values = [sample['value'] for sample in self.calibration_samples]
            reference_values = [sample['reference'] for sample in self.calibration_samples if sample['reference'] is not None]
            
            if not reference_values:
                self.logger.warning("Pas de valeurs de référence pour la calibration linéaire")
                return {'scale': 1.0, 'offset': 0.0}
            
            # Régression linéaire
            n = len(values)
            sum_x = sum(values)
            sum_y = sum(reference_values)
            sum_xy = sum(x * y for x, y in zip(values, reference_values))
            sum_x2 = sum(x * x for x in values)
            
            if n * sum_x2 - sum_x * sum_x == 0:
                self.logger.warning("Division par zéro dans le calcul linéaire")
                return {'scale': 1.0, 'offset': 0.0}
            
            scale = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            offset = (sum_y - scale * sum_x) / n
            
            return {
                'scale': scale,
                'offset': offset,
                'r_squared': self._calculate_r_squared(values, reference_values, scale, offset),
                'mean_error': self._calculate_mean_error(values, reference_values, scale, offset)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul linéaire: {e}")
            return {'scale': 1.0, 'offset': 0.0, 'r_squared': 0.0, 'mean_error': 0.0}
    
    def _calculate_r_squared(self, x_values: List[float], y_values: List[float], 
                            scale: float, offset: float) -> float:
        """Calcule le coefficient de détermination R²"""
        try:
            if len(x_values) != len(y_values):
                return 0.0
            
            # Valeurs prédites
            y_pred = [scale * x + offset for x in x_values]
            
            # Moyenne des valeurs observées
            y_mean = statistics.mean(y_values)
            
            # Somme des carrés des résidus
            ss_res = sum((y - pred) ** 2 for y, pred in zip(y_values, y_pred))
            
            # Somme des carrés totaux
            ss_tot = sum((y - y_mean) ** 2 for y in y_values)
            
            if ss_tot == 0:
                return 1.0 if ss_res == 0 else 0.0
            
            return 1 - (ss_res / ss_tot)
            
        except Exception as e:
            self.logger.error(f"Erreur calcul R²: {e}")
            return 0.0
    
    def _calculate_mean_error(self, x_values: List[float], y_values: List[float], 
                             scale: float, offset: float) -> float:
        """Calcule l'erreur moyenne absolue"""
        try:
            if len(x_values) != len(y_values):
                return 0.0
            
            errors = [abs(y - (scale * x + offset)) for x, y in zip(x_values, y_values)]
            return statistics.mean(errors)
            
        except Exception as e:
            self.logger.error(f"Erreur calcul erreur moyenne: {e}")
            return 0.0
    
    def apply_calibration(self, sensor_name: str, raw_value: float) -> float:
        """
        Applique la calibration à une valeur brute
        
        Args:
            sensor_name: Nom du capteur
            raw_value: Valeur brute
            
        Returns:
            Valeur calibrée
        """
        try:
            if sensor_name not in self.calibration_data:
                return raw_value
            
            calibrated_value = raw_value
            
            # Appliquer l'offset
            if 'offset' in self.calibration_data[sensor_name]:
                offset_params = self.calibration_data[sensor_name]['offset']
                if offset_params.get('status') == 'completed':
                    calibrated_value += offset_params['parameters']['offset']
            
            # Appliquer l'échelle
            if 'scale' in self.calibration_data[sensor_name]:
                scale_params = self.calibration_data[sensor_name]['scale']
                if scale_params.get('status') == 'completed':
                    params = scale_params['parameters']
                    calibrated_value = calibrated_value * params['scale'] + params['offset']
            
            # Appliquer la calibration linéaire
            elif 'linear' in self.calibration_data[sensor_name]:
                linear_params = self.calibration_data[sensor_name]['linear']
                if linear_params.get('status') == 'completed':
                    params = linear_params['parameters']
                    calibrated_value = calibrated_value * params['scale'] + params['offset']
            
            return calibrated_value
            
        except Exception as e:
            self.logger.error(f"Erreur application calibration {sensor_name}: {e}")
            return raw_value
    
    def get_calibration_status(self, sensor_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Retourne le statut de calibration
        
        Args:
            sensor_name: Nom du capteur (None = tous)
            
        Returns:
            Statut de calibration
        """
        try:
            if sensor_name is None:
                return self.calibration_data.copy()
            else:
                return self.calibration_data.get(sensor_name, {})
                
        except Exception as e:
            self.logger.error(f"Erreur récupération statut calibration: {e}")
            return {}
    
    def reset_calibration(self, sensor_name: str) -> None:
        """
        Remet à zéro la calibration d'un capteur
        
        Args:
            sensor_name: Nom du capteur
        """
        try:
            if sensor_name in self.calibration_data:
                del self.calibration_data[sensor_name]
                self._save_calibration_data()
                self.logger.info(f"Calibration {sensor_name} réinitialisée")
            
        except Exception as e:
            self.logger.error(f"Erreur réinitialisation calibration {sensor_name}: {e}")

