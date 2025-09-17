#!/usr/bin/env python3
"""
Analyseur de fonctions orphelines Alimante
Identifie les fonctions/méthodes qui ne sont jamais appelées
"""

import sys
import os
import re
import ast
from pathlib import Path
from collections import defaultdict

class FunctionAnalyzer:
    """Analyseur de fonctions orphelines"""
    
    def __init__(self):
        self.defined_functions = {}  # {file: {function_name: line_number}}
        self.called_functions = set()  # Set de toutes les fonctions appelées
        self.imported_modules = set()  # Modules importés
        self.class_methods = {}  # {class_name: {method_name: line_number}}
        
    def analyze_file(self, file_path):
        """Analyse un fichier Python"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse l'AST
            tree = ast.parse(content, filename=file_path)
            
            # Analyser les définitions de fonctions
            self._analyze_definitions(tree, file_path)
            
            # Analyser les appels de fonctions
            self._analyze_calls(tree, file_path)
            
        except Exception as e:
            print(f"Erreur analyse {file_path}: {e}")
    
    def _analyze_definitions(self, tree, file_path):
        """Analyse les définitions de fonctions et méthodes"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Fonction normale
                if file_path not in self.defined_functions:
                    self.defined_functions[file_path] = {}
                self.defined_functions[file_path][node.name] = node.lineno
                
            elif isinstance(node, ast.ClassDef):
                # Méthodes de classe
                class_name = node.name
                if class_name not in self.class_methods:
                    self.class_methods[class_name] = {}
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        self.class_methods[class_name][item.name] = item.lineno
    
    def _analyze_calls(self, tree, file_path):
        """Analyse les appels de fonctions"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Appel de fonction direct
                if isinstance(node.func, ast.Name):
                    self.called_functions.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    # Méthode d'objet (obj.method())
                    if isinstance(node.func.value, ast.Name):
                        self.called_functions.add(f"{node.func.value.id}.{node.func.attr}")
                    elif isinstance(node.func.value, ast.Attribute):
                        # self.method() ou obj.attr.method()
                        self.called_functions.add(node.func.attr)
                elif isinstance(node.func, ast.Constant):
                    # Appel dynamique
                    if isinstance(node.func.value, str):
                        self.called_functions.add(node.func.value)
    
    def find_orphaned_functions(self):
        """Trouve les fonctions orphelines"""
        orphaned = []
        
        # Analyser les fonctions définies
        for file_path, functions in self.defined_functions.items():
            for func_name, line_num in functions.items():
                if func_name not in self.called_functions:
                    # Vérifier si c'est une fonction spéciale (__init__, __str__, etc.)
                    if not func_name.startswith('__') or func_name in ['__init__', '__str__', '__repr__', '__del__']:
                        orphaned.append({
                            'file': file_path,
                            'function': func_name,
                            'line': line_num,
                            'type': 'function'
                        })
        
        # Analyser les méthodes de classe
        for class_name, methods in self.class_methods.items():
            for method_name, line_num in methods.items():
                full_name = f"{class_name}.{method_name}"
                if full_name not in self.called_functions and method_name not in self.called_functions:
                    # Vérifier si c'est une méthode spéciale
                    if not method_name.startswith('__') or method_name in ['__init__', '__str__', '__repr__', '__del__']:
                        orphaned.append({
                            'file': f"class {class_name}",
                            'function': method_name,
                            'line': line_num,
                            'type': 'method'
                        })
        
        return orphaned
    
    def analyze_directory(self, directory):
        """Analyse un répertoire complet"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    self.analyze_file(file_path)
    
    def get_statistics(self):
        """Retourne les statistiques d'analyse"""
        total_functions = sum(len(funcs) for funcs in self.defined_functions.values())
        total_methods = sum(len(methods) for methods in self.class_methods.values())
        total_defined = total_functions + total_methods
        
        orphaned = self.find_orphaned_functions()
        orphaned_count = len(orphaned)
        
        return {
            'total_functions': total_functions,
            'total_methods': total_methods,
            'total_defined': total_defined,
            'orphaned_count': orphaned_count,
            'coverage': ((total_defined - orphaned_count) / total_defined * 100) if total_defined > 0 else 100
        }

def main():
    """Fonction principale"""
    print("🔍 Analyse des fonctions orphelines Alimante")
    print("=" * 60)
    
    analyzer = FunctionAnalyzer()
    
    # Analyser le répertoire src/
    if os.path.exists('src'):
        analyzer.analyze_directory('src')
        print(f"📁 Répertoire analysé: src/")
    else:
        print("❌ Répertoire src/ non trouvé")
        return 1
    
    # Obtenir les statistiques
    stats = analyzer.get_statistics()
    
    print(f"\n📊 Statistiques:")
    print(f"   - Fonctions définies: {stats['total_functions']}")
    print(f"   - Méthodes définies: {stats['total_methods']}")
    print(f"   - Total défini: {stats['total_defined']}")
    print(f"   - Fonctions orphelines: {stats['orphaned_count']}")
    print(f"   - Couverture: {stats['coverage']:.1f}%")
    
    # Trouver les fonctions orphelines
    orphaned = analyzer.find_orphaned_functions()
    
    if orphaned:
        print(f"\n❌ Fonctions orphelines trouvées ({len(orphaned)}):")
        
        # Grouper par fichier
        by_file = defaultdict(list)
        for func in orphaned:
            by_file[func['file']].append(func)
        
        for file_path, functions in by_file.items():
            print(f"\n📄 {file_path}:")
            for func in functions:
                print(f"   - {func['function']} (ligne {func['line']}) - {func['type']}")
        
        # Identifier les plus critiques
        critical_orphaned = [f for f in orphaned if any(keyword in f['function'].lower() 
                                 for keyword in ['test', 'debug', 'temp', 'old', 'unused'])]
        
        if critical_orphaned:
            print(f"\n🗑️ Fonctions probablement inutiles ({len(critical_orphaned)}):")
            for func in critical_orphaned:
                print(f"   - {func['file']}:{func['function']} (ligne {func['line']})")
        
        return 1
    else:
        print("\n✅ Aucune fonction orpheline trouvée !")
        return 0

if __name__ == "__main__":
    sys.exit(main())
