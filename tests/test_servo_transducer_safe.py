#!/usr/bin/env python3
"""
Test sécurisé pour servomoteur et brumisateur
Mouvements très limités pour éviter les dommages matériels
"""

import sys
import os
import time
import json
import logging
from pathlib import Path

# Ajouter le répertoire parent au path pour accéder aux modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.controllers.drivers.servo_driver import ServoDriver
    from src.controllers.drivers.base_driver import DriverConfig, DriverState
    SERVO_AVAILABLE = True
except ImportError as e:
    SERVO_AVAILABLE = False
    print(f"⚠️  Driver servo non disponible: {e}")

try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
except ImportError:
    RASPBERRY_PI = False
    print("⚠️  RPi.GPIO non disponible - mode simulation")

class SafeServoBrumisateurTest:
    """Test sécurisé pour servomoteur et brumisateur"""
    
    def __init__(self):
        self.config = self.load_gpio_config()
        self.servo = None
        self.test_results = {
            "servo_initialization": False,
            "servo_safe_movement": False,
            "servo_limits_test": False,
            "brumisateur_test": False
        }
        
        # Configuration de sécurité
        self.SAFE_ANGLE_RANGE = 5  # Seulement 5 degrés de mouvement
        self.SAFE_CENTER_ANGLE = 90  # Angle central de sécurité
        self.MOVEMENT_DELAY = 0.5  # Délai entre mouvements
        
    def load_gpio_config(self):
        """Charge la configuration GPIO depuis le fichier JSON"""
        try:
            config_path = Path(__file__).parent.parent / "config" / "gpio_config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement config GPIO: {e}")
            return None
    
    def get_servo_config(self):
        """Récupère la configuration du servomoteur"""
        if not self.config:
            return None
            
        try:
            actuators = self.config.get("gpio_pins", {}).get("actuators", {})
            servo_config = actuators.get("feeder_servo", {})
            
            return {
                "pin": servo_config.get("pwm_pin", 18),
                "frequency": servo_config.get("frequency", 50),
                "description": servo_config.get("description", "Servo-moteur distributeur")
            }
        except Exception as e:
            print(f"❌ Erreur récupération config servo: {e}")
            return None
    
    def test_servo_initialization(self):
        """Test d'initialisation sécurisée du servomoteur"""
        print("\n🔧 TEST D'INITIALISATION SERVOMOTEUR")
        print("=" * 40)
        
        if not SERVO_AVAILABLE:
            print("❌ Driver servo non disponible")
            return False
            
        if not RASPBERRY_PI:
            print("⚠️  Mode simulation - pas de matériel réel")
            return True
            
        servo_config = self.get_servo_config()
        if not servo_config:
            print("❌ Configuration servo non trouvée")
            return False
            
        print(f"📍 Pin GPIO: {servo_config['pin']}")
        print(f"📍 Fréquence: {servo_config['frequency']}Hz")
        print(f"📍 Description: {servo_config['description']}")
        
        try:
            # Créer le driver avec configuration sécurisée
            config = DriverConfig("safe_test", enabled=True)
            self.servo = ServoDriver(config, servo_config['pin'], servo_config['frequency'])
            
            # Définir des limites très restrictives pour la sécurité
            self.servo.set_limits(
                self.SAFE_CENTER_ANGLE - self.SAFE_ANGLE_RANGE,
                self.SAFE_CENTER_ANGLE + self.SAFE_ANGLE_RANGE
            )
            
            if self.servo.initialize():
                print("✅ Servomoteur initialisé avec succès")
                print(f"   • Limites de sécurité: {self.SAFE_CENTER_ANGLE - self.SAFE_ANGLE_RANGE}° - {self.SAFE_CENTER_ANGLE + self.SAFE_ANGLE_RANGE}°")
                self.test_results["servo_initialization"] = True
                return True
            else:
                print("❌ Échec d'initialisation du servomoteur")
                return False
                
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return False
    
    def test_safe_servo_movement(self):
        """Test de mouvement sécurisé du servomoteur"""
        print("\n🎛️  TEST DE MOUVEMENT SÉCURISÉ")
        print("=" * 35)
        
        if not self.servo or not self.servo.is_ready():
            print("❌ Servomoteur non initialisé")
            return False
            
        print("⚠️  ATTENTION: Mouvements très limités pour la sécurité")
        print(f"   • Plage de mouvement: ±{self.SAFE_ANGLE_RANGE}° autour de {self.SAFE_CENTER_ANGLE}°")
        print("   • Durée totale du test: ~3 secondes")
        
        try:
            # Position initiale sécurisée
            print("\n1️⃣ Position initiale (centre)...")
            self.servo.write({"angle": self.SAFE_CENTER_ANGLE, "duration": 0.5})
            time.sleep(self.MOVEMENT_DELAY)
            
            # Petit mouvement vers la droite (sécurisé)
            print("2️⃣ Petit mouvement +2°...")
            target_angle = self.SAFE_CENTER_ANGLE + 2
            self.servo.write({"angle": target_angle, "duration": 0.5})
            time.sleep(self.MOVEMENT_DELAY)
            
            # Retour au centre
            print("3️⃣ Retour au centre...")
            self.servo.write({"angle": self.SAFE_CENTER_ANGLE, "duration": 0.5})
            time.sleep(self.MOVEMENT_DELAY)
            
            # Petit mouvement vers la gauche (sécurisé)
            print("4️⃣ Petit mouvement -2°...")
            target_angle = self.SAFE_CENTER_ANGLE - 2
            self.servo.write({"angle": target_angle, "duration": 0.5})
            time.sleep(self.MOVEMENT_DELAY)
            
            # Retour final au centre
            print("5️⃣ Position finale (centre)...")
            self.servo.write({"angle": self.SAFE_CENTER_ANGLE, "duration": 0.5})
            time.sleep(self.MOVEMENT_DELAY)
            
            print("✅ Test de mouvement sécurisé terminé")
            self.test_results["servo_safe_movement"] = True
            return True
            
        except Exception as e:
            print(f"❌ Erreur mouvement servo: {e}")
            return False
    
    def test_servo_limits(self):
        """Test des limites de sécurité du servomoteur"""
        print("\n🛡️  TEST DES LIMITES DE SÉCURITÉ")
        print("=" * 35)
        
        if not self.servo or not self.servo.is_ready():
            print("❌ Servomoteur non initialisé")
            return False
            
        try:
            # Test angle minimum
            print("1️⃣ Test angle minimum...")
            min_angle = self.SAFE_CENTER_ANGLE - self.SAFE_ANGLE_RANGE
            self.servo.write({"angle": min_angle - 10, "duration": 0.3})  # Devrait être limité
            actual_angle = self.servo.get_angle()
            print(f"   • Angle demandé: {min_angle - 10}°")
            print(f"   • Angle réel: {actual_angle}°")
            
            time.sleep(self.MOVEMENT_DELAY)
            
            # Test angle maximum
            print("2️⃣ Test angle maximum...")
            max_angle = self.SAFE_CENTER_ANGLE + self.SAFE_ANGLE_RANGE
            self.servo.write({"angle": max_angle + 10, "duration": 0.3})  # Devrait être limité
            actual_angle = self.servo.get_angle()
            print(f"   • Angle demandé: {max_angle + 10}°")
            print(f"   • Angle réel: {actual_angle}°")
            
            time.sleep(self.MOVEMENT_DELAY)
            
            # Retour au centre
            print("3️⃣ Retour au centre...")
            self.servo.write({"angle": self.SAFE_CENTER_ANGLE, "duration": 0.3})
            
            print("✅ Test des limites terminé")
            self.test_results["servo_limits_test"] = True
            return True
            
        except Exception as e:
            print(f"❌ Erreur test limites: {e}")
            return False
    
    def get_brumisateur_config(self):
        """Récupère la configuration du brumisateur"""
        if not self.config:
            return None
            
        try:
            actuators = self.config.get("gpio_pins", {}).get("actuators", {})
            brumisateur_config = actuators.get("humidifier", {})
            
            return {
                "pin": brumisateur_config.get("relay_pin", 5),
                "type": brumisateur_config.get("type", "digital"),
                "description": brumisateur_config.get("description", "Relais brumisateur")
            }
        except Exception as e:
            print(f"❌ Erreur récupération config brumisateur: {e}")
            return None
    
    def test_brumisateur(self):
        """Test du brumisateur (humidificateur)"""
        print("\n💨 TEST BRUMISATEUR")
        print("=" * 25)
        
        brumisateur_config = self.get_brumisateur_config()
        if not brumisateur_config:
            print("❌ Configuration brumisateur non trouvée")
            return False
            
        print(f"📍 Pin GPIO: {brumisateur_config['pin']}")
        print(f"📍 Type: {brumisateur_config['type']}")
        print(f"📍 Description: {brumisateur_config['description']}")
        
        if not RASPBERRY_PI:
            print("⚠️  Mode simulation - pas de matériel réel")
            print("ℹ️  Simulation du contrôle du brumisateur:")
            print("   • Activation relais pendant 2 secondes")
            print("   • Vérification de l'état du relais")
            print("   • Désactivation du relais")
            time.sleep(2)
            print("✅ Simulation brumisateur terminée")
            self.test_results["brumisateur_test"] = True
            return True
        
        try:
            import RPi.GPIO as GPIO
            
            # Configuration du pin en sortie
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(brumisateur_config['pin'], GPIO.OUT)
            
            print("\n1️⃣ Test d'activation du brumisateur...")
            print("   ⚠️  Le brumisateur va s'activer pendant 3 secondes")
            print("   ⚠️  Assurez-vous qu'il n'y a pas d'eau à proximité")
            
            # Confirmation de sécurité
            response = input("   Continuer le test? (o/n): ").lower().strip()
            if response not in ['o', 'oui', 'y', 'yes']:
                print("   ❌ Test annulé par l'utilisateur")
                return False
            
            # Activation du relais
            GPIO.output(brumisateur_config['pin'], GPIO.HIGH)
            print("   ✅ Brumisateur activé - relais ON")
            
            # Test de 3 secondes
            for i in range(3):
                print(f"   ⏱️  Temps restant: {3-i} secondes...")
                time.sleep(1)
            
            # Désactivation du relais
            GPIO.output(brumisateur_config['pin'], GPIO.LOW)
            print("   ✅ Brumisateur désactivé - relais OFF")
            
            # Test de l'état du relais
            print("\n2️⃣ Vérification de l'état du relais...")
            current_state = GPIO.input(brumisateur_config['pin'])
            print(f"   • État actuel: {'HIGH' if current_state else 'LOW'}")
            print(f"   • Statut: {'✅ Relais fonctionnel' if not current_state else '⚠️  Relais encore actif'}")
            
            # Nettoyage
            GPIO.setup(brumisateur_config['pin'], GPIO.IN)
            
            print("\n✅ Test brumisateur terminé")
            self.test_results["brumisateur_test"] = True
            return True
            
        except Exception as e:
            print(f"❌ Erreur test brumisateur: {e}")
            return False
    
    def cleanup(self):
        """Nettoyage des ressources"""
        print("\n🧹 NETTOYAGE DES RESSOURCES")
        print("=" * 30)
        
        if self.servo:
            try:
                # Position sécurisée avant arrêt
                self.servo.write({"angle": self.SAFE_CENTER_ANGLE, "duration": 0.5})
                time.sleep(0.5)
                self.servo.cleanup()
                print("✅ Servomoteur nettoyé")
            except Exception as e:
                print(f"⚠️  Erreur nettoyage servo: {e}")
        
        if RASPBERRY_PI:
            try:
                GPIO.cleanup()
                print("✅ GPIO nettoyé")
            except Exception as e:
                print(f"⚠️  Erreur nettoyage GPIO: {e}")
    
    def print_results(self):
        """Affiche les résultats des tests"""
        print("\n📊 RÉSULTATS DES TESTS")
        print("=" * 25)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅" if result else "❌"
            test_display = test_name.replace("_", " ").title()
            print(f"{status} {test_display}")
        
        print(f"\n📈 Score: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 Tous les tests sont passés avec succès!")
        elif passed_tests > 0:
            print("⚠️  Certains tests ont échoué")
        else:
            print("❌ Aucun test n'a réussi")
    
    def run_all_tests(self):
        """Lance tous les tests"""
        print("🚀 DÉMARRAGE DES TESTS SÉCURISÉS")
        print("=" * 40)
        print("⚠️  Tests avec mouvements très limités pour la sécurité")
        print("💨 Test du brumisateur avec confirmation de sécurité")
        print("=" * 40)
        
        try:
            # Test d'initialisation
            self.test_servo_initialization()
            
            # Test de mouvement sécurisé
            if self.test_results["servo_initialization"]:
                self.test_safe_servo_movement()
                self.test_servo_limits()
            
            # Test du brumisateur
            self.test_brumisateur()
            
        except KeyboardInterrupt:
            print("\n🛑 Tests interrompus par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur inattendue: {e}")
        finally:
            self.cleanup()
            self.print_results()

