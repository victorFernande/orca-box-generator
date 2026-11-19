"""Independent articulated-latch acceptance, without reference-model fixtures.

A stationary assembled state must be clear. Only the identified pin cam may
interfere transiently while opening; rigid geometry does not predict force.
"""
from __future__ import annotations

import math
import json
import sys
import unittest
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio import mesh_generator as geometry
from box_studio.schema import normalize_params
import test_functional_mating as mating
import test_stackable_mating as planar
import test_clamshell_mating as slicing

np = geometry.np


def rotate_x(points, pivot, degrees):
    result = np.asarray(points, dtype=float).copy()
    angle = math.radians(degrees); co, si = math.cos(angle), math.sin(angle)
    dy, dz = result[:, 1] - pivot["y"], result[:, 2] - pivot["z"]
    result[:, 1] = pivot["y"] + co * dy - si * dz
    result[:, 2] = pivot["z"] + si * dy + co * dz
    return result


def samples(mesh):
    vertices = mesh.vertices.astype(float)
    return np.concatenate((vertices, vertices[mesh.triangles].mean(axis=1)))


def plate_samples(mesh, g):
    # Large handle faces need interior probes: vertices/centroids alone can miss
    # the small physical stop that crosses the middle of a tall flat triangle.
    triangles = mesh.vertices[mesh.triangles].astype(float)
    triangles = triangles[triangles[:, :, 2].max(axis=1) > g["pivot"]["z"]+g["hub_radius"]+.1]
    weights = np.array([[a/8, b/8, 1-(a+b)/8] for a in range(9) for b in range(9-a)])
    return np.einsum("wi,tij->twj", weights, triangles).reshape(-1, 3)


@lru_cache(maxsize=20)
def _built_case(serialized):
    p = json.loads(serialized)
    meshes = {mesh.part: mesh for _, mesh in geometry.collect_target_meshes(p, assembled=True)}
    fields = {part: geometry.build_part_field(p, part)[0] for part in meshes}
    return p, meshes, fields


def case(p):
    return _built_case(json.dumps(normalize_params(p), sort_keys=True, separators=(",", ":")))


def _case(clearance=.2, retention=.6, thickness=2., diameter=3.):
    return case({"style": "snap_latch", "fit_clearance": clearance,
                 "latch_retention": retention, "latch_thickness": thickness,
                 "latch_pivot_diameter": diameter})


def pin_points(points, p, g, cam_only=False):
    outside_hub = np.abs(points[:, 0] - g["pivot"]["x"]) > p["latch_width"] / 2 + 1e-5
    if cam_only:
        radial = np.hypot(points[:, 1] - g["pivot"]["y"], points[:, 2] - g["pivot"]["z"])
        outside_hub &= radial > g["pin_radius"] + .01
    return outside_hub


def assert_locked_retention(test, p):
    p, meshes, fields = case(p)
    for part in ("clip_left", "clip_right"):
        g = geometry.latch_geometry(p, part)
        xy = np.array([[g["pivot"]["x"], g["hook_y"] - p["latch_retention"] / 2]])
        test.assertTrue(planar.contains_planar_points(meshes["lid"], xy, g["catch_top_z"], True).all())
        test.assertTrue(planar.contains_planar_points(meshes[part], xy, g["hook_bottom_z"], False).all())
        point = np.column_stack((xy, [g["catch_top_z"] - .001]))
        test.assertLess(float(fields["lid"](point)[0]), 0)
        test.assertGreater(float(fields[part](point)[0]), 0)
        moved = point + np.column_stack((np.zeros(121), np.zeros(121), np.linspace(0, 3, 121)))
        test.assertLess(float(fields[part](moved).min()), -.02,
                        "A real catch/hook pair must hold vertical lid motion")
        test.assertLess(xy[0, 1] - g["pivot"]["y"], -.1,
                        "Upward lid contact must act on the closing side of the pivot")


