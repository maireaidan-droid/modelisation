# Croquis 3D de 4 dragons boss (pas des Long) : Colosse de lave, Wyverne des tempêtes, Roi squelette, Reine de cristal.
# Usage : python croquis_boss.py   -> images dans ../croquis/
# Un petit personnage (5 studs, à la taille d'un joueur Roblox) est posé à côté de chaque boss pour l'échelle.
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from meshlib import Asset, blob, fin, gem, normalize, loft, ellipse_ring
from build import render, FOND
from croquis import OUT, X, Y, Z, V, line, head, leg, wing, spikes
from croquis2 import parts
from croquis3 import box


def joueur(a, pos):
    """Silhouette d'un joueur Roblox (5 studs de haut) pour donner l'échelle."""
    a.part("Joueur", "#F2F2F2")
    box(a, "Joueur", pos + V(0, 3.0, 0), 2, 2, 1)       # torse
    box(a, "Joueur", pos + V(0, 4.5, 0), 1.1, 1, 1.1)   # tête
    for sd in (-0.5, 0.5):
        box(a, "Joueur", pos + V(sd, 1.0, 0), 0.95, 2, 1)   # jambes
        box(a, "Joueur", pos + V(sd * 3, 3.0, 0), 0.95, 2, 1)  # bras


def ring(a, part, center, r, thick, axis_u=X, axis_v=Z, n=14):
    """Anneau (couronne, chaîne) : tube refermé sur lui-même."""
    pts = [center + (axis_u * np.cos(t) + axis_v * np.sin(t)) * r for t in np.linspace(0, 2 * np.pi, n + 1)]
    line(a, part, pts, [thick] * len(pts), 5)


# ---------- 1. Colosse de lave ----------
def colosse():
    a = Asset("Colosse")
    parts(a, (("Rock", "#2E2522", "SmoothPlastic"), ("Rock2", "#4A3B35", "SmoothPlastic"),
              ("Magma", "#FF6A1A", "Neon"), ("Core", "#FFC93A", "Neon"), ("Horns", "#1A1412", "SmoothPlastic"),
              ("Eyes", "#FFE14A", "Neon")))
    # Corps massif, bas sur pattes, voûté comme un rocher
    spine = line(a, "Rock", [V(0, 6, -34), V(0, 9, -24), V(0, 15, -12), V(0, 18, 0), V(0, 17, 10), V(0, 16, 17)],
                 [0.8, 3.5, 7.5, 8.5, 6.5, 4.5], 10)
    # Cratère sur le dos : un anneau de roche avec du magma au fond
    cr = V(0, 25.5, -5)
    rings = [ellipse_ring(cr + V(0, h, 0), X, Z, r, r, 12) for h, r in ((-3, 6.5), (0, 5.5), (1.5, 4.0), (0.8, 3.0))]
    a.add("Rock2", *loft(rings))
    a.add("Magma", *blob(cr + V(0, 0.6, 0), Z, Y, X, 3.0, 0.8, 3.0, 10, 3))
    # Plaques de roche en couches sur le dos et les flancs
    rng = np.random.default_rng(4)
    for k in range(4, len(spine) - 5, 2):
        p = spine[k]
        r = 2 + 6.5 * np.sin(np.pi * min(1, k / (len(spine) * 0.75)))
        for ang in (-0.9, -0.45, 0.45, 0.9):
            o = normalize(V(np.sin(ang), np.cos(ang), 0))
            c = p + o * r * 0.95
            a.add("Rock2" if k % 4 else "Rock", *gem(c, normalize(o + V(0, 0, -0.4)), Z, np.cross(o, Z),
                                                    r * 0.35, r * 0.3 * rng.uniform(0.8, 1.2), r * 0.35))
        # fissures de magma entre les plaques
        line(a, "Magma", [p + V(-r * 1.0, r * 0.2, 0), p + V(-r * 0.5, r * 0.95, 0.4), p + V(r * 0.5, r * 0.95, -0.3),
                          p + V(r * 1.0, r * 0.2, 0)], [0.25, 0.3, 0.3, 0.25], 4)
    # Cœur de magma dans la poitrine (point faible)
    # (sous le cou, entre les pattes avant : bien visible de face)
    a.add("Magma", *blob(V(0, 11, 16.5), Z, Y, X, 2.4, 3.6, 3.2, 8, 4))
    a.add("Core", *blob(V(0, 11, 18.4), Z, Y, X, 1.4, 2.6, 2.2, 8, 4))
    # Tête large et basse, cornes vers l'avant comme un taureau
    f, u, s = head(a, V(0, 15, 22), V(0, -0.25, 1), 5.0, horns="Horns", body="Rock", belly="Rock2", horn_len=0.8,
                   horn_up=0.1)
    for sd in (1, -1):
        line(a, "Horns", [V(sd * 3.5, 18, 20), V(sd * 7, 18.5, 23), V(sd * 8, 17, 28)], [1.0, 0.7, 0.0], 6)
        # pattes énormes, piliers de roche
        for z, back in ((10, 0.4), (-14, -0.6)):
            hip = V(sd * 7, 13, z)
            foot = V(sd * 9.5, 0.8, z + back * 2)
            leg(a, "Rock", hip, foot, 3.2, claws="Horns", knee_back=back)
            line(a, "Magma", [hip + V(sd * 2.6, -1, 0), foot + V(sd * 1.8, 2.5, 0)], [0.25, 0.2], 4)
    # Queue en massue de roche
    a.add("Rock2", *gem(V(0, 6, -36), -Z, Y, X, 3.5, 2.8, 3.0))
    joueur(a, V(16, 0, 26))
    return a, "Colosse de lave", "volcan vivant : cratère sur le dos, cœur de magma (point faible), pattes en piliers"


