#!/bin/bash

# Script d'installation Alimante pour Raspberry Pi
echo "=== Installation d'Alimante sur Raspberry Pi ==="

# Vérification du système
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  Attention: Ce script est conçu pour Raspberry Pi"
    read -p "Continuer quand même ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Mise à jour du système
echo "📦 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installation des dépendances système
echo "🔧 Installation des dépendances système..."
sudo apt install -y python3 python3-pip python3-venv git

# Installation des dépendances GPIO
echo "🔌 Installation des dépendances GPIO..."
sudo apt install -y python3-rpi.gpio python3-dev

# Création de l'environnement virtuel
echo "🐍 Création de l'environnement virtuel..."
python3 -m venv alimante_env
source alimante_env/bin/activate

# Installation des dépendances Python
echo "📚 Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configuration des permissions GPIO
echo "🔐 Configuration des permissions GPIO..."
sudo usermod -a -G gpio $USER
sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem

# Création du service systemd
echo "⚙️  Configuration du service systemd..."
sudo tee /etc/systemd/system/alimante.service > /dev/null <<EOF
[Unit]
Description=Alimante - Système de gestion des mantes
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/alimante_env/bin
ExecStart=$(pwd)/alimante_env/bin/python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Activation du service
echo "🚀 Activation du service..."
sudo systemctl daemon-reload
sudo systemctl enable alimante.service

# Configuration du firewall
echo "🔥 Configuration du firewall..."
sudo ufw allow 8000/tcp

# Création des dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p logs
mkdir -p data

# Configuration des permissions
echo "🔐 Configuration des permissions..."
chmod +x start_api.sh
chmod +x main.py

echo "✅ Installation terminée !"
echo ""
echo "📋 Prochaines étapes :"
echo "1. Redémarrer le Raspberry Pi : sudo reboot"
echo "2. Vérifier le service : sudo systemctl status alimante"
echo "3. Démarrer le service : sudo systemctl start alimante"
echo "4. Voir les logs : sudo journalctl -u alimante -f"
echo ""
echo "🌐 L'API sera accessible sur : http://$(hostname -I | awk '{print $1}'):8000"
echo "📖 Documentation API : http://$(hostname -I | awk '{print $1}'):8000/docs" 