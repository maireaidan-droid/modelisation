# Croquis 3D : Wyverne des tempêtes, style électrique (boss aérien).
# Usage : python croquis_wyverne.py   -> image dans ../croquis/
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from meshlib import Asset, blob, fin, gem, normalize
from build import render, FOND
from croquis import OUT, X, Y, Z, V, line, head, leg, wing
from croquis2 import parts
from croquis_boss import joueur

rng = np.random.default_rng(12)


def zigzag(a, part, p0, p1, r0, r1, n=5, amp=0.25):
    """Éclair : ligne brisée entre p0 et p1 (amp = écart des zigzags, en part de la longueur)."""
    d = p1 - p0
    L = np.linalg.norm(d)
    side = normalize(np.cross(d, Y if abs(normalize(d) @ Y) < 0.9 else X))
    up = normalize(np.cross(side, d))
    pts = [p0]
    for k in range(1, n):
        t = k / n
        pts.append(p0 + d * t + (side * (1 if k % 2 else -1) + up * rng.normal() * 0.5) * L * amp / n * 2)
    pts.append(p1)
    for q0, q1, k in zip(pts[:-1], pts[1:], range(n)):
        r = (r0 + (r1 - r0) * k / n) * 1.8
        line(a, part, [q0, q1], [r, r * 0.9], 4)
    return pts


