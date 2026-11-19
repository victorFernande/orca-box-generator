"""Dimensional reconstruction of the removable enclosure's flexible latch.

The two spherical journals belong to the lid; the two lower cam fingers engage
the base. Dimensions below are mathematical primitives in millimetres. This
module never reads a reference mesh or embeds a reference triangulation.
"""

from __future__ import annotations

import math
from collections import OrderedDict
import threading


_LATCH_CACHE = OrderedDict()
_LATCH_CACHE_BYTES = 48 * 1024 * 1024
_LATCH_CACHE_LOCK = threading.Lock()


def _clear_latch_cache():
    """Discard decoded local meshes before an independent fresh-CAD proof."""
    with _LATCH_CACHE_LOCK:
        _LATCH_CACHE.clear()


def _load_canonical_latch(p):
    """Optional source-bound bank seam; build/tests may patch this to None.

    Clearing the local cache and disabling this loader guarantees that the
    factory extracts the current analytic field instead of validating itself
    against an already generated package resource.
    """
    from .preset_mesh_cache import load_standard_preset_mesh

    return load_standard_preset_mesh(p, "clip_right")


def _frame(p, part):
    from .rugged_geometry import rugged_latch_geometry

    meta = rugged_latch_geometry(p, part)
    return tuple(meta["pivot"][k] for k in ("x", "y", "z"))


def _round_box2(x, z, cx, cz, hx, hz, radius):
    from .mesh_generator import np

    a = np.abs(x - cx) - (hx - radius)
    b = np.abs(z - cz) - (hz - radius)
    return (
        np.hypot(np.maximum(a, 0), np.maximum(b, 0))
        + np.minimum(np.maximum(a, b), 0)
        - radius
    )


