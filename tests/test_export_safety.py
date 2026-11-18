"""Regression checks for the actual exported representation and selected bed limits."""

from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.mesh_generator import np
from box_studio.exporters import write_binary_stl, write_orca_3mf
from box_studio import plugin_main as bridge
from box_studio.schema import normalize_params


def tetrahedron(size=10.0):
    return SimpleNamespace(
        bounds_mm={
            "min": [0.0, 0.0, 0.0],
            "max": [size, size, size],
            "size": [size, size, size],
        },
        vertices=np.array(
            ((0, 0, 0), (size, 0, 0), (0, size, 0), (0, 0, size)), dtype=np.float32
        ),
        triangles=np.array(
            ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)), dtype=np.int32
        ),
    )


class ExportSafetyTests(unittest.TestCase):
    def test_invalid_explicit_bed_dimensions_do_not_fall_back(self):
        for key in ("bed_x", "bed_y", "bed_z", "max_z", "printable_height"):
            for value in (0, -1, None, True, "bad", float("nan"), float("inf")):
                for host in ({key: value}, {"printer": {key: value}}):
                    with (
                        self.subTest(host=host),
                        tempfile.TemporaryDirectory() as folder,
                        self.assertRaises(ValueError),
                    ):
                        write_orca_3mf(
                            Path(folder) / "invalid.3mf",
                            [("Part", tetrahedron())],
                            {},
                            host,
                        )
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            write_orca_3mf(
                Path(folder) / "invalid.3mf",
                [("Part", tetrahedron())],
                {},
                {"max_z": 250, "bed_z": 0},
            )

    def test_xml_invalid_names_and_titles_are_rejected(self):
        for invalid in ("Part\x00bad", "Part\ud800bad", "Part\ufffebad"):
            for name, params in ((invalid, {}), ("Part", {"name": invalid})):
                with (
                    tempfile.TemporaryDirectory() as folder,
                    self.assertRaises(ValueError),
                ):
                    write_orca_3mf(
                        Path(folder) / "invalid.3mf", [(name, tetrahedron())], params
                    )

    def test_controller_calls_real_3mf_exporter_with_compatible_arguments(self):
        controller = bridge.BoxStudioController()
        output = []
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(
                controller, "_geometry", return_value=[("Part", tetrahedron())]
            ),
            patch.object(controller, "get_export_dir", return_value=Path(folder)),
        ):
            controller._export_action(
                normalize_params(),
                {"type": "export_file", "format": "3mf"},
                {},
                output.append,
            )
            self.assertTrue(output[-1]["ok"], output[-1])
            self.assertEqual(len(output[-1]["paths"]), 1)
            with zipfile.ZipFile(output[-1]["paths"][0]) as archive:
                self.assertIn("3D/3dmodel.model", archive.namelist())

    def test_invalid_geometry_is_rejected_without_silent_repair(self):
        for invalid in (float("nan"), float("inf")):
            mesh = tetrahedron()
            mesh.vertices[0, 0] = invalid
            with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
                write_binary_stl(Path(folder) / "invalid.stl", mesh)
        for invalid in (-1, 999):
            mesh = tetrahedron()
            mesh.triangles[0, 0] = invalid
            with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
                write_binary_stl(Path(folder) / "invalid.stl", mesh)

    def test_degenerate_after_float32_conversion_is_rejected(self):
        mesh = tetrahedron()
        mesh.vertices = mesh.vertices.astype(np.float64)
        mesh.vertices[1] = (1e-50, 0, 0)
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            write_binary_stl(Path(folder) / "collapsed.stl", mesh)

    def test_actual_small_bed_and_build_height_are_respected(self):
        cases = [
            (tetrahedron(24), {"bed_x": 20, "bed_y": 20}),
            (tetrahedron(10), {"bed_x": 20, "bed_y": 20, "bed_z": 5}),
            (tetrahedron(10), {"bed_x": 20, "bed_y": 20, "max_z": 5}),
            (tetrahedron(10), {"bed_x": 20, "bed_y": 20, "bed_z": float("nan")}),
        ]
        for mesh, host in cases:
            with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
                write_orca_3mf(Path(folder) / "outside.3mf", [("Part", mesh)], {}, host)

    def test_3mf_coordinates_round_trip_at_float32_precision(self):
        mesh = tetrahedron()
        mesh.vertices[1, 0] = np.float32(10.000003)
        with tempfile.TemporaryDirectory() as folder:
            path = write_orca_3mf(Path(folder) / "roundtrip.3mf", [("Part", mesh)], {})
            with zipfile.ZipFile(path) as archive:
                root = ET.fromstring(archive.read("3D/3dmodel.model"))
            ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
            vertices = root.findall(".//m:vertex", ns)
            actual = np.array(
                [[v.attrib[axis] for axis in ("x", "y", "z")] for v in vertices],
                dtype=np.float32,
            )
            np.testing.assert_array_equal(mesh.vertices, actual)


if __name__ == "__main__":
    unittest.main()
