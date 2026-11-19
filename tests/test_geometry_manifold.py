"""Topology, fitted interfaces, functional motion and feature integration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import unittest
from box_studio.schema import normalize_params, validate_params
from box_studio.mesh_generator import (
    np,
    generate_box_mesh,
    generate_fit_test_kit,
    collect_target_meshes,
    topology_report,
    build_part_field,
    hinge_geometry,
)
from box_studio.presets_catalog import BUILTIN_PRESETS


class GeometryTests(unittest.TestCase):
    def assertSolid(self, mesh, components=1):
        report = topology_report(mesh)
        self.assertTrue(report["closed"], report)
        self.assertTrue(report["oriented"], report)
        self.assertEqual(report["components"], components, report)
        self.assertEqual(report["euler"] % 2, 0, report)
        self.assertGreater(mesh.volume_cm3, 0)
        self.assertTrue(np.isfinite(mesh.vertices).all())
        self.assertEqual(len(np.unique(mesh.vertices, axis=0)), len(mesh.vertices))
        self.assertEqual(len(np.unique(mesh.triangles)), len(mesh.vertices))
        vertices = mesh.vertices[mesh.triangles].astype(np.float64)
        area = np.linalg.norm(
            np.cross(vertices[:, 1] - vertices[:, 0], vertices[:, 2] - vertices[:, 0]),
            axis=1,
        )
        self.assertTrue(np.all(area > 0))
        self.assertTrue(
            np.allclose(np.linalg.norm(mesh.face_normals, axis=1), 1, atol=1e-5)
        )

    def test_01_four_styles_closed_oriented_and_connected(self):
        for style in ("lip_snap", "rugged_box", "sliding_lid", "screw_corner"):
            for part in ("base", "lid"):
                with self.subTest(style=style, part=part):
                    self.assertSolid(generate_box_mesh({"style": style}, part))

    def test_02_all_eight_standard_presets(self):
        self.assertEqual(len(BUILTIN_PRESETS), 8)
        for preset in BUILTIN_PRESETS:
            self.assertEqual(validate_params(preset["params"]), [], preset["id"])
            for part in (
                ("base",)
                if preset["params"]["style"] in ("open_bin", "stackable_bin")
                else ("base", "lid")
            ):
                with self.subTest(preset=preset["id"], part=part):
                    self.assertSolid(generate_box_mesh(preset["params"], part))

    def test_03_actual_ports_posts_and_dividers(self):
        p = normalize_params(
            {
                "style": "screw_corner",
                "height_z": 40,
                "standoffs": [
                    {
                        "x": -20,
                        "y": 10,
                        "height": 8,
                        "hole_diameter": 4.2,
                        "hole_depth": 5,
                    }
                ],
                "dividers_x": [10],
                "dividers_y": [-12],
                "cutouts": [
                    {"kind": "usb_c", "face": "front", "u": 0, "z": 15},
                    {"kind": "dc", "face": "right", "u": 0, "z": 15},
                ],
            }
        )
        field, _, _ = build_part_field(p, "base")
        points = np.array(
            [
                [0, -p["depth_y"] / 2 + 1, 15],
                [-20, 10, p["floor_thickness"] + 7],
                [-20 + 3, 10, p["floor_thickness"] + 5],
                [10, 0, 12],
                [0, -12, 12],
            ]
        )
        values = field(points)
        self.assertGreater(values[0], 0, "Port must be a real tunnel")
        self.assertGreater(values[1], 0, "Post bore must be void")
        self.assertTrue(
            np.all(values[2:] < 0), "Post material and dividers must be solid"
        )
        self.assertSolid(generate_box_mesh(p, "base"))

    def test_04_snap_groove_bead_and_interface_error(self):
        p = normalize_params({"fit_clearance": 0.1})
        h = p["height_z"]
        b = p["depth_y"] / 2 - p["wall_thickness"]
        base, _, _ = build_part_field(p, "base")
        lid, _, _ = build_part_field(p, "lid")
        point = np.array([[0, b + 0.07, h - 2.23]])
        self.assertGreater(base(point)[0], 0, "Female retaining groove is missing")
        self.assertLess(lid(point)[0], 0, "Male snap bead is missing")
        for style in ("lip_snap", "sliding_lid"):
            p = normalize_params({"style": style, "fit_clearance": 0.1})
            m = generate_box_mesh(p, "lid")
            field, _, _ = build_part_field(p, "lid")
            centers = m.vertices[m.triangles].mean(axis=1)
            error = float(np.max(np.abs(field(centers))))
            self.assertLess(error, min(p["fit_clearance"] / 4, 0.04))

    def test_05_rugged_snap_hinge_keeps_four_separate_printable_parts(self):
        p = normalize_params({"style": "rugged_box"})
        expected = ["base", "lid", "clip_left", "clip_right"]
        canonical = collect_target_meshes(p, "base_and_lid", assembled=True)
        printed = collect_target_meshes(p, "base_and_lid", assembled=False)
        self.assertEqual([mesh.part for _, mesh in canonical], expected)
        self.assertEqual([mesh.part for _, mesh in printed], expected)
        for (_, closed), (_, placed) in zip(canonical, printed):
            with self.subTest(part=closed.part):
                self.assertSolid(closed)
                self.assertSolid(placed)
                self.assertAlmostEqual(placed.bounds_mm["min"][2], 0, places=4)
                self.assertEqual(len(placed.vertices), len(closed.vertices))
                self.assertEqual(len(placed.triangles), len(closed.triangles))
                self.assertAlmostEqual(placed.volume_cm3, closed.volume_cm3, places=6)
        # A snapped spherical hinge is assembled after printing; it must never
        # be serialized as the previous captive pair, nor require a fifth pin.
        with self.assertRaises(ValueError):
            generate_box_mesh(p, "pin")
        for target, parts in (("base_only", ["base"]), ("lid_only", ["lid"]),
                              ("full_suite", expected)):
            self.assertEqual([mesh.part for _, mesh in collect_target_meshes(p, target)], parts)
        for target in ("gasket", "fit_test_kit"):
            with self.subTest(unsupported=target), self.assertRaises(ValueError):
                collect_target_meshes(p, target)
        with self.assertRaises(ValueError):
            generate_fit_test_kit(p)

    def test_06_fit_kit_and_tpu_gasket(self):
        for _, mesh in generate_fit_test_kit():
            self.assertSolid(mesh)
        p = normalize_params(
            {"style": "screw_corner", "gasket_enabled": True, "wall_thickness": 3}
        )
        gasket = generate_box_mesh(p, "gasket", True)
        self.assertSolid(gasket)
        self.assertEqual(topology_report(gasket)["genus"], 1)

    def test_07_invalid_feature_combinations_are_reported(self):
        for raw in (
            {"standoffs": [{"x": 1000}]},
            {"floor_thickness": 8, "standoffs": [{"height": 30}]},
            {"style": "sliding_lid", "gasket_enabled": True},
            {"cutouts": [{"kind": "usb_c", "z": 3}]},
            {"standoffs": [{"x": 0, "y": 0}], "dividers_x": [0]},
        ):
            p = normalize_params(raw)
            self.assertTrue(validate_params(p))
            with self.assertRaises(ValueError):
                generate_box_mesh(p)
        p = normalize_params({"standoffs": [{"mode": "pilot", "insert": "M3"}]})
        self.assertEqual(p["standoffs"][0]["hole_diameter"], 2.5)

    def test_08_fit_kit_replicates_custom_bore_diameter_and_depth(self):
        items = generate_fit_test_kit(
            {
                "standoffs": [
                    {
                        "x": 0,
                        "y": 0,
                        "height": 8,
                        "outer_diameter": 7,
                        "hole_diameter": 3.2,
                        "hole_depth": 4,
                        "insert": "M2",
                    }
                ]
            }
        )
        base = items[0][1]
        self.assertSolid(base)
        v = base.vertices
        near_bore = (
            (np.abs(np.hypot(v[:, 0], v[:, 1]) - 1.6) < 0.01)
            & (v[:, 2] > 3.5)
            & (v[:, 2] < 7.7)
        )
        bore = v[near_bore]
        self.assertGreater(len(bore), 10)
        self.assertAlmostEqual(
            float(bore[:, 2].max() - bore[:, 2].min()), 4, delta=0.02
        )
        self.assertAlmostEqual(float(bore[:, 2].min()), 3.6, delta=0.02)


if __name__ == "__main__":
    unittest.main()
