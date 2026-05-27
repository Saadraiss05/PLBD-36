# 🤖 PLBD-36 — Robot d'Irrigation Intelligent

**Groupe 36 | École Centrale Casablanca**

Projet de conception d'un robot autonome d'irrigation intelligent pour l'agriculture marocaine, capable de :
- Identifier visuellement les espèces de plantes (via vision par ordinateur)
- Mesurer le taux d'humidité du sol
- Décider d'arroser ou non selon l'espèce et les besoins hydriques
- Naviguer de manière autonome (suivi de ligne + détection d'obstacles)

## 🌱 Culture de référence
**Tomate** (culture de l'agriculteur interrogé lors de l'enquête terrain au Maroc)

## 🛠️ Matériel utilisé
| Composant | Rôle |
|-----------|------|
| Raspberry Pi Zero 2 W | Cerveau du robot |
| Caméra Pi 5MP | Vision par ordinateur |
| Capteur humidité analogique + MCP3008 | Mesure humidité sol |
| Capteur ultrason HC-SR04 | Détection d'obstacles |
| Pompe 12V + Relais 5V | Irrigation |
| 2 moteurs DC + L298N | Déplacement |
| Capteur IR suiveur de ligne | Navigation |
| Panneau solaire + Batterie | Alimentation |

## 📁 Structure du projet
```
PLBD-36/
├── main.py                    # Programme principal
├── requirements.txt           # Dépendances Python
├── config/
│   └── config.py              # Configuration centralisée (broches GPIO, seuils)
├── modules/
│   ├── vision.py              # Reconnaissance visuelle (TensorFlow Lite / EfficientNet-B3)
│   ├── capteur_humidite.py    # Capteur humidité sol (analogique via MCP3008)
│   ├── capteur_ultrasons.py   # Capteur HC-SR04 (détection obstacles)
│   ├── capteur_niveau_eau.py  # Niveau réservoir
│   ├── pompe_eau.py           # Pompe via relais 5V
│   ├── moteurs.py             # Moteurs DC via L298N
│   └── suiveur_ligne.py       # Capteur infrarouge suivi de ligne
└── notebook/
    └── training_efficientnet.ipynb  # Entraînement modèle de vision (PC/GPU)
```

## 🚀 Installation

```bash
# Cloner le repo
git clone https://github.com/Saadraiss05/PLBD-36.git
cd PLBD-36

# Installer les dépendances
pip install -r requirements.txt

# Lancer en mode simulation (sans matériel)
python main.py
```

## ⚙️ Configuration
Tous les paramètres sont dans `config/config.py` :
- Broches GPIO (Raspberry Pi Zero 2 W)
- Seuils d'humidité par espèce
- Mode simulation (True/False)

## ⚠️ Points de sécurité câblage
1. **HC-SR04 ECHO (5V)** → diviseur de tension obligatoire (R1=1kΩ + R2=2kΩ)
2. **Pompe 12V** → jamais directement sur GPIO, toujours via relais 5V
3. **L298N** → alimentation puissance séparée, masse commune avec Pi

## 👥 Équipe
Groupe 36 — École Centrale Casablanca
