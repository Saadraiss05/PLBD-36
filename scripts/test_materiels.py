#!/usr/bin/env python3
# =============================================================================
# scripts/test_materiels.py -- Test individuel de chaque composant
# Groupe 36 | Ecole Centrale Casablanca | Projet PLBD-36
#
# Permet de tester chaque module separement avant l'integration complete.
#
# Usage:
#   python scripts/test_materiels.py --all          # Tout tester
#   python scripts/test_materiels.py --humidite     # Capteur humidite seul
#   python scripts/test_materiels.py --ultrasons    # HC-SR04 seul
#   python scripts/test_materiels.py --pompe        # Pompe seule (2s)
#   python scripts/test_materiels.py --moteurs      # Moteurs (sequence)
#   python scripts/test_materiels.py --camera       # Camera (capture + affichage)
# =============================================================================

import sys
import os
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_humidite():
    print("\n--- TEST CAPTEUR HUMIDITE ---")
    from modules.capteur_humidite import CapteurHumidite
    c = CapteurHumidite()
    for i in range(5):
        val = c.lire_humidite()
        print(f"  Lecture {i+1}/5 : {val}%")
        time.sleep(1)
    c.fermer()
    print("[OK] Capteur humidite")


def test_ultrasons():
    print("\n--- TEST CAPTEUR ULTRASONS HC-SR04 ---")
    from modules.capteur_ultrasons import CapteurUltrasons
    c = CapteurUltrasons()
    for i in range(5):
        d = c.mesurer_distance()
        print(f"  Mesure {i+1}/5 : {d} cm | Obstacle: {c.obstacle_detecte()}")
        time.sleep(0.5)
    c.fermer()
    print("[OK] Capteur ultrasons")


def test_niveau_eau():
    print("\n--- TEST CAPTEUR NIVEAU EAU ---")
    from modules.capteur_niveau_eau import CapteurNiveauEau
    c = CapteurNiveauEau()
    for i in range(3):
        etat = c.lire_niveau()
        print(f"  Lecture {i+1}/3 : {'Reservoir OK' if etat else 'VIDE'}")
        time.sleep(1)
    c.fermer()
    print("[OK] Capteur niveau eau")


def test_pompe():
    print("\n--- TEST POMPE EAU (2 secondes) ---")
    print("  ATTENTION : La pompe va s'activer 2 secondes")
    input("  Appuyez sur ENTREE pour confirmer...")
    from modules.pompe_eau import PompeEau
    p = PompeEau()
    print("  Demarrage pompe...")
    succes = p.arroser(2)
    print(f"  Resultat : {'OK' if succes else 'ECHEC'}")
    p.fermer()
    print("[OK] Pompe")


def test_moteurs():
    print("\n--- TEST MOTEURS L298N ---")
    print("  Le robot va executer : avant 2s -> gauche 1s -> droite 1s -> reculer 1s -> stop")
    input("  Assurez-vous que le robot est en securite. ENTREE pour continuer...")
    from modules.moteurs import Moteurs
    m = Moteurs()

    print("  Avancer 2s...")
    m.avancer()
    time.sleep(2)

    print("  Tourner gauche 1s...")
    m.tourner_gauche()
    time.sleep(1)

    print("  Tourner droite 1s...")
    m.tourner_droit()
    time.sleep(1)

    print("  Reculer 1s...")
    m.reculer()
    time.sleep(1)

    m.arreter()
    m.fermer()
    print("[OK] Moteurs")


def test_suiveur_ligne():
    print("\n--- TEST SUIVEUR DE LIGNE IR ---")
    print("  Lectures pendant 10 secondes (Ctrl+C pour arreter)")
    from modules.suiveur_ligne import SuiveurLigne
    s = SuiveurLigne()
    try:
        for i in range(20):
            pos = s.analyser_position()
            print(f"  {i+1:2d}. Position : {pos}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    s.fermer()
    print("[OK] Suiveur de ligne")


def test_camera():
    print("\n--- TEST CAMERA RASPBERRY PI ---")
    try:
        from picamera2 import Picamera2
        cam = Picamera2()
        config = cam.create_still_configuration(main={"size": (640, 480), "format": "RGB888"})
        cam.configure(config)
        cam.start()
        time.sleep(1)
        image = cam.capture_array()
        cam.stop()
        cam.close()
        print(f"  [OK] Image capturee : {image.shape}")

        # Sauvegarder
        import cv2
        os.makedirs('logs', exist_ok=True)
        cv2.imwrite('logs/test_camera.jpg', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        print("  Image sauvegardee : logs/test_camera.jpg")
    except ImportError:
        print("  [SIM] picamera2 non disponible (mode simulation)")
    except Exception as e:
        print(f"  [ERREUR] {e}")


def main():
    parser = argparse.ArgumentParser(description='Test composants PLBD-36')
    parser.add_argument('--all',          action='store_true', help='Tester tous les composants')
    parser.add_argument('--humidite',     action='store_true', help='Capteur humidite')
    parser.add_argument('--ultrasons',    action='store_true', help='Capteur ultrasons HC-SR04')
    parser.add_argument('--niveau-eau',   action='store_true', help='Capteur niveau eau')
    parser.add_argument('--pompe',        action='store_true', help='Pompe (2s)')
    parser.add_argument('--moteurs',      action='store_true', help='Moteurs DC L298N')
    parser.add_argument('--suiveur',      action='store_true', help='Suiveur de ligne IR')
    parser.add_argument('--camera',       action='store_true', help='Camera Raspberry Pi')
    args = parser.parse_args()

    print("=" * 50)
    print("  TEST MATERIELS PLBD-36")
    print("  Groupe 36 | Ecole Centrale Casablanca")
    print("=" * 50)

    tests = {
        'humidite':   test_humidite,
        'ultrasons':  test_ultrasons,
        'niveau_eau': test_niveau_eau,
        'pompe':      test_pompe,
        'moteurs':    test_moteurs,
        'suiveur':    test_suiveur_ligne,
        'camera':     test_camera,
    }

    if args.all:
        for nom, fn in tests.items():
            try:
                fn()
            except Exception as e:
                print(f"[ERREUR] {nom}: {e}")
    else:
        if args.humidite:  test_humidite()
        if args.ultrasons: test_ultrasons()
        if getattr(args, 'niveau_eau', False): test_niveau_eau()
        if args.pompe:     test_pompe()
        if args.moteurs:   test_moteurs()
        if args.suiveur:   test_suiveur_ligne()
        if args.camera:    test_camera()

        if not any([args.humidite, args.ultrasons, args.pompe,
                    args.moteurs, args.suiveur, args.camera]):
            parser.print_help()

    print("\n[FIN] Tests termines")


if __name__ == '__main__':
    main()
