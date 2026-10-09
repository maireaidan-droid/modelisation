# Croquis 3D, série 2 : même idée (un dragon), 5 styles très différents.
# Usage : python croquis2.py   -> images dans ../croquis/
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from meshlib import Asset, blob, fin, gem, normalize
from build import render, FOND
from croquis import OUT, X, Y, Z, V, line, head, leg, wing, spikes


def parts(a, spec):
    for n, c, m in spec:
        a.part(n, c, m)


# ---------- A. Mignon (chibi) ----------
def chibi():
    a = Asset("Chibi")
    parts(a, (("Body", "#7FD1AE", "SmoothPlastic"), ("Belly", "#FFF1C9", "SmoothPlastic"),
              ("Fins", "#FF9EC4", "SmoothPlastic"), ("Horns", "#FFE7A8", "SmoothPlastic"),
              ("White", "#FFFFFF", "SmoothPlastic"), ("Eyes", "#2A2340", "SmoothPlastic"),
              ("Cheeks", "#FF8FB0", "Neon")))
    a.add("Body", *blob(V(0, 4.5, 0), Z, Y, X, 3.0, 3.2, 2.8, 10, 6))             # corps tout rond
    a.add("Belly", *blob(V(0, 4.2, 1.2), Z, Y, X, 2.0, 2.6, 2.2, 10, 5))
    c = V(0, 10, 1.2)
    a.add("Body", *blob(c, Z, Y, X, 3.6, 3.3, 3.9, 12, 6))                        # grosse tête
    a.add("Body", *blob(c + V(0, -1.0, 3.0), Z, Y, X, 1.4, 1.2, 1.8, 10, 4))       # petit museau
    for sd in (1, -1):
        e = c + V(sd * 1.7, 0.4, 3.0)
        a.add("White", *blob(e, Z, Y, X, 0.5, 1.2, 0.95, 10, 5))                 # grands yeux
        a.add("Eyes", *blob(e + V(0, -0.1, 0.35), Z, Y, X, 0.3, 0.85, 0.65, 10, 5))
        a.add("White", *blob(e + V(sd * -0.2, 0.4, 0.62), Z, Y, X, 0.1, 0.25, 0.22, 6, 3))
        a.add("Cheeks", *blob(c + V(sd * 2.6, -1.3, 2.4), Z, Y, X, 0.2, 0.45, 0.6, 8, 3))
        line(a, "Horns", [c + V(sd * 1.4, 2.6, -0.6), c + V(sd * 1.9, 4.0, -1.4), c + V(sd * 2.0, 4.6, -2.4)],
             [0.6, 0.4, 0.0], 6)
        a.add("Body", *blob(V(sd * 1.8, 1.0, 1.0), Z, Y, X, 1.0, 1.0, 0.9, 8, 4))  # pattes boudinées
        a.add("Body", *blob(V(sd * 1.8, 1.0, -1.4), Z, Y, X, 1.0, 1.0, 0.9, 8, 4))
        a.add("Body", *blob(V(sd * 2.6, 5.6, 1.6), normalize(V(sd * 0.5, -1, 0.6)), Z, X, 1.2, 0.7, 0.7, 8, 4))
        # petites ailes en cœur
        b = V(sd * 1.8, 7.0, -1.6)
        a.add("Fins", *fin(b, b + V(sd * 3.0, 2.6, -0.8), b + V(sd * 2.6, -0.6, -1.2), Z, 0.3))
        a.add("Fins", *fin(b, b + V(sd * 1.5, 3.0, -0.6), b + V(sd * 3.0, 2.6, -0.8), Z, 0.3))
    line(a, "Body", [V(0, 3, -2.5), V(0, 2, -5), V(0, 3, -7.5)], [1.2, 0.7, 0.3], 8)  # queue courte
    a.add("Fins", *gem(V(0, 3.4, -8.0), -Z, Y, X, 0.9, 0.8, 0.3))
    for k in range(3):
        p = V(0, 13.2 - k * 0.2, 0.4 - k * 1.4)
        a.add("Fins", *fin(p - Z * 0.6, p + Z * 0.6, p + V(0, 1.2, -0.6), X, 0.3))
    return a, "Mignon (chibi)", "grosse tête, grands yeux, corps rond : style pet / collection"


