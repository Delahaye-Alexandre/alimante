# Tests de Composants Alimante

Ce répertoire contient les programmes de test pour tous les composants du système d'élevage automatisé Alimante.

## 📋 Composants Testés

1. **DHT22** - Capteur température et humidité
2. **Transducteurs** - Pour la génération de brume
3. **Servomoteur** - Contrôle de la trappe d'alimentation
4. **Caméra CSI** - Surveillance vidéo
5. **Écran TFT 1.8" SPI** - Interface utilisateur
6. **Capteur MQ2** - Qualité de l'air
7. **MOSFET** - Contrôle des actionneurs
8. **Ventilateurs (4x)** - Contrôle de la ventilation (4 ventilateurs en parallèle)
9. **Convertisseur ADC** - Analogique vers numérique

## 🚀 Installation

### 1. Prérequis

- Raspberry Pi (recommandé: Pi 4B)
- Python 3.7+
- Accès root pour l'installation des packages

### 2. Installation des dépendances

```bash
# Rendre le script exécutable
chmod +x tests/install_dependencies.sh

# Exécuter l'installation
./tests/install_dependencies.sh
```

### 3. Configuration des pins

Modifiez le fichier `config/pin_config.json` selon vos connexions :

```json
{
  "pin_assignments": {
    "sensors": {
      "dht22": { "pin": 4 },
      "mq2": { "pin": 17, "adc_channel": 0 }
    }
    // ... autres configurations
  }
}
```

## 🔧 Utilisation

### Test complet de tous les composants

```bash
python3 tests/component_test.py
```

### Test d'un composant spécifique

```bash
python3 tests/quick_test.py dht22
python3 tests/quick_test.py servo
python3 tests/quick_test.py camera
python3 tests/quick_test.py fans
```

### Liste des composants disponibles

```bash
python3 tests/quick_test.py list
```

### Test de tous les composants (version rapide)

```bash
python3 tests/quick_test.py all
```

## 📊 Résultats

Les tests génèrent :

- **Logs** : `component_test.log`
- **Résultats JSON** : `test_results.json`
- **Image de test caméra** : `camera_test.jpg`

### Format des résultats

```json
{
  "total_tests": 9,
  "passed": 8,
  "failed": 1,
  "success_rate": 88.9,
  "total_duration": 12.34,
  "results": [
    {
      "component": "DHT22",
      "status": "PASSED",
      "message": "Température: 23.5°C, Humidité: 45.2%",
      "data": { "temperature": 23.5, "humidity": 45.2 },
      "duration": 1.23
    }
  ]
}
```

## 🔌 Configuration des Pins

### Pins par défaut

| Composant    | Pin | Description                   |
| ------------ | --- | ----------------------------- |
| DHT22        | 4   | Capteur température/humidité  |
| MQ2          | 17  | Capteur qualité air (via ADC) |
| Servo        | 12  | Servomoteur trappe            |
| MOSFET       | 18  | Contrôle actionneurs          |
| Transducteur | 23  | Générateur de brume           |
| Ventilateurs | 16  | 4 ventilateurs en parallèle   |
| Écran CE     | 8   | Écran TFT SPI                 |
| Écran DC     | 25  | Écran TFT SPI                 |
| Écran RST    | 24  | Écran TFT SPI                 |
| ADC CS       | 22  | Convertisseur ADC             |

### Modification des pins

1. Éditez `config/pin_config.json`
2. Modifiez les valeurs selon vos connexions
3. Relancez les tests

## 🛠️ Dépannage

### Erreurs courantes

#### "ModuleNotFoundError: No module named 'RPi.GPIO'"

```bash
pip3 install RPi.GPIO
```

#### "Permission denied" pour GPIO

```bash
sudo usermod -a -G gpio $USER
# Redémarrez la session
```

#### Caméra non détectée

```bash
# Vérifiez que la caméra est activée
sudo raspi-config
# Interface Options > Camera > Enable
```

#### SPI non disponible

```bash
# Activez SPI
sudo raspi-config
# Interface Options > SPI > Enable
```

### Tests individuels

Si un composant échoue, testez-le individuellement :

```bash
python3 tests/quick_test.py dht22
```

### Vérification des connexions

1. **DHT22** : VCC (3.3V), GND, DATA (Pin 4)
2. **Servo** : VCC (5V), GND, Signal (Pin 12)
3. **MQ2** : VCC (5V), GND, Signal (via ADC)
4. **Ventilateurs (4x)** : VCC (12V direct), GND, PWM (Pin 16)
5. **Écran TFT** : SPI + CE/DC/RST pins

## 📈 Calibration

### Capteur MQ2

Le capteur MQ2 nécessite une calibration :

1. Placez le capteur dans un environnement propre
2. Exécutez le test plusieurs fois
3. Notez les valeurs de référence
4. Ajustez les paramètres dans `config/pin_config.json`

### Servomoteur

Ajustez les angles selon votre mécanisme :

```json
{
  "actuators": {
    "servo": {
      "min_angle": 0,
      "max_angle": 180
    }
  }
}
```

## 🔍 Logs détaillés

Les logs complets sont dans `component_test.log` :

```bash
tail -f component_test.log
```

## 📝 Personnalisation

### Ajout d'un nouveau composant

1. Ajoutez la méthode de test dans `ComponentTester`
2. Ajoutez la configuration dans `config/pin_config.json`
3. Ajoutez le test dans la liste `tests` de `run_all_tests()`

### Modification des paramètres de test

Éditez `config/pin_config.json` :

```json
{
  "test_configuration": {
    "servo_test_angles": [0, 90, 180],
    "transducer_test_duration": 0.2
  }
}
```

## 🆘 Support

En cas de problème :

1. Vérifiez les connexions physiques
2. Consultez les logs : `component_test.log`
3. Testez individuellement : `python3 tests/quick_test.py <composant>`
4. Vérifiez la configuration : `config/pin_config.json`

## 📄 Licence

Ce code fait partie du projet Alimante et suit la même licence.
