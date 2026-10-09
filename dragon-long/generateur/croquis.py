# Croquis 3D low-poly de 5 nouveaux dragons (silhouettes à comparer avant d'en choisir un).
# Usage : python croquis.py   -> images dans ../croquis/
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from meshlib import Asset, catmull_rom, tube, blob, fin, gem, normalize
from build import render, FOND

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "croquis")
os.makedirs(OUT, exist_ok=True)

X, Y, Z = np.eye(3)


def V(*c):
    return np.array(c, float)


def line(a, part, pts, radii, sides=7, flat=1.0, up=Y):
    pts = catmull_rom([np.asarray(p, float) for p in pts], max(8, 4 * len(pts)))
    r = np.interp(np.linspace(0, 1, len(pts)), np.linspace(0, 1, len(radii)), radii)
    a.add(part, *tube(pts, r, sides, flat=flat, up=up))
    return pts


def head(a, c, f, size, horns="Horns", body="Body", belly="Belly", eyes="Eyes", horn_len=1.3, horn_up=0.6):
    """Tête de dragon : crâne, museau, mâchoire, yeux, deux cornes vers l'arrière."""
    f = normalize(f)
    u = normalize(Y - f * (Y @ f))
    s = normalize(np.cross(u, f))
    a.add(body, *blob(c, f, u, s, size * 0.6, size * 0.45, size * 0.48, 8, 4))
    line(a, body, [c, c + f * size * 0.8 + u * size * 0.05, c + f * size * 1.45 - u * size * 0.05],
         [size * 0.42, size * 0.32, size * 0.2], 8, flat=0.75, up=u)
    line(a, belly, [c - u * size * 0.3, c + f * size * 0.8 - u * size * 0.38, c + f * size * 1.3 - u * size * 0.32],
         [size * 0.3, size * 0.2, size * 0.1], 6, flat=0.6, up=u)
    for sd in (1, -1):
        a.add(eyes, *gem(c + f * size * 0.35 + u * size * 0.22 + s * sd * size * 0.4, f, u, s,
                         size * 0.17, size * 0.08, size * 0.06))
        base = c + u * size * 0.3 - f * size * 0.1 + s * sd * size * 0.25
        line(a, horns, [base, base - f * size * horn_len * 0.5 + u * size * horn_up + s * sd * size * 0.15,
                        base - f * size * horn_len + u * size * horn_up * 1.2 + s * sd * size * 0.2],
             [size * 0.13, size * 0.08, 0.0], 5)
    return f, u, s


def leg(a, part, hip, foot, r, claws="Horns", knee_out=0.0, knee_back=-0.6):
    knee = (hip + foot) / 2 + V(knee_out, 0, knee_back) * np.linalg.norm(hip - foot) * 0.35
    line(a, part, [hip, knee, foot], [r, r * 0.7, r * 0.55], 6)
    for k in (-1, 0, 1):
        line(a, claws, [foot, foot + V(k * r * 0.5, -r * 0.35, r * 1.1)], [r * 0.2, 0.0], 4)


def wing(a, shoulder, side, span, bone="Horns", skin="Fins", fingers=4, lift=0.35, sweep=0.25):
    """Aile de chauve-souris : bras (épaule, coude, poignet), doigts en éventail, membrane tendue entre eux."""
    elbow = shoulder + V(side * span * 0.35, span * lift * 0.6, -span * 0.08)
    wrist = elbow + V(side * span * 0.3, span * lift * 0.5, span * 0.12)
    line(a, bone, [shoulder, elbow, wrist], [span * 0.035, span * 0.03, span * 0.025], 5)
    line(a, bone, [wrist, wrist + V(side * span * 0.06, span * 0.1, span * 0.08)], [span * 0.02, 0.0], 4)  # pouce
    tips = []
    for k in range(fingers):
        t = k / (fingers - 1)
        tip = wrist + V(side * span * (0.45 - 0.2 * t), -span * (0.05 + 0.55 * t), -span * (sweep + 0.25 * t))
        line(a, bone, [wrist, (wrist + tip) / 2 + V(0, span * 0.03, 0), tip], [span * 0.02, span * 0.015, 0.0], 4)
        tips.append(tip)
    n = V(0, 1, 0)
    root = shoulder + V(side * span * 0.05, -span * 0.1, -span * 0.45)   # la membrane rejoint le flanc
    for t0, t1 in zip(tips[:-1], tips[1:]):
        a.add(skin, *fin(wrist, t0, t1 * 0.97 + t0 * 0.03 - V(0, span * 0.04, 0), n, span * 0.01))
    a.add(skin, *fin(wrist, tips[-1], root, n, span * 0.01))
    a.add(skin, *fin(wrist, root, elbow, n, span * 0.01))
    a.add(skin, *fin(elbow, root, shoulder, n, span * 0.01))


