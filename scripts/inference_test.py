#!/usr/bin/env python3
# =============================================================================
# scripts/inference_test.py -- Test du modele TFLite sur Raspberry Pi
# Groupe 36 | Ecole Centrale Casablanca | Projet PLBD-36
#
# Usage:
#   python scripts/inference_test.py                  # Utilise la camera Pi
#   python scripts/inference_test.py --image photo.jpg # Utilise une image
#   python scripts/inference_test.py --simulation      # Mode simulation (sans materiel)
# =============================================================================

import sys
import os
import argparse
import json
import time
import numpy as np

# Ajouter le dossier racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import (
    MODELE_TFLITE_PATH, LABELS_PATH, BESOINS_HYDRIQUES_PATH,
    SEUIL_CONFIANCE_MIN, RESOLUTION_CAMERA, BESOINS_PAR_ESPECE
)

# ---------------------------------------------------------------------------
# Chargement du modele TFLite
# ---------------------------------------------------------------------------

def charger_modele(chemin_modele):
    """Charge le modele TFLite et alloue les tenseurs."""
    try:
        import tflite_runtime.interpreter as tflite
    except ImportError:
        try:
            import tensorflow as tf
            tflite = tf.lite
        except ImportError:
            print("[ERREUR] TensorFlow Lite non installe.")
            print("Installer avec : pip install tflite-runtime")
            sys.exit(1)

    if not os.path.exists(chemin_modele):
        print(f"[ERREUR] Modele non trouve : {chemin_modele}")
        print("Lancez d'abord : notebook/training_efficientnet.ipynb")
        sys.exit(1)

    interpreter = tflite.Interpreter(model_path=chemin_modele)
    interpreter.allocate_tensors()
    print(f"[OK] Modele charge : {chemin_modele}")
    return interpreter


def charger_labels(chemin_labels):
    """Charge la liste des classes."""
    if not os.path.exists(chemin_labels):
        print(f"[ERREUR] Fichier labels non trouve : {chemin_labels}")
        sys.exit(1)
    with open(chemin_labels, 'r') as f:
        labels = [l.strip() for l in f.readlines()]
    print(f"[OK] {len(labels)} classes chargees")
    return labels


def charger_besoins_hydriques(chemin_json):
    """Charge le mapping espece -> besoins hydriques."""
    if os.path.exists(chemin_json):
        with open(chemin_json, 'r') as f:
            return json.load(f)
    print(f"[INFO] Fichier besoins non trouve, utilisation config.py")
    return BESOINS_PAR_ESPECE


# ---------------------------------------------------------------------------
# Preprocessing image
# ---------------------------------------------------------------------------

def preparer_image(image_np):
    """
    Prepare une image numpy pour EfficientNet-B3.
    Entree : image RGB numpy (H, W, 3)
    Sortie : tensor (1, 300, 300, 3) normalise ImageNet
    """
    try:
        import cv2
    except ImportError:
        print("[ERREUR] opencv non installe : pip install opencv-python-headless")
        sys.exit(1)

    image = cv2.resize(image_np, (300, 300))
    image = image.astype(np.float32)
    # Normalisation ImageNet
    mean = np.array([0.485, 0.456, 0.406]) * 255.0
    std  = np.array([0.229, 0.224, 0.225]) * 255.0
    image = (image - mean) / std
    return np.expand_dims(image, axis=0)


# ---------------------------------------------------------------------------
# Acquisition image
# ---------------------------------------------------------------------------

def capturer_camera():
    """Capture une image avec la camera Raspberry Pi."""
    try:
        from picamera2 import Picamera2
        cam = Picamera2()
        config = cam.create_still_configuration(
            main={"size": RESOLUTION_CAMERA, "format": "RGB888"}
        )
        cam.configure(config)
        cam.start()
        time.sleep(0.5)  # Stabilisation
        image = cam.capture_array()
        cam.stop()
        cam.close()
        print("[OK] Image capturee depuis la camera Pi")
        return image
    except Exception as e:
        print(f"[ERREUR] Camera : {e}")
        sys.exit(1)


def charger_image_fichier(chemin):
    """Charge une image depuis un fichier."""
    try:
        import cv2
        image = cv2.imread(chemin)
        if image is None:
            print(f"[ERREUR] Impossible de lire : {chemin}")
            sys.exit(1)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        print(f"[OK] Image chargee : {chemin} ({image.shape[1]}x{image.shape[0]})")
        return image
    except Exception as e:
        print(f"[ERREUR] {e}")
        sys.exit(1)


