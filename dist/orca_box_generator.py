# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=1.26"]
#
# [tool.orcaslicer.plugin]
# id = "orca-box-studio"
# name = "Orca Box Studio"
# description = "Offline parametric enclosure studio with four construction styles and calibration parts"
# author = "Orca Box Studio"
# version = "1.0.0"
# ///

# MIT License
#
# Copyright (c) 2026 Orca Box Studio
# Copyright (c) 2026 Orca Gear Studio (adapted infrastructure)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

import sys as _orca_init_sys
import types as _orca_init_types
if __name__ not in _orca_init_sys.modules:
    _orca_init_sys.modules[__name__] = _orca_init_types.ModuleType(__name__)

# ===========================================================================
# MODULE: box_studio.schema
# ===========================================================================

"""Validated, JSON-compatible parameters for Orca Box Studio (millimetres)."""

pass  # [bundled] hoisted __future__ import
import copy
import math
from typing import Any

SCHEMA_VERSION = 1
VALID_STYLES = ("lip_snap", "rugged_box", "sliding_lid", "screw_corner")
VALID_EXPORT_TARGETS = (
    "base_and_lid",
    "base_only",
    "lid_only",
    "gasket",
    "fit_test_kit",
    "full_suite",
)
DEFAULT_PARAMS: dict[str, Any] = {
    "schema_version": 1,
    "name": "Caixa de projeto",
    "style": "lip_snap",
    "width_x": 90.0,
    "depth_y": 65.0,
    "height_z": 35.0,
    "wall_thickness": 2.4,
    "floor_thickness": 2.4,
    "lid_height": 3.0,
    "corner_radius": 4.0,
    "fit_clearance": 0.2,
    "lip_depth": 5.0,
    "hinge_mode": "pin",
    "hinge_pin_diameter": 3.0,
    "screw_size": "M3",
    "screw_diameter": 3.0,
    "standoffs": [],
    "cutouts": [],
    "dividers_x": [],
    "dividers_y": [],
    "gasket_enabled": False,
    "gasket_width": 0.8,
    "gasket_depth": 0.8,
    "export_target": "base_and_lid",
    "auto_configure_slicer": True,
    "quality": "standard",
    "lang": "pt",
    "theme": "dark",
}
INSERT_PRESETS = {
    "M2": {"hole_diameter": 3.2, "hole_depth": 4.0},
    "M2.5": {"hole_diameter": 3.8, "hole_depth": 4.0},
    "M3": {"hole_diameter": 4.2, "hole_depth": 5.0},
}
CUTOUT_PRESETS = {
    "usb_c": {"width": 10.0, "height": 4.0, "shape": "rounded"},
    "hdmi": {"width": 16.0, "height": 7.0, "shape": "rounded"},
    "dc": {"width": 8.0, "height": 8.0, "shape": "circle"},
    "slot": {"width": 20.0, "height": 3.0, "shape": "rounded"},
    "hex": {"width": 6.0, "height": 6.0, "shape": "hex"},
}


def _number(value: Any, default: float, lo: float, hi: float) -> float:
    try:
        result = float(value) if not isinstance(value, bool) else default
    except (TypeError, ValueError):
        result = default
    return min(hi, max(lo, result if math.isfinite(result) else default))


def normalize_params(raw: dict[str, Any] | None = None) -> dict[str, Any]:
    """Clamp scalar controls, preserve valid features, reject invalid feature geometry separately."""
    source = raw if isinstance(raw, dict) else {}
    p = copy.deepcopy(DEFAULT_PARAMS)
    for key in p:
        if key in source:
            p[key] = copy.deepcopy(source[key])
    for key, lo, hi in (
        ("width_x", 20, 350),
        ("depth_y", 20, 350),
        ("height_z", 10, 250),
        ("wall_thickness", 1.2, 12),
        ("floor_thickness", 1.2, 12),
        ("lid_height", 1.2, 12),
        ("corner_radius", 0.8, 30),
        ("fit_clearance", 0.1, 0.4),
        ("lip_depth", 3, 10),
        ("hinge_pin_diameter", 2, 6),
        ("screw_diameter", 2, 3),
        ("gasket_width", 0.6, 2),
        ("gasket_depth", 0.5, 2),
    ):
        p[key] = _number(p[key], DEFAULT_PARAMS[key], lo, hi)
    p["wall_thickness"] = min(p["wall_thickness"], min(p["width_x"], p["depth_y"]) / 6)
    p["floor_thickness"] = min(p["floor_thickness"], p["height_z"] / 4)
    p["corner_radius"] = min(p["corner_radius"], min(p["width_x"], p["depth_y"]) / 5)
    p["lip_depth"] = min(p["lip_depth"], p["height_z"] - p["floor_thickness"] - 2)
    p["style"] = p["style"] if p["style"] in VALID_STYLES else "lip_snap"
    p["hinge_mode"] = (
        p["hinge_mode"] if p["hinge_mode"] in ("pin", "print_in_place") else "pin"
    )
    p["quality"] = p["quality"] if p["quality"] in ("standard", "fine") else "standard"
    p["export_target"] = (
        p["export_target"]
        if p["export_target"] in VALID_EXPORT_TARGETS
        else "base_and_lid"
    )
    p["name"] = str(p["name"])[:80].strip() or DEFAULT_PARAMS["name"]
    p["lang"] = "en" if str(p["lang"]).startswith("en") else "pt"
    p["theme"] = "light" if p["theme"] == "light" else "dark"
    p["screw_size"] = p["screw_size"] if p["screw_size"] in INSERT_PRESETS else "M3"
    p["screw_diameter"] = {"M2": 2.0, "M2.5": 2.5, "M3": 3.0}[p["screw_size"]]
    for key in ("gasket_enabled", "auto_configure_slicer"):
        p[key] = p[key] is True or p[key] == 1
    for key in ("dividers_x", "dividers_y"):
        values = p[key] if isinstance(p[key], list) else []
        p[key] = sorted(set(round(_number(v, 0, -170, 170), 3) for v in values[:12]))
    p["standoffs"] = []
    for item in (
        source.get("standoffs", [])
        if isinstance(source.get("standoffs", []), list)
        else []
    )[:24]:
        if not isinstance(item, dict):
            continue
        preset = INSERT_PRESETS.get(item.get("insert", "M3"), INSERT_PRESETS["M3"])
        pilot_default = {"M2": 1.6, "M2.5": 2.1, "M3": 2.5}.get(
            item.get("insert", "M3"), 2.5
        )
        hole = _number(
            item.get("hole_diameter"),
            pilot_default if item.get("mode") == "pilot" else preset["hole_diameter"],
            1,
            10,
        )
        p["standoffs"].append(
            {
                "x": _number(item.get("x"), 0, -170, 170),
                "y": _number(item.get("y"), 0, -170, 170),
                "height": _number(item.get("height"), 8, 3, p["height_z"] - 3),
                "outer_diameter": _number(
                    item.get("outer_diameter"), max(7, hole + 2.4), hole + 2.4, 20
                ),
                "hole_diameter": hole,
                "hole_depth": _number(
                    item.get("hole_depth"), preset["hole_depth"], 1, 20
                ),
                "insert": str(item.get("insert", "M3")),
                "mode": "pilot" if item.get("mode") == "pilot" else "insert",
            }
        )
    p["cutouts"] = []
    for item in (
        source.get("cutouts", []) if isinstance(source.get("cutouts", []), list) else []
    )[:48]:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind", "usb_c")
        defaults = CUTOUT_PRESETS.get(kind, CUTOUT_PRESETS["usb_c"])
        p["cutouts"].append(
            {
                "face": item.get("face")
                if item.get("face") in ("front", "back", "left", "right")
                else "front",
                "kind": kind,
                "shape": item.get("shape", defaults["shape"]),
                "u": _number(item.get("u"), 0, -170, 170),
                "z": _number(item.get("z"), p["height_z"] / 2, 2, p["height_z"] - 2),
                "width": _number(item.get("width"), defaults["width"], 2, 150),
                "height": _number(item.get("height"), defaults["height"], 2, 150),
            }
        )
    return p


def validate_params(p: dict[str, Any]) -> list[str]:
    """Return actionable errors; never silently delete overlapping requested features."""
    errors: list[str] = []
    w, d, h, t, f = (
        p[k]
        for k in ("width_x", "depth_y", "height_z", "wall_thickness", "floor_thickness")
    )
    keepout = t + p["corner_radius"] + 1
    for i, s in enumerate(p["standoffs"]):
        r = s["outer_diameter"] / 2
        if abs(s["x"]) + r > w / 2 - keepout or abs(s["y"]) + r > d / 2 - keepout:
            errors.append(
                f"Torre {i + 1}: mantenha a torre dentro da área útil / keep standoff inside usable floor."
            )
        if s["hole_depth"] > s["height"] - 1.2:
            errors.append(
                f"Torre {i + 1}: fundo do furo deve ter 1.2 mm / hole needs a 1.2 mm blind floor."
            )
        if f + s["height"] > h - p["lip_depth"] - 0.5:
            errors.append(
                f"Torre {i + 1}: altura invade a tampa / standoff height enters lid clearance."
            )
        for j, other in enumerate(p["standoffs"][:i]):
            if (
                math.hypot(s["x"] - other["x"], s["y"] - other["y"])
                < r + other["outer_diameter"] / 2 + 1
            ):
                errors.append(
                    f"Torres {j + 1}/{i + 1}: afastamento insuficiente / insufficient separation."
                )
    for axis, span in (("dividers_x", w), ("dividers_y", d)):
        for v in p[axis]:
            if abs(v) + t / 2 > span / 2 - t - 1:
                errors.append(
                    "Divisória fora da área útil / divider outside usable floor."
                )
        for a, b in zip(p[axis], p[axis][1:]):
            if b - a < t + 1:
                errors.append("Divisórias próximas demais / dividers too close.")
    for i, c in enumerate(p["cutouts"]):
        span = w if c["face"] in ("front", "back") else d
        if (
            abs(c["u"]) + c["width"] / 2 > span / 2 - keepout
            or c["z"] - c["height"] / 2 < f + 1.2
            or c["z"] + c["height"] / 2 > h - p["lip_depth"] - 2
        ):
            errors.append(
                f"Recorte {i + 1}: preserve fundo, cantos e encaixe / preserve floor, corners and lid interface."
            )
        for j, o in enumerate(p["cutouts"][:i]):
            if (
                c["face"] == o["face"]
                and abs(c["u"] - o["u"]) < (c["width"] + o["width"]) / 2 + 1.2
                and abs(c["z"] - o["z"]) < (c["height"] + o["height"]) / 2 + 1.2
            ):
                errors.append(
                    f"Recortes {j + 1}/{i + 1}: mantenha 1.2 mm entre portas / leave 1.2 mm between ports."
                )
    for s in p["standoffs"]:
        for axis, coord in (("dividers_x", "x"), ("dividers_y", "y")):
            if any(
                abs(s[coord] - v) < s["outer_diameter"] / 2 + t / 2 + 0.6
                for v in p[axis]
            ):
                errors.append(
                    "Torre colide com divisória / standoff intersects divider."
                )
    if p["gasket_enabled"] and p["gasket_width"] > t - 1.2:
        errors.append(
            "Canal TPU: preserve 0.6 mm de cada lado / leave 0.6 mm each side of gasket channel."
        )
    if p["gasket_enabled"] and p["style"] == "sliding_lid":
        errors.append(
            "Canal TPU disponível com tampas por pressão, parafusos ou dobradiça / gasket requires a lifting lid."
        )
    return list(dict.fromkeys(errors))

# ===========================================================================
# MODULE: box_studio.mesh_generator
# ===========================================================================

"""NumPy implicit CSG and conforming tetrahedral surface extraction.

Primitives are evaluated analytically. Triangles approximate curved surfaces; local
axis refinement bounds interface chord error below min(clearance/4, 0.04 mm).
Unions are evaluated before meshing: posts/ribs/dividers share one boundary.
"""

pass  # [bundled] hoisted __future__ import
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
pass  # [bundled] resolved intra-package import


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
    radius = min(r, ha * 0.95, hb * 0.95)
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


def _corner_centers(p: dict[str, Any]) -> list[tuple[float, float]]:
    w, d, t = (p[k] for k in ("width_x", "depth_y", "wall_thickness"))
    return [
        (sx * (w / 2 - t - 2.2), sy * (d / 2 - t - 2.2))
        for sx in (-1, 1)
        for sy in (-1, 1)
    ]


def hinge_geometry(p: dict[str, Any]) -> dict[str, float]:
    return {
        "y": p["depth_y"] / 2 + 5.0,
        "z": p["height_z"] - 4.0,
        "radius": p["hinge_pin_diameter"] / 2,
        "outer_radius": p["hinge_pin_diameter"] / 2 + 2.2,
        "span": p["width_x"] * 0.64,
        "knuckle_length": max(5.0, min(12.0, p["width_x"] * 0.13)),
    }


