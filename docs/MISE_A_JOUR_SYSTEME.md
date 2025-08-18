# 📋 Mise à jour système Alimante - Résumé des modifications

## 🎯 **Modifications effectuées**

### **1. 🔧 Architecture clarifiée**

- ✅ **Buck converters** pour distribution alimentation (isolation Raspberry Pi)
- ✅ **4 ventilateurs terrarium** (circulation + brume)
- ✅ **Switch principal** en sortie alimentation
- ✅ **Aucun composant alimenté par le Pi** (sécurité maximale)

### **2. 🕹️ Interface utilisateur améliorée**

- ✅ **Encodeur rotatif** avec clic (remplace 4 boutons)
  - GPIO 5 : CLK (rotation)
  - GPIO 6 : DT (direction)
  - GPIO 13 : SW (validation)
- ✅ **Navigation intuitive** : rotation pour parcourir, clic pour valider
- ✅ **Appui long** : retour menu principal

### **3. 📡 Nouveaux capteurs ajoutés**

#### **💧 Capteur niveau d'eau HC-SR04P**

- **Pins** : 20 (trigger) / 21 (echo)
- **Fonction** : Surveillance réservoir brumisateur
- **Seuils** : Critique (5%), Bas (20%), OK, Plein (80%+)
- **API** : `/api/water-level/*`

#### **🌡️ Capteur température radiateur DS18B20**

- **Pin** : 26 (OneWire)
- **Fonction** : Sécurité surchauffe radiateur
- **Seuils** : Alerte (70°C), Critique (80°C)
- **API** : `/api/radiator-temp/*`

### **4. 🌫️ Transducteur ANGEEK optimisé**

- ✅ **Contrôle PWM précis** (0-100% intensité)
- ✅ **Consommation réduite** : 50mA @ 5V (vs 100mA @ 12V)
- ✅ **Ajustement temps réel** de l'intensité brume
- ✅ **Modes prédéfinis** : light, medium, heavy, continuous

### **5. 📸 Caméra CSI intégrée**

- ✅ **Support Picamera2** + fallback OpenCV
- ✅ **API complète** : capture, snapshot, streaming
- ✅ **Résolution** : 1920x1080@30fps
- ✅ **Interface web** pour webapp

## 🔌 **Configuration GPIO finale**

| GPIO | Composant           | Type    | Description                 |
| ---- | ------------------- | ------- | --------------------------- |
| 4    | DHT22               | Digital | Température/humidité        |
| 5    | Encodeur CLK        | Input   | Navigation menu (rotation)  |
| 6    | Encodeur DT         | Input   | Navigation menu (direction) |
| 12   | Servomoteur         | PWM     | Trappe alimentation         |
| 13   | Encodeur SW         | Input   | Validation menu (bouton)    |
| 18   | Relais chauffage    | Digital | Contrôle radiateur          |
| 19   | LED alimentation    | Digital | Indicateur système          |
| 20   | HC-SR04P Trigger    | Digital | Niveau d'eau (trigger)      |
| 21   | HC-SR04P Echo       | Input   | Niveau d'eau (echo)         |
| 22   | Transducteur ANGEEK | PWM     | Brumisateur (intensité)     |
| 23   | Relais humidité     | Digital | Contrôle ultrasonic mist    |
| 24   | Relais LED          | Digital | Bandeau LED 12V             |
| 25   | Relais ventilateurs | Digital | 4 ventilateurs terrarium    |
| 26   | DS18B20             | OneWire | Température radiateur       |
| 22   | MQ2                 | I2C     | Qualité air (via ADS1115)   |
| CSI  | Caméra              | CSI-2   | Surveillance terrarium      |

## 🛡️ **Sécurités implémentées**

### **Niveau d'eau**

- ⚠️ **Alerte bas niveau** (20%)
- 🚨 **Arrêt critique** (5%) - Désactivation brumisateur
- 📈 **Analyse tendance** (stable/montée/descente)

