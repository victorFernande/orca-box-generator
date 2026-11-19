"""Primitive dimensions and boundary validity for the reconstructed enclosure."""

from pathlib import Path
import math
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio import rugged_geometry as rg
from box_studio.mesh_generator import np, topology_report, _SurfaceBuilder


PARAMS = {
    "width_x": 160,
    "depth_y": 95,
    "height_z": 35,
    "rugged_lid_height": 20,
    "wall_thickness": 2.5,
    "floor_thickness": 2.5,
    "corner_radius": 12,
    "fit_clearance": 0.15,
}


class ReconstructedRuggedTests(unittest.TestCase):
    def test_measured_dimensions_and_axes(self):
        q = rg.rugged_dimensions(PARAMS)
        self.assertEqual(q["height_closed"], 55)
        self.assertEqual(q["fitting_centers"], [-47.25, 47.25])
        hinge = rg.rugged_hinge_geometry(PARAMS)
        self.assertEqual((hinge["y"], hinge["z"]), (52.25, 35))
        self.assertAlmostEqual(hinge["socket_radius"], 5.125)
        self.assertAlmostEqual(hinge["axial_clearance"], 0.25)
        clip = rg.rugged_latch_geometry(PARAMS, "clip_right")
        self.assertEqual(clip["pivot"], {"x": 47.25, "y": -50.5, "z": 45})
        self.assertAlmostEqual(clip["socket_radius"], 3.9)
        self.assertEqual(clip["attachment"], "lid")

    def test_shells_have_positive_closed_oriented_boundaries(self):
        for part in ("base", "lid"):
            mesh = rg._generate_body_mesh(PARAMS, part)
            report = topology_report(mesh)
            self.assertTrue(report["closed"], report)
            self.assertTrue(report["oriented"], report)
            self.assertEqual(report["components"], 1)
            self.assertEqual(report["euler"], 2)
            self.assertGreater(mesh.volume_cm3, 0)
            field = rg._body_field(PARAMS, part)
            self.assertLess(np.max(np.abs(field(mesh.vertices))), 0.00001)
            self.assertLess(
                np.max(np.abs(field(mesh.vertices[mesh.triangles].mean(1)))), 0.03
            )
            self.assertLess(len(mesh.triangles), 2500)

    def test_normal_wall_bevel_and_v_interface(self):
        base = rg._body_field(PARAMS, "base")
        lid = rg._body_field(PARAMS, "lid")
        # Measured neutral section: external bevel is 10 mm high at 30 degrees
        # from vertical; the internal chamfer is a normal 2.5 mm offset.
        points = np.array(
            [
                [0, 47.5, 10],
                [0, 41.7264973081, 0],
                [0, 45, 10.6698729811],
                [0, 40.2831216351, 2.5],
                [0, 47.1, 35],
                [0, 46.25, 34.15],
                [0, 45.4, 35],
            ]
        )
        self.assertLess(np.max(np.abs(base(points))), 0.00001)
        self.assertLess(np.max(np.abs(lid(points[-3:]))), 0.00001)
        # The male/female V has nominal contact, while bearing clearances belong
        # to their spherical pairs. Do not silently impose an axial rim gap.
        self.assertLess(base(np.array([[0, 46.25, 34.14]]))[0], 0)
        self.assertGreater(lid(np.array([[0, 46.25, 34.14]]))[0], 0)
        self.assertGreater(base(np.array([[0, 46.25, 34.16]]))[0], 0)
        self.assertLess(lid(np.array([[0, 46.25, 34.16]]))[0], 0)

    def test_negative_x_open_rotation_and_input_purity(self):
        p = PARAMS
        original = np.array([[47.25, -50.5, 20.0]])
        opened = rg.rugged_transform(original, p, "clip_right", 90)
        np.testing.assert_allclose(opened, [[47.25, -75.5, 45]], atol=1e-12)
        np.testing.assert_array_equal(original, [[47.25, -50.5, 20]])
        lid = np.array([[0.0, -47.5, 55]])
        opened_lid = rg.rugged_transform(lid, p, "lid", 180)
        np.testing.assert_allclose(opened_lid, [[0, 152, 15]], atol=1e-12)

    def test_rear_cup_has_real_open_mouth_and_conforming_boundary(self):
        for clearance in (0.1, 0.15, 0.3):
            p = PARAMS | {"fit_clearance": clearance}
            face = 47.25 - 10.75 - clearance * 5 / 3
            b = _SurfaceBuilder()
            rg._append_rear_socket(b, p, 28.25, face, 40.25, close_back=True)
            mesh = b.mesh("rear", 0.025)
            report = topology_report(mesh)
            self.assertTrue(report["closed"], report)
            self.assertTrue(report["oriented"], report)
            self.assertEqual((report["components"], report["euler"]), (1, 2))
            field = rg._rear_socket_field(p, 28.25, face, 40.25)
            self.assertLess(np.max(np.abs(field(mesh.vertices))), 0.00001)
            self.assertLess(
                np.max(np.abs(field(mesh.vertices[mesh.triangles].mean(1)))), 0.015
            )
            # A downward opening exists before the spherical part of the cup.
            opening = np.array([[face - 0.1, 52.25, 29]])
            self.assertGreater(field(opening)[0], 0)
            self.assertLess(field(np.array([[face - 0.1, 55.5, 34]]))[0], 0)

    def test_rear_attachment_overlap_is_only_inside_existing_wall(self):
        body = rg._body_field(PARAMS, "base")
        ear = rg._rear_socket_field(PARAMS, 28.25, 36.25, 40.25, embed=True)
        witness = np.array([[30, 47.5, 25]])
        self.assertAlmostEqual(body(witness)[0], 0)
        self.assertLess(ear(witness)[0], -0.001)
        # Without an internal overlap min(body,ear) would be zero on a whole
        # internal plane, which an isosurface extractor mistakes for a cavity.

    def test_coupled_floor_and_wall_corner_at_allowed_extreme(self):
        wall, floor = 4, 1.5
        radius = max(
            6.774 + wall / math.sqrt(3), (10 - floor + 2 * wall) / math.sqrt(3) + 0.8
        )
        p = PARAMS | {
            "wall_thickness": wall,
            "floor_thickness": floor,
            "corner_radius": radius,
        }
        for part in ("base", "lid"):
            mesh = rg._generate_body_mesh(p, part)
            report = topology_report(mesh)
            self.assertTrue(report["closed"] and report["oriented"], report)
            self.assertEqual((report["components"], report["euler"]), (1, 2))

    def test_open_fitting_footprints_weld_to_wall_chamfer_and_roof(self):
        for part in ("base", "lid"):
            bottom, top = (15, 35) if part == "base" else (35, 55)
            levels = [bottom, top] if part == "base" else [35, 45, 55]
            foot = np.array(
                [
                    [x, rg.rugged_outer_body_y(PARAMS, part, 0, z), z]
                    for x, z in ((-10, bottom), (10, bottom), (10, top), (-10, top))
                ]
            )
            if part == "lid":
                foot = np.array(
                    [
                        [-10, rg.rugged_outer_body_y(PARAMS, part, 0, 35), 35],
                        [10, rg.rugged_outer_body_y(PARAMS, part, 0, 35), 35],
                        [10, rg.rugged_outer_body_y(PARAMS, part, 0, 45), 45],
                        [10, rg.rugged_outer_body_y(PARAMS, part, 0, 55), 55],
                        [-10, rg.rugged_outer_body_y(PARAMS, part, 0, 55), 55],
                        [-10, rg.rugged_outer_body_y(PARAMS, part, 0, 45), 45],
                    ]
                )
            builder = rg._body_builder(
                PARAMS, part, omit_sides=(0,), foot_loops={0: [foot]}
            )
            rg._append_panel_with_feet(builder, PARAMS, part, 0, [foot])
            loops = []
            for z in levels:
                y = float(rg.rugged_outer_body_y(PARAMS, part, 0, z))
                loops.append(
                    np.array([[-10, y - 4, z], [10, y - 4, z], [10, y, z], [-10, y, z]])
                )
            builder.disk(loops[0], True)
            builder.disk(loops[-1])
            for a, b in zip(loops, loops[1:]):
                for k in (0, 1, 3):
                    j = (k + 1) % 4
                    builder.quad(a[k], a[j], b[j], b[k])
            mesh = builder.mesh(part, 0.025)
            report = topology_report(mesh)
            self.assertTrue(report["closed"] and report["oriented"], report)
            self.assertEqual((report["components"], report["euler"]), (1, 2))
            original_volume = rg._generate_body_mesh(PARAMS, part).volume_cm3
            self.assertAlmostEqual(mesh.volume_cm3 - original_volume, 1.6, places=5)

    def test_socket_cap_regularization_changes_only_empty_gap_classification(self):
        from box_studio.rugged_front_geometry import (
            front_socket_field,
            front_fittings_field,
        )

        p = PARAMS
        mouth = np.array([[34.5, -50.5, 26.80306]])
        self.assertLess(front_socket_field(p, "base")(mouth)[0], -0.001)
        self.assertGreater(front_fittings_field(p, "base")(mouth)[0], 0.001)
        # A larger allowed socket can reach the main wall. Its artificial cap
        # must remain on the measured X datum there, not drill the adjacent wall.
        p = PARAMS | {"fit_clearance": 0.3}
        wall = np.array([[34.501, -47.45, 45]])
        self.assertGreater(front_socket_field(p, "lid")(wall)[0], 0.0005)
        self.assertLess(rg._body_field(p, "lid")(wall)[0], 0)
        outboard_wall = np.array([[34.4, -47.45, 45]])
        self.assertGreater(front_socket_field(p, "lid")(outboard_wall)[0], 0.04)
        self.assertLess(rg.rugged_part_field(p, "lid")[0](outboard_wall)[0], -0.04)
        larger_radius = 4.05
        outboard_sphere = np.array(
            [[34.4, -50.5, 45 + math.sqrt(larger_radius**2 - (34.4 - 37) ** 2)]]
        )
        self.assertAlmostEqual(
            front_socket_field(p, "lid")(outboard_sphere)[0], 0, places=10
        )
        # The spherical physical surface is unchanged by cap regularization.
        radius, x = 3.9, 34.4
        sphere = np.array([[x, -50.5, 45 + math.sqrt(radius**2 - (x - 37) ** 2)]])
        self.assertAlmostEqual(
            front_socket_field(PARAMS, "lid")(sphere)[0], 0, places=10
        )

    def test_rear_slot_draft_removes_reference_negative_space(self):
        field = rg._rear_lid_field(PARAMS, 47.25)
        points = np.array(
            [
                [47.25, 52.25, 35.1],
                [44.4, 52.25, 35.1],
                [44.4, 47.8, 40],
                [44.6, 47.8, 40],
            ]
        )
        values = field(points)
        self.assertTrue(np.all(values[:2] > 0), values)
        self.assertLess(values[2], 0)
        self.assertGreater(values[3], 0)

    def test_whole_bodies_keep_conforming_seams_at_coupled_dimensions(self):
        # Fractional roof/knee planes used to differ by a single float32 ULP
        # between the shell, rear brace and instantiated front patches. The
        # minimum-radius case also exercises a fitting foot at a corner seam.
        coupled_radius = (10 - 1.5 + 2 * 4) / math.sqrt(3) + 0.8
        cases = {
            "minimum": {
                "width_x": 112,
                "depth_y": 44,
                "height_z": 30,
                "rugged_lid_height": 18,
                "wall_thickness": 2.1,
                "floor_thickness": 1.5,
                "fit_clearance": 0.1,
            },
            "decimal_roof": {
                "width_x": 162,
                "height_z": 35.1,
                "rugged_lid_height": 20.3,
                "fit_clearance": 0.2,
            },
            "coupled_minimum_radius": {
                "width_x": 200.3,
                "depth_y": 125.7,
                "height_z": 30.1,
                "rugged_lid_height": 18.2,
                "wall_thickness": 4,
                "floor_thickness": 1.5,
                "fit_clearance": 0.3,
                "corner_radius": coupled_radius,
            },
            "deep_lid": {
                "width_x": 300,
                "depth_y": 200,
                "height_z": 80,
                "rugged_lid_height": 50,
                "wall_thickness": 3,
                "floor_thickness": 4,
                "corner_radius": 16,
                "fit_clearance": 0.3,
            },
        }
        for name, changes in cases.items():
            p = PARAMS | changes
            for part in ("base", "lid"):
                with self.subTest(case=name, part=part):
                    mesh = rg.generate_rugged_mesh(p, part)
                    report = topology_report(mesh)
                    self.assertTrue(report["closed"], report)
                    self.assertTrue(report["oriented"], report)
                    self.assertEqual((report["components"], report["euler"]), (1, 2))
                    self.assertGreater(mesh.volume_cm3, 0)
                    vertices = mesh.vertices.astype(np.float64)
                    points = vertices[mesh.triangles]
                    cross = np.cross(
                        points[:, 1] - points[:, 0], points[:, 2] - points[:, 0]
                    )
                    area = np.linalg.norm(cross, axis=1)
                    self.assertTrue(np.all(area > 0), "degenerate triangle")
                    self.assertTrue(np.all(np.isfinite(mesh.face_normals)))
                    np.testing.assert_allclose(
                        mesh.face_normals, cross / area[:, None], atol=1e-6, rtol=0
                    )
                    field = rg.rugged_part_field(p, part)[0]
                    # This is the declared 0.025 mm surface approximation
                    # budget, not a mating-interference allowance.
                    for sample in (vertices, points.mean(1)):
                        error = float(np.max(np.abs(field(sample))))
                        self.assertLessEqual(error, 0.02501, (name, part, error))


if __name__ == "__main__":
    unittest.main()
