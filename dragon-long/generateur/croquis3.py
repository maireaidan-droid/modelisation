# Croquis 3D, série 3 : encore 5 styles (origami, voxel, forêt, insecte, tortue-île).
# Usage : python croquis3.py   -> images dans ../croquis/
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from meshlib import Asset, blob, fin, gem, normalize, loft, ellipse_ring
from build import render, FOND
from croquis import OUT, X, Y, Z, V, line, head, leg, spikes
from croquis2 import parts


def box(a, part, c, sx, sy, sz):
    c = np.asarray(c, float)
    v = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float) * [sx, sy, sz] / 2 + c
    f = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6),
         (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    a.add(part, v, np.array(f))


def tri(a, part, p0, p1, p2, t=0.08):
    n = np.cross(np.asarray(p1) - p0, np.asarray(p2) - p0)
    a.add(part, *fin(p0, p1, p2, n, t))


# ---------- F. Origami ----------
def origami():
    a = Asset("Origami")
    parts(a, (("Paper", "#F4EFE6", "SmoothPlastic"), ("Paper2", "#E04848", "SmoothPlastic"),
              ("Paper3", "#D9CFC0", "SmoothPlastic"), ("Eyes", "#1C1C1C", "SmoothPlastic")))
    # Corps : une suite de triangles pliés (arête vive sur le dos), du cou à la queue
    spine = [V(0, 9 + 2 * np.sin(k * 0.5 + 0.5), 8 - 2.6 * k) for k in range(10)]
    for k in range(len(spine) - 1):
        p, q = spine[k], spine[k + 1]
        w = 2.4 * (1 - k / 11)
        col = "Paper" if k % 2 else "Paper3"
        for sd in (1, -1):
            tri(a, col, p + V(0, w * 0.6, 0), q + V(0, w * 0.5, 0), p + V(sd * w, -w * 0.7, 0))
            tri(a, col, q + V(0, w * 0.5, 0), q + V(sd * w * 0.9, -w * 0.6, 0), p + V(sd * w, -w * 0.7, 0))
    # Tête : pyramide pliée
    h = spine[0] + V(0, 2.4, 2.2)
    for sd in (1, -1):
        tri(a, "Paper", h, h + V(0, -0.4, 4), h + V(sd * 1.6, -1.6, 0.4))
        tri(a, "Paper3", h + V(0, -0.4, 4), h + V(0, -2.4, 2.2), h + V(sd * 1.6, -1.6, 0.4))
        tri(a, "Paper2", h + V(sd * 0.6, 0.2, -0.2), h + V(sd * 1.2, 2.8, -2.6), h + V(sd * 0.2, 0.4, -1.2))  # cornes
        a.add("Eyes", *gem(h + V(sd * 0.85, -0.6, 1.4), Z, Y, X, 0.3, 0.12, 0.05))
        tri(a, "Paper", spine[0], h + V(sd * 1.2, -1.4, 0), spine[0] + V(sd * 1.8, -1.5, 0))                  # cou
        # Ailes : grands triangles pliés en deux, rouges dessous
        b = spine[2] + V(0, 1.2, 0)
        tip = b + V(sd * 11, 5, -4)
        tri(a, "Paper", b, tip, b + V(sd * 4, 0.5, -5))
        tri(a, "Paper2", b + V(sd * 4, 0.5, -5), tip, b + V(sd * 8, -1, -7))
        # Pattes : bandes pliées en zigzag
        for idx in (1, 6):
            hip = spine[idx] + V(sd * 1.2, -1.2, 0)
            knee = hip + V(sd * 0.8, -3, 1.2)
            foot = V(hip[0] + sd * 1.2, 0.2, hip[2] + 0.4)
            tri(a, "Paper3", hip, knee, hip + V(0, -0.6, -1.2))
            tri(a, "Paper", knee, foot, foot + V(0, 0.3, 1.4))
    # Queue : éventail plié
    e = spine[-1]
    for k in range(4):
        tri(a, "Paper2" if k % 2 else "Paper", e, e + V(-1.6 + k * 1.1, 2 - k * 0.6, -3.5), e + V(-0.6 + k * 1.1, 1.6 - k * 0.6, -3.8))
    return a, "Origami (papier plié)", "fait de triangles de papier, arêtes vives, rouge sous les ailes", 1.6


# ---------- G. Voxel ----------
def voxel():
    a = Asset("Voxel")
    parts(a, (("Body", "#4C9A3B", "SmoothPlastic"), ("Belly", "#E6D27A", "SmoothPlastic"),
              ("Dark", "#2F6B27", "SmoothPlastic"), ("Wing", "#C24A3A", "SmoothPlastic"),
              ("Eyes", "#FFFFFF", "SmoothPlastic"), ("Pupil", "#111111", "SmoothPlastic"), ("Horns", "#F2EBD3", "SmoothPlastic")))
    s = 1.2
    # Corps et queue : colonne de cubes qui rétrécit
    for k in range(12):
        z = 4 - k * s
        y = 7 + (0 if k < 6 else -(k - 6) * 0.5)
        n = 4 if k < 5 else (3 if k < 8 else (2 if k < 10 else 1))
        for i in range(n):
            for j in range(n):
                x = (i - (n - 1) / 2) * s
                yy = y + (j - (n - 1) / 2) * s
                part = "Belly" if (j == 0 and n > 2) else ("Dark" if (i + j + k) % 5 == 0 else "Body")
                box(a, part, V(x, yy, z), s, s, s)
        if k % 2 == 0 and k < 10:
            box(a, "Dark", V(0, y + n * s / 2 + s / 2, z), s * 0.6, s, s * 0.8)               # pics du dos
    # Cou et tête cubique
    for k, (y, z) in enumerate(((9.5, 5.5), (11, 6.5))):
        box(a, "Body", V(0, y, z), 2 * s, 2 * s, 2 * s)
    hc = V(0, 12.5, 8.6)
    box(a, "Body", hc, 4 * s, 3 * s, 4 * s)
    box(a, "Body", hc + V(0, -0.6, 3.6), 3 * s, 2 * s, 3 * s)                                   # museau
    box(a, "Belly", hc + V(0, -2.0, 3.0), 2.6 * s, 0.8 * s, 3.2 * s)                            # mâchoire
    for sd in (1, -1):
        box(a, "Eyes", hc + V(sd * 1.2, 0.6, 2.42), s, s, 0.1)
        box(a, "Pupil", hc + V(sd * 1.0, 0.4, 2.5), s * 0.5, s * 0.7, 0.1)
        box(a, "Horns", hc + V(sd * 1.6, 2.6, -1.2), s * 0.7, 2.2 * s, s * 0.7)
        box(a, "Horns", hc + V(sd * 1.6, 3.6, -2.2), s * 0.6, s * 0.6, 1.4 * s)
        for z in (2.5, -3):                                                                     # pattes
            box(a, "Dark", V(sd * 2.2, 3.6, z), 1.6 * s, 4 * s, 1.6 * s)
            box(a, "Horns", V(sd * 2.2, 0.8, z + 1.0), 1.6 * s, 0.6, 0.6 * s)
        # aile en marches d'escalier
        for k in range(5):
            for j in range(4 - k // 2):
                box(a, "Wing", V(sd * (3 + k * s), 10 + k * 0.6 - j * s, -0.5 - j * s * 0.4), s, s * 0.9, 0.4)
    return a, "Voxel (cubes)", "entièrement en cubes, comme un dragon Minecraft / Roblox classique", 1.15


# ---------- H. Forêt ----------
def foret():
    a = Asset("Foret")
    parts(a, (("Wood", "#6B4A2E", "SmoothPlastic"), ("Moss", "#4F8A3A", "SmoothPlastic"),
              ("Leaf", "#7BC24A", "SmoothPlastic"), ("Leaf2", "#C9D94A", "SmoothPlastic"),
              ("Flower", "#FF7FB0", "SmoothPlastic"), ("Eyes", "#FFE14A", "Neon")))
    path = [V(0.6 * np.sin(k * 0.6), 7 + 1.0 * np.sin(k * 0.5 + 0.5), 10 - 2.6 * k) for k in range(12)]
    body = line(a, "Wood", path, [1.8, 2.4, 2.8, 2.9, 2.7, 2.4, 2.0, 1.6, 1.2, 0.8, 0.5, 0.15], 8)
    line(a, "Moss", [p + V(0, 1.6 - 0.1 * k, 0) for k, p in enumerate(path[1:9])],
         [1.6, 2.0, 2.1, 2.0, 1.8, 1.5, 1.2, 0.8], 7, flat=0.35)                                # mousse sur le dos
    f, u, s = head(a, path[0] + V(0, 1.4, 2.6), V(0, -0.15, 1), 2.6, horns="Wood", body="Wood", belly="Moss")
    rng = np.random.default_rng(2)
    for sd in (1, -1):
        # bois de cerf en branches
        b = path[0] + V(sd * 0.8, 3.6, 2.0)
        br = line(a, "Wood", [b, b + V(sd * 1.5, 3, -1), b + V(sd * 3.2, 5.5, -2.6)], [0.35, 0.25, 0.1], 5)
        line(a, "Wood", [br[len(br) // 2], br[len(br) // 2] + V(sd * 1.8, 1.2, 0.8)], [0.18, 0.05], 4)
        for p in (br[-1], br[len(br) // 2] + V(sd * 1.8, 1.2, 0.8)):
            a.add("Leaf", *blob(p, Z, Y, X, 0.8, 0.5, 0.8, 6, 3))
        for idx, back in ((2, 0.6), (8, -0.6)):                                                 # pattes en racines
            hip = path[idx] + V(sd * 2, -1, 0)
            leg(a, "Wood", hip, V(sd * 3.4, 0.4, hip[2] + back), 0.9, claws="Wood")
        # ailes en feuilles
        sh = path[3] + V(sd * 1.6, 1.8, 0)
        for k in range(5):
            t = k / 4
            d = normalize(V(sd * (1 - 0.4 * t), 0.5 - 0.6 * t, -0.3 - 0.7 * t))
            L = 7 - 2 * t
            c = sh + d * L / 2
            a.add("Leaf" if k % 2 else "Leaf2", *gem(c, d, np.cross(d, Y) * sd, Y, L / 2, 1.3, 0.1))
    for k in range(18):                                                                         # fleurs sur la mousse
        p = path[1 + k % 8] + V(rng.uniform(-1.4, 1.4), 2.2, rng.uniform(-1, 1))
        a.add("Flower", *blob(p, Z, Y, X, 0.35, 0.25, 0.35, 5, 3))
    end = path[-1]
    a.add("Leaf", *gem(end + V(0, 0, -1.6), -Z, X, Y, 2.0, 1.4, 0.1))
    return a, "Forêt (bois et mousse)", "corps en bois, mousse et fleurs sur le dos, bois de cerf, ailes en feuilles", 1.6


# ---------- I. Insecte (libellule) ----------
def insecte():
    a = Asset("Insecte")
    parts(a, (("Shell", "#2B6E6A", "SmoothPlastic"), ("Shell2", "#1C3F4F", "SmoothPlastic"),
              ("Wing", "#B8F1FF", "SmoothPlastic"), ("Vein", "#3FD0C9", "SmoothPlastic"),
              ("Eyes", "#FF3D6E", "Neon"), ("Leg", "#1A1A1A", "SmoothPlastic")))
    # Thorax + abdomen en anneaux de carapace
    for k in range(14):
        z = 4 - k * 1.5
        r = 1.9 if k < 3 else 1.3 - 0.06 * (k - 3)
        a.add("Shell" if k % 2 else "Shell2", *blob(V(0, 8 + 0.1 * k, z), Z, Y, X, 0.9, r, r * 0.95, 8, 4))
    hc = V(0, 9, 7)
    a.add("Shell", *blob(hc, Z, Y, X, 1.8, 1.6, 1.8, 8, 4))
    line(a, "Shell2", [hc + V(0, -0.2, 1.5), hc + V(0, -0.6, 3.6)], [1.0, 0.6], 6)          # museau
    for sd in (1, -1):
        a.add("Eyes", *blob(hc + V(sd * 1.4, 0.6, 0.6), Z, Y, X, 1.0, 1.0, 0.7, 8, 4))        # yeux à facettes
        line(a, "Leg", [hc + V(sd * 0.5, 1.4, 0.8), hc + V(sd * 1.5, 4.0, 1.5), hc + V(sd * 2.6, 4.6, 3.2)], [0.12, 0.08, 0.0], 4)
        line(a, "Shell2", [hc + V(sd * 0.6, -1.2, 3.0), hc + V(sd * 1.6, -2.0, 4.2)], [0.3, 0.0], 4)  # mandibules
        for k, z in enumerate((5.5, 4.5, 3.5)):                                               # 6 pattes fines
            hip = V(sd * 1.2, 7.2, z)
            knee = V(sd * 3.6, 6.5 + k * 0.3, z + 0.5 - k)
            foot = V(sd * 4.6, 0.3, z + 1 - k * 1.4)
            line(a, "Leg", [hip, knee], [0.25, 0.2], 5)
            line(a, "Leg", [knee, foot], [0.2, 0.0], 5)
        # 4 ailes de libellule transparentes
        for z, ang in ((4.8, 0.15), (3.6, -0.15)):
            b = V(sd * 1.2, 9.6, z)
            tip = b + V(sd * 13, 1.5 + ang * 6, -1.5 + ang * 8)
            a.add("Wing", *gem((b + tip) / 2, normalize(tip - b), Y, Z, 6.6, 0.05, 1.5))
            line(a, "Vein", [b, tip], [0.12, 0.04], 4)
    a.add("Eyes", *gem(V(0, 9.4, -17.5), -Z, Y, X, 1.2, 0.5, 0.5))                           # dard lumineux
    return a, "Insecte (libellule)", "carapace en anneaux, 6 pattes, 4 ailes transparentes, yeux à facettes", 1.6


# ---------- J. Tortue-île ----------
def tortue():
    a = Asset("Tortue")
    parts(a, (("Skin", "#5E7A6B", "SmoothPlastic"), ("Shell", "#6B5A3E", "SmoothPlastic"),
              ("Grass", "#6DB84A", "SmoothPlastic"), ("Rock", "#8A8A82", "SmoothPlastic"),
              ("Tree", "#4A3420", "SmoothPlastic"), ("Leaf", "#3E8E3A", "SmoothPlastic"),
              ("Water", "#4FC3F7", "Neon"), ("Horns", "#E6DCC3", "SmoothPlastic"), ("Eyes", "#FFB13B", "Neon")))
    # Carapace : dôme en anneaux, couvert d'herbe sur le dessus
    rings = []
    for k in range(8):
        t = k / 7
        r = 9 * np.cos(t * np.pi / 2) + 0.01
        rings.append(ellipse_ring(V(0, 6 + 5 * np.sin(t * np.pi / 2), 0), X, Z, r, r * 1.2, 14))
    v, f = loft(rings)
    a.add("Shell", v, f)
    a.add("Grass", *blob(V(0, 10.6, 0), Z, Y, X, 7.5, 1.0, 6.0, 12, 4))
    a.add("Skin", *blob(V(0, 5, 0), Z, Y, X, 10, 1.6, 8.5, 14, 4))                             # bord / ventre
    # Petite île : rochers, arbres, cascade
    for p, sz in ((V(-2, 11.8, -2), 1.6), (V(-3, 12.6, -1), 1.0), (V(2.5, 11.4, 3), 1.1)):
        a.add("Rock", *gem(p, Z, Y, X, sz, sz * 1.2, sz))
    for p in (V(2, 11.2, -3), V(-1, 11.4, 3), V(3.5, 11, 0)):
        line(a, "Tree", [p, p + V(0, 3, 0)], [0.3, 0.2], 5)
        a.add("Leaf", *gem(p + V(0, 4.2, 0), Y, Z, X, 1.8, 1.5, 1.5))
    line(a, "Water", [V(-2.4, 12.6, -0.6), V(-4.5, 10.6, 0.5), V(-7.5, 7.5, 1.0)], [0.5, 0.6, 0.7], 6, flat=0.3)
    # Long cou de dragon et tête
    neck = line(a, "Skin", [V(0, 7, 9), V(0, 9.5, 13), V(0, 13, 15)], [2.2, 1.6, 1.3], 8)
    head(a, V(0, 13.8, 16.5), V(0, -0.1, 1), 2.4, horns="Horns", body="Skin", belly="Skin")
    spikes(a, "Rock", neck[3:-2], normalize(V(0, 0.5, -1)), 0.8, 0.6, 3)
    for sd in (1, -1):
        for z in (6, -6):                                                                       # pattes de tortue
            hip = V(sd * 7, 5, z)
            foot = V(sd * 9.5, 0.6, z + (1 if z > 0 else -1))
            line(a, "Skin", [hip, foot], [2.0, 1.6], 7)
            a.add("Horns", *gem(foot + V(0, -0.2, 1.2), Z, Y, X, 0.8, 0.3, 1.2))
    line(a, "Skin", [V(0, 5.5, -10), V(0, 4.5, -14), V(0, 4, -16)], [1.6, 0.9, 0.0], 7)
    return a, "Tortue-dragon (île vivante)", "carapace géante avec une île dessus : herbe, rochers, arbres, cascade", 1.4


def main():
    sketches = [origami(), voxel(), foret(), insecte(), tortue()]
    fig = plt.figure(figsize=(25, 11), facecolor=FOND)
    for k, (a, title, desc, zm) in enumerate(sketches):
        ax = fig.add_subplot(2, 5, k + 1, projection="3d")
        render(ax, a, 22, -50, f"{'FGHIJ'[k]}. {title}", zoom=zm)
        ax = fig.add_subplot(2, 5, k + 6, projection="3d")
        render(ax, a, 6, 0, "profil", zoom=zm)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "styles2-planche.png"), dpi=70, facecolor=FOND)
    plt.close(fig)
    for k, (a, title, desc, zm) in enumerate(sketches):
        fig = plt.figure(figsize=(16, 13), facecolor=FOND)
        for j, (elev, azim, t) in enumerate(((22, -50, "Trois-quarts"), (6, 0, "Profil"), (8, -90, "Face"),
                                              (65, -60, "Dessus"))):
            ax = fig.add_subplot(2, 2, j + 1, projection="3d")
            render(ax, a, elev, azim, t, zoom=zm)
        fig.suptitle(f"{title} : {desc}", color="white", fontsize=16)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, f"style-{'fghij'[k]}-{a.name.lower()}.png"), dpi=60, facecolor=FOND)
        plt.close(fig)
        print(title, a.tri_count(), "triangles")


if __name__ == "__main__":
    main()
