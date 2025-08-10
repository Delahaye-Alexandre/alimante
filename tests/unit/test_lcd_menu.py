#!/usr/bin/env python3
"""
Test du contrôleur LCD menu
"""

import sys
import os
import time
sys.path.insert(0, '.')

from src.controllers.lcd_menu_controller import LCDMenuController
from src.utils.gpio_manager import GPIOManager

def test_lcd_menu_controller():
    """Test le contrôleur LCD menu"""
    print("🧪 Test du contrôleur LCD menu")
    print("=" * 50)
    
    try:
        # Configuration de test
        lcd_config = {
            "lcd_config": {
                "type": "ST7735",
                "resolution": "128x160",
                "spi_pins": {
                    "dc": 8,
                    "cs": 7,
                    "rst": 9
                },
                "voltage": "3.3V",
                "current": "150mA",
                "backlight_pin": 10
            },
            "menu_config": {
                "buttons": {
                    "up": 5,
                    "down": 6,
                    "select": 13,
                    "back": 19
                },
                "debounce_time": 200,
                "long_press_time": 1000
            }
        }
        
        # Initialiser GPIO (simulation)
        gpio_manager = GPIOManager()
        
        # Créer le contrôleur
        lcd_controller = LCDMenuController(gpio_manager, lcd_config)
        print("✅ Contrôleur LCD menu créé")
        
        # Test 1: Statut du contrôleur
        print("\n📊 Test du statut...")
        status = lcd_controller.get_status()
        print(f"   Type d'écran: {status['display_type']}")
        print(f"   Résolution: {status['resolution']}")
        print(f"   Profondeur menu: {status['current_menu_depth']}")
        print(f"   Index sélectionné: {status['selected_index']}")
        print(f"   Thread actif: {status['running']}")
        
        # Test 2: Vérification du statut
        print("\n🔍 Test de vérification du statut...")
        status_ok = lcd_controller.check_status()
        print(f"   Statut OK: {'✅ Oui' if status_ok else '❌ Non'}")
        
        # Test 3: Simulation de navigation
        print("\n🎮 Test de navigation...")
        print("   Navigation vers le bas...")
        lcd_controller._navigate_down()
        print(f"   Nouvel index: {lcd_controller.selected_index}")
        
        print("   Navigation vers le haut...")
        lcd_controller._navigate_up()
        print(f"   Nouvel index: {lcd_controller.selected_index}")
        
        # Test 4: Simulation de sélection
        print("\n🎯 Test de sélection...")
        if len(lcd_controller.current_menu) > 0:
            item = lcd_controller.current_menu[lcd_controller.selected_index]
            print(f"   Élément sélectionné: {item.name}")
            print(f"   Type: {item.type.value}")
        
        # Test 5: Test des boutons (simulation)
        print("\n🔘 Test des boutons...")
        button_pins = [5, 6, 13, 19]
        for pin in button_pins:
            try:
                state = gpio_manager.read_pin(pin)
                print(f"   Bouton GPIO {pin}: {'HIGH' if state else 'LOW'}")
            except Exception as e:
                print(f"   Bouton GPIO {pin}: Erreur - {e}")
        
        # Test 6: Nettoyage
        print("\n🧹 Test de nettoyage...")
        lcd_controller.cleanup()
        print("   ✅ Nettoyage terminé")
        
        print("\n🎉 Tous les tests sont passés !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_menu_navigation():
    """Test la navigation dans le menu"""
    print("\n🎮 Test de navigation dans le menu")
    print("=" * 50)
    
    try:
        lcd_config = {
            "lcd_config": {
                "type": "ST7735",
                "resolution": "128x160",
                "spi_pins": {"dc": 8, "cs": 7, "rst": 9},
                "backlight_pin": 10
            },
            "menu_config": {
                "buttons": {"up": 5, "down": 6, "select": 13, "back": 19},
                "debounce_time": 200,
                "long_press_time": 1000
            }
        }
        
        gpio_manager = GPIOManager()
        lcd_controller = LCDMenuController(gpio_manager, lcd_config)
        
        # Afficher le menu principal
        print("📋 Menu principal:")
        for i, item in enumerate(lcd_controller.current_menu):
            marker = "▶" if i == lcd_controller.selected_index else " "
            print(f"   {marker} {item.name}")
        
        # Navigation vers le bas
        print("\n⬇️ Navigation vers le bas...")
        lcd_controller._navigate_down()
        for i, item in enumerate(lcd_controller.current_menu):
            marker = "▶" if i == lcd_controller.selected_index else " "
            print(f"   {marker} {item.name}")
        
        # Navigation vers le haut
        print("\n⬆️ Navigation vers le haut...")
        lcd_controller._navigate_up()
        for i, item in enumerate(lcd_controller.current_menu):
            marker = "▶" if i == lcd_controller.selected_index else " "
            print(f"   {marker} {item.name}")
        
        # Test d'entrée dans un sous-menu
        print("\n📂 Entrée dans un sous-menu...")
        if len(lcd_controller.current_menu) > 0:
            first_item = lcd_controller.current_menu[0]
            if first_item.submenu:
                print(f"   Entrée dans: {first_item.name}")
                lcd_controller._enter_submenu(first_item)
                print(f"   Profondeur menu: {len(lcd_controller.menu_stack)}")
                print(f"   Éléments dans le sous-menu: {len(lcd_controller.current_menu)}")
        
        lcd_controller.cleanup()
        print("   ✅ Test de navigation terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Programme principal"""
    print("🧪 Tests du contrôleur LCD menu")
    print("=" * 60)
    
    # Test 1: Contrôleur de base
    test1_success = test_lcd_menu_controller()
    
    # Test 2: Navigation dans le menu
    test2_success = test_menu_navigation()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"   Contrôleur LCD menu: {'✅ PASSÉ' if test1_success else '❌ ÉCHOUÉ'}")
    print(f"   Navigation menu: {'✅ PASSÉ' if test2_success else '❌ ÉCHOUÉ'}")
    
    if test1_success and test2_success:
        print("\n🎉 Tous les tests sont passés !")
        print("Le contrôleur LCD menu est fonctionnel.")
        return True
    else:
        print("\n⚠️ Certains tests ont échoué.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
