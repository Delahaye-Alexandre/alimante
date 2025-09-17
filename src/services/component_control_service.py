"""
Service de contrôle des composants
Gère le contrôle manuel et automatique des actionneurs
"""

import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum

class ComponentType(Enum):
    """Types de composants"""
    HEATING = "heating"
    LIGHTING = "lighting"
    HUMIDIFICATION = "humidification"
    VENTILATION = "ventilation"
    FEEDING = "feeding"
    WATER = "water"

class ControlMode(Enum):
    """Modes de contrôle"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    DISABLED = "disabled"

class ComponentControlService:
    """
    Service de contrôle des composants
    """
    
    def __init__(self, event_bus=None):
        """
        Initialise le service de contrôle des composants
        
        Args:
            event_bus: Bus d'événements pour la communication
        """
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # État des composants
        self.components = {}
        self.control_modes = {}
        self.manual_controls = {}
        
        # Statistiques
        self.stats = {
            'commands_sent': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Initialiser les composants par défaut
        self._initialize_components()
        
    def _initialize_components(self) -> None:
        """Initialise les composants par défaut"""
        try:
            # Charger la configuration de l'espèce par défaut
            species_config = self._load_default_species_config()
            
            # Composants de chauffage
            temp_config = species_config.get('environmental_requirements', {}).get('temperature', {})
            day_temp = temp_config.get('day', {}).get('optimal', 25.0)
            night_temp = temp_config.get('night', {}).get('optimal', 20.0)
            
            self.components[ComponentType.HEATING] = {
                'enabled': True,
                'current_state': False,
                'target_temperature': day_temp,
                'night_temperature': night_temp,
                'current_temperature': 20.0,
                'power_level': 0,
                'control_mode': 'automatic',
                'last_update': time.time()
            }
            
            # Composants d'éclairage
            lighting_config = species_config.get('environmental_requirements', {}).get('lighting', {})
            photoperiod = lighting_config.get('photoperiod', {})
            intensity = lighting_config.get('intensity', {})
            
            self.components[ComponentType.LIGHTING] = {
                'enabled': True,
                'current_state': False,
                'brightness': 0,
                'target_brightness': intensity.get('optimal', 60),
                'color_temperature': 6500,
                'control_mode': 'automatic',
                'schedule': {
                    'on_time': photoperiod.get('day_start', '08:00'),
                    'off_time': photoperiod.get('day_end', '20:00'),
                    'fade_duration': lighting_config.get('fade', {}).get('sunrise_duration', 30)
                },
                'last_update': time.time()
            }
            
            # Composants d'humidification
            humidity_config = species_config.get('environmental_requirements', {}).get('humidity', {})
            
            self.components[ComponentType.HUMIDIFICATION] = {
                'enabled': True,
                'current_state': False,
                'target_humidity': humidity_config.get('optimal', 65.0),
                'current_humidity': 45.0,
                'control_mode': 'automatic',
                'cycle_time': 300,  # 5 minutes
                'last_update': time.time()
            }
            
            # Composants de ventilation
            ventilation_config = species_config.get('environmental_requirements', {}).get('ventilation', {})
            air_circulation = ventilation_config.get('air_circulation', {})
            
            self.components[ComponentType.VENTILATION] = {
                'enabled': True,
                'current_state': False,
                'fan_speed': 0,
                'target_speed': air_circulation.get('base_speed', 25),
                'max_speed': air_circulation.get('max_speed', 60),
                'control_mode': 'automatic',
                'auto_mode': True,
                'last_update': time.time()
            }
            
            # Composants d'alimentation
            feeding_config = species_config.get('feeding_requirements', {})
            schedule = feeding_config.get('schedule', {})
            
            self.components[ComponentType.FEEDING] = {
                'enabled': True,
                'current_state': False,
                'servo_angle': 0,
                'control_mode': 'automatic',
                'feeding_schedule': schedule.get('times', ['10:00', '19:00']),
                'last_feeding': None,
                'daily_feeds': 0,
                'max_daily_feeds': 3,
                'portion_size': schedule.get('portion_size', 'small'),
                'last_update': time.time()
            }
            
            # Modes de contrôle par défaut
            for component_type in ComponentType:
                self.control_modes[component_type] = ControlMode.AUTOMATIC
                self.manual_controls[component_type] = False
            
            species_name = species_config.get('common_name', 'espèce par défaut')
            self.logger.info(f"Composants initialisés avec paramètres de {species_name}")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation composants: {e}")
            self.stats['errors'] += 1
    
    def _load_default_species_config(self) -> Dict[str, Any]:
        """Charge la configuration de l'espèce par défaut (mantis_religiosa)"""
        try:
            from pathlib import Path
            import json
            
            # Chemin vers la configuration de l'espèce
            config_dir = Path(__file__).parent.parent.parent / 'config'
            species_file = config_dir / 'species' / 'insects' / 'mantis_religiosa.json'
            
            if species_file.exists():
                with open(species_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Fichier de configuration {species_file} non trouvé, utilisation des valeurs par défaut")
                return self._get_fallback_species_config()
                
        except Exception as e:
            self.logger.error(f"Erreur chargement configuration espèce: {e}")
            return self._get_fallback_species_config()
    
    def _get_fallback_species_config(self) -> Dict[str, Any]:
        """Configuration de fallback si le fichier JSON n'est pas trouvé"""
        return {
            'common_name': 'Mante religieuse',
            'environmental_requirements': {
                'temperature': {
                    'day': {'optimal': 25.0},
                    'night': {'optimal': 20.0}
                },
                'humidity': {'optimal': 65.0},
                'lighting': {
                    'photoperiod': {'day_start': '08:00', 'day_end': '20:00'},
                    'intensity': {'optimal': 60},
                    'fade': {'sunrise_duration': 30}
                },
                'ventilation': {
                    'air_circulation': {'base_speed': 25, 'max_speed': 60}
                }
            },
            'feeding_requirements': {
                'schedule': {'times': ['10:00', '19:00'], 'portion_size': 'small'}
            }
        }
    
    def get_component_status(self, component_type: ComponentType) -> Optional[Dict[str, Any]]:
        """
        Retourne le statut d'un composant
        
        Args:
            component_type: Type de composant
            
        Returns:
            Statut du composant ou None si non trouvé
        """
        return self.components.get(component_type)
    
    def get_all_components_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de tous les composants
        
        Returns:
            Statut de tous les composants
        """
        return {
            component_type.value: status 
            for component_type, status in self.components.items()
        }
    
    def set_control_mode(self, component_type: ComponentType, mode: ControlMode) -> bool:
        """
        Définit le mode de contrôle d'un composant
        
        Args:
            component_type: Type de composant
            mode: Mode de contrôle
            
        Returns:
            True si succès, False sinon
        """
        try:
            if component_type not in self.components:
                self.logger.error(f"Composant {component_type.value} non trouvé")
                return False
            
            self.control_modes[component_type] = mode
            self.logger.info(f"Mode de contrôle {component_type.value}: {mode.value}")
            
            # Émettre un événement de changement de mode
            if self.event_bus:
                self.event_bus.emit('control_mode_changed', {
                    'component': component_type.value,
                    'mode': mode.value,
                    'timestamp': time.time()
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur changement mode contrôle: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_control_mode(self, component_type: ComponentType) -> ControlMode:
        """
        Retourne le mode de contrôle d'un composant
        
        Args:
            component_type: Type de composant
            
        Returns:
            Mode de contrôle actuel
        """
        return self.control_modes.get(component_type, ControlMode.AUTOMATIC)
    
    def manual_control(self, component_type: ComponentType, command: Dict[str, Any]) -> bool:
        """
        Contrôle manuel d'un composant
        
        Args:
            component_type: Type de composant
            command: Commande à exécuter
            
        Returns:
            True si succès, False sinon
        """
        try:
            if component_type not in self.components:
                self.logger.error(f"Composant {component_type.value} non trouvé")
                return False
            
            if not self.components[component_type]['enabled']:
                self.logger.warning(f"Composant {component_type.value} désactivé")
                return False
            
            # Vérifier le mode de contrôle
            if self.control_modes[component_type] == ControlMode.DISABLED:
                self.logger.warning(f"Composant {component_type.value} en mode désactivé")
                return False
            
            # Exécuter la commande selon le type de composant
            success = self._execute_command(component_type, command)
            
            if success:
                self.stats['successful_commands'] += 1
                self.manual_controls[component_type] = True
                
                # Émettre un événement de commande
                if self.event_bus:
                    self.event_bus.emit('component_controlled', {
                        'component': component_type.value,
                        'command': command,
                        'mode': 'manual',
                        'timestamp': time.time()
                    })
            else:
                self.stats['failed_commands'] += 1
            
            self.stats['commands_sent'] += 1
            return success
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle manuel {component_type.value}: {e}")
            self.stats['errors'] += 1
            return False
    
    def _execute_command(self, component_type: ComponentType, command: Dict[str, Any]) -> bool:
        """
        Exécute une commande sur un composant
        
        Args:
            component_type: Type de composant
            command: Commande à exécuter
            
        Returns:
            True si succès, False sinon
        """
        try:
            if component_type == ComponentType.HEATING:
                return self._control_heating(command)
            elif component_type == ComponentType.LIGHTING:
                return self._control_lighting(command)
            elif component_type == ComponentType.HUMIDIFICATION:
                return self._control_humidification(command)
            elif component_type == ComponentType.VENTILATION:
                return self._control_ventilation(command)
            elif component_type == ComponentType.FEEDING:
                return self._control_feeding(command)
            else:
                self.logger.error(f"Type de composant non supporté: {component_type.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur exécution commande {component_type.value}: {e}")
            return False
    
    def _control_heating(self, command: Dict[str, Any]) -> bool:
        """Contrôle du chauffage"""
        try:
            if 'state' in command:
                self.components[ComponentType.HEATING]['current_state'] = command['state']
                self.logger.info(f"Chauffage: {'ON' if command['state'] else 'OFF'}")
            
            if 'target_temperature' in command:
                self.components[ComponentType.HEATING]['target_temperature'] = command['target_temperature']
                self.logger.info(f"Température cible: {command['target_temperature']}°C")
            
            if 'power_level' in command:
                self.components[ComponentType.HEATING]['power_level'] = command['power_level']
                self.logger.info(f"Niveau de puissance: {command['power_level']}%")
            
            self.components[ComponentType.HEATING]['last_update'] = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle chauffage: {e}")
            return False
    
    def _control_lighting(self, command: Dict[str, Any]) -> bool:
        """Contrôle de l'éclairage"""
        try:
            if 'state' in command:
                self.components[ComponentType.LIGHTING]['current_state'] = command['state']
                self.logger.info(f"Éclairage: {'ON' if command['state'] else 'OFF'}")
            
            if 'brightness' in command:
                brightness = max(0, min(100, command['brightness']))
                self.components[ComponentType.LIGHTING]['brightness'] = brightness
                self.components[ComponentType.LIGHTING]['target_brightness'] = brightness
                self.logger.info(f"Luminosité: {brightness}%")
            
            if 'color_temperature' in command:
                self.components[ComponentType.LIGHTING]['color_temperature'] = command['color_temperature']
                self.logger.info(f"Température de couleur: {command['color_temperature']}K")
            
            self.components[ComponentType.LIGHTING]['last_update'] = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle éclairage: {e}")
            return False
    
    def _control_humidification(self, command: Dict[str, Any]) -> bool:
        """Contrôle de l'humidification"""
        try:
            if 'state' in command:
                self.components[ComponentType.HUMIDIFICATION]['current_state'] = command['state']
                self.logger.info(f"Humidificateur: {'ON' if command['state'] else 'OFF'}")
            
            if 'target_humidity' in command:
                self.components[ComponentType.HUMIDIFICATION]['target_humidity'] = command['target_humidity']
                self.logger.info(f"Humidité cible: {command['target_humidity']}%")
            
            if 'cycle_time' in command:
                self.components[ComponentType.HUMIDIFICATION]['cycle_time'] = command['cycle_time']
                self.logger.info(f"Temps de cycle: {command['cycle_time']}s")
            
            self.components[ComponentType.HUMIDIFICATION]['last_update'] = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle humidification: {e}")
            return False
    
    def _control_ventilation(self, command: Dict[str, Any]) -> bool:
        """Contrôle de la ventilation"""
        try:
            if 'state' in command:
                self.components[ComponentType.VENTILATION]['current_state'] = command['state']
                self.logger.info(f"Ventilation: {'ON' if command['state'] else 'OFF'}")
            
            if 'fan_speed' in command:
                speed = max(0, min(100, command['fan_speed']))
                self.components[ComponentType.VENTILATION]['fan_speed'] = speed
                self.components[ComponentType.VENTILATION]['target_speed'] = speed
                self.logger.info(f"Vitesse ventilateur: {speed}%")
            
            if 'auto_mode' in command:
                self.components[ComponentType.VENTILATION]['auto_mode'] = command['auto_mode']
                self.logger.info(f"Mode automatique: {command['auto_mode']}")
            
            self.components[ComponentType.VENTILATION]['last_update'] = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle ventilation: {e}")
            return False
    
    def _control_feeding(self, command: Dict[str, Any]) -> bool:
        """Contrôle de l'alimentation"""
        try:
            if 'feed' in command and command['feed']:
                # Vérifier les limites de sécurité
                if self.components[ComponentType.FEEDING]['daily_feeds'] >= self.components[ComponentType.FEEDING]['max_daily_feeds']:
                    self.logger.warning("Limite quotidienne d'alimentation atteinte")
                    return False
                
                # Exécuter l'alimentation
                self.components[ComponentType.FEEDING]['current_state'] = True
                self.components[ComponentType.FEEDING]['daily_feeds'] += 1
                self.components[ComponentType.FEEDING]['last_feeding'] = time.time()
                self.logger.info(f"Alimentation exécutée (quotidien: {self.components[ComponentType.FEEDING]['daily_feeds']})")
                
                # Simuler l'ouverture du servo
                self.components[ComponentType.FEEDING]['servo_angle'] = 90
                
                # Émettre un événement d'alimentation
                if self.event_bus:
                    self.event_bus.emit('feeding_executed', {
                        'daily_feeds': self.components[ComponentType.FEEDING]['daily_feeds'],
                        'timestamp': time.time()
                    })
            
            if 'servo_angle' in command:
                self.components[ComponentType.FEEDING]['servo_angle'] = command['servo_angle']
                self.logger.info(f"Angle servo: {command['servo_angle']}°")
            
            self.components[ComponentType.FEEDING]['last_update'] = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle alimentation: {e}")
            return False
    
    def update_sensor_data(self, sensor_data: Dict[str, Any]) -> None:
        """
        Met à jour les données des capteurs pour le contrôle automatique
        
        Args:
            sensor_data: Données des capteurs
        """
        try:
            # Mettre à jour la température pour le chauffage
            if 'temperature' in sensor_data:
                self.components[ComponentType.HEATING]['current_temperature'] = sensor_data['temperature']
            
            # Mettre à jour l'humidité pour l'humidification
            if 'humidity' in sensor_data:
                self.components[ComponentType.HUMIDIFICATION]['current_humidity'] = sensor_data['humidity']
            
            # Contrôle automatique si activé
            self._automatic_control(sensor_data)
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour données capteurs: {e}")
            self.stats['errors'] += 1
    
    def _automatic_control(self, sensor_data: Dict[str, Any]) -> None:
        """
        Contrôle automatique basé sur les données des capteurs
        
        Args:
            sensor_data: Données des capteurs
        """
        try:
            # Contrôle automatique du chauffage
            if (self.control_modes[ComponentType.HEATING] == ControlMode.AUTOMATIC and 
                self.components[ComponentType.HEATING]['enabled']):
                
                current_temp = sensor_data.get('temperature', 20.0)
                target_temp = self.components[ComponentType.HEATING]['target_temperature']
                hysteresis = 1.0
                
                if current_temp < target_temp - hysteresis:
                    self.components[ComponentType.HEATING]['current_state'] = True
                elif current_temp > target_temp + hysteresis:
                    self.components[ComponentType.HEATING]['current_state'] = False
            
            # Contrôle automatique de l'humidification
            if (self.control_modes[ComponentType.HUMIDIFICATION] == ControlMode.AUTOMATIC and 
                self.components[ComponentType.HUMIDIFICATION]['enabled']):
                
                current_humidity = sensor_data.get('humidity', 45.0)
                target_humidity = self.components[ComponentType.HUMIDIFICATION]['target_humidity']
                hysteresis = 5.0
                
                if current_humidity < target_humidity - hysteresis:
                    self.components[ComponentType.HUMIDIFICATION]['current_state'] = True
                elif current_humidity > target_humidity + hysteresis:
                    self.components[ComponentType.HUMIDIFICATION]['current_state'] = False
            
            # Contrôle automatique de la ventilation
            if (self.control_modes[ComponentType.VENTILATION] == ControlMode.AUTOMATIC and 
                self.components[ComponentType.VENTILATION]['enabled']):
                
                air_quality = sensor_data.get('air_quality', 50)
                if air_quality > 200:  # Seuil de qualité d'air
                    self.components[ComponentType.VENTILATION]['current_state'] = True
                    self.components[ComponentType.VENTILATION]['fan_speed'] = min(100, (air_quality - 200) * 2)
                else:
                    self.components[ComponentType.VENTILATION]['current_state'] = False
                    self.components[ComponentType.VENTILATION]['fan_speed'] = 0
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle automatique: {e}")
            self.stats['errors'] += 1
    
    def reset_daily_feeds(self) -> None:
        """Remet à zéro le compteur d'alimentations quotidiennes"""
        self.components[ComponentType.FEEDING]['daily_feeds'] = 0
        self.logger.info("Compteur d'alimentations quotidiennes remis à zéro")
    
    def control_component(self, component_name: str, command: Dict[str, Any]) -> bool:
        """
        Contrôle un composant par son nom (interface web)
        
        Args:
            component_name: Nom du composant (heating, lighting, etc.)
            command: Commande à exécuter
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Convertir le nom en ComponentType
            component_type = None
            for ct in ComponentType:
                if ct.value == component_name:
                    component_type = ct
                    break
            
            if not component_type:
                self.logger.error(f"Composant {component_name} non trouvé")
                return False
            
            # Utiliser la méthode manual_control existante
            return self.manual_control(component_type, command)
            
        except Exception as e:
            self.logger.error(f"Erreur contrôle composant {component_name}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du service
        
        Returns:
            Statistiques du service
        """
        return {
            **self.stats,
            'components_count': len(self.components),
            'uptime': time.time() - self.stats['start_time']
        }
