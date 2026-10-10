# Wyverne des tempêtes (boss électrique)

Boss aérien low-poly pour Roblox, généré par code (même outils que `dragon-long/`).

| Version | Fichier | Triangles | Taille (studs) | Notes |
|---|---|---|---|---|
| v1 | `objets/Wyverne_Tempete_v1.glb` | 13 884 | 90 × 44 × 84 | premier modèle : corps, tête en coin avec crocs, pattes digitigrades, ailes de 40 studs, éclairs (Neon) |
| v2 | `objets/Wyverne_Tempete_v2.glb` | 27 748 | 92 × 44 × 84 | écailles en tuiles (deux tons) sur le dos et les flancs, plaques du ventre ; ailes : doigts à phalanges et griffes, bord festonné, membrane deux tons, membrane avant, plaques et épines sur les bras |
| v3 | `objets/Wyverne_Tempete_v3.glb` | 36 860 | 92 × 44 × 84 | **hydre à trois têtes** : deux cous de plus qui partent du poitrail (écailles, crête d'éclairs) |
| **v4** (actuelle) | `objets/Wyverne_Tempete_v4.glb` | 50 348 | 93 × 45 × 84 | buste élargi couvert d'écailles d'où sortent les trois cous (muscles à leur base, plaques du poitrail) ; cous de côté qui montent en courbe ; **deux paires d'ailes** (grande paire aux épaules, petite paire au milieu du dos, plus basse et balayée vers l'arrière pour ne pas se croiser) |

Démo 3D : [Wyverne des tempêtes](https://claude.ai/artifact/DbZy76Cse2rMckSPjAAzsJ) (page `demo/index.html`, le modèle y est joint en base64).

Générer : `cd generateur && python wyverne.py` (crée le `.glb`, un `.json` avec les parties et `apercu-….png`).

Parties : Body, Scales, Belly, Plates, Membrane, Membrane2, Horns, Bolt (éclairs cyan, Neon), Bolt2 (éclairs jaunes, Neon), Eyes (Neon), Mouth.
Pas encore de squelette ni d'animation.
