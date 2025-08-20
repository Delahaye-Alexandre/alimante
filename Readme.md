# 🦗 Alimante - Système de Gestion Automatisée des Mantes

Système intelligent de gestion automatisée des mantes religieuses utilisant un **Raspberry Pi Zero 2W** pour contrôler l'environnement, l'alimentation et le monitoring.

## ✨ Fonctionnalités

- 🌡️ **Contrôle de température** automatique avec chauffage/refroidissement
- 💧 **Gestion de l'humidité** avec brumisateur ultrasonique
- 💡 **Éclairage intelligent** basé sur les cycles jour/nuit
- 🍽️ **Alimentation automatisée** avec programmation
- 🌬️ **Ventilation intelligente** basée sur la qualité de l'air
- 📷 **Monitoring vidéo** avec caméra CSI (optionnel)
- 📱 **Interface mobile** pour contrôle à distance
- 🔒 **Sécurité** avec authentification JWT
- 📊 **Métriques et alertes** en temps réel

## 🛠️ Matériel Requis

### Composants Principaux

- **Raspberry Pi Zero 2W** (recommandé) ou Pi Zero W
- **Carte microSD** 16GB+ (classe 10 recommandée pour les performances)
- **Alimentation** 5V/2.5A minimum pour Pi Zero 2W
- **Boîtier** avec ventilation pour le Raspberry Pi Zero 2W
- **Câble OTG** pour connexion USB

### Capteurs et Composants

- **Capteur DHT22** pour température et humidité
- **Module PCF8591** pour conversion analogique/digitale
- **Relais 5V** pour contrôle des composants
- **LED RGB** pour éclairage et indicateurs
- **Ventilateur 12V** pour refroidissement
- **Brumisateur ultrasonique** pour humidification
- **Caméra CSI** (optionnelle) pour monitoring

### Câblage

- **Breadboard** et **jumpers** pour les tests
- **Câbles GPIO** pour connexion permanente
- **Alimentation 12V** pour composants externes
- **Interrupteurs** et **boutons** pour contrôle manuel

## 🚀 Installation Rapide

### Prérequis Système

- **Raspbian Lite** (Bullseye ou plus récent) - **RECOMMANDÉ**
- **Python 3.7+** (inclus par défaut)
- **Connexion internet** stable (via WiFi ou Ethernet)
- **Accès SSH** ou **écran + clavier**

### Installation Automatique (Recommandée)

```bash
# 1. Cloner le projet
git clone https://github.com/alimante/alimante.git
cd alimante

# 2. Rendre le script exécutable
chmod +x install_raspberry.sh

# 3. Lancer l'installation
./install_raspberry.sh

# 4. Redémarrer le Raspberry Pi Zero 2W
sudo reboot

# 5. Vérifier l'installation
chmod +x scripts/verify_zero2w.sh
./scripts/verify_zero2w.sh
```

### Installation Rapide (Sans Git)

Si git n'est pas installé sur votre Raspberry Pi Zero 2W :

```bash
# 1. Installer les outils de base
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget python3 python3-pip python3-venv

# 2. Cloner et installer
git clone https://github.com/alimante/alimante.git
cd alimante
chmod +x install_raspberry.sh
./install_raspberry.sh
```

### Installation Alternative (Sans Git)

Si git ne fonctionne pas, consultez `INSTALL_MANUAL.md` pour les alternatives :

- Téléchargement direct avec wget
- Transfert manuel du fichier ZIP
- Installation étape par étape

### Installation Manuelle

```bash
# 1. Mise à jour du système
sudo apt update && sudo apt upgrade -y

# 2. Installation des dépendances
sudo apt install -y python3 python3-pip python3-venv git i2c-tools python3-smbus

# 3. Activation des interfaces
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 0

# 4. Création de l'environnement virtuel
python3 -m venv alimante_env
source alimante_env/bin/activate

# 5. Installation des dépendances Python
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# 6. Configuration des permissions GPIO
sudo usermod -a -G gpio $USER
sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem
```

