#!/usr/bin/env python3
"""
Configuration pour le système Alimante
Paramètres GPIO et configuration système
"""

# Configuration des pins GPIO
GPIO_CONFIG = {
    # Encodeur rotatif
    'ENCODER': {
        'CLK_PIN': 17,  # Pin CLK de l'encodeur
        'DT_PIN': 27,   # Pin DT de l'encodeur
        'SW_PIN': 22,   # Pin SW (bouton) de l'encodeur
    },
    
    # Écran PSI (ST7735)
    'DISPLAY': {
        'RESET_PIN': 24,  # Pin Reset de l'écran
        'A0_PIN': 25,     # Pin A0/DC de l'écran
        'CS_PIN': 8,      # Pin CS (Chip Select) de l'écran
        'SDA_PIN': 10,    # Pin SDA/MOSI de l'écran
        'SCL_PIN': 11,    # Pin SCL/SCLK de l'écran
    },
    
    # Bandeaux LED
    'LED': {
        'PWM_PIN': 18,  # Pin PWM pour les bandeaux LED (changé car 24 utilisé par écran)
        'FREQUENCY': 1000,  # Fréquence PWM en Hz
        'MAX_INTENSITY': 100,  # Intensité maximale en %
    },
    
    # Capteurs (optionnels)
    'SENSORS': {
        'TEMP_PIN': 4,   # Pin pour capteur de température
        'LIGHT_PIN': 19, # Pin pour capteur de luminosité (changé car 17 utilisé par encodeur)
    },
    
    # Communication
    'COMMUNICATION': {
        'I2C_ENABLED': True,
        'SERIAL_ENABLED': False,
        'BAUDRATE': 9600,
    }
}

# Configuration de l'interface utilisateur
UI_CONFIG = {
    'DISPLAY': {
        'REFRESH_RATE': 0.1,  # Taux de rafraîchissement en secondes
        'DEBOUNCE_TIME': 200,  # Temps d'anti-rebond en ms
        'MENU_TIMEOUT': 30,    # Timeout du menu en secondes
    },
    
    'MENU': {
        'ITEMS': [
            "🏠 Accueil Alimante",
            "💡 Test LED Bandeaux", 
            "📊 Monitoring Système",
            "⚙️ Configuration",
            "🔧 Tests Hardware",
            "📈 Statistiques",
            "ℹ️ À propos"
        ]
    }
}

# Configuration des tests
TEST_CONFIG = {
    'LED_TEST': {
        'FADE_DURATION': 2.0,  # Durée du fondu en secondes
        'FADE_STEPS': 50,      # Nombre d'étapes pour le fondu
        'BLINK_TIMES': 5,      # Nombre de clignotements
        'BLINK_ON_DURATION': 0.5,  # Durée allumée
        'BLINK_OFF_DURATION': 0.5, # Durée éteinte
    },
    
    'ENCODER_TEST': {
        'DEBOUNCE_TIME': 2,    # Temps d'anti-rebond en ms
        'ROTATION_SENSITIVITY': 1,  # Sensibilité de rotation
    }
}

# Configuration système
SYSTEM_CONFIG = {
    'VERSION': '1.0.0',
    'NAME': 'Alimante',
    'DESCRIPTION': 'Système de contrôle intelligent pour bandeaux LED',
    'AUTHOR': 'Alimante Team',
    'LOG_LEVEL': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'LOG_FILE': '/var/log/alimante.log',
}

def get_gpio_config():
    """Retourne la configuration GPIO"""
    return GPIO_CONFIG

def get_ui_config():
    """Retourne la configuration de l'interface utilisateur"""
    return UI_CONFIG

def get_test_config():
    """Retourne la configuration des tests"""
    return TEST_CONFIG

def get_system_config():
    """Retourne la configuration système"""
    return SYSTEM_CONFIG

def validate_config():
    """Valide la configuration"""
    errors = []
    
    # Vérification des pins GPIO
    encoder_pins = GPIO_CONFIG['ENCODER'].values()
    led_pins = [GPIO_CONFIG['LED']['PWM_PIN']]
    sensor_pins = list(GPIO_CONFIG['SENSORS'].values())
    
    all_pins = list(encoder_pins) + led_pins + sensor_pins
    
    # Vérification des doublons
    if len(all_pins) != len(set(all_pins)):
        errors.append("❌ Pins GPIO en doublon détectés")
    
    # Vérification des plages de pins
    for pin in all_pins:
        if pin < 1 or pin > 27:
            errors.append(f"❌ Pin GPIO {pin} hors plage valide (1-27)")
    
    # Vérification de la fréquence PWM
    freq = GPIO_CONFIG['LED']['FREQUENCY']
    if freq < 1 or freq > 10000:
        errors.append(f"❌ Fréquence PWM {freq}Hz hors plage valide (1-10000)")
    
    if errors:
        print("⚠️  Erreurs de configuration détectées:")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("✅ Configuration valide")
        return True

def print_config():
    """Affiche la configuration actuelle"""
    print("🔧 CONFIGURATION ALIMANTE")
    print("=" * 40)
    
    print("\n📌 Pins GPIO:")
    for category, pins in GPIO_CONFIG.items():
        print(f"   {category}:")
        for pin_name, pin_value in pins.items():
            print(f"     • {pin_name}: {pin_value}")
    
    print(f"\n⚙️  Système:")
    print(f"   • Version: {SYSTEM_CONFIG['VERSION']}")
    print(f"   • Nom: {SYSTEM_CONFIG['NAME']}")
    print(f"   • Description: {SYSTEM_CONFIG['DESCRIPTION']}")
    
    print(f"\n🎛️  Interface:")
    print(f"   • Taux de rafraîchissement: {UI_CONFIG['DISPLAY']['REFRESH_RATE']}s")
    print(f"   • Anti-rebond: {UI_CONFIG['DISPLAY']['DEBOUNCE_TIME']}ms")
    print(f"   • Timeout menu: {UI_CONFIG['DISPLAY']['MENU_TIMEOUT']}s")

if __name__ == "__main__":
    print_config()
    print()
    validate_config()
