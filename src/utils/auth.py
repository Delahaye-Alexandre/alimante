"""
Système d'authentification JWT pour Alimante
Authentification sécurisée avec tokens JWT
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .exceptions import create_exception, ErrorCode, AuthenticationException
from .logging_config import get_logger

logger = get_logger("auth")

# Configuration de sécurité
SECRET_KEY = os.getenv("ALIMANTE_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Gestionnaire de mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Sécurité HTTP
security = HTTPBearer()


@dataclass
class User:
    """Utilisateur du système"""
    username: str
    email: str
    is_active: bool = True
    is_admin: bool = False


class AuthManager:
    """Gestionnaire d'authentification"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        
        # Utilisateurs par défaut (en production, utiliser une base de données)
        self.users = {
            "admin": {
                "username": "admin",
                "email": "admin@alimante.com",
                "hashed_password": pwd_context.hash("admin123"),
                "is_active": True,
                "is_admin": True
            },
            "user": {
                "username": "user",
                "email": "user@alimante.com",
                "hashed_password": pwd_context.hash("user123"),
                "is_active": True,
                "is_admin": False
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash un mot de passe"""
        return pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authentifie un utilisateur"""
        try:
            user_data = self.users.get(username)
            if not user_data:
                logger.warning(f"Tentative de connexion avec utilisateur inexistant: {username}")
                return None
            
            if not self.verify_password(password, user_data["hashed_password"]):
                logger.warning(f"Mot de passe incorrect pour l'utilisateur: {username}")
                return None
            
            if not user_data["is_active"]:
                logger.warning(f"Tentative de connexion avec compte désactivé: {username}")
                return None
            
            logger.info(f"Connexion réussie pour l'utilisateur: {username}")
            return User(
                username=user_data["username"],
                email=user_data["email"],
                is_active=user_data["is_active"],
                is_admin=user_data["is_admin"]
            )
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'authentification: {e}")
            return None
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Crée un token JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"Token créé pour l'utilisateur: {data.get('sub')}")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Vérifie un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            
            if username is None:
                logger.warning("Token invalide: pas de sujet")
                return None
            
            # Vérifier que l'utilisateur existe toujours
            if username not in self.users:
                logger.warning(f"Token pour utilisateur inexistant: {username}")
                return None
            
            # Vérifier que l'utilisateur est toujours actif
            if not self.users[username]["is_active"]:
                logger.warning(f"Token pour utilisateur désactivé: {username}")
                return None
            
            logger.debug(f"Token vérifié pour l'utilisateur: {username}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expiré")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token invalide: {e}")
            return None
        except Exception as e:
            logger.exception(f"Erreur lors de la vérification du token: {e}")
            return None
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Récupère l'utilisateur actuel depuis le token"""
        token = credentials.credentials
        
        payload = self.verify_token(token)
        if payload is None:
            raise create_exception(
                ErrorCode.API_UNAUTHORIZED,
                "Token invalide ou expiré",
                {"token_provided": True}
            )
        
        username = payload.get("sub")
        user_data = self.users.get(username)
        
        if not user_data:
            raise create_exception(
                ErrorCode.API_UNAUTHORIZED,
                "Utilisateur non trouvé",
                {"username": username}
            )
        
        return User(
            username=user_data["username"],
            email=user_data["email"],
            is_active=user_data["is_active"],
            is_admin=user_data["is_admin"]
        )
    
    def require_admin(self, current_user: User = Depends(get_current_user)) -> User:
        """Vérifie que l'utilisateur est administrateur"""
        if not current_user.is_admin:
            logger.warning(f"Tentative d'accès admin par utilisateur non-admin: {current_user.username}")
            raise create_exception(
                ErrorCode.API_FORBIDDEN,
                "Accès administrateur requis",
                {"user": current_user.username, "required_role": "admin"}
            )
        
        return current_user


# Instance globale du gestionnaire d'authentification
auth_manager = AuthManager()


# Dépendances FastAPI
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dépendance FastAPI pour récupérer l'utilisateur actuel"""
    return auth_manager.get_current_user(credentials)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dépendance FastAPI pour vérifier les droits administrateur"""
    return auth_manager.require_admin(current_user)


# Modèles Pydantic pour l'API
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Modèle pour la réponse de token"""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Modèle pour les données du token"""
    username: Optional[str] = None


class UserLogin(BaseModel):
    """Modèle pour la connexion utilisateur"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Modèle pour la réponse utilisateur"""
    username: str
    email: str
    is_admin: bool
    is_active: bool


# Fonctions utilitaires
def create_user_token(user: User) -> Token:
    """Crée un token pour un utilisateur"""
    access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_manager.access_token_expire_minutes * 60
    )


def log_auth_event(event: str, username: str, success: bool, context: Optional[Dict[str, Any]] = None):
    """Log un événement d'authentification"""
    level = "INFO" if success else "WARNING"
    logger.log(
        logger.logger.level,
        f"🔐 {event} - {username}",
        {
            "event": event,
            "username": username,
            "success": success,
            "timestamp": datetime.now().isoformat()
        } | (context or {})
    ) 