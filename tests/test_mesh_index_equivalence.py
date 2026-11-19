"""Exact indexing optimizations must retain coordinates, winding and rejection."""

from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio import mesh_generator as mg

np = mg.np


def row_unique(points):
    _, first, inverse = np.unique(
        points, axis=0, return_index=True, return_inverse=True
    )
    return first, inverse


def row_edge_keys(directed, vertex_count):
    # A one-dimensional structured view invokes the original two-column numeric
    # row ordering. It is used only by the planar simplifier in the oracle run.
    rows = np.sort(directed, axis=1).copy()
    return rows.view([("a", rows.dtype), ("b", rows.dtype)]).reshape(-1)


def reference_topology(mesh):
    t = mesh.triangles.astype(np.int64)
    directed = np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]))
    edges, counts = np.unique(np.sort(directed, axis=1), axis=0, return_counts=True)
    # Independent graph traversal, rather than mirroring label relaxation.
    adjacency = {int(v): set() for v in np.unique(t)}
    for a, b in edges:
        adjacency[int(a)].add(int(b))
        adjacency[int(b)].add(int(a))
    remaining, components = set(adjacency), 0
    while remaining:
        components += 1
        todo = [remaining.pop()]
        while todo:
            for neighbor in adjacency[todo.pop()]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    todo.append(neighbor)
    reverse = directed[:, ::-1]
    order = np.lexsort((directed[:, 1], directed[:, 0]))
    reverse_order = np.lexsort((reverse[:, 1], reverse[:, 0]))
    euler = len(adjacency) - len(edges) + len(t)
    return {
        "closed": bool(np.all(counts == 2)),
        "oriented": bool(np.array_equal(directed[order], reverse[reverse_order])),
        "components": components,
        "euler": euler,
        "genus": (2 * components - euler) // 2,
        "vertices": len(mesh.vertices),
        "triangles": len(t),
        "volume_cm3": mesh.volume_cm3,
        "interface_error_mm": mesh.interface_error_mm,
    }