# ---------- 2. Wyverne des tempêtes ----------
def wyverne_tempete():
    a = Asset("WyverneTempete")
    parts(a, (("Body", "#1E2A4A", "SmoothPlastic"), ("Belly", "#8FA7C9", "SmoothPlastic"),
              ("Horns", "#D9E4F2", "SmoothPlastic"), ("Fins", "#2B3E6B", "SmoothPlastic"),
              ("Bolt", "#7FE9FF", "Neon"), ("Eyes", "#7FE9FF", "Neon")))
    spine = line(a, "Body", [V(0, 14, -40), V(0, 12, -30), V(0, 13, -18), V(0, 17, -6), V(0, 20, 3), V(0, 26, 9),
                             V(0, 31, 12)], [0.2, 1.2, 2.8, 4.6, 4.2, 2.3, 1.8], 9)
    line(a, "Belly", [V(0, 14.5, -8), V(0, 15.5, 0), V(0, 18, 5)], [3.0, 3.4, 2.4], 8, flat=0.45)
    f, u, s = head(a, V(0, 32, 15), V(0, -0.1, 1), 4.0, horn_len=1.8, horn_up=0.2)
    # Tête en forme de lance : une grande corne frontale
    line(a, "Horns", [V(0, 34, 15), V(0, 36, 12), V(0, 38, 6)], [0.9, 0.6, 0.0], 6)
    spikes(a, "Horns", spine[8:-6], Y, 1.5, 0.8, 3)
    for sd in (1, -1):
        leg(a, "Body", V(sd * 3, 15, -4), V(sd * 5, 0.8, -1), 1.7, knee_back=-0.8)
        wing(a, V(sd * 3, 22, 2), sd, 38, bone="Horns", skin="Fins", fingers=5, lift=0.45, sweep=0.2)
        # veines électriques sur la membrane
        sh = V(sd * 3, 22, 2)
        for k in range(4):
            t = k / 3
            tip = sh + V(sd * (26 - 6 * t), 6 - 14 * t, -10 - 8 * t)
            mid = (sh + tip) / 2 + V(sd * 1.5, (-1) ** k * 1.5, 0)
            line(a, "Bolt", [sh + V(sd * 6, 4, -2), mid, tip], [0.25, 0.2, 0.0], 4)
    # Dard foudroyant au bout de la queue
    a.add("Bolt", *gem(V(0, 14.5, -43), -Z, Y, X, 3.0, 1.0, 1.4))
    for k in range(3):
        line(a, "Bolt", [V(0, 14.5, -45), V((k - 1) * 2.5, 16 + k, -48), V((k - 1) * 3.5, 15 - k, -51)], [0.2, 0.15, 0.0], 4)
    joueur(a, V(18, 0, 18))
    return a, "Wyverne des tempêtes", "boss aérien : ailes immenses aux veines électriques, corne en lance, dard foudroyant"


