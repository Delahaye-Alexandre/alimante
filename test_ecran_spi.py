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
import threading
from config_alimante import get_gpio_config

# Import pour l'écran ST7735 (nécessite l'installation de la librairie)
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

class EncodeurRotatif:
    def __init__(self, clk_pin, dt_pin, sw_pin):
        """Initialise l'encodeur rotatif"""
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.position = 0
        self.last_clk_state = 0
        self.button_pressed = False
        self.running = False
        self.callback_rotation = None
        self.callback_button = None
        
        # Configuration des pins
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Configuration des interruptions
        GPIO.add_event_detect(self.clk_pin, GPIO.BOTH, callback=self._clk_callback, bouncetime=2)
        GPIO.add_event_detect(self.dt_pin, GPIO.BOTH, callback=self._dt_callback, bouncetime=2)
        GPIO.add_event_detect(self.sw_pin, GPIO.FALLING, callback=self._button_callback, bouncetime=200)
        
        self.last_clk_state = GPIO.input(self.clk_pin)
        self.running = True
        
    def _clk_callback(self, channel):
        """Callback pour le pin CLK"""
        if not self.running:
            return
            
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        if clk_state != self.last_clk_state:
            if dt_state != clk_state:
                self.position += 1
                if self.callback_rotation:
                    self.callback_rotation(1)  # Rotation horaire
            else:
                self.position -= 1
                if self.callback_rotation:
                    self.callback_rotation(-1)  # Rotation anti-horaire
                    
        self.last_clk_state = clk_state
    
    def _dt_callback(self, channel):
        """Callback pour le pin DT"""
        pass  # Géré dans _clk_callback
    
    def _button_callback(self, channel):
        """Callback pour le bouton"""
        if not self.running:
            return
            
        self.button_pressed = True
        if self.callback_button:
            self.callback_button()
    
    def set_rotation_callback(self, callback):
        """Définit le callback pour la rotation"""
        self.callback_rotation = callback
    
    def set_button_callback(self, callback):
        """Définit le callback pour le bouton"""
        self.callback_button = callback
    
    def get_position(self):
        """Retourne la position actuelle"""
        return self.position
    
    def reset_position(self):
        """Remet la position à zéro"""
        self.position = 0
    
    def is_button_pressed(self):
        """Vérifie si le bouton a été pressé"""
        if self.button_pressed:
            self.button_pressed = False
            return True
        return False
    
    def cleanup(self):
        """Nettoie les ressources"""
        self.running = False
        GPIO.remove_event_detect(self.clk_pin)
        GPIO.remove_event_detect(self.dt_pin)
        GPIO.remove_event_detect(self.sw_pin)

