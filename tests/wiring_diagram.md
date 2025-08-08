# Schéma de Câblage - Alimentation Directe

## 🔌 Principe d'Alimentation Directe

Tous les composants sont alimentés directement depuis l'alimentation principale, **PAS** via le Raspberry Pi pour éviter la surcharge.

## 📋 Composants et Alimentation

### 🔋 Alimentation Principale

- **Alimentation 12V** pour les ventilateurs et actionneurs
- **Alimentation 5V** pour les capteurs et servomoteur
- **Alimentation 3.3V** pour les capteurs numériques

### 🔧 Composants par Alimentation

#### 12V Direct (Alimentation Principale)

```
┌─────────────────┐
│   Alimentation  │
│     12V DC      │
└─────────┬───────┘
          │
          ├─── Ventilateur 1 (12V)
          ├─── Ventilateur 2 (12V)
          ├─── Ventilateur 3 (12V)
          ├─── Ventilateur 4 (12V)
          └─── Transducteurs (12V)
```

#### 5V Direct (Alimentation Principale)

```
┌─────────────────┐
│   Alimentation  │
│     5V DC       │
└─────────┬───────┘
          │
          ├─── Servomoteur (5V)
          ├─── Capteur MQ2 (5V)
          └─── MOSFET (5V)
```

#### 3.3V (Raspberry Pi)

```
┌─────────────────┐
│   Raspberry Pi  │
│     3.3V        │
└─────────┬───────┘
          │
          └─── DHT22 (3.3V)
```

## 🔌 Connexions Détaillées

### Ventilateurs (4x) - Pin 16

```
Alimentation 12V ──┬── Ventilateur 1
                   ├── Ventilateur 2
                   ├── Ventilateur 3
                   └── Ventilateur 4
                          │
                          └── PWM (Pin 16) ── Raspberry Pi
```

### Servomoteur - Pin 12

```
Alimentation 5V ── Servomoteur ── Signal (Pin 12) ── Raspberry Pi
```

### Capteur MQ2 - ADC

```
Alimentation 5V ── MQ2 ── Signal ── ADC ── Raspberry Pi
```

### DHT22 - Pin 4

```
Raspberry Pi 3.3V ── DHT22 ── Data (Pin 4) ── Raspberry Pi
```

## ⚠️ Points Importants

### 1. Masse Commune

- **TOUS** les composants partagent la même masse (GND)
- Connectez la masse de l'alimentation à la masse du Raspberry Pi

### 2. Protection

- Utilisez des diodes de protection pour les ventilateurs
- Ajoutez des condensateurs de découplage si nécessaire

### 3. Courant

- **Ventilateurs** : ~0.5A chacun (2A total)
- **Servomoteur** : ~0.5A
- **Capteurs** : ~0.1A chacun

## 🔧 Configuration PWM

### Ventilateurs (25kHz)

```python
# Fréquence optimale pour les ventilateurs 12V
frequency = 25000  # 25kHz
duty_cycle = 0-100  # 0-100%
```

### Servomoteur (50Hz)

```python
# Fréquence standard pour servomoteur
frequency = 50  # 50Hz
duty_cycle = 2.5-12.5  # 0-180°
```

## 📊 Avantages de l'Alimentation Directe

✅ **Pas de surcharge** du Raspberry Pi  
✅ **Courants élevés** possibles  
✅ **Stabilité** de l'alimentation  
✅ **Séparation** des circuits  
✅ **Maintenance** facilitée

## 🛠️ Vérifications

1. **Masse commune** : Tous les GND connectés
2. **Tensions correctes** : 12V, 5V, 3.3V
3. **Courants adéquats** : Vérifiez les capacités
4. **Protection** : Diodes et condensateurs
5. **Isolation** : Pas de court-circuit

## 🔍 Test de Câblage

```bash
# Test des ventilateurs
python3 tests/quick_test.py fans

# Test du servomoteur
python3 tests/quick_test.py servo

# Test complet
python3 tests/component_test.py
```