# ---------- B. Squelette ----------
def squelette():
    a = Asset("Squelette")
    parts(a, (("Bone", "#E6DCC3", "SmoothPlastic"), ("Dark", "#3B3530", "SmoothPlastic"),
              ("Membrane", "#4B2E5C", "SmoothPlastic"), ("Soul", "#5CFF9D", "Neon"), ("Eyes", "#5CFF9D", "Neon")))
    path = [V(0, 8 + 1.6 * np.sin(k * 0.5 + 0.6), 10 - 2.4 * k) for k in range(13)]
    for k, p in enumerate(path):                                                   # vertèbres
        r = 0.9 - 0.06 * k
        a.add("Bone", *blob(p, Z, Y, X, 0.5, r, r, 6, 3))
        a.add("Bone", *fin(p - Z * 0.3, p + Z * 0.3, p + V(0, r + 0.9, -0.5), X, 0.2))
    line(a, "Dark", path, [0.3] * len(path), 5)
    for k in range(2, 7):                                                          # côtes
        p = path[k]
        for sd in (1, -1):
            line(a, "Bone", [p, p + V(sd * 2.2, -0.8, 0), p + V(sd * 2.0, -3.4, 0.4), p + V(0.3 * sd, -4.3, 0.6)],
                 [0.25, 0.22, 0.18, 0.12], 5)
    a.add("Soul", *blob(path[3] + V(0, -2.0, 0), Z, Y, X, 1.4, 1.6, 1.4, 8, 4))     # flamme de l'âme
    f, u, s = head(a, path[0] + V(0, 1.2, 2.6), V(0, -0.15, 1), 2.6, horns="Bone", body="Bone", belly="Bone",
                   eyes="Eyes")
    for sd in (1, -1):                                                             # orbites creuses
        a.add("Dark", *gem(path[0] + V(sd * 1.05, 1.9, 3.5), Z, Y, X, 0.6, 0.45, 0.3))
        leg(a, "Bone", path[2] + V(sd * 1.2, -0.5, 0), V(sd * 2.6, 0.3, 7), 0.45, claws="Bone", knee_back=0.6)
        leg(a, "Bone", path[7] + V(sd * 1.2, -0.5, 0), V(sd * 2.6, 0.3, -6), 0.5, claws="Bone")
        # aile osseuse avec membrane déchirée (seulement 2 pans sur 4)
        sh = path[3] + V(sd * 0.8, 0.8, 0)
        el = sh + V(sd * 5, 3.5, -1)
        wr = el + V(sd * 4.5, 2.5, 1)
        line(a, "Bone", [sh, el, wr], [0.4, 0.3, 0.25], 5)
        tips = [wr + V(sd * (6 - 2 * t), -2 - 5 * t, -3 - 3 * t) for t in np.linspace(0, 1, 4)]
        for k, tp in enumerate(tips):
            line(a, "Bone", [wr, tp], [0.18, 0.0], 4)
            if k in (0, 2):
                a.add("Membrane", *fin(wr, tp, tips[k + 1] * 0.6 + wr * 0.4, Y, 0.1))
    return a, "Squelette (mort-vivant)", "os, côtes ouvertes, âme verte dans la poitrine, ailes déchirées"


