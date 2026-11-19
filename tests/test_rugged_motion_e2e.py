"""Independent numerical checks of the four-part snap-hinged Rugged case.

Uses the parametric product surfaces, real serialized exports and dimensional
measurements only. No reference mesh/assets are stored, imported or generated
by these tests. Digital clearance does not certify a print or release force.
"""
from __future__ import annotations

import base64
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from box_studio.schema import normalize_params, validate_params
from box_studio.mesh_generator import (
    np, generate_box_mesh, build_part_field, collect_target_meshes,
    orient_mesh_for_print,
)
from box_studio.rugged_geometry import (
    rugged_dimensions, rugged_hinge_geometry, rugged_latch_geometry,
    rugged_transform,
)
from box_studio.exporters import write_binary_stl, write_orca_3mf
from verify_box_e2e_exports import inspect_mesh, verify_exports


def surfaces(mesh, count=14000):
    n = min(count // 2, len(mesh.vertices))
    vertices = mesh.vertices[np.linspace(0, len(mesh.vertices) - 1, n, dtype=int)]
    n = min(count // 2, len(mesh.triangles))
    centers = mesh.vertices[mesh.triangles[np.linspace(0, len(mesh.triangles) - 1, n, dtype=int)]].mean(axis=1)
    return np.r_[vertices, centers].astype(float)


def rotate_x(points, pivot, degrees):
    """Independent row-vector rotation; never calls the product motion helper."""
    points = np.asarray(points, dtype=float)
    angle = np.deg2rad(degrees)
    cs, sn = np.cos(angle), np.sin(angle)
    q = points - np.asarray(pivot)
    result = q.copy()
    result[:, 1] = q[:, 1] * cs - q[:, 2] * sn
    result[:, 2] = q[:, 1] * sn + q[:, 2] * cs
    return result + pivot


def print_vertices(points, params, part):
    """Reproduce the declared rigid print pose independently of the mesher."""
    v = np.asarray(points, dtype=float).copy()
    if part == "lid":
        v[:, 0] *= -1
        v[:, 2] = params["height_z"] + params["rugged_lid_height"] - v[:, 2]
    elif part in ("clip_left", "clip_right"):
        pivot_y = -params["depth_y"] / 2 - 3.0
        v = np.column_stack((-v[:, 0], v[:, 2], v[:, 1] - pivot_y + 3.0))
    return v.astype(np.float32)


def _bvh_candidates(vertices, faces, leaf_size=16, batch_size=256):
    """Yield every distinct overlapping triangle-AABB pair, with bounded batches.

    A balanced median BVH replaces the quadratic scan of all triangle bounds.
    A passing audit visits the complete candidate set: there is no geometric or
    statistical sampling. Bounds use the original Snap oracle's 1e-6 mm pad.
    """
    triangles = np.asarray(vertices)[faces].astype(float)
    low, high = triangles.min(axis=1), triangles.max(axis=1)
    del triangles
    count = len(faces)
    if count < 2:
        return
    maximum = 2 * (1 << max(0, (max(1, (count + leaf_size - 1) // leaf_size) - 1).bit_length())) - 1
    bounds_low = np.empty((maximum, 3)); bounds_high = np.empty((maximum, 3))
    left = np.full(maximum, -1, dtype=np.int32)
    right = np.full(maximum, -1, dtype=np.int32)
    start = np.empty(maximum, dtype=np.intp); end = np.empty(maximum, dtype=np.intp)
    order = np.arange(count); centers = (low + high) / 2
    pending = [(0, 0, count)]; allocated = 1
    while pending:
        node, first, last = pending.pop()
        ids = order[first:last]
        start[node], end[node] = first, last
        bounds_low[node] = low[ids].min(axis=0)
        bounds_high[node] = high[ids].max(axis=0)
        if last - first <= leaf_size:
            continue
        axis = int(np.argmax(np.ptp(centers[ids], axis=0)))
        middle = (last - first) // 2
        order[first:last] = ids[np.argpartition(centers[ids, axis], middle)]
        left[node], right[node] = allocated, allocated + 1
        pending.extend(((allocated, first, first + middle), (allocated + 1, first + middle, last)))
        allocated += 2
    del centers
    offsets = np.arange(leaf_size)
    stack = [np.array([[0, 0]], dtype=np.int32)]
    buffered_u, buffered_v, buffered_count = [], [], 0
    while stack:
        # Keep the traversal itself vectorized, including deep neighbouring
        # leaf pairs. Processing one leaf at a time would retain linear
        # Python/NumPy dispatch overhead on a half-million-face mesh.
        chunks, amount = [], 0
        while stack and amount < 4096:
            chunk = stack.pop()
            remaining = 4096 - amount
            if len(chunk) > remaining:
                stack.append(chunk[remaining:])
                chunk = chunk[:remaining]
            chunks.append(chunk)
            amount += len(chunk)
        pairs = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        a, b = pairs.T
        valid = ((bounds_low[a] <= bounds_high[b] + 1e-6)
                 & (bounds_high[a] >= bounds_low[b] - 1e-6)).all(axis=1)
        a, b = a[valid], b[valid]
        if not len(a):
            continue
        leaves = (left[a] < 0) & (left[b] < 0)
        for first in range(0, int(leaves.sum()), batch_size):
            aa, bb = a[leaves][first:first + batch_size], b[leaves][first:first + batch_size]
            ia = start[aa, None] + offsets
            ib = start[bb, None] + offsets
            allowed_a = ia < end[aa, None]; allowed_b = ib < end[bb, None]
            fa = order[np.minimum(ia, count - 1)]
            fb = order[np.minimum(ib, count - 1)]
            valid_faces = allowed_a[:, :, None] & allowed_b[:, None, :]
            valid_faces &= (aa[:, None, None] != bb[:, None, None]) | (fa[:, :, None] < fb[:, None, :])
            u = np.broadcast_to(fa[:, :, None], valid_faces.shape)[valid_faces]
            v = np.broadcast_to(fb[:, None, :], valid_faces.shape)[valid_faces]
            overlap = ((low[u] <= high[v] + 1e-6) & (high[u] >= low[v] - 1e-6)).all(axis=1)
            if overlap.any():
                buffered_u.append(np.minimum(u[overlap], v[overlap]))
                buffered_v.append(np.maximum(u[overlap], v[overlap]))
                buffered_count += int(overlap.sum())
                if buffered_count >= 16384:
                    yield np.concatenate(buffered_u), np.concatenate(buffered_v)
                    buffered_u, buffered_v, buffered_count = [], [], 0
        a, b = a[~leaves], b[~leaves]
        if not len(a):
            continue
        same = a == b
        expansions = []
        if same.any():
            nodes = a[same]
            expansions.extend((np.column_stack((left[nodes], left[nodes])),
                               np.column_stack((left[nodes], right[nodes])),
                               np.column_stack((right[nodes], right[nodes]))))
        aa, bb = a[~same], b[~same]
        if len(aa):
            split_a = (left[aa] >= 0) & ((left[bb] < 0) | ((end[aa] - start[aa]) >= (end[bb] - start[bb])))
            u, v = aa[split_a], bb[split_a]
            expansions.extend((np.column_stack((left[u], v)), np.column_stack((right[u], v))))
            u, v = aa[~split_a], bb[~split_a]
            expansions.extend((np.column_stack((u, left[v])), np.column_stack((u, right[v]))))
        for expansion in expansions:
            for first in range(0, len(expansion), 4096):
                stack.append(expansion[first:first + 4096])
    if buffered_count:
        yield np.concatenate(buffered_u), np.concatenate(buffered_v)


def _coplanar_pair_overlap(a, b):
    """Vectorized version of the established strict positive-area 2D oracle."""
    def inside(points, boundary):
        edges = np.roll(boundary, -1, axis=1) - boundary
        delta = points[:, None, :, :] - boundary[:, :, None, :]
        signs = edges[:, :, None, 0] * delta[:, :, :, 1] - edges[:, :, None, 1] * delta[:, :, :, 0]
        return (signs > 1e-7).all(axis=1) | (signs < -1e-7).all(axis=1)
    pa = np.concatenate((a, a.mean(axis=1)[:, None, :]), axis=1)
    pb = np.concatenate((b, b.mean(axis=1)[:, None, :]), axis=1)
    overlap = inside(pa, b).any(axis=1) | inside(pb, a).any(axis=1)
    cross = lambda x, y: x[:, 0] * y[:, 1] - x[:, 1] * y[:, 0]
    for i in range(3):
        x, y = a[:, i], a[:, (i + 1) % 3]
        ab = y - x
        for j in range(3):
            c, d = b[:, j], b[:, (j + 1) % 3]
            cd = d - c
            s1, s2 = cross(ab, c - x), cross(ab, d - x)
            t1, t2 = cross(cd, x - c), cross(cd, y - c)
            overlap |= (((s1 > 1e-7) & (s2 < -1e-7)) | ((s1 < -1e-7) & (s2 > 1e-7))) & (
                ((t1 > 1e-7) & (t2 < -1e-7)) | ((t1 < -1e-7) & (t2 > 1e-7)))
    return overlap


def rugged_proper_intersections(mesh):
    """Full BVH audit, retaining Snap's exact narrow-phase tolerance rules."""
    from test_snap_lever_mating import _segment_pierces

    triangles = mesh.vertices[mesh.triangles].astype(float)
    result = []
    for u, v in _bvh_candidates(mesh.vertices, mesh.triangles):
        a, b = triangles[u], triangles[v]
        crossing = np.zeros(len(u), dtype=bool)
        for i in range(3):
            crossing |= _segment_pierces(a[:, i], a[:, (i + 1) % 3], b)
            crossing |= _segment_pierces(b[:, i], b[:, (i + 1) % 3], a)
        normal = np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0])
        length = np.linalg.norm(normal, axis=1)
        if (length == 0).any():
            raise ValueError("Degenerate triangle reached the intersection audit")
        normal /= length[:, None]
        coplanar = (np.abs(np.einsum("nki,ni->nk", b - a[:, None, 0, :], normal)).max(axis=1) < 1e-5) & ~crossing
        drop = np.argmax(np.abs(normal), axis=1)
        for axis in range(3):
            rows = np.flatnonzero(coplanar & (drop == axis))
            if not len(rows):
                continue
            axes = [i for i in range(3) if i != axis]
            xy, yz = a[rows][:, :, axes], b[rows][:, :, axes]
            positive_extent = (np.minimum(xy.max(axis=1), yz.max(axis=1))
                               - np.maximum(xy.min(axis=1), yz.min(axis=1)) > 1e-7).all(axis=1)
            rows = rows[positive_extent]
            if len(rows):
                crossing[rows] |= _coplanar_pair_overlap(a[rows][:, :, axes], b[rows][:, :, axes])
        result.extend(zip(u[crossing].tolist(), v[crossing].tolist()))
        if len(result) >= 10:
            return result[:10]
    return result


def actual_rim_contact(points, counterpart, source, params):
    """Admit only an actual closed seam with opposed outward normals.

    Analytic curvature may classify its own polygonal chord slightly inside.
    That is contact only when the point lies on actual triangles of BOTH
    meshes, with opposite normals. Interior points and same-facing overlap are
    never excused by a shared bounding box or a larger field tolerance.
    """
    points = np.asarray(points, dtype=float)
    tolerance, h = 1e-5, params["height_z"]
    def in_rim(v):
        return ((v[:, 2] >= h - .85 - tolerance) & (v[:, 2] <= h + tolerance)
                & (np.abs(v[:, 0]) <= params["width_x"] / 2 + tolerance)
                & (np.abs(v[:, 1]) <= params["depth_y"] / 2 + tolerance))
    def prepare(mesh):
        vertices = mesh.vertices.astype(float)
        faces = mesh.triangles[in_rim(vertices)[mesh.triangles].all(axis=1)]
        triangles = vertices[faces]
        origin = triangles[:, 0]
        a, b = triangles[:, 1] - origin, triangles[:, 2] - origin
        normal = np.cross(a, b)
        length = np.linalg.norm(normal, axis=1)
        if (length == 0).any():
            raise ValueError("Degenerate triangle in actual rim-contact query")
        normal /= length[:, None]
        aa, ab, bb = np.sum(a*a, axis=1), np.sum(a*b, axis=1), np.sum(b*b, axis=1)
        return origin, a, b, normal, aa, ab, bb, aa*bb-ab*ab
    def contains(v, data):
        origin, a, b, normal, aa, ab, bb, determinant = data
        delta = v[:, None] - origin
        plane = np.abs(np.einsum('ptj,tj->pt', delta, normal)) <= tolerance
        da, db = np.einsum('ptj,tj->pt', delta, a), np.einsum('ptj,tj->pt', delta, b)
        u, w = (bb*da-ab*db)/determinant, (aa*db-ab*da)/determinant
        return plane & (u >= -1e-7) & (w >= -1e-7) & (u+w <= 1+1e-7)
    other, own = prepare(counterpart), prepare(source)
    result = np.zeros(len(points), dtype=bool)
    candidates = np.flatnonzero(in_rim(points))
    for first in range(0, len(candidates), 128):
        ids = candidates[first:first + 128]
        on_other, on_own = contains(points[ids], other), contains(points[ids], own)
        for row in np.flatnonzero(on_other.any(axis=1) & on_own.any(axis=1)):
            normals_b, normals_a = other[3][on_other[row]], own[3][on_own[row]]
            result[ids[row]] = bool((normals_a @ normals_b.T < -1 + 1e-6).any())
    return result


def rugged_unsupported_layer_roots(mesh):
    """Find material births above the bed in the actual oriented mesh.

    A material island must start at a downward-facing local minimum of the
    boundary height function. Equal-height edge plateaus are joined first;
    an edge to a lower vertex anchors that plateau to earlier material. An
    upward-facing cavity floor is not a material birth. This checks all mesh
    vertices/edges, without rescanning every face at every vertex-Z interval.
    """
    from verify_box_e2e_exports import _roots

    vertices, triangles = mesh.vertices.astype(float), mesh.triangles
    a = triangles.ravel()
    b = triangles[:, [1, 2, 0]].ravel()
    za, zb = vertices[a, 2], vertices[b, 2]
    horizontal = za == zb
    labels = _roots(len(vertices), a[horizontal], b[horizontal])
    has_lower = np.zeros(len(vertices), dtype=bool)
    has_lower[labels[a[za > zb]]] = True
    has_lower[labels[b[zb > za]]] = True
    coords = vertices[triangles]
    normal = np.cross(coords[:, 1] - coords[:, 0], coords[:, 2] - coords[:, 0])
    length = np.linalg.norm(normal, axis=1)
    if (length == 0).any():
        raise ValueError("Degenerate triangle reached the print-layer audit")
    downward = normal[:, 2] / length < -1e-8
    has_downward = np.zeros(len(vertices), dtype=bool)
    has_downward[labels[triangles[downward].ravel()]] = True
    roots = np.flatnonzero((labels == np.arange(len(vertices))) & ~has_lower
                           & has_downward & (vertices[:, 2] > 1e-4))
    return [{"vertex": int(i), "position_mm": vertices[i].tolist()} for i in roots]


class RuggedIntersectionBroadphaseTests(unittest.TestCase):
    def test_bvh_covers_the_same_pairs_as_exhaustive_bounds(self):
        rng = np.random.default_rng(901)
        for scale in (.001, 1, 100):
            vertices = rng.normal(size=(240, 3)) * scale
            faces = np.arange(240).reshape(-1, 3)
            tris = vertices[faces]; lo, hi = tris.min(axis=1), tris.max(axis=1)
            expected = {(i, j) for i in range(len(faces)) for j in range(i + 1, len(faces))
                        if (lo[i] <= hi[j] + 1e-6).all() and (hi[i] >= lo[j] - 1e-6).all()}
            actual = [(int(i), int(j)) for u, v in _bvh_candidates(vertices, faces) for i, j in zip(u, v)]
            self.assertEqual(set(actual), expected)
            self.assertEqual(len(actual), len(set(actual)), "BVH emitted duplicate candidate pairs")

    def test_dense_bvh_batches_cover_every_pair_without_sampling(self):
        # Every AABB contains the origin. Unit leaves force the traversal past
        # its 4096-node-pair batches and the 16384-triangle-pair buffer boundary.
        # This is a broad-phase fixture, not a purported printable surface.
        rng = np.random.default_rng(9012)
        vertices = rng.normal(size=(240, 3, 3))
        vertices[:, 0] = 0
        vertices = vertices.reshape(-1, 3)
        faces = np.arange(len(vertices)).reshape(-1, 3)
        actual = [(int(i), int(j)) for u, v in _bvh_candidates(vertices, faces, leaf_size=1)
                  for i, j in zip(u, v)]
        expected = {(i, j) for i in range(240) for j in range(i + 1, 240)}
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(set(actual), expected)

    def test_crossing_and_coplanar_negatives_match_the_original_oracle(self):
        from types import SimpleNamespace
        from test_snap_lever_mating import proper_triangle_intersections

        cases = [
            ([[0, 0, 0], [2, 0, 0], [0, 2, 0], [.5, .5, -1], [.5, .5, 1], [1.5, .5, 0]], True),
            ([[0, 0, 0], [2, 0, 0], [0, 2, 0], [.2, .2, 0], [1.2, .2, 0], [.2, 1.2, 0]], True),
            ([[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 0], [2, 0, 0], [0, 2, 0]], True),
            ([[0, 0, 0], [2, 0, 0], [0, 2, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0]], False),
            ([[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2], [2, 0, 2], [0, 2, 2]], False),
        ]
        for vertices, expected in cases:
            mesh = SimpleNamespace(vertices=np.asarray(vertices, dtype=float), triangles=np.arange(6).reshape(2, 3))
            self.assertEqual(bool(rugged_proper_intersections(mesh)), expected)
            self.assertEqual(bool(proper_triangle_intersections(mesh)), expected)
        rng = np.random.default_rng(119)
        for _ in range(8):
            # Small soups check numerical equivalence; they are not print meshes.
            mesh = SimpleNamespace(vertices=rng.normal(size=(60, 3)), triangles=np.arange(60).reshape(-1, 3))
            self.assertEqual(bool(rugged_proper_intersections(mesh)), bool(proper_triangle_intersections(mesh)))

    def test_layer_birth_audit_rejects_a_suspended_bulb_in_one_connected_shell(self):
        from box_studio.mesh_generator import _extruded_polygon_mesh

        profiles = [
            # One shell, but the right-hand bulb starts at Z=5 before its
            # upper connecting bridge reaches the grounded left post at Z=9.
            ([[-5, 0], [-4, 0], [-4, 9], [4, 9], [4, 5], [6, 5], [6, 10], [-5, 10]], True),
            # Two grounded posts support their common flat upper bridge.
            ([[-5, 0], [-4, 0], [-4, 9], [4, 9], [4, 0], [6, 0], [6, 10], [-5, 10]], False),
            # The upward-facing cavity floor at Z=5 is not new material.
            ([[-5, 0], [5, 0], [5, 10], [3, 10], [3, 5], [-3, 5], [-3, 10], [-5, 10]], False),
        ]
        for profile, suspended in profiles:
            mesh = _extruded_polygon_mesh(np.asarray(profile, dtype=float), -.5, .5, "fixture", 0)
            self.assertEqual(inspect_mesh(mesh.vertices, mesh.triangles)["components"], 1)
            self.assertEqual(bool(rugged_unsupported_layer_roots(mesh)), suspended)

    def test_actual_rim_contact_does_not_hide_real_overlap(self):
        from types import SimpleNamespace

        mesh = SimpleNamespace(vertices=np.array([[0, 0, 34.5], [1, 0, 34.5], [0, 1, 34.5]]),
                               triangles=np.array([[0, 1, 2]]))
        params = {"height_z": 35, "width_x": 160, "depth_y": 95}
        points = np.array([[.25, .25, 34.5], [.25, .25, 34.48], [2, 2, 34.5], [.25, .25, 32]])
        opposed = SimpleNamespace(vertices=mesh.vertices, triangles=np.array([[0, 2, 1]]))
        np.testing.assert_array_equal(actual_rim_contact(points, mesh, opposed, params), [True, False, False, False])
        self.assertFalse(actual_rim_contact(points[:1], mesh, mesh, params)[0],
                         "Same-facing coincident faces are overlap, not complementary rim contact")

    def test_vectorized_coplanar_kernel_matches_each_original_pair(self):
        from test_snap_lever_mating import _coplanar_area_overlap

        rng = np.random.default_rng(1001)
        for scale in (.001, 1, 100):
            a = rng.normal(size=(120, 3, 2)) * scale
            b = rng.normal(size=(120, 3, 2)) * scale
            expected = np.array([_coplanar_area_overlap(x, y[None])[0] for x, y in zip(a, b)])
            np.testing.assert_array_equal(_coplanar_pair_overlap(a, b), expected)


class RuggedMotionE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = normalize_params({"style": "rugged_box"})
        cls.parts = ("base", "lid", "clip_left", "clip_right")
        cls.meshes = {part: generate_box_mesh(cls.p, part) for part in cls.parts}
        cls.fields = {part: build_part_field(cls.p, part)[0] for part in cls.parts}
        cls.hinge = rugged_hinge_geometry(cls.p)
        cls.axis = [0.0, cls.hinge["y"], cls.hinge["z"]]

    def assert_clear(self, values, context):
        self.assertGreaterEqual(float(np.min(values)), -0.01, context)

    def test_nominal_dimensions_and_spherical_datums(self):
        # Measured manufacturing datums, not an assertion about a mesh bbox:
        # the fittings deliberately project past the nominal body and its rim.
        self.assertEqual(validate_params(self.p), [])
        q = rugged_dimensions(self.p)
        for name, expected in {"width": 160, "depth": 95, "base_height": 35,
                               "lid_height": 20, "height_closed": 55,
                               "wall": 2.5, "floor": 2.5, "radius": 12,
                               "clearance": .15}.items():
            self.assertAlmostEqual(q[name], expected)
        np.testing.assert_allclose(q["fitting_centers"], [-47.25, 47.25], atol=1e-9)
        self.assertAlmostEqual(self.hinge["y"], 52.25)
        self.assertAlmostEqual(self.hinge["z"], 35)
        self.assertAlmostEqual(self.hinge["radius"], 5)
        self.assertAlmostEqual(self.hinge["socket_radius"], 5.125)
        self.assertAlmostEqual(self.hinge["axial_clearance"], .25)
        for part, x in (("clip_left", -47.25), ("clip_right", 47.25)):
            g = rugged_latch_geometry(self.p, part)
            self.assertEqual(g["attachment"], "lid")
            np.testing.assert_allclose([g["pivot"][a] for a in ("x", "y", "z")], [x, -50.5, 45])
            self.assertAlmostEqual(g["radius"], 3.75)
            self.assertAlmostEqual(g["socket_radius"], 3.9)

    def test_actual_boundaries_are_single_closed_oriented_manifold_shells(self):
        for part, mesh in self.meshes.items():
            with self.subTest(part=part):
                report = inspect_mesh(mesh.vertices, mesh.triangles)
                self.assertTrue(report["closed"] and report["oriented"])
                self.assertTrue(report["manifold_vertex_links"])
                self.assertEqual(report["components"], 1)
                self.assertGreater(report["volume_mm3"], 0)
                centers = mesh.vertices[mesh.triangles].mean(axis=1)
                self.assertLessEqual(float(np.abs(self.fields[part](centers)).max()), mesh.interface_error_mm)
                self.assertTrue(np.allclose(np.linalg.norm(mesh.face_normals, axis=1), 1, atol=1e-5))

    def test_actual_boundaries_have_no_proper_crossings_or_coplanar_overlaps(self):
        left, right = self.meshes["clip_left"], self.meshes["clip_right"]
        translation = np.array([94.5, 0, 0], dtype=np.float32)
        identical = (np.array_equal(left.triangles, right.triangles)
                     and np.array_equal(left.vertices + translation, right.vertices))
        for part, mesh in self.meshes.items():
            if part == "clip_right" and identical:
                continue  # Exact rigid-copy proof makes the geometric audit identical.
            with self.subTest(part=part):
                self.assertEqual(rugged_proper_intersections(mesh), [])

    def test_motion_helpers_are_pure_rigid_rotations_about_the_measured_axes(self):
        for part in ("lid", "clip_left", "clip_right"):
            original = self.meshes[part].vertices.copy()
            if part == "lid":
                pivot = self.axis
            else:
                g = rugged_latch_geometry(self.p, part)
                pivot = [g["pivot"][k] for k in ("x", "y", "z")]
            for angle in (0, 1, 10, 25, 45, 90):
                actual = rugged_transform(original, self.p, part, angle)
                np.testing.assert_allclose(actual, rotate_x(original, pivot, -angle), atol=1e-9, rtol=0)
                np.testing.assert_allclose(rugged_transform(np.asarray([pivot]), self.p, part, angle), [pivot], atol=1e-9)
                np.testing.assert_array_equal(self.meshes[part].vertices, original)

    def test_actual_rear_spherical_caps_are_clear_at_rest_and_retained_by_open_socket_lips(self):
        # The sockets have a downward opening, not a closed spherical cage.
        # Their 1 mm axial overlap and narrower mouth require local ear
        # deflection for assembly; a rigid ball must encounter a finite barrier.
        lid = surfaces(self.meshes["lid"], count=100000)
        cap_count = 0
        for cx in (-47.25, 47.25):
            for side in (-1, 1):
                center = np.array([cx + side * 7.0, 52.25, 35.0])
                distance = np.linalg.norm(lid - center, axis=1)
                outside_barrel = (lid[:, 0] - cx) * side > 10.75 - 1e-4
                cap = lid[outside_barrel & (distance > 4.95) & (distance < 5.001)]
                self.assertGreater(len(cap), 8, "Actual hinge lacks the measured spherical cap")
                tip = float(((cap[:, 0] - cx) * side).max())
                self.assertAlmostEqual(tip, 12, delta=.025)
                base = self.meshes["base"].vertices.astype(float)
                face_position = (base[:, 0] - cx) * side
                face = base[(np.abs(face_position - 11) < .02)
                            & (np.abs(base[:, 1] - 52.25) < 4.6)
                            & (np.abs(base[:, 2] - 35) < 4.6)]
                self.assertGreater(len(face), 3, "Base lacks its measured socket inner face")
                engagement = tip - float(np.median((face[:, 0] - cx) * side))
                self.assertAlmostEqual(engagement, 1, delta=.025)
                self.assert_clear(self.fields["base"](cap), "Rear ball already intersects its socket")
                depths = []
                for shift in np.linspace(0, 5, 41):
                    moved = cap.copy()
                    moved[:, 2] -= shift
                    depths.append(float(self.fields["base"](moved).min()))
                self.assertLess(min(depths), -.03, "Rear ball escapes the open socket without a retaining barrier")
                cap_count += 1
        self.assertEqual(cap_count, 4)

    def test_front_journals_are_captured_on_the_lid_after_snap_assembly(self):
        lid_vertices = self.meshes["lid"].vertices.astype(float)
        for part in ("clip_left", "clip_right"):
            g = rugged_latch_geometry(self.p, part)
            pivot = np.array([g["pivot"][k] for k in ("x", "y", "z")])
            raw = self.meshes[part].vertices.astype(float)
            caps = []
            for side in (-1, 1):
                center = pivot + [side * 10.25, 0, 0]
                distance = np.linalg.norm(raw - center, axis=1)
                projection = (raw[:, 0] - pivot[0]) * side
                cap = raw[(projection > 12.5 - 1e-4) & (np.abs(distance - 3.75) < .025)]
                self.assertGreater(len(cap), 8, "Actual latch lacks its spherical journal")
                tip = float(((cap[:, 0] - pivot[0]) * side).max())
                face = lid_vertices[(np.abs((lid_vertices[:, 0] - pivot[0]) * side - 12.75) < .02)
                                    & (np.abs(lid_vertices[:, 1] - pivot[1]) < 4.1)
                                    & (np.abs(lid_vertices[:, 2] - pivot[2]) < 4.1)]
                self.assertGreater(len(face), 3, "Lid lacks the measured socket inner face")
                engagement = tip - float(np.median((face[:, 0] - pivot[0]) * side))
                self.assertAlmostEqual(engagement, 1.25, delta=.025)
                self.assert_clear(self.fields["lid"](cap), "Journal permanently intersects the lid socket")
                caps.append(cap)
            caps = np.vstack(caps)
            for direction in ((0, -1, 0), (-1, 0, 0), (1, 0, 0)):
                depths = []
                for distance in np.linspace(0, 5, 31):
                    moved = caps + np.asarray(direction) * distance
                    depths.append(float(self.fields["lid"](moved).min()))
                self.assertLess(min(depths), -.03,
                                f"{part} journals escape their lid sockets rigidly along {direction}")

    def test_released_lid_and_attached_open_clips_clear_the_base_through_180_degrees(self):
        base = surfaces(self.meshes["base"])
        lid = surfaces(self.meshes["lid"])
        opened_clips = {}
        for part in ("clip_left", "clip_right"):
            g = rugged_latch_geometry(self.p, part)
            pivot = [g["pivot"][k] for k in ("x", "y", "z")]
            opened_clips[part] = rotate_x(surfaces(self.meshes[part]), pivot, -90)
        for degrees in np.linspace(0, 180, 73):
            world = rotate_x(lid, self.axis, -degrees)
            values = self.fields["base"](world)
            if degrees == 0:
                candidates = np.flatnonzero(values < -.01)
                contacts = actual_rim_contact(world[candidates], self.meshes["base"], self.meshes["lid"], self.p)
                accepted = candidates[contacts]
                self.assertGreaterEqual(float(values[accepted].min(initial=0)),
                                        -self.meshes["base"].interface_error_mm - 1e-5)
                values[accepted] = 0  # Actual boundary contact, not analytic chord penetration.
            self.assert_clear(values, f"lid/base at {degrees} degrees")
            local_base = rotate_x(base, self.axis, degrees)
            values = self.fields["lid"](local_base)
            if degrees == 0:
                candidates = np.flatnonzero(values < -.01)
                contacts = actual_rim_contact(local_base[candidates], self.meshes["lid"], self.meshes["base"], self.p)
                accepted = candidates[contacts]
                self.assertGreaterEqual(float(values[accepted].min(initial=0)),
                                        -self.meshes["lid"].interface_error_mm - 1e-5)
                values[accepted] = 0
            self.assert_clear(values, f"base/lid at {degrees} degrees")
            for part, points in opened_clips.items():
                moved = rotate_x(points, self.axis, -degrees)
                self.assert_clear(self.fields["base"](moved), f"{part}/base at {degrees} degrees")
                g = rugged_latch_geometry(self.p, part)
                pivot = [g["pivot"][k] for k in ("x", "y", "z")]
                base_in_clip = rotate_x(local_base, pivot, 90)
                self.assert_clear(self.fields[part](base_in_clip),
                                  f"base/{part} at {degrees} degrees")

    def test_latch_release_flexes_only_the_bounded_lower_cam(self):
        # The nominal cam protrudes to |X-cx|=8.5+5=13.5 while the base
        # cheek begins at 12.75. Up to .75 mm temporary finger deflection is
        # geometrically required; this is not closed preload or a force rating.
        for part in ("clip_left", "clip_right"):
            mesh = self.meshes[part]
            g = rugged_latch_geometry(self.p, part)
            pivot = [g["pivot"][k] for k in ("x", "y", "z")]
            cx, cam_z = pivot[0], self.p["height_z"] - 8.19694
            raw = mesh.vertices.astype(float)
            cam_vertices = raw[(np.abs(raw[:, 2] - cam_z) <= 3.05)
                               & (np.abs(raw[:, 0] - cx) >= 9.9)]
            self.assertGreater(len(cam_vertices), 50)
            points = np.vstack((surfaces(mesh), cam_vertices))
            is_cam = ((np.abs(points[:, 2] - cam_z) <= 3.05)
                      & (np.abs(points[:, 0] - cx) >= 9.9))
            worst = 0.0
            for degrees in np.linspace(0, 90, 91):
                moved = rotate_x(points, pivot, -degrees)
                base = self.fields["base"](moved)
                lid = self.fields["lid"](moved)
                self.assert_clear(lid, f"{part} socket/body clips lid at release {degrees}")
                self.assertTrue(np.all(is_cam[base < -.01]),
                                f"{part} collides outside its lower cam at {degrees} degrees")
                self.assertGreaterEqual(float(base.min()), -(13.5 - 12.75) - mesh.interface_error_mm,
                                        f"{part} requires excessive geometric deflection at {degrees} degrees")
                if degrees in (0, 90):
                    self.assertGreaterEqual(float(base.min()), -1e-5,
                                            f"{part} has permanent closed/released overlap")
                worst = min(worst, float(base.min()))
            self.assertLess(worst, -.03, "Missing actual lower-cam retention barrier")

    def test_engaged_front_clips_hold_lid_before_release(self):
        depths = []
        for part in ("clip_left", "clip_right"):
            points = surfaces(self.meshes[part])
            for angle in (.5, 1, 2, 3):
                moved = rotate_x(points, self.axis, -angle)
                # Only front contacts prove the latch. A collision at the rear
                # spherical hinge must not masquerade as successful retention.
                front = moved[moved[:, 1] < -self.p["depth_y"] / 2]
                self.assertGreater(len(front), 10)
                depths.append(float(self.fields["base"](front).min()))
        self.assertLess(min(depths), -.03, "Closed latches do not obstruct lid opening")

    def test_four_print_poses_and_real_serialized_exports_match_the_closed_preview(self):
        printed = collect_target_meshes(self.p, "base_and_lid", assembled=False)
        self.assertEqual([mesh.part for _, mesh in printed], list(self.parts))
        for _, mesh in printed:
            np.testing.assert_allclose(mesh.vertices, print_vertices(self.meshes[mesh.part].vertices, self.p, mesh.part), atol=3e-5, rtol=0)
            self.assertAlmostEqual(float(mesh.vertices[:, 2].min()), 0, delta=1e-4)
            np.testing.assert_array_equal(mesh.triangles, self.meshes[mesh.part].triangles)
        preview = {"ok": True, "params": self.p, "meshes": [
            {"part": part, "vertices": base64.b64encode(mesh.vertices.astype("<f4").tobytes()).decode(),
             "triangles": base64.b64encode(mesh.triangles.astype("<u4").tobytes()).decode()}
            for part, mesh in self.meshes.items()]}
        host = {"bed_x": 350, "bed_y": 350, "max_z": 260}
        with tempfile.TemporaryDirectory(prefix="orca-rugged-mating-") as directory:
            root = Path(directory)
            stls = [write_binary_stl(root / (mesh.part + ".stl"), mesh) for _, mesh in printed]
            project = write_orca_3mf(root / "actual.3mf", printed, self.p, host)
            for paths in (stls, [project]):
                report = verify_exports(paths, printed, self.p, host, preview, "base_and_lid")
                self.assertTrue(report["ok"], report)
                self.assertEqual(report["object_count"], 4)
                self.assertTrue(report["preview_identity"]["ok"])
                self.assertIn("rugged_separate_parts_without_pin_or_captive_assembly", report["checks"])

    def test_printed_latches_do_not_start_new_suspended_material_islands(self):
        for part in ("clip_left", "clip_right"):
            raw = self.meshes[part].vertices.astype(float)
            printed = orient_mesh_for_print(self.meshes[part], self.p, part)
            vertices = printed.vertices.astype(float)
            affine = np.linalg.lstsq(np.column_stack((raw, np.ones(len(raw)))), vertices, rcond=None)[0]
            rotation, shift = affine[:3], affine[3]
            np.testing.assert_allclose(rotation @ rotation.T, np.eye(3), atol=1e-5, rtol=0)
            np.testing.assert_allclose(raw @ rotation + shift, vertices, atol=3e-5, rtol=0)
            self.assertAlmostEqual(float(vertices[:, 2].min()), 0, delta=1e-4)
            self.assertEqual(rugged_unsupported_layer_roots(printed), [],
                             f"{part} starts a downward-facing boundary component above the bed")

    def test_previous_rugged_presets_are_identified_without_changing_the_saved_features(self):
        old = {"schema_version": 1, "style": "rugged_box", "width_x": 90,
               "depth_y": 65, "height_z": 35, "hinge_mode": "print_in_place",
               "standoffs": [{"x": 0, "y": 0, "height": 8}]}
        p = normalize_params(old)
        self.assertEqual(p["rugged_model"], "legacy")
        self.assertEqual(p["width_x"], 90)
        self.assertEqual(len(p["standoffs"]), 1)
        self.assertTrue(validate_params(p))
        with self.assertRaises(ValueError):
            generate_box_mesh(p)


if __name__ == "__main__":
    unittest.main()
