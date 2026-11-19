"""Real storage models retain piece identity, topology and bed placement on export."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.schema import normalize_params
from box_studio.mesh_generator import MeshData, collect_target_meshes, np, topology_report
from box_studio.exporters import write_binary_stl, write_orca_3mf

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


class StorageExportTests(unittest.TestCase):
    def test_real_storage_3mf_preserves_parts_topology_and_nonoverlapping_bed_layout(self):
        # The pivot sockets project beyond the body. Exercise a compact 220 mm
        # layout and the 160x95 case actually loaded on a 260 mm native plate.
        latch_parts = ("base", "lid", "clip_left", "clip_right")
        cases = (("open_bin", 95, 220, ("base",)),
                 ("stackable_bin", 95, 220, ("base",)),
                 ("snap_latch", 90, 220, latch_parts),
                 ("snap_latch", 95, 260, latch_parts))
        for style, depth, bed, expected in cases:
            with self.subTest(style=style, depth=depth, bed=bed), tempfile.TemporaryDirectory() as folder:
                params = normalize_params({"style": style, "width_x": 160,
                                           "depth_y": depth, "height_z": 35})
                items = collect_target_meshes(params, "base_and_lid", "en", assembled=False)
                self.assertEqual(tuple(mesh.part for _, mesh in items), expected)
                path = write_orca_3mf(Path(folder)/"storage.3mf", items, params,
                                     {"bed_x": bed, "bed_y": bed, "bed_z": 250})
                with zipfile.ZipFile(path) as archive:
                    root = ET.fromstring(archive.read("3D/3dmodel.model"))
                objects = root.findall("m:resources/m:object", NS)
                self.assertEqual([obj.attrib["name"] for obj in objects], [name for name, _ in items])
                bounds = {}
                for obj, (_, original) in zip(objects, items):
                    vertices = np.array([[v.attrib[axis] for axis in ("x", "y", "z")]
                                         for v in obj.findall("m:mesh/m:vertices/m:vertex", NS)], dtype=np.float32)
                    triangles = np.array([[t.attrib[key] for key in ("v1", "v2", "v3")]
                                          for t in obj.findall("m:mesh/m:triangles/m:triangle", NS)], dtype=np.int32)
                    np.testing.assert_array_equal(vertices, original.vertices)
                    np.testing.assert_array_equal(triangles, original.triangles)
                    reconstructed = MeshData(vertices, triangles, original.face_normals,
                                             original.bounds_mm, original.volume_cm3, original.part)
                    topology = topology_report(reconstructed)
                    self.assertTrue(topology["closed"] and topology["oriented"])
                    self.assertEqual(topology["components"], 1)
                    # Hand openings make the open bin genus2; do not assume Euler2.
                    self.assertEqual(topology["genus"], 2 if style == "open_bin" else 0)
                    bounds[obj.attrib["id"]] = vertices
                placed = []
                for item in root.findall("m:build/m:item", NS):
                    transform = np.array(item.attrib["transform"].split(), dtype=float).reshape(4, 3)
                    vertices = bounds[item.attrib["objectid"]] @ transform[:3] + transform[3]
                    low, high = vertices.min(axis=0), vertices.max(axis=0)
                    self.assertTrue(np.all(low >= -1e-4))
                    self.assertTrue(np.all(high <= [bed+.0001, bed+.0001, 250.0001]))
                    self.assertAlmostEqual(float(low[2]), 0.0, places=4)
                    for other_low, other_high in placed:
                        overlap = np.minimum(high[:2], other_high[:2])-np.maximum(low[:2], other_low[:2])
                        self.assertTrue(np.any(overlap <= 0), "Print objects overlap in XY")
                    placed.append((low, high))

    def test_snap_layout_does_not_scale_or_overlap_to_force_a_small_plate(self):
        params = normalize_params({"style": "snap_latch", "width_x": 160,
                                   "depth_y": 95, "height_z": 35})
        items = collect_target_meshes(params, assembled=False)
        originals = [mesh.vertices.copy() for _, mesh in items]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/"too-small.3mf"
            with self.assertRaisesRegex(ValueError, "do not fit.*bed"):
                write_orca_3mf(target, items, params,
                               {"bed_x": 220, "bed_y": 220, "bed_z": 250})
            self.assertFalse(target.exists())
        for (_, mesh), original in zip(items, originals):
            np.testing.assert_array_equal(mesh.vertices, original)

    def test_real_snap_latch_binary_stl_contains_each_selected_piece(self):
        params = normalize_params({"style": "snap_latch", "lid_wall_height": 10})
        with tempfile.TemporaryDirectory() as folder:
            for index, (_, mesh) in enumerate(collect_target_meshes(params, assembled=False)):
                with self.subTest(part=mesh.part):
                    path = write_binary_stl(Path(folder)/f"part-{index}.stl", mesh)
                    data = path.read_bytes()
                    count = struct.unpack("<I", data[80:84])[0]
                    self.assertEqual(count, len(mesh.triangles))
                    self.assertEqual(len(data), 84 + 50*count)
                    self.assertAlmostEqual(mesh.bounds_mm["min"][2], 0.0, places=5)


if __name__ == "__main__":
    unittest.main()
