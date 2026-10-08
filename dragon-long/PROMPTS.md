# Prompts IA pour la modélisation du Dragon Long

Prompts conçus pour les générateurs 3D par IA (Meshy, Tripo, Rodin/Hyper3D, Hunyuan3D, Higgsfield 3D…)
et pour les générateurs d'images qui servent de référence (Midjourney, Flux, SDXL…).
Référence visée : buste de dragon oriental façon sculpture ZBrush, rendu argile.

> Astuce : les prompts sont en anglais car la plupart des modèles 3D sont entraînés en anglais.
> Évitez les noms de personnages sous licence : décrivez la forme plutôt que le nom.

---

## 1. Image de référence (étape recommandée avant la 3D)

Les générateurs image→3D donnent de bien meilleurs résultats qu'en texte→3D.
Générez d'abord une vue de face propre, fond neutre, puis passez-la à l'outil 3D.

```
Front view of an eastern Chinese long dragon head bust, digital sculpture,
ZBrush clay render, matte grey-beige clay material, single object centered,
plain light grey background, soft studio lighting, no shadows on background,
symmetrical, full head visible with horns and whiskers,
heavy frowning brow ridges, deep-set angry eyes, feline nose with large round nostrils,
open mouth showing tongue and fangs, overlapping scales on the forehead and snout,
pebbled reptile skin texture, small spikes along the cheeks,
long swept-back mane of thick strands, two antler-like horns,
long thin whiskers coming out of the upper lip, highly detailed, 8k
```

Négatif (si l'outil le permet) :
```
color, painted texture, background scene, multiple heads, cropped, blurry,
low detail, cartoon flat shading, text, watermark, perspective distortion
```

### Vues orthographiques (pour multi-vue image→3D)

Remplacer `Front view` par chacune de ces lignes, en gardant le reste identique :
```
Left side orthographic view of ...
Back view of ...
Three-quarter view of ...
```
Ou en une seule image :
```
Character turnaround sheet, front / side / back orthographic views, same eastern dragon head bust, ...
```

---

## 2. Texte → 3D : tête seule (buste)

```
Highly detailed eastern long dragon head bust, sculpted like a ZBrush digital sculpture.
Thick heavy brow ridges forming an angry frown, deep eye sockets with fierce eyes,
broad feline nose with flared round nostrils, open mouth with visible tongue,
sharp fangs and rows of small teeth, lower jaw lined with a beard of short strands.
Forehead and snout covered in overlapping diamond scales, cheeks with pebbled skin
and small spikes. Two backward antler horns, a crest of tall spines between the horns,
long flowing mane of thick hair strands swept backwards, two long thin whiskers
from the upper lip. Symmetrical, watertight mesh, clean topology, clay material.
```

Réglages conseillés :
- Style : **Realistic / Sculpture** (pas « cartoon » ni « low poly »)
- Symétrie : **activée** (axe X)
- Polycount : élevé pour l'impression ou le rendu (≥ 200k), 30–50k pour le jeu
- Topologie : **quad** si disponible (meilleur pour Blender/ZBrush)
- Texture : désactivée ou PBR argile, la forme est la priorité

---

## 3. Texte → 3D : dragon entier

```
Full body eastern Chinese long dragon, serpentine body coiled in an S-shape,
four short legs with three-clawed talons, long body covered in overlapping scales,
smooth segmented belly plates, row of dorsal spines along the back,
fierce head with antler horns, flowing mane, long whiskers and open fanged mouth,
tail ending with a tuft of hair. Digital sculpture style, clay material,
symmetrical head, watertight mesh, clean topology, high detail.
```

Pour une pose spécifique :
```
... body rising vertically and spiraling upward, head looking down at the viewer ...
```

---

## 4. Prompts de raffinement (éditions ciblées)

À utiliser avec les outils qui acceptent une retouche (Meshy « Refine », Tripo « Edit », retouche d'image) :

| Objectif | Prompt |
|---|---|
| Regard plus menaçant | `deepen the eye sockets, heavier overhanging brows, narrower eyes` |
| Écailles plus nettes | `sharper, more defined overlapping scales on forehead and snout, crisp edges` |
| Peau | `add fine pebbled reptile skin pores on cheeks and lips, micro detail` |
| Bouche | `wider open jaw, longer upper fangs, visible curled tongue, gums detail` |
| Crinière | `thicker mane strands, grouped in clumps, swept back with flow` |
| Moustaches | `longer thin whiskers, slight S-curve, tapering ends` |
| Lisser les défauts | `remove noise and artifacts, keep sculpted details, smooth surfaces between scales` |

---

## 5. Prompt de rendu (présentation façon capture ZBrush)

```
Close-up portrait render of the dragon head sculpture, matcap clay material,
warm beige-grey, rim light from top left, soft ambient occlusion in crevices,
slight specular on scales, shallow depth of field, coiled body blurred in background
```

---

## 6. Méthode optimale (pipeline)

1. **Image de référence** de face (section 1), fond uni, rendu argile → c'est ce qui donne le plus de détails.
2. **Image → 3D** avec cette image (+ vues de côté/dos si l'outil gère le multi-vue).
3. **Raffinement** ciblé (section 4) sur les zones ratées : yeux, bouche, crinière.
4. **Retopologie / remesh** (quad remesh, ou Blender *Remesh* + *Decimate*) selon l'usage.
5. **Finition** dans Blender/ZBrush : écailles, moustaches fines (souvent ratées par l'IA → à modéliser en courbes), symétrie.
6. Export **.glb** dans `objets/` et ajout au `manifest.json`, comme les versions précédentes.

Points faibles connus des IA 3D sur ce sujet :
- éléments fins (moustaches, mèches, dents) fusionnés ou cassés → les ajouter à la main ;
- symétrie approximative → toujours forcer la symétrie ;
- détails d'écailles « peints » dans la texture plutôt que sculptés → demander *sculpted / displacement*, désactiver la texture.
