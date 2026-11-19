"""Independent readers for actual browser-test exports (development only).

No model is generated here. The controller's immutable print-mesh snapshot and
the preview actually delivered to the browser are compared with serialized bytes.
"""
from __future__ import annotations

import base64
from collections import OrderedDict
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from box_studio.mesh_generator import np

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
STL_DTYPE = np.dtype([("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attr", "<u2")])
_INSPECTIONS = OrderedDict()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _roots(size, left, right):
    """Parallel union/find with root hooking, including non-manifold fan checks."""
    parent = np.arange(size, dtype=np.int64)
    while True:
        while True:
            compressed = parent[parent]
            if np.array_equal(compressed, parent):
                break
            parent = compressed
        a, b = parent[left], parent[right]
        unequal = a != b
        if not np.any(unequal):
            return parent
        np.minimum.at(parent, np.maximum(a[unequal], b[unequal]), np.minimum(a[unequal], b[unequal]))


def inspect_mesh(vertices, triangles):
    """Check serialized float32 geometry, directed edges, vertex fans and shells."""
    v = np.ascontiguousarray(vertices, dtype=np.float32)
    t = np.ascontiguousarray(triangles, dtype=np.int64)
    key = (v.shape, t.shape, hashlib.sha256(memoryview(v)).digest(), hashlib.sha256(memoryview(t)).digest())
    if key in _INSPECTIONS:
        _INSPECTIONS.move_to_end(key)
        return copy.deepcopy(_INSPECTIONS[key])
    report = _inspect_uncached(v, t)
    # Only small reports are retained: never vertices, triangles or file bytes.
    _INSPECTIONS[key] = copy.deepcopy(report)
    while len(_INSPECTIONS) > 96:
        _INSPECTIONS.popitem(last=False)
    return report


def _inspect_uncached(vertices, triangles):
    v = np.asarray(vertices, dtype=np.float32)
    t = np.asarray(triangles, dtype=np.int64)
    _require(v.ndim == 2 and v.shape[1] == 3 and len(v) > 3, "invalid vertices")
    _require(t.ndim == 2 and t.shape[1] == 3 and len(t) > 3, "invalid triangles")
    _require(np.isfinite(v).all(), "nonfinite serialized coordinate")
    _require(t.min() >= 0 and t.max() < len(v), "serialized index outside vertex array")
    _require(len(np.unique(v, axis=0)) == len(v), "duplicate serialized vertex positions")
    _require(len(np.unique(t)) == len(v), "unreferenced serialized vertices")
    xyz = v[t].astype(np.float64)
    normal = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    _require(np.all(np.linalg.norm(normal, axis=1) > 0), "collapsed serialized triangle")
    edges = np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]))
    keys = np.minimum(edges[:, 0], edges[:, 1]) * len(v) + np.maximum(edges[:, 0], edges[:, 1])
    order = np.argsort(keys)
    sorted_keys = keys[order]
    _require(len(order) % 2 == 0 and np.array_equal(sorted_keys[::2], sorted_keys[1::2]), "open/non-manifold edge")
    _require(not np.any(sorted_keys[1:-1:2] == sorted_keys[2::2]), "edge incident to more than two faces")
    first, second = order[::2], order[1::2]
    _require(np.array_equal(edges[first], edges[second, ::-1]), "inconsistent edge orientation")
    count = len(t)
    faces = np.tile(np.arange(count, dtype=np.int64), 3)
    slots = np.repeat(np.arange(3, dtype=np.int64), count)
    start, end = faces * 3 + slots, faces * 3 + (slots + 1) % 3
    corners = _roots(3 * count, np.concatenate((start[first], end[first])), np.concatenate((end[second], start[second])))
    vertex_order = np.argsort(t.reshape(-1))
    by_vertex, fans = t.reshape(-1)[vertex_order], corners[vertex_order]
    _require(not np.any((by_vertex[1:] == by_vertex[:-1]) & (fans[1:] != fans[:-1])), "non-manifold vertex link")
    components = _roots(count, faces[first], faces[second])
    unique, labels = np.unique(components, return_inverse=True)
    origin = v.mean(axis=0, dtype=np.float64)
    local = xyz - origin
    signed = np.einsum("ij,ij->i", local[:, 0], np.cross(local[:, 1], local[:, 2])) / 6
    volumes = np.bincount(labels, weights=signed)
    _require(np.all(volumes > 0), "nonpositive shell signed volume")
    return {"vertices": len(v), "triangles": count, "components": len(unique),
            "euler": int(len(v) - len(first) + count), "volume_mm3": float(volumes.sum()),
            "shell_volumes_mm3": volumes.tolist(), "closed": True, "oriented": True,
            "manifold_vertex_links": True, "bounds": {"min": v.min(axis=0).tolist(), "max": v.max(axis=0).tolist()}}


