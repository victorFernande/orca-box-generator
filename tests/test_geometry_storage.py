"""Storage boundaries, analytic complexity budgets and canonical mesh reuse."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.mesh_generator import (
    np,
    generate_box_mesh,
    collect_target_meshes,
    orient_mesh_for_print,
    topology_report,
    build_part_field,
    generate_fit_test_kit,
)
from box_studio.schema import normalize_params, validate_params


class StorageGeometryTests(unittest.TestCase):
    def assert_boundary(self, p, mesh):
        report = topology_report(mesh)
        self.assertTrue(report["closed"], report)
        self.assertTrue(report["oriented"], report)
        self.assertEqual(report["components"], 1, report)
        self.assertGreater(mesh.volume_cm3, 0)
        field, _, _ = build_part_field(p, mesh.part)
        budget = min(p["fit_clearance"] / 4, 0.04)
        self.assertLess(np.max(np.abs(field(mesh.vertices))), budget)
        self.assertLess(
            np.max(np.abs(field(mesh.vertices[mesh.triangles].mean(axis=1)))), budget
        )

    def test_simple_shapes_do_not_tessellate_planar_area(self):
        # Bound complexity, not wall time: a larger planar panel needs no more
        # vertices. This catches a return to globally refined tensor grids.
        for style in ("lip_snap", "open_bin", "snap_latch"):
            counts = []
            for w, d in ((90, 65), (95, 160)):
                p = normalize_params({"style": style, "width_x": w, "depth_y": d})
                items = collect_target_meshes(p, assembled=True)
                total = sum(len(mesh.triangles) for _, mesh in items)
                self.assertLess(total, 10000)
                counts.append(total)
                for _, mesh in items:
                    self.assert_boundary(p, mesh)
            self.assertEqual(counts[0], counts[1])

    def test_handles_have_two_tunnels_in_either_panel_pair(self):
        for faces in ("left_right", "front_back"):
            p = normalize_params(
                {"style": "open_bin", "handle_faces": faces, "fit_clearance": 0.1}
            )
            m = generate_box_mesh(p)
            self.assert_boundary(p, m)
            self.assertEqual(topology_report(m)["genus"], 2)
        p = normalize_params({"style": "open_bin", "handles_enabled": False})
        self.assertEqual(topology_report(generate_box_mesh(p))["genus"], 0)

    def test_lid_wall_below_cap_and_print_pose_are_pure(self):
        p = normalize_params({"style": "snap_latch", "lid_wall_height": 10})
        for _, mesh in collect_target_meshes(p, assembled=True):
            vertices = mesh.vertices.copy()
            triangles = mesh.triangles.copy()
            oriented = orient_mesh_for_print(mesh, p, mesh.part)
            np.testing.assert_array_equal(mesh.vertices, vertices)
            np.testing.assert_array_equal(mesh.triangles, triangles)
            self.assertFalse(np.shares_memory(mesh.vertices, oriented.vertices))
            self.assertFalse(np.shares_memory(mesh.triangles, oriented.triangles))
            self.assertAlmostEqual(oriented.bounds_mm["min"][2], 0, places=5)
            self.assertTrue(topology_report(oriented)["oriented"])
            if mesh.part == "lid":
                self.assertAlmostEqual(
                    mesh.bounds_mm["min"][2], p["height_z"] - 10, places=5
                )
                self.assertAlmostEqual(
                    mesh.bounds_mm["max"][2],
                    p["height_z"] + p["fit_clearance"] + p["lid_height"],
                    places=5,
                )
            if mesh.part.startswith("clip"):
                self.assertAlmostEqual(
                    oriented.bounds_mm["size"][2], mesh.bounds_mm["size"][2], places=5
                )

    def test_factory_receives_actual_targets_and_calibration_is_explicit(self):
        for style, expected in (
            ("open_bin", ["base"]),
            ("snap_latch", ["base", "lid", "clip_left", "clip_right"]),
        ):
            calls = []

            def factory(p, part, print_orientation):
                calls.append((part, print_orientation))
                return generate_box_mesh(p, part, print_orientation)

            collect_target_meshes(
                {"style": style}, "full_suite", assembled=True, mesh_factory=factory
            )
            self.assertEqual(calls, [(part, False) for part in expected])
            with self.assertRaisesRegex(ValueError, "kit|Kit"):
                generate_fit_test_kit({"style": style})
        with self.assertRaisesRegex(ValueError, "open bin"):
            collect_target_meshes({"style": "open_bin"}, "lid_only")

    def test_requested_features_remain_connected_in_csg_fallback(self):
        for style in ("open_bin", "snap_latch"):
            p = normalize_params({"style": style, "standoffs": [{"x": 0, "y": 0}]})
            mesh = generate_box_mesh(p)
            report = topology_report(mesh)
            self.assertTrue(report["closed"], report)
            self.assertTrue(report["oriented"], report)
            self.assertEqual(report["components"], 1, report)
            field, _, _ = build_part_field(p)
            # Annular tower material is really fused to the floor, its bore void.
            self.assertLess(
                field(np.array([[3.0, 0.0, p["floor_thickness"] + 3]]))[0], 0
            )
            self.assertGreater(
                field(np.array([[0.0, 0.0, p["floor_thickness"] + 7]]))[0], 0
            )

    def test_invalid_handles_and_lid_depth_are_actionable(self):
        cases = [
            {"style": "open_bin", "handle_width": 160},
            {"style": "open_bin", "height_z": 16},
            {"style": "snap_latch", "height_z": 16, "lid_wall_height": 25},
            {
                "style": "open_bin",
                "handle_faces": "front_back",
                "cutouts": [{"face": "front", "kind": "usb_c", "z": 20}],
            },
        ]
        for raw in cases:
            self.assertTrue(validate_params(normalize_params(raw)), raw)


if __name__ == "__main__":
    unittest.main()
