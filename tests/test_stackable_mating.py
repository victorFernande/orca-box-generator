"""Independent stacking contact and indexing tests for original generated geometry.

These checks establish sampled geometric contact, not a load rating, friction
coefficient or proof against tipping under arbitrary contents.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio import mesh_generator as geometry
from box_studio.schema import normalize_params, validate_params
import test_functional_mating as mating

np = geometry.np


def params(height, clearance=0.25):
    return normalize_params({"style": "stackable_bin", "width_x": 140,
                             "depth_y": 90, "height_z": height,
                             "stack_clearance": clearance})


def surface_samples(mesh):
    vertices = mesh.vertices.astype(float)
    triangles = vertices[mesh.triangles]
    return np.concatenate((vertices, triangles.mean(axis=1),
                           triangles[:, 0] * 0.6 + triangles[:, 1] * 0.2 + triangles[:, 2] * 0.2))


def contains_planar_points(mesh, points, z, upward):
    triangles = mesh.vertices[mesh.triangles].astype(float)
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    selected = (np.max(np.abs(triangles[:, :, 2] - z), axis=1) < 1e-4)
    selected &= cross[:, 2] > 1e-8 if upward else cross[:, 2] < -1e-8
    triangles = triangles[selected, :, :2]
    if not len(triangles):
        return np.zeros(len(points), dtype=bool)
    a = triangles[:, 0]; u = triangles[:, 1] - a; v = triangles[:, 2] - a
    determinant = u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]
    result = []
    for point in points:
        d = np.asarray(point) - a
        s = (d[:, 0] * v[:, 1] - d[:, 1] * v[:, 0]) / determinant
        t = (u[:, 0] * d[:, 1] - u[:, 1] * d[:, 0]) / determinant
        result.append(bool(np.any((s >= -1e-6) & (t >= -1e-6) & (s + t <= 1 + 1e-6))))
    return np.asarray(result)


def mass_center(mesh):
    triangles = mesh.vertices[mesh.triangles].astype(float)
    weights = np.einsum("ij,ij->i", triangles[:, 0],
                        np.cross(triangles[:, 1], triangles[:, 2]))
    if weights.sum() <= 0:
        raise AssertionError("The actual closed mesh needs positive signed volume")
    return np.sum((triangles[:, 0] + triangles[:, 1] + triangles[:, 2])
                  * weights[:, None], axis=0) / (4 * weights.sum())


class StackableMatingTests(unittest.TestCase):
    def test_actual_base_meshes_are_manifold_and_follow_the_field(self):
        for height in (37, 83):
            with self.subTest(height=height):
                p = params(height)
                self.assertEqual(p["style"], "stackable_bin")
                self.assertEqual(validate_params(p), [])
                items = geometry.collect_target_meshes(p, target="base_and_lid", assembled=True)
                self.assertEqual([mesh.part for _, mesh in items], ["base"])
                mesh = items[0][1]
                euler = mating.FunctionalMatingTests().assert_meshed_boundary(p, "base", mesh)
                self.assertEqual(euler, 2, "An access notch must not introduce a hidden tunnel")
                self.assertAlmostEqual(mesh.bounds_mm["min"][2], 0, delta=1e-4)
                self.assertAlmostEqual(mesh.bounds_mm["max"][2], height, delta=1e-4)

    def test_different_heights_touch_on_three_finite_support_patches(self):
        for lower_h, upper_h in ((37, 83), (83, 37)):
            with self.subTest(lower=lower_h, upper=upper_h):
                lower, upper = params(lower_h), params(upper_h)
                # Access openings may differ without changing the mating family.
                lower.update(front_access_width=70, front_access_drop=12)
                upper.update(front_access_width=80, front_access_drop=22, floor_thickness=3.2)
                lower_mesh = geometry.generate_box_mesh(lower, "base")
                upper_mesh = geometry.generate_box_mesh(upper, "base")
                rise = geometry.stacking_pose_z(lower, upper)
                self.assertAlmostEqual(rise, lower_h - upper["stack_foot_height"])
                w, d, wall = (lower[k] for k in ("width_x", "depth_y", "wall_thickness"))
                contacts = np.array([[-w / 2 + wall / 2, -d / 4],
                                     [w / 2 - wall / 2, -d / 4],
                                     [0, d / 2 - wall / 2]])
                # Each side needs area, not one coincident vertex or a nominal Z.
                offsets = np.array([[dx, dy] for dx in (-wall / 8, 0, wall / 8)
                                              for dy in (-wall / 8, 0, wall / 8)])
                for patch in contacts:
                    points = patch + offsets
                    self.assertTrue(contains_planar_points(lower_mesh, points, lower_h, True).all(),
                                    "Lower rim must have actual upward bearing faces")
                    self.assertTrue(contains_planar_points(upper_mesh, points,
                                    upper["stack_foot_height"], False).all(),
                                    "Upper underside must have actual downward bearing faces")
                centre = mass_center(upper_mesh)[:2]
                triangle = contacts
                signs = []
                for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
                    e, q = b - a, centre - a
                    signs.append(e[0] * q[1] - e[1] * q[0])
                self.assertTrue(min(signs) > 1e-3 or max(signs) < -1e-3,
                                "Empty upper bin mass projection must lie inside the contact polygon")
                self.assertAlmostEqual(rise + upper_mesh.bounds_mm["max"][2],
                                       lower_h + upper_h - upper["stack_foot_height"], delta=1e-4)

    def test_stacking_pose_and_vertical_insertion_have_no_sampled_penetration(self):
        for clearance in (0.1, 0.8):
            with self.subTest(clearance=clearance):
                lower, upper = params(37, clearance), params(83, clearance)
                lower_mesh = geometry.generate_box_mesh(lower, "base")
                upper_mesh = geometry.generate_box_mesh(upper, "base")
                lower_field, _, _ = geometry.build_part_field(lower, "base")
                upper_field, _, _ = geometry.build_part_field(upper, "base")
                low_points, up_points = surface_samples(lower_mesh), surface_samples(upper_mesh)
                rise = geometry.stacking_pose_z(lower, upper)
                shifts = [(0, 0), (clearance * .8, 0), (-clearance * .8, 0),
                          (0, clearance * .8), (0, -clearance * .8)]
                for dx, dy in shifts:
                    for lift in np.linspace(0, upper["stack_foot_height"] + 1, 9):
                        transform = np.array([dx, dy, rise + lift])
                        self.assertGreaterEqual(float(lower_field(up_points + transform).min()), -1e-4)
                        self.assertGreaterEqual(float(upper_field(low_points - transform).min()), -1e-4)

    def test_indexing_blocks_excess_horizontal_and_downward_motion(self):
        for clearance in (0.1, 0.8):
            with self.subTest(clearance=clearance):
                lower, upper = params(37, clearance), params(83, clearance)
                low_field, _, _ = geometry.build_part_field(lower, "base")
                upper_field, _, _ = geometry.build_part_field(upper, "base")
                rise = geometry.stacking_pose_z(lower, upper)
                w, wall, foot = (upper[k] for k in ("width_x", "wall_thickness", "stack_foot_height"))
                point = np.array([[w / 2 - wall - clearance - 0.001, 0, foot / 2]])
                self.assertLess(float(upper_field(point)[0]), 0, "Index witness must be real foot material")
                self.assertGreaterEqual(float(low_field(point + [0, 0, rise])[0]), -1e-5)
                self.assertLess(float(low_field(point + [clearance * 1.2, 0, rise])[0]), -0.005,
                                "An indexing foot must oppose excessive horizontal displacement")
                shoulder = np.array([[w / 2 - wall / 2, 0, foot + .025]])
                self.assertLess(float(upper_field(shoulder)[0]), 0)
                self.assertLess(float(low_field(shoulder + [0, 0, rise - .05])[0]), -.01,
                                "Bearing shoulders must oppose further downward motion")

    def test_incompatible_mating_families_are_rejected(self):
        lower = params(37)
        for key, delta in (("width_x", 1), ("depth_y", 1), ("corner_radius", 1),
                           ("wall_thickness", .2), ("stack_foot_height", .5),
                           ("stack_clearance", .1)):
            with self.subTest(key=key):
                upper = params(83); upper[key] += delta
                with self.assertRaises(ValueError):
                    geometry.stacking_pose_z(lower, upper)


if __name__ == "__main__":
    unittest.main()
