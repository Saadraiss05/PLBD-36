# =============================================================================
# modules/capteur_humidite.py — Lecture humidité du sol
# Supporte : capteur numérique GPIO ou analogique via MCP3008 (ADC SPI)
# =============================================================================

import time
from config.config import (
    MODE_SIMULATION, USE_ADC, HUMIDITE_GPIO_PIN,
    SPI_BUS, SPI_DEVICE, HUMIDITE_CANAL_ADC,
    ADC_VALEUR_SEC, ADC_VALEUR_HUMIDE
)

try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False

try:
    import spidev
    SPI_DISPONIBLE = True
except ImportError:
    SPI_DISPONIBLE = False


class CapteurHumidite:
    """
    Capteur d'humidité du sol.
    - Mode numérique (GPIO) : donne seulement humide/sec
    - Mode analogique (MCP3008 via SPI) : donne un % d'humidité (recommandé)
    """

    def __init__(self):
        self.spi = None
        self.initialise = False

        if MODE_SIMULATION:
            print("[Humidité] Mode SIMULATION")
            return

        if USE_ADC:
            self._init_spi()
        else:
            self._init_gpio()

    def _init_spi(self):
        """Initialise le bus SPI pour le MCP3008."""
        if not SPI_DISPONIBLE:
            print("[Humidité] spidev non disponible")
            return
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(SPI_BUS, SPI_DEVICE)
            self.spi.max_speed_hz = 1350000
            self.initialise = True
            print(f"[Humidité] SPI initialisé (bus={SPI_BUS}, device={SPI_DEVICE})")
        except Exception as e:
            print(f"[Humidité] Erreur init SPI : {e}")

    def _init_gpio(self):
        """Initialise le GPIO pour capteur numérique."""
        if not GPIO_DISPONIBLE:
            print("[Humidité] RPi.GPIO non disponible")
            return
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(HUMIDITE_GPIO_PIN, GPIO.IN)
            self.initialise = True
            print(f"[Humidité] GPIO pin {HUMIDITE_GPIO_PIN} initialisé")
        except Exception as e:
            print(f"[Humidité] Erreur init GPIO : {e}")

    def _lire_adc_brut(self, canal):
        """Lit la valeur brute du MCP3008 sur un canal (0-7). Retourne 0-1023."""
        if self.spi is None:
            return 0
        try:
            # Protocole de lecture MCP3008
            adc = self.spi.xfer2([1, (8 + canal) << 4, 0])
            valeur = ((adc[1] & 3) << 8) + adc[2]
            return valeur
        except Exception as e:
            print(f"[Humidité] Erreur lecture ADC : {e}")
            return 0

    def _convertir_en_pourcentage(self, valeur_brute):
        """
        Convertit la valeur ADC brute (0-1023) en % d'humidité.
        ADC haut = sol sec, ADC bas = sol humide (inversé sur la plupart des capteurs).
        Calibrez ADC_VALEUR_SEC et ADC_VALEUR_HUMIDE dans config.py.
        """
        valeur_clampee = max(ADC_VALEUR_HUMIDE, min(ADC_VALEUR_SEC, valeur_brute))
        pourcentage = (ADC_VALEUR_SEC - valeur_clampee) / (ADC_VALEUR_SEC - ADC_VALEUR_HUMIDE) * 100
        return round(pourcentage, 1)

    def lire_humidite(self):
        """
        Retourne le % d'humidité du sol (0-100).
        En mode simulation, retourne une valeur aléatoire réaliste.
        """
        if MODE_SIMULATION:
            import random
            # Simulation : humidité entre 35 et 75% (valeurs réalistes terrain Maroc)
            valeur = round(random.uniform(35, 75), 1)
            print(f"[Humidité SIM] {valeur}%")
            return valeur

        if USE_ADC:
            if not self.initialise:
                print("[Humidité] SPI non initialisé")
                return None
            valeur_brute = self._lire_adc_brut(HUMIDITE_CANAL_ADC)
            pourcentage = self._convertir_en_pourcentage(valeur_brute)
            print(f"[Humidité] ADC brut={valeur_brute} → {pourcentage}%")
            return pourcentage
        else:
            # Mode numérique (binaire : humide ou sec)
            if not GPIO_DISPONIBLE or not self.initialise:
                return None
            etat = GPIO.input(HUMIDITE_GPIO_PIN)
            # 0 = humide, 1 = sec (selon capteur)
            pourcentage = 30 if etat == 1 else 70
            print(f"[Humidité] GPIO état={etat} → ~{pourcentage}%")
            return pourcentage

    def sol_necessite_arrosage(self, humidite_actuelle, besoins_espece):
        """
        Décide si le sol doit être arrosé selon l'espèce et l'humidité.
        besoins_espece : dict avec humidite_min et humidite_max
        """
        if humidite_actuelle is None:
            print("[Humidité] Lecture impossible — arrosage par prudence")
            return False  # Sécurité : pas d'arrosage si lecture échoue

        humidite_min = besoins_espece.get('humidite_min', 50)
        humidite_max = besoins_espece.get('humidite_max', 80)

        if humidite_actuelle < humidite_min:
            print(f"[Humidité] Sol trop sec ({humidite_actuelle}% < {humidite_min}%) → ARROSAGE")
            return True
        elif humidite_actuelle > humidite_max:
            print(f"[Humidité] Sol trop humide ({humidite_actuelle}% > {humidite_max}%) → pas d'arrosage")
            return False
        else:
            print(f"[Humidité] Sol OK ({humidite_actuelle}%, optimal {humidite_min}-{humidite_max}%) → pas d'arrosage")
            return False

    def fermer(self):
        """Libère les ressources SPI."""
        if self.spi:
            try:
                self.spi.close()
                print("[Humidité] SPI fermé")
            except:
                pass
