#!/bin/bash

# Script de correction des erreurs d'import pour Alimante
# Corrige les problèmes de noms de fonctions et modules

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Correction des Erreurs d'Import ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Arrêter le service
print_status "Arrêt du service alimante..."
sudo systemctl stop alimante

# Vérifier que nous sommes dans le bon dossier
if [ ! -f "src/api/app.py" ]; then
    print_error "Ce script doit être exécuté depuis le dossier racine du projet"
    exit 1
fi

print_status "Correction des erreurs d'import..."

# Correction 1: setup_logger -> setup_logging
print_status "Correction: setup_logger -> setup_logging"
if grep -r "setup_logger" src/ tests/ --include="*.py" >/dev/null 2>&1; then
    print_warning "Erreurs d'import setup_logger trouvées, correction..."
    
    # Corriger dans src/
    find src/ -name "*.py" -exec sed -i 's/setup_logger/setup_logging/g' {} \;
    
    # Corriger dans tests/
    find tests/ -name "*.py" -exec sed -i 's/setup_logger/setup_logging/g' {} \;
    
    print_success "Correction setup_logger terminée"
else
    print_success "Aucune erreur setup_logger trouvée"
fi

# Correction 2: Vérifier les autres imports problématiques
print_status "Vérification des autres imports problématiques..."

# Vérifier les imports relatifs
PROBLEMATIC_IMPORTS=(
    "from ..utils.logging_config import setup_logger"
    "from ..utils.logging_config import setup_logger"
)

for import_pattern in "${PROBLEMATIC_IMPORTS[@]}"; do
    if grep -r "$import_pattern" src/ --include="*.py" >/dev/null 2>&1; then
        print_warning "Import problématique trouvé: $import_pattern"
        # La correction a déjà été faite plus haut
    fi
done

# Vérification de la syntaxe Python
print_status "Vérification de la syntaxe Python..."
PYTHON_FILES=$(find src/ -name "*.py" -o -name "*.py")
SYNTAX_ERRORS=0

for file in $PYTHON_FILES; do
    if python3 -m py_compile "$file" 2>/dev/null; then
        print_success "✓ $file"
    else
        print_error "✗ $file - Erreur de syntaxe"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    print_success "Tous les fichiers Python ont une syntaxe valide"
else
    print_error "$SYNTAX_ERRORS fichier(s) avec des erreurs de syntaxe"
fi

# Test d'import des modules principaux
print_status "Test d'import des modules principaux..."
cd src

# Test 1: logging_config
if python3 -c "from utils.logging_config import setup_logging; print('✓ logging_config OK')" 2>/dev/null; then
    print_success "Module logging_config importé avec succès"
else
    print_error "Erreur d'import logging_config"
fi

# Test 2: auth
if python3 -c "from utils.auth import *; print('✓ auth OK')" 2>/dev/null; then
    print_success "Module auth importé avec succès"
else
    print_error "Erreur d'import auth"
fi

# Test 3: api app
if python3 -c "from api.app import *; print('✓ api app OK')" 2>/dev/null; then
    print_success "Module api app importé avec succès"
else
    print_error "Erreur d'import api app"
fi

cd ..

# Redémarrer le service
print_status "Redémarrage du service alimante..."
sudo systemctl start alimante

# Vérifier le statut
sleep 5
if sudo systemctl is-active alimante >/dev/null 2>&1; then
    print_success "🎉 Service alimante démarré avec succès !"
    
    # Vérifier les logs
    print_status "Vérification des logs..."
    if sudo journalctl -u alimante --no-pager -n 10 | grep -q "error\|Error\|ERROR"; then
        print_warning "Des erreurs sont encore présentes dans les logs"
        print_status "Vérifiez les logs: sudo journalctl -u alimante -f"
    else
        print_success "Aucune erreur détectée dans les logs récents"
    fi
    
else
    print_error "❌ Service ne démarre toujours pas"
    print_status "Vérifiez les logs: sudo journalctl -u alimante -f"
fi

echo ""
print_status "📚 Résumé des corrections :"
echo "   - Erreurs d'import setup_logger corrigées"
echo "   - Syntaxe Python vérifiée"
echo "   - Modules principaux testés"
echo "   - Service redémarré"
echo ""
print_status "🔍 Pour vérifier :"
echo "   - Statut: sudo systemctl status alimante"
echo "   - Logs: sudo journalctl -u alimante -f"
echo "   - API: curl http://localhost:8000/health"
