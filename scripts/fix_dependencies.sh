#!/bin/bash

# Script de correction des dépendances manquantes pour Alimante
# Résout les problèmes de modules Python manquants

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
echo -e "${BLUE}  Correction des Dépendances     ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Arrêter le service
print_status "Arrêt du service alimante..."
sudo systemctl stop alimante

# Vérifier que l'environnement virtuel existe
if [ ! -d "alimante_env" ]; then
    print_error "Environnement virtuel non trouvé"
    print_status "Exécutez d'abord install_raspberry.sh"
    exit 1
fi

# Activer l'environnement virtuel
print_status "Activation de l'environnement virtuel..."
source alimante_env/bin/activate

# Vérifier les dépendances manquantes
print_status "Vérification des dépendances manquantes..."

# Liste des modules critiques
CRITICAL_MODULES=("jwt" "fastapi" "uvicorn" "pydantic" "RPi.GPIO" "smbus2")
MISSING_MODULES=()

for module in "${CRITICAL_MODULES[@]}"; do
    if python -c "import $module" 2>/dev/null; then
        print_success "$module installé"
    else
        print_warning "$module manquant"
        MISSING_MODULES+=("$module")
    fi
done

# Installer les dépendances manquantes
if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
    print_status "Installation des modules manquants..."
    
    # Installer PyJWT spécifiquement
    if [[ " ${MISSING_MODULES[@]} " =~ " jwt " ]]; then
        print_status "Installation de PyJWT..."
        pip install PyJWT
    fi
    
    # Installer toutes les dépendances depuis requirements.txt
    if [ -f "requirements.txt" ]; then
        print_status "Installation des dépendances depuis requirements.txt..."
        pip install -r requirements.txt --no-cache-dir
    else
        print_warning "requirements.txt non trouvé, installation des dépendances de base..."
        pip install fastapi uvicorn pydantic PyJWT RPi.GPIO smbus2
    fi
else
    print_success "Toutes les dépendances critiques sont installées"
fi

# Vérification finale
print_status "Vérification finale des dépendances..."
ALL_GOOD=true

for module in "${CRITICAL_MODULES[@]}"; do
    if python -c "import $module" 2>/dev/null; then
        print_success "$module fonctionne correctement"
    else
        print_error "$module ne fonctionne toujours pas"
        ALL_GOOD=false
    fi
done

if [ "$ALL_GOOD" = true ]; then
    print_success "🎉 Toutes les dépendances sont maintenant installées !"
    
    # Redémarrer le service
    print_status "Redémarrage du service alimante..."
    sudo systemctl start alimante
    
    # Vérifier le statut
    sleep 3
    if sudo systemctl is-active alimante >/dev/null 2>&1; then
        print_success "Service alimante démarré avec succès !"
        print_status "Vérifiez le statut : sudo systemctl status alimante"
        print_status "Vérifiez les logs : sudo journalctl -u alimante -f"
    else
        print_warning "Service ne démarre toujours pas"
        print_status "Vérifiez les logs : sudo journalctl -u alimante -f"
    fi
else
    print_error "❌ Certaines dépendances ne fonctionnent toujours pas"
    print_status "Vérifiez l'installation manuellement"
fi

echo ""
print_status "📚 Pour plus d'aide :"
echo "   - Vérifiez les logs : sudo journalctl -u alimante -f"
echo "   - Testez manuellement : python -c 'import jwt; print(\"JWT OK\")'"
echo "   - Consultez la documentation du projet"
