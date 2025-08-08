#!/usr/bin/env python3
"""
Programme de test des composants pour Alimante
Teste tous les composants du système d'élevage automatisé
"""

import time
import json
import logging
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import os
import sys

# Ajouter le répertoire src au path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import RPi.GPIO as GPIO
    import board
    import busio
    import adafruit_dht
    import adafruit_mcp3xxx.mcp3008 as MCP
    from adafruit_mcp3xxx.analog_in import AnalogIn
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    import spidev
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Assurez-vous d'avoir installé toutes les dépendances:")
    print("pip install RPi.GPIO adafruit-circuitpython-dht adafruit-circuitpython-mcp3xxx opencv-python pillow")
    sys.exit(1)


class TestStatus(Enum):
    """Statuts possibles des tests"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class TestResult:
    """Résultat d'un test de composant"""
    component: str
    status: TestStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    duration: float = 0.0


class ComponentTester:
    """Classe principale pour tester tous les composants"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.results: List[TestResult] = []
        self.gpio_initialized = False
        
        # Configuration des pins
        self.pin_config = {
            # Capteurs
            "dht22_pin": 4,
            "mq2_pin": 17,
            "light_sensor_pin": 27,
            
            # Actionneurs
            "servo_pin": 12,
            "mosfet_pin": 18,
            "transducer_pin": 23,
            "fans_pin": 16,  # 4 ventilateurs sur le même pin
            
            # Écran SPI
            "spi_ce": 8,
            "spi_dc": 25,
            "spi_rst": 24,
            
            # ADC
            "adc_cs": 22,
            "adc_clk": 11,
            "adc_miso": 9,
            "adc_mosi": 10
        }
        
        # Initialisation des composants
        self.dht22 = None
        self.mq2_sensor = None
        self.servo = None
        self.camera = None
        self.display = None
        self.adc = None
        self.fan_pwm = None
        
    def _setup_logging(self) -> logging.Logger:
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('component_test.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _add_result(self, result: TestResult) -> None:
        """Ajoute un résultat de test"""
        self.results.append(result)
        status_icon = "✅" if result.status == TestStatus.PASSED else "❌" if result.status == TestStatus.FAILED else "⚠️"
        print(f"{status_icon} {result.component}: {result.message}")
        self.logger.info(f"Test {result.component}: {result.status.value} - {result.message}")
    
    def test_gpio_setup(self) -> TestResult:
        """Test de l'initialisation GPIO"""
        start_time = time.time()
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            self.gpio_initialized = True
            
            return TestResult(
                component="GPIO Setup",
                status=TestStatus.PASSED,
                message="GPIO initialisé avec succès",
                duration=time.time() - start_time
            )
        except Exception as e:
            return TestResult(
                component="GPIO Setup",
                status=TestStatus.FAILED,
                message=f"Erreur GPIO: {str(e)}",
                duration=time.time() - start_time
            )
    
    def test_dht22(self) -> TestResult:
        """Test du capteur DHT22"""
        start_time = time.time()
        
        try:
            # Configuration du DHT22
            dht22_pin = self.pin_config["dht22_pin"]
            self.dht22 = adafruit_dht.DHT22(board.D4)
            
            # Lecture des données
            temperature = self.dht22.temperature
            humidity = self.dht22.humidity
            
            if temperature is not None and humidity is not None:
                return TestResult(
                    component="DHT22",
                    status=TestStatus.PASSED,
                    message=f"Température: {temperature:.1f}°C, Humidité: {humidity:.1f}%",
                    data={"temperature": temperature, "humidity": humidity},
                    duration=time.time() - start_time
                )
            else:
                return TestResult(
                    component="DHT22",
                    status=TestStatus.FAILED,
                    message="Impossible de lire les données DHT22",
                    duration=time.time() - start_time
                )
                
        except Exception as e:
            return TestResult(
                component="DHT22",
                status=TestStatus.FAILED,
                message=f"Erreur DHT22: {str(e)}",
                duration=time.time() - start_time
            )
    
    def test_mq2_sensor(self) -> TestResult:
        """Test du capteur MQ2 (qualité de l'air)"""
        start_time = time.time()
        
        try:
            # Configuration ADC pour MQ2
            spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
            cs = digitalio.DigitalInOut(board.D22)
            self.adc = MCP.MCP3008(spi, cs)
            
            # Canal pour MQ2
            mq2_channel = AnalogIn(self.adc, MCP.P0)
            
            # Lecture de la valeur
            voltage = mq2_channel.voltage
            raw_value = mq2_channel.value
            
            # Conversion en ppm (approximatif)
            ppm = self._convert_mq2_to_ppm(raw_value)
            
            return TestResult(
                component="MQ2 Sensor",
                status=TestStatus.PASSED,
                message=f"Valeur brute: {raw_value}, Tension: {voltage:.3f}V, PPM estimé: {ppm:.1f}",
                data={"raw_value": raw_value, "voltage": voltage, "ppm": ppm},
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                component="MQ2 Sensor",
                status=TestStatus.FAILED,
                message=f"Erreur MQ2: {str(e)}",
                duration=time.time() - start_time
            )
    
    def _convert_mq2_to_ppm(self, raw_value: int) -> float:
        """Convertit la valeur brute MQ2 en PPM approximatif"""
        # Conversion basique - à calibrer selon votre capteur
        voltage = (raw_value / 65535) * 3.3
        rs_ro_ratio = (5.0 - voltage) / voltage
        
        # Formule approximative pour le gaz combustible
        ppm = 1000 * (rs_ro_ratio ** -1.5)
        return max(0, ppm)
    
    def test_servo(self) -> TestResult:
        """Test du servomoteur"""
        start_time = time.time()
        
        try:
            servo_pin = self.pin_config["servo_pin"]
            GPIO.setup(servo_pin, GPIO.OUT)
            self.servo = GPIO.PWM(servo_pin, 50)  # 50Hz
            self.servo.start(0)
            
            # Test de mouvement
            angles = [0, 45, 90, 135, 180, 90, 0]
            
            for angle in angles:
                duty_cycle = self._angle_to_duty_cycle(angle)
                self.servo.ChangeDutyCycle(duty_cycle)
                time.sleep(0.5)
            
            self.servo.stop()
            
            return TestResult(
                component="Servomoteur",
                status=TestStatus.PASSED,
                message="Servomoteur testé avec succès (mouvement 0-180°)",
                data={"tested_angles": angles},
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                component="Servomoteur",
                status=TestStatus.FAILED,
                message=f"Erreur servomoteur: {str(e)}",
                duration=time.time() - start_time
            )
    
    def _angle_to_duty_cycle(self, angle: int) -> float:
        """Convertit un angle en cycle de travail PWM"""
        return 2.5 + (angle / 180.0) * 10.0
    
    def test_transducers(self) -> TestResult:
        """Test des transducteurs (brume)"""
        start_time = time.time()
        
        try:
            transducer_pin = self.pin_config["transducer_pin"]
            GPIO.setup(transducer_pin, GPIO.OUT)
            
            # Test d'activation courte
            GPIO.output(transducer_pin, GPIO.HIGH)
            time.sleep(0.1)  # 100ms de test
            GPIO.output(transducer_pin, GPIO.LOW)
            
            return TestResult(
                component="Transducteurs",
                status=TestStatus.PASSED,
                message="Transducteurs testés avec succès (activation 100ms)",
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                component="Transducteurs",
                status=TestStatus.FAILED,
                message=f"Erreur transducteurs: {str(e)}",
                duration=time.time() - start_time
            )
    
    def test_camera(self) -> TestResult:
        """Test de la caméra CSI"""
        start_time = time.time()
        
        try:
            # Initialisation de la caméra
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                return TestResult(
                    component="Caméra CSI",
                    status=TestStatus.FAILED,
                    message="Impossible d'ouvrir la caméra",
                    duration=time.time() - start_time
                )
            
            # Capture d'une image de test
            ret, frame = self.camera.read()
            
            if ret:
                # Sauvegarde de l'image de test
                test_image_path = "camera_test.jpg"
                cv2.imwrite(test_image_path, frame)
                
                # Informations sur l'image
                height, width = frame.shape[:2]
                
                self.camera.release()
                
                return TestResult(
                    component="Caméra CSI",
                    status=TestStatus.PASSED,
                    message=f"Image capturée: {width}x{height} pixels",
                    data={"width": width, "height": height, "test_image": test_image_path},
                    duration=time.time() - start_time
                )
            else:
                self.camera.release()
                return TestResult(
                    component="Caméra CSI",
                    status=TestStatus.FAILED,
                    message="Impossible de capturer une image",
                    duration=time.time() - start_time
                )
                
        except Exception as e:
            return TestResult(
                component="Caméra CSI",
                status=TestStatus.FAILED,
                message=f"Erreur caméra: {str(e)}",
                duration=time.time() - start_time
            )
    
    def test_display(self) -> TestResult:
        """Test de l'écran TFT 1.8" SPI"""
        start_time = time.time()
        
        try:
            # Configuration SPI pour l'écran
            spi = spidev.SpiDev()
            spi.open(0, 0)
            spi.max_speed_hz = 32000000
            
            # Configuration des pins
            ce_pin = self.pin_config["spi_ce"]
            dc_pin = self.pin_config["spi_dc"]
            rst_pin = self.pin_config["spi_rst"]
            
            GPIO.setup(ce_pin, GPIO.OUT)
            GPIO.setup(dc_pin, GPIO.OUT)
            GPIO.setup(rst_pin, GPIO.OUT)
            
            # Reset de l'écran
            GPIO.output(rst_pin, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(rst_pin, GPIO.HIGH)
            time.sleep(0.1)
            
            # Test d'affichage simple
            self._display_test_pattern(spi, ce_pin, dc_pin)
            
            spi.close()
            
            return TestResult(
                component="Écran TFT 1.8\"",
                status=TestStatus.PASSED,
                message="Écran TFT testé avec succès",
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                component="Écran TFT 1.8\"",
                status=TestStatus.FAILED,
                message=f"Erreur écran TFT: {str(e)}",
                duration=time.time() - start_time
            )
    
    def _display_test_pattern(self, spi, ce_pin, dc_pin):
        """Affiche un motif de test sur l'écran"""
        # Pattern de test simple (bandes colorées)
        test_data = [0xFF] * 128 * 160 * 2  # 128x160 pixels, 16-bit color
        
        GPIO.output(ce_pin, GPIO.LOW)
        GPIO.output(dc_pin, GPIO.HIGH)  # Mode données
        spi.writebytes(test_data)
        GPIO.output(ce_pin, GPIO.HIGH)
    
    def test_mosfet(self) -> TestResult:
        """Test du MOSFET"""
        start_time = time.time()
        
        try:
            mosfet_pin = self.pin_config["mosfet_pin"]
            GPIO.setup(mosfet_pin, GPIO.OUT)
            
            # Test d'activation/désactivation
            GPIO.output(mosfet_pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(mosfet_pin, GPIO.LOW)
            
            return TestResult(
                component="MOSFET",
                status=TestStatus.PASSED,
                message="MOSFET testé avec succès (activation/désactivation)",
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                component="MOSFET",
                status=TestStatus.FAILED,
                message=f"Erreur MOSFET: {str(e)}",
                duration=time.time() - start_time
            )
    
    def test_fans(self) -> TestResult:
        """Test des 4 ventilateurs sur le même pin"""
        start_time = time.time()
        
        try:
            fans_pin = self.pin_config["fans_pin"]
            GPIO.setup(fans_pin, GPIO.OUT)
            
            # Test PWM pour contrôle de vitesse des 4 ventilateurs
            self.fan_pwm = GPIO.PWM(fans_pin, 25000)  # 25kHz pour ventilateurs
            self.fan_pwm.start(0)
            
            # Test de différentes vitesses
            speeds = [25, 50, 75, 100, 75, 50, 25, 0]
            
            for speed in speeds:
                self.fan_pwm.ChangeDutyCycle(speed)
                time.sleep(0.5)  # 500ms par vitesse
            
            self.fan_pwm.stop()
            
            return TestResult(
                component="Ventilateurs (4x)",
                status=TestStatus.PASSED,
                message="4 ventilateurs testés avec succès (contrôle PWM 0-100%)",
                data={"tested_speeds": speeds, "fan_count": 4},
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                component="Ventilateurs (4x)",
                status=TestStatus.FAILED,
                message=f"Erreur ventilateurs: {str(e)}",
                duration=time.time() - start_time
            )
    
    def test_adc(self) -> TestResult:
        """Test du convertisseur ADC"""
        start_time = time.time()
        
        try:
            # Configuration SPI pour ADC
            spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
            cs = digitalio.DigitalInOut(board.D22)
            adc = MCP.MCP3008(spi, cs)
            
            # Test de plusieurs canaux
            channels = [AnalogIn(adc, MCP.P0), AnalogIn(adc, MCP.P1), AnalogIn(adc, MCP.P2)]
            readings = []
            
            for i, channel in enumerate(channels):
                voltage = channel.voltage
                raw_value = channel.value
                readings.append({
                    "channel": i,
                    "voltage": voltage,
                    "raw_value": raw_value
                })
            
            return TestResult(
                component="Convertisseur ADC",
                status=TestStatus.PASSED,
                message=f"ADC testé sur {len(channels)} canaux",
                data={"readings": readings},
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                component="Convertisseur ADC",
                status=TestStatus.FAILED,
                message=f"Erreur ADC: {str(e)}",
                duration=time.time() - start_time
            )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests"""
        print("🔧 Démarrage des tests de composants Alimante")
        print("=" * 50)
        
        tests = [
            self.test_gpio_setup,
            self.test_dht22,
            self.test_mq2_sensor,
            self.test_servo,
            self.test_transducers,
            self.test_camera,
            self.test_display,
            self.test_mosfet,
            self.test_fans,
            self.test_adc
        ]
        
        for test_func in tests:
            result = test_func()
            self._add_result(result)
            time.sleep(0.5)  # Pause entre les tests
        
        return self._generate_summary()
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Génère un résumé des tests"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAILED])
        skipped_tests = len([r for r in self.results if r.status == TestStatus.SKIPPED])
        
        total_duration = sum(r.duration for r in self.results)
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "results": [vars(r) for r in self.results]
        }
        
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 50)
        print(f"Tests totaux: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"⚠️  Ignorés: {skipped_tests}")
        print(f"📈 Taux de réussite: {summary['success_rate']:.1f}%")
        print(f"⏱️  Durée totale: {total_duration:.2f}s")
        
        return summary
    
    def save_results(self, filename: str = "test_results.json") -> None:
        """Sauvegarde les résultats dans un fichier JSON"""
        summary = self._generate_summary()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Résultats sauvegardés dans: {filename}")
    
    def cleanup(self) -> None:
        """Nettoie les ressources"""
        try:
            if self.servo:
                self.servo.stop()
            if self.fan_pwm:
                self.fan_pwm.stop()
            if self.camera:
                self.camera.release()
            if self.gpio_initialized:
                GPIO.cleanup()
            print("🧹 Nettoyage terminé")
        except Exception as e:
            print(f"⚠️  Erreur lors du nettoyage: {e}")


def main():
    """Fonction principale"""
    tester = ComponentTester()
    
    try:
        # Exécution des tests
        summary = tester.run_all_tests()
        
        # Sauvegarde des résultats
        tester.save_results()
        
        # Affichage du statut final
        if summary["failed"] == 0:
            print("\n🎉 Tous les tests sont passés avec succès!")
        else:
            print(f"\n⚠️  {summary['failed']} test(s) ont échoué. Vérifiez les composants.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n💥 Erreur critique: {e}")
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main() 