def build_part_field(
    raw: dict[str, Any], part: str = "base"
) -> tuple[Field, tuple[float, ...], dict[str, Any]]:
    """Return one unified printable solid in assembled coordinates and refinement hints."""
    p = normalize_params(raw)
    errors = validate_params(p)
    if errors:
        raise ValueError("\n".join(errors))
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
    zcap = h + c
    circles: list[tuple[int, int, float, float, float]] = []
    rectangles: list[tuple[float, float, float]] = [
        (w, d, r),
        (w - 2 * t, d - 2 * t, max(0.15, r - t)),
    ]
    levels = []
    bounds = (-w / 2 - 2, w / 2 + 2, -d / 2 - 2, d / 2 + 2, -2, h + c + lh + 2)
    if part == "base":
        result = _difference(
            _rect(w, d, 0, h, r),
            _rect(w - 2 * t, d - 2 * t, f, h + 3, max(0.15, r - t)),
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
                    h - p["lip_depth"] - 1,
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
                    h - p["lip_depth"] - 1,
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
        if style == "lip_snap":
            groove = _ring(
                w - 2 * t + 0.6,
                d - 2 * t + 0.6,
                h - 3.0,
                h - 2.1,
                0.4,
                max(0.2, r - t + 0.3),
            )
            result = _difference(result, groove)
            rectangles.append((w - 2 * t + 0.6, d - 2 * t + 0.6, max(0.2, r - t + 0.3)))
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
            # Rear detent pocket, away from the lip load path.
            result = _difference(
                result, _box(-2, 2, d / 2 - t - 0.6, d / 2 + 0.2, h - 2.9, h - 1.9)
            )
            levels.extend([h - 4, h - 1.4, h - 2.9, h - 1.9])
        for cut in p["cutouts"]:
            face = cut["face"]

            def opening(v: np.ndarray, cut=cut, face=face) -> np.ndarray:
                u = (v[:, 0] if face in ("front", "back") else v[:, 1]) - cut["u"]
                z = v[:, 2] - cut["z"]
                a, b = cut["width"] / 2, cut["height"] / 2
                if cut["shape"] == "circle":
                    cross = np.hypot(u / a, z / b) - 1
                    cross = cross * min(a, b)
                elif cut["shape"] == "hex":
                    cross = (
                        np.maximum(
                            np.abs(u) * 0.866025403784 + np.abs(z) * 0.5, np.abs(z)
                        )
                        - min(a, b) * 0.866025403784
                    )
                else:
                    cross = _round2(u, z, a, b, min(1.0, a * 0.4, b * 0.4))
                if face in ("front", "back"):
                    normal = v[:, 1] * (1 if face == "back" else -1)
                    slab = _slab(normal, d / 2 - t - 1, d / 2 + 3)
                else:
                    normal = v[:, 0] * (1 if face == "right" else -1)
                    slab = _slab(normal, w / 2 - t - 1, w / 2 + 3)
                return np.maximum(cross, slab)

            result = _difference(result, opening)
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
            # Flexible rear tongue and bump engaging the rear pocket.
            result = _union(
                result,
                _box(-1.5, 1.5, d / 2 - t - 2, d / 2 - t + 0.25, h - 2.7, h - 2.1),
            )
            levels.extend([h - 3 + c, h - 1.4 - c, h + 1.2, h - 2.7, h - 2.1])
        else:
            result = _rect(w, d, zcap, zcap + lh, r)
            skirt = _ring(
                w - 2 * t - 2 * c,
                d - 2 * t - 2 * c,
                h - p["lip_depth"],
                zcap + 0.2,
                1.2,
                max(0.2, r - t - c),
            )
            if style != "rugged_box":
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
                bead = _ring(
                    w - 2 * t + 0.24,
                    d - 2 * t + 0.24,
                    h - 2.85,
                    h - 2.25,
                    c + 0.3,
                    max(0.2, r - t + 0.12),
                )
                result = _union(result, bead)
                rectangles.append(
                    (w - 2 * t + 0.24, d - 2 * t + 0.24, max(0.2, r - t + 0.12))
                )
                levels.extend([h - 2.85, h - 2.25])
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
            h + 0.15,
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
        levels.extend([h - gd + 0.05, h + 0.15])
    elif part == "pin":
        hg = hinge_geometry(p)
        span, kl, pr = hg["span"], hg["knuckle_length"], hg["radius"]
        result = _union(
            _cylinder_x(
                -span / 2 - kl / 2 - 2, span / 2 + kl / 2 + 2, hg["y"], hg["z"], pr
            ),
            _cylinder_x(
                -span / 2 - kl / 2 - 3,
                -span / 2 - kl / 2 - 1.5,
                hg["y"],
                hg["z"],
                pr + 1.2,
            ),
        )
        circles = [(1, 2, hg["y"], hg["z"], pr), (1, 2, hg["y"], hg["z"], pr + 1.2)]
        bounds = (-w / 2 - 3, w / 2 + 3, d / 2, d / 2 + 12, h - 11, h + 5)
    elif part.startswith("clip"):
        cx = (-1 if part == "clip_left" else 1) * w * 0.24
        # Detachable flexure clip; middle relief leaves two connected spring arms.
        result = _difference(
            _box(cx - 4, cx + 4, -d / 2 - 6, -d / 2 - 1, h - 9, zcap + lh + 1),
            _box(
                cx - 2.6, cx + 2.6, -d / 2 - 4.6, -d / 2 + 0.2, h - 7, zcap + lh - 0.4
            ),
        )
        # Inward return toe engages the base's catch boss.
        result = _union(
            result, _box(cx - 4, cx + 4, -d / 2 - 4, -d / 2 - 0.1, h - 9, h - 7.5)
        )
        result = _union(
            result,
            _box(
                cx - 4,
                cx + 4,
                -d / 2 - 6,
                -d / 2 + 1.4,
                zcap + lh + 0.25,
                zcap + lh + 1,
            ),
        )
        bounds = (cx - 6, cx + 6, -d / 2 - 8, -d / 2 + 2, h - 11, zcap + lh + 3)
        levels.extend([h - 9, h - 7.5, h - 7, zcap + lh - 0.4, zcap + lh + 1])
    else:
        raise ValueError(f"Unknown part: {part}")
    if style == "rugged_box" and part in ("base", "lid"):
        hg = hinge_geometry(p)
        cy, cz, pr, hr, span, kl = (
            hg[k]
            for k in ("y", "z", "radius", "outer_radius", "span", "knuckle_length")
        )
        barrel = []
        if part == "base":
            for x in (-span / 2, span / 2):
                barrel.append(
                    _difference(
                        _cylinder_x(x - kl / 2, x + kl / 2, cy, cz, hr),
                        _cylinder_x(x - kl, x + kl, cy, cz, pr + c),
                    )
                )
                barrel.append(
                    _box(
                        x - kl / 2,
                        x + kl / 2,
                        d / 2 - 0.4,
                        cy,
                        cz - hr * 0.8,
                        cz - hr * 0.1,
                    )
                )
            # Reinforcing ribs run to the floor; integrated front catch bosses.
            for x in (-w * 0.3, 0, w * 0.3):
                barrel.extend(
                    [
                        _box(x - 1, x + 1, -d / 2 - 1.2, -d / 2 + 0.4, 1, h - 7),
                        _box(x - 1, x + 1, d / 2 - 0.4, d / 2 + 1.2, 1, h - 8),
                    ]
                )
            for x in (-w * 0.24, w * 0.24):
                barrel.append(
                    _box(x - 3, x + 3, -d / 2 - 2.2, -d / 2 + 0.3, h - 7.2, h - 5.5)
                )
        else:
            barrel.append(_cylinder_x(-kl / 2, kl / 2, cy, cz, hr))
            # Arm behind the box; a negative X rotation opens the lid upward.
            barrel.append(
                _box(-kl / 2, kl / 2, d / 2 + c, cy + hr * 0.7, cz, zcap + 0.5)
            )
            barrel.append(
                _box(-kl / 2, kl / 2, d / 2 - 0.8, cy + hr * 0.7, zcap, zcap + 0.5)
            )
            if p["hinge_mode"] == "pin":
                barrel[0] = _difference(barrel[0], _cylinder_x(-kl, kl, cy, cz, pr + c))
            else:
                end = span / 2 + kl / 2
                barrel.extend(
                    [
                        _cylinder_x(-end - c, end + c, cy, cz, pr),
                        _cylinder_x(-end - c - 1, -end - c, cy, cz, pr + 1),
                        _cylinder_x(end + c, end + c + 1, cy, cz, pr + 1),
                    ]
                )
        result = _union(result, *barrel)
        if part == "base":
            for x in (-span / 2, span / 2):
                result = _difference(
                    result,
                    _cylinder_x(x - kl / 2 - 0.2, x + kl / 2 + 0.2, cy, cz, pr + c),
                )
        circles.extend([(1, 2, cy, cz, hr), (1, 2, cy, cz, pr + c), (1, 2, cy, cz, pr)])
        levels.extend([cz - hr, cz, cz + hr, cz - hr * 0.8, cz - hr * 0.1])
        bounds = (-w / 2 - 3, w / 2 + 3, -d / 2 - 4, d / 2 + 12, -2, h + c + lh + 3)
    if part == "lid" and style != "rugged_box":
        bounds = (*bounds[:4], h - p["lip_depth"] - 2, zcap + lh + 2)
    if part == "gasket":
        bounds = (*bounds[:4], h - p["gasket_depth"] - 1, h + 1)
    hints = {
        "circles": circles + registry["circles"],
        "rectangles": registry["rectangles"],
        "levels": levels,
        "planes": registry["planes"],
        "params": p,
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
    extra = [[], [], list(hints["levels"])]
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
                    np.sort(directed, axis=1),
                    axis=0,
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
        off = offsets.copy()
        off[4:] += nx * ny
        cubeidx = xybase[:, None] + off
        cv = vals[cubeidx]
        active = np.any(cv < 0, axis=1) & np.any(cv > 0, axis=1)
        cubeidx = cubeidx[active]
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
    _, vfirst, vinverse = np.unique(
        rounded, axis=0, return_index=True, return_inverse=True
    )
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


def generate_box_mesh(
    raw: dict[str, Any] | None = None,
    part: str = "base",
    print_orientation: bool = False,
) -> MeshData:
    p = normalize_params(raw)
    field, bounds, hints = build_part_field(p, part)
    mesh = mesh_field(field, bounds, hints, part)
    if print_orientation:
        verts = mesh.vertices.copy()
        if part == "lid" and p["style"] != "sliding_lid":
            # Closed cap face on the bed; skirt points upward without support.
            verts[:, 2] *= -1
            mesh.triangles = mesh.triangles[:, [0, 2, 1]]
        if part == "pin":
            verts = verts[:, [1, 2, 0]]
        verts[:, 2] -= verts[:, 2].min()
        mesh = _reframe(mesh, verts)
    return mesh


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
) -> list[tuple[str, MeshData]]:
    p = normalize_params(raw)
    target = target or p["export_target"]
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
    if target in ("base_and_lid", "lid_only", "full_suite"):
        parts.append("lid")
    if p["style"] == "rugged_box" and target in ("base_and_lid", "full_suite"):
        if p["hinge_mode"] == "pin":
            parts.append("pin")
        parts.extend(("clip_left", "clip_right"))
    if target == "gasket" or (target == "full_suite" and p["gasket_enabled"]):
        parts.append("gasket")
    if not parts:
        raise ValueError(f"Unknown export target: {target}")
    if (
        not assembled
        and p["style"] == "rugged_box"
        and p["hinge_mode"] == "print_in_place"
        and target in ("base_and_lid", "full_suite")
    ):
        connected = [generate_box_mesh(p, part, False) for part in ("base", "lid")]
        assembly = combine_meshes(connected, "print_in_place_assembly")
        result = [("Conjunto cativo / Captive assembly", assembly)]
        return result + [
            (names[part][lang == "en"], generate_box_mesh(p, part, True))
            for part in parts
            if part not in ("base", "lid")
        ]
    return [
        (names[part][lang == "en"], generate_box_mesh(p, part, not assembled))
        for part in parts
    ]


def topology_report(mesh: MeshData) -> dict[str, Any]:
    t = mesh.triangles
    directed = np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]))
    edge = np.sort(directed, axis=1)
    unique, counts = np.unique(edge, axis=0, return_counts=True)
    rev = np.sort(directed[:, 0] * len(mesh.vertices) + directed[:, 1])
    opposite = np.sort(directed[:, 1] * len(mesh.vertices) + directed[:, 0])
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

# ===========================================================================
# MODULE: box_studio.exporters
# ===========================================================================

"""Binary STL and OrcaSlicer 2.5.1+ multi-object 3MF project exporters for Orca Box Studio."""

pass  # [bundled] hoisted __future__ import

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

pass  # [bundled] resolved intra-package import

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

# ===========================================================================
# MODULE: box_studio.presets_catalog
# ===========================================================================

"""Twelve editable starting designs and atomic user-preset persistence."""

pass  # [bundled] hoisted __future__ import
import copy, json, os, re, tempfile
from pathlib import Path
from typing import Any
pass  # [bundled] resolved intra-package import


def _preset(id: str, pt: str, en: str, **kw: Any) -> dict[str, Any]:
    p = normalize_params(kw)
    return {"id": id, "name_pt": pt, "name_en": en, "params": p}


BUILTIN_PRESETS = [
    _preset(
        "everyday",
        "Caixa de bancada",
        "Workbench box",
        width_x=90,
        depth_y=65,
        height_z=35,
    ),
    _preset(
        "esp32",
        "ESP32 · caixa de projeto",
        "ESP32 · project enclosure",
        style="screw_corner",
        width_x=72,
        depth_y=48,
        height_z=25,
    ),
    _preset(
        "raspberry_pi",
        "Raspberry Pi · espaço de montagem",
        "Raspberry Pi · mounting space",
        style="screw_corner",
        width_x=105,
        depth_y=78,
        height_z=35,
        standoffs=[
            {
                "x": x,
                "y": y,
                "height": 6,
                "hole_depth": 4,
                "hole_diameter": 2.5,
                "mode": "pilot",
            }
            for x in (-29, 29)
            for y in (-24.5, 24.5)
        ],
    ),
    _preset(
        "arduino",
        "Arduino Uno · espaço de montagem",
        "Arduino Uno · mounting space",
        style="screw_corner",
        width_x=100,
        depth_y=78,
        height_z=30,
    ),
    _preset(
        "mini_lip",
        "Mini caixa com encaixe",
        "Mini snap enclosure",
        width_x=45,
        depth_y=35,
        height_z=20,
    ),
    _preset(
        "sensor",
        "Sensor com porta USB-C",
        "USB-C sensor case",
        style="screw_corner",
        width_x=75,
        depth_y=55,
        height_z=30,
        cutouts=[{"kind": "usb_c", "face": "front", "z": 12, "u": 0}],
    ),
    _preset(
        "tool_rugged",
        "Ferramentas · reforçada",
        "Tools · rugged",
        style="rugged_box",
        width_x=120,
        depth_y=85,
        height_z=45,
        dividers_x=[-20, 20],
    ),
    _preset(
        "rugged_pip",
        "Reforçada · dobradiça cativa",
        "Rugged · captive hinge",
        style="rugged_box",
        hinge_mode="print_in_place",
        width_x=90,
        depth_y=65,
        height_z=35,
        fit_clearance=0.3,
    ),
    _preset(
        "pencil",
        "Estojo deslizante",
        "Sliding pencil case",
        style="sliding_lid",
        width_x=160,
        depth_y=55,
        height_z=25,
    ),
    _preset(
        "parts",
        "Organizador de peças",
        "Small-parts organizer",
        style="sliding_lid",
        width_x=100,
        depth_y=80,
        height_z=30,
        dividers_x=[-25, 0, 25],
        dividers_y=[0],
    ),
    _preset(
        "gasket",
        "Caixa com canal TPU",
        "TPU gasket enclosure",
        style="screw_corner",
        width_x=90,
        depth_y=70,
        height_z=35,
        gasket_enabled=True,
        wall_thickness=3,
    ),
    _preset(
        "vented",
        "Eletrônica ventilada",
        "Vented electronics",
        style="screw_corner",
        width_x=100,
        depth_y=75,
        height_z=40,
        cutouts=[
            {"kind": "hex", "face": "right", "u": u, "z": z}
            for u in (-12, 0, 12)
            for z in (12, 24)
        ],
    ),
]


def load_user_presets(path: str | Path) -> list[dict[str, Any]]:
    file = Path(path)
    if not file.is_file():
        return []
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Preset file must contain a list.")
        return [
            {
                "id": str(x["id"]),
                "name": str(x.get("name", "Preset"))[:80],
                "params": normalize_params(x.get("params", {})),
            }
            for x in data
            if isinstance(x, dict) and "id" in x
        ]
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValueError(
            f"Arquivo de presets inválido / invalid preset file: {exc}"
        ) from exc


