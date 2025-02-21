#!/bin/bash
# filepath: start.sh
# Ce script démarre l'application sur un Raspberry Pi Zero.

if [ -f "env/bin/activate" ]; then
    echo "Activation de l'environnement virtuel..."
    source env/bin/activate
else
    echo "Environnement virtuel non trouvé. Utilisation du Python système."
fi

# Ajouter le dossier src au PYTHONPATH
export PYTHONPATH="$(pwd)/src"

# Démarrer l'application
echo "Démarrage de l'application Alimante..."
python -m Alimante.main || { echo "Erreur de démarrage de l'application"; exit 1; }