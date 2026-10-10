# Wyverne des tempêtes : boss aérien en style électrique, low-poly à facettes, pour Roblox.
# Même principe que le Dragon Long : le modèle est construit par code, une partie par couleur / matériau.
# Repère : Y vers le haut, la tête regarde vers +Z, unités = studs.
# Usage : python wyverne.py   -> ../objets/Wyverne_Tempete_v1.glb et ../apercu-Wyverne_Tempete_v1.png
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "dragon-long", "generateur"))
from meshlib import Asset, catmull_rom, frames, loft, ellipse_ring, tube, blob, fin, gem, normalize  # noqa: E402

VERSION = "v1"
X, Y, Z = np.eye(3)
rng = np.random.default_rng(21)

# Couleurs (sRGB, comme dans Roblox) et matériaux de chaque partie.
PARTS = [
    ("Body", "#1F2C52", "SmoothPlastic"),      # écailles bleu nuit
    ("Belly", "#3B4F86", "SmoothPlastic"),     # plaques du ventre
    ("Plates", "#2E3C68", "SmoothPlastic"),    # plaques blindées du dos, arcades
    ("Membrane", "#25366A", "SmoothPlastic"),  # membranes des ailes
    ("Horns", "#C9D6F0", "SmoothPlastic"),     # cornes, griffes, dents, os des ailes
    ("Bolt", "#6FF2FF", "Neon"),               # éclairs cyan
    ("Bolt2", "#FFF27A", "Neon"),              # éclairs jaunes (cornes, dard)
    ("Eyes", "#B8FBFF", "Neon"),
    ("Mouth", "#3A1030", "SmoothPlastic"),     # intérieur de la gueule
]


def V(*c):
    return np.array(c, float)


def line(a, part, pts, radii, sides=7, flat=1.0, up=Y, samples=None):
    pts = catmull_rom([np.asarray(p, float) for p in pts], samples or max(8, 4 * len(pts)))
    r = np.interp(np.linspace(0, 1, len(pts)), np.linspace(0, 1, len(radii)), radii)
    a.add(part, *tube(pts, r, sides, flat=flat, up=up))
    return pts