def _persist(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".box_presets_",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(items, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def save_user_preset(
    path: str | Path, name: str, params: dict[str, Any], preset_id: str | None = None
) -> dict[str, Any]:
    p = normalize_params(params)
    errors = validate_params(p)
    if errors:
        raise ValueError("\n".join(errors))
    items = load_user_presets(path)
    slug = re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-")[:50] or "preset"
    pid = preset_id or slug
    if preset_id is None:
        i = 2
        while any(x["id"] == pid for x in items):
            pid = f"{slug}-{i}"
            i += 1
    item = {
        "id": pid,
        "name": str(name).strip()[:80] or "Preset",
        "params": copy.deepcopy(p),
    }
    _persist(Path(path), [x for x in items if x["id"] != pid] + [item])
    return item


def delete_user_preset(path: str | Path, preset_id: str) -> bool:
    items = load_user_presets(path)
    remaining = [x for x in items if x["id"] != preset_id]
    _persist(Path(path), remaining)
    return len(items) != len(remaining)

# ===========================================================================
# MODULE: box_studio.studio_ui
# ===========================================================================

"""Offline HTML/CSS/WebGL2 workspace. Preview displays the exported Python mesh."""

pass  # [bundled] hoisted __future__ import
import json
from typing import Any

_BOX_HTML = r"""<!doctype html>
<html lang="pt" data-theme="dark">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Orca Box Studio</title>
    <style>
      :root {
        --bg: #15171b;
        --panel: #1d2026;
        --card: #242830;
        --input: #16181d;
        --border: #313641;
        --text: #eef2f7;
        --muted: #9aa4b4;
        --accent: #00a896;
        --hover: #00bfa5;
        --warn: #ffcf77;
        --error: #ff726e;
        --soft: rgba(0, 191, 165, 0.12);
      }
      [data-theme="light"] {
        --bg: #edf1f6;
        --panel: #fff;
        --card: #f5f7fb;
        --input: #fff;
        --border: #d4dce5;
        --text: #1b222c;
        --muted: #525e6f;
        --accent: #00897b;
        --hover: #00796b;
        --soft: rgba(0, 137, 123, 0.1);
      }
      * {
        box-sizing: border-box;
      }
      html,
      body {
        height: 100%;
        margin: 0;
        overflow: hidden;
      }
      body {
        font:
          12px/1.42 "Segoe UI",
          -apple-system,
          BlinkMacSystemFont,
          Ubuntu,
          sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      button,
      input,
      select,
      textarea {
        font: inherit;
        color: inherit;
      }
      button {
        cursor: pointer;
        border: 1px solid var(--border);
        border-radius: 6px;
        background: var(--card);
        padding: 7px 10px;
      }
      button:hover {
        border-color: var(--accent);
      }
      button:disabled {
        opacity: 0.45;
        cursor: wait;
      }
      button:focus-visible,
      input:focus-visible,
      select:focus-visible {
        outline: 2px solid var(--hover);
        outline-offset: 2px;
      }
      input,
      select,
      textarea {
        width: 100%;
        min-width: 0;
        background: var(--input);
        border: 1px solid var(--border);
        border-radius: 5px;
        padding: 7px;
      }
      input[type="checkbox"] {
        width: auto;
        accent-color: var(--accent);
      }
      input[type="range"] {
        padding: 0;
        accent-color: var(--accent);
      }
      input[type="number"] {
        font-family: Consolas, monospace;
      }
      h1,
      h2,
      h3,
      p {
        margin: 0;
      }
      h1 {
        font-size: 15px;
        font-weight: 650;
      }
      h2 {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }
      h3 {
        font-size: 12px;
      }
      small,
      .muted {
        color: var(--muted);
      }
      .shell {
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      .header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        border-bottom: 1px solid var(--border);
        background: var(--panel);
      }
      .brand-icon {
        width: 34px;
        height: 34px;
        color: var(--hover);
      }
      .brand {
        min-width: 170px;
      }
      .eyebrow {
        font-size: 10px;
        color: var(--accent);
        letter-spacing: 0.13em;
      }
      .design-name {
        max-width: 190px;
      }
      .actions {
        display: flex;
        gap: 5px;
        margin-left: auto;
      }
      .printer {
        border-radius: 20px;
        background: var(--soft);
        color: var(--accent);
        white-space: nowrap;
        font-size: 11px;
      }
      .workspace {
        display: grid;
        grid-template-columns: 286px minmax(300px, 1fr) 258px;
        min-height: 0;
        flex: 1;
      }
      .column {
        min-height: 0;
        overflow-y: auto;
        padding: 10px;
        background: var(--panel);
      }
      .column.left {
        border-right: 1px solid var(--border);
      }
      .column.right {
        border-left: 1px solid var(--border);
      }
      .card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 9px;
        margin-bottom: 10px;
        overflow: hidden;
      }
      .cardhead {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 11px 12px;
        border-bottom: 1px solid var(--border);
      }
      .cardbody {
        padding: 11px 12px;
        display: grid;
        gap: 10px;
      }
      .pair {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 9px;
      }
      .field {
        display: grid;
        gap: 5px;
      }
      .field span {
        font-size: 11px;
        color: var(--muted);
      }
      .check {
        display: flex;
        gap: 7px;
        align-items: center;
      }
      .primary {
        background: var(--accent);
        color: white;
        border-color: var(--accent);
        font-weight: 600;
      }
      .primary:hover {
        background: var(--hover);
      }
      .soft {
        background: var(--soft);
        color: var(--accent);
      }
      .wide {
        width: 100%;
      }
      .viewport {
        position: relative;
        min-height: 220px;
        background: radial-gradient(ellipse at 50% 25%, #29313d, #111318);
        overflow: hidden;
      }
      .viewport canvas {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        touch-action: none;
      }
      .viewport .tag {
        position: absolute;
        top: 15px;
        left: 16px;
        color: #b9c7d5;
        font:
          11px Consolas,
          monospace;
        pointer-events: none;
      }
      .viewport .status {
        position: absolute;
        bottom: 55px;
        left: 16px;
        right: 16px;
        padding: 9px 11px;
        background: rgba(20, 24, 30, 0.9);
        border: 1px solid #35414e;
        border-radius: 6px;
        color: #b9c7d5;
        pointer-events: none;
        white-space: pre-wrap;
      }
      .viewtools {
        position: absolute;
        left: 12px;
        right: 12px;
        bottom: 10px;
        display: flex;
        align-items: center;
        gap: 7px;
      }
      .viewtools button {
        background: rgba(28, 33, 41, 0.9);
        color: #e4edf6;
        border-color: #3a4654;
      }
      .viewtools input {
        flex: 1;
      }
      .viewtools label {
        color: #c3d0dc;
        font-size: 11px;
      }
      .metrics {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
      }
      .metric {
        background: var(--input);
        border: 1px solid var(--border);
        padding: 10px;
        border-radius: 6px;
      }
      .metric b {
        display: block;
        font:
          18px Consolas,
          monospace;
        margin-bottom: 3px;
      }
      .metric span {
        color: var(--muted);
        font-size: 10px;
      }
      .editor {
        width: 100%;
        height: 180px;
        border: 1px solid var(--border);
        border-radius: 6px;
        background: var(--input);
        touch-action: none;
      }
      .feature {
        padding: 8px;
        background: var(--input);
        border: 1px solid var(--border);
        border-radius: 6px;
        display: grid;
        gap: 7px;
      }
      .featuretitle {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
      }
      .featuretitle button {
        padding: 2px 7px;
        color: var(--error);
      }
      .mini {
        padding: 4px 7px;
        font-size: 11px;
      }
      .tabs {
        display: flex;
        padding: 7px 10px;
        gap: 5px;
        border-bottom: 1px solid var(--border);
        background: var(--panel);
      }
      .tab {
        flex: 1;
        font-size: 11px;
      }
      .tab.active {
        background: var(--soft);
        border-color: var(--accent);
        color: var(--accent);
      }
      .preset-list {
        max-height: 210px;
        overflow-y: auto;
        display: grid;
        gap: 5px;
      }
      .preset {
        width: 100%;
        text-align: left;
        padding: 8px;
      }
      .preset small {
        display: block;
        font-size: 10px;
      }
      .help {
        font-size: 11px;
        color: var(--muted);
        line-height: 1.6;
      }
      .error {
        color: var(--error);
      }
      .footer {
        padding: 5px 12px;
        font-size: 10px;
        color: var(--muted);
        border-top: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
      }
      .badge {
        font:
          10px Consolas,
          monospace;
        color: var(--accent);
        background: var(--soft);
        padding: 2px 5px;
        border-radius: 3px;
      }
      .section-hidden {
        display: none !important;
      }
      .dock .workspace {
        display: flex;
        flex-direction: column;
      }
      .dock .viewport {
        height: 280px;
        flex: none;
        order: -1;
      }
      .dock .column {
        overflow: visible;
        border: 0 !important;
      }
      .dock .workspace {
        overflow: auto;
        display: block;
      }
      .dock .header {
        flex-wrap: wrap;
      }
      .dock .brand {
        min-width: 130px;
      }
      .dock .printer {
        display: none;
      }
      .dock .design-name {
        max-width: 140px;
      }
      .dock .right {
        padding-top: 0;
      }
      .dock .footer {
        display: none;
      }
      .dock .column.left {
        padding-bottom: 0;
      }
      ::-webkit-scrollbar {
        width: 6px;
      }
      ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 9px;
      }
      @media (max-width: 1050px) {
        .workspace {
          grid-template-columns: 260px minmax(260px, 1fr) 220px;
        }
        .printer {
          display: none;
        }
      }
      @media (max-width: 760px) {
        .workspace {
          grid-template-columns: 230px minmax(200px, 1fr);
        }
        .right {
          grid-column: 1/-1;
          display: flex;
          gap: 10px;
          max-height: 220px;
        }
        .right .card {
          flex: 1;
          min-width: 190px;
        }
        .header {
          flex-wrap: wrap;
        }
        .design-name {
          max-width: 130px;
        }
      }

      .dock-views {
        display: none;
        gap: 6px;
        padding: 7px 10px;
        background: var(--panel);
        border-bottom: 1px solid var(--border);
      }
      .dock .dock-views {
        display: flex;
      }
      .dock-views button {
        flex: 1;
      }
      .dock-views button.active {
        background: var(--soft);
        border-color: var(--accent);
        color: var(--accent);
      }
      .dock .workspace {
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      .dock .column {
        flex: 1;
        overflow-y: auto;
        min-height: 0;
      }
      .dock[data-dock-view="3d"] .column {
        display: none;
      }
      .dock[data-dock-view="3d"] .viewport {
        height: auto;
        flex: 1;
        min-height: 200px;
      }
      .dock[data-dock-view="parameters"] .viewport,
      .dock[data-dock-view="parameters"] .right {
        display: none;
      }
      .dock[data-dock-view="export"] .viewport,
      .dock[data-dock-view="export"] .left {
        display: none;
      }
      .dock:not([data-dock-view="parameters"]) .tabs {
        display: none;
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <header class="header">
        <svg class="brand-icon" viewBox="0 0 40 40" fill="none">
          <path
            d="M4 14 20 6 36 14 20 22ZM4 14V29L20 37 36 29V14M20 22V37"
            stroke="currentColor"
            stroke-width="1.5"
          />
          <path d="M4 8 20 1 36 8" stroke="#ffcf77" stroke-width="1.5" />
        </svg>
        <div class="brand">
          <div class="eyebrow">PARAMETRIC ENCLOSURES</div>
          <h1>Orca Box Studio</h1>
        </div>
        <input
          class="design-name"
          id="name"
          aria-label="Design name"
          maxlength="80"
        /><button
          class="printer"
          id="sync"
          title="Sincronizar impressora / Sync printer"
        >
          ● <span id="printer">OrcaSlicer</span> ↻
        </button>
        <div class="actions">
          <button id="undo" title="Desfazer / Undo">↶</button
          ><button id="redo" title="Refazer / Redo">↷</button
          ><button id="reset" title="Restaurar / Reset">↺</button
          ><button id="lang">PT</button
          ><button id="theme" title="Tema / Theme">☾</button>
        </div>
      </header>
      <nav class="dock-views" aria-label="Dock sections">
        <button data-dock-view-button="parameters" data-i="parameters">
          Parâmetros</button
        ><button class="active" data-dock-view-button="3d">3D</button
        ><button data-dock-view-button="export" data-i="export">
          Exportar
        </button>
      </nav>
      <nav class="tabs">
        <button class="tab active" data-tab="shape" data-i="shape">Caixa</button
        ><button class="tab" data-tab="features" data-i="features">
          Acessórios</button
        ><button class="tab" data-tab="presets" data-i="presets">
          Presets
        </button>
      </nav>
      <main class="workspace">
        <aside class="column left">
          <section data-section="shape">
            <div class="card">
              <div class="cardhead">
                <h2 data-i="construction">Construção</h2>
                <span class="badge">mm</span>
              </div>
              <div class="cardbody">
                <label class="field"
                  ><span data-i="style">Estilo de caixa</span
                  ><select id="style">
                    <option value="lip_snap">Lip snap · pressão / snap</option>
                    <option value="rugged_box">
                      Rugged · dobradiça / hinged
                    </option>
                    <option value="sliding_lid">
                      Sliding · deslizante / sliding
                    </option>
                    <option value="screw_corner">
                      Screw corner · parafusos / screws
                    </option>
                  </select></label
                >
                <div class="pair">
                  <label class="field"
                    ><span data-i="width">Largura X</span
                    ><input
                      data-p="width_x"
                      type="number"
                      min="20"
                      max="350"
                      step="1" /></label
                  ><label class="field"
                    ><span data-i="depth">Profundidade Y</span
                    ><input
                      data-p="depth_y"
                      type="number"
                      min="20"
                      max="350"
                      step="1"
                  /></label>
                </div>
                <div class="pair">
                  <label class="field"
                    ><span data-i="height">Altura Z</span
                    ><input
                      data-p="height_z"
                      type="number"
                      min="10"
                      max="250"
                      step="1" /></label
                  ><label class="field"
                    ><span data-i="radius">Raio de canto</span
                    ><input
                      data-p="corner_radius"
                      type="number"
                      min=".8"
                      max="30"
                      step=".2"
                  /></label>
                </div>
                <div class="pair">
                  <label class="field"
                    ><span data-i="wall">Parede</span
                    ><input
                      data-p="wall_thickness"
                      type="number"
                      min="1.2"
                      max="12"
                      step=".2" /></label
                  ><label class="field"
                    ><span data-i="floor">Fundo</span
                    ><input
                      data-p="floor_thickness"
                      type="number"
                      min="1.2"
                      max="12"
                      step=".2"
                  /></label>
                </div>
                <div class="pair">
                  <label class="field"
                    ><span data-i="lid">Espessura tampa</span
                    ><input
                      data-p="lid_height"
                      type="number"
                      min="1.2"
                      max="12"
                      step=".2" /></label
                  ><label class="field"
                    ><span data-i="clearance">Folga por lado</span
                    ><input
                      data-p="fit_clearance"
                      type="number"
                      min=".10"
                      max=".40"
                      step=".01"
                  /></label>
                </div>
                <label class="field"
                  ><span data-i="lip">Profundidade de encaixe</span
                  ><input
                    data-p="lip_depth"
                    type="number"
                    min="3"
                    max="10"
                    step=".5" /></label
                ><label class="field rugged"
                  ><span data-i="hinge">Dobradiça</span
                  ><select id="hinge_mode">
                    <option value="pin">Pino removível / removable pin</option>
                    <option value="print_in_place">
                      Cativa · print-in-place
                    </option>
                  </select></label
                ><label class="field rugged"
                  ><span data-i="pin">Diâmetro do pino</span
                  ><input
                    data-p="hinge_pin_diameter"
                    type="number"
                    min="2"
                    max="6"
                    step=".2" /></label
                ><label class="field screw"
                  ><span data-i="screw">Parafuso de canto</span
                  ><select id="screw_size">
                    <option>M2</option>
                    <option>M2.5</option>
                    <option>M3</option>
                  </select></label
                ><label class="field"
                  ><span data-i="quality">Resolução da superfície</span
                  ><select id="quality">
                    <option value="standard">Standard</option>
                    <option value="fine">Fine</option>
                  </select></label
                >
              </div>
            </div>
            <div class="card">
              <div class="cardhead"><h2 data-i="sealing">Vedação TPU</h2></div>
              <div class="cardbody">
                <label class="check"
                  ><input type="checkbox" id="gasket_enabled" /><span
                    data-i="enableGasket"
                    >Canal perimetral e junta</span
                  ></label
                >
                <div class="pair">
                  <label class="field"
                    ><span data-i="gasketWidth">Largura do canal</span
                    ><input
                      data-p="gasket_width"
                      type="number"
                      min=".6"
                      max="2"
                      step=".1" /></label
                  ><label class="field"
                    ><span data-i="gasketDepth">Profundidade do canal</span
                    ><input
                      data-p="gasket_depth"
                      type="number"
                      min=".5"
                      max="2"
                      step=".1"
                  /></label>
                </div>
                <p class="help" data-i="gasketHelp">
                  Exporte a junta separadamente e selecione TPU no fatiador.
                  Vedação física requer teste.
                </p>
              </div>
            </div>
          </section>
          <section data-section="features" class="section-hidden">
            <div class="card">
              <div class="cardhead">
                <h2 data-i="pcb">Placa & posicionamento</h2>
                <button id="addPost" class="mini">+ PCB</button>
              </div>
              <div class="cardbody">
                <canvas
                  class="editor"
                  id="plan"
                  width="500"
                  height="330"
                  aria-label="Editor de posição de torres / Standoff placement editor"
                ></canvas>
                <p class="help" data-i="planHelp">
                  Arraste as torres no desenho. Origem no centro; X para a
                  direita, Y para trás. Cotas são editáveis abaixo.
                </p>
                <div id="posts"></div>
              </div>
            </div>
            <div class="card">
              <div class="cardhead">
                <h2 data-i="ports">Recortes de painel</h2>
                <button class="mini" id="addPort">+ USB-C</button>
              </div>
              <div class="cardbody">
                <div id="ports"></div>
                <p class="help" data-i="portHelp">
                  Recortes são atravessamentos reais. Preserve cantos, fundo e
                  encaixe. Dimensões de conectores são pontos de partida
                  editáveis.
                </p>
              </div>
            </div>
            <div class="card">
              <div class="cardhead"><h2 data-i="dividers">Divisórias</h2></div>
              <div class="cardbody">
                <label class="field"
                  ><span data-i="dividerX"
                    >Posições X, separadas por vírgula</span
                  ><input id="dividers_x" placeholder="-20, 20" /></label
                ><label class="field"
                  ><span data-i="dividerY"
                    >Posições Y, separadas por vírgula</span
                  ><input id="dividers_y" placeholder="0"
                /></label>
              </div>
            </div>
          </section>
          <section data-section="presets" class="section-hidden">
            <div class="card">
              <div class="cardhead">
                <h2 data-i="library">Biblioteca de projetos</h2>
                <span class="badge">12</span>
              </div>
              <div class="cardbody preset-list" id="presets"></div>
            </div>
            <div class="card">
              <div class="cardhead">
                <h2 data-i="mine">Meus presets</h2>
                <button class="mini" id="savePreset" data-i="save">
                  Salvar
                </button>
              </div>
              <div class="cardbody preset-list" id="userPresets"></div>
            </div>
            <p class="help" data-i="presetHelp">
              Envelopes de placas são referências. Confira o modelo e a revisão
              da sua PCB antes de perfurar ou imprimir.
            </p>
          </section>
        </aside>
        <section class="viewport">
          <canvas
            id="gl"
            aria-label="Pré-visualização 3D / 3D preview"
          ></canvas>
          <div class="tag">
            BOX / ENCLOSURE STUDIO <span id="viewLabel">ASSEMBLY</span>
          </div>
          <div class="status" id="status" role="status" aria-live="polite">
            Preparando visualização / Preparing preview…
          </div>
          <div class="viewtools">
            <button id="home" title="Enquadrar / Fit view">⌂</button
            ><button id="play" title="Animar tampa / Animate lid">▶</button
            ><label for="open" data-i="open">Abrir</label
            ><input
              id="open"
              type="range"
              min="0"
              max="100"
              value="25"
              aria-label="Abertura da tampa / Lid opening"
            /><span id="openValue" style="color: #bcc9d7; font: 11px Consolas"
              >25%</span
            >
          </div>
        </section>
        <aside class="column right">
          <div class="card">
            <div class="cardhead">
              <h2 data-i="inspection">Inspeção</h2>
              <span class="badge">LIVE MESH</span>
            </div>
            <div class="cardbody">
              <div class="metrics">
                <div class="metric">
                  <b id="volume">—</b><span data-i="volume">Volume · cm³</span>
                </div>
                <div class="metric">
                  <b id="triangles">—</b
                  ><span data-i="triangles">Triângulos</span>
                </div>
              </div>
              <label class="check"
                ><input id="xray" type="checkbox" /><span data-i="xray"
                  >Raio-X · componentes internos</span
                ></label
              ><label class="field"
                ><span data-i="cut">Corte axial de inspeção</span
                ><input id="cut" type="range" min="0" max="100" value="0"
              /></label>
              <p class="help" id="surface"></p>
              <p class="help" data-i="sameMesh">
                Visualização e exportação usam a mesma geometria Python. Curvas
                são tesselações; a atualização do modelo acontece em segundo
                plano.
              </p>
            </div>
          </div>
          <div class="card">
            <div class="cardhead"><h2 data-i="manufacture">Fabricação</h2></div>
            <div class="cardbody">
              <select
                id="target"
                aria-label="Peças para exportação / Export parts"
              >
                <option value="base_and_lid" data-i="both">Base + tampa</option>
                <option value="base_only" data-i="baseOnly">Apenas base</option>
                <option value="lid_only" data-i="lidOnly">Apenas tampa</option>
                <option value="gasket" data-i="gasketOnly">Junta TPU</option>
                <option value="fit_test_kit" data-i="kit">
                  Kit de calibração
                </option>
                <option value="full_suite" data-i="full">
                  Conjunto completo
                </option></select
              ><button class="primary wide job" id="send" data-i="send">
                Enviar para a mesa
              </button>
              <div class="pair">
                <button class="job" id="stl">STL ↓</button
                ><button class="job" id="mf">3MF ↓</button>
              </div>
              <label class="check"
                ><input id="auto_configure_slicer" type="checkbox" /><span
                  data-i="auto"
                  >Aplicar fatiamento mecânico</span
                ></label
              ><button id="folder" class="wide" data-i="folder">
                Abrir pasta de exportação
              </button>
              <p class="help" data-i="printHelp">
                Base com fundo na mesa; tampa invertida. Faça o kit de encaixe
                antes da peça final. O tempo depende da impressora e do perfil.
              </p>
              <p class="help" id="pipNote"></p>
            </div>
          </div>
        </aside>
      </main>
      <footer class="footer">
        <span>Orca Box Studio 1.0.0 · NumPy / WebGL2 · Offline</span
        ><span data-i="gesture">Arraste para orbitar · roda para zoom</span>
      </footer>
    </div>
    <script>
      const INITIAL = __BOX_CONTEXT__;
      (() => {
        "use strict";
        const $ = (id) => document.getElementById(id),
          clone = (o) => JSON.parse(JSON.stringify(o));
        let p = clone(INITIAL.params),
          lang = INITIAL.lang || p.lang || "pt",
          theme = INITIAL.theme || "dark",
          tab = "shape",
          history = [],
          future = [],
          meshes = [],
          serial = 0,
          latest = 0,
          timer = null,
          playing = false,
          angle = 25,
          drag = null;
        const texts = {
          pt: {
            shape: "Caixa",
            features: "Acessórios",
            presets: "Presets",
            construction: "Construção",
            style: "Estilo de caixa",
            width: "Largura X",
            depth: "Profundidade Y",
            height: "Altura Z",
            radius: "Raio de canto",
            wall: "Parede",
            floor: "Fundo",
            lid: "Espessura tampa",
            clearance: "Folga por lado",
            lip: "Profundidade de encaixe",
            hinge: "Dobradiça",
            pin: "Diâmetro do pino",
            screw: "Parafuso de canto",
            quality: "Resolução da superfície",
            sealing: "Vedação TPU",
            enableGasket: "Canal perimetral e junta",
            gasketWidth: "Largura do canal",
            gasketDepth: "Profundidade do canal",
            gasketHelp:
              "Exporte a junta separadamente e selecione TPU no fatiador. Vedação física requer teste.",
            pcb: "Placa & posicionamento",
            planHelp:
              "Arraste as torres. Origem no centro; X para a direita, Y para trás. Cotas editáveis abaixo.",
            ports: "Recortes de painel",
            portHelp:
              "Atravessamentos reais. Preserve cantos, fundo e encaixe. Dimensões de conectores são pontos de partida editáveis.",
            dividers: "Divisórias",
            dividerX: "Posições X, separadas por vírgula",
            dividerY: "Posições Y, separadas por vírgula",
            library: "Biblioteca de projetos",
            mine: "Meus presets",
            save: "Salvar",
            presetHelp:
              "Envelopes de placas são referências. Confira o modelo e a revisão da sua PCB.",
            open: "Abrir",
            inspection: "Inspeção",
            volume: "Volume · cm³",
            triangles: "Triângulos",
            xray: "Raio-X · componentes internos",
            cut: "Corte axial de inspeção",
            sameMesh:
              "Visualização e exportação usam a mesma geometria Python. Curvas são tesselações; atualização em segundo plano.",
            manufacture: "Fabricação",
            both: "Base + tampa",
            baseOnly: "Apenas base",
            lidOnly: "Apenas tampa",
            gasketOnly: "Junta TPU",
            kit: "Kit de calibração",
            full: "Conjunto completo",
            send: "Enviar para a mesa",
            auto: "Aplicar fatiamento mecânico",
            folder: "Abrir pasta de exportação",
            printHelp:
              "Base com fundo na mesa; tampa invertida. Imprima o kit de encaixe antes da peça final. Tempo depende da impressora e do perfil.",
            gesture: "Arraste para orbitar · roda para zoom",
            generating: "Gerando malha… você pode continuar editando.",
            ready: "Malha atualizada · pronta para inspecionar.",
            noHost:
              "Pré-visualização de interface. Abra o plugin no OrcaSlicer para gerar malhas.",
            pip: "Print-in-place: conjunto montado. Avalie pontes/suportes removíveis sob a tampa, sem preencher as folgas da dobradiça. Retire as travas para abrir.",
            delete: "Remover",
            heightPost: "Altura torre",
            outer: "Ø externo",
            hole: "Ø furo",
            holeDepth: "Prof. furo",
            insert: "Inserto",
            pilot: "Piloto",
            face: "Face",
            kind: "Tipo",
            front: "Frente",
            back: "Trás",
            left: "Esquerda",
            right: "Direita",
          },
          en: {
            shape: "Enclosure",
            features: "Features",
            presets: "Presets",
            construction: "Construction",
            style: "Enclosure style",
            width: "Width X",
            depth: "Depth Y",
            height: "Height Z",
            radius: "Corner radius",
            wall: "Wall",
            floor: "Floor",
            lid: "Lid thickness",
            clearance: "Clearance per side",
            lip: "Locating skirt depth",
            hinge: "Hinge",
            pin: "Pin diameter",
            screw: "Corner screw",
            quality: "Surface resolution",
            sealing: "TPU gasket",
            enableGasket: "Perimeter channel and gasket",
            gasketWidth: "Channel width",
            gasketDepth: "Channel depth",
            gasketHelp:
              "Export the gasket separately and select TPU in the slicer. Physical sealing requires testing.",
            pcb: "PCB & placement",
            planHelp:
              "Drag standoffs. Centered origin; X right, Y back. Exact coordinates remain editable below.",
            ports: "Panel cutouts",
            portHelp:
              "Real through-openings. Preserve corners, floor and lid interface. Connector dimensions are editable starting points.",
            dividers: "Dividers",
            dividerX: "X positions, comma separated",
            dividerY: "Y positions, comma separated",
            library: "Design library",
            mine: "My presets",
            save: "Save",
            presetHelp:
              "PCB envelopes are references. Check your actual board model and revision.",
            open: "Open",
            inspection: "Inspection",
            volume: "Volume · cm³",
            triangles: "Triangles",
            xray: "X-ray · internal components",
            cut: "Axial inspection cut",
            sameMesh:
              "Preview and export share the Python geometry. Curves are tessellated; model updates run in the background.",
            manufacture: "Manufacture",
            both: "Base + lid",
            baseOnly: "Base only",
            lidOnly: "Lid only",
            gasketOnly: "TPU gasket",
            kit: "Fit calibration kit",
            full: "Complete set",
            send: "Send to Plater",
            auto: "Apply mechanical slicing",
            folder: "Open export folder",
            printHelp:
              "Base on its floor; lid flipped onto the cap. Print the fit kit first. Print time depends on printer and profile.",
            gesture: "Drag to orbit · wheel to zoom",
            generating: "Generating mesh… you can keep editing.",
            ready: "Mesh updated · ready to inspect.",
            noHost:
              "Interface preview. Open this plugin in OrcaSlicer to generate meshes.",
            pip: "Print-in-place: assembled set. Assess bridging/removable support below the lid without filling hinge gaps. Remove clips before opening.",
            delete: "Remove",
            heightPost: "Post height",
            outer: "Outer Ø",
            hole: "Hole Ø",
            holeDepth: "Hole depth",
            insert: "Insert",
            pilot: "Pilot",
            face: "Face",
            kind: "Type",
            front: "Front",
            back: "Back",
            left: "Left",
            right: "Right",
          },
        };
        const tr = (k) => texts[lang][k] || k;
        function send(m) {
          if (window.orca && typeof window.orca.postMessage === "function") {
            window.orca.postMessage(m);
            return true;
          }
          if (window.chrome?.webview) {
            window.chrome.webview.postMessage(m);
            return true;
          }
          return false;
        }
        function status(s, error = false) {
          $("status").textContent = s;
          $("status").style.borderColor = error ? "#ff726e" : "#35414e";
          $("status").style.color = error ? "#ff9b97" : "#b9c7d5";
        }
        texts.pt.parameters = "Parâmetros";
        texts.en.parameters = "Parameters";
        texts.pt.export = "Exportar";
        texts.en.export = "Export";
        document.querySelectorAll("[data-dock-view-button]").forEach(
          (button) =>
            (button.onclick = () => {
              document.body.dataset.dockView = button.dataset.dockViewButton;
              document
                .querySelectorAll("[data-dock-view-button]")
                .forEach((other) =>
                  other.classList.toggle("active", other === button),
                );
              render();
              drawPlan();
            }),
        );
        function translate() {
          document.documentElement.lang = lang;
          document.documentElement.dataset.theme = theme;
          $("lang").textContent = lang.toUpperCase();
          $("theme").textContent = theme === "dark" ? "☾" : "☀";
          document
            .querySelectorAll("[data-i]")
            .forEach((e) => (e.textContent = tr(e.dataset.i)));
          presets();
          features();
          drawPlan();
        }
        function snapshot() {
          history.push(clone(p));
          if (history.length > 40) history.shift();
          future = [];
          buttons();
        }
        function buttons() {
          $("undo").disabled = !history.length;
          $("redo").disabled = !future.length;
        }
        function setDesign(next, remember = true) {
          if (remember) snapshot();
          p = clone(next);
          sync();
          requestPreview();
        }
        function sync() {
          for (const k of ["lid_height", "lip_depth"])
            document
              .querySelector("[data-p=" + k + "]")
              .closest("label").style.display =
              p.style === "sliding_lid" ? "none" : "grid";
          $("name").value = p.name;
          document
            .querySelectorAll("[data-p]")
            .forEach((e) => (e.value = p[e.dataset.p]));
          for (const key of ["style", "hinge_mode", "screw_size", "quality"])
            $(key).value = p[key];
          for (const key of ["gasket_enabled", "auto_configure_slicer"])
            $(key).checked = p[key];
          $("dividers_x").value = p.dividers_x.join(", ");
          $("dividers_y").value = p.dividers_y.join(", ");
          $("target").value = p.export_target;
          document
            .querySelectorAll(".rugged")
            .forEach(
              (e) =>
                (e.style.display = p.style === "rugged_box" ? "grid" : "none"),
            );
          document
            .querySelectorAll(".screw")
            .forEach(
              (e) =>
                (e.style.display =
                  p.style === "screw_corner" ? "grid" : "none"),
            );
          $("pipNote").textContent =
            p.style === "rugged_box" && p.hinge_mode === "print_in_place"
              ? tr("pip")
              : "";
          features();
          drawPlan();
          buttons();
          render();
        }
        function requestPreview() {
          clearTimeout(timer);
          const request_id = ++serial;
          latest = request_id;
          timer = setTimeout(() => {
            status(tr("generating"));
            p.lang = lang;
            p.theme = theme;
            if (!send({ type: "preview", params: p, request_id }))
              status(tr("noHost"));
          }, 350);
        }
        function change(key, value) {
          snapshot();
          p[key] = value;
          sync();
          requestPreview();
        }
        document
          .querySelectorAll("[data-p]")
          .forEach((e) =>
            e.addEventListener("change", () =>
              change(e.dataset.p, Number(e.value)),
            ),
          );
        for (const key of ["style", "hinge_mode", "screw_size", "quality"])
          $(key).onchange = () => change(key, $(key).value);
        for (const key of ["gasket_enabled", "auto_configure_slicer"])
          $(key).onchange = () => change(key, $(key).checked);
        for (const key of ["dividers_x", "dividers_y"])
          $(key).onchange = () =>
            change(
              key,
              $(key)
                .value.split(",")
                .map((s) => s.trim())
                .filter(Boolean)
                .map(Number)
                .filter(Number.isFinite),
            );
        $("name").onchange = () => change("name", $("name").value);
        $("target").onchange = () => change("export_target", $("target").value);
        $("undo").onclick = () => {
          if (!history.length) return;
          future.push(clone(p));
          p = history.pop();
          sync();
          requestPreview();
        };
        $("redo").onclick = () => {
          if (!future.length) return;
          history.push(clone(p));
          p = future.pop();
          sync();
          requestPreview();
        };
        $("reset").onclick = () => setDesign(INITIAL.params);
        $("lang").onclick = () => {
          lang = lang === "pt" ? "en" : "pt";
          translate();
          sync();
        };
        $("theme").onclick = () => {
          theme = theme === "dark" ? "light" : "dark";
          translate();
        };
        $("sync").onclick = () => send({ type: "sync_printer" });
        $("folder").onclick = () => send({ type: "open_exports_folder" });
        document.addEventListener("keydown", (e) => {
          if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
            e.preventDefault();
            (e.shiftKey ? $("redo") : $("undo")).click();
          }
        });
        document.querySelectorAll("[data-tab]").forEach(
          (b) =>
            (b.onclick = () => {
              tab = b.dataset.tab;
              document
                .querySelectorAll("[data-tab]")
                .forEach((x) => x.classList.toggle("active", x === b));
              document
                .querySelectorAll("[data-section]")
                .forEach((x) =>
                  x.classList.toggle(
                    "section-hidden",
                    x.dataset.section !== tab,
                  ),
                );
              drawPlan();
            }),
        );
        function presets() {
          const list = $("presets");
          list.replaceChildren();
          (INITIAL.presets || []).forEach((s) => {
            const b = document.createElement("button");
            b.className = "preset";
            b.textContent = lang === "pt" ? s.name_pt : s.name_en;
            const small = document.createElement("small");
            small.textContent = `${s.params.width_x} × ${s.params.depth_y} × ${s.params.height_z} mm · ${s.params.style}`;
            b.append(small);
            b.onclick = () => setDesign(s.params);
            list.append(b);
          });
          const user = $("userPresets");
          user.replaceChildren();
          (INITIAL.user_presets || []).forEach((s) => {
            const row = document.createElement("div");
            row.className = "pair";
            const b = document.createElement("button");
            b.textContent = s.name;
            b.onclick = () => setDesign(s.params);
            const del = document.createElement("button");
            del.textContent = "×";
            del.title = tr("delete");
            del.onclick = () =>
              send({ type: "delete_preset", preset_id: s.id });
            row.append(b, del);
            user.append(row);
          });
        }
        $("savePreset").onclick = () =>
          send({ type: "save_preset", params: p, name: p.name });
        function fieldInput(label, value, onchange, step = ".1") {
          const lab = document.createElement("label");
          lab.className = "field";
          const span = document.createElement("span");
          span.textContent = label;
          const inp = document.createElement("input");
          inp.type = "number";
          inp.step = step;
          inp.value = value;
          inp.onchange = () => onchange(Number(inp.value));
          lab.append(span, inp);
          return lab;
        }
        function selectInput(label, value, values, onchange) {
          const lab = document.createElement("label");
          lab.className = "field";
          const span = document.createElement("span");
          span.textContent = label;
          const sel = document.createElement("select");
          values.forEach(([v, text]) => {
            const opt = document.createElement("option");
            opt.value = v;
            opt.textContent = text;
            sel.append(opt);
          });
          sel.value = value;
          sel.onchange = () => onchange(sel.value);
          lab.append(span, sel);
          return lab;
        }
        function featureChange(list, index, key, value) {
          snapshot();
          p[list][index][key] = value;
          drawPlan();
          requestPreview();
        }
        function features() {
          const posts = $("posts");
          posts.replaceChildren();
          p.standoffs.forEach((s, i) => {
            const card = document.createElement("div");
            card.className = "feature";
            const head = document.createElement("div");
            head.className = "featuretitle";
            head.textContent = `PCB ${i + 1}`;
            const del = document.createElement("button");
            del.textContent = "×";
            del.onclick = () => {
              snapshot();
              p.standoffs.splice(i, 1);
              sync();
              requestPreview();
            };
            head.append(del);
            card.append(head);
            const pairs = [
              ["X", "x", "Y", "y"],
              [tr("heightPost"), "height", tr("outer"), "outer_diameter"],
              [tr("hole"), "hole_diameter", tr("holeDepth"), "hole_depth"],
            ];
            pairs.forEach(([a, ka, b, kb]) => {
              const row = document.createElement("div");
              row.className = "pair";
              row.append(
                fieldInput(a, s[ka], (v) =>
                  featureChange("standoffs", i, ka, v),
                ),
                fieldInput(b, s[kb], (v) =>
                  featureChange("standoffs", i, kb, v),
                ),
              );
              card.append(row);
            });
            const row = document.createElement("div");
            row.className = "pair";
            row.append(
              selectInput(
                tr("insert"),
                s.insert,
                [
                  ["M2", "M2"],
                  ["M2.5", "M2.5"],
                  ["M3", "M3"],
                ],
                (v) => {
                  featureChange("standoffs", i, "insert", v);
                },
              ),
              selectInput(
                "Modo / Mode",
                s.mode,
                [
                  ["insert", tr("insert")],
                  ["pilot", tr("pilot")],
                ],
                (v) => {
                  featureChange("standoffs", i, "mode", v);
                  p.standoffs[i].hole_diameter =
                    v === "pilot"
                      ? { M2: 1.6, "M2.5": 2.1, M3: 2.5 }[s.insert] || 2.5
                      : { M2: 3.2, "M2.5": 3.8, M3: 4.2 }[s.insert] || 4.2;
                  features();
                },
              ),
            );
            card.append(row);
            posts.append(card);
          });
          const ports = $("ports");
          ports.replaceChildren();
          p.cutouts.forEach((s, i) => {
            const card = document.createElement("div");
            card.className = "feature";
            const head = document.createElement("div");
            head.className = "featuretitle";
            head.textContent = `${tr("ports")} ${i + 1}`;
            const del = document.createElement("button");
            del.textContent = "×";
            del.onclick = () => {
              snapshot();
              p.cutouts.splice(i, 1);
              sync();
              requestPreview();
            };
            head.append(del);
            card.append(head);
            const row = document.createElement("div");
            row.className = "pair";
            row.append(
              selectInput(
                tr("face"),
                s.face,
                ["front", "back", "left", "right"].map((x) => [x, tr(x)]),
                (v) => featureChange("cutouts", i, "face", v),
              ),
              selectInput(
                tr("kind"),
                s.kind,
                [
                  ["usb_c", "USB-C"],
                  ["hdmi", "HDMI"],
                  ["dc", "DC Ø8"],
                  ["slot", "Slot"],
                  ["hex", "Hex"],
                ],
                (v) => {
                  snapshot();
                  const spec = {
                    usb_c: [10, 4, "rounded"],
                    hdmi: [16, 7, "rounded"],
                    dc: [8, 8, "circle"],
                    slot: [20, 3, "rounded"],
                    hex: [6, 6, "hex"],
                  }[v];
                  Object.assign(s, {
                    kind: v,
                    width: spec[0],
                    height: spec[1],
                    shape: spec[2],
                  });
                  features();
                  requestPreview();
                },
              ),
            );
            card.append(row);
            for (const pair of [
              [
                ["U", "u"],
                ["Z", "z"],
              ],
              [
                [tr("width"), "width"],
                [tr("height"), "height"],
              ],
            ]) {
              const r = document.createElement("div");
              r.className = "pair";
              pair.forEach(([label, key]) =>
                r.append(
                  fieldInput(label, s[key], (v) =>
                    featureChange("cutouts", i, key, v),
                  ),
                ),
              );
              card.append(r);
            }
            ports.append(card);
          });
        }
        $("addPost").onclick = () => {
          snapshot();
          p.standoffs.push({
            x: 0,
            y: 0,
            height: 8,
            outer_diameter: 7,
            hole_diameter: 4.2,
            hole_depth: 5,
            insert: "M3",
            mode: "insert",
          });
          sync();
          requestPreview();
        };
        $("addPort").onclick = () => {
          snapshot();
          p.cutouts.push({
            face: "front",
            kind: "usb_c",
            shape: "rounded",
            u: 0,
            z: Math.max(8, p.height_z / 2),
            width: 10,
            height: 4,
          });
          sync();
          requestPreview();
        };
        function drawPlan() {
          const canvas = $("plan"),
            c = canvas.getContext("2d"),
            w = canvas.width,
            h = canvas.height;
          c.clearRect(0, 0, w, h);
          const s = Math.min((w - 45) / p.width_x, (h - 45) / p.depth_y);
          const cx = w / 2,
            cy = h / 2;
          c.strokeStyle = theme === "dark" ? "#627282" : "#9baaba";
          c.lineWidth = 2;
          c.strokeRect(
            cx - (p.width_x * s) / 2,
            cy - (p.depth_y * s) / 2,
            p.width_x * s,
            p.depth_y * s,
          );
          c.strokeStyle = "#36444f";
          c.lineWidth = 1;
          c.beginPath();
          c.moveTo(10, cy);
          c.lineTo(w - 10, cy);
          c.moveTo(cx, 10);
          c.lineTo(cx, h - 10);
          c.stroke();
          c.fillStyle = "#8b9aa8";
          c.font = "13px Consolas";
          c.fillText("X →", w - 50, cy - 5);
          c.fillText("Y ↑", cx + 6, 18);
          p.dividers_x.forEach((x) => {
            c.strokeStyle = "#00a896";
            c.beginPath();
            c.moveTo(cx + x * s, cy - (p.depth_y * s) / 2);
            c.lineTo(cx + x * s, cy + (p.depth_y * s) / 2);
            c.stroke();
          });
          p.dividers_y.forEach((y) => {
            c.beginPath();
            c.moveTo(cx - (p.width_x * s) / 2, cy - y * s);
            c.lineTo(cx + (p.width_x * s) / 2, cy - y * s);
            c.stroke();
          });
          p.standoffs.forEach((q, i) => {
            c.fillStyle = "#00a896";
            c.beginPath();
            c.arc(
              cx + q.x * s,
              cy - q.y * s,
              (q.outer_diameter * s) / 2,
              0,
              Math.PI * 2,
            );
            c.fill();
            c.fillStyle = theme === "dark" ? "#16181d" : "#fff";
            c.beginPath();
            c.arc(
              cx + q.x * s,
              cy - q.y * s,
              (q.hole_diameter * s) / 2,
              0,
              Math.PI * 2,
            );
            c.fill();
            c.fillStyle = "#ffcf77";
            c.fillText(String(i + 1), cx + q.x * s + 8, cy - q.y * s - 8);
          });
        }
        $("plan").onpointerdown = (e) => {
          const r = $("plan").getBoundingClientRect(),
            x = ((e.clientX - r.left) * 500) / r.width,
            y = ((e.clientY - r.top) * 330) / r.height,
            s = Math.min(455 / p.width_x, 285 / p.depth_y);
          const i = p.standoffs.findIndex(
            (q) =>
              Math.hypot(x - (250 + q.x * s), y - (165 - q.y * s)) <
              Math.max(12, (q.outer_diameter * s) / 2),
          );
          if (i >= 0) {
            snapshot();
            drag = i;
            $("plan").setPointerCapture(e.pointerId);
          }
        };
        $("plan").onpointermove = (e) => {
          if (drag === null) return;
          const r = $("plan").getBoundingClientRect(),
            s = Math.min(455 / p.width_x, 285 / p.depth_y);
          p.standoffs[drag].x =
            Math.round(
              ((((e.clientX - r.left) * 500) / r.width - 250) / s) * 10,
            ) / 10;
          p.standoffs[drag].y =
            Math.round(
              ((165 - ((e.clientY - r.top) * 330) / r.height) / s) * 10,
            ) / 10;
          drawPlan();
        };
        $("plan").onpointerup = () => {
          if (drag !== null) {
            drag = null;
            features();
            requestPreview();
          }
        };
        function busy(on) {
          document.querySelectorAll(".job").forEach((b) => (b.disabled = on));
        }
        function manufacture(type, format) {
          p.export_target = $("target").value;
          p.lang = lang;
          busy(true);
          status(tr("generating"));
          if (
            !send({ type, format, params: p, export_target: p.export_target })
          ) {
            busy(false);
            status(tr("noHost"));
          }
        }
        $("send").onclick = () => manufacture("send_to_plater", "3mf");
        $("stl").onclick = () => manufacture("export_file", "stl");
        $("mf").onclick = () => manufacture("export_file", "3mf");
        function receive(raw) {
          let m = raw?.data ?? raw;
          try {
            if (typeof m === "string") m = JSON.parse(m);
          } catch (_) {
            return;
          }
          if (!m || typeof m !== "object") return;
          if (m.type === "design_changed") {
            p = clone(m.params);
            sync();
            requestPreview();
            return;
          }
          if (m.type === "init_state") {
            if (m.host) {
              INITIAL.host = m.host;
              $("printer").textContent =
                `${m.host.printer_name} · ${m.host.nozzle_mm}mm`;
            }
            if (m.user_presets) {
              INITIAL.user_presets = m.user_presets;
              presets();
            }
            return;
          }
          if (m.type === "presets_result") {
            INITIAL.user_presets = m.user_presets;
            presets();
            return;
          }
          if (m.type === "preview_result") {
            if (m.request_id && m.request_id !== latest) return;
            if (!m.ok) {
              status(m.message, true);
              return;
            }
            p = clone(m.params);
            INITIAL.hinge = m.hinge;
            loadMeshes(m.meshes);
            $("volume").textContent = m.volume_cm3.toFixed(1);
            $("triangles").textContent =
              (
                m.meshes.reduce((s, x) => s + x.triangle_count, 0) / 1000
              ).toFixed(0) + "k";
            const err = Math.max(...m.meshes.map((x) => x.interface_error_mm));
            $("surface").textContent =
              (lang === "pt"
                ? "Alvo de erro nas interfaces curvas ≤ "
                : "Curved interface chord-error target ≤ ") +
              err.toFixed(3) +
              " mm";
            status(tr("ready"));
            sync();
            return;
          }
          if (m.type === "action_result") {
            busy(false);
            status(m.message || String(m.ok), !m.ok);
          }
        }
        window.addEventListener("message", receive);
        if (window.chrome?.webview)
          window.chrome.webview.addEventListener("message", receive);
        if (window.orca?.onMessage) window.orca.onMessage(receive);
        window.receiveBoxMessage = receive;
        // WebGL2: arrays are the exact mesh arrays supplied by the Python exporter.
        let gl = $("gl").getContext("webgl2", { antialias: true, alpha: true }),
          program = null,
          yaw = -0.75,
          pitch = 0.68,
          zoom = 1,
          orbit = null;
        function shader(type, source) {
          const s = gl.createShader(type);
          gl.shaderSource(s, source);
          gl.compileShader(s);
          if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
            throw Error(gl.getShaderInfoLog(s));
          return s;
        }
        function initializeGL() {
          if (!gl) {
            status(
              "WebGL2 indisponível / unavailable. Export remains available.",
              true,
            );
            return;
          }
          program = gl.createProgram();
          gl.attachShader(
            program,
            shader(
              gl.VERTEX_SHADER,
              `#version 300 es\nprecision highp float;in vec3 position;in vec3 normal;uniform mat4 vp;uniform mat4 model;out vec3 n;out vec3 world;void main(){vec4 w=model*vec4(position,1.0);world=w.xyz;n=mat3(model)*normal;gl_Position=vp*w;}`.replaceAll(
                "\\n",
                "\n",
              ),
            ),
          );
          gl.attachShader(
            program,
            shader(
              gl.FRAGMENT_SHADER,
              `#version 300 es\nprecision highp float;in vec3 n;in vec3 world;uniform vec4 color;uniform float cut;out vec4 outColor;void main(){if(world.x>cut)discard;vec3 N=normalize(n);if(!gl_FrontFacing)N=-N;float diffuse=.35+.65*max(0.0,dot(N,normalize(vec3(-.4,-.7,1.0))));outColor=vec4(color.rgb*diffuse,color.a);}`.replaceAll(
                "\\n",
                "\n",
              ),
            ),
          );
          gl.linkProgram(program);
          if (!gl.getProgramParameter(program, gl.LINK_STATUS))
            throw Error(gl.getProgramInfoLog(program));
          gl.enable(gl.DEPTH_TEST);
          gl.enable(gl.BLEND);
          gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        }
        function decode(s, ctor) {
          const b = atob(s),
            a = new Uint8Array(b.length);
          for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
          return new ctor(a.buffer);
        }
        function loadMeshes(items) {
          if (!gl) return;
          meshes.forEach((m) => {
            gl.deleteBuffer(m.pb);
            gl.deleteBuffer(m.nb);
            gl.deleteBuffer(m.ib);
            gl.deleteVertexArray(m.vao);
          });
          meshes = items.map((item) => {
            const pos = decode(item.vertices, Float32Array),
              tri = decode(item.triangles, Uint32Array),
              norm = new Float32Array(pos.length);
            for (let i = 0; i < tri.length; i += 3) {
              let a = tri[i] * 3,
                b = tri[i + 1] * 3,
                c = tri[i + 2] * 3;
              const ux = pos[b] - pos[a],
                uy = pos[b + 1] - pos[a + 1],
                uz = pos[b + 2] - pos[a + 2],
                vx = pos[c] - pos[a],
                vy = pos[c + 1] - pos[a + 1],
                vz = pos[c + 2] - pos[a + 2];
              const nx = uy * vz - uz * vy,
                ny = uz * vx - ux * vz,
                nz = ux * vy - uy * vx;
              for (const j of [a, b, c]) {
                norm[j] += nx;
                norm[j + 1] += ny;
                norm[j + 2] += nz;
              }
            }
            for (let i = 0; i < norm.length; i += 3) {
              const l = Math.hypot(norm[i], norm[i + 1], norm[i + 2]) || 1;
              norm[i] /= l;
              norm[i + 1] /= l;
              norm[i + 2] /= l;
            }
            const vao = gl.createVertexArray();
            gl.bindVertexArray(vao);
            const pb = gl.createBuffer();
            gl.bindBuffer(gl.ARRAY_BUFFER, pb);
            gl.bufferData(gl.ARRAY_BUFFER, pos, gl.STATIC_DRAW);
            const loc = gl.getAttribLocation(program, "position");
            gl.enableVertexAttribArray(loc);
            gl.vertexAttribPointer(loc, 3, gl.FLOAT, false, 0, 0);
            const nb = gl.createBuffer();
            gl.bindBuffer(gl.ARRAY_BUFFER, nb);
            gl.bufferData(gl.ARRAY_BUFFER, norm, gl.STATIC_DRAW);
            const nl = gl.getAttribLocation(program, "normal");
            gl.enableVertexAttribArray(nl);
            gl.vertexAttribPointer(nl, 3, gl.FLOAT, false, 0, 0);
            const ib = gl.createBuffer();
            gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
            gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, tri, gl.STATIC_DRAW);
            return { ...item, vao, pb, nb, ib, count: tri.length };
          });
          render();
        }
        const I = () =>
          new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
        function mult(a, b) {
          const c = new Float32Array(16);
          for (let col = 0; col < 4; col++)
            for (let row = 0; row < 4; row++)
              for (let k = 0; k < 4; k++)
                c[col * 4 + row] += a[k * 4 + row] * b[col * 4 + k];
          return c;
        }
        function translateM(x, y, z) {
          const m = I();
          m[12] = x;
          m[13] = y;
          m[14] = z;
          return m;
        }
        function rotateX(a) {
          const m = I();
          m[5] = Math.cos(a);
          m[6] = Math.sin(a);
          m[9] = -Math.sin(a);
          m[10] = Math.cos(a);
          return m;
        }
        function normalize(v) {
          const l = Math.hypot(...v) || 1;
          return v.map((x) => x / l);
        }
        function cross(a, b) {
          return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
          ];
        }
        function dot(a, b) {
          return a.reduce((s, x, i) => s + x * b[i], 0);
        }
        function camera(aspect) {
          const size =
              (Math.max(p.width_x, p.depth_y, p.height_z) * 1.8) /
              (zoom * Math.max(0.1, Math.min(1, aspect))),
            target = [0, 0, p.height_z * 0.52],
            eye = [
              size * Math.cos(yaw) * Math.cos(pitch),
              size * Math.sin(yaw) * Math.cos(pitch),
              target[2] + size * Math.sin(pitch),
            ],
            z = normalize(eye.map((x, i) => x - target[i])),
            x = normalize(cross([0, 0, 1], z)),
            y = cross(z, x),
            v = new Float32Array([
              x[0],
              y[0],
              z[0],
              0,
              x[1],
              y[1],
              z[1],
              0,
              x[2],
              y[2],
              z[2],
              0,
              -dot(x, eye),
              -dot(y, eye),
              -dot(z, eye),
              1,
            ]),
            f = 1 / Math.tan(Math.PI / 7),
            near = 0.1,
            far = 5000,
            pr = new Float32Array([
              f / aspect,
              0,
              0,
              0,
              0,
              f,
              0,
              0,
              0,
              0,
              (far + near) / (near - far),
              -1,
              0,
              0,
              (2 * far * near) / (near - far),
              0,
            ]);
          return mult(pr, v);
        }
        function render() {
          if (!gl || !program) return;
          const cv = $("gl"),
            r = cv.getBoundingClientRect(),
            dpr = Math.min(devicePixelRatio || 1, 1.7);
          cv.width = Math.max(1, Math.round(r.width * dpr));
          cv.height = Math.max(1, Math.round(r.height * dpr));
          gl.viewport(0, 0, cv.width, cv.height);
          gl.depthMask(true);
          gl.clearColor(0, 0, 0, 0);
          gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
          gl.depthMask(!$("xray").checked);
          gl.useProgram(program);
          gl.uniformMatrix4fv(
            gl.getUniformLocation(program, "vp"),
            false,
            camera(cv.width / cv.height),
          );
          gl.uniform1f(
            gl.getUniformLocation(program, "cut"),
            $("cut").value === "0"
              ? 10000
              : p.width_x / 2 - (p.width_x * Number($("cut").value)) / 100,
          );
          for (const m of meshes) {
            let model = I();
            const opening = Number($("open").value) / 100;
            if (m.part === "lid") {
              if (p.style === "rugged_box") {
                const hinge = INITIAL.hinge || {
                  y: p.depth_y / 2 + 5,
                  z: p.height_z - 4,
                };
                model = mult(
                  translateM(0, hinge.y, hinge.z),
                  mult(
                    rotateX(-opening * Math.PI),
                    translateM(0, -hinge.y, -hinge.z),
                  ),
                );
              } else if (p.style === "sliding_lid")
                model = translateM(0, -opening * (p.depth_y + 10), 0);
              else model = translateM(0, 0, opening * 50);
            }
            if (m.part.startsWith("clip"))
              model = translateM(0, -opening * 15, 0);
            const color =
              m.part === "lid"
                ? [1, 0.74, 0.34]
                : m.part === "gasket"
                  ? [0.7, 0.62, 1]
                  : m.part === "pin"
                    ? [0.35, 0.63, 1]
                    : m.part.startsWith("clip")
                      ? [0.65, 0.78, 0.86]
                      : [0, 0.72, 0.61];
            gl.uniform4fv(gl.getUniformLocation(program, "color"), [
              ...color,
              $("xray").checked ? 0.42 : 1,
            ]);
            gl.uniformMatrix4fv(
              gl.getUniformLocation(program, "model"),
              false,
              model,
            );
            gl.bindVertexArray(m.vao);
            gl.drawElements(gl.TRIANGLES, m.count, gl.UNSIGNED_INT, 0);
          }
        }
        $("gl").onpointerdown = (e) => {
          orbit = [e.clientX, e.clientY];
          $("gl").setPointerCapture(e.pointerId);
        };
        $("gl").onpointermove = (e) => {
          if (!orbit) return;
          yaw -= (e.clientX - orbit[0]) * 0.008;
          pitch = Math.max(
            0.08,
            Math.min(1.5, pitch + (e.clientY - orbit[1]) * 0.008),
          );
          orbit = [e.clientX, e.clientY];
          render();
        };
        $("gl").onpointerup = () => (orbit = null);
        $("gl").onwheel = (e) => {
          e.preventDefault();
          zoom = Math.max(
            0.35,
            Math.min(4, zoom * Math.exp(-e.deltaY * 0.001)),
          );
          render();
        };
        $("home").onclick = () => {
          zoom = 1;
          yaw = -0.75;
          pitch = 0.68;
          render();
        };
        $("open").oninput = () => {
          $("openValue").textContent = $("open").value + "%";
          render();
        };
        $("xray").onchange = render;
        $("cut").oninput = render;
        $("play").onclick = () => {
          playing = !playing;
          $("play").textContent = playing ? "Ⅱ" : "▶";
          if (playing) requestAnimationFrame(tick);
        };
        function tick(t) {
          if (!playing) return;
          $("open").value = 50 - 50 * Math.cos(t * 0.0007);
          $("openValue").textContent = Math.round($("open").value) + "%";
          render();
          requestAnimationFrame(tick);
        }
        window.addEventListener("resize", render);
        document.addEventListener("visibilitychange", () => {
          if (document.hidden) {
            playing = false;
            $("play").textContent = "▶";
          }
        });
        if (INITIAL.mode === "dock") {
          document.body.classList.add("dock");
          document.body.dataset.dockView = "3d";
        }
        try {
          initializeGL();
        } catch (e) {
          status(String(e), true);
        }
        translate();
        sync();
        if (INITIAL.host)
          $("printer").textContent =
            `${INITIAL.host.printer_name} · ${INITIAL.host.nozzle_mm}mm`;
        if (INITIAL.meshes) loadMeshes(INITIAL.meshes);
        else requestPreview();
      })();
    </script>
  </body>
</html>
"""


def get_studio_html(
    mode: str = "page", initial_context: dict[str, Any] | None = None
) -> str:
    pass  # [bundled] resolved intra-package import
    pass  # [bundled] resolved intra-package import

    ctx = dict(initial_context or {})
    ctx.setdefault("params", normalize_params())
    ctx.setdefault("presets", BUILTIN_PRESETS)
    ctx["mode"] = mode
    payload = (
        json.dumps(ctx, ensure_ascii=False, separators=(",", ":"))
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return _BOX_HTML.replace("__BOX_CONTEXT__", payload)

# ===========================================================================
# MODULE: box_studio.linux_ipc
# ===========================================================================

"""OrcaSlicer session-bus transport. No subprocess or third-party package.

Protocol reference: OrcaSlicer v2.5.1 src/slic3r/GUI/InstanceCheck.cpp.
Transport completion does not confirm the host has loaded the objects.
"""

pass  # [bundled] hoisted __future__ import

import ctypes
import os
import re
import sys


def send_linux_plater_request(
    payload: str, *, process_id: int | None = None
) -> tuple[bool, str]:
    """Send only to the Orca instance hosted in this process (or explicit PID)."""
    if not sys.platform.startswith("linux"):
        return False, "Linux session D-Bus transport is unavailable on this platform."
    if not isinstance(payload, str) or not payload or "\x00" in payload:
        return False, "The import request must be a nonempty string without NUL."
    connection = None
    library = None
    try:
        library = ctypes.CDLL("libdbus-1.so.3")
        pointer = ctypes.c_void_p
        string = ctypes.c_char_p
        uint = ctypes.c_uint32
        signatures = {
            "dbus_threads_init_default": (ctypes.c_int, []),
            "dbus_bus_get_private": (pointer, [ctypes.c_int, pointer]),
            "dbus_connection_set_exit_on_disconnect": (None, [pointer, ctypes.c_int]),
            "dbus_message_new_method_call": (pointer, [string, string, string, string]),
            "dbus_message_append_args": (ctypes.c_int, [pointer, ctypes.c_int]),
            "dbus_message_get_args": (ctypes.c_int, [pointer, pointer, ctypes.c_int]),
            "dbus_connection_send_with_reply_and_block": (
                pointer,
                [pointer, pointer, ctypes.c_int, pointer],
            ),
            "dbus_message_get_type": (ctypes.c_int, [pointer]),
            "dbus_message_set_no_reply": (None, [pointer, ctypes.c_int]),
            "dbus_message_set_auto_start": (None, [pointer, ctypes.c_int]),
            "dbus_connection_send": (
                ctypes.c_int,
                [pointer, pointer, ctypes.POINTER(uint)],
            ),
            "dbus_connection_flush": (None, [pointer]),
            "dbus_connection_get_is_connected": (ctypes.c_int, [pointer]),
            "dbus_message_unref": (None, [pointer]),
            "dbus_connection_close": (None, [pointer]),
            "dbus_connection_unref": (None, [pointer]),
            "dbus_free_string_array": (None, [ctypes.POINTER(string)]),
        }
        for name, (result, arguments) in signatures.items():
            function = getattr(library, name)
            function.restype = result
            function.argtypes = arguments
        if not library.dbus_threads_init_default():
            return False, "Unable to initialize D-Bus threading."
        connection = library.dbus_bus_get_private(0, None)
        if not connection:
            return False, "No usable session D-Bus connection; export a 3MF instead."
        library.dbus_connection_set_exit_on_disconnect(connection, 0)

        def daemon_call(method: bytes, argument: str | None = None):
            request = library.dbus_message_new_method_call(
                b"org.freedesktop.DBus",
                b"/org/freedesktop/DBus",
                b"org.freedesktop.DBus",
                method,
            )
            if not request:
                raise RuntimeError("Cannot allocate D-Bus request.")
            try:
                if argument is not None:
                    encoded = string(argument.encode("utf-8"))
                    if not library.dbus_message_append_args(
                        request, ord("s"), ctypes.byref(encoded), ctypes.c_int(0)
                    ):
                        raise RuntimeError("Cannot encode D-Bus request.")
                reply = library.dbus_connection_send_with_reply_and_block(
                    connection, request, 1500, None
                )
                if not reply:
                    raise RuntimeError("D-Bus daemon request timed out or failed.")
                if library.dbus_message_get_type(reply) != 2:
                    library.dbus_message_unref(reply)
                    raise RuntimeError("D-Bus daemon rejected the request.")
                return reply
            finally:
                library.dbus_message_unref(request)

        reply = daemon_call(b"ListNames")
        names = ctypes.POINTER(string)()
        count = ctypes.c_int()
        try:
            if not library.dbus_message_get_args(
                reply,
                None,
                ord("a"),
                ctypes.c_int(ord("s")),
                ctypes.byref(names),
                ctypes.byref(count),
                ctypes.c_int(0),
            ):
                raise RuntimeError("Invalid D-Bus service listing.")
            candidates = [names[i].decode("utf-8") for i in range(count.value)]
        finally:
            if names:
                library.dbus_free_string_array(names)
            library.dbus_message_unref(reply)
        expected_pid = os.getpid() if process_id is None else int(process_id)
        owned = []
        for name in candidates:
            if not re.fullmatch(
                r"com\.orcaslicer\.OrcaSlicer\.InstanceCheck\.Object[0-9]+", name
            ):
                continue
            try:
                reply = daemon_call(b"GetNameOwner", name)
                unique_owner = string()
                try:
                    valid = library.dbus_message_get_args(
                        reply,
                        None,
                        ord("s"),
                        ctypes.byref(unique_owner),
                        ctypes.c_int(0),
                    )
                    if not valid or not unique_owner.value:
                        continue
                    owner = unique_owner.value.decode("utf-8")
                finally:
                    library.dbus_message_unref(reply)
                reply = daemon_call(b"GetConnectionUnixProcessID", owner)
            except RuntimeError:
                continue
            pid = uint()
            try:
                valid = library.dbus_message_get_args(
                    reply, None, ord("u"), ctypes.byref(pid), ctypes.c_int(0)
                )
                if valid and pid.value == expected_pid:
                    owned.append((name, owner))
            finally:
                library.dbus_message_unref(reply)
        if len(owned) != 1:
            return (
                False,
                "Unable to identify exactly one OrcaSlicer service for this process; export a 3MF instead.",
            )
        interface, destination = owned[0]
        suffix = interface.rsplit("Object", 1)[1]
        request = library.dbus_message_new_method_call(
            destination.encode("ascii"),
            ("/com/orcaslicer/OrcaSlicer/InstanceCheck/Object" + suffix).encode(
                "ascii"
            ),
            interface.encode("ascii"),
            b"AnotherInstance",
        )
        if not request:
            return False, "Unable to allocate the import request."
        try:
            encoded = string(payload.encode("utf-8"))
            if not library.dbus_message_append_args(
                request, ord("s"), ctypes.byref(encoded), ctypes.c_int(0)
            ):
                return False, "Unable to encode the import request."
            library.dbus_message_set_no_reply(request, 1)
            library.dbus_message_set_auto_start(request, 0)
            serial = uint()
            if not library.dbus_connection_send(
                connection, request, ctypes.byref(serial)
            ):
                return False, "D-Bus could not queue the import request."
            library.dbus_connection_flush(connection)
            if not library.dbus_connection_get_is_connected(connection):
                return False, "D-Bus disconnected while sending the import request."
            return True, "Import request sent; object loading has not been confirmed."
        finally:
            library.dbus_message_unref(request)
    except (OSError, AttributeError, RuntimeError, ValueError) as error:
        return False, "Linux import unavailable: " + str(error)
    finally:
        if connection and library is not None:
            library.dbus_connection_close(connection)
            library.dbus_connection_unref(connection)

# ===========================================================================
# MODULE: box_studio.plugin_main
# ===========================================================================

"""Native Page/Dock host integration; infrastructure adapted from Orca Gear Studio (MIT)."""

pass  # [bundled] hoisted __future__ import
from collections.abc import Sequence
import copy, ctypes, json, locale, os, re, sys, threading, time, types, base64
from pathlib import Path
from typing import Any, Callable
pass  # [bundled] resolved intra-package import
pass  # [bundled] resolved intra-package import
pass  # [bundled] resolved intra-package import
pass  # [bundled] resolved intra-package import
pass  # [bundled] resolved intra-package import
pass  # [bundled] resolved intra-package import


def _build_fallback_orca_module() -> types.ModuleType:
    """Create a lightweight stand-in when imported outside OrcaSlicer."""
    mod = types.ModuleType("orca")
    mod._registered_capabilities = []
    mod._requested_permissions = {}
    mod._plugin_cls = None

    class PythonPluginBase:
        def __init__(self) -> None:
            self._stored_config: str = "{}"

        def get_name(self) -> str:
            return ""

        def on_load(self) -> None:
            pass

        def on_unload(self) -> None:
            pass

        def has_config_ui(self) -> bool:
            return False

        def get_config_ui(self) -> str:
            return ""

        def get_default_config(self) -> dict[str, Any]:
            return {}

        def get_config(self) -> str:
            return self._stored_config

        def get_config_version(self) -> str:
            return "1.3.0"

        def save_config(self, config: str) -> bool:
            self._stored_config = str(config or "{}")
            return True

    class BasePlugin:
        def __init__(self) -> None:
            pass

        def register_capabilities(self) -> None:
            pass

    class PagesPluginCapabilityBase(PythonPluginBase):
        def get_ui(self) -> str:
            return ""

        def get_icon(self) -> str:
            return ""

        def on_message(self, data: Any) -> None:
            pass

        def post_message(self, data: Any) -> None:
            pass

    class ScriptPluginCapabilityBase(PythonPluginBase):
        def execute(self) -> Any:
            return None

    class PluginResult:
        Success = 0
        Skipped = 1
        RecoverableError = 2
        FatalError = 3

    class ExecutionResult:
        def __init__(self, status: int = 0, message: str = "", data: str = "") -> None:
            self.status = status
            self.message = message
            self.data = data

        @classmethod
        def success(cls, message: str = "", data: str = "") -> "ExecutionResult":
            return cls(PluginResult.Success, message, data)

        @classmethod
        def skipped(cls, message: str = "") -> "ExecutionResult":
            return cls(PluginResult.Skipped, message, "")

        @classmethod
        def failure(
            cls, status: int, message: str, data: str = ""
        ) -> "ExecutionResult":
            return cls(status, message, data)

    def plugin_decorator(cls: type) -> type:
        mod._plugin_cls = cls
        return cls

    def register_capability(cap_cls: type) -> None:
        mod._registered_capabilities.append(cap_cls)

    def request_permissions(**kwargs: Any) -> None:
        mod._requested_permissions.update(kwargs)

    pages_mod = types.ModuleType("orca.pages")
    pages_mod.PagesPluginCapabilityBase = PagesPluginCapabilityBase

    script_mod = types.ModuleType("orca.script")
    script_mod.ScriptPluginCapabilityBase = ScriptPluginCapabilityBase

    plugin_sub = types.ModuleType("orca.plugin")
    plugin_sub.storage = lambda: str(Path(__file__).resolve().parent)

    class NotificationLevel:
        RegularNotificationLevel = 0
        HintNotificationLevel = 1
        ProgressBarNotificationLevel = 2
        PrintInfoNotificationLevel = 3
        PrintInfoShortNotificationLevel = 4
        ImportantNotificationLevel = 5
        WarningNotificationLevel = 6
        SeriousWarningNotificationLevel = 7
        ErrorNotificationLevel = 8

    host_mod = types.ModuleType("orca.host")
    host_mod.app_language = lambda: "pt_BR"
    host_mod.app_info = lambda: {"version": "2.5.1", "language": "pt_BR"}
    host_mod.preset_bundle = lambda: None
    host_mod.plater = lambda: None
    host_mod.model = lambda: None
    host_mod.selected_printer = lambda: None
    host_mod.plugin = plugin_sub
    host_mod.ui = types.SimpleNamespace(
        NotificationLevel=NotificationLevel,
        create_dock_panel=None,
        create_window=None,
        push_notification=None,
        message=None,
    )
    host_mod.preset = types.SimpleNamespace(
        process=None,
        printer=None,
        filament=None,
    )

    mod.base = BasePlugin
    mod.PythonPluginBase = PythonPluginBase
    mod.PluginResult = PluginResult
    mod.ExecutionResult = ExecutionResult
    mod.plugin = plugin_decorator
    mod.register_capability = register_capability
    mod.request_permissions = request_permissions
    mod.pages = pages_mod
    mod.script = script_mod
    mod.host = host_mod

    return mod


try:
    import orca  # type: ignore[import-not-found]
except ImportError:
    orca = _build_fallback_orca_module()


PLUGIN_SLUG = "orca_box_generator"
WM_COPYDATA = 0x004A
SMTO_ABORTIFHUNG = 0x0002
ORCA_OTHER_INSTANCE_DWDATA = 1

ICON_SVG_CONTENT: str = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" fill="none"><ellipse cx="32" cy="56" rx="25" ry="5" stroke="#00bfa5" opacity=".4"/><path d="M8 27 32 16 56 27 32 39Z" fill="#00a896" stroke="#a7ffeb" stroke-width="1.5"/><path d="M8 27V47L32 58V39M56 27V47L32 58" fill="#00796b" stroke="#80ffea" stroke-width="1.5"/><path d="M8 16 32 5 56 16 32 27Z" fill="#26333c" stroke="#ffcf77" stroke-width="1.5"/><path d="M8 16V20L32 31 56 20V16M32 27V31" stroke="#ffcf77" stroke-width="1.5"/></svg>'


# ---------------------------------------------------------------------------
# Cross-Platform Environment, Storage & In-Process Plater IPC (Win32 + macOS)
# ---------------------------------------------------------------------------

_MACOS_PENDING_DISPATCH_CBS: list[Any] = []


def _is_native_orca_host() -> bool:
    """Return True only when running inside the real C++ pybind11 OrcaSlicer host."""
    base_cls = getattr(orca, "base", None)
    return base_cls is not None and type(base_cls).__name__ == "pybind11_type"


def _is_mock_callable(obj: Any) -> bool:
    """Detect unittest.mock objects without importing unittest.mock eagerly."""
    cls_mod = getattr(type(obj), "__module__", "")
    return cls_mod.startswith("unittest.mock")


def _orca_user_config_root(platform_name: str | None = None) -> Path:
    """Return OrcaSlicer's user configuration directory on Windows, macOS, and Linux."""
    plat = platform_name or sys.platform
    if plat == "win32":
        appdata = os.environ.get("APPDATA", "").strip()
        if appdata:
            return Path(appdata) / "OrcaSlicer"
        return Path.home() / "AppData" / "Roaming" / "OrcaSlicer"
    if plat == "darwin":
        return Path.home() / "Library" / "Application Support" / "OrcaSlicer"
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg) if xdg else (Path.home() / ".config")
    return base / "OrcaSlicer"


def _default_installed_plugin_dir() -> Path:
    return _orca_user_config_root() / "orca_plugins" / PLUGIN_SLUG


def _default_plugin_data_dir() -> Path:
    return _orca_user_config_root() / "orca_plugins" / "plugin_data" / PLUGIN_SLUG


def _resolve_storage_dir() -> Path:
    """Resolve current plugin storage folder safely (inside or outside callbacks)."""
    # 1. Try orca.plugin.storage() or orca.host.plugin.storage()
    for holder in (
        getattr(orca, "plugin", None),
        getattr(getattr(orca, "host", None), "plugin", None),
    ):
        storage_fn = getattr(holder, "storage", None)
        if callable(storage_fn):
            try:
                raw = storage_fn()
                if isinstance(raw, (str, os.PathLike)) and str(raw).strip():
                    return Path(raw)
            except Exception:
                pass

    # 2. In native OrcaSlicer, prefer `plugin_data/orca_box_generator`
    if _is_native_orca_host():
        data_dir = _default_plugin_data_dir()
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir
        except Exception:
            pass

    # 3. Fallback to __file__ parent if available
    try:
        here = Path(__file__).resolve().parent
        if here.exists():
            return here
    except Exception:
        pass

    return _default_installed_plugin_dir()


def _format_other_instance_payload(file_paths: Sequence[str | Path]) -> str:
    """Format Win32 `WM_COPYDATA` payload matching `OrcaSlicer.dll` `unescape_strings_cstyle`.

    Produces `"orca-slicer.exe";"<resolved_path_1>";...` where every token escapes
    `\\` -> `\\\\`, `"` -> `\\"`, `\\r` -> `\\r`, `\\n` -> `\\n`, wrapped in double quotes and
    joined by `;` with NO trailing `;` (`OtherInstanceMessageHandler::handle_message` skips `args[0]`).
    """
    resolved_files = [str(Path(p).resolve()) for p in file_paths if str(p).strip()]
    if not resolved_files:
        raise ValueError("file_paths must contain at least one model path")

    tokens = ["orca-slicer.exe", *resolved_files]
    escaped: list[str] = []
    for tok in tokens:
        s = (
            tok.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\r", "\\r")
            .replace("\n", "\\n")
        )
        escaped.append(f'"{s}"')
    return ";".join(escaped)


def _find_orca_mainframe_hwnd(target_pid: int | None = None) -> int | None:
    """Locate OrcaSlicer's `MainFrame` `wxWindowNR` `HWND` in `target_pid` (`os.getpid()` by default).

    Prefers `wxWindowNR` windows marked with OrcaSlicer's `Instance_Hash_Minor` or
    `Instance_Hash_Major` properties, falling back to a visible top-level `wxWindowNR` of that PID.
    """
    if sys.platform != "win32":
        return None

    from ctypes import wintypes

    pid = int(target_pid) if target_pid is not None else os.getpid()
    user32 = ctypes.windll.user32

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    enum_windows = user32.EnumWindows
    if not _is_mock_callable(enum_windows):
        enum_windows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
        enum_windows.restype = wintypes.BOOL

    get_pid = user32.GetWindowThreadProcessId
    if not _is_mock_callable(get_pid):
        get_pid.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        get_pid.restype = wintypes.DWORD

    get_class = user32.GetClassNameW
    if not _is_mock_callable(get_class):
        get_class.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        get_class.restype = ctypes.c_int

    get_prop = user32.GetPropW
    if not _is_mock_callable(get_prop):
        get_prop.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
        get_prop.restype = wintypes.HANDLE

    is_visible = user32.IsWindowVisible
    if not _is_mock_callable(is_visible):
        is_visible.argtypes = [wintypes.HWND]
        is_visible.restype = wintypes.BOOL

    get_parent = user32.GetParent
    if not _is_mock_callable(get_parent):
        get_parent.argtypes = [wintypes.HWND]
        get_parent.restype = wintypes.HWND

    hash_visible: list[int] = []
    hash_any: list[int] = []
    fallback_visible: list[int] = []

    def _enum_cb(hwnd: int, _lparam: int) -> bool:
        if not hwnd:
            return True
        win_pid = wintypes.DWORD(0)
        get_pid(hwnd, ctypes.byref(win_pid))
        if int(win_pid.value) != pid:
            return True

        cls_buf = ctypes.create_unicode_buffer(64)
        cls_len = get_class(hwnd, cls_buf, 64)
        if cls_len <= 0 or cls_buf.value != "wxWindowNR":
            return True

        minor = get_prop(hwnd, "Instance_Hash_Minor")
        major = get_prop(hwnd, "Instance_Hash_Major")
        vis = bool(is_visible(hwnd))
        hwnd_int = int(hwnd)

        if bool(minor) or bool(major):
            if vis:
                hash_visible.append(hwnd_int)
            else:
                hash_any.append(hwnd_int)
        elif vis and not get_parent(hwnd):
            fallback_visible.append(hwnd_int)
        return True

    cb_ref = WNDENUMPROC(_enum_cb)
    enum_windows(cb_ref, 0)

    if hash_visible:
        return hash_visible[0]
    if hash_any:
        return hash_any[0]
    if fallback_visible:
        return fallback_visible[0]
    return None


class _COPYDATASTRUCT(ctypes.Structure):
    _fields_ = [
        ("dwData", ctypes.c_size_t),
        ("cbData", ctypes.c_uint32),
        ("lpData", ctypes.c_void_p),
    ]


def _dispatch_copydata_to_hwnd(
    hwnd: int,
    payload_str: str,
    timeout_ms: int = 5000,
) -> tuple[bool, str]:
    """Send UTF-16LE `WM_COPYDATA` (`dwData = 1`) to `hwnd` via `SendMessageTimeoutW` (`0x0002`)."""
    if not hwnd or int(hwnd) <= 0:
        return (False, "OrcaSlicer MainFrame HWND not found")
    if not payload_str:
        return (False, "Empty WM_COPYDATA payload")
    if sys.platform != "win32":
        return (False, "WM_COPYDATA requires win32")

    from ctypes import wintypes

    wchar_buf = ctypes.create_unicode_buffer(payload_str)
    cds = _COPYDATASTRUCT(
        dwData=ORCA_OTHER_INSTANCE_DWDATA,
        cbData=ctypes.sizeof(wchar_buf),
        lpData=ctypes.cast(wchar_buf, ctypes.c_void_p),
    )
    result = ctypes.c_size_t(0)

    user32 = ctypes.windll.user32
    send_msg = user32.SendMessageTimeoutW
    if not _is_mock_callable(send_msg):
        send_msg.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            ctypes.c_void_p,
            wintypes.UINT,
            wintypes.UINT,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        send_msg.restype = ctypes.c_size_t

    ret = send_msg(
        int(hwnd),
        WM_COPYDATA,
        0,
        ctypes.byref(cds),
        SMTO_ABORTIFHUNG,
        max(100, int(timeout_ms)),
        ctypes.byref(result),
    )
    if not ret:
        err = ctypes.windll.kernel32.GetLastError()
        return (False, f"SendMessageTimeoutW failed (GetLastError={err})")
    return (True, "ok")


class _MacDispatchQueueS(ctypes.Structure):
    pass


def _load_macos_objc_and_gcd() -> tuple[Any, Any]:
    """Load Objective-C runtime (`libobjc`) and GCD (`libSystem`) on macOS (`arm64` & `x86_64`)."""
    for fw in (
        "/System/Library/Frameworks/Foundation.framework/Foundation",
        "/System/Library/Frameworks/AppKit.framework/AppKit",
    ):
        try:
            ctypes.CDLL(fw)
        except OSError:
            pass

    objc = None
    for cand in ("/usr/lib/libobjc.A.dylib", "libobjc.A.dylib", "libobjc.dylib"):
        try:
            objc = ctypes.CDLL(cand)
            break
        except OSError:
            continue
    if objc is None:
        raise RuntimeError("Could not load macOS libobjc.A.dylib")

    libsystem = None
    for cand in ("/usr/lib/libSystem.B.dylib", "libSystem.B.dylib", "libSystem.dylib"):
        try:
            libsystem = ctypes.CDLL(cand)
            break
        except OSError:
            continue
    if libsystem is None:
        raise RuntimeError("Could not load macOS libSystem.B.dylib")

    if not _is_mock_callable(objc.objc_getClass):
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.objc_getClass.restype = ctypes.c_void_p
    if not _is_mock_callable(objc.sel_registerName):
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p

    return objc, libsystem


def _resolve_macos_app_bundle_path() -> str | None:
    """Find running `.app` bundle path on macOS from `sys.executable` or `/Applications`."""
    try:
        exe_resolved = Path(sys.executable).resolve()
        for parent in exe_resolved.parents:
            if parent.suffix.lower() == ".app" and parent.is_dir():
                return str(parent)
    except Exception:
        pass

    for cand in (
        Path("/Applications/OrcaSlicer.app"),
        Path.home() / "Applications" / "OrcaSlicer.app",
    ):
        try:
            if cand.is_dir():
                return str(cand)
        except Exception:
            continue
    return None


def _dispatch_macos_open_files(
    file_paths: Sequence[str | Path],
    timeout_ms: int = 5000,
) -> tuple[bool, str]:
    """Send model files in-process to OrcaSlicer's Cocoa `wxAppController` on macOS (`darwin`).

    Marshals onto the Cocoa main queue (`_dispatch_main_q`) using ARM64-safe typed `CFUNCTYPE`
    wrappers around `objc_msgSend`, invoking `[NSApp.delegate application:NSApp openFiles:paths]`
    (`GUI_App::MacOpenFiles` -> `Plater::load_files`), with `NSWorkspace` fallback if needed.
    Requires ZERO external `subprocess` permissions.
    """
    if sys.platform != "darwin":
        return (False, "Cocoa openFiles dispatch requires darwin")

    resolved_files = [str(Path(p).resolve()) for p in file_paths if str(p).strip()]
    if not resolved_files:
        return (False, "Empty file_paths for macOS Plater dispatch")

    try:
        objc, libsystem = _load_macos_objc_and_gcd()
    except Exception as exc:
        return (False, f"macOS Objective-C load error: {exc}")

    msg_addr = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value
    if not msg_addr:
        return (False, "objc_msgSend address unavailable")

    # Non-variadic ARM64 & x86_64 ABI-safe Objective-C message wrappers
    msg_id0 = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(
        msg_addr
    )
    msg_void0 = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)(msg_addr)
    msg_id_cstr = ctypes.CFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p
    )(msg_addr)
    msg_id_id = ctypes.CFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )(msg_addr)
    msg_void_id = ctypes.CFUNCTYPE(
        None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )(msg_addr)
    msg_bool_sel = ctypes.CFUNCTYPE(
        ctypes.c_byte, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )(msg_addr)
    msg_bool_id_id = ctypes.CFUNCTYPE(
        ctypes.c_byte,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )(msg_addr)
    msg_void_id_id = ctypes.CFUNCTYPE(
        None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )(msg_addr)
    msg_open_urls = ctypes.CFUNCTYPE(
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )(msg_addr)

    cls_pool = objc.objc_getClass(b"NSAutoreleasePool")
    cls_app = objc.objc_getClass(b"NSApplication")
    cls_str = objc.objc_getClass(b"NSString")
    cls_url = objc.objc_getClass(b"NSURL")
    cls_arr = objc.objc_getClass(b"NSMutableArray")
    cls_ws = objc.objc_getClass(b"NSWorkspace")
    cls_bundle = objc.objc_getClass(b"NSBundle")

    sel_alloc = objc.sel_registerName(b"alloc")
    sel_init = objc.sel_registerName(b"init")
    sel_drain = objc.sel_registerName(b"drain")
    sel_shared_app = objc.sel_registerName(b"sharedApplication")
    sel_delegate = objc.sel_registerName(b"delegate")
    sel_responds = objc.sel_registerName(b"respondsToSelector:")
    sel_open_files = objc.sel_registerName(b"application:openFiles:")
    sel_open_file = objc.sel_registerName(b"application:openFile:")
    sel_str_utf8 = objc.sel_registerName(b"stringWithUTF8String:")
    sel_file_url = objc.sel_registerName(b"fileURLWithPath:")
    sel_array = objc.sel_registerName(b"array")
    sel_add_obj = objc.sel_registerName(b"addObject:")
    sel_shared_ws = objc.sel_registerName(b"sharedWorkspace")
    sel_main_bundle = objc.sel_registerName(b"mainBundle")
    sel_bundle_url = objc.sel_registerName(b"bundleURL")
    sel_open_urls = objc.sel_registerName(
        b"openURLs:withApplicationAtURL:options:configuration:error:"
    )

    done_evt = threading.Event()
    result_box: dict[str, Any] = {
        "ok": False,
        "msg": "macOS main-queue callback pending",
    }

    DISPATCH_FN = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

    def _run_on_cocoa_main(_ctx: int) -> None:
        pool = msg_id0(msg_id0(cls_pool, sel_alloc), sel_init) if cls_pool else None
        try:
            ns_paths = msg_id0(cls_arr, sel_array)
            ns_urls = msg_id0(cls_arr, sel_array)
            for fp in resolved_files:
                ns_s = msg_id_cstr(cls_str, sel_str_utf8, fp.encode("utf-8"))
                if ns_s:
                    msg_void_id(ns_paths, sel_add_obj, ns_s)
                    if cls_url:
                        ns_u = msg_id_id(cls_url, sel_file_url, ns_s)
                        if ns_u:
                            msg_void_id(ns_urls, sel_add_obj, ns_u)

            ns_app = msg_id0(cls_app, sel_shared_app) if cls_app else None
            delegate = msg_id0(ns_app, sel_delegate) if ns_app else None

            if delegate and bool(msg_bool_sel(delegate, sel_responds, sel_open_files)):
                msg_void_id_id(delegate, sel_open_files, ns_app, ns_paths)
                result_box["ok"] = True
                result_box["msg"] = "ok (NSApp.delegate application:openFiles:)"
                return

            if delegate and bool(msg_bool_sel(delegate, sel_responds, sel_open_file)):
                all_ok = True
                for fp in resolved_files:
                    ns_s = msg_id_cstr(cls_str, sel_str_utf8, fp.encode("utf-8"))
                    if not bool(msg_bool_id_id(delegate, sel_open_file, ns_app, ns_s)):
                        all_ok = False
                if all_ok:
                    result_box["ok"] = True
                    result_box["msg"] = "ok (NSApp.delegate application:openFile:)"
                    return

            # Fallback to NSWorkspace openURLs with running bundle URL
            ws = msg_id0(cls_ws, sel_shared_ws) if cls_ws else None
            app_url = None
            if cls_bundle:
                mb = msg_id0(cls_bundle, sel_main_bundle)
                if mb:
                    app_url = msg_id0(mb, sel_bundle_url)
            if not app_url:
                app_path = _resolve_macos_app_bundle_path()
                if app_path and cls_url:
                    ns_app_s = msg_id_cstr(
                        cls_str, sel_str_utf8, app_path.encode("utf-8")
                    )
                    app_url = msg_id_id(cls_url, sel_file_url, ns_app_s)
            if ws and app_url and ns_urls:
                run_app = msg_open_urls(
                    ws, sel_open_urls, ns_urls, app_url, 0, None, None
                )
                if run_app:
                    result_box["ok"] = True
                    result_box["msg"] = "ok (NSWorkspace openURLs)"
                    return

            result_box["ok"] = False
            result_box["msg"] = (
                "No Cocoa openFiles delegate or NSWorkspace target responded"
            )
        except Exception as inner_exc:
            result_box["ok"] = False
            result_box["msg"] = f"Cocoa main-queue exception: {inner_exc}"
        finally:
            if pool:
                try:
                    msg_void0(pool, sel_drain)
                except Exception:
                    pass
            done_evt.set()

    c_cb = DISPATCH_FN(_run_on_cocoa_main)
    _MACOS_PENDING_DISPATCH_CBS.append(c_cb)

    try:
        main_q = ctypes.cast(
            ctypes.byref(_MacDispatchQueueS.in_dll(libsystem, "_dispatch_main_q")),
            ctypes.c_void_p,
        )
        dispatch_async_f = libsystem.dispatch_async_f
        if not _is_mock_callable(dispatch_async_f):
            dispatch_async_f.argtypes = [ctypes.c_void_p, ctypes.c_void_p, DISPATCH_FN]
            dispatch_async_f.restype = None
        dispatch_async_f(main_q, None, c_cb)
    except Exception as exc:
        if c_cb in _MACOS_PENDING_DISPATCH_CBS:
            _MACOS_PENDING_DISPATCH_CBS.remove(c_cb)
        return (False, f"dispatch_async_f failed: {exc}")

    finished = done_evt.wait(timeout=max(0.2, float(timeout_ms) / 1000.0))
    if finished and c_cb in _MACOS_PENDING_DISPATCH_CBS:
        _MACOS_PENDING_DISPATCH_CBS.remove(c_cb)

    if not finished:
        return (False, "Timed out waiting for Cocoa main-queue openFiles")
    return (bool(result_box["ok"]), str(result_box["msg"]))