def spikes(a, part, pts, ups, h0, h1, every=2):
    for k in range(0, len(pts) - 1, every):
        t = k / (len(pts) - 1)
        h = h0 + (h1 - h0) * t
        p, q = pts[k], pts[min(k + 1, len(pts) - 1)]
        d = normalize(q - p)
        a.add(part, *fin(p - d * h * 0.4, p + d * h * 0.4, p + ups * h - d * h * 0.5, np.cross(d, ups), h * 0.15))


# ---------- 1. Wyverne ----------
def wyverne():
    a = Asset("Wyverne")
    for n, c, m in (("Body", "#8E2B22", "SmoothPlastic"), ("Belly", "#D9A55A", "SmoothPlastic"),
                    ("Fins", "#5E1A1C", "SmoothPlastic"), ("Horns", "#E8DCC0", "SmoothPlastic"),
                    ("Eyes", "#FFC93A", "Neon")):
        a.part(n, c, m)
    spine = line(a, "Body", [V(0, 9, -26), V(0, 7, -18), V(0, 7.5, -9), V(0, 9, -2), V(0, 10, 3), V(0, 13.5, 7), V(0, 16, 9.5)],
                 [0.15, 0.7, 1.6, 2.6, 2.3, 1.3, 1.0], 9)
    line(a, "Belly", [V(0, 8.1, -6), V(0, 8.0, 0), V(0, 9.0, 4)], [1.2, 1.7, 1.2], 7, flat=0.5)
    head(a, V(0, 16.5, 11), V(0, -0.15, 1), 2.4)
    spikes(a, "Fins", spine[6:-6], Y, 0.6, 1.2, 3)
    for sd in (1, -1):
        leg(a, "Body", V(sd * 1.8, 8, -4), V(sd * 2.6, 0.3, -2.5), 1.0)
        wing(a, V(sd * 1.6, 11.5, 2.5), sd, 17)
    # Dard au bout de la queue
    a.add("Horns", *gem(V(0, 9, -27.5), -Z, Y, X, 1.6, 0.5, 0.9))
    return a, "Wyverne", "dragon européen : 2 pattes, 2 grandes ailes, queue à dard"


