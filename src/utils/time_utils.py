"""
Utilitaires de gestion du temps pour Alimante
Fonctions pour la gestion des horaires, photopériodes, etc.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import math

class TimeUtils:
    """
    Utilitaires de gestion du temps
    """
    
    @staticmethod
    def get_current_time() -> Dict[str, Any]:
        """
        Retourne l'heure actuelle sous différents formats
        
        Returns:
            Dictionnaire avec l'heure actuelle
        """
        try:
            now = datetime.now()
            timestamp = time.time()
            
            return {
                'timestamp': timestamp,
                'datetime': now,
                'hour': now.hour,
                'minute': now.minute,
                'second': now.second,
                'day': now.day,
                'month': now.month,
                'year': now.year,
                'weekday': now.weekday(),
                'isoweekday': now.isoweekday(),
                'strftime': now.strftime('%Y-%m-%d %H:%M:%S'),
                'iso': now.isoformat()
            }
            
        except Exception as e:
            logging.error(f"Erreur récupération heure: {e}")
            return {}
    
    @staticmethod
    def is_daytime(hour: int, day_start: int = 6, day_end: int = 18) -> bool:
        """
        Détermine si c'est le jour ou la nuit
        
        Args:
            hour: Heure actuelle (0-23)
            day_start: Heure de début du jour
            day_end: Heure de fin du jour
            
        Returns:
            True si c'est le jour, False sinon
        """
        try:
            if day_start <= day_end:
                return day_start <= hour < day_end
            else:
                # Jour qui traverse minuit (ex: 22h-6h)
                return hour >= day_start or hour < day_end
                
        except Exception as e:
            logging.error(f"Erreur détermination jour/nuit: {e}")
            return True
    
    @staticmethod
    def calculate_lighting_intensity(hour: int, day_start: int = 6, day_end: int = 18,
                                   max_intensity: int = 100, min_intensity: int = 0,
                                   fade_duration: int = 30) -> int:
        """
        Calcule l'intensité d'éclairage selon l'heure
        
        Args:
            hour: Heure actuelle (0-23)
            day_start: Heure de début du jour
            day_end: Heure de fin du jour
            max_intensity: Intensité maximale
            min_intensity: Intensité minimale
            fade_duration: Durée de transition en minutes
            
        Returns:
            Intensité d'éclairage (0-100)
        """
        try:
            if TimeUtils.is_daytime(hour, day_start, day_end):
                # Période de jour
                return max_intensity
            else:
                # Période de nuit
                return min_intensity
                
        except Exception as e:
            logging.error(f"Erreur calcul intensité éclairage: {e}")
            return min_intensity
    
    @staticmethod
    def calculate_photoperiod_intensity(hour: int, minute: int = 0,
                                      day_start: int = 6, day_end: int = 18,
                                      max_intensity: int = 100, min_intensity: int = 0,
                                      sunrise_duration: int = 30, sunset_duration: int = 30) -> int:
        """
        Calcule l'intensité d'éclairage avec transitions douces (lever/coucher du soleil)
        
        Args:
            hour: Heure actuelle (0-23)
            minute: Minute actuelle (0-59)
            day_start: Heure de début du jour
            day_end: Heure de fin du jour
            max_intensity: Intensité maximale
            min_intensity: Intensité minimale
            sunrise_duration: Durée du lever du soleil en minutes
            sunset_duration: Durée du coucher du soleil en minutes
            
        Returns:
            Intensité d'éclairage (0-100)
        """
        try:
            current_minutes = hour * 60 + minute
            day_start_minutes = day_start * 60
            day_end_minutes = day_end * 60
            
            # Lever du soleil
            sunrise_start = day_start_minutes - sunrise_duration
            sunrise_end = day_start_minutes
            
            # Coucher du soleil
            sunset_start = day_end_minutes - sunset_duration
            sunset_end = day_end_minutes
            
            if current_minutes < sunrise_start:
                # Nuit
                return min_intensity
            elif sunrise_start <= current_minutes < sunrise_end:
                # Lever du soleil
                progress = (current_minutes - sunrise_start) / sunrise_duration
                return int(min_intensity + (max_intensity - min_intensity) * progress)
            elif sunrise_end <= current_minutes < sunset_start:
                # Jour
                return max_intensity
            elif sunset_start <= current_minutes < sunset_end:
                # Coucher du soleil
                progress = (current_minutes - sunset_start) / sunset_duration
                return int(max_intensity - (max_intensity - min_intensity) * progress)
            else:
                # Nuit
                return min_intensity
                
        except Exception as e:
            logging.error(f"Erreur calcul photopériode: {e}")
            return min_intensity
    
    @staticmethod
    def get_feeding_times(species_profile: Dict[str, Any]) -> List[int]:
        """
        Récupère les horaires d'alimentation d'une espèce
        
        Args:
            species_profile: Profil de l'espèce
            
        Returns:
            Liste des heures d'alimentation
        """
        try:
            feeding_config = species_profile.get('feeding', {})
            schedule = feeding_config.get('schedule', [])
            
            feeding_times = []
            for feeding in schedule:
                if isinstance(feeding, dict):
                    hour = feeding.get('hour')
                    if hour is not None:
                        feeding_times.append(hour)
                elif isinstance(feeding, int):
                    feeding_times.append(feeding)
            
            return sorted(feeding_times)
            
        except Exception as e:
            logging.error(f"Erreur récupération horaires alimentation: {e}")
            return []
    
    @staticmethod
    def should_feed_now(species_profile: Dict[str, Any], current_hour: int) -> bool:
        """
        Détermine si l'alimentation doit avoir lieu maintenant
        
        Args:
            species_profile: Profil de l'espèce
            current_hour: Heure actuelle
            
        Returns:
            True si l'alimentation doit avoir lieu
        """
        try:
            feeding_times = TimeUtils.get_feeding_times(species_profile)
            return current_hour in feeding_times
            
        except Exception as e:
            logging.error(f"Erreur vérification alimentation: {e}")
            return False
    
    @staticmethod
    def get_next_feeding_time(species_profile: Dict[str, Any], current_hour: int) -> Optional[int]:
        """
        Retourne la prochaine heure d'alimentation
        
        Args:
            species_profile: Profil de l'espèce
            current_hour: Heure actuelle
            
        Returns:
            Prochaine heure d'alimentation ou None
        """
        try:
            feeding_times = TimeUtils.get_feeding_times(species_profile)
            
            if not feeding_times:
                return None
            
            # Chercher la prochaine heure d'alimentation
            for feeding_hour in feeding_times:
                if feeding_hour > current_hour:
                    return feeding_hour
            
            # Si pas trouvé, retourner la première de demain
            return feeding_times[0]
            
        except Exception as e:
            logging.error(f"Erreur prochaine alimentation: {e}")
            return None
    
    @staticmethod
    def calculate_uptime(start_time: float) -> Dict[str, Any]:
        """
        Calcule le temps de fonctionnement
        
        Args:
            start_time: Timestamp de début
            
        Returns:
            Dictionnaire avec le temps de fonctionnement
        """
        try:
            current_time = time.time()
            uptime_seconds = current_time - start_time
            
            uptime_delta = timedelta(seconds=int(uptime_seconds))
            
            return {
                'seconds': int(uptime_seconds),
                'minutes': int(uptime_seconds / 60),
                'hours': int(uptime_seconds / 3600),
                'days': uptime_delta.days,
                'formatted': str(uptime_delta),
                'human_readable': TimeUtils._format_uptime(uptime_seconds)
            }
            
        except Exception as e:
            logging.error(f"Erreur calcul uptime: {e}")
            return {'seconds': 0, 'minutes': 0, 'hours': 0, 'days': 0, 'formatted': '0:00:00', 'human_readable': '0 secondes'}
    
    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """
        Formate le temps de fonctionnement en format lisible
        
        Args:
            seconds: Nombre de secondes
            
        Returns:
            Temps formaté
        """
        try:
            if seconds < 60:
                return f"{int(seconds)} seconde{'s' if seconds != 1 else ''}"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''}"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                minutes = int((seconds % 3600) / 60)
                return f"{hours}h {minutes}m"
            else:
                days = int(seconds / 86400)
                hours = int((seconds % 86400) / 3600)
                return f"{days} jour{'s' if days != 1 else ''} {hours}h"
                
        except Exception as e:
            logging.error(f"Erreur formatage uptime: {e}")
            return "0 secondes"
    
    @staticmethod
    def is_weekend() -> bool:
        """
        Détermine si c'est le weekend
        
        Returns:
            True si c'est le weekend, False sinon
        """
        try:
            weekday = datetime.now().weekday()
            return weekday >= 5  # Samedi = 5, Dimanche = 6
            
        except Exception as e:
            logging.error(f"Erreur vérification weekend: {e}")
            return False
    
    @staticmethod
    def get_time_until_next_hour() -> int:
        """
        Retourne le nombre de minutes jusqu'à la prochaine heure
        
        Returns:
            Minutes jusqu'à la prochaine heure
        """
        try:
            now = datetime.now()
            next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            delta = next_hour - now
            return int(delta.total_seconds() / 60)
            
        except Exception as e:
            logging.error(f"Erreur calcul prochaine heure: {e}")
            return 60
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Formate une durée en format lisible
        
        Args:
            seconds: Durée en secondes
            
        Returns:
            Durée formatée
        """
        try:
            if seconds < 60:
                return f"{int(seconds)}s"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                remaining_seconds = int(seconds % 60)
                return f"{minutes}m {remaining_seconds}s"
            else:
                hours = int(seconds / 3600)
                minutes = int((seconds % 3600) / 60)
                return f"{hours}h {minutes}m"
                
        except Exception as e:
            logging.error(f"Erreur formatage durée: {e}")
            return "0s"

