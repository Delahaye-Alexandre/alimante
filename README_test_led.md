# Test Bandeaux LED - 4 bandeaux de 15cm

## Description

Script de test pour contrôler 4 bandeaux LED de 15cm connectés au même MOSFET sur le GPIO 24 de votre Raspberry Pi.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python test_led_bandeaux.py
```

## Fonctionnalités

### Contrôle de base

- **Intensité en pourcentage** : Contrôle précis de 0% à 100%
- **PWM** : Modulation de largeur d'impulsion pour un contrôle fluide
- **Sécurité** : Gestion des erreurs et arrêt propre

### Fonctions de test

1. **Définir intensité** : Contrôle manuel de l'intensité
2. **Fondu progressif** : Fondu d'entrée et de sortie
3. **Clignotement** : Test de clignotement configurable
4. **Séquence complète** : Test automatisé de toutes les fonctions
5. **Test intensités multiples** : Test de différentes valeurs

## Configuration matérielle

- **GPIO** : Pin 24 (BCM)
- **MOSFET** : Un seul MOSFET pour les 4 bandeaux
- **Fréquence PWM** : 1000 Hz (configurable)
- **Tension** : Compatible 3.3V/5V selon votre MOSFET

## Sécurité

- Arrêt propre avec Ctrl+C
- Validation des valeurs d'intensité
- Gestion des erreurs GPIO
- Nettoyage automatique des ressources

## Exemple d'utilisation

```python
from test_led_bandeaux import LEDBandeauxController

# Création du contrôleur
led = LEDBandeauxController(gpio_pin=24)

# Initialisation
led.initialize()

# Contrôle de l'intensité
led.set_intensity(50)  # 50% d'intensité

# Fondu progressif
led.fade_in(3.0)  # 3 secondes

# Nettoyage
led.cleanup()
```

## Notes

- Ce fichier est temporaire et sera supprimé après les tests
- Assurez-vous que votre Raspberry Pi est correctement configuré
- Vérifiez les connexions avant de lancer le test
