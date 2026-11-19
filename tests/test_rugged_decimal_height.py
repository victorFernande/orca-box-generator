"""Rear mouth poles remain conforming at fractional enclosure heights."""

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from box_studio import rugged_geometry as rg
from box_studio.mesh_generator import _SurfaceBuilder, generate_box_mesh, np
from box_studio.presets_catalog import BUILTIN_PRESETS
from box_studio.schema import normalize_params, validate_params
from verify_box_e2e_exports import inspect_mesh


PARAMS = normalize_params(
    {
        "style": "rugged_box",
        "width_x": 160,
        "depth_y": 95,
        "height_z": 35,
        "rugged_lid_height": 20,
        "wall_thickness": 2.5,
        "floor_thickness": 2.5,
        "corner_radius": 12,
        "fit_clearance": 0.15,
    }
)


class RuggedDecimalHeightTests(unittest.TestCase):
    def assert_boundary(self, mesh):
        # This independent checker verifies every directed edge and every
        # vertex link, not merely edge counts or the product topology report.
        report = inspect_mesh(mesh.vertices, mesh.triangles)
        self.assertTrue(report["closed"] and report["oriented"])
        self.assertTrue(report["manifold_vertex_links"])
        self.assertEqual((report["components"], report["euler"]), (1, 2))
        self.assertGreater(report["volume_mm3"], 0)
        xyz = mesh.vertices[mesh.triangles].astype(np.float64)
        cross = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
        lengths = np.linalg.norm(cross, axis=1)
        self.assertTrue(np.all(lengths > 0), "Collapsed pole triangle")
        self.assertTrue(np.isfinite(mesh.face_normals).all())
        np.testing.assert_allclose(
            mesh.face_normals, cross / lengths[:, None], atol=1e-6, rtol=0
        )
        self.assertAlmostEqual(mesh.volume_cm3, report["volume_mm3"] / 1000, places=9)

    def test_exact_mouth_endpoint_is_one_vertex_at_sixteen_socket_placements(self):
        for height in (35, 36, 36.1, 36.3, 36.7, 36.9, 37.7, 48.7):
            p = PARAMS | {"height_z": height}
            q = rg.rugged_dimensions(p)
            for center in q["fitting_centers"]:
                with self.subTest(height=height, center=center):
                    lo = center - 19
                    hi = center - 10.75 - rg.rugged_hinge_geometry(p)["axial_clearance"]
                    sphere_x = center - 7
                    builder = _SurfaceBuilder()
                    rg._append_rear_socket(
                        builder, p, lo, hi, sphere_x, close_back=True
                    )
                    mesh = builder.mesh("rear", 0.025)
                    self.assert_boundary(mesh)
                    # Independently derived tangent-root height at the pole:
                    # H - R/2 - sqrt(3)*(R*cos(30°)) = H - 2R = H - 9.
                    pole = np.array(
                        [sphere_x - 4.8, p["depth_y"] / 2 + 4.75, height - 9],
                        dtype=np.float32,
                    )
                    matches = np.all(mesh.vertices == pole, axis=1)
                    self.assertEqual(int(matches.sum()), 1)

    def test_ci_surprise_and_neighboring_heights_generate_manifold_bases(self):
        # CI seed 1103020891 produced the first of these: schema-valid,
        # previously open at the two rear cylinder-mouth poles, independent of
        # clearance. Integer heights did not expose the cancellation residue.
        for height in (36.1, 36.3, 36.7, 36.9, 37.7):
            for clearance in (0.15, 0.23):
                with self.subTest(height=height, clearance=clearance):
                    p = PARAMS | {
                        "width_x": 152.2,
                        "depth_y": 92.9,
                        "height_z": height,
                        "rugged_lid_height": 22,
                        "fit_clearance": clearance,
                    }
                    self.assertEqual(validate_params(p), [])
                    mesh = generate_box_mesh(p, "base")
                    self.assert_boundary(mesh)

    def test_approved_default_body_arrays_keep_all_six_original_hashes(self):
        reference = json.loads(
            (ROOT / "tests/fixtures/standard_mesh_reference.json").read_text(
                encoding="utf-8"
            )
        )["rugged_reference"]["parts"]
        p = next(
            item["params"] for item in BUILTIN_PRESETS if item["id"] == "tool_rugged"
        )
        for part in ("base", "lid"):
            with self.subTest(part=part):
                # Direct generator: never obtain this proof from a prepared
                # resource whose source fingerprint predates the pole fix.
                mesh = generate_box_mesh(p, part)
                expected = reference["tool_rugged-" + part]["array_sha256"]
                for name, array in (
                    ("vertices", mesh.vertices),
                    ("triangles", mesh.triangles),
                    ("normals", mesh.face_normals),
                ):
                    self.assertEqual(
                        hashlib.sha256(array.tobytes()).hexdigest(), expected[name]
                    )


if __name__ == "__main__":
    unittest.main()