def wyverne_electrique():
    a = Asset("WyverneElectrique")
    parts(a, (("Body", "#1F2C52", "SmoothPlastic"), ("Belly", "#2E3F6B", "SmoothPlastic"),
              ("Plate", "#3A4A78", "SmoothPlastic"), ("Membrane", "#26386B", "SmoothPlastic"),
              ("Horns", "#C9D6F0", "SmoothPlastic"), ("Bolt", "#6FF2FF", "Neon"), ("Bolt2", "#FFF27A", "Neon"),
              ("Eyes", "#B8FBFF", "Neon")))
    spine = line(a, "Body", [V(0, 14, -42), V(0, 12, -31), V(0, 13, -19), V(0, 17, -6), V(0, 20, 3), V(0, 26, 9),
                             V(0, 31, 12)], [0.2, 1.3, 3.0, 4.8, 4.4, 2.4, 1.9], 9)
    line(a, "Belly", [V(0, 14.4, -8), V(0, 15.4, 0), V(0, 18, 5)], [3.1, 3.5, 2.5], 8, flat=0.45)
    # Plaques blindées sur le dos, chacune bordée d'une ligne électrique
    for k in range(6, len(spine) - 8, 3):
        p = spine[k]
        a.add("Plate", *gem(p + V(0, 2.6, 0), Z, Y, X, 1.8, 0.8, 2.4))
    # Crête en éclairs : des pics en zigzag qui crépitent tout le long du dos
    for k in range(4, len(spine) - 6, 3):
        p = spine[k]
        h = 2.0 + 3.0 * np.sin(np.pi * k / len(spine))
        zigzag(a, "Bolt", p + V(0, 2.0, 0), p + V(0, 2.0 + h, -h * 0.6), 0.28, 0.05, n=3, amp=0.35)
    # Rayures électriques sur les flancs
    for k in range(8, len(spine) - 12, 6):
        p = spine[k]
        for sd in (1, -1):
            zigzag(a, "Bolt", p + V(sd * 3.6, 1.5, 1.5), p + V(sd * 3.2, -2.0, -2.5), 0.18, 0.1, n=4, amp=0.3)
    # Tête : corne frontale en lance et cornes en éclairs fourchus, gueule lumineuse
    hc = V(0, 32, 15)
    head(a, hc, V(0, -0.1, 1), 4.0, horns="Horns", body="Body", belly="Belly", eyes="Eyes", horn_len=0.01, horn_up=0)
    line(a, "Horns", [V(0, 34, 15), V(0, 36, 12), V(0, 38.5, 6)], [0.9, 0.6, 0.0], 6)
    for sd in (1, -1):
        b = hc + V(sd * 1.4, 1.6, -1.0)
        pts = zigzag(a, "Bolt2", b, b + V(sd * 3.5, 4.5, -6.5), 0.45, 0.15, n=4, amp=0.3)
        zigzag(a, "Bolt2", pts[2], pts[2] + V(sd * 2.5, 2.5, 0.5), 0.25, 0.05, n=2, amp=0.3)    # fourche
        # moustaches électriques
        zigzag(a, "Bolt", hc + V(sd * 1.2, -1.0, 4.5), hc + V(sd * 5.0, -2.5, 1.0), 0.15, 0.05, n=5, amp=0.25)
    a.add("Bolt", *blob(hc + V(0, -1.4, 3.6), Z, Y, X, 1.6, 0.5, 1.0, 8, 3))         # lueur dans la gueule
    for sd in (1, -1):
        leg(a, "Body", V(sd * 3, 15, -4), V(sd * 5, 0.8, -1), 1.8, claws="Horns", knee_back=-0.8)
        # Ailes immenses : membrane sombre, bord d'attaque lumineux, nervures en éclairs ramifiés
        sh = V(sd * 3, 22, 2)
        wing(a, sh, sd, 40, bone="Horns", skin="Membrane", fingers=5, lift=0.45, sweep=0.2)
        el = sh + V(sd * 40 * 0.35, 40 * 0.45 * 0.6, -40 * 0.08)
        wr = el + V(sd * 40 * 0.3, 40 * 0.45 * 0.5, 40 * 0.12)
        line(a, "Bolt", [sh + V(0, 0.6, 0.3), el + V(0, 0.6, 0.3), wr + V(0, 0.6, 0.3)], [0.3, 0.3, 0.25], 4)
        for k in range(5):
            t = k / 4
            tip = wr + V(sd * 40 * (0.45 - 0.2 * t), -40 * (0.05 + 0.55 * t), -40 * (0.2 + 0.25 * t))
            start = wr * 0.7 + tip * 0.3
            pts = zigzag(a, "Bolt", start, start * 0.4 + tip * 0.6 + V(0, 0.4, 0), 0.22, 0.08, n=4, amp=0.25)
            zigzag(a, "Bolt", pts[2], pts[2] + V(sd * -3, -3, -2), 0.12, 0.03, n=2, amp=0.3)
    # Queue : anneaux électriques (comme une bobine) et dard foudroyant à 3 pointes
    for k, z in enumerate((-30, -34, -38)):
        c = V(0, 13 - 0.4 * k, z)
        pts = [c + V(np.cos(t), np.sin(t), 0) * (2.2 - 0.3 * k) for t in np.linspace(0, 2 * np.pi, 13)]
        line(a, "Bolt", pts, [0.18] * len(pts), 4)
    a.add("Bolt2", *gem(V(0, 14.5, -44), -Z, Y, X, 3.0, 1.0, 1.4))
    for k in range(3):
        zigzag(a, "Bolt2", V(0, 14.5, -46), V((k - 1) * 4, 16 + 2 * (k == 1), -52), 0.25, 0.0, n=4, amp=0.3)
    # Petits éclairs qui crépitent autour du corps
    for _ in range(10):
        p = spine[int(rng.uniform(8, len(spine) - 8))] + V(rng.uniform(-6, 6), rng.uniform(-2, 5), rng.uniform(-2, 2))
        zigzag(a, "Bolt2" if rng.random() < 0.3 else "Bolt", p, p + V(rng.normal() * 2, rng.normal() * 2, rng.normal() * 2),
               0.1, 0.02, n=3, amp=0.4)
    joueur(a, V(18, 0, 18))
    return a


def main():
    a = wyverne_electrique()
    fig = plt.figure(figsize=(16, 13), facecolor=FOND)
    for j, (elev, azim, t) in enumerate(((18, -50, "Trois-quarts"), (6, 0, "Profil"), (8, -90, "Face (ailes ouvertes)"),
                                          (25, -140, "De derrière"))):
        ax = fig.add_subplot(2, 2, j + 1, projection="3d")
        render(ax, a, elev, azim, t, zoom=1.45)
        ax.set_facecolor(FOND)
    fig.suptitle("Wyverne des tempêtes (électrique) : le petit blanc = un joueur", color="white", fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "boss-wyverne-electrique.png"), dpi=62, facecolor=FOND)
    plt.close(fig)
    print(a.tri_count(), "triangles")


if __name__ == "__main__":
    main()
