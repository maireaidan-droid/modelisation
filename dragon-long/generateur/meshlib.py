# Petite bibliothèque de formes low-poly à facettes, pour générer des modèles Roblox sans Blender.
# Repère Roblox : Y vers le haut, 1 unité = 1 stud.
import numpy as np


def hex_to_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def normalize(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


class Asset:
    """Un modèle composé de parties (une par couleur/matériau, comme dans Roblox)."""

    def __init__(self, name):
        self.name = name
        self.parts = {}

    def part(self, name, color, material="SmoothPlastic"):
        self.parts.setdefault(name, {"color": color, "material": material, "v": [], "f": []})

    def add(self, part_name, verts, faces):
        """Ajoute un volume fermé ; l'orientation des faces est corrigée pour qu'elles regardent vers l'extérieur."""
        verts = np.asarray(verts, float)
        faces = np.asarray(faces, int)
        a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
        if np.einsum("ij,ij->i", a, np.cross(b, c)).sum() < 0:
            faces = faces[:, ::-1]
        p = self.parts[part_name]
        base = len(p["v"])
        p["v"].extend(verts.tolist())
        p["f"].extend((faces + base).tolist())

    def tri_count(self):
        return sum(len(p["f"]) for p in self.parts.values())

    def bounds(self):
        allv = np.array([v for p in self.parts.values() for v in p["v"]])
        return allv.min(0), allv.max(0)


# ---------- courbes ----------

def catmull_rom(points, samples):
    """Courbe lisse qui passe par tous les points de contrôle."""
    P = np.asarray(points, float)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    segs = len(P) - 3
    out = []
    for s in np.linspace(0, segs, samples, endpoint=True):
        i = min(int(s), segs - 1)
        t = s - i
        p0, p1, p2, p3 = P[i:i + 4]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)


def frames(points, up=(0, 1, 0)):
    """Repère qui suit la courbe sans vriller (transport parallèle) : tangente T, dessus N, côté B."""
    pts = np.asarray(points, float)
    T = np.gradient(pts, axis=0)
    T = np.array([normalize(t) for t in T])
    N = [normalize(np.asarray(up) - np.dot(up, T[0]) * T[0])]
    for i in range(1, len(T)):
        n = N[-1] - np.dot(N[-1], T[i]) * T[i]
        N.append(normalize(n))
    N = np.array(N)
    B = np.cross(T, N)
    return T, N, B


# ---------- volumes ----------

def loft(rings, cap_start=True, cap_end=True):
    """Relie des anneaux de même taille. Un anneau d'un seul point fait une pointe."""
    verts, idx = [], []
    for r in rings:
        r = np.atleast_2d(r)
        idx.append(list(range(len(verts), len(verts) + len(r))))
        verts.extend(r.tolist())
    faces = []
    for a, b in zip(idx[:-1], idx[1:]):
        if len(a) == 1:
            faces += [(a[0], b[(k + 1) % len(b)], b[k]) for k in range(len(b))]
        elif len(b) == 1:
            faces += [(a[k], a[(k + 1) % len(a)], b[0]) for k in range(len(a))]
        else:
            n = len(a)
            for k in range(n):
                k2 = (k + 1) % n
                faces += [(a[k], a[k2], b[k2]), (a[k], b[k2], b[k])]
    for cap, ring_idx, flip in ((cap_start, idx[0], True), (cap_end, idx[-1], False)):
        if cap and len(ring_idx) > 2:
            c = len(verts)
            verts.append(np.mean([verts[i] for i in ring_idx], axis=0).tolist())
            n = len(ring_idx)
            for k in range(n):
                f = (c, ring_idx[k], ring_idx[(k + 1) % n])
                faces.append(f[::-1] if flip else f)
    return np.array(verts), np.array(faces)


def ellipse_ring(center, ax_u, ax_v, ru, rv, sides, angle0=0.0):
    a = angle0 + np.arange(sides) * 2 * np.pi / sides
    return (np.asarray(center) + np.outer(np.cos(a) * ru, ax_u) + np.outer(np.sin(a) * rv, ax_v))


def tube(points, radii, sides=6, tip=True, up=(0, 1, 0), flat=1.0):
    """Tube le long d'une ligne ; si un rayon d'extrémité est 0 et tip=True, il finit en pointe.
    flat < 1 aplatit le tube dans la direction « up » (ruban : mèches, sourcils)."""
    pts = np.asarray(points, float)
    T, N, B = frames(pts, up)
    rings = []
    for p, r, n, b in zip(pts, radii, N, B):
        rings.append(p[None] if (tip and r <= 1e-6) else ellipse_ring(p, b, n, r, r * flat, sides, np.pi / sides))
    return loft(rings)


def blob(center, ax_f, ax_u, ax_s, rf, ru, rs, sides=8, rows=4):
    """Ellipsoïde low-poly (joues, coussinets du museau)."""
    c = np.asarray(center, float)
    rings = [c - ax_f * rf]
    for k in range(1, rows):
        t = -np.pi / 2 + k * np.pi / rows
        rings.append(ellipse_ring(c + ax_f * rf * np.sin(t), ax_s, ax_u, rs * np.cos(t), ru * np.cos(t), sides))
    rings.append(c + ax_f * rf)
    return loft(rings)


def fin(a, b, tip, normal, thickness=0.15):
    """Nageoire / épine plate : un triangle épaissi."""
    off = normalize(normal) * thickness / 2
    tri = np.array([a, b, tip], float)
    verts = np.vstack([tri + off, tri - off])
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4), (0, 4, 1), (1, 4, 5), (1, 5, 2), (2, 5, 3), (2, 3, 0)]
    return verts, np.array(faces)


def gem(center, fwd, up, side, lf, lu, ls):
    """Octaèdre aplati (œil, pierre)."""
    c = np.asarray(center, float)
    v = [c + fwd * lf, c - fwd * lf, c + up * lu, c - up * lu, c + side * ls, c - side * ls]
    faces = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    return np.array(v), np.array(faces)


# ---------- export ----------

def export_glb(asset, path_glb):
    """GLB : un nœud par partie (nommé), couleur en matériau PBR, sommets non partagés = rendu à facettes."""
    import trimesh
    from trimesh.visual.material import PBRMaterial
    scene = trimesh.Scene()
    for pname, p in asset.parts.items():
        v = np.array(p["v"], float)
        f = np.array(p["f"], int)
        fv = v[f].reshape(-1, 3)
        faces = np.arange(len(fv)).reshape(-1, 3)
        rgb = hex_to_rgb(p["color"])
        neon = p["material"] == "Neon"
        mat = PBRMaterial(name=f"{asset.name}_{pname}", baseColorFactor=rgb + [1.0], metallicFactor=0.0,
                          roughnessFactor=0.9, emissiveFactor=rgb if neon else None)
        m = trimesh.Trimesh(fv, faces, process=False)
        m.visual = trimesh.visual.TextureVisuals(material=mat)
        scene.add_geometry(m, node_name=pname, geom_name=pname)
    with open(path_glb, "wb") as fh:
        fh.write(scene.export(file_type="glb", include_normals=True))
