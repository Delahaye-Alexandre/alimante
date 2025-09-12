# Système de Double Trappe Simultanée

## 🎯 Principe de Fonctionnement

Le système de double trappe simultanée utilise **un seul servomoteur** pour contrôler les deux trappes en opposition, garantissant qu'une seule trappe soit ouverte à la fois.

## 🔧 Mécanisme

### Position 0° - Entrée Ouverte

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   MOUCHES   │───▶│     SAS     │    │  TERRARIUM  │
│   (SOURCE)  │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
      ▲                   ▲                   ▲
   OUVERTE            FERMÉE              FERMÉE
```

### Position 90° - Sortie Ouverte

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   MOUCHES   │    │     SAS     │───▶│  TERRARIUM  │
│   (SOURCE)  │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
      ▲                   ▲                   ▲
   FERMÉE            OUVERTE              FERMÉE
```

## 📋 Séquence d'Alimentation

1. **Phase d'entrée** (Position 0°)

   - Entrée ouverte, sortie fermée
   - Les mouches entrent dans le sas
   - Durée basée sur le nombre de mouches souhaitées

2. **Phase de sortie** (Position 90°)

   - Entrée fermée, sortie ouverte
   - Les mouches s'échappent vers le terrarium
   - Délai de stabilisation pour vider le sas

3. **Phase de repos** (Position 0°)
   - Retour à la position fermée
   - Système prêt pour la prochaine alimentation

## ⚙️ Configuration

```json
{
  "double_trap": {
    "enabled": true,
    "simultaneous": true,
    "fly_count": 5,
    "trap_delay": 1.0,
    "calibration": {
      "fly_per_second": 2.0,
      "min_duration": 1.0,
      "max_duration": 5.0
    }
  }
}
```

## 🎛️ Positions du Servo

- **0°** : `trap_entrance_open` - Entrée ouverte, sortie fermée
- **90°** : `trap_entrance_closed` - Entrée fermée, sortie ouverte

## ✅ Avantages

1. **Simplicité mécanique** : Un seul servomoteur
2. **Fiabilité** : Impossible d'avoir les deux trappes ouvertes simultanément
3. **Hygiène** : Aucune mouche ne reste dans le sas
4. **Contrôle statistique** : Nombre de mouches basé sur la durée
5. **Économie d'énergie** : Un seul actionneur

## 🔬 Calibration

Le système peut être calibré pour optimiser le nombre de mouches :

```python
calibration = actuator_controller.calibrate_fly_feeding(test_runs=5)
```

## 📊 Exemple d'Utilisation

```python
# Distribuer 5 mouches
success = actuator_controller.feed_animals_double_trap(
    fly_count=5,
    trap_delay=1.0
)
```

## 🚨 Sécurité

- Vérification de la position du servo avant chaque action
- Gestion des erreurs de positionnement
- Logs détaillés pour le débogage
- Retour à la position fermée en cas d'erreur