def _open_folder_native(folder_path: Path) -> bool:
    """Open `folder_path` in Explorer (Windows) or Finder (macOS) without `subprocess`."""
    resolved = str(Path(folder_path).resolve())
    if sys.platform == "win32":
        startfile_fn = getattr(os, "startfile", None)
        if callable(startfile_fn):
            startfile_fn(resolved)
            return True
        return False

    if sys.platform == "darwin":
        objc, _ = _load_macos_objc_and_gcd()
        msg_addr = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value
        if not msg_addr:
            return False
        msg_id0 = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(
            msg_addr
        )
        msg_id_cstr = ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p
        )(msg_addr)
        msg_id_id = ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )(msg_addr)
        msg_bool_id = ctypes.CFUNCTYPE(
            ctypes.c_byte, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )(msg_addr)

        cls_str = objc.objc_getClass(b"NSString")
        cls_url = objc.objc_getClass(b"NSURL")
        cls_ws = objc.objc_getClass(b"NSWorkspace")
        sel_str_utf8 = objc.sel_registerName(b"stringWithUTF8String:")
        sel_file_url = objc.sel_registerName(b"fileURLWithPath:")
        sel_shared_ws = objc.sel_registerName(b"sharedWorkspace")
        sel_open_url = objc.sel_registerName(b"openURL:")

        ns_s = msg_id_cstr(cls_str, sel_str_utf8, resolved.encode("utf-8"))
        ns_u = msg_id_id(cls_url, sel_file_url, ns_s) if ns_s else None
        ws = msg_id0(cls_ws, sel_shared_ws) if cls_ws else None
        if ws and ns_u:
            return bool(msg_bool_id(ws, sel_open_url, ns_u))
        return False

    return False