def rugged_latch_field(p, part="clip_left"):
    """Return independent signed membership for canonical CLOSED coordinates.

    The hourglass is a conical profile about X, clipped by the two Y faces;
    extruding its front silhouette would change its waist and spherical fits.
    Lower cam and slot dimensions remain fixed when lid height changes.
    """
    from .mesh_generator import np

    px, py, pivot = _frame(p, part)
    h = float(p["height_z"])
    shoulder = h - 4.69694
    cam_z = h - 8.19694
    # At the reference height the neutral section has rho=5/10/15 mm.
    # Stretch the neck between the fixed cam shoulder and the lid journal.
    neck_span = pivot - shoulder
    if neck_span <= 7.0:
        raise ValueError("Tampa muito baixa para a trava / lid too shallow for latch.")
    slope = math.tan(math.radians(40))
    reference_pivot = h + 10
    neck_top = pivot - 5
    reference_neck_top = reference_pivot - 5
    neck_scale = (reference_neck_top - shoulder) / (neck_top - shoulder)

    def field(points):
        v = np.asarray(points, dtype=float)
        x, y, z = (v - (px, py, 0)).T
        ax = np.abs(x)
        # A continuous material-coordinate map lengthens only the neck. Using
        # different radius scales on the cone and its fillet would make a crack
        # when the lid height differs from the reference height.
        upper_z = np.where(
            z >= neck_top,
            z - pivot + reference_pivot,
            np.where(z > shoulder, shoulder + (z - shoulder) * neck_scale, z),
        )
        radius = np.hypot(y, reference_pivot - upper_z)
        signed_radius = np.where(upper_z <= reference_pivot, radius, -radius)
        effective = signed_radius
        waist = 12.5 - 5 * slope
        width = np.where(
            effective < 10,
            12.5 - slope * np.maximum(effective - 5, 0),
            waist + slope * (effective - 10),
        )
        cone = (ax - width) * math.cos(math.radians(40))
        bottom = shoulder - upper_z
        # Half-millimetre convex blend at the lower cone/shoulder edge.
        center_z = shoulder + 0.5
        center_effective = np.hypot(y, reference_pivot - center_z)
        center_x = (
            waist + slope * (center_effective - 10) - 0.5 / math.cos(math.radians(40))
        )
        corner = np.hypot(ax - center_x, upper_z - center_z) - 0.5
        tangent_z = center_z + 0.5 * math.sin(math.radians(40))
        lower_edge = np.where(
            (ax > center_x) & (upper_z < tangent_z), corner, np.maximum(cone, bottom)
        )
        body = np.maximum.reduce((lower_edge, np.abs(y) - 3, upper_z - reference_pivot))
        # A radius-2 toroidal inside corner joins the U's rho=5 bottom to
        # the straight x=+/-7.5 fork walls.
        u = _round_box2(x, signed_radius, 0, -48.5, 7.5, 53.5, 2)
        body = np.maximum(body, -u)
        # Rounded tops of the two fork ears, plus the outward spherical caps.
        ear = np.maximum.reduce((ax - 12.5, 7.5 - ax, np.hypot(y, z - pivot) - 3))
        ear_back = np.maximum.reduce(
            (ax - 12.5, 7.5 - ax, y, pivot - z, np.hypot(y, z - pivot + 2) - 5)
        )
        ear = np.minimum(ear, ear_back)
        body = np.minimum(body, ear)
        ball = (
            np.minimum(
                np.sqrt((x - 10.25) ** 2 + y * y + (z - pivot) ** 2),
                np.sqrt((x + 10.25) ** 2 + y * y + (z - pivot) ** 2),
            )
            - 3.75
        )
        # The cap overlaps the existing ear within its radius-3 cylinder.
        # Merely touching at x=12.5 would leave F=0 on an internal membrane.
        cap = np.maximum.reduce((ball, 12.48 - ax, np.hypot(y, z - pivot) - 3))
        body = np.minimum(body, cap)

        # Flexible lower fingers are joined only beneath the rounded slit tips.
        # A flat wedge on the grip is limited by the radius-30 back contour.
        lower_bottom = np.maximum(
            h + 10 - np.sqrt(np.maximum(900 - y * y, 0)), h - 18.18425 + 0.87474 * y
        )
        grip = np.maximum.reduce(
            (ax - 13.5, np.abs(y) - 3, lower_bottom - z, z - (h - 16.530625 - 1.25 * y))
        )
        stem = np.maximum.reduce(
            (ax - 12.5, np.abs(y) - 3, lower_bottom - z, z - shoulder)
        )
        lower = np.minimum(grip, stem)
        # Concave R1 blend where the wider grip wing meets the central stem.
        # Its cylinder follows the slanted upper grip plane, hence a normal
        # plane distance rather than a vertical one is used here.
        grip_plane = (z - (h - 16.530625 - 1.25 * y)) / math.sqrt(1 + 1.25**2)
        wing_blend = np.maximum.reduce(
            (
                1 - np.hypot(ax - 13.5, grip_plane - 1),
                ax - 13.5,
                grip_plane - 1,
                np.abs(y) - 3,
                lower_bottom - z,
            )
        )
        lower = np.minimum(lower, wing_blend)
        # Cylinders with 45-degree conical ends. The measured reference's
        # "rounded" edge is a straight radial/axial chamfer, not a torus.
        radial = np.hypot(ax - 8.5, y)
        cap = np.abs(z - cam_z)
        cam = np.maximum.reduce((radial - 5, cap - 3, radial + cap - 7.001))
        lower = np.minimum(lower, np.maximum(cam, 10 - ax))
        body = np.minimum(body, lower)
        # One-millimetre slots with semicircular lower tips and a horizontal
        # mouth separating the cam finger from the conical neck.
        slot = _round_box2(ax, z, 9.5, h - 9.69694, 0.5, 5, 0.5)
        mouth = np.maximum.reduce((9.5 - ax, z - shoulder, shoulder - 0.5 - z))
        mouth_corner = np.maximum.reduce(
            (
                ax - 10.5,
                9.9 - ax,
                shoulder - 1 - z,
                z - shoulder + 0.4,
                0.5 - np.hypot(ax - 10.5, z - shoulder + 1),
            )
        )
        void = np.minimum.reduce((slot, mouth, mouth_corner))
        return np.maximum.reduce((body, -void, np.abs(y) - 3))

    return field


