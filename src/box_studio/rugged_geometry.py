"""Independent parametric reconstruction of a snap-hinged storage enclosure.

Dimensions describe the nominal outer body, not the protruding fittings. The
base and lid heights are independent. No reference mesh, asset, or triangulation
is read by this module. Curves are generated from dimensional primitives.
"""

from __future__ import annotations

import math
from typing import Any


def rugged_dimensions(p: dict[str, Any]) -> dict[str, Any]:
    """Dimensional contract, without normalization or hidden parameter changes."""
    w, d, h = (float(p[k]) for k in ("width_x", "depth_y", "height_z"))
    lh = float(p.get("rugged_lid_height", 20.0))
    t, f, r, c = (
        float(p.get(k, default))
        for k, default in (
            ("wall_thickness", 2.5),
            ("floor_thickness", 2.5),
            ("corner_radius", 12.0),
            ("fit_clearance", 0.15),
        )
    )
    return {
        "width": w,
        "depth": d,
        "base_height": h,
        "lid_height": lh,
        "height_closed": h + lh,
        "wall": t,
        "floor": f,
        "radius": r,
        "clearance": c,
        "bevel_height": 10.0,
        "bevel_inset": 10.0 / math.sqrt(3),
        "rim_depth": 0.85,
        "rim_width": 1.7,
        "fitting_centers": [-w / 2 + r + 20.75, w / 2 - r - 20.75],
    }


def rugged_hinge_geometry(p: dict[str, Any]) -> dict[str, Any]:
    q = rugged_dimensions(p)
    return {
        "axis": "x",
        "y": q["depth"] / 2 + 4.75,
        "z": q["base_height"],
        "centers": q["fitting_centers"],
        "open_sign": -1,
        "radius": 5.0,
        "socket_radius": 5.0 + q["clearance"] * 5 / 6,
        "outer_radius": 4.5,
        "axial_clearance": q["clearance"] * 5 / 3,
        "ball_centers": [
            {"x": center + offset, "y": q["depth"] / 2 + 4.75, "z": q["base_height"]}
            for center in q["fitting_centers"]
            for offset in (-7, 7)
        ],
        "mouth_radius": 4.8,
        "mouth_open_direction": "-z",
        "mouth_join_z": q["base_height"]
        - math.sqrt((5 + q["clearance"] * 5 / 6) ** 2 - 4.8**2),
        "axial_capture": 1.25 - q["clearance"] * 5 / 3,
        "base_outer_draft_slope": 1 / 3,
        "lid_slot_width": 5.5,
        "lid_slot_draft_slope": 1 / 3,
    }


def rugged_latch_geometry(p: dict[str, Any], part: str) -> dict[str, Any]:
    if part not in ("clip_left", "clip_right"):
        raise ValueError("Use uma trava / use a latch.")
    q = rugged_dimensions(p)
    return {
        "axis": "x",
        "open_sign": -1,
        "pivot": {
            "x": q["fitting_centers"][part == "clip_right"],
            "y": -q["depth"] / 2 - 3.0,
            "z": q["base_height"] + q["lid_height"] - 10.0,
        },
        "release_angle": 90.0,
        "release_fraction": 0.25,
        "radius": 3.75,
        "socket_radius": 3.75 + q["clearance"],
        "ball_centers_x": [-10.25, 10.25],
        "attachment": "lid",
        "cam_centers": [
            {
                "x": q["fitting_centers"][part == "clip_right"] + offset,
                "y": -q["depth"] / 2 - 3,
                "z": q["base_height"] - 8.19694,
            }
            for offset in (-8.5, 8.5)
        ],
        "cam_radius": 5.0,
        "cam_axial_cap": 3.0,
        "cam_release_interference_nominal": 0.75,
    }


def rugged_transform(vertices, p: dict[str, Any], part: str, angle: float):
    """Rotate a canonical CLOSED part outwards; never mutate the input array."""
    from .mesh_generator import np

    if part == "lid":
        meta = rugged_hinge_geometry(p)
        pivot = [0.0, meta["y"], meta["z"]]
    elif part in ("clip_left", "clip_right"):
        meta = rugged_latch_geometry(p, part)
        pivot = [meta["pivot"][key] for key in ("x", "y", "z")]
    else:
        raise ValueError("Somente tampa/travas giram / only lid/latches rotate.")
    theta = math.radians(-float(angle))
    cs, sn = math.cos(theta), math.sin(theta)
    local = np.asarray(vertices, dtype=float) - pivot
    result = local.copy()
    result[:, 1] = local[:, 1] * cs - local[:, 2] * sn
    result[:, 2] = local[:, 1] * sn + local[:, 2] * cs
    return result + pivot


def _body_sections(p, part):
    q = rugged_dimensions(p)
    t, f, h = q["wall"], q["floor"], q["base_height"]
    k = q["bevel_height"]
    height = h if part == "base" else q["lid_height"]
    inner_knee = k + t * (2 - math.sqrt(3))
    floor_inset = (k - f) / math.sqrt(3) + t * 2 / math.sqrt(3)
    outer = [(0.0, q["bevel_inset"]), (k, 0.0), (height, 0.0)]
    inner = [(f, floor_inset), (inner_knee, t), (height, t)]
    land = (t - q["rim_width"]) / 2
    rim = [
        (0.0, height),
        (land, height),
        (t / 2, height - q["rim_depth"] if part == "base" else height + q["rim_depth"]),
        (t - land, height),
        (t, height),
    ]
    if part == "lid":
        reflect = lambda z: h + height - z
        outer = [(reflect(z), s) for z, s in outer]
        inner = [(reflect(z), s) for z, s in inner]
        rim = [(s, reflect(z)) for s, z in rim]
    return q, outer, inner, rim


