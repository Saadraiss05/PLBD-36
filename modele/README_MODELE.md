# 📁 Dossier modele/ — Fichiers ML du robot PLBD-36

Ce dossier contient (ou doit contenir) les fichiers issus de l'entraînement du modèle.

## Fichiers attendus

| Fichier | Taille approx. | Description |
|---------|---------------|-------------|
| `efficientnet_b3_plants.tflite` | ~15-40 MB | Modèle TFLite pour déploiement Raspberry Pi |
| `efficientnet_b3_plants_complet.pth` | ~45 MB | Checkpoint PyTorch complet (entraînement/dev) |
| `classes.txt` | ~1 KB | Liste des noms de classes PlantVillage |
| `besoins_hydriques.json` | ~2 KB | Mapping classes → seuils d'arrosage par espèce |
| `matrice_confusion.png` | ~200 KB | Visualisation performances du modèle |

## ⚠️ Pourquoi ces fichiers ne sont pas dans Git ?

Les fichiers `.tflite` et `.pth` sont trop lourds pour Git standard (>10 MB).
Ils sont exclus via `.gitignore`. Deux options :

1. **Git LFS** (recommandé) : `git lfs track "modele/*.tflite"`
2. **Partage manuel** : partager via Google Drive / clé USB au sein de l'équipe

## 🚀 Comment générer ces fichiers ?

Lance le notebook d'entraînement sur un PC avec GPU :

```bash
cd notebook/
jupyter notebook training_efficientnet.ipynb
```

Le notebook génère automatiquement tous les fichiers ci-dessus dans ce dossier.

## 📐 Format du fichier classes.txt

```
Tomato___Bacterial_spot
Tomato___Early_blight
Tomato___healthy
Pepper___healthy
...
```

## 📐 Format du fichier besoins_hydriques.json

```json
{
  "tomate": {
    "humidite_min": 60,
    "humidite_max": 80,
    "duree_arrosage": 10,
    "intervalle_min": 3600
  },
  ...
}
```
