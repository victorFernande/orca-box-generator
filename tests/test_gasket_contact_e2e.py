"""Nominal TPU compression against actual lid lands, not a physical seal rating."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.schema import normalize_params, validate_params
from box_studio.mesh_generator import (
    np,
    build_part_field,
    generate_box_mesh,
    orient_mesh_for_print,
    topology_report,
)


class GasketContactE2E(unittest.TestCase):
    styles = ("lip_snap", "screw_corner", "snap_latch")

    def params(self, style, clearance):
        return normalize_params(
            {
                "style": style,
                "width_x": 70,
                "depth_y": 50,
                "height_z": 30,
                "wall_thickness": 3,
                "fit_clearance": clearance,
                "gasket_enabled": True,
                "gasket_width": 0.8,
                "gasket_depth": 0.8,
            }
        )

    def land_points(self, p, z):
        w, d, t, r = (
            p[k] for k in ("width_x", "depth_y", "wall_thickness", "corner_radius")
        )
        xy = [
            [0, d / 2 - t / 2],
            [0, -d / 2 + t / 2],
            [w / 2 - t / 2, 0],
            [-w / 2 + t / 2, 0],
        ]
        radius = r - t / 2
        xy.extend(
            [
                [
                    sx * (w / 2 - r + radius / np.sqrt(2)),
                    sy * (d / 2 - r + radius / np.sqrt(2)),
                ]
                for sx in (-1, 1)
                for sy in (-1, 1)
            ]
        )
        return np.column_stack((np.asarray(xy), np.full(len(xy), z)))

    def test_counterfactual_old_top_has_gap_at_default_and_large_clearance(self):
        for c, old_gap in ((0.1, -0.05), (0.2, 0.05), (0.4, 0.25)):
            p = self.params("lip_snap", c)
            lid, _, _ = build_part_field(p, "lid")
            # The former fixed H+.15 top is retained as a regression witness.
            actual = lid(self.land_points(p, p["height_z"] + 0.15))
            np.testing.assert_allclose(actual, old_gap, atol=1e-10)

    def test_positive_nominal_compression_for_every_supported_lid_and_clearance(self):
        for style in self.styles:
            for c in (0.1, 0.2, 0.4):
                with self.subTest(style=style, clearance=c):
                    p = self.params(style, c)
                    self.assertEqual(validate_params(p), [])
                    lid, _, _ = build_part_field(p, "lid")
                    gasket, _, _ = build_part_field(p, "gasket")
                    contact = self.land_points(p, p["height_z"] + c + 0.15)
                    np.testing.assert_allclose(gasket(contact), 0, atol=1e-10)
                    np.testing.assert_allclose(lid(contact), -0.15, atol=1e-10)
                    # The true land is a flat lid underside at H+c, with no
                    # gasket recess that could invalidate this compression.
                    np.testing.assert_allclose(
                        lid(self.land_points(p, p["height_z"] + c)), 0, atol=1e-10
                    )

    def test_one_actual_ring_per_style_keeps_channel_dimensions_and_prints_flat(self):
        for style, c in zip(self.styles, (0.1, 0.2, 0.2)):
            with self.subTest(style=style, clearance=c):
                p = self.params(style, c)
                mesh = generate_box_mesh(p, "gasket")
                report = topology_report(mesh)
                self.assertTrue(report["closed"], report)
                self.assertTrue(report["oriented"], report)
                self.assertEqual(report["components"], 1, report)
                self.assertEqual(report["euler"], 0, report)
                self.assertGreater(mesh.volume_cm3, 0)
                bottom = p["height_z"] - p["gasket_depth"] + 0.05
                top = p["height_z"] + c + 0.15
                np.testing.assert_allclose(mesh.bounds_mm["min"][2], bottom, atol=1e-5)
                np.testing.assert_allclose(mesh.bounds_mm["max"][2], top, atol=1e-5)
                np.testing.assert_allclose(
                    mesh.bounds_mm["size"][:2],
                    [
                        p["width_x"] - p["wall_thickness"] + p["gasket_width"] - 0.12,
                        p["depth_y"] - p["wall_thickness"] + p["gasket_width"] - 0.12,
                    ],
                    atol=2e-5,
                )
                pts = mesh.vertices[mesh.triangles].mean(axis=1)
                upper = pts[np.abs(pts[:, 2] - top) < 1e-5]
                self.assertGreater(len(upper), 10)
                lid, _, _ = build_part_field(p, "lid")
                np.testing.assert_allclose(lid(upper), -0.15, atol=1e-5)
                in_channel = pts[
                    (pts[:, 2] > bottom + 0.01) & (pts[:, 2] < p["height_z"] - 0.01)
                ]
                self.assertGreater(len(in_channel), 10)
                base, _, _ = build_part_field(p, "base")
                self.assertGreater(float(base(in_channel).min()), 0.01)
                original = mesh.vertices.copy()
                triangles = mesh.triangles.copy()
                printed = orient_mesh_for_print(mesh, p, "gasket")
                np.testing.assert_array_equal(mesh.vertices, original)
                np.testing.assert_array_equal(mesh.triangles, triangles)
                self.assertEqual(printed.bounds_mm["min"][2], 0)
                np.testing.assert_allclose(
                    printed.bounds_mm["size"][2], p["gasket_depth"] + c + 0.1, atol=1e-5
                )
                printed_report = topology_report(printed)
                self.assertTrue(printed_report["closed"] and printed_report["oriented"])
                self.assertEqual(printed_report["euler"], 0)

    def test_rugged_preserves_a_requested_gasket_and_rejects_generation_explicitly(self):
        for clearance in (.1, .15, .3):
            with self.subTest(clearance=clearance):
                base = normalize_params({"style": "rugged_box", "fit_clearance": clearance})
                self.assertEqual(validate_params(base), [])
                requested = normalize_params({**base, "gasket_enabled": True})
                self.assertTrue(requested["gasket_enabled"], "An unsupported request must not be silently removed")
                errors = validate_params(requested)
                self.assertEqual(len(errors), 1)
                self.assertIn("gasket", errors[0])
                for part in ("base", "gasket"):
                    with self.assertRaisesRegex(ValueError, "gasket"):
                        generate_box_mesh(requested, part)


if __name__ == "__main__":
    unittest.main()
