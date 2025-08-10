#!/bin/bash

# Script d'installation des dépendances pour les tests de composants Alimante
# À exécuter sur Raspberry Pi

echo "🔧 Installation des dépendances pour les tests de composants Alimante"
echo "=================================================================="

# Mise à jour du système
echo "📦 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installation des packages système nécessaires
echo "📦 Installation des packages système..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    git \
    cmake \
    build-essential \
    libopencv-dev \
    python3-opencv \
    libatlas-base-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libatlas-base-dev \
    libjasper-dev \
    libqtcore4 \
    libqtgui4 \
    libqt4-test \
    python3-pyqt5 \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    libgtk-3-dev \
    libcanberra-gtk3-module \
    libcanberra-gtk-module \
    libcanberra-gtk3-dev

# Activation de l'interface SPI et I2C
echo "🔧 Configuration des interfaces..."
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0

# Installation des dépendances Python
echo "🐍 Installation des dépendances Python..."
pip3 install --upgrade pip setuptools wheel

# Installation des packages Python principaux
pip3 install \
    RPi.GPIO \
    adafruit-circuitpython-dht \
    adafruit-circuitpython-mcp3xxx \
    adafruit-circuitpython-busdevice \
    opencv-python \
    pillow \
    numpy \
    spidev \
    smbus2 \
    board \
    busio \
    digitalio

# Installation des packages pour l'écran TFT (optionnel)
echo "📺 Installation des packages pour l'écran TFT..."
pip3 install \
    adafruit-circuitpython-rgb-display \
    adafruit-circuitpython-framebuf

# Vérification de l'installation
echo "✅ Vérification de l'installation..."
python3 -c "
import sys
packages = [
    'RPi.GPIO',
    'board',
    'busio',
    'digitalio',
    'adafruit_dht',
    'adafruit_mcp3xxx',
    'cv2',
    'PIL',
    'numpy',
    'spidev'
]

missing = []
for package in packages:
    try:
        __import__(package)
        print(f'✅ {package}')
    except ImportError:
        missing.append(package)
        print(f'❌ {package}')

if missing:
    print(f'\\n⚠️  Packages manquants: {missing}')
    print('Essayez de les installer manuellement:')
    for pkg in missing:
        print(f'pip3 install {pkg}')
else:
    print('\\n🎉 Toutes les dépendances sont installées!')
"

echo ""
echo "🚀 Installation terminée!"
echo "Vous pouvez maintenant exécuter: python3 tests/component_test.py" 