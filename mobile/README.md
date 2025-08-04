# Application Mobile Alimante

## Vue d'ensemble

Application mobile pour contrôler et monitorer le système Alimante depuis votre téléphone.

## Technologies recommandées

### Option 1 : React Native (Recommandé)

- **Avantages** : Cross-platform (iOS + Android), grande communauté
- **API** : REST + WebSocket pour temps réel
- **Notifications** : Push notifications natives

### Option 2 : Flutter

- **Avantages** : Performance native, UI fluide
- **API** : REST + WebSocket
- **Notifications** : Firebase Cloud Messaging

## Fonctionnalités principales

### 📊 Dashboard

- Température en temps réel
- Humidité actuelle
- Statut des systèmes
- Graphiques historiques

### 🎛️ Contrôles

- Activation/désactivation manuelle
- Déclenchement alimentation
- Ajustement des paramètres
- Mode maintenance

### 🔔 Notifications

- Alertes de température
- Rappels d'alimentation
- Erreurs système
- Notifications push

### 📱 Interface

- Design moderne et intuitif
- Mode sombre/clair
- Responsive design
- Accessibilité

## Structure du projet

```
mobile/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── Controls.tsx
│   │   └── Settings.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── notifications.ts
│   ├── screens/
│   │   ├── HomeScreen.tsx
│   │   ├── ControlScreen.tsx
│   │   └── SettingsScreen.tsx
│   └── utils/
│       ├── constants.ts
│       └── helpers.ts
├── assets/
│   ├── icons/
│   └── images/
└── package.json
```

## API Endpoints utilisés

### REST API

- `GET /api/status` - Statut système
- `GET /api/metrics` - Métriques capteurs
- `POST /api/control` - Contrôle systèmes
- `POST /api/feeding/trigger` - Alimentation manuelle

### WebSocket

- `ws://raspberry-pi:8000/ws` - Données temps réel

## Installation et développement

```bash
# React Native
npx react-native init AlimanteApp
cd AlimanteApp

# Installation des dépendances
npm install axios websocket react-native-charts-wrapper
npm install @react-navigation/native @react-navigation/stack

# Démarrage
npx react-native run-android
npx react-native run-ios
```

## Configuration

1. **Adresse du Raspberry Pi** : Modifier dans `src/services/api.ts`
2. **Notifications** : Configurer Firebase/APNS
3. **Thème** : Personnaliser dans `src/utils/constants.ts`

## Déploiement

### Android

```bash
cd android
./gradlew assembleRelease
```

### iOS

```bash
cd ios
xcodebuild -workspace AlimanteApp.xcworkspace -scheme AlimanteApp archive
```