# ---------- C. Cristal ----------
def cristal():
    a = Asset("Cristal")
    parts(a, (("Crystal", "#7FD8FF", "SmoothPlastic"), ("Crystal2", "#B48CFF", "SmoothPlastic"),
              ("Core", "#E8FBFF", "Neon"), ("Eyes", "#FFFFFF", "Neon")))
    path = [V(0.8 * np.sin(k * 0.8), 8 + 1.2 * np.sin(k * 0.6), 10 - 2.6 * k) for k in range(12)]
    for k, p in enumerate(path):                       # corps fait de gros cristaux taillés, bout à bout
        r = 2.2 - 0.16 * k
        d = normalize(path[min(k + 1, 11)] - path[max(k - 1, 0)])
        a.add("Crystal" if k % 2 else "Crystal2", *gem(p, d, Y, X, 2.1, r, r * 0.95))
        a.add("Crystal2" if k % 2 else "Crystal", *gem(p + d * 1.3, d, Y, X, 1.5, r * 0.7, r * 0.75))
        a.add("Crystal2" if k % 2 else "Crystal", *gem(p + V(0, r * 1.1, 0), normalize(Y - d * 0.6), d, X,
                                                        r * 1.0, 0.35 * r, 0.3 * r))
    a.add("Core", *blob(path[2], Z, Y, X, 1.0, 1.0, 1.0, 6, 3))
    hc = path[0] + V(0, 1.5, 3.2)                       # tête : 3 cristaux (crâne, museau, mâchoire)
    a.add("Crystal", *gem(hc, Z, Y, X, 2.6, 1.9, 2.0))
    a.add("Crystal2", *gem(hc + V(0, -0.4, 3.0), Z, Y, X, 2.2, 1.1, 1.2))
    a.add("Crystal", *gem(hc + V(0, -1.8, 2.0), normalize(V(0, -0.3, 1)), Y, X, 2.0, 0.7, 1.0))
    for sd in (1, -1):
        a.add("Eyes", *gem(hc + V(sd * 1.3, 0.6, 1.4), Z, Y, X, 0.6, 0.2, 0.15))
        a.add("Crystal2", *gem(hc + V(sd * 1.0, 2.6, -1.8), normalize(V(sd * 0.3, 1, -1.2)), Z, X, 2.6, 0.5, 0.5))
        for idx, back in ((2, 0.6), (7, -0.6)):        # pattes : deux cristaux (cuisse, jambe)
            p = path[idx]
            knee = V(sd * 3.2, 4.0, p[2] + back)
            a.add("Crystal", *gem((p + knee) / 2, normalize(knee - p), Z, X, 2.6, 0.9, 0.9))
            foot = V(sd * 3.4, 0.2, p[2] + back * 2)
            a.add("Crystal2", *gem((knee + foot) / 2, normalize(foot - knee), Z, X, 2.4, 0.7, 0.7))
        # ailes : grands éclats plats en éventail
        sh = path[3] + V(sd * 1.0, 1.0, 0)
        for k, ang in enumerate(np.linspace(0.2, 1.1, 4)):
            d = normalize(V(sd * np.cos(ang), np.sin(ang) * 0.8, -0.5 - 0.4 * k))
            L = 13 - 2 * k
            a.add("Crystal" if k % 2 else "Crystal2", *gem(sh + d * L / 2, d, Y, np.cross(d, Y), L / 2, 0.2, 1.6))
    end = path[-1]
    for k, ang in enumerate(np.linspace(-0.6, 0.6, 3)):
        d = normalize(V(np.sin(ang), 0.2, -1))
        a.add("Crystal2", *gem(end + d * 1.6, d, Y, X, 2.0, 0.5, 0.4))
    return a, "Cristal (géométrique)", "corps fait de cristaux taillés, cœur lumineux, ailes en éclats"


