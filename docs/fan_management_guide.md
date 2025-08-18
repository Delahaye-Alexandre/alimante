# Guide de Gestion des Ventilateurs - Alimante

## Vue d'ensemble

Le système Alimante intègre une gestion complète des ventilateurs qui s'adapte automatiquement aux conditions environnementales et à la qualité de l'air. Cette fonctionnalité assure un environnement optimal pour l'élevage des insectes.

## Architecture du Système

### Composants Principaux

1. **AirQualityController** - Gère le capteur MQ2 et détermine la qualité de l'air
2. **FanController** - Contrôle les ventilateurs et leur vitesse
3. **Intégration automatique** dans la boucle principale du système

### Flux de Contrôle

```
Capteur MQ2 → AirQualityController → FanController → Ventilateurs
     ↓
Qualité de l'air (PPM) → Niveau de qualité → Vitesse des ventilateurs
```

## Configuration des Ventilateurs

### Configuration GPIO

```json
{
  "gpio_pins": {
    "actuators": {
      "fan_relay": {
        "pin": 25,
        "type": "relay",
        "voltage": "5V",
        "current": "30mA",
        "description": "Relais ventilateurs"
      }
    }
  },
  "hardware_config": {
    "fan": {
      "count": 4,
      "voltage": "5V",
      "current_per_fan": "200mA",
      "total_current": "800mA",
      "control": "relay",
      "min_runtime": 30
    }
  }
}
```

### Configuration par Espèce

Chaque espèce peut avoir sa propre configuration de ventilation :

```json
{
  "ventilation": {
    "enabled": true,
    "fan_count": 4,
    "auto_mode": true,
    "air_quality_thresholds": {
      "excellent": 0,
      "good": 50,
      "moderate": 100,
      "poor": 150,
      "unhealthy": 200,
      "very_unhealthy": 300
    },
    "fan_speed_levels": {
      "excellent": 0,
      "good": 25,
      "moderate": 50,
      "poor": 75,
      "unhealthy": 100,
      "very_unhealthy": 100
    },
    "temperature_threshold": 28.0,
    "humidity_threshold": 80.0,
    "min_runtime_seconds": 30,
    "max_runtime_seconds": 3600
  }
}
```

## Niveaux de Qualité de l'Air

### Seuils PPM (Parties Par Million)

| Niveau       | PPM     | Description    | Action Ventilateurs       |
| ------------ | ------- | -------------- | ------------------------- |
| Excellent    | 0-50    | Air pur        | Éteints (0%)              |
| Bon          | 50-100  | Air acceptable | Vitesse faible (25%)      |
| Modéré       | 100-150 | Air passable   | Vitesse moyenne (50%)     |
| Mauvais      | 150-200 | Air dégradé    | Vitesse élevée (75%)      |
| Malsain      | 200-300 | Air nocif      | Vitesse maximale (100%)   |
| Très malsain | 300+    | Air dangereux  | Vitesse maximale + alerte |

### Logique de Contrôle

1. **Lecture continue** du capteur MQ2
2. **Détermination automatique** du niveau de qualité
3. **Ajustement de la vitesse** des ventilateurs
4. **Surveillance des seuils** de température et humidité

## Contrôle Automatique

### Basé sur la Qualité de l'Air

- **Activation automatique** selon les seuils PPM
- **Ajustement progressif** de la vitesse
- **Désactivation** quand l'air redevient excellent

### Basé sur la Température et l'Humidité

- **Seuils configurables** par espèce
- **Activation** si température > seuil ou humidité > seuil
- **Protection contre le sur-fonctionnement** (temps min/max)

## Intégration dans le Système

### Initialisation

```python
# Dans main.py
controllers['air_quality'] = AirQualityController(gpio_manager, air_quality_config)
controllers['fan'] = FanController(gpio_manager, fan_config)
```

### Boucle Principale

```python
# Contrôle automatique de la ventilation
if 'air_quality' in controllers and 'fan' in controllers:
    success = controllers['air_quality'].control_ventilation(controllers['fan'])
```

### Nettoyage

