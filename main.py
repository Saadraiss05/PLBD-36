# =============================================================================
# main.py — Programme principal du robot d'irrigation PLBD-36
# Centrale Casablanca — Groupe 36
# =============================================================================
# Architecture :
#   1. Securite (obstacle + niveau eau)
#   2. Navigation (suivi de ligne)
#   3. Vision (identification plante)
#   4. Humidite (mesure sol)
#   5. Decision (arroser ou non selon espece)
#   6. Action (activer pompe si besoin)
# =============================================================================

import time
import signal
import sys

from config.config import MODE_SIMULATION, INTERVALLE_CYCLE_SEC
from modules.vision import VisionPlante
from modules.capteur_humidite import CapteurHumidite
from modules.capteur_ultrasons import CapteurUltrasons
from modules.capteur_niveau_eau import CapteurNiveauEau
from modules.pompe_eau import PompeEau
from modules.moteurs import Moteurs
from modules.suiveur_ligne import SuiveurLigne


class RobotIrrigation:
    """
    Orchestrateur principal du robot d'irrigation intelligent PLBD-36.
    """

    def __init__(self):
        print("=" * 60)
        print("  ROBOT PLBD-36 — Demarrage")
        print(f"  Mode : {'SIMULATION' if MODE_SIMULATION else 'REEL (Raspberry Pi)'}")
        print("=" * 60)

        # Initialisation de tous les modules
        self.vision = VisionPlante()
        self.humidite = CapteurHumidite()
        self.ultrasons = CapteurUltrasons()
        self.niveau_eau = CapteurNiveauEau()
        self.pompe = PompeEau()
        self.moteurs = Moteurs()
        self.suiveur = SuiveurLigne()

        self.cycle_actuel = 0
        self.arrosages_effectues = 0
        self.en_marche = True

        # Gestion de l'arret propre (Ctrl+C ou signal systeme)
        signal.signal(signal.SIGINT, self._arret_urgence)
        signal.signal(signal.SIGTERM, self._arret_urgence)

        print("  Tous les modules initialises. Demarrage dans 2s...")
        time.sleep(2)

    def _arret_urgence(self, sig=None, frame=None):
        """Arret propre : pompe et moteurs coupes avant fermeture."""
        print("\n[ROBOT] Arret d'urgence — securisation en cours...")
        self.en_marche = False
        try:
            self.moteurs.arreter()
            self.pompe.arreter()
        except: pass
        self.fermer()
        print("[ROBOT] Robot arrete proprement.")
        sys.exit(0)

    def naviguer(self):
        """
        Navigation autonome : suit la ligne et s'arrete si obstacle.
        Retourne True pour continuer, False si obstacle bloquant.
        """
        # Verification obstacle en priorite
        if self.ultrasons.obstacle_detecte():
            print("[ROBOT] Obstacle detecte — arret de navigation")
            self.moteurs.arreter()
            return False

        # Suivi de ligne
        direction = self.suiveur.obtenir_direction()

        if direction == 'AVANT':
            self.moteurs.avancer()
        elif direction == 'GAUCHE':
            self.moteurs.tourner_gauche()
        elif direction == 'DROITE':
            self.moteurs.tourner_droit()
        elif direction == 'STOP':
            self.moteurs.arreter()
            print("[ROBOT] Ligne perdue — attente...")

        return True

    def analyser_et_irriguer(self):
        """
        Cycle complet : identification plante -> mesure humidite -> decision irrigation.
        """
        print(f"\n{'='*50}")
        print(f"  CYCLE #{self.cycle_actuel} — Analyse en cours")
        print(f"{'='*50}")

        # 1. Verification reservoir
        if not self.niveau_eau.lire_niveau():
            print("[ROBOT] Reservoir vide — cycle annule")
            return

        # 2. Identification de la plante par vision
        resultat_vision = self.vision.identifier_plante()
        espece = resultat_vision['espece']
        confiance = resultat_vision['confiance']
        besoins = resultat_vision['besoins']

        print(f"[ROBOT] Plante : {espece} (confiance: {confiance:.0%})")
        print(f"[ROBOT] Seuils : {besoins['humidite_min']}% - {besoins['humidite_max']}%")

        # 3. Mesure humidite du sol
        humidite = self.humidite.lire_humidite()
        if humidite is None:
            print("[ROBOT] Lecture humidite impossible — cycle interrompu")
            return

        print(f"[ROBOT] Humidite sol : {humidite}%")

        # 4. Decision d'arrosage
        doit_arroser = self.humidite.sol_necessite_arrosage(humidite, besoins)

        if doit_arroser:
            intervalle_min = besoins.get('intervalle_min', 3600)
            if self.pompe.peut_arroser(intervalle_min):
                duree = besoins.get('duree_arrosage', 10)
                print(f"[ROBOT] ARROSAGE de {espece} pendant {duree}s")
                succes = self.pompe.arroser(duree, self.niveau_eau)
                if succes:
                    self.arrosages_effectues += 1
                    print(f"[ROBOT] Arrosage #{self.arrosages_effectues} effectue")
            else:
                print("[ROBOT] Intervalle non ecoule — pas d'arrosage")
        else:
            print("[ROBOT] Sol suffisamment humide — aucune action")

    def demarrer(self):
        """Boucle principale du robot."""
        print("[ROBOT] Demarrage de la boucle principale...")

        CYCLES_AVANT_ANALYSE = 5  # Naviguer 5 cycles puis analyser

        try:
            while self.en_marche:
                self.cycle_actuel += 1

                # Navigation continue
                for _ in range(CYCLES_AVANT_ANALYSE):
                    if not self.en_marche:
                        break
                    self.naviguer()
                    time.sleep(0.1)

                # Arret pour analyse toutes les N iterations
                self.moteurs.arreter()
                self.analyser_et_irriguer()

                print(f"[ROBOT] Pause {INTERVALLE_CYCLE_SEC}s avant prochain cycle...")
                time.sleep(INTERVALLE_CYCLE_SEC)

        except KeyboardInterrupt:
            self._arret_urgence()

    def fermer(self):
        """Liberation de toutes les ressources."""
        self.vision.fermer()
        self.pompe.fermer()
        self.moteurs.fermer()
        self.humidite.fermer()
        self.ultrasons.fermer()
        self.suiveur.fermer()
        self.niveau_eau.fermer()
        print("[ROBOT] Toutes les ressources liberees")


if __name__ == "__main__":
    robot = RobotIrrigation()
    robot.demarrer()
