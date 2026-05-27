# =============================================================================
# modules/moteurs.py — Controle des moteurs DC via driver L298N
# 2 moteurs DC pour la propulsion du robot
# =============================================================================

import time
from config.config import (
    MODE_SIMULATION,
    MOTEUR_GAUCHE_IN1, MOTEUR_GAUCHE_IN2, MOTEUR_GAUCHE_PWM,
    MOTEUR_DROIT_IN1, MOTEUR_DROIT_IN2, MOTEUR_DROIT_PWM,
    VITESSE_DEFAUT
)

try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False


class Moteurs:
    """
    Controle les 2 moteurs DC via le driver L298N.
    Vitesse reglable par PWM (0-100%).
    """

    FREQUENCE_PWM = 100  # Hz

    def __init__(self):
        self.pwm_gauche = None
        self.pwm_droit = None
        self.vitesse = VITESSE_DEFAUT
        self.initialise = False

        if MODE_SIMULATION:
            print("[Moteurs] Mode SIMULATION")
            return

        if not GPIO_DISPONIBLE:
            print("[Moteurs] RPi.GPIO non disponible")
            return

        try:
            GPIO.setmode(GPIO.BCM)
            # Moteur gauche
            GPIO.setup(MOTEUR_GAUCHE_IN1, GPIO.OUT)
            GPIO.setup(MOTEUR_GAUCHE_IN2, GPIO.OUT)
            GPIO.setup(MOTEUR_GAUCHE_PWM, GPIO.OUT)
            # Moteur droit
            GPIO.setup(MOTEUR_DROIT_IN1, GPIO.OUT)
            GPIO.setup(MOTEUR_DROIT_IN2, GPIO.OUT)
            GPIO.setup(MOTEUR_DROIT_PWM, GPIO.OUT)

            # Initialisation PWM
            self.pwm_gauche = GPIO.PWM(MOTEUR_GAUCHE_PWM, self.FREQUENCE_PWM)
            self.pwm_droit = GPIO.PWM(MOTEUR_DROIT_PWM, self.FREQUENCE_PWM)
            self.pwm_gauche.start(0)
            self.pwm_droit.start(0)

            self.initialise = True
            print("[Moteurs] L298N initialise")
        except Exception as e:
            print(f"[Moteurs] Erreur init : {e}")

    def _set_moteur(self, in1, in2, pwm, avant, vitesse):
        if not GPIO_DISPONIBLE or not self.initialise:
            return
        if avant:
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
        else:
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.HIGH)
        if pwm:
            pwm.ChangeDutyCycle(vitesse)

    def avancer(self, vitesse=None):
        v = vitesse or self.vitesse
        if MODE_SIMULATION:
            print(f"[Moteurs SIM] Avancer (vitesse={v}%)")
            return
        self._set_moteur(MOTEUR_GAUCHE_IN1, MOTEUR_GAUCHE_IN2, self.pwm_gauche, True, v)
        self._set_moteur(MOTEUR_DROIT_IN1, MOTEUR_DROIT_IN2, self.pwm_droit, True, v)

    def reculer(self, vitesse=None):
        v = vitesse or self.vitesse
        if MODE_SIMULATION:
            print(f"[Moteurs SIM] Reculer (vitesse={v}%)")
            return
        self._set_moteur(MOTEUR_GAUCHE_IN1, MOTEUR_GAUCHE_IN2, self.pwm_gauche, False, v)
        self._set_moteur(MOTEUR_DROIT_IN1, MOTEUR_DROIT_IN2, self.pwm_droit, False, v)

    def tourner_gauche(self, vitesse=None):
        v = vitesse or self.vitesse
        if MODE_SIMULATION:
            print(f"[Moteurs SIM] Tourner gauche")
            return
        self._set_moteur(MOTEUR_GAUCHE_IN1, MOTEUR_GAUCHE_IN2, self.pwm_gauche, False, v)
        self._set_moteur(MOTEUR_DROIT_IN1, MOTEUR_DROIT_IN2, self.pwm_droit, True, v)

    def tourner_droit(self, vitesse=None):
        v = vitesse or self.vitesse
        if MODE_SIMULATION:
            print(f"[Moteurs SIM] Tourner droite")
            return
        self._set_moteur(MOTEUR_GAUCHE_IN1, MOTEUR_GAUCHE_IN2, self.pwm_gauche, True, v)
        self._set_moteur(MOTEUR_DROIT_IN1, MOTEUR_DROIT_IN2, self.pwm_droit, False, v)

    def arreter(self):
        if MODE_SIMULATION:
            print("[Moteurs SIM] Arret")
            return
        if not self.initialise:
            return
        GPIO.output(MOTEUR_GAUCHE_IN1, GPIO.LOW)
        GPIO.output(MOTEUR_GAUCHE_IN2, GPIO.LOW)
        GPIO.output(MOTEUR_DROIT_IN1, GPIO.LOW)
        GPIO.output(MOTEUR_DROIT_IN2, GPIO.LOW)
        if self.pwm_gauche: self.pwm_gauche.ChangeDutyCycle(0)
        if self.pwm_droit: self.pwm_droit.ChangeDutyCycle(0)

    def fermer(self):
        self.arreter()
        if self.pwm_gauche: self.pwm_gauche.stop()
        if self.pwm_droit: self.pwm_droit.stop()
        if GPIO_DISPONIBLE and self.initialise:
            try:
                GPIO.cleanup([MOTEUR_GAUCHE_IN1, MOTEUR_GAUCHE_IN2, MOTEUR_GAUCHE_PWM,
                               MOTEUR_DROIT_IN1, MOTEUR_DROIT_IN2, MOTEUR_DROIT_PWM])
            except: pass
        print("[Moteurs] Fermeture propre")
