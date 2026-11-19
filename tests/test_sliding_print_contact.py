"""Sliding latch retention with a broad, supported lid underside on the bed."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.schema import normalize_params
from box_studio.mesh_generator import (
    np,
    build_part_field,
    generate_box_mesh,
    orient_mesh_for_print,
    topology_report,
)


class SlidingPrintContact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {}
        for c in (0.1, 0.2, 0.4):
            p = normalize_params(
                {
                    "style": "sliding_lid",
                    "width_x": 70,
                    "depth_y": 50,
                    "height_z": 30,
                    "fit_clearance": c,
                }
            )
            mesh = generate_box_mesh(p, "lid")
            n = min(6000, len(mesh.vertices))
            v = mesh.vertices[np.linspace(0, len(mesh.vertices) - 1, n, dtype=int)]
            n = min(6000, len(mesh.triangles))
            cent = mesh.vertices[
                mesh.triangles[np.linspace(0, len(mesh.triangles) - 1, n, dtype=int)]
            ].mean(axis=1)
            cls.cases[c] = (
                p,
                mesh,
                np.r_[v, cent].astype(float),
                build_part_field(p, "base")[0],
                build_part_field(p, "lid")[0],
            )
        cls.base = generate_box_mesh(cls.cases[0.2][0], "base")

    def solid(self, mesh):
        r = topology_report(mesh)
        self.assertTrue(r["closed"], r)
        self.assertTrue(r["oriented"], r)
        self.assertEqual(r["components"], 1, r)
        self.assertEqual(r["euler"], 2, r)
        self.assertGreater(mesh.volume_cm3, 0)

    def test_actual_print_lid_has_broad_plate_contact_not_a_detent_foot(self):
        for c, (p, mesh, _, _, _) in self.cases.items():
            with self.subTest(clearance=c):
                self.solid(mesh)
                lid = self.cases[c][4]
                budget = min(c / 4, 0.04)
                self.assertLess(float(np.abs(lid(mesh.vertices)).max()), budget)
                self.assertLess(
                    float(
                        np.abs(lid(mesh.vertices[mesh.triangles].mean(axis=1))).max()
                    ),
                    budget,
                )
                self.assertAlmostEqual(
                    mesh.bounds_mm["min"][2], p["height_z"] - 3 + c, delta=1e-5
                )
                original = mesh.vertices.copy()
                printed = orient_mesh_for_print(mesh, p, "lid")
                np.testing.assert_array_equal(mesh.vertices, original)
                tri = printed.vertices[printed.triangles].astype(float)
                area = (
                    np.linalg.norm(
                        np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1
                    )
                    / 2
                )
                # Surface extraction can leave <2 µm of planar vertex jitter;
                # this is 1% of a 0.2 mm layer, not a geometric support gap.
                bed = np.all(np.abs(tri[:, :, 2]) < 0.002, axis=1)
                expected = (p["width_x"] - 2 * p["wall_thickness"] - 4 * c) * (
                    p["depth_y"] - 2 * p["wall_thickness"] - c
                ) - 1.6 * (7 - c)
                self.assertAlmostEqual(
                    float(area[bed].sum()) / expected, 1, delta=0.005
                )
                self.assertGreater(float(area[bed].sum()), 2700)
                # A few micron-height boundary slivers are oblique; virtually
                # all classified area must still face down, not up or sideways.
                down_area = float(
                    (area[bed] * np.clip(-printed.face_normals[bed, 2], 0, 1)).sum()
                )
                self.assertGreater(down_area / float(area[bed].sum()), 0.999)
                self.assertEqual(printed.bounds_mm["min"][2], 0)
                self.assertTrue(np.all(printed.vertices[:, 2] >= 0))

    def test_closed_parts_are_clear_and_only_the_tooth_deflects_in_transit(self):
        travel = np.unique(np.r_[np.linspace(0, 5, 51), np.linspace(5, 60, 56)])
        for c, (p, mesh, points, base, _) in self.cases.items():
            rear = p["depth_y"] / 2 - p["wall_thickness"]
            top = p["height_z"] - 1.4 - c
            tooth = (
                (points[:, 2] > top + 0.01)
                & (np.abs(points[:, 0]) < 1.13)
                & (points[:, 1] > rear - 1.53)
                & (points[:, 1] < rear - 0.37)
            )
            self.assertGreater(int(tooth.sum()), 10)
            self.assertGreaterEqual(float(base(points).min()), -0.01)
            barrier = 0.0
            for distance in travel:
                q = points.copy()
                q[:, 1] -= distance
                values = base(q)
                self.assertGreaterEqual(
                    float(values[~tooth].min()),
                    -0.01,
                    (c, distance, "rigid rail/plate"),
                )
                penetration = max(0, -float(values[tooth].min()))
                barrier = max(barrier, penetration)
                self.assertLessEqual(penetration, 0.36, (c, distance))
                if distance >= 3.7:
                    self.assertLessEqual(
                        penetration, 0.01, (c, distance, "released tooth")
                    )
            self.assertGreater(barrier, 0.12, (c, "retaining shoulder absent"))

    def test_entry_ramp_progresses_and_tooth_roots_in_the_plate(self):
        for c, (p, _, _, _, lid) in self.cases.items():
            rear = p["depth_y"] / 2 - p["wall_thickness"]
            top = p["height_z"] - 1.4 - c
            ys = np.linspace(rear - 0.9, rear - 0.4, 31)
            zs = np.linspace(top + 0.005, p["height_z"] - 1.04, 180)
            heights = []
            for y in ys:
                q = np.column_stack((np.zeros(len(zs)), np.full(len(zs), y), zs))
                solid = zs[lid(q) < 0]
                heights.append(0 if not len(solid) else float(solid.max() - top))
            peak = max(heights)
            self.assertGreater(peak, 0.35)
            self.assertGreater(sum(0.2 * peak < h < 0.8 * peak for h in heights), 4)
            root = np.array(
                [[0, y, top - 0.25] for y in np.linspace(rear - 1.45, rear - 0.45, 31)]
            )
            self.assertTrue(np.all(lid(root) < 0))
            # There is material directly below the new tooth root, unlike the
            # old downward tip that began 0.45–0.75 mm before the broad plate.
            root[:, 2] -= 0.1
            self.assertTrue(np.all(lid(root) < 0))

    def test_ceiling_socket_is_connected_to_the_rear_wall_and_mesh_is_manifold(self):
        self.solid(self.base)
        p, _, _, base, _ = self.cases[0.2]
        rear = p["depth_y"] / 2 - p["wall_thickness"]
        z = p["height_z"] - 1.35
        # A path in the first ceiling layer links its front bar through a side
        # beam to the pre-existing rear wall: no separate printed island.
        path = np.r_[
            np.column_stack((np.linspace(0, 2, 21), np.full(21, rear - 3))),
            np.column_stack((np.full(41, 2), np.linspace(rear - 3, rear + 0.1, 41))),
            np.column_stack((np.linspace(2, 0, 21), np.full(21, rear + 0.1))),
        ]
        self.assertTrue(
            np.all(base(np.column_stack((path, np.full(len(path), z)))) < 0)
        )
        rear_support = np.array([[0, rear + 0.1, z - 0.1]])
        self.assertLess(base(rear_support)[0], 0)
        # Socket roof remains 0.9 mm of material below the nominal outer top;
        # neither the box height nor the 45-degree side rails were moved.
        self.assertAlmostEqual(self.base.bounds_mm["max"][2], p["height_z"], delta=1e-5)

    def test_former_rear_corner_interferences_are_now_relieved(self):
        witnesses = {
            0.1: [32.3964, 22.486977, 27.1036],
            0.2: [32.19559, 22.380266, 27.204407],
        }
        for c, point in witnesses.items():
            _, _, _, base, lid = self.cases[c]
            q = np.array([point])
            self.assertLess(base(q)[0], -0.2)
            self.assertGreater(lid(q)[0], 0.1)


if __name__ == "__main__":
    unittest.main()
