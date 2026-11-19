"""NumPy implicit CSG and conforming tetrahedral surface extraction.

Primitives are evaluated analytically. Triangles approximate curved surfaces; local
axis refinement bounds interface chord error below min(clearance/4, 0.04 mm).
Unions are evaluated before meshing: posts/ribs/dividers share one boundary.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
import math
from contextvars import ContextVar

try:
    import numpy as np
except ModuleNotFoundError:
    import os, sys
    from pathlib import Path

    _pkgroot = (
        Path(os.environ.get("APPDATA", "")) / "OrcaSlicer"
        if sys.platform == "win32"
        else Path.home() / "Library/Application Support/OrcaSlicer"
        if sys.platform == "darwin"
        else Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        / "OrcaSlicer"
    )
    sys.path.insert(
        0,
        str(
            _pkgroot
            / "python/packages"
            / f"cp{sys.version_info.major}{sys.version_info.minor}"
        ),
    )
    import numpy as np
from .schema import normalize_params, validate_params


@dataclass
class MeshData:
    vertices: np.ndarray
    triangles: np.ndarray
    face_normals: np.ndarray
    bounds_mm: dict[str, list[float]]
    volume_cm3: float
    part: str = ""
    interface_error_mm: float = 0.0


Field = Callable[[np.ndarray], np.ndarray]
_GEOMETRY_HINTS: ContextVar[dict[str, Any] | None] = ContextVar(
    "box_geometry_hints", default=None
)


def _planes(axis: int, *values: float) -> None:
    registry = _GEOMETRY_HINTS.get()
    if registry is not None:
        registry["planes"][axis].extend(values)


def _slab(v: np.ndarray, low: float, high: float) -> np.ndarray:
    return np.maximum(low - v, v - high)


def _round2(a: np.ndarray, b: np.ndarray, ha: float, hb: float, r: float) -> np.ndarray:
    radius = min(r, ha, hb)
    qa, qb = np.abs(a) - ha + radius, np.abs(b) - hb + radius
    return (
        np.hypot(np.maximum(qa, 0), np.maximum(qb, 0))
        + np.minimum(np.maximum(qa, qb), 0)
        - radius
    )


def _rect(
    w: float,
    d: float,
    z0: float,
    z1: float,
    r: float = 0.2,
    cx: float = 0,
    cy: float = 0,
) -> Field:
    registry = _GEOMETRY_HINTS.get()
    if registry is not None:
        _planes(0, cx - w / 2, cx + w / 2)
        _planes(1, cy - d / 2, cy + d / 2)
        _planes(2, z0, z1)
        registry["rectangles"].append((w, d, r, cx, cy))
    return lambda v: np.maximum(
        _round2(v[:, 0] - cx, v[:, 1] - cy, w / 2, d / 2, r), _slab(v[:, 2], z0, z1)
    )


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Field:
    _planes(0, x0, x1)
    _planes(1, y0, y1)
    _planes(2, z0, z1)
    return lambda v: np.maximum.reduce(
        (_slab(v[:, 0], x0, x1), _slab(v[:, 1], y0, y1), _slab(v[:, 2], z0, z1))
    )


def _cylinder(cx: float, cy: float, r: float, z0: float, z1: float) -> Field:
    registry = _GEOMETRY_HINTS.get()
    if registry is not None:
        registry["circles"].append((0, 1, cx, cy, r))
    _planes(2, z0, z1)
    return lambda v: np.maximum(
        np.hypot(v[:, 0] - cx, v[:, 1] - cy) - r, _slab(v[:, 2], z0, z1)
    )


def _cylinder_x(x0: float, x1: float, cy: float, cz: float, r: float) -> Field:
    registry = _GEOMETRY_HINTS.get()
    if registry is not None:
        registry["circles"].append((1, 2, cy, cz, r))
    _planes(0, x0, x1)
    return lambda v: np.maximum(
        np.hypot(v[:, 1] - cy, v[:, 2] - cz) - r, _slab(v[:, 0], x0, x1)
    )


def _union(*fs: Field) -> Field:
    def field(v: np.ndarray) -> np.ndarray:
        result = fs[0](v)
        for f in fs[1:]:
            result = np.minimum(result, f(v))
        return result

    return field


def _difference(a: Field, *bs: Field) -> Field:
    def field(v: np.ndarray) -> np.ndarray:
        result = a(v)
        for b in bs:
            result = np.maximum(result, -b(v))
        return result

    return field


def _ring(w: float, d: float, z0: float, z1: float, t: float, r: float) -> Field:
    return _difference(
        _rect(w, d, z0, z1, r),
        _rect(w - 2 * t, d - 2 * t, z0 - 2, z1 + 2, max(0.15, r - t)),
    )


def _loft_rect_field(a: tuple, b: tuple) -> Field:
    """Analytic linear loft between concentric rounded rectangle sections."""
    z0, w0, d0, r0 = a
    z1, w1, d1, r1 = b

    def field(v):
        u = np.clip((v[:, 2] - z0) / (z1 - z0), 0, 1)
        w, d, radius = w0 + (w1 - w0) * u, d0 + (d1 - d0) * u, r0 + (r1 - r0) * u
        radius = np.minimum(radius, np.minimum(w, d) * 0.475)
        qx, qy = np.abs(v[:, 0]) - w / 2 + radius, np.abs(v[:, 1]) - d / 2 + radius
        cross = (
            np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
            + np.minimum(np.maximum(qx, qy), 0)
            - radius
        )
        return np.maximum(cross, _slab(v[:, 2], z0, z1))

    return field


def _lip_outer_profile(p):
    w, d, h, t, c, r = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "fit_clearance",
            "corner_radius",
        )
    )
    sw, sd, sr = w - 2 * t - 2 * c, d - 2 * t - 2 * c, max(0.2, r - t - c)
    z = h - p["lip_depth"]
    retention = p["snap_retention"]
    # The lower chamfer starts the skirt freely; the bead ramps outward before
    # its flat retaining shoulder. Retention and dimensional clearance differ.
    chamfer = min(0.6, p["lip_depth"] - 2.9, (sw - 2.4) / 8, (sd - 2.4) / 8)
    return [
        (z, sw - 2 * chamfer, sd - 2 * chamfer, max(0.15, sr - chamfer)),
        (z + chamfer, sw, sd, sr),
        (h - 2.85, sw, sd, sr),
        (
            h - 2.25,
            w - 2 * t + 2 * retention,
            d - 2 * t + 2 * retention,
            max(0.2, r - t + retention),
        ),
        (
            h - 2.20,
            w - 2 * t + 2 * retention,
            d - 2 * t + 2 * retention,
            max(0.2, r - t + retention),
        ),
        (h - 2.20, sw, sd, sr),
        (h + c, sw, sd, sr),
    ]


def _corner_centers(p: dict[str, Any]) -> list[tuple[float, float]]:
    w, d, t = (p[k] for k in ("width_x", "depth_y", "wall_thickness"))
    return [
        (sx * (w / 2 - t - 2.2), sy * (d / 2 - t - 2.2))
        for sx in (-1, 1)
        for sy in (-1, 1)
    ]


def hinge_geometry(p: dict[str, Any]) -> dict[str, Any]:
    if p.get("style") == "rugged_box":
        from .rugged_geometry import rugged_hinge_geometry

        return rugged_hinge_geometry(p)
    if p.get("style") == "clamshell_pip":
        radius = p["hinge_pin_diameter"] / 2
        return {
            "y": p["depth_y"] / 2 + p["hinge_separation"],
            "z": p["height_z"] + p["fit_clearance"] / 2,
            "radius": radius,
            "outer_radius": radius + p["pip_clearance"] + 1.4,
            "knuckle_length": max(4.0, min(6.0, p["width_x"] * 0.06)),
            "centers": [-p["width_x"] * 0.26, p["width_x"] * 0.26],
        }
    return {
        "y": p["depth_y"] / 2 + 5.0,
        "z": p["height_z"] - 4.0,
        "radius": p["hinge_pin_diameter"] / 2,
        "outer_radius": p["hinge_pin_diameter"] / 2 + 2.2,
        "span": p["width_x"] * 0.64,
        "knuckle_length": max(5.0, min(12.0, p["width_x"] * 0.13)),
    }


def clamshell_open_transform(
    vertices: np.ndarray, raw: dict[str, Any], angle: float = 180.0
) -> np.ndarray:
    """Rotate the canonical closed lid about the actual hinge, without mutation."""
    p = normalize_params(raw)
    if p["style"] != "clamshell_pip" or not math.isfinite(float(angle)):
        raise ValueError(
            "Use um estojo articulado e ângulo finito / use an articulated case and finite angle."
        )
    hg = hinge_geometry(p)
    theta = -math.radians(float(angle))
    cosine, sine = math.cos(theta), math.sin(theta)
    v = np.asarray(vertices, dtype=np.float64).copy()
    dy, dz = v[:, 1] - hg["y"], v[:, 2] - hg["z"]
    v[:, 1] = hg["y"] + dy * cosine - dz * sine
    v[:, 2] = hg["z"] + dy * sine + dz * cosine
    v[np.abs(v) < 1e-10] = 0.0
    if math.isclose(float(angle), 180.0, rel_tol=0, abs_tol=1e-10):
        # Canonical meshes are float32. Snap only the analytically zero floor
        # plane, avoiding a few microns of negative round-off on the print bed.
        v[np.abs(v[:, 2]) < 3e-5, 2] = 0.0
    return v


def clamshell_print_bounds(raw: dict[str, Any]) -> dict[str, list[float]]:
    """Analytic bounds of the open, captive assembly; no tessellation required."""
    p = normalize_params(raw)
    errors = validate_params(p)
    if p["style"] != "clamshell_pip" or errors:
        raise ValueError(
            "Estojo inválido / invalid articulated case. " + "; ".join(errors)
        )
    hg = hinge_geometry(p)
    low = [-p["width_x"] / 2, -p["depth_y"] / 2, 0.0]
    high = [
        p["width_x"] / 2,
        3 * p["depth_y"] / 2 + 2 * p["hinge_separation"],
        hg["z"] + hg["outer_radius"],
    ]
    return {"min": low, "max": high, "size": [b - a for a, b in zip(low, high)]}


def stacking_pose_z(
    raw_lower: dict[str, Any], raw_upper: dict[str, Any] | None = None
) -> float:
    """Bottom Z of the upper bin when its shoulders rest on the lower U rim.

    height_z includes the foot. Heights and front access may differ; matching
    exterior dimensions, wall/radius and guide parameters define a family.
    This is geometric compatibility, not a physical load or print certification.
    """
    lower = normalize_params(raw_lower)
    upper = normalize_params(raw_upper if raw_upper is not None else raw_lower)
    for p in (lower, upper):
        errors = validate_params(p)
        if p["style"] != "stackable_bin" or errors:
            raise ValueError(
                "Use caixas empilháveis válidas / use valid stackable bins. "
                + "; ".join(errors)
            )
    for key in (
        "width_x",
        "depth_y",
        "corner_radius",
        "wall_thickness",
        "stack_foot_height",
        "stack_clearance",
    ):
        if not math.isclose(lower[key], upper[key], rel_tol=0, abs_tol=1e-6):
            raise ValueError(
                "Famílias de empilhamento incompatíveis / incompatible stacking family: "
                + key
            )
    return lower["height_z"] - upper["stack_foot_height"]


def _stack_front_top(p, x):
    half = p["front_access_width"] / 2
    ramp = min(4.0, p["front_access_width"] / 4, p["front_access_drop"] / 2)
    return (
        p["height_z"]
        - p["front_access_drop"]
        + np.clip((np.abs(x) - (half - ramp)) / ramp, 0, 1) * p["front_access_drop"]
    )


def _clamshell_spans(p, part):
    return [(a, b) for a, b, _ in _clamshell_knuckles(p, part)]


def _clamshell_knuckles(p, part):
    hg = hinge_geometry(p)
    k = hg["knuckle_length"]
    pc = p["pip_clearance"]
    if part == "base":
        return [
            (
                cx + side * (k + pc) - k / 2,
                cx + side * (k + pc) + k / 2,
                hg["outer_radius"],
            )
            for cx in hg["centers"]
            for side in (-1, 1)
        ]
    end = 1.5 * k + 2 * pc
    capr = hg["radius"] + pc + 0.8
    return [
        profile
        for cx in hg["centers"]
        for profile in (
            (cx - end - 1.2, cx - end, capr),
            (cx - k / 2, cx + k / 2, hg["outer_radius"]),
            (cx + end, cx + end + 1.2, capr),
        )
    ]


def _build_clamshell_field(p, part):
    if part not in ("base", "lid"):
        _GEOMETRY_HINTS.set(None)
        raise ValueError(
            "Estojo articulado usa apenas duas metades cativas / articulated case has only two captive halves."
        )
    hg = hinge_geometry(p)
    w, d, h, t, f, r = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "floor_thickness",
            "corner_radius",
        )
    )
    cy, cz, R, pr, k = (
        hg[key] for key in ("y", "z", "outer_radius", "radius", "knuckle_length")
    )
    pc = p["pip_clearance"]
    zlo, zhi = 0.0, cz - 0.1 * R
    solid = _difference(
        _rect(w, d, 0, h, r), _rect(w - 2 * t, d - 2 * t, f, h + 1, max(0.15, r - t))
    )
    additions = []
    for a, b, rr in _clamshell_knuckles(p, part):
        additions.extend(
            (
                _cylinder_x(a, b, cy, cz, rr),
                _box(a, b, d / 2 - 0.1, cy, 0.0, cz - 0.1 * rr),
            )
        )
    solid = _union(solid, *additions)
    if part == "base":
        for a, b in _clamshell_spans(p, part):
            solid = _difference(solid, _cylinder_x(a - 0.1, b + 0.1, cy, cz, pr + pc))
    else:
        for cx in hg["centers"]:
            end = 1.5 * k + 2 * pc
            solid = _union(
                solid,
                _cylinder_x(cx - end - 1.2, cx + end + 1.2, cy, cz, pr),
            )
    registry = _GEOMETRY_HINTS.get() or {
        "planes": [[], [], []],
        "circles": [],
        "rectangles": [],
    }
    _GEOMETRY_HINTS.set(None)
    if part == "lid":
        upright = solid

        def mirrored(v):
            query = v.copy()
            query[:, 2] = 2 * h + p["fit_clearance"] - v[:, 2]
            return upright(query)

        solid = mirrored
    lowz = 0 if part == "base" else min(h + p["fit_clearance"], cz - R)
    highz = max(h, cz + R) if part == "base" else 2 * h + p["fit_clearance"]
    bounds = (-w / 2 - 1, w / 2 + 1, -d / 2 - 1, cy + R + 1, lowz - 1, highz + 1)
    hints = {**registry, "levels": [0, f, h, zlo, zhi, cz - R, cz + R], "params": p}
    return solid, bounds, hints


def build_part_field(
    raw: dict[str, Any], part: str = "base"
) -> tuple[Field, tuple[float, ...], dict[str, Any]]:
    """Return one unified printable solid in assembled coordinates and refinement hints."""
    p = normalize_params(raw)
    errors = validate_params(p)
    if errors:
        raise ValueError("\n".join(errors))
    if p["style"] == "rugged_box":
        from .rugged_geometry import rugged_part_field

        return rugged_part_field(p, part)
    registry = {"planes": [[], [], []], "circles": [], "rectangles": []}
    _GEOMETRY_HINTS.set(registry)
    w, d, h, t, f, c, lh, r = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "floor_thickness",
            "fit_clearance",
            "lid_height",
            "corner_radius",
        )
    )
    style = p["style"]
    if style == "snap_latch" and part in ("base", "lid", "clip_left", "clip_right"):
        return _build_snap_latch_field(p, part)
    if style == "clamshell_pip":
        return _build_clamshell_field(p, part)
    if style in ("open_bin", "stackable_bin") and part != "base":
        raise ValueError(
            "Caixa aberta tem apenas base / open bin has no lid or fit kit."
        )
    zcap = h + c
    circles: list[tuple[int, int, float, float, float]] = []
    rectangles: list[tuple[float, float, float]] = [
        (w, d, r),
        (w - 2 * t, d - 2 * t, max(0.15, r - t)),
    ]
    levels = []
    bounds = (-w / 2 - 2, w / 2 + 2, -d / 2 - 2, d / 2 + 2, -2, h + c + lh + 2)
    if part == "base":
        foot = p["stack_foot_height"] if style == "stackable_bin" else 0.0
        if foot:
            f += foot
        result = _difference(
            _rect(w, d, foot, h, r),
            _rect(w - 2 * t, d - 2 * t, f, h + 3, max(0.15, r - t)),
        )
        if style == "stackable_bin":
            sc = p["stack_clearance"]
            result = _union(
                result,
                _rect(
                    w - 2 * t - 2 * sc,
                    d - 2 * t - 2 * sc,
                    0,
                    foot + 0.1,
                    max(0.2, r - t - sc),
                ),
            )
        additions = []
        for x in p["dividers_x"]:
            additions.append(
                _box(
                    x - t / 2,
                    x + t / 2,
                    -d / 2 + t - 0.2,
                    d / 2 - t + 0.2,
                    f - 0.2,
                    h - (foot + 0.2 if foot else p["lip_depth"]) - 1,
                )
            )
        for y in p["dividers_y"]:
            additions.append(
                _box(
                    -w / 2 + t - 0.2,
                    w / 2 - t + 0.2,
                    y - t / 2,
                    y + t / 2,
                    f - 0.2,
                    h - (foot + 0.2 if foot else p["lip_depth"]) - 1,
                )
            )
        for s in p["standoffs"]:
            x, y = s["x"], s["y"]
            additions.append(
                _difference(
                    _cylinder(x, y, s["outer_diameter"] / 2, f - 0.2, f + s["height"]),
                    _cylinder(
                        x,
                        y,
                        s["hole_diameter"] / 2,
                        f + s["height"] - s["hole_depth"],
                        f + s["height"] + 1,
                    ),
                )
            )
            circles.extend(
                [
                    (0, 1, x, y, s["outer_diameter"] / 2),
                    (0, 1, x, y, s["hole_diameter"] / 2),
                ]
            )
            levels.extend([f + s["height"], f + s["height"] - s["hole_depth"]])
        if style == "screw_corner":
            for x, y in _corner_centers(p):
                cr = max(4.2, p["screw_diameter"] / 2 + 2.4)
                additions.append(
                    _difference(
                        _cylinder(x, y, cr, f - 0.2, h),
                        _cylinder(
                            x, y, p["screw_diameter"] / 2 - 0.2, max(1.2, h - 9), h + 1
                        ),
                    )
                )
                circles.extend(
                    [(0, 1, x, y, cr), (0, 1, x, y, p["screw_diameter"] / 2 - 0.2)]
                )
            levels.append(h - 9)
        result = _union(result, *additions)
        if style == "stackable_bin":

            def access(v):
                return np.maximum.reduce(
                    (
                        np.abs(v[:, 0]) - p["front_access_width"] / 2,
                        _stack_front_top(p, v[:, 0]) - v[:, 2],
                        v[:, 2] - (h + 1),
                        _slab(v[:, 1], -d / 2 - 1, -d / 2 + t + 0.5),
                    )
                )

            result = _difference(result, access)
            half = p["front_access_width"] / 2
            ramp = min(4.0, p["front_access_width"] / 4, p["front_access_drop"] / 2)
            _planes(0, -half, -half + ramp, half - ramp, half)
            _planes(1, -d / 2, -d / 2 + t)
            levels.extend([foot, f, h - p["front_access_drop"]])
        if style == "lip_snap":
            relief = p["snap_retention"] + 0.18
            groove = _ring(
                w - 2 * t + 2 * relief,
                d - 2 * t + 2 * relief,
                h - 3.0,
                h - 2.1,
                0.4,
                max(0.2, r - t + relief),
            )
            result = _difference(result, groove)
            rectangles.append(
                (
                    w - 2 * t + 2 * relief,
                    d - 2 * t + 2 * relief,
                    max(0.2, r - t + relief),
                )
            )
        if style == "sliding_lid":
            _planes(0, -w / 2 + t, -w / 2 + t + 1.6, w / 2 - t - 1.6, w / 2 - t)
            _planes(1, -d / 2 + t, d / 2 - t)
            result = _difference(
                result,
                _box(-w / 2 + t, w / 2 - t, -d / 2 - 1, -d / 2 + t + 1, h - 4, h + 2),
            )

            # Female 45-degree dovetail rails, open at the front for insertion.
            def rail(v: np.ndarray) -> np.ndarray:
                intrusion = np.clip(v[:, 2] - (h - 3), 0, 1.6)
                return np.maximum.reduce(
                    (
                        w / 2 - t - intrusion - np.abs(v[:, 0]),
                        np.abs(v[:, 0]) - (w / 2 - t + 0.2),
                        _slab(v[:, 1], -d / 2 + t, d / 2 - t + 0.2),
                        _slab(v[:, 2], h - 3, h - 1.4),
                    )
                )

            result = _union(result, rail)
            # A rear ceiling carries an underside socket. Keeping the mating
            # tooth above the plate leaves the entire lid underside printable
            # on the bed, rather than balancing it on a small downward foot.
            rear = d / 2 - t
            result = _union(result, _box(-2.5, 2.5, rear - 4, rear + 0.2, h - 1.4, h))
            result = _difference(
                result, _box(-1.5, 1.5, rear - 1.7, rear - 0.2, h - 1.6, h - 0.9)
            )
            levels.extend([h - 1.6, h - 1.4, h - 0.9, h - 4, h])
        cuts = list(p["cutouts"])
        if style == "open_bin" and p["handles_enabled"]:
            for face in (
                ("left", "right")
                if p["handle_faces"] == "left_right"
                else ("front", "back")
            ):
                cuts.append(
                    {
                        "face": face,
                        "kind": "handle",
                        "shape": "rounded",
                        "u": 0.0,
                        "z": h - p["handle_top_margin"] - p["handle_height"] / 2,
                        "width": p["handle_width"],
                        "height": p["handle_height"],
                    }
                )
        for cut in cuts:
            face = cut["face"]

            def opening(v: np.ndarray, cut=cut, face=face) -> np.ndarray:
                u = (v[:, 0] if face in ("front", "back") else v[:, 1]) - cut["u"]
                z = v[:, 2] - cut["z"]
                a, b = cut["width"] / 2, cut["height"] / 2
                if cut["shape"] == "circle":
                    cross = np.hypot(u / a, z / b) - 1
                    cross = cross * min(a, b)
                elif cut["shape"] == "hex":
                    # Scale a normalized six-sided envelope independently.
                    # Vertices are (±a,0), (±a/2,±b): controls are actual W/H.
                    cross = (
                        np.maximum(np.abs(u) / a + np.abs(z) / (2 * b), np.abs(z) / b)
                        - 1
                    ) * min(a, b)
                else:
                    cross = _round2(
                        u,
                        z,
                        a,
                        b,
                        min(a, b)
                        if cut.get("kind") == "handle"
                        else min(1.0, a * 0.4, b * 0.4),
                    )
                if face in ("front", "back"):
                    normal = v[:, 1] * (1 if face == "back" else -1)
                    slab = _slab(normal, d / 2 - t - 1, d / 2 + 3)
                else:
                    normal = v[:, 0] * (1 if face == "right" else -1)
                    slab = _slab(normal, w / 2 - t - 1, w / 2 + 3)
                return np.maximum(cross, slab)

            result = _difference(result, opening)
            if cut["shape"] == "hex":
                axis = 0 if face in ("front", "back") else 1
                a, b = cut["width"] / 2, cut["height"] / 2
                _planes(axis, *[cut["u"] + v for v in (-a, -a / 2, a / 2, a)])
                _planes(2, cut["z"] - b, cut["z"], cut["z"] + b)
            if cut["shape"] == "circle":
                circles.append(
                    (
                        0 if face in ("front", "back") else 1,
                        2,
                        cut["u"],
                        cut["z"],
                        min(cut["width"], cut["height"]) / 2,
                    )
                )
            levels.extend([cut["z"] - cut["height"] / 2, cut["z"] + cut["height"] / 2])
            if cut.get("kind") == "handle":
                axis = 0 if face in ("front", "back") else 1
                rad = min(cut["width"], cut["height"]) / 2
                for u in (-cut["width"] / 2 + rad, cut["width"] / 2 - rad):
                    circles.append((axis, 2, u, cut["z"], rad))
                _planes(axis, -cut["width"] / 2, cut["width"] / 2)
        if p["gasket_enabled"]:
            gw, gd = p["gasket_width"], p["gasket_depth"]
            result = _difference(
                result,
                _ring(
                    w - t + gw,
                    d - t + gw,
                    h - gd,
                    h + 1,
                    gw,
                    max(0.2, r - t / 2 + gw / 2),
                ),
            )
            rectangles.extend(
                [
                    (w - t + gw, d - t + gw, max(0.2, r - t / 2 + gw / 2)),
                    (w - t - gw, d - t - gw, max(0.15, r - t / 2 - gw / 2)),
                ]
            )
            levels.append(h - gd)
    elif part == "lid":
        if style == "sliding_lid":
            _planes(
                0,
                -w / 2 + t + c,
                -w / 2 + t + c + 1.6,
                w / 2 - t - c - 1.6,
                w / 2 - t - c,
            )
            _planes(1, -d / 2 + t, d / 2 - t - c)
            _planes(2, h - 3 + c, h - 1.4 - c, h - 3, h - 1.4)

            def slide(v: np.ndarray) -> np.ndarray:
                half = w / 2 - t - c - np.clip(v[:, 2] - (h - 3), 0, 1.6)
                return np.maximum.reduce(
                    (
                        np.abs(v[:, 0]) - half,
                        _slab(v[:, 1], -d / 2 + t, d / 2 - t - c),
                        _slab(v[:, 2], h - 3 + c, h - 1.4 - c),
                    )
                )

            result = _union(
                slide,
                _box(
                    -w / 2 + t + c + 1.6,
                    w / 2 - t - c - 1.6,
                    -d / 2 + t,
                    -d / 2 + t + 2,
                    h - 3 + c,
                    h + 1.2,
                ),
            )
            # A connected 7 mm flexure carries an upward tooth. Its rear ramp
            # enters the ceiling socket; the front shoulder retains withdrawal.
            # Only the tooth flexes down temporarily during insertion/removal.
            rear = d / 2 - t
            result = _difference(
                result,
                _box(-2, -1.2, rear - 7, rear + 0.1, h - 4, h + 1),
                _box(1.2, 2, rear - 7, rear + 0.1, h - 4, h + 1),
            )

            def tooth(v):
                top = (
                    h
                    - 1.05
                    - np.clip((v[:, 1] - (rear - 0.9)) / 0.5, 0, 1) * (0.35 + c)
                )
                return np.maximum.reduce(
                    (
                        np.abs(v[:, 0]) - 1.1,
                        _slab(v[:, 1], rear - 1.5, rear - 0.4),
                        (h - 1.7 - c) - v[:, 2],
                        v[:, 2] - top,
                    )
                )

            result = _union(result, tooth)
            # The rails define the nominal width, while the back corners must
            # also clear the rounded female cavity. Clamp only the rear half;
            # the front opening and pull handle retain their original outline.
            unrelieved = result
            relief_radius = max(0.15, r - t - c)

            def rear_clearance(v):
                return _round2(
                    v[:, 0],
                    np.maximum(v[:, 1], 0),
                    w / 2 - t - c,
                    d / 2 - t - c,
                    relief_radius,
                )

            result = lambda v: np.maximum(unrelieved(v), rear_clearance(v))
            registry["rectangles"].append(
                (w - 2 * t - 2 * c, d - 2 * t - 2 * c, relief_radius, 0.0, 0.0)
            )
            # Sample the curved rear-envelope / 45-degree rail intersection
            # locally through the plate thickness; long Z slabs chamfer it.
            registry["sample_z"] = np.linspace(
                h - 3 + c, h - 1.4 - c, int(math.ceil((1.6 - 2 * c) / 0.1)) + 1
            ).tolist()
            intrusion = np.asarray(registry["sample_z"]) - (h - 3)
            edge = w / 2 - t - c - intrusion
            delta = np.clip(relief_radius - intrusion, 0, relief_radius)
            registry["sample_x"] = np.r_[-edge, edge].tolist()
            registry["sample_y"] = (
                d / 2
                - t
                - c
                - relief_radius
                + np.sqrt(np.maximum(0, relief_radius**2 - delta**2))
            ).tolist()
            _planes(0, -1.1, 1.1)
            _planes(1, rear - 1.5, rear - 0.9, rear - 0.4)
            levels.extend([h - 1.05, h - 1.7 - c, h - 3 + c, h - 1.4 - c, h + 1.2])
        else:
            result = _rect(w, d, zcap, zcap + lh, r)
            skirt = _ring(
                w - 2 * t - 2 * c,
                d - 2 * t - 2 * c,
                h - (p["lid_wall_height"] if style == "snap_latch" else p["lip_depth"]),
                zcap + 0.2,
                1.2,
                max(0.2, r - t - c),
            )
            result = _union(result, skirt)
            rectangles.extend(
                [
                    (w - 2 * t - 2 * c, d - 2 * t - 2 * c, max(0.2, r - t - c)),
                    (
                        w - 2 * t - 2 * c - 2.4,
                        d - 2 * t - 2 * c - 2.4,
                        max(0.15, r - t - c - 1.2),
                    ),
                ]
            )
            if style == "lip_snap":
                profile = _lip_outer_profile(p)
                outer = _union(
                    *[
                        _loft_rect_field(a, b)
                        for a, b in zip(profile, profile[1:])
                        if b[0] > a[0]
                    ]
                )
                inner = _rect(
                    w - 2 * t - 2 * c - 2.4,
                    d - 2 * t - 2 * c - 2.4,
                    h - p["lip_depth"] - 1,
                    zcap + 0.1,
                    max(0.15, r - t - c - 1.2),
                )
                result = _union(
                    _rect(w, d, zcap, zcap + lh, r), _difference(outer, inner)
                )
                for z, pw, pd, pr in profile:
                    _rect(pw, pd, z, z + 0.001, pr)
                    levels.append(z)
            if style == "screw_corner":
                # Relieve skirt around bosses: the four screw posts are continuous to the rim.
                for x, y in _corner_centers(p):
                    result = _difference(
                        result,
                        _cylinder(x, y, 4.2 + c, h - p["lip_depth"] - 1, zcap),
                        _cylinder(
                            x, y, p["screw_diameter"] / 2 + c, zcap - 0.1, zcap + lh + 1
                        ),
                    )
                    circles.extend(
                        [
                            (0, 1, x, y, 4.2 + c),
                            (0, 1, x, y, p["screw_diameter"] / 2 + c),
                        ]
                    )
    elif part == "gasket":
        if not p["gasket_enabled"] or style == "sliding_lid":
            raise ValueError(
                "Ative um canal TPU compatível / enable a compatible TPU channel."
            )
        gw, gd = p["gasket_width"], p["gasket_depth"]
        result = _ring(
            w - t + gw - 0.12,
            d - t + gw - 0.12,
            h - gd + 0.05,
            h + c + 0.15,
            gw - 0.12,
            max(0.2, r - t / 2 + gw / 2 - 0.06),
        )
        rectangles = [
            (w - t + gw - 0.12, d - t + gw - 0.12, max(0.2, r - t / 2 + gw / 2 - 0.06)),
            (
                w - t - gw + 0.12,
                d - t - gw + 0.12,
                max(0.15, r - t / 2 - gw / 2 + 0.06),
            ),
        ]
        levels.extend([h - gd + 0.05, h + c + 0.15])
    else:
        raise ValueError(f"Unknown part: {part}")
    if style == "snap_latch" and part == "base":
        bounds = (-w / 2 - 2, w / 2 + 2, -d / 2 - 4.2, d / 2 + 2, -2, h + c + lh + 2)
        for cx in (-w * 0.24, w * 0.24):
            bottom = h - 7.2
            roof = bottom + p["latch_retention"] + c
            top = roof + 1.2
            catch = _difference(
                _box(
                    cx - p["latch_width"] / 2 + c,
                    cx + p["latch_width"] / 2 - c,
                    -d / 2 - 2.2,
                    -d / 2 + 0.1,
                    bottom,
                    top,
                ),
                _box(
                    cx - p["latch_width"] / 2 - 0.1,
                    cx + p["latch_width"] / 2 + 0.1,
                    -d / 2 - 1.8,
                    -d / 2 - 0.5,
                    bottom - 0.1,
                    roof,
                ),
            )
            result = _union(result, catch)
    if part == "lid":
        bounds = (*bounds[:4], h - p["lip_depth"] - 2, zcap + lh + 2)
        if style == "snap_latch":
            bounds = (*bounds[:4], h - p["lid_wall_height"] - 2, zcap + lh + 2)
    if part == "gasket":
        bounds = (*bounds[:4], h - p["gasket_depth"] - 1, h + 1)
    hints = {
        "circles": circles + registry["circles"],
        "rectangles": registry["rectangles"],
        "levels": levels,
        "planes": registry["planes"],
        "params": p,
        "sample_z": registry.get("sample_z", []),
        "sample_x": registry.get("sample_x", []),
        "sample_y": registry.get("sample_y", []),
    }
    _GEOMETRY_HINTS.set(None)
    return result, bounds, hints


def _axis_grid(lo: float, hi: float, base: float, extra: list[float]) -> np.ndarray:
    values = np.concatenate(
        (
            np.linspace(lo, hi, int(math.ceil((hi - lo) / base)) + 1),
            np.asarray(extra, dtype=float),
        )
    )
    values = values[(values >= lo) & (values <= hi)]
    values = np.unique(np.round(values, 7))
    # Avoid nearly identical layers (tiny triangles after float32 export).
    values = values[np.r_[True, np.diff(values) > 0.001]]
    # A translated sampling lattice avoids exact iso-nodes without offsetting the
    # physical surface. Primitive boundaries remain at their requested dimensions.
    values[1:-1] += 0.0013719
    return np.sort(values)


def _refinement(
    bounds: tuple[float, ...], hints: dict[str, Any]
) -> tuple[list[np.ndarray], float]:
    p = hints["params"]
    tol = min(p["fit_clearance"] / 4, 0.04)
    extra = [
        list(hints.get("sample_x", [])),
        list(hints.get("sample_y", [])),
        list(hints["levels"]) + list(hints.get("sample_z", [])),
    ]
    for axis in range(3):
        for value in set(hints.get("planes", [[], [], []])[axis]):
            extra[axis].extend([value - tol * 0.15, value + tol * 0.15])
    for value in set(hints["levels"]):
        extra[2].extend([value - tol * 0.15, value + tol * 0.15])
    for rect in hints["rectangles"]:
        w, d, r = rect[:3]
        cx, cy = rect[3:] if len(rect) > 3 else (0.0, 0.0)
        for ax, span in ((0, w), (1, d)):
            step = max(0.04, min(0.35, math.sqrt(4 * r * tol) * 0.5))
            for sign in (-1, 1):
                center = cx if ax == 0 else cy
                extra[ax].extend(
                    center
                    + np.linspace(
                        sign * (span / 2 - r),
                        sign * span / 2,
                        int(math.ceil(r / step)) + 1,
                    )
                )
                extra[ax].extend(
                    [center + sign * span / 2, center + sign * (span / 2 - r)]
                )
    for a, b, ca, cb, r in hints["circles"]:
        step = max(0.04, min(0.3, math.sqrt(4 * r * tol) * 0.5))
        for ax, center in ((a, ca), (b, cb)):
            extra[ax].extend(
                np.linspace(center - r, center + r, int(math.ceil(2 * r / step)) + 1)
            )
    # Features with planar boundaries must be sampled on both sides.
    for axis, key in ((0, "dividers_x"), (1, "dividers_y")):
        for v in p[key]:
            extra[axis].extend(
                [v - p["wall_thickness"] / 2, v, v + p["wall_thickness"] / 2]
            )
    # General detail is 0.9 mm; curvature/interface neighbourhoods are refined above.
    spacing = 0.65 if p["quality"] == "fine" else 1.1
    axes = [
        _axis_grid(
            bounds[i * 2], bounds[i * 2 + 1], spacing if i < 2 else 20.0, extra[i]
        )
        for i in range(3)
    ]
    return axes, tol * 0.65


_TETRA = np.array(
    (
        (0, 1, 3, 7),
        (0, 3, 2, 7),
        (0, 2, 6, 7),
        (0, 6, 4, 7),
        (0, 4, 5, 7),
        (0, 5, 1, 7),
    ),
    dtype=np.int32,
)
_TET_EDGES = np.array(((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)), dtype=np.int32)


def _tet_cases() -> dict[int, list[tuple[int, int, int]]]:
    table = {}
    for mask in range(1, 15):
        inside = [i for i in range(4) if mask & (1 << i)]
        outside = [i for i in range(4) if not mask & (1 << i)]

        def edge(a: int, b: int) -> int:
            return next(
                k for k, (u, v) in enumerate(_TET_EDGES) if {int(u), int(v)} == {a, b}
            )

        if len(inside) == 1:
            table[mask] = [tuple(edge(inside[0], j) for j in outside)]
        elif len(inside) == 3:
            table[mask] = [tuple(edge(outside[0], j) for j in inside)]
        else:
            a, b = inside
            u, v = outside
            e0, e1, e2, e3 = edge(a, u), edge(a, v), edge(b, u), edge(b, v)
            table[mask] = [(e0, e1, e2), (e1, e3, e2)]
    return table


_TET_CASES = _tet_cases()


def _unique_xyz_indices(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return first/inverse indices in NumPy's numeric XYZ unique order.

    Surface coordinates are finite float32 values. Numeric lexsort avoids the
    structured-row comparison used by unique(axis=0); its stable ordering also
    retains the first original signed-zero representation, just like unique.
    """
    order = np.lexsort((points[:, 2], points[:, 1], points[:, 0]))
    ordered = points[order]
    start = np.empty(len(points), dtype=bool)
    if len(points):
        start[0] = True
        start[1:] = np.any(ordered[1:] != ordered[:-1], axis=1)
    inverse = np.empty(len(points), dtype=np.intp)
    inverse[order] = np.cumsum(start, dtype=np.intp) - 1
    return order[start], inverse


