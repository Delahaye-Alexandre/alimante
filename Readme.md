# Alimante - Gestion Automatisée des Mantes avec Raspberry Pi

## 🍓 Description

Alimante est un système de gestion automatisé pour l'élevage de mantes utilisant un **Raspberry Pi** et une **API moderne**. Le système contrôle automatiquement :

- **🌡️ Température** : Maintien optimal avec relais de chauffage
- **💧 Humidité** : Contrôle automatique avec pulvérisateur
- **💡 Éclairage** : Synchronisation lever/coucher du soleil
- **🦗 Alimentation** : Distribution automatique selon planning

## 🚀 Fonctionnalités

### Backend (Raspberry Pi)

- **API FastAPI** avec documentation auto-générée
- **WebSocket** pour données temps réel
- **GPIO** pour contrôle des capteurs/actionneurs
- **Service systemd** pour démarrage automatique
- **Logging** complet avec rotation

### Application Mobile (Prévue)

- **React Native** cross-platform
- **Dashboard** temps réel
- **Notifications** push
- **Contrôles** manuels

## 📋 Matériel Requis

### Électronique

- **Raspberry Pi Zero W** (ou Pi 3/4)
- **Capteur DHT22** (température + humidité)
- **Relais 5V** (chauffage, pulvérisateur, éclairage)
- **Servo SG90** (trappe alimentation)
- **LED RGB** (statut système)
- **Capteur LDR** (luminosité, optionnel)

### Connexions GPIO

```
DHT22     → Pin 4   (température/humidité)
LDR       → Pin 17  (luminosité)
Relais H  → Pin 18  (chauffage)
Relais H  → Pin 23  (pulvérisateur)
Servo     → Pin 12  (trappe alimentation)
Relais L  → Pin 24  (éclairage)
LED Stat  → Pin 25  (statut)
```

## 🛠️ Installation

### 1. Installation automatique (Recommandé)

```bash
# Cloner le projet
git clone https://github.com/votre-repo/alimante.git
cd alimante

# Installation automatique
chmod +x install_raspberry.sh
./install_raspberry.sh
```

### 2. Installation manuelle

```bash
# Dépendances système
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# Environnement virtuel
python3 -m venv alimante_env
source alimante_env/bin/activate

# Dépendances Python
pip install -r requirements.txt

# Permissions GPIO
sudo usermod -a -G gpio $USER
sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem
```

## 🧪 Tests

### Test GPIO

```bash
python3 test_gpio.py
```

### Test API

```bash
# Démarrage API
./start_api.sh

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/api/status
curl http://localhost:8000/api/metrics
```

## 🚀 Utilisation

### Démarrage manuel

```bash
# API
./start_api.sh

# Système complet
python3 main.py
```

### Service systemd

```bash
# Démarrer le service
sudo systemctl start alimante

# Vérifier le statut
sudo systemctl status alimante

# Voir les logs
sudo journalctl -u alimante -f
```

## 📱 API Endpoints

### REST API

- `GET /` - Statut de l'API
- `GET /api/status` - Statut complet du système
- `GET /api/metrics` - Métriques des capteurs
- `POST /api/control` - Contrôle des systèmes
- `POST /api/feeding/trigger` - Alimentation manuelle

### WebSocket

- `ws://raspberry-pi:8000/ws` - Données temps réel

### Documentation

- `http://raspberry-pi:8000/docs` - Swagger UI

## ⚙️ Configuration

### Fichiers de configuration

- `config/config.json` - Configuration générale
- `config/gpio_config.json` - Configuration GPIO
- `config/orthopteres/` - Configurations par espèce

### Variables d'environnement

```bash
# Créer .env
ALIMANTE_ENV=production
ALIMANTE_LOG_LEVEL=INFO
ALIMANTE_API_HOST=0.0.0.0
ALIMANTE_API_PORT=8000
```

## 🔧 Développement

### Structure du projet

```
alimante/
├── src/
│   ├── api/           # API FastAPI
│   ├── controllers/   # Contrôleurs GPIO
│   └── utils/         # Utilitaires
├── config/            # Configurations
├── mobile/            # App mobile (prévue)
├── tests/             # Tests unitaires
└── logs/              # Logs système
```

### Tests

```bash
# Tests unitaires
pytest tests/

# Tests avec coverage
pytest --cov=src tests/
```

## 📊 Monitoring

### Logs

- `logs/alimante.log` - Logs application
- `sudo journalctl -u alimante` - Logs service

### Métriques

- Température actuelle/optimale
- Humidité actuelle/optimale
- Statut des actionneurs
- Historique des repas

## 🆘 Dépannage

### Problèmes courants

1. **GPIO non accessible** : Vérifier les permissions
2. **Capteur DHT22** : Vérifier le câblage
3. **Service ne démarre pas** : Vérifier les logs systemd
4. **API non accessible** : Vérifier le firewall

### Commandes utiles

```bash
# Vérifier GPIO
python3 test_gpio.py

# Redémarrer le service
sudo systemctl restart alimante

# Voir les logs en temps réel
sudo journalctl -u alimante -f

# Tester l'API
curl http://localhost:8000/api/status
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commiter les changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `License` pour plus de détails.

## 📞 Support

- **Issues** : [GitHub Issues](https://github.com/votre-repo/alimante/issues)
- **Documentation** : [Wiki](https://github.com/votre-repo/alimante/wiki)
- **Email** : alexandre-delahaye@outlook.fr

---

**Alimante** - Gestion intelligente de vos mantes 🦗
