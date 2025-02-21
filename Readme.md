# Gestion Automatisée des Mantes avec Raspberry Pi Zero

## Description

Ce projet automatise la gestion de l'environnement des mantes en utilisant un Raspberry Pi Zero et une application Python.  
Le système contrôle :

- **Température** : Activation d’un relais pour maintenir une température optimale.
- **Lumière** : Synchronisation avec les heures de lever/coucher (UTC).
- **Humidité** : Activation d’un pulvérisateur pour maintenir un taux d'humidité défini.
- **Distribution alimentaire** : Ouverture d’une trappe pour libérer des mouches à intervalles réguliers.

## Matériel Requis

### Électronique

- **Raspberry Pi Zero** (ou équivalent)
- **Capteur de température et d'humidité (DHT22)**
- **Relais** pour le chauffage et la pulvérisation
- **Moteur Servo** pour la trappe
- **LED ou bande LED** pour l'éclairage
- **Pompe connectée** pour faire fonctionner la buse de pulvérisation
- **Capteur ou barrière** pour compter les mouches (optionnel)

### Non Électronique

- **Câblage adapté**
- **Alimentation 5V/3.3V** avec régulateurs
- **Raccords et boîtiers**

## Installation

1. Cloner le dépôt sur votre Raspberry Pi Zero.
2. Installez [Python 3.x](https://www.python.org/downloads/) et créez un environnement virtuel :

   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