def zigzag(a, part, p0, p1, r0, r1, n=5, amp=0.25, normal=None):
    """Éclair : ligne brisée entre p0 et p1. normal : direction à éviter (les zigzags restent à plat sur la peau)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    ref = normal if normal is not None else (Y if abs(normalize(d) @ Y) < 0.9 else X)
    side = normalize(np.cross(d, ref))
    pts = [p0]
    for k in range(1, n):
        pts.append(p0 + d * k / n + side * (1 if k % 2 else -1) * L * amp / n * 2 * rng.uniform(0.6, 1.2))
    pts.append(p1)
    for k, (q0, q1) in enumerate(zip(pts[:-1], pts[1:])):
        r = r0 + (r1 - r0) * k / n
        a.add(part, *tube(np.array([q0, q1]), [r, r * 0.92], 4))
    return pts


def double_sided(a, part, verts, faces, normals, thick=0.12):
    """Surface fine (membrane) : deux faces décalées de l'épaisseur, tournées vers l'extérieur, pour qu'elle se
    voie de partout sans que les deux couches se chevauchent."""
    p = a.parts[part]
    verts = np.asarray(verts)
    for sgn, f in ((1, faces), (-1, faces[:, ::-1])):
        base = len(p["v"])
        p["v"].extend((verts + normals * thick * 0.5 * sgn).tolist())
        p["f"].extend((np.asarray(f) + base).tolist())
        p["g"].extend([a.gid] * len(verts))


def scale_since(a, mark, center, k):
    """Agrandit (facteur k, autour de center) tout ce qui a été ajouté depuis mark = {partie: nb de sommets}."""
    for name, p in a.parts.items():
        v = np.array(p["v"][mark.get(name, 0):])
        if len(v):
            p["v"][mark.get(name, 0):] = ((v - center) * k + center).tolist()


def mark(a):
    return {name: len(p["v"]) for name, p in a.parts.items()}


# ---------------------------------------------------------------- corps
# Colonne, de la pointe de la queue à la base du crâne : (point, rayon).
SPINE = [
    (V(0, 13.0, -50), 0.12), (V(0, 11.5, -42), 0.6), (V(0, 11.0, -33), 1.3), (V(0, 12.0, -24), 2.2),
    (V(0, 14.5, -15), 3.4), (V(0, 17.0, -6), 4.6), (V(0, 19.0, 2), 5.0), (V(0, 21.0, 7), 3.9),
    (V(0, 24.5, 10), 2.8), (V(0, 28.5, 12.5), 2.3), (V(0, 31.5, 14.5), 2.1),
]
SIDES = 12
BELLY_K = {4, 5, 6, 7}          # faces du dessous (anneau à 12 côtés, 0 = flanc droit, sens trigo vers le haut)


def build_body(a):
    ctrl = [p for p, _ in SPINE]
    pts = catmull_rom(ctrl, 90)
    rr = np.interp(np.linspace(0, 1, len(pts)), np.linspace(0, 1, len(SPINE)), [r for _, r in SPINE])
    T, N, B = frames(pts, Y)
    # Anneaux un peu plus larges que hauts, ventre légèrement aplati.
    rings = []
    for p, t, n, b, r in zip(pts, T, N, B, rr):
        ang = np.pi / 2 + np.arange(SIDES) * 2 * np.pi / SIDES + np.pi / SIDES
        ring = [p + b * np.cos(x) * r * 1.08 + n * np.sin(x) * r * (0.95 if np.sin(x) > 0 else 0.82) for x in ang]
        rings.append(np.array(ring))
    verts, faces = loft(rings)
    ring_faces = (len(rings) - 1) * SIDES * 2
    labels = []
    for i in range(len(faces)):
        k = (i // 2) % SIDES if i < ring_faces else -1
        labels.append("Belly" if k in {5, 6} else "Body")
    a.add_split(verts, faces, labels)
    a.spine = (pts, T, N, B, rr)
    return pts, T, N, B, rr


def build_back(a, pts, T, N, B, rr):
    """Plaques blindées sur le dos et crête d'éclairs entre elles ; rayures électriques sur les flancs."""
    n = len(pts)
    for i in range(14, n - 14, 4):
        p, t, nn, r = pts[i], T[i], N[i], rr[i]
        a.add("Plates", *gem(p + nn * r * 0.92, t, nn, B[i], 0.9 + 0.3 * r, 0.25 + 0.08 * r, 0.6 + 0.25 * r))
    for i in range(12, n - 12, 4):
        p, t, nn, r = pts[i + 2], T[i + 2], N[i + 2], rr[i + 2]
        h = 1.2 + 1.1 * r
        base = p + nn * r * 0.95
        zigzag(a, "Bolt", base, base + nn * h - t * h * 0.55, 0.32, 0.06, n=3, amp=0.35, normal=B[i])
    # Rayures : éclairs posés à plat sur les flancs
    for i in range(22, n - 26, 9):
        for sd in (1, -1):
            r0, r1 = rr[i], rr[i + 6]
            q0 = pts[i] + B[i] * sd * r0 * 1.04 + N[i] * r0 * 0.25
            q1 = pts[i + 6] + B[i + 6] * sd * r1 * 1.0 - N[i + 6] * r1 * 0.45
            zigzag(a, "Bolt", q0, q1, 0.16, 0.1, n=4, amp=0.22, normal=B[i] * sd)


