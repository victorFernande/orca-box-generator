"""Binary STL and OrcaSlicer 2.5.1+ multi-object 3MF project exporters for Orca Box Studio."""

from __future__ import annotations

import datetime as _dt
import json
import math
import re
import struct
import uuid
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as _xml_escape

from .mesh_generator import np

_STL_RECORD_DTYPE = np.dtype(
    [
        ("normal", "<f4", (3,)),
        ("v0", "<f4", (3,)),
        ("v1", "<f4", (3,)),
        ("v2", "<f4", (3,)),
        ("attr", "<u2"),
    ]
)

_CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="config" ContentType="text/xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="json" ContentType="application/json"/>
</Types>
"""

_RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""


def _extract_mesh_arrays(mesh: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Validate the actual float32 export surface; never repair bad coordinates silently."""
    source = np.asarray(mesh.vertices, dtype=np.float64)
    if source.ndim != 2 or source.shape[1] != 3 or not len(source):
        raise ValueError("Expected a nonempty vertex array with shape (V, 3).")
    if not np.isfinite(source).all() or np.any(
        np.abs(source) > np.finfo(np.float32).max
    ):
        raise ValueError("Mesh contains nonfinite or unrepresentable coordinates.")
    vertices = source.astype(np.float32)
    indices = np.asarray(mesh.triangles)
    if indices.ndim != 2 or indices.shape[1] != 3 or not len(indices):
        raise ValueError("Expected a nonempty triangle array with shape (F, 3).")
    if indices.dtype.kind not in "iu":
        raise ValueError("Triangle indices must be integers.")
    if np.any(indices < 0) or np.any(indices >= len(vertices)):
        raise ValueError("Triangle index is outside the vertex array.")
    triangles = indices.astype(np.int32)
    points = vertices[triangles].astype(np.float64)
    cross = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
    lengths = np.linalg.norm(cross, axis=1)
    if np.any(lengths <= 0) or not np.isfinite(lengths).all():
        raise ValueError(
            "Mesh contains degenerate triangles after export precision conversion."
        )
    normals = (cross / lengths[:, None]).astype(np.float32)
    return vertices, triangles, normals


def _mesh_xy_extents(
    mesh: Any, vertices: np.ndarray | None = None
) -> tuple[float, float]:
    """Return (width_x_mm, depth_y_mm) of a mesh from vertices or bounds_mm."""
    verts = (
        vertices
        if vertices is not None
        else np.asarray(getattr(mesh, "vertices", []), dtype=np.float32)
    )
    if verts.ndim == 2 and verts.shape[0] > 0 and verts.shape[1] >= 2:
        dx = float(np.max(verts[:, 0]) - np.min(verts[:, 0]))
        dy = float(np.max(verts[:, 1]) - np.min(verts[:, 1]))
        return max(dx, 1.0), max(dy, 1.0)
    bounds = getattr(mesh, "bounds_mm", None)
    if isinstance(bounds, dict):
        size = bounds.get("size")
        if isinstance(size, (list, tuple)) and len(size) >= 2:
            return max(float(size[0]), 1.0), max(float(size[1]), 1.0)
        bmin = bounds.get("min")
        bmax = bounds.get("max")
        if (
            isinstance(bmin, (list, tuple))
            and isinstance(bmax, (list, tuple))
            and len(bmin) >= 2
            and len(bmax) >= 2
        ):
            return max(float(bmax[0]) - float(bmin[0]), 1.0), max(
                float(bmax[1]) - float(bmin[1]), 1.0
            )
    return 10.0, 10.0


def _mesh_xy_center_offset(
    mesh: Any, vertices: np.ndarray | None = None
) -> tuple[float, float]:
    """Return the local XY bounding-box midpoint `(mid_x, mid_y)` of `mesh`."""
    verts = (
        vertices
        if vertices is not None
        else np.asarray(mesh.vertices, dtype=np.float32)
    )
    if verts.shape[0] == 0:
        return 0.0, 0.0
    mx = 0.5 * float(np.max(verts[:, 0]) + np.min(verts[:, 0]))
    my = 0.5 * float(np.max(verts[:, 1]) + np.min(verts[:, 1]))
    return mx, my


