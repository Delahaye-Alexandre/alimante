# Test Matériel Alimante

Ce document explique comment tester les drivers Alimante sur le vrai matériel Raspberry Pi.

## Prérequis

- Raspberry Pi (Zero 2W recommandé)
- Matériel Alimante connecté selon `config/gpio_config.json`
- Python 3.7+

## Installation

### 1. Sur le Raspberry Pi

```bash
# Rendre le script d'installation exécutable
chmod +x install_raspberry_pi_dependencies.sh

# Exécuter l'installation
./install_raspberry_pi_dependencies.sh
```

### 2. Vérification des dépendances

```bash
# Test de préparation (doit être exécuté sur Windows)
python test_hardware_readiness.py

# Test complet sur Raspberry Pi
python3 test_raspberry_pi.py
```

## Matériel Requis

### Capteurs

- **DHT22** : Pin 4 (température/humidité)
- **Capteur qualité d'air** : Pin 5 + ADC (qualité de l'air)
- **Tenflyer water sensor** : Pin 21 (niveau d'eau)

### Actionneurs

- **PWM** : Pin 12 (LED, ventilateurs)
- **Relais chauffage** : Pin 19 (chauffage)
- **Relais humidificateur** : Pin 5 (humidification)
- **Servo distributeur** : Pin 18 (nourriture)

### Périphériques

- **ST7735** : Pins 25 (DC), 24 (RST), SPI (MOSI, SCLK, CS)
- **Encodeur rotatif** : Pins 17 (CLK), 27 (DT), 22 (SW)

## Configuration GPIO

Vérifiez que votre câblage correspond à `config/gpio_config.json` :

```json
{
  "sensors": {
    "temperature_humidity": 4,
    "air_quality": 5,
    "water_level": 21
  },
  "actuators": {
    "pwm_led": 12,
    "heater": 19,
    "humidifier": 5,
    "feeder_servo": 18
  },
  "ui": {
    "display_dc": 25,
    "display_rst": 24,
    "encoder_clk": 17,
    "encoder_dt": 27,
    "encoder_sw": 22
  }
}
```

## Tests Individuels

### Test DHT22

```python
from src.controllers.drivers import DHT22Sensor, DriverConfig

dht22 = DHT22Sensor(DriverConfig("test", enabled=True), gpio_pin=4)
dht22.initialize()
data = dht22.safe_read()
print(f"Température: {data['temperature']}°C")
print(f"Humidité: {data['humidity']}%")
dht22.cleanup()
```

### Test ST7735

```python
from src.controllers.drivers import ST7735Driver, DriverConfig

display = ST7735Driver(DriverConfig("test", enabled=True), dc_pin=25, rst_pin=24)
display.initialize()
display.show_message("Test", "Alimante OK", "green")
display.cleanup()
```

### Test Encodeur Rotatif

```python
from src.controllers.drivers import RotaryEncoderDriver, DriverConfig

def on_rotation(direction, position, old_position):
    print(f"Rotation: {direction}, Position: {position}")

def on_button(position):
    print(f"Bouton pressé: {position}")

encoder = RotaryEncoderDriver(DriverConfig("test", enabled=True), 17, 27, 22)
encoder.set_rotation_callback(on_rotation)
encoder.set_button_callback(on_button)
encoder.initialize()

# Testez en tournant l'encodeur et en appuyant sur le bouton
time.sleep(10)
encoder.cleanup()
```

## Dépannage

### Erreur "DHT22 nécessite un Raspberry Pi"

- Vérifiez que vous êtes sur un Raspberry Pi
- Vérifiez l'installation de RPi.GPIO : `pip3 install RPi.GPIO`

### Erreur "ST7735 nécessite un Raspberry Pi avec st7735"

- Vérifiez l'installation : `pip3 install st7735`
- Vérifiez le câblage SPI

### Erreur "Encodeur rotatif nécessite un Raspberry Pi avec gpiozero"

- Vérifiez l'installation : `pip3 install gpiozero`
- Vérifiez le câblage des pins

### Problèmes de permissions GPIO

```bash
# Ajouter l'utilisateur au groupe gpio
sudo usermod -a -G gpio $USER

# Redémarrer ou se déconnecter/reconnecter
sudo reboot
```

## Résultats Attendus

Si tout fonctionne correctement, vous devriez voir :

- ✅ Température et humidité du DHT22
- ✅ Niveau de qualité d'air
- ✅ Niveau d'eau du réservoir
- ✅ Contrôle PWM des LED/ventilateurs
- ✅ Activation/désactivation des relais
- ✅ Mouvement du servo distributeur
- ✅ Affichage sur l'écran ST7735
- ✅ Réponse de l'encodeur rotatif

## Prochaines Étapes

Une fois que tous les tests passent, vous pouvez :

1. Passer à l'étape 4 : Développement des contrôleurs
2. Intégrer les drivers dans l'application principale
3. Configurer les politiques de contrôle automatique
