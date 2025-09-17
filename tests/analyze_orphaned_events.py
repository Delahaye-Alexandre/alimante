#!/usr/bin/env python3
"""
Analyseur d'événements orphelins Alimante
Identifie précisément quels événements n'ont pas de gestionnaires
"""

import sys
import os
import re
from pathlib import Path

def find_emitted_events():
    """Trouve tous les événements émis dans le code"""
    emitted_events = set()
    
    # Chercher tous les event_bus.emit() dans src/
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Chercher les patterns event_bus.emit('event_name', ...)
                    pattern = r"event_bus\.emit\(['\"]([^'\"]+)['\"]"
                    matches = re.findall(pattern, content)
                    
                    for match in matches:
                        emitted_events.add(match)
                        
                except Exception as e:
                    print(f"Erreur lecture {file_path}: {e}")
    
    return emitted_events

def find_subscribed_events():
    """Trouve tous les événements auxquels on s'abonne"""
    subscribed_events = set()
    
    # Chercher tous les event_bus.on() dans src/
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Chercher les patterns event_bus.on('event_name', ...)
                    pattern = r"event_bus\.on\(['\"]([^'\"]+)['\"]"
                    matches = re.findall(pattern, content)
                    
                    for match in matches:
                        subscribed_events.add(match)
                        
                except Exception as e:
                    print(f"Erreur lecture {file_path}: {e}")
    
    return subscribed_events

def analyze_events():
    """Analyse les événements orphelins"""
    print("🔍 Analyse des événements orphelins Alimante")
    print("=" * 60)
    
    # Trouver tous les événements
    emitted = find_emitted_events()
    subscribed = find_subscribed_events()
    
    print(f"📊 Événements émis: {len(emitted)}")
    print(f"📊 Événements avec gestionnaires: {len(subscribed)}")
    
    # Trouver les orphelins
    orphaned = emitted - subscribed
    connected = emitted & subscribed
    
    print(f"📊 Événements connectés: {len(connected)}")
    print(f"📊 Événements orphelins: {len(orphaned)}")
    
    if orphaned:
        print(f"\n❌ Événements orphelins ({len(orphaned)}):")
        for event in sorted(orphaned):
            print(f"   - {event}")
    else:
        print("\n✅ Aucun événement orphelin !")
    
    if connected:
        print(f"\n✅ Événements connectés ({len(connected)}):")
        for event in sorted(connected):
            print(f"   - {event}")
    
    # Trouver les gestionnaires sans événements correspondants
    unused_handlers = subscribed - emitted
    if unused_handlers:
        print(f"\n⚠️ Gestionnaires sans événements ({len(unused_handlers)}):")
        for event in sorted(unused_handlers):
            print(f"   - {event}")
    
    # Calculer le pourcentage de couverture
    if emitted:
        coverage = (len(connected) / len(emitted)) * 100
        print(f"\n📈 Couverture des événements: {coverage:.1f}%")
    
    return orphaned, connected, unused_handlers

def main():
    """Fonction principale"""
    # Changer vers le répertoire du projet
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.chdir('..')
    
    orphaned, connected, unused = analyze_events()
    
    if orphaned:
        print(f"\n🎯 Le dernier événement orphelin est: {sorted(orphaned)[0]}")
        return 1
    else:
        print("\n🎉 Tous les événements sont connectés !")
        return 0

if __name__ == "__main__":
    sys.exit(main())
