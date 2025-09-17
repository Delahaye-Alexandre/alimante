"""
Service de sécurité Alimante
Surveille les limites de sécurité et gère les arrêts d'urgence
"""

import time
import logging
from typing import Dict, Any, Optional, List
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.event_bus import EventBus

class SafetyService:
    """
    Service de sécurité pour surveiller les limites et gérer les arrêts d'urgence
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialise le service de sécurité
        
        Args:
            event_bus: Bus d'événements
        """
        self.event_bus = event_bus or EventBus()
        self.logger = logging.getLogger(__name__)
        
        # Configuration de sécurité
        self.safety_limits = {}
        self.failsafes = {}
        
        # État de sécurité
        self.emergency_stop = False
        self.active_alerts = []
        self.safety_violations = []
        
        # Statistiques
        self.stats = {
            'safety_checks': 0,
            'violations_detected': 0,
            'emergency_stops': 0,
            'alerts_generated': 0,
            'start_time': time.time()
        }
        
        # Charger la configuration de sécurité
        self._load_safety_config()
        
    def _load_safety_config(self) -> None:
        """Charge la configuration de sécurité"""
        try:
            import json
            from pathlib import Path
            
            config_path = Path(__file__).parent.parent.parent / 'config' / 'safety_limits.json'
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                self.safety_limits = config
                self.failsafes = config.get('failsafes', {})
                
                self.logger.info("Configuration de sécurité chargée")
            else:
                self.logger.warning("Fichier de configuration de sécurité non trouvé")
                
        except Exception as e:
            self.logger.error(f"Erreur chargement configuration sécurité: {e}")
    
    def check_safety_limits(self, sensor_data: Dict[str, Any]) -> bool:
        """
        Vérifie les limites de sécurité
        
        Args:
            sensor_data: Données des capteurs
            
        Returns:
            True si tout est sécurisé, False si violation détectée
        """
        try:
            self.stats['safety_checks'] += 1
            violations = []
            
            # Vérifier la température (format direct ou dht22)
            temperature = None
            humidity = None
            
            if 'dht22' in sensor_data and isinstance(sensor_data['dht22'], dict):
                temp_data = sensor_data['dht22']
                temperature = temp_data.get('temperature')
                humidity = temp_data.get('humidity')
            elif 'temperature' in sensor_data:
                temperature = sensor_data.get('temperature')
                humidity = sensor_data.get('humidity')
            
            if temperature is not None:
                temp_violation = self._check_temperature_limits(temperature)
                if temp_violation:
                    violations.append(temp_violation)
            
            if humidity is not None:
                hum_violation = self._check_humidity_limits(humidity)
                if hum_violation:
                    violations.append(hum_violation)
            
            # Vérifier la qualité de l'air (format direct ou air_quality)
            aqi = None
            if 'air_quality' in sensor_data:
                if isinstance(sensor_data['air_quality'], dict):
                    air_data = sensor_data['air_quality']
                    aqi = air_data.get('aqi')
                else:
                    aqi = sensor_data['air_quality']
            
            if aqi is not None:
                air_violation = self._check_air_quality_limits(aqi)
                if air_violation:
                    violations.append(air_violation)
            
            # Vérifier le niveau d'eau (format direct ou water_level)
            water_level = None
            if 'water_level' in sensor_data:
                if isinstance(sensor_data['water_level'], dict):
                    water_data = sensor_data['water_level']
                    water_level = water_data.get('level')
                else:
                    water_level = sensor_data['water_level']
            
            if water_level is not None:
                water_violation = self._check_water_level_limits(water_level)
                if water_violation:
                    violations.append(water_violation)
            
            # Traiter les violations
            if violations:
                self._handle_safety_violations(violations)
                return False
            else:
                # Aucune violation détectée
                return True
                
        except Exception as e:
            self.logger.error(f"Erreur vérification limites sécurité: {e}")
            return False
    
    def _check_temperature_limits(self, temperature: float) -> Optional[Dict[str, Any]]:
        """Vérifie les limites de température"""
        try:
            temp_limits = self.safety_limits.get('temperature', {})
            
            critical_max = temp_limits.get('critical_max', 45.0)
            critical_min = temp_limits.get('critical_min', 5.0)
            
            if temperature > critical_max:
                return {
                    'type': 'temperature_critical_high',
                    'parameter': 'temperature',
                    'value': temperature,
                    'limit': critical_max,
                    'severity': 'critical',
                    'message': f"Température critique élevée: {temperature:.1f}°C (limite: {critical_max}°C)"
                }
            elif temperature < critical_min:
                return {
                    'type': 'temperature_critical_low',
                    'parameter': 'temperature',
                    'value': temperature,
                    'limit': critical_min,
                    'severity': 'critical',
                    'message': f"Température critique basse: {temperature:.1f}°C (limite: {critical_min}°C)"
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur vérification température: {e}")
            return None
    
    def _check_humidity_limits(self, humidity: float) -> Optional[Dict[str, Any]]:
        """Vérifie les limites d'humidité"""
        try:
            hum_limits = self.safety_limits.get('humidity', {})
            
            critical_max = hum_limits.get('critical_max', 99.0)
            critical_min = hum_limits.get('critical_min', 10.0)
            
            if humidity > critical_max:
                return {
                    'type': 'humidity_critical_high',
                    'parameter': 'humidity',
                    'value': humidity,
                    'limit': critical_max,
                    'severity': 'critical',
                    'message': f"Humidité critique élevée: {humidity:.1f}% (limite: {critical_max}%)"
                }
            elif humidity < critical_min:
                return {
                    'type': 'humidity_critical_low',
                    'parameter': 'humidity',
                    'value': humidity,
                    'limit': critical_min,
                    'severity': 'critical',
                    'message': f"Humidité critique basse: {humidity:.1f}% (limite: {critical_min}%)"
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur vérification humidité: {e}")
            return None
    
    def _check_air_quality_limits(self, aqi: int) -> Optional[Dict[str, Any]]:
        """Vérifie les limites de qualité de l'air"""
        try:
            air_limits = self.safety_limits.get('air_quality', {})
            
            hazardous_threshold = air_limits.get('hazardous_threshold', 300)
            
            if aqi >= hazardous_threshold:
                return {
                    'type': 'air_quality_hazardous',
                    'parameter': 'air_quality',
                    'value': aqi,
                    'limit': hazardous_threshold,
                    'severity': 'critical',
                    'message': f"Qualité d'air dangereuse: AQI {aqi} (limite: {hazardous_threshold})"
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur vérification qualité air: {e}")
            return None
    
    def _check_water_level_limits(self, level: float) -> Optional[Dict[str, Any]]:
        """Vérifie les limites de niveau d'eau"""
        try:
            water_limits = self.safety_limits.get('water_level', {})
            
            critical_level = water_limits.get('critical_level', 15.0)
            
            if level <= critical_level:
                return {
                    'type': 'water_level_critical',
                    'parameter': 'water_level',
                    'value': level,
                    'limit': critical_level,
                    'severity': 'critical',
                    'message': f"Niveau d'eau critique: {level:.1f}% (limite: {critical_level}%)"
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur vérification niveau eau: {e}")
            return None
    
    def _handle_safety_violations(self, violations: List[Dict[str, Any]]) -> None:
        """Gère les violations de sécurité"""
        try:
            for violation in violations:
                self.safety_violations.append(violation)
                self.stats['violations_detected'] += 1
                
                # Ajouter à la liste des alertes actives
                self.active_alerts.append({
                    'type': violation['type'],
                    'message': violation['message'],
                    'severity': violation['severity'],
                    'timestamp': time.time(),
                    'acknowledged': False
                })
                
                self.stats['alerts_generated'] += 1
                
                # Émettre un événement d'alerte
                self.event_bus.emit('safety_alert', violation)
                
                # Vérifier si un arrêt d'urgence est nécessaire
                if violation['severity'] == 'critical':
                    self._trigger_emergency_stop(violation)
                
                self.logger.critical(f"VIOLATION SÉCURITÉ: {violation['message']}")
            
        except Exception as e:
            self.logger.error(f"Erreur gestion violations sécurité: {e}")
    
    def _trigger_emergency_stop(self, violation: Dict[str, Any]) -> None:
        """Déclenche un arrêt d'urgence"""
        try:
            if not self.emergency_stop:
                self.emergency_stop = True
                self.stats['emergency_stops'] += 1
                
                # Émettre un événement d'arrêt d'urgence
                self.event_bus.emit('emergency_stop', {
                    'reason': violation['message'],
                    'timestamp': time.time(),
                    'violation': violation
                })
                
                self.logger.critical(f"ARRÊT D'URGENCE DÉCLENCHÉ: {violation['message']}")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt d'urgence: {e}")
    
    def acknowledge_alert(self, alert_index: int) -> bool:
        """
        Acquitte une alerte
        
        Args:
            alert_index: Index de l'alerte à acquitter
            
        Returns:
            True si succès, False sinon
        """
        try:
            if 0 <= alert_index < len(self.active_alerts):
                self.active_alerts[alert_index]['acknowledged'] = True
                self.logger.info(f"Alerte {alert_index} acquittée")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur acquittement alerte: {e}")
            return False
    
    def clear_emergency_stop(self) -> bool:
        """
        Désactive l'arrêt d'urgence
        
        Returns:
            True si succès, False sinon
        """
        try:
            if self.emergency_stop:
                self.emergency_stop = False
                
                # Émettre un événement de reprise
                self.event_bus.emit('emergency_resume', {
                    'timestamp': time.time()
                })
                
                self.logger.info("Arrêt d'urgence désactivé")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur désactivation arrêt d'urgence: {e}")
            return False
    
    def get_safety_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de sécurité
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'emergency_stop': self.emergency_stop,
            'active_alerts': len([a for a in self.active_alerts if not a['acknowledged']]),
            'total_alerts': len(self.active_alerts),
            'safety_violations': len(self.safety_violations),
            'stats': self.stats.copy()
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Retourne les alertes actives
        
        Returns:
            Liste des alertes actives
        """
        return [alert for alert in self.active_alerts if not alert['acknowledged']]
    
    def get_safety_violations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Retourne les violations de sécurité récentes
        
        Args:
            hours: Nombre d'heures d'historique
            
        Returns:
            Liste des violations
        """
        try:
            cutoff_time = time.time() - (hours * 3600)
            return [v for v in self.safety_violations if v.get('timestamp', 0) >= cutoff_time]
            
        except Exception as e:
            self.logger.error(f"Erreur récupération violations: {e}")
            return []
    
    def reset_safety_data(self) -> None:
        """Remet à zéro les données de sécurité"""
        try:
            self.active_alerts.clear()
            self.safety_violations.clear()
            self.emergency_stop = False
            
            self.logger.info("Données de sécurité réinitialisées")
            
        except Exception as e:
            self.logger.error(f"Erreur réinitialisation données sécurité: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut complet du service
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'service_name': 'safety_service',
            'enabled': True,
            'safety_status': self.get_safety_status(),
            'safety_limits': self.safety_limits,
            'failsafes': self.failsafes
        }
