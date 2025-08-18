# Intégration du PCF8591 - Remplacement de l'ADS1115

## 📋 **Vue d'ensemble**

Ce document décrit la migration du convertisseur analogique-numérique ADS1115 vers le PCF8591 dans le projet Alimante.

## 🔄 **Pourquoi cette migration ?**

### **Avantages du PCF8591 :**

- ✅ **Plus simple** : Interface I2C basique
- ✅ **Moins cher** : Coût réduit de ~30-50%
- ✅ **Suffisant** : 8-bit de résolution pour le capteur MQ2
- ✅ **Compatible** : Même adresse I2C (0x48)
- ✅ **Moins de dépendances** : Pas besoin de bibliothèques Adafruit

### **Limitations :**

- ⚠️ **Résolution réduite** : 8-bit (0-255) vs 16-bit (0-65535)
- ⚠️ **Précision** : Moins précise mais suffisante pour MQ2

## 🔧 **Spécifications techniques**

### **PCF8591 :**

- **Résolution** : 8-bit (256 valeurs)
- **Canaux** : 4 entrées analogiques (AIN0-AIN3)
- **Sortie** : 1 sortie analogique (AOUT)
- **Interface** : I2C
- **Adresse** : 0x48 (configurable)
- **Alimentation** : 2.5V - 6V
- **Consommation** : ~10mA @ 3.3V

### **Comparaison avec ADS1115 :**

| Caractéristique | PCF8591    | ADS1115    |
| --------------- | ---------- | ---------- |
| Résolution      | 8-bit      | 16-bit     |
| Canaux          | 4          | 4          |
| Interface       | I2C simple | I2C avancé |
| Coût            | ~2-3€      | ~8-12€     |
| Complexité      | Faible     | Élevée     |
| Précision       | Suffisante | Excellente |

## 🔌 **Câblage**

### **Connexions :**

```
PCF8591 → Raspberry Pi
├── VCC → 3.3V
├── GND → GND
├── SDA → GPIO 22 (I2C SDA)
├── SCL → GPIO 3 (I2C SCL)
└── A0, A1, A2 → GND (adresse 0x48)

MQ2 → PCF8591
├── VCC → 5.1V (alimentation séparée)
├── GND → GND (commun)
└── SIGNAL → AIN0 (canal 0)
```

### **Adressage I2C :**

- **A0, A1, A2 = GND** → Adresse 0x48 (défaut)
- **A0, A1, A2 = VCC** → Adresse 0x4F
- **Configuration actuelle** : 0x48

## 💻 **Code d'intégration**

### **Lecture analogique :**

```python
from smbus2 import SMBus

def read_pcf8591(channel=0, address=0x48):
    """Lit une valeur analogique du PCF8591"""
    with SMBus(1) as bus:  # Bus I2C 1 sur Raspberry Pi
        # Configuration: Enable + Canal + Auto-increment
        config_byte = 0x40 | (channel << 4)

        # Envoyer configuration
        bus.write_byte(address, config_byte)

        # Lire 2 bytes (ancienne + nouvelle valeur)
        data = bus.read_i2c_block_data(address, config_byte, 2)

        # Nouvelle valeur dans le 2ème byte
        raw_value = data[1]  # 0-255

        # Convertir en tension (0-3.3V)
        voltage = (raw_value / 255.0) * 3.3

        return raw_value, voltage
```

### **Configuration dans le contrôleur :**

```python
# Dans AirQualityController._read_raw_sensor()
from smbus2 import SMBus

with SMBus(1) as bus:
    address = int(self.i2c_address, 16)
    config_byte = 0x40 | (self.adc_channel << 4)

    bus.write_byte(address, config_byte)
    data = bus.read_i2c_block_data(address, config_byte, 2)

    raw_value = data[1]
    voltage = (raw_value / 255.0) * 3.3
    ppm = (voltage / 3.3) * 1000  # Conversion MQ2
```

## 📊 **Calibration et conversion**

### **Conversion MQ2 :**

- **Tension 0V** → 0 ppm (air pur)
- **Tension 3.3V** → 1000 ppm (concentration élevée)
- **Formule** : `ppm = (voltage / 3.3) * 1000`

### **Seuils de qualité :**

- **Excellent** : 0-50 ppm
- **Bon** : 50-100 ppm
- **Modéré** : 100-150 ppm
- **Mauvais** : 150-200 ppm
- **Malsain** : 200-300 ppm
- **Très malsain** : 300+ ppm

## 🧪 **Tests et validation**

### **Test de connectivité :**

```bash
# Détecter le PCF8591
i2cdetect -y 1

# Résultat attendu :
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --
# 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

### **Test de lecture :**

```python
# Test simple
raw, voltage = read_pcf8591(channel=0)
print(f"Valeur brute: {raw}, Tension: {voltage:.2f}V")
```

## 📦 **Dépendances**

### **Remplacement dans requirements.txt :**

```diff
- adafruit-circuitpython-ads1x15>=1.3.8
+ # PCF8591 I2C ADC/DAC (remplace ADS1115)
+ smbus2>=0.4.3
```

### **Installation :**

```bash
pip install smbus2
# ou
pip install -r requirements.txt
```

## 🔍 **Dépannage**

### **Problèmes courants :**

1. **Erreur "No module named 'smbus2'"**

   ```bash
   pip install smbus2
   ```

2. **Erreur "Permission denied"**

   ```bash
   sudo usermod -a -G i2c $USER
   # Redémarrer la session
   ```

3. **PCF8591 non détecté**

   - Vérifier le câblage I2C
   - Vérifier l'alimentation 3.3V
   - Vérifier les résistances pull-up

4. **Lectures incorrectes**
   - Vérifier la configuration du canal
   - Vérifier l'adresse I2C
   - Vérifier la calibration

## 📈 **Performance**

### **Comparaison des performances :**

| Métrique         | PCF8591    | ADS1115     |
| ---------------- | ---------- | ----------- |
| Temps de lecture | ~1ms       | ~2ms        |
| Précision        | ±1 LSB     | ±0.5 LSB    |
| Bruit            | Plus élevé | Plus faible |
| Consommation     | ~10mA      | ~15mA       |

### **Impact sur l'application :**

- **Qualité de l'air** : Détection suffisante
- **Ventilation** : Contrôle identique
- **Calibration** : Processus identique
- **Fiabilité** : Excellente

## 🎯 **Conclusion**

La migration vers le PCF8591 est **complète et fonctionnelle**. Le composant offre :

- ✅ **Fonctionnalité identique** pour le capteur MQ2
- ✅ **Réduction des coûts** significative
- ✅ **Simplification** de l'implémentation
- ✅ **Compatibilité** avec l'existant

Le PCF8591 est **parfaitement adapté** aux besoins du projet Alimante.