# ---------- 3. Roi squelette ----------
def roi_squelette():
    a = Asset("RoiSquelette")
    parts(a, (("Bone", "#E3D8BF", "SmoothPlastic"), ("Dark", "#2B2621", "SmoothPlastic"),
              ("Iron", "#5A5F66", "SmoothPlastic"), ("Gold", "#D9A93F", "SmoothPlastic"),
              ("Soul", "#5CFF9D", "Neon"), ("Eyes", "#5CFF9D", "Neon"), ("Membrane", "#3A2A44", "SmoothPlastic")))
    path = [V(0, 16 + 4 * np.sin(k * 0.45 + 0.8), 22 - 4.2 * k) for k in range(14)]
    for k, p in enumerate(path):                                             # vertèbres
        r = 2.0 - 0.12 * k
        a.add("Bone", *blob(p, Z, Y, X, 1.1, r, r, 6, 3))
        a.add("Bone", *fin(p - Z * 0.7, p + Z * 0.7, p + V(0, r + 2.2, -1.0), X, 0.4))
    line(a, "Dark", path, [0.6] * len(path), 5)
    for k in range(2, 7):                                                    # cage thoracique
        p = path[k]
        for sd in (1, -1):
            line(a, "Bone", [p, p + V(sd * 5, -1.5, 0), p + V(sd * 4.6, -7.5, 0.6), p + V(sd * 0.6, -9.5, 1)],
                 [0.55, 0.5, 0.4, 0.3], 5)
    a.add("Soul", *blob(path[4] + V(0, -4.5, 0), Z, Y, X, 3.2, 3.5, 3.0, 8, 4))  # âme (point faible)
    f, u, s = head(a, path[0] + V(0, 2.5, 5.5), V(0, -0.2, 1), 5.5, horns="Bone", body="Bone", belly="Bone",
                   eyes="Eyes", horn_len=1.6, horn_up=0.4)
    hc = path[0] + V(0, 2.5, 5.5)
    ring(a, "Gold", hc + V(0, 3.0, -0.8), 2.6, 0.4)                          # couronne
    for k in range(6):
        t = k * np.pi / 3
        b = hc + V(2.6 * np.cos(t), 3.0, -0.8 + 2.6 * np.sin(t))
        line(a, "Gold", [b, b + V(0, 2.0, 0)], [0.4, 0.0], 4)
    for sd in (1, -1):                                                       # flammes fantômes aux yeux
        e = hc + V(sd * 2.2, 1.4, 2.2)
        line(a, "Soul", [e, e + V(sd * 1.0, 2.0, -2.0), e + V(sd * 1.8, 3.6, -5.0)], [0.5, 0.35, 0.0], 5)
        leg(a, "Bone", path[2] + V(sd * 2, -1.5, 0), V(sd * 6, 0.6, 16), 1.1, claws="Bone", knee_back=0.6)
        leg(a, "Bone", path[8] + V(sd * 2, -1.5, 0), V(sd * 6, 0.6, -14), 1.2, claws="Bone")
        # chaînes cassées qui pendent des pattes avant
        for k in range(4):
            ring(a, "Iron", V(sd * 6.5, 2.5 - k * 0.0 + 1.6 * k, 16 + (k % 2) * 0.3), 0.55, 0.15,
                 axis_u=Y, axis_v=(Z if k % 2 else X), n=8)
        # aile en os, membrane déchirée
        sh = path[3] + V(sd * 1.5, 2, 0)
        el = sh + V(sd * 11, 8, -2)
        wr = el + V(sd * 10, 5, 2)
        line(a, "Bone", [sh, el, wr], [0.9, 0.7, 0.55], 5)
        tips = [wr + V(sd * (13 - 4 * t), -5 - 11 * t, -6 - 6 * t) for t in np.linspace(0, 1, 4)]
        for k, tp in enumerate(tips):
            line(a, "Bone", [wr, tp], [0.4, 0.0], 4)
            if k in (0, 2):
                a.add("Membrane", *fin(wr, tp, tips[k + 1] * 0.6 + wr * 0.4, Y, 0.2))
    joueur(a, V(16, 0, 26))
    return a, "Roi squelette", "mort-vivant couronné : âme verte dans les côtes (point faible), chaînes cassées, ailes déchirées"


