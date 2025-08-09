# 🔌 Guide de câblage Alimante

## 📋 **Liste des composants et leurs tensions**

### **Capteurs**

| Composant    | Tension | Courant | Pin GPIO | Description                     |
| ------------ | ------- | ------- | -------- | ------------------------------- |
| **DHT22**    | 3.3V    | 5mA     | 4        | Température et humidité         |
| **MQ135**    | 5V      | 120mA   | 27       | Qualité de l'air                |
| **HC-SR04P** | 3.3V    | 15mA    | 20/21    | Niveau d'eau (trigger/echo)     |
| **DS18B20**  | 3.3V    | 1mA     | 26       | Température radiateur (OneWire) |

### **Actionneurs**

| Composant                     | Tension | Courant   | Pin GPIO | Description              |
| ----------------------------- | ------- | --------- | -------- | ------------------------ |
| **Relais chauffage**          | 5V      | 30mA      | 18       | Contrôle chauffage       |
| **Relais humidité**           | 5V      | 30mA      | 23       | Contrôle pulvérisateur   |
| **Servomoteur**               | 5V      | 100-250mA | 12       | Trappe alimentation      |
| **Relais LED**                | 5V      | 30mA      | 24       | Contrôle bandeau LED 12V |
| **Relais ventilateurs**       | 5V      | 30mA      | 25       | Contrôle 4 ventilateurs  |
| **Transducteur ultrasonique** | 5V      | 50mA      | 22       | Brumisateur ANGEEK 1/2   |

### **Interface utilisateur**

| Composant                | Tension | Courant     | Pin GPIO | Description               |
| ------------------------ | ------- | ----------- | -------- | ------------------------- |
| **Encodeur rotatif CLK** | 3.3V    | négligeable | 5        | Navigation menu (horloge) |
| **Encodeur rotatif DT**  | 3.3V    | négligeable | 6        | Navigation menu (data)    |
| **Encodeur rotatif SW**  | 3.3V    | négligeable | 13       | Validation menu (bouton)  |
| **Switch principal**     | 12V     | selon alim  | externe  | On/Off système            |

### **Indicateurs**

| Composant            | Tension | Courant | Pin GPIO | Description               |
| -------------------- | ------- | ------- | -------- | ------------------------- |
| **LED statut**       | 3.3V    | 20mA    | 13       | Indicateur de statut      |
| **LED alimentation** | 3.3V    | 20mA    | 19       | Indicateur d'alimentation |

### **Caméra**

| Composant      | Tension | Courant | Interface | Description            |
| -------------- | ------- | ------- | --------- | ---------------------- |
| **Caméra CSI** | 3.3V    | 200mA   | CSI-2     | Surveillance terrarium |

---

## 🔧 **Schéma de câblage**

### **Alimentation principale**

```
Raspberry Pi Zero 2W
├── 5V (USB ou alimentation externe)
├── 3.3V (GPIO)
└── GND (masse commune)
```

### **Capteurs**

```
DHT22 (Pin 4)
├── VCC → 3.3V
├── DATA → GPIO 4
└── GND → GND

LDR (Pin 17)
├── VCC → 3.3V
├── SIGNAL → GPIO 17
└── GND → GND

MQ135 (Pin 27)
├── VCC → 5V
├── SIGNAL → GPIO 27
└── GND → GND

HC-SR04P Niveau d'eau (Pins 20/21)
├── VCC → 3.3V
├── TRIGGER → GPIO 20
├── ECHO → GPIO 21
└── GND → GND

DS18B20 Temp radiateur (Pin 26)
├── VCC → 3.3V
├── DATA → GPIO 26 (OneWire)
└── GND → GND
```

### **Relais (5V)**

```
Relais chauffage (Pin 18)
├── VCC → 5V
├── IN → GPIO 18
└── GND → GND

Relais humidité (Pin 23)
├── VCC → 5V
├── IN → GPIO 23
└── GND → GND

Relais LED (Pin 24)
├── VCC → 5V
├── IN → GPIO 24
└── GND → GND

Relais ventilateurs (Pin 25)
├── VCC → 5V
├── IN → GPIO 25
└── GND → GND
```

### **Servomoteur**

```
Servomoteur 9G (Pin 12)
├── VCC → 5V (alimentation externe recommandée)
├── SIGNAL → GPIO 12
└── GND → GND
```

### **Transducteur ultrasonique**

```
Transducteur ultrasonique ANGEEK (Pin 22)
├── VCC → 5V (avec PWM pour contrôle intensité)
├── SIGNAL → GPIO 22
└── GND → GND
```

### **Encodeur rotatif**

```
Encodeur rotatif (Pins 5/6/13)
├── CLK → GPIO 5 (pull-up)
├── DT → GPIO 6 (pull-up)
├── SW → GPIO 13 (pull-up)
├── VCC → 3.3V
└── GND → GND
```

### **LEDs**

