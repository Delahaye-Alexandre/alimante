# 🦗 Alimante - Système de Gestion Automatisée des Mantes

Système intelligent de gestion automatisée des mantes religieuses utilisant un Raspberry Pi pour contrôler l'environnement, l'alimentation et le monitoring.

## ✨ Fonctionnalités

- 🌡️ **Contrôle de température** automatique avec chauffage/refroidissement
- 💧 **Gestion de l'humidité** avec brumisateur ultrasonique
- 💡 **Éclairage intelligent** basé sur les cycles jour/nuit
- 🍽️ **Alimentation automatisée** avec programmation
- 🌬️ **Ventilation intelligente** basée sur la qualité de l'air
- 📷 **Monitoring vidéo** avec caméra CSI
- 📱 **Interface mobile** pour contrôle à distance
- 🔒 **Sécurité** avec authentification JWT
- 📊 **Métriques et alertes** en temps réel

## 🚀 Installation Rapide

### Prérequis

- Python 3.8+
- Raspberry Pi (recommandé)
- Composants GPIO (capteurs, relais, etc.)

### Installation Automatique

```bash
# Cloner le projet
git clone https://github.com/alimante/alimante.git
cd alimante

# Installation automatique
chmod +x install_dev.sh
./install_dev.sh
```

### Installation Manuelle

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -e .

# Installer les dépendances de développement
pip install -e ".[dev]"
```

## 🔧 Configuration

### Variables d'Environnement

Créez un fichier `.env` basé sur `.env.example` :

```bash
# Configuration de l'environnement Alimante
ALIMANTE_SECRET_KEY=votre-cle-secrete-change-en-production
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
LOG_LEVEL=INFO
LOG_FILE=logs/alimante.log
GPIO_MODE=BCM
GPIO_WARNINGS=false
```

### Configuration GPIO

Modifiez `config/gpio_config.json` selon votre câblage :

```json
{
  "gpio_pins": {
    "TEMPERATURE_SENSOR": 4,
    "HUMIDITY_SENSOR": 17,
    "HEATING_RELAY": 18,
    "COOLING_RELAY": 23,
    "HUMIDIFIER_RELAY": 24
  }
}
```

## 🚀 Démarrage

### API FastAPI

```bash
# Démarrer l'API
python start_api.py

# Ou avec uvicorn directement
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Programme Principal

```bash
# Démarrer le système complet
python main.py
```

### Interface Web

- **Documentation API** : http://localhost:8000/docs
- **Interface ReDoc** : http://localhost:8000/redoc

## 🧪 Tests

```bash
# Tests unitaires
pytest tests/unit/ -v

# Tests d'intégration
pytest tests/integration/ -v

# Tests matériels
pytest tests/hardware/ -v

# Tous les tests
pytest tests/ -v
```

## 📁 Structure du Projet

```
alimante/
├── src/                    # Code source principal
│   ├── api/               # API FastAPI
│   ├── controllers/       # Contrôleurs matériels
│   ├── services/          # Services métier
│   └── utils/             # Utilitaires
├── config/                 # Configuration
├── tests/                  # Tests
├── docs/                   # Documentation
├── logs/                   # Logs
└── mobile/                 # Application mobile
```

## 🔌 Câblage GPIO

Consultez `docs/wiring_guide.md` pour le schéma de câblage détaillé.

## 📱 Application Mobile

L'application mobile est dans le dossier `mobile/`. Consultez `mobile/README.md` pour l'installation.

## 🐛 Dépannage

### Problèmes d'Imports

```bash
# Réinstaller le package en mode développement
pip install -e . --force-reinstall
```

### Problèmes GPIO

```bash
# Vérifier les permissions
sudo usermod -a -G gpio $USER
sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem
```

### Logs

```bash
# Voir les logs en temps réel
tail -f logs/alimante.log
```

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `License` pour plus de détails.

## 📞 Support

- 📧 Email : contact@alimante.com
- 🐛 Issues : [GitHub Issues](https://github.com/alimante/alimante/issues)
- 📖 Documentation : [Wiki](https://github.com/alimante/alimante/wiki)

## 🙏 Remerciements

- Raspberry Pi Foundation
- Communauté Python
- Contributeurs open source

---

**Alimante** - Élevez vos mantes avec intelligence ! 🦗✨