def build_tail(a, pts, T, N, B, rr):
    """Anneaux électriques autour de la queue (comme une bobine) et dard foudroyant à trois pointes."""
    for i in (10, 16, 22):
        p, r = pts[i], rr[i] * 1.6 + 0.4
        ring = [p + (B[i] * np.cos(x) + N[i] * np.sin(x)) * r for x in np.linspace(0, 2 * np.pi, 15)]
        a.add("Bolt", *tube(np.array(ring), [0.16] * len(ring), 4, tip=False))
    tip, t, nn, b = pts[0], -T[0], N[0], B[0]
    a.add("Bolt2", *gem(tip + t * 2.2, t, nn, b, 2.6, 0.9, 1.3))
    for k in (-1, 0, 1):
        end = tip + t * 9 + b * k * 3.5 + nn * (1.5 if k == 0 else 0.3)
        zigzag(a, "Bolt2", tip + t * 4.4, end, 0.3, 0.02, n=4, amp=0.25)


# ---------------------------------------------------------------- tête
def build_head(a):
    """Tête en coin, allongée : crâne plat, museau en lance, mâchoire légèrement ouverte, crocs, arcades,
    grande corne frontale, deux cornes vers l'arrière et des cornes-éclairs fourchues."""
    base = SPINE[-1][0]
    f = normalize(V(0, -0.12, 1))              # la tête regarde devant, un peu vers le bas
    u = normalize(Y - f * (Y @ f))
    s = np.cross(u, f)
    c = base + f * 1.2
    a.head_center = c + f * 3

    def section(x, w, h, top=1.0, drop=0.0):
        """Section du crâne à la distance x : hexagone plat dessus, en V dessous."""
        o = c + f * x - u * drop
        return np.array([o + s * w + u * h * 0.2, o + s * w * 0.75 + u * h * top, o - s * w * 0.75 + u * h * top,
                         o - s * w + u * h * 0.2, o - s * w * 0.6 - u * h * 0.55, o + s * w * 0.6 - u * h * 0.55])

    upper = [section(-1.0, 2.2, 1.9), section(0.8, 2.5, 2.1), section(2.6, 2.3, 1.7), section(4.4, 1.7, 1.3, 0.95, 0.1),
             section(6.0, 1.2, 1.0, 0.9, 0.2), section(7.3, 0.6, 0.6, 0.8, 0.3)]
    a.add("Body", *loft(upper))
    # Mâchoire du bas, ouverte de 12°
    ja = 0.21
    jf = normalize(f * np.cos(ja) - u * np.sin(ja))
    ju = np.cross(jf, s)
    hinge = c + f * 0.2 - u * 1.0

    def jsec(x, w, h):
        o = hinge + jf * x
        return np.array([o + s * w + ju * h * 0.35, o - s * w + ju * h * 0.35, o - s * w * 0.6 - ju * h * 0.6,
                         o + s * w * 0.6 - ju * h * 0.6])
    a.add("Belly", *loft([jsec(0, 1.8, 1.4), jsec(2.5, 1.6, 1.1), jsec(5.0, 1.1, 0.8), jsec(6.8, 0.45, 0.4)]))
    # Intérieur sombre de la gueule
    a.add("Mouth", *loft([np.array([hinge + jf * x + s * w * k + ju * 0.4 for k in (1, -1)] +
                                   [c + f * x * 1.02 - u * 0.75 + s * w * k for k in (-1, 1)])
                          for x, w in ((0.5, 1.4), (3.0, 1.2), (5.5, 0.7))]))
    # Crocs : en haut et en bas, plus grands devant
    for k, x in enumerate(np.linspace(1.6, 6.4, 6)):
        w = np.interp(x, [0, 7.3], [2.2, 0.6]) * 0.8
        L = 0.55 + 0.35 * (k in (3, 4))
        for sd in (1, -1):
            top = c + f * x + s * sd * w - u * 0.75
            a.add("Horns", *gem(top - u * L * 0.5, -u, f, s, L, 0.12, 0.12))
            bot = hinge + jf * (x - 0.3) + s * sd * w * 0.9 + ju * 0.35
            a.add("Horns", *gem(bot + ju * L * 0.4, ju, jf, s, L * 0.8, 0.1, 0.1))
    # Arcades sourcilières et yeux enfoncés dessous
    for sd in (1, -1):
        e = c + f * 2.3 + s * sd * 1.95 + u * 0.75
        a.add("Plates", *gem(e + u * 0.55 - f * 0.2, normalize(f - u * 0.15), u, s, 1.9, 0.35, 0.55))
        a.add("Eyes", *gem(e, normalize(f + s * sd * 0.25), u, s, 0.75, 0.28, 0.15))
        # narines
        a.add("Mouth", *gem(c + f * 6.8 + s * sd * 0.45 + u * 0.45, f, u, s, 0.25, 0.1, 0.12))
    # Corne frontale en lance, qui part du museau vers l'arrière
    line(a, "Horns", [c + f * 4.8 + u * 1.2, c + f * 2.0 + u * 2.6, c - f * 1.5 + u * 3.5, c - f * 5.0 + u * 4.8],
         [0.75, 0.6, 0.38, 0.0], 6)
    # Deux cornes balayées vers l'arrière, et une corne-éclair fourchue au-dessus de chacune
    for sd in (1, -1):
        h0 = c - f * 0.6 + s * sd * 1.7 + u * 1.5
        line(a, "Horns", [h0, h0 - f * 3.0 + s * sd * 1.0 + u * 0.8, h0 - f * 6.0 + s * sd * 1.6 + u * 0.3],
             [0.55, 0.38, 0.0], 6)
        b0 = c + f * 0.3 + s * sd * 1.2 + u * 1.9
        pts = zigzag(a, "Bolt2", b0, b0 - f * 4.5 + s * sd * 2.8 + u * 3.8, 0.36, 0.1, n=4, amp=0.28)
        zigzag(a, "Bolt2", pts[2], pts[2] + s * sd * 2.0 + u * 1.8 + f * 0.5, 0.22, 0.03, n=2, amp=0.3)
        # Moustaches électriques qui partent du museau vers l'arrière
        m0 = c + f * 5.4 + s * sd * 1.25 + u * 0.35
        zigzag(a, "Bolt", m0, m0 - f * 6.0 + s * sd * 3.4 - u * 0.6, 0.14, 0.04, n=6, amp=0.2, normal=u)
    # Lueur électrique au fond de la gueule
    a.add("Bolt", *blob(c + f * 1.8 - u * 0.9, f, u, s, 1.4, 0.35, 0.9, 8, 3))


