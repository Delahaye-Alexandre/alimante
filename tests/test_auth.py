#!/usr/bin/env python3
"""
Tests pour le système d'authentification Alimante
Valide l'authentification JWT et les autorisations
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.auth import (
    AuthManager, 
    User, 
    create_user_token,
    log_auth_event
)
from utils.exceptions import ErrorCode, create_exception


def test_auth_manager_initialization():
    """Test l'initialisation du gestionnaire d'authentification"""
    print("🧪 Test initialisation AuthManager...")
    
    auth_manager = AuthManager()
    
    # Vérifier que les utilisateurs par défaut existent
    assert "admin" in auth_manager.users
    assert "user" in auth_manager.users
    
    # Vérifier les propriétés des utilisateurs
    admin_user = auth_manager.users["admin"]
    assert admin_user["username"] == "admin"
    assert admin_user["is_admin"] is True
    assert admin_user["is_active"] is True
    
    user_user = auth_manager.users["user"]
    assert user_user["username"] == "user"
    assert user_user["is_admin"] is False
    assert user_user["is_active"] is True
    
    print("✅ Initialisation AuthManager OK")


def test_password_hashing():
    """Test le hachage des mots de passe"""
    print("🧪 Test hachage des mots de passe...")
    
    auth_manager = AuthManager()
    
    # Test hachage
    password = "test123"
    hashed = auth_manager.get_password_hash(password)
    
    # Vérifier que le hash est différent du mot de passe original
    assert hashed != password
    assert len(hashed) > len(password)
    
    # Test vérification
    assert auth_manager.verify_password(password, hashed) is True
    assert auth_manager.verify_password("wrong_password", hashed) is False
    
    print("✅ Hachage des mots de passe OK")


def test_user_authentication():
    """Test l'authentification des utilisateurs"""
    print("🧪 Test authentification utilisateurs...")
    
    auth_manager = AuthManager()
    
    # Test authentification réussie
    user = auth_manager.authenticate_user("admin", "admin123")
    assert user is not None
    assert user.username == "admin"
    assert user.is_admin is True
    
    user = auth_manager.authenticate_user("user", "user123")
    assert user is not None
    assert user.username == "user"
    assert user.is_admin is False
    
    # Test authentification échouée
    user = auth_manager.authenticate_user("admin", "wrong_password")
    assert user is None
    
    user = auth_manager.authenticate_user("nonexistent", "password")
    assert user is None
    
    print("✅ Authentification utilisateurs OK")


def test_token_creation():
    """Test la création de tokens JWT"""
    print("🧪 Test création de tokens...")
    
    auth_manager = AuthManager()
    
    # Créer un utilisateur de test
    test_user = User(username="test", email="test@test.com", is_admin=False)
    
    # Créer un token
    token = auth_manager.create_access_token({"sub": test_user.username})
    
    # Vérifier que le token est une chaîne
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Vérifier le token
    payload = auth_manager.verify_token(token)
    assert payload is not None
    assert payload["sub"] == test_user.username
    
    print("✅ Création de tokens OK")


def test_token_verification():
    """Test la vérification de tokens"""
    print("🧪 Test vérification de tokens...")
    
    auth_manager = AuthManager()
    
    # Créer un token valide
    token = auth_manager.create_access_token({"sub": "admin"})
    
    # Vérifier le token
    payload = auth_manager.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "admin"
    
    # Test token invalide
    invalid_token = "invalid.token.here"
    payload = auth_manager.verify_token(invalid_token)
    assert payload is None
    
    print("✅ Vérification de tokens OK")


def test_token_expiration():
    """Test l'expiration des tokens"""
    print("🧪 Test expiration des tokens...")
    
    auth_manager = AuthManager()
    
    # Créer un token avec expiration courte
    from datetime import timedelta
    token = auth_manager.create_access_token(
        {"sub": "admin"}, 
        expires_delta=timedelta(seconds=1)
    )
    
    # Vérifier que le token est valide immédiatement
    payload = auth_manager.verify_token(token)
    assert payload is not None
    
    # Attendre l'expiration
    import time
    time.sleep(2)
    
    # Vérifier que le token est expiré
    payload = auth_manager.verify_token(token)
    assert payload is None
    
    print("✅ Expiration des tokens OK")


