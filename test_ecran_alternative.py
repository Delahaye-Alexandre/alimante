#!/usr/bin/env python3
"""
Test alternatif de l'écran ST7735
Utilise une approche différente pour éviter les conflits GPIO
"""

import time
import sys
import signal
from config_alimante import get_gpio_config

# Import pour l'écran ST7735
try:
    import st7735
    from PIL import Image, ImageDraw, ImageFont
    ST7735_AVAILABLE = True
    print("✅ Librairies ST7735 et PIL importées avec succès")
except Exception as e:
    ST7735_AVAILABLE = False
    print(f"⚠️  Erreur lors de l'import: {e}")
    print("⚠️  Librairie ST7735 non disponible. Installation requise:")
    print("   pip install st7735 Pillow")

class EcranTestAlternative:
    def __init__(self):
        """Initialise le testeur d'écran alternatif"""
        self.config = get_gpio_config()
        self.display = None
        self.is_initialized = False
        
        # Configuration des pins depuis config_alimante.py
        self.reset_pin = self.config['DISPLAY']['RESET_PIN']
        self.a0_pin = self.config['DISPLAY']['A0_PIN']
        
        # Gestionnaire de signal pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialise l'écran SPI avec approche alternative"""
        if not ST7735_AVAILABLE:
            print("❌ Impossible d'initialiser l'écran: librairie ST7735 manquante")
            return False
        
        try:
            print("🔧 Initialisation alternative de l'écran ST7735...")
            print(f"   RST={self.reset_pin}, A0={self.a0_pin}")
            
            # Attendre un peu pour éviter les conflits
            time.sleep(1)
            
            # Initialisation de l'écran ST7735
            self.display = st7735.ST7735(
                port=0,
                cs=0,  # Utilise spidev0.0
                dc=self.a0_pin,
                rst=self.reset_pin,
                spi_speed_hz=2000000,  # Fréquence réduite pour stabilité
                rotation=270  # Rotation de 270°
            )
            
            print("🔧 Démarrage de l'écran...")
            self.display.begin()
            self.is_initialized = True
            
            print("✅ Écran SPI ST7735 initialisé avec succès")
            print(f"   📐 Résolution: {self.display.width}x{self.display.height}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            print(f"   Type d'erreur: {type(e).__name__}")
            
            # Suggestions de résolution
            print("\n💡 Suggestions de résolution:")
            print("   1. Redémarrer le Raspberry Pi: sudo reboot")
            print("   2. Vérifier les conflits: python3 diagnostic_gpio.py")
            print("   3. Nettoyer les pins: python3 cleanup_gpio.py")
            
            return False
    
    def test_couleurs(self):
        """Test des couleurs de base"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        print("\n🎨 Test des couleurs...")
        
        couleurs = [
            ("Rouge", (0, 0, 255)),      # BGR
            ("Vert", (0, 255, 0)),       # BGR
            ("Bleu", (255, 0, 0)),       # BGR
            ("Jaune", (0, 255, 255)),    # BGR
            ("Cyan", (255, 255, 0)),     # BGR
            ("Magenta", (255, 0, 255)),  # BGR
            ("Blanc", (255, 255, 255)),
            ("Noir", (0, 0, 0))
        ]
        
        try:
            for nom, couleur in couleurs:
                print(f"   Affichage {nom}...")
                image = Image.new('RGB', (self.display.width, self.display.height), color=couleur)
                
                # Ajouter un cadre blanc
                draw = ImageDraw.Draw(image)
                draw.rectangle([0, 0, self.display.width-1, self.display.height-1], 
                             outline=(255, 255, 255), width=2)
                
                # Ajouter le nom de la couleur
                try:
                    font = ImageFont.load_default()
                    text_bbox = draw.textbbox((0, 0), nom, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    x = (self.display.width - text_width) // 2
                    y = (self.display.height - 20) // 2
                    draw.text((x, y), nom, fill=(255, 255, 255), font=font)
                except:
                    x = (self.display.width - len(nom) * 6) // 2
                    y = (self.display.height - 20) // 2
                    draw.text((x, y), nom, fill=(255, 255, 255))
                
                self.display.display(image)
                time.sleep(2)
            
            print("✅ Test des couleurs terminé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test des couleurs: {e}")
            return False
    
    def test_formes(self):
        """Test des formes géométriques"""
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        print("\n📐 Test des formes...")
        
        try:
            image = Image.new('RGB', (self.display.width, self.display.height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Cadre blanc
            draw.rectangle([0, 0, self.display.width-1, self.display.height-1], 
                         outline=(255, 255, 255), width=2)
            
            # Formes dans chaque coin
            draw.rectangle([5, 5, 45, 25], fill=(0, 0, 255), outline=(255, 255, 255))  # Rouge
            draw.ellipse([self.display.width-45, 5, self.display.width-5, 45], 
                        fill=(0, 255, 0), outline=(255, 255, 255))  # Vert
            draw.polygon([(30, self.display.height-30), (50, self.display.height-10), 
                         (10, self.display.height-10)], fill=(0, 255, 255))  # Jaune
            draw.rectangle([self.display.width-40, self.display.height-30, 
                          self.display.width-10, self.display.height-10], 
                         fill=(255, 0, 255), outline=(255, 255, 255))  # Magenta
            
            # Ligne diagonale
            draw.line([(0, 0), (self.display.width-1, self.display.height-1)], 
                     fill=(255, 255, 0), width=2)  # Cyan
            
            self.display.display(image)
            print("✅ Formes affichées")
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test des formes: {e}")
            return False
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self.display:
            try:
                image = Image.new('RGB', (self.display.width, self.display.height), color=(0, 0, 0))
                self.display.display(image)
            except:
                pass
        
        self.is_initialized = False
        print("🧹 Ressources nettoyées")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre"""
        print("\n🛑 Arrêt du programme...")
        self.cleanup()
        sys.exit(0)
    
    def run_tests(self):
        """Exécute tous les tests"""
        print("🔧 TEST ALTERNATIF ÉCRAN ST7735")
        print("=" * 50)
        
        if not self.initialize():
            print("❌ Impossible de continuer sans initialisation")
            return False
        
        tests = [
            ("Couleurs", self.test_couleurs),
            ("Formes", self.test_formes)
        ]
        
        results = []
        for nom, test_func in tests:
            print(f"\n🔄 Test: {nom}")
            try:
                result = test_func()
                results.append((nom, result))
                if result:
                    print(f"✅ {nom}: RÉUSSI")
                else:
                    print(f"❌ {nom}: ÉCHEC")
            except Exception as e:
                print(f"❌ {nom}: ERREUR - {e}")
                results.append((nom, False))
        
        # Résumé
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ")
        print("=" * 50)
        
        reussis = sum(1 for _, result in results if result)
        total = len(results)
        
        for nom, result in results:
            status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
            print(f"   {nom}: {status}")
        
        print(f"\n📈 Résultat: {reussis}/{total} tests réussis")
        
        if reussis == total:
            print("🎉 Tous les tests sont passés!")
        else:
            print("⚠️  Certains tests ont échoué")
        
        return reussis == total

def main():
    """Fonction principale"""
    testeur = EcranTestAlternative()
    
    try:
        testeur.run_tests()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        testeur.cleanup()
        print("👋 Test terminé!")

if __name__ == "__main__":
    main()
