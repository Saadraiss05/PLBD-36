# CLAUDE.md — Contexte projet PLBD-36

> Ce fichier est lu automatiquement par Claude Code à chaque session.
> Il contient tout le contexte nécessaire pour bosser sur ce repo.

## 🎯 Projet

**Robot d'irrigation intelligent PLBD-36** — Projet de groupe à l'École Centrale Casablanca, Groupe 36.

Robot autonome qui :
- Identifie visuellement les plantes (vision par ordinateur, EfficientNet-B3 / TFLite)
- Mesure l'humidité du sol (capteur analogique via MCP3008)
- Décide d'arroser selon les besoins de l'espèce
- Navigue (suivi de ligne IR + évitement obstacles ultrasons)

**Culture de référence :** Tomate (enquête terrain Maroc).

## 🛠️ Stack technique

- **Plateforme cible :** Raspberry Pi Zero 2 W
- **Langage :** Python 3
- **ML :** PyTorch (entraînement) → TensorFlow Lite (déploiement)
- **Hardware :** Caméra Pi, MCP3008 (SPI), HC-SR04, L298N, relais 5V, pompe 12V

## ⏰ Contexte temporel

**Soutenance avec démo dans 1 mois.** Priorité absolue : que la démo marche sans accroc.

- Le notebook d'entraînement n'a **jamais tourné** → priorité à ce qu'il marche du premier coup
- Le matériel n'est **pas encore monté** (un composant en attente) → tout doit être validé en `MODE_SIMULATION = True` d'abord
- Le passage simu → réel doit se faire en basculant un seul flag

## 📐 Architecture du code

```
PLBD-36/
├── main.py                      # Orchestrateur principal du robot
├── config/config.py             # Configuration centralisée (pins GPIO, seuils, etc.)
├── modules/
│   ├── gpio_manager.py          # Singleton GPIO (setmode + cleanup atexit)
│   ├── vision.py                # Reconnaissance plantes (TFLite + caméra)
│   ├── capteur_humidite.py      # MCP3008 SPI ou GPIO numérique
│   ├── capteur_ultrasons.py     # HC-SR04 (obstacles)
│   ├── capteur_niveau_eau.py    # Niveau réservoir
│   ├── pompe_eau.py             # Pompe 12V via relais 5V (NON-BLOQUANT)
│   ├── moteurs.py               # 2 moteurs DC via L298N
│   └── suiveur_ligne.py         # IR pour suivi de ligne
├── utils/logger.py              # Logger coloré console + fichier rotatif
├── scripts/                     # Outils standalone (calibration, tests, démo)
├── tests/                       # Tests pytest (sans matériel)
├── notebook/                    # Entraînement EfficientNet-B3
└── modele/                      # .tflite, classes.txt, besoins_hydriques.json
```

## 🔒 Conventions critiques

### Sécurité (NE JAMAIS ENFREINDRE)
- **Pompe 12V** → JAMAIS directement sur GPIO, TOUJOURS via relais 5V
- **HC-SR04 ECHO (5V)** → diviseur de tension obligatoire (R1=1kΩ + R2=2kΩ)
- **L298N** → alimentation puissance séparée, MASSE COMMUNE avec le Pi
- **Arrosage** → toujours non-bloquant et interruptible (boucle 100ms qui check niveau eau + flag d'arrêt)
- **Watchdog atexit** → garantit l'arrêt du relais et le cleanup GPIO même en cas de crash

### Code
- Tous les modules utilisent `from utils.logger import get_logger`
- Tous les modules GPIO passent par `gpio_manager` (jamais de `GPIO.setmode(BCM)` direct)
- En cas d'erreur de lecture capteur : retourner `None`, JAMAIS 0 (un 0 ferait croire à un sol sec → arrosage)
- Mode simulation : `MODE_SIMULATION = True` dans `config/config.py`, doit fonctionner sur PC sans matériel
- Encodage : UTF-8 sans accents dans le code (commentaires en français mais sans é/à pour compat Windows)

## 📋 Plan d'optimisation en cours (3 vagues)

### ✅ VAGUE 1 — Bugs critiques & sécurité (FAIT)
- [x] Logger centralisé (utils/logger.py)
- [x] GPIO manager (modules/gpio_manager.py)
- [x] Pompe non-bloquante + watchdog
- [x] Thread surveillance obstacles dans main.py
- [x] Fix bug humidité retourne None au lieu de 0
- [x] Fix calibration_humidite.py (sauts de ligne cassés)

### 🚧 VAGUE 2 — Robustesse démo & qualité (À FAIRE)
- [ ] Tests pytest dans tests/ (sans matériel, ~30 tests)
- [ ] `scripts/demo_soutenance.py` ← ⭐ CRITIQUE POUR LA DÉMO
  - Scénarios déterministes (seed fixée)
  - Affichage bluffant avec couleurs + emojis
  - Modes --auto et --step
  - Doit montrer : tomate sèche → arrose, sol OK → pas d'arrosage, obstacle → stoppe, réservoir vide → arrêt
- [ ] Refonte scripts/inference_test.py et test_materiels.py avec logger
- [ ] Refonte scripts/decision_arrosage.py avec logger
- [ ] Remplacer tous les `except: pass` par `except Exception as e: logger.warning(...)`
- [ ] Type hints sur les API publiques
- [ ] CI GitHub Actions ultra-simple (pytest sur push)

### 🚧 VAGUE 3 — Perfs Pi + docs + bonus (À FAIRE)
- [ ] Fix bug random_split dans le notebook (transform_val écrase aussi train_ds)
- [ ] Ajout quantification int8 dans le notebook → modèle 3-4x plus rapide sur Pi Zero 2 W
- [ ] Notebook robuste (versions pinned, gestion mémoire Colab)
- [ ] Thread caméra séparé pour pipeline
- [ ] README enrichi avec schémas, diagramme de cycle, section démo
- [ ] requirements-dev.txt séparé

## 🎤 Pour la soutenance

Le script `scripts/demo_soutenance.py` (à créer) est la pièce maîtresse. Il doit :
- Tourner en `MODE_SIMULATION = True` avec une seed déterministe (résultats reproductibles)
- Afficher chaque étape clairement (l'oral expliquera ce qui se passe)
- Démontrer les sécurités (obstacle, réservoir vide, intervalle minimum)
- Pouvoir tourner en mode `--auto` (démo continue) ou `--step` (validation manuelle de chaque étape)

## 💬 Comment je travaille avec toi

- Demande-moi de te montrer le `git diff` avant tout commit
- Crée une branche par vague (ex: `optimisations-vague-2`) plutôt que de pousser direct sur main
- Préfère les petits commits ciblés ("feat: ajout demo_soutenance.py") plutôt qu'un gros commit fourre-tout
- Lance les tests pytest avant de commit si la vague 2 est en place
- Si tu touches au notebook : ne lance pas l'entraînement, juste valide la syntaxe Python

## 🚫 Choses à NE PAS faire

- Ne JAMAIS modifier les valeurs de sécurité (`DUREE_MAX_POMPE_SEC`, `DISTANCE_OBSTACLE_CM`) sans demander
- Ne JAMAIS supprimer les watchdogs atexit
- Ne JAMAIS désactiver le `MODE_SIMULATION` par défaut dans le repo (l'agriculteur de l'équipe le mettra à False sur le Pi)
- Ne JAMAIS commit dans `modele/` (fichiers .tflite trop lourds, déjà dans .gitignore)
- Ne JAMAIS pousser sans avoir montré le diff
