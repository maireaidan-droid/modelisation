# Dragon Long (dragon chinois) stylisé, low-poly.
# v1 : premier croquis. v2 : écailles en relief sur le dos, plaques sur le ventre, crête plus fournie, yeux retravaillés.
# v3 : tête plus grande et sculptée (nez de félin, sourcils dorés en volutes, barbichette, joues, rides du museau).
# v14 : peau du visage en écailles couchées (plaques presque à plat, bord arrière à peine soulevé) au lieu de pointes.
# v13 : mâchoire du bas un peu affinée ; peau du visage : écailles-tuiles graduées sur le front et le chanfrein qui
#       se changent en galets (peau granuleuse) sur les joues et autour des yeux, truffe et lèvres lisses avec
#       quelques pores, plis profonds, rangée de petites pointes le long des joues.
# v12 : mâchoire du bas avec du volume (plus profonde, menton arrondi, joues musclées vers l'articulation).
# v11 : mâchoire supérieure affinée en hauteur (dessus du museau −38 %, dessous remonté de 22 %).
# v10 : museau affiné (−26 % en largeur, −20 % en hauteur par le dessus), à partir de l'arrière des yeux.
# v9 : intérieur de la gueule (gorge, palais à bourrelets, langue fendue) et dentition acérée.
# v8 : nez agressif : arête tranchante sur le museau, corne de nez, narines en fentes inclinées comme le V
#      des arcades avec ailes évasées, rides en chevrons, bout du museau plus crochu.
# v7 : nez de la v4 (museau, coussinets, narines en virgule, rides du museau) + zone des yeux de la v6.
# v6 : zone des yeux (arcades en V froncé, pli entre les arcades, yeux mi-clos, poches à 2 plis, pommettes,
#      écailles du front) ; narines creusées vers l'intérieur.
# v5 : nouveau nez (seul changement) : truffe large en 2 lobes, sillon, grosses narines à bourrelet, coussinets
#      de lèvre, chanfrein court à plis et petites écailles.
# v4 : nez fondu dans le crâne (truffe, coussinets et sillon sculptés dans la même peau), yeux enfoncés dans des orbites.
# Corps de serpent en S, ventre doré, crinière et nageoires rouges, cornes en bois de cerf,
# moustaches, 4 pattes à 3 griffes. Repère Roblox : Y en haut, 1 unité = 1 stud, la tête regarde vers +Z.
import numpy as np
from meshlib import Asset, catmull_rom, frames, loft, ellipse_ring, tube, fin, gem, blob, normalize

COULEURS = {
    "Body": ("#2F7D63", "SmoothPlastic"),      # écailles jade
    "Belly": ("#E2B65C", "SmoothPlastic"),     # ventre doré
    "Fins": ("#C8432F", "SmoothPlastic"),      # crinière, nageoires, épines du dos
    "Horns": ("#E6DCC3", "SmoothPlastic"),     # cornes, griffes, dents
    "Whiskers": ("#F0C24B", "SmoothPlastic"),  # moustaches
    "Eyes": ("#FFD23F", "Neon"),               # yeux qui brillent
    "Pupils": ("#17120E", "SmoothPlastic"),    # pupilles fendues, narines
    "Mouth": ("#3A1013", "SmoothPlastic"),     # intérieur de la gueule, palais
    "Tongue": ("#B9434C", "SmoothPlastic"),    # langue
}

SIDES = 8          # côtés du corps (8 = bien facetté, léger pour téléphone)
RINGS = 72         # anneaux le long du corps

# Ligne du dos, de la nuque (index 0) au bout de la queue : un S qui ondule dans l'espace.
SPINE = [
    (0.0, 15.0, 2.0),
    (0.0, 12.5, -2.5),
    (2.5, 8.5, -7.0),
    (5.0, 6.5, -13.0),
    (3.0, 8.5, -19.0),
    (-2.5, 11.0, -24.0),
    (-5.0, 8.5, -30.0),
    (-2.5, 4.5, -35.0),
    (2.0, 3.5, -40.0),
    (4.0, 5.5, -44.0),
    (3.0, 8.0, -46.5),
]


def body_radius(t):
    """Fin au cou, épais au premier tiers, puis s'affine jusqu'à la queue."""
    if t < 0.2:
        return 1.35 + (1.85 - 1.35) * (t / 0.2)
    return 1.85 - (1.85 - 0.28) * ((t - 0.2) / 0.8) ** 1.1


def build_body(a, pts, T, N, B, radii):
    # Anneaux octogonaux : 3 faces tournées vers le bas forment le ventre doré.
    angle0 = np.pi / 2 + np.pi / SIDES
    rings = [ellipse_ring(p, b, n, r * 1.05, r * 0.95, SIDES, angle0) for p, n, b, r in zip(pts, N, B, radii)]
    verts, faces = loft(rings)
    belly_k = {2, 3, 4}
    ring_faces = (len(rings) - 1) * SIDES * 2
    body_f, belly_f = [], []
    for i, f in enumerate(faces):
        k = (i // 2) % SIDES if i < ring_faces else -1
        (belly_f if k in belly_k else body_f).append(f)
    # On ajoute le corps entier (fermé) en une fois pour l'orientation, puis on répartit les faces.
    tmp = Asset("tmp")
    tmp.part("x", "#000")
    tmp.add("x", verts, faces)
    flipped = not np.array_equal(np.array(tmp.parts["x"]["f"]), faces)
    for name, fl in (("Body", body_f), ("Belly", belly_f)):
        fl = np.array(fl)
        if flipped:
            fl = fl[:, ::-1]
        p = a.parts[name]
        base = len(p["v"])
        p["v"].extend(verts.tolist())
        p["f"].extend((fl + base).tolist())


def surface(pts, T, N, B, radii, x, ang, k=1.0):
    """Point sur la peau du corps à l'anneau x (décimal) et à l'angle ang (pi/2 = dessus, 3pi/2 = ventre).
    Renvoie le point, la normale vers l'extérieur, la tangente (vers la queue) et le rayon."""
    i = int(np.clip(np.floor(x), 0, RINGS - 2))
    w = x - i
    p = pts[i] * (1 - w) + pts[i + 1] * w
    t = normalize(T[i] * (1 - w) + T[i + 1] * w)
    n = normalize(N[i] * (1 - w) + N[i + 1] * w)
    b = normalize(B[i] * (1 - w) + B[i + 1] * w)
    r = radii[i] * (1 - w) + radii[i + 1] * w
    o = normalize(np.cos(ang) * b * 0.95 + np.sin(ang) * n * 1.05)
    return p + (np.cos(ang) * b * 1.05 + np.sin(ang) * n * 0.95) * r * k, o, t, r


def build_scales(a, pts, T, N, B, radii):
    # Écailles en losange, en quinconce, la pointe relevée vers la queue (comme des tuiles qui se chevauchent).
    step = 2 * np.pi / 10
    spacing = np.linalg.norm(pts[1] - pts[0])
    for row in range(3, RINGS - 4):
        offs = [j * step for j in range(-3, 4)] if row % 2 == 0 else [(j + 0.5) * step for j in range(-3, 3)]
        for d in offs:
            c, o, t, r = surface(pts, T, N, B, radii, row + 0.5, np.pi / 2 + d, 0.97)
            x = normalize(np.cross(o, t))
            L, W, H = spacing * 1.7, r * step * 1.2, 0.1 + 0.07 * r
            sink = -o * 0.1 * r
            front, back = c - t * L * 0.45 + sink, c + t * L * 0.55 + sink
            left, right = c - x * W / 2 + sink, c + x * W / 2 + sink
            apex = c + t * L * 0.3 + o * H
            verts = [front, right, back, left, apex]
            faces = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2), (0, 2, 1)]
            a.add("Body", verts, faces)