# ---------------------------------------------------------------- pattes
def build_legs(a):
    """Pattes arrière puissantes, digitigrades : cuisse, jambe, métatarse, 3 doigts griffus devant + 1 derrière."""
    for sd in (1, -1):
        hip = V(sd * 3.6, 16.0, -6.5)
        knee = V(sd * 5.2, 10.5, -1.0)
        ankle = V(sd * 5.0, 4.6, -6.0)
        foot = V(sd * 5.0, 1.0, -3.6)
        a.add("Body", *blob((hip + knee) / 2 + V(sd * 0.3, 0.5, 0), normalize(knee - hip), Z, X, 4.0, 2.4, 2.2, 8, 4))
        line(a, "Body", [knee, (knee + ankle) / 2 + V(0, 0, -0.5), ankle], [1.5, 1.1, 0.85], 7)
        line(a, "Body", [ankle, foot], [0.8, 0.7], 7)
        a.add("Plates", *gem(knee + V(sd * 0.6, 0.2, 0.8), normalize(V(0, -0.3, 1)), Y, X, 1.0, 0.8, 0.6))
        for k, ang in enumerate((-0.45, 0, 0.45)):
            d = normalize(V(np.sin(ang) * sd, 0, np.cos(ang)))
            toe = foot + d * 2.6 + V(0, -0.4, 0)
            line(a, "Body", [foot, foot + d * 1.4 + V(0, 0.1, 0), toe], [0.45, 0.38, 0.3], 6)
            a.add("Horns", *gem(toe + d * 0.6 - Y * 0.2, normalize(d - Y * 0.6), Y, np.cross(d, Y), 0.8, 0.18, 0.18))
        a.add("Horns", *gem(foot - Z * 1.3 - Y * 0.3, normalize(-Z - Y * 0.5), Y, X, 0.6, 0.15, 0.15))
        # éclair qui descend le long de la jambe
        zigzag(a, "Bolt", knee + V(sd * 1.5, 0, 0.6), ankle + V(sd * 0.9, 0, 0.5), 0.14, 0.08, n=4, amp=0.2)


