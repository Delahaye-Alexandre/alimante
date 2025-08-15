#!/usr/bin/env python3
"""
Diagnostic complet de l'application Alimante
Identifie toutes les incohérences et problèmes potentiels
"""

import os
import sys
import json
import importlib
import inspect
from typing import Dict, List, Any, Set
from pathlib import Path

class DiagnosticComplet:
    """Classe pour effectuer un diagnostic complet de l'application"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.project_root = Path(__file__).parent
        
    def run_diagnostic(self):
        """Exécute le diagnostic complet"""
        print("🔍 DIAGNOSTIC COMPLET DE L'APPLICATION ALIMANTE")
        print("=" * 60)
        
        self.check_project_structure()
        self.check_imports_and_dependencies()
        self.check_configuration_files()
        self.check_controller_consistency()
        self.check_api_consistency()
        self.check_gpio_configuration()
        self.check_method_signatures()
        self.check_error_handling()
        self.check_logging_consistency()
        
        self.print_report()
        
    def check_project_structure(self):
        """Vérifie la structure du projet"""
        print("\n📁 Vérification de la structure du projet...")
        
        required_dirs = [
            "src", "config", "tests", "docs", "logs"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                self.errors.append(f"Répertoire requis manquant: {dir_name}")
            else:
                self.info.append(f"✅ Répertoire {dir_name} trouvé")
                
        # Vérifier les fichiers requis
        required_files = [
            "main.py", "requirements.txt", "setup.py", "Readme.md"
        ]
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                self.errors.append(f"Fichier requis manquant: {file_name}")
            else:
                self.info.append(f"✅ Fichier {file_name} trouvé")
    
    def check_imports_and_dependencies(self):
        """Vérifie les imports et dépendances"""
        print("\n📦 Vérification des imports et dépendances...")
        
        # Vérifier requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                requirements = f.read()
                
            # Vérifier les dépendances critiques
            critical_deps = ["RPi.GPIO", "Flask", "FastAPI"]
            for dep in critical_deps:
                if dep in requirements:
                    self.info.append(f"✅ Dépendance critique trouvée: {dep}")
                else:
                    self.warnings.append(f"⚠️ Dépendance critique manquante: {dep}")
        
        # Vérifier les imports dans main.py
        main_file = self.project_root / "main.py"
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()
                
            # Vérifier les imports critiques
            critical_imports = [
                "src.utils.config_manager",
                "src.utils.gpio_manager",
                "src.controllers.temperature_controller"
            ]
            
            for imp in critical_imports:
                if imp in content:
                    self.info.append(f"✅ Import critique trouvé: {imp}")
                else:
                    self.warnings.append(f"⚠️ Import critique manquant: {imp}")
    
    def check_configuration_files(self):
        """Vérifie les fichiers de configuration"""
        print("\n⚙️ Vérification des fichiers de configuration...")
        
        config_dir = self.project_root / "config"
        if not config_dir.exists():
            self.errors.append("Répertoire de configuration manquant")
            return
            
        # Vérifier config.json principal
        main_config = config_dir / "config.json"
        if main_config.exists():
            try:
                with open(main_config, 'r') as f:
                    config_data = json.load(f)
                    
                # Vérifier les sections requises
                required_sections = [
                    "system_info", "hardware", "communication", 
                    "location", "species_profiles", "system_control",
                    "safety", "api", "logging", "performance"
                ]
                
                for section in required_sections:
                    if section in config_data:
                        self.info.append(f"✅ Section de configuration: {section}")
                    else:
                        self.warnings.append(f"⚠️ Section de configuration manquante: {section}")
                        
            except json.JSONDecodeError as e:
                self.errors.append(f"Erreur JSON dans config.json: {e}")
        else:
            self.errors.append("Fichier de configuration principal manquant")
            
        # Vérifier gpio_config.json
        gpio_config = config_dir / "gpio_config.json"
        if gpio_config.exists():
            try:
                with open(gpio_config, 'r') as f:
                    gpio_data = json.load(f)
                    
                # Vérifier les sections GPIO requises
                gpio_sections = ["gpio_pins", "pin_assignments", "hardware_config"]
                for section in gpio_sections:
                    if section in gpio_data:
                        self.info.append(f"✅ Section GPIO: {section}")
                    else:
                        self.warnings.append(f"⚠️ Section GPIO manquante: {section}")
                        
            except json.JSONDecodeError as e:
                self.errors.append(f"Erreur JSON dans gpio_config.json: {e}")
        else:
            self.warnings.append("Configuration GPIO manquante")
            
        # Vérifier les configurations d'espèces
        species_dir = config_dir / "orthopteres" / "mantidae"
        if species_dir.exists():
            species_files = list(species_dir.glob("*.json"))
            if species_files:
                self.info.append(f"✅ {len(species_files)} configuration(s) d'espèce trouvée(s)")
                
                # Vérifier mantis_religiosa.json
                mantis_config = species_dir / "mantis_religiosa.json"
                if mantis_config.exists():
                    try:
                        with open(mantis_config, 'r') as f:
                            mantis_data = json.load(f)
                            
                        # Vérifier les sections requises
                        required_species_sections = [
                            "temperature", "humidity", "feeding", "lighting"
                        ]
                        
                        for section in required_species_sections:
                            if section in mantis_data:
                                self.info.append(f"✅ Configuration espèce: {section}")
                            else:
                                self.warnings.append(f"⚠️ Configuration espèce manquante: {section}")
                                
                    except json.JSONDecodeError as e:
                        self.errors.append(f"Erreur JSON dans mantis_religiosa.json: {e}")
                else:
                    self.warnings.append("Configuration mantis_religiosa manquante")
            else:
                self.warnings.append("Aucune configuration d'espèce trouvée")
        else:
            self.warnings.append("Répertoire des espèces manquant")
    
    def check_controller_consistency(self):
        """Vérifie la cohérence des contrôleurs"""
        print("\n🎮 Vérification de la cohérence des contrôleurs...")
        
        controllers_dir = self.project_root / "src" / "controllers"
        if not controllers_dir.exists():
            self.errors.append("Répertoire des contrôleurs manquant")
            return
            
        # Vérifier les contrôleurs requis
        required_controllers = [
            "temperature_controller.py",
            "humidity_controller.py", 
            "light_controller.py",
            "feeding_controller.py",
            "base_controller.py"
        ]
        
        for controller in required_controllers:
            controller_path = controllers_dir / controller
            if controller_path.exists():
                self.info.append(f"✅ Contrôleur trouvé: {controller}")
                
                # Vérifier la cohérence des méthodes
                if controller != "base_controller.py":
                    self.check_controller_methods(controller_path)
            else:
                self.errors.append(f"Contrôleur requis manquant: {controller}")
    
    def check_controller_methods(self, controller_path: Path):
        """Vérifie la cohérence des méthodes d'un contrôleur"""
        try:
            with open(controller_path, 'r') as f:
                content = f.read()
                
            # Vérifier les méthodes requises
            required_methods = [
                "check_status", "get_status", "control"
            ]
            
            for method in required_methods:
                if f"def {method}" in content:
                    self.info.append(f"  ✅ Méthode {method} trouvée")
                else:
                    self.warnings.append(f"  ⚠️ Méthode {method} manquante dans {controller_path.name}")
                    
            # Vérifier l'héritage de BaseController
            if "BaseController" in content:
                self.info.append(f"  ✅ Hérite de BaseController")
            else:
                self.warnings.append(f"  ⚠️ N'hérite pas de BaseController")
                
        except Exception as e:
            self.errors.append(f"Erreur lors de la vérification de {controller_path.name}: {e}")
    
    def check_api_consistency(self):
        """Vérifie la cohérence de l'API"""
        print("\n🌐 Vérification de la cohérence de l'API...")
        
        api_dir = self.project_root / "src" / "api"
        if not api_dir.exists():
            self.warnings.append("Répertoire API manquant")
            return
            
        # Vérifier app.py
        app_file = api_dir / "app.py"
        if app_file.exists():
            try:
                with open(app_file, 'r') as f:
                    content = f.read()
                    
                # Vérifier les imports des contrôleurs
                controller_imports = [
                    "TemperatureController", "HumidityController", 
                    "LightController", "FeedingController"
                ]
                
                for controller in controller_imports:
                    if controller in content:
                        self.info.append(f"✅ Import contrôleur API: {controller}")
                    else:
                        self.warnings.append(f"⚠️ Import contrôleur API manquant: {controller}")
                        
                # Vérifier les endpoints
                required_endpoints = [
                    "/api/status", "/api/control", "/api/health"
                ]
                
                for endpoint in required_endpoints:
                    if endpoint in content:
                        self.info.append(f"✅ Endpoint trouvé: {endpoint}")
                    else:
                        self.warnings.append(f"⚠️ Endpoint manquant: {endpoint}")
                        
            except Exception as e:
                self.errors.append(f"Erreur lors de la vérification de l'API: {e}")
        else:
            self.warnings.append("Fichier API principal manquant")
    
    def check_gpio_configuration(self):
        """Vérifie la configuration GPIO"""
        print("\n🔌 Vérification de la configuration GPIO...")
        
        gpio_config = self.project_root / "config" / "gpio_config.json"
        if not gpio_config.exists():
            self.warnings.append("Configuration GPIO manquante")
            return
            
        try:
            with open(gpio_config, 'r') as f:
                gpio_data = json.load(f)
                
            # Vérifier les pins critiques
            critical_pins = [
                "TEMP_HUMIDITY_PIN", "HEATING_RELAY_PIN", 
                "HUMIDITY_RELAY_PIN", "LIGHT_RELAY_PIN"
            ]
            
            pin_assignments = gpio_data.get("pin_assignments", {})
            for pin in critical_pins:
                if pin in pin_assignments:
                    self.info.append(f"✅ Pin GPIO configuré: {pin}")
                else:
                    self.warnings.append(f"⚠️ Pin GPIO manquant: {pin}")
                    
            # Vérifier la cohérence des pins
            used_pins = set()
            for pin_name, pin_number in pin_assignments.items():
                if pin_number in used_pins:
                    self.errors.append(f"Pin {pin_number} utilisé plusieurs fois: {pin_name}")
                used_pins.add(pin_number)
                
        except Exception as e:
            self.errors.append(f"Erreur lors de la vérification GPIO: {e}")
    
    def check_method_signatures(self):
        """Vérifie la cohérence des signatures de méthodes"""
        print("\n📝 Vérification des signatures de méthodes...")
        
        # Vérifier les méthodes critiques dans les contrôleurs
        critical_methods = {
            "control_temperature": "bool",
            "control_humidity": "bool", 
            "control_lighting": "bool",
            "control_feeding": "bool"
        }
        
        controllers_dir = self.project_root / "src" / "controllers"
        if controllers_dir.exists():
            for controller_file in controllers_dir.glob("*.py"):
                if controller_file.name == "base_controller.py":
                    continue
                    
                try:
                    with open(controller_file, 'r') as f:
                        content = f.read()
                        
                    for method_name, return_type in critical_methods.items():
                        if method_name in content:
                            # Vérifier le type de retour
                            if f"-> {return_type}" in content:
                                self.info.append(f"✅ Signature correcte: {controller_file.name}.{method_name}")
                            else:
                                self.warnings.append(f"⚠️ Type de retour incorrect: {controller_file.name}.{method_name}")
                                
                except Exception as e:
                    self.errors.append(f"Erreur lors de la vérification de {controller_file.name}: {e}")
    
    def check_error_handling(self):
        """Vérifie la gestion d'erreurs"""
        print("\n🚨 Vérification de la gestion d'erreurs...")
        
        # Vérifier les exceptions personnalisées
        exceptions_file = self.project_root / "src" / "utils" / "exceptions.py"
        if exceptions_file.exists():
            try:
                with open(exceptions_file, 'r') as f:
                    content = f.read()
                    
                # Vérifier les classes d'exception
                exception_classes = [
                    "AlimanteException", "SystemException", "GPIOException", "ControllerException"
                ]
                
                for exc_class in exception_classes:
                    if exc_class in content:
                        self.info.append(f"✅ Classe d'exception trouvée: {exc_class}")
                    else:
                        self.warnings.append(f"⚠️ Classe d'exception manquante: {exc_class}")
                        
            except Exception as e:
                self.errors.append(f"Erreur lors de la vérification des exceptions: {e}")
        else:
            self.warnings.append("Fichier d'exceptions manquant")
            
        # Vérifier la gestion d'erreurs dans main.py
        main_file = self.project_root / "main.py"
        if main_file.exists():
            try:
                with open(main_file, 'r') as f:
                    content = f.read()
                    
                # Vérifier les blocs try-catch
                if "try:" in content and "except" in content:
                    self.info.append("✅ Gestion d'erreurs trouvée dans main.py")
                else:
                    self.warnings.append("⚠️ Gestion d'erreurs manquante dans main.py")
                    
            except Exception as e:
                self.errors.append(f"Erreur lors de la vérification de main.py: {e}")
    
    def check_logging_consistency(self):
        """Vérifie la cohérence du système de logging"""
        print("\n📊 Vérification de la cohérence du logging...")
        
        # Vérifier le fichier de configuration de logging
        logging_config = self.project_root / "src" / "utils" / "logging_config.py"
        if logging_config.exists():
            try:
                with open(logging_config, 'r') as f:
                    content = f.read()
                    
                # Vérifier les fonctions de logging
                logging_functions = [
                    "get_logger", "log_system_start", "log_system_stop", "log_controller_action"
                ]
                
                for func in logging_functions:
                    if f"def {func}" in content:
                        self.info.append(f"✅ Fonction de logging trouvée: {func}")
                    else:
                        self.warnings.append(f"⚠️ Fonction de logging manquante: {func}")
                        
            except Exception as e:
                self.errors.append(f"Erreur lors de la vérification du logging: {e}")
        else:
            self.warnings.append("Configuration de logging manquante")
            
        # Vérifier la configuration YAML de logging
        logging_yaml = self.project_root / "config" / "logging.yaml"
        if logging_yaml.exists():
            self.info.append("✅ Configuration YAML de logging trouvée")
        else:
            self.warnings.append("⚠️ Configuration YAML de logging manquante")
    
    def print_report(self):
        """Affiche le rapport de diagnostic"""
        print("\n" + "=" * 60)
        print("📋 RAPPORT DE DIAGNOSTIC")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ ERREURS CRITIQUES ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
                
        if self.warnings:
            print(f"\n⚠️ AVERTISSEMENTS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
                
        if self.info:
            print(f"\n✅ INFORMATIONS ({len(self.info)}):")
            for info in self.info:
                print(f"  • {info}")
                
        # Résumé
        print(f"\n📊 RÉSUMÉ:")
        print(f"  • Erreurs critiques: {len(self.errors)}")
        print(f"  • Avertissements: {len(self.warnings)}")
        print(f"  • Informations: {len(self.info)}")
        
        if self.errors:
            print(f"\n🚨 L'application présente {len(self.errors)} erreur(s) critique(s) à corriger!")
        elif self.warnings:
            print(f"\n⚠️ L'application présente {len(self.warnings)} avertissement(s) à examiner.")
        else:
            print(f"\n🎉 Aucun problème critique détecté! L'application semble cohérente.")
            
        # Recommandations
        if self.errors:
            print(f"\n🔧 RECOMMANDATIONS:")
            print(f"  • Corriger toutes les erreurs critiques avant de déployer")
            print(f"  • Tester l'application après chaque correction")
            
        if self.warnings:
            print(f"\n📝 POINTS À VÉRIFIER:")
            print(f"  • Examiner les avertissements pour améliorer la robustesse")
            print(f"  • Vérifier la cohérence des configurations")

if __name__ == "__main__":
    diagnostic = DiagnosticComplet()
    diagnostic.run_diagnostic()
