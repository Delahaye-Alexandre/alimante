#!/usr/bin/env python3
"""
Test interactif de tous les composants sur GPIO 4
Guide l'utilisateur pour tester chaque composant un par un
"""

import RPi.GPIO as GPIO
import time
import sys

class ComposantTester:
    """Classe pour tester les composants sur GPIO 4"""
    
    def __init__(self):
        self.GPIO_PIN = 4
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
    def nettoyer(self):
        """Nettoie les GPIO"""
        GPIO.cleanup()
        
    def test_led(self):
        """Test d'une LED"""
        print("\n🔴 Test LED")
        print("=" * 30)
        print("📋 Instructions:")
        print("   1. Connectez une LED sur GPIO 4")
        print("   2. LED + → GPIO 4")
        print("   3. LED - → GND (via résistance 220Ω)")
        print("   4. Appuyez sur Entrée quand c'est fait")
        
        input("✅ LED connectée ? (Entrée pour continuer): ")
        
        try:
            GPIO.setup(self.GPIO_PIN, GPIO.OUT)
            
            print("🔄 Test en cours...")
            for i in range(5):
                GPIO.output(self.GPIO_PIN, GPIO.HIGH)
                print(f"   Cycle {i+1}: LED ON")
                time.sleep(0.5)
                
                GPIO.output(self.GPIO_PIN, GPIO.LOW)
                print(f"   Cycle {i+1}: LED OFF")
                time.sleep(0.5)
            
            result = input("✅ La LED clignote-t-elle ? (o/n): ").lower()
            return result == 'o'
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
            
    def test_bouton(self):
        """Test d'un bouton"""
        print("\n🔘 Test Bouton")
        print("=" * 30)
        print("📋 Instructions:")
        print("   1. Connectez un bouton sur GPIO 4")
        print("   2. Bouton → GPIO 4")
        print("   3. Bouton → GND")
        print("   4. Résistance 10kΩ entre GPIO 4 et 3.3V (pull-up)")
        print("   5. Appuyez sur Entrée quand c'est fait")
        
        input("✅ Bouton connecté ? (Entrée pour continuer): ")
        
        try:
            GPIO.setup(self.GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            print("🔄 Test en cours...")
            print("   Appuyez sur le bouton (Ctrl+C pour arrêter)")
            
            count = 0
            start_time = time.time()
            
            while count < 5 and (time.time() - start_time) < 30:
                if GPIO.input(self.GPIO_PIN) == GPIO.LOW:
                    print(f"   ✅ Bouton pressé ! (Compteur: {count+1})")
                    count += 1
                    time.sleep(0.5)  # Anti-rebond
                    
            return count > 0
            
        except KeyboardInterrupt:
            print("\n⏹️ Test arrêté")
            return False
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
            
    def test_relais(self):
        """Test d'un relais"""
        print("\n⚡ Test Relais")
        print("=" * 30)
        print("📋 Instructions:")
        print("   1. Connectez un relais sur GPIO 4")
        print("   2. Relais IN → GPIO 4")
        print("   3. Relais VCC → 5V")
        print("   4. Relais GND → GND")
        print("   5. Appuyez sur Entrée quand c'est fait")
        
        input("✅ Relais connecté ? (Entrée pour continuer): ")
        
        try:
            GPIO.setup(self.GPIO_PIN, GPIO.OUT)
            
            print("🔄 Test en cours...")
            for i in range(3):
                GPIO.output(self.GPIO_PIN, GPIO.HIGH)
                print(f"   Cycle {i+1}: Relais ON (cliquez ?)")
                time.sleep(1)
                
                GPIO.output(self.GPIO_PIN, GPIO.LOW)
                print(f"   Cycle {i+1}: Relais OFF")
                time.sleep(1)
            
            result = input("✅ Le relais clique-t-il ? (o/n): ").lower()
            return result == 'o'
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
            
    def test_servo(self):
        """Test d'un servomoteur"""
        print("\n⚙️ Test Servomoteur")
        print("=" * 30)
        print("📋 Instructions:")
        print("   1. Connectez un servomoteur sur GPIO 4")
        print("   2. Servo Signal → GPIO 4")
        print("   3. Servo VCC → 5V")
        print("   4. Servo GND → GND")
        print("   5. Appuyez sur Entrée quand c'est fait")
        
        input("✅ Servomoteur connecté ? (Entrée pour continuer): ")
        
        try:
            GPIO.setup(self.GPIO_PIN, GPIO.OUT)
            servo = GPIO.PWM(self.GPIO_PIN, 50)  # 50Hz
            servo.start(0)
            
            print("🔄 Test en cours...")
            for i in range(3):
                print(f"   Cycle {i+1}: Position 0°")
                servo.ChangeDutyCycle(2.5)  # 0°
                time.sleep(1)
                
                print(f"   Cycle {i+1}: Position 90°")
                servo.ChangeDutyCycle(7.5)  # 90°
                time.sleep(1)
                
                print(f"   Cycle {i+1}: Position 180°")
                servo.ChangeDutyCycle(12.5)  # 180°
                time.sleep(1)
            
            servo.stop()
            result = input("✅ Le servo bouge-t-il ? (o/n): ").lower()
            return result == 'o'
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
            
    def test_buzzer(self):
        """Test d'un buzzer"""
        print("\n🔊 Test Buzzer")
        print("=" * 30)
        print("📋 Instructions:")
        print("   1. Connectez un buzzer sur GPIO 4")
        print("   2. Buzzer + → GPIO 4")
        print("   3. Buzzer - → GND")
        print("   4. Appuyez sur Entrée quand c'est fait")
        
        input("✅ Buzzer connecté ? (Entrée pour continuer): ")
        
        try:
            GPIO.setup(self.GPIO_PIN, GPIO.OUT)
            
            print("🔄 Test en cours...")
            for i in range(3):
                print(f"   Cycle {i+1}: Buzzer ON")
                GPIO.output(self.GPIO_PIN, GPIO.HIGH)
                time.sleep(0.5)
                
                print(f"   Cycle {i+1}: Buzzer OFF")
                GPIO.output(self.GPIO_PIN, GPIO.LOW)
                time.sleep(0.5)
            
            result = input("✅ Le buzzer fait-il du bruit ? (o/n): ").lower()
            return result == 'o'
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
            
    def test_capteur_analogique(self):
        """Test d'un capteur analogique (LDR, etc.)"""
        print("\n📊 Test Capteur Analogique")
        print("=" * 30)
        print("📋 Instructions:")
        print("   1. Connectez un capteur analogique sur GPIO 4")
        print("   2. Capteur → GPIO 4")
        print("   3. Résistance pull-up entre GPIO 4 et 3.3V")
        print("   4. Appuyez sur Entrée quand c'est fait")
        
        input("✅ Capteur connecté ? (Entrée pour continuer): ")
        
        try:
            GPIO.setup(self.GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            print("🔄 Test en cours...")
            print("   Modifiez l'environnement du capteur")
            
            for i in range(10):
                state = GPIO.input(self.GPIO_PIN)
                print(f"   Lecture {i+1}: {'HIGH' if state else 'LOW'}")
                time.sleep(1)
            
            result = input("✅ Les valeurs changent-elles ? (o/n): ").lower()
            return result == 'o'
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False

def main():
    """Programme principal"""
    print("🧪 Test Interactif des Composants")
    print("=" * 50)
    print("Ce programme vous guide pour tester chaque composant")
    print("sur le GPIO 4 du Raspberry Pi.")
    print()
    
    tester = ComposantTester()
    resultats = {}
    
    # Liste des tests disponibles
    tests = [
        ("LED", tester.test_led),
        ("Bouton", tester.test_bouton),
        ("Relais", tester.test_relais),
        ("Servomoteur", tester.test_servo),
        ("Buzzer", tester.test_buzzer),
        ("Capteur Analogique", tester.test_capteur_analogique)
    ]
    
    print("📋 Composants à tester:")
    for i, (nom, _) in enumerate(tests, 1):
        print(f"   {i}. {nom}")
    print()
    
    # Tests interactifs
    for nom, test_func in tests:
        print(f"\n🎯 Test: {nom}")
        print("-" * 30)
        
        choix = input(f"Voulez-vous tester {nom} ? (o/n): ").lower()
        if choix == 'o':
            try:
                resultat = test_func()
                resultats[nom] = resultat
                print(f"   Résultat: {'✅ SUCCÈS' if resultat else '❌ ÉCHEC'}")
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                resultats[nom] = False
        else:
            print(f"   ⏭️ Test {nom} ignoré")
            resultats[nom] = None
    
    # Résumé final
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    for nom, resultat in resultats.items():
        if resultat is None:
            print(f"   {nom}: ⏭️ IGNORÉ")
        elif resultat:
            print(f"   {nom}: ✅ SUCCÈS")
        else:
            print(f"   {nom}: ❌ ÉCHEC")
    
    # Statistiques
    total = len([r for r in resultats.values() if r is not None])
    succes = len([r for r in resultats.values() if r is True])
    
    print(f"\n📈 Statistiques:")
    print(f"   Tests effectués: {total}")
    print(f"   Succès: {succes}")
    print(f"   Échecs: {total - succes}")
    
    if total > 0:
        taux = (succes / total) * 100
        print(f"   Taux de succès: {taux:.1f}%")
    
    print("\n🎉 Test terminé !")
    
    # Nettoyage
    tester.nettoyer()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Test arrêté par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)