```
LED statut (Pin 13)
├── VCC → 3.3V
├── SIGNAL → GPIO 13
└── GND → GND

LED alimentation (Pin 19)
├── VCC → 3.3V
├── SIGNAL → GPIO 19
└── GND → GND
```

### **Caméra CSI**

```
Caméra CSI
├── Connecteur CSI-2 → Port CSI Raspberry Pi
├── Alimentation 3.3V automatique
└── Communication série rapide
```

---

## ⚡ **Alimentation externe**

### **Convertisseur 12V pour LED**

```
Alimentation 12V
├── Convertisseur 12V → 5V
├── LED Strip (12V, 7.2W/m)
└── Relais LED (contrôle)
```

### **Alimentation servo**

```
Alimentation 5V séparée
├── Servomoteur (4.8V-6V)
└── Protection contre les pics de courant
```

---

## 🔍 **Points d'attention**

### **1. Masse commune**

- **TOUS** les composants doivent partager la même masse (GND)
- Éviter les boucles de masse

### **2. Alimentation servo**

- Le servomoteur peut causer des chutes de tension
- Utiliser une alimentation séparée si possible
- Ajouter un condensateur de découplage

### **3. Relais**

- Les relais peuvent générer des interférences
- Utiliser des diodes de protection
- Isoler les circuits haute tension

### **4. Capteur MQ135**

- Consomme 120mA à 5V
- Vérifier la capacité de l'alimentation
- Chauffe pendant le fonctionnement

### **5. Ventilateurs**

- 4 ventilateurs = 800mA à 5V
- Vérifier la capacité de l'alimentation USB
- Considérer une alimentation externe

---

## 🛠️ **Matériel nécessaire**

### **Composants électroniques**

- [ ] Résistances pull-up (10kΩ) pour les boutons
- [ ] Résistances (220Ω) pour les LEDs
- [ ] Diodes de protection pour les relais
- [ ] Condensateurs de découplage (100µF)
- [ ] Convertisseur 12V → 5V pour LED

### **Câblage**

- [ ] Fils de connexion (mâle-femelle)
- [ ] Breadboard pour tests
- [ ] Plaque de prototypage finale
- [ ] Connecteurs JST pour servomoteur

### **Alimentation**

- [ ] Alimentation 5V/3A minimum
- [ ] Alimentation 12V/1A pour LED
- [ ] Bloc d'alimentation multiple

---

## 🧪 **Tests de câblage**

### **Test 1 : LEDs**

```python
# Test LED statut
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(13, GPIO.OUT)
GPIO.output(13, GPIO.HIGH)  # Allumer
time.sleep(1)
GPIO.output(13, GPIO.LOW)   # Éteindre
```

### **Test 2 : Boutons**

```python
# Test bouton urgence
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print(GPIO.input(5))  # Devrait afficher 1 (non pressé)
```

### **Test 3 : Relais**

```python
# Test relais
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.HIGH)  # Activer
time.sleep(1)
GPIO.output(18, GPIO.LOW)   # Désactiver
```

### **Test 4 : Transducteur ultrasonique**

```python
# Test transducteur ultrasonique
GPIO.setup(22, GPIO.OUT)
GPIO.output(22, GPIO.HIGH)  # Activer brumisateur
time.sleep(2)  # Test plus long pour voir la brume
GPIO.output(22, GPIO.LOW)   # Désactiver
```

---

## ⚠️ **Sécurité**

### **1. Vérifications avant alimentation**

- [ ] Toutes les connexions vérifiées
- [ ] Aucun court-circuit
- [ ] Tensions correctes
- [ ] Masse commune

### **2. Tests progressifs**

1. **Alimentation Raspberry Pi** uniquement
2. **LEDs** et **boutons**
3. **Relais** (sans charge)
4. **Capteurs**
5. **Servomoteur**
6. **Ventilateurs**
7. **LED strip**

### **3. Protection**

- Fusibles si nécessaire
- Diodes de protection
- Condensateurs de découplage
- Isolation des circuits haute tension

---

## 📊 **Consommation électrique**

### **Calcul total**

```
Raspberry Pi Zero 2W: ~500mA @ 5V
Capteurs: ~126mA @ 5V
Relais: ~120mA @ 5V
Servomoteur: ~250mA @ 5V (pic)
Ventilateurs: ~800mA @ 5V
Transducteur ultrasonique ANGEEK: ~50mA @ 5V
Capteur niveau d'eau HC-SR04P: ~15mA @ 3.3V
Capteur température DS18B20: ~1mA @ 3.3V
Caméra CSI: ~200mA @ 3.3V
LEDs: ~40mA @ 3.3V

TOTAL: ~1.85A @ 5V + 0.256A @ 3.3V + 0.1A @ 12V (pic)
```

### **Recommandations**

- **Alimentation 5V/3A** minimum
- **Alimentation 12V/1A** pour LED strip et transducteur ultrasonique
- **Protection contre les surtensions**
- **Ventilation** du boîtier
