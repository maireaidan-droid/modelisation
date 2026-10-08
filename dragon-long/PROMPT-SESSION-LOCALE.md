# Dragon Long v18 (animé) : import dans Roblox Studio (instructions pour une session Claude locale)

> **À coller tel quel dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP),
> après avoir importé le fichier `Dragon_Long_v18_rig.glb` (voir « Import »).

---

## Contexte
Tu m'aides à intégrer un **dragon chinois (Long)** dans mon jeu Roblox. C'est un modèle low-poly à facettes, généré par code, en **un seul fichier `.glb` découpé en 9 parties** (une par couleur). Il a un **squelette de 40 os** : un script (`DragonAnimator`) le fait onduler, cligner des yeux, marcher et voler.

Parle en **français**, simplement, et explique ce que tu fais.

### Règles
1. **Ne supprime rien** dans le jeu. Si tu dois remplacer quelque chose, déplace l'ancien dans `ServerStorage > Backup_<date>`.
2. Fais d'abord **un seul exemplaire de test**, montre-moi une **capture d'écran**, et attends mon accord avant d'aller plus loin.
3. Si le jeu a un journal d'équipe (par exemple `ServerStorage > DevJournal`), lis-le avant de commencer et respecte ses règles.
4. À la fin : **aucune erreur rouge** dans la console.

## Le modèle
| | |
|---|---|
| Fichier | `Dragon_Long_v18_rig.glb` (branche `claude/roblox-3d-dragons-t7lch1` du dépôt `maireaidan-droid/modelisation`, dossier `dragon-long/objets/`) |
| Taille attendue | **16,5 × 19 × 58 studs** (largeur × hauteur × longueur) |
| Triangles | environ 28 700 au total |
| Orientation | la **tête regarde vers +Z**, le pivot est **sous le dragon** (Y = 0), centré |

### Les 9 parties et leurs réglages
| Partie | Rôle | Couleur | Matériau | Triangles |
|---|---|---|---|---|
| `Body` | écailles du corps et de la tête, écailles des joues, pattes | `#2F7D63` (jade) | SmoothPlastic | 14 730 |
| `Belly` | ventre en plaques, dessous de la mâchoire | `#E2B65C` (doré) | SmoothPlastic | 3 362 |
| `Fins` | crinière, crête du dos, nageoires, barbichette | `#C8432F` (rouge) | SmoothPlastic | 5 794 |
| `Horns` | cornes, corne de nez, pointes des joues, griffes, dents | `#E6DCC3` (ivoire) | SmoothPlastic | 2 404 |
| `Whiskers` | moustaches, sourcils en volutes, marque du front | `#F0C24B` (or) | SmoothPlastic | 1 288 |
| `Eyes` | yeux | `#FFD23F` (jaune) | **Neon** | 96 |
| `Pupils` | pupilles fendues, narines, pores du museau | `#17120E` (presque noir) | SmoothPlastic | 112 |
| `Mouth` | intérieur de la gueule : gorge, palais, plancher, intérieur des lèvres | `#8E2529` (rouge) | SmoothPlastic | 684 |
| `Tongue` | langue | `#B9434C` (rouge rosé) | SmoothPlastic | 192 |

## Import (fait par moi, à la main)
1. Dans Studio : **Avatar → Import 3D** (ou **Fichier → Import 3D**), puis choisir `Dragon_Long_v18_rig.glb`.
2. Dans la fenêtre d'import :
   - unité **Stud** ;
   - parties **séparées** (ne pas fusionner) ;
   - **Anchored** coché.
3. Le modèle arrive dans le Workspace.

**Toi, vérifie la taille** avec `GetExtentsSize()` : environ 16,5 × 19 × 58. Si c'est environ 3,5 fois trop grand ou trop petit, c'est l'unité : dis-le-moi pour que je réimporte (le format `.glb` est prévu en mètres). Vérifie aussi que les **9 parties** sont là avec les bons noms. Si Studio les a renommées (par exemple `Body_Mesh`), renomme-les comme dans le tableau.