# ---------- 2. Amphiptère ----------
def amphiptere():
    a = Asset("Amphiptere")
    for n, c, m in (("Body", "#1F8A70", "SmoothPlastic"), ("Belly", "#F2D16B", "SmoothPlastic"),
                    ("Feathers", "#E8483B", "SmoothPlastic"), ("Feathers2", "#2EC4E6", "SmoothPlastic"),
                    ("Feathers3", "#F6B21A", "SmoothPlastic"), ("Horns", "#F3E9D2", "SmoothPlastic"),
                    ("Eyes", "#7CFF6B", "Neon")):
        a.part(n, c, m)
    ctrl = [V(1.5 * np.sin(k * 0.7), 9 + 3.2 * np.sin(k * 0.55 + 1), 14 - 3.4 * k) for k in range(12)]
    spine = line(a, "Body", ctrl, [1.4, 1.6, 1.7, 1.6, 1.4, 1.2, 1.0, 0.8, 0.6, 0.45, 0.3, 0.1], 9)
    f, u, s = head(a, ctrl[0] + V(0, 0.6, 1.8), V(0, -0.1, 1), 1.9, horn_len=0.6, horn_up=0.3)
    # Collerette de plumes autour de la tête
    c0 = ctrl[0] + V(0, 0.4, 0.3)
    for k in range(14):
        ang = -0.2 + np.pi * 1.4 * k / 13 - 0.5
        d = normalize(V(np.cos(ang), np.sin(ang), -0.5))
        col = ("Feathers", "Feathers2", "Feathers3")[k % 3]
        w = normalize(np.cross(d, Z)) * 0.55
        a.add(col, *fin(c0 + d * 1.2 - w, c0 + d * 1.2 + w, c0 + d * 4.4 - Z * 1.2, Z, 0.12))
    # Ailes en plumes : chaque plume est une longue lame colorée
    for sd in (1, -1):
        sh = spine[10] + V(sd * 1.2, 0.8, 0)
        arm = [sh, sh + V(sd * 5, 3.5, -1), sh + V(sd * 10.5, 4.5, -2.5)]
        line(a, "Body", arm, [0.45, 0.35, 0.2], 5)
        for k in range(11):
            t = k / 10
            base = arm[1] * (1 - t) + arm[2] * t if t > 0.3 else sh * (1 - t / 0.3) + arm[1] * (t / 0.3)
            L = 3.5 + 4.5 * t
            tip = base + V(sd * L * 0.35 * t, -L * 0.15, -L)
            col = ("Feathers", "Feathers2", "Feathers3")[k % 3]
            a.add(col, *fin(base - X * 0.7, base + X * 0.7, tip, V(0, 1, 0), 0.12))
    # Plumes au bout de la queue
    end = ctrl[-1]
    for k, ang in enumerate(np.linspace(-0.7, 0.7, 5)):
        d = normalize(V(np.sin(ang), 0.2, -np.cos(ang)))
        a.add(("Feathers", "Feathers2", "Feathers3")[k % 3], *fin(end - X * 0.6, end + X * 0.6, end + d * 5, Y, 0.1))
    return a, "Amphiptère", "serpent à plumes : pas de pattes, 2 ailes de plumes, collerette"


# ---------- 3. Drake de lave ----------
def drake():
    a = Asset("Drake")
    for n, c, m in (("Body", "#3A2F2C", "SmoothPlastic"), ("Belly", "#6B4A3A", "SmoothPlastic"),
                    ("Rock", "#5C5550", "SmoothPlastic"), ("Magma", "#FF6A1A", "Neon"),
                    ("Horns", "#2A2321", "SmoothPlastic"), ("Eyes", "#FFE14A", "Neon")):
        a.part(n, c, m)
    spine = line(a, "Body", [V(0, 4, -20), V(0, 5.5, -13), V(0, 7.5, -6), V(0, 8.5, 0), V(0, 8, 5), V(0, 8.5, 9)],
                 [0.4, 1.6, 3.4, 3.9, 3.0, 2.2], 10)
    line(a, "Belly", [V(0, 5.2, -7), V(0, 5.0, 0), V(0, 5.6, 5)], [2.4, 2.8, 2.0], 8, flat=0.45)
    head(a, V(0, 9, 11.5), V(0, -0.2, 1), 3.0, horn_len=1.0, horn_up=0.2)
    for sd in (1, -1):
        leg(a, "Body", V(sd * 3, 6.5, 4), V(sd * 4.2, 0.6, 5.5), 1.5, knee_back=0.5)
        leg(a, "Body", V(sd * 3, 6.5, -6), V(sd * 4.2, 0.6, -6.5), 1.7)
    # Plaques de roche sur le dos, avec du magma dans les fentes
    rng = np.random.default_rng(3)
    for k in range(3, len(spine) - 4, 2):
        p = spine[k]
        r = 0.9 + 1.3 * np.sin(np.pi * k / len(spine))
        for sd in (-1, 0, 1):
            c = p + V(sd * r * 0.9, r * 1.0 + 1.6 - abs(sd) * 0.6, 0)
            a.add("Rock", *gem(c, normalize(V(rng.normal() * 0.2, 0.3, 1)), Y, X, r * 0.6, r * 0.5, r * 0.55))
        line(a, "Magma", [p + V(-r * 1.5, r * 0.6 + 1, 0), p + V(0, r * 0.9 + 1.2, 0.3), p + V(r * 1.5, r * 0.6 + 1, 0)],
             [0.12, 0.16, 0.12], 4)
    for k in range(4, len(spine) - 6, 3):       # fissures sur les flancs
        p = spine[k]
        for sd in (1, -1):
            line(a, "Magma", [p + V(sd * 3.2, 0.5, -1), p + V(sd * 3.4, -0.6, 0.2), p + V(sd * 3.1, -1.6, 1.3)],
                 [0.1, 0.13, 0.0], 4)
    return a, "Drake de lave", "dragon de sol massif : 4 pattes, dos de roche, fissures de magma"


