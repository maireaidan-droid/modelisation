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

---

## 7. Prompts ciblés : nez et zone des yeux

### Nez
```
Close-up of an eastern dragon nose, digital sculpture, clay render.
Broad bulbous feline snout, rounded fleshy nose pad split by a deep vertical groove,
two large round flared nostrils facing forward with thick rolled rims,
nostrils deeply carved with dark shadowed interiors, puffy upper lip lobes under the nose,
short nose bridge covered in small overlapping scales that blend into smooth skin
at the tip, horizontal wrinkle folds across the bridge, fine pebbled skin pores,
symmetrical, highly detailed sculpted surface, no texture color.
```

### Zone des yeux
```
Close-up of an eastern dragon eye area, digital sculpture, clay render.
Massive overhanging brow ridges forming a deep angry V-shaped frown,
thick fleshy brow folds pressing down on the eyes, deeply recessed narrow
almond eyes set in dark eye sockets, heavy hooded upper eyelids,
puffy rounded under-eye bags with stacked wrinkle folds, strong cheekbone bulges,
deep furrow between the brows running down to the nose bridge,
forehead above the brows covered in overlapping diamond scales,
pebbled reptile skin on the lids and cheeks, symmetrical, highly detailed sculpted surface.
```

### Retouches
| Objectif | Prompt |
|---|---|
| Narines plus marquées | `larger, rounder nostrils with thicker rims, deeper dark cavities` |
| Nez plus félin | `wider flatter nose pad, deeper central groove, shorter bridge` |
| Sourcils plus lourds | `heavier brow ridges overhanging the eyes, deeper V frown` |
| Yeux plus enfoncés | `push the eyes deeper into the sockets, narrower lids, stronger shadow` |
| Poches sous les yeux | `more pronounced puffy under-eye folds, layered wrinkles` |

---

## 8. Prompts de modification du dragon existant (nez et yeux)

À donner à l'IA qui travaille déjà sur le dragon (générateur `generateur/dragon_long.py`, version actuelle v4).
Chaque prompt ne touche qu'une zone, pour ne pas casser le reste.

### Nez
```
Sur le dragon existant (v4), modifie uniquement le nez. Ne touche ni aux yeux,
ni aux cornes, ni à la crinière, ni à la mâchoire, ni au corps.

Forme visée (référence : buste sculpté de dragon oriental) :
- truffe large et bombée, type félin/bouledogue, plus large que haute,
  qui reste fondue dans le crâne (pas de pièce collée) ;
- un sillon vertical profond au milieu qui sépare la truffe en deux lobes arrondis ;
- deux grosses narines rondes tournées vers l'avant, avec un bourrelet épais
  tout autour du bord, et un creux profond et sombre à l'intérieur ;
- sous la truffe, deux coussinets de lèvre supérieure gonflés, d'où partent les moustaches ;
- chanfrein court entre les yeux et la truffe, avec 2 ou 3 plis horizontaux
  et de petites écailles qui disparaissent en approchant de la truffe.

Contraintes : symétrie gauche/droite, style low-poly à facettes conservé,
garder les couleurs et matériaux du manifest (narines en Pupils),
rester sous ~13 000 triangles au total. Génère une v5 avec son aperçu,
compare-la à la v4 et ajuste si la truffe paraît collée ou trop pointue.
```

### Zone des yeux
```
Sur le dragon existant (v4), modifie uniquement la zone des yeux : arcades,
paupières, orbites, dessous des yeux et pommettes. Ne touche pas au nez,
aux cornes, à la crinière ni au corps.

Forme visée (référence : buste sculpté de dragon oriental) :
- arcades sourcilières massives qui avancent au-dessus des yeux et forment
  un V froncé et colérique, la pointe du V descendant vers le haut du nez ;
- un pli profond entre les deux arcades, qui file jusqu'au chanfrein ;
- yeux en amande étroits, enfoncés dans l'orbite, à moitié couverts par
  une paupière supérieure lourde (regard mi-clos, menaçant) ;
- sous chaque œil, une poche gonflée avec 2 plis superposés ;
- pommettes saillantes sous les poches, qui partent vers l'arrière de la tête ;
- au-dessus des arcades, le front couvert d'écailles en losange qui se chevauchent.

Contraintes : symétrie, style low-poly à facettes conservé, les yeux restent
en Neon et doivent rester visibles (ne pas les enterrer sous l'arcade),
garder les sourcils dorés en volutes mais les poser sur la nouvelle arcade,
rester sous ~13 000 triangles. Génère une v5 avec un aperçu de face
et un de profil, et vérifie qu'on voit encore les yeux de face.
```

### Retouches après un premier essai
| Problème | Prompt |
|---|---|
| Truffe qui paraît collée | `Fonds mieux la truffe dans le crâne : pas d'arête visible entre le chanfrein et la truffe.` |
| Narines trop petites | `Agrandis les narines de 30 %, épaissis leur bourrelet et creuse-les davantage.` |
| Nez trop pointu | `Aplatis et élargis la truffe, raccourcis le chanfrein.` |
| Regard pas assez méchant | `Fais descendre l'arcade de 15 % sur l'œil et accentue le V entre les sourcils.` |
| Yeux invisibles de face | `Recule légèrement l'arcade ou avance l'œil pour qu'il reste visible de face.` |
| Zone trop lisse | `Ajoute les plis sous les yeux et sur le chanfrein, sans dépasser le budget de triangles.` |

---

## 9. Prompt de modification : aspect de la peau du visage

```
Sur le dragon existant, modifie uniquement la surface de la peau du visage
(front, chanfrein, joues, paupières, lèvres). Ne change pas les volumes déjà
en place (nez, arcades, orbites, mâchoire), seulement leur relief de surface.

Aspect visé (référence : buste sculpté de dragon oriental) :
- front et dessus du chanfrein : écailles en losange qui se chevauchent comme
  des tuiles, pointes vers l'arrière, grandes au milieu du front et de plus en
  plus petites vers les yeux et la truffe ;
- joues, paupières et dessous des yeux : peau granuleuse « en galets »,
  petits bombements ronds serrés (peau de crocodile/iguane), pas d'écailles plates ;
- truffe et lèvres : peau plus lisse et charnue, juste quelques pores ;
- plis profonds aux endroits où la peau se tasse : entre les sourcils,
  sur le chanfrein, sous les yeux, au coin de la bouche ;
- le long des joues, une rangée de petites pointes coniques qui suivent
  la ligne de la mâchoire vers l'arrière ;
- transitions douces entre les zones : les écailles se transforment
  progressivement en galets, sans bord net.

Contraintes : relief sculpté dans la géométrie (pas peint en texture),
symétrie, couleurs et matériaux inchangés. Le modèle étant low-poly à facettes,
rester sous ~15 000 triangles : suggérer les écailles par des facettes
saillantes plutôt que de les modéliser une par une, et réserver le détail
au front et au chanfrein. Génère une nouvelle version avec un aperçu de face
et de trois quarts.
```

### Retouches
| Problème | Prompt |
|---|---|
| Peau trop lisse | `Accentue le relief des galets sur les joues et creuse davantage les plis.` |
| Trop de bruit, visage illisible | `Réduis la densité des écailles et garde les grands volumes lisibles.` |
| Écailles qui paraissent collées | `Fonds les écailles dans la peau : elles doivent sortir de la surface, pas posées dessus.` |
| Budget dépassé | `Supprime les écailles des zones peu visibles (dessous, arrière des joues).` |
