# =============================================================================
# modules/vision.py — Reconnaissance visuelle de plantes
# Utilise TensorFlow Lite avec EfficientNet-B3 pré-entraîné sur PlantVillage
# =============================================================================

import os
import json
import numpy as np
from config.config import (
    MODE_SIMULATION, MODELE_TFLITE_PATH, LABELS_PATH,
    BESOINS_HYDRIQUES_PATH, SEUIL_CONFIANCE_MIN,
    RESOLUTION_CAMERA, BESOINS_PAR_ESPECE
)

# Imports conditionnels (pas disponibles en mode simulation sur PC)
try:
    import tflite_runtime.interpreter as tflite
    TFLITE_DISPONIBLE = True
except ImportError:
    try:
        import tensorflow as tf
        tflite = tf.lite
        TFLITE_DISPONIBLE = True
    except ImportError:
        TFLITE_DISPONIBLE = False
        print("[Vision] TensorFlow Lite non disponible — mode simulation activé")

try:
    from picamera2 import Picamera2
    CAMERA_DISPONIBLE = True
except ImportError:
    CAMERA_DISPONIBLE = False
    print("[Vision] PiCamera2 non disponible — mode simulation activé")


class VisionPlante:
    """
    Module de reconnaissance visuelle des plantes.
    Utilise EfficientNet-B3 entraîné sur PlantVillage dataset.
    """

    def __init__(self):
        self.interpreter = None
        self.camera = None
        self.labels = []
        self.besoins_hydriques = {}
        self.initialise = False

        if not MODE_SIMULATION:
            self._charger_modele()
            self._charger_labels()
            self._init_camera()
        else:
            print("[Vision] Mode SIMULATION — pas de caméra ni de modèle réel")
            # Labels de démonstration pour la simulation
            self.labels = list(BESOINS_PAR_ESPECE.keys())

    def _charger_modele(self):
        """Charge le modèle TFLite EfficientNet-B3."""
        if not TFLITE_DISPONIBLE:
            print("[Vision] TFLite non disponible")
            return
        if not os.path.exists(MODELE_TFLITE_PATH):
            print(f"[Vision] Modèle non trouvé : {MODELE_TFLITE_PATH}")
            print("[Vision] Entraînez le modèle avec notebook/training_efficientnet.ipynb")
            return
        try:
            self.interpreter = tflite.Interpreter(model_path=MODELE_TFLITE_PATH)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.initialise = True
            print(f"[Vision] Modèle TFLite chargé : {MODELE_TFLITE_PATH}")
        except Exception as e:
            print(f"[Vision] Erreur chargement modèle : {e}")

    def _charger_labels(self):
        """Charge les noms de classes et les besoins hydriques."""
        if os.path.exists(LABELS_PATH):
            with open(LABELS_PATH, 'r', encoding='utf-8') as f:
                self.labels = [line.strip() for line in f.readlines()]
            print(f"[Vision] {len(self.labels)} classes chargées")

        if os.path.exists(BESOINS_HYDRIQUES_PATH):
            with open(BESOINS_HYDRIQUES_PATH, 'r', encoding='utf-8') as f:
                self.besoins_hydriques = json.load(f)
            print(f"[Vision] Besoins hydriques chargés pour {len(self.besoins_hydriques)} espèces")

    def _init_camera(self):
        """Initialise la caméra Raspberry Pi."""
        if not CAMERA_DISPONIBLE:
            print("[Vision] PiCamera2 non disponible")
            return
        try:
            self.camera = Picamera2()
            config = self.camera.create_still_configuration(
                main={"size": RESOLUTION_CAMERA, "format": "RGB888"}
            )
            self.camera.configure(config)
            self.camera.start()
            print("[Vision] Caméra initialisée")
        except Exception as e:
            print(f"[Vision] Erreur initialisation caméra : {e}")

    def _capturer_image(self):
        """Capture une image avec la caméra."""
        if self.camera is None:
            return None
        try:
            image = self.camera.capture_array()
            return image
        except Exception as e:
            print(f"[Vision] Erreur capture image : {e}")
            return None

    def _preparer_image(self, image):
        """
        Prétraite l'image pour EfficientNet-B3.
        Entrée attendue : (300, 300, 3), normalisé ImageNet.
        """
        try:
            import cv2
            image_resized = cv2.resize(image, (300, 300))
            image_float = image_resized.astype(np.float32)
            # Normalisation ImageNet
            mean = np.array([0.485, 0.456, 0.406]) * 255.0
            std = np.array([0.229, 0.224, 0.225]) * 255.0
            image_norm = (image_float - mean) / std
            return np.expand_dims(image_norm, axis=0)
        except Exception as e:
            print(f"[Vision] Erreur préparation image : {e}")
            return None

    def _map_classe_vers_espece(self, nom_classe):
        """
        Mappe un nom de classe PlantVillage vers une espèce gérée.
        PlantVillage utilise le format 'Tomato___Leaf_Mold', etc.
        """
        nom_lower = nom_classe.lower()

        # Tomate (culture de référence — enquête terrain Maroc)
        if 'tomato' in nom_lower or 'tomate' in nom_lower:
            if 'cherry' in nom_lower or 'cerise' in nom_lower:
                return 'tomate_cerise'
            return 'tomate'

        # Olivier
        if 'olive' in nom_lower or 'olivier' in nom_lower:
            return 'olivier'

        # Espèce générique connue
        for espece in BESOINS_PAR_ESPECE:
            if espece in nom_lower:
                return espece

        return 'inconnu'

    def identifier_plante(self):
        """
        Capture une image et identifie l'espèce de plante.
        Retourne un dict avec espece, confiance, besoins_hydriques.
        """
        if MODE_SIMULATION:
            # Simulation : retourne tomate avec confiance variable
            import random
            especes_sim = ['tomate', 'tomate', 'tomate', 'olivier', 'inconnu']
            espece = random.choice(especes_sim)
            confiance = round(random.uniform(0.72, 0.95), 2)
            besoins = BESOINS_PAR_ESPECE.get(espece, BESOINS_PAR_ESPECE['inconnu'])
            print(f"[Vision SIM] Espèce détectée : {espece} (confiance: {confiance:.0%})")
            return {
                'espece': espece,
                'confiance': confiance,
                'besoins': besoins,
                'classe_brute': f'Simulated_{espece}',
                'fiable': confiance >= SEUIL_CONFIANCE_MIN
            }

        if not self.initialise:
            print("[Vision] Modèle non initialisé — retour espèce inconnue")
            return self._resultat_inconnu()

        # Capture image
        image = self._capturer_image()
        if image is None:
            return self._resultat_inconnu()

        # Préparation
        image_prep = self._preparer_image(image)
        if image_prep is None:
            return self._resultat_inconnu()

        # Inférence TFLite
        try:
            self.interpreter.set_tensor(self.input_details[0]['index'], image_prep)
            self.interpreter.invoke()
            output = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

            idx_max = int(np.argmax(output))
            confiance = float(output[idx_max])

            if confiance < SEUIL_CONFIANCE_MIN:
                print(f"[Vision] Confiance trop faible ({confiance:.0%}) — espèce inconnue")
                return self._resultat_inconnu()

            classe_brute = self.labels[idx_max] if idx_max < len(self.labels) else 'inconnu'
            espece = self._map_classe_vers_espece(classe_brute)
            besoins = BESOINS_PAR_ESPECE.get(espece, BESOINS_PAR_ESPECE['inconnu'])

            print(f"[Vision] Espèce : {espece} | Classe : {classe_brute} | Confiance : {confiance:.0%}")
            return {
                'espece': espece,
                'confiance': confiance,
                'besoins': besoins,
                'classe_brute': classe_brute,
                'fiable': True
            }
        except Exception as e:
            print(f"[Vision] Erreur inférence : {e}")
            return self._resultat_inconnu()

    def _resultat_inconnu(self):
        """Retourne un résultat par défaut en cas d'erreur."""
        return {
            'espece': 'inconnu',
            'confiance': 0.0,
            'besoins': BESOINS_PAR_ESPECE['inconnu'],
            'classe_brute': 'unknown',
            'fiable': False
        }

    def fermer(self):
        """Libère les ressources."""
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                print("[Vision] Caméra fermée")
            except:
                pass
