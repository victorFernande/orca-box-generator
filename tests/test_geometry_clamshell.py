"""Canonical equal-depth halves and their captive, open print assembly."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.schema import normalize_params, validate_params
from box_studio.mesh_generator import (
    np,
    generate_box_mesh,
    build_part_field,
    collect_target_meshes,
    hinge_geometry,
    clamshell_open_transform,
    clamshell_print_bounds,
    orient_mesh_for_print,
    topology_report,
    generate_fit_test_kit,
)


class ClamshellGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = normalize_params(
            {"style": "clamshell_pip", "height_z": 16, "depth_y": 60}
        )
        cls.meshes = {part: generate_box_mesh(cls.p, part) for part in ("base", "lid")}

    def assert_solid(self, mesh, components=1, euler=None):
        report = topology_report(mesh)
        self.assertTrue(report["closed"], report)
        self.assertTrue(report["oriented"], report)
        self.assertEqual(report["components"], components, report)
        if euler is not None:
            self.assertEqual(report["euler"], euler, report)
        self.assertGreater(mesh.volume_cm3, 0)
        self.assertEqual(len(np.unique(mesh.triangles)), len(mesh.vertices))
        self.assertEqual(len(np.unique(mesh.vertices, axis=0)), len(mesh.vertices))
        pts = mesh.vertices[mesh.triangles].astype(float)
        self.assertTrue(
            np.all(
                np.linalg.norm(
                    np.cross(pts[:, 1] - pts[:, 0], pts[:, 2] - pts[:, 0]), axis=1
                )
                > 0
            )
        )

    def test_equal_external_halves_have_real_floors_and_cavities(self):
        p = self.p
        h = p["height_z"]
        f = p["floor_thickness"]
        c = p["fit_clearance"]
        base, _, _ = build_part_field(p, "base")
        lid, _, _ = build_part_field(p, "lid")
        samples = np.array(
            [
                [0, 0, f / 2],
                [0, 0, f + 1],
                [p["width_x"] / 2 - p["wall_thickness"] / 2, 0, h - 1],
            ]
        )
        mirrored = samples.copy()
        mirrored[:, 2] = 2 * h + c - samples[:, 2]
        np.testing.assert_allclose(base(samples), lid(mirrored), atol=1e-10)
        self.assertLess(base(samples)[0], 0)
        self.assertGreater(base(samples)[1], 0)
        self.assertLess(base(samples)[2], 0)
        self.assert_solid(self.meshes["base"], euler=-6)
        self.assert_solid(self.meshes["lid"], euler=-6)

    def test_transform_is_pure_and_matches_rigid_rotation(self):
        p = self.p
        mesh = self.meshes["lid"]
        original = mesh.vertices.copy()
        tri = mesh.triangles.copy()
        hg = hinge_geometry(p)
        for angle in (0, 45, 90, 135, 180):
            q = clamshell_open_transform(mesh.vertices, p, angle)
            a = -np.deg2rad(angle)
            expected = original.astype(float).copy()
            dy, dz = expected[:, 1] - hg["y"], expected[:, 2] - hg["z"]
            expected[:, 1] = hg["y"] + dy * np.cos(a) - dz * np.sin(a)
            expected[:, 2] = hg["z"] + dy * np.sin(a) + dz * np.cos(a)
            np.testing.assert_allclose(q, expected, atol=3e-5)
            self.assertFalse(np.shares_memory(q, mesh.vertices))
        print_mesh = orient_mesh_for_print(mesh, p, "lid")
        np.testing.assert_array_equal(mesh.vertices, original)
        np.testing.assert_array_equal(mesh.triangles, tri)
        self.assert_solid(print_mesh, euler=-6)
        self.assertEqual(print_mesh.bounds_mm["min"][2], 0)

    def test_print_is_one_open_object_with_two_floors_on_bed(self):
        for target in ("base_and_lid", "full_suite"):
            items = collect_target_meshes(self.p, target, assembled=False)
            self.assertEqual(len(items), 1)
            m = items[0][1]
            self.assertEqual(m.part, "clamshell_pip_assembly")
            self.assert_solid(m, components=2, euler=-12)
            self.assertTrue(np.all(m.vertices[:, 2] >= 0))
            bounds = clamshell_print_bounds(self.p)
            for key in ("min", "max", "size"):
                np.testing.assert_allclose(m.bounds_mm[key], bounds[key], atol=2e-5)
            pts = m.vertices[m.triangles].astype(float)
            on_bed = np.all(pts[:, :, 2] == 0, axis=1)
            center_y = pts[:, :, 1].mean(axis=1)
            on_bed &= (center_y <= self.p["depth_y"] / 2 + 1e-6) | (
                center_y
                >= self.p["depth_y"] / 2 + 2 * self.p["hinge_separation"] - 1e-6
            )
            area = (
                np.linalg.norm(
                    np.cross(pts[:, 1] - pts[:, 0], pts[:, 2] - pts[:, 0]), axis=1
                )
                / 2
            )
            expected = 2 * (
                self.p["width_x"] * self.p["depth_y"]
                - (4 - np.pi) * self.p["corner_radius"] ** 2
            )
            self.assertAlmostEqual(float(area[on_bed].sum()) / expected, 1, delta=0.001)
            self.assertTrue(np.all(m.face_normals[on_bed, 2] < -0.99))

    def test_preview_remains_canonical_and_factory_is_used(self):
        calls = []

        def factory(p, part, printing):
            calls.append((part, printing))
            return (
                orient_mesh_for_print(self.meshes[part], p, part)
                if printing
                else self.meshes[part]
            )

        canonical = collect_target_meshes(
            self.p, "full_suite", assembled=True, mesh_factory=factory
        )
        self.assertEqual([m.part for _, m in canonical], ["base", "lid"])
        self.assertEqual(calls, [("base", False), ("lid", False)])
        calls.clear()
        collect_target_meshes(
            self.p, "full_suite", assembled=False, mesh_factory=factory
        )
        self.assertEqual(calls, [("base", False), ("lid", True)])

    def test_parameter_extremes_stay_compact_manifold_and_match_fields(self):
        cases = [
            {
                "width_x": 60,
                "depth_y": 40,
                "height_z": 10,
                "hinge_pin_diameter": 2,
                "pip_clearance": 0.2,
                "hinge_separation": 4,
            },
            {
                "width_x": 120,
                "depth_y": 80,
                "height_z": 14,
                "corner_radius": 12,
                "hinge_pin_diameter": 6,
                "pip_clearance": 0.6,
                "hinge_separation": 6.2,
                "fit_clearance": 0.4,
            },
        ]
        for kw in cases:
            p = normalize_params({"style": "clamshell_pip", **kw})
            self.assertEqual(validate_params(p), [])
            total = 0
            for part, euler in (("base", -6), ("lid", -6)):
                m = generate_box_mesh(p, part)
                total += len(m.triangles)
                self.assert_solid(m, euler=euler)
                field, _, _ = build_part_field(p, part)
                budget = min(p["fit_clearance"] / 4, p["pip_clearance"] / 4, 0.04)
                self.assertLess(np.max(np.abs(field(m.vertices))), budget)
                self.assertLess(
                    np.max(np.abs(field(m.vertices[m.triangles].mean(axis=1)))), budget
                )
            self.assertLess(total, 15000)

    def test_knuckles_and_endstops_have_real_bed_rooted_pedestals(self):
        p = self.p
        hg = hinge_geometry(p)
        k = hg["knuckle_length"]
        pc = p["pip_clearance"]
        base, _, _ = build_part_field(p, "base")
        lid, _, _ = build_part_field(p, "lid")
        ys = np.linspace(p["depth_y"] / 2 - p["wall_thickness"] / 2, hg["y"] - 0.1, 51)
        for cx in hg["centers"]:
            for side in (-1, 1):
                x = cx + side * (k + pc)
                q = np.column_stack((np.full(len(ys), x), ys, np.full(len(ys), 0.1)))
                self.assertLess(base(q).max(), 0)
            for x in (cx, cx - (1.5 * k + 2 * pc + 0.6), cx + (1.5 * k + 2 * pc + 0.6)):
                q = np.column_stack(
                    (
                        np.full(len(ys), x),
                        ys,
                        np.full(len(ys), 2 * p["height_z"] + p["fit_clearance"] - 0.1),
                    )
                )
                self.assertLess(lid(q).max(), 0)

    def test_previous_seven_styles_keep_single_part_boundaries(self):
        # Compact geometries exercise shared boundary helpers without a repeat
        # of the full preset benchmark owned by the release validation suite.
        for style in (
            "lip_snap",
            "rugged_box",
            "sliding_lid",
            "screw_corner",
            "open_bin",
            "snap_latch",
            "stackable_bin",
        ):
            p = normalize_params(
                {
                    "style": style,
                    "width_x": 45,
                    "depth_y": 35,
                    "height_z": 16,
                    "handles_enabled": False,
                    "latch_width": 10,
                    "front_access_width": 20,
                    "front_access_drop": 4,
                }
            )
            if style in ("snap_latch", "rugged_box"):
                p = normalize_params({"style": style})
            self.assertEqual(validate_params(p), [], style)
            for part in (
                ("base",) if style in ("open_bin", "stackable_bin") else ("base", "lid")
            ):
                with self.subTest(style=style, part=part):
                    self.assert_solid(generate_box_mesh(p, part))

    def test_unsupported_requests_are_explicit_and_not_deleted(self):
        for target in ("base_only", "lid_only", "gasket", "fit_test_kit"):
            with self.assertRaisesRegex(ValueError, "complete open assembly"):
                collect_target_meshes(self.p, target)
        with self.assertRaises(ValueError):
            generate_fit_test_kit(self.p)
        for kw in (
            {"standoffs": [{"x": 0, "y": 0}]},
            {"dividers_x": [0]},
            {"dividers_y": [0]},
            {"cutouts": [{"kind": "usb_c", "z": 8}]},
            {"gasket_enabled": True},
        ):
            p = normalize_params({**self.p, **kw})
            self.assertTrue(validate_params(p), kw)
            for key, value in kw.items():
                self.assertTrue(p[key], (key, value))
            with self.assertRaises(ValueError):
                generate_box_mesh(p)
        for kw in (
            {"width_x": 20},
            {"hinge_pin_diameter": 6, "pip_clearance": 0.6, "hinge_separation": 4},
        ):
            self.assertTrue(validate_params(normalize_params({**self.p, **kw})))


if __name__ == "__main__":
    unittest.main()
