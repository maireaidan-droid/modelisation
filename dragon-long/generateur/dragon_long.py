# Dragon Long (dragon chinois) stylisé, low-poly.
# v1 : premier croquis. v2 : écailles en relief sur le dos, plaques sur le ventre, crête plus fournie, yeux retravaillés.
# v3 : tête plus grande et sculptée (nez de félin, sourcils dorés en volutes, barbichette, joues, rides du museau).
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
    "Pupils": ("#17120E", "SmoothPlastic"),    # pupilles fendues
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

    # Poche sous l'œil : 2 plis superposés en croissant, posés sur la peau.
    for k, (dy, r) in enumerate(((0.36, 0.085), (0.56, 0.07))):
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
    (4.25, -0.04, 1.03, 0.79, 0.76),
    (4.45, -0.05, 0.99, 0.77, 0.74),   # bord de la face avant du museau (la truffe est sculptée dedans)
]
NOSE_X = 4.45     # x du bord de la face avant
SIDES_HEAD = 32   # côtés du crâne (multiple de 4 : sommets pile sur le dessus, le dessous et les côtés)
SUPER = 2.6   # > 2 : section plus carrée, joues pleines
EYE = (1.5, 0.5)  # centre de l'œil (x, y) dans le repère de la tête


FOLDS = (2.93, 3.32, 3.7)   # crêtes des plis du chanfrein
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
    # Coussinets de lèvre : leur bord extérieur déborde un peu sur les côtés du museau.
    d += 0.16 * gauss(np.hypot((x - 4.1) / 0.4, (y + 0.4) / 0.3)) * side_w
    # Chanfrein : 3 plis en travers (bourrelet suivi d'un creux), qui s'estompent sur les côtés.
    for xc in FOLDS:
        d += (0.075 * gauss((x - xc) / 0.06) - 0.055 * gauss((x - xc + 0.1) / 0.06)) * top_w
    return d


def skull_section(x):
    xs = [r[0] for r in SKULL]
    return [np.interp(x, xs, [r[k] for r in SKULL]) for k in (1, 2, 3, 4)]


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
    return np.array([x, yc + y + ny * d, z + nz * d])


def skin_normal(x, t):
    p = skull_point(x, t)
    n = np.cross(skull_point(x + 0.04, t) - skull_point(x - 0.04, t), skull_point(x, t + 0.04) - skull_point(x, t - 0.04))
    n = normalize(n)
    c = np.array([x, skull_section(x)[0], 0.0])
    return n if n @ (p - c) > 0 else -n


# ---------- face avant du museau : truffe, narines, coussinets ----------
# Coordonnées normalisées de la face avant : u de -1 (côté droit) à 1 (côté gauche), v de -1 (bas) à 1 (haut).
NOSTRIL = (0.37, 0.33, 0.23)   # centre u, v et rayon des narines


def nose_shape(u, v, r):
    """Avancée (en studs) de la face avant au point (u, v) ; r = 0 au centre, 1 sur le bord.
    Renvoie aussi la distance normalisée au centre de la narine la plus proche (< 1 : dans la narine)."""
    nu, nv, nr = NOSTRIL
    dome = 0.26 * np.sqrt(max(0.0, 1 - r * r))                       # museau arrondi, pas pointu
    # Truffe : une seule masse ovale, large et bombée (plus large que haute), en haut de la face.
    feat = 0.3 * gauss(np.hypot(u / 0.66, (v - 0.32) / 0.42))
    # Coussinets de lèvre : une masse plus basse, gonflée, sous la truffe.
    feat += 0.24 * gauss(np.hypot(u / 0.72, (v + 0.52) / 0.32))
    # Sillon vertical au milieu : coupe la truffe en 2 lobes et descend entre les 2 coussinets.
    feat -= 0.24 * gauss(u / 0.1) * smoothstep(-1.05, -0.85, v) * (1 - smoothstep(0.75, 0.98, v))
    # Narines rondes : bourrelet épais autour, creux profond dedans.
    dn = min(np.hypot(u - nu, v - nv), np.hypot(u + nu, v - nv)) / nr
    # Naseaux creusés vers l'intérieur : à peine un rebord, et un trou profond à parois raides.
    feat += 0.03 * gauss((dn - 1.15) / 0.4)
    feat -= 0.55 * max(0.0, 1 - dn * dn) ** 0.45
    return dome + feat * (1 - smoothstep(0.7, 1.0, r)), dn


def unit_dir(t):
    ct, st = np.cos(t), np.sin(t)
    return np.sign(ct) * abs(ct) ** (2 / SUPER), np.sign(st) * abs(st) ** (2 / SUPER)