def rugged_outer_body_y(p, part, side, z):
    """Shared float64 mapping of the flat front/rear panel and its chamfer."""
    from .mesh_generator import np

    q = rugged_dimensions(p)
    z = np.asarray(z, dtype=float)
    if part == "base":
        inset = np.interp(z, [0.0, 10.0], [q["bevel_inset"], 0.0])
    else:
        knee = float(np.float32(q["height_closed"] - 10))
        roof = float(np.float32(q["height_closed"]))
        inset = np.interp(z, [knee, roof], [0.0, q["bevel_inset"]])
    return (-q["depth"] / 2 + inset) if side == 0 else (q["depth"] / 2 - inset)


def _body_boundary_x_events(p, part, loops):
    from .mesh_generator import np

    q = rugged_dimensions(p)
    boundaries = (
        [0, q["base_height"]]
        if part == "base"
        else [q["base_height"], q["height_closed"]]
    )
    levels = {float(np.float32(z)) for z in boundaries}
    extent = q["width"] / 2 - q["radius"]

    def canonical_x(x):
        for boundary in (-extent, extent):
            if np.float32(x) == np.float32(boundary):
                return boundary
        return float(x)

    return [
        canonical_x(v[0])
        for loop in loops
        for v in loop
        if float(np.float32(v[2])) in levels
    ]


def _body_builder(
    p, part, attachments=(), omit_sides=(), foot_loops=None, local_panel_seams=False
):
    """Boundary loft of the shell. Fittings replace patches in the final build."""
    from .mesh_generator import _SurfaceBuilder, _rectangle_loop, np

    q, outer, inner, rim = _body_sections(p, part)
    outer = [(float(np.float32(z)), inset) for z, inset in outer]
    inner = [(float(np.float32(z)), inset) for z, inset in inner]
    rim = [(inset, float(np.float32(z))) for inset, z in rim]
    tolerance = min(q["clearance"] / 4, 0.025)
    n = max(8, math.ceil(math.pi / (4 * math.acos(1 - tolerance / q["radius"]))))
    # An attachment replaces an outer panel patch. All profiles share its exact
    # X seam coordinates, including the chamfer and V-rim sections.
    extent = q["width"] / 2 - q["radius"]
    stops = {}
    foot_loops = foot_loops or {}
    for side in (0, 2):
        seam_x = _body_boundary_x_events(p, part, foot_loops.get(side, []))
        xs = sorted(
            set(
                [-extent, extent]
                + [x for a in attachments if a[0] == side for x in a[1:3]]
                + seam_x
            )
        )
        if side == 2:
            xs = xs[::-1]
        stops[side] = [
            (x + extent) / (2 * extent) if side == 0 else (extent - x) / (2 * extent)
            for x in xs
        ]
    extra_z = [float(np.float32(z)) for a in attachments for z in a[3:5]]
    if not local_panel_seams:
        extra_z += [
            float(v[2]) for loops in foot_loops.values() for loop in loops for v in loop
        ]

    def insert_levels(profile):
        result = list(profile)
        for z in extra_z:
            for (za, sa), (zb, sb) in zip(profile, profile[1:]):
                if min(za, zb) < z < max(za, zb):
                    result.append((z, sa + (z - za) * (sb - sa) / (zb - za)))
        return sorted(set(result), reverse=profile[0][0] > profile[-1][0])

    outer = insert_levels(outer)

    def loop(inset, z):
        return _rectangle_loop(
            q["width"] - 2 * inset,
            q["depth"] - 2 * inset,
            q["radius"] - inset,
            z,
            n,
            stops,
        )

    out = [loop(s, z) for z, s in outer]
    ins = [loop(s, z) for z, s in inner]
    builder = _SurfaceBuilder()
    builder.disk(out[0], True)
    builder.disk(ins[0])
    for a, b in zip(out, out[1:]):
        for k in range(len(a)):
            j = (k + 1) % len(a)
            middle_x, middle_z = (a[k, 0] + a[j, 0]) / 2, (a[k, 2] + b[k, 2]) / 2
            flat = abs(a[k, 1] - a[j, 1]) < 1e-8
            skipped_side = 0 if a[k, 1] < 0 else 2
            skip = (flat and skipped_side in omit_sides) or any(
                lo < middle_x < hi
                and min(zlo, zhi) < middle_z < max(zlo, zhi)
                and abs(a[k, 1] - a[j, 1]) < 1e-8
                and (a[k, 1] < 0 if side == 0 else a[k, 1] > 0)
                for side, lo, hi, zlo, zhi in attachments
            )
            if not skip:

                def seam_nodes(pa, pb):
                    if (
                        not local_panel_seams
                        or abs(abs(pa[0]) - extent) > 1e-8
                        or abs(pa[0] - pb[0]) > 1e-8
                    ):
                        return []
                    side = 0 if pa[1] < 0 else 2
                    if (
                        abs(pa[1] - float(rugged_outer_body_y(p, part, side, pa[2])))
                        > 1e-8
                        or abs(pb[1] - float(rugged_outer_body_y(p, part, side, pb[2])))
                        > 1e-8
                    ):
                        return []
                    fractions = sorted(
                        set(
                            (float(v[2]) - pa[2]) / (pb[2] - pa[2])
                            for loop in foot_loops.get(side, [])
                            for v in loop
                            if min(pa[2], pb[2]) < v[2] < max(pa[2], pb[2])
                        )
                    )
                    return [pa + t * (pb - pa) for t in fractions]

                polygon = [
                    a[k],
                    a[j],
                    *seam_nodes(a[j], b[j]),
                    b[j],
                    b[k],
                    *seam_nodes(b[k], a[k]),
                ]
                if len(polygon) == 4:
                    builder.quad(*polygon)
                else:
                    builder.disk(polygon)
    for a, b in zip(ins, ins[1:]):
        builder.join(a, b, True)
    rim_loops = [loop(s, z) for s, z in rim]
    for a, b in zip(rim_loops, rim_loops[1:]):
        builder.join(a, b)
    if part == "lid":
        builder.faces = [face[::-1] for face in builder.faces]
    return builder


def _generate_body_mesh(p, part):
    q = rugged_dimensions(p)
    builder = _body_builder(p, part)
    tolerance = min(q["clearance"] / 4, 0.025)
    return builder.mesh(part, tolerance)


def _body_field(p, part):
    from .mesh_generator import np, _round2

    q = rugged_dimensions(p)
    h, t, f, k = q["base_height"], q["wall"], q["floor"], q["bevel_height"]
    height = h if part == "base" else q["lid_height"]

    def field(points):
        x, y, z = np.asarray(points).T
        if part == "lid":
            z = h + height - z
        radial = _round2(x, y, q["width"] / 2, q["depth"] / 2, q["radius"])
        inset = -radial
        v_depth = np.maximum(0.0, q["rim_depth"] - np.abs(inset - t / 2))
        top = height - v_depth if part == "base" else height + v_depth
        exterior = np.maximum.reduce(
            (radial + np.maximum(0, (k - z) / math.sqrt(3)), -z, z - top)
        )
        cavity_inset = np.maximum(t, (k - z) / math.sqrt(3) + t * 2 / math.sqrt(3))
        cavity = np.maximum(radial + cavity_inset, f - z)
        return np.maximum(exterior, -cavity)

    return field


def rugged_print_transform(vertices, p, part):
    """Apply saved broad-face print orientations without arrangement or scaling."""
    from .mesh_generator import np

    result = np.asarray(vertices, dtype=float).copy()
    q = rugged_dimensions(p)
    if part == "lid":
        result[:, 0] *= -1
        result[:, 2] = q["height_closed"] - result[:, 2]
    elif part in ("clip_left", "clip_right"):
        pivot = rugged_latch_geometry(p, part)["pivot"]
        result[:, 0] *= -1
        result[:, 1] = vertices[:, 2]
        result[:, 2] = vertices[:, 1] - pivot["y"] + 3
    elif part != "base":
        raise ValueError("Peça inválida / invalid part.")
    return result


def rugged_print_bounds(p, part):
    """Conservative analytic print AABB, without generating a fitting mesh."""
    from .mesh_generator import np

    q = rugged_dimensions(p)
    if part == "base":
        low = [-q["width"] / 2, -q["depth"] / 2 - 8, 0]
        high = [q["width"] / 2, q["depth"] / 2 + 9.25, q["base_height"] + 4.5]
    elif part == "lid":
        low = [-q["width"] / 2, -q["depth"] / 2 - 8, q["base_height"] - 4.5]
        high = [q["width"] / 2, q["depth"] / 2 + 9.25, q["height_closed"]]
    elif part in ("clip_left", "clip_right"):
        pivot = rugged_latch_geometry(p, part)["pivot"]
        low = [pivot["x"] - 14, pivot["y"] - 3, q["base_height"] - 19.93335]
        high = [pivot["x"] + 14, pivot["y"] + 3, pivot["z"] + 3]
    else:
        raise ValueError("Peça inválida / invalid part.")
    corners = np.array(
        [
            [x, y, z]
            for x in (low[0], high[0])
            for y in (low[1], high[1])
            for z in (low[2], high[2])
        ]
    )
    transformed = rugged_print_transform(corners, p, part)
    lo, hi = transformed.min(0), transformed.max(0)
    return {"min": lo.tolist(), "max": hi.tolist(), "size": (hi - lo).tolist()}


def _face_polygon(builder, points, reverse=False):
    """Triangulate a simple planar contour, preserving every seam vertex."""
    from .mesh_generator import np

    poly = np.asarray(points, dtype=float)
    keep = np.r_[True, np.linalg.norm(np.diff(poly, axis=0), axis=1) > 1e-8]
    poly = poly[keep]
    if np.linalg.norm(poly[-1] - poly[0]) < 1e-8:
        poly = poly[:-1]
    if len(poly) < 3:
        return
    normal = np.sum(np.cross(poly, np.roll(poly, -1, axis=0)), axis=0)
    drop = int(np.argmax(np.abs(normal)))
    xy = poly[:, [i for i in range(3) if i != drop]]
    cross2 = lambda a, b: a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]
    area = float(np.sum(cross2(xy, np.roll(xy, -1, axis=0))))
    sign = 1 if area > 0 else -1
    indices = list(range(len(poly)))
    while len(indices) > 3:
        for k, middle in enumerate(indices):
            left, right = indices[k - 1], indices[(k + 1) % len(indices)]
            a, b, c = xy[[left, middle, right]]
            if cross2(b - a, c - b) * sign <= 1e-11:
                continue
            others = [i for i in indices if i not in (left, middle, right)]
            points2 = xy[others]
            inside = (
                (cross2(b - a, points2 - a) * sign >= -1e-10)
                & (cross2(c - b, points2 - b) * sign >= -1e-10)
                & (cross2(a - c, points2 - c) * sign >= -1e-10)
            )
            if np.any(inside):
                continue
            builder.triangle(poly[left], poly[middle], poly[right], reverse)
            indices.pop(k)
            break
        else:
            raise ValueError("Contorno não triangulável / non-simple fitting contour.")
    builder.triangle(*(poly[i] for i in indices), reverse=reverse)