def _compare(vertices, triangles, expected):
    _require(np.array_equal(vertices, expected.vertices), f"float32 vertex identity changed: {expected.part}")
    _require(np.array_equal(triangles, expected.triangles), f"triangle/source identity changed: {expected.part}")
    report = inspect_mesh(vertices, triangles)
    report.update(part=expected.part)
    tolerance = max(0.002, report["volume_mm3"] * 2e-5)
    _require(abs(report["volume_mm3"] - expected.volume_cm3 * 1000) <= tolerance, f"reported/exported volume mismatch: {expected.part}")
    return report


def _read_stl(data, expected):
    _require(len(data) >= 84, "truncated binary STL")
    count = struct.unpack_from("<I", data, 80)[0]
    _require(len(data) == 84 + count * 50, "binary STL record length mismatch")
    records = np.frombuffer(data, dtype=STL_DTYPE, offset=84, count=count)
    _require(np.array_equal(records["vertices"], expected.vertices[expected.triangles]), "STL facets differ from controller print snapshot")
    _require(np.isfinite(records["normal"]).all(), "invalid STL normals")
    # Exact facet equality above plus unique source coordinates checked below
    # establishes the same geometric weld/adjacency without sorting 3F STL
    # points again for every target/format. The bounded hash cache stores only
    # inspection reports, and every file still undergoes exact byte-array checks.
    report = inspect_mesh(expected.vertices, expected.triangles)
    report.update(part=expected.part)
    _require(abs(report["volume_mm3"] - expected.volume_cm3 * 1000) <= max(0.002, report["volume_mm3"] * 2e-5), "STL reported/exported volume mismatch")
    normal = np.cross(records["vertices"][:, 1].astype(np.float64) - records["vertices"][:, 0], records["vertices"][:, 2].astype(np.float64) - records["vertices"][:, 0])
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    _require(np.allclose(records["normal"], normal, atol=2e-5, rtol=2e-5), "STL normals disagree with winding")
    _require(abs(report["bounds"]["min"][2]) <= 0.001, "STL print pose does not rest on bed")
    return report


def _expected_settings(params, host):
    settings = dict(host.get("project_settings") or {})
    settings.update(spiral_mode="0", spiral_mode_smooth="0")
    if params.get("auto_configure_slicer", True):
        settings.update(wall_loops="4", top_shell_layers="5", bottom_shell_layers="5",
                        sparse_infill_density="35%", sparse_infill_pattern="gyroid", elefant_foot_compensation="0.15")
    return settings


