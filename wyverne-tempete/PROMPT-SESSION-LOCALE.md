# Wyverne des tempêtes v4 : import dans Roblox Studio (instructions pour une session Claude locale)

> **À coller tel quel dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP),
> après avoir importé le fichier `Wyverne_Tempete_v4.glb` (voir « Import »). Tous les fichiers sont dans
> `wyverne-tempete-v4.zip` (dossiers `modele/` et `roblox/`).

---

## Contexte
Tu m'aides à intégrer un **boss dragon** dans mon jeu Roblox : la **Wyverne des tempêtes**, une hydre électrique à
**trois têtes et quatre ailes**. C'est un modèle low-poly à facettes, généré par code, en **un seul fichier `.glb`
découpé en 11 parties** (une par couleur / matériau). **Il n'a pas encore de squelette ni d'animation** : pour
l'instant, c'est un modèle fixe.

Parle en **français**, simplement, et explique ce que tu fais.

### Règles
1. **Ne supprime rien** dans le jeu. Si tu dois remplacer quelque chose, déplace l'ancien dans `ServerStorage > Backup_<date>`.
2. Fais d'abord **un seul exemplaire de test**, montre-moi une **capture d'écran**, et attends mon accord avant d'aller plus loin.
3. Si le jeu a un journal d'équipe (par exemple `ServerStorage > DevJournal`), lis-le avant de commencer et respecte ses règles.
4. À la fin : **aucune erreur rouge** dans la console.

## Le modèle
| | |
|---|---|
| Fichier | `Wyverne_Tempete_v4.glb` (branche `claude/roblox-3d-dragons-t7lch1` du dépôt `maireaidan-droid/modelisation`, dossier `wyverne-tempete/objets/`) |
| Taille attendue | **environ 95 × 45 × 84 studs** (envergure × hauteur × longueur) |
| Triangles | environ 52 900 au total |
| Orientation | les **têtes regardent vers +Z**, le pivot est **sous le dragon** (Y = 0), centré |

### Les 11 parties et leurs réglages
| Partie | Rôle | Couleur | Matériau |
|---|---|---|---|
| `Body` | peau, cous, pattes, bras des ailes | `#1F2C52` (bleu nuit) | SmoothPlastic |
| `Scales` | écailles en tuiles (un ton plus clair) | `#2A3D72` | SmoothPlastic |
| `Belly` | plaques du ventre et du poitrail, mâchoires | `#3B4F86` | SmoothPlastic |
| `Plates` | plaques blindées (dos, bras, arcades) | `#2E3C68` | SmoothPlastic |
| `Membrane` | membranes des ailes | `#2A3E7A` | SmoothPlastic, **DoubleSided** |
| `Membrane2` | bords sombres des membranes | `#16204A` | SmoothPlastic, **DoubleSided** |
| `Horns` | cornes, crocs, griffes, os des ailes | `#C9D6F0` (ivoire bleuté) | SmoothPlastic |
| `Bolt` | éclairs cyan (crêtes, ailes, flancs, queue) | `#6FF2FF` | **Neon** |
| `Bolt2` | éclairs jaunes (cornes, dard) | `#FFF27A` | **Neon** |
| `Eyes` | yeux | `#B8FBFF` | **Neon** |
| `Mouth` | intérieur des gueules, narines | `#3A1030` | SmoothPlastic |

## Import (fait par moi, à la main)
1. Dans Studio : **Avatar → Import 3D** (ou **Fichier → Import 3D**), puis choisir `Wyverne_Tempete_v4.glb`.
2. Dans la fenêtre d'import : unité **Stud**, parties **séparées** (ne pas fusionner), **Anchored** coché.
3. Le modèle arrive dans le Workspace.

**Toi, vérifie la taille** avec `GetExtentsSize()` : environ 95 × 45 × 84. Si c'est environ 3,5 fois trop grand ou trop
petit, c'est l'unité : dis-le-moi pour que je réimporte. Vérifie aussi que les **11 parties** sont là. Si Studio les a
renommées (par exemple `Body_Mesh`), le script de réglage les renomme tout seul.

## A. Réglages du modèle
Lance `roblox/setup_wyverne.lua` dans la **barre de commande** (le modèle importé sélectionné). Il :
- applique couleurs et matériaux (éclairs et yeux en Neon, membranes DoubleSided si possible) ;
- coupe les collisions du modèle détaillé et ajoute **5 Hitbox invisibles** (corps, buste et chacune des trois têtes),
  qui servent aussi de zones à toucher pour le combat ;
- range un exemplaire dans `ServerStorage > Dragons > Wyverne_Tempete` et garde `Workspace > Wyverne_Tempete_Test` ;
- ajoute le tag `WyverneTempete`.

Lis le rapport dans la sortie. Vérifie ensuite que les Hitbox sont bien placées sur le corps et les trois têtes (rends-les
visibles un instant avec `Transparency = 0.5`, puis remets 1). Si elles sont décalées, ajuste-les et dis-moi de combien.

## B. Exemplaire de test
1. Place `Wyverne_Tempete_Test` à un endroit dégagé (c'est un boss : prévois une arène d'au moins 150 × 150 studs).
2. Prends une **capture de face** (les trois têtes et les quatre ailes doivent se voir) et une **de profil**.
   - Les éclairs cyan et jaunes doivent briller (Neon).
   - Les **ailes ne doivent avoir aucun trou** et se voir des deux côtés ; si une face disparaît selon l'angle,
     dis-le-moi (il faudra activer `DoubleSided` à la main sur `Membrane` et `Membrane2`).
   - Aucun morceau ne doit flotter à côté du modèle.

## C. Option : ambiance d'orage (seulement si je te le demande)
- Un `PointLight` cyan (Brightness 2, Range 40, `Shadows = false`) dans `Bolt`, pour que le boss éclaire l'arène.
- Un `ParticleEmitter` de petites étincelles cyan sur `Bolt` (Rate 15, Lifetime 0,3, LightEmission 1).

## D. Vérifications finales
- Lance le jeu : **aucune erreur rouge** dans la console.
- Simulateur **téléphone** : avec environ 52 900 triangles, un seul boss à l'écran passe ; dis-moi si ça rame.
- Récapitule ce que tu as fait, où est rangé le modèle et ce qui reste à faire (le squelette et les animations viendront
  dans une prochaine version).