def generate_rugged_latch(p, part="clip_left"):
    """Return an independent mesh, reusing identical local dimensional solids.

    Changing enclosure width, depth, height, or the left/right fitting translates
    the latch without extracting it again. The cache stores at most 48 MiB and
    two lid-height/tolerance combinations; it never retains a private asset.
    """
    from .mesh_generator import MeshData, np

    px, py, _ = _frame(p, part)
    lh = float(p.get("rugged_lid_height", 20))
    clearance = float(p.get("fit_clearance", 0.15))
    key = (lh, clearance)
    with _LATCH_CACHE_LOCK:
        canonical = _LATCH_CACHE.get(key)
        if canonical is not None:
            _LATCH_CACHE.move_to_end(key)
    if canonical is None:
        canonical_params = {
            "style": "rugged_box",
            "width_x": 160,
            "depth_y": 95,
            "height_z": 35,
            "rugged_lid_height": lh,
            "corner_radius": 12,
            "fit_clearance": clearance,
            "wall_thickness": 2.5,
            "floor_thickness": 2.5,
        }
        canonical = _load_canonical_latch(canonical_params)
        if canonical is None:
            canonical = _extract_latch(canonical_params, "clip_right")
        size = sum(
            a.nbytes
            for a in (canonical.vertices, canonical.triangles, canonical.face_normals)
        )
        if size <= _LATCH_CACHE_BYTES:
            for a in (canonical.vertices, canonical.triangles, canonical.face_normals):
                a.flags.writeable = False
            with _LATCH_CACHE_LOCK:
                _LATCH_CACHE[key] = canonical
                while (
                    len(_LATCH_CACHE) > 2
                    or sum(
                        sum(a.nbytes for a in (m.vertices, m.triangles, m.face_normals))
                        for m in _LATCH_CACHE.values()
                    )
                    > _LATCH_CACHE_BYTES
                ):
                    _LATCH_CACHE.popitem(last=False)
    shift = np.array((px - 47.25, py + 50.5, float(p["height_z"]) - 35))
    vertices = (canonical.vertices.astype(float) + shift).astype(np.float32)
    low, high = vertices.min(0), vertices.max(0)
    return MeshData(
        vertices,
        canonical.triangles.copy(),
        canonical.face_normals.copy(),
        {"min": low.tolist(), "max": high.tolist(), "size": (high - low).tolist()},
        canonical.volume_cm3,
        part,
        canonical.interface_error_mm,
    )


def _extract_latch(p, part):
    """Extract one welded boundary of the analytic solid, with no solid overlap."""
    from .mesh_generator import np

    px, py, pivot = _frame(p, part)
    h = float(p["height_z"])
    bounds = (px - 14.5, px + 14.5, py - 3.5, py + 3.5, h - 21, pivot + 4)
    # Curvature sampling is independent of the UI's general quality setting.
    # Fine sampling across the slit tips preserves their 0.5 mm radii.
    step = 0.3
    waist_radius = (pivot - h + 10) / 2
    waist_levels = np.arange(
        pivot - waist_radius - 0.03, pivot - math.sqrt(waist_radius**2 - 9) + 0.03, 0.02
    )
    hints = {
        "params": {
            "fit_clearance": float(p.get("fit_clearance", 0.15)),
            "quality": "fine",
            "dividers_x": [],
            "dividers_y": [],
        },
        "planes": [
            [px + s for s in (-13.5, -12.5, -10, -9, -7.5, 0, 7.5, 9, 10, 12.5, 13.5)],
            [py - 3, py, py + 3],
            [
                pivot,
                h - 14.19694,
                h - 4.69694,
                h - 5.19694,
                h - 11.19694,
                h - 10.19794,
                h - 6.19594,
                h - 5.19694,
            ],
        ],
        "circles": [],
        "rectangles": [],
        "levels": [],
        "sample_x": [
            px + sign * float(x)
            for sign in (-1, 1)
            for x in [
                *np.arange(5.5, 7.51, 0.18),
                *np.arange(8.9, 10.51, 0.12),
                *np.arange(11, 14.01, 0.18),
                8.3045,
                8.5,
            ]
        ],
        "sample_y": np.arange(bounds[2], bounds[3], step).tolist(),
        "sample_z": [*np.arange(bounds[4], bounds[5], step), *waist_levels],
    }
    # Keep the very same sampling planes, but do not move an extracted vertex
    # off its original tetrahedral edge merely because it is close to a plane.
    # Such a snap can fold a sub-micrometre triangle at a cam/cone junction.
    plane_distance = min(float(p.get("fit_clearance", 0.15)) / 4, 0.04) * 0.15
    for axis, key in enumerate(("sample_x", "sample_y", "sample_z")):
        hints[key].extend(
            plane + offset
            for plane in hints["planes"][axis]
            for offset in (-plane_distance, plane_distance)
        )
    hints["planes"] = [[], [], []]
    field = rugged_latch_field(p, part)
    return _extract_refined(
        field, bounds, hints, part, min(float(p.get("fit_clearance", 0.15)) / 4, 0.025)
    )


