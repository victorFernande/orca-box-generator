"""Independent functional mating checks; no reference-model assets or dependencies.

Closed-state clearance and deliberately transient snap interference are different
requirements. These checks use analytic solid membership, not a watertightness
proxy or a material-deformation simulation.
"""
from __future__ import annotations

import sys
from collections import defaultdict
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.mesh_generator import build_part_field, collect_target_meshes, generate_box_mesh, np
from box_studio.schema import normalize_params


def solid_grid(field, bounds, spacing=0.45):
    axes = [np.linspace(bounds[i], bounds[i + 1],
                        int(np.ceil((bounds[i + 1] - bounds[i]) / spacing)) + 1)
            for i in (0, 2, 4)]
    points = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
    return points[field(points) < -1e-5]


class FunctionalMatingTests(unittest.TestCase):
    @staticmethod
    def lip_profile(params):
        lid, _, _ = build_part_field(params, "lid")
        inside = params["width_x"] / 2 - params["wall_thickness"]
        zs = np.linspace(params["height_z"] - params["lip_depth"] + 0.02,
                         params["height_z"] - 0.1, 241)
        xs = np.linspace(inside - 0.8, inside + 0.4, 601)
        xx, zz = np.meshgrid(xs, zs, indexing="xy")
        points = np.column_stack((xx.ravel(), np.zeros(xx.size), zz.ravel()))
        solid = (lid(points) < -1e-7).reshape(xx.shape)
        outside = np.where(solid, xx, -np.inf).max(axis=1)
        return zs, outside - inside

    def test_lip_snap_retention_is_explicit_and_independent_of_locating_gap(self):
        for retention in (0.06, 0.22):
            peaks = []
            for clearance in (0.1, 0.4):
                with self.subTest(retention=retention, clearance=clearance):
                    p = normalize_params({"style": "lip_snap", "fit_clearance": clearance,
                                          "snap_retention": retention})
                    self.assertIn("snap_retention", p,
                                  "Snap interference must be an explicit parameter")
                    self.assertAlmostEqual(p["snap_retention"], retention)
                    _, profile = self.lip_profile(p)
                    peak = float(profile.max())
                    self.assertAlmostEqual(peak, retention, delta=0.004,
                                           msg="Actual bead interference must match its control")
                    peaks.append(peak)
            if len(peaks) == 2:
                self.assertAlmostEqual(peaks[0], peaks[1], delta=0.004,
                                       msg="Locating clearance must not silently redefine retention")

    def test_lip_bead_has_progressive_axial_entry_ramp(self):
        p = normalize_params({"style": "lip_snap", "snap_retention": 0.22})
        zs, profile = self.lip_profile(p)
        peak = float(profile.max())
        self.assertGreater(peak, 0.02, "A snap bead must provide deliberate retention")
        # The lower bead edge enters first as the lid moves down. Distinct
        # intermediate radial extents prove a ramp rather than a square step.
        first_peak = int(np.flatnonzero(profile >= peak * 0.9)[0])
        entering = profile[:first_peak + 1]
        middle = entering[(entering > peak * 0.2) & (entering < peak * 0.8)]
        self.assertGreaterEqual(len(np.unique(np.round(middle, 3))), 3,
                                "Snap entrance jumps directly to full interference")
        self.assertGreater(float(np.ptp(zs[:first_peak + 1][
            (entering > peak * 0.2) & (entering < peak * 0.8)])), 0.1,
            "Entry relief must extend axially, not only round XY corners")

    def assert_meshed_boundary(self, params, part, mesh):
        vertices = mesh.vertices.astype(np.float64)
        faces = mesh.triangles
        self.assertTrue(np.isfinite(vertices).all())
        self.assertTrue((faces >= 0).all() and (faces < len(vertices)).all())
        triangles = vertices[faces]
        cross = np.cross(triangles[:, 1] - triangles[:, 0],
                         triangles[:, 2] - triangles[:, 0])
        self.assertTrue((np.linalg.norm(cross, axis=1) > 0).all())
        directed = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
        edges, counts = np.unique(np.sort(directed, axis=1), axis=0, return_counts=True)
        self.assertTrue((counts == 2).all(), "Actual float32 mesh must be closed")
        adjacency = defaultdict(set)
        for a, b in edges.tolist():
            adjacency[a].add(b); adjacency[b].add(a)
        visited, pending = set(), [next(iter(adjacency))]
        while pending:
            vertex = pending.pop()
            if vertex not in visited:
                visited.add(vertex); pending.extend(adjacency[vertex] - visited)
        self.assertEqual(len(visited), len(vertices), "Each printable part must be one connected shell")
        codes = np.sort(directed[:, 0] * len(vertices) + directed[:, 1])
        opposite = np.sort(directed[:, 1] * len(vertices) + directed[:, 0])
        self.assertTrue(np.array_equal(codes, opposite), "Every edge needs opposite orientations")
        self.assertGreater(float(np.einsum("ij,ij->i", triangles[:, 0],
                               np.cross(triangles[:, 1], triangles[:, 2])).sum()), 0)
        # Edge incidence misses two surface fans pinched at a single vertex.
        links = defaultdict(list)
        for a, b, c in faces.tolist():
            links[a].append((b, c)); links[b].append((c, a)); links[c].append((a, b))
        for vertex, pairs in links.items():
            graph = defaultdict(set)
            for a, b in pairs:
                graph[a].add(b); graph[b].add(a)
            seen, todo = set(), [next(iter(graph))]
            while todo:
                node = todo.pop()
                if node not in seen:
                    seen.add(node); todo.extend(graph[node] - seen)
            self.assertEqual(len(seen), len(graph), f"Pinched surface at vertex {vertex}")
            self.assertTrue(all(len(neighbours) == 2 for neighbours in graph.values()))
        field, _, _ = build_part_field(params, part)
        chord_budget = min(params["fit_clearance"] / 4, 0.04)
        self.assertLessEqual(float(np.abs(field(vertices)).max()), chord_budget + 1e-4,
                             "Fast mesh vertices must agree with the analytic solid")
        self.assertLessEqual(float(np.abs(field(triangles.mean(axis=1))).max()), chord_budget + 1e-4,
                             "Triangle interiors must meet the actual chord budget")
        return len(vertices) - len(edges) + len(faces)

    def test_open_bin_hand_openings_and_actual_mesh(self):
        for faces in ("left_right", "front_back"):
            with self.subTest(faces=faces):
                p = normalize_params({"style": "open_bin", "handle_faces": faces})
                items = collect_target_meshes(p, target="base_and_lid", assembled=True)
                self.assertEqual([mesh.part for _, mesh in items], ["base"],
                                 "An open bin must not silently export a lid or latch")
                mesh = items[0][1]
                euler = self.assert_meshed_boundary(p, "base", mesh)
                self.assertEqual(euler, -2, "Two hand openings must yield genus two")
                field, _, _ = build_part_field(p, "base")
                axis = 0 if faces == "left_right" else 1
                size = p["width_x"] if axis == 0 else p["depth_y"]
                z = p["height_z"] - p["handle_top_margin"] - p["handle_height"] / 2
                for sign in (-1, 1):
                    hole = np.array([[0., 0., z]])
                    hole[0, axis] = sign * (size / 2 - p["wall_thickness"] / 2)
                    self.assertGreater(float(field(hole)[0]), 0, "Hand opening must pass through the wall")
                    bridge = hole.copy(); bridge[0, 2] = p["height_z"] - p["handle_top_margin"] / 2
                    self.assertLess(float(field(bridge)[0]), 0, "A continuous upper grip bridge is required")
                self.assertLess(float(field(np.array([[0., 0., p["floor_thickness"] / 2]]))[0]), 0)
                self.assertGreater(float(field(np.array([[0., 0., p["height_z"]]]))[0]), 0,
                                   "Open bin must remain open at the top")

    def test_snap_latch_actual_parts_are_closed_and_clear_at_rest(self):
        p = normalize_params({"style": "snap_latch"})
        items = collect_target_meshes(p, target="base_and_lid", assembled=True)
        meshes = {mesh.part: mesh for _, mesh in items}
        self.assertEqual(set(meshes), {"base", "lid", "clip_left", "clip_right"})
        base, _, _ = build_part_field(p, "base")
        lid, _, _ = build_part_field(p, "lid")
        for part, mesh in meshes.items():
            with self.subTest(part=part):
                self.assert_meshed_boundary(p, part, mesh)
                if part.startswith("clip"):
                    clip, bounds, _ = build_part_field(p, part)
                    points = solid_grid(clip, bounds, spacing=0.3)
                    self.assertGreater(len(points), 10)
                    for other, field in (("base", base), ("lid", lid)):
                        self.assertGreaterEqual(float(field(points).min()), -1e-5,
                                                f"Closed latch permanently intersects {other}")

    def test_snap_latch_clips_actually_retain_vertical_lid_motion(self):
        import test_snap_lever_mating as lever
        for clearance in (0.1, 0.4):
            for retention in (0.2, 1.2):
                with self.subTest(clearance=clearance, retention=retention):
                    p = normalize_params({"style": "snap_latch", "fit_clearance": clearance,
                                          "latch_retention": retention})
                    lever.assert_locked_retention(self, p)

    def test_snap_latch_detent_has_progressive_entry_ramp(self):
        import test_snap_lever_mating as lever
        p = normalize_params({"style": "snap_latch"})
        lever.assert_detent_ramp(self, p)

    def test_snap_latch_rotates_with_only_the_intended_transient_cam_interference(self):
        import test_snap_lever_mating as lever
        for clearance in (0.1, 0.4):
            with self.subTest(clearance=clearance):
                p = normalize_params({"style": "snap_latch", "fit_clearance": clearance})
                lever.assert_operating_motion(self, p)

    def test_snap_latch_lid_detaches_while_open_levers_remain_attached(self):
        import test_snap_lever_mating as lever
        for clearance in (0.1, 0.4):
            with self.subTest(clearance=clearance):
                p = normalize_params({"style": "snap_latch", "fit_clearance": clearance})
                lever.assert_open_lid_lift(self, p)

    def test_rugged_clips_have_no_permanent_closed_overlap(self):
        for clearance in (0.1, 0.2, 0.4):
            p = normalize_params({"style": "rugged_box", "fit_clearance": clearance})
            base, _, _ = build_part_field(p, "base")
            lid, _, _ = build_part_field(p, "lid")
            for part in ("clip_left", "clip_right"):
                with self.subTest(clearance=clearance, part=part):
                    clip, bounds, _ = build_part_field(p, part)
                    points = solid_grid(clip, bounds)
                    self.assertGreater(len(points), 10, "Clip must contain a printable solid")
                    # Exact historical counterexamples supplement the grid so a
                    # narrow overlapping arm cannot hide between sampled planes.
                    cx = (-1 if part == "clip_left" else 1) * p["width_x"] * 0.24
                    witnesses = np.array([
                        [cx + 2.8, -p["depth_y"] / 2 - 1.5, p["height_z"] - 6],
                        [cx - 2.8, -p["depth_y"] / 2 - 1.5, p["height_z"] - 6],
                        [cx, -p["depth_y"] / 2 - 1.5, p["height_z"] - 7.1],
                    ])
                    points = np.concatenate((points, witnesses[clip(witnesses) < -1e-5]))
                    for other, field in (("base", base), ("lid", lid)):
                        values = field(points)
                        index = int(np.argmin(values))
                        self.assertGreaterEqual(
                            float(values[index]), -1e-5,
                            f"{part} permanently penetrates {other} at {points[index].tolist()}; "
                            "transient insertion flexure does not justify undeformed closed overlap",
                        )

    def test_sliding_detent_resists_withdrawal_and_is_clear_when_closed(self):
        for clearance in (0.1, 0.2, 0.4):
            with self.subTest(clearance=clearance):
                p = normalize_params({"style": "sliding_lid", "fit_clearance": clearance})
                base, _, _ = build_part_field(p, "base")
                lid, _, _ = build_part_field(p, "lid")
                # Probe the central rear detent, excluding the side rails and
                # front puller. A snap may interfere transiently, but is clear
                # in its resting closed pocket.
                edge = p["depth_y"] / 2 - p["wall_thickness"]
                h = p["height_z"]
                axes = [np.linspace(-2.5, 2.5, 21),
                        np.linspace(edge - 4, edge + 0.6, 47),
                        np.linspace(h - 3.4, h - 1.2, 45)]
                points = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
                points = points[lid(points) < -1e-5]
                self.assertGreater(len(points), 0, "A rear detent must exist")
                self.assertGreaterEqual(float(base(points).min()), -1e-5,
                                        "Detent permanently overlaps the base when closed")
                penetration = 0.0
                for travel in np.linspace(0.05, 4, 80):
                    moved = points - np.array([0, travel, 0])
                    penetration = max(penetration, -float(base(moved).min()))
                self.assertGreater(
                    penetration, 1e-4,
                    "Rear detent exits into the cavity without a retention barrier; "
                    "closed topology alone does not establish a detent",
                )


if __name__ == "__main__":
    unittest.main()
