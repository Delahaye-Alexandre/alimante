#!/usr/bin/env python3
"""
Analyse des connexions des composants Alimante
Vérifie que tous les services et contrôleurs sont bien "branchés" et effectifs
"""

import os
import sys
import ast
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple

class ComponentConnectionAnalyzer:
    """
    Analyseur des connexions entre composants
    """
    
    def __init__(self, src_dir: str = "src"):
        self.src_dir = Path(src_dir)
        self.logger = logging.getLogger(__name__)
        
        # Composants identifiés
        self.services = set()
        self.controllers = set()
        self.drivers = set()
        
        # Connexions identifiées
        self.initializations = {}  # Qui initialise quoi
        self.imports = {}  # Qui importe quoi
        self.instantiations = {}  # Qui instancie quoi
        
        # Problèmes détectés
        self.orphaned_components = set()
        self.missing_initializations = set()
        self.circular_dependencies = set()
        
    def analyze_codebase(self) -> Dict[str, any]:
        """
        Analyse complète du codebase
        
        Returns:
            Dictionnaire contenant l'analyse
        """
        print("🔍 Analyse des connexions des composants Alimante")
        print("=" * 60)
        
        # 1. Identifier tous les composants
        self._identify_components()
        
        # 2. Analyser les imports et initialisations
        self._analyze_imports_and_initializations()
        
        # 3. Identifier les composants orphelins
        self._identify_orphaned_components()
        
        # 4. Vérifier les connexions dans main.py
        self._analyze_main_connections()
        
        # 5. Générer le rapport
        return self._generate_report()
    
    def _identify_components(self) -> None:
        """Identifie tous les composants du système"""
        print("📋 Identification des composants...")
        
        # Services
        services_dir = self.src_dir / "services"
        if services_dir.exists():
            for py_file in services_dir.glob("*.py"):
                if py_file.name != "__init__.py":
                    class_name = self._extract_class_name(py_file)
                    if class_name and "Service" in class_name:
                        self.services.add(class_name)
        
        # Contrôleurs
        controllers_dir = self.src_dir / "controllers"
        if controllers_dir.exists():
            for py_file in controllers_dir.rglob("*.py"):
                if py_file.name != "__init__.py":
                    class_name = self._extract_class_name(py_file)
                    if class_name and "Controller" in class_name:
                        self.controllers.add(class_name)
        
        # Drivers
        drivers_dir = self.src_dir / "controllers" / "drivers"
        if drivers_dir.exists():
            for py_file in drivers_dir.glob("*.py"):
                if py_file.name != "__init__.py":
                    class_name = self._extract_class_name(py_file)
                    if class_name and "Driver" in class_name:
                        self.drivers.add(class_name)
        
        print(f"   Services: {len(self.services)}")
        print(f"   Contrôleurs: {len(self.controllers)}")
        print(f"   Drivers: {len(self.drivers)}")
    
    def _extract_class_name(self, file_path: Path) -> str:
        """Extrait le nom de la classe principale d'un fichier"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    return node.name
            
            return None
        except Exception as e:
            self.logger.error(f"Erreur analyse {file_path}: {e}")
            return None
    
    def _analyze_imports_and_initializations(self) -> None:
        """Analyse les imports et initialisations"""
        print("🔗 Analyse des imports et initialisations...")
        
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                file_imports = set()
                file_instantiations = set()
                
                for node in ast.walk(tree):
                    # Analyser les imports
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            file_imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            file_imports.add(node.module)
                            for alias in node.names:
                                file_imports.add(f"{node.module}.{alias.name}")
                    
                    # Analyser les instantiations
                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            file_instantiations.add(node.func.id)
                        elif isinstance(node.func, ast.Attribute):
                            if isinstance(node.func.value, ast.Name):
                                file_instantiations.add(f"{node.func.value.id}.{node.func.attr}")
                
                self.imports[str(py_file)] = file_imports
                self.instantiations[str(py_file)] = file_instantiations
                
            except Exception as e:
                self.logger.error(f"Erreur analyse {py_file}: {e}")
    
    def _identify_orphaned_components(self) -> None:
        """Identifie les composants orphelins (non utilisés)"""
        print("🔍 Identification des composants orphelins...")
        
        all_components = self.services | self.controllers | self.drivers
        used_components = set()
        
        # Vérifier les instantiations
        for file_path, instantiations in self.instantiations.items():
            for instantiation in instantiations:
                for component in all_components:
                    if component in instantiation:
                        used_components.add(component)
        
        # Vérifier les imports
        for file_path, imports in self.imports.items():
            for import_name in imports:
                for component in all_components:
                    if component in import_name:
                        used_components.add(component)
        
        self.orphaned_components = all_components - used_components
    
    def _analyze_main_connections(self) -> None:
        """Analyse les connexions dans main.py"""
        print("🏠 Analyse des connexions dans main.py...")
        
        main_file = Path("main.py")
        if not main_file.exists():
            print("   ❌ Fichier main.py non trouvé")
            return
        
        try:
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            main_initializations = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if isinstance(node.value, ast.Call):
                                if isinstance(node.value.func, ast.Name):
                                    main_initializations.add(node.value.func.id)
                                elif isinstance(node.value.func, ast.Attribute):
                                    if isinstance(node.value.func.value, ast.Name):
                                        main_initializations.add(f"{node.value.func.value.id}.{node.value.func.attr}")
            
            self.initializations["main.py"] = main_initializations
            
        except Exception as e:
            self.logger.error(f"Erreur analyse main.py: {e}")
    
    def _generate_report(self) -> Dict[str, any]:
        """Génère le rapport d'analyse"""
        print("\\n📊 RAPPORT D'ANALYSE DES CONNEXIONS")
        print("=" * 60)
        
        # Composants identifiés
        print("\\n📋 COMPOSANTS IDENTIFIÉS")
        print("-" * 30)
        print(f"Services ({len(self.services)}):")
        for service in sorted(self.services):
            print(f"  ✅ {service}")
        
        print(f"\\nContrôleurs ({len(self.controllers)}):")
        for controller in sorted(self.controllers):
            print(f"  ✅ {controller}")
        
        print(f"\\nDrivers ({len(self.drivers)}):")
        for driver in sorted(self.drivers):
            print(f"  ✅ {driver}")
        
        # Composants orphelins
        print("\\n🔍 COMPOSANTS ORPHELINS")
        print("-" * 30)
        if self.orphaned_components:
            for component in sorted(self.orphaned_components):
                print(f"  ❌ {component} (non utilisé)")
        else:
            print("  ✅ Aucun composant orphelin détecté")
        
        # Connexions dans main.py
        print("\\n🏠 CONNEXIONS DANS MAIN.PY")
        print("-" * 30)
        if "main.py" in self.initializations:
            for init in sorted(self.initializations["main.py"]):
                print(f"  ✅ {init}")
        else:
            print("  ❌ Aucune initialisation détectée dans main.py")
        
        # Problèmes détectés
        print("\\n⚠️ PROBLÈMES DÉTECTÉS")
        print("-" * 30)
        
        problems = []
        
        # Vérifier les services manquants dans main.py
        expected_main_services = {
            "EventBus", "SafetyService", "UIController", "MainLoop"
        }
        if "main.py" in self.initializations:
            missing_services = expected_main_services - self.initializations["main.py"]
            if missing_services:
                problems.append(f"Services manquants dans main.py: {missing_services}")
        
        # Vérifier les services non initialisés
        services_not_in_main = self.services - {"EventBus", "SafetyService", "UIController", "MainLoop"}
        if services_not_in_main:
            problems.append(f"Services non initialisés dans main.py: {services_not_in_main}")
        
        if problems:
            for problem in problems:
                print(f"  ❌ {problem}")
        else:
            print("  ✅ Aucun problème majeur détecté")
        
        # Recommandations
        print("\\n💡 RECOMMANDATIONS")
        print("-" * 30)
        
        recommendations = []
        
        if self.orphaned_components:
            recommendations.append("Supprimer ou connecter les composants orphelins")
        
        if "main.py" in self.initializations:
            missing_services = expected_main_services - self.initializations["main.py"]
            if missing_services:
                recommendations.append("Ajouter les services manquants dans main.py")
        
        if not recommendations:
            recommendations.append("Tous les composants semblent bien connectés")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        return {
            'services': list(self.services),
            'controllers': list(self.controllers),
            'drivers': list(self.drivers),
            'orphaned_components': list(self.orphaned_components),
            'main_initializations': list(self.initializations.get("main.py", [])),
            'problems': problems,
            'recommendations': recommendations
        }

def main():
    """Fonction principale"""
    analyzer = ComponentConnectionAnalyzer()
    report = analyzer.analyze_codebase()
    
    print("\\n🎯 RÉSUMÉ")
    print("=" * 60)
    print(f"Total composants: {len(report['services']) + len(report['controllers']) + len(report['drivers'])}")
    print(f"Composants orphelins: {len(report['orphaned_components'])}")
    print(f"Problèmes détectés: {len(report['problems'])}")
    
    if len(report['orphaned_components']) == 0 and len(report['problems']) == 0:
        print("\\n🎉 TOUS LES COMPOSANTS SONT BIEN CONNECTÉS !")
        return True
    else:
        print("\\n⚠️ CERTAINS COMPOSANTS NÉCESSITENT UNE ATTENTION")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
