# Exporte le dragon AVEC son squelette (os + poids de peau) en .glb, pour l'animer dans Roblox.
# Même géométrie et mêmes couleurs que le modèle statique ; chaque sommet suit 1 à 4 os.
# Usage : python build_rig.py [variante]   (variantes : glace, celeste ; rien = forme de base)
import json
import os
import struct
import numpy as np

from meshlib import hex_to_rgb
from dragon_long import build, SPINE_BONES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "objets")


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def spine_weights(v, pts):
    """Corps, crête, queue : on cherche le point de la colonne le plus proche et on mélange les 2 os voisins."""
    i = int(np.argmin(np.linalg.norm(pts - v, axis=1)))
    ctrl = SPINE_BONES
    if i >= ctrl[-1][0]:
        return {ctrl[-1][1]: 1.0}
    for (i0, b0), (i1, b1) in zip(ctrl[:-1], ctrl[1:]):
        if i0 <= i <= i1:
            w = (i - i0) / (i1 - i0)
            return {b0: 1 - w, b1: w}


def seg_param(p, a, b):
    ab = b - a
    t = float(np.clip((p - a) @ ab / (ab @ ab), 0, 1))
    return t, float(np.linalg.norm(p - (a + ab * t)))


def leg_weights(v, g):
    hip, elbow, wrist, foot = [np.asarray(q) for q in g["poly"]]
    name = g["leg"]
    t0, d0 = seg_param(v, hip, elbow)
    t1, d1 = seg_param(v, elbow, wrist)
    t2, d2 = seg_param(v, wrist, foot)
    k = int(np.argmin([d0, d1 - 0.05, d2 - 0.15]))     # doigts et griffes : plus loin que le pied, vont au pied
    if k == 0:
        w = {name + "_Upper": 1.0}
        if t0 < 0.3:                                    # épaule : se fond dans le corps
            p = 0.5 * (1 - t0 / 0.3)
            w = {name + "_Upper": 1 - p, g["parent"]: p}
        elif t0 > 0.85:
            p = 0.5 * (t0 - 0.85) / 0.15
            w = {name + "_Upper": 1 - p, name + "_Fore": p}
        return w
    if k == 1:
        if t1 < 0.15:
            p = 0.5 + 0.5 * t1 / 0.15
            return {name + "_Upper": 1 - p, name + "_Fore": p}
        if t1 > 0.85:
            p = 0.5 * (t1 - 0.85) / 0.15
            return {name + "_Fore": 1 - p, name + "_Foot": p}
        return {name + "_Fore": 1.0}
    return {name + "_Foot": 1.0}


def vertex_weights(a, v, g):
    kind = g["kind"]
    if kind == "spine":
        return spine_weights(v, a.spine_pts)
    if kind == "leg":
        return leg_weights(v, g)
    if kind == "bone":
        return {g["bone"]: 1.0}
    if kind == "lock":
        q = smooth(0.0, 0.85, np.linalg.norm(v - g["base"]) / g["length"] * 2.0)
        return {g["parent"]: 1 - q, g["bone"]: q} if q > 1e-3 else {g["parent"]: 1.0}
    raise ValueError(kind)


def bone_order(bones):
    order, seen = [], set()

    def visit(n):
        if n in seen:
            return
        p = bones[n]["parent"]
        if p:
            visit(p)
        seen.add(n)
        order.append(n)
    for n in bones:
        visit(n)
    return order


