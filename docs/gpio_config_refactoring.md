# Refactorisation de la Configuration GPIO

## Vue d'ensemble

Ce document décrit la refactorisation effectuée pour centraliser la gestion des pins GPIO dans le projet Alimante. Avant cette refactorisation, les pins GPIO étaient hardcodés dans chaque contrôleur, ce qui rendait la maintenance et la configuration difficiles.

## Problèmes identifiés

### Avant la refactorisation

- **Pins hardcodés** : Chaque contrôleur définissait ses propres pins GPIO
- **Duplication de code** : Configuration répétée dans plusieurs fichiers
- **Maintenance difficile** : Changement de pin nécessitait la modification de plusieurs fichiers
- **Risque d'erreur** : Possibilité de conflits de pins entre contrôleurs
- **Configuration dispersée** : Pas de vue d'ensemble centralisée

### Exemples de code problématique

```python
# Dans temperature_controller.py (AVANT)
self.temp_sensor_pin = 4  # Hardcodé
self.heating_relay_pin = 18  # Hardcodé

# Dans humidity_controller.py (AVANT)
self.humidity_relay_pin = 23  # Hardcodé

# Dans fan_controller.py (AVANT)
self.fan_relay_pin = 25  # Hardcodé
```

## Solution implémentée

### 1. Service de Configuration GPIO Centralisé

Création du service `GPIOConfigService` qui :

- Charge la configuration depuis `config/gpio_config.json`
- Extrait et valide les configurations des capteurs, actionneurs et interfaces
- Fournit des méthodes pour récupérer les pins de manière cohérente
- Gère les fallbacks et la validation

### 2. Structure de Configuration Standardisée

```python
@dataclass
class GPIOPinConfig:
    pin: int
    type: str
    voltage: str
    current: str
    power_connection: str
    description: str
    mode: str = "input"
    initial_state: Optional[bool] = None
    pull_up: Optional[bool] = None
    frequency: Optional[int] = None
    adc_channel: Optional[int] = None
    i2c_address: Optional[str] = None
```

### 3. Méthodes d'Accès Unifiées

```python
class GPIOConfigService:
    def get_sensor_pin(self, sensor_name: str) -> Optional[int]
    def get_actuator_pin(self, actuator_name: str) -> Optional[int]
    def get_pin_assignment(self, pin_name: str) -> Optional[int]
    def get_sensor_config(self, sensor_name: str) -> Optional[GPIOPinConfig]
    def get_actuator_config(self, actuator_name: str) -> Optional[GPIOPinConfig]
    def get_interface_config(self, interface_name: str) -> Optional[Dict[str, Any]]
```

## Contrôleurs Refactorisés

### ✅ Contrôleurs déjà refactorisés

1. **TemperatureController** - Utilise `get_sensor_pin('temp_humidity')` et `get_actuator_pin('heating_relay')`
2. **HumidityController** - Utilise `get_sensor_pin('temp_humidity')` et `get_actuator_pin('humidity_relay')`
3. **FanController** - Utilise `get_actuator_pin('fan_relay')`
4. **LightController** - Utilise `get_actuator_pin('led_strip')` et `get_sensor_pin('light')`
5. **FeedingController** - Utilise `get_actuator_pin('feeding_servo')`
6. **WaterLevelController** - Utilise `get_sensor_config('water_level')`
7. **RadiatorTempController** - Utilise `get_sensor_config('radiator_temp')`
8. **AirQualityController** - Utilise `get_sensor_config('mq2_gas')`
9. **LCDMenuController** - Utilise `get_interface_config('lcd_st7735')` et `get_interface_config('rotary_encoder')`

### 🔄 Contrôleurs à refactoriser

- **CameraController** - N'utilise pas de pins GPIO (interface CSI)
- **UltrasonicMistController** - À vérifier s'il existe

## Exemples de Code Refactorisé

### Avant (hardcodé)

```python
def _setup_pins(self):
    # Pin du capteur DHT22
    temp_sensor_pin = 4  # Hardcodé
    temp_sensor_config = PinConfig(
        pin=temp_sensor_pin,
        mode=PinMode.INPUT
    )
    self.gpio_manager.setup_pin(temp_sensor_config)
```

### Après (configuration centralisée)

```python
def _setup_pins(self):
    # Utiliser le service de configuration GPIO
    from ..services.gpio_config_service import GPIOConfigService
    gpio_service = GPIOConfigService()

    # Pin du capteur DHT22
    temp_sensor_pin = gpio_service.get_sensor_pin('temp_humidity')
    if temp_sensor_pin is None:
        temp_sensor_pin = gpio_service.get_pin_assignment('TEMP_HUMIDITY_PIN')

    temp_sensor_config = PinConfig(
        pin=temp_sensor_pin,
        mode=PinMode.INPUT
    )
    self.gpio_manager.setup_pin(temp_sensor_config)
```