# ---------------------------------------------------------------- ailes
SPAN = 40.0


def build_wings(a):
    """Ailes de chauve-souris immenses : bras (épaule, coude, poignet), pouce griffu, 4 doigts ; membrane qui se
    creuse entre les doigts ; bord d'attaque lumineux et nervures en éclairs ramifiés."""
    for sd in (1, -1):
        sh = V(sd * 3.4, 22.0, 3.0)
        el = sh + V(sd * SPAN * 0.32, SPAN * 0.30, -SPAN * 0.06)
        wr = el + V(sd * SPAN * 0.28, SPAN * 0.18, SPAN * 0.10)
        line(a, "Body", [sh, (sh + el) / 2 + V(0, 0.8, 0), el], [1.6, 1.1, 0.9], 7)
        line(a, "Horns", [el, (el + wr) / 2 + V(0, 0.5, 0), wr], [0.8, 0.6, 0.55], 6)
        a.add("Plates", *blob(el, normalize(el - sh), Y, Z, 1.3, 1.0, 1.0, 6, 3))
        # pouce griffu
        th = wr + V(sd * 1.2, 2.2, 1.8)
        line(a, "Horns", [wr, th], [0.4, 0.25], 5)
        a.add("Horns", *gem(th + V(0, -0.2, 0.8), normalize(V(0, -0.3, 1)), Y, X, 0.9, 0.2, 0.2))
        # 4 doigts en éventail, de l'avant (vers l'extérieur) à l'arrière (vers la queue)
        tips = []
        fingers = []
        for k in range(4):
            t = k / 3
            tip = wr + V(sd * SPAN * (0.44 - 0.24 * t), -SPAN * (0.10 + 0.52 * t), -SPAN * (0.22 + 0.28 * t))
            mid = (wr + tip) / 2 + V(sd * 0.6, 1.2, 0)
            fpts = catmull_rom([wr, mid, tip], 12)
            line(a, "Horns", [wr, mid, tip], [0.42, 0.3, 0.0], 5)
            tips.append(tip)
            fingers.append(fpts)
        # dernier « doigt » : le flanc, du poignet jusqu'à la cuisse (la membrane s'y attache)
        root = V(sd * 3.6, 16.5, -8.0)
        fingers.append(catmull_rom([el, (el + root) / 2 + V(0, -1.5, 0), root], 12))
        fingers.insert(0, catmull_rom([sh, el, wr], 12))   # bord d'attaque (bras)
        # Membrane : grille entre deux doigts voisins, creusée vers le bas au milieu
        for fa, fb in zip(fingers[1:-1], fingers[2:]):
            build_membrane(a, fa, fb, sd)
        build_membrane(a, fingers[1], fingers[0], sd, sag=0.3)   # entre le premier doigt et le bras
        build_membrane(a, fingers[-1], fingers[-2], sd)
        # Bord d'attaque lumineux
        line(a, "Bolt", [p + V(0, 0.9, 0.2) for p in (sh, el, wr)], [0.22, 0.22, 0.18], 4)
        # Nervures en éclairs le long des doigts, avec des branches
        for fp in fingers[1:5]:
            a0, a1 = fp[2], fp[-3]
            pts = zigzag(a, "Bolt", a0 + V(0, 0.35, 0), a1 + V(0, 0.35, 0), 0.2, 0.08, n=6, amp=0.12)
            for j in (2, 4):
                br = pts[j] + normalize(np.cross(a1 - a0, Y)) * sd * 3.5 + V(0, 0.2, -1)
                zigzag(a, "Bolt", pts[j], br, 0.12, 0.03, n=3, amp=0.3)