def front_point(t, r):
    """Point de la face avant : anneau de rayon r (1 = bord, 0 = centre) à l'angle t. Renvoie (point, dn)."""
    yc = skull_section(NOSE_X)[0]
    rim = skull_point(NOSE_X, t)
    un, vn = unit_dir(t)
    dx, dn = nose_shape(r * un, r * vn, r)
    return np.array([NOSE_X + dx, yc + (rim[1] - yc) * r, rim[2] * r]), dn


def front_point_uv(u, v):
    """Même chose à partir de (u, v) : sert à poser les moustaches sur les coussinets."""
    r = (abs(u) ** SUPER + abs(v) ** SUPER) ** (1 / SUPER)
    t = np.arctan2(np.sign(v) * abs(v / r) ** (SUPER / 2), np.sign(u) * abs(u / r) ** (SUPER / 2))
    return front_point(t, r)[0]


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

    def on_skin(x, y, side, lift=0.04):
        return P(x, y, side * (skull_side(x, y) + lift))

    # Crâne + museau d'un seul tenant : les côtés, puis la face avant en anneaux concentriques jusqu'au bout
    # du nez. Truffe, sillon, narines et coussinets sont sculptés dans cette même peau (rien de collé).
    xs = np.concatenate([np.linspace(-1.4, 0.6, 3), np.linspace(0.85, 2.3, 10),
                         [2.65, 2.83, 2.93, 3.08, 3.22, 3.32, 3.47, 3.6, 3.7, 4.0, 4.25, NOSE_X]])
    angs = np.arange(SIDES_HEAD) * 2 * np.pi / SIDES_HEAD
    rings = [np.array([P(*skull_point(x, t)) for t in angs]) for x in xs]
    dns = [np.full(SIDES_HEAD, 9.0) for _ in xs]
    # Anneaux plus serrés à la hauteur des narines, pour qu'elles restent bien rondes.
    for rr in (0.96, 0.88, 0.79, 0.71, 0.64, 0.57, 0.5, 0.43, 0.36, 0.28, 0.18, 0.08):
        pts = [front_point(t, rr) for t in angs]
        rings.append(np.array([P(*p) for p, _ in pts]))
        dns.append(np.array([d for _, d in pts]))
    tip, _ = front_point(0.0, 0.0)
    rings.append(P(*tip)[None])
    dns.append(np.array([0.0 if abs(NOSTRIL[0]) < NOSTRIL[2] else 9.0]))
    verts, faces = loft(rings)
    dn = np.concatenate(dns + [[9.0]])                       # + centre du bouchon arrière
    # L'intérieur des narines (le creux) prend la couleur sombre des pupilles.
    inside = dn[faces].max(axis=1) < 0.95
    a.add_split(verts, faces, np.where(inside, "Pupils", "Body"))

    def head_scale(x, t, size):
        """Petite écaille en losange posée sur la peau, la pointe vers l'arrière de la tête."""
        p0 = skull_point(x, t)
        dxp = skull_point(x + 0.05, t) - skull_point(x - 0.05, t)
        dtp = skull_point(x, t + 0.05) - skull_point(x, t - 0.05)
        nrm = normalize(np.cross(dxp, dtp))
        if nrm[1] < 0:
            nrm = -nrm
        back, side_v = np.array([-1.0, 0, 0]), normalize(dtp)
        L, W, H = size * 1.5, size * 1.1, size * 0.45
        sink = -nrm * size * 0.25
        loc = [p0 - back * L * 0.45 + sink, p0 + side_v * W / 2 + sink, p0 + back * L * 0.55 + sink,
               p0 - side_v * W / 2 + sink, p0 + back * L * 0.25 + nrm * H]
        a.add("Body", [P(*q) for q in loc], [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2), (0, 2, 1)])

    # Petites écailles sur le chanfrein, de plus en plus petites, qui disparaissent avant la truffe.
    for x, n, size in ((1.95, 4, 0.2), (2.25, 3, 0.17), (2.55, 4, 0.13), (2.78, 3, 0.1), (3.15, 2, 0.07), (3.52, 2, 0.045)):
        for k in range(n):
            head_scale(x, np.pi / 2 + (k - (n - 1) / 2) * 0.32, size)

    # Front au-dessus des arcades : écailles en losange qui se chevauchent, en quinconce.
    for row, x in enumerate(np.arange(-0.35, 1.75, 0.21)):
        offs = np.arange(-4, 5) * 0.17 + (0.085 if row % 2 else 0.0)
        for dt in offs:
            t = np.pi / 2 + dt
            if abs(dt) > 0.72:
                continue
            bp = base_point(x, t)
            if brow_bump(*bp) > 0.06 or (0.75 < x < 1.75 and abs(dt) < 0.2):   # pas sur l'arcade ni la marque dorée
                continue
            if min(np.linalg.norm(bp - np.array([-0.1, 1.5, 0.7])), np.linalg.norm(bp - np.array([-0.1, 1.5, -0.7]))) < 0.45:
                continue                                                         # pas sur la base des cornes
            head_scale(x, t, 0.19)

    # Mâchoire du bas, entrouverte de 20°.
    hinge = np.array([0.4, -0.55])
    c, sn = np.cos(-0.35), np.sin(-0.35)

    def jaw_ring(x, y, w, h, n=8):
        ang = np.pi / n + np.arange(n) * 2 * np.pi / n
        out = []
        for t in ang:
            px, py = x - hinge[0], y + np.sin(t) * h - hinge[1]
            out.append(P(hinge[0] + px * c - py * sn, hinge[1] + px * sn + py * c, np.cos(t) * w))
        return np.array(out)

    def jaw_point(x, y, z):
        px, py = x - hinge[0], y - hinge[1]
        return P(hinge[0] + px * c - py * sn, hinge[1] + px * sn + py * c, z)

    jaw = [jaw_ring(0.2, -0.85, 1.25, 0.42), jaw_ring(1.6, -0.95, 1.08, 0.36), jaw_ring(3.0, -0.95, 0.95, 0.32),
           jaw_ring(3.8, -0.92, 0.82, 0.32), jaw_ring(4.15, -0.95, 0.5, 0.25)]
    a.add("Body", *loft(jaw))
    a.add("Belly", *loft([jaw_ring(0.4, -1.08, 1.02, 0.25), jaw_ring(3.7, -1.12, 0.62, 0.2)]))
    # Lèvre du haut en bourrelet, qui remonte au coin de la gueule.
    for side in (1, -1):
        lip = [P(0.5, -0.25, 1.45 * side), P(1.2, -0.6, 1.35 * side), P(2.2, -0.75, 1.2 * side),
               P(3.2, -0.78, 1.1 * side), P(3.9, -0.72, 0.95 * side)]
        a.add("Body", *tube(catmull_rom(lip, 9), [0.06, 0.12, 0.15, 0.16, 0.16, 0.15, 0.14, 0.12, 0.05], 5))
        low = [jaw_point(x, -0.62, w * side) for x, w in ((0.9, 1.15), (2.0, 1.02), (3.0, 0.92), (3.9, 0.72))]
        a.add("Body", *tube(low, [0.05, 0.1, 0.1, 0.04], 5))

    # Dents : crocs en haut, plus petites dents, et 2 crocs en bas.
    for x, z, L in ((3.85, 0.85, 0.8), (3.35, 0.98, 0.35), (2.85, 1.05, 0.32), (2.3, 1.12, 0.3)):
        for side in (1, -1):
            top = P(x, -0.7, z * side)
            a.add("Horns", *tube([top, P(x + 0.05, -0.7 - L * 0.6, z * side * 0.97), P(x + 0.12, -0.7 - L, z * side * 0.95)],
                                 [0.14 if L > 0.5 else 0.09, 0.07, 0.0], 4))
    for side in (1, -1):
        b0 = jaw_point(3.55, -0.65, 0.66 * side)
        a.add("Horns", *tube([b0, b0 + u * 0.38 * S, b0 + u * 0.65 * S - f * 0.05], [0.13, 0.07, 0.0], 4))

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
        pts = [P(*front_point_uv(0.66 * side, -0.48)), P(3.9, -0.35, 2.2 * side), P(2.8, -0.8, 3.4 * side),
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
        b0 = jaw_point(3.7 - abs(z) * 0.5, -1.1, z)
        rel = ((0, 0), (-0.1, -0.6), (-0.45, -1.3), (-1.05, -1.85), (-1.7, -1.95), (-2.1, -1.65), (-1.95, -1.35))
        pts = [b0 + (f * dx * L + u * dy * L + s * z * 0.4 * min(1, -dy)) * S for dx, dy in rel]
        line = catmull_rom(pts, 14)
        radii = [r * np.sin(np.pi * (0.15 + 0.85 * k / 13)) ** 0.6 for k in range(14)]
        radii[-1] = 0.0
        a.add("Fins", *tube(line, radii, 6, up=s, flat=0.45))



def build():
    a = Asset("Dragon_Long_v6")
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
