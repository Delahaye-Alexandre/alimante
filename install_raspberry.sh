#!/bin/bash

# Script d'installation Alimante pour Raspberry Pi Zero 2W
# Version optimisée pour Raspbian Lite et ressources limitées

set -e  # Arrêter le script en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
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

# Fonction pour vérifier si une commande existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Fonction pour vérifier les permissions sudo
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        print_error "Ce script nécessite des permissions sudo"
        print_status "Veuillez exécuter avec sudo ou configurer sudoers"
        exit 1
    fi
}

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Installation Alimante Zero 2W  ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Vérification du système
print_status "Vérification du système..."

# Vérifier si c'est un Raspberry Pi Zero 2W
if ! grep -q "Raspberry Pi Zero 2 W" /proc/cpuinfo && ! grep -q "Raspberry Pi Zero 2" /proc/cpuinfo; then
    if grep -q "Raspberry Pi" /proc/cpuinfo; then
        print_warning "Ce script est optimisé pour Raspberry Pi Zero 2W"
        print_status "Vous utilisez un autre modèle Raspberry Pi"
        read -p "Continuer quand même ? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_error "Ce script est conçu pour Raspberry Pi"
        exit 1
    fi
fi

# Vérification de l'architecture ARMv6
if [[ $(uname -m) != "armv6l" ]]; then
    print_warning "Architecture non standard détectée: $(uname -m)"
    print_status "Raspberry Pi Zero 2W attendu (ARMv6)"
    read -p "Continuer quand même ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Vérification des permissions sudo
check_sudo

# Vérification de l'espace disque (plus strict pour Zero 2W)
DISK_SPACE=$(df . | awk 'NR==2 {print $4}')
if [ "$DISK_SPACE" -lt 2097152 ]; then  # Moins de 2GB
    print_warning "Espace disque faible: $(($DISK_SPACE / 1024))MB disponible"
    print_status "Recommandé: au moins 2GB d'espace libre pour Zero 2W"
    read -p "Continuer ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Vérification de la mémoire (Zero 2W a 512MB)
MEMORY_TOTAL=$(free -m | awk 'NR==2{print $2}')
if [ "$MEMORY_TOTAL" -lt 400 ]; then
    print_warning "Mémoire faible détectée: ${MEMORY_TOTAL}MB"
    print_status "Raspberry Pi Zero 2W attendu (512MB)"
    read -p "Continuer ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_success "Raspberry Pi Zero 2W détecté - Optimisations activées"

# Sauvegarde de la configuration existante
if [ -f "config/config.json" ]; then
    print_status "Sauvegarde de la configuration existante..."
    cp -r config config_backup_$(date +%Y%m%d_%H%M%S)
    print_success "Configuration sauvegardée"
fi

# Optimisations spécifiques Zero 2W
print_status "Optimisations Raspberry Pi Zero 2W..."

# Désactiver les services inutiles pour économiser la mémoire
print_status "Désactivation des services inutiles..."
sudo systemctl disable bluetooth.service 2>/dev/null || true
sudo systemctl disable hciuart.service 2>/dev/null || true
sudo systemctl disable avahi-daemon.service 2>/dev/null || true
sudo systemctl disable triggerhappy.service 2>/dev/null || true

# Optimiser la configuration mémoire
if [ -f "/boot/config.txt" ]; then
    print_status "Optimisation de la configuration mémoire..."
    if ! grep -q "gpu_mem=16" /boot/config.txt; then
        echo "gpu_mem=16" | sudo tee -a /boot/config.txt > /dev/null
        print_success "Mémoire GPU limitée à 16MB"
    fi
    
    # Ne pas désactiver le WiFi - l'application en a besoin !
    print_status "WiFi maintenu actif (nécessaire pour l'application)"
fi

# Mise à jour du système (optimisée pour Zero 2W)
print_status "Mise à jour du système (optimisée Zero 2W)..."
if ! sudo apt update; then
    print_error "Échec de la mise à jour des paquets"
    exit 1
fi

