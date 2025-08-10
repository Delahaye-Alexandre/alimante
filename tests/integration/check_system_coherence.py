#!/usr/bin/env python3
"""
Vérification de la cohérence du système Alimante
Vérifie que tous les composants sont cohérents et fonctionnels
"""

import os
import sys
import json
from pathlib import Path

def check_file_structure():
    """Vérifie la structure des fichiers"""
    print("📁 Vérification de la structure des fichiers...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "setup.py",
        "start_api.sh",
        "install_raspberry.sh",
        "test_gpio.py",
        "test_complete_system.py",
        "config/config.json",
        "config/pin_config.json",
        "src/__init__.py",
        "src/api/app.py",
        "src/utils/gpio_manager.py",
        "src/utils/config_manager.py",
        "src/utils/logging_config.py",
        "src/utils/exceptions.py",
        "src/utils/select_config.py",
        "src/controllers/__init__.py",
        "src/controllers/base_controller.py",
        "src/controllers/temperature_controller.py",
        "src/controllers/humidity_controller.py",
        "src/controllers/light_controller.py",
        "src/controllers/feeding_controller.py",
        "tests/test_main.py",
        "tests/test_system.py",
        "tests/test_temperature_controller.py",
        "mobile/README.md",
        "Readme.md",
        ".gitignore"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Fichiers manquants: {missing_files}")
        return False
    else:
        print("✅ Tous les fichiers requis sont présents")
        return True

def check_imports():
    """Vérifie que tous les imports fonctionnent"""
    print("🔍 Vérification des imports...")
    
    try:
        # Ajouter src au path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Test imports principaux
        from utils.config_manager import SystemConfig
        from utils.gpio_manager import GPIOManager, PinAssignments
        from controllers.temperature_controller import TemperatureController
        from controllers.humidity_controller import HumidityController
        from controllers.light_controller import LightController
        from controllers.feeding_controller import FeedingController
        from api.app import app
        
        print("✅ Tous les imports fonctionnent")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def check_config_files():
    """Vérifie les fichiers de configuration"""
    print("⚙️  Vérification des fichiers de configuration...")
    
    try:
        # Vérifier config.json
        with open('config/config.json', 'r') as f:
            config = json.load(f)
            required_keys = ['serial_port', 'baud_rate', 'location']
            for key in required_keys:
                if key not in config:
                    print(f"❌ Clé manquante dans config.json: {key}")
                    return False
        
        # Vérifier pin_config.json
        with open('config/pin_config.json', 'r') as f:
            gpio_config = json.load(f)
            required_sections = ['pins', 'servo_config', 'relay_config']
            for section in required_sections:
                if section not in gpio_config:
                    print(f"❌ Section manquante dans pin_config.json: {section}")
                    return False
        
        print("✅ Fichiers de configuration valides")
        return True
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return False

def check_requirements():
    """Vérifie les dépendances"""
    print("📦 Vérification des dépendances...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
            
        required_packages = [
            'fastapi',
            'uvicorn',
            'websockets',
            'RPi.GPIO',
            'pydantic',
            'astral',
            'pytest'
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Packages manquants: {missing_packages}")
            return False
        else:
            print("✅ Toutes les dépendances sont définies")
            return True
    except Exception as e:
        print(f"❌ Erreur requirements: {e}")
        return False

def check_obsolete_references():
    """Vérifie qu'il n'y a plus de références obsolètes"""
    print("🧹 Vérification des références obsolètes...")
    
    obsolete_terms = [
        'SerialManager',
        'serial_manager',
        'send_command',
        'Arduino',
        'mantcare'
    ]
    
    problematic_files = []
    
    for root, dirs, files in os.walk('.'):
        # Ignorer les dossiers git et cache
        if '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith(('.py', '.json', '.md', '.txt', '.sh')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for term in obsolete_terms:
                            if term in content and file_path not in problematic_files:
                                # Vérifier si c'est un commentaire ou documentation
                                if not content.strip().startswith('#') and term not in ['mantcare']:
                                    problematic_files.append(file_path)
                except:
                    pass
    
    if problematic_files:
        print(f"❌ Fichiers avec références obsolètes: {problematic_files}")
        return False
    else:
        print("✅ Aucune référence obsolète trouvée")
        return True

def check_gpio_coherence():
    """Vérifie la cohérence des pins GPIO"""
    print("🔌 Vérification de la cohérence GPIO...")
    
    try:
        from src.utils.gpio_manager import PinAssignments
        
        # Vérifier que tous les pins sont définis
        required_pins = [
            'TEMP_HUMIDITY_PIN',
            'LIGHT_SENSOR_PIN',
            'HEATING_RELAY_PIN',
            'HUMIDITY_RELAY_PIN',
            'FEEDING_SERVO_PIN',
            'LIGHT_RELAY_PIN',
            'STATUS_LED_PIN'
        ]
        
        missing_pins = []
        for pin in required_pins:
            if not hasattr(PinAssignments, pin):
                missing_pins.append(pin)
        
        if missing_pins:
            print(f"❌ Pins GPIO manquants: {missing_pins}")
            return False
        else:
            print("✅ Tous les pins GPIO sont définis")
            return True
    except Exception as e:
        print(f"❌ Erreur GPIO: {e}")
        return False

def main():
    """Vérification complète du système"""
    print("🔍 Vérification de la cohérence du système Alimante")
    print("=" * 60)
    
    checks = [
        ("Structure des fichiers", check_file_structure),
        ("Imports", check_imports),
        ("Configuration", check_config_files),
        ("Dépendances", check_requirements),
        ("Références obsolètes", check_obsolete_references),
        ("Cohérence GPIO", check_gpio_coherence)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 Vérification: {check_name}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append((check_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 Résumé de la vérification:")
    
    success_count = 0
    for check_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            success_count += 1
    
    print(f"\n📈 Résultat: {success_count}/{len(results)} vérifications réussies")
    
    if success_count == len(results):
        print("🎉 Toutes les vérifications sont réussies !")
        print("🚀 Le système Alimante est cohérent et prêt à fonctionner.")
        print("\n📋 Prochaines étapes:")
        print("1. Transférer sur Raspberry Pi")
        print("2. Exécuter: ./install_raspberry.sh")
        print("3. Tester: python3 test_gpio.py")
        print("4. Démarrer: ./start_api.sh")
    else:
        print("⚠️  Certaines vérifications ont échoué.")
        print("🔧 Corrigez les problèmes avant de déployer.")
    
    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 