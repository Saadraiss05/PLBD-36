#!/usr/bin/env python3
# =============================================================================
# scripts/decision_arrosage.py -- Moteur de decision d'arrosage standalone
# Groupe 36 | Ecole Centrale Casablanca | Projet PLBD-36
#
# Ce script peut tourner independamment du robot complet.
# Il combine : vision (detection espece) + capteur humidite + logique de decision.
#
# Usage:
#   python scripts/decision_arrosage.py                    # Mode reel
#   python scripts/decision_arrosage.py --simulation       # Sans materiel
#   python scripts/decision_arrosage.py --humidite 45      # Forcer humidite
#   python scripts/decision_arrosage.py --espece tomate     # Forcer espece
# =============================================================================

import sys
import os
import argparse
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import (
    MODE_SIMULATION, BESOINS_PAR_ESPECE,
    MODELE_TFLITE_PATH, LABELS_PATH, BESOINS_HYDRIQUES_PATH,
    SEUIL_CONFIANCE_MIN
)


# ---------------------------------------------------------------------------
# Classe principale : Moteur de decision
# ---------------------------------------------------------------------------

class MoteurDecisionArrosage:
    """
    Moteur de decision d'arrosage intelligent.
    Combine detection visuelle + humidite sol + regles agronomiques.
    
    Logique de decision :
        1. Identifier l'espece via camera (EfficientNet-B3 / TFLite)
        2. Mesurer l'humidite du sol (capteur analogique MCP3008)
        3. Comparer avec les besoins hydriques de l'espece
        4. Decider et actionner la pompe si necessaire
        5. Logger la decision pour traçabilite
    """

    def __init__(self, simulation=False, humidite_forcee=None, espece_forcee=None):
        self.simulation = simulation or MODE_SIMULATION
        self.humidite_forcee = humidite_forcee
        self.espece_forcee = espece_forcee
        self.historique = []

        print("=" * 60)
        print("  MOTEUR DE DECISION D'ARROSAGE -- PLBD-36")
        print(f"  Mode : {'SIMULATION' if self.simulation else 'REEL'}")
        print("=" * 60)

        if not self.simulation:
            self._init_modules()

    def _init_modules(self):
        """Initialise les modules materiels."""
        from modules.vision import VisionPlante
        from modules.capteur_humidite import CapteurHumidite
        from modules.pompe_eau import PompeEau
        from modules.capteur_niveau_eau import CapteurNiveauEau

        self.vision = VisionPlante()
        self.humidite_capteur = CapteurHumidite()
        self.pompe = PompeEau()
        self.niveau_eau = CapteurNiveauEau()
        print("[Init] Modules materiels initialises")

    # -------------------------------------------------------------------------
    # Etape 1 : Detection de l'espece
    # -------------------------------------------------------------------------

    def detecter_espece(self):
        """
        Identifie l'espece de plante.
        Retourne dict avec espece, confiance, besoins.
        """
        if self.espece_forcee:
            espece = self.espece_forcee
            besoins = BESOINS_PAR_ESPECE.get(espece, BESOINS_PAR_ESPECE['inconnu'])
            print(f"[Vision] Espece forcee : {espece}")
            return {
                'espece': espece,
                'confiance': 1.0,
                'besoins': besoins,
                'fiable': True,
                'source': 'force'
            }

        if self.simulation:
            import random
            espece = random.choice(['tomate', 'tomate', 'tomate', 'olivier'])
            confiance = round(random.uniform(0.75, 0.97), 3)
            besoins = BESOINS_PAR_ESPECE.get(espece, BESOINS_PAR_ESPECE['inconnu'])
            print(f"[Vision SIM] {espece} ({confiance:.0%})")
            return {
                'espece': espece,
                'confiance': confiance,
                'besoins': besoins,
                'fiable': confiance >= SEUIL_CONFIANCE_MIN,
                'source': 'simulation'
            }

        resultat = self.vision.identifier_plante()
        resultat['source'] = 'camera'
        return resultat

    # -------------------------------------------------------------------------
    # Etape 2 : Mesure de l'humidite
    # -------------------------------------------------------------------------

    def mesurer_humidite(self):
        """
        Lit le taux d'humidite du sol.
        Retourne un float entre 0 et 100.
        """
        if self.humidite_forcee is not None:
            print(f"[Humidite] Valeur forcee : {self.humidite_forcee}%")
            return float(self.humidite_forcee)

        if self.simulation:
            import random
            valeur = round(random.uniform(30, 80), 1)
            print(f"[Humidite SIM] {valeur}%")
            return valeur

        return self.humidite_capteur.lire_humidite()

    # -------------------------------------------------------------------------
    # Etape 3 : Logique de decision
    # -------------------------------------------------------------------------

    def analyser_besoin_arrosage(self, espece_info, humidite):
        """
        Applique la logique de decision d'arrosage.

        Regles :
          - Si humidite < humidite_min  → SOL TROP SEC  → ARROSER
          - Si humidite > humidite_max  → SOL TROP HUMIDE → NE PAS ARROSER
          - Sinon                        → OPTIMAL → NE PAS ARROSER

        Retourne un dict de decision detaille.
        """
        besoins = espece_info['besoins']
        espece  = espece_info['espece']
        h_min   = besoins.get('humidite_min', 50)
        h_max   = besoins.get('humidite_max', 80)
        duree   = besoins.get('duree_arrosage', 10)

        # Calcul du score hydrique (0 = critique sec, 1 = optimal, 2 = trop humide)
        if humidite < h_min:
            etat_sol = 'sec'
            urgence  = round((h_min - humidite) / h_min, 2)  # 0=limite, 1=critique
            decision = True
            raison   = f"Humidite {humidite}% < minimum {h_min}% pour {espece}"
        elif humidite > h_max:
            etat_sol = 'sur-sature'
            urgence  = 0.0
            decision = False
            raison   = f"Humidite {humidite}% > maximum {h_max}% — risque pourriture racinaire"
        else:
            etat_sol = 'optimal'
            urgence  = 0.0
            decision = False
            raison   = f"Humidite {humidite}% dans la plage optimale [{h_min}%, {h_max}%]"

        return {
            'arroser': decision,
            'etat_sol': etat_sol,
            'urgence': urgence,
            'duree_recommandee': duree if decision else 0,
            'raison': raison,
            'humidite_mesuree': humidite,
            'humidite_min': h_min,
            'humidite_max': h_max,
            'espece': espece,
            'confiance_detection': espece_info['confiance']
        }

    # -------------------------------------------------------------------------
    # Etape 4 : Execution de l'arrosage
    # -------------------------------------------------------------------------

    def executer_arrosage(self, decision):
        """
        Execute l'arrosage si la decision le requiert.
        Retourne True si l'arrosage a eu lieu.
        """
        if not decision['arroser']:
            print(f"[Pompe] Pas d'arrosage : {decision['raison']}")
            return False

        duree = decision['duree_recommandee']
        espece = decision['espece']

        if self.simulation:
            print(f"[Pompe SIM] Arrosage {espece} pendant {duree}s...")
            time.sleep(min(duree, 2))
            print(f"[Pompe SIM] Termine")
            return True

        # Verification niveau eau avant arrosage
        if not self.niveau_eau.lire_niveau():
            print("[Pompe] Arrosage annule : reservoir vide")
            return False

        print(f"[Pompe] Arrosage {espece} : {duree}s")
        return self.pompe.arroser(duree, self.niveau_eau)

    # -------------------------------------------------------------------------
    # Etape 5 : Logging
    # -------------------------------------------------------------------------

    def logger_decision(self, espece_info, humidite, decision, arrosage_effectue):
        """Enregistre la decision dans l'historique et un fichier log."""
        entree = {
            'timestamp': datetime.now().isoformat(),
            'espece': espece_info['espece'],
            'confiance_detection': round(espece_info['confiance'], 3),
            'humidite': humidite,
            'etat_sol': decision['etat_sol'],
            'decision_arroser': decision['arroser'],
            'arrosage_effectue': arrosage_effectue,
            'duree_arrosage': decision['duree_recommandee'] if arrosage_effectue else 0,
            'raison': decision['raison']
        }
        self.historique.append(entree)

        # Affichage console structure
        print("\n" + "-" * 50)
        print(f"  DECISION #{len(self.historique)}")
        print(f"  Heure      : {entree['timestamp'][:19]}")
        print(f"  Espece     : {entree['espece']} ({entree['confiance_detection']:.0%})")
        print(f"  Humidite   : {entree['humidite']}%  [{decision['humidite_min']}-{decision['humidite_max']}%]")
        print(f"  Sol        : {entree['etat_sol'].upper()}")
        print(f"  Decision   : {'ARROSER' if entree['decision_arroser'] else 'NE PAS ARROSER'}")
        if arrosage_effectue:
            print(f"  Arrosage   : {entree['duree_arrosage']}s effectues")
        print(f"  Raison     : {entree['raison']}")
        print("-" * 50)

        # Sauvegarde JSON
        log_path = 'logs/decisions_arrosage.json'
        os.makedirs('logs', exist_ok=True)
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.historique, f, ensure_ascii=False, indent=2)

        return entree

    # -------------------------------------------------------------------------
    # Cycle complet
    # -------------------------------------------------------------------------

    def executer_cycle(self):
        """Execute un cycle complet de decision d'arrosage."""
        print(f"\n[Cycle] Debut analyse -- {datetime.now().strftime('%H:%M:%S')}")

        # 1. Detection espece
        espece_info = self.detecter_espece()

        # 2. Mesure humidite
        humidite = self.mesurer_humidite()
        if humidite is None:
            print("[ERREUR] Lecture humidite echouee")
            return None

        # 3. Decision
        decision = self.analyser_besoin_arrosage(espece_info, humidite)

        # 4. Execution arrosage
        arrosage_ok = self.executer_arrosage(decision)

        # 5. Log
        entree = self.logger_decision(espece_info, humidite, decision, arrosage_ok)

        return entree

    def fermer(self):
        """Liberation des ressources."""
        if not self.simulation:
            try:
                self.vision.fermer()
                self.pompe.fermer()
                self.humidite_capteur.fermer()
                self.niveau_eau.fermer()
            except:
                pass
        print(f"[Fermeture] {len(self.historique)} decisions enregistrees")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Moteur de decision d arrosage PLBD-36'
    )
    parser.add_argument('--simulation', action='store_true',
                        help='Mode simulation sans materiel')
    parser.add_argument('--humidite', type=float, default=None,
                        help='Forcer une valeur d humidite (0-100)')
    parser.add_argument('--espece', type=str, default=None,
                        choices=list(BESOINS_PAR_ESPECE.keys()),
                        help='Forcer une espece de plante')
    parser.add_argument('--cycles', type=int, default=1,
                        help='Nombre de cycles a executer (defaut: 1)')
    parser.add_argument('--intervalle', type=int, default=10,
                        help='Pause entre cycles en secondes (defaut: 10)')
    args = parser.parse_args()

    moteur = MoteurDecisionArrosage(
        simulation=args.simulation,
        humidite_forcee=args.humidite,
        espece_forcee=args.espece
    )

    try:
        for i in range(args.cycles):
            if i > 0:
                print(f"\n[Attente] Prochain cycle dans {args.intervalle}s...")
                time.sleep(args.intervalle)
            moteur.executer_cycle()

        # Resume final
        if len(moteur.historique) > 0:
            arrosages = sum(1 for e in moteur.historique if e['arrosage_effectue'])
            print(f"\n[Resume] {len(moteur.historique)} cycles | {arrosages} arrosages")
            print(f"[Resume] Log sauvegarde : logs/decisions_arrosage.json")

    except KeyboardInterrupt:
        print("\n[ARRET] Interruption utilisateur")
    finally:
        moteur.fermer()


if __name__ == '__main__':
    main()
