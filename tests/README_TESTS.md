# 🧪 Guide des tests Alimante

Ce guide explique comment utiliser la suite de tests pour valider votre système Alimante.

## 📋 Tests disponibles

### 1. **Tests du système d'événements** (`test_event_system.py`)

- ✅ Vérifie que tous les événements sont émis et reçus
- ✅ Teste les événements critiques (emergency_stop, safety_alert)
- ✅ Valide les événements de données et de contrôle
- ✅ Mesure les performances du bus d'événements

### 2. **Tests de sécurité** (`test_safety_system.py`)

- 🛡️ Vérifie les limites de température, humidité, qualité d'air
- 🚨 Teste le déclenchement d'arrêts d'urgence
- ⚠️ Valide le système d'alertes
- 🔄 Teste la reprise après arrêt d'urgence

### 3. **Tests d'intégration** (`test_system_integration.py`)

- 🔗 Teste le fonctionnement global du système
- 📊 Valide le flux de données des capteurs
- 🎛️ Vérifie le système de contrôle
- 💪 Teste la stabilité sous charge

### 4. **Tests de performance** (`test_performance.py`)

- ⚡ Mesure les performances du bus d'événements
- 💾 Vérifie l'utilisation mémoire
- 🔄 Teste les événements concurrents
- 🖥️ Valide la réactivité de l'interface

## 🚀 Comment exécuter les tests

### **Option 1 : Tous les tests d'un coup**

```bash
cd tests
python run_all_tests.py
```

### **Option 2 : Tests individuels**

```bash
cd tests

# Tests d'événements
python test_event_system.py

# Tests de sécurité
python test_safety_system.py

# Tests d'intégration
python test_system_integration.py

# Tests de performance
python test_performance.py
```

### **Option 3 : Tests spécifiques**

```bash
# Seulement les tests critiques
python test_event_system.py
python test_safety_system.py
```

## 📊 Interprétation des résultats

### **✅ Succès**

```
🎉 Tous les tests sont passés avec succès !
✅ Votre système Alimante est prêt pour la production !
```

### **❌ Échec**

```
💥 Certains tests ont échoué !
🔧 Veuillez corriger les problèmes avant de continuer.
```

## 🔧 Résolution des problèmes courants

### **Problème : "Module not found"**

```bash
# Assurez-vous d'être dans le bon répertoire
cd /chemin/vers/alimante
python tests/test_event_system.py
```

### **Problème : "Event not received"**

- Vérifiez que les gestionnaires d'événements sont bien enregistrés
- Vérifiez que le bus d'événements est correctement initialisé

### **Problème : "UI not started"**

- Vérifiez que les dépendances UI sont installées
- Vérifiez la configuration de l'interface

### **Problème : "Memory usage too high"**

- Vérifiez qu'il n'y a pas de fuites mémoire
- Optimisez le traitement des événements

## 📈 Métriques de performance attendues

### **Bus d'événements**

- **1000 événements/seconde** minimum
- **Latence < 1ms** par événement
- **Mémoire stable** (< 50 MB d'augmentation)

### **Système de sécurité**

- **Vérifications < 10ms** par cycle
- **Alertes < 100ms** de latence
- **Arrêt d'urgence < 500ms** de réaction

### **Interface utilisateur**

- **Mise à jour < 100ms** de latence
- **Réactivité < 50ms** aux interactions
- **Stabilité** sous charge

## 🎯 Tests recommandés par phase

### **Phase 1 : Développement**

```bash
python test_event_system.py
```

### **Phase 2 : Intégration**

```bash
python test_system_integration.py
```

### **Phase 3 : Sécurité**

```bash
python test_safety_system.py
```

### **Phase 4 : Production**

```bash
python run_all_tests.py
```

## 🔍 Debugging des tests

### **Activer les logs détaillés**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Vérifier les événements manquants**

```python
# Dans le test, ajouter :
print(f"Événements reçus: {len(self.received_events)}")
for event in self.received_events:
    print(f"  - {event['event']}: {event['data']}")
```

### **Tester un événement spécifique**

```python
# Émettre un événement de test
event_bus.emit('test_event', {'data': 'test'})

# Vérifier qu'il est reçu
assert 'test_event' in [e['event'] for e in received_events]
```

## 📝 Ajout de nouveaux tests

### **Structure d'un test**

```python
def test_nouveau_fonctionnalite(self):
    """Test de la nouvelle fonctionnalité"""
    print("\n🔧 Test de la nouvelle fonctionnalité...")

    try:
        # Préparer le test
        test_data = {'param': 'value'}

        # Exécuter l'action
        result = self.service.nouvelle_fonctionnalite(test_data)

        # Vérifier le résultat
        assert result is not None, "Résultat attendu"

        print("✅ Test réussi")
        return True

    except Exception as e:
        print(f"❌ Test échoué: {e}")
        return False
```

### **Ajouter le test à la suite**

```python
def run_all_tests(self):
    tests = [
        self.test_existing,
        self.test_nouveau_fonctionnalite,  # Nouveau test
        # ... autres tests
    ]
```

## 🎉 Conclusion

Cette suite de tests vous permet de valider que votre système Alimante fonctionne correctement avant la mise en production. Exécutez les tests régulièrement pendant le développement et systématiquement avant chaque déploiement.

**Bon testage !** 🚀