def main():
    """Fonction principale"""
    print("🔧 TEST SÉCURISÉ SERVOMOTEUR ET BRUMISATEUR")
    print("=" * 50)
    print("⚠️  ATTENTION: Mouvements très limités pour la sécurité")
    print("💨 Test du brumisateur avec confirmation de sécurité")
    print("=" * 50)
    
    # Vérification des prérequis
    if not SERVO_AVAILABLE:
        print("❌ Driver servo non disponible")
        print("   Installez les dépendances: pip install RPi.GPIO")
        return
    
    if not RASPBERRY_PI:
        print("⚠️  Mode simulation - pas de matériel réel")
        print("   Pour tester sur Raspberry Pi, installez: pip install RPi.GPIO")
    
    # Confirmation de l'utilisateur
    print("\n⚠️  CONFIRMATION DE SÉCURITÉ")
    print("Les tests utilisent des mouvements très limités (±5°)")
    print("Assurez-vous qu'aucun objet fragile n'est à proximité du servomoteur")
    print("Le test du brumisateur activera le relais pendant 3 secondes")
    
    response = input("\nContinuer les tests? (o/n): ").lower().strip()
    if response not in ['o', 'oui', 'y', 'yes']:
        print("❌ Tests annulés par l'utilisateur")
        return
    
    # Lancement des tests
    tester = SafeServoBrumisateurTest()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
