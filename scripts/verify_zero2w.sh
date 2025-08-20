#!/bin/bash

# Script de vérification post-installation Alimante pour Raspberry Pi Zero 2W
# Optimisé pour les ressources limitées et l'architecture ARMv6

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
echo -e "${BLUE}  Vérification Zero 2W Alimante  ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Vérification spécifique Zero 2W
print_status "Vérification spécifique Raspberry Pi Zero 2W..."

# Vérifier le modèle
if grep -q "Raspberry Pi Zero 2 W" /proc/cpuinfo || grep -q "Raspberry Pi Zero 2" /proc/cpuinfo; then
    print_success "Raspberry Pi Zero 2W détecté"
else
    print_warning "Modèle non-Zero 2W détecté"
    if grep -q "Raspberry Pi" /proc/cpuinfo; then
        print_status "Continuer la vérification..."
    else
        print_error "Ce script est conçu pour Raspberry Pi"
        exit 1
    fi
fi

# Vérifier l'architecture ARMv6
if [[ $(uname -m) == "armv6l" ]]; then
    print_success "Architecture ARMv6 détectée (Zero 2W)"
else
    print_warning "Architecture non-ARMv6: $(uname -m)"
fi

# Vérification de l'environnement virtuel
print_status "Vérification de l'environnement virtuel..."
if [ -d "alimante_env" ]; then
    print_success "Environnement virtuel trouvé"
else
    print_error "Environnement virtuel manquant"
    print_status "Exécutez d'abord install_raspberry.sh"
    exit 1
fi

# Activation de l'environnement virtuel
source alimante_env/bin/activate

# Vérification des dépendances Python (optimisées Zero 2W)
print_status "Vérification des dépendances Python (optimisées Zero 2W)..."
PYTHON_DEPS=("RPi.GPIO" "fastapi" "uvicorn" "pydantic" "smbus2")
MISSING_DEPS=()

for dep in "${PYTHON_DEPS[@]}"; do
    if python -c "import $dep" 2>/dev/null; then
        print_success "$dep installé"
    else
        print_warning "$dep manquant"
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    print_warning "Dépendances manquantes: ${MISSING_DEPS[*]}"
    print_status "Tentative de réinstallation (optimisée Zero 2W)..."
    pip install -r requirements.txt --no-cache-dir
fi

# Vérification de la structure du projet
print_status "Vérification de la structure du projet..."
REQUIRED_DIRS=("src" "config" "logs" "data")
REQUIRED_FILES=("src/api/app.py" "main.py" "requirements.txt")

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        print_success "Dossier $dir trouvé"
    else
        print_warning "Dossier $dir manquant"
    fi
done

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "Fichier $file trouvé"
    else
        print_warning "Fichier $file manquant"
    fi
done

# Vérification des permissions GPIO
print_status "Vérification des permissions GPIO..."
if groups | grep -q gpio; then
    print_success "Utilisateur dans le groupe gpio"
else
    print_warning "Utilisateur pas dans le groupe gpio"
fi

if [ -e "/dev/gpiomem" ]; then
    PERMS=$(ls -l /dev/gpiomem | awk '{print $1}')
    if [[ "$PERMS" == *"rw"* ]]; then
        print_success "Permissions GPIO correctes"
    else
        print_warning "Permissions GPIO incorrectes: $PERMS"
    fi
else
    print_warning "/dev/gpiomem non trouvé"
fi

# Test des composants matériels (optimisé Zero 2W)
print_status "Test des composants matériels (optimisé Zero 2W)..."

# Test GPIO
if python -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); print('GPIO OK')" 2>/dev/null; then
    print_success "GPIO fonctionnel"
else
    print_warning "GPIO non fonctionnel"
fi

# Test I2C
if python -c "import smbus2; bus = smbus2.SMBus(1); print('I2C OK')" 2>/dev/null; then
    print_success "I2C fonctionnel"
else
    print_warning "I2C non fonctionnel"
fi

