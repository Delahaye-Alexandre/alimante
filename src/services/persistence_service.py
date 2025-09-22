"""
Service de persistance des données Alimante
Gère le stockage SQLite pour l'historique des données et la configuration
"""

import sqlite3
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class PersistenceService:
    """
    Service de persistance des données dans SQLite
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        """
        Initialise le service de persistance
        
        Args:
            config: Configuration du service
            event_bus: Bus d'événements
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Configuration de la base de données
        self.db_path = Path("data/db.sqlite")
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Configuration de rétention des données
        self.data_retention_days = config.get('terrariums', {}).get('data_retention_days', 30)
        
        # État du service
        self.is_running = False
        self.connection = None
        
        # Statistiques
        self.stats = {
            'queries_executed': 0,
            'data_points_stored': 0,
            'errors': 0,
            'last_cleanup': 0
        }
        
    def initialize(self) -> bool:
        """
        Initialise le service de persistance
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            self.logger.info("Initialisation du service de persistance...")
            
            # Créer la connexion à la base de données
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            
            # Créer les tables
            self._create_tables()
            
            # Nettoyer les anciennes données
            self._cleanup_old_data()
            
            self.is_running = True
            self.logger.info("Service de persistance initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation service persistance: {e}")
            return False
    
    def _create_tables(self) -> None:
        """Crée les tables de la base de données"""
        try:
            cursor = self.connection.cursor()
            
            # Table des données de capteurs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    terrarium_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    air_quality REAL,
                    air_quality_level TEXT,
                    water_level REAL,
                    water_percentage REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des alimentations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feeding_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    terrarium_id TEXT NOT NULL,
                    species_id TEXT,
                    feeding_date TEXT NOT NULL,
                    feeding_time TEXT NOT NULL,
                    food_type TEXT,
                    quantity REAL,
                    success BOOLEAN DEFAULT 1,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des alertes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    terrarium_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    value REAL,
                    threshold REAL,
                    timestamp REAL NOT NULL,
                    acknowledged BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des décisions de contrôle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS control_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    terrarium_id TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    component TEXT NOT NULL,
                    action TEXT NOT NULL,
                    value REAL,
                    reason TEXT,
                    timestamp REAL NOT NULL,
                    success BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des configurations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_type TEXT NOT NULL,
                    config_key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    changed_by TEXT,
                    timestamp REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des statistiques système
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    terrarium_id TEXT,
                    stat_name TEXT NOT NULL,
                    stat_value REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Créer les index pour améliorer les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_data_terrarium_time ON sensor_data(terrarium_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feeding_log_terrarium_date ON feeding_log(terrarium_id, feeding_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_terrarium_time ON alerts(terrarium_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_control_decisions_terrarium_time ON control_decisions(terrarium_id, timestamp)")
            
            self.connection.commit()
            self.logger.info("Tables de base de données créées")
            
        except Exception as e:
            self.logger.error(f"Erreur création tables: {e}")
            raise
    
    def start(self) -> None:
        """Démarre le service de persistance"""
        try:
            if not self.is_running:
                self.initialize()
            
            self.logger.info("Service de persistance démarré")
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage service persistance: {e}")
    
    def stop(self) -> None:
        """Arrête le service de persistance"""
        try:
            self.is_running = False
            
            if self.connection:
                self.connection.close()
                self.connection = None
            
            self.logger.info("Service de persistance arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt service persistance: {e}")
    
    def store_sensor_data(self, terrarium_id: str, data: Dict[str, Any]) -> bool:
        """
        Stocke les données des capteurs
        
        Args:
            terrarium_id: ID du terrarium
            data: Données des capteurs
            
        Returns:
            True si le stockage réussit, False sinon
        """
        try:
            if not self.is_running or not self.connection:
                return False
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO sensor_data 
                (terrarium_id, timestamp, temperature, humidity, air_quality, 
                 air_quality_level, water_level, water_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                terrarium_id,
                data.get('timestamp', time.time()),
                data.get('temperature'),
                data.get('humidity'),
                data.get('air_quality'),
                data.get('air_quality_level'),
                data.get('water_level'),
                data.get('water_percentage')
            ))
            
            self.connection.commit()
            self.stats['data_points_stored'] += 1
            self.stats['queries_executed'] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur stockage données capteurs: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_last_feeding_date(self, terrarium_id: str) -> Optional[str]:
        """
        Récupère la date de la dernière alimentation
        
        Args:
            terrarium_id: ID du terrarium
            
        Returns:
            Date de la dernière alimentation ou None
        """
        try:
            if not self.is_running or not self.connection:
                return None
            
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT feeding_date FROM feeding_log 
                WHERE terrarium_id = ? AND success = 1
                ORDER BY feeding_date DESC, feeding_time DESC
                LIMIT 1
            """, (terrarium_id,))
            
            result = cursor.fetchone()
            self.stats['queries_executed'] += 1
            
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Erreur récupération dernière alimentation: {e}")
            self.stats['errors'] += 1
            return None
    
    def set_last_feeding_date(self, terrarium_id: str, species_id: str, 
                            food_type: str = "default", quantity: float = 1.0, 
                            notes: str = "") -> bool:
        """
        Enregistre une nouvelle alimentation
        
        Args:
            terrarium_id: ID du terrarium
            species_id: ID de l'espèce
            food_type: Type de nourriture
            quantity: Quantité donnée
            notes: Notes additionnelles
            
        Returns:
            True si l'enregistrement réussit, False sinon
        """
        try:
            if not self.is_running or not self.connection:
                return False
            
            now = datetime.now()
            feeding_date = now.strftime("%Y-%m-%d")
            feeding_time = now.strftime("%H:%M:%S")
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO feeding_log 
                (terrarium_id, species_id, feeding_date, feeding_time, 
                 food_type, quantity, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                terrarium_id, species_id, feeding_date, feeding_time,
                food_type, quantity, notes
            ))
            
            self.connection.commit()
            self.stats['queries_executed'] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur enregistrement alimentation: {e}")
            self.stats['errors'] += 1
            return False
    
    def store_alert(self, terrarium_id: str, alert_type: str, severity: str, 
                   message: str, value: Optional[float] = None, 
                   threshold: Optional[float] = None) -> bool:
        """
        Stocke une alerte
        
        Args:
            terrarium_id: ID du terrarium
            alert_type: Type d'alerte
            severity: Gravité (info, warning, error, critical)
            message: Message d'alerte
            value: Valeur qui a déclenché l'alerte
            threshold: Seuil dépassé
            
        Returns:
            True si le stockage réussit, False sinon
        """
        try:
            if not self.is_running or not self.connection:
                return False
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO alerts 
                (terrarium_id, alert_type, severity, message, value, threshold, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                terrarium_id, alert_type, severity, message, 
                value, threshold, time.time()
            ))
            
            self.connection.commit()
            self.stats['queries_executed'] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur stockage alerte: {e}")
            self.stats['errors'] += 1
            return False
    
    def store_control_decision(self, terrarium_id: str, decision_type: str, 
                             component: str, action: str, value: Optional[float] = None,
                             reason: str = "", success: bool = True) -> bool:
        """
        Stocke une décision de contrôle
        
        Args:
            terrarium_id: ID du terrarium
            decision_type: Type de décision
            component: Composant concerné
            action: Action effectuée
            value: Valeur de l'action
            reason: Raison de la décision
            success: Succès de l'action
            
        Returns:
            True si le stockage réussit, False sinon
        """
        try:
            if not self.is_running or not self.connection:
                return False
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO control_decisions 
                (terrarium_id, decision_type, component, action, value, reason, timestamp, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                terrarium_id, decision_type, component, action, 
                value, reason, time.time(), success
            ))
            
            self.connection.commit()
            self.stats['queries_executed'] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur stockage décision contrôle: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_sensor_history(self, terrarium_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des données de capteurs
        
        Args:
            terrarium_id: ID du terrarium
            hours: Nombre d'heures d'historique à récupérer
            
        Returns:
            Liste des données historiques
        """
        try:
            if not self.is_running or not self.connection:
                return []
            
            cutoff_time = time.time() - (hours * 3600)
            
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM sensor_data 
                WHERE terrarium_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (terrarium_id, cutoff_time))
            
            results = cursor.fetchall()
            self.stats['queries_executed'] += 1
            
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erreur récupération historique capteurs: {e}")
            self.stats['errors'] += 1
            return []
    
    def get_feeding_history(self, terrarium_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des alimentations
        
        Args:
            terrarium_id: ID du terrarium
            days: Nombre de jours d'historique à récupérer
            
        Returns:
            Liste des alimentations
        """
        try:
            if not self.is_running or not self.connection:
                return []
            
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM feeding_log 
                WHERE terrarium_id = ? AND feeding_date >= ?
                ORDER BY feeding_date DESC, feeding_time DESC
            """, (terrarium_id, cutoff_date))
            
            results = cursor.fetchall()
            self.stats['queries_executed'] += 1
            
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erreur récupération historique alimentations: {e}")
            self.stats['errors'] += 1
            return []
    
    def get_alerts(self, terrarium_id: Optional[str] = None, 
                  severity: Optional[str] = None, 
                  acknowledged: bool = False) -> List[Dict[str, Any]]:
        """
        Récupère les alertes
        
        Args:
            terrarium_id: ID du terrarium (optionnel)
            severity: Gravité des alertes (optionnel)
            acknowledged: Inclure les alertes acquittées
            
        Returns:
            Liste des alertes
        """
        try:
            if not self.is_running or not self.connection:
                return []
            
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            
            if terrarium_id:
                query += " AND terrarium_id = ?"
                params.append(terrarium_id)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            if not acknowledged:
                query += " AND acknowledged = 0"
            
            query += " ORDER BY timestamp DESC"
            
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            
            results = cursor.fetchall()
            self.stats['queries_executed'] += 1
            
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erreur récupération alertes: {e}")
            self.stats['errors'] += 1
            return []
    
    def _cleanup_old_data(self) -> None:
        """Nettoie les anciennes données selon la rétention configurée"""
        try:
            if not self.connection:
                return
            
            cutoff_time = time.time() - (self.data_retention_days * 24 * 3600)
            cutoff_date = (datetime.now() - timedelta(days=self.data_retention_days)).strftime("%Y-%m-%d")
            
            cursor = self.connection.cursor()
            
            # Nettoyer les données de capteurs
            cursor.execute("DELETE FROM sensor_data WHERE timestamp < ?", (cutoff_time,))
            sensor_deleted = cursor.rowcount
            
            # Nettoyer les alimentations
            cursor.execute("DELETE FROM feeding_log WHERE feeding_date < ?", (cutoff_date,))
            feeding_deleted = cursor.rowcount
            
            # Nettoyer les alertes acquittées
            cursor.execute("DELETE FROM alerts WHERE timestamp < ? AND acknowledged = 1", (cutoff_time,))
            alerts_deleted = cursor.rowcount
            
            # Nettoyer les décisions de contrôle
            cursor.execute("DELETE FROM control_decisions WHERE timestamp < ?", (cutoff_time,))
            decisions_deleted = cursor.rowcount
            
            self.connection.commit()
            self.stats['last_cleanup'] = time.time()
            
            if any([sensor_deleted, feeding_deleted, alerts_deleted, decisions_deleted]):
                self.logger.info(f"Nettoyage données: {sensor_deleted} capteurs, {feeding_deleted} alimentations, "
                               f"{alerts_deleted} alertes, {decisions_deleted} décisions supprimées")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage données: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du service"""
        return {
            'service': 'persistence',
            'is_running': self.is_running,
            'db_path': str(self.db_path),
            'data_retention_days': self.data_retention_days,
            'stats': self.stats.copy()
        }
    
    def cleanup(self) -> None:
        """Nettoie le service"""
        try:
            self.stop()
            self.logger.info("Service de persistance nettoyé")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage service persistance: {e}")
