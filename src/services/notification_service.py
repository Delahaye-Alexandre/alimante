"""
Service de notifications multi-canaux pour Alimante
Gère l'envoi de notifications via email, SMS, webhook et notifications push
"""

import logging
import smtplib
import json
import requests
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import os
import re

from ..utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory

class NotificationChannel(Enum):
    """Canaux de notification"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    LOG = "log"

class NotificationPriority(Enum):
    """Priorités de notification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationStatus(Enum):
    """Statuts de notification"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class NotificationTemplate:
    """Template de notification"""
    name: str
    subject: str
    body: str
    channels: List[NotificationChannel]
    priority: NotificationPriority
    variables: List[str]

@dataclass
class Notification:
    """Notification à envoyer"""
    id: str
    template: str
    recipient: str
    channel: NotificationChannel
    priority: NotificationPriority
    status: NotificationStatus
    subject: str
    body: str
    created_at: datetime
    sent_at: Optional[datetime]
    retry_count: int
    max_retries: int
    metadata: Dict[str, Any]

class NotificationService:
    """
    Service de notifications multi-canaux
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        
        # Configuration des canaux
        self.email_config = config.get('email', {})
        self.sms_config = config.get('sms', {})
        self.webhook_config = config.get('webhook', {})
        self.push_config = config.get('push', {})
        
        # Configuration générale
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 60)  # secondes
        self.batch_size = config.get('batch_size', 10)
        self.queue_size = config.get('queue_size', 1000)
        
        # Queue de notifications
        self.notification_queue: List[Notification] = []
        self.sent_notifications: List[Notification] = []
        
        # Templates de notifications
        self.templates: Dict[str, NotificationTemplate] = {}
        
        # Threads de traitement
        self.processing_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Statistiques
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'by_channel': {channel.value: 0 for channel in NotificationChannel},
            'by_priority': {priority.value: 0 for priority in NotificationPriority}
        }
        
        self.logger.info("Service de notifications initialisé")
    
    def initialize(self) -> bool:
        """Initialise le service de notifications"""
        try:
            self.logger.info("Initialisation du service de notifications...")
            
            # Créer le répertoire de données si nécessaire
            os.makedirs('data/notifications', exist_ok=True)
            
            # Charger les templates par défaut
            self._load_default_templates()
            
            # Charger les templates personnalisés
            self._load_custom_templates()
            
            # Démarrer le thread de traitement
            self.running = True
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                name="NotificationProcessingThread",
                daemon=True
            )
            self.processing_thread.start()
            
            self.logger.info("Service de notifications initialisé avec succès")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "initialize",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def start(self) -> bool:
        """Démarre le service de notifications"""
        return True  # Déjà démarré dans initialize
    
    def stop(self) -> bool:
        """Arrête le service de notifications"""
        try:
            self.running = False
            
            # Attendre que le thread se termine
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5.0)
            
            # Traiter les notifications restantes
            self._process_remaining_notifications()
            
            self.logger.info("Service de notifications arrêté")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "stop",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
    
    def _load_default_templates(self):
        """Charge les templates de notifications par défaut"""
        try:
            # Template d'alerte système
            self.templates['system_alert'] = NotificationTemplate(
                name='system_alert',
                subject='🚨 Alerte Système Alimante',
                body='''Alerte système détectée :

Type : {alert_type}
Composant : {component}
Message : {message}
Timestamp : {timestamp}

Veuillez vérifier le système.
''',
                channels=[NotificationChannel.EMAIL, NotificationChannel.LOG],
                priority=NotificationPriority.HIGH,
                variables=['alert_type', 'component', 'message', 'timestamp']
            )
            
            # Template d'erreur critique
            self.templates['critical_error'] = NotificationTemplate(
                name='critical_error',
                subject='💥 Erreur Critique Alimante',
                body='''ERREUR CRITIQUE DÉTECTÉE !

Composant : {component}
Fonction : {function}
Erreur : {error_message}
Timestamp : {timestamp}

Action immédiate requise !
''',
                channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.LOG],
                priority=NotificationPriority.CRITICAL,
                variables=['component', 'function', 'error_message', 'timestamp']
            )
            
            # Template de récupération réussie
            self.templates['recovery_success'] = NotificationTemplate(
                name='recovery_success',
                subject='✅ Récupération Réussie Alimante',
                body='''Récupération automatique réussie :

Composant : {component}
Stratégie : {strategy}
Durée : {duration}
Timestamp : {timestamp}

Le système est de nouveau opérationnel.
''',
                channels=[NotificationChannel.EMAIL, NotificationChannel.LOG],
                priority=NotificationPriority.MEDIUM,
                variables=['component', 'strategy', 'duration', 'timestamp']
            )
            
            # Template de rapport quotidien
            self.templates['daily_report'] = NotificationTemplate(
                name='daily_report',
                subject='📊 Rapport Quotidien Alimante',
                body='''Rapport quotidien du système :

Période : {date}
Terrariums actifs : {active_terrariums}
Erreurs : {error_count}
Alertes : {alert_count}
Santé globale : {health_status}

Détails complets disponibles dans l'interface web.
''',
                channels=[NotificationChannel.EMAIL, NotificationChannel.LOG],
                priority=NotificationPriority.LOW,
                variables=['date', 'active_terrariums', 'error_count', 'alert_count', 'health_status']
            )
            
            # Template de maintenance
            self.templates['maintenance'] = NotificationTemplate(
                name='maintenance',
                subject='🔧 Maintenance Alimante',
                body='''Maintenance programmée :

Type : {maintenance_type}
Début : {start_time}
Durée estimée : {duration}
Description : {description}

Le système sera temporairement indisponible.
''',
                channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.LOG],
                priority=NotificationPriority.MEDIUM,
                variables=['maintenance_type', 'start_time', 'duration', 'description']
            )
            
            self.logger.info(f"Chargé {len(self.templates)} templates par défaut")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_load_default_templates",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _load_custom_templates(self):
        """Charge les templates personnalisés"""
        try:
            templates_file = 'data/notifications/templates.json'
            if os.path.exists(templates_file):
                with open(templates_file, 'r') as f:
                    data = json.load(f)
                
                for template_name, template_data in data.items():
                    template = NotificationTemplate(
                        name=template_data['name'],
                        subject=template_data['subject'],
                        body=template_data['body'],
                        channels=[NotificationChannel(ch) for ch in template_data['channels']],
                        priority=NotificationPriority(template_data['priority']),
                        variables=template_data['variables']
                    )
                    self.templates[template_name] = template
                
                self.logger.info(f"Chargé {len(data)} templates personnalisés")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_load_custom_templates",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
    
    def send_notification(self, 
                         template_name: str, 
                         recipient: str, 
                         variables: Dict[str, Any],
                         channels: Optional[List[NotificationChannel]] = None,
                         priority: Optional[NotificationPriority] = None) -> bool:
        """
        Envoie une notification
        
        Args:
            template_name: Nom du template
            recipient: Destinataire
            variables: Variables à remplacer dans le template
            channels: Canaux à utiliser (optionnel)
            priority: Priorité (optionnel)
        
        Returns:
            bool: Succès de l'ajout à la queue
        """
        try:
            if template_name not in self.templates:
                self.logger.error(f"Template non trouvé: {template_name}")
                return False
            
            template = self.templates[template_name]
            
            # Utiliser les canaux du template si non spécifiés
            if channels is None:
                channels = template.channels
            
            # Utiliser la priorité du template si non spécifiée
            if priority is None:
                priority = template.priority
            
            # Remplacer les variables dans le sujet et le corps
            subject = self._replace_variables(template.subject, variables)
            body = self._replace_variables(template.body, variables)
            
            # Créer une notification pour chaque canal
            for channel in channels:
                notification = Notification(
                    id=f"{template_name}_{int(time.time())}_{channel.value}",
                    template=template_name,
                    recipient=recipient,
                    channel=channel,
                    priority=priority,
                    status=NotificationStatus.PENDING,
                    subject=subject,
                    body=body,
                    created_at=datetime.now(),
                    sent_at=None,
                    retry_count=0,
                    max_retries=self.max_retries,
                    metadata=variables
                )
                
                # Ajouter à la queue si elle n'est pas pleine
                if len(self.notification_queue) < self.queue_size:
                    self.notification_queue.append(notification)
                else:
                    self.logger.warning("Queue de notifications pleine, notification ignorée")
                    return False
            
            self.logger.info(f"Notification ajoutée à la queue: {template_name} -> {recipient}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "send_notification",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
    
    def _replace_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Remplace les variables dans un texte"""
        try:
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                text = text.replace(placeholder, str(value))
            return text
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_replace_variables",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
            return text
    
    def _processing_loop(self):
        """Boucle principale de traitement des notifications"""
        while self.running:
            try:
                # Traiter les notifications par batch
                batch = self.notification_queue[:self.batch_size]
                if batch:
                    self._process_batch(batch)
                    # Retirer les notifications traitées
                    self.notification_queue = self.notification_queue[self.batch_size:]
                
                time.sleep(1)  # Attendre 1 seconde entre les cycles
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "NotificationService", "_processing_loop",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                time.sleep(5)
    
    def _process_batch(self, notifications: List[Notification]):
        """Traite un batch de notifications"""
        for notification in notifications:
            try:
                success = self._send_single_notification(notification)
                
                if success:
                    notification.status = NotificationStatus.SENT
                    notification.sent_at = datetime.now()
                    self.stats['total_sent'] += 1
                    self.stats['by_channel'][notification.channel.value] += 1
                    self.stats['by_priority'][notification.priority.value] += 1
                else:
                    if notification.retry_count < notification.max_retries:
                        notification.status = NotificationStatus.RETRYING
                        notification.retry_count += 1
                        # Remettre en queue pour retry
                        self.notification_queue.append(notification)
                    else:
                        notification.status = NotificationStatus.FAILED
                        self.stats['total_failed'] += 1
                
                # Ajouter à l'historique
                self.sent_notifications.append(notification)
                
                # Garder seulement les 1000 dernières notifications
                if len(self.sent_notifications) > 1000:
                    self.sent_notifications = self.sent_notifications[-1000:]
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "NotificationService", "_process_batch",
                    ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
                )
                notification.status = NotificationStatus.FAILED
    
    def _send_single_notification(self, notification: Notification) -> bool:
        """Envoie une notification via le canal approprié"""
        try:
            if notification.channel == NotificationChannel.EMAIL:
                return self._send_email(notification)
            elif notification.channel == NotificationChannel.SMS:
                return self._send_sms(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                return self._send_webhook(notification)
            elif notification.channel == NotificationChannel.PUSH:
                return self._send_push(notification)
            elif notification.channel == NotificationChannel.LOG:
                return self._send_log(notification)
            else:
                self.logger.error(f"Canal non supporté: {notification.channel}")
                return False
                
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_send_single_notification",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def _send_email(self, notification: Notification) -> bool:
        """Envoie une notification par email"""
        try:
            if not self.email_config.get('enabled', False):
                self.logger.debug("Email désactivé, notification ignorée")
                return True
            
            # Configuration SMTP
            smtp_server = self.email_config.get('smtp_server', 'localhost')
            smtp_port = self.email_config.get('smtp_port', 587)
            username = self.email_config.get('username', '')
            password = self.email_config.get('password', '')
            from_email = self.email_config.get('from_email', 'alimante@localhost')
            
            # Créer le message
            message = f"""From: {from_email}
To: {notification.recipient}
Subject: {notification.subject}

{notification.body}
"""
            
            # Envoyer l'email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if username and password:
                    server.starttls()
                    server.login(username, password)
                server.sendmail(from_email, notification.recipient, message)
            
            self.logger.info(f"Email envoyé à {notification.recipient}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_send_email",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def _send_sms(self, notification: Notification) -> bool:
        """Envoie une notification par SMS"""
        try:
            if not self.sms_config.get('enabled', False):
                self.logger.debug("SMS désactivé, notification ignorée")
                return True
            
            # Configuration SMS (exemple avec Twilio)
            account_sid = self.sms_config.get('account_sid', '')
            auth_token = self.sms_config.get('auth_token', '')
            from_number = self.sms_config.get('from_number', '')
            
            if not all([account_sid, auth_token, from_number]):
                self.logger.warning("Configuration SMS incomplète")
                return False
            
            # Simuler l'envoi SMS (remplacer par l'API réelle)
            self.logger.info(f"SMS envoyé à {notification.recipient}: {notification.body[:50]}...")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_send_sms",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def _send_webhook(self, notification: Notification) -> bool:
        """Envoie une notification via webhook"""
        try:
            if not self.webhook_config.get('enabled', False):
                self.logger.debug("Webhook désactivé, notification ignorée")
                return True
            
            webhook_url = self.webhook_config.get('url', '')
            if not webhook_url:
                self.logger.warning("URL webhook non configurée")
                return False
            
            # Préparer les données
            data = {
                'notification_id': notification.id,
                'template': notification.template,
                'recipient': notification.recipient,
                'channel': notification.channel.value,
                'priority': notification.priority.value,
                'subject': notification.subject,
                'body': notification.body,
                'timestamp': notification.created_at.isoformat(),
                'metadata': notification.metadata
            }
            
            # Envoyer la requête
            response = requests.post(
                webhook_url,
                json=data,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.logger.info(f"Webhook envoyé à {webhook_url}")
                return True
            else:
                self.logger.warning(f"Webhook échoué: {response.status_code}")
                return False
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_send_webhook",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def _send_push(self, notification: Notification) -> bool:
        """Envoie une notification push"""
        try:
            if not self.push_config.get('enabled', False):
                self.logger.debug("Push désactivé, notification ignorée")
                return True
            
            # Configuration push (exemple avec Firebase)
            server_key = self.push_config.get('server_key', '')
            if not server_key:
                self.logger.warning("Clé serveur push non configurée")
                return False
            
            # Simuler l'envoi push
            self.logger.info(f"Push envoyé à {notification.recipient}: {notification.subject}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_send_push",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def _send_log(self, notification: Notification) -> bool:
        """Envoie une notification dans les logs"""
        try:
            log_level = {
                NotificationPriority.LOW: logging.INFO,
                NotificationPriority.MEDIUM: logging.WARNING,
                NotificationPriority.HIGH: logging.ERROR,
                NotificationPriority.CRITICAL: logging.CRITICAL
            }.get(notification.priority, logging.INFO)
            
            self.logger.log(
                log_level,
                f"NOTIFICATION [{notification.channel.value}] {notification.subject}: {notification.body}"
            )
            
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_send_log",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
            return False
    
    def _process_remaining_notifications(self):
        """Traite les notifications restantes à l'arrêt"""
        try:
            while self.notification_queue:
                batch = self.notification_queue[:self.batch_size]
                self._process_batch(batch)
                self.notification_queue = self.notification_queue[self.batch_size:]
                
        except Exception as e:
            self.error_handler.log_error(
                e, "NotificationService", "_process_remaining_notifications",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des notifications"""
        return {
            'queue_size': len(self.notification_queue),
            'total_sent': self.stats['total_sent'],
            'total_failed': self.stats['total_failed'],
            'by_channel': self.stats['by_channel'],
            'by_priority': self.stats['by_priority'],
            'templates_count': len(self.templates)
        }
    
    def get_recent_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne les notifications récentes"""
        recent = self.sent_notifications[-limit:]
        return [
            {
                'id': n.id,
                'template': n.template,
                'recipient': n.recipient,
                'channel': n.channel.value,
                'priority': n.priority.value,
                'status': n.status.value,
                'subject': n.subject,
                'created_at': n.created_at.isoformat(),
                'sent_at': n.sent_at.isoformat() if n.sent_at else None
            }
            for n in recent
        ]
