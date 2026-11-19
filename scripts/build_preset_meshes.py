"""Rebuild the exact standard-box resources after changing geometry or presets.

Development only: this does not install or launch OrcaSlicer. Resources preserve
all original float32 bits and triangle indices, and remain MIT project output.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import pprint
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    from box_studio.mesh_generator import generate_box_mesh, topology_report, np
    from box_studio.presets_catalog import BUILTIN_PRESETS
    from box_studio import rugged_latch_geometry as latch
    from box_studio import rugged_front_mesh as front
    from unittest.mock import patch
    from box_studio.preset_mesh_cache import preset_parameter_key, preset_source_fingerprint

    package = ROOT / "src" / "box_studio"
    output = package / "preset_meshes"
    output.mkdir(exist_ok=True)
    source_hash = preset_source_fingerprint({name: (package / name).read_bytes() for name in
                                          ("schema.py", "mesh_generator.py", "presets_catalog.py", "rugged_geometry.py", "rugged_latch_geometry.py", "rugged_front_geometry.py", "rugged_front_mesh.py")})
    index = {}
    # Always reconstruct our current surfaces rather than reading this same bank.
    latch._clear_latch_cache()
    front._clear_front_patch_cache()
    with patch.object(latch, "_load_canonical_latch", return_value=None):
        for preset in BUILTIN_PRESETS:
            p = preset["params"]
            if p["style"] not in ("screw_corner", "rugged_box", "sliding_lid"):
                continue
            parts = ("base", "lid", "clip_left", "clip_right") if p["style"] == "rugged_box" else ("base", "lid")
            design = {"id": preset["id"], "parts": {}}
            for part in parts:
                mesh = generate_box_mesh(p, part)
                topology = topology_report(mesh)
                if not topology["closed"] or not topology["oriented"] or mesh.volume_cm3 <= 0:
                    raise ValueError(f"Invalid source surface: {preset['id']}/{part}")
                arrays = {"vertices": mesh.vertices.astype("<f4", copy=False),
                          "triangles": mesh.triangles.astype("<i4", copy=False),
                          "normals": mesh.face_normals.astype("<f4", copy=False)}
                packed = {}
                for name, array in arrays.items():
                    if name == "triangles":
                        packed[name] = np.diff(array.ravel(), prepend=np.int32(0))
                    else:
                        bits = array.view("<u4")
                        previous = np.concatenate((np.zeros((1, 3), dtype="<u4"), bits[:-1]))
                        packed[name] = np.bitwise_xor(bits, previous)
                stream = io.BytesIO()
                np.savez_compressed(stream, **packed)
                blob = stream.getvalue()
                filename = f"{preset['id']}-{part}.npz"
                (output / filename).write_bytes(blob)
                design["parts"][part] = {
                    "file": filename, "size_bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                    "array_sha256": {name: hashlib.sha256(array.tobytes()).hexdigest() for name, array in arrays.items()},
                    "vertices": len(mesh.vertices), "triangles": len(mesh.triangles),
                    "bounds_mm": mesh.bounds_mm, "volume_cm3": mesh.volume_cm3,
                    "interface_error_mm": mesh.interface_error_mm, "topology": topology,
                }
                print(f"{filename}: {len(mesh.triangles)} unchanged facets, {len(blob)} bytes", flush=True)
            index[hashlib.sha256(preset_parameter_key(p).encode("utf-8")).hexdigest()] = design
    content = ('"""Generated lossless standard-box index; rebuild with scripts/build_preset_meshes.py."""\n\n'
               + "PRESET_MESH_SOURCE_HASH = " + repr(source_hash) + "\n\n"
               + "PRESET_MESH_INDEX = " + pprint.pformat(index, width=110, sort_dicts=False) + "\n")
    (package / "preset_mesh_index.py").write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
