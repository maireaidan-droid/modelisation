# Dragon Long (dragon chinois stylisé) : v1, premier croquis

Modèle low-poly à facettes pour Roblox, inspiré du dragon chinois (Long) : corps de serpent en S,
ventre doré, crinière et épines rouges, cornes en bois de cerf, moustaches, 4 pattes à 3 griffes, yeux qui brillent.

![aperçu](apercu-Dragon_Long_v1.png)

- **Fichier à importer** : `objets/Dragon_Long_v1.glb` (environ 3 000 triangles, 14 × 18,5 × 57 studs)
- **Couleurs et matériaux** de chaque partie : `objets/manifest.json`

| Partie | Couleur | Matériau |
|---|---|---|
| Body | `#2F7D63` jade | SmoothPlastic |
| Belly | `#E2B65C` doré | SmoothPlastic |
| Fins | `#C8432F` rouge | SmoothPlastic |
| Horns (cornes, griffes, dents) | `#E6DCC3` ivoire | SmoothPlastic |
| Whiskers | `#F0C24B` or | SmoothPlastic |
| Eyes | `#FFD23F` | **Neon** |

## Import dans Roblox Studio
**Avatar → Import 3D**, unité **Stud**, parties séparées. Le pivot est sous le dragon (Y = 0) et la tête regarde vers +Z.
Pour les nageoires, mettre `DoubleSided = true` si elles disparaissent sous certains angles.

## Régénérer
```
pip install numpy trimesh matplotlib scipy
cd dragon-long/generateur && python build.py
```
La forme se règle dans `dragon_long.py` : `SPINE` (la ligne du dos), `body_radius` (l'épaisseur), `COULEURS`.
