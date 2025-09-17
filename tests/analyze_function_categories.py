#!/usr/bin/env python3
"""
Analyseur de catégories de fonctions orphelines
Classe les fonctions orphelines par type et utilité
"""

import sys
import os
import re
from collections import defaultdict

def categorize_orphaned_functions():
    """Catégorise les fonctions orphelines par type"""
    
    # Données des fonctions orphelines (extrait de l'analyse précédente)
    orphaned_functions = [
        # Fonctions de test/debug (à supprimer)
        ("src/controllers/drivers/test_drivers.py", "test_all_drivers", "test"),
        ("src/controllers/drivers/test_drivers.py", "_test_dht22", "test"),
        ("src/controllers/drivers/test_drivers.py", "_test_air_quality", "test"),
        ("src/controllers/drivers/test_drivers.py", "_test_water_sensor", "test"),
        ("src/controllers/drivers/test_drivers.py", "_test_pwm", "test"),
        ("src/controllers/drivers/test_drivers.py", "_test_relay", "test"),
        ("src/controllers/drivers/test_drivers.py", "_test_servo", "test"),
        ("src/controllers/drivers/test_drivers.py", "_test_st7735", "test"),
        ("src/controllers/drivers/test_drivers.py", "_test_rotary_encoder", "test"),
        
        # Fonctions d'initialisation (à garder)
        ("src/services/sensor_service.py", "_initialize_dht22_sensor", "init"),
        ("src/services/sensor_service.py", "_initialize_air_quality_sensor", "init"),
        ("src/services/sensor_service.py", "_initialize_water_level_sensor", "init"),
        ("src/ui/ui_controller.py", "_initialize_services", "init"),
        ("src/ui/ui_controller.py", "_initialize_components", "init"),
        
        # Fonctions de configuration (à garder)
        ("src/services/sensor_service.py", "_load_calibration_data", "config"),
        ("src/services/sensor_service.py", "_save_calibration_data", "config"),
        ("src/ui/ui_controller.py", "_load_config", "config"),
        ("src/ui/ui_controller.py", "_load_default_config", "config"),
        
        # Fonctions de contrôle interne (à garder)
        ("src/services/control_service.py", "_control_temperature", "control"),
        ("src/services/control_service.py", "_control_humidity", "control"),
        ("src/services/control_service.py", "_control_lighting", "control"),
        ("src/services/control_service.py", "_control_ventilation", "control"),
        ("src/services/control_service.py", "_control_feeding", "control"),
        
        # Fonctions de validation (à garder)
        ("src/services/safety_service.py", "_check_temperature_limits", "validation"),
        ("src/services/safety_service.py", "_check_humidity_limits", "validation"),
        ("src/services/safety_service.py", "_check_air_quality_limits", "validation"),
        ("src/services/safety_service.py", "_check_water_level_limits", "validation"),
        
        # Fonctions d'affichage (à garder)
        ("src/ui/lcd_interface.py", "_display_home_screen", "display"),
        ("src/ui/lcd_interface.py", "_display_sensors_screen", "display"),
        ("src/ui/lcd_interface.py", "_display_controls_screen", "display"),
        ("src/ui/lcd_interface.py", "_display_config_screen", "display"),
        ("src/ui/lcd_interface.py", "_display_alerts_screen", "display"),
        
        # Fonctions utilitaires (à garder)
        ("src/utils/time_utils.py", "get_current_time", "utility"),
        ("src/utils/time_utils.py", "is_daytime", "utility"),
        ("src/utils/time_utils.py", "calculate_lighting_intensity", "utility"),
        ("src/utils/time_utils.py", "should_feed_now", "utility"),
        ("src/utils/time_utils.py", "calculate_uptime", "utility"),
        
        # Fonctions de calibration (à garder)
        ("src/utils/calibration.py", "start_calibration", "calibration"),
        ("src/utils/calibration.py", "add_calibration_sample", "calibration"),
        ("src/utils/calibration.py", "finish_calibration", "calibration"),
        ("src/utils/calibration.py", "apply_calibration", "calibration"),
        
        # Fonctions de gestion d'événements (à garder)
        ("src/ui/ui_controller.py", "_on_sensor_data_updated", "event_handler"),
        ("src/ui/ui_controller.py", "_on_emergency_stop", "event_handler"),
        ("src/ui/ui_controller.py", "_on_heating_changed", "event_handler"),
        ("src/services/control_service.py", "_on_emergency_stop", "event_handler"),
        ("src/services/control_service.py", "_on_safety_alert", "event_handler"),
        
        # Fonctions de statut (à garder)
        ("src/services/sensor_service.py", "get_data_history", "status"),
        ("src/services/control_service.py", "get_decision_history", "status"),
        ("src/services/safety_service.py", "get_safety_status", "status"),
        ("src/services/heating_service.py", "get_heating_status", "status"),
        
        # Fonctions de nettoyage (à garder)
        ("src/services/safety_service.py", "acknowledge_alert", "cleanup"),
        ("src/services/safety_service.py", "clear_emergency_stop", "cleanup"),
        ("src/services/safety_service.py", "reset_safety_data", "cleanup"),
    ]
    
    # Catégoriser
    categories = defaultdict(list)
    for file_path, func_name, category in orphaned_functions:
        categories[category].append((file_path, func_name))
    
    return categories

