#!/bin/bash

# Script d'installation pour l'environnement de développement Alimante
# Ce script configure l'environnement Python et installe les dépendances

echo "🚀 Installation de l'environnement de développement Alimante..."

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

# Installer le package en mode développement
echo "🔧 Installation du package en mode développement..."
pip install -e .

# Installer les dépendances de développement
echo "🔧 Installation des dépendances de développement..."
pip install -e ".[dev]"

# Créer les dossiers nécessaires
echo "🔧 Création des dossiers nécessaires..."
mkdir -p logs
mkdir -p data
mkdir -p config/backups

# Copier la configuration d'exemple
if [ ! -f ".env" ]; then
    echo "🔧 Création du fichier .env..."
    cat > .env << EOF
# Configuration de l'environnement Alimante
ALIMANTE_SECRET_KEY=dev-secret-key-change-in-production
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
LOG_LEVEL=DEBUG
LOG_FILE=logs/alimante.log
GPIO_MODE=BCM
GPIO_WARNINGS=false
SENSOR_READ_INTERVAL=30
SENSOR_CALIBRATION_ENABLED=true
CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:3000
MAX_LOGIN_ATTEMPTS=5
SESSION_TIMEOUT_MINUTES=30
EOF
    echo "✅ Fichier .env créé"
else
    echo "✅ Fichier .env existant"
fi

# Vérifier l'installation
echo "🔧 Vérification de l'installation..."
python -c "import src; print('✅ Package src importé avec succès')"
python -c "import src.api.app; print('✅ API app importée avec succès')"
python -c "import src.controllers.temperature_controller; print('✅ Contrôleur de température importé avec succès')"

echo ""
echo "🎉 Installation terminée avec succès !"
echo ""
echo "Pour démarrer l'application :"
echo "1. Activez l'environnement virtuel: source venv/bin/activate"
echo "2. Lancez l'API: python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000"
echo "3. Ou lancez le programme principal: python main.py"
echo ""
echo "Pour les tests :"
echo "pytest tests/ -v"
echo ""
echo "Documentation API disponible sur : http://localhost:8000/docs"
