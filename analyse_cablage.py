#!/usr/bin/env python3
"""
Analyse de câblage pour Alimante
Vérifie la cohérence entre les contrôleurs et la configuration GPIO
"""

import json
import sys
from typing import Dict, Any, List, Set

def load_gpio_config():
    """Charge la configuration GPIO"""
    try:
        with open('config/gpio_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement GPIO config: {e}")
        return None

def analyze_controllers():
    """Analyse les contrôleurs disponibles"""
    print("🔍 Analyse des contrôleurs...")
    
    # Contrôleurs définis dans l'application
    app_controllers = {
        'temperature': {
            'sensor': 'DHT22',
            'actuator': 'heating_relay',
            'pins_needed': ['temp_humidity', 'heating_relay']
        },
        'humidity': {
            'sensor': 'DHT22', 
            'actuator': 'humidity_relay',
            'pins_needed': ['temp_humidity', 'humidity_relay']
        },
        'light': {
            'sensor': 'LDR',
            'actuator': 'light_relay',
            'pins_needed': ['light', 'light_relay']
        },
        'feeding': {
            'actuator': 'feeding_servo',
            'pins_needed': ['feeding_servo']
        },
        'fan': {
            'actuator': 'fan_relay',
            'pins_needed': ['fan_relay']
        },
        'buzzer': {
            'actuator': 'buzzer',
            'pins_needed': ['buzzer']
        },
        'air_quality': {
            'sensor': 'MQ135',
            'pins_needed': ['air_quality']
        },
        'lcd_menu': {
            'display': 'ST7735',
            'pins_needed': ['lcd_display', 'menu_up_button', 'menu_down_button', 'menu_select_button', 'menu_back_button']
        }
    }
    
    return app_controllers

def analyze_gpio_pins(gpio_config):
    """Analyse les pins GPIO configurés"""
    print("🔍 Analyse des pins GPIO...")
    
    if not gpio_config or 'pins' not in gpio_config:
        print("❌ Configuration GPIO invalide")
        return None
    
    pins = gpio_config['pins']
    all_pins = {}
    
    # Collecter tous les pins
    for category, components in pins.items():
        for name, config in components.items():
            all_pins[name] = {
                'pin': config.get('pin'),
                'type': config.get('type'),
                'voltage': config.get('voltage'),
                'category': category
            }
    
    return all_pins

def check_controller_gpio_mapping(app_controllers, gpio_pins):
    """Vérifie la correspondance entre contrôleurs et pins GPIO"""
    print("🔍 Vérification correspondance contrôleurs ↔ GPIO...")
    
    issues = []
    missing_pins = []
    unused_pins = []
    
    # Vérifier que chaque contrôleur a ses pins nécessaires
    for controller_name, controller_info in app_controllers.items():
        print(f"\n🎛️ Contrôleur: {controller_name}")
        
        for pin_name in controller_info.get('pins_needed', []):
            if pin_name in gpio_pins:
                pin_info = gpio_pins[pin_name]
                print(f"   ✅ {pin_name}: GPIO {pin_info['pin']} ({pin_info['type']})")
            else:
                print(f"   ❌ {pin_name}: MANQUANT")
                missing_pins.append(f"{controller_name}.{pin_name}")
                issues.append(f"Pin manquant pour {controller_name}: {pin_name}")
    
    # Vérifier les pins non utilisés
    used_pins = set()
    for controller_info in app_controllers.values():
        for pin_name in controller_info.get('pins_needed', []):
            used_pins.add(pin_name)
    
    for pin_name, pin_info in gpio_pins.items():
        if pin_name not in used_pins:
            unused_pins.append(pin_name)
            print(f"   ⚠️ {pin_name}: Non utilisé par les contrôleurs")
    
    return issues, missing_pins, unused_pins

def check_voltage_consistency(gpio_pins):
    """Vérifie la cohérence des tensions"""
    print("\n🔍 Vérification cohérence des tensions...")
    
    voltage_issues = []
    
    # Vérifier les composants 3.3V
    components_3v3 = []
    components_5v = []
    
    for pin_name, pin_info in gpio_pins.items():
        voltage = pin_info.get('voltage', 'N/A')
        if voltage == '3.3V':
            components_3v3.append(pin_name)
        elif voltage == '5V':
            components_5v.append(pin_name)
    
    print(f"   📊 Composants 3.3V: {len(components_3v3)}")
    for comp in components_3v3:
        print(f"      - {comp}")
    
    print(f"   📊 Composants 5V: {len(components_5v)}")
    for comp in components_5v:
        print(f"      - {comp}")
    
    return voltage_issues

def check_power_requirements(gpio_config):
    """Vérifie les besoins en alimentation"""
    print("\n🔍 Analyse des besoins en alimentation...")
    
    if 'power_supply' not in gpio_config:
        print("   ⚠️ Section power_supply manquante")
        return
    
    power_config = gpio_config['power_supply']
    
    print("   📊 Configuration alimentation:")
    for key, value in power_config.items():
        print(f"      - {key}: {value}")
    
    # Vérifier les tensions spéciales
    if 'led_strip_voltage' in power_config and power_config['led_strip_voltage'] == '12V':
        print("   ✅ Bandeau LED 12V configuré")
    
    if 'sensors_voltage' in power_config and power_config['sensors_voltage'] == '3.3V':
        print("   ✅ Capteurs 3.3V configurés")

def generate_wiring_summary(gpio_pins, app_controllers):
    """Génère un résumé du câblage"""
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DU CÂBLAGE")
    print("=" * 60)
    
    # Par catégorie
    categories = {
        'sensors': [],
        'actuators': [],
        'inputs': [],
        'status': []
    }
    
    for pin_name, pin_info in gpio_pins.items():
        category = pin_info.get('category', 'unknown')
        if category in categories:
            categories[category].append({
                'name': pin_name,
                'pin': pin_info['pin'],
                'type': pin_info['type'],
                'voltage': pin_info['voltage']
            })
    
    for category, components in categories.items():
        if components:
            print(f"\n🔧 {category.upper()}:")
            for comp in components:
                status = "✅" if any(comp['name'] in c.get('pins_needed', []) for c in app_controllers.values()) else "⚠️"
                print(f"   {status} {comp['name']}: GPIO {comp['pin']} ({comp['type']}) - {comp['voltage']}")

def main():
    """Programme principal"""
    print("🧪 Analyse de Câblage Alimante")
    print("=" * 50)
    
    # Charger la configuration
    gpio_config = load_gpio_config()
    if not gpio_config:
        return False
    
    # Analyser les contrôleurs
    app_controllers = analyze_controllers()
    
    # Analyser les pins GPIO
    gpio_pins = analyze_gpio_pins(gpio_config)
    if not gpio_pins:
        return False
    
    # Vérifications
    issues, missing_pins, unused_pins = check_controller_gpio_mapping(app_controllers, gpio_pins)
    check_voltage_consistency(gpio_pins)
    check_power_requirements(gpio_config)
    
    # Résumé
    generate_wiring_summary(gpio_pins, app_controllers)
    
    # Rapport final
    print("\n" + "=" * 60)
    print("📊 RAPPORT FINAL")
    print("=" * 60)
    
    if issues:
        print(f"❌ Problèmes détectés: {len(issues)}")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ Aucun problème de câblage détecté")
    
    if missing_pins:
        print(f"⚠️ Pins manquants: {len(missing_pins)}")
        for pin in missing_pins:
            print(f"   - {pin}")
    
    if unused_pins:
        print(f"ℹ️ Pins non utilisés: {len(unused_pins)}")
        for pin in unused_pins:
            print(f"   - {pin}")
    
    # Recommandations
    print("\n💡 Recommandations:")
    if missing_pins:
        print("   - Ajouter les pins manquants dans la configuration")
    if unused_pins:
        print("   - Vérifier si les pins non utilisés sont nécessaires")
    if not issues and not missing_pins:
        print("   - Le câblage semble correct !")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
