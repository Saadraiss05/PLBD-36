# modules/capteur_niveau_eau.py
from config.config import MODE_SIMULATION, NIVEAU_EAU_PIN, NIVEAU_EAU_MIN

try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False

class CapteurNiveauEau:
    def __init__(self):
        self.initialise = False
        if MODE_SIMULATION:
            print("[NiveauEau] Mode SIMULATION")
            return
        if not GPIO_DISPONIBLE:
            return
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(NIVEAU_EAU_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.initialise = True
            print(f"[NiveauEau] OK (pin={NIVEAU_EAU_PIN})")
        except Exception as e:
            print(f"[NiveauEau] Erreur: {e}")

    def lire_niveau(self):
        if MODE_SIMULATION:
            import random
            plein = random.random() > 0.1
            print(f"[NiveauEau SIM] {'OK' if plein else 'VIDE'}")
            return plein
        if not self.initialise:
            return True
        try:
            etat = GPIO.input(NIVEAU_EAU_PIN)
            vide = (etat == NIVEAU_EAU_MIN)
            if vide: print("[NiveauEau] RESERVOIR VIDE")
            return not vide
        except:
            return True

    def fermer(self):
        if GPIO_DISPONIBLE and self.initialise:
            try: GPIO.cleanup([NIVEAU_EAU_PIN])
            except: pass
