# 🔌 Guide de câblage Alimante

## 📋 **Liste des composants et leurs tensions**

### **Capteurs**

| Composant | Tension | Courant | Pin GPIO | Description             |
| --------- | ------- | ------- | -------- | ----------------------- |
| **DHT22** | 3.3V    | 5mA     | 4        | Température et humidité |
| **LDR**   | 3.3V    | 1mA     | 17       | Capteur de lumière      |
| **MQ135** | 5V      | 120mA   | 27       | Qualité de l'air        |

### **Actionneurs**

| Composant               | Tension | Courant   | Pin GPIO | Description              |
| ----------------------- | ------- | --------- | -------- | ------------------------ |
| **Relais chauffage**    | 5V      | 30mA      | 18       | Contrôle chauffage       |
| **Relais humidité**     | 5V      | 30mA      | 23       | Contrôle pulvérisateur   |
| **Servomoteur**         | 5V      | 100-250mA | 12       | Trappe alimentation      |
| **Relais LED**          | 5V      | 30mA      | 24       | Contrôle bandeau LED 12V |
| **Relais ventilateurs** | 5V      | 30mA      | 25       | Contrôle 4 ventilateurs  |
| **Buzzer**              | 3.3V    | 20-40mA   | 22       | Transducteur sonore      |

### **Entrées**

| Composant               | Tension | Courant     | Pin GPIO | Description              |
| ----------------------- | ------- | ----------- | -------- | ------------------------ |
| **Bouton urgence**      | 3.3V    | négligeable | 5        | Bouton d'arrêt d'urgence |
| **Bouton alimentation** | 3.3V    | négligeable | 6        | Alimentation manuelle    |

### **Indicateurs**

| Composant            | Tension | Courant | Pin GPIO | Description               |
| -------------------- | ------- | ------- | -------- | ------------------------- |
| **LED statut**       | 3.3V    | 20mA    | 13       | Indicateur de statut      |
| **LED alimentation** | 3.3V    | 20mA    | 19       | Indicateur d'alimentation |

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

### **Buzzer**

```
Buzzer (Pin 22)
├── VCC → 3.3V
├── SIGNAL → GPIO 22
└── GND → GND
```

### **Boutons**

```
Bouton urgence (Pin 5)
├── VCC → 3.3V
├── SIGNAL → GPIO 5 (pull-up)
└── GND → GND

Bouton alimentation (Pin 6)
├── VCC → 3.3V
├── SIGNAL → GPIO 6 (pull-up)
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

### **Test 4 : Buzzer**

```python
# Test buzzer
GPIO.setup(22, GPIO.OUT)
GPIO.output(22, GPIO.HIGH)  # Activer
time.sleep(0.5)
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
Buzzer: ~30mA @ 3.3V
LEDs: ~40mA @ 3.3V

TOTAL: ~1.8A @ 5V (pic)
```

### **Recommandations**

- **Alimentation 5V/3A** minimum
- **Alimentation 12V/1A** pour LED strip
- **Protection contre les surtensions**
- **Ventilation** du boîtier
