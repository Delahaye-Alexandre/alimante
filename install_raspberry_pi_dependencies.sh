#!/bin/bash
"""
Script d'installation des dépendances pour Raspberry Pi
À exécuter sur le Raspberry Pi avant de tester Alimante
"""

echo "🍓 INSTALLATION DES DÉPENDANCES ALIMANTE"
echo "========================================"

# Mise à jour du système
echo "📦 Mise à jour du système..."
sudo apt update
sudo apt upgrade -y

# Installation des dépendances système
echo "🔧 Installation des dépendances système..."
sudo apt install -y python3-pip python3-dev python3-pil python3-spidev python3-smbus

# Installation des dépendances Python
echo "🐍 Installation des dépendances Python..."
pip3 install RPi.GPIO st7735 gpiozero

# Vérification de l'installation
echo "✅ Vérification de l'installation..."
python3 -c "
import RPi.GPIO as GPIO
import st7735
from PIL import Image, ImageDraw, ImageFont
from gpiozero import RotaryEncoder, Button
import spidev
print('✅ Toutes les dépendances sont installées')
"

echo ""
echo "🎉 INSTALLATION TERMINÉE"
echo "Vous pouvez maintenant exécuter: python3 test_raspberry_pi.py"
