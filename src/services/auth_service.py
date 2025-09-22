"""
Service d'authentification sécurisé pour Alimante
Gère l'authentification, l'autorisation et la sécurité des utilisateurs
"""

import logging
import hashlib
import secrets
import time
import threading
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import os
import base64
import hmac

from ..utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory

class UserRole(Enum):
    """Rôles utilisateur"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    GUEST = "guest"

class AuthStatus(Enum):
    """Statuts d'authentification"""
    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    EXPIRED = "expired"
    LOCKED = "locked"
    DISABLED = "disabled"

@dataclass
class User:
    """Utilisateur du système"""
    username: str
    email: str
    role: UserRole
    status: AuthStatus
    created_at: datetime
    last_login: Optional[datetime]
    failed_attempts: int
    locked_until: Optional[datetime]
    password_hash: str
    salt: str
    permissions: List[str]
    metadata: Dict[str, Any]

@dataclass
class AuthToken:
    """Token d'authentification"""
    token: str
    user_id: str
    expires_at: datetime
    created_at: datetime
    permissions: List[str]
    is_refresh: bool

class AuthService:
    """
    Service d'authentification sécurisé
    """
    
    def __init__(self, config: Dict[str, Any], event_bus: Optional[Any] = None):
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        
        # Configuration de sécurité
        self.jwt_secret = config.get('jwt_secret', self._generate_secret())
        self.jwt_expiry = config.get('jwt_expiry', 3600)  # 1 heure
        self.refresh_expiry = config.get('refresh_expiry', 86400 * 7)  # 7 jours
        self.max_failed_attempts = config.get('max_failed_attempts', 5)
        self.lockout_duration = config.get('lockout_duration', 900)  # 15 minutes
        self.password_min_length = config.get('password_min_length', 8)
        
        # Stockage des utilisateurs et tokens
        self.users: Dict[str, User] = {}
        self.active_tokens: Dict[str, AuthToken] = {}
        self.refresh_tokens: Dict[str, AuthToken] = {}
        
        # Sessions actives
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Thread de nettoyage
        self.cleanup_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Permissions par rôle
        self.role_permissions = {
            UserRole.ADMIN: [
                'read', 'write', 'delete', 'admin', 'manage_users', 
                'manage_system', 'view_logs', 'manage_config'
            ],
            UserRole.OPERATOR: [
                'read', 'write', 'control_terrariums', 'view_logs'
            ],
            UserRole.VIEWER: [
                'read', 'view_terrariums'
            ],
            UserRole.GUEST: [
                'read'
            ]
        }
        
        self.logger.info("Service d'authentification initialisé")
    
    def initialize(self) -> bool:
        """Initialise le service d'authentification"""
        try:
            self.logger.info("Initialisation du service d'authentification...")
            
            # Créer le répertoire de données si nécessaire
            os.makedirs('data/auth', exist_ok=True)
            
            # Charger les utilisateurs existants
            self._load_users()
            
            # Créer l'utilisateur admin par défaut si nécessaire
            if not self.users:
                self._create_default_admin()
            
            # Démarrer le thread de nettoyage
            self.running = True
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                name="AuthCleanupThread",
                daemon=True
            )
            self.cleanup_thread.start()
            
            self.logger.info("Service d'authentification initialisé avec succès")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "initialize",
                ErrorSeverity.CRITICAL, ErrorCategory.SERVICE
            )
            return False
    
    def start(self) -> bool:
        """Démarre le service d'authentification"""
        return True  # Déjà démarré dans initialize
    
    def stop(self) -> bool:
        """Arrête le service d'authentification"""
        try:
            self.running = False
            
            # Attendre que le thread se termine
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5.0)
            
            # Sauvegarder les utilisateurs
            self._save_users()
            
            self.logger.info("Service d'authentification arrêté")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "stop",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False
    
    def _generate_secret(self) -> str:
        """Génère une clé secrète pour JWT"""
        return secrets.token_urlsafe(32)
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hache un mot de passe avec un sel"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _generate_salt(self) -> str:
        """Génère un sel aléatoire"""
        return secrets.token_hex(16)
    
    def _create_default_admin(self):
        """Crée l'utilisateur admin par défaut"""
        try:
            salt = self._generate_salt()
            password_hash = self._hash_password("admin123", salt)
            
            admin_user = User(
                username="admin",
                email="admin@alimante.local",
                role=UserRole.ADMIN,
                status=AuthStatus.AUTHENTICATED,
                created_at=datetime.now(),
                last_login=None,
                failed_attempts=0,
                locked_until=None,
                password_hash=password_hash,
                salt=salt,
                permissions=self.role_permissions[UserRole.ADMIN],
                metadata={"is_default": True}
            )
            
            self.users["admin"] = admin_user
            self._save_users()
            
            self.logger.info("Utilisateur admin par défaut créé (username: admin, password: admin123)")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "_create_default_admin",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
    
    def _load_users(self):
        """Charge les utilisateurs depuis le fichier"""
        try:
            users_file = 'data/auth/users.json'
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    data = json.load(f)
                
                for username, user_data in data.items():
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        role=UserRole(user_data['role']),
                        status=AuthStatus(user_data['status']),
                        created_at=datetime.fromisoformat(user_data['created_at']),
                        last_login=datetime.fromisoformat(user_data['last_login']) if user_data['last_login'] else None,
                        failed_attempts=user_data['failed_attempts'],
                        locked_until=datetime.fromisoformat(user_data['locked_until']) if user_data['locked_until'] else None,
                        password_hash=user_data['password_hash'],
                        salt=user_data['salt'],
                        permissions=user_data['permissions'],
                        metadata=user_data['metadata']
                    )
                    self.users[username] = user
                
                self.logger.info(f"Chargé {len(self.users)} utilisateurs")
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "_load_users",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def _save_users(self):
        """Sauvegarde les utilisateurs dans le fichier"""
        try:
            users_file = 'data/auth/users.json'
            data = {}
            
            for username, user in self.users.items():
                data[username] = {
                    'username': user.username,
                    'email': user.email,
                    'role': user.role.value,
                    'status': user.status.value,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'failed_attempts': user.failed_attempts,
                    'locked_until': user.locked_until.isoformat() if user.locked_until else None,
                    'password_hash': user.password_hash,
                    'salt': user.salt,
                    'permissions': user.permissions,
                    'metadata': user.metadata
                }
            
            with open(users_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "_save_users",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Authentifie un utilisateur
        
        Returns:
            Tuple[success, access_token, refresh_token]
        """
        try:
            # Vérifier si l'utilisateur existe
            if username not in self.users:
                self.logger.warning(f"Tentative d'authentification avec utilisateur inexistant: {username}")
                return False, None, None
            
            user = self.users[username]
            
            # Vérifier si le compte est verrouillé
            if user.locked_until and datetime.now() < user.locked_until:
                self.logger.warning(f"Tentative d'authentification avec compte verrouillé: {username}")
                return False, None, None
            
            # Vérifier si le compte est désactivé
            if user.status == AuthStatus.DISABLED:
                self.logger.warning(f"Tentative d'authentification avec compte désactivé: {username}")
                return False, None, None
            
            # Vérifier le mot de passe
            password_hash = self._hash_password(password, user.salt)
            if password_hash != user.password_hash:
                # Incrémenter les tentatives échouées
                user.failed_attempts += 1
                
                # Verrouiller le compte si trop de tentatives
                if user.failed_attempts >= self.max_failed_attempts:
                    user.locked_until = datetime.now() + timedelta(seconds=self.lockout_duration)
                    user.status = AuthStatus.LOCKED
                    self.logger.warning(f"Compte verrouillé après {self.max_failed_attempts} tentatives échouées: {username}")
                
                self._save_users()
                return False, None, None
            
            # Réinitialiser les tentatives échouées
            user.failed_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now()
            user.status = AuthStatus.AUTHENTICATED
            
            # Générer les tokens
            access_token = self._generate_jwt_token(user, False)
            refresh_token = self._generate_jwt_token(user, True)
            
            # Stocker les tokens
            self.active_tokens[access_token] = AuthToken(
                token=access_token,
                user_id=username,
                expires_at=datetime.now() + timedelta(seconds=self.jwt_expiry),
                created_at=datetime.now(),
                permissions=user.permissions,
                is_refresh=False
            )
            
            self.refresh_tokens[refresh_token] = AuthToken(
                token=refresh_token,
                user_id=username,
                expires_at=datetime.now() + timedelta(seconds=self.refresh_expiry),
                created_at=datetime.now(),
                permissions=user.permissions,
                is_refresh=True
            )
            
            # Créer une session
            session_id = secrets.token_urlsafe(32)
            self.active_sessions[session_id] = {
                'user_id': username,
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'ip_address': None,  # À implémenter si nécessaire
                'user_agent': None
            }
            
            self._save_users()
            
            self.logger.info(f"Authentification réussie pour {username}")
            return True, access_token, refresh_token
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "authenticate",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False, None, None
    
    def _generate_jwt_token(self, user: User, is_refresh: bool) -> str:
        """Génère un token JWT (version simplifiée)"""
        try:
            # Header
            header = {
                "alg": "HS256",
                "typ": "JWT"
            }
            
            # Payload
            expiry = self.refresh_expiry if is_refresh else self.jwt_expiry
            payload = {
                "sub": user.username,
                "role": user.role.value,
                "permissions": user.permissions,
                "iat": int(time.time()),
                "exp": int(time.time()) + expiry,
                "is_refresh": is_refresh
            }
            
            # Encoder header et payload
            header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
            payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
            
            # Créer la signature
            message = f"{header_encoded}.{payload_encoded}"
            signature = hmac.new(
                self.jwt_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
            
            return f"{message}.{signature_encoded}"
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "_generate_jwt_token",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return ""
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[User], Optional[List[str]]]:
        """
        Vérifie un token d'authentification
        
        Returns:
            Tuple[is_valid, user, permissions]
        """
        try:
            # Vérifier si le token est actif
            if token not in self.active_tokens:
                return False, None, None
            
            auth_token = self.active_tokens[token]
            
            # Vérifier l'expiration
            if datetime.now() > auth_token.expires_at:
                del self.active_tokens[token]
                return False, None, None
            
            # Récupérer l'utilisateur
            if auth_token.user_id not in self.users:
                return False, None, None
            
            user = self.users[auth_token.user_id]
            
            # Vérifier le statut de l'utilisateur
            if user.status != AuthStatus.AUTHENTICATED:
                return False, None, None
            
            return True, user, auth_token.permissions
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "verify_token",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False, None, None
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Optional[str]]:
        """
        Rafraîchit un token d'accès
        
        Returns:
            Tuple[success, new_access_token]
        """
        try:
            # Vérifier le refresh token
            if refresh_token not in self.refresh_tokens:
                return False, None
            
            auth_token = self.refresh_tokens[refresh_token]
            
            # Vérifier l'expiration
            if datetime.now() > auth_token.expires_at:
                del self.refresh_tokens[refresh_token]
                return False, None
            
            # Récupérer l'utilisateur
            if auth_token.user_id not in self.users:
                return False, None
            
            user = self.users[auth_token.user_id]
            
            # Vérifier le statut de l'utilisateur
            if user.status != AuthStatus.AUTHENTICATED:
                return False, None
            
            # Générer un nouveau token d'accès
            new_access_token = self._generate_jwt_token(user, False)
            
            # Stocker le nouveau token
            self.active_tokens[new_access_token] = AuthToken(
                token=new_access_token,
                user_id=user.username,
                expires_at=datetime.now() + timedelta(seconds=self.jwt_expiry),
                created_at=datetime.now(),
                permissions=user.permissions,
                is_refresh=False
            )
            
            return True, new_access_token
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "refresh_access_token",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False, None
    
    def logout(self, token: str) -> bool:
        """Déconnecte un utilisateur"""
        try:
            # Supprimer le token d'accès
            if token in self.active_tokens:
                del self.active_tokens[token]
            
            # Supprimer les refresh tokens associés
            user_id = None
            for t, auth_token in list(self.refresh_tokens.items()):
                if auth_token.user_id == user_id:
                    del self.refresh_tokens[t]
            
            # Supprimer les sessions
            for session_id, session in list(self.active_sessions.items()):
                if session['user_id'] == user_id:
                    del self.active_sessions[session_id]
            
            self.logger.info(f"Déconnexion réussie")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "logout",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def create_user(self, username: str, email: str, password: str, role: UserRole) -> Tuple[bool, str]:
        """
        Crée un nouvel utilisateur
        
        Returns:
            Tuple[success, message]
        """
        try:
            # Vérifier si l'utilisateur existe déjà
            if username in self.users:
                return False, "L'utilisateur existe déjà"
            
            # Vérifier la force du mot de passe
            if len(password) < self.password_min_length:
                return False, f"Le mot de passe doit contenir au moins {self.password_min_length} caractères"
            
            # Créer l'utilisateur
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            
            user = User(
                username=username,
                email=email,
                role=role,
                status=AuthStatus.UNAUTHENTICATED,
                created_at=datetime.now(),
                last_login=None,
                failed_attempts=0,
                locked_until=None,
                password_hash=password_hash,
                salt=salt,
                permissions=self.role_permissions[role],
                metadata={}
            )
            
            self.users[username] = user
            self._save_users()
            
            self.logger.info(f"Utilisateur créé: {username} ({role.value})")
            return True, "Utilisateur créé avec succès"
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "create_user",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False, f"Erreur lors de la création de l'utilisateur: {str(e)}"
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change le mot de passe d'un utilisateur
        
        Returns:
            Tuple[success, message]
        """
        try:
            if username not in self.users:
                return False, "Utilisateur non trouvé"
            
            user = self.users[username]
            
            # Vérifier l'ancien mot de passe
            old_password_hash = self._hash_password(old_password, user.salt)
            if old_password_hash != user.password_hash:
                return False, "Ancien mot de passe incorrect"
            
            # Vérifier la force du nouveau mot de passe
            if len(new_password) < self.password_min_length:
                return False, f"Le nouveau mot de passe doit contenir au moins {self.password_min_length} caractères"
            
            # Mettre à jour le mot de passe
            new_salt = self._generate_salt()
            new_password_hash = self._hash_password(new_password, new_salt)
            
            user.password_hash = new_password_hash
            user.salt = new_salt
            user.failed_attempts = 0
            user.locked_until = None
            
            self._save_users()
            
            self.logger.info(f"Mot de passe changé pour {username}")
            return True, "Mot de passe changé avec succès"
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "change_password",
                ErrorSeverity.HIGH, ErrorCategory.SERVICE
            )
            return False, f"Erreur lors du changement de mot de passe: {str(e)}"
    
    def check_permission(self, token: str, permission: str) -> bool:
        """Vérifie si un utilisateur a une permission spécifique"""
        try:
            is_valid, user, permissions = self.verify_token(token)
            if not is_valid or not permissions:
                return False
            
            return permission in permissions
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "check_permission",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return False
    
    def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un utilisateur"""
        try:
            is_valid, user, permissions = self.verify_token(token)
            if not is_valid or not user:
                return None
            
            return {
                'username': user.username,
                'email': user.email,
                'role': user.role.value,
                'permissions': permissions,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'status': user.status.value
            }
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "get_user_info",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return None
    
    def list_users(self, token: str) -> Optional[List[Dict[str, Any]]]:
        """Liste tous les utilisateurs (admin seulement)"""
        try:
            if not self.check_permission(token, 'manage_users'):
                return None
            
            users_list = []
            for user in self.users.values():
                users_list.append({
                    'username': user.username,
                    'email': user.email,
                    'role': user.role.value,
                    'status': user.status.value,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                })
            
            return users_list
            
        except Exception as e:
            self.error_handler.log_error(
                e, "AuthService", "list_users",
                ErrorSeverity.MEDIUM, ErrorCategory.SERVICE
            )
            return None
    
    def _cleanup_loop(self):
        """Boucle de nettoyage des tokens expirés"""
        while self.running:
            try:
                now = datetime.now()
                
                # Nettoyer les tokens d'accès expirés
                expired_tokens = [
                    token for token, auth_token in self.active_tokens.items()
                    if now > auth_token.expires_at
                ]
                for token in expired_tokens:
                    del self.active_tokens[token]
                
                # Nettoyer les refresh tokens expirés
                expired_refresh_tokens = [
                    token for token, auth_token in self.refresh_tokens.items()
                    if now > auth_token.expires_at
                ]
                for token in expired_refresh_tokens:
                    del self.refresh_tokens[token]
                
                # Nettoyer les sessions inactives (plus de 24h)
                inactive_sessions = [
                    session_id for session_id, session in self.active_sessions.items()
                    if now - session['last_activity'] > timedelta(hours=24)
                ]
                for session_id in inactive_sessions:
                    del self.active_sessions[session_id]
                
                if expired_tokens or expired_refresh_tokens or inactive_sessions:
                    self.logger.debug(f"Nettoyage: {len(expired_tokens)} tokens, {len(expired_refresh_tokens)} refresh tokens, {len(inactive_sessions)} sessions")
                
                time.sleep(300)  # Nettoyer toutes les 5 minutes
                
            except Exception as e:
                self.error_handler.log_error(
                    e, "AuthService", "_cleanup_loop",
                    ErrorSeverity.LOW, ErrorCategory.SERVICE
                )
                time.sleep(60)
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'authentification"""
        return {
            'total_users': len(self.users),
            'active_tokens': len(self.active_tokens),
            'refresh_tokens': len(self.refresh_tokens),
            'active_sessions': len(self.active_sessions),
            'locked_users': sum(1 for user in self.users.values() if user.status == AuthStatus.LOCKED),
            'disabled_users': sum(1 for user in self.users.values() if user.status == AuthStatus.DISABLED)
        }
