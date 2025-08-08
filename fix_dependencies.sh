#!/bin/bash

echo "🔧 Correction des dépendances Alimante..."

# Créer le dossier logs
mkdir -p logs
echo "✅ Dossier logs créé"

# Mettre à jour les dépendances problématiques
pip install --upgrade PyJWT==2.8.0
pip install --upgrade passlib[bcrypt]==1.7.4
pip install --upgrade python-jose[cryptography]==3.3.0

echo "✅ Dépendances mises à jour"

# Vérifier les versions
echo "📋 Versions installées :"
pip show PyJWT passlib python-jose

echo "✅ Correction terminée"