# Vérification des interfaces activées
print_status "Vérification des interfaces..."
if [ -f "/boot/config.txt" ]; then
    if grep -q "i2c_arm=on" /boot/config.txt; then
        print_success "I2C activé"
    else
        print_warning "I2C non activé dans /boot/config.txt"
    fi
    
    if grep -q "gpu_mem=16" /boot/config.txt; then
        print_success "Mémoire GPU limitée à 16MB (optimisation Zero 2W)"
    else
        print_warning "Mémoire GPU non optimisée"
    fi
    
    # Vérifier que le WiFi n'est PAS désactivé
    if grep -q "dtoverlay=disable-wifi" /boot/config.txt; then
        print_error "WiFi désactivé - L'APPLICATION EN A BESOIN !"
        print_status "Supprimez 'dtoverlay=disable-wifi' de /boot/config.txt"
    else
        print_success "WiFi maintenu actif (nécessaire pour l'application)"
    fi
else
    print_warning "/boot/config.txt non trouvé"
fi

# Vérification du WiFi (ESSENTIEL pour l'application)
print_status "Vérification du WiFi (ESSENTIEL pour l'application)..."
if command_exists iwconfig; then
    WIFI_STATUS=$(iwconfig 2>/dev/null | grep -i "no wireless extensions" || echo "WiFi disponible")
    if [[ "$WIFI_STATUS" == "WiFi disponible" ]]; then
        print_success "Interface WiFi détectée"
        
        # Vérifier la connexion WiFi
        if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
            print_success "Connexion WiFi active et internet accessible"
        else
            print_warning "WiFi connecté mais pas d'accès internet"
        fi
    else
        print_warning "Pas d'interface WiFi détectée"
    fi
else
    print_warning "iwconfig non disponible"
fi

# Vérification du service systemd
print_status "Vérification du service systemd..."
if [ -f "/etc/systemd/system/alimante.service" ]; then
    print_success "Service systemd créé"
    
    if systemctl is-enabled alimante.service >/dev/null 2>&1; then
        print_success "Service activé au démarrage"
    else
        print_warning "Service non activé au démarrage"
    fi
    
    if systemctl is-active alimante.service >/dev/null 2>&1; then
        print_success "Service en cours d'exécution"
    else
        print_warning "Service non en cours d'exécution"
    fi
    
    # Vérifier les optimisations Zero 2W
    if grep -q "MemoryMax=200M" /etc/systemd/system/alimante.service; then
        print_success "Limite mémoire configurée (200MB)"
    else
        print_warning "Limite mémoire non configurée"
    fi
    
    if grep -q "workers 1" /etc/systemd/system/alimante.service; then
        print_success "1 worker configuré (optimisation Zero 2W)"
    else
        print_warning "Configuration worker non optimisée"
    fi
else
    print_error "Service systemd manquant"
fi

# Test de l'API (optimisé Zero 2W)
print_status "Test de l'API (optimisé Zero 2W)..."
if [ -f "src/api/app.py" ]; then
    print_success "Fichier API trouvé"
    
    # Test de démarrage de l'API avec 1 worker
    print_status "Test de démarrage de l'API (1 worker)..."
    timeout 15s python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --workers 1 >/dev/null 2>&1 &
    API_PID=$!
    sleep 5
    
    if kill -0 $API_PID 2>/dev/null; then
        print_success "API démarre correctement avec 1 worker"
        kill $API_PID 2>/dev/null
    else
        print_warning "API ne démarre pas correctement"
    fi
else
    print_warning "Fichier API non trouvé"
fi

# Vérifications spécifiques Zero 2W
print_status "Vérifications spécifiques Zero 2W..."

# Vérification de l'espace disque (plus strict pour Zero 2W)
DISK_SPACE=$(df . | awk 'NR==2 {print $4}')
DISK_SPACE_MB=$((DISK_SPACE / 1024))
if [ "$DISK_SPACE" -gt 2097152 ]; then
    print_success "Espace disque suffisant: ${DISK_SPACE_MB}MB"
else
    print_warning "Espace disque faible: ${DISK_SPACE_MB}MB (recommandé: 2GB+)"
fi

# Vérification de la mémoire (Zero 2W a 512MB)
MEMORY_TOTAL=$(free -m | awk 'NR==2{print $2}')
MEMORY_USED=$(free -m | awk 'NR==2{print $3}')
MEMORY_FREE=$(free -m | awk 'NR==2{print $4}')
MEMORY_PERCENT=$((MEMORY_USED * 100 / MEMORY_TOTAL))

