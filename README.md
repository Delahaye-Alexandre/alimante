# 🎛️ Alimante - Système de Contrôle LED

Système de contrôle intelligent pour bandeaux LED avec interface utilisateur basée sur encodeur rotatif et écran ST7735.

## 📁 Structure du Projet

```
alimante/
├── alimante_menu.py          # Menu principal (à utiliser)
├── test_rotation_menu.py     # Test de rotation (debug)
├── config_alimante.py        # Configuration système
├── requirements.txt          # Dépendances Python
└── README.md                # Documentation
```

## 🚀 Utilisation

### Lancement du menu principal

```bash
python alimante_menu.py
```

### Test de rotation (debug)

```bash
python test_rotation_menu.py
```

## 🔧 Configuration

### Branchements ST7735

```
ST7735    →    Raspberry Pi
VCC       →    3.3V (Pin 1 ou 17)
GND       →    GND (Pin 6, 9, 14, 20, 25, 30, 34, 39)
CS        →    GPIO 8 (Pin 24)
RST       →    GPIO 24 (Pin 18)
A0/DC     →    GPIO 25 (Pin 22)
SDA/MOSI  →    GPIO 10 (Pin 19)
SCL/SCLK  →    GPIO 11 (Pin 23)
```

### Branchements Encodeur

```
Encodeur  →    Raspberry Pi
CLK       →    GPIO 17 (Pin 11)
DT        →    GPIO 27 (Pin 13)
SW        →    GPIO 22 (Pin 15)
VCC       →    3.3V
GND       →    GND
```

## 📋 Contrôles

- **Rotation horaire** : Menu vers le bas
- **Rotation anti-horaire** : Menu vers le haut
- **Bouton** : Sélectionner l'option
- **Ctrl+C** : Quitter

## 🎨 Menu Disponible

1. 🏠 **Accueil Alimante**
2. 💡 **Test LED Bandeaux**
3. 📊 **Monitoring Système**
4. ⚙️ **Configuration**
5. 🔧 **Tests Hardware**
6. 📈 **Statistiques**
7. ℹ️ **À propos**

## 📦 Installation

```bash
# Installation des dépendances
pip install -r requirements.txt

# Lancement
python alimante_menu.py
```

## 🔧 Configuration Technique

- **Écran** : ST7735 160x128 pixels
- **Format couleur** : RGB standard
- **Rotation** : 270° (ajustable)
- **Encodeur** : Logique inversée pour votre montage
- **Anti-rebond** : Intégré dans gpiozero

## 🛠️ Développement

Pour ajouter de nouvelles fonctionnalités :

1. Modifiez `config_alimante.py` pour les nouveaux items de menu
2. Ajoutez les actions correspondantes dans `alimante_menu.py`
3. Testez avec `test_rotation_menu.py` si nécessaire

## 📝 Notes

- Configuration testée et validée
- Couleurs RGB standard (pas de conversion nécessaire)
- Encodeur monté à l'envers (logique inversée)
- Interface temps réel avec mise à jour automatique
