#!/usr/bin/env python3
# =============================================================================
# scripts/calibration_humidite.py -- Calibration du capteur d'humidite sol
# Groupe 36 | Ecole Centrale Casablanca | Projet PLBD-36
#
# A executer UNE SEULE FOIS apres avoir connecte le capteur MCP3008.
# Permet de determiner ADC_VALEUR_SEC et ADC_VALEUR_HUMIDE pour config.py.
#
# Usage:
#   python scripts/calibration_humidite.py
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import spidev
    SPI_DISPONIBLE = True
except ImportError:
    SPI_DISPONIBLE = False
    print("[ERREUR] spidev non installe : pip install spidev")
    print("[INFO] Mode affichage des instructions uniquement")


def lire_adc(spi, canal=0):
    """Lit la valeur brute du MCP3008 (0-1023) sur un canal."""
    adc = spi.xfer2([1, (8 + canal) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]


def moyenne_lectures(spi, canal=0, n=10, delai=0.1):
    """Prend n lectures et retourne la moyenne."""
    valeurs = []
    for _ in range(n):
        valeurs.append(lire_adc(spi, canal))
        time.sleep(delai)
    return round(sum(valeurs) / len(valeurs), 1)


def main():
    print("=" * 55)
    print("  CALIBRATION CAPTEUR HUMIDITE SOL -- PLBD-36")
    print("=" * 55)
    print()
    print("Ce script va mesurer les valeurs ADC brutes du capteur")
    print("dans deux conditions : SOL SEC et SOL HUMIDE.")
    print("Ces valeurs seront a copier dans config/config.py.")
    print()
    print("Connexion MCP3008 :")
    print("  VCC  -> 3.3V Pi")
    print("  GND  -> GND Pi")
    print("  CLK  -> GPIO11 (SCLK)")
    print("  DOUT -> GPIO9  (MISO)")
    print("  DIN  -> GPIO10 (MOSI)")
    print("  CS   -> GPIO8  (CE0)")
    print("  CH0  -> Signal capteur humidite")
    print()

    if not SPI_DISPONIBLE:
        print("[SIMULATION] spidev non disponible")
        print("Valeurs typiques pour reference :")
        print("  ADC_VALEUR_SEC    = 800  (sol completement sec)")
        print("  ADC_VALEUR_HUMIDE = 300  (sol bien humide)")
        print()
        print("Copiez ces valeurs dans config/config.py et ajustez apres test reel.")
        return

    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1350000

    resultats = {}

    try:
        # --- Etape 1 : Sol sec ---
        print("ETAPE 1 : Mesure sol SEC")
        print("-" * 40)
        print("Placez le capteur dans de la TERRE SECHE (ou a l'air libre)")
        input("Appuyez sur ENTREE quand pret...")
        print("Lecture en cours (10 mesures)...")
        val_sec = moyenne_lectures(spi)
        print(f"  --> Valeur ADC SOL SEC : {val_sec}")
        resultats['sec'] = val_sec
        print()

        # --- Etape 2 : Sol humide ---
        print("ETAPE 2 : Mesure sol HUMIDE")
        print("-" * 40)
        print("Placez le capteur dans de la TERRE BIEN ARROSEE (ou dans l'eau)")
        input("Appuyez sur ENTREE quand pret...")
        print("Lecture en cours (10 mesures)...")
        val_humide = moyenne_lectures(spi)
        print(f"  --> Valeur ADC SOL HUMIDE : {val_humide}")
        resultats['humide'] = val_humide
        print()

        # --- Etape 3 : Test en continu ---
        print("ETAPE 3 : Test de verification (30 secondes)")
        print("-" * 40)
        print("Deplacez le capteur entre sol sec et humide pour verifier...")
        print("(Ctrl+C pour arreter)")
        t_debut = time.time()
        while time.time() - t_debut < 30:
            val = lire_adc(spi)
            pct = (val_sec - max(val_humide, min(val_sec, val))) / (val_sec - val_humide) * 100
            pct = max(0, min(100, pct))
            barre = '#' * int(pct / 5) + '-' * (20 - int(pct / 5))
            print(f"  ADC={val:4d} | Humidite~{pct:5.1f}% [{barre}]", end='', flush=True)
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("
[OK] Verification terminee")
    finally:
        spi.close()

    # --- Resultats finaux ---
    print()
    print("=" * 55)
    print("  RESULTATS DE CALIBRATION")
    print("=" * 55)
    print(f"  ADC_VALEUR_SEC    = {int(resultats.get('sec', 800))}")
    print(f"  ADC_VALEUR_HUMIDE = {int(resultats.get('humide', 300))}")
    print()
    print("Copiez ces valeurs dans config/config.py :")
    print()
    print(f"  ADC_VALEUR_SEC    = {int(resultats.get('sec', 800))}")
    print(f"  ADC_VALEUR_HUMIDE = {int(resultats.get('humide', 300))}")
    print()

    # Sauvegarder dans un fichier
    os.makedirs('logs', exist_ok=True)
    with open('logs/calibration_humidite.txt', 'w') as f:
        f.write(f"ADC_VALEUR_SEC = {int(resultats.get('sec', 800))}\n")
        f.write(f"ADC_VALEUR_HUMIDE = {int(resultats.get('humide', 300))}\n")
    print("Sauvegarde : logs/calibration_humidite.txt")


if __name__ == '__main__':
    main()