## Avantages de la Refactorisation

### 1. **Maintenance Simplifiée**

- Changement de pin dans un seul fichier (`gpio_config.json`)
- Pas de risque d'oublier de modifier un contrôleur

### 2. **Configuration Centralisée**

- Vue d'ensemble de tous les pins utilisés
- Validation automatique des conflits de pins
- Documentation intégrée dans la configuration

### 3. **Flexibilité**

- Support des fallbacks vers les anciennes assignations
- Configuration dynamique sans redémarrage
- Support de différents types de composants

### 4. **Validation et Sécurité**

- Vérification automatique des pins configurés
- Détection des conflits potentiels
- Gestion des erreurs centralisée

### 5. **Tests et Développement**

- Tests unitaires simplifiés
- Configuration de test facile
- Démonstrations et exemples

## Utilisation du Service

### Initialisation

```python
from src.services.gpio_config_service import GPIOConfigService

# Service avec chemin par défaut
gpio_service = GPIOConfigService()

# Service avec chemin personnalisé
gpio_service = GPIOConfigService("config/custom_gpio_config.json")
```

### Récupération des Pins

```python
# Pins des capteurs
temp_pin = gpio_service.get_sensor_pin('temp_humidity')
light_pin = gpio_service.get_sensor_pin('light')

# Pins des actionneurs
heating_pin = gpio_service.get_actuator_pin('heating_relay')
fan_pin = gpio_service.get_actuator_pin('fan_relay')

# Assignations de pins (fallback)
temp_pin = gpio_service.get_pin_assignment('TEMP_HUMIDITY_PIN')
```

### Configuration Complète

```python
# Configuration complète d'un capteur
sensor_config = gpio_service.get_sensor_config('mq2_gas')
if sensor_config:
    print(f"Pin: {sensor_config.pin}")
    print(f"Type: {sensor_config.type}")
    print(f"Tension: {sensor_config.voltage}")
    print(f"Canal ADC: {sensor_config.adc_channel}")
```

## Tests et Validation

### Tests Unitaires

```bash
cd tests/unit
python -m pytest test_gpio_config_service.py -v
```

### Démonstration

```bash
cd tests/demos
python demo_gpio_config_service.py
```

### Validation de Configuration

```python
# Vérifier qu'un pin est configuré
is_valid = gpio_service.validate_pin_config(4)

# Obtenir un résumé de la configuration
summary = gpio_service.get_config_summary()
```

## Migration et Rétrocompatibilité

### Stratégie de Fallback

Le service implémente une stratégie de fallback en deux étapes :

1. **Première tentative** : Récupération depuis la nouvelle structure (`sensors`, `actuators`, `interface`)
2. **Fallback** : Utilisation des anciennes assignations (`pin_assignments`)

### Migration Progressive

- Les contrôleurs existants continuent de fonctionner
- Migration possible contrôleur par contrôleur
- Pas de rupture de compatibilité

## Configuration du Fichier JSON

### Structure Recommandée

```json
{
  "gpio_pins": {
    "sensors": {
      "temp_humidity": {
        "gpio_pin": 4,
        "type": "DHT22",
        "voltage": "3.3V",
        "current": "5mA",
        "power_connection": "3v3_power_rail",
        "description": "Capteur température et humidité DHT22"
      }
    },
    "actuators": {
      "heating_relay": {
        "gpio_pin": 18,
        "type": "relay",
        "voltage": "5.1V",
        "current": "30mA",
        "power_connection": "5v1_power_rail",
        "description": "Relais chauffage"
      }
    }
  },
  "pin_assignments": {
    "TEMP_HUMIDITY_PIN": 4,
    "HEATING_RELAY_PIN": 18
  }
}
```

## Prochaines Étapes

### 1. **Validation Complète**

- Tester tous les contrôleurs refactorisés
- Vérifier la compatibilité avec l'ancien système
- Valider les performances

### 2. **Documentation**

- Mettre à jour la documentation technique
- Créer des guides de migration
- Documenter les bonnes pratiques

### 3. **Améliorations Futures**

- Interface web pour la configuration
- Validation automatique des schémas de câblage
- Gestion des profils de configuration

### 4. **Formation**

- Former l'équipe sur le nouveau système
- Créer des exemples d'utilisation
- Établir des standards de développement

## Conclusion

Cette refactorisation apporte une amélioration significative de la maintenabilité et de la flexibilité du système de configuration GPIO. En centralisant la gestion des pins, nous avons éliminé les problèmes de duplication et de maintenance, tout en préservant la compatibilité avec l'ancien système.

Le nouveau service `GPIOConfigService` fournit une interface claire et cohérente pour accéder aux configurations GPIO, facilitant le développement futur et la maintenance du système Alimante.
