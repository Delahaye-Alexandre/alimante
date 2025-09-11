# 🦎 Alimante - Système de gestion automatique de terrariums

Alimante est une application Python pour gérer automatiquement des terrariums pour insectes et reptiles. Le système supervise et contrôle automatiquement la température, l'humidité, la lumière, la ventilation et l'alimentation selon des profils d'espèces personnalisables.

## 🌟 Fonctionnalités

- **🌡️ Contrôle de température** (jour/nuit selon profil espèce)
- **💧 Gestion de l'humidité** et du niveau d'eau
- **💡 Éclairage intelligent** (photopériode avec transitions douces)
- **🌪️ Ventilation adaptative** (selon qualité de l'air)
- **🍽️ Alimentation automatique** (via SAS et servo)
- **📷 Caméras et monitoring** (snapshots et streaming)
- **🖥️ Interface utilisateur** (LCD local + PWA web)
- **🔒 Sécurité intégrée** (limites et failsafes)

## 🏗️ Architecture

Le système suit une architecture modulaire :

- **Drivers** : Interaction directe avec le matériel (GPIO, I2C, PWM...)
- **Controllers** : Traduction des décisions des services en commandes matérielles
- **Services** : Logique métier et supervision, adaptation aux profils espèces
- **UI** : Interface utilisateur (LCD + PWA web)

## 📁 Structure du projet

```
alimante/
├── config/                 # Configurations
│   ├── policies/          # Règles d'automatisation
│   ├── species/           # Profils d'espèces
│   └── terrariums/        # Instances de terrariums
├── src/                   # Code source
│   ├── api/              # API REST
│   ├── controllers/      # Contrôleurs matériel
│   ├── services/         # Services métier
│   ├── ui/               # Interface utilisateur
│   ├── loops/            # Boucles principales
│   └── utils/            # Utilitaires
├── data/                  # Base de données et snapshots
├── docs/                  # Documentation
├── tests/                 # Tests unitaires et intégration
└── scripts/              # Scripts d'installation
```

## 🚀 Installation

### Prérequis

- Python 3.8+
- Raspberry Pi (recommandé)
- Matériel de terrarium (capteurs, actionneurs, etc.)

### Installation sur Windows (développement)

```bash
# Cloner le projet
git clone <repository-url>
cd alimante

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python main.py
```

### Installation sur Raspberry Pi

```bash
# Exécuter le script d'installation
chmod +x scripts/install_raspberry.sh
./scripts/install_raspberry.sh
```

## ⚙️ Configuration

1. **Profils d'espèces** : Configurez vos espèces dans `config/species/`
2. **Terrariums** : Créez vos instances dans `config/terrariums/`
3. **Politiques** : Ajustez les règles dans `config/policies/`
4. **Sécurité** : Définissez les limites dans `config/safety_limits.json`

## 🎯 Utilisation

### Interface LCD

- Navigation avec encodeur rotatif
- Affichage des métriques en temps réel
- Contrôle manuel des actionneurs

### Interface Web (PWA)

- Dashboard complet
- Configuration à distance
- Monitoring en temps réel
- Historique des données

## 🔧 Développement

Le projet suit un plan de développement séquentiel :

1. ✅ Structure du projet
2. ⏳ Configurations initiales
3. ⏳ Développement des drivers
4. ⏳ Développement des controllers
5. ⏳ Développement des services
6. ⏳ Interface utilisateur
7. ⏳ Boucles principales
8. ⏳ Tests et validation
9. ⏳ Documentation

## 📊 Espèces supportées

- **Insectes** : Mantes religieuses, phasmes, etc.
- **Reptiles** : Lézards, serpents, geckos, etc.

Chaque espèce a son profil personnalisé définissant ses besoins spécifiques.

## 🛡️ Sécurité

- Limites de sécurité configurables
- Failsafes matériels et logiciels
- Monitoring continu des paramètres critiques
- Arrêt d'urgence automatique

## 📝 Licence

[À définir]

## 🤝 Contribution

[À définir]

## 📞 Support

[À définir]
