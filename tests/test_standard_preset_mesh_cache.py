"""Prepared presets retain the approved surfaces and cannot leak into edits."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from box_studio import preset_mesh_cache as cache
from box_studio import plugin_main as bridge
from box_studio import rugged_latch_geometry as latch
from box_studio import rugged_front_mesh as front
from box_studio.mesh_generator import generate_box_mesh, topology_report, np
from box_studio.presets_catalog import BUILTIN_PRESETS


class StandardPresetCacheTests(unittest.TestCase):
    def setUp(self):
        cache._PRESET_SOURCE_CHECK = None
        self.items = {item["id"]: item["params"] for item in BUILTIN_PRESETS}

    def test_legacy_surface_hashes_and_rebuilt_rugged_resource_identity(self):
        reference = json.loads((ROOT / "tests/fixtures/standard_mesh_reference.json").read_text(encoding="utf-8"))
        self.assertEqual(reference["reference_commit"], "75f3be346516ff7c4be557e9ee05d999dc476a3b")
        observed = set()
        latch._clear_latch_cache()
        front._clear_front_patch_cache()
        for design in cache.PRESET_MESH_INDEX.values():
            for part, entry in design["parts"].items():
                with self.subTest(preset=design["id"], part=part):
                    mesh = cache.load_standard_preset_mesh(self.items[design["id"]], part)
                    self.assertIsNotNone(mesh)
                    name = design["id"] + "-" + part
                    if design["id"] == "tool_rugged":
                        with patch.object(latch, "_load_canonical_latch", return_value=None):
                            regenerated = generate_box_mesh(self.items[design["id"]], part)
                        for actual, source in ((mesh.vertices, regenerated.vertices), (mesh.triangles, regenerated.triangles), (mesh.face_normals, regenerated.face_normals)):
                            np.testing.assert_array_equal(actual, source)
                            self.assertFalse(actual.flags.writeable)
                        self.assertEqual(topology_report(mesh), entry["topology"])
                        continue
                    original = reference["parts"][name]
                    self.assertEqual(len(mesh.vertices), original["vertices"])
                    self.assertEqual(len(mesh.triangles), original["triangles"])
                    for field, array in (("vertices", mesh.vertices), ("triangles", mesh.triangles), ("normals", mesh.face_normals)):
                        self.assertEqual(hashlib.sha256(array.tobytes()).hexdigest(), original["array_sha256"][field])
                        self.assertFalse(array.flags.writeable)
                    self.assertEqual(topology_report(mesh), entry["topology"])
                    observed.add(name)
        self.assertEqual(observed, set(reference["parts"]))

    def test_geometry_edits_miss_while_presentation_changes_reuse_exact_arrays(self):
        original = self.items["screw_corner_standard"]
        for change in ({"width_x": 91}, {"height_z": 36}, {"fit_clearance": .3}, {"quality": "fine"},
                       {"hinge_mode": "print_in_place"}, {"hinge_pin_diameter": 3.2},
                       {"cutouts": [{"kind": "usb_c", "face": "front", "z": 15}]},
                       {"standoffs": [{"x": 0, "y": 0}]}, {"dividers_x": [0]}, {"gasket_enabled": True}):
            with self.subTest(change=change):
                self.assertIsNone(cache.load_standard_preset_mesh({**original, **change}, "base"))
        changed = {**original, "name": "Personal", "lang": "en", "theme": "light",
                   "export_target": "base_only", "auto_configure_slicer": False}
        mesh = cache.load_standard_preset_mesh(changed, "base")
        self.assertIsNotNone(mesh)
        self.assertEqual(cache.preset_parameter_key(changed), bridge.BoxStudioController._geometry_key(changed))
        self.assertIsNone(cache.load_standard_preset_mesh(self.items["everyday"], "base"))
        self.assertIsNone(cache.load_standard_preset_mesh(self.items["screw_corner_standard"], "pin"))

    def test_latch_array_sharing_requires_immutable_exact_hashes_and_keeps_coordinates_separate(self):
        p = self.items["tool_rugged"]
        left = cache.load_standard_preset_mesh(p, "clip_left")
        direct = cache.load_standard_preset_mesh(p, "clip_right")
        shared = cache.load_standard_preset_mesh(p, "clip_right", reuse_from=left)
        self.assertIs(shared.triangles, left.triangles)
        self.assertIs(shared.face_normals, left.face_normals)
        self.assertFalse(np.shares_memory(shared.vertices, left.vertices))
        for actual, expected in ((shared.vertices, direct.vertices), (shared.triangles, direct.triangles),
                                 (shared.face_normals, direct.face_normals)):
            np.testing.assert_array_equal(actual, expected)
            self.assertFalse(actual.flags.writeable)
        corrupted = left.face_normals.copy()
        corrupted[0, 0] += .1
        corrupted.flags.writeable = False
        for untrusted in (left.face_normals.copy(), corrupted):
            repaired = cache.load_standard_preset_mesh(p, "clip_right", reuse_from=replace(left, face_normals=untrusted))
            self.assertIsNot(repaired.face_normals, untrusted)
            np.testing.assert_array_equal(repaired.face_normals, direct.face_normals)
        modified = copy.deepcopy(cache.PRESET_MESH_INDEX)
        key = next(key for key, design in modified.items() if design["id"] == "tool_rugged")
        modified[key]["parts"]["clip_right"]["sha256"] = "0" * 64
        with patch.object(cache, "PRESET_MESH_INDEX", modified):
            self.assertIsNone(cache.load_standard_preset_mesh(p, "clip_right", reuse_from=left))
        controller = bridge.BoxStudioController()
        parts = {mesh.part: mesh for _, mesh in controller._geometry(p, target="base_and_lid")}
        self.assertIs(parts["clip_left"].triangles, parts["clip_right"].triangles)
        self.assertIs(parts["clip_left"].face_normals, parts["clip_right"].face_normals)
        self.assertLessEqual(controller._mesh_cache_bytes, controller._mesh_cache_limit)

    def test_corrupt_blob_and_reconstructed_array_are_cache_misses(self):
        key = next(k for k, v in cache.PRESET_MESH_INDEX.items() if v["id"] == "pencil")
        for kind in ("blob", "array"):
            modified = copy.deepcopy(cache.PRESET_MESH_INDEX)
            if kind == "blob":
                modified[key]["parts"]["base"]["sha256"] = "0" * 64
            else:
                modified[key]["parts"]["base"]["array_sha256"]["vertices"] = "0" * 64
            with self.subTest(kind=kind), patch.object(cache, "PRESET_MESH_INDEX", modified):
                self.assertIsNone(cache.load_standard_preset_mesh(self.items["pencil"], "base"))

    def test_missing_or_stale_assets_fall_back_without_trusting_ui_flags(self):
        read = Path.read_bytes
        def missing(path):
            if path.suffix == ".npz":
                raise FileNotFoundError(path.name)
            return read(path)
        with patch.object(Path, "read_bytes", missing):
            self.assertIsNone(cache.load_standard_preset_mesh(self.items["pencil"], "base"))
        cache._PRESET_SOURCE_CHECK = None
        with patch.object(cache, "PRESET_MESH_SOURCE_HASH", "0" * 64):
            self.assertIsNone(cache.load_standard_preset_mesh(self.items["pencil"], "base"))
        cache._PRESET_SOURCE_CHECK = None
        # No message field can turn an edited design into the prepared default.
        edited = {**self.items["pencil"], "width_x": 91, "preset_cache_validated": True}
        self.assertIsNone(cache.load_standard_preset_mesh(edited, "base"))

    def test_controller_reuses_the_exact_mesh_for_print_orientation(self):
        p = self.items["pencil"]
        controller = bridge.BoxStudioController()
        with patch.object(bridge, "generate_box_mesh", side_effect=AssertionError("Unexpected regeneration")):
            assembled = controller._geometry(p, assembled=True, target="base_and_lid")
            before = [mesh.vertices.tobytes() for _, mesh in assembled]
            printed = controller._geometry(p, assembled=False, target="base_and_lid")
            repeated = controller._geometry(p, assembled=True, target="base_and_lid")
        self.assertTrue(all(mesh.bounds_mm["min"][2] == 0 for _, mesh in printed))
        self.assertEqual(before, [mesh.vertices.tobytes() for _, mesh in repeated])
        self.assertLessEqual(controller._mesh_cache_bytes, controller._mesh_cache_limit)

    def test_bundle_source_fingerprint_rejects_a_changed_dependency(self):
        package = ROOT / "src/box_studio"
        parts = {name: (package / name).read_bytes() for name in cache._PRESET_DEPENDENCIES}
        source = b"".join(("# BOX_GEOMETRY_SOURCE_BEGIN " + name + "\n").encode() + content +
                          ("# BOX_GEOMETRY_SOURCE_END " + name + "\n").encode() for name, content in parts.items())
        resources = {entry["file"]: base64.b64encode((package / "preset_meshes" / entry["file"]).read_bytes()).decode("ascii")
                     for design in cache.PRESET_MESH_INDEX.values() for entry in design["parts"].values()}
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / "standalone.py"
            filename.write_bytes(source)
            with (patch.object(cache, "__file__", str(filename)),
                  patch.object(cache, "_BUNDLED_PRESET_DATA", resources),
                  patch.object(cache, "_BUNDLED_PRESET_RAW_HASH", cache.PRESET_MESH_SOURCE_HASH),
                  patch.object(cache, "_BUNDLED_PRESET_CODE_HASH", cache.preset_source_fingerprint(parts))):
                self.assertIsNotNone(cache.load_standard_preset_mesh(self.items["pencil"], "lid"))
                filename.write_bytes(source.replace(b"# BOX_GEOMETRY_SOURCE_END mesh_generator.py", b"# edited\n# BOX_GEOMETRY_SOURCE_END mesh_generator.py"))
                self.assertIsNone(cache.load_standard_preset_mesh(self.items["pencil"], "lid"))
        cache._PRESET_SOURCE_CHECK = None


if __name__ == "__main__":
    unittest.main()
