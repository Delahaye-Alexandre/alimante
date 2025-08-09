#!/usr/bin/env python3
"""
Script de diagnostic complet pour Alimante
Identifie tous les problèmes potentiels avant le déploiement
"""

import sys
import os
import json
import importlib
from pathlib import Path

def check_imports():
    """Vérifie que tous les modules peuvent être importés"""
    print("🔍 Vérification des imports...")
    
    modules_to_check = [
        'src.utils.logging_config',
        'src.utils.exceptions',
        'src.utils.error_handler',
        'src.utils.auth',
        'src.utils.config_manager',
        'src.utils.gpio_manager',
        'src.services.system_service',
        'src.services.control_service',
        'src.services.config_service',
        'src.services.sensor_service',
        'src.controllers.base_controller',
        'src.controllers.temperature_controller',
        'src.controllers.humidity_controller',
        'src.controllers.light_controller',
        'src.controllers.feeding_controller',
        'src.controllers.fan_controller',
        'src.controllers.ultrasonic_mist_controller',
        'src.api.app',
        'src.api.models'
    ]
    
    failed_imports = []
    for module in modules_to_check:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            failed_imports.append((module, str(e)))
    
    return failed_imports

def check_config_files():
    """Vérifie que tous les fichiers de configuration existent"""
    print("\n🔍 Vérification des fichiers de configuration...")
    
    config_files = [
        'config/config.json',
        'config/gpio_config.json',
        'config/classification_reference.json',
        'config/orthopteres/mantidae/mantis_religiosa.json',
        'config/orthopteres/mantidae/mantis_religiosa.json',
        'config/orthopteres/mantidae/sphodromantis_viridis.json',
        'config/orthopteres/mantidae/hymenopus_coronatus.json',
        'config/lepidopteres/saturniidae/saturnia_pyri.json',
        'config/dipteres/drosophilidae/drosophila_melanogaster.json',
        'config/coleopteres/tenebrionidae/tenebrio_molitor.json',
        'config/coleopteres/tenebrionidae/zophobas_morio.json'
    ]
    
    missing_files = []
    for file_path in config_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (manquant)")
            missing_files.append(file_path)
    
    return missing_files

def check_json_syntax():
    """Vérifie la syntaxe JSON des fichiers de configuration"""
    print("\n🔍 Vérification de la syntaxe JSON...")
    
    json_files = [
        'config/config.json',
        'config/gpio_config.json',
        'config/classification_reference.json',
        'config/orthopteres/mantidae/mantis_religiosa.json'
    ]
    
    json_errors = []
    for file_path in json_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"  ✅ {file_path}")
            except json.JSONDecodeError as e:
                print(f"  ❌ {file_path}: {e}")
                json_errors.append((file_path, str(e)))
        else:
            print(f"  ⚠️ {file_path} (fichier manquant)")
    
    return json_errors

def check_system_config():
    """Vérifie la configuration système"""
    print("\n🔍 Vérification de la configuration système...")
    
    try:
        from src.utils.config_manager import SystemConfig
        from src.services.config_service import config_service
        
        # Test de chargement
        config = config_service.load_system_config()
        print(f"  ✅ Configuration système chargée")
        print(f"     - Port série: {config.serial_port}")
        print(f"     - Baud rate: {config.baud_rate}")
        print(f"     - Espèce: {config.species_name}")
        print(f"     - Nom commun: {config.common_name}")
        
        return None
    except Exception as e:
        print(f"  ❌ Erreur configuration système: {e}")
        return str(e)

def check_gpio_config():
    """Vérifie la configuration GPIO"""
    print("\n🔍 Vérification de la configuration GPIO...")
    
    try:
        with open('config/gpio_config.json', 'r', encoding='utf-8') as f:
            gpio_config = json.load(f)
        
        # Vérifier la structure avec 'pins'
        if 'pins' in gpio_config:
            print(f"  ✅ Section pins")
            pins = gpio_config['pins']
            
            required_pin_sections = ['sensors', 'actuators', 'inputs', 'status']
            missing_sections = []
            
            for section in required_pin_sections:
                if section in pins:
                    print(f"    ✅ Sous-section {section}")
                else:
                    print(f"    ❌ Sous-section {section} manquante")
                    missing_sections.append(section)
        else:
            print(f"  ❌ Section pins manquante")
            return ['pins']
        
        # Vérifier power_supply
        if 'power_supply' in gpio_config:
            print(f"  ✅ Section power_supply")
        else:
            print(f"  ❌ Section power_supply manquante")
            missing_sections.append('power_supply')
        
        return missing_sections
    except Exception as e:
        print(f"  ❌ Erreur configuration GPIO: {e}")
        return [str(e)]

def check_dependencies():
    """Vérifie les dépendances Python"""
    print("\n🔍 Vérification des dépendances...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'PyJWT',
        'passlib',
        'python-jose',
        'websockets',
        'sqlalchemy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (manquant)")
            missing_packages.append(package)
    
    return missing_packages

def check_file_structure():
    """Vérifie la structure des fichiers"""
    print("\n🔍 Vérification de la structure des fichiers...")
    
    required_dirs = [
        'src',
        'src/api',
        'src/controllers',
        'src/services',
        'src/utils',
        'config',
        'tests',
        'logs'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ (manquant)")
            missing_dirs.append(dir_path)
    
    return missing_dirs

def main():
    """Exécute le diagnostic complet"""
    print("🔧 Diagnostic complet Alimante")
    print("=" * 50)
    
    # Créer le dossier logs s'il n'existe pas
    os.makedirs('logs', exist_ok=True)
    
    # Exécuter tous les diagnostics
    import_errors = check_imports()
    missing_configs = check_config_files()
    json_errors = check_json_syntax()
    config_error = check_system_config()
    gpio_errors = check_gpio_config()
    missing_deps = check_dependencies()
    missing_dirs = check_file_structure()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 50)
    
    total_errors = (
        len(import_errors) + 
        len(missing_configs) + 
        len(json_errors) + 
        (1 if config_error else 0) +
        len(gpio_errors) + 
        len(missing_deps) + 
        len(missing_dirs)
    )
    
    if total_errors == 0:
        print("🎉 Aucun problème détecté !")
        print("✅ Le système est prêt pour le déploiement.")
    else:
        print(f"⚠️ {total_errors} problème(s) détecté(s):")
        
        if import_errors:
            print(f"  - {len(import_errors)} erreur(s) d'import")
        if missing_configs:
            print(f"  - {len(missing_configs)} fichier(s) de config manquant(s)")
        if json_errors:
            print(f"  - {len(json_errors)} erreur(s) JSON")
        if config_error:
            print(f"  - 1 erreur de configuration système")
        if gpio_errors:
            print(f"  - {len(gpio_errors)} erreur(s) GPIO")
        if missing_deps:
            print(f"  - {len(missing_deps)} dépendance(s) manquante(s)")
        if missing_dirs:
            print(f"  - {len(missing_dirs)} dossier(s) manquant(s)")
    
    return total_errors == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