def build_belly_plates(a, pts, T, N, B, radii):
    # Plaques du ventre en bandes, comme sur la référence : bord avant bombé, qui redescend vers l'arrière.
    angs = np.linspace(9 * np.pi / 8 + 0.08, 15 * np.pi / 8 - 0.08, 5)
    for i in range(1, RINGS - 3):
        sections = []
        for sfrac, lift in ((0.06, 0.03), (0.35, 0.17), (0.94, 0.0)):
            outer = []
            for ang in angs:
                p, o, t, r = surface(pts, T, N, B, radii, i + sfrac, ang, 1.0)
                outer.append(p + o * lift * (0.5 + 0.5 * r / 1.85))
            inner = [surface(pts, T, N, B, radii, i + sfrac, ang, 0.82)[0] for ang in (angs[-1], angs[0])]
            sections.append(np.array(outer + inner))
        a.add("Belly", *loft(sections))


def build_spines(a, pts, T, N, B, radii):
    # Crête du dos en triangles, couchés vers l'arrière : grand / petit / moyen, penchés un peu à gauche puis à droite.
    sizes = (1.3, 0.75, 1.0, 0.8)
    for j, i in enumerate(range(4, RINGS - 4, 2)):
        r = radii[i]
        base_a = pts[i] + N[i] * r * 0.85
        base_b = pts[i + 3] + N[i + 3] * radii[i + 3] * 0.85
        h = (0.6 + 0.55 * r) * sizes[j % 4]
        lean = B[i + 1] * (0.12 if j % 2 else -0.12) * h
        tip = (base_a + base_b) / 2 + N[i + 1] * h + T[i + 1] * h * 0.95 + lean
        a.add("Fins", *fin(base_a, base_b, tip, B[i + 1], 0.14))
    # Franges sur les côtés de la queue.
    for i in range(int(RINGS * 0.55), RINGS - 3, 5):
        for s in (1, -1):
            r = radii[i]
            base_a = pts[i] + B[i] * s * r * 0.8
            base_b = pts[i + 2] + B[i + 2] * s * radii[i + 2] * 0.8
            tip = (base_a + base_b) / 2 + B[i + 1] * s * (0.9 + r * 0.6) + T[i + 1] * 1.2 - N[i + 1] * 0.2
            a.add("Fins", *fin(base_a, base_b, tip, N[i + 1], 0.12))
    # Nageoire de queue en forme de flamme.
    end, t_end, n_end, b_end = pts[-1], T[-1], N[-1], B[-1]
    for k, ang in enumerate(np.linspace(-1.2, 1.2, 6)):
        d = normalize(t_end * np.cos(ang) + n_end * np.sin(ang))
        length = 3.4 - abs(ang) * 0.9
        base_a = end - t_end * 0.9 + n_end * 0.15 * np.sin(ang)
        base_b = end + d * 0.3
        tip = end + d * length + t_end * 0.4
        a.add("Fins", *fin(base_a, base_b, tip, b_end, 0.12))


def build_leg(a, hip, fwd, down, side):
    knee = hip + side * 1.9 - down * 0.4 + fwd * 0.6
    ankle = knee + down * 2.0 + fwd * 1.0 + side * 0.2
    foot = ankle + down * 0.5 + fwd * 0.5
    a.add("Body", *tube([hip, knee, ankle, foot], [0.75, 0.55, 0.42, 0.4], 6, tip=False))
    # Petite nageoire au coude.
    a.add("Fins", *fin(knee - fwd * 0.2 + down * 0.3, knee + fwd * 0.5, knee - fwd * 1.6 - down * 0.6 + side * 0.4,
                       np.cross(fwd, side), 0.1))
    # 3 griffes vers l'avant + 1 ergot à l'arrière.
    for ang in (-0.6, 0.0, 0.6):
        d = normalize(fwd * np.cos(ang) + side * np.sin(ang))
        pts = [foot, foot + d * 0.7, foot + d * 1.25 + down * 0.35, foot + d * 1.45 + down * 0.85]
        a.add("Horns", *tube(pts, [0.24, 0.2, 0.12, 0.0], 5))
    pts = [foot, foot - fwd * 0.6, foot - fwd * 0.85 + down * 0.5]
    a.add("Horns", *tube(pts, [0.18, 0.12, 0.0], 5))


def build_legs(a, pts, T, N, B, radii):
    for t in (0.2, 0.6):
        i = int(t * (RINGS - 1))
        fwd = -T[i]                        # la tête est vers les t petits
        fwd = normalize(fwd - np.dot(fwd, (0, 1, 0)) * np.array([0, 1, 0]) * 0.5)
        down = np.array([0.0, -1.0, 0.0])
        for s in (1, -1):
            side = normalize(B[i] * s - np.dot(B[i] * s, down) * down)
            hip = pts[i] + B[i] * s * radii[i] * 0.6 - N[i] * radii[i] * 0.35
            build_leg(a, hip, fwd, down, side)


