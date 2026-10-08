# Génère le .glb, le manifeste (couleurs/matériaux par partie) et une planche d'aperçu 4 vues.
# Usage : python build.py   (depuis ce dossier)
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from meshlib import export_glb, hex_to_rgb, normalize
from dragon_long import all_assets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "objets")
os.makedirs(OUT, exist_ok=True)

FOND = "#3B3335"
LUMIERE = normalize([0.4, 0.8, 0.6])


def render(ax, asset, elev, azim, title, zoom=1.35, focus=None):
    tris, cols = [], []
    for p in asset.parts.values():
        v = np.array(p["v"])
        f = np.array(p["f"])
        tri = v[f]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        base = np.array(hex_to_rgb(p["color"]))
        if p["material"] == "Neon":
            shade = np.ones(len(tri))
        else:
            shade = 0.38 + 0.62 * np.clip(n @ LUMIERE, 0, 1)
        cols.extend(np.clip(base[None] * shade[:, None], 0, 1))
        # Roblox (x, y, z) -> matplotlib (x, -z, y) : Y reste vertical.
        tris.extend(tri[:, :, [0, 2, 1]] * np.array([1, -1, 1]))
    pc = Poly3DCollection(tris, facecolors=cols, edgecolors=cols, linewidths=0.2)
    ax.add_collection3d(pc)
    allv = np.concatenate(tris)
    mid = (allv.max(0) + allv.min(0)) / 2
    half = (allv.max(0) - allv.min(0)).max() / 2
    if focus is not None:  # gros plan : centre et demi-taille donnés en coordonnées Roblox
        c, half = focus
        mid = np.array([c[0], -c[2], c[1]])
    ax.set_xlim(mid[0] - half, mid[0] + half)
    ax.set_ylim(mid[1] - half, mid[1] + half)
    ax.set_zlim(mid[2] - half, mid[2] + half)
    ax.set_box_aspect((1, 1, 1), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_facecolor(FOND)
    ax.set_title(title, color="white", fontsize=13)


def main():
    manifest = []
    for a in all_assets():
        # Pivot : posé à Y = 0, centré sur X/Z.
        mn, mx = a.bounds()
        shift = np.array([(mn[0] + mx[0]) / 2, mn[1], (mn[2] + mx[2]) / 2])
        for p in a.parts.values():
            p["v"] = (np.array(p["v"]) - shift).tolist()
        export_glb(a, os.path.join(OUT, a.name + ".glb"))
        mn, mx = a.bounds()
        manifest.append({
            "name": a.name,
            "tris": a.tri_count(),
            "size_studs": [round(float(x), 1) for x in (mx - mn)],
            "parts": {k: {"tris": len(p["f"]), "color": p["color"], "material": p["material"]}
                      for k, p in a.parts.items()},
        })

        fig = plt.figure(figsize=(16, 14), facecolor=FOND)
        head = (np.array([0, mx[1] - 4, mx[2] - 5]), 6.5)
        centre = ((mn + mx) / 2, (mx - mn)[:2].max() / 2 + 1)
        views = [(221, 5, 0, "Profil gauche", None), (222, 25, -55, "Trois-quarts", None),
                 (234, 5, -90, "Face", centre), (235, 8, 90, "Dos", centre), (236, 15, -40, "Tête (gros plan)", head)]
        for pos, e, az, t, foc in views:
            ax = fig.add_subplot(pos, projection="3d")
            render(ax, a, e, az, t, zoom=1.35 if foc is not None else 1.75, focus=foc)
        size = manifest[-1]["size_studs"]
        fig.suptitle(f"{a.name}  ·  {a.tri_count()} triangles  ·  {size[0]} × {size[1]} × {size[2]} studs (L × H × P)",
                     color="white", fontsize=15)
        plt.subplots_adjust(left=0, right=1, bottom=0, top=0.94, wspace=0, hspace=0.05)
        fig.savefig(os.path.join(ROOT, f"apercu-{a.name}.png"), dpi=110, facecolor=FOND)
        plt.close(fig)

    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    for m in manifest:
        print(m["name"], m["tris"], "tris", m["size_studs"])


if __name__ == "__main__":
    main()