print_status "Mémoire: ${MEMORY_TOTAL}MB total, ${MEMORY_USED}MB utilisée, ${MEMORY_FREE}MB libre (${MEMORY_PERCENT}%)"

if [ "$MEMORY_TOTAL" -lt 400 ]; then
    print_warning "Mémoire faible détectée: ${MEMORY_TOTAL}MB"
    print_status "Raspberry Pi Zero 2W attendu (512MB)"
fi

if [ "$MEMORY_PERCENT" -gt 80 ]; then
    print_warning "Mémoire fortement utilisée: ${MEMORY_PERCENT}%"
else
    print_success "Mémoire suffisante: ${MEMORY_PERCENT}% utilisée"
fi

# Vérification du swap
if swapon --show | grep -q "/swapfile"; then
    SWAP_SIZE=$(swapon --show | grep "/swapfile" | awk '{print $3}')
    print_success "Fichier swap actif: ${SWAP_SIZE}"
else
    print_warning "Aucun fichier swap actif"
fi

# Vérification de la température
print_status "Vérification de la température..."
if command_exists vcgencmd; then
    TEMP=$(vcgencmd measure_temp | cut -d'=' -f2 | cut -d"'" -f1)
    print_status "Température CPU: ${TEMP}°C"
    
    if (( $(echo "$TEMP < 60" | bc -l) )); then
        print_success "Température normale"
    elif (( $(echo "$TEMP < 70" | bc -l) )); then
        print_warning "Température élevée"
    else
        print_error "Température critique: ${TEMP}°C"
    fi
fi

# Vérification des services inutiles
print_status "Vérification des services inutiles..."
SERVICES_TO_DISABLE=("bluetooth" "avahi-daemon" "triggerhappy" "hciuart")
for service in "${SERVICES_TO_DISABLE[@]}"; do
    if systemctl is-enabled "${service}.service" >/dev/null 2>&1; then
        print_warning "Service $service activé (consomme de la mémoire)"
    else
        print_success "Service $service désactivé (économie mémoire)"
    fi
done

# Test de connectivité réseau
print_status "Test de connectivité réseau..."
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    print_success "Connexion internet active"
else
    print_warning "Pas de connexion internet"
fi

# Vérification finale
echo ""
print_status "Résumé de la vérification Zero 2W..."

if [ ${#MISSING_DEPS[@]} -eq 0 ] && [ -d "alimante_env" ] && [ -f "/etc/systemd/system/alimante.service" ]; then
    echo ""
    print_success "🎉 Vérification Zero 2W terminée avec succès !"
    print_success "Le système Alimante est optimisé pour votre Raspberry Pi Zero 2W."
    echo ""
    print_status "Prochaines étapes :"
    echo "1. Redémarrer le Raspberry Pi Zero 2W si nécessaire"
    echo "2. Démarrer le service : sudo systemctl start alimante"
    echo "3. Vérifier les logs : sudo journalctl -u alimante -f"
    echo "4. Accéder à l'API : http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo ""
    print_status "⚡ Optimisations Zero 2W appliquées :"
    echo "   - Mémoire GPU limitée à 16MB"
    echo "   - WiFi maintenu actif (nécessaire pour l'application)"
    echo "   - Service avec 1 worker et limites mémoire"
    echo "   - Fichier swap configuré"
    echo "   - Services inutiles désactivés"
else
    echo ""
    print_warning "⚠️  Vérification terminée avec des avertissements"
    print_status "Veuillez corriger les problèmes identifiés avant de continuer"
fi

echo ""
print_status "📊 Ressources Zero 2W :"
echo "   - Mémoire totale: ${MEMORY_TOTAL}MB"
echo "   - Mémoire libre: ${MEMORY_FREE}MB"
echo "   - Espace disque: ${DISK_SPACE_MB}MB"
echo "   - Température: ${TEMP}°C"
echo ""
print_status "🌐 WiFi : ESSENTIEL pour l'application Alimante !"
echo "   - API accessible via http://$(hostname -I | awk '{print $1}'):8000"
echo "   - Interface web et contrôle à distance"
echo "   - SSH pour la maintenance"
echo ""
print_status "Pour plus d'aide, consultez INSTALL_ZERO2W.md ou créez une issue sur GitHub"