def build_eye(a, P, f, u, side_v, S):
    """Œil en amande étroit, enfoncé, mi-clos sous une paupière lourde ; poche à 2 plis dessous."""
    sd = 1 if side_v @ np.cross(u, f) > 0 else -1
    ex, ey = EYE
    c = P(ex, ey, (skull_side(ex, ey) + 0.03) * sd)              # au fond de l'orbite
    out = normalize(side_v + f * 0.8 + u * 0.1)               # tourné vers l'avant : visible de face
    e1 = normalize(f - out * (f @ out) - u * 0.2)             # grand axe, coin arrière relevé
    e2 = normalize(np.cross(out, e1))
    if e2 @ u < 0:
        e2 = -e2
    L, Hh, D = 0.6 * S, 0.24 * S, 0.19 * S

    # Amande étroite.
    rings = [c - e1 * L]
    for x, k in ((-0.55, 0.75), (0.0, 1.0), (0.55, 0.75)):
        ang = np.arange(8) * np.pi / 4
        rings.append(np.array([c + e1 * L * x + e2 * np.sin(t) * Hh * k + out * np.cos(t) * D * k for t in ang]))
    rings.append(c + e1 * L)
    a.add("Eyes", *loft(rings))

    # Pupille fendue, verticale.
    a.add("Pupils", *gem(c + out * D * 0.95 + e1 * L * 0.05, e1, e2, out, 0.07 * S, Hh * 0.9, 0.06 * S))

    # Paupière du haut lourde : couvre la moitié de l'œil (regard mi-clos), plus basse côté nez (air colérique).
    lid = [c + e1 * L * x + e2 * Hh * (0.75 - 0.35 * max(0.0, x)) + out * D * (0.45 + 0.45 * (1 - abs(x)))
           for x in np.linspace(-1.2, 1.15, 8)]
    a.add("Body", *tube(lid, [0.07, 0.19, 0.25, 0.28, 0.28, 0.24, 0.16, 0.06], 6, up=out))
    # Peau granuleuse sur la paupière : une rangée de petits galets sur le bourrelet.
    lid_r = [0.07, 0.19, 0.25, 0.28, 0.28, 0.24, 0.16, 0.06]
    lid_up = normalize(e2 * 0.75 + out * 0.65)
    for i in range(1, 7):
        for off in (-0.25, 0.25):
            q = lid[i] + (lid[i + (1 if off > 0 else -1)] - lid[i]) * abs(off) + lid_up * lid_r[i] * 0.92
            a.add("Body", *gem(q, e1, lid_up, normalize(np.cross(lid_up, e1)), 0.06 * S, 0.035 * S, 0.06 * S))

    # Poche sous l'œil : 2 plis superposés en croissant, posés sur la peau.
    for k, (dy, r) in enumerate(((0.36, 0.1), (0.56, 0.085))):
        fold = []
        for q in np.linspace(-1, 1, 7):
            xx = ex + 0.05 + q * (0.55 - 0.08 * k)
            yy = ey - dy - 0.08 * (1 - q * q)
            fold.append(P(xx, yy, (skull_side(xx, yy) + 0.01) * sd))
        a.add("Body", *tube(fold, [0.0, r * 0.6, r, r, r, r * 0.6, 0.0], 5))


# Profil du crâne : x (vers l'avant), centre vertical, demi-largeur, demi-hauteur dessus, demi-hauteur dessous.
# Front haut, « stop » marqué entre les yeux, chanfrein court et museau large et carré comme un félin.
SKULL = [
    (-1.4, 0.15, 1.15, 1.2, 1.2),
    (-0.5, 0.3, 1.5, 1.45, 1.3),
    (0.4, 0.4, 1.72, 1.55, 1.3),
    (1.2, 0.42, 1.68, 1.45, 1.25),
    (1.9, 0.25, 1.42, 1.12, 1.12),
    (2.6, 0.08, 1.22, 0.95, 0.95),
    (3.3, 0.02, 1.15, 0.88, 0.85),
    (3.9, -0.02, 1.1, 0.84, 0.8),
    (4.3, -0.05, 0.98, 0.76, 0.72),
    (4.55, -0.07, 0.78, 0.64, 0.58),
    (4.72, -0.08, 0.5, 0.44, 0.38),
]
SIDES_HEAD = 32   # côtés du crâne (multiple de 4 : sommets pile sur le dessus, le dessous et les côtés)
SUPER = 2.6   # > 2 : section plus carrée, joues pleines
EYE = (1.5, 0.5)  # centre de l'œil (x, y) dans le repère de la tête


# Arcade sourcilière gauche, de l'arrière de l'œil jusqu'au haut du nez : (x, angle sur le crâne, épaisseur).
# Vue de face elle descend vers le milieu : les 2 arcades forment un V froncé dont la pointe touche le nez.
BROW_CTRL = [(0.85, 0.8, 0.55), (1.2, 0.62, 0.85), (1.55, 0.47, 1.0), (1.9, 0.78, 1.0),
             (2.2, 1.1, 0.9), (2.5, 1.35, 0.75), (2.75, 1.5, 0.55)]
BROW_H = 0.5      # hauteur de l'arcade (studs)
BROW_W = 0.23       # demi-largeur de l'arcade


def gauss(v):
    return np.exp(-v * v)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def base_point(x, t):
    """Point de la super-ellipse du crâne, sans relief : (x, y, z)."""
    yc, w, ht, hb = skull_section(x)
    ct, st = np.cos(t), np.sin(t)
    h = ht if st >= 0 else hb
    return np.array([x, yc + h * np.sign(st) * abs(st) ** (2 / SUPER), w * np.sign(ct) * abs(ct) ** (2 / SUPER)])


_BROW = None


def brow_line():
    """Tracé dense de l'arcade : liste de (x, angle), points 3D (côté gauche, sans relief) et épaisseurs."""
    global _BROW
    if _BROW is None:
        xt = catmull_rom([(x, t, k) for x, t, k in BROW_CTRL], 40)
        pts = np.array([base_point(x, t) for x, t, _ in xt])
        _BROW = (xt[:, :2], pts, xt[:, 2])
    return _BROW


def brow_bump(x, y, z):
    _, pts, k = brow_line()
    d = np.linalg.norm(pts - np.array([x, y, abs(z)]), axis=1)
    i = np.argmin(d)
    return BROW_H * k[i] * gauss(d[i] / BROW_W)


def seg_dist(px, py, a, b):
    a, b, p = np.asarray(a, float), np.asarray(b, float), np.array([px, py])
    t = np.clip((p - a) @ (b - a) / ((b - a) @ (b - a)), 0, 1)
    return np.linalg.norm(p - a - t * (b - a))


def relief(x, y, side_w, top_w=0.0, z=None):
    """Bosses et creux sculptés dans la peau du crâne (en studs, vers l'extérieur).
    side_w : 1 sur le côté de la tête, 0 dessus/dessous (les orbites ne creusent que les côtés).
    top_w : 1 sur le dessus (arête du nez). z : demi-largeur au point (pour l'arcade et le pli du front)."""
    ex, ey = EYE
    d = 0.0
    # Orbite : creux en amande, étroit, où l'œil s'enfonce.
    d -= 0.4 * gauss(np.hypot((x - ex) / 0.6, (y - ey) / 0.32)) * side_w
    # Poche gonflée sous l'œil.
    d += 0.17 * gauss(np.hypot((x - ex - 0.05) / 0.5, (y - ey + 0.45) / 0.18)) * side_w
    # Pommette saillante, en arête qui file vers l'arrière de la tête.
    d += 0.17 * gauss(seg_dist(x, y, (1.85, -0.12), (-0.7, 0.24)) / 0.2) * side_w
    if z is not None:
        # Arcades massives en V au-dessus des yeux.
        d += brow_bump(x, y, z)
        # Pli profond entre les 2 arcades, qui descend jusqu'au chanfrein.
        d -= 0.32 * gauss(z / 0.13) * smoothstep(1.55, 1.85, x) * (1 - smoothstep(2.55, 2.85, x)) * top_w
    # Coussinets des moustaches, gonflés de chaque côté du museau (comme un tigre).
    d += 0.3 * gauss(np.hypot((x - 4.05) / 0.5, (y + 0.3) / 0.36)) * side_w
    # Arête du nez : léger creux, puis la truffe qui se relève au bout.
    d -= 0.07 * gauss((x - 4.0) / 0.22) * top_w
    d += 0.12 * gauss((x - 4.5) / 0.22) * top_w
    # Plis en travers sur le dessus du chanfrein, là où la peau se tasse.
    for xc in (3.05, 3.4):
        d += (0.06 * gauss((x - xc) / 0.06) - 0.07 * gauss((x - xc + 0.1) / 0.05)) * top_w
    if z is not None:
        # Arête tranchante au milieu du museau : prend le relais du pli entre les arcades, jusqu'à la truffe.
        d += 0.16 * gauss(z / 0.16) * smoothstep(2.75, 3.05, x) * (1 - smoothstep(4.3, 4.6, x)) * top_w
    return d