def _extract_refined(field, bounds, hints, part, tolerance):
    """Refine original tetrahedral cells without unconstrained vertex movement.

    A projected midpoint can leave its parent cell and fold a planar neighbour.
    Instead, only sampling intervals containing an inaccurate curved triangle
    receive extra axis planes. Every new vertex remains on its original grid
    edge and shares that edge with the adjacent tetrahedron.
    """
    from .mesh_generator import mesh_field, _refinement, np

    for iteration in range(7):
        mesh = mesh_field(field, bounds, hints, part)
        triangles = mesh.vertices[mesh.triangles].astype(float)
        centers = triangles.mean(axis=1)
        errors = np.abs(field(centers))
        maximum = float(errors.max())
        if maximum <= tolerance:
            mesh = _contract_float32_edges(mesh)
            maximum = float(
                np.max(
                    np.abs(
                        field(mesh.vertices[mesh.triangles].astype(float).mean(axis=1))
                    )
                )
            )
            if maximum <= tolerance:
                mesh.interface_error_mm = max(maximum, mesh.interface_error_mm)
                return mesh
            triangles = mesh.vertices[mesh.triangles].astype(float)
            centers = triangles.mean(axis=1)
            errors = np.abs(field(centers))
        if iteration == 6:
            break
        bad = errors > tolerance * 0.8
        axes, _ = _refinement(bounds, hints)
        for axis, key in enumerate(("sample_x", "sample_y", "sample_z")):
            samples = axes[axis]
            intervals = np.unique(
                np.clip(
                    np.searchsorted(samples, centers[bad, axis]) - 1,
                    0,
                    len(samples) - 2,
                )
            )
            # The triangle can touch a crease on a cell face, so refine both
            # neighbouring intervals as well as its own interval.
            intervals = np.unique(
                np.clip(
                    np.concatenate((intervals - 1, intervals, intervals + 1)),
                    0,
                    len(samples) - 2,
                )
            )
            midpoints = (samples[intervals] + samples[intervals + 1]) / 2
            hints[key] = [*hints.get(key, []), *midpoints]
    raise ValueError("Tolerância da trava excedida / latch tolerance exceeded.")


