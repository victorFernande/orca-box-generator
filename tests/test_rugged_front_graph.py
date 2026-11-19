"""The two paired interval graphs form one closed front fitting per ear."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from box_studio.mesh_generator import np
from box_studio.schema import normalize_params
from box_studio import rugged_front_mesh as graph
from box_studio.rugged_front_geometry import front_fittings_field, front_fitting_dimensions
from box_studio.rugged_geometry import rugged_outer_body_y
from verify_box_e2e_exports import inspect_mesh


class FrontGraphTests(unittest.TestCase):
    def test_every_representative_interval_stays_closed_and_matches_the_independent_field(self):
        for part in ("base", "lid"):
            for clearance in (.1, .15, .3):
                for lid_height in (18, 20, 30):
                    with self.subTest(part=part, clearance=clearance, lid_height=lid_height):
                        p = normalize_params({"style": "rugged_box", "fit_clearance": clearance,
                                              "rugged_lid_height": lid_height})
                        result = graph.generate_front_patch(p, part, 47.25, 1)
                        report = result["closed_topology"]
                        self.assertTrue(report["closed"] and report["oriented"])
                        self.assertEqual((report["components"], report["euler"]), (1, 2))
                        self.assertLessEqual(result["measured_error_mm"], .025)
                        self.assertEqual(len(result["foot_loops"]), 1)
                        foot = result["foot_loops"][0]
                        np.testing.assert_array_equal(foot[:, 1], rugged_outer_body_y(p, part, 0, foot[:, 2]).astype(np.float32))

    def test_actual_graphs_have_manifold_links_and_no_unreferenced_or_degenerate_faces(self):
        p = normalize_params({"style": "rugged_box"})
        for part in ("base", "lid"):
            result = graph.generate_front_patch(p, part, 47.25, 1)
            report = inspect_mesh(result["vertices"], result["triangles"])
            self.assertTrue(report["closed"] and report["oriented"] and report["manifold_vertex_links"])
            self.assertGreater(report["volume_mm3"], 0)
            self.assertLess(len(result["triangles"]), 300_000)
            points = result["vertices"][result["triangles"][~result["cap_triangles"]]].mean(axis=1)
            self.assertLessEqual(float(np.abs(front_fittings_field(p, part)(points)).max()), .025)

    def test_translated_and_reflected_ears_reuse_the_shape_with_an_exact_attachment(self):
        p = normalize_params({"style": "rugged_box"})
        original = graph.generate_front_patch(p, "lid", 47.25, 1)
        copied = original["vertices"].copy()
        changed = normalize_params({**p, "width_x": 180, "depth_y": 110, "height_z": 42})
        with patch.object(graph, "_canonical_front_patch", side_effect=AssertionError("Unexpected remeshing")):
            moved = graph.generate_front_patch(changed, "lid", -57.25, -1)
        expected = original["vertices"].astype(float).copy()
        expected[:, 0] = -expected[:, 0] - 10
        expected[:, 1] -= 7.5
        expected[:, 2] += 7
        np.testing.assert_allclose(moved["vertices"], expected, atol=8e-6, rtol=0)
        np.testing.assert_array_equal(moved["triangles"], original["triangles"][:, [0, 2, 1]])
        np.testing.assert_array_equal(original["vertices"], copied)
        self.assertFalse(np.shares_memory(moved["vertices"], original["vertices"]))
        for loop in moved["foot_loops"]:
            np.testing.assert_array_equal(loop[:, 1], rugged_outer_body_y(changed, "lid", 0, loop[:, 2]).astype(np.float32))
        retained = sum(graph._front_patch_bytes(v) for v in graph._FRONT_PATCH_CACHE.values())
        self.assertLessEqual(retained, graph._FRONT_PATCH_CACHE_BYTES)

    def test_larger_clearance_retains_the_real_flat_cam_endcaps(self):
        p = normalize_params({"style": "rugged_box", "fit_clearance": .3})
        result = graph.generate_front_patch(p, "base", 47.25, 1)
        q = front_fitting_dimensions(p)
        xyz = result["vertices"][result["triangles"]]
        for sign in (-1, 1):
            height = np.float32(q["cam_center_z"] + sign * q["cam_socket_half_height"])
            on_plane = np.all(xyz[:, :, 2] == height, axis=1)
            on_plane &= np.all(xyz[:, :, 0] < 61, axis=1)
            faces = xyz[on_plane].astype(float)
            area = np.linalg.norm(np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0]), axis=1).sum() / 2
            self.assertGreater(float(area), .01, "Flat pocket cap was smoothed into a ramp")

    def test_decimal_translation_preserves_the_authored_roof_and_knee_planes(self):
        from box_studio.rugged_front_geometry import front_z_events
        p = normalize_params({"style": "rugged_box", "height_z": 35.1,
                              "rugged_lid_height": 20.3, "fit_clearance": .2})
        q = normalize_params({**p, "height_z": 35})
        original = graph.generate_front_patch(q, "lid", 47.25, 1)
        moved = graph.generate_front_patch(p, "lid", 47.25, 1)
        planes = list(zip(front_z_events(q, "lid"), front_z_events(p, "lid")))
        planes.extend(((45.3, 45.4), (55.3, 55.4)))
        checked = 0
        for source, target in planes:
            mask = original["vertices"][:, 2] == np.float32(source)
            if np.any(mask):
                checked += 1
                np.testing.assert_array_equal(moved["vertices"][mask, 2],
                                              np.full(np.count_nonzero(mask), target, dtype=np.float32))
        self.assertGreaterEqual(checked, 5)


if __name__ == "__main__":
    unittest.main()