def _read_3mf(data, items, params, host):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        _require(archive.testzip() is None, "corrupt 3MF ZIP CRC")
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        _require(model.get("unit") == "millimeter", "unexpected 3MF units")
        objects = model.findall("m:resources/m:object", NS)
        _require(len(objects) == len(items), "wrong 3MF object count")
        parts, arrays = [], {}
        for obj, (name, mesh) in zip(objects, items):
            _require(obj.get("name") == name, "3MF part name/order mismatch")
            v = np.array([[x.get(k) for k in ("x", "y", "z")] for x in obj.findall("m:mesh/m:vertices/m:vertex", NS)], dtype=np.float32)
            t = np.array([[x.get(k) for k in ("v1", "v2", "v3")] for x in obj.findall("m:mesh/m:triangles/m:triangle", NS)], dtype=np.int64)
            parts.append(_compare(v, t, mesh))
            _require(obj.get("id") not in arrays, "duplicate 3MF object id")
            arrays[obj.get("id")] = v
        placed = []
        build = model.findall("m:build/m:item", NS)
        _require(len(build) == len(items) and {x.get("objectid") for x in build} == set(arrays), "3MF build/object identity mismatch")
        bed = np.array([host.get("bed_x", 220), host.get("bed_y", 220), host.get("max_z", host.get("bed_z", 250))], dtype=float)
        for item in build:
            matrix = np.array(item.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0").split(), dtype=float).reshape(4, 3)
            _require(np.isfinite(matrix).all() and np.array_equal(matrix[:3], np.eye(3)), "3MF changes scale/rotation of print snapshot")
            v = arrays[item.get("objectid")].astype(float) @ matrix[:3] + matrix[3]
            low, high = v.min(axis=0), v.max(axis=0)
            _require(np.all(low >= -0.001) and np.all(high <= bed + 0.001), "3MF outside bed/height")
            _require(abs(low[2]) <= 0.001, "3MF print object does not rest on bed")
            for old_low, old_high in placed:
                _require(np.any(np.minimum(high[:2], old_high[:2]) - np.maximum(low[:2], old_low[:2]) <= 0), "3MF print objects overlap")
            placed.append((low, high))
        settings = json.loads(archive.read("Metadata/project_settings.config"))
        for key, value in _expected_settings(params, host).items():
            _require(settings.get(key) == value, f"3MF project setting mismatch: {key}")
        configuration = ET.fromstring(archive.read("Metadata/model_settings.config"))
        _require({x.get("id") for x in configuration.findall("object")} == set(arrays), "Orca object metadata ids mismatch")
        return parts, {"object_count": len(objects), "bed_mm": bed.tolist(), "settings": settings, "placements": [{"min": a.tolist(), "max": b.tolist()} for a, b in placed]}


def preview_identity(preview, items, params, target):
    """Apply print transforms independently to the preview sent to the browser."""
    _require(preview and preview.get("ok") and preview.get("meshes"), "no successful preview delivered to this browser mode")
    previous = preview["params"]
    ignored = {"name", "theme", "lang", "auto_configure_slicer"}
    _require({k: v for k, v in previous.items() if k not in ignored} == {k: v for k, v in params.items() if k not in ignored}, "export parameters differ from delivered preview snapshot")
    _require(previous["export_target"] == target, "export target differs from delivered preview")
    decoded = []
    for mesh in preview["meshes"]:
        v = np.frombuffer(base64.b64decode(mesh["vertices"]), dtype="<f4").reshape(-1, 3).copy()
        t = np.frombuffer(base64.b64decode(mesh["triangles"]), dtype="<u4").reshape(-1, 3).copy()
        part = mesh["part"]
        if target != "fit_test_kit":
            if part == "lid" and params["style"] == "clamshell_pip":
                # 180-degree X rotation about the actual hinge, using float64.
                v = v.astype(float)
                v[:, 1] = params["depth_y"] + 2 * params["hinge_separation"] - v[:, 1]
                v[:, 2] = 2 * params["height_z"] + params["fit_clearance"] - v[:, 2]
                v = v.astype(np.float32)
            elif params["style"] == "rugged_box" and part in ("base", "lid", "clip_left", "clip_right"):
                # Independent rigid print poses of the reconstructed four-piece
                # enclosure. Neither the old hinge mode nor the opening slider
                # changes the actual printed part membership or orientation.
                v = v.astype(np.float64)
                if part == "lid":
                    v[:, 0] *= -1
                    v[:, 2] = params["height_z"] + params["rugged_lid_height"] - v[:, 2]
                elif part in ("clip_left", "clip_right"):
                    pivot_y = -params["depth_y"] / 2 - 3.0
                    v = np.column_stack((-v[:, 0], v[:, 2], v[:, 1] - pivot_y + 3.0))
                v = v.astype(np.float32)
            elif part == "lid" and params["style"] != "sliding_lid":
                v[:, 2] *= -1
                t = t[:, [0, 2, 1]]
            if part == "pin":
                v = v[:, [1, 2, 0]]
            if not (params["style"] == "rugged_box" and part in ("base", "lid", "clip_left", "clip_right")):
                v[:, 2] -= v[:, 2].min()
        decoded.append((part, v, t))
    if params["style"] == "clamshell_pip":
        pair = [m for m in decoded if m[0] in ("base", "lid")]
        _require(len(pair) == 2, "captive preview must contain both halves")
        assembly = items[0][1].part
        decoded = [(assembly, np.concatenate([m[1] for m in pair]), np.concatenate([pair[0][2], pair[1][2] + len(pair[0][1])]))] + [m for m in decoded if m[0] not in ("base", "lid")]
    _require(len(decoded) == len(items), "preview/export part count differs")
    for (part, v, t), (_, expected) in zip(decoded, items):
        _require(part == expected.part and np.array_equal(t, expected.triangles), "preview/export connectivity or part identity differs")
        _require(v.shape == expected.vertices.shape and np.allclose(v, expected.vertices, atol=3e-5, rtol=0), f"preview/print pose identity differs: {part}")
    return {"ok": True, "observed": True, "geometry_key": preview.get("geometry_key"), "parts": [m[0] for m in decoded], "method": "delivered float32 preview + independent print transforms versus exact export snapshot"}


def sliding_bed_contact(vertices, triangles):
    """Measure first-plane support, independently of the source CAD field."""
    v = np.asarray(vertices, dtype=np.float64)
    t = np.asarray(triangles, dtype=np.int64)
    low, high = v.min(axis=0), v.max(axis=0)
    tolerance_mm = 0.005  # 5 micrometres; not a layer-height or printer guarantee.
    xyz = v[t]
    flat = np.all(np.abs(xyz[:, :, 2] - low[2]) <= tolerance_mm, axis=1)
    area = float(np.linalg.norm(np.cross(xyz[flat, 1] - xyz[flat, 0], xyz[flat, 2] - xyz[flat, 0]), axis=1).sum() / 2)
    footprint = float((high[0] - low[0]) * (high[1] - low[1]))
    _require(footprint > 0, "Sliding lid has no XY footprint")
    return {"bed_contact_mm2": area, "bed_contact_bbox_fraction": area / footprint,
            "bed_contact_bbox_mm2": footprint, "bed_contact_plane_z_mm": float(low[2]),
            "bed_contact_tolerance_mm": tolerance_mm}


def verify_exports(paths, items, params, host, preview, target):
    """Return a JSON report; errors remain separate from the product action result."""
    result = {"ok": False, "checks": [], "errors": [], "parts": [], "preview_identity": {"ok": False, "observed": bool(preview)},
              "print_snapshot": [{"name": name, "part": mesh.part,
                                  "vertices": len(mesh.vertices), "triangles": len(mesh.triangles),
                                  "vertices_sha256": hashlib.sha256(mesh.vertices.astype("<f4", copy=False).tobytes()).hexdigest(),
                                  "triangles_sha256": hashlib.sha256(mesh.triangles.astype("<u4", copy=False).tobytes()).hexdigest()}
                                 for name, mesh in items]}
    try:
        result["preview_identity"] = preview_identity(preview, items, params, target)
        result["checks"].append("delivered_preview_matches_print_snapshot")
    except Exception as exc:
        result["errors"].append(str(exc))
    try:
        _require(bool(paths), "no actual export bytes produced")
        if paths[0].suffix.lower() == ".3mf":
            _require(len(paths) == 1, "unexpected 3MF file count")
            result["parts"], details = _read_3mf(paths[0].read_bytes(), items, params, host)
            result.update(details)
            result["checks"].extend(["3mf_exact_float32_source_identity", "build_part_ids_and_names", "bed_height_and_nonoverlap", "orca_process_settings"])
        else:
            _require(len(paths) == len(items), "wrong STL part/file count")
            result["parts"] = [_read_stl(path.read_bytes(), mesh) for path, (_, mesh) in zip(paths, items)]
            result["object_count"] = len(items)
            result["checks"].append("binary_stl_exact_facet_source_identity")
        result["checks"].extend(["finite_nondegenerate_float32", "oriented_closed_edges", "manifold_vertex_links", "positive_shell_volumes"])
        for part in result["parts"]:
            expected_shells = 2 if part["part"] == "clamshell_pip_assembly" else 1
            _require(part["components"] == expected_shells, f"unexpected disconnected shells: {part['part']}")
        result["checks"].append("expected_connected_shell_count")
        if params["style"] == "rugged_box":
            required = {
                "base_only": ["base"], "lid_only": ["lid"],
                "base_and_lid": ["base", "lid", "clip_left", "clip_right"],
                "full_suite": ["base", "lid", "clip_left", "clip_right"],
            }
            _require(target in required and not params["gasket_enabled"],
                     "Rugged requires its actual shell/latch parts; gasket and generic fit kit are unsupported")
            _require([part["part"] for part in result["parts"]] == required.get(target),
                     "Rugged export must contain its separate shell parts and two latches, without a pin or captive assembly")
            result["checks"].append("rugged_separate_parts_without_pin_or_captive_assembly")
        if params["style"] == "sliding_lid" and target != "fit_test_kit":
            for report, (_, mesh) in zip(result["parts"], items):
                if mesh.part == "lid":
                    # The readers above already established exact equality of
                    # these print vertices/facets with the serialized bytes.
                    report.update(sliding_bed_contact(mesh.vertices, mesh.triangles))
                    _require(report["bed_contact_bbox_fraction"] >= 0.25,
                             "Sliding lid rests on too little of its footprint (minimum 25% at the bed plane)")
                    result["checks"].append("sliding_lid_broad_bed_contact")
        if params["style"] == "clamshell_pip":
            _require(len(result["parts"]) == 1 and result["parts"][0]["components"] == 2, "captive case must remain one object with two shells")
            result["checks"].append("captive_open_assembly_one_object_two_shells")
    except Exception as exc:
        result["errors"].append(str(exc))
    result["ok"] = not result["errors"]
    return result
