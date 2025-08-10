# Guide d'utilisation du système de logging Alimante

## Vue d'ensemble

Le système de logging d'Alimante est un système robuste et configurable qui permet de tracer l'activité du système hydroponique avec différents niveaux de détail et formats de sortie.

## Fonctionnalités principales

- **Logging structuré** : Support JSON pour l'analyse automatisée
- **Logging coloré** : Sortie console avec couleurs pour une meilleure lisibilité
- **Rotation automatique** : Gestion automatique de la taille des fichiers de logs
- **Handlers multiples** : Console, fichiers principaux, erreurs, critiques et métriques
- **Gestion d'erreurs robuste** : Fallback automatique en cas de problème
- **Contexte structuré** : Ajout d'informations contextuelles aux logs

## Utilisation de base

### Import et configuration

```python
from src.utils.logging_config import get_logger, setup_logging

# Configuration automatique
logger = get_logger("mon_module")

# Ou configuration manuelle
logger = setup_logging("mon_module")
```

### Logging simple

```python
logger.debug("Message de debug")
logger.info("Information générale")
logger.warning("Avertissement")
logger.error("Erreur")
logger.critical("Erreur critique")
```

### Logging avec contexte

```python
logger.info("Action utilisateur", {
    "user_id": "12345",
    "action": "modifier_config",
    "timestamp": "2024-01-01T12:00:00"
})
```

### Logging d'exceptions

```python
try:
    # Code qui peut lever une exception
    pass
except Exception as e:
    logger.exception("Erreur lors de l'opération", {
        "operation": "lecture_capteur",
        "sensor_id": "temp_01"
    })
```

## Fonctions utilitaires

### Logs système

```python
from src.utils.logging_config import log_system_start, log_system_stop

log_system_start()  # Au démarrage
log_system_stop()   # À l'arrêt
```

### Logs de capteurs

```python
from src.utils.logging_config import log_sensor_reading

log_sensor_reading("temperature", 25.5, "°C")
log_sensor_reading("humidite", 65.2, "%")
```

### Logs de contrôleurs

```python
from src.utils.logging_config import log_controller_action

log_controller_action("pompe", "demarrer", True, {
    "pression": 2.1,
    "debit": 5.0
})
```

### Logs d'API

```python
from src.utils.logging_config import log_api_request

log_api_request("GET", "/api/sensors", 200, 45.2, "user123")
```

## Configuration

### Fichier de configuration

Le système peut être configuré via le fichier `config/logging.yaml` :

```yaml
logging:
  level: INFO
  format: colored
  
  handlers:
    console:
      enabled: true
      level: INFO
      
    file:
      enabled: true
      level: DEBUG
      max_size: 10MB
      backup_count: 5
```

### Variables d'environnement

```bash
export LOG_LEVEL=DEBUG
export LOG_FORMAT=json
export LOG_FILE_ENABLED=true
```

## Structure des logs

### Format JSON (fichiers)

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "level": "INFO",
  "logger": "alimante.controllers",
  "message": "Pompe démarrée",
  "module": "pump_controller",
  "function": "start_pump",
  "line": 45,
  "context": {
    "pump_id": "pump_01",
    "pressure": 2.1
  }
}
```

### Format coloré (console)

```
[12:00:00] INFO | pump_controller:start_pump:45 | 🚰 Pompe démarrée
```

## Gestion des erreurs

Le système de logging est conçu pour être robuste :

1. **Fallback automatique** : Si la configuration échoue, un handler de base est utilisé
2. **Gestion des permissions** : Les erreurs de fichiers sont gérées gracieusement
3. **Logs d'erreur** : Les erreurs de configuration sont loggées quand possible

## Tests

### Test automatique

```python
from src.utils.logging_config import test_logging_system

if test_logging_system():
    print("Système de logging fonctionnel")
else:
    print("Problème avec le système de logging")
```

### Statut du système

```python
from src.utils.logging_config import get_logging_status

status = get_logging_status()
print(f"Handlers configurés: {status['handlers_count']}")
```

## Bonnes pratiques

1. **Utilisez des noms de logger descriptifs** : `alimante.controllers.pump`
2. **Ajoutez du contexte pertinent** : IDs, paramètres, métriques
3. **Choisissez le bon niveau** : DEBUG pour le développement, INFO pour la production
4. **Évitez les logs sensibles** : mots de passe, tokens, données personnelles
5. **Utilisez les fonctions utilitaires** : `log_sensor_reading`, `log_controller_action`

## Dépannage

### Problèmes courants

1. **Pas de logs dans les fichiers** : Vérifiez les permissions du dossier `logs/`
2. **Logs dupliqués** : Vérifiez que `propagate=False` est configuré correctement
3. **Performance** : Évitez de logger dans les boucles critiques

### Vérifications

```python
# Vérifier la configuration
status = get_logging_status()
print(status)

# Tester le système
test_logging_system()

# Vérifier les handlers
logger = get_logger()
for handler in logger.logger.handlers:
    print(f"Handler: {handler.__class__.__name__}")
```

## Intégration avec d'autres systèmes

Le système de logging peut être intégré avec :

- **Systèmes de monitoring** : Prometheus, Grafana
- **Agrégateurs de logs** : ELK Stack, Fluentd
- **Alertes** : Notifications en cas d'erreurs critiques
- **Métriques** : Collecte de métriques système