def assert_detent_ramp(test, p):
    p, meshes, fields = case(p); part = "clip_left"
    g = geometry.latch_geometry(p, part); points = samples(meshes[part])
    points = points[pin_points(points, p, g, cam_only=True)]
    test.assertGreater(len(points), 4, "The pin cam must be actual mesh material")
    depths = []
    for angle in np.linspace(0, 25, 101):
        moved = rotate_x(points, g["pivot"], angle)
        depths.append(max(0., -float(fields["base"](moved).min())))
    test.assertEqual(depths[0], 0, "Closed detent must have neutral clearance")
    peak = max(depths); test.assertGreater(peak, .01, "A closed click needs a real temporary barrier")
    middle = np.array(depths)[(np.array(depths) > peak * .2) & (np.array(depths) < peak * .8)]
    test.assertGreaterEqual(len(np.unique(np.round(middle, 3))), 3,
                            "Cam entry must progress across a ramp rather than a square obstruction")
    test.assertAlmostEqual(depths[-1], 0, delta=1e-4)


def assert_operating_motion(test, p):
    p, meshes, fields = case(p); part = "clip_left"
    g = geometry.latch_geometry(p, part)
    points = np.concatenate((samples(meshes[part]), plate_samples(meshes[part], g)))
    cam = pin_points(points, p, g, cam_only=True)
    for angle in np.unique(np.r_[np.linspace(0, 25, 26), [30, 45, 60, 75, 90]]):
        moved = rotate_x(points, g["pivot"], float(angle))
        test.assertGreaterEqual(float(fields["lid"](moved).min()), -1e-4,
                                f"Hook or grip traverses the lid at {angle} degrees")
        test.assertGreaterEqual(float(fields["base"](moved[~cam]).min()), -1e-4,
                                f"Non-cam latch material collides with the base at {angle} degrees")
        penetration = float(fields["base"](moved[cam]).min())
        if angle < g["cam_interval"][0] or angle > g["cam_interval"][1]:
            test.assertGreaterEqual(penetration, -1e-4, "Interference must be transient and confined to the cam")
        else:
            test.assertGreaterEqual(penetration, -g["socket_snap"] - .02,
                                    "Cam interference must be bounded, not a hidden rigid collision")


def assert_open_lid_lift(test, p):
    p, meshes, fields = case(p); points = samples(meshes["lid"])
    for travel in np.linspace(0, p["height_z"] + p["lid_wall_height"] + 5, 25):
        moved = points + [0, 0, travel]
        test.assertGreaterEqual(float(fields["base"](moved).min()), -1e-4)
        for part in ("clip_left", "clip_right"):
            g = geometry.latch_geometry(p, part)
            query = rotate_x(moved, g["pivot"], -g["release_angle"])
            test.assertGreaterEqual(float(fields[part](query).min()), -1e-4,
                                    "Lid must lift while the unlocked levers stay attached to the base")


def _inside_triangle_2d(points, triangle, epsilon=1e-7):
    signs = []
    for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
        edge, delta = b-a, points-a
        signs.append(edge[0]*delta[:, 1]-edge[1]*delta[:, 0])
    signs = np.asarray(signs)
    return (signs > epsilon).all(axis=0) | (signs < -epsilon).all(axis=0)


def _segment_pierces(a, b, triangles):
    # Two-sided segment/triangle test; strict interiors exclude shared boundaries.
    direction = b-a; u = triangles[:, 1]-triangles[:, 0]; v = triangles[:, 2]-triangles[:, 0]
    cross = np.cross(direction, v); determinant = np.einsum("ij,ij->i", u, cross)
    good = np.abs(determinant) > 1e-9
    inverse = np.divide(1., determinant, out=np.zeros_like(determinant), where=good)
    delta = a-triangles[:, 0]
    first = np.einsum("ij,ij->i", delta, cross)*inverse
    normal = np.cross(delta, u)
    second = np.sum(normal*direction, axis=1)*inverse
    distance = np.einsum("ij,ij->i", v, normal)*inverse
    return good & (first > 1e-7) & (second > 1e-7) & (first+second < 1-1e-7) & (distance > 1e-7) & (distance < 1-1e-7)


