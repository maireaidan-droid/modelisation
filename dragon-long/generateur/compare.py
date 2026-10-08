# Planche de comparaison en gros plan sur la tête entre deux versions exportées (.glb).
# Usage : python compare.py Dragon_Long_v4 Dragon_Long_v5 [nez|yeux|gueule]
import os
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from build import FOND, LUMIERE, CONTRE_JOUR, ROOT, OUT
from dragon_long import build


def load(name):
    scene = trimesh.load(os.path.join(OUT, name + ".glb"))
    parts = []
    for g in scene.geometry.values():
        rgb = np.array(g.visual.material.baseColorFactor[:3], float)
        rgb = rgb / 255 if rgb.max() > 1 else rgb
        neon = g.visual.material.emissiveFactor is not None and np.max(g.visual.material.emissiveFactor) > 0
        parts.append((g.triangles, rgb, neon))
    return parts


def draw(ax, parts, elev, azim, centre, half, title):
    tris, cols = [], []
    for tri, rgb, neon in parts:
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        shade = np.ones(len(tri)) if neon else (0.38 + 0.62 * np.clip(n @ LUMIERE, 0, 1)
                                                 + 0.22 * np.clip(n @ CONTRE_JOUR, 0, 1))
        cols.extend(np.clip(rgb[None] * shade[:, None], 0, 1))
        tris.extend(tri[:, :, [0, 2, 1]] * np.array([1, -1, 1]))
    ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolors=cols, linewidths=0.15))
    mid = np.array([centre[0], -centre[2], centre[1]])
    for setter, k in ((ax.set_xlim, 0), (ax.set_ylim, 1), (ax.set_zlim, 2)):
        setter(mid[k] - half, mid[k] + half)
    ax.set_box_aspect((1, 1, 1), zoom=1.35)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_facecolor(FOND)
    ax.set_title(title, color="white", fontsize=13)


def main(old, new, mode="nez"):
    a = build()
    mn, mx = a.bounds()
    shift = np.array([(mn[0] + mx[0]) / 2, mn[1], (mn[2] + mx[2]) / 2])
    tete = np.asarray(a.head_center) - shift
    nez = tete + np.array([0, -0.35, 3.6])
    yeux = tete + np.array([0, 0.5, 1.0])
    gueule = tete + np.array([0, -1.0, 2.7])
    if mode == "gueule":
        views = [(-4, -90, "gueule de face", gueule, 2.6), (-8, -55, "gueule trois-quarts", gueule, 2.8),
                 (2, 0, "gueule profil", gueule, 3.0), (-30, -75, "gueule vue d'en dessous", gueule, 2.8)]
        mode_name = "gueule"
    elif mode == "yeux":
        views = [(8, -90, "yeux de face", yeux, 2.9), (12, -45, "yeux trois-quarts", yeux, 2.9),
                 (4, 0, "yeux profil", yeux, 3.0), (35, -150, "front, vue de dessus", yeux, 3.4)]
        mode_name = "yeux"
    else:
        views = [(6, -90, "de face", nez, 2.6), (14, -40, "trois-quarts", nez, 2.8), (3, 0, "profil", nez, 2.8),
                 (8, -90, "tête entière de face", tete, 5.2)]
        mode_name = "nez"
    fig = plt.figure(figsize=(18, 9.5), facecolor=FOND)
    for row, name in enumerate((old, new)):
        parts = load(name)
        for col, (e, az, t, c, h) in enumerate(views):
            ax = fig.add_subplot(2, 4, row * 4 + col + 1, projection="3d")
            draw(ax, parts, e, az, c, h, f"{name} · {t}")
    plt.subplots_adjust(left=0, right=1, bottom=0, top=0.95, wspace=0, hspace=0.08)
    path = os.path.join(ROOT, f"comparaison-{mode_name}-{old}-{new}.png")
    fig.savefig(path, dpi=100, facecolor=FOND)
    print(path)


if __name__ == "__main__":
    main(*sys.argv[1:4])