MUZZLE_W = 0.74   # largeur du museau par rapport au profil de base
MUZZLE_H = 0.62   # hauteur du dessus du museau par rapport au profil de base
MUZZLE_HB = 0.78  # hauteur du dessous du museau (mâchoire supérieure) par rapport au profil de base


def muzzle_w(x):
    """Facteur de largeur : 1 au niveau des yeux, MUZZLE_W sur le museau (transition douce)."""
    return 1 - (1 - MUZZLE_W) * smoothstep(2.2, 3.1, x)


def jaw_lift(x):
    """De combien le dessous de la mâchoire supérieure remonte à l'avant-arrière x (lèvres et dents suivent)."""
    xs = [r[0] for r in SKULL]
    return np.interp(x, xs, [r[4] for r in SKULL]) * (1 - MUZZLE_HB) * smoothstep(2.1, 3.1, x)


def skull_section(x):
    xs = [r[0] for r in SKULL]
    yc, w, ht, hb = [np.interp(x, xs, [r[k] for r in SKULL]) for k in (1, 2, 3, 4)]
    return [yc, w * muzzle_w(x), ht * (1 - (1 - MUZZLE_H) * smoothstep(2.1, 3.1, x)), hb - jaw_lift(x)]


def skull_point(x, t):
    """Point de la peau du crâne à l'avant-arrière x et à l'angle t (0 = côté gauche, pi/2 = dessus).
    Tout le museau (truffe, coussinets, sillon) est sculpté ici, d'un seul tenant avec le crâne."""
    yc, w, ht, hb = skull_section(x)
    ct, st = np.cos(t), np.sin(t)
    h = ht if st >= 0 else hb
    z = w * np.sign(ct) * abs(ct) ** (2 / SUPER)
    y = h * np.sign(st) * abs(st) ** (2 / SUPER)
    # Normale de la super-ellipse, pour pousser les bosses vers l'extérieur.
    nz = np.sign(z) * abs(z / w) ** (SUPER - 1) / w
    ny = np.sign(y) * abs(y / h) ** (SUPER - 1) / h
    nn = np.hypot(nz, ny) or 1.0
    nz, ny = nz / nn, ny / nn
    d = relief(x, yc + y, abs(nz) ** 1.5, max(0.0, ny) ** 2, z)
    # Avant du museau : la truffe déborde en haut, les coussinets avancent, le sillon recule au milieu.
    front = smoothstep(4.0, 4.72, x)
    dx = 0.38 * front * max(0.0, st) ** 1.3          # truffe qui avance en crochet au-dessus de la gueule
    dx += 0.14 * front * np.clip(-st * abs(ct) * 2.2, 0, 1)
    dx -= 0.18 * front * gauss(ct / 0.22) * max(0.0, -st)
    return np.array([x + dx, yc + y + ny * d, z + nz * d])


def skin_normal(x, t):
    p = skull_point(x, t)
    n = np.cross(skull_point(x + 0.04, t) - skull_point(x - 0.04, t), skull_point(x, t + 0.04) - skull_point(x, t - 0.04))
    n = normalize(n)
    c = np.array([x, skull_section(x)[0], 0.0])
    return n if n @ (p - c) > 0 else -n


def skull_side(x, y):
    """Demi-largeur du crâne (relief compris) à l'avant-arrière x et à la hauteur y."""
    yc, w, ht, hb = skull_section(x)
    h = ht if y >= yc else hb
    v = min(abs(y - yc) / h, 0.999)
    z = w * (1 - v ** SUPER) ** (1 / SUPER)
    return z + relief(x, y, (1 - v) ** 0.5, 0.0, z)


def skull_top(x):
    yc, w, ht, hb = skull_section(x)
    return yc + ht


