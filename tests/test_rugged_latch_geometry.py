"""Public dimensional and boundary regressions for the reconstructed latch.

No private reference file is needed by these tests. Dimensions exercise the
actual spherical caps, conical cams, open flexure slots, and printing face.
"""

from pathlib import Path
from dataclasses import replace
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio import rugged_latch_geometry as latch
from box_studio.mesh_generator import np, topology_report


PARAMS = {
    "width_x": 160,
    "depth_y": 95,
    "height_z": 35,
    "rugged_lid_height": 20,
    "corner_radius": 12,
    "fit_clearance": 0.15,
}


class RuggedLatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        latch._clear_latch_cache()
        with patch.object(latch, "_load_canonical_latch", return_value=None):
            cls.mesh = latch.generate_rugged_latch(PARAMS, "clip_right")
        cls.field = staticmethod(latch.rugged_latch_field(PARAMS, "clip_right"))

    def test_bank_is_optional_and_loaded_before_fresh_extraction(self):
        latch._clear_latch_cache()
        with patch.object(
            latch, "_load_canonical_latch", return_value=self.mesh
        ) as load:
            with patch.object(
                latch, "_extract_latch", side_effect=AssertionError("remeshed")
            ):
                reused = latch.generate_rugged_latch(PARAMS, "clip_right")
        self.assertEqual(load.call_count, 1)
        self.assertEqual(load.call_args.args[0]["style"], "rugged_box")
        np.testing.assert_array_equal(reused.vertices, self.mesh.vertices)
        np.testing.assert_array_equal(reused.triangles, self.mesh.triangles)

    def test_closed_connected_oriented_solid(self):
        report = topology_report(self.mesh)
        self.assertTrue(report["closed"], report)
        self.assertTrue(report["oriented"], report)
        self.assertEqual(report["components"], 1)
        self.assertEqual(report["euler"], 2)
        self.assertGreater(self.mesh.volume_cm3, 3.5)
        self.assertLess(self.mesh.volume_cm3, 3.9)

    def test_boundary_and_curved_face_error(self):
        vertices = self.mesh.vertices
        centers = vertices[self.mesh.triangles].astype(float).mean(1)
        self.assertLess(np.max(np.abs(self.field(vertices))), 0.0006)
        self.assertLessEqual(np.max(np.abs(self.field(centers))), 0.025)

    def test_spherical_journals_and_conical_cams(self):
        # Right outer spherical cap: center X=10.25, radius 3.75.
        points = np.array(
            [
                [14, 0, 45],
                [13.25, 0, 47.25],
                [13.5, 0, 26.80306],
                [13, 0, 24.30206],
                [12.501, 0, 23.80306],
            ]
        ) + [47.25, -50.5, 0]
        np.testing.assert_allclose(self.field(points), 0, atol=0.00001)
        self.assertGreater(self.field(points[:1] + [0.1, 0, 0])[0], 0)
        self.assertLess(self.field(points[:1] - [0.1, 0, 0])[0], 0)

    def test_open_flexure_slots_and_connected_grip(self):
        points = np.array(
            [
                [9.5, 0, 25],
                [-9.5, 0, 25],
                [11, 0, 30.05],
                [-11, 0, 30.05],
                [9.5, 0, 19.5],
                [11.5, 0, 25],
                [0, 0, 25],
            ]
        ) + [47.25, -50.5, 0]
        values = self.field(points)
        self.assertTrue(np.all(values[:4] > 0.1), values)
        self.assertTrue(np.all(values[4:] < -0.1), values)

    def test_hourglass_is_radial_not_silhouette_extrusion(self):
        waist = 12.5 - 5 * np.tan(np.deg2rad(40))
        points = np.array(
            [
                [waist, 0, 35],
                [waist, 3, 45 - np.sqrt(91)],
                [waist + 0.1, 0, 35],
                [waist - 0.1, 0, 35],
            ]
        ) + [47.25, -50.5, 0]
        values = self.field(points)
        np.testing.assert_allclose(values[:2], 0, atol=1e-8)
        self.assertGreater(values[2], 0)
        self.assertLess(values[3], 0)

    def test_print_pose_has_broad_flat_contact_and_preserves_input(self):
        original = self.mesh.vertices.copy()
        printed = latch.rugged_latch_print_transform(original, PARAMS, "clip_right")
        np.testing.assert_array_equal(original, self.mesh.vertices)
        self.assertAlmostEqual(float(printed[:, 2].min()), 0, places=5)
        self.assertAlmostEqual(float(printed[:, 2].max()), 6, places=5)
        q = printed[self.mesh.triangles]
        on_bed = np.all(np.abs(q[:, :, 2]) < 1e-6, axis=1)
        area = (
            np.linalg.norm(np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]), axis=1) / 2
        )
        self.assertGreater(float(area[on_bed].sum()), 600)

    def test_lower_grip_and_cam_junctions_do_not_overlap(self):
        from test_rugged_motion_e2e import rugged_proper_intersections

        triangles = self.mesh.vertices[self.mesh.triangles].astype(float)
        local = triangles - [47.25, -50.5, 0]
        low, high = local.min(1), local.max(1)
        # Independent BVH audit of both numerical regression regions. The
        # complete boundary is independently audited by Rugged motion tests.
        for lower, upper in (
            ([12.49, 1.1, 17.8], [12.51, 1.4, 18.1]),
            ([13.4, -0.3, 24.7], [13.51, 0.3, 24.9]),
        ):
            selected = np.all(high >= lower, axis=1) & np.all(low <= upper, axis=1)
            self.assertGreater(int(selected.sum()), 20)
            patch_mesh = replace(
                self.mesh,
                triangles=self.mesh.triangles[selected],
                face_normals=self.mesh.face_normals[selected],
            )
            self.assertEqual(rugged_proper_intersections(patch_mesh), [])

    def test_cached_local_shape_translates_without_remeshing(self):
        p = dict(PARAMS, width_x=180, depth_y=110, height_z=42)
        with patch.object(
            latch, "_extract_latch", side_effect=AssertionError("remeshed")
        ):
            moved = latch.generate_rugged_latch(p, "clip_left")
        expected_shift = [-104.5, -7.5, 7]
        np.testing.assert_allclose(
            moved.vertices, self.mesh.vertices + expected_shift, atol=1e-5
        )
        np.testing.assert_array_equal(moved.triangles, self.mesh.triangles)
        self.assertFalse(np.shares_memory(moved.vertices, self.mesh.vertices))
        self.assertFalse(np.shares_memory(moved.triangles, self.mesh.triangles))
        retained = sum(
            sum(a.nbytes for a in (m.vertices, m.triangles, m.face_normals))
            for m in latch._LATCH_CACHE.values()
        )
        self.assertLessEqual(retained, latch._LATCH_CACHE_BYTES)
        self.assertLessEqual(len(latch._LATCH_CACHE), 2)

    def test_lid_height_moves_journals_without_scaling_lower_cams(self):
        p = dict(PARAMS, rugged_lid_height=25)
        field = latch.rugged_latch_field(p, "clip_right")
        points = np.array([[14, 0, 50], [13.5, 0, 26.80306]]) + [47.25, -50.5, 0]
        np.testing.assert_allclose(field(points), 0, atol=1e-8)


if __name__ == "__main__":
    unittest.main()