def _undirected_edge_keys(directed: np.ndarray, vertex_count: int) -> np.ndarray:
    """Pack nonnegative vertex pairs in the same order as sorted row pairs.

    The extractor's grid limit keeps vertex_count squared inside int64. Cast
    before multiplying: int32 triangle indices otherwise overflow on large meshes.
    """
    lo = np.minimum(directed[:, 0], directed[:, 1]).astype(np.int64)
    hi = np.maximum(directed[:, 0], directed[:, 1])
    return lo * vertex_count + hi


def _simplify_planar(
    vertices: np.ndarray, triangles: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Replace convex coplanar patches by fans while preserving every seam vertex.

    Concave patches/patches with holes retain their conforming triangulation.
    No boundary vertex is removed, so adjacent curved patches keep identical seams.
    """
    v = vertices[triangles]
    cross = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    keep = np.ones(len(triangles), dtype=bool)
    extra_v = []
    extra_t = []
    for axis in range(3):
        flat = np.flatnonzero(
            (v[:, :, axis].max(axis=1) - v[:, :, axis].min(axis=1)) < 1e-7
        )
        if not len(flat):
            continue
        plane_values = v[flat, 0, axis]
        for plane in np.unique(plane_values):
            for sign in (-1, 1):
                group = flat[(plane_values == plane) & (cross[flat, axis] * sign > 0)]
                if len(group) < 100:
                    continue
                t = triangles[group]
                directed = np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]))
                _, inverse, counts = np.unique(
                    _undirected_edge_keys(directed, len(vertices)),
                    return_inverse=True,
                    return_counts=True,
                )
                boundary = directed[counts[inverse] == 1]
                links = {int(a): int(b) for a, b in boundary}
                if len(links) != len(boundary):
                    continue
                loops = []
                remaining = set(links)
                while remaining:
                    start = next(iter(remaining))
                    loop = []
                    current = start
                    while current in remaining:
                        loop.append(current)
                        remaining.remove(current)
                        current = links[current]
                    if current != start:
                        loops = []
                        break
                    loops.append(loop)
                if len(loops) != 1:
                    continue
                loop = loops[0]
                axes = [i for i in range(3) if i != axis]
                q = vertices[loop][:, axes]
                a = np.roll(q, 1, axis=0) - q
                b = np.roll(q, -1, axis=0) - q
                turn = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
                if np.any(turn > 1e-5) and np.any(turn < -1e-5):
                    continue
                center = vertices[loop].mean(axis=0)
                center = center.astype(np.float32).astype(np.float64)
                fan_cross = np.cross(
                    vertices[loop] - center, vertices[np.roll(loop, -1)] - center
                )
                if np.any(np.linalg.norm(fan_cross, axis=1) == 0):
                    continue
                center_index = len(vertices) + len(extra_v)
                extra_v.append(center)
                fan = np.array(
                    [
                        (center_index, loop[i], loop[(i + 1) % len(loop)])
                        for i in range(len(loop))
                    ],
                    dtype=np.int32,
                )
                keep[group] = False
                extra_t.append(fan)
    if extra_t:
        vertices = np.concatenate((vertices, np.asarray(extra_v)))
        triangles = np.concatenate((triangles[keep], *extra_t))
    used, remap = np.unique(triangles, return_inverse=True)
    return vertices[used], remap.reshape(-1, 3).astype(np.int32)


def mesh_field(
    field: Field, bounds: tuple[float, ...], hints: dict[str, Any], part: str = ""
) -> MeshData:
    axes, error = _refinement(bounds, hints)
    xs, ys, zs = axes
    nx, ny, nz = len(xs), len(ys), len(zs)
    if nx * ny * nz > 35_000_000:
        raise ValueError(
            "Modelo muito complexo: reduza dimensões ou acessórios / reduce dimensions or features."
        )
    xx, yy = np.meshgrid(xs, ys, indexing="ij")
    flatxy = np.column_stack((xx.ravel(), yy.ravel()))
    ix, iy = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing="ij")
    xybase = (ix * ny + iy).ravel()
    offsets = np.array((0, ny, 1, ny + 1, 0, ny, 1, ny + 1), dtype=np.int64)
    offsets[4:] += nx * ny
    # Every iteration joins precisely two XY layers with the same local indices.
    layer_cubeidx = xybase[:, None] + offsets
    all_keys = []
    all_points = []
    ngrid = nx * ny * nz

    def layer(z: float) -> tuple[np.ndarray, np.ndarray]:
        pts = np.column_stack((flatxy, np.full(len(flatxy), z)))
        values = field(pts)
        # Deterministic iso-zero convention shared by every tetrahedron.
        values = np.where(np.abs(values) < 1e-10, 1e-10, values)
        return pts, values

    prev, prevval = layer(zs[0])
    for k in range(nz - 1):
        nxt, nxtval = layer(zs[k + 1])
        joined = np.concatenate((prev, nxt))
        vals = np.concatenate((prevval, nxtval))
        cv = vals[layer_cubeidx]
        active = np.any(cv < 0, axis=1) & np.any(cv > 0, axis=1)
        cubeidx = layer_cubeidx[active]
        if len(cubeidx):
            for tet in _TETRA:
                ids = cubeidx[:, tet]
                tv = vals[ids]
                masks = ((tv < 0) * np.array((1, 2, 4, 8))).sum(axis=1)
                for mask, tris in _TET_CASES.items():
                    idx = np.flatnonzero(masks == mask)
                    if not len(idx):
                        continue
                    t_ids = ids[idx]
                    t_vals = tv[idx]
                    for edges in tris:
                        ep = _TET_EDGES[np.asarray(edges)]
                        ai = t_ids[:, ep[:, 0]]
                        bi = t_ids[:, ep[:, 1]]
                        av = t_vals[:, ep[:, 0]]
                        bv = t_vals[:, ep[:, 1]]
                        frac = av / (av - bv)
                        frac = np.where(
                            frac < 1e-9, 0.0, np.where(frac > 1 - 1e-9, 1.0, frac)
                        )
                        pts = joined[ai] + frac[:, :, None] * (joined[bi] - joined[ai])
                        ga = ai + k * nx * ny
                        gb = bi + k * nx * ny
                        keys = np.minimum(ga, gb) * ngrid + np.maximum(ga, gb)
                        keys = np.where(
                            frac == 0,
                            ga * ngrid + ga,
                            np.where(frac == 1, gb * ngrid + gb, keys),
                        )
                        # Orient using the linear tetrahedral field. Querying the
                        # nonlinear CSG at a triangle center is unreliable at creases.
                        ins = [q for q in range(4) if mask & (1 << q)]
                        outs = [q for q in range(4) if not mask & (1 << q)]
                        direction = joined[t_ids[:, outs]].mean(axis=1) - joined[
                            t_ids[:, ins]
                        ].mean(axis=1)
                        cross = np.cross(pts[:, 1] - pts[:, 0], pts[:, 2] - pts[:, 0])
                        flip = np.einsum("ij,ij->i", cross, direction) < 0
                        keys[flip] = keys[flip][:, [0, 2, 1]]
                        pts[flip] = pts[flip][:, [0, 2, 1]]
                        all_keys.append(keys)
                        all_points.append(pts)
        prev, prevval = nxt, nxtval
    if not all_keys:
        raise ValueError("A geometria não contém um sólido / empty geometry.")
    keys = np.concatenate(all_keys).ravel()
    points = np.concatenate(all_points).reshape(-1, 3)
    unique_keys, first, inverse = np.unique(
        keys, return_index=True, return_inverse=True
    )
    vertices = points[first]
    bad = np.abs(field(vertices)) > 0.00025
    if np.any(bad):
        ga = unique_keys[bad] // ngrid
        gb = unique_keys[bad] % ngrid

        def decode(ids: np.ndarray) -> np.ndarray:
            return np.column_stack(
                (xs[(ids % (nx * ny)) // ny], ys[ids % ny], zs[ids // (nx * ny)])
            )

        va, vb = decode(ga), decode(gb)
        av = field(va)
        for _ in range(24):
            mid = (va + vb) * 0.5
            mv = field(mid)
            same = (mv < 0) == (av < 0)
            va[same] = mid[same]
            av[same] = mv[same]
            vb[~same] = mid[~same]
        vertices[bad] = (va + vb) * 0.5
    for axis in range(3):
        for plane in set(hints.get("planes", [[], [], []])[axis]):
            close = np.abs(vertices[:, axis] - plane) < 0.0002
            vertices[close, axis] = plane
    triangles = inverse.reshape(-1, 3).astype(np.int32)
    # Degenerate iso-edge vertices weld consistently. This is necessary when an exact
    # planar boundary passes through a grid node before float32 export.
    rounded = vertices.astype(np.float32)
    vfirst, vinverse = _unique_xyz_indices(rounded)
    vertices = rounded[vfirst].astype(np.float64)
    triangles = vinverse[triangles].astype(np.int32)
    # Collapse sub-micron edge clusters before float32 STL serialization. Removing
    # their tiny triangles alone would open cracks on a tangent grid line.
    for _ in range(20):
        q = vertices[triangles]
        zero = (
            np.linalg.norm(np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]), axis=1) == 0
        )
        if not np.any(zero):
            break
        bad_tri = triangles[zero]
        candidate = bad_tri[:, np.array(((0, 1), (1, 2), (2, 0)))]
        lengths = np.linalg.norm(
            vertices[candidate[:, :, 0]] - vertices[candidate[:, :, 1]], axis=2
        )
        short = candidate[np.arange(len(candidate)), np.argmin(lengths, axis=1)]
        if np.any(np.min(lengths, axis=1) > 0.002):
            sample = q[zero][np.argmax(np.min(lengths, axis=1))]
            raise ValueError(
                "Ambiguous surface cell; choose fine quality or adjust dimension by 0.01 mm. "
                + repr(sample.tolist())
            )
        labels = np.arange(len(vertices))
        for _ in range(20):
            low = np.minimum(labels[short[:, 0]], labels[short[:, 1]])
            old = labels.copy()
            np.minimum.at(labels, short[:, 0], low)
            np.minimum.at(labels, short[:, 1], low)
            labels = labels[labels]
            if np.array_equal(labels, old):
                break
        triangles = labels[triangles]
        triangles = triangles[
            (triangles[:, 0] != triangles[:, 1])
            & (triangles[:, 1] != triangles[:, 2])
            & (triangles[:, 2] != triangles[:, 0])
        ]
    used, remap = np.unique(triangles, return_inverse=True)
    vertices = vertices[used]
    triangles = remap.reshape(-1, 3).astype(np.int32)
    vertices, triangles = _simplify_planar(vertices, triangles)
    vectors = vertices[triangles]
    crosses = np.cross(vectors[:, 1] - vectors[:, 0], vectors[:, 2] - vectors[:, 0])
    area = np.linalg.norm(crosses, axis=1)
    good = area > 0
    triangles = triangles[good]
    crosses = crosses[good]
    area = area[good]
    vertices = vertices.astype(np.float32)
    tri = vertices[triangles].astype(np.float64)
    normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    length = np.linalg.norm(normal, axis=1)
    if np.any(length <= 0):
        raise ValueError(
            "Resolução degenerada / degenerate extraction; use a larger feature."
        )
    normals = (normal / length[:, None]).astype(np.float32)
    volume = float(
        np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6000
    )
    if volume <= 0:
        raise ValueError("Orientação ou volume inválido / invalid surface orientation.")
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    return MeshData(
        vertices,
        triangles,
        normals,
        {"min": low.tolist(), "max": high.tolist(), "size": (high - low).tolist()},
        volume,
        part,
        error,
    )


class _SurfaceBuilder:
    """Small, welded boundary mesh builder; never concatenates overlapping solids."""

    def __init__(self):
        self.vertices = []
        self.faces = []
        self.lookup = {}

    def vertex(self, p):
        key = tuple(float(x) for x in np.asarray(p, dtype=np.float32))
        if key not in self.lookup:
            self.lookup[key] = len(self.vertices)
            self.vertices.append(key)
        return self.lookup[key]

    def triangle(self, a, b, c, reverse=False):
        ids = [self.vertex(x) for x in (a, b, c)]
        if len(set(ids)) == 3:
            v = np.asarray([self.vertices[i] for i in ids], dtype=float)
            if np.linalg.norm(np.cross(v[1] - v[0], v[2] - v[0])) > 1e-12:
                self.faces.append(ids[::-1] if reverse else ids)

    def quad(self, a, b, c, d, reverse=False):
        self.triangle(a, b, c, reverse)
        self.triangle(a, c, d, reverse)

    def join(self, a, b, reverse=False):
        for i in range(len(a)):
            j = (i + 1) % len(a)
            self.quad(a[i], a[j], b[j], b[i], reverse)

    def disk(self, loop, reverse=False):
        center = np.mean(loop, axis=0)
        for i in range(len(loop)):
            self.triangle(center, loop[i], loop[(i + 1) % len(loop)], reverse)

    def mesh(self, part, error):
        v = np.asarray(self.vertices, dtype=np.float32)
        tri = np.asarray(self.faces, dtype=np.int32)
        pts = v[tri].astype(float)
        normals = np.cross(pts[:, 1] - pts[:, 0], pts[:, 2] - pts[:, 0])
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        volume = float(np.sum(pts[:, 0] * np.cross(pts[:, 1], pts[:, 2])) / 6 / 1000)
        if volume < 0:
            tri = tri[:, [0, 2, 1]]
            normals = -normals
            volume = -volume
        low, high = v.min(axis=0), v.max(axis=0)
        return MeshData(
            v,
            tri,
            normals.astype(np.float32),
            {"min": low.tolist(), "max": high.tolist(), "size": (high - low).tolist()},
            volume,
            part,
            error,
        )


def _rectangle_loop(w, d, r, z, n, edge_stops=None):
    """CCW section with matching arc angles and optional straight-edge splits."""
    r = min(r, w * 0.475, d * 0.475)
    sections = []
    corners = [
        (w / 2 - r, -d / 2 + r, -90),
        (w / 2 - r, d / 2 - r, 0),
        (-w / 2 + r, d / 2 - r, 90),
        (-w / 2 + r, -d / 2 + r, 180),
    ]
    # front, right, back, left: each edge followed by its CCW corner.
    endpoints = [
        ((-w / 2 + r, -d / 2), (w / 2 - r, -d / 2)),
        ((w / 2, -d / 2 + r), (w / 2, d / 2 - r)),
        ((w / 2 - r, d / 2), (-w / 2 + r, d / 2)),
        ((-w / 2, d / 2 - r), (-w / 2, -d / 2 + r)),
    ]
    for k, ((a, b), (c, e)) in enumerate(endpoints):
        stops = (edge_stops or {}).get(k, [0.0, 1.0])
        for u in stops[:-1]:
            sections.append((a + (c - a) * u, b + (e - b) * u, z))
        cx, cy, angle = corners[k]
        for theta in np.linspace(math.radians(angle), math.radians(angle + 90), n + 1)[
            :-1
        ]:
            sections.append((cx + r * math.cos(theta), cy + r * math.sin(theta), z))
    return np.asarray(sections)


def _analytic_profile_mesh(p, part):
    """Exact planar/profile patches with curved chords below the interface budget."""
    if p["style"] == "rugged_box":
        from .rugged_geometry import generate_rugged_mesh

        return generate_rugged_mesh(p, part)
    if p["style"] == "snap_latch":
        if part in ("clip_left", "clip_right"):
            return _analytic_snap_lever(p, part)
        if part == "lid":
            return _analytic_snap_lid(p)
        if part == "base" and not any(
            p[k]
            for k in (
                "standoffs",
                "cutouts",
                "dividers_x",
                "dividers_y",
                "gasket_enabled",
            )
        ):
            return _analytic_snap_base(p)
        return None
    if p["style"] == "clamshell_pip":
        return _analytic_clamshell_mesh(p, part)
    if p["style"] == "stackable_bin" and part == "base":
        if any(
            p[k]
            for k in (
                "standoffs",
                "cutouts",
                "dividers_x",
                "dividers_y",
                "gasket_enabled",
            )
        ):
            return None
        return _analytic_stackable_mesh(p)
    if p["style"] == "snap_latch" and part in ("clip_left", "clip_right"):
        return _analytic_storage_mesh(p, part)
    if p["style"] not in ("lip_snap", "open_bin", "snap_latch") or part not in (
        "base",
        "lid",
    ):
        return None
    if part == "base" and any(
        p[k]
        for k in ("standoffs", "cutouts", "dividers_x", "dividers_y", "gasket_enabled")
    ):
        return None
    w, d, h, t, f, c, r, lh = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "floor_thickness",
            "fit_clearance",
            "corner_radius",
            "lid_height",
        )
    )
    if (
        r < t + 0.25
    ):  # Different tangent locations need the general CSG boundary mesher.
        return None
    if p["style"] == "snap_latch":
        return _analytic_storage_mesh(p, part)
    tol = min(c / 4, 0.04) * 0.45
    n = max(
        4,
        int(math.ceil((math.pi / 2) / math.acos(max(-1, min(1, 1 - tol / max(r, 1)))))),
    )
    b = _SurfaceBuilder()
    if part == "base" and p["style"] == "open_bin":
        return _analytic_storage_mesh(p, part)
    if part == "base":
        outer = [(0, w, d, r), (h, w, d, r)]
        iw, id_, ir = w - 2 * t, d - 2 * t, max(0.15, r - t)
        q = p["snap_retention"] + 0.18
        inner = [
            (f, iw, id_, ir),
            (h - 3, iw, id_, ir),
            (h - 3, iw + 2 * q, id_ + 2 * q, ir + q),
            (h - 2.1, iw + 2 * q, id_ + 2 * q, ir + q),
            (h - 2.1, iw, id_, ir),
            (h, iw, id_, ir),
        ]
        outloops = [_rectangle_loop(pw, pd, pr, z, n) for z, pw, pd, pr in outer]
        inloops = [_rectangle_loop(pw, pd, pr, z, n) for z, pw, pd, pr in inner]
        for a, bb in zip(outloops, outloops[1:]):
            b.join(a, bb)
        for a, bb in zip(inloops, inloops[1:]):
            b.join(a, bb, True)
        b.disk(outloops[0], True)
        b.disk(inloops[0])
        b.join(outloops[-1], inloops[-1])
    else:
        outer = _lip_outer_profile(p) + [(h + c, w, d, r), (h + c + lh, w, d, r)]
        iw, id_, ir = (
            w - 2 * t - 2 * c - 2.4,
            d - 2 * t - 2 * c - 2.4,
            max(0.15, r - t - c - 1.2),
        )
        outloops = [_rectangle_loop(pw, pd, pr, z, n) for z, pw, pd, pr in outer]
        inloops = [
            _rectangle_loop(iw, id_, ir, z, n) for z in (h - p["lip_depth"], h + c)
        ]
        for a, bb in zip(outloops, outloops[1:]):
            b.join(a, bb)
        b.join(inloops[0], inloops[1], True)
        b.join(inloops[0], outloops[0])
        b.disk(inloops[-1], True)
        b.disk(outloops[-1])
    return b.mesh(part, tol)


def _analytic_stackable_mesh(p):
    """One boundary: foot guide, load shoulders, floor and open-access U rim."""
    w, d, h, t, r, fh, sc = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "corner_radius",
            "stack_foot_height",
            "stack_clearance",
        )
    )
    floor = fh + p["floor_thickness"]
    tol = min(p["fit_clearance"] / 4, sc / 4, 0.04) * 0.45
    n = max(4, int(math.ceil((math.pi / 2) / math.acos(1 - tol / max(r, 1)))))
    half = p["front_access_width"] / 2
    ramp = min(4.0, p["front_access_width"] / 4, p["front_access_drop"] / 2)
    breaks = [-half, -half + ramp, half - ramp, half]

    def stops(width, radius):
        extent = width / 2 - radius
        return {0: [(v + extent) / (2 * extent) for v in [-extent, *breaks, extent]]}

    outer_stops = stops(w, r)
    iw, id_, ir = w - 2 * t, d - 2 * t, max(0.15, r - t)
    inner_stops = stops(iw, ir)
    fw, fd, fr = iw - 2 * sc, id_ - 2 * sc, max(0.2, r - t - sc)
    foot0 = _rectangle_loop(fw, fd, fr, 0, n, outer_stops)
    foot1 = _rectangle_loop(fw, fd, fr, fh, n, outer_stops)
    body0 = _rectangle_loop(w, d, r, fh, n, outer_stops)
    outer_top = _rectangle_loop(w, d, r, h, n, outer_stops)
    floor_loop = _rectangle_loop(iw, id_, ir, floor, n, inner_stops)
    inner_top = _rectangle_loop(iw, id_, ir, h, n, inner_stops)
    # Only the straight front panel is lowered. Its end posts and all corner
    # arcs remain at full height, leaving three continuous load-bearing sides.
    front_count = len(outer_stops[0])
    outer_top[:front_count, 2] = _stack_front_top(p, outer_top[:front_count, 0])
    inner_top[:front_count, 2] = _stack_front_top(p, inner_top[:front_count, 0])
    b = _SurfaceBuilder()
    b.disk(foot0, True)
    b.join(foot0, foot1)
    b.join(foot1, body0)
    b.join(body0, outer_top)
    b.disk(floor_loop)
    b.join(floor_loop, inner_top, True)
    b.join(outer_top, inner_top)
    return b.mesh("base", tol)


def _clamshell_angles(p):
    hg = hinge_geometry(p)
    R = hg["outer_radius"]
    tol = min(p["fit_clearance"] / 4, p["pip_clearance"] / 4, 0.04) * 0.45
    segments = 4 * math.ceil((2 * math.pi / (2 * math.acos(1 - tol / R))) / 4)
    hi = math.atan2(-0.1, -math.sqrt(1 - 0.1**2)) % (2 * math.pi)
    lo = 3 * math.pi / 2
    angles = np.unique(np.r_[np.arange(segments) * 2 * math.pi / segments, hi, lo])
    return angles, hi, lo, tol


def _hinge_circle(angles, x, cy, cz, radius):
    return np.column_stack(
        (
            np.full(len(angles), x),
            cy + radius * np.cos(angles),
            cz + radius * np.sin(angles),
        )
    )


def _append_captive_knuckle(
    builder, p, a, b, inner_radius, bored, outer_radius, attachment_levels
):
    """A barrel fused to its wall aperture, with a bore or an integral shaft.

    The circular cap annulus and the connector cap meet along one shared arc.
    Internal circle/rectangle union surfaces and the wall attachment are omitted.
    """
    hg = hinge_geometry(p)
    cy, cz = (hg[k] for k in ("y", "z"))
    R = outer_radius
    angles, hi, lo, _ = _clamshell_angles(p)
    outer0 = _hinge_circle(angles, a, cy, cz, R)
    outer1 = _hinge_circle(angles, b, cy, cz, R)
    inner0 = _hinge_circle(angles, a, cy, cz, inner_radius)
    inner1 = _hinge_circle(angles, b, cy, cz, inner_radius)
    builder.join(outer0, inner0, True)
    builder.join(outer1, inner1)
    if bored:
        builder.join(inner0, inner1, True)
    for i, theta in enumerate(angles):
        j = (i + 1) % len(angles)
        end = angles[j] + (2 * math.pi if j == 0 else 0)
        if hi < (theta + end) / 2 < lo:
            continue
        builder.quad(outer0[i], outer0[j], outer1[j], outer1[i])
    zlo, zhi = 0.0, cz - 0.1 * R
    arc = angles[(angles >= hi - 1e-10) & (angles <= lo + 1e-10)][::-1]
    poly = np.r_[
        np.array([[p["depth_y"] / 2, zlo], [cy, 0.0]]),
        np.column_stack((cy + R * np.cos(arc), cz + R * np.sin(arc))),
        np.array([[p["depth_y"] / 2, zhi]]),
        np.array(
            [[p["depth_y"] / 2, z] for z in reversed(attachment_levels) if 0 < z < zhi]
        ).reshape(-1, 2),
    ]

    def internal(u, v):
        # The circular seam belongs to the disc boundary, not an exterior wall.
        return (
            abs(np.linalg.norm(u - [cy, cz]) - R) < 1e-7
            and abs(np.linalg.norm(v - [cy, cz]) - R) < 1e-7
        )

    _append_polygon_extrusion(builder, poly, a, b, p["depth_y"] / 2, internal)


def _analytic_clamshell_mesh(p, part):
    if part not in ("base", "lid"):
        raise ValueError(
            "Estojo articulado usa duas metades / articulated case has two halves."
        )
    w, d, h, t, f, r = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "floor_thickness",
            "corner_radius",
        )
    )
    hg = hinge_geometry(p)
    cy, cz, R, pr, k = (
        hg[key] for key in ("y", "z", "outer_radius", "radius", "knuckle_length")
    )
    pc = p["pip_clearance"]
    knuckles = _clamshell_knuckles(p, part)
    spans = _clamshell_spans(p, part)
    angles, _, _, tol = _clamshell_angles(p)
    n = max(4, int(math.ceil((math.pi / 2) / math.acos(1 - tol / max(r, 1)))))
    xs = sorted([v for span in spans for v in span], reverse=True)

    def stops(width, radius):
        extent = width / 2 - radius
        return {2: [(extent - v) / (2 * extent) for v in [extent, *xs, -extent]]}

    outer_stops = stops(w, r)
    iw, id_, ir = w - 2 * t, d - 2 * t, max(0.15, r - t)
    inner_stops = stops(iw, ir)
    levels = sorted(set([0.0, f, h] + [cz - 0.1 * rr for _, _, rr in knuckles]))
    outer = [_rectangle_loop(w, d, r, z, n, outer_stops) for z in levels]
    inner = [_rectangle_loop(iw, id_, ir, z, n, inner_stops) for z in levels if z >= f]
    builder = _SurfaceBuilder()
    builder.disk(outer[0], True)
    builder.disk(inner[0])
    builder.join(outer[-1], inner[-1])
    for lower, upper in zip(outer, outer[1:]):
        midz = (lower[0, 2] + upper[0, 2]) / 2
        for i in range(len(lower)):
            j = (i + 1) % len(lower)
            midx = (lower[i, 0] + lower[j, 0]) / 2
            if (
                abs(lower[i, 1] - d / 2) < 1e-8
                and abs(lower[j, 1] - d / 2) < 1e-8
                and any(
                    a < midx < b and 0 < midz < cz - 0.1 * rr for a, b, rr in knuckles
                )
            ):
                continue
            builder.quad(lower[i], lower[j], upper[j], upper[i])
    for lower, upper in zip(inner, inner[1:]):
        builder.join(lower, upper, True)
    for a, b, rr in knuckles:
        _append_captive_knuckle(
            builder,
            p,
            a,
            b,
            pr + pc if part == "base" else pr,
            part == "base",
            rr,
            levels,
        )
    if part == "lid":
        for cx in hg["centers"]:
            end = 1.5 * k + 2 * pc
            left = [(cx - end, pr), (cx - k / 2, pr)]
            right = [(cx + k / 2, pr), (cx + end, pr)]
            for profile in (left, right):
                loops = [_hinge_circle(angles, x, cy, cz, rr) for x, rr in profile]
                for aa, bb in zip(loops, loops[1:]):
                    builder.join(aa, bb)
            builder.disk(_hinge_circle(angles, cx - end - 1.2, cy, cz, pr), True)
            builder.disk(_hinge_circle(angles, cx + end + 1.2, cy, cz, pr))
    mesh = builder.mesh(part, tol)
    if part == "lid":
        verts = mesh.vertices.copy()
        verts[:, 2] = 2 * h + p["fit_clearance"] - verts[:, 2]
        reflected = MeshData(
            verts,
            mesh.triangles[:, [0, 2, 1]].copy(),
            mesh.face_normals.copy(),
            {},
            mesh.volume_cm3,
            part,
            tol,
        )
        return _reframe(reflected, verts)
    return mesh


def _storage_clip_profile(p):
    """Closed-pose C clip. Hooks have positive vertical clearance and entry bevels."""
    front = -p["depth_y"] / 2
    thick = p["latch_thickness"]
    ret = p["latch_retention"]
    c = p["fit_clearance"]
    spring_length = max(10.0, 6 * thick)
    far = front - 2.2 - c - spring_length - thick
    inner = far + thick
    lower = p["height_z"] - 7.2 - c
    upper = p["height_z"] + c + p["lid_height"] + c
    lower_tip = front - 0.4
    upper_tip = front + ret
    bevel = min(ret, thick * 0.4)
    return np.asarray(
        [
            (far, lower - thick),
            (lower_tip, lower - thick + bevel),
            (lower_tip, lower),
            (front - 0.7, lower),
            (front - 1.1, p["height_z"] - 7.2 + ret),
            (front - 1.6, p["height_z"] - 7.2 + ret),
            (front - 1.6, lower),
            (inner, lower),
            (inner, upper),
            (upper_tip - bevel, upper),
            (upper_tip, upper + bevel),
            (upper_tip, upper + thick - bevel),
            (far, upper + thick),
        ],
        dtype=float,
    )


_CAP_TRIANGLES: dict[bytes, tuple[tuple[int, int, int], ...]] = {}


def _append_polygon_extrusion(b, poly, x0, x1, attachment=None, skip_edge=None):
    """Ear-clip a simple planar contour and stitch its extrusion, sharing edges."""
    area = float(
        np.sum(
            poly[:, 0] * np.roll(poly[:, 1], -1) - poly[:, 1] * np.roll(poly[:, 0], -1)
        )
    )
    if area < 0:
        poly = poly[::-1]

    def cross(a, bb, c):
        return (bb[0] - a[0]) * (c[1] - a[1]) - (bb[1] - a[1]) * (c[0] - a[0])

    key = np.ascontiguousarray(poly, dtype=np.float64).tobytes()
    faces = _CAP_TRIANGLES.get(key)
    if faces is None:
        indices = list(range(len(poly)))
        result = []
        while len(indices) > 3:
            found = False
            for j in range(len(indices)):
                a, bb, c = (indices[(j + k) % len(indices)] for k in (-1, 0, 1))
                if cross(poly[a], poly[bb], poly[c]) <= 1e-10:
                    continue
                others = [i for i in indices if i not in (a, bb, c)]
                if any(
                    cross(poly[a], poly[bb], poly[i]) >= -1e-10
                    and cross(poly[bb], poly[c], poly[i]) >= -1e-10
                    and cross(poly[c], poly[a], poly[i]) >= -1e-10
                    for i in others
                ):
                    continue
                result.append((a, bb, c))
                indices.pop(j)
                found = True
                break
            if not found:
                raise ValueError("Invalid latch contour / contorno de trava inválido.")
        result.append(tuple(indices))
        faces = tuple(result)
        if len(_CAP_TRIANGLES) >= 64:
            _CAP_TRIANGLES.pop(next(iter(_CAP_TRIANGLES)))
        _CAP_TRIANGLES[key] = faces
    lo = np.column_stack((np.full(len(poly), x0), poly))
    hi = np.column_stack((np.full(len(poly), x1), poly))
    for a, bb, c in faces:
        b.triangle(lo[a], lo[bb], lo[c], True)
        b.triangle(hi[a], hi[bb], hi[c])
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        if skip_edge is not None and skip_edge(poly[i], poly[j]):
            continue
        if (
            attachment is not None
            and abs(poly[i, 0] - attachment) < 1e-8
            and abs(poly[j, 0] - attachment) < 1e-8
        ):
            continue
        b.quad(lo[i], lo[j], hi[j], hi[i])


def _extruded_polygon_mesh(poly, x0, x1, part, error):
    b = _SurfaceBuilder()
    _append_polygon_extrusion(b, poly, x0, x1)
    return b.mesh(part, error)


def _analytic_storage_mesh(p, part):
    w, d, h, t, f, c, r, lh = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "floor_thickness",
            "fit_clearance",
            "corner_radius",
            "lid_height",
        )
    )
    tol = min(c / 4, 0.04) * 0.45
    n = max(4, int(math.ceil((math.pi / 2) / math.acos(1 - tol / max(r, 1)))))
    if part.startswith("clip"):
        cx = (-1 if part == "clip_left" else 1) * w * 0.24
        return _extruded_polygon_mesh(
            _storage_clip_profile(p),
            cx - p["latch_width"] / 2,
            cx + p["latch_width"] / 2,
            part,
            0.0,
        )
    b = _SurfaceBuilder()
    if part == "lid":
        bottom = h - p["lid_wall_height"]
        cap = h + c
        top = cap + lh
        sw, sd, sr = w - 2 * t - 2 * c, d - 2 * t - 2 * c, max(0.2, r - t - c)
        outer = [
            (bottom, sw, sd, sr),
            (cap, sw, sd, sr),
            (cap, w, d, r),
            (top, w, d, r),
        ]
        out = [_rectangle_loop(pw, pd, pr, z, n) for z, pw, pd, pr in outer]
        innerbelow = [
            _rectangle_loop(sw - 2.4, sd - 2.4, max(0.15, sr - 1.2), z, n)
            for z in (bottom, cap)
        ]
        for a, bb in zip(out, out[1:]):
            b.join(a, bb)
        b.join(innerbelow[0], innerbelow[1], True)
        b.join(innerbelow[0], out[0])
        b.disk(innerbelow[-1], True)
        b.disk(out[-1])
        return b.mesh(part, tol)
    # Four flat panels and four corner patches share the same boundary vertices.
    # A handle is a capsule-shaped hole with a stitched wall tunnel, never a
    # second shell pushed through the wall. Catch bosses replace front patches.
    handles = p["style"] == "open_bin" and p["handles_enabled"]
    handle_sides = (1, 3) if p["handle_faces"] == "left_right" else (0, 2)
    stops = {}
    handle_u = {}
    rad = p["handle_height"] / 2
    for k, span in enumerate((w, d, w, d)):
        extent = span / 2 - r
        values = [-extent, extent]
        if handles and k in handle_sides:
            hw = p["handle_width"] / 2
            rr = rad
            # Arc coordinates, including the two horizontal tangencies.
            hn = max(2 * n, int(math.ceil(math.pi / math.acos(1 - tol / rad))))
            vals = sorted(
                set(
                    float(x)
                    for x in np.r_[np.linspace(-math.pi / 2, math.pi / 2, hn + 1), 0.0]
                )
            )
            us = np.r_[
                [-hw + rr - rr * math.cos(a) for a in vals],
                [hw - rr + rr * math.cos(a) for a in vals],
            ]
            values.extend(us.tolist())
            handle_u[k] = True
        if p["style"] == "snap_latch" and k == 0:
            for cx in (-w * 0.24, w * 0.24):
                values.extend(
                    [cx - p["latch_width"] / 2 + c, cx + p["latch_width"] / 2 - c]
                )
        values = sorted(set(round(float(x), 9) for x in values))
        # CCW edge order reverses the back and left panels.
        if k >= 2:
            values = values[::-1]
        stops[k] = [
            (x + extent) / (2 * extent) if k < 2 else (extent - x) / (2 * extent)
            for x in values
        ]
    out0 = _rectangle_loop(w, d, r, 0, n, stops)
    inf = _rectangle_loop(w - 2 * t, d - 2 * t, r - t, f, n, stops)
    outh = _rectangle_loop(w, d, r, h, n, stops)
    inh = _rectangle_loop(w - 2 * t, d - 2 * t, r - t, h, n, stops)
    b.disk(out0, True)
    b.disk(inf)
    b.join(outh, inh)
    catch_bottom = h - 7.2
    catch_roof = catch_bottom + p["latch_retention"] + c
    catch_top = catch_roof + 1.2
    zlevels = sorted(
        set(
            [0.0, f, h]
            + ([h - p["handle_top_margin"] - rad] if handles else [])
            + (
                [catch_bottom, catch_roof, catch_top]
                if p["style"] == "snap_latch"
                else []
            )
        )
    )
    cursor = 0
    for k, span in enumerate((w, d, w, d)):
        count = len(stops[k]) - 1
        # Planar edge endpoints are immediately followed by the first arc point.
        outer = out0[cursor : cursor + count + 1].copy()
        inner = inf[cursor : cursor + count + 1].copy()
        axis = 0 if k in (0, 2) else 1
        normal_axis = 1 - axis
        normal_sign = -1 if k in (0, 3) else 1
        us = outer[:, axis]
        if k in handle_u:
            center = h - p["handle_top_margin"] - rad
            hw = p["handle_width"] / 2

            def limits(u):
                if abs(u) > hw + 1e-6:
                    return None
                dx = max(0.0, abs(u) - (hw - rad))
                dz = math.sqrt(max(0.0, rad * rad - dx * dx))
                return center - dz, center + dz

            for j in range(count):
                u0, u1 = us[j], us[j + 1]
                mid = (u0 + u1) / 2
                if abs(mid) > hw:
                    for loop, low, reverse in ((outer, 0, False), (inner, f, True)):
                        for za, zb in zip(zlevels, zlevels[1:]):
                            if za < low:
                                continue
                            a, bb = loop[j].copy(), loop[j + 1].copy()
                            a[2] = bb[2] = za
                            cc, dd = bb.copy(), a.copy()
                            cc[2] = dd[2] = zb
                            b.quad(a, bb, cc, dd, reverse)
                else:
                    lows = [limits(u)[0] for u in (u0, u1)]
                    highs = [limits(u)[1] for u in (u0, u1)]
                    for loop, low, reverse in ((outer, 0, False), (inner, f, True)):
                        a, bb = loop[j].copy(), loop[j + 1].copy()
                        a[2] = bb[2] = low
                        if low == 0:
                            cc, dd = bb.copy(), a.copy()
                            cc[2] = dd[2] = f
                            b.quad(a, bb, cc, dd, reverse)
                            a[2] = bb[2] = f
                        cc, dd = bb.copy(), a.copy()
                        cc[2], dd[2] = lows[1], lows[0]
                        b.quad(a, bb, cc, dd, reverse)
                        a, bb = loop[j].copy(), loop[j + 1].copy()
                        a[2], bb[2] = highs
                        cc, dd = bb.copy(), a.copy()
                        cc[2] = dd[2] = h
                        b.quad(a, bb, cc, dd, reverse)
                    for zs, reverse in ((lows, False), (highs, True)):
                        a, bb = outer[j].copy(), outer[j + 1].copy()
                        a[2], bb[2] = zs
                        cc, dd = inner[j + 1].copy(), inner[j].copy()
                        cc[2], dd[2] = zs[1], zs[0]
                        b.quad(a, bb, cc, dd, reverse)
        else:
            # Remove only the body's attachment patches. The catch boundary is
            # extruded below with its underside socket, sharing those open edges.
            catches = np.zeros((len(zlevels) - 1, count), dtype=bool)
            if p["style"] == "snap_latch" and k == 0:
                for zi, (za, zb) in enumerate(zip(zlevels, zlevels[1:])):
                    for j in range(count):
                        if catch_bottom < (za + zb) / 2 < catch_top and any(
                            abs((us[j] + us[j + 1]) / 2 - cx) < p["latch_width"] / 2 - c
                            for cx in (-w * 0.24, w * 0.24)
                        ):
                            catches[zi, j] = True
            for zi, (za, zb) in enumerate(zip(zlevels, zlevels[1:])):
                for j in range(count):
                    if not catches[zi, j]:
                        a, bb = outer[j].copy(), outer[j + 1].copy()
                        a[2] = bb[2] = za
                        cc, dd = bb.copy(), a.copy()
                        cc[2] = dd[2] = zb
                        b.quad(a, bb, cc, dd)
                    if za >= f:
                        a, bb = inner[j].copy(), inner[j + 1].copy()
                        a[2] = bb[2] = za
                        cc, dd = bb.copy(), a.copy()
                        cc[2] = dd[2] = zb
                        b.quad(a, bb, cc, dd, True)
        # Corner wall patches (all straight panel Z events remain shared).
        for j in range(cursor + count, cursor + count + n):
            jj = (j + 1) % len(out0)
            for loop, low, reverse in ((out0, 0, False), (inf, f, True)):
                for za, zb in zip(zlevels, zlevels[1:]):
                    if za < low:
                        continue
                    a, bb = loop[j].copy(), loop[jj].copy()
                    a[2] = bb[2] = za
                    cc, dd = bb.copy(), a.copy()
                    cc[2] = dd[2] = zb
                    b.quad(a, bb, cc, dd, reverse)
        cursor += count + n
    if p["style"] == "snap_latch":
        front = -d / 2
        poly = np.asarray(
            [
                (front, catch_bottom),
                (front - 0.5, catch_bottom),
                (front - 0.5, catch_roof),
                (front - 1.8, catch_roof),
                (front - 1.8, catch_bottom),
                (front - 2.2, catch_bottom),
                (front - 2.2, catch_top),
                (front, catch_top),
                (front, catch_roof),
            ]
        )
        for cx in (-w * 0.24, w * 0.24):
            _append_polygon_extrusion(
                b,
                poly,
                cx - p["latch_width"] / 2 + c,
                cx + p["latch_width"] / 2 - c,
                front,
            )
    return b.mesh(part, tol)


def generate_box_mesh(
    raw: dict[str, Any] | None = None,
    part: str = "base",
    print_orientation: bool = False,
) -> MeshData:
    p = normalize_params(raw)
    if p["style"] == "rugged_box":
        errors = validate_params(p)
        if errors:
            raise ValueError("\n".join(errors))
        mesh = _analytic_profile_mesh(p, part)
    else:
        field, bounds, hints = build_part_field(p, part)
        mesh = _analytic_profile_mesh(p, part)
        if mesh is None:
            mesh = mesh_field(field, bounds, hints, part)
    return orient_mesh_for_print(mesh, p, part) if print_orientation else mesh


def orient_mesh_for_print(mesh: MeshData, raw: dict[str, Any], part: str) -> MeshData:
    """Return a print pose without modifying the cached canonical mesh or its arrays."""
    p = normalize_params(raw)
    verts = mesh.vertices.copy()
    triangles = mesh.triangles.copy()
    if p["style"] == "rugged_box" and part.startswith("clip_"):
        # Lay the latch's broad XZ face on the bed (original Y thickness is Z).
        verts[:, 0] *= -1
        verts = verts[:, [0, 2, 1]]
    elif p["style"] == "rugged_box" and part == "lid":
        # Proper half-turn around Y, retaining the part's handedness.
        verts[:, [0, 2]] *= -1
    elif part == "lid" and p["style"] == "clamshell_pip":
        verts = clamshell_open_transform(verts, p, 180.0)
    elif part == "lid" and p["style"] != "sliding_lid":
        verts[:, 2] *= -1
        triangles = triangles[:, [0, 2, 1]]
    if part == "pin":
        verts = verts[:, [1, 2, 0]]
    verts[:, 2] -= verts[:, 2].min()
    copy = MeshData(
        verts,
        triangles,
        mesh.face_normals.copy(),
        {},
        mesh.volume_cm3,
        part,
        mesh.interface_error_mm,
    )
    return _reframe(copy, verts)


def _reframe(mesh: MeshData, vertices: np.ndarray) -> MeshData:
    v = vertices.astype(np.float32)
    tr = v[mesh.triangles]
    n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
    n /= np.linalg.norm(n, axis=1)[:, None]
    lo, hi = v.min(axis=0), v.max(axis=0)
    return MeshData(
        v,
        mesh.triangles,
        n,
        {"min": lo.tolist(), "max": hi.tolist(), "size": (hi - lo).tolist()},
        mesh.volume_cm3,
        mesh.part,
        mesh.interface_error_mm,
    )


def generate_fit_test_kit(
    raw: dict[str, Any] | None = None,
) -> list[tuple[str, MeshData]]:
    p = normalize_params(raw)
    if p["style"] in ("open_bin", "snap_latch", "stackable_bin", "clamshell_pip", "rugged_box"):
        raise ValueError(
            "Kit de encaixe indisponível para este mecanismo; exporte base/tampa/travas / fit kit unavailable for this mechanism; export the actual parts."
        )
    kit = copy_params(p)
    kit.update(
        width_x=28.0,
        depth_y=24.0,
        height_z=14.0,
        corner_radius=3.0,
        standoffs=[],
        cutouts=[],
        dividers_x=[],
        dividers_y=[],
        gasket_enabled=False,
        style="lip_snap",
    )
    post = (
        copy_params(p["standoffs"][0])
        if p["standoffs"]
        else {
            "height": 5.0,
            "outer_diameter": 7.0,
            "hole_diameter": 4.2,
            "hole_depth": 3.5,
            "insert": "M3",
            "mode": "insert",
        }
    )
    post.update(x=0.0, y=0.0, height=max(5.0, post["hole_depth"] + 1.2))
    kit["standoffs"] = [post]
    kit["height_z"] = max(
        14.0, kit["floor_thickness"] + post["height"] + p["lip_depth"] + 1.0
    )
    kit["width_x"] = kit["depth_y"] = max(
        28.0,
        post["outer_diameter"] + 2 * (p["wall_thickness"] + kit["corner_radius"] + 1.2),
    )
    result = [
        ("Amostra base / Base sample", generate_box_mesh(kit, "base", True)),
        ("Amostra tampa / Lid sample", generate_box_mesh(kit, "lid", True)),
    ]
    # Flexible snap tongue with hooked free end, rooted in a small test foot.
    registry = {"planes": [[], [], []], "circles": [], "rectangles": []}
    _GEOMETRY_HINTS.set(registry)
    fld = _union(
        _box(-6, 6, -4, 4, 0, 1.6),
        _box(-1, 1, -1, 1, 1.4, 12),
        _box(-1, 2.2, -1, 1, 10.5, 12),
    )
    _GEOMETRY_HINTS.set(None)
    hint = {
        "params": p,
        "circles": [],
        "rectangles": [],
        "levels": [0, 1.4, 1.6, 10.5, 12],
        "planes": registry["planes"],
    }
    result.append(
        (
            "Lingueta / Snap tongue",
            mesh_field(fld, (-8, 8, -6, 6, -1, 14), hint, "snap_sample"),
        )
    )
    return result


def copy_params(p: dict[str, Any]) -> dict[str, Any]:
    import copy

    return copy.deepcopy(p)


def combine_meshes(items: list[MeshData], part: str = "assembly") -> MeshData:
    offsets = np.cumsum([0] + [len(m.vertices) for m in items[:-1]])
    vertices = np.concatenate([m.vertices for m in items])
    triangles = np.concatenate(
        [m.triangles + off for m, off in zip(items, offsets)]
    ).astype(np.int32)
    normals = np.concatenate([m.face_normals for m in items])
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    return MeshData(
        vertices,
        triangles,
        normals,
        {"min": low.tolist(), "max": high.tolist(), "size": (high - low).tolist()},
        sum(m.volume_cm3 for m in items),
        part,
        max(m.interface_error_mm for m in items),
    )


def collect_target_meshes(
    raw: dict[str, Any] | None = None,
    target: str | None = None,
    lang: str = "pt",
    assembled: bool = False,
    mesh_factory: Callable | None = None,
) -> list[tuple[str, MeshData]]:
    p = normalize_params(raw)
    generate = mesh_factory or generate_box_mesh
    target = target or p["export_target"]
    if p["style"] == "clamshell_pip":
        if target not in ("base_and_lid", "full_suite"):
            raise ValueError(
                "Estojo cativo requer o conjunto aberto completo / captive case requires the complete open assembly."
            )
        names = ("Base", "Tampa" if lang == "pt" else "Lid")
        if assembled:
            return [
                (name, generate(p, part, False))
                for name, part in zip(names, ("base", "lid"))
            ]
        base = generate(p, "base", False)
        lid = generate(p, "lid", True)
        return [
            (
                "Estojo aberto articulado / Open articulated case",
                combine_meshes([base, lid], "clamshell_pip_assembly"),
            )
        ]
    if p["style"] in ("open_bin", "stackable_bin") and target in (
        "lid_only",
        "gasket",
        "fit_test_kit",
    ):
        raise ValueError("Caixa aberta tem apenas base / open bin supports base only.")
    if target == "fit_test_kit":
        return generate_fit_test_kit(p)
    names = {
        "base": ("Base", "Base"),
        "lid": ("Tampa", "Lid"),
        "pin": ("Pino", "Hinge pin"),
        "clip_left": ("Trava esquerda", "Left clip"),
        "clip_right": ("Trava direita", "Right clip"),
        "gasket": ("Junta TPU", "TPU gasket"),
    }
    parts = []
    if target in ("base_and_lid", "base_only", "full_suite"):
        parts.append("base")
    if target in ("base_and_lid", "lid_only", "full_suite") and p["style"] not in (
        "open_bin",
        "stackable_bin",
    ):
        parts.append("lid")
    if p["style"] == "rugged_box" and target in ("base_and_lid", "full_suite"):
        parts.extend(("clip_left", "clip_right"))
    if p["style"] == "snap_latch" and target in ("base_and_lid", "full_suite"):
        parts.extend(("clip_left", "clip_right"))
    if target == "gasket" or (target == "full_suite" and p["gasket_enabled"]):
        parts.append("gasket")
    if not parts:
        raise ValueError(f"Unknown export target: {target}")
    return [
        (names[part][lang == "en"], generate(p, part, not assembled)) for part in parts
    ]


def topology_report(mesh: MeshData) -> dict[str, Any]:
    t = mesh.triangles
    directed = np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]))
    vertex_count = len(mesh.vertices)
    unique_keys, counts = np.unique(
        _undirected_edge_keys(directed, vertex_count), return_counts=True
    )
    unique = np.column_stack((unique_keys // vertex_count, unique_keys % vertex_count))
    # Directed comparisons use the same collision-free numeric encoding.
    a, b = directed[:, 0].astype(np.int64), directed[:, 1].astype(np.int64)
    rev = np.sort(a * vertex_count + b)
    opposite = np.sort(b * vertex_count + a)
    parent = np.arange(len(mesh.vertices))
    # Vectorised label relaxation avoids a per-triangle Python traversal.
    for _ in range(1000):
        left_roots, right_roots = parent[unique[:, 0]], parent[unique[:, 1]]
        labels = np.minimum(left_roots, right_roots)
        old = parent.copy()
        np.minimum.at(parent, left_roots, labels)
        np.minimum.at(parent, right_roots, labels)
        parent = parent[parent]
        if np.array_equal(old, parent):
            break
    else:
        raise ValueError("Connectivity did not converge; mesh requires inspection.")
    used = np.unique(t)
    components = len(np.unique(parent[used]))
    euler = len(used) - len(unique) + len(t)
    return {
        "closed": bool(np.all(counts == 2)),
        "oriented": bool(np.array_equal(rev, opposite)),
        "components": components,
        "euler": euler,
        "genus": (2 * components - euler) // 2,
        "vertices": len(mesh.vertices),
        "triangles": len(t),
        "volume_cm3": mesh.volume_cm3,
        "interface_error_mm": mesh.interface_error_mm,
    }


def latch_geometry(raw: dict[str, Any], part: str = "clip_left") -> dict[str, Any]:
    """Articulated latch contract. Positive X rotation releases the front hook."""
    p = normalize_params(raw)
    if p["style"] != "snap_latch" or part not in ("clip_left", "clip_right"):
        raise ValueError("Use uma trava articulada / use an articulated latch.")
    c = p["fit_clearance"]
    pr = p["latch_pivot_diameter"] / 2
    front = -p["depth_y"] / 2
    cy = front - pr - c - 0.4
    cz = p["height_z"] - 7.5
    radius = pr + 2 * c + 0.15 + 1.2
    ear = max(1.6, p["latch_thickness"])
    stub = c + 0.6 * ear
    mouth = pr - min(0.225, pr * 0.15)
    cx = (-1 if part == "clip_left" else 1) * p["width_x"] * 0.24
    hook = p["height_z"] + c + p["lid_height"] + max(0.25, c)
    return {
        "pivot": {"x": cx, "y": cy, "z": cz},
        "release_angle": 90.0,
        "release_fraction": 0.35,
        "lid_lift_mm": 50.0,
        "hook_gap": max(0.25, c),
        "cam_interval": [4.0, 22.0],
        "pin_radius": pr,
        "bore_radius": pr + c,
        "outer_radius": radius,
        "mouth_half_height": mouth,
        "socket_snap": pr - mouth,
        "ear_thickness": ear,
        "stub_length": stub,
        "axial_engagement": stub - c,
        "hook_y": cy - 1.0,
        "hook_bottom_z": hook,
        "catch_outer_y": cy - 1 - p["latch_retention"],
        "catch_top_z": p["height_z"] + c + p["lid_height"],
        "hub_radius": pr + c + 0.25,
        "flat_z": cz - pr + 0.2,
        "grip_inner_y": cy - 1 - p["latch_retention"] - c,
        "grip_outer_y": cy - 1 - p["latch_retention"] - c - p["latch_thickness"],
    }


def latch_open_transform(
    vertices: np.ndarray, raw: dict[str, Any], part: str, angle: float = 90.0
) -> np.ndarray:
    g = latch_geometry(raw, part)
    pivot = g["pivot"]
    if not math.isfinite(float(angle)):
        raise ValueError("Ângulo finito necessário / finite angle required.")
    v = np.asarray(vertices, dtype=float).copy()
    a = math.radians(float(angle))
    dy, dz = v[:, 1] - pivot["y"], v[:, 2] - pivot["z"]
    v[:, 1] = pivot["y"] + dy * math.cos(a) - dz * math.sin(a)
    v[:, 2] = pivot["z"] + dy * math.sin(a) + dz * math.cos(a)
    return v


def _snap_profiles(p):
    g = latch_geometry(p)
    cy, cz = (g["pivot"][k] for k in ("y", "z"))
    pr, R, c = g["pin_radius"], g["outer_radius"], p["fit_clearance"]
    seat = pr + 2 * c + 0.15
    br = pr + c
    mouth = g["mouth_half_height"]
    front = -p["depth_y"] / 2
    outer_delta = math.asin((pr + 0.2) / R)
    upper_inner = math.pi - math.asin(mouth / seat)
    lower_inner = -math.pi + math.asin(mouth / br)
    root = cz - R - (front - cy)
    top = cz + math.sqrt(R * R - (front - cy) ** 2)

    def samples(a, b, critical=()):
        return np.unique(
            np.r_[
                np.linspace(a, b, max(2, int(abs(b - a) / 0.05) + 1)),
                [v for v in critical if a < v < b],
            ]
        )

    lower = samples(math.pi + outer_delta, 1.5 * math.pi)
    upper = samples(math.acos((front - cy) / R), math.pi - outer_delta)
    theta = samples(
        lower_inner,
        upper_inner,
        np.deg2rad([78, 80, 86, 90, 94, 98, 100, 104, 106, 110]),
    )[::-1]
    degrees = np.rad2deg(theta)
    relief = np.minimum(
        np.clip((degrees - 78) / 2, 0, 1),
        np.maximum(
            np.clip((100 - degrees) / 2, 0, 1), np.clip((degrees - 104) / 2, 0, 1)
        ),
    )
    inner = br + relief * (seat - br)
    socket = np.r_[
        np.column_stack((cy + R * np.cos(lower), cz + R * np.sin(lower))),
        [[front, root], [front, top]],
        np.column_stack((cy + R * np.cos(upper), cz + R * np.sin(upper))),
        np.column_stack((cy + inner * np.cos(theta), cz + inner * np.sin(theta))),
    ]
    hub = g["hub_radius"]
    flat = pr - 0.2
    critical = np.deg2rad(
        [0, 78, 80, 86, 90, 94, 98, 100, 104, 106, 110, 135, 180, 270]
    )
    grip_offset = 1 + p["latch_retention"] + c
    join_angle = (
        3 * math.pi / 4
        if grip_offset >= hub / math.sqrt(2)
        else math.acos(-grip_offset / hub)
    )
    critical = np.r_[critical, join_angle]
    for radius in (pr, hub):
        a = math.asin(flat / radius)
        critical = np.r_[critical, math.pi + a, 2 * math.pi - a]
    angles = samples(0, 2 * math.pi, critical)[:-1]
    cam = np.maximum(0, 1 - np.abs(np.rad2deg(angles) - 90) / 4) * (c + 0.15)
    pin_radius = pr + cam
    sine = np.sin(angles)
    limit = np.where(sine < -0.00001, flat / np.maximum(-sine, 0.00001), np.inf)
    pin_radius = np.minimum(pin_radius, limit)
    hub_radius = np.minimum(np.full(len(angles), hub), limit)
    pin = np.column_stack(
        (cy + pin_radius * np.cos(angles), cz + pin_radius * np.sin(angles))
    )
    hub_profile = np.column_stack(
        (cy + hub_radius * np.cos(angles), cz + hub_radius * np.sin(angles))
    )
    a = 1 + p["latch_retention"] + c
    th = p["latch_thickness"]
    hook = g["hook_bottom_z"]
    arc = angles[(angles >= join_angle - 1e-9) & (angles <= math.pi + 1e-9)]
    grip = np.r_[
        [
            [cy - hub, cz],
            [cy - a - th, cz + max(0.3, a + th - hub)],
            [cy - a - th, hook + th],
            [cy - 1, hook + th],
            [cy - 1, hook],
            [cy - a, hook],
            [cy - a, cz + max(a, math.sqrt(max(0, hub * hub - a * a)))],
        ],
        np.column_stack((cy + hub * np.cos(arc), cz + hub * np.sin(arc))),
    ]
    stop_y = cy - a + c
    stop_top = cz + 6.5
    clearance_radius = g["hub_radius"] + c
    arc_y = cy + clearance_radius * np.cos(np.linspace(0, math.pi, 65))
    ys = np.sort(np.r_[front, stop_y, arc_y[(arc_y > stop_y) & (arc_y < front)]])[::-1]
    lower = stop_top - 1 + stop_y - ys
    rel = ys - cy
    relief = np.where(
        np.abs(rel) < clearance_radius,
        cz + np.sqrt(np.maximum(0, clearance_radius**2 - rel**2)),
        -np.inf,
    )
    stop = np.r_[
        np.column_stack((ys, np.maximum(lower, relief))),
        [[stop_y, stop_top], [front, stop_top]],
    ]
    return g, socket, pin, hub_profile, grip, stop, angles


def _polygon_prism_field(poly, x0, x1):
    low, high = poly.min(axis=0), poly.max(axis=0)

    def field(v):
        # Far from the prism a positive box bound preserves its zero set.
        # Exact polygon distances are evaluated throughout a 0.5 mm surface band.
        yz_all = v[:, [1, 2]]
        slab = _slab(v[:, 0], x0, x1)
        box = np.maximum(np.max(low - yz_all, axis=1), np.max(yz_all - high, axis=1))
        result = np.maximum(slab, box)
        near = (slab <= 0.5) & (box <= 0.5)
        yz = yz_all[near]
        inside = np.zeros(len(yz), dtype=bool)
        distance = np.full(len(yz), np.inf)
        for a, b in zip(poly, np.roll(poly, -1, axis=0)):
            edge = b - a
            length = float(edge @ edge)
            if length < 1e-18:
                continue
            u = np.clip(((yz - a) * edge).sum(axis=1) / length, 0, 1)
            distance = np.minimum(
                distance, np.linalg.norm(yz - a - u[:, None] * edge, axis=1)
            )
            inside ^= ((a[1] > yz[:, 1]) != (b[1] > yz[:, 1])) & (
                yz[:, 0]
                < (b[0] - a[0]) * (yz[:, 1] - a[1]) / (b[1] - a[1] + 1e-30) + a[0]
            )
        result[near] = np.maximum(np.where(inside, -distance, distance), slab[near])
        return result

    return field


def _clean_profile(poly):
    p = np.asarray(poly, dtype=float)
    p = p[np.r_[True, np.linalg.norm(np.diff(p, axis=0), axis=1) > 1e-9]]
    return p[:-1] if len(p) > 1 and np.linalg.norm(p[0] - p[-1]) < 1e-9 else p


def _attachment_splits(poly, front, levels):
    result = []
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        result.append(a)
        if abs(a[0] - front) < 1e-7 and abs(b[0] - front) < 1e-7:
            zs = sorted(
                z for z in levels if min(a[1], b[1]) + 1e-8 < z < max(a[1], b[1]) - 1e-8
            )
            if b[1] < a[1]:
                zs = zs[::-1]
            result.extend([[front, z] for z in zs])
    return _clean_profile(result)


def _analytic_snap_base(p):
    w, d, h, t, f, r = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "floor_thickness",
            "corner_radius",
        )
    )
    parts = [(a, b, _clean_profile(poly)) for a, b, poly in _snap_base_parts(p)]
    tol = min(p["fit_clearance"] / 4, 0.04) * 0.3
    n = max(4, int(math.ceil((math.pi / 2) / math.acos(1 - tol / max(r, 1)))))
    xs = sorted(set(v for a, b, _ in parts for v in (a, b)))

    def stops(width, radius):
        extent = width / 2 - radius
        return {0: [(v + extent) / (2 * extent) for v in [-extent, *xs, extent]]}

    iw, id_, ir = w - 2 * t, d - 2 * t, max(0.15, r - t)
    levels = sorted(
        set(
            [0.0, f, h]
            + [
                float(q[1])
                for _, _, poly in parts
                for q in poly
                if abs(q[0] + d / 2) < 1e-7
            ]
        )
    )
    outer = [_rectangle_loop(w, d, r, z, n, stops(w, r)) for z in levels]
    inner = [
        _rectangle_loop(iw, id_, ir, z, n, stops(iw, ir)) for z in levels if z >= f
    ]
    build = _SurfaceBuilder()
    build.disk(outer[0], True)
    build.disk(inner[0])
    build.join(outer[-1], inner[-1])
    for lower, upper in zip(outer, outer[1:]):
        midz = (lower[0, 2] + upper[0, 2]) / 2
        for i in range(len(lower)):
            j = (i + 1) % len(lower)
            x = (lower[i, 0] + lower[j, 0]) / 2
            if (
                abs(lower[i, 1] + d / 2) < 1e-7
                and abs(lower[j, 1] + d / 2) < 1e-7
                and any(
                    a < x < b
                    and poly[np.abs(poly[:, 0] + d / 2) < 1e-7, 1].min()
                    < midz
                    < poly[np.abs(poly[:, 0] + d / 2) < 1e-7, 1].max()
                    for a, b, poly in parts
                )
            ):
                continue
            build.quad(lower[i], lower[j], upper[j], upper[i])
    for a, b in zip(inner, inner[1:]):
        build.join(a, b, True)
    for a, b, poly in parts:
        _append_polygon_extrusion(
            build, _attachment_splits(poly, -d / 2, levels), a, b, -d / 2
        )
    return build.mesh("base", tol)


def _analytic_snap_lever(p, part):
    g, _, pin, hub, grip, _, angles = _snap_profiles(p)
    g = latch_geometry(p, part)
    pin, hub, grip = (_clean_profile(v) for v in (pin, hub, grip))
    cx = g["pivot"]["x"]
    L = p["latch_width"]
    stub = g["stub_length"]
    build = _SurfaceBuilder()

    def loop(poly, x):
        return np.column_stack((np.full(len(poly), x), poly))

    p0, p1, p2, p3 = [
        loop(pin, x)
        for x in (cx - L / 2 - stub, cx - L / 2, cx + L / 2, cx + L / 2 + stub)
    ]
    h1, h2 = [loop(hub, x) for x in (cx - L / 2, cx + L / 2)]
    build.join(p0, p1)
    build.join(p2, p3)
    build.join(h1, p1, True)
    build.join(h2, p2)
    cy, cz = (g["pivot"][k] for k in ("y", "z"))
    R = g["hub_radius"]
    grip_offset = 1 + p["latch_retention"] + p["fit_clearance"]
    join_angle = (
        3 * math.pi / 4
        if grip_offset >= R / math.sqrt(2)
        else math.acos(-grip_offset / R)
    )

    def seam(a, b):
        return (
            abs(np.linalg.norm(a - [cy, cz]) - R) < 1e-7
            and abs(np.linalg.norm(b - [cy, cz]) - R) < 1e-7
            and join_angle - 1e-7 <= math.atan2(a[1] - cz, a[0] - cy) <= math.pi + 1e-7
            and join_angle - 1e-7 <= math.atan2(b[1] - cz, b[0] - cy) <= math.pi + 1e-7
        )

    for i in range(len(hub)):
        j = (i + 1) % len(hub)
        if not seam(hub[i], hub[j]):
            build.quad(h1[i], h1[j], h2[j], h2[i])
    _append_polygon_extrusion(
        build, pin, cx - L / 2 - stub, cx + L / 2 + stub, skip_edge=lambda a, b: True
    )
    _append_polygon_extrusion(build, grip, cx - L / 2, cx + L / 2, skip_edge=seam)
    return build.mesh(part, min(p["fit_clearance"] / 4, 0.04) * 0.3)


def _analytic_snap_lid(p):
    w, d, h, t, c, r, lh = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "fit_clearance",
            "corner_radius",
            "lid_height",
        )
    )
    g = latch_geometry(p)
    tol = min(c / 4, 0.04) * 0.3
    n = max(4, int(math.ceil((math.pi / 2) / math.acos(1 - tol / max(r, 1)))))
    spans = [
        (cx - p["latch_width"] / 2 + c, cx + p["latch_width"] / 2 - c)
        for cx in (-w * 0.24, w * 0.24)
    ]
    xs = sorted(v for a, b in spans for v in (a, b))

    def loop(pw, pd, pr, z):
        extent = pw / 2 - pr
        return _rectangle_loop(
            pw,
            pd,
            pr,
            z,
            n,
            {0: [(v + extent) / (2 * extent) for v in [-extent, *xs, extent]]},
        )

    sw, sd, sr = w - 2 * t - 2 * c, d - 2 * t - 2 * c, max(0.2, r - t - c)
    outer = [
        loop(pw, pd, pr, z)
        for z, pw, pd, pr in (
            (h - p["lid_wall_height"], sw, sd, sr),
            (h + c, sw, sd, sr),
            (h + c, w, d, r),
            (h + c + lh, w, d, r),
        )
    ]
    inner = [
        loop(sw - 2.4, sd - 2.4, max(0.15, sr - 1.2), z)
        for z in (h - p["lid_wall_height"], h + c)
    ]
    b = _SurfaceBuilder()
    b.join(inner[0], outer[0])
    b.join(inner[0], inner[1], True)
    b.disk(inner[1], True)
    b.disk(outer[-1])
    b.join(outer[0], outer[1])
    b.join(outer[1], outer[2])
    low, high = outer[-2], outer[-1]
    for i in range(len(low)):
        j = (i + 1) % len(low)
        x = (low[i, 0] + low[j, 0]) / 2
        if (
            abs(low[i, 1] + d / 2) < 1e-7
            and abs(low[j, 1] + d / 2) < 1e-7
            and any(a < x < bb for a, bb in spans)
        ):
            continue
        b.quad(low[i], low[j], high[j], high[i])
    for x0, x1 in spans:
        y0, y1 = g["catch_outer_y"], -d / 2
        z0, z1 = h + c, h + c + lh
        b.quad((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), True)
        b.quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))
        b.quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))
        b.quad((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))
        b.quad((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1))
    return b.mesh("lid", tol)


def _snap_base_parts(p):
    g, socket, _, _, _, stop, _ = _snap_profiles(p)
    L = p["latch_width"]
    c = p["fit_clearance"]
    ear = g["ear_thickness"]
    return [
        (
            cx + side * (L / 2 + c + ear / 2) - ear / 2,
            cx + side * (L / 2 + c + ear / 2) + ear / 2,
            socket,
        )
        for cx in (-p["width_x"] * 0.24, p["width_x"] * 0.24)
        for side in (-1, 1)
    ] + [
        (cx - L * 0.25, cx + L * 0.25, stop)
        for cx in (-p["width_x"] * 0.24, p["width_x"] * 0.24)
    ]


def _build_snap_latch_field(p, part):
    g, socket, pin, hub, grip, stop, _ = _snap_profiles(p)
    w, d, h, t, f, r, c, lh = (
        p[k]
        for k in (
            "width_x",
            "depth_y",
            "height_z",
            "wall_thickness",
            "floor_thickness",
            "corner_radius",
            "fit_clearance",
            "lid_height",
        )
    )
    if part.startswith("clip"):
        g = latch_geometry(p, part)
        cx = g["pivot"]["x"]
        L = p["latch_width"]
        stub = g["stub_length"]
        field = _union(
            _polygon_prism_field(pin, cx - L / 2 - stub, cx + L / 2 + stub),
            _polygon_prism_field(hub, cx - L / 2, cx + L / 2),
            _polygon_prism_field(grip, cx - L / 2, cx + L / 2),
        )
        points = np.r_[pin, hub, grip]
        bounds = (
            cx - L / 2 - stub - 1,
            cx + L / 2 + stub + 1,
            points[:, 0].min() - 1,
            points[:, 0].max() + 1,
            points[:, 1].min() - 1,
            points[:, 1].max() + 1,
        )
        return field, bounds, {"params": p}
    # Reuse the validated shell/features without the previous latch geometry.
    shell = copy_params(p)
    shell["style"] = "open_bin" if part == "base" else "screw_corner"
    shell["handles_enabled"] = False
    if part == "base":
        use_gasket = shell["gasket_enabled"]
        shell["gasket_enabled"] = False
        field, bounds, hints = build_part_field(shell, "base")
        for a, b, poly in _snap_base_parts(p):
            outline = []
            for u, v in zip(poly, np.roll(poly, -1, axis=0)):
                outline.append(u)
                if abs(u[0] + d / 2) < 1e-7 and abs(v[0] + d / 2) < 1e-7:
                    outline.extend([[-d / 2 + 0.1, u[1]], [-d / 2 + 0.1, v[1]]])
            overlap = np.asarray(outline)
            field = _union(field, _polygon_prism_field(overlap, a, b))
        if use_gasket:
            gw, gd = p["gasket_width"], p["gasket_depth"]
            field = _difference(
                field,
                _ring(
                    w - t + gw,
                    d - t + gw,
                    h - gd,
                    h + 1,
                    gw,
                    max(0.2, r - t / 2 + gw / 2),
                ),
            )
            hints["rectangles"].extend(
                [
                    (w - t + gw, d - t + gw, max(0.2, r - t / 2 + gw / 2)),
                    (w - t - gw, d - t - gw, max(0.15, r - t / 2 - gw / 2)),
                ]
            )
            hints["levels"].append(h - gd)
        polygons = [poly for _, _, poly in _snap_base_parts(p)]
        bounds = (
            *bounds[:2],
            min(float(poly[:, 0].min()) for poly in polygons) - 1,
            bounds[3],
            bounds[4],
            bounds[5],
        )
        hints["params"] = p
        for a, b, poly in _snap_base_parts(p):
            hints["planes"][0].extend((a, b))
            boundary = poly[np.abs(poly[:, 0] + d / 2) < 1e-7]
            hints["planes"][2].extend(boundary[:, 1].tolist())
        hints["circles"].extend(
            [
                (1, 2, g["pivot"]["y"], g["pivot"]["z"], rr)
                for rr in (
                    g["outer_radius"],
                    g["bore_radius"],
                    g["pin_radius"] + 2 * c + 0.15,
                )
            ]
        )
    elif part == "lid":
        field = _union(
            _rect(w, d, h + c, h + c + lh, r),
            _ring(
                w - 2 * t - 2 * c,
                d - 2 * t - 2 * c,
                h - p["lid_wall_height"],
                h + c + 0.1,
                1.2,
                max(0.2, r - t - c),
            ),
        )
        for cx in (-w * 0.24, w * 0.24):
            field = _union(
                field,
                _box(
                    cx - p["latch_width"] / 2 + c,
                    cx + p["latch_width"] / 2 - c,
                    g["catch_outer_y"],
                    -d / 2 + 0.1,
                    h + c,
                    h + c + lh,
                ),
            )
        bounds = (
            -w / 2 - 1,
            w / 2 + 1,
            g["catch_outer_y"] - 1,
            d / 2 + 1,
            h - p["lid_wall_height"] - 1,
            h + c + lh + 1,
        )
        hints = {"params": p}
    else:
        raise ValueError("Unknown latch part: " + part)
    return field, bounds, hints