```python
# Nettoyage automatique des ressources
for controller_name, controller in controllers.items():
    if hasattr(controller, 'cleanup'):
        controller.cleanup()
```

## API REST

### Endpoints Disponibles

- `POST /api/air-quality/control-ventilation` - Contrôle manuel de la ventilation
- `GET /api/air-quality/status` - Statut du capteur de qualité de l'air
- `GET /api/fan/status` - Statut des ventilateurs
- `POST /api/fan/set-speed` - Définir la vitesse manuellement

### Exemple d'Utilisation

```bash
# Contrôler la ventilation basée sur la qualité de l'air
curl -X POST http://localhost:5000/api/air-quality/control-ventilation \
  -H "Authorization: Bearer <token>"

# Obtenir le statut des ventilateurs
curl http://localhost:5000/api/fan/status \
  -H "Authorization: Bearer <token>"
```

## Surveillance et Logging

### Métriques Collectées

- **Qualité de l'air** (PPM, niveau)
- **Vitesse des ventilateurs** (pourcentage)
- **Temps de fonctionnement** (actif/inactif)
- **Erreurs et alertes**

### Logs Système

```
INFO - Qualité de l'air: moderate (125.0 ppm) - Ventilateurs: 50%
INFO - Ventilateurs activés: 4 ventilateurs, 800mA, 5V, 50%
WARNING - ⚠️ Qualité de l'air dégradée: poor (175.0 ppm)
```

## Sécurité et Protection

### Protections Intégrées

1. **Temps de fonctionnement minimum** (30s) pour éviter les cycles courts
2. **Temps de fonctionnement maximum** (1h) pour éviter la surchauffe
3. **Surveillance du courant** et protection contre la surcharge
4. **Arrêt d'urgence** en cas d'erreur critique

### Gestion des Erreurs

- **Capteur défaillant** → Mode dégradé avec ventilation de sécurité
- **GPIO défaillant** → Alerte et arrêt sécurisé
- **Configuration invalide** → Valeurs par défaut sécurisées

## Maintenance

### Vérifications Régulières

1. **Nettoyage des ventilateurs** (poussière, débris)
2. **Calibration du capteur MQ2** (mensuelle)
3. **Vérification des connexions GPIO**
4. **Test des seuils** de qualité de l'air

### Calibration du Capteur

```python
# Calibration automatique au démarrage
success = air_quality_controller.calibrate_sensor()
if not success:
    logger.warning("Capteur non calibré, utilisation des valeurs par défaut")
```

## Dépannage

### Problèmes Courants

1. **Ventilateurs ne démarrent pas**

   - Vérifier la configuration GPIO
   - Contrôler l'alimentation
   - Tester le relais

2. **Qualité de l'air incorrecte**

   - Recalibrer le capteur MQ2
   - Vérifier l'alimentation du capteur
   - Contrôler les connexions

3. **Ventilateurs toujours actifs**
   - Vérifier les seuils de température/humidité
   - Contrôler la logique de contrôle
   - Examiner les logs système

### Tests de Diagnostic

```bash
# Test complet de la gestion des ventilateurs
python test_fan_management.py

# Test d'intégration du système
python -c "import asyncio; from test_fan_management import test_integration; asyncio.run(test_integration())"
```

## Personnalisation

### Ajustement des Seuils

Modifiez les valeurs dans la configuration de l'espèce :

```json
{
  "ventilation": {
    "air_quality_thresholds": {
      "excellent": 0, // Ajuster selon vos besoins
      "good": 40, // Plus strict
      "moderate": 80 // Plus strict
    }
  }
}
```

### Ajout de Nouveaux Niveaux

```python
# Dans AirQualityController
self.air_quality_thresholds["critical"] = 500
self.fan_speed_levels["critical"] = 100
```

## Conclusion

La gestion des ventilateurs d'Alimante offre un contrôle intelligent et automatique de la ventilation, garantissant un environnement optimal pour l'élevage des insectes. L'intégration avec le capteur de qualité de l'air assure une réponse rapide aux changements environnementaux, tandis que les protections intégrées garantissent la sécurité du système.

Pour toute question ou problème, consultez les logs système et utilisez les outils de diagnostic fournis.