def _resolve_bed_dimensions(host_config: dict[str, Any] | None) -> tuple[float, float]:
    """Use defaults only for absent settings; supplied invalid dimensions are errors."""
    return (
        _resolve_positive_limit(host_config, ("bed_x",), 220.0),
        _resolve_positive_limit(host_config, ("bed_y",), 220.0),
    )


def _resolve_positive_limit(host_config, keys, default):
    selected, found = None, False
    sources = [host_config] if isinstance(host_config, dict) else []
    if sources and isinstance(host_config.get("printer"), dict):
        sources.append(host_config["printer"])
    for source in sources:
        for key in keys:
            if key not in source:
                continue
            raw = source[key]
            try:
                value = float(raw)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid printer dimension: {key}.") from error
            if isinstance(raw, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid printer dimension: {key}.")
            if not found:
                selected, found = value, True
    return selected if found else default


def _validated_xml_text(value, label):
    text = str(value)
    for character in text:
        code = ord(character)
        if not (
            code in (9, 10, 13)
            or 0x20 <= code <= 0xD7FF
            or 0xE000 <= code <= 0xFFFD
            or 0x10000 <= code <= 0x10FFFF
        ):
            raise ValueError(f"{label} contains a character not permitted in XML 1.0.")
    return text


def _resolve_line_width(host_config: dict[str, Any] | None) -> float:
    """Resolve active outer wall line width in mm from host_config (default 0.42 mm)."""
    if isinstance(host_config, dict):
        for direct_key in ("line_width_mm",):
            if direct_key in host_config:
                try:
                    lw = float(host_config[direct_key])
                    if 0.18 <= lw <= 2.5:
                        return lw
                except (TypeError, ValueError):
                    pass
        printer = host_config.get("printer")
        if isinstance(printer, dict) and "line_width_mm" in printer:
            try:
                lw = float(printer["line_width_mm"])
                if 0.18 <= lw <= 2.5:
                    return lw
            except (TypeError, ValueError):
                pass
        ps = host_config.get("project_settings")
        if isinstance(ps, dict):
            raw_lw = ps.get("outer_wall_line_width") or ps.get("line_width")
            if isinstance(raw_lw, (list, tuple)) and raw_lw:
                raw_lw = raw_lw[0]
            if raw_lw is not None:
                s = str(raw_lw).strip()
                if not s.endswith("%"):
                    m = re.search(r"[-+]?\d*\.?\d+", s)
                    if m:
                        try:
                            lw = float(m.group(0))
                            if 0.18 <= lw <= 2.5:
                                return lw
                        except ValueError:
                            pass
    return 0.42


def _positions_overlap(
    positions: list[tuple[float, float, float]],
    extents: list[tuple[float, float]],
    min_clearance_mm: float = 3.0,
) -> bool:
    """Return True if any two axis-aligned bounding boxes overlap on the XY build plate."""
    n = len(positions)
    for i in range(n):
        xi, yi, _ = positions[i]
        wxi, wyi = extents[i]
        for j in range(i + 1, n):
            xj, yj, _ = positions[j]
            wxj, wyj = extents[j]
            overlap_x = abs(xi - xj) < (0.5 * (wxi + wxj) + min_clearance_mm)
            overlap_y = abs(yi - yj) < (0.5 * (wyi + wyj) + min_clearance_mm)
            if overlap_x and overlap_y:
                return True
    return False


def _pack_shelves(
    ordered_indices: list[int],
    extents: list[tuple[float, float]],
    max_row_width: float,
    gap_mm: float,
) -> tuple[list[list[int]], float, float]:
    """Pack `ordered_indices` greedily into horizontal shelves bounded by `max_row_width`."""
    rows: list[list[int]] = []
    cur_row: list[int] = []
    cur_w = 0.0

    for idx in ordered_indices:
        w, _ = extents[idx]
        needed_w = w if not cur_row else (cur_w + gap_mm + w)
        if cur_row and needed_w > max_row_width:
            rows.append(cur_row)
            cur_row = [idx]
            cur_w = w
        else:
            cur_row.append(idx)
            cur_w = needed_w
    if cur_row:
        rows.append(cur_row)

    total_w = 0.0
    total_h = 0.0
    for r_idx, row in enumerate(rows):
        rw = sum(extents[i][0] for i in row) + gap_mm * (len(row) - 1)
        rh = max(extents[i][1] for i in row)
        total_w = max(total_w, rw)
        total_h += rh + (gap_mm if r_idx > 0 else 0.0)

    return rows, total_w, total_h


def _arrange_items_on_bed(
    extents: list[tuple[float, float]],
    z_offsets: list[float],
    bed_x: float,
    bed_y: float,
    gap_mm: float = 8.0,
) -> list[tuple[float, float, float]]:
    """Arrange 1 to 6+ items in a compact 2D multi-row shelf/grid layout centered on `(bed_x/2, bed_y/2)`."""
    cx = bed_x * 0.5
    cy = bed_y * 0.5
    count = len(extents)
    if count == 0:
        return []
    if count == 1:
        return [(cx, cy, z_offsets[0])]

    usable_x = max(bed_x - 8.0, 40.0)
    usable_y = max(bed_y - 8.0, 40.0)

    if count == 2:
        (w0, d0), (w1, d1) = extents
        total_w = w0 + gap_mm + w1
        if total_w <= usable_x:
            left_edge = cx - 0.5 * total_w
            x0 = left_edge + 0.5 * w0
            x1 = left_edge + w0 + gap_mm + 0.5 * w1
            return [(x0, cy, z_offsets[0]), (x1, cy, z_offsets[1])]

        total_h = d0 + gap_mm + d1
        if total_h <= usable_y and max(w0, w1) <= usable_x:
            bot_edge = cy - 0.5 * total_h
            y0 = bot_edge + 0.5 * d0
            y1 = bot_edge + d0 + gap_mm + 0.5 * d1
            return [(cx, y0, z_offsets[0]), (cx, y1, z_offsets[1])]

        # Place along bed diagonal with guaranteed AABB clearance when side-by-side exceeds bed width
        sep_x = 0.5 * (w0 + w1) + gap_mm
        sep_y = 0.5 * (d0 + d1) + gap_mm
        dx = min(sep_x, max(0.5 * sep_x + 1.0, usable_x - 0.5 * (w0 + w1)))
        dy = sep_y if dx < sep_x else 0.0
        return [
            (cx - 0.5 * dx, cy - 0.5 * dy, z_offsets[0]),
            (cx + 0.5 * dx, cy + 0.5 * dy, z_offsets[1]),
        ]

    # Multi-item 2D shelf bin-packing for 3..N items (e.g. 4-item fit_test_kit or full_suite)
    sum_w = sum(w for w, _ in extents) + gap_mm * (count - 1)
    max_single_w = max(w for w, _ in extents)

    # Evaluate both natural order and height-sorted order across candidate shelf widths
    orderings = [
        list(range(count)),
        sorted(range(count), key=lambda i: (-extents[i][1], -extents[i][0], i)),
    ]
    candidate_widths = sorted(
        {
            max(max_single_w, usable_x),
            max(max_single_w, 0.88 * usable_x),
            max(max_single_w, 0.74 * usable_x),
            max(max_single_w, 0.60 * usable_x),
            max(max_single_w, 0.52 * sum_w),
            max(max_single_w, sum_w + 1.0),
        }
    )

    best_rows: list[list[int]] | None = None
    best_total_h = 0.0
    best_score: tuple[int, float, float] | None = None

    for order in orderings:
        for cap_w in candidate_widths:
            rows, tw, th = _pack_shelves(order, extents, cap_w, gap_mm)
            fits = 0 if (tw <= usable_x and th <= usable_y) else 1
            norm_aspect = max(tw / usable_x, th / usable_y)
            area_box = tw * th
            score = (fits, round(norm_aspect, 4), round(area_box, 2))
            if best_score is None or score < best_score:
                best_score = score
                best_rows = rows
                best_total_h = th

    assert best_rows is not None
    placed: list[tuple[float, float, float]] = [(cx, cy, 0.0)] * count
    y_cursor = cy - 0.5 * best_total_h

    for row in best_rows:
        row_w = sum(extents[i][0] for i in row) + gap_mm * (len(row) - 1)
        row_h = max(extents[i][1] for i in row)
        row_cy = y_cursor + 0.5 * row_h
        x_cursor = cx - 0.5 * row_w
        for orig_idx in row:
            w_i, _ = extents[orig_idx]
            px = x_cursor + 0.5 * w_i
            placed[orig_idx] = (px, row_cy, z_offsets[orig_idx])
            x_cursor += w_i + gap_mm
        y_cursor += row_h + gap_mm

    return placed


def _build_project_settings_dict(
    params: dict[str, Any] | None, host_config: dict[str, Any] | None
) -> dict[str, Any]:
    """Merge host settings with mechanical enclosure settings when requested."""
    merged: dict[str, Any] = {}
    if isinstance(host_config, dict):
        raw_ps = host_config.get("project_settings")
        if isinstance(raw_ps, dict):
            merged.update(raw_ps)

    p = params if isinstance(params, dict) else {}

    # Enclosures need closed floors and multiple walls.
    merged["spiral_mode"] = "0"
    merged["spiral_mode_smooth"] = "0"

    if bool(p.get("auto_configure_slicer", True)):
        wall_loops = 4

        merged["wall_loops"] = str(wall_loops)
        merged["top_shell_layers"] = "5"
        merged["bottom_shell_layers"] = "5"
        merged["sparse_infill_density"] = "35%"
        merged["sparse_infill_pattern"] = "gyroid"
        merged["elefant_foot_compensation"] = "0.15"

    return merged


def write_binary_stl(
    path: str | Path, mesh: Any, header_name: str = "OrcaBoxStudio"
) -> Path:
    """Write a duck-typed MeshData object to a standard little-endian binary STL file.

    Binary layout: 80-byte ASCII header + uint32 triangle count + F * 50-byte facet records.
    """
    out_path = Path(path)
    if not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)

    vertices, triangles, normals = _extract_mesh_arrays(mesh)
    num_triangles = int(triangles.shape[0])

    clean_header = str(header_name or "OrcaBoxStudio").strip() or "OrcaBoxStudio"
    if clean_header.lower().startswith("solid"):
        clean_header = f"Orca_{clean_header}"
    header_text = f"{clean_header} - Orca Box Studio Binary STL"
    header_bytes = header_text.encode("ascii", errors="replace")[:80].ljust(80, b"\x00")

    records = np.zeros(num_triangles, dtype=_STL_RECORD_DTYPE)
    if num_triangles > 0:
        tris_xyz = vertices[triangles]
        records["normal"] = normals.astype("<f4", copy=False)
        records["v0"] = tris_xyz[:, 0, :].astype("<f4", copy=False)
        records["v1"] = tris_xyz[:, 1, :].astype("<f4", copy=False)
        records["v2"] = tris_xyz[:, 2, :].astype("<f4", copy=False)
        records["attr"] = 0

    with open(out_path, "wb") as fh:
        fh.write(header_bytes)
        fh.write(struct.pack("<I", num_triangles))
        if num_triangles > 0:
            fh.write(records.tobytes())

    return out_path