def _dispatch_files_to_plater(
    file_paths: Sequence[str | Path],
    timeout_ms: int = 5000,
) -> tuple[bool, str, int | None]:
    """Cross-platform in-process Plater file loader for Windows (`win32`) and macOS (`darwin`)."""
    if sys.platform == "win32":
        copydata_payload = _format_other_instance_payload(file_paths)
        hwnd = _find_orca_mainframe_hwnd()
        ok, msg = _dispatch_copydata_to_hwnd(
            hwnd or 0, copydata_payload, timeout_ms=timeout_ms
        )
        return (ok, msg, hwnd)

    if sys.platform == "darwin":
        ok, msg = _dispatch_macos_open_files(file_paths, timeout_ms=timeout_ms)
        return (ok, msg, None)

    if sys.platform.startswith("linux"):
        ok, message = send_linux_plater_request(
            _format_other_instance_payload(file_paths)
        )
        return ok, message, None
    return (False, f"Unsupported platform: {sys.platform}", None)


def _slugify_filename(name: str, fallback: str = "caixas") -> str:
    """Slugify filename while scrubbing OrcaSlicer `PluginAuditManager` denied path keywords
    (`secret`, `cert`, `conf` — which C++ `is_denied_path_keyword` blocks case-insensitively).
    """
    cleaned = re.sub(r"[^\w\-. ]+", "", str(name or "").strip(), flags=re.ASCII)
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._-")
    cleaned = re.sub(r"secret", "secr", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"cert", "crt", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"conf", "cfg", cleaned, flags=re.IGNORECASE)
    if not cleaned:
        return fallback
    return cleaned[:64]