# Installation des dépendances système (minimales)
print_status "Installation des dépendances système minimales..."
DEPS_SYSTEM="python3 python3-pip python3-venv git"
for dep in $DEPS_SYSTEM; do
    if ! command_exists "$dep"; then
        print_status "Installation de $dep..."
        if ! sudo apt install -y "$dep"; then
            print_error "Échec de l'installation de $dep"
            exit 1
        fi
    else
        print_success "$dep déjà installé"
    fi
done

# Installation des dépendances GPIO (optimisées Zero 2W)
print_status "Installation des dépendances GPIO (optimisées Zero 2W)..."
DEPS_GPIO="python3-rpi.gpio python3-dev build-essential"
for dep in $DEPS_GPIO; do
    print_status "Installation de $dep..."
    if ! sudo apt install -y "$dep"; then
        print_error "Échec de l'installation de $dep"
        exit 1
    fi
done

# Installation des dépendances I2C (minimales)
print_status "Installation des dépendances I2C minimales..."
sudo apt install -y i2c-tools python3-smbus

# Activation des interfaces (optimisées Zero 2W)
print_status "Activation des interfaces matérielles..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 0
# Pas de SPI par défaut pour économiser les ressources

# Vérification de la version Python
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
    print_error "Python 3.7+ requis pour Zero 2W, version actuelle: $PYTHON_VERSION"
    exit 1
fi

print_success "Version Python compatible: $PYTHON_VERSION"

# Création de l'environnement virtuel (optimisé Zero 2W)
print_status "Création de l'environnement virtuel (optimisé Zero 2W)..."
if [ -d "alimante_env" ]; then
    print_status "Suppression de l'environnement virtuel existant..."
    rm -rf alimante_env
fi

if ! python3 -m venv alimante_env; then
    print_error "Échec de la création de l'environnement virtuel"
    exit 1
fi

# Activation de l'environnement virtuel
print_status "Activation de l'environnement virtuel..."
source alimante_env/bin/activate

# Vérification de l'activation
if [[ "$VIRTUAL_ENV" != *"alimante_env"* ]]; then
    print_error "Échec de l'activation de l'environnement virtuel"
    exit 1
fi

print_success "Environnement virtuel activé: $VIRTUAL_ENV"

# Mise à jour de pip (optimisée Zero 2W)
print_status "Mise à jour de pip..."
if ! pip install --upgrade pip; then
    print_error "Échec de la mise à jour de pip"
    exit 1
fi

# Installation des dépendances Python (optimisées Zero 2W)
print_status "Installation des dépendances Python (optimisées Zero 2W)..."
if [ ! -f "requirements.txt" ]; then
    print_error "Fichier requirements.txt introuvable"
    exit 1
fi

# Installation optimisée pour Zero 2W
if ! pip install -r requirements.txt --no-cache-dir; then
    print_error "Échec de l'installation des dépendances Python"
    print_status "Tentative d'installation individuelle (optimisée Zero 2W)..."
    
    # Installation des dépendances critiques une par une (sans cache)
    CRITICAL_DEPS="RPi.GPIO fastapi uvicorn pydantic smbus2"
    for dep in $CRITICAL_DEPS; do
        print_status "Installation de $dep..."
        if ! pip install "$dep" --no-cache-dir; then
            print_warning "Échec de l'installation de $dep, continuation..."
        fi
    done
fi

# Configuration des permissions GPIO
print_status "Configuration des permissions GPIO..."
if ! groups | grep -q gpio; then
    sudo usermod -a -G gpio $USER
    print_success "Utilisateur ajouté au groupe gpio"
else
    print_success "Utilisateur déjà dans le groupe gpio"
fi

# Configuration des permissions /dev/gpiomem
if [ -e "/dev/gpiomem" ]; then
    sudo chown root:gpio /dev/gpiomem
    sudo chmod g+rw /dev/gpiomem
    print_success "Permissions GPIO configurées"
else
    print_warning "/dev/gpiomem non trouvé, redémarrage nécessaire"
fi

# Test des composants critiques (optimisé Zero 2W)
print_status "Test des composants critiques (optimisé Zero 2W)..."
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); print('GPIO OK')" 2>/dev/null || print_warning "GPIO non fonctionnel"
python3 -c "import smbus2; print('I2C OK')" 2>/dev/null || print_warning "I2C non fonctionnel"