def _coplanar_area_overlap(triangle, others):
    amount = len(others)
    points = np.concatenate((others, others.mean(axis=1)[:, None, :]), axis=1)
    result = _inside_triangle_2d(points.reshape(-1, 2), triangle).reshape(amount, 4).any(axis=1)
    edges = np.roll(others, -1, axis=1)-others
    for point in np.r_[triangle, triangle.mean(axis=0)[None]]:
        delta = point-others
        signs = edges[:, :, 0]*delta[:, :, 1]-edges[:, :, 1]*delta[:, :, 0]
        result |= (signs > 1e-7).all(axis=1) | (signs < -1e-7).all(axis=1)
    for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
        ab = b-a
        for corner in range(3):
            c, d = others[:, corner], others[:, (corner+1)%3]; cd = d-c
            s1 = ab[0]*(c[:, 1]-a[1])-ab[1]*(c[:, 0]-a[0])
            s2 = ab[0]*(d[:, 1]-a[1])-ab[1]*(d[:, 0]-a[0])
            t1 = cd[:, 0]*(a[1]-c[:, 1])-cd[:, 1]*(a[0]-c[:, 0])
            t2 = cd[:, 0]*(b[1]-c[:, 1])-cd[:, 1]*(b[0]-c[:, 0])
            result |= (((s1 > 1e-7) & (s2 < -1e-7)) | ((s1 < -1e-7) & (s2 > 1e-7))) & (
                ((t1 > 1e-7) & (t2 < -1e-7)) | ((t1 < -1e-7) & (t2 > 1e-7)))
    return result


def proper_triangle_intersections(mesh):
    """Focused actual-mesh audit: proper crossings and coplanar area overlaps.

    Shared vertices/edges and zero-area tangencies are not failures. This is
    a numerical check at stated tolerances, not a general exact CAD predicate.
    """
    triangles = mesh.vertices[mesh.triangles].astype(float)
    low, high = triangles.min(axis=1), triangles.max(axis=1)
    numbers = np.arange(len(triangles)); result = []
    for index, triangle in enumerate(triangles):
        candidates = numbers[(numbers > index) & (low <= high[index]+1e-6).all(axis=1)
                             & (high >= low[index]-1e-6).all(axis=1)]
        if not len(candidates):
            continue
        other = triangles[candidates]; crossing = np.zeros(len(other), dtype=bool)
        for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
            crossing |= _segment_pierces(a, b, other)
        for corner in range(3):
            # Reverse direction, vectorized over candidate triangles.
            target = np.broadcast_to(triangle, other.shape)
            crossing |= _segment_pierces(other[:, corner], other[:, (corner+1)%3], target)
        normal = np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0])
        normal /= np.linalg.norm(normal)
        coplanar = (np.abs((other-triangle[0]) @ normal).max(axis=1) < 1e-5)
        axes = [axis for axis in range(3) if axis != int(np.argmax(np.abs(normal)))]
        projected = triangle[:, axes]
        other_xy = other[:, :, axes]
        coplanar &= (np.minimum(projected.max(axis=0), other_xy.max(axis=1))
                     - np.maximum(projected.min(axis=0), other_xy.min(axis=1)) > 1e-7).all(axis=1)
        rows = np.flatnonzero(coplanar & ~crossing)
        if len(rows):
            crossing[rows] = _coplanar_area_overlap(projected, other_xy[rows])
        result.extend((index, int(candidates[row])) for row in np.flatnonzero(crossing))
        if len(result) >= 10:
            return result
    return result


def profile_crossings(poly):
    """Nonadjacent proper segment crossings in the authored planar profiles."""
    result = []
    for i, (a, b) in enumerate(zip(poly, np.roll(poly, -1, axis=0))):
        for j, (c, d) in enumerate(zip(poly, np.roll(poly, -1, axis=0))):
            if j <= i+1 or (i == 0 and j == len(poly)-1):
                continue
            ab, cd = b-a, d-c
            cross = lambda x, y: x[0]*y[1]-x[1]*y[0]
            s1, s2 = cross(ab, c-a), cross(ab, d-a)
            t1, t2 = cross(cd, a-c), cross(cd, b-c)
            if s1*s2 < -1e-14 and t1*t2 < -1e-14:
                result.append((i, j))
    return result


