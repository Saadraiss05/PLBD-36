# =============================================================================
# modules/suiveur_ligne.py — Capteur infrarouge pour suivi de ligne
# Compatible avec les modules KY-033 / TCRT5000 / similaires
# =============================================================================

import time
from config.config import (
    MODE_SIMULATION,
    SUIVI_LIGNE_PIN_GAUCHE, SUIVI_LIGNE_PIN_DROIT
)

try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False


class SuiveurLigne:
    """
    Capteur infrarouge pour suivi de ligne noire sur fond blanc.
    Retourne des directives de navigation : AVANT, GAUCHE, DROITE, STOP.
    """

    # Valeurs GPIO selon capteur : 0 = ligne noire detectee, 1 = fond blanc
    # (peut varier selon le module — a verifier en testant)
    LIGNE_DETECTEE = 0

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
            print(f"[SuiveurLigne] OK (gauche={SUIVI_LIGNE_PIN_GAUCHE}, droit={SUIVI_LIGNE_PIN_DROIT})")
        except Exception as e:
            print(f"[SuiveurLigne] Erreur init : {e}")

    def lire_capteurs(self):
        """
        Lit les deux capteurs IR.
        Retourne (gauche, droit) : True si ligne detectee.
        """
        if MODE_SIMULATION:
            import random
            # Simulation : 70% ligne suivie normalement
            r = random.random()
            if r < 0.70:
                return (True, True)   # Ligne au centre
            elif r < 0.80:
                return (True, False)  # Ligne a gauche
            elif r < 0.90:
                return (False, True)  # Ligne a droite
            else:
                return (False, False) # Ligne perdue
        
        if not self.initialise:
            return (False, False)

        try:
            gauche = GPIO.input(SUIVI_LIGNE_PIN_GAUCHE) == self.LIGNE_DETECTEE
            droit = GPIO.input(SUIVI_LIGNE_PIN_DROIT) == self.LIGNE_DETECTEE
            return (gauche, droit)
        except Exception as e:
            print(f"[SuiveurLigne] Erreur lecture : {e}")
            return (False, False)

    def obtenir_direction(self):
        """
        Retourne la direction a prendre selon la position de la ligne.
        Retourne : 'AVANT', 'GAUCHE', 'DROITE', ou 'STOP'
        """
        gauche, droit = self.lire_capteurs()

        if gauche and droit:
            direction = 'AVANT'
        elif gauche and not droit:
            direction = 'GAUCHE'
        elif not gauche and droit:
            direction = 'DROITE'
        else:
            direction = 'STOP'  # Ligne perdue

        print(f"[SuiveurLigne] G={gauche} D={droit} -> {direction}")
        return direction

    def fermer(self):
        if GPIO_DISPONIBLE and self.initialise:
            try:
                GPIO.cleanup([SUIVI_LIGNE_PIN_GAUCHE, SUIVI_LIGNE_PIN_DROIT])
            except: pass