def quat_from_matrix(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1.0) * 2
        return [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    i = int(np.argmax(np.diag(m)))
    j, k = (i + 1) % 3, (i + 2) % 3
    s = np.sqrt(1.0 + m[i, i] - m[j, j] - m[k, k]) * 2
    q = [0.0] * 4
    q[i] = 0.25 * s
    q[j] = (m[j, i] + m[i, j]) / s
    q[k] = (m[k, i] + m[i, k]) / s
    q[3] = (m[k, j] - m[j, k]) / s
    return q


def orthonormal(m):
    u, _, vt = np.linalg.svd(m)
    r = u @ vt
    if np.linalg.det(r) < 0:
        raise ValueError("repère d'os en miroir (main gauche) : il faut un repère direct")
    return r


class GLB:
    def __init__(self):
        self.bin = bytearray()
        self.views, self.accessors = [], []

    def add(self, arr, comp, typ, target=None, minmax=False):
        arr = np.ascontiguousarray(arr)
        while len(self.bin) % 4:
            self.bin.append(0)
        view = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": arr.nbytes}
        if target:
            view["target"] = target
        self.bin.extend(arr.tobytes())
        self.views.append(view)
        acc = {"bufferView": len(self.views) - 1, "componentType": comp, "count": len(arr), "type": typ}
        if minmax:
            acc["min"] = arr.min(0).tolist()
            acc["max"] = arr.max(0).tolist()
        self.accessors.append(acc)
        return len(self.accessors) - 1


def main(variant=""):
    a = build(variant)
    name = a.name + "_rig"
    # Même pivot que le modèle statique : posé à Y = 0, centré sur X/Z.
    mn, mx = a.bounds()
    shift = np.array([(mn[0] + mx[0]) / 2, mn[1], (mn[2] + mx[2]) / 2])

    order = bone_order(a.bones)
    index = {n: i for i, n in enumerate(order)}
    glob = {}
    nodes = []
    for n in order:
        b = a.bones[n]
        R = orthonormal(b["basis"])
        pos = b["pos"] - shift
        glob[n] = (R, pos)
        if b["parent"]:
            Rp, pp = glob[b["parent"]]
            lr, lt = Rp.T @ R, Rp.T @ (pos - pp)
        else:
            lr, lt = R, pos
        node = {"name": n, "translation": [float(x) for x in lt]}
        if not np.allclose(lr, np.eye(3)):
            node["rotation"] = [float(x) for x in quat_from_matrix(lr)]
        nodes.append(node)
    for n in order:
        p = a.bones[n]["parent"]
        if p:
            nodes[index[p]].setdefault("children", []).append(index[n])

    g = GLB()
    ibm = []
    for n in order:
        R, pos = glob[n]
        M = np.eye(4)
        M[:3, :3], M[:3, 3] = R, pos
        ibm.append(np.linalg.inv(M).T.reshape(-1))        # glTF : matrices en colonnes
    ibm_acc = g.add(np.array(ibm, np.float32), 5126, "MAT4")

    meshes, materials, mesh_nodes = [], [], []
    stats = {}
    for pname, p in a.parts.items():
        v = np.array(p["v"], float)
        f = np.array(p["f"], int)
        joints = np.zeros((len(v), 4), np.uint16)
        weights = np.zeros((len(v), 4), np.float32)
        for k, (vert, gid) in enumerate(zip(v, p["g"])):
            w = vertex_weights(a, vert, a.groups[gid])
            items = sorted(((x, bn) for bn, x in w.items() if x > 1e-4), reverse=True)[:4]
            tot = sum(x for x, _ in items)
            for j, (x, bn) in enumerate(items):
                joints[k, j] = index[bn]
                weights[k, j] = x / tot
        fv = (v[f] - shift).reshape(-1, 3).astype(np.float32)
        tri = fv.reshape(-1, 3, 3)
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        nrm = np.repeat(nrm, 3, axis=0).astype(np.float32)
        attrs = {
            "POSITION": g.add(fv, 5126, "VEC3", 34962, minmax=True),
            "NORMAL": g.add(nrm, 5126, "VEC3", 34962),
            "JOINTS_0": g.add(joints[f].reshape(-1, 4), 5123, "VEC4", 34962),
            "WEIGHTS_0": g.add(weights[f].reshape(-1, 4), 5126, "VEC4", 34962),
        }
        rgb = hex_to_rgb(p["color"])
        mat = {"name": f"{name}_{pname}", "pbrMetallicRoughness": {"baseColorFactor": rgb + [1.0],
               "metallicFactor": 0.0, "roughnessFactor": 0.9}}
        if p["material"] == "Neon":
            mat["emissiveFactor"] = rgb
        materials.append(mat)
        meshes.append({"name": pname, "primitives": [{"attributes": attrs, "material": len(materials) - 1}]})
        mesh_nodes.append({"name": pname, "mesh": len(meshes) - 1, "skin": 0})
        stats[pname] = {"tris": len(f), "color": p["color"], "material": p["material"]}

    first_mesh = len(nodes)
    nodes += mesh_nodes
    gltf = {
        "asset": {"version": "2.0", "generator": "dragon-long build_rig.py"},
        "scene": 0,
        "scenes": [{"nodes": [index["Root"]] + list(range(first_mesh, len(nodes)))}],
        "nodes": nodes,
        "skins": [{"name": "Dragon", "joints": list(range(len(order))), "skeleton": index["Root"],
                   "inverseBindMatrices": ibm_acc}],
        "meshes": meshes,
        "materials": materials,
        "accessors": g.accessors,
        "bufferViews": g.views,
        "buffers": [{"byteLength": len(g.bin)}],
    }
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binc = bytes(g.bin) + b"\0" * ((4 - len(g.bin) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(binc)
    path = os.path.join(OUT, name + ".glb")
    with open(path, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, total))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        fh.write(struct.pack("<II", len(binc), 0x004E4942) + binc)

    rig = {"name": name, "tris": a.tri_count(), "bones": order,
           "parents": {n: a.bones[n]["parent"] for n in order},
           "blink_up_rad": round(a.blink_up, 3), "blink_low_rad": round(a.blink_low, 3),
           "eye": {k: round(v, 3) for k, v in a.eye_geom.items()}, "pupil_forward": a.eye_fwd, "parts": stats}
    with open(os.path.join(OUT, name + ".json"), "w") as fh:
        json.dump(rig, fh, indent=2, ensure_ascii=False)
    print(path, len(order), "os", a.tri_count(), "triangles", os.path.getsize(path) // 1024, "Ko")


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "")