def _extract_first_float(val: Any, default: float) -> float:
    if val is None:
        return default
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        f = float(val)
        return f if f == f else default
    if isinstance(val, (list, tuple)):
        for item in val:
            res = _extract_first_float(item, float("nan"))
            if res == res:
                return res
        return default
    s = str(val).strip()
    if not s:
        return default
    m = re.search(r"[-+]?\d*\.?\d+", s)
    if not m:
        return default
    try:
        return float(m.group(0))
    except ValueError:
        return default


def _parse_printable_area(
    raw: Any, default_x: float = 220.0, default_y: float = 220.0
) -> tuple[float, float]:
    """Parse OrcaSlicer `printable_area` into `(bed_x_mm, bed_y_mm)`."""
    if raw is None:
        return (default_x, default_y)

    xs: list[float] = []
    ys: list[float] = []

    tokens: list[Any]
    if isinstance(raw, str):
        s = raw.strip()
        if s.startswith("["):
            try:
                parsed = json.loads(s)
                tokens = parsed if isinstance(parsed, list) else [s]
            except Exception:
                tokens = re.split(r"[;,]+", s)
        else:
            tokens = re.split(r"[;,]+", s)
    elif isinstance(raw, (list, tuple)):
        tokens = list(raw)
    else:
        return (default_x, default_y)

    for tok in tokens:
        if isinstance(tok, (list, tuple)) and len(tok) >= 2:
            try:
                xs.append(float(tok[0]))
                ys.append(float(tok[1]))
            except (TypeError, ValueError):
                continue
        elif isinstance(tok, str):
            m = re.search(r"([-+]?\d*\.?\d+)\s*[xX:]\s*([-+]?\d*\.?\d+)", tok)
            if m:
                try:
                    xs.append(float(m.group(1)))
                    ys.append(float(m.group(2)))
                except ValueError:
                    continue

    if len(xs) >= 2 and len(ys) >= 2:
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        if dx >= 30.0 and dy >= 30.0:
            return (round(dx, 2), round(dy, 2))

    return (default_x, default_y)


