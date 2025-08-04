#!/bin/bash

# Script de démarrage pour l'API Alimante
echo "Démarrage de l'API Alimante..."

# Activation de l'environnement virtuel (si existant)
if [ -d "env" ]; then
    source env/bin/activate
fi

# Installation des dépendances si nécessaire
pip install -r requirements.txt

# Démarrage de l'API
echo "Lancement de l'API sur http://localhost:8000"
echo "Documentation disponible sur http://localhost:8000/docs"
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload 