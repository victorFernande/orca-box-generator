"""Lossless resource transport, including malformed and inexact reuse cases."""
import base64
import copy
import hashlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from box_studio import preset_mesh_cache as cache
from box_studio.mesh_generator import np
from box_studio.presets_catalog import BUILTIN_PRESETS

spec = importlib.util.spec_from_file_location("box_resource_encoder", ROOT / "scripts/build_preset_meshes.py")
encoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(encoder)


class ResourceEncodingTests(unittest.TestCase):
    def setUp(self):
        self.params = next(p["params"] for p in BUILTIN_PRESETS if p["id"] == "pencil")
        self.arrays = {
            "vertices": np.array([[0., -0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]], dtype="<f4"),
            "triangles": np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]], dtype="<i4"),
            "normals": np.array([[0., -0., -1.], [0., -1., 0.], [-1., 0., 0.], [.57735026]*3], dtype="<f4"),
        }

    def entry(self, blob, encoding):
        return {
            "file": "test-base.npz", "size_bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
            "encoding": encoding, "vertices": 4, "triangles": 4,
            "array_sha256": {k: hashlib.sha256(a.tobytes()).hexdigest() for k, a in self.arrays.items()},
            "bounds_mm": {"min": [0., 0., 0.], "max": [1., 1., 1.], "size": [1., 1., 1.]},
            "volume_cm3": 1/6000, "interface_error_mm": .04,
            "topology": {"closed": True, "oriented": True, "vertices": 4, "triangles": 4},
        }

    def load(self, blob, entry):
        key = hashlib.sha256(cache.preset_parameter_key(self.params).encode()).hexdigest()
        index = {key: {"id": "pencil", "parts": {"base": entry}}}
        with (patch.object(cache, "PRESET_MESH_INDEX", index),
              patch.object(cache, "_BUNDLED_PRESET_DATA", {entry["file"]: base64.b64encode(blob).decode()}),
              patch.object(cache, "_preset_sources_match", return_value=True)):
            return cache.load_standard_preset_mesh(self.params, "base")

    def test_legacy_and_shuffled_resources_preserve_signed_zero_and_every_index(self):
        legacy = {}
        for name, a in self.arrays.items():
            if name == "triangles":
                legacy[name] = np.diff(a.ravel(), prepend=np.int32(0))
            else:
                bits = a.view("<u4")
                legacy[name] = np.bitwise_xor(bits, np.vstack((np.zeros((1, 3), dtype="<u4"), bits[:-1])))
        stream = io.BytesIO()
        np.savez_compressed(stream, **legacy)
        for encoding, blob in (("xor-delta-v1", stream.getvalue()),
                               ("xor-delta-shuffle12-v1", encoder.encode_resource_arrays(self.arrays))):
            with self.subTest(encoding=encoding):
                mesh = self.load(blob, self.entry(blob, encoding))
                self.assertIsNotNone(mesh)
                for name, array in (("vertices", mesh.vertices), ("triangles", mesh.triangles), ("normals", mesh.face_normals)):
                    self.assertEqual(array.tobytes(), self.arrays[name].tobytes())
                    self.assertFalse(array.flags.writeable)

    def test_malformed_plane_shape_dtype_or_unknown_encoding_is_a_miss(self):
        blob = encoder.encode_resource_arrays(self.arrays)
        with np.load(io.BytesIO(blob), allow_pickle=False) as archive:
            original = {name: archive[name] for name in archive.files}
        cases = [("unknown-v99", original),
                 ("xor-delta-shuffle12-v1", {**original, "vertices": original["vertices"].transpose(0, 2, 1)}),
                 ("xor-delta-shuffle12-v1", {**original, "vertices": original["vertices"].astype("<u2")})]
        for encoding, arrays in cases:
            with self.subTest(encoding=encoding, shape=arrays["vertices"].shape, dtype=str(arrays["vertices"].dtype)):
                stream = io.BytesIO()
                np.savez_compressed(stream, **arrays)
                invalid = stream.getvalue()
                self.assertIsNone(self.load(invalid, self.entry(invalid, encoding)))

    def test_resource_reuse_requires_exact_translation_indices_and_normal_bits(self):
        source = {k: a.copy() for k, a in self.arrays.items()}
        source_entry = self.entry(encoder.encode_resource_arrays(source), "xor-delta-shuffle12-v1")
        moved = {k: a.copy() for k, a in source.items()}
        # Signed zero is deliberately preserved in the source fixture; choose an
        # offset that has exactly the same float32 operation as the runtime.
        moved["vertices"] = np.add(source["vertices"], np.array([94.5, 0., 0.], dtype="<f4"))
        entry = {**source_entry, "file": "test-right.npz",
                 "array_sha256": {k: hashlib.sha256(a.tobytes()).hexdigest() for k, a in moved.items()}}
        shared = encoder.translated_resource(entry, moved, source_entry, source)
        self.assertIsNotNone(shared)
        self.assertEqual(shared["file"], source_entry["file"])
        for field in ("vertices", "triangles", "normals"):
            altered = copy.deepcopy(moved)
            altered[field][1, 1] += 1 if field == "triangles" else .01
            self.assertIsNone(encoder.translated_resource(entry, altered, source_entry, source))

    def test_translated_latch_rejects_wrong_offsets_and_does_not_mutate_reuse_input(self):
        params = next(p["params"] for p in BUILTIN_PRESETS if p["id"] == "tool_rugged")
        left = cache.load_standard_preset_mesh(params, "clip_left")
        direct = cache.load_standard_preset_mesh(params, "clip_right")
        before = left.vertices.tobytes()
        shared = cache.load_standard_preset_mesh(params, "clip_right", reuse_from=left)
        self.assertEqual(shared.vertices.tobytes(), direct.vertices.tobytes())
        self.assertFalse(np.shares_memory(shared.vertices, left.vertices))
        self.assertEqual(left.vertices.tobytes(), before)
        key = next(k for k, design in cache.PRESET_MESH_INDEX.items() if design["id"] == "tool_rugged")
        for translation in ([0., 0., 0.], [94.5], [float("nan"), 0., 0.]):
            altered = copy.deepcopy(cache.PRESET_MESH_INDEX)
            altered[key]["parts"]["clip_right"]["vertex_translation"] = translation
            with self.subTest(translation=translation), patch.object(cache, "PRESET_MESH_INDEX", altered):
                self.assertIsNone(cache.load_standard_preset_mesh(params, "clip_right", reuse_from=left))
        # An unmatched source digest cannot authorize reuse. Decode the verified
        # source resource instead; the final approved vertex digest still holds.
        altered = copy.deepcopy(cache.PRESET_MESH_INDEX)
        altered[key]["parts"]["clip_right"]["vertex_source_sha256"] = "0" * 64
        with patch.object(cache, "PRESET_MESH_INDEX", altered):
            recovered = cache.load_standard_preset_mesh(params, "clip_right", reuse_from=left)
            self.assertEqual(recovered.vertices.tobytes(), direct.vertices.tobytes())
        self.assertEqual(left.vertices.tobytes(), before)


if __name__ == "__main__":
    unittest.main()