def _parse_line_width(raw: Any, nozzle_mm: float) -> float:
    default_lw = round(nozzle_mm * 1.05, 2)
    if raw is None:
        return default_lw
    if isinstance(raw, (list, tuple)):
        return _parse_line_width(raw[0] if raw else None, nozzle_mm)
    s = str(raw).strip()
    if not s:
        return default_lw
    if s.endswith("%"):
        pct = _extract_first_float(s[:-1], 0.0)
        if pct > 10.0:
            return round(max(0.2, min(2.5, nozzle_mm * (pct / 100.0))), 3)
        return default_lw
    val = _extract_first_float(s, 0.0)
    if val <= 0.05:
        return default_lw
    return round(max(0.2, min(2.5, val)), 3)


def _extract_preset_name(obj: Any, fallback: str = "") -> str:
    if obj is None:
        return fallback
    if isinstance(obj, str):
        return obj.strip() or fallback
    if isinstance(obj, dict):
        for k in ("name", "preset_name", "id"):
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return fallback
    for attr in ("name", "preset_name"):
        try:
            val = getattr(obj, attr, None)
            if callable(val):
                val = val()
            if isinstance(val, str) and val.strip():
                return val.strip()
        except Exception:
            continue
    return fallback


def _bundle_get_value(bundle: Any, key: str) -> Any:
    if bundle is None:
        return None
    for method_name in ("full_config_value", "config_value", "get"):
        fn = getattr(bundle, method_name, None)
        if callable(fn):
            try:
                val = fn(key)
                if val is not None and val != "":
                    return val
            except Exception:
                continue
    return None


def _detect_language(app_info: dict[str, Any]) -> str:
    raw = str(app_info.get("language") or app_info.get("lang") or "").strip().lower()
    if raw.startswith("en"):
        return "en"
    if raw.startswith("pt"):
        return "pt"
    if raw:
        return "en" if not raw.startswith("pt") else "pt"
    try:
        loc = (locale.getlocale()[0] or "").lower()
        if loc.startswith("en"):
            return "en"
        if loc.startswith("pt"):
            return "pt"
    except Exception:
        pass
    return "pt"


def _detect_theme(app_info: dict[str, Any]) -> str:
    theme_raw = (
        str(app_info.get("theme") or app_info.get("color_mode") or "").strip().lower()
    )
    if theme_raw == "light":
        return "light"
    if theme_raw == "dark":
        return "dark"
    if app_info.get("dark_mode") is False:
        return "light"
    return "dark"


def _make_execution_result_success(message: str) -> Any:
    exec_cls = getattr(orca, "ExecutionResult", None)
    if exec_cls is not None:
        success_fn = getattr(exec_cls, "success", None)
        if callable(success_fn):
            try:
                return success_fn(message)
            except TypeError:
                return success_fn(message, "")
        try:
            ok_code = getattr(getattr(orca, "PluginResult", None), "Success", 0)
            return exec_cls(ok_code, message, "")
        except Exception:
            pass
    return {"status": "Success", "message": message}


# ---------------------------------------------------------------------------
# Shared Box Studio Session & Message Router
# ---------------------------------------------------------------------------


class BoxStudioController:
    """One shared design; geometry and exports run off the host UI thread."""

    def __init__(self):
        self._lock = threading.RLock()
        self._current_params = normalize_params()
        self._preview_serial = 0
        self._last_worker = None
        self._mesh_cache = {}
        self._subscriptions = {}
        self._preview_waiters = {}

    def current_params(self):
        with self._lock:
            return copy.deepcopy(self._current_params)

    def set_current_params(self, raw):
        result = normalize_params(raw)
        with self._lock:
            self._current_params = result
        return copy.deepcopy(result)

    def get_presets_dir(self):
        return _resolve_storage_dir() / "presets"

    def get_export_dir(self):
        path = _resolve_storage_dir() / "exports"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def read_host_context(self) -> dict[str, Any]:
        """Defensively inspect `orca.host.app_language()` and `orca.host.preset_bundle()`."""
        app_info: dict[str, Any] = {}
        host = getattr(orca, "host", None)
        if host is not None:
            # Official OrcaSlicer API Reference (`orca.host.app_language()`)
            app_lang_fn = getattr(host, "app_language", None)
            if callable(app_lang_fn):
                try:
                    raw_lang = app_lang_fn()
                    if isinstance(raw_lang, str) and raw_lang.strip():
                        app_info["language"] = raw_lang.strip()
                except Exception:
                    pass

            app_info_fn = getattr(host, "app_info", None)
            if callable(app_info_fn):
                try:
                    info = app_info_fn()
                    if isinstance(info, dict):
                        for k, v in info.items():
                            app_info.setdefault(k, v)
                except Exception:
                    pass

        lang = _detect_language(app_info)
        theme = _detect_theme(app_info)
        theme_explicit = bool(
            app_info.get("theme")
            or app_info.get("color_mode")
            or ("dark_mode" in app_info)
        )
        orca_version = str(app_info.get("version") or "2.5.1")

        bundle = None
        if host is not None:
            bundle_fn = getattr(host, "preset_bundle", None)
            if callable(bundle_fn):
                try:
                    bundle = bundle_fn()
                except Exception:
                    bundle = None

        printer_name = "Generic FDM 220x220"
        process_name = "0.20mm Standard"
        filament_name = "Generic PLA"

        if bundle is not None:
            for m in ("current_printer_preset",):
                fn = getattr(bundle, m, None)
                if callable(fn):
                    try:
                        printer_name = _extract_preset_name(fn(), printer_name)
                    except Exception:
                        pass

            for m in ("current_print_preset", "current_process_preset"):
                fn = getattr(bundle, m, None)
                if callable(fn):
                    try:
                        got = _extract_preset_name(fn(), "")
                        if got:
                            process_name = got
                            break
                    except Exception:
                        pass

            for m in ("current_filament_preset_names", "current_filament_presets"):
                fn = getattr(bundle, m, None)
                if callable(fn):
                    try:
                        fils = fn()
                        if isinstance(fils, (list, tuple)) and fils:
                            got = _extract_preset_name(fils[0], "")
                            if got:
                                filament_name = got
                                break
                    except Exception:
                        pass

            if printer_name == "Generic FDM 220x220":
                p_id = _bundle_get_value(bundle, "printer_settings_id")
                if isinstance(p_id, str) and p_id.strip():
                    printer_name = p_id.strip()

        bed_x, bed_y = _parse_printable_area(
            _bundle_get_value(bundle, "printable_area"),
            default_x=220.0,
            default_y=220.0,
        )
        max_z = max(
            50.0,
            min(
                1000.0,
                _extract_first_float(
                    _bundle_get_value(bundle, "printable_height"), 250.0
                ),
            ),
        )
        nozzle_mm = max(
            0.15,
            min(
                2.0,
                _extract_first_float(_bundle_get_value(bundle, "nozzle_diameter"), 0.4),
            ),
        )
        layer_height_mm = max(
            0.04,
            min(
                1.2,
                _extract_first_float(_bundle_get_value(bundle, "layer_height"), 0.2),
            ),
        )
        line_width_mm = _parse_line_width(
            _bundle_get_value(bundle, "outer_wall_line_width"),
            nozzle_mm=nozzle_mm,
        )

        return {
            "lang": lang,
            "theme": theme,
            "theme_explicit": theme_explicit,
            "orca_version": orca_version,
            "printer_name": printer_name,
            "process_name": process_name,
            "filament_name": filament_name,
            "bed_x": float(bed_x),
            "bed_y": float(bed_y),
            "max_z": float(max_z),
            "nozzle_mm": float(nozzle_mm),
            "layer_height_mm": float(layer_height_mm),
            "line_width_mm": float(line_width_mm),
        }

    def read_full_host_config_snapshot(
        self, host_ctx: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Collect full resolved `project_settings` snapshot from `preset_bundle()` for `.3mf` export."""
        ctx = dict(host_ctx) if host_ctx is not None else self.read_host_context()
        project_settings: dict[str, Any] = {}

        host = getattr(orca, "host", None)
        bundle = None
        if host is not None:
            bundle_fn = getattr(host, "preset_bundle", None)
            if callable(bundle_fn):
                try:
                    bundle = bundle_fn()
                except Exception:
                    bundle = None

        if bundle is not None:
            keys_fn = getattr(bundle, "full_config_keys", None)
            val_fn = getattr(bundle, "full_config_value", None) or getattr(
                bundle, "config_value", None
            )
            if callable(keys_fn) and callable(val_fn):
                try:
                    keys = keys_fn()
                    if isinstance(keys, (list, tuple, set)):
                        for k in keys:
                            ks = str(k)
                            if not ks:
                                continue
                            try:
                                v = val_fn(ks)
                                if v is not None:
                                    project_settings[ks] = v
                            except Exception:
                                continue
                except Exception:
                    pass

        ctx["project_settings"] = project_settings
        return ctx

    def _apply_process_presets(self, updates: dict[str, str]) -> dict[str, Any]:
        """Apply process preset changes on the calling background worker thread.

        NEVER call `orca.host.preset.process.begin_update()` on the wxWidgets UI thread!
        """
        outcome: dict[str, Any] = {"applied": False, "error": None}
        if not updates:
            return outcome
        try:
            host = getattr(orca, "host", None)
            preset_ns = getattr(host, "preset", None) if host is not None else None
            process_ed = (
                getattr(preset_ns, "process", None) if preset_ns is not None else None
            )
            begin_fn = (
                getattr(process_ed, "begin_update", None)
                if process_ed is not None
                else None
            )
            if not callable(begin_fn):
                return outcome

            tx = begin_fn()
            if tx is None:
                return outcome

            staged_any = False
            for key, val in updates.items():
                try:
                    tx.set(str(key), str(val))
                    staged_any = True
                except Exception:
                    continue

            if staged_any:
                commit_fn = getattr(tx, "commit", None)
                if callable(commit_fn):
                    commit_fn()
                outcome["applied"] = True
        except Exception as exc:
            outcome["error"] = str(exc)
        return outcome

    def build_initial_context(self, mode="page"):
        ctx = self.read_host_context()
        return {
            "params": self.current_params(),
            "presets": BUILTIN_PRESETS,
            "user_presets": load_user_presets(
                self.get_presets_dir() / "user_presets.json"
            ),
            "host": ctx,
            "mode": mode,
            "lang": ctx["lang"],
            "theme": ctx["theme"],
            "version": "1.0.0",
        }

    def _geometry(self, p, assembled=True, target="full_suite"):
        geometry = {
            k: v
            for k, v in p.items()
            if k
            not in ("name", "lang", "theme", "export_target", "auto_configure_slicer")
        }
        key = json.dumps([geometry, assembled, target], sort_keys=True)
        with self._lock:
            if key in self._mesh_cache:
                return self._mesh_cache[key]
        items = collect_target_meshes(
            p, target=target, lang=p["lang"], assembled=assembled
        )
        for name, mesh in items:
            report = topology_report(mesh)
            if not report["closed"] or not report["oriented"]:
                raise ValueError(
                    f"{name}: invalid surface topology; choose fine quality or adjust geometry."
                )
        with self._lock:
            self._mesh_cache = {key: items}
        return items

    def _preview_payload(self, p):
        items = self._geometry(p)
        encoded = []
        for name, mesh in items:
            encoded.append(
                {
                    "name": name,
                    "part": mesh.part,
                    "vertices": base64.b64encode(
                        mesh.vertices.astype("<f4").tobytes()
                    ).decode("ascii"),
                    "triangles": base64.b64encode(
                        mesh.triangles.astype("<u4").tobytes()
                    ).decode("ascii"),
                    "bounds": mesh.bounds_mm,
                    "volume_cm3": mesh.volume_cm3,
                    "interface_error_mm": mesh.interface_error_mm,
                    "triangle_count": len(mesh.triangles),
                }
            )
        return {
            "type": "preview_result",
            "ok": True,
            "params": p,
            "meshes": encoded,
            "hinge": hinge_geometry(p),
            "volume_cm3": sum(m.volume_cm3 for _, m in items),
            "surface_note": "Curved surfaces are tessellated; fit-interface chord target is shown in mm.",
        }

    def _enqueue_preview(self, p, send_fn, request_id, mode="page"):
        with self._lock:
            self._preview_waiters[mode] = (send_fn, request_id)
            if (
                not getattr(self, "_preview_running", False)
                or self._preview_pending[1] != p
            ):
                self._preview_serial += 1
                self._preview_pending = (self._preview_serial, p)
            if getattr(self, "_preview_running", False):
                return
            self._preview_running = True

        def work():
            try:
                while True:
                    with self._lock:
                        serial, params = self._preview_pending
                    try:
                        payload = self._preview_payload(params)
                    except Exception as exc:
                        payload = {
                            "type": "preview_result",
                            "ok": False,
                            "message": str(exc),
                        }
                    with self._lock:
                        latest = serial == self._preview_serial
                        if latest:
                            self._preview_running = False
                            deliveries = list(self._preview_waiters.values())
                            self._preview_waiters = {}
                    if latest:
                        for post, rid in deliveries:
                            try:
                                post({**payload, "request_id": rid})
                            except Exception:
                                pass
                        return
            finally:
                with self._lock:
                    if (
                        getattr(self, "_preview_owner", None)
                        is threading.current_thread()
                    ):
                        self._preview_running = False

        worker = threading.Thread(
            target=work, name="OrcaBoxStudio-Preview", daemon=True
        )
        self._preview_owner = worker
        self._last_worker = worker
        worker.start()

    def _export_action(self, p, msg, host_config, send_fn):
        action = msg["type"]
        target = msg.get("export_target", p["export_target"])
        try:
            items = self._geometry(p, assembled=False, target=target)
            folder = self.get_export_dir()
            stem = _slugify_filename(p["name"], "caixa") + "_" + str(time.time_ns())
            fmt = (
                "3mf"
                if action == "send_to_plater"
                else str(msg.get("format", "3mf")).lower()
            )
            if fmt not in ("stl", "3mf"):
                raise ValueError("Choose STL or 3MF.")
            if any(
                mesh.bounds_mm["size"][2] > host_config.get("max_z", 250)
                for _, mesh in items
            ):
                raise ValueError(
                    "Peça excede altura da impressora / part exceeds printer height."
                )
            paths = []
            if fmt == "3mf":
                path = folder / (stem + ".3mf")
                write_orca_3mf(path, items, params=p, host_config=host_config)
                paths = [str(path)]
            else:
                for name, mesh in items:
                    path = folder / (
                        stem + "_" + _slugify_filename(name, "peca") + ".stl"
                    )
                    write_binary_stl(path, mesh, header_name="OrcaBoxStudio:" + name)
                    paths.append(str(path))
            configured = False
            if action == "send_to_plater":
                ok, info, _ = _dispatch_files_to_plater(paths)
                if not ok:
                    raise RuntimeError(
                        info + " Files remain in the plugin export folder."
                    )
                if p["auto_configure_slicer"]:
                    time.sleep(0.25)
                    config = self._apply_process_presets(
                        {
                            "spiral_mode": "0",
                            "spiral_mode_smooth": "0",
                            "wall_loops": "4",
                            "top_shell_layers": "5",
                            "bottom_shell_layers": "5",
                            "sparse_infill_density": "35%",
                            "sparse_infill_pattern": "gyroid",
                        }
                    )
                    configured = bool(config.get("applied"))
                text = "Pedido enviado à mesa / Import request sent to Plater."
            else:
                text = "Arquivos exportados / Files exported."
            send_fn(
                {
                    "type": "action_result",
                    "action": action,
                    "ok": True,
                    "paths": paths,
                    "message": text,
                    "slicer_configured": configured,
                    "transport_only": action == "send_to_plater",
                }
            )
        except Exception as exc:
            send_fn(
                {
                    "type": "action_result",
                    "action": action,
                    "ok": False,
                    "paths": [],
                    "message": str(exc),
                }
            )

    def handle_message(self, raw_data, send_fn, default_mode="page"):
        try:
            msg = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            if not isinstance(msg, dict):
                raise ValueError("Invalid plugin message.")
            self._subscriptions[default_mode] = send_fn
            action = msg.get("type", "")
            if action in ("get_initial_state", "init", "sync_printer"):
                send_fn(
                    {"type": "init_state", **self.build_initial_context(default_mode)}
                )
                return
            if action in (
                "preview",
                "update_params",
                "export_file",
                "send_to_plater",
                "save_preset",
            ):
                previous = self.current_params()
                p = normalize_params(msg.get("params") or previous)
                errors = validate_params(p)
                if errors:
                    raise ValueError("\n".join(errors))
                self.set_current_params(p)
                shared = lambda data: {
                    k: v for k, v in data.items() if k not in ("lang", "theme")
                }
                if shared(p) != shared(previous):
                    for mode, post in list(self._subscriptions.items()):
                        if mode != default_mode:
                            try:
                                post({"type": "design_changed", "params": p})
                            except Exception:
                                pass
            if action in ("preview", "update_params"):
                self._enqueue_preview(p, send_fn, msg.get("request_id"), default_mode)
                return
            if action in ("export_file", "send_to_plater"):
                host_config = self.read_full_host_config_snapshot()
                worker = threading.Thread(
                    target=self._export_action,
                    args=(p, msg, host_config, send_fn),
                    name="OrcaBoxStudio-Export",
                    daemon=True,
                )
                self._last_worker = worker
                worker.start()
                return
            path = self.get_presets_dir() / "user_presets.json"
            if action == "save_preset":
                save_user_preset(
                    path, msg.get("name", p["name"]), p, msg.get("preset_id")
                )
            elif action == "delete_preset":
                delete_user_preset(path, str(msg.get("preset_id", "")))
            elif action == "open_exports_folder":
                opened = _open_folder_native(self.get_export_dir())
                send_fn(
                    {
                        "type": "action_result",
                        "ok": opened,
                        "message": str(self.get_export_dir()),
                    }
                )
                return
            else:
                raise ValueError("Unknown plugin message: " + str(action))
            payload = {
                "type": "presets_result",
                "ok": True,
                "user_presets": load_user_presets(path),
            }
            for post in list(self._subscriptions.values()):
                try:
                    post(payload)
                except Exception:
                    pass
        except Exception as exc:
            send_fn(
                {
                    "type": "action_result",
                    "ok": False,
                    "action": raw_data.get("type", "")
                    if isinstance(raw_data, dict)
                    else "message",
                    "message": str(exc),
                }
            )


_SHARED_CONTROLLER = BoxStudioController()


class BoxStudioPageCapability(orca.pages.PagesPluginCapabilityBase):
    """Full-screen top-bar tab (`Gerador de Caixas`) beside Prepare / Preview / Device."""

    def __init__(self, controller: BoxStudioController | None = None) -> None:
        super().__init__()
        self._controller = controller or _SHARED_CONTROLLER

    def get_name(self) -> str:
        return "Gerador de Caixas"

    def get_default_config(self) -> dict[str, Any]:
        return {
            "default_style": "lip_snap",
            "default_width_x": 90.0,
            "default_export_target": "base_and_lid",
            "auto_configure_slicer": True,
        }

    def get_icon(self) -> str:
        storage_dir = _resolve_storage_dir()
        existing_candidates: list[Path] = []
        try:
            existing_candidates.append(Path(__file__).resolve().parent / "icon.svg")
        except Exception:
            pass
        existing_candidates.extend(
            [
                storage_dir / "icon.svg",
                _default_installed_plugin_dir() / "icon.svg",
            ]
        )
        for cand in existing_candidates:
            try:
                if cand.is_file() and cand.stat().st_size > 0:
                    return str(cand)
            except Exception:
                continue

        # Auto-materialize embedded `icon.svg` when user side-loaded only `orca_box_generator.py`
        write_targets: list[Path] = [
            storage_dir / "icon.svg",
            _default_plugin_data_dir() / "icon.svg",
        ]
        try:
            write_targets.append(Path(__file__).resolve().parent / "icon.svg")
        except Exception:
            pass
        write_targets.append(Path.home() / "Documents" / "OrcaBoxStudio" / "icon.svg")

        seen_dirs: set[str] = set()
        for target in write_targets:
            key = str(target)
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(ICON_SVG_CONTENT)
                if target.is_file() and target.stat().st_size > 0:
                    return str(target)
            except Exception:
                continue
        return ""

    def get_ui(self) -> str:
        initial_ctx = self._controller.build_initial_context(mode="page")
        return get_studio_html(mode="page", initial_context=initial_ctx)

    def post_message(self, data: Any) -> None:
        super_post = getattr(super(), "post_message", None)
        if callable(super_post):
            super_post(data)

    def on_message(self, data: Any) -> None:
        self._controller.handle_message(
            raw_data=data,
            send_fn=self.post_message,
            default_mode="page",
        )


class BoxStudioDockCapability(orca.script.ScriptPluginCapabilityBase):
    """Opens/shows a docked right-hand Box Studio panel directly beside the 3D Plater."""

    _active_panel: Any = None
    _panel_lock = threading.RLock()

    def __init__(self, controller: BoxStudioController | None = None) -> None:
        super().__init__()
        self._controller = controller or _SHARED_CONTROLLER

    def get_name(self) -> str:
        return "Orca Box Studio - Painel Lateral"

    def get_default_config(self) -> dict[str, Any]:
        return {
            "default_export_target": "base_and_lid",
            "auto_configure_slicer": True,
            "dock_side": "right",
        }

    def get_ui(self) -> str:
        initial_ctx = self._controller.build_initial_context(mode="dock")
        return get_studio_html(mode="dock", initial_context=initial_ctx)

    def _post_to_panel(self, payload: dict[str, Any]) -> None:
        with self._panel_lock:
            panel = BoxStudioDockCapability._active_panel
        if panel is None:
            return
        try:
            is_open_fn = getattr(panel, "is_open", None)
            if callable(is_open_fn) and not is_open_fn():
                return
            post_fn = getattr(panel, "post", None)
            if callable(post_fn):
                post_fn(payload)
        except Exception:
            pass

    def _on_panel_message(self, data: Any) -> None:
        self._controller.handle_message(
            raw_data=data,
            send_fn=self._post_to_panel,
            default_mode="dock",
        )

    def _on_panel_close(self) -> None:
        with self._panel_lock:
            BoxStudioDockCapability._active_panel = None

    def on_message(self, data: Any) -> None:
        """Direct message entry point for testing or programmatic invocation."""
        self._on_panel_message(data)

    def execute(self) -> Any:
        """Invoked on OrcaSlicer's background Script worker thread."""
        with self._panel_lock:
            existing = BoxStudioDockCapability._active_panel

        if existing is not None:
            try:
                is_open_fn = getattr(existing, "is_open", None)
                if not callable(is_open_fn) or is_open_fn():
                    show_fn = getattr(existing, "show", None)
                    if callable(show_fn):
                        show_fn()
                    init_ctx = self._controller.build_initial_context(mode="dock")
                    self._post_to_panel({"type": "init_state", **init_ctx})
                    return _make_execution_result_success(
                        "Painel lateral Orca Box Studio exibido."
                    )
            except Exception:
                with self._panel_lock:
                    BoxStudioDockCapability._active_panel = None

        html = self.get_ui()
        host = getattr(orca, "host", None)
        ui = getattr(host, "ui", None) if host is not None else None
        create_dock_fn = (
            getattr(ui, "create_dock_panel", None) if ui is not None else None
        )

        if callable(create_dock_fn):
            panel = create_dock_fn(
                html,
                title="Orca Box Studio",
                width=430,
                height=800,
                on_message=self._on_panel_message,
                on_close=self._on_panel_close,
                dock="right",
            )
            with self._panel_lock:
                BoxStudioDockCapability._active_panel = panel
            if panel is not None:
                show_fn = getattr(panel, "show", None)
                if callable(show_fn):
                    try:
                        show_fn()
                    except Exception:
                        pass
            return _make_execution_result_success(
                "Painel lateral Orca Box Studio aberto."
            )

        create_win_fn = getattr(ui, "create_window", None) if ui is not None else None
        if callable(create_win_fn):
            panel = create_win_fn(
                html,
                title="Orca Box Studio",
                width=450,
                height=820,
                on_message=self._on_panel_message,
                on_close=self._on_panel_close,
            )
            with self._panel_lock:
                BoxStudioDockCapability._active_panel = panel
            return _make_execution_result_success("Janela Orca Box Studio aberta.")

        result = getattr(orca, "ExecutionResult", None)
        code = getattr(getattr(orca, "PluginResult", None), "RecoverableError", 2)
        if result is not None:
            return result.failure(
                code, "Dock UI API unavailable in this OrcaSlicer host.", ""
            )
        return {"status": "RecoverableError", "message": "Dock UI API unavailable."}


# ---------------------------------------------------------------------------
# Single `@orca.plugin` Entry Point Class
# ---------------------------------------------------------------------------


@orca.plugin
class OrcaBoxStudioPlugin(orca.base):
    """OrcaSlicer 2.5.1+ Native Plugin Entry Point for Orca Box Studio."""

    def __init__(self) -> None:
        super().__init__()

    def register_capabilities(self) -> None:
        """Declare required plugin permissions and register Page + Script Dock capabilities.

        Per OrcaSlicer's `Plugin Audit Hook` specification:
        - `data_dir()` (`orca_plugins` and `orca.host.plugin.storage()`) is already a global
          read+write Allowed Root requiring zero `fs_read`/`fs_readwrite` prompts.
        - `has_permission` uses exact string equality (glob wildcards like `/*` are invalid).
        - `threading=True` declares the fixed `"thread"` audit target once up front.
        """
        req_fn = getattr(orca, "request_permissions", None)
        if callable(req_fn):
            req_fn(threading=True)

        orca.register_capability(BoxStudioPageCapability)
        orca.register_capability(BoxStudioDockCapability)
