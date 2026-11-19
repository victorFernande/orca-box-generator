"""Lossless, source-bound canonical surfaces for the three slow standard boxes.

Only exact manufacturing parameters may use these reviewed package resources.
Every other design, or an unavailable/stale/damaged resource, uses the generator.
The controller's existing byte-bounded LRU owns decoded meshes; this module does
not retain a second decoded cache or load the entire library at startup.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from .schema import normalize_params
from .mesh_generator import MeshData, np
from .preset_mesh_index import PRESET_MESH_SOURCE_HASH, PRESET_MESH_INDEX

# Replaced by the bundler only after checking the source/resource fingerprints.
_BUNDLED_PRESET_DATA = {}
_BUNDLED_PRESET_RAW_HASH = ""
_BUNDLED_PRESET_CODE_HASH = ""
_PRESET_DEPENDENCIES = ("schema.py", "mesh_generator.py", "presets_catalog.py")
_PRESET_SOURCE_CHECK = None


def preset_parameter_key(raw):
    p = normalize_params(raw)
    return json.dumps({k: v for k, v in p.items() if k not in (
        "name", "lang", "theme", "export_target", "auto_configure_slicer"
    )}, sort_keys=True)


def preset_source_fingerprint(parts):
    digest = hashlib.sha256()
    for name in _PRESET_DEPENDENCIES:
        digest.update(name.encode("ascii") + b"\0")
        digest.update(parts[name].replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def _preset_sources_match():
    global _PRESET_SOURCE_CHECK
    location = Path(__file__).resolve()
    try:
        paths = [location] if _BUNDLED_PRESET_DATA else [location.with_name(n) for n in _PRESET_DEPENDENCIES]
        token = tuple((str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in paths)
        if _PRESET_SOURCE_CHECK is not None and _PRESET_SOURCE_CHECK[0] == token:
            return _PRESET_SOURCE_CHECK[1]
        if _BUNDLED_PRESET_DATA:
            source = location.read_bytes().replace(b"\r\n", b"\n")
            parts = {}
            for name in _PRESET_DEPENDENCIES:
                start = ("# BOX_GEOMETRY_SOURCE_BEGIN " + name + "\n").encode("ascii")
                end = ("# BOX_GEOMETRY_SOURCE_END " + name + "\n").encode("ascii")
                if source.count(start) != 1 or source.count(end) != 1:
                    return False
                parts[name] = source.split(start, 1)[1].split(end, 1)[0]
            valid = (PRESET_MESH_SOURCE_HASH == _BUNDLED_PRESET_RAW_HASH and
                     preset_source_fingerprint(parts) == _BUNDLED_PRESET_CODE_HASH)
        else:
            valid = preset_source_fingerprint({p.name: p.read_bytes() for p in paths}) == PRESET_MESH_SOURCE_HASH
        _PRESET_SOURCE_CHECK = (token, valid)
        return valid
    except (OSError, ValueError):
        return False


def load_standard_preset_mesh(raw, part):
    """Return an exact, already validated package surface, or None on a miss.

    A digest is checked both before decompression and after reconstructing each
    original array. XOR on float bits and integer deltas are reversible, without
    quantization, smoothing, triangle removal or a change of coordinate order.
    No trust decision is accepted from a UI message or a user-preset file.
    """
    key = hashlib.sha256(preset_parameter_key(raw).encode("utf-8")).hexdigest()
    design = PRESET_MESH_INDEX.get(key)
    entry = design.get("parts", {}).get(part) if design else None
    if not entry or not _preset_sources_match():
        return None
    try:
        filename = entry["file"]
        if not re.fullmatch(r"[a-z0-9_]+-[a-z0-9_]+\.npz", filename):
            return None
        if _BUNDLED_PRESET_DATA:
            blob = base64.b64decode(_BUNDLED_PRESET_DATA[filename], validate=True)
        else:
            blob = (Path(__file__).resolve().parent / "preset_meshes" / filename).read_bytes()
        if len(blob) != entry["size_bytes"] or hashlib.sha256(blob).hexdigest() != entry["sha256"]:
            return None
        vertices_count, faces_count = entry["vertices"], entry["triangles"]
        if not (0 < vertices_count <= 5_000_000 and 0 < faces_count <= 10_000_000):
            return None
        expected = {"vertices": (vertices_count, "<u4"),
                    "triangles": (faces_count, "<i4"), "normals": (faces_count, "<u4")}
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            if set(archive.namelist()) != {name + ".npy" for name in expected}:
                return None
            if any(archive.getinfo(name + ".npy").file_size > count * 12 + 1024
                   for name, (count, _) in expected.items()):
                return None
        arrays = {}
        with np.load(io.BytesIO(blob), allow_pickle=False) as archive:
            for name, (count, dtype) in expected.items():
                encoded = archive[name]
                shape = (count * 3,) if name == "triangles" else (count, 3)
                if encoded.shape != shape or encoded.dtype != np.dtype(dtype):
                    return None
                if name == "triangles":
                    array = np.cumsum(encoded, dtype=np.int64).astype("<i4").reshape(-1, 3)
                else:
                    array = np.bitwise_xor.accumulate(encoded, axis=0).view("<f4")
                if hashlib.sha256(array.tobytes()).hexdigest() != entry["array_sha256"][name]:
                    return None
                arrays[name] = array
        vertices, triangles, normals = (arrays[name] for name in ("vertices", "triangles", "normals"))
        report = entry["topology"]
        if (not np.isfinite(vertices).all() or not np.isfinite(normals).all() or
                triangles.min() < 0 or triangles.max() >= vertices_count or
                not report["closed"] or not report["oriented"] or
                report["vertices"] != vertices_count or report["triangles"] != faces_count or
                not np.isfinite(entry["volume_cm3"]) or entry["volume_cm3"] <= 0):
            return None
        for array in arrays.values():
            array.flags.writeable = False
        bounds = {key: list(value) for key, value in entry["bounds_mm"].items()}
        return MeshData(vertices, triangles, normals, bounds, entry["volume_cm3"],
                        part, entry["interface_error_mm"])
    except (OSError, ValueError, KeyError, TypeError, OverflowError, EOFError, zipfile.BadZipFile):
        return None
