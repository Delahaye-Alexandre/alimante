#!/usr/bin/env python3
"""
Test pour l'écran SPI ST7735
Vérification du fonctionnement de l'écran avec tests complets
"""

import RPi.GPIO as GPIO
import time
import sys
import signal
import random
from config_alimante import get_gpio_config

# Import pour l'écran ST7735 (nécessite l'installation de la librairie)
try:
    import ST7735
    from PIL import Image, ImageDraw, ImageFont
    ST7735_AVAILABLE = True
except ImportError:
    ST7735_AVAILABLE = False
    print("⚠️  Librairie ST7735 non disponible. Installation requise:")
    print("   pip install ST7735 Pillow")

class EcranSPITest:
    def __init__(self):
        """Initialise le testeur d'écran SPI"""
        self.config = get_gpio_config()
        self.display = None
        self.is_initialized = False
        
        # Configuration des pins depuis config_alimante.py
        self.reset_pin = self.config['DISPLAY']['RESET_PIN']
        self.a0_pin = self.config['DISPLAY']['A0_PIN']
        self.cs_pin = self.config['DISPLAY']['CS_PIN']
        self.sda_pin = self.config['DISPLAY']['SDA_PIN']
        self.scl_pin = self.config['DISPLAY']['SCL_PIN']
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Gestionnaire de signal pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise l'écran SPI"""
        if not ST7735_AVAILABLE:
            print("❌ Impossible d'initialiser l'écran: librairie ST7735 manquante")
            return False
        
        try:
            # Configuration des pins de contrôle
            GPIO.setup(self.reset_pin, GPIO.OUT)
            GPIO.setup(self.a0_pin, GPIO.OUT)
            GPIO.setup(self.cs_pin, GPIO.OUT)
            
            # Initialisation de l'écran ST7735
            self.display = ST7735.ST7735(
                port=0,
                cs=self.cs_pin,
                dc=self.a0_pin,
                rst=self.reset_pin,
                spi_speed_hz=4000000  # 4MHz pour stabilité
            )
            
            # Démarrage de l'écran
            self.display.begin()
            self.is_initialized = True
            print("✅ Écran SPI ST7735 initialisé avec succès")
            print(f"   📌 Pins: RST={self.reset_pin}, A0={self.a0_pin}, CS={self.cs_pin}")
            print(f"   📌 SPI: SDA={self.sda_pin}, SCL={self.scl_pin}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de l'écran: {e}")
            return False
    
    def test_initialisation(self):
        """Test 1: Vérification de l'initialisation"""
        print("\n🔧 TEST 1: Initialisation de l'écran")
        print("-" * 40)
        
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        try:
            # Test de création d'image
            image = Image.new('RGB', (self.display.width, self.display.height), color=(0, 0, 0))
            self.display.display(image)
            print("✅ Écran initialisé et prêt")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du test d'initialisation: {e}")
            return False
    
    def test_couleurs_base(self):
        """Test 2: Affichage des couleurs de base"""
        print("\n🎨 TEST 2: Couleurs de base")
        print("-" * 40)
        
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        couleurs = [
            ("Noir", (0, 0, 0)),
            ("Blanc", (255, 255, 255)),
            ("Rouge", (255, 0, 0)),
            ("Vert", (0, 255, 0)),
            ("Bleu", (0, 0, 255)),
            ("Jaune", (255, 255, 0)),
            ("Cyan", (0, 255, 255)),
            ("Magenta", (255, 0, 255))
        ]
        
        try:
            for nom, couleur in couleurs:
                print(f"   Affichage {nom}...")
                image = Image.new('RGB', (self.display.width, self.display.height), color=couleur)
                self.display.display(image)
                time.sleep(1)
            
            print("✅ Test des couleurs de base réussi")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du test des couleurs: {e}")
            return False
    
    def test_formes_geometriques(self):
        """Test 3: Affichage de formes géométriques"""
        print("\n📐 TEST 3: Formes géométriques")
        print("-" * 40)
        
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        try:
            # Création d'une image avec formes
            image = Image.new('RGB', (self.display.width, self.display.height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Rectangle
            draw.rectangle([10, 10, 50, 30], fill=(255, 0, 0), outline=(255, 255, 255))
            
            # Cercle
            draw.ellipse([70, 10, 110, 50], fill=(0, 255, 0), outline=(255, 255, 255))
            
            # Ligne
            draw.line([(10, 70), (100, 70)], fill=(0, 0, 255), width=3)
            
            # Triangle (polygone)
            draw.polygon([(60, 80), (80, 100), (40, 100)], fill=(255, 255, 0))
            
            self.display.display(image)
            print("✅ Formes géométriques affichées")
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test des formes: {e}")
            return False
    
    def test_texte(self):
        """Test 4: Affichage de texte"""
        print("\n📝 TEST 4: Affichage de texte")
        print("-" * 40)
        
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        try:
            # Création d'une image avec texte
            image = Image.new('RGB', (self.display.width, self.display.height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Essayer d'utiliser une police par défaut
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Texte de test
            text_lines = [
                "ALIMANTE",
                "Test SPI",
                "ST7735 OK",
                "GPIO Test"
            ]
            
            y_position = 10
            for line in text_lines:
                if font:
                    draw.text((10, y_position), line, fill=(255, 255, 255), font=font)
                else:
                    draw.text((10, y_position), line, fill=(255, 255, 255))
                y_position += 20
            
            self.display.display(image)
            print("✅ Texte affiché avec succès")
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test du texte: {e}")
            return False
    
    def test_animation(self):
        """Test 5: Animation simple"""
        print("\n🎬 TEST 5: Animation")
        print("-" * 40)
        
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        try:
            print("   Animation de barre de progression...")
            
            for progress in range(0, 101, 5):
                image = Image.new('RGB', (self.display.width, self.display.height), color=(0, 0, 0))
                draw = ImageDraw.Draw(image)
                
                # Barre de progression
                bar_width = int((self.display.width - 20) * progress / 100)
                draw.rectangle([10, 10, 10 + bar_width, 30], fill=(0, 255, 0))
                draw.rectangle([10, 10, self.display.width - 10, 30], outline=(255, 255, 255))
                
                # Texte de pourcentage
                try:
                    font = ImageFont.load_default()
                    draw.text((10, 40), f"{progress}%", fill=(255, 255, 255), font=font)
                except:
                    draw.text((10, 40), f"{progress}%", fill=(255, 255, 255))
                
                self.display.display(image)
                time.sleep(0.1)
            
            print("✅ Animation terminée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test d'animation: {e}")
            return False
    
    def test_performance(self):
        """Test 6: Test de performance"""
        print("\n⚡ TEST 6: Performance")
        print("-" * 40)
        
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        try:
            print("   Test de rafraîchissement rapide...")
            
            start_time = time.time()
            frames = 0
            
            # Test de 50 frames avec couleurs aléatoires
            for i in range(50):
                # Couleur aléatoire
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                image = Image.new('RGB', (self.display.width, self.display.height), color=color)
                self.display.display(image)
                frames += 1
            
            end_time = time.time()
            duration = end_time - start_time
            fps = frames / duration
            
            print(f"✅ Performance: {fps:.1f} FPS sur {frames} frames")
            print(f"   Durée: {duration:.2f}s")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test de performance: {e}")
            return False
    
    def test_complet(self):
        """Exécute tous les tests"""
        print("=" * 60)
        print("🔧 TEST COMPLET ÉCRAN SPI ST7735")
        print("=" * 60)
        
        if not self.initialize():
            print("❌ Impossible de continuer sans initialisation")
            return False
        
        tests = [
            ("Initialisation", self.test_initialisation),
            ("Couleurs de base", self.test_couleurs_base),
            ("Formes géométriques", self.test_formes_geometriques),
            ("Affichage texte", self.test_texte),
            ("Animation", self.test_animation),
            ("Performance", self.test_performance)
        ]
        
        results = []
        
        for nom_test, fonction_test in tests:
            print(f"\n🔄 Exécution: {nom_test}")
            try:
                result = fonction_test()
                results.append((nom_test, result))
                if result:
                    print(f"✅ {nom_test}: RÉUSSI")
                else:
                    print(f"❌ {nom_test}: ÉCHEC")
            except Exception as e:
                print(f"❌ {nom_test}: ERREUR - {e}")
                results.append((nom_test, False))
        
        # Résumé des résultats
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        reussis = sum(1 for _, result in results if result)
        total = len(results)
        
        for nom_test, result in results:
            status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
            print(f"   {nom_test}: {status}")
        
        print(f"\n📈 Résultat global: {reussis}/{total} tests réussis")
        
        if reussis == total:
            print("🎉 Tous les tests sont passés avec succès!")
        else:
            print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        
        return reussis == total
    
    def menu_interactif(self):
        """Menu interactif pour tests individuels"""
        if not self.initialize():
            print("❌ Impossible d'initialiser l'écran")
            return
        
        while True:
            print("\n" + "=" * 40)
            print("MENU DE TEST ÉCRAN SPI")
            print("=" * 40)
            print("1. Test d'initialisation")
            print("2. Test des couleurs de base")
            print("3. Test des formes géométriques")
            print("4. Test d'affichage de texte")
            print("5. Test d'animation")
            print("6. Test de performance")
            print("7. Test complet")
            print("0. Quitter")
            print("=" * 40)
            
            choice = input("Votre choix (0-7): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.test_initialisation()
            elif choice == "2":
                self.test_couleurs_base()
            elif choice == "3":
                self.test_formes_geometriques()
            elif choice == "4":
                self.test_texte()
            elif choice == "5":
                self.test_animation()
            elif choice == "6":
                self.test_performance()
            elif choice == "7":
                self.test_complet()
            else:
                print("❌ Choix invalide")
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self.display:
            # Effacer l'écran
            try:
                image = Image.new('RGB', (self.display.width, self.display.height), color=(0, 0, 0))
                self.display.display(image)
            except:
                pass
        
        GPIO.cleanup()
        self.is_initialized = False
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du programme...")
        self.cleanup()
        sys.exit(0)

def main():
    """Fonction principale"""
    print("🔧 TESTEUR ÉCRAN SPI ST7735")
    print("Configuration depuis config_alimante.py")
    
    if not ST7735_AVAILABLE:
        print("\n❌ Librairie ST7735 non disponible")
        print("Installation requise:")
        print("   pip install ST7735 Pillow")
        return
    
    testeur = EcranSPITest()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--auto":
            # Mode automatique
            testeur.test_complet()
        else:
            # Mode interactif
            testeur.menu_interactif()
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        testeur.cleanup()
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
