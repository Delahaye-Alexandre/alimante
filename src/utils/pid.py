"""
Contrôleur PID pour Alimante
Implémentation d'un contrôleur PID pour la régulation des paramètres
"""

import time
import logging
from typing import Dict, Any, Optional

class PIDController:
    """
    Contrôleur PID (Proportionnel, Intégral, Dérivé)
    """
    
    def __init__(self, kp: float = 1.0, ki: float = 0.0, kd: float = 0.0, 
                 setpoint: float = 0.0, output_limits: Optional[tuple] = None):
        """
        Initialise le contrôleur PID
        
        Args:
            kp: Gain proportionnel
            ki: Gain intégral
            kd: Gain dérivé
            setpoint: Consigne
            output_limits: Limites de sortie (min, max)
        """
        self.logger = logging.getLogger(__name__)
        
        # Paramètres PID
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        # Consigne
        self.setpoint = setpoint
        
        # Limites de sortie
        self.output_limits = output_limits
        
        # Variables internes
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = None
        
        # Statistiques
        self.stats = {
            'output_calculations': 0,
            'integral_windup_count': 0,
            'output_limited_count': 0,
            'last_output': 0.0
        }
        
    def set_setpoint(self, setpoint: float) -> None:
        """
        Définit la consigne
        
        Args:
            setpoint: Nouvelle consigne
        """
        self.setpoint = setpoint
        self.logger.debug(f"Consigne définie: {setpoint}")
    
    def set_parameters(self, kp: float, ki: float, kd: float) -> None:
        """
        Définit les paramètres PID
        
        Args:
            kp: Gain proportionnel
            ki: Gain intégral
            kd: Gain dérivé
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.logger.debug(f"Paramètres PID définis: Kp={kp}, Ki={ki}, Kd={kd}")
    
    def set_output_limits(self, limits: tuple) -> None:
        """
        Définit les limites de sortie
        
        Args:
            limits: Tuple (min, max)
        """
        self.output_limits = limits
        self.logger.debug(f"Limites de sortie définies: {limits}")
    
    def calculate(self, current_value: float) -> float:
        """
        Calcule la sortie du contrôleur PID
        
        Args:
            current_value: Valeur actuelle
            
        Returns:
            Sortie du contrôleur
        """
        try:
            current_time = time.time()
            
            # Calcul de l'erreur
            error = self.setpoint - current_value
            
            # Calcul du terme proportionnel
            p_term = self.kp * error
            
            # Calcul du terme intégral
            if self.last_time is not None:
                dt = current_time - self.last_time
                if dt > 0:
                    self.integral += error * dt
                    
                    # Anti-windup
                    if self.output_limits:
                        max_integral = (self.output_limits[1] - p_term) / self.ki if self.ki != 0 else 0
                        min_integral = (self.output_limits[0] - p_term) / self.ki if self.ki != 0 else 0
                        
                        if self.integral > max_integral:
                            self.integral = max_integral
                            self.stats['integral_windup_count'] += 1
                        elif self.integral < min_integral:
                            self.integral = min_integral
                            self.stats['integral_windup_count'] += 1
            
            i_term = self.ki * self.integral
            
            # Calcul du terme dérivé
            if self.last_time is not None and self.last_time > 0:
                dt = current_time - self.last_time
                if dt > 0:
                    d_term = self.kd * (error - self.last_error) / dt
                else:
                    d_term = 0
            else:
                d_term = 0
            
            # Calcul de la sortie
            output = p_term + i_term + d_term
            
            # Application des limites
            if self.output_limits:
                if output > self.output_limits[1]:
                    output = self.output_limits[1]
                    self.stats['output_limited_count'] += 1
                elif output < self.output_limits[0]:
                    output = self.output_limits[0]
                    self.stats['output_limited_count'] += 1
            
            # Mise à jour des variables
            self.last_error = error
            self.last_time = current_time
            self.stats['output_calculations'] += 1
            self.stats['last_output'] = output
            
            self.logger.debug(f"PID: erreur={error:.2f}, P={p_term:.2f}, I={i_term:.2f}, D={d_term:.2f}, sortie={output:.2f}")
            
            return output
            
        except Exception as e:
            self.logger.error(f"Erreur calcul PID: {e}")
            return 0.0
    
    def reset(self) -> None:
        """Remet à zéro le contrôleur PID"""
        try:
            self.last_error = 0.0
            self.integral = 0.0
            self.last_time = None
            self.stats['last_output'] = 0.0
            
            self.logger.debug("Contrôleur PID réinitialisé")
            
        except Exception as e:
            self.logger.error(f"Erreur réinitialisation PID: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du contrôleur PID
        
        Returns:
            Dictionnaire du statut
        """
        return {
            'kp': self.kp,
            'ki': self.ki,
            'kd': self.kd,
            'setpoint': self.setpoint,
            'output_limits': self.output_limits,
            'last_error': self.last_error,
            'integral': self.integral,
            'stats': self.stats.copy()
        }
    
    def tune_parameters(self, method: str = 'ziegler_nichols', 
                       ku: float = 1.0, tu: float = 1.0) -> None:
        """
        Ajuste automatiquement les paramètres PID
        
        Args:
            method: Méthode d'ajustement ('ziegler_nichols', 'cohen_coon')
            ku: Gain critique (méthode Ziegler-Nichols)
            tu: Période d'oscillation (méthode Ziegler-Nichols)
        """
        try:
            if method == 'ziegler_nichols':
                # Méthode Ziegler-Nichols
                self.kp = 0.6 * ku
                self.ki = 1.2 * ku / tu
                self.kd = 0.075 * ku * tu
                
            elif method == 'cohen_coon':
                # Méthode Cohen-Coon (approximation)
                self.kp = 0.9 * ku
                self.ki = 1.2 * ku / tu
                self.kd = 0.075 * ku * tu
                
            else:
                self.logger.warning(f"Méthode d'ajustement inconnue: {method}")
                return
            
            self.logger.info(f"Paramètres PID ajustés ({method}): Kp={self.kp:.3f}, Ki={self.ki:.3f}, Kd={self.kd:.3f}")
            
        except Exception as e:
            self.logger.error(f"Erreur ajustement paramètres PID: {e}")


class TemperaturePID(PIDController):
    """
    Contrôleur PID spécialisé pour la température
    """
    
    def __init__(self, setpoint: float = 25.0):
        """
        Initialise le contrôleur PID de température
        
        Args:
            setpoint: Température cible en °C
        """
        # Paramètres optimisés pour la température
        super().__init__(
            kp=2.0,      # Gain proportionnel
            ki=0.1,      # Gain intégral
            kd=0.5,      # Gain dérivé
            setpoint=setpoint,
            output_limits=(0.0, 100.0)  # 0-100% de puissance
        )
        
        self.logger.info(f"Contrôleur PID température initialisé (consigne: {setpoint}°C)")


class HumidityPID(PIDController):
    """
    Contrôleur PID spécialisé pour l'humidité
    """
    
    def __init__(self, setpoint: float = 60.0):
        """
        Initialise le contrôleur PID d'humidité
        
        Args:
            setpoint: Humidité cible en %
        """
        # Paramètres optimisés pour l'humidité
        super().__init__(
            kp=1.5,      # Gain proportionnel
            ki=0.05,     # Gain intégral
            kd=0.2,      # Gain dérivé
            setpoint=setpoint,
            output_limits=(0.0, 100.0)  # 0-100% de puissance
        )
        
        self.logger.info(f"Contrôleur PID humidité initialisé (consigne: {setpoint}%)")

