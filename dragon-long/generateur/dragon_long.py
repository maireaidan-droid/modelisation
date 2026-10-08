# Dragon Long (dragon chinois) stylisé, low-poly.
# v1 : premier croquis. v2 : écailles en relief sur le dos, plaques sur le ventre, crête plus fournie, yeux retravaillés.
# v3 : tête plus grande et sculptée (nez de félin, sourcils dorés en volutes, barbichette, joues, rides du museau).
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
    sd = 1 if side_v @ np.cross(u, f) > 0 else -1
    ex, ey = EYE
    c = P(ex, ey, (skull_side(ex, ey) + 0.02) * sd)              # posé au fond de l'orbite
    out = normalize(side_v + f * 0.45 + u * 0.1)              # l'œil regarde un peu vers l'avant
    e1 = normalize(f - out * (f @ out) - u * 0.22)            # grand axe, coin arrière relevé
    e2 = normalize(np.cross(out, e1))
    if e2 @ u < 0:
        e2 = -e2
    L, Hh, D = 0.55 * S, 0.33 * S, 0.2 * S

    # Amande : anneaux le long du grand axe.
    rings = [c - e1 * L]
    for x, k in ((-0.55, 0.75), (0.0, 1.0), (0.55, 0.75)):
        ang = np.arange(8) * np.pi / 4
        rings.append(np.array([c + e1 * L * x + e2 * np.sin(t) * Hh * k + out * np.cos(t) * D * k for t in ang]))
    rings.append(c + e1 * L)
    a.add("Eyes", *loft(rings))

    # Pupille fendue, verticale, posée sur l'œil.
    a.add("Pupils", *gem(c + out * D * 0.95 + e1 * L * 0.1, e1, e2, out, 0.075 * S, Hh * 0.85, 0.06 * S))

    # Paupière du haut : bourrelet qui couvre le tiers supérieur, plus lourd vers l'arrière.
    lid = [c + e1 * L * x + e2 * Hh * (0.55 + 0.25 * (1 - abs(x))) + out * D * (0.35 + 0.4 * (1 - abs(x)))
           - e2 * Hh * 0.25 * max(0.0, -x)
           for x in np.linspace(-1.15, 1.1, 7)]
    a.add("Body", *tube(lid, [0.06, 0.15, 0.2, 0.2, 0.17, 0.12, 0.05], 6, up=out))
    # Petite paupière du bas.
    low = [c + e1 * L * x - e2 * Hh * (0.8 + 0.1 * abs(x)) + out * D * 0.4 for x in np.linspace(-0.9, 0.8, 5)]
    a.add("Body", *tube(low, [0.03, 0.08, 0.09, 0.07, 0.02], 5, up=out))



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
SUPER = 2.6   # > 2 : section plus carrée, joues pleines
EYE = (1.5, 0.5)  # centre de l'œil (x, y) dans le repère de la tête


def gauss(v):
    return np.exp(-v * v)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def relief(x, y, side_w, top_w=0.0):
    """Bosses et creux sculptés dans la peau du crâne (en studs, vers l'extérieur).
    side_w : 1 sur le côté de la tête, 0 dessus/dessous (les orbites ne creusent que les côtés).
    top_w : 1 sur le dessus (arête du nez)."""
    ex, ey = EYE
    d = 0.0
    # Orbite : creux en amande autour de l'œil, et arcade sourcilière en bourrelet au-dessus.
    d -= 0.38 * gauss(np.hypot((x - ex) / 0.62, (y - ey) / 0.42)) * side_w
    d += 0.22 * gauss(np.hypot((x - ex - 0.1) / 0.8, (y - ey - 0.58) / 0.2)) * side_w
    # Pommette sous l'orbite, qui file vers l'arrière.
    d += 0.1 * gauss(np.hypot((x - ex + 0.4) / 0.9, (y - ey + 0.62) / 0.22)) * side_w
    # Coussinets des moustaches, gonflés de chaque côté du museau (comme un tigre).
    d += 0.3 * gauss(np.hypot((x - 4.05) / 0.5, (y + 0.3) / 0.36)) * side_w
    # Arête du nez : léger creux, puis la truffe qui se relève au bout.
    d -= 0.07 * gauss((x - 4.0) / 0.22) * top_w
    d += 0.12 * gauss((x - 4.5) / 0.22) * top_w
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
    d = relief(x, yc + y, abs(nz) ** 1.5, max(0.0, ny) ** 2)
    # Avant du museau : la truffe déborde en haut, les coussinets avancent, le sillon recule au milieu.
    front = smoothstep(4.0, 4.72, x)
    dx = 0.3 * front * max(0.0, st) ** 1.3
    dx += 0.14 * front * np.clip(-st * abs(ct) * 2.2, 0, 1)
    dx -= 0.18 * front * gauss(ct / 0.22) * max(0.0, -st)
    return np.array([x + dx, yc + y + ny * d, z + nz * d])