## 🔧 Configuration

### Configuration GPIO

Modifiez `config/gpio_config.json` selon votre câblage :

```json
{
  "gpio_pins": {
    "TEMPERATURE_SENSOR": 4,
    "HUMIDITY_SENSOR": 4,
    "HEATING_RELAY": 18,
    "COOLING_RELAY": 23,
    "HUMIDIFIER_RELAY": 24,
    "FAN_RELAY": 25,
    "LIGHT_RELAY": 8,
    "FEEDING_RELAY": 12
  },
  "i2c_addresses": {
    "PCF8591": "0x48"
  }
}
```

### Variables d'Environnement

Créez un fichier `.env` basé sur `env.example` :

```bash
# Configuration de l'environnement Alimante
ALIMANTE_SECRET_KEY=votre-cle-secrete-change-en-production
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
LOG_LEVEL=INFO
LOG_FILE=logs/alimante.log
GPIO_MODE=BCM
GPIO_WARNINGS=false
```

### Configuration des Composants

#### PCF8591 (ADC/DAC)

- **Adresse I2C** : 0x48 (par défaut)
- **Tension de référence** : 3.3V
- **Résolution** : 8-bit (0-255)

#### DHT22

- **Broche de données** : GPIO 4 (configurable)
- **Tension** : 3.3V
- **Précision** : ±0.5°C, ±2% RH

## 🚀 Démarrage

### Service Systemd (Recommandé)

```bash
# Démarrer le service
sudo systemctl start alimante

# Vérifier le statut
sudo systemctl status alimante

# Activer au démarrage
sudo systemctl enable alimante

# Voir les logs
sudo journalctl -u alimante -f
```

### Démarrage Manuel

```bash
# Activer l'environnement virtuel
source alimante_env/bin/activate

# Démarrer l'API
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 1

# Ou démarrer le système complet
python main.py
```

### Interface Web

- **Documentation API** : http://localhost:8000/docs
- **Interface ReDoc** : http://localhost:8000/redoc
- **Interface Swagger** : http://localhost:8000/docs

## 🔌 Câblage GPIO

### Schéma de Base (Optimisé Zero 2W)

```
Raspberry Pi Zero 2W
├── GPIO 4  → DHT22 (DATA)
├── GPIO 2  → PCF8591 (SDA)
├── GPIO 3  → PCF8591 (SCL)
├── GPIO 18 → Relais Chauffage
├── GPIO 23 → Relais Refroidissement
├── GPIO 24 → Relais Brumisateur
├── 3.3V   → Alimentation capteurs
└── GND     → Masse commune
```

### Détails du Câblage

Consultez `docs/wiring_guide.md` pour le schéma de câblage détaillé et les photos.

### Migration PCF8591

Le projet utilise maintenant le **PCF8591** (8-bit) au lieu de l'ADS1115 (16-bit) pour une meilleure simplicité et réduction des coûts. Consultez `docs/pcf8591_integration.md` pour les détails.

## 🧪 Tests et Vérification

### Tests Automatiques

```bash
# Vérification post-installation
./scripts/verify_installation.sh

# Tests unitaires
pytest tests/unit/ -v

# Tests d'intégration
pytest tests/integration/ -v

# Tests matériels
pytest tests/hardware/ -v

# Tous les tests
pytest tests/ -v
```

### Tests Manuels

```bash
# Test GPIO
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); print('GPIO OK')"

# Test I2C
i2cdetect -y 1

# Test des composants
python tests/utils/component_test.py
```

## 🐛 Dépannage

### Problèmes Courants

#### Installation

```bash
# Dépendances manquantes
pip install -r requirements.txt --no-cache-dir --force-reinstall

# Permissions GPIO
sudo usermod -a -G gpio $USER
sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem

# Redémarrer après configuration
sudo reboot
```

#### Service Systemd

```bash
# Vérifier les logs
sudo journalctl -u alimante -f

# Redémarrer le service
sudo systemctl restart alimante

# Vérifier la configuration
sudo systemctl status alimante
```

