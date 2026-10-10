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

VERSION = "v4"
X, Y, Z = np.eye(3)
rng = np.random.default_rng(21)

# Couleurs (sRGB, comme dans Roblox) et matériaux de chaque partie.
PARTS = [
    ("Body", "#1F2C52", "SmoothPlastic"),      # peau bleu nuit
    ("Scales", "#2A3D72", "SmoothPlastic"),    # écailles en tuiles, un ton plus clair
    ("Belly", "#3B4F86", "SmoothPlastic"),     # plaques du ventre
    ("Plates", "#2E3C68", "SmoothPlastic"),    # plaques blindées du dos, arcades
    ("Membrane", "#2A3E7A", "SmoothPlastic"),  # membranes des ailes
    ("Membrane2", "#16204A", "SmoothPlastic"), # bords sombres de la membrane, le long des doigts
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


def double_sided(a, part, verts, faces, normals, thick=0.12, labels=None):
    """Surface fine (membrane) : deux faces décalées de l'épaisseur, tournées vers l'extérieur, pour qu'elle se
    voie de partout sans que les deux couches se chevauchent. labels : partie de chaque face (sinon part)."""
    verts = np.asarray(verts)
    faces = np.asarray(faces)
    labels = np.array(labels if labels is not None else [part] * len(faces))
    for name in np.unique(labels):
        p = a.parts[name]
        sel = faces[labels == name]
        for sgn, f in ((1, sel), (-1, sel[:, ::-1])):
            base = len(p["v"])
            p["v"].extend((verts + normals * thick * 0.5 * sgn).tolist())
            p["f"].extend((f + base).tolist())
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
    global SPINE_DATA
    SPINE_DATA = (pts, T, N, B, rr)
    return pts, T, N, B, rr


def surface(x, ang, k=1.0):
    """Point de la peau du corps à l'anneau x (décimal) et à l'angle ang (pi/2 = dos, 3pi/2 = ventre) :
    point, normale vers l'extérieur, tangente (vers la tête), rayon. Même forme que les anneaux de build_body."""
    pts, T, N, B, rr = SPINE_DATA
    i = int(np.clip(np.floor(x), 0, len(pts) - 2))
    w = x - i
    p = pts[i] * (1 - w) + pts[i + 1] * w
    t = normalize(T[i] * (1 - w) + T[i + 1] * w)
    n = normalize(N[i] * (1 - w) + N[i + 1] * w)
    b = normalize(B[i] * (1 - w) + B[i + 1] * w)
    r = rr[i] * (1 - w) + rr[i + 1] * w
    ky = 0.95 if np.sin(ang) > 0 else 0.82
    q = p + (b * np.cos(ang) * 1.08 + n * np.sin(ang) * ky) * r * k
    o = normalize(b * np.cos(ang) * ky + n * np.sin(ang) * 1.08)
    return q, o, t, r


def build_scales(a, pts, rr):
    """Écailles en tuiles sur le dos et les flancs, en quinconce : bouclier à 5 côtés, pointe tournée vers la
    queue, bord avant enfoncé sous l'écaille précédente. Elles grossissent avec le corps et s'affinent sur
    la queue et le cou ; deux tons qui alternent par rangée."""
    n = len(pts)
    spacing = np.linalg.norm(pts[1] - pts[0])
    for row in range(4, n - 5):
        r = rr[row]
        cols = int(np.clip(round(r * 3.2), 5, 15))          # plus de colonnes là où le corps est épais
        step = 3.6 / cols                                  # couvre ±1,8 rad autour du dos (jusqu'au ventre)
        offs = [(j - (cols - 1) / 2 + (0.5 if row % 2 else 0)) * step for j in range(cols)]
        part = "Scales" if (row // 2) % 2 else "Body"
        for d in offs:
            if abs(d) > 1.85:
                continue
            c, o, t, r = surface(row + 0.5, np.pi / 2 + d, 0.98)
            t = -t                                         # vers la queue
            x = normalize(np.cross(o, t))
            L, W = spacing * 1.8, r * step * 1.2
            base = []
            for k in range(5):
                ang = 2 * np.pi * k / 5                    # k = 0 : pointe arrière
                ca, sa = np.cos(ang), np.sin(ang)
                lift = (0.04 + 0.03 * r) * max(0.0, ca) - (0.06 + 0.04 * r) * max(0.0, -ca)
                base.append(c + t * ca * L * (0.6 if ca > 0 else 0.45) + x * sa * W / 2 + o * lift)
            apex = c + t * L * 0.15 + o * (0.06 + 0.04 * r)
            a.add(part, base + [apex], [(k, (k + 1) % 5, 5) for k in range(5)] + [(0, 2, 1), (0, 3, 2), (0, 4, 3)])


def build_belly_plates(a, pts, rr):
    """Plaques du ventre en bandes transversales, bord avant bombé qui redescend vers l'arrière."""
    angs = np.linspace(3 * np.pi / 2 - 0.62, 3 * np.pi / 2 + 0.62, 6)
    for i in range(6, len(pts) - 8, 2):
        sections = []
        for sfrac, lift in ((0.0, 0.03), (0.6, 0.2), (1.85, 0.0)):
            outer = []
            for ang in angs:
                q, o, t, r = surface(i + sfrac, ang, 1.0)
                outer.append(q + o * lift * (0.5 + 0.25 * r))
            inner = [surface(i + sfrac, ang, 0.85)[0] for ang in (angs[-1], angs[0])]
            sections.append(np.array(outer + inner))
        a.add("Belly", *loft(sections))


def build_back(a, pts, T, N, B, rr):
    """Plaques blindées sur le dos et crête d'éclairs entre elles ; rayures électriques sur les flancs."""
    n = len(pts)
    for i in range(14, n - 14, 4):
        p, t, nn, r = pts[i], T[i], N[i], rr[i]
        a.add("Plates", *gem(p + nn * r * 0.92, t, nn, B[i], 0.9 + 0.3 * r, 0.25 + 0.08 * r, 0.6 + 0.25 * r))
    for i in range(12, n - 12, 4):
        p, t, nn, r = pts[i + 2], T[i + 2], N[i + 2], rr[i + 2]
        h = 1.2 + 1.1 * r
        base = p + nn * r * 1.05
        zigzag(a, "Bolt", base, base + nn * h - t * h * 0.55, 0.32, 0.06, n=3, amp=0.35, normal=B[i])
    # Rayures : éclairs posés à plat sur les flancs
    for i in range(22, n - 26, 9):
        for sd in (1, -1):
            r0, r1 = rr[i], rr[i + 6]
            q0 = surface(i, np.pi / 2 - sd * 1.25, 1.12)[0]
            q1 = surface(i + 6, np.pi / 2 - sd * 1.75, 1.12)[0]
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
def build_head(a, base, f):
    """Tête en coin, allongée : crâne plat, museau en lance, mâchoire légèrement ouverte, crocs, arcades,
    grande corne frontale, deux cornes vers l'arrière et des cornes-éclairs fourchues.
    base : base du crâne (bout du cou), f : direction du regard."""
    f = normalize(f)
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


# Hydre : deux cous de plus, qui partent du poitrail de chaque côté du cou principal et s'écartent.
SIDE_NECKS = [
    # (points du cou, du poitrail vers la tête), direction du regard. Le premier point est dans le buste.
    ([V(2.8, 20.5, 5.5), V(6.0, 24.0, 7.5), V(9.0, 27.5, 9.5), V(11.0, 29.0, 12.5)], V(0.38, -0.15, 1)),
]
CHEST = V(0, 20.5, 5.5)          # centre du buste élargi d'où sortent les trois cous


def build_chest(a):
    """Buste élargi (une large épaule de chaque côté du cou principal) : les trois cous en sortent comme d'un
    même tronc. Couvert d'écailles en tuiles, plaques du poitrail dessous, muscles à la base de chaque cou."""
    rf, ru, rs = 5.2, 4.4, 7.6
    a.add("Body", *blob(CHEST, Z, Y, X, rf, ru, rs, 14, 7))
    # écailles en tuiles sur le dessus et les côtés de l'ellipsoïde, en quinconce
    for row, el in enumerate(np.linspace(-0.25, 1.25, 9)):
        nb = max(4, int(round(16 * np.cos(el) + 4)))
        for j in range(nb):
            az = (j + 0.5 * (row % 2)) / nb * 2 * np.pi
            d = V(np.cos(el) * np.sin(az), np.sin(el), np.cos(el) * np.cos(az))
            c = CHEST + V(d[0] * rs, d[1] * ru, d[2] * rf)
            o = normalize(V(d[0] / rs, d[1] / ru, d[2] / rf))
            if o[2] > 0.75:                                   # devant : laissé aux plaques du poitrail
                continue
            t = normalize(np.cross(o, normalize(np.cross(V(0, 0, -1), o)) if abs(o[2]) < 0.99 else X))
            t = normalize(V(0, -0.3, -1) - o * (V(0, -0.3, -1) @ o))   # pointe vers l'arrière et le bas
            x = normalize(np.cross(o, t))
            L, W = 1.7, 1.5
            base = [c + t * np.cos(2 * np.pi * k / 5) * L * (0.6 if np.cos(2 * np.pi * k / 5) > 0 else 0.45)
                    + x * np.sin(2 * np.pi * k / 5) * W / 2 - o * 0.08 * (np.cos(2 * np.pi * k / 5) < 0)
                    for k in range(5)]
            a.add("Scales" if row % 2 else "Body", base + [c + o * 0.18],
                  [(k, (k + 1) % 5, 5) for k in range(5)] + [(0, 2, 1), (0, 3, 2), (0, 4, 3)])
    # plaques du poitrail, en bandes horizontales sous les cous
    for k in range(5):
        y = CHEST[1] - 2.8 + k * 1.3
        w = rs * 0.75 * np.sqrt(max(0.1, 1 - ((y - CHEST[1]) / ru) ** 2))
        a.add("Belly", *gem(V(0, y, CHEST[2] + rf * 0.86 * np.sqrt(max(0.1, 1 - ((y - CHEST[1]) / ru) ** 2))),
                            Z, Y, X, 0.5, 0.55, w))
    # muscles à la base des cous de côté
    for sd in (1, -1):
        a.add("Body", *blob(V(sd * 4.4, 22.5, 6.8), normalize(V(sd * 0.6, 0.6, 0.4)), Y, Z, 3.2, 2.6, 2.4, 8, 4))
SIDE_NECKS.append(([p * V(-1, 1, 1) for p in SIDE_NECKS[0][0]], SIDE_NECKS[0][1] * V(-1, 1, 1)))


def build_side_neck(a, ctrl):
    """Cou d'une tête d'hydre : écailles en tuiles sur le dessus, plaques de ventre dessous, crête d'éclairs."""
    pts = catmull_rom(ctrl, 40)
    rr = np.interp(np.linspace(0, 1, len(pts)), [0, 0.25, 1], [3.4, 2.5, 1.9])
    T, N, B = frames(pts, Y)
    rings = [np.array([p + (b * np.cos(x) * 1.05 + n * np.sin(x) * 0.95) * r
                       for x in np.pi / 2 + np.arange(10) * 2 * np.pi / 10]) for p, n, b, r in zip(pts, N, B, rr)]
    v, f = loft(rings)
    a.add("Body", v, f)
    for i in range(3, len(pts) - 2):
        t, n, b, r = T[i], N[i], B[i], rr[i]
        # écailles sur le dessus et les côtés
        for d in np.linspace(-1.6, 1.6, 7) + (0.23 if i % 2 else 0):
            o = normalize(n * np.sin(np.pi / 2 + d) + b * np.cos(np.pi / 2 + d))
            c = pts[i] + o * r * 0.99
            x = normalize(np.cross(o, -t))
            L, W = 1.5, r * 0.55
            base = [c - t * np.cos(2 * np.pi * k / 5) * L * 0.55 + x * np.sin(2 * np.pi * k / 5) * W / 2
                    - o * 0.06 * (np.cos(2 * np.pi * k / 5) < 0) for k in range(5)]
            a.add("Scales" if (i // 2) % 2 else "Body", base + [c + o * 0.12],
                  [(k, (k + 1) % 5, 5) for k in range(5)] + [(0, 2, 1), (0, 3, 2), (0, 4, 3)])
        if i % 2 == 0:                                       # plaques de ventre
            a.add("Belly", *gem(pts[i] - n * r * 0.85, t, n, b, 0.9, 0.3, r * 0.75))
        if i % 6 == 1:                                       # crête d'éclairs
            q = pts[i] + n * r * 1.05
            zigzag(a, "Bolt", q, q + n * 2.2 - t * 1.3, 0.26, 0.05, n=3, amp=0.35, normal=b)
    return pts[-1]


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


def at(curve, u):
    """Point à la fraction u (0 à 1) d'une courbe échantillonnée."""
    x = u * (len(curve) - 1)
    k = int(min(np.floor(x), len(curve) - 2))
    w = x - k
    return curve[k] * (1 - w) + curve[k + 1] * w


def finger(a, wr, tip, sd, r0):
    """Doigt d'aile : trois phalanges qui s'affinent, articulations renflées, griffe crochue au bout."""
    mid = (wr + tip) / 2 + V(sd * 0.6, 1.2, 0)
    pts = catmull_rom([wr, mid, tip], 24)
    rad = np.interp(np.linspace(0, 1, len(pts)), [0, 0.33, 0.66, 1], [r0, r0 * 0.72, r0 * 0.5, r0 * 0.28])
    a.add("Horns", *tube(pts, rad, 6, tip=False))
    for u in (0.33, 0.66):                                   # articulations
        q = at(pts, u)
        a.add("Horns", *blob(q, normalize(at(pts, u + 0.02) - q), Y, X, r0 * 0.7, r0 * 0.75, r0 * 0.75, 6, 3))
    d = normalize(pts[-1] - pts[-3])
    hook = normalize(d - Y * 0.8)
    a.add("Horns", *gem(pts[-1] + hook * 0.6, hook, Y if abs(hook @ Y) < 0.9 else Z, X, 0.9, 0.18, 0.2))
    return pts


# Deux paires d'ailes : la grande devant (aux épaules) et une plus petite au milieu du dos, plus basse et
# balayée vers l'arrière, pour que les deux ne se croisent pas.
# (épaule, envergure, montée, recul, attache arrière de la membrane sur le flanc, attache avant ou None)
WINGS = [
    (V(4.0, 23.0, 2.0), 40.0, 1.0, 0.0, V(4.2, 19.5, -6.5), V(4.2, 24.0, 3.0)),
    (V(3.8, 19.5, -10.0), 28.0, 0.55, 0.16, V(3.6, 15.0, -19.0), V(4.2, 19.8, -6.0)),
]


def build_wings(a):
    for sh, S, rise, back, root, front in WINGS:
        for sd in (1, -1):
            m = V(sd, 1, 1)
            build_wing(a, sd, sh * m, S, rise, back, root * m, front * m if front is not None else None)


def build_wing(a, sd, sh, S, rise, back, root, front):
    """Aile de chauve-souris :
    - bras épais (épaule, coude, poignet) avec plaques et épines, pouce griffu ;
    - 4 doigts à phalanges, articulations et griffes ;
    - membrane avant, membrane entre les doigts au bord festonné, membrane du flanc ;
    - membrane en deux tons (plus sombre le long des os), bord d'attaque lumineux, nervures en éclairs.
    rise < 1 : aile plus basse ; back : aile balayée vers l'arrière."""
    k_ = S / 40.0                                             # épaisseur des os selon la taille de l'aile
    el = sh + V(sd * S * 0.32, S * 0.30 * rise, -S * 0.06 - S * back)
    wr = el + V(sd * S * 0.28, S * 0.18 * rise, S * 0.10 - S * back)
    # Bras : épaule musclée, avant-bras en os, plaques blindées et épines au coude et au poignet
    a.add("Body", *blob(sh + V(sd * 2.0, 1.0, 0) * k_, normalize(el - sh), Y, Z, 3.6 * k_, 2.2 * k_, 2.0 * k_, 8, 4))
    line(a, "Body", [sh, (sh + el) / 2 + V(0, 0.8, 0), el], [1.8 * k_, 1.3 * k_, 1.0 * k_], 8)
    line(a, "Horns", [el, (el + wr) / 2 + V(0, 0.5, 0), wr], [0.9 * k_, 0.7 * k_, 0.6 * k_], 6)
    a.add("Plates", *blob(el, normalize(el - sh), Y, Z, 1.5 * k_, 1.2 * k_, 1.2 * k_, 6, 3))
    a.add("Plates", *blob(wr, normalize(wr - el), Y, Z, 1.0 * k_, 0.9 * k_, 0.9 * k_, 6, 3))
    for k in range(3):                                       # plaques le long du haut du bras
        q = sh + (el - sh) * (0.3 + 0.25 * k) + V(0, 1.3 * k_, 0)
        a.add("Plates", *gem(q, normalize(el - sh), Y, Z, 1.6 * k_, 0.4 * k_, 0.9 * k_))
    a.add("Horns", *gem(el + V(0, 0.2, -1.8 * k_), normalize(V(0, 0.2, -1)), Y, X, 2.2 * k_, 0.3, 0.3))
    a.add("Horns", *gem(wr + V(sd * 0.3, 1.0, -1.2) * k_, normalize(V(sd * 0.2, 0.6, -1)), Y, X, 1.2 * k_, 0.2, 0.2))
    # Pouce griffu
    th = wr + V(sd * 1.2, 2.4, 2.0) * k_
    line(a, "Horns", [wr, (wr + th) / 2 + V(0, 0.4, 0) * k_, th], [0.5 * k_, 0.4 * k_, 0.3 * k_], 5)
    a.add("Horns", *gem(th + V(0, -0.3, 0.9) * k_, normalize(V(0, -0.5, 1)), Y, X, 1.1 * k_, 0.22, 0.24))
    # 4 doigts en éventail, de l'avant (vers l'extérieur) à l'arrière (vers la queue)
    fingers = []
    for k in range(4):
        t = k / 3
        # Doigts en éventail régulier : l'aile reste une seule grande surface, peu plongeante.
        tip = wr + V(sd * S * (0.46 - 0.30 * t), -S * (0.06 + 0.36 * t) * (0.6 + 0.4 * rise),
                     -S * (0.18 + 0.36 * t) - S * back * 0.5)
        fingers.append(finger(a, wr, tip, sd, (0.62 - 0.08 * k) * max(0.75, k_)))
    arm = catmull_rom([wr, el, sh], 24)                      # bras, du poignet vers l'épaule
    flank = catmull_rom([wr, (wr + root) / 2 + V(sd * 2, -3.0, -2.0) * k_, root], 24)   # flanc : poignet -> corps
    for fa, fb in zip(fingers[:-1], fingers[1:]):
        build_membrane(a, fa, fb, scallop=0.12)
    build_membrane(a, fingers[-1], flank, scallop=0.08)
    build_membrane(a, arm, fingers[0], scallop=0.0, sag=0.25)   # entre le bras et le premier doigt
    if front is not None:                                        # membrane avant : du corps au poignet
        fr = catmull_rom([wr, (wr + sh) / 2 + V(0, -1.0, 1.5) * k_, front], 24)
        build_membrane(a, arm, fr, scallop=0.0, sag=0.2, rows=4)
    # Bord d'attaque lumineux
    line(a, "Bolt", [p + V(0, 1.0, 0.3) * k_ for p in (sh, el, wr)], [0.24, 0.24, 0.2], 4)
    # Nervures en éclairs entre les doigts, avec des branches
    for fa, fb in zip(fingers[:-1], fingers[1:]):
        a0, a1 = at(fa, 0.15) * 0.5 + at(fb, 0.15) * 0.5, at(fa, 0.7) * 0.5 + at(fb, 0.7) * 0.5
        pts = zigzag(a, "Bolt", a0 + V(0, 0.3, 0), a1 + V(0, 0.3, 0), 0.2, 0.06, n=6, amp=0.1)
        for jj in (2, 4):
            br = at(fa, 0.15 + jj * 0.1) * 0.7 + at(fb, 0.15 + jj * 0.1) * 0.3 + V(0, 0.3, 0)
            zigzag(a, "Bolt", pts[jj], br, 0.12, 0.03, n=3, amp=0.25)


def build_membrane(a, fa, fb, sag=1.0, rows=7, scallop=0.0):
    """Surface entre deux courbes partant du même point (le poignet). Le milieu se creuse vers le bas ; avec
    scallop, le bord libre se creuse vers le poignet entre les deux doigts (bord festonné). Plus sombre le
    long des os."""
    n = len(fa)
    verts = []
    for i in range(n):
        u = i / (n - 1)
        for j in range(rows + 1):
            t = j / rows
            uu = u * (1 - scallop * np.sin(np.pi * t) * u ** 2)
            pa, pb = at(fa, uu), at(fb, uu)
            dist = np.linalg.norm(pa - pb)
            verts.append(pa * (1 - t) + pb * t - Y * np.sin(np.pi * t) * dist * 0.08 * sag)
    faces, labels = [], []
    for i in range(n - 1):
        for j in range(rows):
            a0 = i * (rows + 1) + j
            b0 = a0 + rows + 1
            faces += [(a0, b0, b0 + 1), (a0, b0 + 1, a0 + 1)]
            edge = j == 0 or j == rows - 1 or i >= n - 3
            labels += ["Membrane2" if edge else "Membrane"] * 2
    g = np.array(verts).reshape(n, rows + 1, 3)
    nrm = np.cross(np.gradient(g, axis=0), np.gradient(g, axis=1)).reshape(-1, 3)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    double_sided(a, "Membrane", np.array(verts), np.array(faces), nrm, labels=labels)


def build():
    a = Asset(f"Wyverne_Tempete_{VERSION}")
    for name, color, mat in PARTS:
        a.part(name, color, mat)
    pts, T, N, B, rr = build_body(a)
    build_scales(a, pts, rr)
    build_belly_plates(a, pts, rr)
    build_chest(a)
    build_back(a, pts, T, N, B, rr)
    build_tail(a, pts, T, N, B, rr)
    # Trois têtes (hydre) : celle du milieu, plus grosse, et deux sur les cous de côté.
    m = mark(a)
    build_head(a, SPINE[-1][0], V(0, -0.12, 1))
    scale_since(a, m, SPINE[-1][0], 1.3)          # tête de boss : un peu plus grosse
    center = (np.asarray(a.head_center) - SPINE[-1][0]) * 1.3 + SPINE[-1][0]
    for ctrl, look in SIDE_NECKS:
        end = build_side_neck(a, ctrl)
        m = mark(a)
        build_head(a, end, look)
        scale_since(a, m, end, 1.15)
    a.head_center = center
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
