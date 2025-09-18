# Système de Double Trappe avec SAS

## 🎯 Principe de Fonctionnement

Le système utilise **un seul servomoteur** qui actionne les deux trappes en même temps :

- **Trappe 1** : Contrôle l'accès depuis la source de mouches vers le SAS
- **Trappe 2** : Contrôle l'accès depuis le SAS vers le terrarium

Les deux trappes sont **toujours en opposition** : quand l'une s'ouvre, l'autre se ferme automatiquement.

## 🔧 Mécanisme

### Position 0° - SAS Ouvert (Entrée des mouches)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   MOUCHES   │───▶│     SAS     │    │  TERRARIUM  │
│   (SOURCE)  │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
      ▲                   ▲                   ▲
   OUVERTE            FERMÉE              FERMÉE
   (Trap 1)          (Trap 2)           (Trap 2)
```

**État :** Les mouches peuvent entrer dans le SAS, mais ne peuvent pas sortir vers le terrarium.

### Position 100° - SAS Fermé (Sortie vers terrarium)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   MOUCHES   │    │     SAS     │───▶│  TERRARIUM  │
│   (SOURCE)  │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
      ▲                   ▲                   ▲
   FERMÉE            OUVERTE              OUVERTE
   (Trap 1)          (Trap 2)           (Trap 2)
```

**État :** Les mouches ne peuvent plus entrer dans le SAS, mais peuvent sortir vers le terrarium.

## 📋 Séquence d'Alimentation

1. **Phase d'entrée** (Position 0°)

   - **Trappe 1** : OUVERTE (mouches entrent dans le SAS)
   - **Trappe 2** : FERMÉE (pas d'accès au terrarium)
   - Les mouches s'accumulent dans le SAS
   - Durée basée sur le nombre de mouches souhaitées

2. **Phase de sortie** (Position 100°)

   - **Trappe 1** : FERMÉE (plus d'entrée de mouches)
   - **Trappe 2** : OUVERTE (accès au terrarium)
   - Les mouches s'échappent vers le terrarium
   - Délai de stabilisation pour vider le SAS

3. **Phase de repos** (Position 0°)
   - Retour à la position d'entrée
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

- **0°** : `trap1_open` - Trappe 1 ouverte (entrée SAS), Trappe 2 fermée (sortie terrarium)
- **100°** : `trap2_open` - Trappe 1 fermée (entrée SAS), Trappe 2 ouverte (sortie terrarium)

## ✅ Avantages

1. **Simplicité mécanique** : Un seul servomoteur actionne les deux trappes
2. **Sécurité** : Impossible d'avoir les deux trappes ouvertes simultanément
3. **Contrôle du flux** : Les mouches sont d'abord piégées dans le SAS
4. **Hygiène** : Aucune mouche ne reste dans le SAS après utilisation
5. **Contrôle statistique** : Nombre de mouches basé sur la durée d'ouverture
6. **Économie d'énergie** : Un seul actionneur pour deux fonctions

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
