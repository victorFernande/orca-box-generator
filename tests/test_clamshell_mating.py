"""Independent geometry, support and captive-motion checks for the PIP case.

This is sampled rigid geometry, not elastic-contact, support-free printing,
release-force, fatigue or load validation. Export round trips live separately.
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio import mesh_generator as geometry
from box_studio.schema import normalize_params, validate_params
import test_functional_mating as mating

np = geometry.np


def rotate_about_x(points, axis, degrees):
    result = np.asarray(points, dtype=float).copy()
    angle = math.radians(degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    y, z = result[:, 1] - axis["y"], result[:, 2] - axis["z"]
    result[:, 1] = axis["y"] + cosine * y - sine * z
    result[:, 2] = axis["z"] + sine * y + cosine * z
    return result


def actual_samples(mesh):
    vertices = mesh.vertices.astype(float)
    faces = vertices[mesh.triangles]
    return np.concatenate((vertices, faces.mean(axis=1),
                           faces[:, 0] * .6 + faces[:, 1] * .2 + faces[:, 2] * .2))


def bed_floor_area(mesh, vertices):
    triangles = vertices[mesh.triangles]
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    on_bed = (np.max(np.abs(triangles[:, :, 2]), axis=1) < 1e-4) & (cross[:, 2] < 0)
    return float(np.linalg.norm(cross[on_bed], axis=1).sum() / 2)


def layer_outer_contours(mesh, vertices, height):
    """Slice the actual oriented triangles; positive contours are solid islands.

    Heights are strictly between vertex events, avoiding coplanar-face ambiguity.
    Rings contribute one positive outer contour and a negative hole contour.
    """
    triangles = vertices[mesh.triangles]
    active = (triangles[:, :, 2].min(axis=1) < height) & (triangles[:, :, 2].max(axis=1) > height)
    outgoing = {}
    scale = 1e6
    for triangle in triangles[active]:
        hits = []
        for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
            if (a[2] < height) != (b[2] < height):
                hits.append((a + (b - a) * ((height - a[2]) / (b[2] - a[2])))[:2])
        if len(hits) != 2:
            raise AssertionError("A noncritical slice must cross two triangle edges")
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        tangent = np.array([-normal[1], normal[0]])
        if np.dot(hits[1] - hits[0], tangent) < 0:
            hits.reverse()
        a, b = (tuple(np.rint(point * scale).astype(np.int64)) for point in hits)
        if a == b:
            continue
        if a in outgoing and outgoing[a] != b:
            raise AssertionError("Ambiguous or intersecting layer boundary")
        outgoing[a] = b
    contours = []
    remaining = set(outgoing)
    while remaining:
        start = next(iter(remaining)); point = start; loop = []
        while True:
            if point not in remaining:
                if point != start:
                    raise AssertionError("Layer contour failed to close")
                break
            remaining.remove(point); loop.append(point)
            if point not in outgoing:
                raise AssertionError("Layer has an open boundary")
            point = outgoing[point]
        polygon = np.asarray(loop, dtype=float) / scale
        area = float(np.sum(polygon[:, 0] * np.roll(polygon[:, 1], -1)
                            - polygon[:, 1] * np.roll(polygon[:, 0], -1)) / 2)
        if area > 1e-6:
            contours.append((polygon, area))
    return contours


def polygon_probes(polygon):
    centre = polygon.mean(axis=0)
    mids = (polygon + np.roll(polygon, -1, axis=0)) / 2
    candidates = [centre[None, :]]
    for fraction in (.001, .05, .2, .5):
        candidates.append(mids * (1 - fraction) + centre * fraction)
    low, high = polygon.min(axis=0), polygon.max(axis=0)
    candidates.append(np.stack(np.meshgrid(np.linspace(low[0], high[0], 11),
                                          np.linspace(low[1], high[1], 11)), -1).reshape(-1, 2))
    candidates = np.concatenate(candidates)
    inside = np.zeros(len(candidates), dtype=bool)
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        if abs(b[1] - a[1]) < 1e-12:
            continue
        inside ^= ((a[1] > candidates[:, 1]) != (b[1] > candidates[:, 1])) & (
            candidates[:, 0] < (b[0] - a[0]) * (candidates[:, 1] - a[1]) / (b[1] - a[1]) + a[0])
    return candidates[inside]


class ClamshellMatingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = normalize_params({"style": "clamshell_pip", "width_x": 90,
                                  "depth_y": 65, "height_z": 25,
                                  "fit_clearance": .2, "pip_clearance": .3})
        if cls.p["style"] != "clamshell_pip" or validate_params(cls.p):
            raise AssertionError("Valid equal-depth captive case parameters are required")
        cls.meshes = dict((mesh.part, mesh) for _, mesh in
                          geometry.collect_target_meshes(cls.p, "base_and_lid", assembled=True))
        cls.fields = {part: geometry.build_part_field(cls.p, part)[0] for part in ("base", "lid")}
        cls.axis = geometry.hinge_geometry(cls.p)
        cls.samples = {part: actual_samples(mesh) for part, mesh in cls.meshes.items()}

    def test_each_half_is_one_real_manifold_shell_with_correct_hinge_topology(self):
        self.assertEqual(set(self.meshes), {"base", "lid"})
        for part, expected_euler in (("base", -6), ("lid", -6)):
            with self.subTest(part=part):
                mesh = self.meshes[part]
                actual = mating.FunctionalMatingTests().assert_meshed_boundary(self.p, part, mesh)
                self.assertEqual(actual, expected_euler)
                points = mesh.vertices[mesh.triangles].astype(float)
                cross = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
                normal = cross / np.linalg.norm(cross, axis=1)[:, None]
                centre = points.mean(axis=1)
                field = self.fields[part]
                self.assertGreaterEqual(float(field(centre + normal * .05).min()), -1e-4,
                                        "Exterior normals must agree with the analytic unified solid")
                self.assertLessEqual(float(field(centre - normal * .05).max()), 1e-4)

    def test_equal_body_depth_and_both_open_floors_have_real_bed_area(self):
        p = self.p; h = p["height_z"]; c = p["fit_clearance"]; floor = p["floor_thickness"]
        x = p["width_x"] / 2 - p["wall_thickness"] / 2
        base, lid = self.fields["base"], self.fields["lid"]
        self.assertLess(float(base(np.array([[0, 0, floor / 2]]))[0]), 0)
        self.assertGreater(float(base(np.array([[0, 0, floor + .1]]))[0]), 0)
        self.assertLess(float(base(np.array([[x, 0, h - .01]]))[0]), 0)
        self.assertGreater(float(base(np.array([[x, 0, h + .01]]))[0]), 0)
        self.assertLess(float(lid(np.array([[0, 0, 2*h+c-floor/2]]))[0]), 0)
        self.assertGreater(float(lid(np.array([[0, 0, 2*h+c-floor-.1]]))[0]), 0)
        self.assertLess(float(lid(np.array([[x, 0, h+c+.01]]))[0]), 0)
        self.assertGreater(float(lid(np.array([[x, 0, h+c-.01]]))[0]), 0)
        self.assertAlmostEqual(float(self.meshes["lid"].vertices[:, 2].max()), 2*h+c, delta=1e-4)
        for part in ("base", "lid"):
            mesh = self.meshes[part]
            opened = (mesh.vertices.astype(float) if part == "base" else
                      geometry.clamshell_open_transform(mesh.vertices, p, 180))
            self.assertGreaterEqual(float(opened[:, 2].min()), -1e-4)
            self.assertAlmostEqual(float(opened[:, 2].min()), 0, delta=1e-4)
            self.assertGreater(bed_floor_area(mesh, opened), p["width_x"] * p["depth_y"] * .5,
                               "Both moving halves need a broad real floor on the bed")

    def test_print_layer_events_have_no_new_hinge_islands_below_the_rim(self):
        # Whole-shell connectivity is insufficient: an elevated barrel or head
        # can start as an isolated print island and join the wall many layers later.
        # Between mesh vertex-Z events the section topology is unchanged, so
        # slicing every interval catches those starts without choosing one layer height.
        for part in ("base", "lid"):
            mesh = self.meshes[part]
            vertices = (mesh.vertices.astype(float) if part == "base" else
                        geometry.clamshell_open_transform(mesh.vertices, self.p, 180))
            levels = np.unique(vertices[:, 2])
            levels = np.r_[0., levels[(levels > 1e-5) & (levels < self.p["height_z"] - 1e-5)],
                           self.p["height_z"]]
            for low, high in zip(levels, levels[1:]):
                if high - low < 1e-4:
                    continue
                height = float((low + high) / 2)
                with self.subTest(part=part, height=height):
                    contours = layer_outer_contours(mesh, vertices, height)
                    self.assertGreater(len(contours), 0)
                    for polygon, area in contours:
                        xy = polygon_probes(polygon)
                        current = np.column_stack((xy, np.full(len(xy), height)))
                        query = (current if part == "base" else
                                 rotate_about_x(current, self.axis, 180))
                        current = current[self.fields[part](query) < -1e-5]
                        self.assertGreater(len(current), 0, "Layer interior must match the analytic solid")
                        if low <= 1e-5:
                            continue  # Initial material starts on the bed.
                        # An upper section can split into several supported islands.
                        # Reject births without overlap with material immediately
                        # below the event; do not demand one contour on every layer.
                        previous = current.copy(); previous[:, 2] = low - 1e-4
                        query = (previous if part == "base" else
                                 rotate_about_x(previous, self.axis, 180))
                        self.assertLessEqual(float(self.fields[part](query).min()), 1e-4,
                            f"New unsupported {area:.4f} mm² island in {part} near Z={low}")

    def test_open_transform_is_pure_and_matches_independent_rotation(self):
        original = self.meshes["lid"].vertices.copy()
        for angle in (0, 27.5, 90, 180):
            moved = geometry.clamshell_open_transform(original, self.p, angle)
            expected = rotate_about_x(original, self.axis, -angle)
            np.testing.assert_allclose(moved, expected, atol=1e-4, rtol=0)
            self.assertFalse(np.shares_memory(original, moved))
        np.testing.assert_array_equal(original, self.meshes["lid"].vertices)

    def test_actual_mesh_motion_avoids_both_halves_in_both_query_directions(self):
        angles = np.unique(np.r_[np.linspace(0, 180, 73),
                                 [.1, .25, .5, 1, 2, 178, 179, 179.5, 179.75, 179.9]])
        for angle in angles:
            with self.subTest(angle=float(angle)):
                moved_lid = geometry.clamshell_open_transform(self.samples["lid"], self.p, angle)
                self.assertGreaterEqual(float(self.fields["base"](moved_lid).min()), -1e-4)
                base_in_lid_frame = rotate_about_x(self.samples["base"], self.axis, angle)
                self.assertGreaterEqual(float(self.fields["lid"](base_in_lid_frame).min()), -1e-4)

    def test_integral_axle_end_stops_provide_real_axial_capture(self):
        pc = self.p["pip_clearance"]
        for sign in (-1, 1):
            with self.subTest(direction=sign):
                freely_shifted = self.samples["lid"] + [sign * pc * .8, 0, 0]
                self.assertGreaterEqual(float(self.fields["base"](freely_shifted).min()), -1e-4)
                captured = self.samples["lid"] + [sign * (pc + .4), 0, 0]
                self.assertLess(float(self.fields["base"](captured).min()), -.02,
                                "Integral end stops must not pass freely through the bearing bores")

    def test_open_collection_preserves_both_halves_as_one_print_assembly(self):
        items = geometry.collect_target_meshes(self.p, "base_and_lid", assembled=False)
        self.assertEqual(len(items), 1)
        assembly = items[0][1]
        self.assertEqual(assembly.part, "clamshell_pip_assembly")
        expected = np.concatenate((self.meshes["base"].vertices,
                    geometry.clamshell_open_transform(self.meshes["lid"].vertices, self.p, 180)))
        np.testing.assert_array_equal(assembly.vertices, expected.astype(np.float32))
        helper = geometry.clamshell_print_bounds(self.p)
        np.testing.assert_allclose(assembly.vertices.min(axis=0), helper["min"], atol=1e-4, rtol=0)
        np.testing.assert_allclose(assembly.vertices.max(axis=0), helper["max"], atol=1e-4, rtol=0)

    def test_individual_targets_and_unimplemented_features_are_rejected(self):
        for target in ("base_only", "lid_only", "gasket", "fit_test_kit"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                geometry.collect_target_meshes(self.p, target, assembled=False)
        for update in ({"dividers_x": [0]}, {"gasket_enabled": True},
                       {"standoffs": [{"x": 0, "y": 0}]},
                       {"cutouts": [{"kind": "usb_c", "face": "front", "u": 0, "z": 10}]}):
            with self.subTest(update=update):
                candidate = dict(self.p); candidate.update(update)
                self.assertTrue(validate_params(normalize_params(candidate)),
                                "Unsupported features must raise a useful error rather than disappear")


if __name__ == "__main__":
    unittest.main()
