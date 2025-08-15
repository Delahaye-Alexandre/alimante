"""
Service de surveillance critique (Watchdog) pour Alimante
Surveille le système et redémarre automatiquement en cas de problème
"""

import time
import threading
import logging
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..utils.gpio_manager import GPIOManager
from ..utils.logging_config import setup_logger


class AlertLevel(Enum):
    """Niveaux d'alerte du système"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class SystemAlert:
    """Structure d'une alerte système"""
    level: AlertLevel
    message: str
    timestamp: datetime
    source: str
    details: Optional[Dict] = None
    resolved: bool = False


class WatchdogService:
    """
    Service de surveillance critique du système Alimante
    
    Fonctionnalités :
    - Watchdog hardware avec GPIO
    - Monitoring CPU/RAM/température
    - Surveillance des capteurs
    - Alertes multi-niveaux
    - Redémarrage automatique
    - Historique des événements
    """
    
    def __init__(self, gpio_manager: GPIOManager, config: Dict = None):
        self.config = config or {}
        self.gpio_manager = gpio_manager
        self.logger = setup_logger("watchdog_service")
        
        # Configuration watchdog
        self.watchdog_pin = self.config.get("watchdog_pin", 18)
        self.watchdog_timeout = self.config.get("timeout_seconds", 30)
        self.max_cpu_temp = self.config.get("max_cpu_temp", 80.0)
        self.max_cpu_usage = self.config.get("max_cpu_usage", 90.0)
        self.max_memory_usage = self.config.get("max_memory_usage", 85.0)
        
        # État du système
        self.is_running = False
        self.last_heartbeat = time.time()
        self.heartbeat_thread = None
        self.monitoring_thread = None
        
        # Historique des alertes
        self.alerts: List[SystemAlert] = []
        self.max_alerts_history = self.config.get("max_alerts_history", 1000)
        
        # Callbacks d'alerte
        self.alert_callbacks: List[Callable] = []
        
        # Statistiques
        self.stats = {
            "heartbeats_sent": 0,
            "restarts_triggered": 0,
            "alerts_generated": 0,
            "last_restart": None
        }
        
        self._setup_gpio()
        self.logger.info("Service Watchdog initialisé")
    
    def _setup_gpio(self):
        """Configure le GPIO pour le watchdog hardware"""
        try:
            # Pin de sortie pour le signal de heartbeat
            self.gpio_manager.setup_pin(self.watchdog_pin, "out")
            self.gpio_manager.write_pin(self.watchdog_pin, False)
            self.logger.info(f"GPIO watchdog configuré sur pin {self.watchdog_pin}")
        except Exception as e:
            self.logger.error(f"Erreur configuration GPIO watchdog: {e}")
    
    def start(self):
        """Démarre le service watchdog"""
        if self.is_running:
            self.logger.warning("Watchdog déjà en cours d'exécution")
            return
        
        self.is_running = True
        
        # Thread de heartbeat
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, 
            daemon=True,
            name="WatchdogHeartbeat"
        )
        self.heartbeat_thread.start()
        
        # Thread de monitoring système
        self.monitoring_thread = threading.Thread(
            target=self._system_monitoring_loop,
            daemon=True,
            name="WatchdogMonitoring"
        )
        self.monitoring_thread.start()
        
        self.logger.info("Service Watchdog démarré")
    
    def stop(self):
        """Arrête le service watchdog"""
        self.is_running = False
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        
        # Désactive le signal hardware
        try:
            self.gpio_manager.write_pin(self.watchdog_pin, False)
        except:
            pass
        
        self.logger.info("Service Watchdog arrêté")
    
    def _heartbeat_loop(self):
        """Boucle principale de heartbeat pour le watchdog hardware"""
        while self.is_running:
            try:
                # Envoie un pulse au watchdog hardware
                self.gpio_manager.write_pin(self.watchdog_pin, True)
                time.sleep(0.1)  # Pulse de 100ms
                self.gpio_manager.write_pin(self.watchdog_pin, False)
                
                self.last_heartbeat = time.time()
                self.stats["heartbeats_sent"] += 1
                
                # Attendre jusqu'au prochain heartbeat
                time.sleep(self.watchdog_timeout - 0.1)
                
            except Exception as e:
                self.logger.error(f"Erreur heartbeat watchdog: {e}")
                time.sleep(1)
    
    def _system_monitoring_loop(self):
        """Boucle de surveillance du système"""
        while self.is_running:
            try:
                self._check_system_health()
                time.sleep(5)  # Vérification toutes les 5 secondes
            except Exception as e:
                self.logger.error(f"Erreur monitoring système: {e}")
                time.sleep(10)
    
    def _check_system_health(self):
        """Vérifie la santé du système"""
        try:
            # Température CPU
            cpu_temp = self._get_cpu_temperature()
            if cpu_temp and cpu_temp > self.max_cpu_temp:
                self._create_alert(
                    AlertLevel.CRITICAL,
                    f"Température CPU critique: {cpu_temp}°C",
                    "system_monitor",
                    {"cpu_temp": cpu_temp, "threshold": self.max_cpu_temp}
                )
            
            # Utilisation CPU
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > self.max_cpu_usage:
                self._create_alert(
                    AlertLevel.WARNING,
                    f"Utilisation CPU élevée: {cpu_usage}%",
                    "system_monitor",
                    {"cpu_usage": cpu_usage, "threshold": self.max_cpu_usage}
                )
            
            # Utilisation mémoire
            memory = psutil.virtual_memory()
            if memory.percent > self.max_memory_usage:
                self._create_alert(
                    AlertLevel.WARNING,
                    f"Utilisation mémoire élevée: {memory.percent}%",
                    "system_monitor",
                    {"memory_usage": memory.percent, "threshold": self.max_memory_usage}
                )
            
            # Vérification espace disque
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self._create_alert(
                    AlertLevel.WARNING,
                    f"Espace disque faible: {disk.percent}%",
                    "system_monitor",
                    {"disk_usage": disk.percent}
                )
                
        except Exception as e:
            self.logger.error(f"Erreur vérification santé système: {e}")
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """Récupère la température du CPU"""
        try:
            # Méthode 1: Fichier système
            if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp = int(f.read().strip()) / 1000.0
                    return temp
            
            # Méthode 2: Commande vcgencmd
            import subprocess
            result = subprocess.run(
                ["vcgencmd", "measure_temp"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                temp_str = result.stdout.strip()
                temp = float(temp_str.replace("temp=", "").replace("'C", ""))
                return temp
                
        except Exception as e:
            self.logger.debug(f"Impossible de lire température CPU: {e}")
        
        return None
    
    def _create_alert(self, level: AlertLevel, message: str, source: str, details: Optional[Dict] = None):
        """Crée une nouvelle alerte"""
        alert = SystemAlert(
            level=level,
            message=message,
            timestamp=datetime.now(),
            source=source,
            details=details
        )
        
        self.alerts.append(alert)
        self.stats["alerts_generated"] += 1
        
        # Limite l'historique
        if len(self.alerts) > self.max_alerts_history:
            self.alerts.pop(0)
        
        # Log selon le niveau
        if level == AlertLevel.EMERGENCY:
            self.logger.critical(f"ALERTE CRITIQUE: {message}")
        elif level == AlertLevel.CRITICAL:
            self.logger.error(f"ALERTE: {message}")
        elif level == AlertLevel.WARNING:
            self.logger.warning(f"ATTENTION: {message}")
        else:
            self.logger.info(f"INFO: {message}")
        
        # Notifie les callbacks
        self._notify_alert_callbacks(alert)
        
        # Actions automatiques selon le niveau
        if level == AlertLevel.EMERGENCY:
            self._handle_emergency_alert(alert)
    
    def _handle_emergency_alert(self, alert: SystemAlert):
        """Gère les alertes d'urgence"""
        self.logger.critical("ALERTE D'URGENCE - Redémarrage système dans 10 secondes")
        
        # Attendre un peu pour permettre la sauvegarde des logs
        time.sleep(10)
        
        try:
            # Redémarrage système
            os.system("sudo reboot")
        except Exception as e:
            self.logger.error(f"Impossible de redémarrer: {e}")
    
    def add_alert_callback(self, callback: Callable[[SystemAlert], None]):
        """Ajoute un callback pour les alertes"""
        self.alert_callbacks.append(callback)
    
    def _notify_alert_callbacks(self, alert: SystemAlert):
        """Notifie tous les callbacks d'alerte"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Erreur callback alerte: {e}")
    
    def get_system_status(self) -> Dict:
        """Retourne le statut complet du système"""
        try:
            cpu_temp = self._get_cpu_temperature()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "running" if self.is_running else "stopped",
                "last_heartbeat": self.last_heartbeat,
                "heartbeat_timeout": self.watchdog_timeout,
                "system": {
                    "cpu_temp": cpu_temp,
                    "cpu_usage": psutil.cpu_percent(interval=1),
                    "memory_usage": memory.percent,
                    "memory_available": memory.available // (1024**3),  # GB
                    "disk_usage": disk.percent,
                    "disk_free": disk.free // (1024**3),  # GB
                    "uptime": time.time() - psutil.boot_time()
                },
                "alerts": {
                    "total": len(self.alerts),
                    "unresolved": len([a for a in self.alerts if not a.resolved]),
                    "by_level": {
                        level.value: len([a for a in self.alerts if a.level == level])
                        for level in AlertLevel
                    }
                },
                "stats": self.stats
            }
        except Exception as e:
            self.logger.error(f"Erreur récupération statut: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_alerts(self, level: Optional[AlertLevel] = None, 
                   source: Optional[str] = None, 
                   limit: int = 100) -> List[SystemAlert]:
        """Récupère les alertes avec filtres"""
        filtered_alerts = self.alerts
        
        if level:
            filtered_alerts = [a for a in filtered_alerts if a.level == level]
        
        if source:
            filtered_alerts = [a for a in filtered_alerts if a.source == source]
        
        # Tri par timestamp décroissant
        filtered_alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered_alerts[:limit]
    
    def resolve_alert(self, alert_index: int):
        """Marque une alerte comme résolue"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index].resolved = True
            self.logger.info(f"Alerte résolue: {self.alerts[alert_index].message}")
    
    def clear_old_alerts(self, days: int = 7):
        """Nettoie les anciennes alertes"""
        cutoff_date = datetime.now() - timedelta(days=days)
        initial_count = len(self.alerts)
        
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff_date]
        
        removed_count = initial_count - len(self.alerts)
        if removed_count > 0:
            self.logger.info(f"Supprimé {removed_count} anciennes alertes")
    
    def trigger_manual_restart(self, reason: str = "Manuel"):
        """Déclenche un redémarrage manuel"""
        self.logger.warning(f"Redémarrage manuel déclenché: {reason}")
        self.stats["restarts_triggered"] += 1
        self.stats["last_restart"] = datetime.now()
        
        # Créer une alerte
        self._create_alert(
            AlertLevel.WARNING,
            f"Redémarrage manuel: {reason}",
            "manual_trigger"
        )
        
        # Redémarrage dans 5 secondes
        time.sleep(5)
        os.system("sudo reboot")
    
    def cleanup(self):
        """Nettoyage du service"""
        self.stop()
        self.logger.info("Service Watchdog nettoyé")