def build_head(a, neck, neck_r):
    """Tête construite dans un repère local (x vers l'avant, y en haut, z sur le côté), puis placée sur la nuque."""
    S = 1.3
    f = normalize(np.array([0.0, 0.12, 1.0]))
    u = normalize(np.array([0.0, 1.0, 0.0]) - f[1] * f)
    s = np.cross(u, f)
    origin = np.asarray(neck) + f * 0.4
    a.head_center = origin + (f * 1.6 + u * 0.3) * S

    def P(x, y, z):
        return origin + (f * x + u * y + s * z) * S

    def Pm(x, y, z):
        """Comme P, mais la largeur suit l'affinement du museau."""
        return P(x, y, z * muzzle_w(x))

    def on_skin(x, y, side, lift=0.04):
        return P(x, y, side * (skull_side(x, y) + lift))

    # Crâne + museau d'un seul tenant (truffe, coussinets, sillon et orbites sculptés dans la même peau).
    xs = np.concatenate([np.linspace(-1.4, 0.6, 3), np.linspace(0.85, 2.3, 10), np.linspace(2.6, 3.8, 4),
                         np.linspace(3.95, 4.72, 7)])
    angs = np.arange(SIDES_HEAD) * 2 * np.pi / SIDES_HEAD
    a.add("Body", *loft([np.array([P(*skull_point(x, t)) for t in angs]) for x in xs]))

    # Narines en fentes, inclinées comme le V des arcades (bas côté milieu, haut vers l'arrière et l'extérieur),
    # avec une aile évasée en lame au-dessus de chacune.
    for side in (1, -1):
        tt = np.pi / 2 - side * 0.95
        c0 = skull_point(4.68, tt)
        nrm = skin_normal(4.68, tt if side > 0 else np.pi - (np.pi - tt))
        n_w = P(*(c0 + nrm)) - P(*c0)
        n_w = normalize(n_w)
        slit = normalize(-f * 0.55 + u * 0.5 + s * side * 0.45)
        slit = normalize(slit - n_w * (slit @ n_w))
        cen = P(*c0) - n_w * 0.02 * S
        a.add("Pupils", *gem(cen, slit, n_w, normalize(np.cross(n_w, slit)), 0.33 * S, 0.06 * S, 0.1 * S))
        wing_up = normalize(np.cross(slit, n_w) * side)
        if wing_up @ u < 0:
            wing_up = -wing_up
        # L'aile suit la peau : chaque point est reposé sur le crâne puis légèrement soulevé.
        wing = []
        for k in (0.0, 0.25, 0.5, 0.75, 1.0):
            xx, tt2 = 4.6 - 0.75 * k, np.pi / 2 - side * (0.78 - 0.18 * k)
            wing.append(P(*(skull_point(xx, tt2) + skin_normal(xx, tt2) * (0.03 + 0.04 * k))))
        a.add("Body", *tube(wing, [0.03, 0.1, 0.12, 0.08, 0.0], 5, up=n_w, flat=0.45))

    # Corne de nez au bout de l'arête, et une plus petite derrière, courbées vers l'arrière.
    for x0, L, r in ((4.25, 0.8, 0.2), (3.7, 0.45, 0.13)):
        b0 = P(*skull_point(x0, np.pi / 2)) - u * 0.05 * S
        horn = [b0, b0 + (u * 0.4 + f * 0.05) * L * S, b0 + (u * 0.75 - f * 0.12) * L * S, b0 + (u * 0.95 - f * 0.4) * L * S]
        a.add("Horns", *tube(horn, [r, r * 0.7, r * 0.4, 0.0], 6))

    # Rides en chevrons : partent de l'arête et filent vers l'arrière et le bas, comme un museau qui gronde.
    for side in (1, -1):
        for x0 in (3.0, 3.35, 3.7):
            line = []
            for q in np.linspace(0, 1, 6):
                xx, tt = x0 - 0.45 * q, np.pi / 2 - side * (0.28 + 0.75 * q)
                line.append(P(*(skull_point(xx, tt) + skin_normal(xx, tt) * 0.02)))
            a.add("Body", *tube(line, [0.0, 0.11, 0.13, 0.12, 0.08, 0.0], 5))

    # ---------- Peau du visage ----------
    # Un seul système d'éléments posés sur la peau : en haut (front, chanfrein) ce sont des écailles en losange
    # qui se chevauchent comme des tuiles, pointe vers l'arrière ; sur les côtés (joues, autour des yeux) elles
    # deviennent progressivement des galets ronds serrés. Truffe et lèvres restent lisses.
    def skin_frame(x, t):
        p0 = skull_point(x, t)
        dxp = skull_point(x + 0.04, t) - skull_point(x - 0.04, t)
        dtp = skull_point(x, t + 0.04) - skull_point(x, t - 0.04)
        nrm = normalize(np.cross(dxp, dtp))
        if nrm @ (p0 - np.array([x, skull_section(x)[0], 0.0])) < 0:
            nrm = -nrm
        back = normalize(-dxp - nrm * (-dxp @ nrm))
        return p0, nrm, back, normalize(np.cross(nrm, back))

    def skin_element(x, t, size, b):
        """Écaille couchée sur la peau, comme une tuile : bouclier arrondi à 6 côtés, presque plat ; le bord avant
        s'enfonce sous la précédente, le bord arrière se soulève à peine. b = 1 : plus allongée (front) ;
        b petit : plus ronde (joues)."""
        p0, nrm, back, side_v = skin_frame(x, t)
        L_back = size * (0.52 + 0.22 * b)
        L_front = size * (0.48 + 0.04 * b)
        W = size * 0.5
        base = []
        for k in range(6):
            ang = 2 * np.pi * k / 6               # k = 0 : vers l'arrière (bord libre)
            ca, sa = np.cos(ang), np.sin(ang)
            r_back = L_back if ca > 0 else L_front
            lift = size * (0.035 + 0.035 * b) * max(0.0, ca) - size * 0.13 * max(0.0, -ca)
            base.append(p0 + back * ca * r_back + side_v * sa * W + nrm * (lift - size * 0.02))
        apex = p0 + back * size * 0.12 + nrm * size * (0.085 + 0.025 * (1 - b))
        verts = [P(*q) for q in base + [apex]]
        faces = [(k, (k + 1) % 6, 6) for k in range(6)] + [(0, 2, 1), (0, 3, 2), (0, 4, 3), (0, 5, 4)]
        a.add("Body", verts, faces)

    def skin_zone(x, t):
        """Taille de l'élément et b (écaille 1 / galet 0) ; None si la peau doit rester nue à cet endroit."""
        bp = base_point(x, t)
        y, z = bp[1], abs(bp[2])
        dt = abs(t - np.pi / 2)
        ex, ey = EYE
        d_eye = np.hypot((x - ex) / 0.75, (y - ey) / 0.45)
        if d_eye < 1.0 and z > 0.9:
            return None                                                   # l'œil et sa paupière
        if brow_bump(x, y, z) > 0.2:
            return None                                                   # crête de l'arcade (sourcils dorés)
        if 0.75 < x < 1.75 and dt < 0.2:
            return None                                                   # marque dorée du front
        if x > 4.05 or (x > 0.4 and y < -0.42):
            return None                                                   # truffe et lèvres : peau lisse
        if x < -0.7 or y < -0.62:
            return None
        for hb in ((-0.1, 1.5, 0.7), (3.7, None, 0.0), (4.25, None, 0.0)):
            hx, hy, hz = hb
            hy = skull_top(hx) if hy is None else hy
            if np.linalg.norm(np.array([x - hx, y - hy, z - hz])) < (0.45 if hz else 0.22):
                return None                                               # bases des cornes
        if x > 2.75 and dt < 0.12:
            return None                                                   # arête tranchante du museau
        # Écailles en haut, galets sur les côtés et près des yeux, transition douce.
        b = 0.3 + 0.7 * (1 - smoothstep(0.45, 1.0, dt)) * smoothstep(0.9, 1.6, d_eye)
        scale_size = 0.48 * (1 - 0.5 * smoothstep(0.0, 0.85, dt)) * (1 - 0.68 * smoothstep(1.2, 4.0, x)) \
            * (1 - 0.35 * (1 - smoothstep(1.0, 1.8, d_eye)))
        pebble_size = 0.2 - 0.05 * (1 - smoothstep(1.0, 1.6, d_eye))
        return pebble_size + (scale_size - pebble_size) * b, b

    cands = []
    for x in np.arange(-0.7, 4.06, 0.06):
        for t in np.arange(np.pi / 2 - 1.75, np.pi / 2 + 1e-6, 0.045):
            z = skin_zone(x, t)
            if z is not None:
                cands.append((z[0], x, t, z[1]))
    cands.sort(key=lambda c: -c[0])
    placed, pts = [], np.zeros((0, 3)), 
    pts = np.zeros((0, 3))
    rad = np.zeros(0)
    gap = np.zeros(0)
    for size, x, t, b in cands:
        p = skull_point(x, t)
        r = size * 0.5
        g = 0.7 + 0.15 * (1 - b)                      # les écailles se chevauchent comme des tuiles
        if len(pts) and np.any(np.linalg.norm(pts - p, axis=1) < (rad + r) * np.minimum(gap, g)):
            continue
        pts = np.vstack([pts, p])
        rad = np.append(rad, r)
        gap = np.append(gap, g)
        placed.append((x, t, size, b))
    for x, t, size, b in placed:
        skin_element(x, t, size, b)
        if abs(t - np.pi / 2) > 0.02:                 # symétrique (le milieu n'est posé qu'une fois)
            skin_element(x, np.pi - t, size, b)

    # Rangée de petites pointes coniques le long des joues, qui suivent la mâchoire vers l'arrière.
    for side in (1, -1):
        for k, x in enumerate(np.linspace(2.2, -0.65, 8)):
            y = np.interp(x, [-0.65, 2.2], [-0.12, -0.42])
            b0 = P(x, y, (skull_side(x, y) - 0.03) * side)
            L = 0.32 + 0.26 * k / 7
            tip = b0 + (-f * 0.75 + s * side * 0.62 - u * 0.1) * L * S
            a.add("Horns", *tube([b0, (b0 + tip) / 2 + s * side * 0.03 * S, tip], [0.11 + 0.05 * k / 7, 0.07, 0.0], 5))

    # Plis au coin de la gueule : 3 rides en éventail.
    for side in (1, -1):
        for k, (dy, L) in enumerate(((0.12, 0.55), (0.0, 0.7), (-0.12, 0.5))):
            fold = []
            for q in np.linspace(0, 1, 5):
                xx = 0.75 - q * L
                yy = -0.42 + dy * q + 0.05 * np.sin(q * np.pi)
                fold.append(P(xx, yy, (skull_side(xx, yy) + 0.03) * side))
            a.add("Body", *tube(fold, [0.0, 0.11, 0.12, 0.09, 0.0], 5))

    # Truffe et lèvres lisses : seulement quelques pores, en rangées sur les coussinets des moustaches.
    for side in (1, -1):
        for x, y in ((3.75, -0.18), (3.95, -0.22), (4.15, -0.22), (3.85, -0.36), (4.05, -0.4)):
            p0 = P(x, y, (skull_side(x, y) + 0.005) * side)
            a.add("Pupils", *gem(p0, f, u, s * side, 0.035 * S, 0.035 * S, 0.02 * S))

    # Mâchoire du bas, entrouverte de 20°.
    hinge = np.array([0.4, -0.55])
    c, sn = np.cos(-0.35), np.sin(-0.35)

    def jaw_ring(x, y, w, h, n=8):
        w = w * muzzle_w(x)
        ang = np.pi / n + np.arange(n) * 2 * np.pi / n
        out = []
        for t in ang:
            px, py = x - hinge[0], y + np.sin(t) * h - hinge[1]
            out.append(P(hinge[0] + px * c - py * sn, hinge[1] + px * sn + py * c, np.cos(t) * w))
        return np.array(out)

    def jaw_point(x, y, z):
        px, py = x - hinge[0], y - hinge[1]
        return P(hinge[0] + px * c - py * sn, hinge[1] + px * sn + py * c, z)

    # Mâchoire du bas avec du volume : le dessus (dents, langue) reste en place, le dessous descend
    # en ventre arrondi, avec des joues musclées vers l'articulation et un menton marqué.
    # Profil : x, dessus, dessous, demi-largeur.
    JAW = [(0.0, -0.4, -1.34, 1.16), (0.8, -0.52, -1.48, 1.12), (1.6, -0.59, -1.46, 1.03), (2.4, -0.62, -1.42, 0.96),
           (3.0, -0.63, -1.37, 0.91), (3.55, -0.61, -1.38, 0.83), (3.95, -0.63, -1.28, 0.7), (4.2, -0.72, -1.08, 0.44)]

    def jaw_bottom(x):
        return np.interp(x, [j[0] for j in JAW], [j[2] for j in JAW])

    def jaw_section(x, top, bot, w, n=12, p=2.4):
        """Section de la mâchoire : super-ellipse (flancs pleins), un peu plus large en bas qu'en haut."""
        yc, h = (top + bot) / 2, (top - bot) / 2
        out = []
        for t in np.pi / n + np.arange(n) * 2 * np.pi / n:
            ct, st = np.cos(t), np.sin(t)
            zz = w * muzzle_w(x) * np.sign(ct) * abs(ct) ** (2 / p) * (1.0 if st > 0 else 1.06)
            yy = yc + h * np.sign(st) * abs(st) ** (2 / p)
            out.append(jaw_point(x, yy, zz))
        return np.array(out)

    a.add("Body", *loft([jaw_section(*j) for j in JAW]))
    # Bande dorée sous la mâchoire, qui suit le nouveau dessous.
    a.add("Belly", *loft([jaw_section(x, jaw_bottom(x) + 0.42, jaw_bottom(x) - 0.04, w * 0.72, 10)
                          for x, w in ((0.4, 1.15), (1.6, 1.0), (2.8, 0.88), (3.6, 0.7))]))
    # Lèvre du haut en bourrelet, qui remonte au coin de la gueule.
    for side in (1, -1):
        lip = [Pm(x, y + jaw_lift(x), z * side) for x, y, z in
               ((0.5, -0.25, 1.45), (1.2, -0.6, 1.35), (2.2, -0.75, 1.2), (3.2, -0.78, 1.1), (3.9, -0.72, 0.95))]
        a.add("Body", *tube(catmull_rom(lip, 9), [0.06, 0.12, 0.15, 0.16, 0.16, 0.15, 0.14, 0.12, 0.05], 5))
        low = [jaw_point(x, -0.62, w * muzzle_w(x) * side) for x, w in ((0.9, 1.15), (2.0, 1.02), (3.0, 0.92), (3.9, 0.72))]
        a.add("Body", *tube(low, [0.05, 0.1, 0.1, 0.04], 5))

    def jaw_up(x):
        return normalize(jaw_point(x, 0.0, 0.0) - jaw_point(x, -1.0, 0.0))

    def jaw_top(x):
        return np.interp(x, [0.2, 1.6, 3.0, 3.8, 4.15], [-0.43, -0.59, -0.63, -0.6, -0.7])

    # Intérieur de la gueule : la gorge sombre au fond, un palais fin en haut et un plancher fin en bas.
    # La langue repose sur le plancher. On ne voit plus « à travers » la gueule.
    def mouth_w(x):
        yc, w, ht, hb = skull_section(x)
        return min(w, 1.15) * (0.82 if x < 3.6 else 0.62)

    rings = []
    for x in (-0.2, 0.6, 1.2):
        yc, w, ht, hb = skull_section(x)
        top_y, bot_y, wz = yc - hb + 0.12, jaw_top(x) - 0.08, mouth_w(x)
        rings.append(np.array([P(x, top_y, wz * 0.55), P(x, top_y + 0.04, 0.0), P(x, top_y, -wz * 0.55),
                               P(x, top_y - 0.15, -wz), jaw_point(x, bot_y + 0.12, -wz),
                               jaw_point(x, bot_y, -wz * 0.55), jaw_point(x, bot_y - 0.04, 0.0),
                               jaw_point(x, bot_y, wz * 0.55), jaw_point(x, bot_y + 0.12, wz), P(x, top_y - 0.15, wz)]))
    a.add("Mouth", *loft(rings))
    palate, floor = [], []
    for x in (0.9, 1.8, 2.8, 3.55, 3.95):
        yc, w, ht, hb = skull_section(x)
        y0, wz = yc - hb, mouth_w(x)
        palate.append(np.array([P(x, y0 + 0.12, wz), P(x, y0 + 0.12, -wz), P(x, y0 - 0.1, -wz * 0.95),
                                P(x, y0 - 0.06, 0.0), P(x, y0 - 0.1, wz * 0.95)]))
        if x < 3.9:
            j0 = jaw_top(x)
            jw = np.interp(x, [j[0] for j in JAW], [j[3] for j in JAW]) * muzzle_w(x) * 0.72   # dans la mâchoire
            floor.append(np.array([jaw_point(x, j0 - 0.2, jw * 0.9), jaw_point(x, j0 - 0.2, -jw * 0.9),
                                   jaw_point(x, j0 + 0.04, -jw), jaw_point(x, j0, 0.0),
                                   jaw_point(x, j0 + 0.04, jw)]))
    a.add("Mouth", *loft(palate))
    a.add("Mouth", *loft(floor))
    # Palais : 4 bourrelets en travers, visibles quand on regarde dans la gueule.
    for x in (1.6, 2.2, 2.8, 3.35):
        yc, w, ht, hb = skull_section(x)
        y0 = yc - hb + 0.1
        ridge = [Pm(x + 0.12, y0, -0.62), Pm(x - 0.08, y0 - 0.06, -0.3), Pm(x - 0.12, y0 - 0.08, 0.0),
                 Pm(x - 0.08, y0 - 0.06, 0.3), Pm(x + 0.12, y0, 0.62)]
        a.add("Mouth", *tube(ridge, [0.0, 0.08, 0.09, 0.08, 0.0], 5))

    # Langue : large et plate sur le plancher, le bout qui se relève et se fend en deux.
    tongue = [jaw_point(x, jaw_top(x) + lift, 0.0) for x, lift in
              ((0.6, 0.2), (1.5, 0.21), (2.4, 0.22), (3.1, 0.25), (3.55, 0.38))]
    tl = catmull_rom(tongue, 9)
    a.add("Tongue", *tube(tl, [0.36, 0.41, 0.42, 0.4, 0.37, 0.33, 0.29, 0.25, 0.2], 8, tip=False,
                          up=jaw_up(2.0), flat=0.38))
    for side in (1, -1):
        b0 = tl[-1]
        fork = [b0, b0 + (f * 0.25 + s * side * 0.12) * S + jaw_up(3.6) * 0.12 * S,
                b0 + (f * 0.45 + s * side * 0.25) * S + jaw_up(3.6) * 0.32 * S]
        a.add("Tongue", *tube(fork, [0.15, 0.1, 0.0], 6, up=jaw_up(3.6), flat=0.5))

    # Dentition acérée : dents fines à 3 faces (arêtes tranchantes), recourbées vers la gorge,
    # longues et courtes en alternance, crocs en poignard et incisives pointues devant.
    def fang(base, down, L, r):
        pts = [base, base + down * L * 0.4 * S, base + (down * L * 0.75 - f * 0.06) * S,
               base + (down * L - f * 0.16) * S]
        a.add("Horns", *tube(pts, [r, r * 0.72, r * 0.38, 0.0], 3))

    for side in (1, -1):
        # Rangée du haut, enracinée dans la gencive sous la lèvre.
        for k, x in enumerate(np.arange(1.15, 3.65, 0.27)):
            yc, w, ht, hb = skull_section(x)
            L = (0.42 if k % 2 else 0.26) + 0.08 * x / 3.6
            fang(P(x, -0.66 + jaw_lift(x), side * min(w, 1.2) * 0.9), -u, L, 0.075)
        fang(Pm(3.85, -0.66 + jaw_lift(3.85), 0.85 * side), -u, 1.05, 0.15)                       # grand croc
        fang(Pm(3.45, -0.66 + jaw_lift(3.45), 0.95 * side), -u, 0.62, 0.1)                        # croc secondaire
        for z in (0.2, 0.47):
            fang(Pm(4.3 - z * 0.35, -0.66 + jaw_lift(4.3), z * side), -u, 0.3, 0.065)           # incisives
        # Rangée du bas, sur la mâchoire, pointes vers le haut.
        for k, x in enumerate(np.arange(1.3, 3.4, 0.3)):
            w = np.interp(x, [0.2, 1.6, 3.0, 3.8], [1.25, 1.08, 0.95, 0.82]) * 0.82 * muzzle_w(x)
            L = (0.36 if k % 2 else 0.22) + 0.06 * x / 3.4
            fang(jaw_point(x, jaw_top(x) - 0.02, w * side), jaw_up(x), L, 0.07)
        fang(jaw_point(3.55, -0.65, 0.66 * muzzle_w(3.55) * side), jaw_up(3.55), 0.85, 0.14)      # croc du bas
        for z in (0.18, 0.4):
            fang(jaw_point(4.0 - z * 0.3, -0.72, z * muzzle_w(4.0) * side), jaw_up(4.0), 0.26, 0.06)

    # Yeux : amande dorée qui brille, pupille fendue, paupières.
    for side in (1, -1):
        build_eye(a, P, f, u, s * side, S)

    # Sourcils dorés en volutes, posés sur la crête de l'arcade : une volute à la pointe du V (près du nez),
    # puis la mèche suit l'arcade vers l'arrière et file derrière la tête, avec 2 petites flammes.
    xt, _, _ = brow_line()
    for side in (1, -1):
        def crest(x, t, lift=0.07):
            tt = t if side > 0 else np.pi - t
            return P(*(skull_point(x, tt) + skin_normal(x, tt) * lift))
        cx, ct0 = xt[-1][0] + 0.05, xt[-1][1] - 0.25
        spiral = []
        for k, th in enumerate(np.linspace(2.2 * np.pi, 0.0, 12)):
            rho = 0.06 + 0.26 * k / 11
            spiral.append(crest(cx + rho * np.cos(th), ct0 + rho * np.sin(th) * 1.3, 0.06 + 0.03 * k / 11))
        along = [crest(x, t) for x, t in xt[::-1][4::4]]
        sweep = along + [P(-0.4, 1.85, (skull_side(-0.4, 1.4) + 0.2) * side),
                         P(-1.3, 1.95, (skull_side(-1.3, 1.0) + 0.35) * side), P(-2.2, 2.1, 1.95 * side),
                         P(-3.0, 2.4, 2.25 * side), P(-3.4, 2.75, 2.3 * side), P(-3.2, 3.0, 2.2 * side)]
        line = np.vstack([spiral, catmull_rom(sweep, 22)])
        n = len(line)
        radii = [0.07 + 0.17 * min(1.0, k / 10) * (1 - max(0, k - 16) / (n - 16)) ** 0.8 for k in range(n)]
        radii[-1] = 0.0
        a.add("Whiskers", *tube(line, radii, 6, up=s * side, flat=0.45))
        for j, L in ((12, 0.9), (20, 1.0)):
            b0 = crest(*xt[j], 0.12)
            tuft = [b0, b0 + (-f * 0.45 + u * 0.25 + s * side * 0.15) * S * L, b0 + (-f * 1.0 + u * 0.4 + s * side * 0.3) * S * L,
                    b0 + (-f * 1.5 + u * 0.38 + s * side * 0.38) * S * L, b0 + (-f * 1.75 + u * 0.2 + s * side * 0.4) * S * L]
            a.add("Whiskers", *tube(catmull_rom(tuft, 8), [0.15, 0.15, 0.13, 0.11, 0.08, 0.06, 0.03, 0.0], 5,
                                    up=s * side, flat=0.5))

    # Front : marque dorée en losange entre les arcades.
    a.add("Whiskers", *gem(P(1.25, skull_top(1.25) + 0.02, 0), f, u, s, 0.45 * S, 0.1 * S, 0.24 * S))

    # Pommettes en relief et joues en flammes vers l'arrière.
    for side in (1, -1):
        cheek = [on_skin(x, y, side, lift) for x, y, lift in
                 ((2.4, 0.0, 0.0), (1.7, -0.08, 0.08), (0.9, -0.12, 0.1), (0.1, 0.0, 0.08), (-0.5, 0.25, 0.0))]
        a.add("Body", *tube(catmull_rom(cheek, 9), [0.04, 0.12, 0.17, 0.19, 0.19, 0.17, 0.14, 0.09, 0.03], 6))
        for y0, L in ((0.15, 2.2), (-0.25, 2.6), (-0.65, 2.0)):
            b0 = on_skin(0.4, y0, side, 0.0)
            b1 = on_skin(-0.4, y0 + 0.1, side, 0.0)
            tip = P(-0.4 - L, y0 + 0.2 + L * 0.25, (skull_side(-0.4, y0) + L * 0.55) * side)
            a.add("Fins", *fin(b0, b1, tip, np.cross(tip - b0, b1 - b0), 0.12))

    # Cornes en bois de cerf, vers l'arrière, avec une branche.
    for side in (1, -1):
        h0 = P(-0.1, 1.5, 0.7 * side)
        h1 = P(-1.1, 2.6, 1.0 * side)
        h2 = P(-2.6, 3.3, 1.35 * side)
        h3 = P(-4.0, 3.3, 1.5 * side)
        h4 = P(-4.7, 3.8, 1.55 * side)
        a.add("Horns", *tube([h0, h1, h2, h3, h4], [0.33, 0.28, 0.22, 0.12, 0.0], 6))
        a.add("Horns", *tube([h1 * 0.5 + h2 * 0.5, P(-1.6, 4.0, 1.2 * side), P(-1.4, 4.6, 1.15 * side)],
                             [0.15, 0.09, 0.0], 5))
        # Oreilles en nageoire.
        a.add("Fins", *fin(P(-0.4, 0.9, 1.45 * side), P(-1.2, 0.6, 1.2 * side), P(-2.3, 1.5, 2.4 * side),
                           normalize(u - s * side * 0.5), 0.12))

    # Moustaches longues et ondulées, qui partent des coussinets du museau.
    for side in (1, -1):
        pts = [Pm(4.1, -0.25 + jaw_lift(4.1) * 0.6, 1.05 * side), P(3.9, -0.35, 2.2 * side), P(2.8, -0.8, 3.4 * side),
               P(1.0, -0.45, 4.3 * side), P(-0.9, -1.05, 4.9 * side), P(-2.8, -0.65, 5.3 * side)]
        a.add("Whiskers", *tube(catmull_rom(pts, 14), np.linspace(0.16, 0.0, 14), 4))

    # Crinière en flammes autour de la nuque.
    for ang in np.linspace(np.radians(-150), np.radians(150), 11):
        rad = np.array([0, np.cos(ang), np.sin(ang)])  # 0° = vers le haut
        base_a = P(0.2, 0.3 + rad[1] * 1.3, rad[2] * 1.4)
        base_b = P(-1.1, 0.2 + rad[1] * 1.1, rad[2] * 1.15)
        length = 2.6 if abs(ang) < 1.6 else 1.9
        tip = P(-1.1 - length, 0.3 + rad[1] * (1.1 + length * 0.75), rad[2] * (1.15 + length * 0.75))
        normal = np.cross(tip - base_a, base_b - base_a)
        a.add("Fins", *fin(base_a, base_b, tip, normal, 0.14))

    # Barbichette : 3 grosses mèches rouges sous le menton, qui descendent puis s'enroulent vers l'arrière.
    for z, L, r in ((0.0, 1.0, 0.34), (0.32, 0.8, 0.26), (-0.32, 0.8, 0.26)):
        xb = 3.7 - abs(z) * 0.5
        b0 = jaw_point(xb, jaw_bottom(xb) + 0.08, z)
        rel = ((0, 0), (-0.1, -0.6), (-0.45, -1.3), (-1.05, -1.85), (-1.7, -1.95), (-2.1, -1.65), (-1.95, -1.35))
        pts = [b0 + (f * dx * L + u * dy * L + s * z * 0.4 * min(1, -dy)) * S for dx, dy in rel]
        line = catmull_rom(pts, 14)
        radii = [r * np.sin(np.pi * (0.15 + 0.85 * k / 13)) ** 0.6 for k in range(14)]
        radii[-1] = 0.0
        a.add("Fins", *tube(line, radii, 6, up=s, flat=0.45))



def build():
    a = Asset("Dragon_Long_v14")
    for name, (color, mat) in COULEURS.items():
        a.part(name, color, mat)
    pts = catmull_rom(SPINE, RINGS)
    T, N, B = frames(pts)
    t = np.linspace(0, 1, RINGS)
    radii = np.array([body_radius(x) for x in t])
    build_body(a, pts, T, N, B, radii)
    build_scales(a, pts, T, N, B, radii)
    build_belly_plates(a, pts, T, N, B, radii)
    build_spines(a, pts, T, N, B, radii)
    build_legs(a, pts, T, N, B, radii)
    build_head(a, pts[0], radii[0])
    return a


def all_assets():
    return [build()]
