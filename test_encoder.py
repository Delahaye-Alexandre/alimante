#!/usr/bin/env python3
"""
Test d'un encodeur rotatif avec gpiozero
Affiche le compteur quand tu tournes dans un sens ou dans l'autre
"""

from gpiozero import RotaryEncoder
from signal import pause

# ⚠️ À adapter selon ton câblage !
CLK_PIN = 17  # Pin A de l'encodeur
DT_PIN = 18   # Pin B de l'encodeur

print("🔧 Initialisation de l'encodeur rotatif...")
encoder = RotaryEncoder(a=CLK_PIN, b=DT_PIN, max_steps=0)

def rotation():
    print(f"🔄 Position actuelle : {encoder.steps}")

# Appeler la fonction à chaque mouvement
encoder.when_rotated = rotation

print("✅ Prêt ! Tourne l'encodeur (Ctrl+C pour quitter)")
pause()
