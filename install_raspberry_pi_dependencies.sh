#!/bin/bash
"""
Script d'installation des dépendances pour Raspberry Pi
À exécuter sur le Raspberry Pi avant de tester Alimante
Version complète avec résolution de tous les problèmes de dépendances
"""

echo "🍓 INSTALLATION DES DÉPENDANCES ALIMANTE"
echo "========================================"

# Mise à jour du système
echo "📦 Mise à jour du système..."
sudo apt update
sudo apt upgrade -y

# Installation des dépendances système de base
echo "🔧 Installation des dépendances système de base..."
sudo apt install -y python3-pip python3-dev python3-pil python3-spidev python3-smbus

# Installation des bibliothèques BLAS/LAPACK pour numpy
echo "🔢 Installation des bibliothèques BLAS/LAPACK pour numpy..."
sudo apt install -y libopenblas0 libopenblas-dev libatlas-base-dev liblapack-dev

# Installation des bibliothèques pour Pillow (traitement d'images)
echo "🖼️ Installation des bibliothèques pour Pillow..."
sudo apt install -y libopenjp2-7 libopenjp2-7-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev libtiff5-dev libharfbuzz-dev libfribidi-dev libxcb1-dev

# Installation de lgpio pour gpiozero
echo "🔌 Installation de lgpio pour gpiozero..."
sudo apt install -y python3-lgpio

# Activation de SPI (nécessaire pour l'écran ST7735)
echo "📡 Activation de SPI..."
# Vérifier si SPI est déjà activé
if ! lsmod | grep -q spi; then
    echo "⚠️ SPI non activé. Activation en cours..."
    # Ajouter dtparam=spi=on au fichier de configuration
    if ! grep -q "dtparam=spi=on" /boot/config.txt; then
        echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
        echo "✅ SPI activé dans /boot/config.txt"
        echo "⚠️ Redémarrage nécessaire pour activer SPI"
        echo "   Exécutez: sudo reboot"
    else
        echo "✅ SPI déjà activé dans /boot/config.txt"
    fi
else
    echo "✅ SPI déjà activé"
fi

# Vérification des interfaces GPIO
echo "🔍 Vérification des interfaces GPIO..."
if [ -e /dev/gpiochip0 ]; then
    echo "✅ Interface GPIO disponible: /dev/gpiochip0"
else
    echo "❌ Interface GPIO non disponible"
fi

if [ -e /dev/spi* ]; then
    echo "✅ Interface SPI disponible"
else
    echo "❌ Interface SPI non disponible (redémarrage nécessaire)"
fi

# Installation des dépendances Python
echo "🐍 Installation des dépendances Python..."
pip3 install -r requirements.txt

# Installation supplémentaire de lgpio dans l'environnement virtuel
echo "🔌 Installation de lgpio dans l'environnement virtuel..."
pip3 install lgpio

# Vérification de l'installation
echo "✅ Vérification de l'installation..."
python3 -c "
try:
    import RPi.GPIO as GPIO
    print('✅ RPi.GPIO importé')
except Exception as e:
    print(f'❌ Erreur RPi.GPIO: {e}')

try:
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    print('✅ ST7735 et PIL importés')
except Exception as e:
    print(f'❌ Erreur ST7735/PIL: {e}')

try:
    from gpiozero import RotaryEncoder, Button
    print('✅ gpiozero importé')
except Exception as e:
    print(f'❌ Erreur gpiozero: {e}')

try:
    import lgpio
    print('✅ lgpio importé')
except Exception as e:
    print(f'❌ Erreur lgpio: {e}')

try:
    import numpy
    print('✅ numpy importé')
except Exception as e:
    print(f'❌ Erreur numpy: {e}')

try:
    import spidev
    print('✅ spidev importé')
except Exception as e:
    print(f'❌ Erreur spidev: {e}')
"

echo ""
echo "🎉 INSTALLATION TERMINÉE"
echo ""
echo "📋 RÉSUMÉ DES ÉTAPES:"
echo "1. ✅ Dépendances système installées"
echo "2. ✅ Bibliothèques BLAS/LAPACK installées"
echo "3. ✅ Bibliothèques Pillow installées"
echo "4. ✅ lgpio installé"
echo "5. ✅ SPI activé (redémarrage nécessaire si pas déjà fait)"
echo ""
echo "🚀 Vous pouvez maintenant exécuter:"
echo "   python3 tests/alimante_menu_improved.py"
echo ""
echo "⚠️ Si SPI n'était pas activé, redémarrez d'abord:"
echo "   sudo reboot"
