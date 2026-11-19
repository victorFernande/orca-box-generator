"""Hex panel ports honor independent requested width and height envelopes."""

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


class HexCutoutDimensions(unittest.TestCase):
    def params(self, face, width, height):
        return normalize_params(
            {
                "style": "lip_snap",
                "width_x": 70,
                "depth_y": 50,
                "height_z": 30,
                "cutouts": [
                    {
                        "kind": "hex",
                        "face": face,
                        "u": 0,
                        "z": 12,
                        "width": width,
                        "height": height,
                    }
                ],
            }
        )

    def points(self, p, face, uv):
        u, z = np.asarray(uv).T
        normal = (p["depth_y"] if face in ("front", "back") else p["width_x"]) / 2 - p[
            "wall_thickness"
        ] / 2
        normal *= 1 if face in ("back", "right") else -1
        if face in ("front", "back"):
            return np.column_stack((u, np.full(len(u), normal), 12 + z))
        return np.column_stack((np.full(len(u), normal), u, 12 + z))

    def test_envelopes_and_six_vertices_on_every_face(self):
        for face in ("front", "back", "left", "right"):
            for width, height in ((6, 6), (12, 6), (6, 12)):
                with self.subTest(face=face, width=width, height=height):
                    p = self.params(face, width, height)
                    self.assertEqual(validate_params(p), [])
                    field, _, _ = build_part_field(p, "base")
                    a, b = width / 2, height / 2
                    vertices = [
                        [-a, 0],
                        [-a / 2, b],
                        [a / 2, b],
                        [a, 0],
                        [a / 2, -b],
                        [-a / 2, -b],
                    ]
                    np.testing.assert_allclose(
                        field(self.points(p, face, vertices)), 0, atol=1e-10
                    )
                    inside = [
                        [-a + 0.05, 0],
                        [a - 0.05, 0],
                        [0, -b + 0.05],
                        [0, b - 0.05],
                    ]
                    outside = [
                        [-a - 0.05, 0],
                        [a + 0.05, 0],
                        [0, -b - 0.05],
                        [0, b + 0.05],
                    ]
                    self.assertTrue(np.all(field(self.points(p, face, inside)) > 0))
                    self.assertTrue(np.all(field(self.points(p, face, outside)) < 0))

    def test_single_dimension_edits_change_real_openings(self):
        for face in ("front", "right"):
            fields = [
                build_part_field(self.params(face, w, h), "base")[0]
                for w, h in ((6, 6), (12, 6), (6, 12))
            ]
            p = self.params(face, 6, 6)
            width_witness = self.points(p, face, [[4, 0]])
            height_witness = self.points(p, face, [[0, 4]])
            self.assertLess(fields[0](width_witness)[0], 0)
            self.assertGreater(fields[1](width_witness)[0], 0)
            self.assertLess(fields[2](width_witness)[0], 0)
            self.assertLess(fields[0](height_witness)[0], 0)
            self.assertLess(fields[1](height_witness)[0], 0)
            self.assertGreater(fields[2](height_witness)[0], 0)

    def test_actual_printed_boundary_has_front_and_right_hex_tunnels(self):
        p = self.params("front", 12, 6)
        p["cutouts"].append(
            {**p["cutouts"][0], "face": "right", "width": 6.0, "height": 12.0}
        )
        self.assertEqual(validate_params(p), [])
        mesh = generate_box_mesh(p, "base")
        report = topology_report(mesh)
        self.assertTrue(report["closed"], report)
        self.assertTrue(report["oriented"], report)
        self.assertEqual(report["components"], 1, report)
        self.assertEqual(report["euler"], -2, report)
        self.assertGreater(mesh.volume_cm3, 0)
        vertices = mesh.vertices
        eps = 0.015
        for face, width, height in (("front", 12, 6), ("right", 6, 12)):
            if face == "front":
                mask = (
                    (np.abs(vertices[:, 1] + p["depth_y"] / 2) < 1e-4)
                    & (np.abs(vertices[:, 0]) < width / 2 + eps)
                    & (np.abs(vertices[:, 2] - 12) < height / 2 + eps)
                )
                opening = vertices[mask][:, [0, 2]]
            else:
                mask = (
                    (np.abs(vertices[:, 0] - p["width_x"] / 2) < 1e-4)
                    & (np.abs(vertices[:, 1]) < width / 2 + eps)
                    & (np.abs(vertices[:, 2] - 12) < height / 2 + eps)
                )
                opening = vertices[mask][:, [1, 2]]
            self.assertGreater(len(opening), 12)
            np.testing.assert_allclose(opening[:, 0].min(), -width / 2, atol=eps)
            np.testing.assert_allclose(opening[:, 0].max(), width / 2, atol=eps)
            np.testing.assert_allclose(opening[:, 1].min(), 12 - height / 2, atol=eps)
            np.testing.assert_allclose(opening[:, 1].max(), 12 + height / 2, atol=eps)
        original = mesh.vertices.copy()
        printed = orient_mesh_for_print(mesh, p, "base")
        np.testing.assert_array_equal(mesh.vertices, original)
        self.assertEqual(printed.bounds_mm["min"][2], 0)
        self.assertTrue(topology_report(printed)["oriented"])


if __name__ == "__main__":
    unittest.main()
