# =============================================================================
# modules/suiveur_ligne.py -- Capteur infrarouge suivi de ligne
# Permet au robot de suivre une ligne noire sur fond blanc
# =============================================================================

import time
from config.config import MODE_SIMULATION, SUIVI_LIGNE_PIN_GAUCHE, SUIVI_LIGNE_PIN_DROIT

try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False


class SuiveurLigne:
    """
    Gestion du capteur IR pour le suivi de ligne.
    Convention capteur : 0 = ligne noire detectee, 1 = fond blanc
    """

    def __init__(self):
        self.initialise = False
        if MODE_SIMULATION:
            print("[SuiveurLigne] Mode SIMULATION")
            return
        if not GPIO_DISPONIBLE:
            print("[SuiveurLigne] RPi.GPIO non disponible")
            return
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(SUIVI_LIGNE_PIN_GAUCHE, GPIO.IN)
            GPIO.setup(SUIVI_LIGNE_PIN_DROIT, GPIO.IN)
            self.initialise = True
            print(f"[SuiveurLigne] OK (G={SUIVI_LIGNE_PIN_GAUCHE}, D={SUIVI_LIGNE_PIN_DROIT})")
        except Exception as e:
            print(f"[SuiveurLigne] Erreur: {e}")

    def lire_capteurs(self):
        """Retourne (gauche, droite) : 0=ligne noire, 1=fond blanc"""
        if MODE_SIMULATION:
            import random
            scenarios = [(0,0),(0,0),(0,0),(0,1),(1,0)]
            return random.choice(scenarios)
        if not self.initialise:
            return (1, 1)
        try:
            return (GPIO.input(SUIVI_LIGNE_PIN_GAUCHE), GPIO.input(SUIVI_LIGNE_PIN_DROIT))
        except:
            return (1, 1)

    def analyser_position(self):
        """
        Analyse la position du robot par rapport a la ligne.
        Retourne: 'centre', 'derive_gauche', 'derive_droite', 'perdu'
        """
        g, d = self.lire_capteurs()
        if g == 0 and d == 0:
            position = 'centre'
        elif g == 0 and d == 1:
            position = 'derive_droite'
        elif g == 1 and d == 0:
            position = 'derive_gauche'
        else:
            position = 'perdu'
        print(f"[SuiveurLigne] G={g} D={d} -> {position}")
        return position

    def guider_moteurs(self, moteurs):
        """
        Ajuste les moteurs selon la position par rapport a la ligne.
        Retourne False si le robot est perdu.
        """
        position = self.analyser_position()
        if position == 'centre':
            moteurs.avancer()
            return True
        elif position == 'derive_gauche':
            moteurs.tourner_gauche(vitesse=40)
            return True
        elif position == 'derive_droite':
            moteurs.tourner_droit(vitesse=40)
            return True
        else:
            moteurs.arreter()
            print("[SuiveurLigne] Robot perdu - arret")
            return False

    def fermer(self):
        if GPIO_DISPONIBLE and self.initialise:
            try:
                GPIO.cleanup([SUIVI_LIGNE_PIN_GAUCHE, SUIVI_LIGNE_PIN_DROIT])
            except:
                pass