def test_user_creation():
    """Test la création d'utilisateurs"""
    print("🧪 Test création d'utilisateurs...")
    
    auth_manager = AuthManager()
    
    # Créer un nouvel utilisateur
    new_user_data = {
        "username": "newuser",
        "email": "newuser@test.com",
        "hashed_password": auth_manager.get_password_hash("newpass123"),
        "is_active": True,
        "is_admin": False
    }
    
    auth_manager.users["newuser"] = new_user_data
    
    # Tester l'authentification du nouvel utilisateur
    user = auth_manager.authenticate_user("newuser", "newpass123")
    assert user is not None
    assert user.username == "newuser"
    assert user.is_admin is False
    
    print("✅ Création d'utilisateurs OK")


def test_admin_authorization():
    """Test les autorisations administrateur"""
    print("🧪 Test autorisations administrateur...")
    
    auth_manager = AuthManager()
    
    # Créer des tokens pour admin et user
    admin_token = auth_manager.create_access_token({"sub": "admin"})
    user_token = auth_manager.create_access_token({"sub": "user"})
    
    # Vérifier les tokens
    admin_payload = auth_manager.verify_token(admin_token)
    user_payload = auth_manager.verify_token(user_token)
    
    assert admin_payload is not None
    assert user_payload is not None
    
    # Simuler la vérification des droits admin
    admin_user_data = auth_manager.users["admin"]
    user_user_data = auth_manager.users["user"]
    
    assert admin_user_data["is_admin"] is True
    assert user_user_data["is_admin"] is False
    
    print("✅ Autorisations administrateur OK")


def test_auth_logging():
    """Test le logging des événements d'authentification"""
    print("🧪 Test logging d'authentification...")
    
    # Créer un dossier temporaire
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        # Tester le logging d'événements
        log_auth_event("test_login", "testuser", True, {"ip": "127.0.0.1"})
        log_auth_event("test_login", "testuser", False, {"reason": "wrong_password"})
        
        # Vérifier que les logs ont été créés
        log_files = list(Path("logs").glob("*.log"))
        assert len(log_files) > 0
        
        print("✅ Logging d'authentification OK")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)


def test_error_handling():
    """Test la gestion d'erreurs d'authentification"""
    print("🧪 Test gestion d'erreurs d'authentification...")
    
    auth_manager = AuthManager()
    
    # Test avec utilisateur inexistant
    user = auth_manager.authenticate_user("nonexistent", "password")
    assert user is None
    
    # Test avec mot de passe incorrect
    user = auth_manager.authenticate_user("admin", "wrong_password")
    assert user is None
    
    # Test avec token invalide
    payload = auth_manager.verify_token("invalid.token")
    assert payload is None
    
    # Test création d'exception d'authentification
    auth_exc = create_exception(
        ErrorCode.API_UNAUTHORIZED,
        "Test erreur d'authentification",
        {"username": "test"}
    )
    
    assert auth_exc.error_code == ErrorCode.API_UNAUTHORIZED
    assert "Test erreur d'authentification" in str(auth_exc)
    
    print("✅ Gestion d'erreurs d'authentification OK")


def main():
    """Exécute tous les tests d'authentification"""
    print("🧪 Tests du système d'authentification Alimante")
    print("=" * 60)
    
    tests = [
        ("Initialisation AuthManager", test_auth_manager_initialization),
        ("Hachage des mots de passe", test_password_hashing),
        ("Authentification utilisateurs", test_user_authentication),
        ("Création de tokens", test_token_creation),
        ("Vérification de tokens", test_token_verification),
        ("Expiration des tokens", test_token_expiration),
        ("Création d'utilisateurs", test_user_creation),
        ("Autorisations administrateur", test_admin_authorization),
        ("Logging d'authentification", test_auth_logging),
        ("Gestion d'erreurs", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        try:
            test_func()
            print(f"✅ {test_name} - PASSÉ")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} - ÉCHOUÉ: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 Tous les tests d'authentification sont passés !")
        print("✅ Le système d'authentification fonctionne correctement.")
        print("\n🔐 Informations de connexion par défaut:")
        print("   Admin: username=admin, password=admin123")
        print("   User:  username=user,  password=user123")
    else:
        print("⚠️ Certains tests d'authentification ont échoué.")
        print("🔧 Vérifiez les erreurs ci-dessus.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 