"""The PIP case must retain its open, captive relationship in the actual files."""
from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.schema import normalize_params, validate_params
from box_studio.mesh_generator import MeshData, collect_target_meshes, np, topology_report
from box_studio.exporters import write_binary_stl, write_orca_3mf

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


class ClamshellExportTests(unittest.TestCase):
    def params(self, **updates):
        return normalize_params({"style": "clamshell_pip", "width_x": 120,
                                 "depth_y": 65, "height_z": 14, **updates})

    def assert_assembly(self, mesh):
        report = topology_report(mesh)
        self.assertTrue(report["closed"] and report["oriented"], report)
        self.assertEqual(report["components"], 2, "Each moving half must be a connected shell")
        self.assertGreater(mesh.volume_cm3, 0)
        self.assertAlmostEqual(float(mesh.vertices[:, 2].min()), 0, delta=1e-4)
        return report

    def test_3mf_has_one_object_and_one_transform_for_both_open_halves(self):
        for height in (14, 25):
            with self.subTest(height=height), tempfile.TemporaryDirectory() as folder:
                params = self.params(height_z=height)
                self.assertEqual(validate_params(params), [])
                preview = collect_target_meshes(params, "base_and_lid", assembled=True)
                self.assertEqual([mesh.part for _, mesh in preview], ["base", "lid"])
                items = collect_target_meshes(params, "base_and_lid", assembled=False)
                self.assertEqual(len(items), 1, "Packing must never separate the two hinge halves")
                name, assembly = items[0]
                report = self.assert_assembly(assembly)
                self.assertEqual(report["euler"], sum(topology_report(mesh)["euler"] for _, mesh in preview))
                self.assertEqual(len(assembly.triangles), sum(len(mesh.triangles) for _, mesh in preview))
                path = write_orca_3mf(Path(folder)/"clamshell.3mf", items, params,
                                     {"bed_x": 220, "bed_y": 220, "bed_z": 250})
                with zipfile.ZipFile(path) as archive:
                    model = ET.fromstring(archive.read("3D/3dmodel.model"))
                    settings = ET.fromstring(archive.read("Metadata/model_settings.config"))
                    print_settings = json.loads(archive.read("Metadata/project_settings.config"))
                objects = model.findall("m:resources/m:object", NS)
                placed = model.findall("m:build/m:item", NS)
                self.assertEqual(len(objects), 1)
                self.assertEqual(len(placed), 1)
                self.assertEqual(objects[0].attrib["name"], name)
                self.assertEqual(len(settings.findall("object")), 1)
                vertices = np.array([[v.attrib[axis] for axis in ("x", "y", "z")]
                                     for v in objects[0].findall("m:mesh/m:vertices/m:vertex", NS)], dtype=np.float32)
                triangles = np.array([[t.attrib[key] for key in ("v1", "v2", "v3")]
                                      for t in objects[0].findall("m:mesh/m:triangles/m:triangle", NS)], dtype=np.int32)
                np.testing.assert_array_equal(vertices, assembly.vertices)
                np.testing.assert_array_equal(triangles, assembly.triangles)
                transform = np.array(placed[0].attrib["transform"].split(), dtype=float).reshape(4, 3)
                np.testing.assert_array_equal(transform[:3], np.eye(3))
                printed = vertices @ transform[:3] + transform[3]
                self.assertTrue(np.all(printed.min(axis=0) >= -1e-4))
                self.assertTrue(np.all(printed.max(axis=0) <= [220.0001, 220.0001, 250.0001]))
                # Both floors lie on the same plane. The hinge can extend above
                # the rim, so its envelope must not be confused with half height.
                floor = printed[np.isclose(printed[:, 2], 0, atol=1e-4)]
                self.assertGreater(float(np.ptp(floor[:, 1])), params["depth_y"] * 1.8)
                self.assertGreater(float(np.ptp(printed[:, 1])), params["depth_y"] * 2)
                self.assertEqual(print_settings["spiral_mode"], "0")
                self.assertEqual(print_settings["wall_loops"], "4")

    def test_binary_stl_reconstructs_two_oriented_shells_in_the_same_open_pose(self):
        params = self.params()
        _, assembly = collect_target_meshes(params, assembled=False)[0]
        expected = self.assert_assembly(assembly)
        with tempfile.TemporaryDirectory() as folder:
            path = write_binary_stl(Path(folder)/"clamshell.stl", assembly)
            data = path.read_bytes()
        count = struct.unpack("<I", data[80:84])[0]
        self.assertEqual(count, len(assembly.triangles))
        records = np.frombuffer(data, dtype=np.dtype([("normal", "<f4", (3,)),
                                ("points", "<f4", (3, 3)), ("attribute", "<u2")]), offset=84)
        np.testing.assert_array_equal(records["points"], assembly.vertices[assembly.triangles])
        vertices, inverse = np.unique(records["points"].reshape(-1, 3), axis=0, return_inverse=True)
        reconstructed = MeshData(vertices, inverse.reshape(-1, 3), records["normal"],
                                 assembly.bounds_mm, assembly.volume_cm3, assembly.part)
        actual = self.assert_assembly(reconstructed)
        self.assertEqual(actual["euler"], expected["euler"])

    def test_oversize_open_assembly_is_rejected_without_rearranging_or_scaling(self):
        params = self.params()
        items = collect_target_meshes(params, assembled=False)
        before = items[0][1].vertices.copy()
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            write_orca_3mf(Path(folder)/"too-small.3mf", items, params,
                           {"bed_x": 100, "bed_y": 100, "bed_z": 250})
        np.testing.assert_array_equal(items[0][1].vertices, before)


if __name__ == "__main__":
    unittest.main()