def build_membrane(a, fa, fb, sd, sag=1.0, rows=6):
    """Surface entre deux doigts (mêmes nombres de points) ; le milieu se creuse vers le bas."""
    n = len(fa)
    verts, faces = [], []
    for i in range(n):
        dist = np.linalg.norm(fa[i] - fb[i])
        for j in range(rows + 1):
            t = j / rows
            p = fa[i] * (1 - t) + fb[i] * t - Y * np.sin(np.pi * t) * dist * 0.08 * sag
            verts.append(p)
    for i in range(n - 1):
        for j in range(rows):
            a0 = i * (rows + 1) + j
            b0 = a0 + rows + 1
            faces += [(a0, b0, b0 + 1), (a0, b0 + 1, a0 + 1)]
    # Normale en chaque point de la grille (pour décaler les deux faces de la membrane)
    g = np.array(verts).reshape(n, rows + 1, 3)
    du = np.gradient(g, axis=0)
    dv = np.gradient(g, axis=1)
    nrm = np.cross(du, dv).reshape(-1, 3)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    double_sided(a, "Membrane", np.array(verts), np.array(faces), nrm)


def build():
    a = Asset(f"Wyverne_Tempete_{VERSION}")
    for name, color, mat in PARTS:
        a.part(name, color, mat)
    pts, T, N, B, rr = build_body(a)
    build_back(a, pts, T, N, B, rr)
    build_tail(a, pts, T, N, B, rr)
    m = mark(a)
    build_head(a)
    scale_since(a, m, SPINE[-1][0], 1.3)          # tête de boss : un peu plus grosse
    a.head_center = (np.asarray(a.head_center) - SPINE[-1][0]) * 1.3 + SPINE[-1][0]
    build_legs(a)
    build_wings(a)
    return a


# ---------------------------------------------------------------- export + aperçu
def main():
    import json
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from meshlib import export_glb
    from build import render, FOND

    root = os.path.dirname(HERE)
    out = os.path.join(root, "objets")
    os.makedirs(out, exist_ok=True)
    a = build()
    mn, mx = a.bounds()
    shift = np.array([(mn[0] + mx[0]) / 2, mn[1], (mn[2] + mx[2]) / 2])
    head = np.asarray(a.head_center) - shift
    for p in a.parts.values():
        p["v"] = (np.array(p["v"]) - shift).tolist()
    export_glb(a, os.path.join(out, a.name + ".glb"))
    mn, mx = a.bounds()
    size = [round(float(x), 1) for x in (mx - mn)]
    info = {"name": a.name, "tris": a.tri_count(), "size_studs": size,
            "parts": {k: {"tris": len(p["f"]), "color": p["color"], "material": p["material"]} for k, p in a.parts.items()}}
    with open(os.path.join(out, a.name + ".json"), "w") as fh:
        json.dump(info, fh, indent=2, ensure_ascii=False)

    fig = plt.figure(figsize=(16, 20), facecolor=FOND)
    hv = (head, 9.5)
    views = [(321, 18, -50, "Trois-quarts", None), (322, 6, 0, "Profil gauche", None),
             (323, 8, -90, "Face (ailes ouvertes)", None), (324, 22, -140, "Trois-quarts arrière", None),
             (325, 10, -55, "Tête trois-quarts", hv), (326, 4, 0, "Tête de profil", hv)]
    for pos, e, az, t, foc in views:
        ax = fig.add_subplot(pos, projection="3d")
        render(ax, a, e, az, t, zoom=1.35 if foc is not None else 1.6, focus=foc)
    fig.suptitle(f"{a.name}  ·  {a.tri_count()} triangles  ·  {size[0]} × {size[1]} × {size[2]} studs (L × H × P)",
                 color="white", fontsize=15, y=0.995)
    plt.subplots_adjust(left=0, right=1, bottom=0, top=0.95, wspace=0, hspace=0.05)
    fig.savefig(os.path.join(root, f"apercu-{a.name}.png"), dpi=80, facecolor=FOND)
    plt.close(fig)
    print(a.name, a.tri_count(), "triangles", size)


if __name__ == "__main__":
    main()
