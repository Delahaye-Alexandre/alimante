# 🏠 Alimante - Système de contrôle intelligent

Système de contrôle pour bandeaux LED avec interface écran PSI et encodeur rotatif.

## 📋 Fonctionnalités

- **Interface écran PSI** avec navigation par encodeur rotatif
- **Contrôle des bandeaux LED** via PWM (GPIO 24)
- **Encodeur rotatif** pour la navigation (GPIO 18, 19, 20)
- **Page d'accueil** avec informations système
- **Menu interactif** avec plusieurs options
- **Tests hardware** intégrés
- **Monitoring système** en temps réel

## 🔧 Installation

### Prérequis

- Raspberry Pi
- Python 3.x
- Bibliothèque RPi.GPIO

### Installation des dépendances

```bash
pip install RPi.GPIO
```

### Câblage

#### Encodeur rotatif

- **CLK** → GPIO 17
- **DT** → GPIO 27
- **SW** (bouton) → GPIO 22
- **VCC** → 3.3V
- **GND** → GND

#### Écran PSI

- **Reset** → GPIO 24
- **A0** → GPIO 25
- **SDA** → GPIO 10 (I2C)
- **SCL** → GPIO 11 (I2C)
- **VCC** → 3.3V
- **GND** → GND

#### Bandeaux LED

- **Signal** → GPIO 18 (via MOSFET)
- **VCC** → 12V
- **GND** → GND

## 🚀 Utilisation

### Script principal (interface complète)

```bash
python3 alimante_main.py
```

### Test simple de l'encodeur

```bash
python3 test_ecran_psi_simple.py
```

### Test des bandeaux LED

```bash
python3 test_led_bandeaux.py
```

### Test écran PSI avec encodeur

```bash
python3 test_ecran_psi_encoder.py
```

## 🎛️ Navigation

### Encodeur rotatif

- **Rotation droite** : Navigation vers le bas
- **Rotation gauche** : Navigation vers le haut
- **Appui bouton** : Sélection/Validation

### Menu principal

1. 🏠 **Accueil Alimante** - Page d'accueil
2. 💡 **Test LED Bandeaux** - Contrôle des LED
3. 📊 **Monitoring Système** - État du système
4. ⚙️ **Configuration** - Paramètres
5. 🔧 **Tests Hardware** - Tests des composants
6. 📈 **Statistiques** - Données d'utilisation
7. ℹ️ **À propos** - Informations système

## ⚙️ Configuration

Modifiez le fichier `config_alimante.py` pour personnaliser :

### Pins GPIO

```python
GPIO_CONFIG = {
    'ENCODER': {
        'CLK_PIN': 17,  # Pin CLK
        'DT_PIN': 27,   # Pin DT
        'SW_PIN': 22,   # Pin SW (bouton)
    },
    'DISPLAY': {
        'RESET_PIN': 24,  # Pin Reset écran
        'A0_PIN': 25,     # Pin A0 écran
        'SDA_PIN': 10,    # Pin SDA (I2C)
        'SCL_PIN': 11,    # Pin SCL (I2C)
    },
    'LED': {
        'PWM_PIN': 18,  # Pin PWM LED
        'FREQUENCY': 1000,  # Fréquence PWM
    }
}
```

### Interface utilisateur

```python
UI_CONFIG = {
    'DISPLAY': {
        'REFRESH_RATE': 0.1,  # Taux de rafraîchissement
        'DEBOUNCE_TIME': 200,  # Anti-rebond
    }
}
```

## 📁 Structure des fichiers

```
alimante/
├── alimante_main.py          # Script principal
├── test_ecran_psi_encoder.py # Test écran PSI complet
├── test_ecran_psi_simple.py  # Test encodeur simple
├── test_led_bandeaux.py      # Test bandeaux LED
├── config_alimante.py        # Configuration système
└── README_ALIMANTE.md        # Documentation
```

## 🔧 Tests

### Test de l'encodeur

Le script `test_ecran_psi_simple.py` permet de tester uniquement l'encodeur :

- Affiche les rotations (gauche/droite)
- Affiche les appuis sur le bouton
- Compteur en temps réel

### Test des LED

Le script `test_led_bandeaux.py` permet de tester les bandeaux LED :

- Contrôle d'intensité (0-100%)
- Fondu progressif
- Clignotement
- Séquence de test complète

### Test complet

Le script `alimante_main.py` intègre tous les composants :

- Interface écran PSI
- Navigation par encodeur
- Contrôle des LED
- Menu interactif

## 🛠️ Dépannage

### Problèmes courants

1. **Erreur GPIO** : Vérifiez les permissions

   ```bash
   sudo usermod -a -G gpio $USER
   ```

2. **Encodeur non détecté** : Vérifiez le câblage et les pins

3. **LED ne s'allument pas** : Vérifiez le MOSFET et l'alimentation 12V

4. **Interface ne répond pas** : Vérifiez les interruptions GPIO

### Logs

Les erreurs sont affichées dans la console. Pour un logging avancé, modifiez `config_alimante.py`.

## 📞 Support

Pour toute question ou problème :

- Email : contact@alimante.fr
- Documentation : Voir les commentaires dans le code

## 📄 Licence

Projet Alimante - Système de contrôle intelligent
Développé pour la gestion des bandeaux LED avec interface utilisateur avancée.

---

**Version** : 1.0.0  
**Auteur** : Alimante Team  
**Date** : 2024