# ---------- 4. Hydre ----------
def hydre():
    a = Asset("Hydre")
    for n, c, m in (("Body", "#3E6B3A", "SmoothPlastic"), ("Belly", "#C9C27A", "SmoothPlastic"),
                    ("Fins", "#7A2E5A", "SmoothPlastic"), ("Horns", "#E0D6B8", "SmoothPlastic"),
                    ("Eyes", "#FF4A3A", "Neon")):
        a.part(n, c, m)
    spine = line(a, "Body", [V(0, 4, -22), V(0, 5, -14), V(0, 7, -6), V(0, 8, 0), V(0, 7.6, 4)],
                 [0.3, 1.5, 3.2, 3.6, 2.8], 10)
    line(a, "Belly", [V(0, 4.6, -6), V(0, 4.6, 0), V(0, 5.4, 3)], [2.2, 2.6, 1.8], 8, flat=0.45)
    spikes(a, "Fins", spine[4:-6], Y, 0.8, 1.6, 3)
    for sd in (1, -1):
        leg(a, "Body", V(sd * 2.6, 6, 2), V(sd * 3.8, 0.5, 3.5), 1.3, knee_back=0.5)
        leg(a, "Body", V(sd * 2.6, 6, -7), V(sd * 3.8, 0.5, -7.5), 1.5)
    for k, (ox, oy, lean) in enumerate(((-3.5, 0, -0.5), (0, 2.5, 0), (3.5, 0, 0.5))):
        base = V(ox * 0.4, 8.5, 4.5)
        mid = V(ox, 13 + oy, 8)
        top = V(ox * 1.5, 16 + oy, 11)
        neck = line(a, "Body", [base, mid, top], [1.8, 1.1, 0.9], 8)
        spikes(a, "Fins", neck[2:-2], normalize(V(0, 0.4, -1)), 0.5, 0.7, 3)
        head(a, top + V(lean * 0.5, 0.4, 1.4), V(lean * 0.4, -0.25, 1), 1.9, horn_len=1.0)
    return a, "Hydre", "corps de lézard massif, 3 longs cous, 3 têtes"


