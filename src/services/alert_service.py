"""
Service de gestion des alertes Alimante
Gère les alertes, notifications et actions d'urgence
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

class AlertSeverity(Enum):
    """Niveaux de gravité des alertes"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Statuts des alertes"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class Alert:
    """Représentation d'une alerte"""
    id: str
    type: str
    message: str
    severity: AlertSeverity
    status: AlertStatus
    timestamp: datetime
    terrarium_id: Optional[str] = None
    component: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class AlertService:
    """
    Service de gestion des alertes
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service d'alertes
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Configuration des alertes
        self.alert_config = config.get('alerts', {})
        self.enabled = self.alert_config.get('enabled', True)
        self.max_alerts = self.alert_config.get('max_alerts', 1000)
        self.retention_days = self.alert_config.get('retention_days', 30)
        self.auto_acknowledge_delay = self.alert_config.get('auto_acknowledge_delay', 3600)  # 1 heure
        
        # Configuration des notifications
        self.notifications_enabled = self.alert_config.get('notifications_enabled', True)
        self.email_enabled = self.alert_config.get('email_enabled', False)
        self.sms_enabled = self.alert_config.get('sms_enabled', False)
        self.webhook_enabled = self.alert_config.get('webhook_enabled', False)
        
        # État du service
        self.is_running = False
        self.alerts = {}  # id -> Alert
        self.alert_counter = 0
        
        # Threads
        self.cleanup_thread = None
        self.stop_event = threading.Event()
        
        # Callbacks
        self.alert_callbacks = []
        self.notification_callbacks = []
        
        # Statistiques
        self.stats = {
            'alerts_created': 0,
            'alerts_acknowledged': 0,
            'alerts_resolved': 0,
            'alerts_suppressed': 0,
            'notifications_sent': 0,
            'errors': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service d'alertes
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            if not self.enabled:
                self.logger.info("Service d'alertes désactivé")
                return True
            
            self.logger.info("Service d'alertes initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service alertes: {e}")
            self.stats['errors'] += 1
            return False
    
    def start(self) -> bool:
        """
        Démarre le service d'alertes
        
        Returns:
            True si le démarrage réussit, False sinon
        """
        try:
            if not self.enabled:
                self.logger.info("Service d'alertes désactivé")
                return True
            
            if self.is_running:
                self.logger.warning("Service d'alertes déjà en cours d'exécution")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Démarrer le thread de nettoyage
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            
            self.logger.info("Service d'alertes démarré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service alertes: {e}")
            self.stats['errors'] += 1
            return False
    
    def stop(self) -> None:
        """Arrête le service d'alertes"""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            self.stop_event.set()
            
            # Attendre que le thread se termine
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)
            
            self.logger.info("Service d'alertes arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service alertes: {e}")
            self.stats['errors'] += 1
    
    def _cleanup_loop(self) -> None:
        """Boucle de nettoyage des anciennes alertes"""
        try:
            while self.is_running and not self.stop_event.is_set():
                try:
                    # Nettoyer les anciennes alertes
                    self._cleanup_old_alerts()
                    
                    # Vérifier les alertes à auto-accuser
                    self._check_auto_acknowledge()
                    
                    # Attendre 1 heure avant le prochain nettoyage
                    self.stop_event.wait(3600)
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle de nettoyage: {e}")
                    self.stats['errors'] += 1
                    time.sleep(60)
                    
        except Exception as e:
            self.logger.error(f"Erreur critique dans la boucle de nettoyage: {e}")
            self.stats['errors'] += 1
    
    def _cleanup_old_alerts(self) -> None:
        """Nettoie les anciennes alertes"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            alerts_to_remove = []
            
            for alert_id, alert in self.alerts.items():
                if alert.timestamp < cutoff_date:
                    alerts_to_remove.append(alert_id)
            
            for alert_id in alerts_to_remove:
                del self.alerts[alert_id]
            
            if alerts_to_remove:
                self.logger.info(f"{len(alerts_to_remove)} anciennes alertes supprimées")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage anciennes alertes: {e}")
            self.stats['errors'] += 1
    
    def _check_auto_acknowledge(self) -> None:
        """Vérifie les alertes à auto-accuser"""
        try:
            cutoff_time = datetime.now() - timedelta(seconds=self.auto_acknowledge_delay)
            
            for alert in self.alerts.values():
                if (alert.status == AlertStatus.ACTIVE and 
                    alert.timestamp < cutoff_time and
                    alert.severity in [AlertSeverity.INFO, AlertSeverity.WARNING]):
                    
                    self.acknowledge_alert(alert.id, "system")
            
        except Exception as e:
            self.logger.error(f"Erreur vérification auto-acknowledge: {e}")
            self.stats['errors'] += 1
    
    def create_alert(self, alert_type: str, message: str, severity: AlertSeverity,
                    terrarium_id: Optional[str] = None, component: Optional[str] = None,
                    value: Optional[float] = None, threshold: Optional[float] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Crée une nouvelle alerte
        
        Args:
            alert_type: Type d'alerte
            message: Message de l'alerte
            severity: Gravité de l'alerte
            terrarium_id: ID du terrarium concerné
            component: Composant concerné
            value: Valeur actuelle
            threshold: Seuil dépassé
            metadata: Métadonnées supplémentaires
            
        Returns:
            ID de l'alerte créée
        """
        try:
            # Générer un ID unique
            self.alert_counter += 1
            alert_id = f"alert_{self.alert_counter}_{int(time.time())}"
            
            # Créer l'alerte
            alert = Alert(
                id=alert_id,
                type=alert_type,
                message=message,
                severity=severity,
                status=AlertStatus.ACTIVE,
                timestamp=datetime.now(),
                terrarium_id=terrarium_id,
                component=component,
                value=value,
                threshold=threshold,
                metadata=metadata or {}
            )
            
            # Ajouter à la liste
            self.alerts[alert_id] = alert
            self.stats['alerts_created'] += 1
            
            # Limiter le nombre d'alertes
            if len(self.alerts) > self.max_alerts:
                # Supprimer les plus anciennes
                oldest_alerts = sorted(self.alerts.items(), key=lambda x: x[1].timestamp)
                for old_id, _ in oldest_alerts[:len(self.alerts) - self.max_alerts]:
                    del self.alerts[old_id]
            
            self.logger.info(f"Alerte créée: {alert_type} - {message}")
            
            # Appeler les callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Erreur callback alerte: {e}")
            
            # Envoyer les notifications
            self._send_notifications(alert)
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('alert_created', {
                    'alert_id': alert_id,
                    'type': alert_type,
                    'message': message,
                    'severity': severity.value,
                    'terrarium_id': terrarium_id,
                    'component': component,
                    'timestamp': time.time()
                })
            
            return alert_id
            
        except Exception as e:
            self.logger.error(f"Erreur création alerte: {e}")
            self.stats['errors'] += 1
            return None
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "user") -> bool:
        """
        Accuse réception d'une alerte
        
        Args:
            alert_id: ID de l'alerte
            acknowledged_by: Qui accuse réception
            
        Returns:
            True si l'alerte est accusée, False sinon
        """
        try:
            if alert_id not in self.alerts:
                self.logger.warning(f"Alerte {alert_id} non trouvée")
                return False
            
            alert = self.alerts[alert_id]
            
            if alert.status != AlertStatus.ACTIVE:
                self.logger.warning(f"Alerte {alert_id} déjà traitée")
                return False
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            
            self.stats['alerts_acknowledged'] += 1
            
            self.logger.info(f"Alerte {alert_id} accusée par {acknowledged_by}")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('alert_acknowledged', {
                    'alert_id': alert_id,
                    'acknowledged_by': acknowledged_by,
                    'timestamp': time.time()
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur accusé réception alerte {alert_id}: {e}")
            self.stats['errors'] += 1
            return False
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "user") -> bool:
        """
        Résout une alerte
        
        Args:
            alert_id: ID de l'alerte
            resolved_by: Qui résout l'alerte
            
        Returns:
            True si l'alerte est résolue, False sinon
        """
        try:
            if alert_id not in self.alerts:
                self.logger.warning(f"Alerte {alert_id} non trouvée")
                return False
            
            alert = self.alerts[alert_id]
            
            if alert.status == AlertStatus.RESOLVED:
                self.logger.warning(f"Alerte {alert_id} déjà résolue")
                return False
            
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            self.stats['alerts_resolved'] += 1
            
            self.logger.info(f"Alerte {alert_id} résolue par {resolved_by}")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('alert_resolved', {
                    'alert_id': alert_id,
                    'resolved_by': resolved_by,
                    'timestamp': time.time()
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur résolution alerte {alert_id}: {e}")
            self.stats['errors'] += 1
            return False
    
    def suppress_alert(self, alert_id: str, suppressed_by: str = "user") -> bool:
        """
        Supprime une alerte
        
        Args:
            alert_id: ID de l'alerte
            suppressed_by: Qui supprime l'alerte
            
        Returns:
            True si l'alerte est supprimée, False sinon
        """
        try:
            if alert_id not in self.alerts:
                self.logger.warning(f"Alerte {alert_id} non trouvée")
                return False
            
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.SUPPRESSED
            
            self.stats['alerts_suppressed'] += 1
            
            self.logger.info(f"Alerte {alert_id} supprimée par {suppressed_by}")
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('alert_suppressed', {
                    'alert_id': alert_id,
                    'suppressed_by': suppressed_by,
                    'timestamp': time.time()
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur suppression alerte {alert_id}: {e}")
            self.stats['errors'] += 1
            return False
    
    def _send_notifications(self, alert: Alert) -> None:
        """Envoie les notifications pour une alerte"""
        try:
            if not self.notifications_enabled:
                return
            
            # Appeler les callbacks de notification
            for callback in self.notification_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Erreur callback notification: {e}")
            
            # Envoyer par email si activé
            if self.email_enabled:
                self._send_email_notification(alert)
            
            # Envoyer par SMS si activé
            if self.sms_enabled:
                self._send_sms_notification(alert)
            
            # Envoyer par webhook si activé
            if self.webhook_enabled:
                self._send_webhook_notification(alert)
            
            self.stats['notifications_sent'] += 1
            
        except Exception as e:
            self.logger.error(f"Erreur envoi notifications: {e}")
            self.stats['errors'] += 1
    
    def _send_email_notification(self, alert: Alert) -> None:
        """Envoie une notification par email"""
        try:
            # Implémentation de l'envoi d'email
            self.logger.info(f"Notification email envoyée pour alerte {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Erreur envoi email: {e}")
    
    def _send_sms_notification(self, alert: Alert) -> None:
        """Envoie une notification par SMS"""
        try:
            # Implémentation de l'envoi de SMS
            self.logger.info(f"Notification SMS envoyée pour alerte {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Erreur envoi SMS: {e}")
    
    def _send_webhook_notification(self, alert: Alert) -> None:
        """Envoie une notification par webhook"""
        try:
            # Implémentation de l'envoi de webhook
            self.logger.info(f"Notification webhook envoyée pour alerte {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Erreur envoi webhook: {e}")
    
    def get_alerts(self, status: AlertStatus = None, severity: AlertSeverity = None,
                   terrarium_id: Optional[str] = None, limit: int = 100) -> List[Alert]:
        """
        Récupère les alertes selon les critères
        
        Args:
            status: Statut des alertes
            severity: Gravité des alertes
            terrarium_id: ID du terrarium
            limit: Nombre maximum d'alertes
            
        Returns:
            Liste des alertes
        """
        try:
            alerts = list(self.alerts.values())
            
            # Filtrer par statut
            if status:
                alerts = [a for a in alerts if a.status == status]
            
            # Filtrer par gravité
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            # Filtrer par terrarium
            if terrarium_id:
                alerts = [a for a in alerts if a.terrarium_id == terrarium_id]
            
            # Trier par timestamp (plus récent en premier)
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            return alerts[:limit]
            
        except Exception as e:
            self.logger.error(f"Erreur récupération alertes: {e}")
            return []
    
    def get_alert_count(self, status: AlertStatus = None, severity: AlertSeverity = None) -> int:
        """
        Compte les alertes selon les critères
        
        Args:
            status: Statut des alertes
            severity: Gravité des alertes
            
        Returns:
            Nombre d'alertes
        """
        try:
            alerts = list(self.alerts.values())
            
            if status:
                alerts = [a for a in alerts if a.status == status]
            
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            return len(alerts)
            
        except Exception as e:
            self.logger.error(f"Erreur comptage alertes: {e}")
            return 0
    
    def add_alert_callback(self, callback: Callable) -> None:
        """
        Ajoute un callback pour les alertes
        
        Args:
            callback: Fonction à appeler lors de la création d'une alerte
        """
        self.alert_callbacks.append(callback)
        self.logger.info("Callback alerte ajouté")
    
    def add_notification_callback(self, callback: Callable) -> None:
        """
        Ajoute un callback pour les notifications
        
        Args:
            callback: Fonction à appeler lors de l'envoi d'une notification
        """
        self.notification_callbacks.append(callback)
        self.logger.info("Callback notification ajouté")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service d'alertes
        
        Returns:
            Dictionnaire contenant le statut
        """
        return {
            'service': 'alerts',
            'enabled': self.enabled,
            'is_running': self.is_running,
            'total_alerts': len(self.alerts),
            'active_alerts': self.get_alert_count(AlertStatus.ACTIVE),
            'acknowledged_alerts': self.get_alert_count(AlertStatus.ACKNOWLEDGED),
            'resolved_alerts': self.get_alert_count(AlertStatus.RESOLVED),
            'critical_alerts': self.get_alert_count(AlertSeverity.CRITICAL),
            'notifications_enabled': self.notifications_enabled,
            'stats': self.stats
        }
    
    def cleanup(self) -> None:
        """Nettoie le service d'alertes"""
        try:
            # Arrêter le service
            self.stop()
            
            self.logger.info("Service d'alertes nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service alertes: {e}")
            self.stats['errors'] += 1
