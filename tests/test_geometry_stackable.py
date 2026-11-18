"""Own stackable-bin boundaries, dimensions, feature preservation and API rules."""

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
    generate_fit_test_kit,
    stacking_pose_z,
    topology_report,
    orient_mesh_for_print,
)


class StackableGeometryTests(unittest.TestCase):
    def params(self, **kw):
        return normalize_params({"style": "stackable_bin", **kw})

    def assert_boundary(self, p, m):
        report = topology_report(m)
        self.assertTrue(report["closed"], report)
        self.assertTrue(report["oriented"], report)
        self.assertEqual(report["components"], 1, report)
        self.assertEqual(report["euler"], 2, report)
        self.assertGreater(m.volume_cm3, 0)
        tri = m.vertices[m.triangles].astype(float)
        self.assertTrue(
            np.all(
                np.linalg.norm(
                    np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1
                )
                > 0
            )
        )
        self.assertEqual(len(np.unique(m.triangles)), len(m.vertices))
        self.assertEqual(len(np.unique(m.vertices, axis=0)), len(m.vertices))
        return report

    def test_total_height_includes_foot_and_planar_complexity_is_constant(self):
        counts = []
        for w, d, h in ((90, 65, 35), (95, 160, 83), (140, 100, 80)):
            p = self.params(width_x=w, depth_y=d, height_z=h)
            m = generate_box_mesh(p)
            self.assert_boundary(p, m)
            self.assertEqual(m.bounds_mm["min"][2], 0)
            self.assertEqual(m.bounds_mm["max"][2], h)
            self.assertLess(len(m.triangles), 3000)
            counts.append(len(m.triangles))
        self.assertEqual(len(set(counts)), 1)

    def test_small_clearance_and_corner_variants_match_analytic_field(self):
        for r, sc, fh in ((4, 0.1, 1), (8, 0.8, 5), (0.8, 0.25, 2)):
            p = self.params(corner_radius=r, stack_clearance=sc, stack_foot_height=fh)
            m = generate_box_mesh(p)
            self.assert_boundary(p, m)
            field, _, _ = build_part_field(p)
            budget = min(p["fit_clearance"] / 4, sc / 4, 0.04)
            self.assertLess(np.max(np.abs(field(m.vertices))), budget)
            self.assertLess(
                np.max(np.abs(field(m.vertices[m.triangles].mean(axis=1)))), budget
            )

    def test_foot_floor_and_front_opening_are_real_solid_and_void(self):
        p = self.params()
        h = p["height_z"]
        fh = p["stack_foot_height"]
        f = p["floor_thickness"]
        front = -p["depth_y"] / 2 + p["wall_thickness"] / 2
        field, _, _ = build_part_field(p)
        self.assertLess(field(np.array([[0, 0, fh / 2], [0, 0, fh + f / 2]])).max(), 0)
        self.assertGreater(
            field(np.array([[0, 0, fh + f + 1], [0, front, h - 1]])).min(), 0
        )
        self.assertLess(
            field(np.array([[0, front, h - p["front_access_drop"] - 1]]))[0], 0
        )
        self.assertLess(
            field(np.array([[p["width_x"] / 2 - p["wall_thickness"] / 2, 0, h - 1]]))[
                0
            ],
            0,
        )

    def test_same_family_allows_different_heights_and_front_access(self):
        lower = self.params(height_z=37)
        upper = self.params(height_z=83, front_access_width=50, front_access_drop=30)
        self.assertEqual(stacking_pose_z(lower, upper), 35)
        self.assertEqual(stacking_pose_z(upper, lower), 81)
        self.assertEqual(stacking_pose_z(lower), 35)
        for key, value in (
            ("width_x", 95),
            ("depth_y", 75),
            ("wall_thickness", 3),
            ("corner_radius", 5),
            ("stack_foot_height", 3),
            ("stack_clearance", 0.4),
        ):
            with self.subTest(key=key):
                different = dict(upper)
                different[key] = value
                with self.assertRaisesRegex(ValueError, "family"):
                    stacking_pose_z(lower, different)

    def test_targets_have_only_base_and_print_pose_does_not_mutate(self):
        p = self.params()
        for target in ("base_only", "base_and_lid", "full_suite"):
            items = collect_target_meshes(p, target, assembled=True)
            self.assertEqual([m.part for _, m in items], ["base"])
        for target in ("lid_only", "gasket", "fit_test_kit"):
            with self.assertRaises(ValueError):
                collect_target_meshes(p, target)
        with self.assertRaises(ValueError):
            generate_fit_test_kit(p)
        with self.assertRaises(ValueError):
            generate_box_mesh(p, "lid")
        m = generate_box_mesh(p)
        original = m.vertices.copy()
        tri = m.triangles.copy()
        print_mesh = orient_mesh_for_print(m, p, "base")
        np.testing.assert_array_equal(original, m.vertices)
        np.testing.assert_array_equal(tri, m.triangles)
        self.assertFalse(np.shares_memory(print_mesh.vertices, m.vertices))
        self.assertFalse(np.shares_memory(print_mesh.triangles, m.triangles))

    def test_invalid_access_and_internal_obstructions_are_rejected(self):
        cases = [
            {"front_access_width": 300},
            {"front_access_drop": 32},
            {"height_z": 10, "stack_foot_height": 5},
            {"gasket_enabled": True},
            {"standoffs": [{"height": 30}]},
            {"cutouts": [{"face": "front", "kind": "usb_c", "z": 20}]},
        ]
        for kw in cases:
            with self.subTest(params=kw):
                self.assertTrue(validate_params(self.params(**kw)))

    def test_csg_features_share_floor_and_preserve_port_and_bore(self):
        p = self.params(
            standoffs=[{"x": -15, "y": 8}],
            dividers_x=[15],
            cutouts=[{"face": "front", "kind": "usb_c", "u": 0, "z": 9}],
        )
        self.assertEqual(validate_params(p), [])
        m = generate_box_mesh(p)
        # The one port is a tunnel, so Euler zero (genus one) is intentional.
        report = topology_report(m)
        self.assertTrue(report["closed"], report)
        self.assertTrue(report["oriented"], report)
        self.assertEqual(report["components"], 1, report)
        self.assertEqual(report["euler"], 0, report)
        field, _, _ = build_part_field(p)
        floor = p["stack_foot_height"] + p["floor_thickness"]
        self.assertLess(
            field(np.array([[-12.0, 8.0, floor + 3], [15.0, 0.0, floor + 3]])).max(), 0
        )
        self.assertGreater(
            field(
                np.array([[-15.0, 8.0, floor + 7], [0.0, -p["depth_y"] / 2 + 1, 9.0]])
            ).min(),
            0,
        )


if __name__ == "__main__":
    unittest.main()