class ExactMeshIndexTests(unittest.TestCase):
    def test_unique_xyz_matches_first_inverse_and_signed_zero_bits(self):
        rng = np.random.default_rng(514)
        for dtype in (np.float32, np.float64):
            points = rng.integers(-12, 13, (12000, 3)).astype(dtype) / 4
            points = np.concatenate(
                (np.array([[0.0, -0.0, 0.0], [-0.0, 0.0, -0.0]], dtype=dtype), points)
            )
            expected_first, expected_inverse = row_unique(points)
            first, inverse = mg._unique_xyz_indices(points)
            np.testing.assert_array_equal(first, expected_first)
            np.testing.assert_array_equal(inverse, expected_inverse)
            self.assertEqual(points[first].tobytes(), points[expected_first].tobytes())
        first, inverse = mg._unique_xyz_indices(np.empty((0, 3), dtype=np.float32))
        self.assertEqual((len(first), len(inverse)), (0, 0))

    def test_packed_edges_match_original_row_order_and_groups(self):
        rng = np.random.default_rng(43)
        vertex_count = 250000
        directed = rng.integers(0, vertex_count, (20000, 2), dtype=np.int32)
        directed = np.concatenate((directed, directed[::-1, ::-1], [[0, 0]]))
        rows, first, inverse, counts = np.unique(
            np.sort(directed, axis=1),
            axis=0,
            return_index=True,
            return_inverse=True,
            return_counts=True,
        )
        keys, actual_first, actual_inverse, actual_counts = np.unique(
            mg._undirected_edge_keys(directed, vertex_count),
            return_index=True,
            return_inverse=True,
            return_counts=True,
        )
        np.testing.assert_array_equal(first, actual_first)
        np.testing.assert_array_equal(inverse, actual_inverse)
        np.testing.assert_array_equal(counts, actual_counts)
        np.testing.assert_array_equal(
            rows, np.column_stack((keys // vertex_count, keys % vertex_count))
        )
        self.assertGreater(int(keys.max()), np.iinfo(np.int32).max)

    def test_planar_fans_and_holes_remain_byte_identical(self):
        nx = 22
        vertices = np.array([(x, y, 0.0) for x in range(nx) for y in range(nx)])
        for hole in (False, True):
            triangles = []
            for x in range(nx - 1):
                for y in range(nx - 1):
                    if hole and 7 <= x <= 13 and 7 <= y <= 13:
                        continue
                    a = x * nx + y
                    triangles.extend(((a, a + nx, a + 1), (a + 1, a + nx, a + nx + 1)))
            triangles = np.asarray(triangles, dtype=np.int32)
            with patch.object(mg, "_undirected_edge_keys", row_edge_keys):
                expected = mg._simplify_planar(vertices, triangles)
            actual = mg._simplify_planar(vertices, triangles)
            for a, b in zip(actual, expected):
                self.assertEqual(a.dtype, b.dtype)
                self.assertEqual(a.tobytes(), b.tobytes())

    def test_csg_extraction_is_byte_identical_to_row_unique_oracles(self):
        # Exercise curved surfaces, unions, an enclosed hole and planar seams.
        def field(points):
            x, y, z = points.T
            body = np.maximum(np.hypot(x, y) - 3.4, np.abs(z) - 2)
            ear = np.maximum.reduce((np.abs(x - 3) - 2, np.abs(y) - 1, np.abs(z) - 1))
            return np.maximum(np.minimum(body, ear), 0.7 - np.hypot(x, y))

        hints = {
            "params": mg.normalize_params({}),
            "levels": [-2, -1, 1, 2],
            "rectangles": [],
            "circles": [(0, 1, 0, 0, 3.4), (0, 1, 0, 0, 0.7)],
            "planes": [[-3.4, 1, 5], [-1, 1], [-2, -1, 1, 2]],
        }
        with (
            patch.object(mg, "_unique_xyz_indices", row_unique),
            patch.object(mg, "_undirected_edge_keys", row_edge_keys),
        ):
            expected = mg.mesh_field(field, (-4, 6, -4, 4, -3, 3), hints, "oracle")
        actual = mg.mesh_field(field, (-4, 6, -4, 4, -3, 3), hints, "oracle")
        for attribute in ("vertices", "triangles", "face_normals"):
            self.assertEqual(
                getattr(actual, attribute).tobytes(),
                getattr(expected, attribute).tobytes(),
            )
        self.assertEqual(actual.bounds_mm, expected.bounds_mm)
        self.assertEqual(actual.volume_cm3, expected.volume_cm3)
        self.assertEqual(mg.topology_report(actual), reference_topology(expected))

    def test_topology_valid_and_invalid_cases_match_independent_oracle(self):
        vertices = np.array(
            [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float32
        )
        triangles = np.array(
            [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]], dtype=np.int32
        )
        mesh = mg.MeshData(vertices, triangles, np.zeros((4, 3)), {}, 1 / 6000)
        reversed_face = triangles.copy()
        reversed_face[0] = reversed_face[0, ::-1]
        cases = [
            mesh,
            replace(mesh, triangles=triangles[:-1]),
            replace(mesh, triangles=reversed_face),
            replace(mesh, triangles=np.concatenate((triangles, triangles[:1]))),
            replace(
                mesh,
                vertices=np.concatenate((vertices, vertices + 3)),
                triangles=np.concatenate((triangles, triangles + 4)),
            ),
        ]
        for case in cases:
            self.assertEqual(mg.topology_report(case), reference_topology(case))
        self.assertTrue(mg.topology_report(mesh)["oriented"])
        self.assertFalse(mg.topology_report(cases[1])["closed"])
        self.assertFalse(mg.topology_report(cases[2])["oriented"])
        self.assertFalse(mg.topology_report(cases[3])["closed"])
        self.assertEqual(mg.topology_report(cases[4])["components"], 2)

    def test_large_vertex_indices_cannot_hide_an_inverted_face(self):
        # With 131072 vertices these tails collided under int32 a*N+b. Then an
        # inverted face incorrectly passed because each triangle has the same
        # multiset of incoming and outgoing vertex indices.
        vertices = np.zeros((131072, 3), dtype=np.float32)
        ids = np.array([0, 32768, 65536, 98304], dtype=np.int32)
        vertices[ids] = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
        t = ids[np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])]
        mesh = mg.MeshData(vertices, t, np.zeros((4, 3)), {}, 1 / 6000)
        self.assertTrue(mg.topology_report(mesh)["oriented"])
        t[0] = t[0, ::-1]
        self.assertFalse(mg.topology_report(mesh)["oriented"])
        self.assertEqual(mg.topology_report(mesh), reference_topology(mesh))


if __name__ == "__main__":
    unittest.main()