### **Température radiateur**

- ⚠️ **Alerte surchauffe** (70°C)
- 🚨 **Arrêt d'urgence** (80°C) - Coupure radiateur
- 🔄 **Vérification continue** avec historique

### **Transducteur ANGEEK**

- ⏱️ **Temps max continu** : 5 minutes
- 😴 **Pause obligatoire** : 1 minute entre activations
- 🔄 **Contrôle PWM** pour intensité précise

## 🌐 **API endpoints ajoutés**

### **Niveau d'eau**

- `GET /api/water-level/status` - Statut capteur
- `GET /api/water-level/read` - Lecture niveau
- `GET /api/water-level/check-availability` - Vérif disponibilité

### **Température radiateur**

- `GET /api/radiator-temp/status` - Statut capteur
- `GET /api/radiator-temp/read` - Lecture température
- `GET /api/radiator-temp/safety-check` - Vérif sécurité
- `GET /api/radiator-temp/is-safe` - État sécuritaire

### **Caméra CSI**

- `GET /api/camera/status` - Statut caméra
- `GET /api/camera/capture` - Capture image
- `POST /api/camera/snapshot` - Snapshot sauvegardé
- `POST /api/camera/streaming/start` - Démarrer streaming
- `POST /api/camera/streaming/stop` - Arrêter streaming

## 📦 **Nouvelles dépendances**

```bash
# Dans requirements.txt
picamera2>=0.3.0           # Caméra CSI
opencv-python>=4.8.0       # Fallback caméra
w1thermsensor>=2.0.0       # Capteur OneWire DS18B20
```

## 🧪 **Scripts de test ajoutés**

- ✅ `test_camera_csi.py` - Test complet caméra
- ✅ `test_nouveaux_capteurs.py` - Test niveau d'eau + temp radiateur
- ✅ `test_ultrasonic_mist.py` - Test brumisateur ANGEEK (existant)

## ⚡ **Consommation électrique mise à jour**

```
Raspberry Pi Zero 2W: ~500mA @ 5V
Capteurs: ~171mA @ 5V (DHT22 + MQ2)
Capteurs 3.3V: ~216mA @ 3.3V (HC-SR04P + DS18B20 + Caméra)
Relais: ~120mA @ 5V
Servomoteur: ~250mA @ 5V (pics)
Ventilateurs: ~800mA @ 5V
Transducteur ANGEEK: ~50mA @ 5V
LEDs: ~40mA @ 3.3V

TOTAL: ~1.86A @ 5V + 0.256A @ 3.3V + 0.1A @ 12V (pic)
```

**Recommandations alimentation :**

- **5V/3A** minimum (marge de sécurité)
- **12V/1A** pour bandeau LED
- **3.3V fourni par Pi** (via buck converter si nécessaire)

## 🔄 **Prochaines étapes (selon PLANIFICATION_PROJET.md)**

### **En attente de vos spécifications :**

1. **Puissance radiateur** → Dimensionnement MOSFET
2. **Puissance bandeau LED** → Dimensionnement MOSFET
3. **Type d'espèce** → Calibrage paramètres
4. **Dimensions terrarium** → Optimisation ventilation
5. **Capacité réservoir** → Calibrage capteur niveau

### **Tests à effectuer :**

1. **Câblage physique** complet
2. **Calibrage capteurs** individuels
3. **Intégration système** complète
4. **Tests endurance** 24h+

## 🎯 **Statut actuel**

✅ **Architecture logicielle** : Complète
✅ **Contrôleurs** : Tous implémentés
✅ **API** : Endpoints fonctionnels
✅ **Interface utilisateur** : Encodeur rotatif
✅ **Sécurités** : Niveau eau + temp radiateur
✅ **Documentation** : À jour

🔄 **En attente** : Spécifications matériel (voir PLANIFICATION_PROJET.md)

---

_Système prêt pour tests physiques dès réception des spécifications techniques !_ 🚀
