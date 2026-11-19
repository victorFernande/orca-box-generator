"""Connected front fittings from paired dimensional interval graphs.

Both sides use the same two-dimensional triangulation, so the ear's thickness
stays positive and its shared foot is explicit. No overlapping closed solids
or reference meshes are imported into the enclosure.
"""
from __future__ import annotations


def _cap_boundary_loops(vertices, triangles, cap):
    from .mesh_generator import np, _undirected_edge_keys

    faces = triangles[cap]
    edges = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    keys = _undirected_edge_keys(edges, len(vertices))
    _, first, counts = np.unique(keys, return_index=True, return_counts=True)
    if np.any(counts > 2):
        raise ValueError("Cap boundary is non-manifold")
    boundary = edges[first[counts == 1]]
    if not len(boundary):
        raise ValueError("Fitting has no shared foot boundary")
    origins, origin_counts = np.unique(boundary[:, 0], return_counts=True)
    ends, end_counts = np.unique(boundary[:, 1], return_counts=True)
    if (np.any(origin_counts != 1) or np.any(end_counts != 1)
            or not np.array_equal(origins, ends)):
        raise ValueError("Fitting foot has ambiguous or pinched loops")
    links = dict(boundary.tolist())
    remaining = set(links)
    loops = []
    while remaining:
        start = min(remaining)
        current, loop = start, []
        while current in remaining:
            loop.append(current)
            remaining.remove(current)
            current = links[current]
        if current != start or len(loop) < 3:
            raise ValueError("Fitting foot is not a simple closed loop")
        loops.append(np.asarray(loop, dtype=np.int32))
    return loops


# Canonical front fittings are small, shared dimensional surfaces. Retention is
# bounded by bytes, independently of the controller and latch caches.
from collections import OrderedDict
import threading
_FRONT_PATCH_CACHE = OrderedDict()
_FRONT_PATCH_CACHE_BYTES = 8 * 1024 * 1024
_FRONT_PATCH_LOCK = threading.Lock()


def _clear_front_patch_cache():
    with _FRONT_PATCH_LOCK:
        _FRONT_PATCH_CACHE.clear()


def _front_patch_bytes(patch):
    return (sum(patch[k].nbytes for k in ("vertices", "triangles", "cap_triangles"))
            + sum(loop.nbytes for loop in patch["foot_indices"]))