#### Composants Matériels

```bash
# Vérifier I2C
i2cdetect -y 1

# Vérifier GPIO
gpio readall

# Tester les composants
python tests/hardware/test_gpio.py
```

#### API

```bash
# Vérifier les ports
netstat -tlnp | grep 8000

# Tester l'API
curl http://localhost:8000/health

# Vérifier les logs
tail -f logs/alimante.log
```

### Diagnostic Complet

```bash
# Script de diagnostic
python tests/diagnostics/diagnostic_complet.py

# Analyse du câblage
python tests/diagnostics/analyse_cablage.py

# Vérification système
python tests/diagnostics/check_system_coherence.py
```

## 📱 Application Mobile

L'application mobile est dans le dossier `mobile/`. Consultez `mobile/README.md` pour l'installation et la configuration.

## 📁 Structure du Projet

```
alimante/
├── src/                    # Code source principal
│   ├── api/               # API FastAPI
│   ├── controllers/       # Contrôleurs matériels
│   ├── services/          # Services métier
│   └── utils/             # Utilitaires
├── config/                 # Configuration
├── tests/                  # Tests et diagnostics
├── docs/                   # Documentation
├── scripts/                # Scripts d'installation
├── logs/                   # Logs
└── mobile/                 # Application mobile
```

## 🔒 Sécurité

### Authentification

- **JWT tokens** pour l'API
- **Hachage bcrypt** pour les mots de passe
- **CORS configuré** pour l'accès web

### Réseau

- **Port 8000** pour l'API
- **Firewall UFW** configuré automatiquement
- **HTTPS** recommandé en production

## ⚡ Optimisations Raspberry Pi Zero 2W

### Optimisations Appliquées

- **Mémoire GPU limitée** à 16MB (économise la RAM)
- **WiFi maintenu actif** (nécessaire pour l'API et le contrôle à distance)
- **Service optimisé** avec 1 worker et limites mémoire
- **Fichier swap** de 256MB pour les cartes SD lentes
- **Services inutiles désactivés** (bluetooth, avahi, etc.)
- **Paramètres mémoire optimisés** pour ARMv6

### Limitations et Recommandations

- **Mémoire limitée** : 512MB RAM disponible
- **CPU ARMv6** : Plus lent que les modèles récents
- **Carte SD** : Utilisez une carte classe 10+ pour les performances
- **Connexion** : WiFi ou Ethernet via adaptateur USB
- **Température** : Surveillez la température en cas d'usage intensif

## 🤝 Contribution

1. **Fork** le projet
2. **Créez** une branche feature (`git checkout -b feature/AmazingFeature`)
3. **Commitez** vos changements (`git commit -m 'Add AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrez** une Pull Request

### Standards de Code

- **PEP 8** pour Python
- **Type hints** pour les fonctions
- **Docstrings** pour la documentation
- **Tests** pour les nouvelles fonctionnalités

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `License` pour plus de détails.

## 📞 Support

### Ressources

- 📧 **Email** : contact@alimante.com
- 🐛 **Issues** : [GitHub Issues](https://github.com/alimante/alimante/issues)
- 📖 **Documentation** : [Wiki](https://github.com/alimante/alimante/wiki)
- 💬 **Discussions** : [GitHub Discussions](https://github.com/alimante/alimante/discussions)

### Communauté

- **Forum** : [Forum Alimante](https://forum.alimante.com)
- **Discord** : [Serveur Discord](https://discord.gg/alimante)
- **YouTube** : [Chaîne YouTube](https://youtube.com/@alimante)

## 🙏 Remerciements

- **Raspberry Pi Foundation** pour le matériel
- **Communauté Python** pour les bibliothèques
- **Contributeurs open source** pour l'inspiration
- **Éleveurs de mantes** pour les retours d'expérience

---

**Alimante** - Élevez vos mantes avec intelligence ! 🦗✨

_Dernière mise à jour : $(date +%Y-%m-%d)_