def write_orca_3mf(
    path: str | Path,
    items: list[tuple[str, Any] | tuple[str, Any, tuple[float, float, float] | None]],
    params: dict[str, Any],
    host_config: dict[str, Any] | None = None,
) -> Path:
    """Write an OrcaSlicer 2.5.1+ compatible .3mf project archive with multi-object layout & slicer settings."""
    if not items:
        raise ValueError("write_orca_3mf requires at least one item in 'items'.")

    out_path = Path(path)
    if not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)

    bed_x, bed_y = _resolve_bed_dimensions(host_config)
    cx, cy = bed_x * 0.5, bed_y * 0.5

    parsed_items: list[
        tuple[str, np.ndarray, np.ndarray, tuple[float, float], tuple[float, float]]
    ] = []
    raw_positions: list[tuple[float, float, float] | None] = []
    z_offsets: list[float] = []

    for idx, entry in enumerate(items):
        if len(entry) == 2:
            raw_name, mesh = entry  # type: ignore[misc]
            raw_pos = None
        elif len(entry) >= 3:
            raw_name, mesh, raw_pos = entry[0], entry[1], entry[2]
        else:
            raise ValueError(f"Invalid item tuple at index {idx}: {entry!r}")

        item_name = (
            _validated_xml_text(raw_name or f"Box_{idx + 1}", "Part name").strip()
            or f"Box_{idx + 1}"
        )
        vertices, triangles, _ = _extract_mesh_arrays(mesh)
        ext = _mesh_xy_extents(mesh, vertices)
        local_mid = _mesh_xy_center_offset(mesh, vertices)
        parsed_items.append((item_name, vertices, triangles, ext, local_mid))

        if raw_pos is None:
            raw_positions.append(None)
            z_offsets.append(0.0)
        else:
            px, py, pz = float(raw_pos[0]), float(raw_pos[1]), float(raw_pos[2])
            if not all(math.isfinite(value) for value in (px, py, pz)):
                raise ValueError("Object placement must contain finite coordinates.")
            raw_positions.append((px, py, pz))
            z_offsets.append(pz)

    extents_list = [it[3] for it in parsed_items]
    if any(pos is None for pos in raw_positions):
        if len(parsed_items) == 1:
            box_centers = [(cx, cy, z_offsets[0])]
        else:
            box_centers = _arrange_items_on_bed(
                extents_list, z_offsets, bed_x, bed_y, gap_mm=8.0
            )
        # Subtract local mesh midpoint so even asymmetric sector/gauge meshes land centered on their box!
        final_positions = [
            (bx - parsed_items[i][4][0], by - parsed_items[i][4][1], bz)
            for i, (bx, by, bz) in enumerate(box_centers)
        ]
    else:
        concrete_centers = [
            (pos[0] + parsed_items[i][4][0], pos[1] + parsed_items[i][4][1], pos[2])
            for i, pos in enumerate(raw_positions)
            if pos is not None
        ]
        if len(concrete_centers) >= 2 and _positions_overlap(
            concrete_centers, extents_list, min_clearance_mm=3.0
        ):
            box_centers = _arrange_items_on_bed(
                extents_list, z_offsets, bed_x, bed_y, gap_mm=8.0
            )
            final_positions = [
                (bx - parsed_items[i][4][0], by - parsed_items[i][4][1], bz)
                for i, (bx, by, bz) in enumerate(box_centers)
            ]
        else:
            final_positions = [pos for pos in raw_positions if pos is not None]

    centers = [
        (position[0] + item[4][0], position[1] + item[4][1], position[2])
        for position, item in zip(final_positions, parsed_items)
    ]
    if _positions_overlap(centers, extents_list, min_clearance_mm=0.01):
        raise ValueError("Parts overlap on the build plate; export fewer parts.")
    height_limit = _resolve_positive_limit(
        host_config, ("bed_z", "max_z", "printable_height"), None
    )
    for item, position in zip(parsed_items, final_positions):
        vertices = item[1]
        translated_min = vertices.min(axis=0).astype(np.float64) + position
        translated_max = vertices.max(axis=0).astype(np.float64) + position
        if (translated_min[:2] < -0.001).any() or (
            translated_max[:2] > np.array((bed_x, bed_y)) + 0.001
        ).any():
            raise ValueError(
                "Parts do not fit the selected bed; export fewer parts or reduce dimensions."
            )
        if translated_min[2] < -0.001:
            raise ValueError("A part extends below the build plate.")
        if height_limit is not None and translated_max[2] > float(height_limit) + 0.001:
            raise ValueError("A part exceeds the selected printer's build height.")

    title = _validated_xml_text(
        (params or {}).get("name") or parsed_items[0][0] or "Orca Box Studio",
        "Project title",
    ).strip()
    escaped_title = _xml_escape(title, {'"': "&quot;"})
    today_iso = _dt.date.today().isoformat()
    ns_seed = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    build_uuid = str(uuid.uuid5(ns_seed, f"orca-box-build-{title}"))

    object_blocks: list[str] = []
    build_items_xml: list[str] = []
    model_settings_objects: list[str] = []
    model_settings_instances: list[str] = []
    model_settings_assemble: list[str] = []

    for idx, (item_name, vertices, triangles, _, _) in enumerate(parsed_items):
        obj_id = idx + 1
        tx, ty, tz = final_positions[idx]
        esc_name = _xml_escape(item_name, {'"': "&quot;"})
        obj_uuid = str(uuid.uuid5(ns_seed, f"orca-box-obj-{obj_id}-{item_name}"))
        item_uuid = str(uuid.uuid5(ns_seed, f"orca-box-item-{obj_id}-{item_name}"))

        verts_py = vertices.tolist()
        tris_py = triangles.tolist()

        vertex_lines = "\n".join(
            f'     <vertex x="{vx:.9g}" y="{vy:.9g}" z="{vz:.9g}"/>'
            for vx, vy, vz in verts_py
        )
        triangle_lines = "\n".join(
            f'     <triangle v1="{v1}" v2="{v2}" v3="{v3}"/>' for v1, v2, v3 in tris_py
        )

        object_blocks.append(
            f'  <object id="{obj_id}" p:UUID="{obj_uuid}" name="{esc_name}" type="model">\n'
            f"   <mesh>\n"
            f"    <vertices>\n"
            f"{vertex_lines}\n"
            f"    </vertices>\n"
            f"    <triangles>\n"
            f"{triangle_lines}\n"
            f"    </triangles>\n"
            f"   </mesh>\n"
            f"  </object>"
        )

        transform_3x4 = f"1 0 0 0 1 0 0 0 1 {tx:.4f} {ty:.4f} {tz:.4f}"
        build_items_xml.append(
            f'  <item objectid="{obj_id}" p:UUID="{item_uuid}" transform="{transform_3x4}" printable="1"/>'
        )

        model_settings_objects.append(
            f'  <object id="{obj_id}">\n'
            f'    <metadata key="name" value="{esc_name}"/>\n'
            f'    <metadata key="extruder" value="1"/>\n'
            f'    <part id="1" subtype="normal_part">\n'
            f'      <metadata key="name" value="{esc_name}"/>\n'
            f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
            f'      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
            f"    </part>\n"
            f"  </object>"
        )
        model_settings_instances.append(
            f"    <model_instance>\n"
            f'      <metadata key="object_id" value="{obj_id}"/>\n'
            f'      <metadata key="instance_id" value="0"/>\n'
            f'      <metadata key="identify_id" value="{100 + obj_id}"/>\n'
            f"    </model_instance>"
        )
        model_settings_assemble.append(
            f'    <assemble_item object_id="{obj_id}" instance_id="0" transform="{transform_3x4}" offset="0 0 0"/>'
        )

    model_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
        'requiredextensions="p">\n'
        ' <metadata name="Application">OrcaSlicer-2.5.1</metadata>\n'
        ' <metadata name="OrcaSlicer">2.5.1</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        f' <metadata name="Title">{escaped_title}</metadata>\n'
        f' <metadata name="CreationDate">{today_iso}</metadata>\n'
        " <resources>\n"
        + "\n".join(object_blocks)
        + "\n </resources>\n"
        + f' <build p:UUID="{build_uuid}">\n'
        + "\n".join(build_items_xml)
        + "\n </build>\n"
        "</model>\n"
    )

    model_settings_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<config>\n" + "\n".join(model_settings_objects) + "\n  <plate>\n"
        '    <metadata key="plater_id" value="1"/>\n'
        '    <metadata key="plater_name" value=""/>\n'
        '    <metadata key="locked" value="false"/>\n'
        + "\n".join(model_settings_instances)
        + "\n  </plate>\n"
        "  <assemble>\n" + "\n".join(model_settings_assemble) + "\n  </assemble>\n"
        "</config>\n"
    )

    project_settings = _build_project_settings_dict(params, host_config)
    project_settings_json = json.dumps(project_settings, indent=2, ensure_ascii=False)

    with zipfile.ZipFile(
        out_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", _RELS_XML)
        zf.writestr("3D/3dmodel.model", model_xml)
        zf.writestr("Metadata/model_settings.config", model_settings_xml)
        zf.writestr("Metadata/project_settings.config", project_settings_json)

    return out_path