def _contract_float32_edges(mesh):
    """Collapse only topologically valid, orientation-preserving tiny edges.

    A float32 junction may contain several near-coincident vertices. An
    unconstrained cluster weld can invert an adjacent narrow triangle, so every
    contraction checks the manifold link condition and all incident face normals.
    No point travels more than 0.002 mm and the curved error is checked afterwards.
    """
    from .mesh_generator import MeshData, np

    vertices = mesh.vertices.astype(float)
    triangles = mesh.triangles.copy()
    q = vertices[triangles]
    edges = np.concatenate(
        (triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]])
    )
    length = np.linalg.norm(vertices[edges[:, 0]] - vertices[edges[:, 1]], axis=1)
    edges = np.unique(np.sort(edges[length < 0.001], axis=1), axis=0)
    if not len(edges):
        return mesh
    edge_length = np.linalg.norm(vertices[edges[:, 0]] - vertices[edges[:, 1]], axis=1)
    active_vertices = set(map(int, edges.ravel()))
    relevant = np.any(np.isin(triangles, list(active_vertices)), axis=1)
    incidence = {}
    for face in np.flatnonzero(relevant):
        for vertex in triangles[face]:
            incidence.setdefault(int(vertex), set()).add(int(face))
    parents = np.arange(len(vertices))
    alive = np.ones(len(triangles), dtype=bool)
    low, high = vertices.copy(), vertices.copy()

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return int(index)

    for u, v in edges[np.argsort(edge_length)]:
        u, v = root(int(u)), root(int(v))
        if u == v:
            continue
        fu = {f for f in incidence.get(u, ()) if alive[f]}
        fv = {f for f in incidence.get(v, ()) if alive[f]}
        shared = fu & fv
        if len(shared) != 2:
            continue
        nu = set(map(int, triangles[list(fu)].ravel())) - {u, v}
        nv = set(map(int, triangles[list(fv)].ravel())) - {u, v}
        opposite = set(map(int, triangles[list(shared)].ravel())) - {u, v}
        if nu & nv != opposite:
            continue
        lower, upper = np.minimum(low[u], low[v]), np.maximum(high[u], high[v])
        if np.linalg.norm(upper - lower) > 0.002:
            continue
        faces = np.asarray(sorted((fu | fv) - shared), dtype=int)
        original = vertices[triangles[faces]]
        before = np.cross(
            original[:, 1] - original[:, 0], original[:, 2] - original[:, 0]
        )
        selected = None
        # Both endpoints and their midpoint are tested. The best valid local
        # normal agreement determines the representative, rather than its ID.
        best = -1.0
        for point in (vertices[u], vertices[v], (vertices[u] + vertices[v]) * 0.5):
            point = np.asarray(point, dtype=np.float32).astype(float)
            changed = original.copy()
            mask = (triangles[faces] == u) | (triangles[faces] == v)
            changed[mask] = point
            after = np.cross(
                changed[:, 1] - changed[:, 0], changed[:, 2] - changed[:, 0]
            )
            scale = np.linalg.norm(before, axis=1) * np.linalg.norm(after, axis=1)
            if np.any(scale == 0):
                continue
            cosine = np.einsum("ij,ij->i", before, after) / scale
            score = float(cosine.min())
            if score > 0.05 and score > best:
                selected, best = point, score
        if selected is None:
            continue
        all_faces = fu | fv
        for face in all_faces:
            for vertex in triangles[face]:
                incidence.setdefault(int(vertex), set()).discard(face)
        parents[v] = u
        vertices[u] = selected
        low[u], high[u] = lower, upper
        for face in all_faces:
            if face in shared:
                alive[face] = False
                continue
            triangles[face][triangles[face] == v] = u
            for vertex in triangles[face]:
                incidence.setdefault(int(vertex), set()).add(face)
    triangles = triangles[alive]
    used, remap = np.unique(triangles, return_inverse=True)
    vertices = vertices[used].astype(np.float32)
    triangles = remap.reshape(-1, 3).astype(np.int32)
    q = vertices[triangles].astype(float)
    normals = np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0])
    length = np.linalg.norm(normals, axis=1)
    if np.any(length <= 0):
        raise ValueError("Trava degenerada / degenerate latch boundary.")
    normals = (normals / length[:, None]).astype(np.float32)
    volume = float(
        np.einsum("ij,ij->i", q[:, 0], np.cross(q[:, 1], q[:, 2])).sum() / 6000
    )
    return MeshData(
        vertices,
        triangles,
        normals,
        mesh.bounds_mm,
        volume,
        mesh.part,
        mesh.interface_error_mm,
    )


def rugged_latch_print_transform(vertices, p, part="clip_left"):
    """Put the broad, planar Y=-3 face on the bed; return a new array.

    The cyclic frame X'=-X, Y'=Z, Z'=Y has positive determinant, preserving
    triangle winding and avoiding the old clip's upright printing pose.
    """
    from .mesh_generator import np

    px, py, _ = _frame(p, part)
    v = np.asarray(vertices, dtype=float)
    return np.column_stack((-(v[:, 0] - px), v[:, 2], v[:, 1] - py + 3))
