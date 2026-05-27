# modules/capteur_ultrasons.py
import time
from config.config import MODE_SIMULATION, TRIG_PIN, ECHO_PIN, DISTANCE_OBSTACLE_CM

try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False

class CapteurUltrasons:
    TIMEOUT = 0.04

    def __init__(self):
        self.initialise = False
        if MODE_SIMULATION:
            print("[Ultrasons] Mode SIMULATION")
            return
        if not GPIO_DISPONIBLE:
            print("[Ultrasons] RPi.GPIO non disponible")
            return
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(TRIG_PIN, GPIO.OUT)
            GPIO.setup(ECHO_PIN, GPIO.IN)
            GPIO.output(TRIG_PIN, False)
            time.sleep(0.1)
            self.initialise = True
            print(f"[Ultrasons] HC-SR04 OK (TRIG={TRIG_PIN}, ECHO={ECHO_PIN})")
        except Exception as e:
            print(f"[Ultrasons] Erreur: {e}")

    def mesurer_distance(self):
        if MODE_SIMULATION:
            import random
            d = round(random.uniform(5, 150), 1)
            print(f"[Ultrasons SIM] {d} cm")
            return d
        if not self.initialise:
            return None
        try:
            GPIO.output(TRIG_PIN, True)
            time.sleep(0.00001)
            GPIO.output(TRIG_PIN, False)
            t0 = time.time()
            while GPIO.input(ECHO_PIN) == 0:
                if time.time() - t0 > self.TIMEOUT: return None
            t1 = time.time()
            while GPIO.input(ECHO_PIN) == 1:
                if time.time() - t1 > self.TIMEOUT: return None
            t2 = time.time()
            return round((t2 - t1) * 34300 / 2, 1)
        except:
            return None

    def obstacle_detecte(self):
        d = self.mesurer_distance()
        if d is None: return False
        if d < DISTANCE_OBSTACLE_CM:
            print(f"[Ultrasons] OBSTACLE a {d} cm")
            return True
        return False

    def fermer(self):
        if GPIO_DISPONIBLE and self.initialise:
            try: GPIO.cleanup([TRIG_PIN, ECHO_PIN])
            except: pass