# ---------- 5. Léviathan des abysses ----------
def leviathan():
    a = Asset("Leviathan")
    for n, c, m in (("Body", "#123A5E", "SmoothPlastic"), ("Belly", "#7FC8D8", "SmoothPlastic"),
                    ("Fins", "#2BA6C9", "SmoothPlastic"), ("Horns", "#D8EEF2", "SmoothPlastic"),
                    ("Glow", "#5BFFE6", "Neon"), ("Eyes", "#5BFFE6", "Neon")):
        a.part(n, c, m)
    ctrl = [V(2.4 * np.sin(k * 0.6), 8 + 1.2 * np.sin(k * 0.45), 16 - 3.6 * k) for k in range(12)]
    spine = line(a, "Body", ctrl, [1.8, 2.0, 2.1, 2.0, 1.8, 1.6, 1.3, 1.0, 0.8, 0.6, 0.4, 0.2], 9)
    line(a, "Belly", [p - Y * 0.9 for p in ctrl[1:8]], [1.3, 1.4, 1.3, 1.2, 1.0, 0.8, 0.6], 7, flat=0.4)
    f, u, s = head(a, ctrl[0] + V(0, 0.4, 2.2), V(0, -0.05, 1), 2.4, horn_len=0.8, horn_up=0.2)
    # Barbillons lumineux qui pendent du menton, et un « lampion » au bout d'une antenne sur le front
    for sd in (1, -1):
        root = ctrl[0] + V(sd * 0.9, -0.8, 4.4)
        line(a, "Glow", [root, root + V(sd * 1, -2, 0.5), root + V(sd * 1.6, -3.5, -0.8)], [0.15, 0.1, 0.0], 4)
    ant = [ctrl[0] + V(0, 1.4, 2.4), ctrl[0] + V(0, 4.2, 3.5), ctrl[0] + V(0, 4.8, 6)]
    line(a, "Horns", ant, [0.15, 0.1, 0.08], 4)
    a.add("Glow", *blob(ant[-1], Z, Y, X, 0.6, 0.6, 0.6, 6, 3))
    # Nageoires : grande paire à l'avant, petite paire au milieu, crête dorsale continue
    for idx, size in ((2, 5.5), (6, 3.5)):
        p = spine[idx * len(spine) // 12]
        for sd in (1, -1):
            a.add("Fins", *fin(p + V(sd * 1.5, -0.5, 1.2), p + V(sd * 1.5, -0.5, -1.2),
                               p + V(sd * (1.5 + size), -size * 0.5, -size * 0.6), Y, 0.15))
    spikes(a, "Fins", spine[4:-4], Y, 1.6, 0.6, 2)
    # Points lumineux le long des flancs
    for k in range(4, len(spine) - 8, 4):
        p = spine[k]
        for sd in (1, -1):
            a.add("Glow", *blob(p + V(sd * 1.6, -0.3, 0), Z, Y, X, 0.25, 0.25, 0.25, 5, 3))
    # Queue en éventail
    end = ctrl[-1]
    for k, ang in enumerate(np.linspace(-0.9, 0.9, 7)):
        d = normalize(V(np.sin(ang), 0.1, -np.cos(ang)))
        a.add("Fins", *fin(end + Y * 0.3, end - Y * 0.3, end + d * (5 - abs(ang) * 1.5), Y, 0.12))
    return a, "Léviathan des abysses", "dragon marin : nageoires, barbillons et points lumineux, queue en éventail"


def main():
    sketches = [wyverne(), amphiptere(), drake(), hydre(), leviathan()]
    # Planche : les 5 en trois-quarts
    fig = plt.figure(figsize=(25, 11), facecolor=FOND)
    for k, (a, title, desc) in enumerate(sketches):
        ax = fig.add_subplot(2, 5, k + 1, projection="3d")
        render(ax, a, 22, -50, f"{k + 1}. {title}", zoom=1.65)
        ax = fig.add_subplot(2, 5, k + 6, projection="3d")
        render(ax, a, 6, 0, "profil", zoom=1.65)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "croquis-planche.png"), dpi=70, facecolor=FOND)
    plt.close(fig)
    # Une image par dragon (trois-quarts, profil, face, dessus)
    for k, (a, title, desc) in enumerate(sketches):
        fig = plt.figure(figsize=(16, 13), facecolor=FOND)
        for j, (elev, azim, t) in enumerate(((22, -50, "Trois-quarts"), (6, 0, "Profil"), (8, -90, "Face"),
                                              (65, -60, "Dessus"))):
            ax = fig.add_subplot(2, 2, j + 1, projection="3d")
            render(ax, a, elev, azim, t, zoom=1.6)
        fig.suptitle(f"{title} : {desc}", color="white", fontsize=16)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, f"croquis-{k + 1}-{a.name.lower()}.png"), dpi=60, facecolor=FOND)
        plt.close(fig)
        print(title, a.tri_count(), "triangles")


if __name__ == "__main__":
    main()