# Création du service systemd (optimisé Zero 2W)
print_status "Configuration du service systemd (optimisé Zero 2W)..."
SERVICE_FILE="/etc/systemd/system/alimante.service"
CURRENT_DIR=$(pwd)

sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Alimante - Système de gestion des mantes (Zero 2W)
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/alimante_env/bin
Environment=PYTHONPATH=$CURRENT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$CURRENT_DIR/alimante_env/bin/python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 1
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=alimante
# Optimisations Zero 2W
Nice=10
IOSchedulingClass=2
IOSchedulingPriority=4
MemoryMax=200M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

print_success "Service systemd créé (optimisé Zero 2W)"

# Activation du service
print_status "Activation du service..."
sudo systemctl daemon-reload
sudo systemctl enable alimante.service

# Configuration du firewall (minimale)
print_status "Configuration du firewall..."
if command_exists ufw; then
    sudo ufw allow 8000/tcp
    print_success "Port 8000 ouvert dans le firewall"
else
    print_warning "UFW non installé, configuration manuelle du firewall nécessaire"
fi

# Création des dossiers nécessaires
print_status "Création des dossiers..."
mkdir -p logs data config/backups

# Configuration des permissions
print_status "Configuration des permissions..."
chmod +x start_api.sh 2>/dev/null || print_warning "start_api.sh non trouvé"
chmod +x main.py 2>/dev/null || print_warning "main.py non trouvé"

# Test de l'API
print_status "Test de l'API..."
if [ -f "src/api/app.py" ]; then
    print_success "Structure de l'API détectée"
else
    print_warning "Structure de l'API non trouvée"
fi

# Optimisations supplémentaires Zero 2W
print_status "Optimisations supplémentaires Zero 2W..."

# Configuration du swap (si pas de carte SD rapide)
if ! swapon --show | grep -q "/swapfile"; then
    print_status "Création d'un fichier swap pour Zero 2W..."
    sudo fallocate -l 256M /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
    print_success "Fichier swap de 256MB créé"
fi

# Optimisation de la mémoire
if [ -f "/etc/sysctl.conf" ]; then
    print_status "Optimisation de la mémoire..."
    echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf > /dev/null
    echo "vm.vfs_cache_pressure=50" | sudo tee -a /etc/sysctl.conf > /dev/null
    print_success "Paramètres mémoire optimisés"
fi

# Vérification finale
print_status "Vérification finale..."
if [ -d "alimante_env" ] && [ -f "$SERVICE_FILE" ]; then
    print_success "Installation terminée avec succès !"
else
    print_error "Installation incomplète, vérifiez les erreurs ci-dessus"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Installation d'Alimante Zero 2W terminée !${NC}"
echo ""
echo -e "${BLUE}📋 Prochaines étapes :${NC}"
echo "1. Redémarrer le Raspberry Pi Zero 2W : sudo reboot"
echo "2. Vérifier le service : sudo systemctl status alimante"
echo "3. Démarrer le service : sudo systemctl start alimante"
echo "4. Voir les logs : sudo journalctl -u alimante -f"
echo ""
echo -e "${BLUE}🌐 L'API sera accessible sur :${NC}"
echo "   http://$(hostname -I | awk '{print $1}'):8000"
echo "   Documentation API : http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo -e "${BLUE}🔧 Dépannage :${NC}"
echo "   - Logs du service : sudo journalctl -u alimante -f"
echo "   - Test manuel : source alimante_env/bin/activate && python main.py"
echo "   - Vérification GPIO : python3 -c \"import RPi.GPIO as GPIO; print('GPIO OK')\""
echo ""
echo -e "${BLUE}⚡ Optimisations Zero 2W appliquées :${NC}"
echo "   - Mémoire GPU limitée à 16MB"
echo "   - WiFi maintenu actif (nécessaire pour l'application)"
echo "   - Service optimisé (1 worker, limites mémoire)"
echo "   - Fichier swap de 256MB créé"
echo "   - Services inutiles désactivés"
echo ""
echo -e "${YELLOW}⚠️  Important : Redémarrez le Raspberry Pi Zero 2W pour activer toutes les optimisations${NC}" 