def _front_graph_mesh(p, part, zlevels, fractions):
    from .mesh_generator import np, _unique_xyz_indices, MeshData, topology_report
    from .rugged_front_geometry import front_strip_bounds, front_interval, front_fitting_dimensions

    q = front_fitting_dimensions(p)
    zlevels = np.asarray(zlevels, dtype=float)
    # Flat cam endcaps are actual graph jumps. Two coincident height rows carry
    # the limits on either side, preserving a cap rather than smoothing it.
    caps = ([q["cam_center_z"] - q["cam_socket_half_height"],
             q["cam_center_z"] + q["cam_socket_half_height"]] if part == "base" else [])
    rows, probes = [], []
    for z in zlevels:
        if any(abs(z - cap) < 1e-9 for cap in caps):
            rows.extend((z, z)); probes.extend((z - 1e-7, z + 1e-7))
        else:
            rows.append(z); probes.append(z)
    z = np.asarray(rows)[:, None]
    sample_z = np.asarray(probes)[:, None]
    low, high = front_strip_bounds(p, part, z)
    ss = low + (high - low) * np.asarray(fractions)[None, :]
    zz = np.broadcast_to(z, ss.shape)
    ain, aout = front_interval(p, part, ss, np.broadcast_to(sample_z, ss.shape))
    # Only the cavity's inner graph jumps at a flat cap. The exterior is
    # evaluated at the same physical height on both coincident rows.
    _, aout = front_interval(p, part, ss, zz)
    if not np.all(np.isfinite(ain)) or not np.all(np.isfinite(aout)) or np.any(aout < ain):
        raise ValueError("Front fitting interval is invalid")
    inner = np.stack((47.25 + ain, -47.5 - ss, zz), axis=-1)
    outer = np.stack((47.25 + aout, -47.5 - ss, zz), axis=-1)
    nr, nc = ss.shape
    ids = np.arange(nr * nc, dtype=np.int32).reshape(nr, nc)
    n = nr * nc
    faces, root_caps, row_meta, col_meta = [], [], [], []

    def quad(a, b, c, d, r, t, cap=False, reverse=False):
        tr = np.stack((a, b, c, a, c, d), axis=-1).reshape(-1, 3)
        if reverse:
            tr = tr[:, [0, 2, 1]]
        faces.append(tr)
        root_caps.append(np.full(len(tr), cap, dtype=bool))
        row_meta.append(np.repeat(np.asarray(r).ravel(), 2))
        col_meta.append(np.repeat(np.asarray(t).ravel(), 2))

    rr, tt = np.meshgrid(np.arange(nr - 1), np.arange(nc - 1), indexing="ij")
    a, b, c, d = ids[:-1, :-1], ids[:-1, 1:], ids[1:, 1:], ids[1:, :-1]
    quad(a, b, c, d, rr, tt)
    quad(a + n, b + n, c + n, d + n, rr, tt, reverse=True)
    r = np.arange(nr - 1)
    quad(ids[:-1, 0], ids[1:, 0], ids[1:, 0] + n, ids[:-1, 0] + n,
         r, np.zeros(nr - 1, dtype=int), cap=True)
    quad(ids[:-1, -1], ids[:-1, -1] + n, ids[1:, -1] + n, ids[1:, -1],
         r, np.full(nr - 1, nc - 2))
    t = np.arange(nc - 1)
    quad(ids[0, :-1], ids[0, :-1] + n, ids[0, 1:] + n, ids[0, 1:],
         np.full(nc - 1, -1), t)
    quad(ids[-1, :-1], ids[-1, 1:], ids[-1, 1:] + n, ids[-1, :-1] + n,
         np.full(nc - 1, -1), t)
    vertices = np.concatenate((inner.reshape(-1, 3), outer.reshape(-1, 3))).astype(np.float32)
    triangles = np.concatenate(faces)
    cap = np.concatenate(root_caps)
    ri, ti = np.concatenate(row_meta), np.concatenate(col_meta)
    first, inverse = _unique_xyz_indices(vertices)
    vertices = vertices[first]
    triangles = inverse[triangles].astype(np.int32)
    keep = ((triangles[:, 0] != triangles[:, 1]) & (triangles[:, 1] != triangles[:, 2]) &
            (triangles[:, 2] != triangles[:, 0]))
    triangles, cap, ri, ti = triangles[keep], cap[keep], ri[keep], ti[keep]
    xyz = vertices[triangles].astype(float)
    normals = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    if np.any(lengths == 0):
        raise ValueError(f"Degenerate front graph face: {xyz[lengths == 0][:2].tolist()}")
    volume = float(np.einsum("ij,ij->i", xyz[:, 0], np.cross(xyz[:, 1], xyz[:, 2])).sum() / 6000)
    if volume < 0:
        triangles = triangles[:, [0, 2, 1]]
        normals = -normals
        volume = -volume
    mesh = MeshData(vertices, triangles, (normals / lengths[:, None]).astype(np.float32),
                    {}, volume, "front_patch", .025)
    topology = topology_report(mesh)
    if not topology["closed"] or not topology["oriented"] or topology["components"] != 1 or topology["euler"] != 2:
        raise ValueError(f"Front graph boundary is invalid: {topology}")
    return mesh, cap, ri, ti, np.asarray(rows), topology