def main():
    """Fonction principale"""
    print("🔍 Analyse des catégories de fonctions orphelines")
    print("=" * 60)
    
    categories = categorize_orphaned_functions()
    
    # Afficher les catégories
    for category, functions in categories.items():
        print(f"\n📂 {category.upper()} ({len(functions)} fonctions):")
        
        # Recommandations par catégorie
        recommendations = {
            'test': '🗑️ À SUPPRIMER - Fonctions de test uniquement',
            'init': '✅ À GARDER - Initialisation nécessaire',
            'config': '✅ À GARDER - Configuration système',
            'control': '✅ À GARDER - Logique de contrôle interne',
            'validation': '✅ À GARDER - Validation de sécurité',
            'display': '✅ À GARDER - Affichage UI',
            'utility': '✅ À GARDER - Utilitaires système',
            'calibration': '✅ À GARDER - Calibration hardware',
            'event_handler': '✅ À GARDER - Gestionnaires d\'événements',
            'status': '✅ À GARDER - Fonctions de statut',
            'cleanup': '✅ À GARDER - Nettoyage et maintenance'
        }
        
        print(f"   {recommendations.get(category, '❓ À ÉVALUER')}")
        
        for file_path, func_name in functions[:5]:  # Afficher les 5 premières
            print(f"   - {file_path}:{func_name}")
        if len(functions) > 5:
            print(f"   ... et {len(functions) - 5} autres")
    
    # Résumé des recommandations
    print(f"\n📊 RÉSUMÉ DES RECOMMANDATIONS:")
    print(f"   🗑️ À supprimer: {len(categories.get('test', []))} fonctions")
    print(f"   ✅ À garder: {sum(len(funcs) for cat, funcs in categories.items() if cat != 'test')} fonctions")
    
    # Calcul du pourcentage réellement orphelin
    total_test = len(categories.get('test', []))
    total_keep = sum(len(funcs) for cat, funcs in categories.items() if cat != 'test')
    total_analyzed = total_test + total_keep
    
    if total_analyzed > 0:
        real_orphaned_pct = (total_test / total_analyzed) * 100
        print(f"   📈 Vraiment orphelines: {real_orphaned_pct:.1f}%")
    
    print(f"\n🎯 CONCLUSION:")
    print(f"   La plupart des 'fonctions orphelines' sont en fait des fonctions")
    print(f"   utilitaires, d'initialisation ou de contrôle interne nécessaires.")
    print(f"   Seules les fonctions de test peuvent être supprimées en toute sécurité.")

if __name__ == "__main__":
    main()
