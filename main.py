#!/usr/bin/env python3
# =============================================================================
# main.py -- Robot d'irrigation intelligent PLBD-36
# Groupe 36 | Ecole Centrale Casablanca
#
# Cycle complet :
#   1. Securite : obstacles + niveau eau
#   2. Navigation : suivi de ligne
#   3. Vision : identification espece de plante
#   4. Capteur : mesure humidite sol
#   5. Decision : arrosage selon besoins hydriques
#   6. Repeter
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
    """Orchestrateur principal du robot d'irrigation PLBD-36."""

    def __init__(self):
        print("=" * 60)
        print("  ROBOT D'IRRIGATION -- PLBD-36")
        print("  Groupe 36 | Ecole Centrale Casablanca")
        print(f"  Mode : {'SIMULATION' if MODE_SIMULATION else 'REEL (Raspberry Pi)'}")
        print("=" * 60)

        print("\n[Init] Initialisation des modules...")
        self.vision = VisionPlante()
        self.humidite = CapteurHumidite()
        self.ultrasons = CapteurUltrasons()
        self.niveau_eau = CapteurNiveauEau()
        self.pompe = PompeEau()
        self.moteurs = Moteurs()
        self.suiveur = SuiveurLigne()

        self.cycle = 0
        self.arrosages_effectues = 0
        self.en_marche = True

        signal.signal(signal.SIGINT, self._arret_urgence)
        signal.signal(signal.SIGTERM, self._arret_urgence)
        print("[Init] Tous les modules prets\n")

    def _arret_urgence(self, signum, frame):
        print("\n[ARRET] Arret d'urgence...")
        self.en_marche = False
        self.moteurs.arreter()
        self.pompe.arreter()
        self.fermer()
        sys.exit(0)

    def etape_securite(self):
        if self.ultrasons.obstacle_detecte():
            print("[Securite] OBSTACLE -- arret navigation")
            self.moteurs.arreter()
            return False
        if not self.niveau_eau.lire_niveau():
            print("[Securite] RESERVOIR VIDE -- arrosage desactive")
        return True

    def etape_navigation(self, duree_sec=5):
        print(f"[Navigation] Deplacement ({duree_sec}s)...")
        t_debut = time.time()
        while time.time() - t_debut < duree_sec:
            if self.ultrasons.obstacle_detecte():
                self.moteurs.arreter()
                print("[Navigation] Obstacle! Attente 2s...")
                time.sleep(2)
                continue
            sur_ligne = self.suiveur.guider_moteurs(self.moteurs)
            if not sur_ligne:
                print("[Navigation] Ligne perdue -- recuperation")
                time.sleep(0.5)
            time.sleep(0.1)
        self.moteurs.arreter()
        print("[Navigation] Position atteinte")

    def etape_analyse(self):
        print("[Analyse] Identification de la plante...")
        resultat_vision = self.vision.identifier_plante()
        print("[Analyse] Mesure humidite sol...")
        humidite = self.humidite.lire_humidite()
        return resultat_vision, humidite

    def etape_decision_arrosage(self, resultat_vision, humidite):
        espece = resultat_vision['espece']
        confiance = resultat_vision['confiance']
        besoins = resultat_vision['besoins']

        print(f"\n[Decision] Espece: {espece} (confiance: {confiance:.0%})")
        print(f"[Decision] Humidite: {humidite}% | Optimal: {besoins['humidite_min']}-{besoins['humidite_max']}%")

        if not self.pompe.peut_arroser(besoins['intervalle_min']):
            return False
        if not self.niveau_eau.lire_niveau():
            print("[Decision] Reservoir vide -- arrosage impossible")
            return False

        doit_arroser = self.humidite.sol_necessite_arrosage(humidite, besoins)
        if doit_arroser:
            succes = self.pompe.arroser(besoins['duree_arrosage'], self.niveau_eau)
            if succes:
                self.arrosages_effectues += 1
                print(f"[Decision] Arrosage OK (total: {self.arrosages_effectues})")
        else:
            print("[Decision] Pas d'arrosage necessaire")
        return doit_arroser

    def executer_cycle(self):
        self.cycle += 1
        print(f"\n{'='*50}")
        print(f"  CYCLE #{self.cycle}")
        print(f"{'='*50}")

        if not self.etape_securite():
            time.sleep(5)
            return

        self.etape_navigation(duree_sec=5)
        resultat_vision, humidite = self.etape_analyse()
        self.etape_decision_arrosage(resultat_vision, humidite)

        print(f"\n[Cycle] #{self.cycle} termine -- pause {INTERVALLE_CYCLE_SEC}s")
        time.sleep(INTERVALLE_CYCLE_SEC)

    def demarrer(self):
        print("\n[Robot] Demarrage -- Ctrl+C pour arreter\n")
        while self.en_marche:
            try:
                self.executer_cycle()
            except Exception as e:
                print(f"[ERREUR] {e}")
                self.moteurs.arreter()
                self.pompe.arreter()
                time.sleep(5)

    def fermer(self):
        print("[Fermeture] Liberation ressources...")
        self.moteurs.fermer()
        self.pompe.fermer()
        self.humidite.fermer()
        self.ultrasons.fermer()
        self.niveau_eau.fermer()
        self.suiveur.fermer()
        self.vision.fermer()
        print("[Fermeture] Termine")


if __name__ == "__main__":
    robot = RobotIrrigation()
    try:
        robot.demarrer()
    finally:
        robot.fermer()
