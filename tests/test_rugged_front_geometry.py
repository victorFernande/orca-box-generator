"""Dimensional witnesses for the enclosure's reconstructed front supports."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.rugged_front_geometry import (
    _front_profile_distance,
    front_fitting_dimensions,
    front_fittings_field,
    front_interval,
    front_socket_field,
    front_strip_bounds,
    front_z_events,
    rugged_front_bounds,
)
from box_studio.mesh_generator import np


PARAMS = {
    "width_x": 160,
    "depth_y": 95,
    "height_z": 35,
    "rugged_lid_height": 20,
    "corner_radius": 12,
    "wall_thickness": 2.5,
    "floor_thickness": 2.5,
    "fit_clearance": 0.15,
}


class RuggedFrontFieldTests(unittest.TestCase):
    def test_strip_bounds_and_height_events_are_finite_and_ordered(self):
        for part in ("base", "lid"):
            for lid_height in (18, 20, 30):
                p = dict(PARAMS, rugged_lid_height=lid_height)
                events = front_z_events(p, part)
                self.assertEqual(events, sorted(set(events)))
                self.assertEqual(events[0], 16 if part == "base" else 35)
                self.assertEqual(events[-1], 35 if part == "base" else 35 + lid_height)
                z = np.linspace(events[0], events[-1], 501)
                lower, upper = front_strip_bounds(p, part, z)
                self.assertTrue(np.isfinite(lower).all())
                self.assertTrue(np.isfinite(upper).all())
                self.assertTrue(np.all(upper >= lower))
                if part == "base":
                    self.assertAlmostEqual(float(upper[0]), 0)
                else:
                    self.assertAlmostEqual(float(lower[-1]), -10 / np.sqrt(3))
                    self.assertAlmostEqual(float(upper[-1]), 8 - 10 / np.sqrt(3))

    def test_interval_graphs_agree_with_the_independent_implicit_solid(self):
        rng = np.random.default_rng(6842)
        for part in ("base", "lid"):
            for clearance in (0.10, 0.15, 0.30):
                for lid_height in (18, 20, 30):
                    p = dict(
                        PARAMS, fit_clearance=clearance, rugged_lid_height=lid_height
                    )
                    events = front_z_events(p, part)
                    z = rng.uniform(events[0], events[-1], 257)
                    minimum, maximum = front_strip_bounds(p, part, z)
                    s = minimum + (maximum - minimum) * rng.uniform(
                        0.001, 0.999, len(z)
                    )
                    inner, outer = front_interval(p, part, s, z)
                    self.assertTrue(
                        np.all(outer > inner), (part, clearance, lid_height)
                    )
                    inside = np.column_stack((47.25 - inner, -47.5 - s, z))
                    outside = np.column_stack((47.25 - outer, -47.5 - s, z))
                    field = front_fittings_field(p, part)
                    np.testing.assert_allclose(field(inside), 0, atol=1e-9)
                    np.testing.assert_allclose(field(outside), 0, atol=1e-9)
                    self.assertTrue(np.all(field((inside + outside) / 2) < 0))
                    self.assertTrue(np.all(field(inside + [0.005, 0, 0]) >= -1e-9))
                    self.assertTrue(np.all(field(outside - [0.005, 0, 0]) >= -1e-9))

    def test_interval_contains_the_actual_conical_cam_recess(self):
        center = 26.80306
        z = np.array([center, 24.33993, 23.83993, 23.8])
        inner, _ = front_interval(PARAMS, "base", 3, z)
        np.testing.assert_allclose(inner, [13.65, 13.25, 12.75, 12.75], atol=1e-9)
        points = np.column_stack((47.25 - inner, np.full(4, -50.5), z))
        np.testing.assert_allclose(
            front_fittings_field(PARAMS, "base")(points), 0, atol=1e-9
        )

    def test_larger_cam_clearance_preserves_its_real_flat_cap_step(self):
        p = dict(PARAMS, fit_clearance=0.30)
        cap_z = 26.80306 - 2.96313
        z = np.array([cap_z - 1e-6, cap_z, cap_z + 1e-6])
        inner, _ = front_interval(p, "base", 3, z)
        np.testing.assert_allclose(inner, [12.75, 12.9, 12.900001], atol=1e-9)
        self.assertTrue(any(abs(v - cap_z) < 1e-9 for v in front_z_events(p, "base")))

    def test_profile_distance_and_normal_match_tangent_line_and_arc(self):
        for part in ("base", "lid"):
            angles = (
                np.linspace(-np.arctan(1 / 1.25), -0.01, 31)
                if part == "base"
                else np.linspace(0.01, np.pi / 6, 31)
            )
            center_z = 35 - 5.4921894 if part == "base" else 55 - (30 - 10 * np.sqrt(3))
            s, z = -2 + 10 * np.cos(angles), center_z + 10 * np.sin(angles)
            distance, normal = _front_profile_distance(s, z, 35, 20, part)
            np.testing.assert_allclose(distance, 0, atol=1e-12)
            np.testing.assert_allclose(normal, np.cos(angles), atol=1e-10)
            distance, _ = _front_profile_distance(
                s + 0.1 * np.cos(angles), z + 0.1 * np.sin(angles), 35, 20, part
            )
            np.testing.assert_allclose(distance, 0.1, atol=1e-10)

    def test_fillets_are_continuous_at_former_medial_plane_and_front_endpoint(self):
        epsilon = 1e-6
        for part in ("base", "lid"):
            center_z = 35 - 5.4921894 if part == "base" else 55 - (30 - 10 * np.sqrt(3))
            medial = (100 - 9.55**2) / 20
            z = center_z + (medial if part == "base" else -medial)
            ray_z = center_z + (0.5 if part == "base" else -0.5)
            points = np.array(
                [
                    [65.65, -55.05, z],
                    [64.4653467, -55.5, ray_z],
                    [27.9346533, -53.5, 33 if part == "base" else 40],
                ]
            )
            field = front_fittings_field(PARAMS, part)
            for axis in np.eye(3):
                difference = np.abs(
                    field(points + axis * epsilon) - field(points - axis * epsilon)
                )
                self.assertTrue(np.all(difference < 5 * epsilon), difference)

    def test_dimensional_frame_and_socket_clearances(self):
        q = front_fitting_dimensions(PARAMS)
        self.assertEqual(q["centers"], [-47.25, 47.25])
        self.assertEqual(q["front"], -47.5)
        self.assertAlmostEqual(q["cam_socket_radius"], 5.15)
        self.assertAlmostEqual(q["ball_radius"], 3.9)
        self.assertAlmostEqual(q["cam_center_z"], 26.80306)
        self.assertAlmostEqual(q["ball_center_z"], 45)

    def test_base_outer_fifteen_degree_plane_and_front_corner(self):
        field = front_fittings_field(PARAMS, "base")
        points = np.array(
            [
                [26.5, -48.0358983849, 30],
                [28.10280165, -54.01763809, 32],
                [30.0346533, -55.5, 32],
            ]
        )
        np.testing.assert_allclose(field(points), 0, atol=1e-6)
        self.assertGreater(field(points[:1] + [-0.1, 0, 0])[0], 0)
        self.assertLess(field(points[:1] + [0.1, 0, 0])[0], 0)

    def test_base_lower_plane_and_radius_ten_profile(self):
        field = front_fittings_field(PARAMS, "base")
        points = np.array(
            [[32, -50.5, 19.75], [32, -53.3086881, 23.2608595], [32, -55.5, 29.5078106]]
        )
        np.testing.assert_allclose(field(points), 0, atol=1e-5)

    def test_lid_upper_sixty_degree_plane_and_radius_ten_profile(self):
        field = front_fittings_field(PARAMS, "lid")
        points = np.array(
            [
                [32, -49.7264973081, 55],
                [32, -54.1602540378, 47.3205080757],
                [32, -55.5, 42.3205080757],
            ]
        )
        np.testing.assert_allclose(field(points), 0, atol=1e-6)

    def test_spherical_and_conical_recesses(self):
        base = front_socket_field(PARAMS, "base")
        lid = front_socket_field(PARAMS, "lid")
        # Left cap of the left cam: radius and axial distance change equally
        # along its 45-degree chamfer, rather than following a circular fillet.
        points = np.array(
            [[34.5, -50.5, 23.83993], [34.0, -50.5, 24.33993], [33.6, -50.5, 26.80306]]
        )
        np.testing.assert_allclose(base(points), 0, atol=1e-8)
        np.testing.assert_allclose(lid(np.array([[33.1, -50.5, 45]])), 0, atol=1e-8)
        self.assertLess(lid(np.array([[33.2, -50.5, 45]]))[0], 0)

    def test_lid_lower_cone_does_not_fill_the_upper_latch_gap(self):
        field = front_fittings_field(PARAMS, "lid")
        points = np.array(
            [
                [51.25, -48.5, 54.9],
                [47.25, -50.5, 54.9],
                [47.25, -50.5, 40],
                [35.8, -54.5, 54.9],
            ]
        )
        self.assertTrue(np.all(field(points) > 0), field(points))
        material = np.array([[34.8, -55.4, 36.1]])
        self.assertLess(field(material)[0], 0)

    def test_lid_support_reaches_receding_shell_attachment(self):
        from box_studio.rugged_geometry import rugged_outer_body_y

        field = front_fittings_field(PARAMS, "lid")
        z = np.array([45.0, 50.0, 54.9])
        y = rugged_outer_body_y(PARAMS, "lid", 0, z)
        points = np.column_stack((np.full(3, 31.0), y - 0.01, z))
        self.assertTrue(np.all(field(points) < 0), field(points))
        points[:, 1] = y + 0.021
        self.assertTrue(np.all(field(points) > 0), field(points))
        bounds = rugged_front_bounds(PARAMS, "lid")
        self.assertGreater(bounds[3], -42)

    def test_four_supports_are_symmetric_and_bounds_contain_witnesses(self):
        points = np.array([[31, -53, 32], [31, -53, 40]])
        for part, index in (("base", 0), ("lid", 1)):
            field = front_fittings_field(PARAMS, part)
            point = points[index : index + 1]
            mirror = point.copy()
            mirror[:, 0] *= -1
            np.testing.assert_allclose(field(point), field(mirror), atol=1e-12)
            lower = rugged_front_bounds(PARAMS, part)[::2]
            upper = rugged_front_bounds(PARAMS, part)[1::2]
            self.assertTrue(np.all(point >= lower))
            self.assertTrue(np.all(point <= upper))


if __name__ == "__main__":
    unittest.main()
