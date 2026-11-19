"""Independent geometry audit of the full Rugged release-then-open trajectory.

Uses actual printable surfaces and analytic CSG queries, rather than reading or
repeating the UI implementation. This is a digital collision check, not a print
or force certification.
"""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.schema import normalize_params
from box_studio.mesh_generator import (
    np,
    generate_box_mesh,
    build_part_field,
    hinge_geometry,
    collect_target_meshes,
    orient_mesh_for_print,
    topology_report,
)


def surfaces(mesh, count=14000):
    n = min(count // 2, len(mesh.vertices))
    vertices = mesh.vertices[np.linspace(0, len(mesh.vertices) - 1, n, dtype=int)]
    n = min(count // 2, len(mesh.triangles))
    centers = mesh.vertices[
        mesh.triangles[np.linspace(0, len(mesh.triangles) - 1, n, dtype=int)]
    ].mean(axis=1)
    return np.r_[vertices, centers].astype(float)


def rotate_about_hinge(points, hinge, degrees):
    angle = np.deg2rad(degrees)
    out = points.copy()
    y, z = points[:, 1] - hinge["y"], points[:, 2] - hinge["z"]
    out[:, 1] = hinge["y"] + y * np.cos(angle) - z * np.sin(angle)
    out[:, 2] = hinge["z"] + y * np.sin(angle) + z * np.cos(angle)
    return out


class RuggedMotionE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = normalize_params({"style": "rugged_box"})
        cls.hinge = hinge_geometry(cls.p)
        cls.base = generate_box_mesh(cls.p, "base")
        cls.base_points = surfaces(cls.base)
        cls.base_field = staticmethod(build_part_field(cls.p, "base")[0])
        cls.lids = {}
        cls.lid_fields = {}
        for mode in ("pin", "print_in_place"):
            p = normalize_params({**cls.p, "hinge_mode": mode})
            cls.lids[mode] = generate_box_mesh(p, "lid")
            cls.lid_fields[mode] = build_part_field(p, "lid")[0]
        cls.clips = {
            part: generate_box_mesh(cls.p, part) for part in ("clip_left", "clip_right")
        }
        cls.clip_fields = {part: build_part_field(cls.p, part)[0] for part in cls.clips}
        cls.pin_field = staticmethod(build_part_field(cls.p, "pin")[0])

    def assert_clear(self, values, context):
        self.assertGreaterEqual(float(np.min(values)), -0.01, context)

    def test_old_simultaneous_motion_has_real_surface_interference(self):
        # A permanent witness that the old interpolation was mechanically wrong.
        # The redesigned trajectory below must release these same actual clips.
        points = self.clips["clip_right"].vertices.astype(float).copy()
        points[:, 1] -= 0.15
        in_lid = rotate_about_hinge(points, self.hinge, 1.8)
        self.assertLess(float(self.lid_fields["pin"](in_lid).min()), -0.05)

    def test_pin_bore_remains_open_after_the_lid_arm_union(self):
        hg = self.hinge
        radius = hg["radius"]
        clearance = self.p["fit_clearance"]
        witness = np.array([[0, hg["y"], hg["z"] + 1]])
        self.assertAlmostEqual(float(self.lid_fields["pin"](witness)[0]), 0.7, places=5)
        self.assertLess(float(self.pin_field(witness)[0]), 0)
        angles = np.linspace(0, 2 * np.pi, 65)
        for radial, expected in ((radius, clearance), (radius + clearance + 0.1, -0.1)):
            q = np.column_stack(
                (
                    np.zeros(len(angles)),
                    hg["y"] + radial * np.cos(angles),
                    hg["z"] + radial * np.sin(angles),
                )
            )
            np.testing.assert_allclose(self.lid_fields["pin"](q), expected, atol=1e-7)

    def test_both_clips_can_withdraw_fifteen_mm_with_lid_stationary(self):
        for part, mesh in self.clips.items():
            actual = surfaces(mesh)
            for distance in np.linspace(0, 15, 61):
                q = actual.copy()
                q[:, 1] -= distance
                self.assert_clear(
                    self.base_field(q), f"{part} vs base at release {distance}"
                )
                for mode, field in self.lid_fields.items():
                    self.assert_clear(
                        field(q), f"{part} vs {mode} lid at release {distance}"
                    )
            # The release amount gives a finite geometric margin, rather than
            # merely moving the clip vertices just beyond a sampled surface.
            self.assertLess(mesh.bounds_mm["max"][1] - 15, -self.p["depth_y"] / 2 - 10)

    def test_pin_and_captive_lids_open_without_base_or_released_clip_collision(self):
        for mode, mesh in self.lids.items():
            lid = surfaces(mesh)
            for degrees in np.linspace(0, 180, 73):
                world = rotate_about_hinge(lid, self.hinge, -degrees)
                self.assert_clear(
                    self.base_field(world), f"{mode} lid vs base {degrees}"
                )
                # Bidirectional surface queries also catch a base protrusion
                # lying inside a large, sparsely triangulated cap face.
                base_local = rotate_about_hinge(self.base_points, self.hinge, degrees)
                self.assert_clear(
                    self.lid_fields[mode](base_local), f"base vs {mode} lid {degrees}"
                )
                clip_local = world.copy()
                clip_local[:, 1] += 15
                for part, field in self.clip_fields.items():
                    self.assert_clear(
                        field(clip_local), f"{mode} lid vs released {part} {degrees}"
                    )
                if mode == "pin":
                    self.assert_clear(
                        self.pin_field(world), f"pin vs moving lid {degrees}"
                    )

    def test_captive_export_preserves_pair_and_rejects_separate_halves(self):
        p = normalize_params({**self.p, "hinge_mode": "print_in_place"})

        def factory(params, part, printing):
            if part == "base":
                mesh = self.base
            elif part == "lid":
                mesh = self.lids["print_in_place"]
            else:
                mesh = self.clips[part]
            return orient_mesh_for_print(mesh, params, part) if printing else mesh

        items = collect_target_meshes(
            p, "base_and_lid", assembled=False, mesh_factory=factory
        )
        self.assertEqual(
            [m.part for _, m in items],
            ["print_in_place_assembly", "clip_left", "clip_right"],
        )
        report = topology_report(items[0][1])
        self.assertTrue(report["closed"] and report["oriented"], report)
        self.assertEqual(report["components"], 2, report)
        self.assertEqual(items[0][1].bounds_mm["min"][2], 0)
        for target in ("base_only", "lid_only"):
            for assembled in (False, True):
                with self.assertRaisesRegex(ValueError, "preserve the assembly"):
                    collect_target_meshes(
                        p, target, assembled=assembled, mesh_factory=factory
                    )
        # These are intentional accessory/calibration exports, not separated
        # captive halves. Their availability must survive the new target guard.
        gasket = collect_target_meshes(
            {**p, "gasket_enabled": True, "wall_thickness": 3}, "gasket"
        )
        self.assertEqual([m.part for _, m in gasket], ["gasket"])
        kit = collect_target_meshes(p, "fit_test_kit")
        self.assertEqual([m.part for _, m in kit], ["base", "lid", "snap_sample"])


if __name__ == "__main__":
    unittest.main()
