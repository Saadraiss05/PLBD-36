# =============================================================================
# modules/pompe_eau.py — Controle de la pompe 12V via relais 5V
# SECURITE : Ne jamais connecter la pompe 12V directement au GPIO Raspberry Pi
# La pompe est toujours pilotee via le module relais 5V
# =============================================================================

import time
from config.config import (
    MODE_SIMULATION, RELAIS_PIN, RELAIS_ACTIF_BAS,
    DUREE_MAX_POMPE_SEC, NIVEAU_EAU_MIN
)

try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False


class PompeEau:
    """
    Controle la pompe a eau 12V via un relais 5V.
    Inclut des securites : duree max, verification niveau eau.
    """

    def __init__(self):
        self.en_marche = False
        self.heure_dernier_arrosage = 0
        self.initialise = False

        if MODE_SIMULATION:
            print("[Pompe] Mode SIMULATION")
            return

        if not GPIO_DISPONIBLE:
            print("[Pompe] RPi.GPIO non disponible")
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(RELAIS_PIN, GPIO.OUT)
            # Etat initial : pompe ARRETEE
            # Relais actif bas : HIGH = OFF, LOW = ON
            etat_initial = GPIO.LOW if not RELAIS_ACTIF_BAS else GPIO.HIGH
            GPIO.output(RELAIS_PIN, etat_initial)
            self.initialise = True
            print(f"[Pompe] Relais initialise (pin={RELAIS_PIN}, actif_bas={RELAIS_ACTIF_BAS})")
        except Exception as e:
            print(f"[Pompe] Erreur init : {e}")

    def _activer_relais(self):
        """Active le relais (allume la pompe)."""
        if not GPIO_DISPONIBLE or not self.initialise:
            return
        etat = GPIO.LOW if RELAIS_ACTIF_BAS else GPIO.HIGH
        GPIO.output(RELAIS_PIN, etat)

    def _desactiver_relais(self):
        """Desactive le relais (eteint la pompe)."""
        if not GPIO_DISPONIBLE or not self.initialise:
            return
        etat = GPIO.HIGH if RELAIS_ACTIF_BAS else GPIO.LOW
        GPIO.output(RELAIS_PIN, etat)

    def arroser(self, duree_sec, capteur_niveau=None):
        """
        Active la pompe pendant duree_sec secondes.
        - duree_sec : duree d'arrosage (limitee a DUREE_MAX_POMPE_SEC)
        - capteur_niveau : instance CapteurNiveauEau (optionnel, securite)
        Retourne True si l'arrosage a eu lieu, False sinon.
        """
        # Verification niveau eau
        if capteur_niveau is not None:
            if not capteur_niveau.lire_niveau():
                print("[Pompe] Arrosage annule : reservoir vide")
                return False

        # Securite duree max
        duree_reelle = min(duree_sec, DUREE_MAX_POMPE_SEC)
        if duree_reelle != duree_sec:
            print(f"[Pompe] Duree limitee a {DUREE_MAX_POMPE_SEC}s (securite)")

        if MODE_SIMULATION:
            print(f"[Pompe SIM] Arrosage {duree_reelle}s... GO")
            time.sleep(min(duree_reelle, 2))  # Max 2s en simulation
            print(f"[Pompe SIM] Arrosage termine")
            self.heure_dernier_arrosage = time.time()
            return True

        if not self.initialise:
            print("[Pompe] Non initialisee")
            return False

        try:
            print(f"[Pompe] Demarrage arrosage ({duree_reelle}s)")
            self.en_marche = True
            self._activer_relais()
            time.sleep(duree_reelle)
            self._desactiver_relais()
            self.en_marche = False
            self.heure_dernier_arrosage = time.time()
            print(f"[Pompe] Arrosage termine")
            return True
        except Exception as e:
            # Securite : toujours eteindre la pompe en cas d'erreur
            self._desactiver_relais()
            self.en_marche = False
            print(f"[Pompe] Erreur : {e} — pompe arretee")
            return False

    def arreter(self):
        """Arret d'urgence de la pompe."""
        self._desactiver_relais()
        self.en_marche = False
        print("[Pompe] Arretee (arret d'urgence)")

    def peut_arroser(self, intervalle_min_sec):
        """
        Verifie si l'intervalle minimum depuis le dernier arrosage est ecoule.
        Evite de noyer les plantes.
        """
        if self.heure_dernier_arrosage == 0:
            return True
        temps_ecoule = time.time() - self.heure_dernier_arrosage
        if temps_ecoule < intervalle_min_sec:
            restant = int(intervalle_min_sec - temps_ecoule)
            print(f"[Pompe] Intervalle non ecoule — prochain arrosage dans {restant}s")
            return False
        return True

    def fermer(self):
        """Securite : s'assurer que la pompe est arretee avant fermeture."""
        self.arreter()
        if GPIO_DISPONIBLE and self.initialise:
            try:
                GPIO.cleanup([RELAIS_PIN])
            except:
                pass
        print("[Pompe] Fermeture propre")