# ---------- D. Mécanique ----------
def mecanique():
    a = Asset("Mecanique")
    parts(a, (("Metal", "#8A8F96", "SmoothPlastic"), ("Brass", "#C9973B", "SmoothPlastic"),
              ("Dark", "#2E3136", "SmoothPlastic"), ("Core", "#FF8A1E", "Neon"), ("Eyes", "#FF8A1E", "Neon")))
    path = [V(0, 8 + 1.4 * np.sin(k * 0.5 + 0.4), 10 - 2.5 * k) for k in range(12)]
    for k, p in enumerate(path):                       # segments blindés reliés par des joints en laiton
        r = 2.0 - 0.13 * k
        d = normalize(path[min(k + 1, 11)] - path[max(k - 1, 0)])
        line(a, "Metal", [p - d * 0.9, p + d * 0.9], [r, r], 8)
        line(a, "Brass", [p + d * 0.9, p + d * 1.6], [r * 0.7, r * 0.7], 8)
        a.add("Dark", *fin(p - d * 0.6, p + d * 0.6, p + V(0, r + 1.0, -0.6), X, 0.3))
    a.add("Core", *blob(path[2] + V(0, 0, 0), Z, Y, X, 1.2, 1.2, 2.2, 8, 4))       # cœur-chaudière
    hc = path[0] + V(0, 1.3, 3)
    line(a, "Metal", [hc - Z * 1.2, hc + Z * 1.0, hc + V(0, -0.3, 3.2)], [1.6, 1.4, 0.9], 6)   # tête en boîte
    line(a, "Dark", [hc + V(0, -1.2, 0), hc + V(0, -1.5, 3.0)], [0.9, 0.5], 6)                 # mâchoire
    for sd in (1, -1):
        a.add("Eyes", *gem(hc + V(sd * 1.2, 0.5, 1.2), Z, Y, X, 0.5, 0.25, 0.15))
        line(a, "Brass", [hc + V(sd * 0.8, 1.2, -0.8), hc + V(sd * 1.4, 2.6, -3.2)], [0.35, 0.0], 5)
        line(a, "Dark", [hc + V(sd * 0.9, -0.2, 2.6), hc + V(sd * 2.0, 1.0, 3.6)], [0.12, 0.08], 4)  # cheminées
        for idx, back in ((2, 0.6), (8, -0.6)):        # pattes : vérins
            hip = path[idx] + V(sd * 1.6, -0.5, 0)
            foot = V(sd * 3.0, 0.4, path[idx][2] + back * 2)
            knee = (hip + foot) / 2 + V(sd * 0.8, 0.5, -back)
            line(a, "Metal", [hip, knee], [1.1, 0.9], 6)
            line(a, "Brass", [knee, foot], [0.7, 0.6], 6)
            a.add("Dark", *blob(knee, Z, Y, X, 0.6, 0.6, 0.6, 6, 3))
            a.add("Dark", *gem(foot, Z, Y, X, 1.0, 0.3, 0.7))
        # ailes : lames métalliques articulées
        sh = path[3] + V(sd * 1.6, 1.0, 0)
        el = sh + V(sd * 5, 3.0, -0.5)
        line(a, "Brass", [sh, el], [0.35, 0.3], 6)
        for k in range(5):
            t = k / 4
            d = normalize(V(sd * (1 - 0.6 * t), -0.2 - 0.5 * t, -0.4 - 0.8 * t))
            L = 8 - 2 * t
            a.add("Metal", *gem(el + d * L / 2, d, Y, np.cross(d, Y), L / 2, 0.12, 0.7))
    a.add("Core", *gem(path[-1] + V(0, 0, -1), -Z, Y, X, 1.0, 0.6, 0.6))
    return a, "Mécanique (steampunk)", "plaques de métal, joints en laiton, chaudière lumineuse, ailes en lames"