class EcranSPITest:
    def __init__(self):
        """Initialise le testeur d'écran SPI"""
        self.config = get_gpio_config()
        self.display = None
        self.is_initialized = False
        self.encoder = None
        
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
    
    def force_cleanup_gpio(self):
        """Force le nettoyage des pins GPIO"""
        try:
            print("🧹 Nettoyage forcé des pins GPIO...")
            GPIO.cleanup()
            time.sleep(0.5)  # Attendre un peu
        except:
            pass
    
    def initialize(self):
        """Initialise l'écran SPI"""
        if not ST7735_AVAILABLE:
            print("❌ Impossible d'initialiser l'écran: librairie ST7735 manquante")
            return False
        
        # Nettoyage préventif
        self.force_cleanup_gpio()
        
        try:
            print(f"🔧 Initialisation de l'écran ST7735...")
            print(f"   Port SPI: 0, CS: 0, DC: {self.a0_pin}, RST: {self.reset_pin}")
            
            # Initialisation de l'écran ST7735 SANS configurer les pins GPIO d'abord
            # La librairie st7735 gère elle-même les pins
            self.display = st7735.ST7735(
                port=0,
                cs=0,  # Utilise spidev0.0
                dc=self.a0_pin,
                rst=self.reset_pin,
                spi_speed_hz=4000000,  # 4MHz pour stabilité
                rotation=270  # Rotation de 270° (90° + 180° = 270°)
            )
            
            print(f"🔧 Démarrage de l'écran...")
            # Démarrage de l'écran
            self.display.begin()
            self.is_initialized = True
            print("✅ Écran SPI ST7735 initialisé avec succès")
            print(f"   📌 Pins: RST={self.reset_pin}, A0={self.a0_pin}, CS={self.cs_pin}")
            print(f"   📌 SPI: SDA={self.sda_pin}, SCL={self.scl_pin}")
            print(f"   📐 Résolution: {self.display.width}x{self.display.height} (rotation 180°)")
            
            # Initialisation de l'encodeur rotatif
            self.initialize_encoder()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de l'écran: {e}")
            print(f"   Type d'erreur: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_encoder(self):
        """Initialise l'encodeur rotatif"""
        try:
            # Attendre un peu pour que l'écran soit complètement initialisé
            time.sleep(1)
            
            encoder_config = self.config['ENCODER']
            self.encoder = EncodeurRotatif(
                clk_pin=encoder_config['CLK_PIN'],
                dt_pin=encoder_config['DT_PIN'],
                sw_pin=encoder_config['SW_PIN']
            )
            print("✅ Encodeur rotatif initialisé")
            print(f"   📌 Pins: CLK={encoder_config['CLK_PIN']}, DT={encoder_config['DT_PIN']}, SW={encoder_config['SW_PIN']}")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de l'encodeur: {e}")
            print("   L'écran fonctionnera sans l'encodeur")
            self.encoder = None
    
    def test_encoder_interactif(self):
        """Test 7: Test interactif avec l'encodeur rotatif"""
        print("\n🎛️ TEST 7: Contrôle avec encodeur rotatif")
        print("-" * 40)
        
        if not self.is_initialized:
            print("❌ Écran non initialisé")
            return False
        
        if not self.encoder:
            print("❌ Encodeur non initialisé")
            return False
        
        try:
            print("🎮 Contrôles:")
            print("   • Tourner l'encodeur: Change la couleur")
            print("   • Appuyer sur le bouton: Change le mode")
            print("   • Ctrl+C: Quitter le test")
            
            # Variables de contrôle
            current_color = 0
            current_mode = 0
            modes = ["Couleurs", "Formes", "Texte"]
            colors = [
                ("Rouge", (0, 0, 255)),
                ("Vert", (0, 255, 0)),
                ("Bleu", (255, 0, 0)),
                ("Jaune", (0, 255, 255)),
                ("Cyan", (255, 255, 0)),
                ("Magenta", (255, 0, 255)),
                ("Blanc", (255, 255, 255)),
                ("Noir", (0, 0, 0))
            ]
            
            # Callbacks pour l'encodeur
            def on_rotation(direction):
                nonlocal current_color
                current_color = (current_color + direction) % len(colors)
                self.update_encoder_display(modes[current_mode], colors[current_color])
            
            def on_button():
                nonlocal current_mode
                current_mode = (current_mode + 1) % len(modes)
                self.update_encoder_display(modes[current_mode], colors[current_color])
            
            # Configuration des callbacks
            self.encoder.set_rotation_callback(on_rotation)
            self.encoder.set_button_callback(on_button)
            
            # Affichage initial
            self.update_encoder_display(modes[current_mode], colors[current_color])
            
            # Boucle principale
            print("🔄 Test en cours... (Ctrl+C pour quitter)")
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n✅ Test de l'encodeur terminé")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du test de l'encodeur: {e}")
            return False
    
    def update_encoder_display(self, mode, color_info):
        """Met à jour l'affichage selon l'encodeur"""
        try:
            color_name, color_rgb = color_info
            
            # Créer l'image
            image = Image.new('RGB', (self.display.width, self.display.height), color=color_rgb)
            draw = ImageDraw.Draw(image)
            
            # Cadre blanc
            draw.rectangle([0, 0, self.display.width-1, self.display.height-1], outline=(255, 255, 255), width=2)
            
            # Texte central
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Mode
            mode_text = f"Mode: {mode}"
            if font:
                text_bbox = draw.textbbox((0, 0), mode_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                x = (self.display.width - text_width) // 2
                draw.text((x, 10), mode_text, fill=(255, 255, 255), font=font)
            else:
                x = (self.display.width - len(mode_text) * 6) // 2
                draw.text((x, 10), mode_text, fill=(255, 255, 255))
            
            # Couleur
            color_text = f"Couleur: {color_name}"
            if font:
                text_bbox = draw.textbbox((0, 0), color_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                x = (self.display.width - text_width) // 2
                draw.text((x, 30), color_text, fill=(255, 255, 255), font=font)
            else:
                x = (self.display.width - len(color_text) * 6) // 2
                draw.text((x, 30), color_text, fill=(255, 255, 255))
            
            # Instructions
            instructions = "Tourner: couleur | Bouton: mode"
            if font:
                text_bbox = draw.textbbox((0, 0), instructions, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                x = (self.display.width - text_width) // 2
                draw.text((x, self.display.height - 20), instructions, fill=(255, 255, 255), font=font)
            else:
                x = (self.display.width - len(instructions) * 6) // 2
                draw.text((x, self.display.height - 20), instructions, fill=(255, 255, 255))
            
            # Position de l'encodeur
            pos_text = f"Pos: {self.encoder.get_position()}"
            if font:
                text_bbox = draw.textbbox((0, 0), pos_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                x = (self.display.width - text_width) // 2
                draw.text((x, 50), pos_text, fill=(255, 255, 255), font=font)
            else:
                x = (self.display.width - len(pos_text) * 6) // 2
                draw.text((x, 50), pos_text, fill=(255, 255, 255))
            
            self.display.display(image)
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour de l'affichage: {e}")
    
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
        
        # Test de diagnostic des couleurs - test de tous les ordres possibles
        print("🔍 Test de diagnostic des couleurs...")
        
        # Test 1: RGB standard
        print("   Test RGB standard:")
        test_rgb = [
            ("Rouge RGB", (255, 0, 0)),
            ("Vert RGB", (0, 255, 0)),
            ("Bleu RGB", (0, 0, 255))
        ]
        
        for nom, couleur in test_rgb:
            print(f"     {nom}: RGB{couleur}")
            image = Image.new('RGB', (self.display.width, self.display.height), color=couleur)
            self.display.display(image)
            time.sleep(1)
        
        # Test 2: BGR
        print("   Test BGR:")
        test_bgr = [
            ("Rouge BGR", (0, 0, 255)),
            ("Vert BGR", (0, 255, 0)),
            ("Bleu BGR", (255, 0, 0))
        ]
        
        for nom, couleur in test_bgr:
            print(f"     {nom}: BGR{couleur}")
            image = Image.new('RGB', (self.display.width, self.display.height), color=couleur)
            self.display.display(image)
            time.sleep(1)
        
        # Test 3: Autres ordres possibles
        print("   Test autres ordres:")
        test_other = [
            ("Rouge RBG", (255, 0, 0)),  # RBG
            ("Vert GRB", (0, 255, 0)),   # GRB
            ("Bleu GBR", (0, 0, 255))    # GBR
        ]
        
        for nom, couleur in test_other:
            print(f"     {nom}: {couleur}")
            image = Image.new('RGB', (self.display.width, self.display.height), color=couleur)
            self.display.display(image)
            time.sleep(1)
        
        couleurs = [
            ("Noir", (0, 0, 0)),
            ("Blanc", (255, 255, 255)),
            ("Rouge", (0, 0, 255)),      # BGR: Bleu=0, Vert=0, Rouge=255
            ("Vert", (0, 255, 0)),       # BGR: Bleu=0, Vert=255, Rouge=0
            ("Bleu", (255, 0, 0)),       # BGR: Bleu=255, Vert=0, Rouge=0
            ("Jaune", (0, 255, 255)),    # BGR: Bleu=0, Vert=255, Rouge=255
            ("Cyan", (255, 255, 0)),     # BGR: Bleu=255, Vert=255, Rouge=0
            ("Magenta", (255, 0, 255)),  # BGR: Bleu=255, Vert=0, Rouge=255
            ("Orange", (0, 165, 255)),   # BGR: Bleu=0, Vert=165, Rouge=255
            ("Violet", (128, 0, 128)),   # BGR: Bleu=128, Vert=0, Rouge=128
            ("Rose", (203, 192, 255)),   # BGR: Bleu=203, Vert=192, Rouge=255
            ("Vert Lime", (50, 205, 50)) # BGR: Bleu=50, Vert=205, Rouge=50
        ]
        
        try:
            for nom, couleur in couleurs:
                print(f"   Affichage {nom}...")
                # Créer une image qui remplit tout l'écran
                image = Image.new('RGB', (self.display.width, self.display.height), color=couleur)
                
                # Ajouter un cadre blanc pour bien voir les bords
                draw = ImageDraw.Draw(image)
                draw.rectangle([0, 0, self.display.width-1, self.display.height-1], outline=(255, 255, 255), width=2)
                
                # Ajouter le nom de la couleur au centre
                try:
                    font = ImageFont.load_default()
                    text_bbox = draw.textbbox((0, 0), nom, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    x = (self.display.width - text_width) // 2
                    y = (self.display.height - text_height) // 2
                    draw.text((x, y), nom, fill=(255, 255, 255), font=font)
                except:
                    # Si pas de police, centrer le texte manuellement
                    x = (self.display.width - len(nom) * 6) // 2
                    y = self.display.height // 2
                    draw.text((x, y), nom, fill=(255, 255, 255))
                
                self.display.display(image)
                time.sleep(2)  # Plus de temps pour voir chaque couleur
            
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
            # Création d'une image avec formes utilisant toute la résolution
            image = Image.new('RGB', (self.display.width, self.display.height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Rectangle (coin supérieur gauche)
            draw.rectangle([5, 5, 45, 25], fill=(255, 0, 0), outline=(255, 255, 255))
            
            # Cercle (coin supérieur droit)
            draw.ellipse([self.display.width-45, 5, self.display.width-5, 45], fill=(0, 255, 0), outline=(255, 255, 255))
            
            # Ligne horizontale (milieu)
            draw.line([(10, self.display.height//2), (self.display.width-10, self.display.height//2)], fill=(0, 0, 255), width=3)
            
            # Triangle (coin inférieur gauche)
            draw.polygon([(30, self.display.height-30), (50, self.display.height-10), (10, self.display.height-10)], fill=(255, 255, 0))
            
            # Rectangle plein (coin inférieur droit)
            draw.rectangle([self.display.width-40, self.display.height-30, self.display.width-10, self.display.height-10], fill=(255, 0, 255), outline=(255, 255, 255))
            
            # Ligne diagonale
            draw.line([(0, 0), (self.display.width-1, self.display.height-1)], fill=(0, 255, 255), width=2)
            
            self.display.display(image)
            print("✅ Formes géométriques affichées (pleine résolution)")
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
            
            # Texte de test adapté à la résolution
            text_lines = [
                "ALIMANTE",
                "Test SPI",
                "ST7735 OK",
                f"{self.display.width}x{self.display.height}",
                "Rotation 180°"
            ]
            
            y_position = 5
            line_height = (self.display.height - 10) // len(text_lines)
            
            for line in text_lines:
                if font:
                    draw.text((5, y_position), line, fill=(255, 255, 255), font=font)
                else:
                    draw.text((5, y_position), line, fill=(255, 255, 255))
                y_position += line_height
            
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
            ("Performance", self.test_performance),
            ("Encodeur rotatif", self.test_encoder_interactif)
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
            print("7. Test encodeur rotatif")
            print("8. Test complet")
            print("0. Quitter")
            print("=" * 40)
            
            choice = input("Votre choix (0-8): ").strip()
            
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
                self.test_encoder_interactif()
            elif choice == "8":
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
            # Libérer l'objet display
            try:
                del self.display
            except:
                pass
        
        if self.encoder:
            self.encoder.cleanup()
        
        # Nettoyage GPIO plus agressif
        try:
            GPIO.cleanup()
        except:
            pass
        
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
        print("   pip install st7735 Pillow")
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