class SnapLeverMatingTests(unittest.TestCase):
    def test_transform_is_pure_and_rotation_preserves_the_pin_axis(self):
        p, meshes, _ = _case()
        for part in ("clip_left", "clip_right"):
            g = geometry.latch_geometry(p, part); original = meshes[part].vertices.copy()
            pivot = np.array([[g["pivot"][key] for key in ("x", "y", "z")]])
            for angle in (0, 10, 45, 90):
                moved = geometry.latch_open_transform(original, p, part, angle)
                np.testing.assert_allclose(moved, rotate_x(original, g["pivot"], angle), atol=1e-4, rtol=0)
                np.testing.assert_allclose(geometry.latch_open_transform(pivot, p, part, angle), pivot, atol=1e-8)
                self.assertFalse(np.shares_memory(original, moved))
            np.testing.assert_array_equal(original, meshes[part].vertices)

    def test_pin_mouth_and_hub_provide_radial_and_axial_capture(self):
        p, meshes, fields = _case(); part = "clip_left"
        g = geometry.latch_geometry(p, part); points = samples(meshes[part]); pins = points[pin_points(points, p, g)]
        self.assertGreater(len(pins), 10)
        for angle in (0, 45, 90):
            with self.subTest(angle=angle):
                moved = rotate_x(pins, g["pivot"], angle)
                depths = [float(fields["base"](moved - [0, travel, 0]).min())
                          for travel in np.linspace(0, 2*g["pin_radius"] + 2, 61)]
                self.assertLess(min(depths), -.02, "A pin must not slide through the C socket mouth freely")
                self.assertGreater(depths[-1], 0, "The mounting route must ultimately reach the exterior")
                all_points = rotate_x(points, g["pivot"], angle)
                for sign in (-1, 1):
                    self.assertGreaterEqual(float(fields["base"](all_points + [sign*p["fit_clearance"]*.8, 0, 0]).min()), -1e-4)
                    self.assertLess(float(fields["base"](all_points + [sign*(p["fit_clearance"]+.25), 0, 0]).min()), -.01)
                self.assertGreater(g["axial_engagement"] - p["fit_clearance"] - .25, 0)

    def test_stop_limits_further_closing_and_grip_has_an_accessible_front_patch(self):
        p, meshes, fields = _case(); part = "clip_left"
        g = geometry.latch_geometry(p, part); points = samples(meshes[part])
        stop_points = plate_samples(meshes[part], g)
        self.assertLess(float(fields["base"](rotate_x(stop_points, g["pivot"], -5)).min()), -.01,
                        "The over-centre hook needs a real closing stop")
        # Probe the exposed lower grip between the stop and lid, not behind the catch.
        x = g["pivot"]["x"]
        inner, outer = g["grip_inner_y"], g["grip_outer_y"]
        accessible = False
        for z in np.linspace(g["pivot"]["z"]+g["hub_radius"]+.5, g["catch_top_z"]-.5, 20):
            if fields[part](np.array([[x, (inner+outer)/2, z]]))[0] >= 0:
                continue
            probes = np.array([[x+dx, inner+gap, z+dz] for dx in (-2, 0, 2)
                                for dz in (-.3, 0, .3) for gap in (.3, .8, 1.3)])
            if fields["base"](probes).min() > 0 and fields["lid"](probes).min() > 0:
                accessible = True; break
        self.assertTrue(accessible, "Catch and stop must leave a real accessible patch behind the grip")

    def test_profiles_and_actual_boundary_have_no_proper_self_crossings(self):
        cases = [normalize_params({"style": "snap_latch"}),
                 normalize_params({"style": "snap_latch", "fit_clearance": .4,
                                   "latch_retention": .2, "latch_thickness": 1.2,
                                   "latch_pivot_diameter": 4.})]
        for p in cases:
            with self.subTest(clearance=p["fit_clearance"], diameter=p["latch_pivot_diameter"]):
                # Inspection of the actual planar contours supplements the 3D boundary check.
                _, socket, pin, hub, grip, stop, _ = geometry._snap_profiles(p)
                for name, profile in (("socket", socket), ("pin", pin), ("hub", hub), ("grip", grip), ("stop", stop)):
                    self.assertEqual(profile_crossings(geometry._clean_profile(profile)), [], name)
                parts = ("base", "lid", "clip_left") if p["fit_clearance"] == .2 else ("clip_left",)
                for part in parts:
                    mesh = geometry.generate_box_mesh(p, part)
                    self.assertEqual(proper_triangle_intersections(mesh), [],
                                     f"Actual {part} triangles have a proper crossing or area overlap")

    def test_large_pin_thin_grip_extremes_agree_with_the_unified_solid(self):
        for clearance in (.1, .4):
            p = normalize_params({"style": "snap_latch", "fit_clearance": clearance,
                                  "latch_retention": .2, "latch_thickness": 1.2,
                                  "latch_pivot_diameter": 4.})
            with self.subTest(clearance=clearance):
                mesh = geometry.generate_box_mesh(p, "clip_left")
                mating.FunctionalMatingTests().assert_meshed_boundary(p, "clip_left", mesh)

    def test_mounting_route_flexes_socket_mouth_without_blocking_the_lever_body(self):
        p, meshes, fields = _case(); part = "clip_left"
        g = geometry.latch_geometry(p, part); points = samples(meshes[part])
        mask = pin_points(points, p, g)
        opened = rotate_x(points, g["pivot"], g["release_angle"])
        depths = []
        for travel in np.linspace(0, 2*g["pin_radius"] + 2, 61):
            moved = opened - [0, travel, 0]
            self.assertGreaterEqual(float(fields["base"](moved[~mask]).min()), -1e-4,
                                    "A mountable snap pin cannot require the whole handle to cross the base")
            depths.append(float(fields["base"](moved[mask]).min()))
        self.assertGreaterEqual(depths[0], -1e-4)
        self.assertGreater(depths[-1], 0)
        self.assertLess(min(depths), -.01, "Pin entry must cross the retaining mouth")
        self.assertGreaterEqual(min(depths), -g["socket_snap"] - .03,
                                "Only the bounded mouth snap is allowed during mounting")

    def test_print_layer_events_have_previous_same_part_material(self):
        p, meshes, fields = _case()
        for part in ("clip_left", "clip_right"):
            raw = meshes[part].vertices.astype(float)
            printed = geometry.generate_box_mesh(p, part, print_orientation=True)
            vertices = printed.vertices.astype(float)
            self.assertEqual(len(raw), len(vertices))
            affine = np.linalg.lstsq(np.column_stack((raw, np.ones(len(raw)))), vertices, rcond=None)[0]
            rotation, shift = affine[:3], affine[3]
            np.testing.assert_allclose(rotation @ rotation.T, np.eye(3), atol=1e-5, rtol=0)
            np.testing.assert_allclose(raw @ rotation + shift, vertices, atol=1e-4, rtol=0)
            self.assertAlmostEqual(float(vertices[:, 2].min()), 0, delta=1e-4)
            # Use every noncritical interval of the actual printable triangle mesh.
            # A supported contour may split, but no new floating pin/head/grip may start.
            levels = np.unique(vertices[:, 2])
            for low, high in zip(levels, levels[1:]):
                if high-low < 1e-4:
                    continue
                height = float((low+high)/2)
                for polygon, area in slicing.layer_outer_contours(printed, vertices, height):
                    xy = slicing.polygon_probes(polygon)
                    current = np.column_stack((xy, np.full(len(xy), height)))
                    canonical = (current-shift) @ rotation.T
                    current = current[fields[part](canonical) < -1e-5]
                    self.assertGreater(len(current), 0)
                    if low <= 1e-5:
                        continue
                    previous = current.copy(); previous[:, 2] = low-1e-4
                    canonical = (previous-shift) @ rotation.T
                    self.assertLessEqual(float(fields[part](canonical).min()), 1e-4,
                                         f"New unsupported {area:.4f} mm² lever island near Z={low}")



if __name__ == "__main__":
    unittest.main()
