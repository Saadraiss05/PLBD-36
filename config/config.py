# =============================================================================
# config/config.py — Configuration centralisée du robot PLBD-36
# Raspberry Pi Zero 2 W + Python
# =============================================================================

# ---------------------------------------------------------------------------
# MODE SIMULATION (True = pas de GPIO réel, pour développer sur PC)
# ---------------------------------------------------------------------------
MODE_SIMULATION = True  # Mettre False sur la vraie Raspberry Pi

# ---------------------------------------------------------------------------
# BROCHES GPIO — Raspberry Pi Zero 2 W (numérotation BCM)
# ---------------------------------------------------------------------------

# Capteur ultrason HC-SR04
TRIG_PIN = 23
ECHO_PIN = 24

# Capteur d'humidité via MCP3008 (SPI)
USE_ADC = True           # True = capteur analogique via MCP3008
HUMIDITE_GPIO_PIN = 17   # Utilisé seulement si USE_ADC = False (capteur numérique)

# MCP3008 SPI (canal 0 pour humidité)
SPI_BUS = 0
SPI_DEVICE = 0
HUMIDITE_CANAL_ADC = 0   # Canal MCP3008 pour le capteur d'humidité

# Pompe à eau — pilotée via relais 5V
RELAIS_PIN = 18
RELAIS_ACTIF_BAS = True  # True si le relais se déclenche sur signal LOW (très courant)

# Capteur niveau d'eau du réservoir
NIVEAU_EAU_PIN = 25

# Moteurs DC — driver L298N
# Moteur gauche
MOTEUR_GAUCHE_IN1 = 5
MOTEUR_GAUCHE_IN2 = 6
MOTEUR_GAUCHE_PWM = 12   # Broche PWM pour vitesse

# Moteur droit
MOTEUR_DROIT_IN1 = 13
MOTEUR_DROIT_IN2 = 19
MOTEUR_DROIT_PWM = 16    # Broche PWM pour vitesse

# Vitesse par défaut (0-100)
VITESSE_DEFAUT = 60

# Capteur suiveur de ligne infrarouge
SUIVI_LIGNE_PIN_GAUCHE = 20
SUIVI_LIGNE_PIN_DROIT = 21

# Caméra Raspberry Pi
RESOLUTION_CAMERA = (640, 480)
FRAMERATE = 30

# ---------------------------------------------------------------------------
# CAPTEUR D'HUMIDITÉ — Calibration
# ---------------------------------------------------------------------------
# Valeurs ADC brutes (0-1023) pour votre capteur spécifique
# À calibrer en plongeant le capteur dans de la terre sèche vs humide
ADC_VALEUR_SEC = 800    # Valeur ADC quand le sol est sec
ADC_VALEUR_HUMIDE = 300 # Valeur ADC quand le sol est bien humide

# ---------------------------------------------------------------------------
# MODÈLE DE VISION — TensorFlow Lite
# ---------------------------------------------------------------------------
MODELE_TFLITE_PATH = "modele/efficientnet_b3_plants.tflite"
LABELS_PATH = "modele/classes.txt"
BESOINS_HYDRIQUES_PATH = "modele/besoins_hydriques.json"
SEUIL_CONFIANCE_MIN = 0.5   # Confiance minimale pour accepter une prédiction

# ---------------------------------------------------------------------------
# BESOINS HYDRIQUES PAR ESPÈCE
# La tomate est notre culture de référence (agriculteur interrogé lors enquête terrain)
# ---------------------------------------------------------------------------
BESOINS_PAR_ESPECE = {
    # TOMATE — Culture de référence (enquête terrain, Maroc)
    "tomate": {
        "humidite_min": 60,   # % d'humidité minimale avant arrosage
        "humidite_max": 80,   # % d'humidité maximale (risque pourriture racinaire)
        "duree_arrosage": 10, # secondes d'arrosage par déclenchement
        "intervalle_min": 3600, # secondes entre deux arrosages (1h minimum)
    },
    "tomate_cerise": {
        "humidite_min": 60,
        "humidite_max": 75,
        "duree_arrosage": 8,
        "intervalle_min": 3600,
    },
    # OLIVE
    "olivier": {
        "humidite_min": 30,   # L'olivier tolère la sécheresse
        "humidite_max": 60,
        "duree_arrosage": 15,
        "intervalle_min": 7200,
    },
    # CULTURES GÉNÉRIQUES
    "plante_generique": {
        "humidite_min": 50,
        "humidite_max": 75,
        "duree_arrosage": 10,
        "intervalle_min": 3600,
    },
    # Fallback si espèce non reconnue
    "inconnu": {
        "humidite_min": 50,
        "humidite_max": 75,
        "duree_arrosage": 8,
        "intervalle_min": 3600,
    },
}

# ---------------------------------------------------------------------------
# SÉCURITÉ
# ---------------------------------------------------------------------------
DISTANCE_OBSTACLE_CM = 20    # Distance en cm déclenchant l'arrêt d'urgence
DUREE_MAX_POMPE_SEC = 30      # Durée maximale d'arrosage par sécurité
NIVEAU_EAU_MIN = False        # Valeur GPIO indiquant réservoir vide

# ---------------------------------------------------------------------------
# CYCLE DU ROBOT
# ---------------------------------------------------------------------------
INTERVALLE_CYCLE_SEC = 30    # Pause entre chaque cycle d'analyse (secondes)
