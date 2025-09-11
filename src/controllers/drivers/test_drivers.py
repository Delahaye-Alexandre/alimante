"""
Tests pour valider tous les drivers
"""

import time
import logging
from typing import Dict, Any
from .base_driver import DriverConfig
from .dht22_sensor import DHT22Sensor
from .air_quality_sensor import AirQualitySensor
from .tenflyer_water_sensor import TenflyerWaterSensor
from .pwm_driver import PWMDriver
from .relay_driver import RelayDriver
from .servo_driver import ServoDriver
from .st7735_driver import ST7735Driver
from .rotary_encoder_driver import RotaryEncoderDriver

class DriverTester:
    """
    Classe pour tester tous les drivers
    """
    
    def __init__(self):
        self.logger = logging.getLogger("alimante.driver_tester")
        self.drivers = {}
        self.test_results = {}
        
    def test_all_drivers(self) -> Dict[str, bool]:
        """
        Teste tous les drivers
        
        Returns:
            Dictionnaire des résultats de test
        """
        self.logger.info("Démarrage des tests de drivers")
        
        # Tests des capteurs
        self.test_results["dht22"] = self._test_dht22()
        self.test_results["air_quality"] = self._test_air_quality()
        self.test_results["water_sensor"] = self._test_water_sensor()
        
        # Tests des actionneurs
        self.test_results["pwm"] = self._test_pwm()
        self.test_results["relay"] = self._test_relay()
        self.test_results["servo"] = self._test_servo()
        
        # Tests des périphériques
        self.test_results["st7735"] = self._test_st7735()
        self.test_results["rotary_encoder"] = self._test_rotary_encoder()
        
        # Résumé
        self._print_summary()
        
        return self.test_results
    
    def _test_dht22(self) -> bool:
        """Test du capteur DHT22"""
        try:
            self.logger.info("Test DHT22...")
            
            config = DriverConfig(
                name="test_dht22",
                enabled=True,
                calibration={"temperature_offset": 0.0, "humidity_offset": 0.0}
            )
            
            driver = DHT22Sensor(config, gpio_pin=4)
            
            # Test d'initialisation
            if not driver.initialize():
                self.logger.error("Échec initialisation DHT22")
                return False
            
            # Test de lecture
            data = driver.safe_read()
            if data is None:
                self.logger.error("Échec lecture DHT22")
                return False
            
            self.logger.info(f"DHT22 - Température: {data.get('temperature', 'N/A')}°C, "
                           f"Humidité: {data.get('humidity', 'N/A')}%")
            
            # Test de statut
            status = driver.get_status()
            self.logger.info(f"DHT22 Status: {status}")
            
            driver.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur test DHT22: {e}")
            return False
    
    def _test_air_quality(self) -> bool:
        """Test du capteur de qualité d'air"""
        try:
            self.logger.info("Test capteur qualité d'air...")
            
            config = DriverConfig(
                name="test_air_quality",
                enabled=True,
                calibration={"baseline": 50, "sensitivity": 1.0}
            )
            
            driver = AirQualitySensor(config, gpio_pin=5, adc_channel=0)
            
            # Test d'initialisation
            if not driver.initialize():
                self.logger.error("Échec initialisation capteur qualité d'air")
                return False
            
            # Test de lecture
            data = driver.safe_read()
            if data is None:
                self.logger.error("Échec lecture capteur qualité d'air")
                return False
            
            self.logger.info(f"Qualité d'air - AQI: {data.get('aqi', 'N/A')}, "
                           f"Niveau: {data.get('level', 'N/A')}")
            
            driver.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur test qualité d'air: {e}")
            return False
    
    def _test_water_sensor(self) -> bool:
        """Test du capteur de niveau d'eau"""
        try:
            self.logger.info("Test capteur niveau d'eau...")
            
            config = DriverConfig(
                name="test_water_sensor",
                enabled=True,
                calibration={"empty_level": 0, "full_level": 100}
            )
            
            driver = TenflyerWaterSensor(config, gpio_pin=21)
            
            # Test d'initialisation
            if not driver.initialize():
                self.logger.error("Échec initialisation capteur niveau d'eau")
                return False
            
            # Test de lecture
            data = driver.safe_read()
            if data is None:
                self.logger.error("Échec lecture capteur niveau d'eau")
                return False
            
            self.logger.info(f"Niveau d'eau - Pourcentage: {data.get('percentage', 'N/A')}%, "
                           f"Niveau: {data.get('level', 'N/A')}")
            
            # Test des méthodes utilitaires
            is_empty = driver.is_empty()
            is_low = driver.is_low()
            is_full = driver.is_full()
            
            self.logger.info(f"État réservoir - Vide: {is_empty}, Bas: {is_low}, Plein: {is_full}")
            
            driver.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur test niveau d'eau: {e}")
            return False
    
    def _test_pwm(self) -> bool:
        """Test du driver PWM"""
        try:
            self.logger.info("Test PWM...")
            
            config = DriverConfig(name="test_pwm", enabled=True)
            driver = PWMDriver(config, gpio_pin=12, frequency=1000)
            
            # Test d'initialisation
            if not driver.initialize():
                self.logger.error("Échec initialisation PWM")
                return False
            
            # Test de lecture
            data = driver.safe_read()
            if data is None:
                self.logger.error("Échec lecture PWM")
                return False
            
            self.logger.info(f"PWM - Duty cycle: {data.get('duty_cycle', 'N/A')}%, "
                           f"Fréquence: {data.get('frequency', 'N/A')}Hz")
            
            # Test d'écriture
            if not driver.safe_write({"duty_cycle": 50}):
                self.logger.error("Échec écriture PWM")
                return False
            
            time.sleep(0.1)
            
            # Test de fade
            if not driver.safe_write({"duty_cycle": 80, "fade": True, "fade_duration": 0.5}):
                self.logger.error("Échec fade PWM")
                return False
            
            time.sleep(0.6)
            
            driver.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur test PWM: {e}")
            return False
    
    def _test_relay(self) -> bool:
        """Test du driver de relais"""
        try:
            self.logger.info("Test relais...")
            
            config = DriverConfig(name="test_relay", enabled=True)
            driver = RelayDriver(config, gpio_pin=19, active_high=True)
            
            # Test d'initialisation
            if not driver.initialize():
                self.logger.error("Échec initialisation relais")
                return False
            
            # Test de lecture
            data = driver.safe_read()
            if data is None:
                self.logger.error("Échec lecture relais")
                return False
            
            self.logger.info(f"Relais - État: {data.get('state', 'N/A')}, "
                           f"Commutations: {data.get('switch_count', 'N/A')}")
            
            # Test d'activation
            if not driver.turn_on():
                self.logger.error("Échec activation relais")
                return False
            
            time.sleep(0.1)
            
            # Test de désactivation
            if not driver.turn_off():
                self.logger.error("Échec désactivation relais")
                return False
            
            driver.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur test relais: {e}")
            return False
    
    def _test_servo(self) -> bool:
        """Test du driver de servo"""
        try:
            self.logger.info("Test servo...")
            
            config = DriverConfig(name="test_servo", enabled=True)
            driver = ServoDriver(config, gpio_pin=18, frequency=50)
            
            # Test d'initialisation
            if not driver.initialize():
                self.logger.error("Échec initialisation servo")
                return False
            
            # Test de lecture
            data = driver.safe_read()
            if data is None:
                self.logger.error("Échec lecture servo")
                return False
            
            self.logger.info(f"Servo - Angle: {data.get('angle', 'N/A')}°, "
                           f"Position: {data.get('position', 'N/A')}")
            
            # Test de mouvement
            if not driver.move_to_position("open", duration=0.5):
                self.logger.error("Échec mouvement servo vers ouvert")
                return False
            
            time.sleep(0.6)
            
            if not driver.move_to_position("closed", duration=0.5):
                self.logger.error("Échec mouvement servo vers fermé")
                return False
            
            time.sleep(0.6)
            
            driver.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur test servo: {e}")
            return False
    
    def _test_st7735(self) -> bool:
        """Test du driver ST7735"""
        try:
            self.logger.info("Test ST7735...")
            
            config = DriverConfig(name="test_st7735", enabled=True)
            driver = ST7735Driver(
                config, 
                dc_pin=25, rst_pin=24, 
                port=0, cs=0, width=128, height=160
            )
            
            # Test d'initialisation
            if not driver.initialize():
                self.logger.error("Échec initialisation ST7735")
                return False
            
            # Test de lecture
            data = driver.safe_read()
            if data is None:
                self.logger.error("Échec lecture ST7735")
                return False
            
            self.logger.info(f"ST7735 - Taille: {data.get('width', 'N/A')}x{data.get('height', 'N/A')}, "
                           f"Rotation: {data.get('rotation', 'N/A')}°")
            
            # Test d'effacement
            if not driver.safe_write({"command": "clear", "color": "black"}):
                self.logger.error("Échec effacement ST7735")
                return False
            
            # Test de dessin
            if not driver.safe_write({
                "command": "rectangle",
                "x": 10, "y": 10, "width": 50, "height": 30,
                "color": "red", "filled": True
            }):
                self.logger.error("Échec dessin rectangle ST7735")
                return False
            
            if not driver.safe_write({
                "command": "text",
                "text": "Test", "x": 20, "y": 20,
                "color": "white", "size": 1
            }):
                self.logger.error("Échec dessin texte ST7735")
                return False
            
            driver.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur test ST7735: {e}")
            return False
    
    def _test_rotary_encoder(self) -> bool:
        """Test du driver d'encodeur rotatif"""
        try:
            self.logger.info("Test encodeur rotatif...")
            
            config = DriverConfig(name="test_rotary_encoder", enabled=True)
            driver = RotaryEncoderDriver(config, clk_pin=17, dt_pin=27, sw_pin=22)
            
            # Test d'initialisation
            if not driver.initialize():
                self.logger.error("Échec initialisation encodeur")
                return False
            
            # Test de lecture
            data = driver.safe_read()
            if data is None:
                self.logger.error("Échec lecture encodeur")
                return False
            
            self.logger.info(f"Encodeur - Position: {data.get('position', 'N/A')}, "
                           f"Bouton: {data.get('button_pressed', 'N/A')}")
            
            # Test de configuration
            if not driver.safe_write({
                "min_position": -10,
                "max_position": 10,
                "step_size": 2
            }):
                self.logger.error("Échec configuration encodeur")
                return False
            
            # Test de définition de position
            if not driver.set_position(5):
                self.logger.error("Échec définition position encodeur")
                return False
            
            time.sleep(0.1)
            
            driver.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur test encodeur: {e}")
            return False
    
    def _print_summary(self) -> None:
        """Affiche le résumé des tests"""
        self.logger.info("=" * 50)
        self.logger.info("RÉSUMÉ DES TESTS DE DRIVERS")
        self.logger.info("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        for driver_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.logger.info(f"{driver_name:20} : {status}")
        
        self.logger.info("-" * 50)
        self.logger.info(f"Total: {total_tests} tests")
        self.logger.info(f"Réussis: {passed_tests}")
        self.logger.info(f"Échoués: {failed_tests}")
        self.logger.info(f"Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        self.logger.info("=" * 50)

def main():
    """Fonction principale de test"""
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer et exécuter les tests
    tester = DriverTester()
    results = tester.test_all_drivers()
    
    # Retourner le code de sortie approprié
    if all(results.values()):
        print("\n🎉 Tous les tests sont passés avec succès !")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué.")
        return 1

if __name__ == "__main__":
    exit(main())