def image_simulation():
    """Genere une image de test (bruit aleatoire) en mode simulation."""
    print("[SIM] Generation image de test aleatoire")
    return np.random.randint(0, 255, (*RESOLUTION_CAMERA[::-1], 3), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def map_classe_espece(nom_classe):
    """Mappe un nom de classe PlantVillage vers une espece connue."""
    nom = nom_classe.lower()
    if 'tomato' in nom or 'tomate' in nom:
        return 'tomate_cerise' if ('cherry' in nom) else 'tomate'
    if 'olive' in nom or 'olivier' in nom:
        return 'olivier'
    for espece in BESOINS_PAR_ESPECE:
        if espece in nom:
            return espece
    return 'inconnu'


def inference(interpreter, labels, besoins_hydriques, image_np):
    """
    Effectue l'inference et retourne les resultats complets.
    """
    input_details  = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    t0 = time.time()
    image_prep = preparer_image(image_np)
    interpreter.set_tensor(input_details[0]['index'], image_prep)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])[0]
    temps_inference = round((time.time() - t0) * 1000, 1)

    # Top-3 predictions
    top3_idx = np.argsort(output)[::-1][:3]

    resultats = []
    for i, idx in enumerate(top3_idx):
        classe = labels[idx] if idx < len(labels) else f'classe_{idx}'
        confiance = float(output[idx])
        espece = map_classe_espece(classe)
        besoins = besoins_hydriques.get(espece, BESOINS_PAR_ESPECE.get('inconnu', {}))
        resultats.append({
            'rang': i + 1,
            'classe_brute': classe,
            'espece': espece,
            'confiance': confiance,
            'besoins': besoins
        })

    return resultats, temps_inference


def afficher_resultats(resultats, temps_ms):
    """Affiche les resultats de maniere claire."""
    print("\n" + "=" * 55)
    print("  RESULTATS DE LA DETECTION")
    print("=" * 55)
    print(f"  Temps d'inference : {temps_ms} ms\n")

    meilleur = resultats[0]
    fiable = meilleur['confiance'] >= SEUIL_CONFIANCE_MIN

    print(f"  Espece detectee   : {meilleur['espece'].upper()}")
    print(f"  Classe brute      : {meilleur['classe_brute']}")
    print(f"  Confiance         : {meilleur['confiance']:.1%}")
    print(f"  Fiabilite         : {'OUI' if fiable else 'NON (< seuil)'}")

    if fiable:
        b = meilleur['besoins']
        print(f"\n  Besoins hydriques :")
        print(f"    Humidite min    : {b.get('humidite_min', '?')}%")
        print(f"    Humidite max    : {b.get('humidite_max', '?')}%")
        print(f"    Duree arrosage  : {b.get('duree_arrosage', '?')}s")

    print("\n  Top-3 predictions :")
    for r in resultats:
        print(f"    {r['rang']}. {r['classe_brute']:<40} {r['confiance']:.1%}")

    print("=" * 55)
    return meilleur, fiable


# ---------------------------------------------------------------------------
# Mode simulation
# ---------------------------------------------------------------------------

def run_simulation():
    """Simule une detection sans materiel."""
    import random
    especes = ['tomate', 'tomate', 'tomate', 'olivier', 'inconnu']
    espece = random.choice(especes)
    confiance = round(random.uniform(0.72, 0.95), 3)
    besoins = BESOINS_PAR_ESPECE.get(espece, {})

    print("\n" + "=" * 55)
    print("  RESULTATS SIMULATION")
    print("=" * 55)
    print(f"  Espece detectee   : {espece.upper()}")
    print(f"  Confiance         : {confiance:.1%}")
    print(f"  Besoins hydriques :")
    print(f"    Humidite min    : {besoins.get('humidite_min', 60)}%")
    print(f"    Humidite max    : {besoins.get('humidite_max', 80)}%")
    print(f"    Duree arrosage  : {besoins.get('duree_arrosage', 10)}s")
    print("=" * 55)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Test du modele de detection de plantes PLBD-36'
    )
    parser.add_argument('--image', type=str, default=None,
                        help='Chemin vers une image (defaut: camera Pi)')
    parser.add_argument('--simulation', action='store_true',
                        help='Mode simulation sans materiel')
    parser.add_argument('--modele', type=str, default=MODELE_TFLITE_PATH,
                        help=f'Chemin modele TFLite (defaut: {MODELE_TFLITE_PATH})')
    parser.add_argument('--labels', type=str, default=LABELS_PATH,
                        help='Chemin fichier classes.txt')
    args = parser.parse_args()

    print("=" * 55)
    print("  TEST DETECTION PLANTES -- PLBD-36")
    print("  Groupe 36 | Ecole Centrale Casablanca")
    print("=" * 55)

    if args.simulation:
        run_simulation()
        return

    # Chargement modele et labels
    interpreter = charger_modele(args.modele)
    labels = charger_labels(args.labels)
    besoins = charger_besoins_hydriques(BESOINS_HYDRIQUES_PATH)

    # Acquisition image
    if args.image:
        image = charger_image_fichier(args.image)
    else:
        print("[INFO] Aucune image specifiee -- utilisation camera Pi")
        image = capturer_camera()

    # Inference
    resultats, temps_ms = inference(interpreter, labels, besoins, image)

    # Affichage
    afficher_resultats(resultats, temps_ms)


if __name__ == '__main__':
    main()
