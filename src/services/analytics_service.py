"""
Service d'analyse de données et de reporting pour Alimante
Gère l'analyse des données, la génération de rapports et les statistiques
"""

import logging
import json
import sqlite3
import time
import threading
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import os
import statistics

from src.utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory

class ReportType(Enum):
    """Types de rapports"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"
    ALERT = "alert"
    PERFORMANCE = "performance"

class MetricType(Enum):
    """Types de métriques"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    AIR_QUALITY = "air_quality"
    WATER_LEVEL = "water_level"
    ERROR_RATE = "error_rate"
    SYSTEM_LOAD = "system_load"
    RESPONSE_TIME = "response_time"

@dataclass
class DataPoint:
    """Point de données"""
    timestamp: datetime
    metric_type: MetricType
    value: float
    terrarium_id: str
    metadata: Dict[str, Any]

@dataclass
class Report:
    """Rapport généré"""
    id: str
    type: ReportType
    title: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    data: Dict[str, Any]
    summary: Dict[str, Any]
    recommendations: List[str]

class AnalyticsService:
    """
    Service d'analyse de données et de reporting
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        
        # Configuration
        self.analysis_interval = config.get('analysis_interval', 300)  # 5 minutes
        self.report_interval = config.get('report_interval', 86400)  # 24 heures
        self.data_retention_days = config.get('data_retention_days', 90)
        self.alert_thresholds = config.get('alert_thresholds', {})
        
        # Base de données
        self.db_path = 'data/analytics.db'
        
        # Données en mémoire
        self.data_points: List[DataPoint] = []
        self.reports: List[Report] = []
        
        # Threads
        self.analysis_thread: Optional[threading.Thread] = None
        self.report_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Statistiques en temps réel
        self.real_time_stats = {
            'total_data_points': 0,
            'last_analysis': None,
            'anomalies_detected': 0,
            'reports_generated': 0
        }
        
        self.logger.info("Service d'analyse initialisé")
    
    def initialize(self) -> bool:
        """Initialise le service d'analyse"""
        try:
            self.logger.info("Initialisation du service d'analyse...")
            
            # Créer le répertoire de données
            os.makedirs('data', exist_ok=True)
            
            # Initialiser la base de données
            self._init_database()
            
            # Charger les données existantes
            self._load_existing_data()
            
            # Démarrer les threads
            self.running = True
            
            self.analysis_thread = threading.Thread(
                target=self._analysis_loop,
                name="AnalyticsThread",
                daemon=True
            )
            self.analysis_thread.start()
            
            self.report_thread = threading.Thread(
                target=self._report_loop,
                name="ReportThread",
                daemon=True
            )
            self.report_thread.start()
            
            self.logger.info("Service d'analyse initialisé avec succès")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "initialize",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def start(self) -> bool:
        """Démarre le service d'analyse"""
        return True  # Déjà démarré dans initialize
    
    def stop(self) -> bool:
        """Arrête le service d'analyse"""
        try:
            self.running = False
            
            # Attendre que les threads se terminent
            if self.analysis_thread and self.analysis_thread.is_alive():
                self.analysis_thread.join(timeout=5.0)
            
            if self.report_thread and self.report_thread.is_alive():
                self.report_thread.join(timeout=5.0)
            
            # Sauvegarder les données
            self._save_data()
            
            self.logger.info("Service d'analyse arrêté")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "stop",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
    
    def _init_database(self):
        """Initialise la base de données SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table des points de données
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_points (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        terrarium_id TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Table des rapports
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reports (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        generated_at TEXT NOT NULL,
                        period_start TEXT NOT NULL,
                        period_end TEXT NOT NULL,
                        data TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        recommendations TEXT NOT NULL
                    )
                ''')
                
                # Index pour les requêtes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_timestamp ON data_points(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_metric ON data_points(metric_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_terrarium ON data_points(terrarium_id)')
                
                conn.commit()
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_init_database",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
    
    def _load_existing_data(self):
        """Charge les données existantes depuis la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Charger les points de données récents
                cursor.execute('''
                    SELECT timestamp, metric_type, value, terrarium_id, metadata
                    FROM data_points
                    WHERE timestamp > datetime('now', '-7 days')
                    ORDER BY timestamp DESC
                ''')
                
                for row in cursor.fetchall():
                    data_point = DataPoint(
                        timestamp=datetime.fromisoformat(row[0]),
                        metric_type=MetricType(row[1]),
                        value=row[2],
                        terrarium_id=row[3],
                        metadata=json.loads(row[4]) if row[4] else {}
                    )
                    self.data_points.append(data_point)
                
                # Charger les rapports récents
                cursor.execute('''
                    SELECT id, type, title, generated_at, period_start, period_end, 
                           data, summary, recommendations
                    FROM reports
                    ORDER BY generated_at DESC
                    LIMIT 100
                ''')
                
                for row in cursor.fetchall():
                    report = Report(
                        id=row[0],
                        type=ReportType(row[1]),
                        title=row[2],
                        generated_at=datetime.fromisoformat(row[3]),
                        period_start=datetime.fromisoformat(row[4]),
                        period_end=datetime.fromisoformat(row[5]),
                        data=json.loads(row[6]),
                        summary=json.loads(row[7]),
                        recommendations=json.loads(row[8])
                    )
                    self.reports.append(report)
                
                self.logger.info(f"Chargé {len(self.data_points)} points de données et {len(self.reports)} rapports")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_load_existing_data",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _analysis_loop(self):
        """Boucle principale d'analyse"""
        while self.running:
            try:
                # Analyser les données récentes
                self._analyze_recent_data()
                
                # Détecter les anomalies
                self._detect_anomalies()
                
                # Mettre à jour les statistiques
                self._update_stats()
                
                # Nettoyer les anciennes données
                self._cleanup_old_data()
                
                time.sleep(self.analysis_interval)
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "AnalyticsService", "_analysis_loop",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                time.sleep(60)
    
    def _report_loop(self):
        """Boucle principale de génération de rapports"""
        while self.running:
            try:
                # Vérifier si un rapport doit être généré
                if self._should_generate_report():
                    self._generate_daily_report()
                
                time.sleep(self.report_interval)
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "AnalyticsService", "_report_loop",
                    ErrorSeverity.HIGH, ErrorCategory.SERVICE
                )
                time.sleep(300)
    
    def add_data_point(self, metric_type: MetricType, value: float, terrarium_id: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Ajoute un point de données
        
        Args:
            metric_type: Type de métrique
            value: Valeur
            terrarium_id: ID du terrarium
            metadata: Métadonnées supplémentaires
        
        Returns:
            bool: Succès de l'ajout
        """
        try:
            data_point = DataPoint(
                timestamp=datetime.now(),
                metric_type=metric_type,
                value=value,
                terrarium_id=terrarium_id,
                metadata=metadata or {}
            )
            
            # Ajouter en mémoire
            self.data_points.append(data_point)
            
            # Sauvegarder en base
            self._save_data_point(data_point)
            
            self.real_time_stats['total_data_points'] += 1
            
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "add_data_point",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def _save_data_point(self, data_point: DataPoint):
        """Sauvegarde un point de données en base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO data_points (timestamp, metric_type, value, terrarium_id, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    data_point.timestamp.isoformat(),
                    data_point.metric_type.value,
                    data_point.value,
                    data_point.terrarium_id,
                    json.dumps(data_point.metadata)
                ))
                conn.commit()
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_save_data_point",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _analyze_recent_data(self):
        """Analyse les données récentes"""
        try:
            # Analyser les dernières 24 heures
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_data = [dp for dp in self.data_points if dp.timestamp > cutoff_time]
            
            if not recent_data:
                return
            
            # Grouper par type de métrique
            by_metric = {}
            for dp in recent_data:
                if dp.metric_type not in by_metric:
                    by_metric[dp.metric_type] = []
                by_metric[dp.metric_type].append(dp.value)
            
            # Calculer les statistiques pour chaque métrique
            for metric_type, values in by_metric.items():
                if len(values) > 1:
                    stats = {
                        'count': len(values),
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0,
                        'min': min(values),
                        'max': max(values)
                    }
                    
                    # Émettre un événement avec les statistiques
                    if self.event_bus:
                        self.event_bus.emit('metric_analysis', {
                            'metric_type': metric_type.value,
                            'stats': stats,
                            'timestamp': datetime.now().isoformat()
                        })
            
            self.real_time_stats['last_analysis'] = datetime.now()
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_analyze_recent_data",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _detect_anomalies(self):
        """Détecte les anomalies dans les données"""
        try:
            # Analyser les dernières 2 heures
            cutoff_time = datetime.now() - timedelta(hours=2)
            recent_data = [dp for dp in self.data_points if dp.timestamp > cutoff_time]
            
            if len(recent_data) < 10:  # Pas assez de données
                return
            
            # Grouper par type de métrique
            by_metric = {}
            for dp in recent_data:
                if dp.metric_type not in by_metric:
                    by_metric[dp.metric_type] = []
                by_metric[dp.metric_type].append(dp)
            
            # Détecter les anomalies pour chaque métrique
            for metric_type, data_points in by_metric.items():
                if len(data_points) < 5:
                    continue
                
                values = [dp.value for dp in data_points]
                mean = statistics.mean(values)
                std = statistics.stdev(values) if len(values) > 1 else 0
                
                # Seuil d'anomalie (2 écarts-types)
                threshold = 2 * std
                
                for dp in data_points:
                    if abs(dp.value - mean) > threshold:
                        self.real_time_stats['anomalies_detected'] += 1
                        
                        # Émettre une alerte
                        if self.event_bus:
                            self.event_bus.emit('anomaly_detected', {
                                'metric_type': metric_type.value,
                                'value': dp.value,
                                'expected_range': [mean - threshold, mean + threshold],
                                'terrarium_id': dp.terrarium_id,
                                'timestamp': dp.timestamp.isoformat()
                            })
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_detect_anomalies",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _update_stats(self):
        """Met à jour les statistiques en temps réel"""
        try:
            # Calculer les statistiques globales
            total_points = len(self.data_points)
            recent_points = len([dp for dp in self.data_points 
                               if dp.timestamp > datetime.now() - timedelta(hours=1)])
            
            self.real_time_stats.update({
                'total_data_points': total_points,
                'recent_points_1h': recent_points,
                'reports_generated': len(self.reports)
            })
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_update_stats",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
    
    def _cleanup_old_data(self):
        """Nettoie les anciennes données"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.data_retention_days)
            
            # Nettoyer les points de données en mémoire
            self.data_points = [dp for dp in self.data_points if dp.timestamp > cutoff_time]
            
            # Nettoyer la base de données
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM data_points 
                    WHERE timestamp < ?
                ''', (cutoff_time.isoformat(),))
                conn.commit()
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_cleanup_old_data",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
    
    def _should_generate_report(self) -> bool:
        """Détermine si un rapport doit être généré"""
        try:
            if not self.reports:
                return True
            
            # Vérifier le dernier rapport
            last_report = max(self.reports, key=lambda r: r.generated_at)
            time_since_last = datetime.now() - last_report.generated_at
            
            return time_since_last.total_seconds() >= self.report_interval
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_should_generate_report",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
            return False
    
    def _generate_daily_report(self):
        """Génère un rapport quotidien"""
        try:
            report_id = f"daily_{int(time.time())}"
            now = datetime.now()
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Collecter les données de la journée
            daily_data = [dp for dp in self.data_points 
                         if start_of_day <= dp.timestamp <= now]
            
            # Analyser les données
            analysis = self._analyze_data_period(daily_data)
            
            # Générer le rapport
            report = Report(
                id=report_id,
                type=ReportType.DAILY,
                title=f"Rapport Quotidien - {now.strftime('%Y-%m-%d')}",
                generated_at=now,
                period_start=start_of_day,
                period_end=now,
                data=analysis['data'],
                summary=analysis['summary'],
                recommendations=analysis['recommendations']
            )
            
            self.reports.append(report)
            self._save_report(report)
            
            self.real_time_stats['reports_generated'] += 1
            
            # Émettre un événement
            if self.event_bus:
                self.event_bus.emit('report_generated', {
                    'report_id': report_id,
                    'report_type': 'daily',
                    'timestamp': now.isoformat()
                })
            
            self.logger.info(f"Rapport quotidien généré: {report_id}")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_generate_daily_report",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
    
    def _analyze_data_period(self, data_points: List[DataPoint]) -> Dict[str, Any]:
        """Analyse une période de données"""
        try:
            if not data_points:
                return {
                    'data': {},
                    'summary': {'message': 'Aucune donnée disponible'},
                    'recommendations': []
                }
            
            # Grouper par métrique et terrarium
            analysis = {}
            for dp in data_points:
                key = f"{dp.metric_type.value}_{dp.terrarium_id}"
                if key not in analysis:
                    analysis[key] = []
                analysis[key].append(dp.value)
            
            # Calculer les statistiques
            data = {}
            summary = {}
            recommendations = []
            
            for key, values in analysis.items():
                if len(values) > 0:
                    stats = {
                        'count': len(values),
                        'mean': statistics.mean(values),
                        'min': min(values),
                        'max': max(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0
                    }
                    data[key] = stats
                    
                    # Ajouter des recommandations basées sur les valeurs
                    metric_type = key.split('_')[0]
                    if metric_type == 'temperature':
                        if stats['mean'] > 30:
                            recommendations.append("Température élevée détectée, vérifier le refroidissement")
                        elif stats['mean'] < 15:
                            recommendations.append("Température basse détectée, vérifier le chauffage")
                    
                    elif metric_type == 'humidity':
                        if stats['mean'] > 80:
                            recommendations.append("Humidité élevée détectée, vérifier la ventilation")
                        elif stats['mean'] < 30:
                            recommendations.append("Humidité basse détectée, vérifier l'humidification")
            
            summary = {
                'total_data_points': len(data_points),
                'metrics_analyzed': len(analysis),
                'period_hours': (data_points[-1].timestamp - data_points[0].timestamp).total_seconds() / 3600,
                'data_quality': 'good' if len(data_points) > 100 else 'limited'
            }
            
            return {
                'data': data,
                'summary': summary,
                'recommendations': recommendations
            }
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_analyze_data_period",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return {
                'data': {},
                'summary': {'error': str(e)},
                'recommendations': []
            }
    
    def _save_report(self, report: Report):
        """Sauvegarde un rapport en base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO reports 
                    (id, type, title, generated_at, period_start, period_end, data, summary, recommendations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report.id,
                    report.type.value,
                    report.title,
                    report.generated_at.isoformat(),
                    report.period_start.isoformat(),
                    report.period_end.isoformat(),
                    json.dumps(report.data),
                    json.dumps(report.summary),
                    json.dumps(report.recommendations)
                ))
                conn.commit()
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_save_report",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _save_data(self):
        """Sauvegarde les données en mémoire"""
        try:
            # Les données sont déjà sauvegardées individuellement
            pass
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "_save_data",
                ErrorSeverity.LOW, ErrorCategory.SERVICE
            )
    
    def get_analytics_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'analyse"""
        return {
            'real_time_stats': self.real_time_stats,
            'total_reports': len(self.reports),
            'data_retention_days': self.data_retention_days,
            'analysis_interval': self.analysis_interval,
            'report_interval': self.report_interval
        }
    
    def get_recent_data(self, metric_type: Optional[MetricType] = None, 
                       terrarium_id: Optional[str] = None, 
                       hours: int = 24) -> List[Dict[str, Any]]:
        """Récupère les données récentes"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_data = [dp for dp in self.data_points if dp.timestamp > cutoff_time]
            
            if metric_type:
                filtered_data = [dp for dp in filtered_data if dp.metric_type == metric_type]
            
            if terrarium_id:
                filtered_data = [dp for dp in filtered_data if dp.terrarium_id == terrarium_id]
            
            return [
                {
                    'timestamp': dp.timestamp.isoformat(),
                    'metric_type': dp.metric_type.value,
                    'value': dp.value,
                    'terrarium_id': dp.terrarium_id,
                    'metadata': dp.metadata
                }
                for dp in filtered_data
            ]
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "get_recent_data",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return []
    
    def get_reports(self, report_type: Optional[ReportType] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les rapports"""
        try:
            filtered_reports = self.reports
            
            if report_type:
                filtered_reports = [r for r in filtered_reports if r.type == report_type]
            
            return [
                {
                    'id': report.id,
                    'type': report.type.value,
                    'title': report.title,
                    'generated_at': report.generated_at.isoformat(),
                    'period_start': report.period_start.isoformat(),
                    'period_end': report.period_end.isoformat(),
                    'summary': report.summary,
                    'recommendations': report.recommendations
                }
                for report in sorted(filtered_reports, key=lambda r: r.generated_at, reverse=True)[:limit]
            ]
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AnalyticsService", "get_reports",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return []
