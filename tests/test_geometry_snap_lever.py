"""Four printable parts: captive pivots, frontal lever grips and a removable lid."""

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
    topology_report,
    latch_geometry,
    latch_open_transform,
    orient_mesh_for_print,
)


class SnapLeverGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = normalize_params({"style": "snap_latch"})
        cls.meshes = {
            part: generate_box_mesh(cls.p, part)
            for part in ("base", "lid", "clip_left", "clip_right")
        }

    def test_real_parts_are_single_closed_boundaries_matching_fields(self):
        for part, m in self.meshes.items():
            report = topology_report(m)
            self.assertTrue(report["closed"], (part, report))
            self.assertTrue(report["oriented"], (part, report))
            self.assertEqual(report["components"], 1, (part, report))
            self.assertEqual(report["euler"], 2, (part, report))
            self.assertGreater(m.volume_cm3, 0)
            field, _, _ = build_part_field(self.p, part)
            self.assertLess(np.abs(field(m.vertices)).max(), 0.01)
            self.assertLess(
                np.abs(field(m.vertices[m.triangles].mean(axis=1))).max(), 0.02
            )
        self.assertLess(sum(len(m.triangles) for m in self.meshes.values()), 12000)

    def test_motion_helper_rotates_about_base_pivot_without_mutation(self):
        for part in ("clip_left", "clip_right"):
            m = self.meshes[part]
            vertices = m.vertices.copy()
            g = latch_geometry(self.p, part)
            self.assertEqual(g["release_angle"], 90)
            self.assertEqual(g["release_fraction"], 0.35)
            self.assertEqual(g["lid_lift_mm"], 50)
            self.assertLess(g["hook_y"], g["pivot"]["y"])
            for angle in (0, 25, 90):
                actual = latch_open_transform(vertices, self.p, part, angle)
                a = np.deg2rad(angle)
                expected = vertices.astype(float).copy()
                y, z = (
                    vertices[:, 1] - g["pivot"]["y"],
                    vertices[:, 2] - g["pivot"]["z"],
                )
                expected[:, 1] = g["pivot"]["y"] + y * np.cos(a) - z * np.sin(a)
                expected[:, 2] = g["pivot"]["z"] + y * np.sin(a) + z * np.cos(a)
                np.testing.assert_allclose(actual, expected, atol=4e-6)
            np.testing.assert_array_equal(vertices, m.vertices)

    def test_large_hub_and_thin_grip_intersection_is_a_true_union(self):
        cases = [
            {
                "fit_clearance": c,
                "latch_retention": 0.2,
                "latch_thickness": 1.2,
                "latch_pivot_diameter": 4,
            }
            for c in (0.1, 0.4)
        ]
        cases.append(
            {
                "width_x": 120,
                "depth_y": 90,
                "height_z": 45,
                "wall_thickness": 3,
                "latch_retention": 1.2,
                "latch_thickness": 4,
                "latch_pivot_diameter": 4,
                "fit_clearance": 0.4,
                "lid_height": 1.2,
            }
        )
        for kw in cases:
            p = normalize_params({"style": "snap_latch", **kw})
            self.assertEqual(validate_params(p), [])
            for part in ("base", "lid", "clip_left"):
                with self.subTest(params=kw, part=part):
                    m = generate_box_mesh(p, part)
                    report = topology_report(m)
                    self.assertTrue(report["closed"], report)
                    self.assertTrue(report["oriented"], report)
                    self.assertEqual(report["components"], 1)
                    field, _, _ = build_part_field(p, part)
                    self.assertLess(np.abs(field(m.vertices)).max(), 0.01)
                    self.assertLess(
                        np.abs(field(m.vertices[m.triangles].mean(axis=1))).max(), 0.02
                    )

    def test_upright_print_has_hub_and_stub_feet_on_same_bed_plane(self):
        for part in ("clip_left", "clip_right"):
            m = self.meshes[part]
            g = latch_geometry(self.p, part)
            np.testing.assert_allclose(m.bounds_mm["min"][2], g["flat_z"], atol=3e-6)
            printed = orient_mesh_for_print(m, self.p, part)
            self.assertEqual(printed.bounds_mm["min"][2], 0)
            onbed = np.abs(printed.vertices[:, 2]) < 3e-6
            cx = g["pivot"]["x"]
            half = self.p["latch_width"] / 2
            self.assertTrue(np.any(onbed & (printed.vertices[:, 0] < cx - half)))
            self.assertTrue(np.any(onbed & (printed.vertices[:, 0] > cx + half)))
            faces = printed.vertices[printed.triangles]
            bedfaces = np.all(np.abs(faces[:, :, 2]) < 3e-6, axis=1)
            self.assertTrue(
                np.any(bedfaces & (np.abs(faces[:, :, 0].mean(axis=1) - cx) < half))
            )
            self.assertTrue(topology_report(printed)["oriented"])

    def test_throat_and_axial_engagement_remain_captive(self):
        for diameter in (2.4, 4):
            for c in (0.1, 0.4):
                p = normalize_params(
                    {
                        "style": "snap_latch",
                        "latch_pivot_diameter": diameter,
                        "fit_clearance": c,
                        "height_z": 45,
                    }
                )
                self.assertEqual(validate_params(p), [])
                g = latch_geometry(p)
                # A D-flat circle's minimum directional width is diameter-.2.
                self.assertGreater(diameter - 0.2, 2 * g["mouth_half_height"])
                self.assertGreater(g["axial_engagement"] - c, 0.5)

    def test_new_front_envelope_is_validated_without_deleting_ports(self):
        p = normalize_params(
            {
                "style": "snap_latch",
                "cutouts": [{"face": "front", "u": -21.6, "z": 20, "kind": "usb_c"}],
            }
        )
        self.assertTrue(validate_params(p))
        self.assertEqual(len(p["cutouts"]), 1)
        safe = normalize_params(
            {
                "style": "snap_latch",
                "cutouts": [{"face": "front", "u": 0, "z": 12, "kind": "usb_c"}],
            }
        )
        self.assertEqual(validate_params(safe), [])
        for kw in ({"height_z": 12}, {"width_x": 45}, {"wall_thickness": 1.2}):
            self.assertTrue(
                validate_params(normalize_params({"style": "snap_latch", **kw}))
            )

    def test_exports_keep_pivoting_latches_as_two_separate_parts(self):
        calls = []

        def factory(p, part, printing):
            calls.append((part, printing))
            return (
                orient_mesh_for_print(self.meshes[part], p, part)
                if printing
                else self.meshes[part]
            )

        items = collect_target_meshes(
            self.p, "base_and_lid", assembled=False, mesh_factory=factory
        )
        self.assertEqual(
            [m.part for _, m in items], ["base", "lid", "clip_left", "clip_right"]
        )
        self.assertEqual(
            calls, [(part, True) for part in ("base", "lid", "clip_left", "clip_right")]
        )


if __name__ == "__main__":
    unittest.main()