def skull_side(x, y):
    """Demi-largeur du crâne (relief compris) à l'avant-arrière x et à la hauteur y."""
    yc, w, ht, hb = skull_section(x)
    h = ht if y >= yc else hb
    v = min(abs(y - yc) / h, 0.999)
    z = w * (1 - v ** SUPER) ** (1 / SUPER)
    return z + relief(x, y, (1 - v) ** 0.5)


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

    # Crâne + museau d'un seul tenant (truffe, coussinets, sillon et orbites sculptés dans la même peau).
    xs = np.concatenate([np.linspace(-1.4, 0.6, 5), np.linspace(0.85, 2.3, 8), np.linspace(2.6, 3.8, 4),
                         np.linspace(3.95, 4.72, 7)])
    angs = np.pi / 24 + np.arange(24) * 2 * np.pi / 24
    a.add("Body", *loft([np.array([P(*skull_point(x, t)) for t in angs]) for x in xs]))

    # Narines en virgule, creusées dans le haut de la truffe.
    for side in (1, -1):
        rim = skull_point(4.72, np.pi / 2 - side * 0.9)
        n0 = P(*(rim * 0.72 + np.array([4.86, 0.05, 0.0]) * 0.28))
        a.add("Pupils", *gem(n0, normalize(f * 0.9 + s * side * 0.3), u, normalize(s * side - f * 0.3),
                             0.09 * S, 0.12 * S, 0.2 * S))

    # Rides du chanfrein (le « grognement » des félins) : 3 bourrelets en arc sur le museau.
    for x in (2.55, 2.95, 3.35):
        arc = [P(x + 0.06 * abs(np.cos(t)), skull_top(x) * np.sin(t) * 0.97 + 0.02 * (1 - np.sin(t)),
                 skull_side(x, 0.3) * np.cos(t) * 0.92) for t in np.linspace(np.radians(35), np.radians(145), 7)]
        a.add("Body", *tube(arc, [0.0, 0.07, 0.1, 0.11, 0.1, 0.07, 0.0], 5))

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

    # Sourcils dorés gracieux : une volute devant l'œil, puis une longue mèche qui passe au-dessus
    # et file vers l'arrière, avec 2 petites flammes qui s'en échappent.
    for side in (1, -1):
        cx, cy = 2.45, 1.05
        spiral = []
        for k, th in enumerate(np.linspace(-np.pi / 2 + 2.3 * np.pi, -np.pi / 2, 12)):
            rho = 0.08 + 0.34 * k / 11
            x, y = cx + rho * np.cos(th), cy + rho * np.sin(th)
            spiral.append(on_skin(x, y, side, 0.06 + 0.05 * k / 11))
        sweep = [on_skin(x, y, side, lift) for x, y, lift in
                 ((2.1, 0.8, 0.1), (1.7, 1.05, 0.12), (1.1, 1.35, 0.12), (0.4, 1.55, 0.12), (-0.4, 1.7, 0.15))]
        sweep += [P(-1.3, 1.8, (skull_side(-1.3, 1.0) + 0.35) * side), P(-2.2, 2.0, 1.95 * side),
                  P(-3.0, 2.35, 2.25 * side), P(-3.4, 2.7, 2.3 * side), P(-3.2, 2.95, 2.2 * side)]
        line = np.vstack([spiral, catmull_rom(sweep, 16)[1:]])
        n = len(line)
        radii = [0.07 + 0.17 * min(1.0, k / 10) * (1 - max(0, k - 12) / (n - 12)) ** 0.8 for k in range(n)]
        radii[-1] = 0.0
        a.add("Whiskers", *tube(line, radii, 6, up=s * side, flat=0.45))
        for x0, y0, L in ((1.2, 1.3, 0.9), (0.2, 1.45, 1.15)):
            b0 = on_skin(x0, y0, side, 0.12)
            tuft = [b0, b0 + (-f * 0.35 + u * 0.45 + s * side * 0.1) * S * L, b0 + (-f * 0.95 + u * 0.75 + s * side * 0.2) * S * L,
                    b0 + (-f * 1.5 + u * 0.7 + s * side * 0.25) * S * L, b0 + (-f * 1.75 + u * 0.45 + s * side * 0.25) * S * L]
            a.add("Whiskers", *tube(catmull_rom(tuft, 8), [0.15, 0.15, 0.13, 0.11, 0.08, 0.06, 0.03, 0.0], 5,
                                    up=s * side, flat=0.5))

    # Front : marque dorée en losange entre les yeux, et deux arêtes qui montent vers les cornes.
    a.add("Whiskers", *gem(P(1.25, skull_top(1.25) + 0.02, 0), f, u, s, 0.45 * S, 0.1 * S, 0.24 * S))
    for side in (1, -1):
        ridge = [P(2.0, skull_top(2.0) - 0.02, 0.35 * side), P(1.1, skull_top(1.1) + 0.02, 0.55 * side),
                 P(0.1, skull_top(0.1) - 0.02, 0.7 * side)]
        a.add("Body", *tube(ridge, [0.05, 0.13, 0.12], 5, tip=False))

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
        pts = [P(4.1, -0.25, 1.05 * side), P(3.9, -0.35, 2.2 * side), P(2.8, -0.8, 3.4 * side),
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
    a = Asset("Dragon_Long_v4")
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