## A. Réglages du modèle
1. Range le modèle dans `ServerStorage > Dragons` (crée le dossier s'il n'existe pas) et nomme-le `Dragon_Long`.
2. Pour **chaque partie** : `Color` et `Material` d'après le tableau ci-dessus.
3. Pour **toutes** les parties :
   - `Anchored = true` ;
   - `CanCollide = false`, `CanTouch = false`, `CanQuery = false` (le modèle est très détaillé : on ne s'en sert pas pour les collisions) ;
   - `CastShadow = true`, **sauf** `Eyes`, `Pupils`, `Mouth` et `Tongue` : `CastShadow = false`.
4. Si la propriété `DoubleSided` est modifiable dans les propriétés, active-la sur `Fins` et `Whiskers` (les nageoires et sourcils fins peuvent sinon disparaître sous certains angles). Sinon, ignore cette étape.
5. **Collision simple** : ajoute dans le modèle une `Part` invisible nommée `Hitbox` qui couvre la tête et le cou (environ 8 × 8 × 12 studs, autour de la tête, côté +Z), avec `Transparency = 1`, `Anchored = true`, `CanCollide = true`, `CanQuery = true`. Si le dragon doit bloquer les joueurs sur toute sa longueur, ajoute 3 ou 4 autres `Part` invisibles le long du corps.
6. `PrimaryPart` = `Body`. Le pivot doit rester sous le dragon : vérifie avec `GetPivot()`.

## B. Exemplaire de test
1. Clone `ServerStorage > Dragons > Dragon_Long` dans `Workspace`, à un endroit dégagé et bien visible (pas sur un chemin), avec `PivotTo`.
2. Si la taille ne convient pas : `Model:ScaleTo(...)`. Par exemple 0,5 pour un dragon de 29 studs de long.
3. Prends une **capture de face** et une **capture de profil**, montre-les-moi.
   - Les yeux jaunes doivent briller (Neon) et se voir de face, sous les arcades.
   - On doit voir l'intérieur sombre de la gueule, la langue et les dents.
   - Aucun morceau ne doit flotter à côté du modèle.

## C. Option : lumière des yeux (seulement si je te le demande)
Un `PointLight` jaune très discret dans `Eyes` (Brightness 0,5, Range 6, `Shadows = false`) pour que le regard ressorte dans les zones sombres.

## D. Vérifications finales
- Lance le jeu et lis la console : **aucune erreur rouge**.
- Simulateur d'appareil **téléphone** : la scène reste fluide avec le dragon visible. Avec environ 28 700 triangles, un dragon à l'écran ne pose pas de problème ; s'il en faut beaucoup, dis-le-moi, il faudra une version allégée.
- Récapitule-moi ce que tu as fait, où est rangé le modèle, et ce qui reste à faire.

## E. Animation
Fichiers fournis avec le modèle : `DragonAnimator.client.lua` et `DragonDemo.server.lua`.
1. Vérifie que l'import a bien créé des **Bones** (objets `Bone`) dans les MeshParts du dragon, avec les noms `Root`, `Neck`, `Head`, `Jaw`, `S01`…`S14`, `Eye_L`, `Lid_L`, `Mane_Top`, `LegFL_Upper`… (40 en tout). S'il n'y en a aucun, l'import a perdu le squelette : préviens-moi.
2. Crée un **LocalScript** `DragonAnimator` dans `StarterPlayer > StarterPlayerScripts` et colle `DragonAnimator.client.lua`. Il anime chez chaque joueur tout Model tagué `DragonLong` (le script de réglage ajoute le tag) ou dont le nom commence par `Dragon_Long`.
3. Le mode se règle avec l'attribut **`Mode`** du Model : `Idle` (repos), `Walk` (marche), `Fly` (vol).
4. Pour tester : crée un **Script** `DragonDemo` dans `ServerScriptService` et colle `DragonDemo.server.lua`. Le dragon `Dragon_Long_Test` enchaîne repos, marche et vol en cercle. **Si le dragon avance à reculons**, mets `HEAD_FORWARD = -1` en haut du script.
5. Lance le jeu (Play) et montre-moi une vidéo ou des captures : ondulation, clignement, pattes en marche, pattes repliées en vol.