# ---------- E. Esprit de flammes ----------
def esprit():
    a = Asset("Esprit")
    parts(a, (("Flame", "#FF7A2E", "Neon"), ("Flame2", "#FFC93A", "Neon"), ("Flame3", "#FF3E6C", "Neon"),
              ("Core", "#FFF4C9", "Neon"), ("Eyes", "#FFFFFF", "Neon")))
    path = [V(2.2 * np.sin(k * 0.55), 9 + 2.4 * np.sin(k * 0.45 + 0.8), 12 - 2.6 * k) for k in range(13)]
    line(a, "Core", path[:10], [1.0, 1.1, 1.1, 1.0, 0.9, 0.8, 0.6, 0.45, 0.3, 0.0], 7)
    rng = np.random.default_rng(5)
    for k, p in enumerate(path):                       # langues de flamme tout autour du corps, vers l'arrière
        r = 1.8 * (1 - k / 14)
        d = normalize(path[min(k + 1, 12)] - path[max(k - 1, 0)])
        for j in range(6):
            ang = j * np.pi / 3 + k * 0.4
            o = normalize(np.cross(d, Y) * np.cos(ang) + Y * np.sin(ang))
            L = (2.2 + rng.uniform(0, 1.6)) * (1 - k / 16)
            base = p + o * r * 0.6
            a.add(("Flame", "Flame2", "Flame3")[(j + k) % 3],
                  *fin(base - d * 0.6, base + d * 0.6, base + o * L * 0.8 + d * L * 0.9 + Y * 0.5, np.cross(o, d), 0.12))
    hc = path[0] + V(0, 0.5, 2.2)
    a.add("Core", *blob(hc, Z, Y, X, 1.8, 1.2, 1.3, 8, 4))
    a.add("Flame2", *blob(hc + V(0, -0.3, 1.8), Z, Y, X, 1.2, 0.7, 0.8, 8, 3))
    for sd in (1, -1):
        a.add("Eyes", *gem(hc + V(sd * 0.8, 0.4, 1.2), Z, Y, X, 0.45, 0.15, 0.1))
        for k in range(4):                             # crinière et cornes de feu
            b = hc + V(sd * 0.7, 0.8, -0.4 - 0.5 * k)
            a.add(("Flame2", "Flame", "Flame3")[k % 3], *fin(b - Z * 0.5, b + Z * 0.5, b + V(sd * 1.0, 2.8 - 0.3 * k, -2.0), X, 0.15))
        # ailes de flammes
        sh = path[3] + V(sd * 0.8, 0.6, 0)
        for k in range(5):
            t = k / 4
            tip = sh + V(sd * (7 - 2.5 * t), 3.5 - 4 * t, -2 - 3 * t)
            a.add(("Flame", "Flame2", "Flame3")[k % 3], *fin(sh - Z * 0.8, sh + Z * 0.8, tip, Y, 0.12))
    return a, "Esprit de flammes", "corps fait de flammes lumineuses, pas de pattes, flotte dans l'air"


def main():
    sketches = [chibi(), squelette(), cristal(), mecanique(), esprit()]
    zooms = [1.05, 1.65, 1.65, 1.65, 1.65]
    fig = plt.figure(figsize=(25, 11), facecolor=FOND)
    for k, (a, title, desc) in enumerate(sketches):
        ax = fig.add_subplot(2, 5, k + 1, projection="3d")
        render(ax, a, 22, -50, f"{'ABCDE'[k]}. {title}", zoom=zooms[k])
        ax = fig.add_subplot(2, 5, k + 6, projection="3d")
        render(ax, a, 6, 0, "profil", zoom=zooms[k])
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "styles-planche.png"), dpi=70, facecolor=FOND)
    plt.close(fig)
    for k, (a, title, desc) in enumerate(sketches):
        fig = plt.figure(figsize=(16, 13), facecolor=FOND)
        for j, (elev, azim, t) in enumerate(((22, -50, "Trois-quarts"), (6, 0, "Profil"), (8, -90, "Face"),
                                              (65, -60, "Dessus"))):
            ax = fig.add_subplot(2, 2, j + 1, projection="3d")
            render(ax, a, elev, azim, t, zoom=zooms[k])
        fig.suptitle(f"{title} : {desc}", color="white", fontsize=16)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, f"style-{'abcde'[k]}-{a.name.lower()}.png"), dpi=60, facecolor=FOND)
        plt.close(fig)
        print(title, a.tri_count(), "triangles")


if __name__ == "__main__":
    main()
