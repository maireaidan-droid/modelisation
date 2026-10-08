# Dragon Long (dragon chinois) stylisé, low-poly.
# v1 : premier croquis. v2 : écailles en relief sur le dos, plaques sur le ventre, crête plus fournie, yeux retravaillés.
# Corps de serpent en S, ventre doré, crinière et nageoires rouges, cornes en bois de cerf,
# moustaches, 4 pattes à 3 griffes. Repère Roblox : Y en haut, 1 unité = 1 stud, la tête regarde vers +Z.
import numpy as np
from meshlib import Asset, catmull_rom, frames, loft, ellipse_ring, tube, fin, gem, normalize

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
    c = P(1.5, 0.5, 1.52 * sd)
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

    # Arcade en relief au-dessus de l'œil, et 2 mèches rouges vers l'arrière.
    brow = [P(2.25, 0.95, 1.2 * sd), P(1.6, 1.2, 1.45 * sd), P(0.8, 1.3, 1.5 * sd), P(0.1, 1.15, 1.4 * sd)]
    a.add("Body", *tube(brow, [0.12, 0.26, 0.26, 0.12], 6))
    for x0, h in ((1.4, 0.9), (0.6, 1.15)):
        a.add("Fins", *fin(P(x0 + 0.4, 1.3, 1.45 * sd), P(x0 - 0.4, 1.3, 1.5 * sd),
                           P(x0 - 1.2, 1.3 + h, 1.85 * sd), normalize(side_v - u * 0.3), 0.14))


def build_head(a, neck, neck_r):
    """Tête construite dans un repère local (x vers l'avant, y en haut, z sur le côté), puis placée sur la nuque."""
    S = 1.15
    f = normalize(np.array([0.0, 0.12, 1.0]))
    u = normalize(np.array([0.0, 1.0, 0.0]) - f[1] * f)
    s = np.cross(u, f)
    origin = np.asarray(neck) + f * 0.6

    def P(x, y, z):
        return origin + (f * x + u * y + s * z) * S

    def ring(x, y, w, h, n=8):
        ang = np.pi / n + np.arange(n) * 2 * np.pi / n
        return np.array([P(x, y + np.sin(t) * h, np.cos(t) * w) for t in ang])

    # Crâne + museau (le nez des dragons chinois est large et bombé).
    rings = [ring(-1.4, 0.15, 1.15, 1.2), ring(0.0, 0.35, 1.7, 1.55), ring(1.3, 0.4, 1.65, 1.35),
             ring(2.3, 0.05, 1.25, 0.95), ring(3.3, -0.1, 1.15, 0.78), ring(4.1, -0.02, 1.38, 0.82),
             ring(4.65, -0.12, 0.85, 0.5)]
    a.add("Body", *loft(rings))

    # Mâchoire du bas, entrouverte de 20°.
    hinge = np.array([0.4, -0.55])
    c, sn = np.cos(-0.35), np.sin(-0.35)

    def jaw_ring(x, y, w, h, n=6):
        ang = np.pi / n + np.arange(n) * 2 * np.pi / n
        out = []
        for t in ang:
            px, py = x - hinge[0], y + np.sin(t) * h - hinge[1]
            out.append(P(hinge[0] + px * c - py * sn, hinge[1] + px * sn + py * c, np.cos(t) * w))
        return np.array(out)

    jaw = [jaw_ring(0.3, -0.85, 1.2, 0.4), jaw_ring(1.6, -0.95, 1.05, 0.33), jaw_ring(3.0, -0.95, 0.9, 0.28),
           jaw_ring(3.9, -0.9, 0.75, 0.25)]
    a.add("Body", *loft(jaw))
    a.add("Belly", *loft([jaw_ring(0.4, -1.05, 1.0, 0.25), jaw_ring(3.6, -1.08, 0.6, 0.2)]))

    def jaw_point(x, y, z):
        px, py = x - hinge[0], y - hinge[1]
        return P(hinge[0] + px * c - py * sn, hinge[1] + px * sn + py * c, z)

    # Dents : crocs en haut, plus petites dents, et 2 crocs en bas.
    for x, z, L in ((3.9, 0.95, 0.75), (3.0, 0.95, 0.35), (2.4, 1.05, 0.35)):
        for side in (1, -1):
            top = P(x, -0.62, z * side)
            a.add("Horns", *tube([top, P(x + 0.05, -0.62 - L * 0.6, z * side * 0.97), P(x + 0.1, -0.62 - L, z * side * 0.95)],
                                 [0.13 if L > 0.5 else 0.09, 0.07, 0.0], 4))
    for side in (1, -1):
        b0 = jaw_point(3.6, -0.7, 0.62 * side)
        a.add("Horns", *tube([b0, b0 + u * 0.35 * S, b0 + u * 0.6 * S - f * 0.05], [0.12, 0.07, 0.0], 4))

    # Yeux : amande dorée qui brille, pupille fendue, paupière du haut qui donne le regard
    # (entre mignon et féroce), arcade en relief et 2 petites mèches rouges au-dessus.
    for side in (1, -1):
        build_eye(a, P, f, u, s * side, S)

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

    # Moustaches longues et ondulées.
    for side in (1, -1):
        pts = [P(4.1, -0.15, 1.2 * side), P(3.9, -0.3, 2.2 * side), P(2.8, -0.75, 3.4 * side),
               P(1.0, -0.4, 4.3 * side), P(-0.9, -1.0, 4.9 * side), P(-2.8, -0.6, 5.3 * side)]
        a.add("Whiskers", *tube(catmull_rom(pts, 14), np.linspace(0.16, 0.0, 14), 4))

    # Crinière en flammes autour de la nuque + barbe sous la mâchoire.
    for ang in np.linspace(np.radians(-150), np.radians(150), 11):
        rad = np.array([0, np.cos(ang), np.sin(ang)])  # 0° = vers le haut
        base_a = P(0.2, 0.3 + rad[1] * 1.3, rad[2] * 1.4)
        base_b = P(-1.1, 0.2 + rad[1] * 1.1, rad[2] * 1.15)
        length = 2.6 if abs(ang) < 1.6 else 1.9
        tip = P(-1.1 - length, 0.3 + rad[1] * (1.1 + length * 0.75), rad[2] * (1.15 + length * 0.75))
        normal = np.cross(tip - base_a, base_b - base_a)
        a.add("Fins", *fin(base_a, base_b, tip, normal, 0.14))
    for k, x in enumerate((0.6, 1.3, 2.0)):
        base_a, base_b = jaw_point(x, -1.2, 0.0), jaw_point(x + 0.7, -1.2, 0.0)
        a.add("Fins", *fin(base_a, base_b, jaw_point(x - 0.4, -2.3 + k * 0.25, 0.0), s, 0.12))


def build():
    a = Asset("Dragon_Long_v2")
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