def _append_panel_with_feet(builder, p, part, side, foot_loops):
    """Fill an outer panel around open fitting footprints in X/Z coordinates.

    Trapezoidal strips handle footprints touching the rim, roof or side seam.
    Horizontal event edges retain all footprint vertices, preventing T junctions
    when a fitting begins or ends on an otherwise continuous panel.
    """
    from .mesh_generator import np

    q = rugged_dimensions(p)
    extent = q["width"] / 2 - q["radius"]
    bottom, top = (
        (0.0, q["base_height"])
        if part == "base"
        else (q["base_height"], q["height_closed"])
    )
    knee = 10.0 if part == "base" else top - 10
    bottom, top, knee = (float(np.float32(z)) for z in (bottom, top, knee))
    loops = [np.asarray(loop, dtype=float)[:, [0, 2]].copy() for loop in foot_loops]
    for loop in loops:
        loop[:, 1] = loop[:, 1].astype(np.float32)
        for edge in (-extent, extent):
            loop[loop[:, 0].astype(np.float32) == np.float32(edge), 0] = edge
    levels = np.unique(
        np.r_[
            [bottom, top, knee],
            [v[1] for loop in loops for v in loop if bottom <= v[1] <= top],
        ]
    )
    edges = [(a, b) for loop in loops for a, b in zip(loop, np.roll(loop, -1, axis=0))]

    def horizontal_events(z):
        values = [-extent, extent]
        if abs(z - bottom) < 1e-6 or abs(z - top) < 1e-6:
            values.extend(_body_boundary_x_events(p, part, foot_loops))
        for a, b in edges:
            if abs(a[1] - z) < 1e-6:
                values.append(a[0])
            if abs(b[1] - z) < 1e-6:
                values.append(b[0])
            if min(a[1], b[1]) < z < max(a[1], b[1]):
                values.append(a[0] + (z - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
        return np.unique(values)

    for za, zb in zip(levels, levels[1:]):
        if zb - za < 1e-8:
            continue
        zm = (za + zb) / 2
        holes = []
        for loop in loops:
            active = []
            for a, b in zip(loop, np.roll(loop, -1, axis=0)):
                if min(a[1], b[1]) < zm < max(a[1], b[1]):
                    xs = [
                        a[0] + (z - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                        for z in (za, zb, zm)
                    ]
                    active.append(xs)
            active.sort(key=lambda item: item[2])
            if len(active) % 2:
                raise ValueError("Footprint is not a closed contour / contorno aberto.")
            holes.extend(zip(active[::2], active[1::2]))
        holes.sort(key=lambda item: item[0][2])
        fill, left = [], [-extent] * 3
        for hole_left, hole_right in holes:
            if hole_left[2] < left[2] - 1e-5:
                raise ValueError("Overlapping fitting footprints / apoios sobrepostos.")
            fill.append((left, hole_left))
            left = hole_right
        fill.append((left, [extent] * 3))
        event_a, event_b = horizontal_events(za), horizontal_events(zb)
        ya, yb = (
            float(rugged_outer_body_y(p, part, side, za)),
            float(rugged_outer_body_y(p, part, side, zb)),
        )
        for left, right in fill:
            if right[2] - left[2] < 1e-8:
                continue
            lower = [
                left[0],
                *event_a[(event_a > left[0] + 1e-7) & (event_a < right[0] - 1e-7)],
                right[0],
            ]
            upper = [
                right[1],
                *event_b[(event_b > left[1] + 1e-7) & (event_b < right[1] - 1e-7)][
                    ::-1
                ],
                left[1],
            ]
            points = [[x, ya, za] for x in lower] + [[x, yb, zb] for x in upper]
            builder.disk(np.asarray(points), side == 2)


def _rear_profile(p, attachment_levels=()):
    from .mesh_generator import np

    q = rugged_dimensions(p)
    cy, cz, radius = q["depth"] / 2 + 4.75, q["base_height"], 4.5
    back = q["depth"] / 2
    draft_angle = math.acos((back + 1 - cy) / radius)
    arc = np.unique(np.r_[np.linspace(-math.pi / 6, math.pi, 34), draft_angle])
    tangent_y, tangent_z = (
        cy + radius * math.cos(arc[0]),
        cz + radius * math.sin(arc[0]),
    )
    root = tangent_z - math.sqrt(3) * (tangent_y - back)
    back_levels = sorted(
        set([root, cz] + [z for z in attachment_levels if root < z < cz]), reverse=True
    )
    profile = np.r_[
        np.array([[back, root]]),
        np.column_stack((cy + radius * np.cos(arc), cz + radius * np.sin(arc))),
        np.array([[back, z] for z in back_levels]),
    ]
    return profile, root, tangent_y


def _clip_profile_y(profile, level, above):
    from .mesh_generator import np

    result = []
    for a, b in zip(profile, np.roll(profile, -1, axis=0)):
        da, db = a[0] - level, b[0] - level
        inside_a = da >= -1e-9 if above else da <= 1e-9
        inside_b = db >= -1e-9 if above else db <= 1e-9
        if inside_a:
            result.append(a)
        if inside_a != inside_b:
            result.append(a + da / (da - db) * (b - a))
    return np.asarray(result)


def _append_rear_socket(
    builder, p, lo, hi, sphere_x, attachment_levels=(), close_back=False
):
    """Left socket: spherical blind cup with a genuine downward insertion mouth.

    The cup and mouth are parameterized on common X rings. Its lower opening
    replaces part of the tangent root plane, so no internal face or overlap
    remains after attachment to the analytic body wall.
    """
    from .mesh_generator import np

    q = rugged_dimensions(p)
    cy, cz = q["depth"] / 2 + 4.75, q["base_height"]
    rs, rm = 5 + q["clearance"] * 5 / 6, 4.8
    dz = math.sqrt(rs * rs - rm * rm)
    join_z = cz - dz
    profile, root_z, tangent_y = _rear_profile(p, attachment_levels)
    back = q["depth"] / 2
    draft_y = back + 1
    outer_x = lambda y: lo + max(0, (y - draft_y) / 3)
    lower_z = lambda y: root_z + math.sqrt(3) * (y - back)
    sphere_tip, mouth_tip = sphere_x - rs, sphere_x - rm
    # Include both curvature parameterizations, not a uniform sampling lattice.
    theta_s = math.acos((sphere_x - hi) / rs)
    theta_m = math.acos((sphere_x - hi) / rm)
    xs = np.unique(
        np.r_[
            sphere_x - rs * np.cos(np.linspace(0, theta_s, 11)),
            sphere_x - rm * np.cos(np.linspace(0, theta_m, 11)),
            sphere_tip,
            mouth_tip,
            hi,
        ]
    )
    xs[-1] = hi
    n = 36
    rings, left, right = [], [], []
    for x in xs:
        r = math.sqrt(max(0, rs * rs - (x - sphere_x) ** 2))
        alpha = -math.pi / 2 if r <= dz else math.asin(-dz / r)
        angles = np.linspace(alpha, math.pi - alpha, n + 1)
        ring = np.column_stack(
            (np.full(n + 1, x), cy + r * np.cos(angles), cz + r * np.sin(angles))
        )
        if x >= mouth_tip - 1e-8:
            yh = math.sqrt(max(0, rm * rm - (x - sphere_x) ** 2))
            ring[0] = [x, cy + yh, join_z]
            ring[-1] = [x, cy - yh, join_z]
            left.append((x, cy - yh))
            right.append((x, cy + yh))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            builder.quad(a[k], a[k + 1], b[k + 1], b[k], True)
    for branch, reverse in ((left, True), (right, False)):
        for (xa, ya), (xb, yb) in zip(branch, branch[1:]):
            builder.quad(
                [xa, ya, lower_z(ya)],
                [xb, yb, lower_z(yb)],
                [xb, yb, join_z],
                [xa, ya, join_z],
                reverse,
            )
    # Outer sweep; only the tangent bottom face is replaced by the mouth patch.
    for k in range(1, len(profile) - 1):
        a, b = profile[k], profile[k + 1]
        if not close_back and abs(a[0] - back) < 1e-8 and abs(b[0] - back) < 1e-8:
            continue
        builder.quad([outer_x(a[0]), *a], [outer_x(b[0]), *b], [hi, *b], [hi, *a])
    for above in (False, True):
        cap = _clip_profile_y(profile, draft_y, above)
        _face_polygon(builder, [[outer_x(y), y, z] for y, z in cap], True)
    left_y, right_y = left[-1][1], right[-1][1]
    cap = [[hi, back, root_z], [hi, left_y, lower_z(left_y)], [hi, left_y, join_z]]
    cap.extend(rings[-1][::-1].tolist())
    cap.extend(
        [[hi, right_y, lower_z(right_y)], *[[hi, *point] for point in profile[1:]]]
    )
    _face_polygon(builder, cap)
    bottom = [
        [lo, back],
        [hi, back],
        [hi, left_y],
        *left[::-1],
        *right[1:],
        [hi, tangent_y],
        [outer_x(tangent_y), tangent_y],
        [lo, draft_y],
    ]
    _face_polygon(builder, [[x, y, lower_z(y)] for x, y in bottom], True)


def _rear_socket_field(p, lo, hi, sphere_x, embed=False):
    from .mesh_generator import np, _polygon_prism_field

    q = rugged_dimensions(p)
    cy, cz = q["depth"] / 2 + 4.75, q["base_height"]
    rs, rm = 5 + q["clearance"] * 5 / 6, 4.8
    join_z = cz - math.sqrt(rs * rs - rm * rm)
    profile, root, tangent_y = _rear_profile(p)
    back = q["depth"] / 2
    shift = 0.02 if embed else 0
    tangent_z = root + math.sqrt(3) * (tangent_y - back)
    root_polygon = np.array(
        [
            [back - shift, root - math.sqrt(3) * shift],
            [tangent_y, tangent_z],
            [cy, cz],
            [back - shift, cz],
        ]
    )
    root_field = _polygon_prism_field(root_polygon, lo, hi)

    def field(points):
        delta = np.asarray(points) - [sphere_x, cy, cz]
        cup = np.linalg.norm(delta, axis=1) - rs
        mouth = np.maximum(
            np.linalg.norm(delta[:, :2], axis=1) - rm, points[:, 2] - join_z
        )
        barrel = np.maximum.reduce(
            (
                np.linalg.norm(delta[:, 1:], axis=1) - 4.5,
                lo - points[:, 0],
                points[:, 0] - hi,
            )
        )
        draft = lo + np.maximum(0, (points[:, 1] - (back + 1)) / 3) - points[:, 0]
        outer = np.maximum(np.minimum(root_field(points), barrel), draft)
        return np.maximum(outer, -np.minimum(cup, mouth))

    return field


def _rear_lid_profile(p, embed=False):
    from .mesh_generator import np

    q = rugged_dimensions(p)
    h, top = q["base_height"], q["height_closed"]
    h_plane, top_plane, knee_plane = (float(np.float32(z)) for z in (h, top, top - 10))
    back, cy = q["depth"] / 2, q["depth"] / 2 + 4.75
    angles = np.linspace(math.pi, 2 * math.pi + math.pi / 6, 34)
    arc = np.column_stack((cy + 4.5 * np.cos(angles), h + 4.5 * np.sin(angles)))
    roof_y = arc[-1, 0] - (top - arc[-1, 1]) / math.sqrt(3)
    body_roof_y = back - q["bevel_inset"]
    shift = 0.02 if embed else 0
    vertical_root_z = arc[-1, 1] + math.sqrt(3) * (arc[-1, 0] - back)
    if vertical_root_z <= top - 10:
        # A deeper lid meets the tangent brace on its straight wall before the
        # roof chamfer. Continuing to the roof would create a bow-tie contour.
        return np.r_[
            np.array([[back - shift, h_plane]]),
            arc,
            np.array(
                [
                    [
                        back - shift,
                        float(np.float32(vertical_root_z)) + math.sqrt(3) * shift,
                    ]
                ]
            ),
        ]
    return np.r_[
        np.array([[back - shift, h_plane]]),
        arc,
        np.array(
            [
                [roof_y, top_plane],
                [body_roof_y - shift, top_plane],
                [back - shift, knee_plane],
            ]
        ),
    ]


def _rear_lid_field(p, center):
    from .mesh_generator import np, _polygon_prism_field

    q = rugged_dimensions(p)
    h, cy, back = q["base_height"], q["depth"] / 2 + 4.75, q["depth"] / 2
    lo, hi = center - 10.75, center + 10.75
    profile = _rear_lid_profile(p, True)
    root_polygon = np.array([profile[0], [cy, h], profile[34], *profile[35:]])
    root_field = _polygon_prism_field(root_polygon, lo, hi)

    def field(points):
        points = np.asarray(points)
        # The central root slot makes two flexible mounting roots. It removes
        # only the fitting: the lid shell remains intact behind the opening.
        slot = (
            np.abs(points[:, 0] - center)
            - 2.75
            - np.maximum(0, (points[:, 1] - (back + 0.5)) / 3)
        )
        barrel = np.maximum.reduce(
            (
                np.linalg.norm(points[:, 1:] - [cy, h], axis=1) - 4.5,
                lo - points[:, 0],
                points[:, 0] - hi,
            )
        )
        support = np.maximum(np.minimum(root_field(points), barrel), -slot)
        left = np.maximum(
            np.linalg.norm(points - [center - 7, cy, h], axis=1) - 5,
            points[:, 0] - lo - 0.02,
        )
        right = np.maximum(
            np.linalg.norm(points - [center + 7, cy, h], axis=1) - 5,
            hi - points[:, 0] - 0.02,
        )
        return np.minimum.reduce((support, left, right))

    return field


def _insert_profile_events(profile, y_events=(), z_events=()):
    from .mesh_generator import np

    result = []
    for a, b in zip(profile, np.roll(profile, -1, axis=0)):
        cuts = [0.0]
        for axis, values in ((0, y_events), (1, z_events)):
            if abs(b[axis] - a[axis]) > 1e-12:
                cuts.extend(
                    (value - a[axis]) / (b[axis] - a[axis])
                    for value in values
                    if min(a[axis], b[axis]) < value < max(a[axis], b[axis])
                )
        result.extend(a + t * (b - a) for t in sorted(set(cuts)))
    return np.asarray(result)


def _rear_lid_foot(p, center, right=False, z_events=()):
    from .mesh_generator import np

    q = rugged_dimensions(p)
    h, top = q["base_height"], q["height_closed"]
    vertical_end = h + 17.22724133595217
    end = vertical_end if vertical_end <= top - 10 else top
    zs = sorted(
        set([h, end] + [float(z) for z in [top - 10, *z_events] if h < z < end])
    )
    lo, hi = center - 10.75, center - 2.75
    result = [
        [lo, float(rugged_outer_body_y(p, "lid", 2, h)), h],
        [hi, float(rugged_outer_body_y(p, "lid", 2, h)), h],
    ]
    result.extend([hi, float(rugged_outer_body_y(p, "lid", 2, z)), z] for z in zs[1:])
    result.extend(
        [lo, float(rugged_outer_body_y(p, "lid", 2, z)), z] for z in zs[:0:-1]
    )
    loop = np.asarray(result)
    if right:
        loop[:, 0] = 2 * center - loop[:, 0]
        loop = loop[::-1]
    return loop


def _append_rear_lid_arm(builder, p, center, z_events=(), close_back=False):
    """One analytic flex arm, spherical journal and its drafted inside face.

    Its end face is partitioned into an annulus and a simple brace contour.
    Those disjoint patches share the outer-circle seam; no polygon-with-hole
    triangulation, Boolean volume overlay, or voxel extraction is required.
    """
    from .mesh_generator import np

    q = rugged_dimensions(p)
    h, back = q["base_height"], q["depth"] / 2
    cy, radius, draft_y = back + 4.75, 4.5, back + 0.5
    lo, inner, sx = center - 10.75, center - 2.75, center - 7
    cut_angle = math.acos((draft_y - cy) / radius)
    angles = np.unique(
        np.r_[
            np.arange(48) * 2 * math.pi / 48,
            math.pi / 6,
            math.pi,
            cut_angle,
            2 * math.pi - cut_angle,
        ]
    )
    circle = np.column_stack(
        (cy + radius * np.cos(angles), h + radius * np.sin(angles))
    )
    lower_angles = np.r_[
        angles[angles >= math.pi], angles[angles <= math.pi / 6] + 2 * math.pi
    ]
    arc = np.column_stack(
        (cy + radius * np.cos(lower_angles), h + radius * np.sin(lower_angles))
    )
    tail = _rear_lid_profile(p)[35:]
    profile = np.r_[np.array([[back, h]]), arc, tail]
    profile = _insert_profile_events(profile, [draft_y], z_events)
    end_x = lambda y: inner - max(0, (y - draft_y) / 3)

    def attachment(a, b):
        return (
            abs(a[0] - float(rugged_outer_body_y(p, "lid", 2, a[1]))) < 1e-7
            and abs(b[0] - float(rugged_outer_body_y(p, "lid", 2, b[1]))) < 1e-7
        )

    for a, b in zip(profile, np.roll(profile, -1, axis=0)):
        if not close_back and attachment(a, b):
            continue
        builder.quad([lo, *a], [lo, *b], [end_x(b[0]), *b], [end_x(a[0]), *a])
    for above in (False, True):
        face = _clip_profile_y(profile, draft_y, above)
        _face_polygon(builder, [[end_x(y), y, z] for y, z in face])
    # Outer end: full annulus around the journal's base circle.
    base_r = math.sqrt(25 - (lo - sx) ** 2)
    outer = np.column_stack((np.full(len(angles), lo), circle))
    inner_circle = np.column_stack(
        (
            np.full(len(angles), lo),
            cy + base_r * np.cos(angles),
            h + base_r * np.sin(angles),
        )
    )
    builder.join(outer, inner_circle, True)
    upper_angles = angles[(angles >= math.pi / 6) & (angles <= math.pi)][::-1]
    # Brace outside the circle, preserving all wall/roof attachment events.
    brace = np.r_[
        np.array([[cy + radius * math.cos(math.pi / 6), h + radius / 2]]),
        tail,
        np.array([[back, h]]),
        np.column_stack(
            (cy + radius * np.cos(upper_angles), h + radius * np.sin(upper_angles))
        ),
    ]
    brace = _insert_profile_events(brace, [draft_y], z_events)
    _face_polygon(builder, np.column_stack((np.full(len(brace), lo), brace)), True)
    # The sphere extends outward, and joins exactly the annulus's inner seam.
    polar = np.linspace(math.acos((sx - lo) / 5), 0, 7)
    rings = [
        np.column_stack(
            (
                np.full(len(angles), sx - 5 * math.cos(phi)),
                cy + 5 * math.sin(phi) * np.cos(angles),
                h + 5 * math.sin(phi) * np.sin(angles),
            )
        )
        for phi in polar[:-1]
    ]
    for a, b in zip(rings, rings[1:]):
        builder.join(a, b, True)
    tip = [sx - 5, cy, h]
    for a, b in zip(rings[-1], np.roll(rings[-1], -1, axis=0)):
        builder.triangle(a, b, tip, True)


class _ReflectedBoundary:
    """Reflect raw patch coordinates before the single final float32 weld."""

    def __init__(self, target, center):
        self.target, self.center = target, center

    def point(self, point):
        return [2 * self.center - point[0], point[1], point[2]]

    def triangle(self, a, b, c, reverse=False):
        self.target.triangle(self.point(a), self.point(b), self.point(c), not reverse)

    def quad(self, a, b, c, d, reverse=False):
        self.triangle(a, b, c, reverse)
        self.triangle(a, c, d, reverse)

    def join(self, a, b, reverse=False):
        for i in range(len(a)):
            j = (i + 1) % len(a)
            self.quad(a[i], a[j], b[j], b[i], reverse)


def _generate_rear_only_mesh(p, part):
    """Development boundary proof of the shell and its rear fittings."""
    q = rugged_dimensions(p)
    if part == "base":
        _, root, _ = _rear_profile(p)
        ac = rugged_hinge_geometry(p)["axial_clearance"]
        attachments = [
            (2, center + a, center + b, root, q["base_height"])
            for center in q["fitting_centers"]
            for a, b in ((-19, -10.75 - ac), (10.75 + ac, 19))
        ]
        builder = _body_builder(p, part, attachments)
        for center in q["fitting_centers"]:
            for target in (builder, _ReflectedBoundary(builder, center)):
                _append_rear_socket(
                    target, p, center - 19, center - 10.75 - ac, center - 7
                )
    elif part == "lid":
        feet = [
            _rear_lid_foot(p, center, right)
            for center in q["fitting_centers"]
            for right in (False, True)
        ]
        builder = _body_builder(p, part, omit_sides=(2,), foot_loops={2: feet})
        _append_panel_with_feet(builder, p, part, 2, feet)
        levels = [float(v[2]) for loop in feet for v in loop]
        for center in q["fitting_centers"]:
            for target in (builder, _ReflectedBoundary(builder, center)):
                _append_rear_lid_arm(target, p, center, levels)
    else:
        raise ValueError("Use base/lid")
    return builder.mesh(part, min(q["clearance"] / 4, 0.025))


def _mesh_join_patches(builder, patches, part, tolerance):
    """Bulk-weld open fitting boundaries to the analytic shell exactly once."""
    from .mesh_generator import np, MeshData, _unique_xyz_indices

    arrays = [np.asarray(builder.vertices, dtype=np.float32)]
    faces = [np.asarray(builder.faces, dtype=np.int32)]
    offset = len(arrays[0])
    for patch in patches:
        vertices = patch["vertices"]
        triangles = patch["triangles"][~patch["cap_triangles"]]
        arrays.append(vertices)
        faces.append(triangles + offset)
        offset += len(vertices)
    vertices = np.concatenate(arrays)
    triangles = np.concatenate(faces)
    first, inverse = _unique_xyz_indices(vertices)
    vertices = vertices[first]
    triangles = inverse[triangles].astype(np.int32)
    used, inverse = np.unique(triangles, return_inverse=True)
    vertices = vertices[used]
    triangles = inverse.reshape(-1, 3).astype(np.int32)
    xyz = vertices[triangles].astype(float)
    cross = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    length = np.linalg.norm(cross, axis=1)
    if np.any(length == 0):
        raise ValueError("Degenerate joined boundary / emenda degenerada.")
    volume = float(
        np.einsum("ij,ij->i", xyz[:, 0], np.cross(xyz[:, 1], xyz[:, 2])).sum() / 6000
    )
    if volume <= 0:
        raise ValueError(
            "Joined boundary orientation is invalid / orientação inválida."
        )
    lo, hi = vertices.min(0), vertices.max(0)
    return MeshData(
        vertices,
        triangles,
        (cross / length[:, None]).astype(np.float32),
        {"min": lo.tolist(), "max": hi.tolist(), "size": (hi - lo).tolist()},
        volume,
        part,
        tolerance,
    )


def _generate_patched_mesh(p, part):
    from .rugged_front_mesh import generate_front_patch

    q = rugged_dimensions(p)
    patches = [
        generate_front_patch(p, part, center, side)
        for center in q["fitting_centers"]
        for side in (-1, 1)
    ]
    front_feet = [loop for patch in patches for loop in patch["foot_loops"]]
    if part == "base":
        _, root, _ = _rear_profile(p)
        ac = rugged_hinge_geometry(p)["axial_clearance"]
        rear_feet = []
        for center in q["fitting_centers"]:
            for lo, hi in (
                (center - 19, center - 10.75 - ac),
                (center + 10.75 + ac, center + 19),
            ):
                rear_feet.append(
                    [
                        [lo, q["depth"] / 2, root],
                        [hi, q["depth"] / 2, root],
                        [hi, q["depth"] / 2, q["base_height"]],
                        [lo, q["depth"] / 2, q["base_height"]],
                    ]
                )
    else:
        rear_feet = [
            _rear_lid_foot(p, center, right)
            for center in q["fitting_centers"]
            for right in (False, True)
        ]
    feet = {0: front_feet, 2: rear_feet}
    builder = _body_builder(
        p, part, omit_sides=(0, 2), foot_loops=feet, local_panel_seams=True
    )
    for side in (0, 2):
        _append_panel_with_feet(builder, p, part, side, feet[side])
    for center in q["fitting_centers"]:
        for target in (builder, _ReflectedBoundary(builder, center)):
            if part == "base":
                _append_rear_socket(
                    target, p, center - 19, center - 10.75 - ac, center - 7
                )
            else:
                _append_rear_lid_arm(target, p, center)
    return _mesh_join_patches(builder, patches, part, min(q["clearance"] / 4, 0.025))


def _rear_base_fields(p):
    from .mesh_generator import np

    q = rugged_dimensions(p)
    ac = rugged_hinge_geometry(p)["axial_clearance"]
    fields = []
    for center in q["fitting_centers"]:
        left = _rear_socket_field(p, center - 19, center - 10.75 - ac, center - 7, True)
        fields.append(left)

        def mirrored(points, source=left, cx=center):
            qpoints = np.asarray(points).copy()
            qpoints[:, 0] = 2 * cx - qpoints[:, 0]
            return source(qpoints)

        fields.append(mirrored)
    return fields


def _coalesced_curve_samples(circles, clearance):
    """Unify overlapping curve bands without increasing any sampling pitch.

    Independent lattices across the same interval multiply tensor-grid nodes.
    Every original circle extremum and center is retained, and every merged
    interval uses the smallest pitch requested by any constituent circle.
    """
    from .mesh_generator import np

    tolerance = min(clearance / 4, 0.04)
    bands = [[], [], []]
    events = [[], [], []]
    for a, b, ca, cb, radius in circles:
        step = max(0.04, min(0.3, math.sqrt(4 * radius * tolerance) * 0.5))
        for axis, center in ((a, ca), (b, cb)):
            bands[axis].append((center - radius, center + radius, step))
            events[axis].extend([center - radius, center, center + radius])
    for axis in range(3):
        merged = []
        for lo, hi, step in sorted(bands[axis]):
            if merged and lo <= merged[-1][1]:
                prior_lo, prior_hi, prior_step = merged[-1]
                merged[-1] = (prior_lo, max(hi, prior_hi), min(step, prior_step))
            else:
                merged.append((lo, hi, step))
        for lo, hi, step in merged:
            events[axis].extend(
                np.linspace(lo, hi, math.ceil((hi - lo) / step) + 1).tolist()
            )
    return events


def rugged_part_field(p, part):
    """Return the analytic signed field, conservative bounds, and mesh hints."""
    from .mesh_generator import np

    if part in ("clip_left", "clip_right"):
        from .rugged_latch_geometry import rugged_latch_field

        field = rugged_latch_field(p, part)
        q = rugged_dimensions(p)
        pivot = rugged_latch_geometry(p, part)["pivot"]
        bounds = (
            pivot["x"] - 14.1,
            pivot["x"] + 14.1,
            pivot["y"] - 3.1,
            pivot["y"] + 3.1,
            q["base_height"] - 20.1,
            pivot["z"] + 3.1,
        )
        return field, bounds, {}
    if part not in ("base", "lid"):
        raise ValueError(
            "Caixa usa base/tampa/duas travas / box uses base/lid/two latches."
        )
    from .rugged_front_geometry import front_fittings_field, front_socket_field

    q = rugged_dimensions(p)
    body = _body_field(p, part)
    rear = (
        _rear_base_fields(p)
        if part == "base"
        else [_rear_lid_field(p, center) for center in q["fitting_centers"]]
    )
    front, cut = front_fittings_field(p, part), front_socket_field(p, part)

    def field(points):
        solid = np.minimum.reduce(
            [body(points), front(points), *[f(points) for f in rear]]
        )
        return np.maximum(solid, -cut(points))

    w, d, h, lh, t, f, r, c = (
        q[k]
        for k in (
            "width",
            "depth",
            "base_height",
            "lid_height",
            "wall",
            "floor",
            "radius",
            "clearance",
        )
    )
    bounds = (
        -w / 2 - 0.3,
        w / 2 + 0.3,
        -d / 2 - 8.3,
        d / 2 + 9.55,
        -0.3 if part == "base" else h - 4.8,
        h + 4.8 if part == "base" else h + lh + 0.3,
    )
    params = dict(p)
    params.setdefault("quality", "standard")
    params.setdefault("dividers_x", [])
    params.setdefault("dividers_y", [])
    levels = [
        0,
        f,
        10,
        10 + t * (2 - math.sqrt(3)),
        h - 0.85,
        h,
        h - 4.5,
        h + 4.5,
        h + lh - 10,
        h + lh - f,
        h + lh,
    ]
    circles = []
    planes = [[], [], list(levels)]
    cy = d / 2 + 4.75
    for center in q["fitting_centers"]:
        planes[0].extend(
            [
                center + x
                for x in (
                    (-19, -11, 11, 19)
                    if part == "base"
                    else (-12, -10.75, -2.75, 2.75, 10.75, 12)
                )
            ]
        )
        circles.append((1, 2, cy, h, 5.125))
        for ball_x in (center - 7, center + 7):
            circles.append((0, 1, ball_x, cy, 5.125))
    try:
        from .rugged_front_geometry import front_refinement_hints

        extra = front_refinement_hints(p, part)
        levels.extend(extra.get("levels", []))
        circles.extend(extra.get("circles", []))
        for axis in range(3):
            planes[axis].extend(extra.get("planes", [[], [], []])[axis])
    except ImportError:
        pass
    samples = _coalesced_curve_samples(circles, c)
    bevel_lo, bevel_hi = (
        (0, 10 + t * (2 - math.sqrt(3)))
        if part == "base"
        else (h + lh - 10 - t * (2 - math.sqrt(3)), h + lh)
    )
    # A sloped thin wall must persist between layers, not jump several XY cells
    # across the default 20 mm general-Z slab.
    samples[2].extend(
        np.linspace(
            bevel_lo, bevel_hi, math.ceil((bevel_hi - bevel_lo) / 0.8) + 1
        ).tolist()
    )
    hints = {
        "params": params,
        "levels": levels,
        "rectangles": [(w, d, r), (w - 2 * t, d - 2 * t, r - t)],
        "circles": [],
        "planes": planes,
        "sample_x": samples[0],
        "sample_y": samples[1],
        "sample_z": samples[2],
    }
    return field, bounds, hints


def generate_rugged_mesh(p, part="base"):
    """Build the welded analytic shell, fitting graphs and captive rear journals."""
    if part in ("clip_left", "clip_right"):
        from .rugged_latch_geometry import generate_rugged_latch

        return generate_rugged_latch(p, part)
    if part not in ("base", "lid"):
        raise ValueError("Use base/tampa/travas / use base/lid/latches.")
    return _generate_patched_mesh(p, part)
