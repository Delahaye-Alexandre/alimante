#!/bin/bash

# Script d'installation pour l'environnement de production Alimante
# Ce script configure l'environnement Python et installe les dépendances

echo "🚀 Installation de l'environnement de production Alimante..."

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

echo "✅ Python 3 détecté: $(python3 --version)"

# Créer un environnement virtuel
if [ ! -d "venv" ]; then
    echo "🔧 Création de l'environnement virtuel..."
    python3 -m venv venv
else
    echo "✅ Environnement virtuel existant détecté"
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Mettre à jour pip
echo "🔧 Mise à jour de pip..."
pip install --upgrade pip

# Installer le package en mode production
echo "🔧 Installation du package en mode production..."
pip install .

# Créer les dossiers nécessaires
echo "🔧 Création des dossiers nécessaires..."
mkdir -p logs
mkdir -p data
mkdir -p config/backups

# Créer le fichier .env de production
if [ ! -f ".env" ]; then
    echo "🔧 Création du fichier .env de production..."
    cat > .env << EOF
# Configuration de l'environnement Alimante (PRODUCTION)
ALIMANTE_SECRET_KEY=$(openssl rand -hex 32)
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
LOG_LEVEL=INFO
LOG_FILE=logs/alimante.log
GPIO_MODE=BCM
GPIO_WARNINGS=false
SENSOR_READ_INTERVAL=30
SENSOR_CALIBRATION_ENABLED=false
CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:3000
MAX_LOGIN_ATTEMPTS=3
SESSION_TIMEOUT_MINUTES=15
EOF
    echo "✅ Fichier .env de production créé"
else
    echo "✅ Fichier .env existant"
fi

# Créer le service systemd
echo "🔧 Création du service systemd..."
sudo tee /etc/systemd/system/alimante.service > /dev/null << EOF
[Unit]
Description=Alimante - Système de gestion automatisée des mantes
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Recharger systemd et activer le service
echo "🔧 Configuration du service systemd..."
sudo systemctl daemon-reload
sudo systemctl enable alimante.service

# Créer le script de démarrage
echo "🔧 Création du script de démarrage..."
cat > start_alimante.sh << 'EOF'
#!/bin/bash
# Script de démarrage d'Alimante

echo "🚀 Démarrage d'Alimante..."

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier la configuration
if [ ! -f ".env" ]; then
    echo "❌ Fichier .env manquant. Veuillez le configurer."
    exit 1
fi

# Démarrer l'application
echo "✅ Démarrage de l'application..."
python main.py
EOF

chmod +x start_alimante.sh

# Créer le script d'arrêt
echo "🔧 Création du script d'arrêt..."
cat > stop_alimante.sh << 'EOF'
#!/bin/bash
# Script d'arrêt d'Alimante

echo "🛑 Arrêt d'Alimante..."

# Arrêter le service systemd
sudo systemctl stop alimante.service

# Vérifier que tous les processus sont arrêtés
pkill -f "python main.py" || true

echo "✅ Alimante arrêté"
EOF

chmod +x stop_alimante.sh

# Créer le script de redémarrage
echo "🔧 Création du script de redémarrage..."
cat > restart_alimante.sh << 'EOF'
#!/bin/bash
# Script de redémarrage d'Alimante

echo "🔄 Redémarrage d'Alimante..."

# Arrêter
./stop_alimante.sh

# Attendre un peu
sleep 2

# Redémarrer
./start_alimante.sh
EOF

chmod +x restart_alimante.sh

# Vérifier l'installation
echo "🔧 Vérification de l'installation..."
python -c "import src; print('✅ Package src importé avec succès')"
python -c "import src.api.app; print('✅ API app importée avec succès')"

echo ""
echo "🎉 Installation de production terminée avec succès !"
echo ""
echo "Services créés :"
echo "  - start_alimante.sh  : Démarrage manuel"
echo "  - stop_alimante.sh   : Arrêt manuel"
echo "  - restart_alimante.sh: Redémarrage"
echo ""
echo "Service systemd :"
echo "  - sudo systemctl start alimante    : Démarrer le service"
echo "  - sudo systemctl stop alimante     : Arrêter le service"
echo "  - sudo systemctl status alimante   : Vérifier le statut"
echo "  - sudo systemctl enable alimante   : Activer au démarrage"
echo ""
echo "Logs :"
echo "  - tail -f logs/alimante.log        : Logs en temps réel"
echo "  - sudo journalctl -u alimante -f   : Logs systemd"
echo ""
echo "Documentation API : http://localhost:8000/docs"