def _canonical_front_patch(p, part):
    from .mesh_generator import np
    from .rugged_front_geometry import front_z_events, front_fittings_field

    events = front_z_events(p, part)
    def height_samples(lo, hi):
        return np.linspace(lo, hi, int(np.ceil((hi - lo) / .4)) + 1)

    if part == "lid" and events[-1] - events[0] > 28:
        # Between the lower horn and the upper journal/roof, both interval
        # graphs are an exact straight extrusion. Endpoint rows preserve that
        # surface without multiplying planar triangles with lid height.
        regular = np.r_[height_samples(events[0], events[0] + 6),
                        height_samples(events[-1] - 22, events[-1])]
    else:
        regular = height_samples(events[0], events[-1])
    zlevels = np.unique(np.r_[regular, events])
    fractions = np.linspace(0, 1, 33)
    field = front_fittings_field(p, part)
    tolerance = min(float(p["fit_clearance"]) / 4, .025)
    for iteration in range(8):
        mesh, cap, ri, ti, rows, topology = _front_graph_mesh(p, part, zlevels, fractions)
        xyz = mesh.vertices[mesh.triangles].astype(float)
        active = ~cap
        errors = np.zeros(len(xyz))
        for weights in ([1/3, 1/3, 1/3], [.5, .5, 0], [0, .5, .5], [.5, 0, .5]):
            probes = np.einsum('i,tij->tj', np.asarray(weights), xyz[active])
            errors[active] = np.maximum(errors[active], np.abs(field(probes)))
        maximum = float(errors.max())
        if maximum <= tolerance:
            loops = _cap_boundary_loops(mesh.vertices, mesh.triangles, cap)
            if len(loops) != 1:
                raise ValueError("Front ear requires one attachment loop")
            return {"vertices": mesh.vertices, "triangles": mesh.triangles,
                    "cap_triangles": cap, "foot_indices": loops,
                    "interface_error_mm": tolerance, "measured_error_mm": maximum,
                    "closed_topology": topology}
        bad = np.flatnonzero(errors > tolerance * .8)
        new_z, new_t = [], []
        for face in bad:
            row, col = int(ri[face]), int(ti[face])
            if row >= 0 and rows[row + 1] - rows[row] > 1e-6:
                new_z.append((rows[row] + rows[row + 1]) / 2)
            if fractions[col + 1] - fractions[col] > 1e-5:
                new_t.append((fractions[col] + fractions[col + 1]) / 2)
        zlevels = np.unique(np.r_[zlevels, new_z])
        fractions = np.unique(np.r_[fractions, new_t])
        if len(zlevels) * len(fractions) > 150_000:
            break
    raise ValueError(f"Front fitting surface error {maximum:.6f} exceeds {tolerance:.6f} mm")


def generate_front_patch(p, part, center, side):
    """Return one exact connected ear; its root cap is removed by the caller."""
    from .mesh_generator import np
    from .schema import normalize_params
    from .rugged_geometry import rugged_outer_body_y
    from .rugged_front_geometry import front_z_events

    if part not in ("base", "lid") or side not in (-1, 1):
        raise ValueError("Use base/lid and side -1/+1")
    lh, clearance = float(p.get("rugged_lid_height", 20)), float(p["fit_clearance"])
    q = normalize_params({"style": "rugged_box", "rugged_lid_height": lh,
                          "fit_clearance": clearance})
    key = (part, lh if part == "lid" else 20, clearance)
    with _FRONT_PATCH_LOCK:
        canonical = _FRONT_PATCH_CACHE.get(key)
        if canonical is not None:
            _FRONT_PATCH_CACHE.move_to_end(key)
    if canonical is None:
        canonical = _canonical_front_patch(q, part)
        size = _front_patch_bytes(canonical)
        if size <= _FRONT_PATCH_CACHE_BYTES:
            for array in [canonical[k] for k in ("vertices", "triangles", "cap_triangles")] + canonical["foot_indices"]:
                array.flags.writeable = False
            with _FRONT_PATCH_LOCK:
                _FRONT_PATCH_CACHE[key] = canonical
                while sum(_front_patch_bytes(v) for v in _FRONT_PATCH_CACHE.values()) > _FRONT_PATCH_CACHE_BYTES:
                    _FRONT_PATCH_CACHE.popitem(last=False)
    v = canonical["vertices"].astype(float).copy()
    v[:, 0] = float(center) + side * (v[:, 0] - 47.25)
    v[:, 1] += -float(p["depth_y"]) / 2 + 47.5
    canonical_z = canonical["vertices"][:, 2]
    height = float(p["height_z"])
    v[:, 2] += height - 35
    # Preserve authored crease planes through translation. Adding a decimal
    # height to already rounded canonical float32 coordinates otherwise rounds
    # twice and can put the shell and its ear on opposite adjacent float32s.
    actual_events = front_z_events(p, part)
    planes = []
    for event in front_z_events(q, part):
        translated = event + height - 35
        nearest = min(actual_events, key=lambda value: abs(value - translated))
        planes.append((event, nearest if abs(nearest - translated) < 1e-7 else translated))
    if part == "lid":
        planes.extend(((35 + lh - 10, height + lh - 10),
                       (35 + lh, height + lh)))
    for original, translated in planes:
        v[canonical_z == np.float32(original), 2] = translated
    v = v.astype(np.float32)
    foot = np.unique(np.concatenate(canonical["foot_indices"]))
    v[foot, 1] = rugged_outer_body_y(p, part, 0, v[foot, 2])
    triangles = canonical["triangles"].copy()
    if side == -1:
        triangles = triangles[:, [0, 2, 1]]
    result = {**canonical, "vertices": v, "triangles": triangles,
              "foot_loops": [v[loop].copy() for loop in canonical["foot_indices"]]}
    return result