# ---------- 4. Reine de cristal ----------
def reine_cristal():
    a = Asset("ReineCristal")
    parts(a, (("Crystal", "#8FD8FF", "SmoothPlastic"), ("Crystal2", "#B48CFF", "SmoothPlastic"),
              ("Crystal3", "#E7F7FF", "SmoothPlastic"), ("Core", "#FF7FE6", "Neon"), ("Eyes", "#FFFFFF", "Neon")))
    path = [V(1.5 * np.sin(k * 0.7), 14 + 2.5 * np.sin(k * 0.55 + 0.6), 18 - 4.0 * k) for k in range(13)]
    for k, p in enumerate(path):
        r = 4.5 - 0.32 * k
        d = normalize(path[min(k + 1, 12)] - path[max(k - 1, 0)])
        # corps : gros cristaux qui se chevauchent, en alternant deux couleurs
        a.add("Crystal" if k % 2 else "Crystal2", *gem(p, d, Y, X, 3.6, r, r * 0.95))
        if k < 10 and k % 2 == 0:                                             # pics de cristal sur le dos
            a.add("Crystal3", *gem(p + V(0, r * 1.3, -0.5), normalize(Y - d * 0.6), d, X, r * 1.0, 0.3 * r, 0.25 * r))
    a.add("Core", *gem(path[1] + V(0, -1, 2.6), Z, Y, X, 1.8, 2.4, 1.8))      # cristal-cœur (point faible)
    hc = path[0] + V(0, 3, 5)
    a.add("Crystal", *gem(hc, Z, Y, X, 5.0, 3.6, 3.8))
    a.add("Crystal2", *gem(hc + V(0, -0.6, 5.4), Z, Y, X, 4.0, 1.9, 2.1))
    a.add("Crystal3", *gem(hc + V(0, -3.0, 3.8), normalize(V(0, -0.3, 1)), Y, X, 3.6, 1.2, 1.8))
    for k in range(7):                                                       # couronne de cristaux
        ang = -0.9 + 1.8 * k / 6
        b = hc + V(np.sin(ang) * 2.4, 2.4, -1.0 - np.cos(ang) * 0.6)
        L = 4.5 - abs(ang) * 2
        a.add(("Crystal3", "Crystal2")[k % 2], *gem(b + V(np.sin(ang) * 0.6, L / 2, -0.4), normalize(V(np.sin(ang) * 0.4, 1, -0.3)),
                                                     Z, X, L / 2, 0.35, 0.35))
    for sd in (1, -1):
        a.add("Eyes", *gem(hc + V(sd * 2.0, 0.9, 2.4), Z, Y, X, 1.0, 0.3, 0.2))
        for idx, back in ((2, 0.6), (8, -0.6)):                               # pattes
            p = path[idx]
            knee = V(sd * 6.5, 8, p[2] + back)
            a.add("Crystal", *gem((p + knee) / 2, normalize(knee - p), Z, X, 4.5, 1.6, 1.6))
            foot = V(sd * 7.5, 0.4, p[2] + back * 3)
            a.add("Crystal2", *gem((knee + foot) / 2, normalize(foot - knee), Z, X, 4.2, 1.3, 1.3))
        # ailes en grands éclats de verre
        sh = path[3] + V(sd * 2.5, 3, 0)
        for k, ang in enumerate(np.linspace(0.25, 1.05, 3)):
            d = normalize(V(sd * np.cos(ang), np.sin(ang) * 0.9, -0.4 - 0.5 * k))
            L = 26 - 5 * k
            a.add(("Crystal3", "Crystal", "Crystal2")[k % 3], *gem(sh + d * L / 2, d, Y, np.cross(d, Y), L / 2, 0.3, 2.6))
    end = path[-1]
    for ang in np.linspace(-0.7, 0.7, 3):
        d = normalize(V(np.sin(ang), 0.2, -1))
        a.add("Crystal3", *gem(end + d * 3, d, Y, X, 3.8, 1.0, 0.8))
    joueur(a, V(16, 0, 24))
    return a, "Reine de cristal", "dragonne en cristaux taillés : couronne, cristal-cœur rose (point faible), ailes en éclats"


def main():
    sketches = [colosse(), wyverne_tempete(), roi_squelette(), reine_cristal()]
    fig = plt.figure(figsize=(22, 11), facecolor=FOND)
    for k, (a, title, desc) in enumerate(sketches):
        ax = fig.add_subplot(2, 4, k + 1, projection="3d")
        render(ax, a, 18, -50, f"{k + 1}. {title}", zoom=1.5)
        ax = fig.add_subplot(2, 4, k + 5, projection="3d")
        render(ax, a, 6, 0, "profil (le petit blanc = un joueur)", zoom=1.5)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "boss-planche.png"), dpi=72, facecolor=FOND)
    plt.close(fig)
    for k, (a, title, desc) in enumerate(sketches):
        fig = plt.figure(figsize=(16, 13), facecolor=FOND)
        for j, (elev, azim, t) in enumerate(((18, -50, "Trois-quarts"), (6, 0, "Profil"), (8, -90, "Face"),
                                              (60, -60, "Dessus"))):
            ax = fig.add_subplot(2, 2, j + 1, projection="3d")
            render(ax, a, elev, azim, t, zoom=1.45)
        fig.suptitle(f"{title} : {desc}", color="white", fontsize=15)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, f"boss-{k + 1}-{a.name.lower()}.png"), dpi=60, facecolor=FOND)
        plt.close(fig)
        print(title, a.tri_count(), "triangles")


if __name__ == "__main__":
    main()
