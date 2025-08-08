#!/bin/bash

echo "🔧 Correction complète des problèmes Alimante..."
echo "================================================"

# 1. Installer les dépendances manquantes
echo "📦 Installation des dépendances manquantes..."
pip install PyJWT==2.8.0 python-jose[cryptography]==3.3.0

# 2. Créer le dossier logs
echo "📁 Création du dossier logs..."
mkdir -p logs

# 3. Vérifier les versions
echo "📋 Versions installées :"
pip show PyJWT python-jose

# 4. Tester la configuration
echo "🧪 Test de la configuration..."
python -c "
import sys
sys.path.insert(0, '.')
from src.utils.config_manager import SystemConfig
from src.services.config_service import config_service

try:
    config = config_service.load_system_config()
    print('✅ Configuration système chargée avec succès')
    print(f'   - Espèce: {config.species_name}')
    print(f'   - Nom commun: {config.common_name}')
    print(f'   - Classification: {config.classification is not None}')
except Exception as e:
    print(f'❌ Erreur configuration: {e}')
    sys.exit(1)
"

# 5. Tester l'API
echo "🚀 Test de démarrage de l'API..."
timeout 10s python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001 &
API_PID=$!

sleep 3

if kill -0 $API_PID 2>/dev/null; then
    echo "✅ API démarrée avec succès"
    kill $API_PID
else
    echo "❌ Échec du démarrage de l'API"
fi

echo "✅ Correction terminée"
