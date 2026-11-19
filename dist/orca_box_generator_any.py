# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=1.26"]
#
# [tool.orcaslicer.plugin]
# id = "orca-box-studio"
# name = "Orca Box Studio"
# description = "Offline parametric boxes, handgrip bins, removable latching lids and calibration parts"
# author = "Orca Box Studio"
# version = "1.2.2"
# ///

# MIT License
#
# Copyright (c) 2026 Orca Box Studio
# Copyright (c) 2026 Orca Gear Studio (adapted infrastructure)
# Copyright (c) 2026 Orca Vase Studio (adapted interface template)
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
VALID_STYLES = (
    "lip_snap",
    "rugged_box",
    "sliding_lid",
    "screw_corner",
    "open_bin",
    "snap_latch",
    "stackable_bin",
    "clamshell_pip",
)
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
    "snap_retention": 0.12,
    "handles_enabled": True,
    "handle_faces": "left_right",
    "handle_width": 45.0,
    "handle_height": 12.0,
    "handle_top_margin": 8.0,
    "latch_width": 18.0,
    "latch_thickness": 2.0,
    "latch_retention": 0.6,
    "latch_pivot_diameter": 3.0,
    "lid_wall_height": 8.0,
    "stack_foot_height": 2.0,
    "stack_clearance": 0.25,
    "front_access_width": 60.0,
    "front_access_drop": 14.0,
    "pip_clearance": 0.30,
    "hinge_separation": 5.0,
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
        ("snap_retention", 0.03, 0.30),
        ("handle_width", 12, 160),
        ("handle_height", 6, 40),
        ("handle_top_margin", 3, 40),
        ("latch_width", 8, 30),
        ("latch_thickness", 1.2, 4),
        ("latch_retention", 0.2, 1.2),
        ("latch_pivot_diameter", 2.4, 4.0),
        ("lid_wall_height", 3, 25),
        ("stack_foot_height", 1, 5),
        ("stack_clearance", 0.1, 0.8),
        ("front_access_width", 12, 300),
        ("front_access_drop", 4, 150),
        ("pip_clearance", 0.20, 0.60),
        ("hinge_separation", 4, 12),
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
    p["handle_faces"] = (
        "front_back" if p["handle_faces"] == "front_back" else "left_right"
    )
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
    for key in ("gasket_enabled", "auto_configure_slicer", "handles_enabled"):
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
    if p["style"] == "clamshell_pip":
        outer_radius = p["hinge_pin_diameter"] / 2 + p["pip_clearance"] + 1.4
        knuckle = max(4.0, min(6.0, w * 0.06))
        tangent = min(
            w / 2 - p["corner_radius"], w / 2 - t - max(0.15, p["corner_radius"] - t)
        )
        if w * 0.26 + 1.5 * knuckle + 2 * p["pip_clearance"] + 1.2 > tangent - 1.2:
            errors.append(
                "Dobradiças: aumente a largura ou reduza o raio dos cantos / increase width or reduce corner radius for both hinges."
            )
        if p["hinge_separation"] < outer_radius + 0.8:
            errors.append(
                "Dobradiças: aumente a separação para preservar a rotação / increase hinge separation for the barrel radius."
            )
        if h + p["fit_clearance"] / 2 - 0.7 * outer_radius < f + 1.2:
            errors.append(
                "Dobradiças: aumente a altura de cada metade / increase the height of each half."
            )
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
            errors.append(
                "Estojo articulado: torres, recortes, divisórias e TPU ainda não são compatíveis / articulated case does not yet support posts, ports, dividers or TPU."
            )
    if p["style"] == "stackable_bin":
        f += p["stack_foot_height"]
        if p["front_access_width"] > w - 2 * (p["corner_radius"] + 2 * t):
            errors.append(
                "Acesso frontal: preserve os cantos e apoios / front access must preserve corners and side supports."
            )
        if h - p["front_access_drop"] < f + max(3.0, t):
            errors.append(
                "Acesso frontal: preserve o fundo e a ponte inferior / front access must preserve the floor and lower bridge."
            )
        if h - p["stack_foot_height"] < f + 1.2:
            errors.append(
                "Altura insuficiente para receber o pé da próxima caixa / insufficient cavity height for the next stacking foot."
            )
        if min(w, d) - 2 * (t + p["stack_clearance"]) < 4:
            errors.append(
                "Pé de empilhamento pequeno demais / stacking guide footprint is too small."
            )
    if p["style"] == "open_bin" and p["handles_enabled"]:
        span = d if p["handle_faces"] == "left_right" else w
        if p["handle_width"] < p["handle_height"] or p["handle_width"] > span - 2 * (
            p["corner_radius"] + 1.2
        ):
            errors.append(
                "Alças: reduza a largura para preservar os cantos / reduce handle width to preserve corners."
            )
        if h - p["handle_top_margin"] - p["handle_height"] < f + 1.2:
            errors.append(
                "Alças: preserve 1.2 mm acima do fundo / leave 1.2 mm above the floor."
            )
        if p["handle_top_margin"] < max(3, t):
            errors.append(
                "Alças: preserve a espessura da borda superior / preserve the top rim thickness."
            )
    if p["style"] == "snap_latch":
        c = p["fit_clearance"]
        pr = p["latch_pivot_diameter"] / 2
        outer = pr + 2 * c + 0.15 + 1.2
        offset = pr + c + 0.4
        ear = max(1.6, p["latch_thickness"])
        frame = p["latch_width"] / 2 + c + ear
        tangent = min(
            w / 2 - p["corner_radius"], w / 2 - t - max(0.15, p["corner_radius"] - t)
        )
        if w * 0.24 + frame > tangent - 1.2 or w * 0.48 < 2 * frame + 1.2:
            errors.append(
                "Travas: preserve espaço para as orelhas dos pivôs / increase box width or reduce latch width for the pivot ears."
            )
        if h - 7.5 - outer - offset < f + 1.2:
            errors.append(
                "Travas: aumente a altura para apoiar os pivôs / increase height to support the latch pivots."
            )
        if t < outer - offset + 0.8:
            errors.append(
                "Travas: aumente a parede atrás dos pivôs / increase wall thickness behind the latch sockets."
            )
        if p["lid_wall_height"] > h - f - 1.2:
            errors.append(
                "Parede da tampa invade o fundo / lid wall height enters the floor clearance."
            )
    if p["style"] in ("open_bin", "stackable_bin") and p["gasket_enabled"]:
        errors.append(
            "Caixa aberta não usa junta de tampa / open bin does not use a lid gasket."
        )
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
        depth = (
            0
            if p["style"] == "open_bin"
            else p["stack_foot_height"]
            if p["style"] == "stackable_bin"
            else p["lid_wall_height"]
            if p["style"] == "snap_latch"
            else p["lip_depth"]
        )
        if f + s["height"] > h - depth - 0.5:
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
            or c["z"] + c["height"] / 2
            > h
            - (
                p["stack_foot_height"]
                if p["style"] == "stackable_bin"
                else p["lid_wall_height"]
                if p["style"] == "snap_latch"
                else p["lip_depth"]
            )
            - 2
        ):
            errors.append(
                f"Recorte {i + 1}: preserve fundo, cantos e encaixe / preserve floor, corners and lid interface."
            )
        if (
            p["style"] == "stackable_bin"
            and c["face"] == "front"
            and abs(c["u"]) < p["front_access_width"] / 2 + c["width"] / 2 + 1.2
            and c["z"] + c["height"] / 2 > h - p["front_access_drop"] - 1.2
        ):
            errors.append(
                f"Recorte {i + 1}: afaste o acesso frontal / move port away from the front access opening."
            )
        if p["style"] in ("rugged_box", "snap_latch") and c["face"] == "front":
            half = (
                3
                if p["style"] == "rugged_box"
                else p["latch_width"] / 2
                + p["fit_clearance"]
                + max(1.6, p["latch_thickness"])
            )
            top = h - 5.5 if p["style"] == "rugged_box" else h
            root = (
                h - 7.2
                if p["style"] == "rugged_box"
                else h
                - 7.5
                - (p["latch_pivot_diameter"] / 2 + 2 * p["fit_clearance"] + 0.15 + 1.2)
                - (p["latch_pivot_diameter"] / 2 + p["fit_clearance"] + 0.4)
            )
            if (
                c["z"] + c["height"] / 2 > root - 1.2
                and c["z"] - c["height"] / 2 < top + 1.2
                and any(
                    abs(c["u"] - cx) < c["width"] / 2 + half + 1.2
                    for cx in (-w * 0.24, w * 0.24)
                )
            ):
                errors.append(
                    f"Recorte {i + 1}: afaste o suporte da trava / move port away from latch catch."
                )
        faces = (
            ("left", "right")
            if p["handle_faces"] == "left_right"
            else ("front", "back")
        )
        if p["style"] == "open_bin" and p["handles_enabled"] and c["face"] in faces:
            center = h - p["handle_top_margin"] - p["handle_height"] / 2
            if (
                abs(c["u"]) < (c["width"] + p["handle_width"]) / 2 + 1.2
                and abs(c["z"] - center) < (c["height"] + p["handle_height"]) / 2 + 1.2
            ):
                errors.append(
                    f"Recorte {i + 1}: afaste a alça / move port away from handle opening."
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
        if style == "snap_latch":
            poly = _storage_clip_profile(p)

            def clipfield(v):
                yz = v[:, [1, 2]]
                inside = np.zeros(len(v), dtype=bool)
                distance = np.full(len(v), np.inf)
                for a, b in zip(poly, np.roll(poly, -1, axis=0)):
                    edge = b - a
                    u = np.clip(((yz - a) * edge).sum(axis=1) / (edge @ edge), 0, 1)
                    distance = np.minimum(
                        distance, np.linalg.norm(yz - a - u[:, None] * edge, axis=1)
                    )
                    inside ^= ((a[1] > yz[:, 1]) != (b[1] > yz[:, 1])) & (
                        yz[:, 0]
                        < (b[0] - a[0]) * (yz[:, 1] - a[1]) / (b[1] - a[1] + 1e-30)
                        + a[0]
                    )
                return np.maximum(
                    np.where(inside, -distance, distance),
                    np.abs(v[:, 0] - cx) - p["latch_width"] / 2,
                )

            result = clipfield
            for y, z in poly:
                _planes(1, float(y))
                _planes(2, float(z))
            _planes(0, cx - p["latch_width"] / 2, cx + p["latch_width"] / 2)
            bounds = (
                cx - p["latch_width"] / 2 - 1,
                cx + p["latch_width"] / 2 + 1,
                float(poly[:, 0].min() - 1),
                float(poly[:, 0].max() + 1),
                float(poly[:, 1].min() - 1),
                float(poly[:, 1].max() + 1),
            )
        else:
            # Detachable flexure clip; middle relief leaves two connected spring arms.
            result = _difference(
                _box(cx - 4, cx + 4, -d / 2 - 6, -d / 2 - 1, h - 9, zcap + lh + 1),
                _box(
                    cx - 3 - c,
                    cx + 3 + c,
                    -d / 2 - 4.6,
                    -d / 2 + 0.2,
                    h - 7.2 - c,
                    zcap + lh - 0.4,
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
            levels.extend([h - 9, h - 7.5, h - 7.2 - c, zcap + lh - 0.4, zcap + lh + 1])
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
        elif p["hinge_mode"] == "pin":
            # The lid arm is fused after the barrel. Bore the final union so
            # the arm cannot refill the upper half of the separate pin passage.
            result = _difference(
                result, _cylinder_x(-kl / 2 - 0.2, kl / 2 + 0.2, cy, cz, pr + c)
            )
        circles.extend([(1, 2, cy, cz, hr), (1, 2, cy, cz, pr + c), (1, 2, cy, cz, pr)])
        levels.extend([cz - hr, cz, cz + hr, cz - hr * 0.8, cz - hr * 0.1])
        bounds = (-w / 2 - 3, w / 2 + 3, -d / 2 - 4, d / 2 + 12, -2, h + c + lh + 3)
    if part == "lid" and style != "rugged_box":
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
    if part == "lid" and p["style"] == "clamshell_pip":
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
    if p["style"] in ("open_bin", "snap_latch", "stackable_bin", "clamshell_pip"):
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
    if (
        p["style"] == "rugged_box"
        and p["hinge_mode"] == "print_in_place"
        and target in ("base_only", "lid_only")
    ):
        raise ValueError(
            "Dobradiça cativa: use Base + tampa ou Conjunto completo / captive hinge: use Base + lid or Full suite to preserve the assembly."
        )
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
        if p["hinge_mode"] == "pin":
            parts.append("pin")
        parts.extend(("clip_left", "clip_right"))
    if p["style"] == "snap_latch" and target in ("base_and_lid", "full_suite"):
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
        connected = [generate(p, part, False) for part in ("base", "lid")]
        assembly = combine_meshes(connected, "print_in_place_assembly")
        result = [("Conjunto cativo / Captive assembly", assembly)]
        return result + [
            (names[part][lang == "en"], generate(p, part, True))
            for part in parts
            if part not in ("base", "lid")
        ]
    return [
        (names[part][lang == "en"], generate(p, part, not assembled)) for part in parts
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

"""Eight standard box designs and atomic user-preset persistence."""

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
        "Caixa com tampa de encaixe",
        "Snap-fit lid box",
        width_x=90,
        depth_y=65,
        height_z=35,
    ),
    _preset(
        "screw_corner_standard",
        "Caixa com tampa parafusada",
        "Screw-lid box",
        style="screw_corner",
        width_x=90,
        depth_y=65,
        height_z=35,
    ),
    _preset(
        "tool_rugged",
        "Caixa reforçada com dobradiça",
        "Rugged hinged box",
        style="rugged_box",
        width_x=90,
        depth_y=65,
        height_z=35,
    ),
    _preset(
        "pencil",
        "Caixa com tampa deslizante",
        "Sliding-lid box",
        style="sliding_lid",
        width_x=90,
        depth_y=65,
        height_z=35,
    ),
    _preset(
        "open_bin_handles",
        "Caixa aberta com alças",
        "Open bin with hand grips",
        style="open_bin",
        width_x=140,
        depth_y=100,
        height_z=60,
        handles_enabled=True,
        handle_faces="left_right",
        handle_width=45,
        handle_height=12,
        handle_top_margin=8,
    ),
    _preset(
        "snap_latch_case",
        "Tampa removível · fechos articulados",
        "Removable lid · pivoting latches",
        style="snap_latch",
        width_x=110,
        depth_y=80,
        height_z=40,
        lid_wall_height=8,
        latch_width=18,
        latch_thickness=2,
        latch_retention=0.6,
        latch_pivot_diameter=3,
    ),
    _preset(
        "stackable_parts_bin",
        "Organizador empilhável · acesso frontal",
        "Stackable organizer · front access",
        style="stackable_bin",
        width_x=140,
        depth_y=100,
        height_z=80,
        stack_foot_height=2,
        stack_clearance=0.25,
        front_access_width=90,
        front_access_drop=30,
    ),
    _preset(
        "clamshell_pip_short",
        "Estojo articulado print-in-place",
        "Print-in-place clamshell",
        style="clamshell_pip",
        width_x=120,
        depth_y=65,
        height_z=14,
        pip_clearance=0.3,
        hinge_separation=5,
        hinge_pin_diameter=3,
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


def generate_random_printable_params(current=None, seed=None, limits=None):
    """Seeded, validated current-style variation; never silently discard features."""
    import random

    original = normalize_params(current)
    errors = validate_params(original)
    if errors:
        raise ValueError(
            "Corrija os recursos / fix features before randomizing: "
            + "\n".join(errors)
        )
    rng = random.Random(seed)
    constrained = any(
        original[k] for k in ("standoffs", "cutouts", "dividers_x", "dividers_y")
    )
    host = limits or {}
    stacking_family = original["style"] == "stackable_bin"
    clamshell = original["style"] == "clamshell_pip"
    maxima = {
        "width_x": min(350.0, float(host.get("bed_x", 358)) - 8),
        "depth_y": min(
            350.0,
            float(host.get("bed_y", 372))
            - (22 if original["style"] == "rugged_box" else 8),
        ),
        "height_z": min(
            250.0,
            float(host.get("max_z", 265))
            - (
                0
                if original["style"] in ("open_bin", "stackable_bin")
                else original["lid_height"] + 1
            ),
        ),
    }
    if clamshell:
        # Sampling bounds accelerate rejection; the exact analytic open envelope
        # below is authoritative, including the hinge's height above each floor.
        maxima["depth_y"] = min(
            maxima["depth_y"],
            (float(host.get("bed_y", 372)) - 2 * original["hinge_separation"]) / 2,
        )
    dimensions_to_vary = ("height_z",) if stacking_family else tuple(maxima)

    def fits(candidate):
        if validate_params(candidate) or not all(
            candidate[k] <= limit for k, limit in maxima.items()
        ):
            return False
        if clamshell:
            pass  # [bundled] resolved intra-package import

            size = clamshell_print_bounds(candidate)["size"]
            return all(
                value <= float(host.get(key, default))
                for value, key, default in zip(
                    size, ("bed_x", "bed_y", "max_z"), (358, 372, 265)
                )
            )
        return True

    for _ in range(64):
        candidate = copy.deepcopy(original)
        for key in dimensions_to_vary:
            maximum = maxima[key]
            lo = original[key] if constrained else original[key] * 0.78
            hi = min(maximum, original[key] * 1.24)
            if hi < lo:
                break
            candidate[key] = round(rng.uniform(lo, hi), 1)
        else:
            candidate["fit_clearance"] = round(rng.uniform(0.12, 0.35), 2)
            if not constrained and not stacking_family:
                candidate["corner_radius"] = round(
                    rng.uniform(2, min(candidate["width_x"], candidate["depth_y"]) / 9),
                    1,
                )
            candidate = normalize_params(candidate)
            if fits(candidate):
                return candidate
    for preset in BUILTIN_PRESETS:
        if preset["params"]["style"] != original["style"]:
            continue
        candidate = copy.deepcopy(original)
        for key in dimensions_to_vary:
            candidate[key] = (
                max(original[key], preset["params"][key])
                if constrained
                else preset["params"][key]
            )
        candidate = normalize_params(candidate)
        if fits(candidate):
            return candidate
    raise ValueError(
        "Nenhuma variação segura cabe sem alterar recursos / no safe variation fits without changing requested features."
    )

# ===========================================================================
# MODULE: box_studio.studio_ui
# ===========================================================================

"""Canonical offline Orca Studio interface; MIT reference styling and real Python meshes."""

pass  # [bundled] hoisted __future__ import
import copy
import json
from typing import Any
pass  # [bundled] resolved intra-package import
pass  # [bundled] resolved intra-package import

_BOX_HTML = r"""<!doctype html>
<html lang="__INITIAL_LANG__" data-theme="__INITIAL_THEME__">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Orca Box Studio</title>
    <style>
:root,
[data-theme="dark"] {
  --bg-app: #16181c;
  --bg-panel: #1e2026;
  --bg-card: #252830;
  --bg-card-hover: #2c303a;
  --bg-input: #17191e;
  --bg-viewport-top: #232730;
  --bg-viewport-bot: #121418;
  --bg-hud: rgba(24, 27, 33, 0.86);
  --border-subtle: #313640;
  --border-strong: #414856;
  --text-main: #eef2f6;
  --text-muted: #9aa3b2;
  --text-dim: #6e7787;
  --orca-accent: #00a896;
  --orca-accent-hover: #00bfa5;
  --orca-accent-soft: rgba(0, 191, 165, 0.15);
  --orca-accent-border: rgba(0, 191, 165, 0.48);
  --status-ok: #00c853;
  --status-warn: #ffb300;
  --status-crit: #ff5252;
  --shadow-soft: 0 8px 24px rgba(0, 0, 0, 0.35);
  --radius-sm: 6px;
  --radius-md: 9px;
  --radius-lg: 12px;
  --font-sans: var(--orca-font, "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, Ubuntu, sans-serif);
  --font-mono: "Cascadia Code", Consolas, "SFMono-Regular", monospace;
}

[data-theme="light"] {
  --bg-app: #eef2f6;
  --bg-panel: #ffffff;
  --bg-card: #f5f7fa;
  --bg-card-hover: #eaeff5;
  --bg-input: #ffffff;
  --bg-viewport-top: #dde4ec;
  --bg-viewport-bot: #c7d1dc;
  --bg-hud: rgba(255, 255, 255, 0.90);
  --border-subtle: #d5dce4;
  --border-strong: #b8c3cf;
  --text-main: #1c222b;
  --text-muted: #556070;
  --text-dim: #7b8696;
  --orca-accent: #00897b;
  --orca-accent-hover: #00796b;
  --orca-accent-soft: rgba(0, 137, 123, 0.12);
  --orca-accent-border: rgba(0, 137, 123, 0.45);
  --status-ok: #1b9e4b;
  --status-warn: #d98200;
  --status-crit: #d93025;
  --shadow-soft: 0 8px 24px rgba(15, 25, 40, 0.10);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--bg-app);
  color: var(--text-main);
  font-family: var(--font-sans);
  font-size: 12.5px;
  line-height: 1.4;
  user-select: none;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--border-strong);
  border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--orca-accent);
}

button, input, select {
  font-family: inherit;
  font-size: inherit;
  color: inherit;
}

.studio-shell {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

/* Header Bar */
.studio-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 7px 12px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  z-index: 20;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
  flex: 1 1 auto;
}

.brand-logo {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: linear-gradient(135deg, #00bfa5 0%, #00796b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 191, 165, 0.30);
}

.brand-titles {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.brand-title {
  font-weight: 700;
  font-size: 13.5px;
  letter-spacing: 0.2px;
  white-space: nowrap;
}

.design-name-input {
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main);
  width: 165px;
  transition: border-color 0.15s;
}
.design-name-input:focus {
  outline: none;
  border-color: var(--orca-accent);
}

.printer-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 11px;
  border-radius: 99px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 11px;
  white-space: nowrap;
  max-width: min(560px, 56vw);
  min-width: 0;
  flex: 0 1 auto;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}
.printer-pill:hover {
  border-color: var(--orca-accent-border);
  background: var(--bg-card-hover);
  color: var(--text-main);
}
.printer-pill:active {
  transform: translateY(1px);
}

.printer-pill-text {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  overflow: hidden;
}

.printer-pill-name {
  min-width: 0;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  color: var(--text-main);
}

.printer-pill-specs {
  flex-shrink: 0;
  white-space: nowrap;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 10.6px;
}

.printer-pill-sync {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11.5px;
  line-height: 1;
  color: var(--orca-accent-hover);
  margin-left: 1px;
  transition: transform 0.38s ease;
}
[data-theme="light"] .printer-pill-sync {
  color: var(--orca-accent);
}
.printer-pill.syncing .printer-pill-sync {
  transform: rotate(360deg);
}

.printer-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--orca-accent-hover);
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  color: var(--text-main);
  font-weight: 600;
  font-size: 11.5px;
  cursor: pointer;
  transition: background 0.14s, border-color 0.14s, transform 0.08s;
  white-space: nowrap;
}
.btn:hover:not(:disabled) {
  background: var(--bg-card-hover);
  border-color: var(--border-strong);
}
.btn:active:not(:disabled) {
  transform: translateY(1px);
}
.btn:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.btn-icon {
  padding: 5px 7px;
}

.btn-accent {
  background: linear-gradient(135deg, var(--orca-accent) 0%, #00897b 100%);
  border-color: transparent;
  color: #ffffff;
}
.btn-accent:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--orca-accent-hover) 0%, var(--orca-accent) 100%);
  border-color: transparent;
}

.btn-soft {
  background: var(--orca-accent-soft);
  border-color: var(--orca-accent-border);
  color: var(--orca-accent-hover);
}
[data-theme="light"] .btn-soft {
  color: var(--orca-accent);
}
.btn-soft:hover:not(:disabled) {
  background: var(--orca-accent);
  color: #ffffff;
}

/* Main Workspace Grid */
.studio-workspace {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 332px minmax(340px, 1fr) 364px;
  overflow: hidden;
}

.col-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-panel);
  overflow: hidden;
}
.col-left {
  border-right: 1px solid var(--border-subtle);
}
.col-right {
  border-left: 1px solid var(--border-subtle);
}

.col-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Dock Mode Navigation Tabs (hidden in wide page mode) */
.dock-tabs {
  display: none;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border-subtle);
  padding: 4px 6px;
  gap: 4px;
  flex-shrink: 0;
}

.dock-tab-btn {
  flex: 1;
  padding: 6px 4px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  transition: all 0.14s;
}
.dock-tab-btn:hover {
  color: var(--text-main);
  background: var(--bg-card);
}
.dock-tab-btn.active {
  background: var(--orca-accent-soft);
  border-color: var(--orca-accent-border);
  color: var(--orca-accent-hover);
}
[data-theme="light"] .dock-tab-btn.active {
  color: var(--orca-accent);
}

/* Cards & Sections */
.studio-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.card-title {
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.55px;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 99px;
  background: var(--orca-accent-soft);
  color: var(--orca-accent-hover);
}
[data-theme="light"] .card-badge {
  color: var(--orca-accent);
}

/* Presets Grid */
.preset-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.filter-chip {
  padding: 3px 7px;
  font-size: 10.5px;
  font-weight: 600;
  border-radius: 99px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-input);
  color: var(--text-muted);
  cursor: pointer;
}
.filter-chip.active {
  background: var(--orca-accent);
  border-color: var(--orca-accent);
  color: #ffffff;
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  max-height: 205px;
  overflow-y: auto;
  padding-right: 2px;
}

.preset-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 7px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-panel);
  cursor: pointer;
  transition: border-color 0.14s, background 0.14s;
  text-align: left;
}
.preset-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-strong);
}
.preset-card.active {
  border-color: var(--orca-accent-hover);
  background: var(--orca-accent-soft);
}

.preset-thumb {
  width: 30px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preset-meta {
  min-width: 0;
  flex: 1;
}

.preset-name {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preset-sub {
  font-size: 9.8px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preset-del-btn {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 17px;
  height: 17px;
  border-radius: 4px;
  border: none;
  background: rgba(255, 82, 82, 0.16);
  color: var(--status-crit);
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preset-del-btn:hover {
  background: var(--status-crit);
  color: #ffffff;
}

.save-preset-bar {
  display: none;
  gap: 5px;
  align-items: center;
  padding-top: 4px;
  border-top: 1px dashed var(--border-subtle);
}
.save-preset-bar.open {
  display: flex;
}
.save-preset-input {
  flex: 1;
  min-width: 0;
  background: var(--bg-input);
  border: 1px solid var(--orca-accent-border);
  border-radius: var(--radius-sm);
  padding: 4px 7px;
  font-size: 11.5px;
}

/* Segmented Mode Switch */
.seg-group {
  display: flex;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 2px;
  gap: 2px;
}

.seg-btn {
  flex: 1;
  padding: 5px 6px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.14s;
}
.seg-btn.active {
  background: var(--orca-accent);
  color: #ffffff;
}

/* 2D Curve Canvas Box */
.curve-editor-wrap {
  position: relative;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-input);
  overflow: hidden;
}

#curve-canvas {
  display: block;
  width: 100%;
  height: 220px;
  cursor: crosshair;
  touch-action: none;
}

.curve-overlay-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: var(--bg-panel);
  border-top: 1px solid var(--border-subtle);
  font-size: 10.5px;
  color: var(--text-muted);
}

.curve-coord-readout {
  font-family: var(--font-mono);
  font-size: 10.5px;
  color: var(--orca-accent-hover);
}
[data-theme="light"] .curve-coord-readout {
  color: var(--orca-accent);
}

.curve-hint {
  font-size: 10.2px;
  color: var(--text-dim);
}

/* Slider Controls */
.ctrl-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.ctrl-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.ctrl-label {
  font-size: 11.3px;
  color: var(--text-muted);
  font-weight: 500;
}

.ctrl-val-wrap {
  display: flex;
  align-items: center;
  gap: 3px;
}

.ctrl-num {
  width: 58px;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  padding: 2px 5px;
  text-align: right;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-main);
}
.ctrl-num:focus {
  outline: none;
  border-color: var(--orca-accent);
}

.ctrl-unit {
  font-size: 10px;
  color: var(--text-dim);
  min-width: 18px;
}

input[type="range"].orca-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 5px;
  border-radius: 99px;
  background: var(--border-strong);
  outline: none;
  cursor: pointer;
}
input[type="range"].orca-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--orca-accent-hover);
  border: 2px solid #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
  cursor: grab;
  transition: transform 0.1s;
}
input[type="range"].orca-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

/* Toggle Switch */
.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 34px;
  height: 18px;
  flex-shrink: 0;
}
.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.toggle-track {
  position: absolute;
  inset: 0;
  background: var(--border-strong);
  border-radius: 99px;
  cursor: pointer;
  transition: background 0.18s;
}
.toggle-track::before {
  content: "";
  position: absolute;
  width: 14px;
  height: 14px;
  left: 2px;
  top: 2px;
  border-radius: 50%;
  background: #ffffff;
  transition: transform 0.18s;
}
.toggle-switch input:checked + .toggle-track {
  background: var(--orca-accent);
}
.toggle-switch input:checked + .toggle-track::before {
  transform: translateX(16px);
}

/* Texture Accordion Layer Cards */
.tex-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  overflow: hidden;
  transition: border-color 0.15s;
}
.tex-card.enabled {
  border-color: var(--orca-accent-border);
}

.tex-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 9px;
  background: var(--bg-card);
  cursor: pointer;
}
.tex-card.enabled .tex-head {
  background: var(--orca-accent-soft);
}

.tex-title-wrap {
  display: flex;
  align-items: center;
  gap: 7px;
  font-weight: 600;
  font-size: 12px;
}

.tex-chevron {
  font-size: 10px;
  color: var(--text-muted);
  transition: transform 0.15s;
}
.tex-card.expanded .tex-chevron {
  transform: rotate(90deg);
}

.tex-body {
  display: none;
  padding: 8px 9px 10px;
  border-top: 1px solid var(--border-subtle);
  flex-direction: column;
  gap: 7px;
}
.tex-card.expanded .tex-body {
  display: flex;
}

/* Center 3D Viewport */
.viewport-col {
  position: relative;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  background: radial-gradient(circle at 50% 32%, var(--bg-viewport-top) 0%, var(--bg-viewport-bot) 100%);
  overflow: hidden;
}

#gl-canvas {
  width: 100%;
  height: 100%;
  display: block;
  touch-action: none;
  cursor: grab;
}
#gl-canvas:active {
  cursor: grabbing;
}

#vp-caliper-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
  z-index: 5;
}

/* Wall Thickness Quick Presets & Perimeter Hint */
.wall-preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 1px;
}

.wall-chip {
  flex: 1;
  min-width: 48px;
  padding: 3px 5px;
  border-radius: 5px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-input);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 10.2px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  transition: all 0.14s;
}
.wall-chip:hover {
  color: var(--text-main);
  border-color: var(--border-strong);
  background: var(--bg-card-hover);
}
.wall-chip.active {
  background: var(--orca-accent-soft);
  border-color: var(--orca-accent-hover);
  color: var(--orca-accent-hover);
}
[data-theme="light"] .wall-chip.active {
  color: var(--orca-accent);
  border-color: var(--orca-accent);
}

.wall-perim-hint {
  font-size: 10.4px;
  color: var(--orca-accent-hover);
  font-family: var(--font-mono);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 3px 7px;
  border-radius: 5px;
  background: var(--orca-accent-soft);
  border: 1px solid var(--orca-accent-border);
}
[data-theme="light"] .wall-perim-hint {
  color: var(--orca-accent);
}

/* Floating Viewport Overlays */
.vp-toolbar-left {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  max-width: calc(100% - 252px);
  z-index: 10;
}

.vp-glass {
  background: var(--bg-hud);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-soft);
}

.vp-select {
  background: var(--bg-hud);
  color: var(--text-main);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 5px 8px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
}

.vp-chip {
  padding: 5px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-hud);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.vp-chip:hover {
  color: var(--text-main);
  border-color: var(--border-strong);
}
.vp-chip.active {
  background: var(--orca-accent);
  border-color: var(--orca-accent);
  color: #ffffff;
}
.vp-chip-xray {
  border-color: var(--orca-accent-border);
  color: var(--text-main);
}
.vp-chip-xray.active {
  background: linear-gradient(135deg, #00bfa5 0%, #ff8f00 130%);
  border-color: transparent;
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(0, 191, 165, 0.35);
}

.spiral-mode-banner {
  display: none;
  position: absolute;
  top: 48px;
  left: 10px;
  max-width: calc(100% - 256px);
  padding: 5px 10px;
  font-size: 10.6px;
  font-weight: 600;
  line-height: 1.3;
  z-index: 12;
  border-left: 3px solid var(--orca-accent-hover);
  color: var(--text-main);
  pointer-events: none;
}
.spiral-mode-banner.visible {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.spiral-mode-banner.warn {
  border-left-color: var(--status-warn);
  background: rgba(45, 34, 14, 0.90);
}
[data-theme="light"] .spiral-mode-banner.warn {
  background: rgba(255, 245, 224, 0.94);
}

.vp-cam-bar {
  position: absolute;
  bottom: 56px;
  left: 10px;
  display: flex;
  gap: 4px;
  z-index: 10;
}

.vp-cut-bar {
  position: absolute;
  bottom: 10px;
  left: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  z-index: 10;
}

.vp-cut-modes {
  display: inline-flex;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 2px;
  gap: 2px;
  flex-shrink: 0;
}

.vp-cut-mode-btn {
  padding: 3px 7px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted);
  font-size: 10.5px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.14s;
}
.vp-cut-mode-btn:hover {
  color: var(--text-main);
}
.vp-cut-mode-btn.active {
  background: var(--orca-accent);
  color: #ffffff;
}

.vp-cut-label {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  color: var(--text-muted);
}

/* Printability HUD */
.vp-hud-right {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 236px;
  padding: 9px 11px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  z-index: 10;
}

.hud-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
}

.hud-status-pill {
  padding: 1px 7px;
  border-radius: 99px;
  font-size: 10px;
  font-weight: 700;
}
.hud-status-pill.ok {
  background: rgba(0, 200, 83, 0.18);
  color: var(--status-ok);
}
.hud-status-pill.warn {
  background: rgba(255, 179, 0, 0.20);
  color: var(--status-warn);
}
.hud-status-pill.crit {
  background: rgba(255, 82, 82, 0.22);
  color: var(--status-crit);
}

.hud-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px 8px;
}

.hud-metric {
  display: flex;
  flex-direction: column;
}
.hud-metric-k {
  font-size: 9.8px;
  color: var(--text-dim);
}
.hud-metric-v {
  font-family: var(--font-mono);
  font-size: 11.2px;
  font-weight: 600;
  color: var(--text-main);
}

.hud-warnings {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-height: 92px;
  overflow-y: auto;
}

.hud-warn-item {
  font-size: 10.2px;
  padding: 3px 6px;
  border-radius: 4px;
  background: rgba(255, 179, 0, 0.13);
  border-left: 2px solid var(--status-warn);
  color: var(--text-main);
}
.hud-warn-item.crit {
  background: rgba(255, 82, 82, 0.15);
  border-left-color: var(--status-crit);
}

.heatmap-legend {
  display: none;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  padding-top: 4px;
  border-top: 1px solid var(--border-subtle);
  color: var(--text-muted);
}
.heatmap-legend.visible {
  display: flex;
}
.legend-swatch {
  width: 9px;
  height: 9px;
  border-radius: 2px;
  display: inline-block;
}

.bed-alert-banner {
  display: none;
  position: absolute;
  top: 52px;
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 12px 6px 14px;
  border-radius: 99px;
  background: rgba(213, 0, 0, 0.90);
  color: #ffffff;
  font-weight: 700;
  font-size: 11.5px;
  box-shadow: 0 4px 16px rgba(213, 0, 0, 0.45);
  z-index: 15;
  pointer-events: auto;
  white-space: nowrap;
}
.bed-alert-banner.visible {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.bed-fit-btn {
  padding: 2px 9px;
  border-radius: 99px;
  border: 1px solid rgba(255, 255, 255, 0.65);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 10.5px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.14s;
}
.bed-fit-btn:hover {
  background: rgba(255, 255, 255, 0.32);
}

/* Right Action Footer */
.action-footer {
  padding: 10px;
  background: var(--bg-panel);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 7px;
  flex-shrink: 0;
}

.btn-hero {
  width: 100%;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 700;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #00bfa5 0%, #00897b 100%);
  color: #ffffff;
  border: none;
  box-shadow: 0 4px 14px rgba(0, 191, 165, 0.32);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: filter 0.15s, transform 0.08s;
}
.btn-hero:hover:not(:disabled) {
  filter: brightness(1.07);
}
.btn-hero:active:not(:disabled) {
  transform: translateY(1px);
}
.btn-hero:disabled {
  opacity: 0.55;
  cursor: wait;
}

.export-btn-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 6px;
}

.helper-note {
  font-size: 10.5px;
  color: var(--text-muted);
  background: var(--bg-input);
  border-left: 2px solid var(--orca-accent);
  padding: 5px 7px;
  border-radius: 0 4px 4px 0;
}

.helper-note.warn {
  border-left-color: var(--status-warn);
  background: rgba(255, 179, 0, 0.10);
}

/* Toast Notification */
.toast-banner {
  position: fixed;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  opacity: 0;
  pointer-events: none;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  background: var(--bg-card);
  border: 1px solid var(--orca-accent);
  color: var(--text-main);
  font-size: 12px;
  font-weight: 600;
  box-shadow: var(--shadow-soft);
  transition: opacity 0.2s, transform 0.2s;
  z-index: 999;
  max-width: 90vw;
}
.toast-banner.visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
.toast-banner.error {
  border-color: var(--status-crit);
}

/* ============================================================================
   COMPACT SIDE-DOCK MODE (`data-mode="dock"` or narrow viewports <= 960px)
   ============================================================================ */
body[data-mode="dock"] .printer-pill,
body[data-mode="dock"] .brand-title {
  display: none;
}

body[data-mode="dock"] .design-name-input {
  width: 118px;
}

body[data-mode="dock"] .studio-workspace {
  display: flex;
  flex-direction: column;
}

body[data-mode="dock"] .viewport-col {
  order: -1;
  height: 245px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-subtle);
}

body[data-mode="dock"] .vp-hud-right {
  width: 172px;
  padding: 5px 7px;
  gap: 3px;
}
body[data-mode="dock"] .hud-warnings,
body[data-mode="dock"] .spiral-mode-banner {
  display: none;
}
body[data-mode="dock"] .vp-cam-bar {
  display: none;
}
body[data-mode="dock"] .vp-cut-bar {
  padding: 4px 6px;
  bottom: 6px;
  gap: 4px;
}
body[data-mode="dock"] .vp-cut-mode-btn {
  padding: 2px 5px;
  font-size: 9.8px;
}

body[data-mode="dock"] .dock-tabs {
  display: flex;
  order: 0;
}

body[data-mode="dock"] .col-left,
body[data-mode="dock"] .col-right {
  border: none;
  flex: 1;
  min-height: 0;
}

body[data-mode="dock"] .col-right .action-footer {
  display: none;
}

.dock-global-footer {
  display: none;
}
body[data-mode="dock"] .dock-global-footer {
  display: flex;
}

body[data-mode="dock"][data-dock-tab="shape"] .col-right {
  display: none;
}
body[data-mode="dock"][data-dock-tab="shape"] #card-presets {
  display: none;
}

body[data-mode="dock"][data-dock-tab="presets"] .col-right {
  display: none;
}
body[data-mode="dock"][data-dock-tab="presets"] #card-silhouette,
body[data-mode="dock"][data-dock-tab="presets"] #card-resolution {
  display: none;
}
body[data-mode="dock"][data-dock-tab="presets"] .presets-grid {
  max-height: none;
}

body[data-mode="dock"][data-dock-tab="textures"] .col-left {
  display: none;
}
body[data-mode="dock"][data-dock-tab="textures"] #card-print-mode,
body[data-mode="dock"][data-dock-tab="textures"] #card-gardening {
  display: none;
}

body[data-mode="dock"][data-dock-tab="print"] .col-left {
  display: none;
}
body[data-mode="dock"][data-dock-tab="print"] #card-envelope,
body[data-mode="dock"][data-dock-tab="print"] #card-textures {
  display: none;
}

@media (max-width: 960px) {
  .printer-pill {
    display: none;
  }
  .studio-workspace {
    grid-template-columns: 280px minmax(260px, 1fr) 300px;
  }
}
</style>
    <style>
      /* Preserve the reference page height when fallback font metrics differ. */
      body[data-mode="page"] .studio-header {
        min-height: 43px;
      }
      .box-select {
        width: 100%;
        max-width: 100%;
      }
      .box-pair {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 7px;
      }
      .box-feature {
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        padding: 7px;
        display: flex;
        flex-direction: column;
        gap: 7px;
      }
      .box-feature-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .box-feature .ctrl-num {
        max-width: 100%;
      }
      .box-feature .ctrl-row {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .box-feature-title button {
        padding: 1px 6px;
      }
      .section-hidden {
        display: none;
      }
      .box-style-controls[hidden] { display: none; }
      .box-status-error {
        color: var(--status-crit);
      }
    </style>
    <style id="orca-box-host-adapter">
      /* Orca's late, bare element defaults must not replace the studio tokens.
         Keep this adapter separate from the unchanged canonical design sheet. */
      html[data-theme],
      html[data-theme] body {
        background: var(--bg-app);
        color: var(--text-main);
        font-family: var(--font-sans);
        font-size: 12.5px;
        line-height: 1.4;
      }
      html[data-theme="dark"] {
        --orca-accent: #00a896;
        color-scheme: dark;
      }
      html[data-theme="light"] {
        --orca-accent: #00897b;
        color-scheme: light;
      }
      html[data-theme] :is(h1, h2, h3, h4, h5, h6),
      html[data-theme] .brand-title,
      html[data-theme] .tex-title-wrap {
        color: var(--text-main);
      }
      html[data-theme] :is(input, select, textarea) {
        color: var(--text-main);
      }
      html[data-theme] input[type="range"].orca-slider {
        border: 0;
        padding: 0;
        min-height: 0;
        box-shadow: none;
      }
      html[data-theme] .toggle-switch input {
        border: 0;
        padding: 0;
        min-width: 0;
        min-height: 0;
      }
    </style>
  </head>
  <body data-mode="__INITIAL_MODE__" data-dock-tab="shape">
    <div class="studio-shell">
      <header class="studio-header">
        <div class="brand-group">
          <div class="brand-logo" title="Orca Box Studio">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="m3 8 9-5 9 5-9 5Zm0 0v10l9 5 9-5V8M12 13v10" />
            </svg>
          </div>
          <div class="brand-titles">
            <div class="brand-name-row">
              <span class="brand-title">Orca Box Studio</span>
              <input
                id="name"
                class="design-name-input"
                type="text"
                maxlength="80"
                value="Caixa de projeto"
                aria-label="Design Name"
              />
            </div>
          </div>
          <button
            id="sync"
            type="button"
            class="printer-pill"
            title="Clique para sincronizar impressora ativa do OrcaSlicer"
          >
            <span class="printer-dot"></span>
            <span id="printer-pill-text" class="printer-pill-text">
              <span id="printer-pill-name" class="printer-pill-name"
                >Generic 3D Printer</span
              >
              <span id="printer-pill-specs" class="printer-pill-specs"
                >· 220×220×250 mm · 0.4mm</span
              >
            </span>
            <span
              id="printer-pill-sync"
              class="printer-pill-sync"
              aria-hidden="true"
              >↻</span
            >
          </button>
        </div>

        <div class="header-actions">
          <button id="undo" class="btn btn-icon" title="Undo (Ctrl+Z)" disabled>
            ↶
          </button>
          <button id="redo" class="btn btn-icon" title="Redo (Ctrl+Y)" disabled>
            ↷
          </button>
          <button id="btn-randomize" class="btn btn-soft">
            <span>🎲</span>
            <span data-i18n="btn_surprise">Surpreenda-me</span>
          </button>
          <button id="reset" class="btn btn-icon" title="Reset">↺</button>
          <button id="lang" class="btn btn-icon" title="Português / English">
            PT
          </button>
          <button id="theme" class="btn btn-icon" title="Dark / Light">
            ☾
          </button>
        </div>
      </header>

      <nav class="dock-tabs" aria-label="Studio Sections">
        <button class="dock-tab-btn active" data-tab="shape" data-i18n="shape">
          Forma</button
        ><button class="dock-tab-btn" data-tab="textures" data-i18n="features">
          Recursos</button
        ><button class="dock-tab-btn" data-tab="print" data-i18n="manufacture">
          Impressão</button
        ><button class="dock-tab-btn" data-tab="presets" data-i18n="presets">
          Presets
        </button>
      </nav>
      <main class="studio-workspace">
        <section class="col-panel col-left">
          <div class="col-scroll">
            <div id="card-presets" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="sec_presets"
                  >sec_presets</span
                ><button
                  id="btn-toggle-save-preset"
                  class="btn btn-soft"
                  style="padding: 2px 8px; font-size: 10.5px"
                  data-i18n="btn_save_preset"
                >
                  + Salvar
                </button>
              </div>
              <div id="save-preset-bar" class="save-preset-bar">
                <input
                  id="inp-save-preset-name"
                  class="save-preset-input"
                  type="text"
                  maxlength="64"
                /><button
                  id="savePreset"
                  class="btn btn-accent"
                  data-i18n="save"
                >
                  Salvar
                </button>
              </div>
              <div id="preset-filters" class="preset-filter-row">
                <button
                  class="filter-chip active"
                  data-cat="all"
                  data-i18n="cat_all"
                >
                  Todos</button
                ><button class="filter-chip" data-cat="lip_snap">Snap</button
                ><button class="filter-chip" data-cat="rugged_box">
                  Rugged</button
                ><button class="filter-chip" data-cat="sliding_lid">
                  Sliding</button
                ><button class="filter-chip" data-cat="screw_corner">
                  Screw</button
                ><button class="filter-chip" data-cat="open_bin" data-i18n="openBin">Caixa aberta</button
                ><button class="filter-chip" data-cat="snap_latch" data-i18n="snapLatch">Travas</button
                ><button class="filter-chip" data-cat="stackable_bin" data-i18n="stackableBin">Empilhável</button
                ><button class="filter-chip" data-cat="clamshell_pip" data-i18n="clamshellPip">Articulado PIP</button
                ><button
                  class="filter-chip"
                  data-cat="user"
                  data-i18n="cat_user"
                >
                  Meus
                </button>
              </div>
              <div id="presets-grid" class="presets-grid"></div>
            </div>
            <div id="card-silhouette" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="construction"
                  >construction</span
                ><span id="poly-badge" class="card-badge">BOX</span>
              </div>
              <label class="ctrl-row"
                ><span class="ctrl-label" data-i18n="style">style</span
                ><select id="style" class="vp-select box-select">
                  <option value="lip_snap">Lip Snap</option>
                  <option value="rugged_box">Rugged Box</option>
                  <option value="sliding_lid">Sliding Lid</option>
                  <option value="screw_corner">Screw Corner</option>
                  <option value="open_bin" data-i18n="openBin">Caixa aberta</option>
                  <option value="snap_latch" data-i18n="snapLatch">Tampa com travas</option>
                  <option value="stackable_bin" data-i18n="stackableBin">Caixa empilhável</option>
                  <option value="clamshell_pip" data-i18n="clamshellPip">Estojo articulado PIP</option>
                </select></label
              >
              <div data-slider="width_x" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Largura X"
                    data-en="Width X"
                    >Largura X</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="width_x"
                      type="number"
                      min="20"
                      max="350"
                      step="1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="width_x"
                  type="range"
                  min="20"
                  max="350"
                  step="1"
                />
              </div>
              <div data-slider="depth_y" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Profundidade Y"
                    data-en="Depth Y"
                    >Profundidade Y</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="depth_y"
                      type="number"
                      min="20"
                      max="350"
                      step="1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="depth_y"
                  type="range"
                  min="20"
                  max="350"
                  step="1"
                />
              </div>
              <div data-slider="height_z" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Altura Z"
                    data-en="Height Z"
                    >Altura Z</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="height_z"
                      type="number"
                      min="10"
                      max="250"
                      step="1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="height_z"
                  type="range"
                  min="10"
                  max="250"
                  step="1"
                />
              </div>
              <div data-slider="corner_radius" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Raio de canto"
                    data-en="Corner radius"
                    >Raio de canto</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="corner_radius"
                      type="number"
                      min="0.8"
                      max="30"
                      step="0.2"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="corner_radius"
                  type="range"
                  min="0.8"
                  max="30"
                  step="0.2"
                />
              </div>
              <div class="ctrl-row">
                <div class="ctrl-top">
                  <span class="ctrl-label" data-i18n="open">Abrir</span
                  ><span class="ctrl-val-wrap"
                    ><span id="openValue" class="ctrl-num">25%</span></span
                  >
                </div>
                <input
                  id="open"
                  class="orca-slider"
                  type="range"
                  min="0"
                  max="100"
                  value="25"
                />
              </div>
              <div class="curve-editor-wrap">
                <canvas id="curve-canvas" width="500" height="330"></canvas>
                <div class="curve-overlay-bar">
                  <span id="curve-coord-readout" class="curve-coord-readout"
                    >X/Y · mm</span
                  ><button
                    id="addPost"
                    class="btn"
                    style="padding: 2px 6px; font-size: 10px"
                  >
                    + PCB
                  </button>
                </div>
              </div>
              <div class="curve-hint" data-i18n="planHelp"></div>
            </div>
            <div id="card-resolution" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="quality">quality</span>
              </div>
              <label class="ctrl-row"
                ><span class="ctrl-label" data-i18n="quality">quality</span
                ><select id="quality" class="vp-select box-select">
                  <option value="standard" data-i18n="qualityStandard">Standard</option>
                  <option value="fine" data-i18n="qualityFine">Fine</option>
                </select></label
              >
              <p id="surface" class="helper-note"></p>
            </div>
          </div>
        </section>
        <section class="viewport-col">
          <canvas id="gl-canvas"></canvas>
          <canvas id="vp-caliper-canvas"></canvas>

          <!-- Top-Left Material & View Controls -->
          <div class="vp-toolbar-left">
            <select id="sel-material" class="vp-select" aria-label="Material">
              <option value="emerald_silk" data-i18n="mat_emerald">
                Seda Esmeralda Orca
              </option>
              <option value="terracotta" data-i18n="mat_terracotta">
                Cerâmica Terracota
              </option>
              <option value="matte_ceramic" data-i18n="mat_white">
                Porcelana Branca Mate
              </option>
              <option value="copper_bronze" data-i18n="mat_copper">
                Bronze Cobre Escovado
              </option>
              <option value="xray" data-i18n="mat_xray">
                🔬 Raio-X / Parede (Translúcido)
              </option>
              <option value="heatmap" data-i18n="mat_heatmap">
                Mapa de Overhang (°)
              </option>
            </select>
            <button id="xray" class="vp-chip vp-chip-xray" data-i18n="vp_xray">
              🔬 Raio-X / Parede
            </button>
            <button
              id="btn-vp-calipers"
              class="vp-chip"
              data-i18n="vp_calipers"
            >
              📏 Cotas mm
            </button>
            <button id="btn-vp-heatmap" class="vp-chip" data-i18n="vp_heatmap">
              🔥 Overhang
            </button>
            <button id="btn-vp-wire" class="vp-chip" data-i18n="vp_wire">
              ⌗ Malha
            </button>
            <button id="play" class="vp-chip" title="Animate lid">▶</button>
            <button id="btn-vp-spin" class="vp-chip" title="Auto-Rotate">
              ⟳
            </button>
          </div>

          <!-- Out-of-bed live warning -->
          <div id="bed-alert-banner" class="bed-alert-banner">
            <span>⚠</span>
            <span id="bed-alert-text"
              >Dimensões excedem o volume da impressora!</span
            >
            <button
              id="btn-fit-to-printer"
              style="display: none"
              type="button"
              class="bed-fit-btn"
              data-i18n="btn_fit_printer"
            >
              Ajustar à Mesa
            </button>
          </div>

          <!-- Top-Right Live Printability & Dimensions HUD -->
          <aside id="vp-hud-right" class="vp-hud-right vp-glass">
            <div class="hud-title-row">
              <span data-i18n="hud_title">Printabilidade</span>
              <span id="hud-status-pill" class="hud-status-pill ok">OK</span>
            </div>
            <div class="hud-grid">
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_wall_floor"
                  >Parede / Fundo</span
                >
                <span id="hud-wall-floor" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_mouth_hole"
                  >Folga por lado</span
                >
                <span id="hud-clearance" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_dims"
                  >Dimensões (mm)</span
                >
                <span id="hud-dims" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_overhang"
                  >Overhang Máx</span
                >
                <span id="hud-overhang" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_weight"
                  >Volume sólido</span
                >
                <span id="volume" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_Tris"
                  >Triângulos</span
                >
                <span id="triangles" class="hud-metric-v">—</span>
              </div>
            </div>
            <div id="xray-legend" class="heatmap-legend">
              <span
                ><i class="legend-swatch" style="background: #0fd6c2"></i
                ><span data-i18n="leg_outer">Externa</span></span
              >
              <span
                ><i class="legend-swatch" style="background: #ff8c38"></i
                ><span data-i18n="leg_inner">Cavidade &amp; Fundo</span></span
              >
            </div>
            <div id="heatmap-legend" class="heatmap-legend">
              <span
                ><i class="legend-swatch" style="background: #00c853"></i
                >≤45°</span
              >
              <span
                ><i class="legend-swatch" style="background: #ffb300"></i
                >45–55°</span
              >
              <span
                ><i class="legend-swatch" style="background: #ff3d00"></i
                >&gt;55°</span
              >
            </div>
            <div
              id="status"
              class="helper-note"
              role="status"
              aria-live="polite"
            ></div>
            <div id="hud-warnings" class="hud-warnings"></div>
          </aside>

          <!-- Camera Preset Pills -->
          <div class="vp-cam-bar">
            <button class="vp-chip" data-cam="iso">Iso</button>
            <button class="vp-chip" data-cam="front" data-i18n="cam_front">
              Frente
            </button>
            <button class="vp-chip" data-cam="top" data-i18n="cam_top">
              Topo
            </button>
            <button class="vp-chip" data-cam="bottom" data-i18n="cam_bottom">
              Base
            </button>
            <button
              class="vp-chip"
              id="home"
              data-cam="fit"
              data-i18n="cam_fit"
            >
              Enquadrar
            </button>
          </div>

          <!-- Bottom Dual Section Inspector Slider (Vertical Profile Y + Horizontal Plan Slice Z) -->
          <div class="vp-cut-bar vp-glass">
            <div
              class="vp-cut-modes"
              role="group"
              aria-label="Section Cut Mode"
            >
              <button
                id="btn-cut-mode-y"
                class="vp-cut-mode-btn active"
                data-i18n="vp_cut_y"
              >
                ✂ Corte Vertical (Perfil Y)
              </button>
              <button
                id="btn-cut-mode-z"
                class="vp-cut-mode-btn"
                data-i18n="vp_cut_z"
              >
                💿 Fatia Horizontal Z (Planta 5%–100%)
              </button>
            </div>
            <input
              id="cut"
              class="orca-slider"
              type="range"
              min="0"
              max="100"
              step="1"
              value="0"
            />
            <span
              id="lbl-cross-cut"
              class="ctrl-num"
              style="width: 62px; text-align: center"
              >Off</span
            >
            <button
              id="btn-cut-half"
              class="btn"
              style="padding: 3px 7px; font-size: 10.5px"
            >
              50%
            </button>
            <button
              id="btn-cut-off"
              class="btn"
              style="padding: 3px 7px; font-size: 10.5px"
            >
              Off
            </button>
          </div>
        </section>

        <section class="col-panel col-right">
          <div class="col-scroll">
            <div id="card-print-mode" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="wall">wall</span
                ><span id="wall-mode-badge" class="card-badge">mm</span>
              </div>
              <div data-slider="wall_thickness" class="ctrl-row">
                <label class="ctrl-top"
                  ><span class="ctrl-label" data-pt="Parede" data-en="Wall"
                    >Parede</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="wall_thickness"
                      type="number"
                      min="1.2"
                      max="12"
                      step="0.2"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="wall_thickness"
                  type="range"
                  min="1.2"
                  max="12"
                  step="0.2"
                />
              </div>
              <div data-slider="floor_thickness" class="ctrl-row">
                <label class="ctrl-top"
                  ><span class="ctrl-label" data-pt="Fundo" data-en="Floor"
                    >Fundo</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="floor_thickness"
                      type="number"
                      min="1.2"
                      max="12"
                      step="0.2"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="floor_thickness"
                  type="range"
                  min="1.2"
                  max="12"
                  step="0.2"
                />
              </div>
              <div data-slider="lid_height" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Espessura da tampa"
                    data-en="Lid thickness"
                    >Espessura da tampa</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="lid_height"
                      type="number"
                      min="1.2"
                      max="12"
                      step="0.2"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="lid_height"
                  type="range"
                  min="1.2"
                  max="12"
                  step="0.2"
                />
              </div>
              <div data-slider="fit_clearance" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Folga por lado"
                    data-en="Clearance per side"
                    >Folga por lado</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="fit_clearance"
                      type="number"
                      min="0.1"
                      max="0.4"
                      step="0.01"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="fit_clearance"
                  type="range"
                  min="0.1"
                  max="0.4"
                  step="0.01"
                />
              </div>
              <div id="wall-preset-chips" class="wall-preset-row">
                <button class="wall-chip" data-wall-preset="1.2">1.2 mm</button
                ><button class="wall-chip" data-wall-preset="2.4">2.4 mm</button
                ><button class="wall-chip" data-wall-preset="4">4 mm</button
                ><button class="wall-chip" data-wall-preset="8">8 mm</button>
              </div>
              <div id="wall-perim-hint" class="wall-perim-hint"></div>
            </div>
            <div id="card-textures" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="features">features</span>
              </div>
              <div class="tex-card expanded">
                <div class="tex-head">
                  <span class="tex-title-wrap" data-i18n="pcb">PCB</span>
                </div>
                <div class="tex-body" id="posts"></div>
              </div>
              <div class="tex-card expanded">
                <div class="tex-head">
                  <span class="tex-title-wrap" data-i18n="ports">Recortes</span
                  ><button
                    id="addPort"
                    class="btn btn-soft"
                    style="padding: 2px 6px"
                  >
                    + USB-C
                  </button>
                </div>
                <div class="tex-body" id="ports"></div>
              </div>
              <div class="tex-card expanded">
                <div class="tex-head">
                  <span class="tex-title-wrap" data-i18n="dividers"
                    >Divisórias</span
                  >
                </div>
                <div class="tex-body">
                  <label class="ctrl-row"
                    ><span class="ctrl-label" data-i18n="dividerX"></span
                    ><input
                      id="dividers_x"
                      class="save-preset-input"
                      placeholder="-20, 20" /></label
                  ><label class="ctrl-row"
                    ><span class="ctrl-label" data-i18n="dividerY"></span
                    ><input
                      id="dividers_y"
                      class="save-preset-input"
                      placeholder="0"
                  /></label>
                </div>
              </div>
            </div>
            <div id="card-envelope" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="connections">Encaixes & alças</span>
              </div>
              <div data-slider="lip_depth" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Profundidade de encaixe"
                    data-en="Locating skirt depth"
                    >Profundidade de encaixe</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="lip_depth"
                      type="number"
                      min="3"
                      max="10"
                      step="0.5"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="lip_depth"
                  type="range"
                  min="3"
                  max="10"
                  step="0.5"
                />
              </div>
              <div class="rugged">
                <label class="ctrl-row"
                  ><span class="ctrl-label" data-i18n="hinge">hinge</span
                  ><select id="hinge_mode" class="vp-select box-select">
                    <option value="pin">Pino / Pin</option>
                    <option value="print_in_place">Print-in-place</option>
                  </select></label
                >
                <p id="rugged-motion-phase" class="helper-note" aria-live="polite" hidden></p>
              </div>
                <div data-slider="hinge_pin_diameter" class="ctrl-row">
                  <label class="ctrl-top"
                    ><span
                      class="ctrl-label"
                      data-pt="Diâmetro do pino"
                      data-en="Pin diameter"
                      >Diâmetro do pino</span
                    ><span class="ctrl-val-wrap"
                      ><input
                        class="ctrl-num"
                        data-p="hinge_pin_diameter"
                        type="number"
                        min="2"
                        max="6"
                        step="0.2"
                      /><span class="ctrl-unit">mm</span></span
                    ></label
                  ><input
                    class="orca-slider"
                    data-param-range="hinge_pin_diameter"
                    type="range"
                    min="2"
                    max="6"
                    step="0.2"
                  />
                </div>

              <div class="screw">
                <label class="ctrl-row"
                  ><span class="ctrl-label" data-i18n="screw">screw</span
                  ><select id="screw_size" class="vp-select box-select">
                    <option value="M2">M2</option>
                    <option value="M2.5">M2.5</option>
                    <option value="M3">M3</option>
                  </select></label
                >
              </div>
<div id="open-bin-handles" class="ctrl-row box-style-controls" hidden>
  <div class="switch-row">
    <span class="ctrl-label" data-i18n="handles">Alças de mão</span
    ><label class="toggle-switch"
      ><input id="handles_enabled" type="checkbox" /><span
        class="toggle-track"
      ></span
    ></label>
  </div>
  <label class="ctrl-row"
    ><span class="ctrl-label" data-i18n="handleFaces">Par de faces</span
    ><select id="handle_faces" class="vp-select box-select">
      <option value="left_right" data-i18n="leftRight">
        Esquerda / direita
      </option>
      <option value="front_back" data-i18n="frontBack">Frente / trás</option>
    </select></label
  >
  <div data-slider="handle_width" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Largura útil da alça"
        data-en="Grip clear width"
        >Largura útil da alça</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="handle_width"
          type="number"
          min="12"
          max="160"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="handle_width"
      type="range"
      min="12"
      max="160"
      step="1"
    />
  </div>
  <div data-slider="handle_height" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Altura útil da alça"
        data-en="Grip clear height"
        >Altura útil da alça</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="handle_height"
          type="number"
          min="6"
          max="40"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="handle_height"
      type="range"
      min="6"
      max="40"
      step="1"
    />
  </div>
  <div data-slider="handle_top_margin" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Distância ao topo"
        data-en="Distance from top"
        >Distância ao topo</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="handle_top_margin"
          type="number"
          min="3"
          max="40"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="handle_top_margin"
      type="range"
      min="3"
      max="40"
      step="1"
    />
  </div>
</div>
<div id="snap-latch-options" class="ctrl-row box-style-controls" hidden>
  <div data-slider="lid_wall_height" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Profundidade de encaixe da tampa"
        data-en="Lid skirt depth"
        >Profundidade de encaixe da tampa</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="lid_wall_height"
          type="number"
          min="3"
          max="25"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="lid_wall_height"
      type="range"
      min="3"
      max="25"
      step="1"
    />
  </div>
  <div data-slider="latch_width" class="ctrl-row">
    <label class="ctrl-top"
      ><span class="ctrl-label" data-pt="Largura da trava" data-en="Latch width"
        >Largura da trava</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="latch_width"
          type="number"
          min="8"
          max="30"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="latch_width"
      type="range"
      min="8"
      max="30"
      step="1"
    />
  </div>
  <div data-slider="latch_thickness" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Espessura do fecho"
        data-en="Latch body thickness"
        >Espessura do fecho</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="latch_thickness"
          type="number"
          min="1.2"
          max="4"
          step="0.1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="latch_thickness"
      type="range"
      min="1.2"
      max="4"
      step="0.1"
    />
  </div>
  <div data-slider="latch_retention" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Engate do gancho"
        data-en="Hook engagement"
        >Engate do gancho</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="latch_retention"
          type="number"
          min="0.2"
          max="1.2"
          step="0.05"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="latch_retention"
      type="range"
      min="0.2"
      max="1.2"
      step="0.05"
    />
  </div>
  <div data-slider="latch_pivot_diameter" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Diâmetro do pivô do fecho"
        data-en="Latch pivot diameter"
        >Diâmetro do pivô do fecho</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="latch_pivot_diameter"
          type="number"
          min="2.4"
          max="4"
          step="0.1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="latch_pivot_diameter"
      type="range"
      min="2.4"
      max="4"
      step="0.1"
    />
  </div>
  <p class="helper-note" data-i18n="twoLatches">
    Duas travas articuladas na base, com pega e gancho. Solte as travas antes de
    retirar a tampa.
  </p>
  <p id="latch-motion-phase" class="helper-note" aria-live="polite" hidden></p>
</div>
<div data-slider="snap_retention" class="ctrl-row">
  <label class="ctrl-top"
    ><span
      class="ctrl-label"
      data-pt="Retenção do encaixe"
      data-en="Snap interference"
      >Retenção do encaixe</span
    ><span class="ctrl-val-wrap"
      ><input
        class="ctrl-num"
        data-p="snap_retention"
        type="number"
        min="0.03"
        max="0.30"
        step="0.01"
      /><span class="ctrl-unit">mm</span></span
    ></label
  ><input
    class="orca-slider"
    data-param-range="snap_retention"
    type="range"
    min="0.03"
    max="0.30"
    step="0.01"
  />
</div>
<div id="stackable-bin-options" class="ctrl-row box-style-controls" hidden>
  <div data-slider="front_access_width" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Largura da abertura frontal"
        data-en="Front access width"
        >Largura da abertura frontal</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="front_access_width"
          type="number"
          min="12"
          max="300"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="front_access_width"
      type="range"
      min="12"
      max="300"
      step="1"
    />
  </div>
  <div data-slider="front_access_drop" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Rebaixo frontal a partir do topo"
        data-en="Front opening drop from top"
        >Rebaixo frontal a partir do topo</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="front_access_drop"
          type="number"
          min="4"
          max="150"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="front_access_drop"
      type="range"
      min="4"
      max="150"
      step="1"
    />
  </div>
  <div data-slider="stack_foot_height" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Altura do pé de empilhamento"
        data-en="Stacking foot height"
        >Altura do pé de empilhamento</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="stack_foot_height"
          type="number"
          min="1"
          max="5"
          step="0.1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="stack_foot_height"
      type="range"
      min="1"
      max="5"
      step="0.1"
    />
  </div>
  <div data-slider="stack_clearance" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Folga por lado para empilhar"
        data-en="Stacking clearance per side"
        >Folga por lado para empilhar</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="stack_clearance"
          type="number"
          min="0.1"
          max="0.8"
          step="0.05"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="stack_clearance"
      type="range"
      min="0.1"
      max="0.8"
      step="0.05"
    />
  </div>
  <p class="helper-note" data-i18n="stackingFamily">
    A altura total inclui o pé. Para empilhar alturas diferentes, mantenha as
    dimensões X/Y, cantos, paredes e encaixes iguais.
  </p>
</div>
<div id="clamshell-pip-options" class="ctrl-row box-style-controls" hidden>
  <div data-slider="pip_clearance" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Folga da dobradiça PIP"
        data-en="PIP hinge clearance"
        >Folga da dobradiça PIP</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="pip_clearance"
          type="number"
          min="0.2"
          max="0.6"
          step="0.05"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="pip_clearance"
      type="range"
      min="0.2"
      max="0.6"
      step="0.05"
    />
  </div>
  <div data-slider="hinge_separation" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Afastamento da articulação"
        data-en="Hinge separation"
        >Afastamento da articulação</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="hinge_separation"
          type="number"
          min="4"
          max="12"
          step="0.5"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="hinge_separation"
      type="range"
      min="4"
      max="12"
      step="0.5"
    />
  </div>
  <p id="clamshell-closed-height" class="helper-note"></p>
  <p
    id="clamshell-feature-warning"
    class="helper-note warn"
    data-i18n="clamshellFeatures"
    hidden
  >
    Remova acessórios incompatíveis.
  </p>
</div>
<p id="pipNote" class="helper-note warn"></p>
            </div>
            <div id="card-gardening" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="manufacture"
                  >manufacture</span
                >
              </div>
              <div class="switch-row">
                <span class="ctrl-label" data-i18n="enableGasket"
                  >enableGasket</span
                ><label class="toggle-switch"
                  ><input id="gasket_enabled" type="checkbox" /><span
                    class="toggle-track"
                  ></span
                ></label>
              </div>
              <div data-slider="gasket_width" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Largura do canal TPU"
                    data-en="TPU channel width"
                    >Largura do canal TPU</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="gasket_width"
                      type="number"
                      min="0.6"
                      max="2"
                      step="0.1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="gasket_width"
                  type="range"
                  min="0.6"
                  max="2"
                  step="0.1"
                />
              </div>
              <div data-slider="gasket_depth" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Profundidade do canal"
                    data-en="Channel depth"
                    >Profundidade do canal</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="gasket_depth"
                      type="number"
                      min="0.5"
                      max="2"
                      step="0.1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="gasket_depth"
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                />
              </div>
              <div class="switch-row">
                <span class="ctrl-label" data-i18n="auto">auto</span
                ><label class="toggle-switch"
                  ><input id="auto_configure_slicer" type="checkbox" /><span
                    class="toggle-track"
                  ></span
                ></label>
              </div>
              <label class="ctrl-row"
                ><span class="ctrl-label" data-i18n="manufacture"
                  >manufacture</span
                ><select id="target" class="vp-select box-select">
                  <option value="base_and_lid">base_and_lid</option>
                  <option value="base_only">base_only</option>
                  <option value="lid_only">lid_only</option>
                  <option value="gasket">gasket</option>
                  <option value="fit_test_kit">fit_test_kit</option>
                  <option value="full_suite">full_suite</option>
                </select></label
              >
              <p class="helper-note" data-i18n="printHelp"></p>
            </div>
          </div>
          <!-- Wide Mode Sticky Action Footer -->
          <footer class="action-footer">
            <button class="btn-hero" id="send" data-action="send_to_plater">
              <span>🚀</span>
              <span data-i18n="btn_send_plater"
                >Enviar para a Mesa do OrcaSlicer</span
              >
            </button>
            <div class="export-btn-row">
              <button class="btn" id="mf" data-action="export_3mf">
                💾 <span data-i18n="btn_exp_3mf">Exportar .3MF</span>
              </button>
              <button class="btn" id="stl" data-action="export_stl">
                📐 <span data-i18n="btn_exp_stl">Exportar .STL</span>
              </button>
              <button
                class="btn btn-icon"
                id="folder"
                data-action="open_folder"
                title="Open Exports Folder"
              >
                📂
              </button>
            </div>
          </footer>
        </section>
      </main>
      <!-- Compact Dock Mode Sticky Footer -->
      <footer class="action-footer dock-global-footer">
        <button
          class="btn-hero job"
          data-action="send_to_plater"
          style="padding: 8px 10px; font-size: 12px"
        >
          <span>🚀</span>
          <span data-i18n="btn_send_plater"
            >Enviar para a Mesa do OrcaSlicer</span
          >
        </button>
        <div class="export-btn-row">
          <button class="btn job" data-action="export_3mf">💾 .3MF</button>
          <button class="btn job" data-action="export_stl">📐 .STL</button>
          <button
            class="btn btn-icon"
            data-action="open_folder"
            title="Open Exports Folder"
          >
            📂
          </button>
        </div>
      </footer>
    </div>
    <div
      id="toast-banner"
      class="toast-banner"
      role="status"
      aria-live="polite"
    ></div>
    <script>
const INITIAL = __BOX_CONTEXT__;
(() => {
  "use strict";
  const $ = (id) =>
      document.getElementById(
        {
          gl: "gl-canvas",
          presets: "presets-grid",
          printer: "printer-pill-name",
          plan: "curve-canvas",
        }[id] || id,
      ),
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
    localDirty = false,
    meshParams = clone(INITIAL.params),
    meshRevisionKey = null,
    openingStyle = null,
    lastInterfaceError = null,
    statusTranslationKey = null,
    timer = null,
    playing = false,
    angle = 25,
    drag = null;
  let userOverrodeTheme = false;
  let hostThemeExplicit =
    INITIAL.theme_explicit ?? INITIAL.host?.theme_explicit ?? true;
  function detectInjectedOrcaTheme() {
    if (
      typeof window === "undefined" ||
      typeof window.getComputedStyle !== "function"
    )
      return null;
    if (typeof document === "undefined" || !document.documentElement)
      return null;
    try {
      const style = window.getComputedStyle(document.documentElement);
      if (!style || typeof style.getPropertyValue !== "function") return null;
      const raw = String(style.getPropertyValue("--orca-bg") || "").trim();
      if (!raw) return null;
      let r = NaN,
        g = NaN,
        b = NaN;
      if (raw[0] === "#") {
        const hex = raw.slice(1).trim();
        if (hex.length === 3) {
          r = parseInt(hex[0] + hex[0], 16);
          g = parseInt(hex[1] + hex[1], 16);
          b = parseInt(hex[2] + hex[2], 16);
        } else if (hex.length >= 6) {
          r = parseInt(hex.slice(0, 2), 16);
          g = parseInt(hex.slice(2, 4), 16);
          b = parseInt(hex.slice(4, 6), 16);
        }
      } else {
        const m = raw.match(
          /rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/i,
        );
        if (m) {
          r = parseFloat(m[1]);
          g = parseFloat(m[2]);
          b = parseFloat(m[3]);
        }
      }
      if (!Number.isFinite(r) || !Number.isFinite(g) || !Number.isFinite(b))
        return null;
      const lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0;
      return lum > 0.52 ? "light" : "dark";
    } catch (_) {
      return null;
    }
  }

  function resolveHostTheme(message = {}) {
    if (typeof message.theme_explicit === "boolean")
      hostThemeExplicit = message.theme_explicit;
    else if (typeof message.host?.theme_explicit === "boolean")
      hostThemeExplicit = message.host.theme_explicit;
    if (userOverrodeTheme) return;
    const injected =
      hostThemeExplicit === false ? detectInjectedOrcaTheme() : null;
    const resolved = injected || message.theme || message.host?.theme;
    if ((resolved === "light" || resolved === "dark") && resolved !== theme) {
      theme = resolved;
      translate();
    }
  }
  function watchHostTheme() {
    if (typeof MutationObserver !== "function") return;
    const apply = () => resolveHostTheme();
    const rootObserver = new MutationObserver(apply);
    rootObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-orca-theme"],
    });
    if (document.head) {
      const styleObserver = new MutationObserver(apply);
      styleObserver.observe(document.head, {
        childList: true,
        subtree: true,
        characterData: true,
      });
    }
  }

  const texts = {
    pt: {
      shape: "Caixa",
      features: "Acessórios",
      presets: "Presets",
      construction: "Construção",
      style: "Estilo de caixa",
      openBin: "Caixa aberta",
      snapLatch: "Tampa com travas",
      stackableBin: "Caixa empilhável",
      clamshellPip: "Estojo articulado PIP",
      hingedAssembly: "Conjunto articulado",
      equalHalfNote:
        "Metades iguais · altura fechada: {height} mm. O conjunto é impresso aberto a 180°.",
      clamshellPrintBounds: "Na mesa, aberto: {size} mm.",
      clamshellFeatures:
        "Remova torres, recortes, divisórias e TPU existentes para usar este estilo.",
      stackingFamily:
        "A altura total inclui o pé. Para empilhar alturas diferentes, mantenha as dimensões X/Y, cantos, paredes e encaixes iguais.",
      connections: "Encaixes & alças",
      handles: "Alças de mão",
      handleFaces: "Par de faces",
      leftRight: "Esquerda / direita",
      frontBack: "Frente / trás",
      twoLatches:
        "Duas travas articuladas na base, com pega e gancho. Solte as travas antes de retirar a tampa.",
      releaseAndOpen: "Soltar fechos e abrir",
      releaseClipsAndOpen: "Retirar presilhas e abrir",
      ruggedClosed: "Presilhas instaladas · tampa fechada",
      ruggedReleasing: "Retirando presilhas · tampa parada",
      ruggedOpening: "Presilhas retiradas · abrindo a tampa",
      ruggedOpen: "Presilhas retiradas · tampa aberta",
      latchesEngaged: "Fechos presos · tampa fechada",
      releasingLatches: "Soltando os fechos · tampa parada",
      liftingLid: "Fechos abertos · afastando a tampa",
      lidRemoved: "Fechos abertos · tampa afastada",
      latchMotionUnavailable:
        "Movimento dos fechos indisponível. Gere a prévia novamente.",
      width: "Largura X",
      depth: "Profundidade Y",
      height: "Altura da base Z",
      radius: "Raio de canto",
      wall: "Parede",
      floor: "Fundo",
      lid: "Espessura tampa",
      clearance: "Folga por lado",
      hingeClearance: "Folga da dobradiça",
      lip: "Profundidade de encaixe",
      hinge: "Dobradiça",
      pin: "Diâmetro do pino",
      screw: "Parafuso de canto",
      quality: "Resolução da superfície",
      qualityStandard: "Padrão",
      qualityFine: "Fina",
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
        "Base com fundo na mesa; preserve a orientação exportada das peças. Imprima o kit de encaixe antes da peça final. Tempo depende da impressora e do perfil.",
      printHelpClamshell:
        "Base e tampa com a mesma altura. Exporte o conjunto articulado aberto a 180°, com as duas faces externas apoiadas na mesa. Preserve essa posição no fatiador e teste a articulação impressa.",
      printHelpOpen:
        "Base com fundo na mesa e abertura para cima. Confira as paredes e as pontes das alças, quando ativadas, na prévia do fatiador.",
      printHelpStack:
        "Imprima com o pé apoiado na mesa e a frente aberta. A altura total inclui o pé. Teste o encaixe entre peças da mesma família antes de empilhar.",
      printHelpLatch:
        "Conjunto: base, tampa e duas travas. Imprima base e tampa pelas faces externas, e as travas em pé. Monte as travas nos pivôs da base; solte os ganchos antes de retirar a tampa. Teste o encaixe das peças impressas.",
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
      openBin: "Open bin",
      snapLatch: "Latch lid",
      stackableBin: "Stackable bin",
      clamshellPip: "PIP clamshell",
      hingedAssembly: "Hinged assembly",
      equalHalfNote:
        "Equal halves · closed height: {height} mm. The assembly prints open at 180°.",
      clamshellPrintBounds: "Open footprint on the bed: {size} mm.",
      clamshellFeatures:
        "Remove existing standoffs, cutouts, dividers and TPU features to use this style.",
      stackingFamily:
        "Total height includes the foot. To stack different heights, keep X/Y dimensions, corners, walls and mating features identical.",
      connections: "Connections & grips",
      handles: "Hand grips",
      handleFaces: "Pair of faces",
      leftRight: "Left / right",
      frontBack: "Front / back",
      twoLatches:
        "Two latches pivot on the base, each with a grip and hook. Release them before lifting off the lid.",
      releaseAndOpen: "Release latches & open",
      releaseClipsAndOpen: "Remove clips & open",
      ruggedClosed: "Clips installed · lid closed",
      ruggedReleasing: "Removing clips · lid stationary",
      ruggedOpening: "Clips removed · opening the lid",
      ruggedOpen: "Clips removed · lid open",
      latchesEngaged: "Latches engaged · lid closed",
      releasingLatches: "Releasing latches · lid stationary",
      liftingLid: "Latches open · lifting the lid",
      lidRemoved: "Latches open · lid removed",
      latchMotionUnavailable:
        "Latch motion unavailable. Regenerate the preview.",
      width: "Width X",
      depth: "Depth Y",
      height: "Base height Z",
      radius: "Corner radius",
      wall: "Wall",
      floor: "Floor",
      lid: "Lid thickness",
      clearance: "Clearance per side",
      hingeClearance: "Hinge clearance",
      lip: "Locating skirt depth",
      hinge: "Hinge",
      pin: "Pin diameter",
      screw: "Corner screw",
      quality: "Surface resolution",
      qualityStandard: "Standard",
      qualityFine: "Fine",
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
        "Base on its floor; preserve the exported orientation of each part. Print the fit kit first. Print time depends on printer and profile.",
      printHelpClamshell:
        "Base and lid have equal height. Export the hinged assembly open at 180°, both outer faces on the bed. Keep that pose in the slicer and check the printed hinge.",
      printHelpOpen:
        "Base floor down, opening upwards. Check the walls and the bridges above hand grips, when enabled, in the slicer preview.",
      printHelpStack:
        "Print with the foot on the bed and the front open. Total height includes the foot. Test the fit between bins of the same family before stacking.",
      printHelpLatch:
        "Set: base, lid and two latches. Print the shells on their outer faces and the latches upright. Fit the latches onto the base pivots; release the hooks before lifting the lid. Check the fit of the printed parts.",
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
  function status(s, error = false, translationKey = null) {
    statusTranslationKey = translationKey;
    $("status").textContent = s;
    $("status").classList.toggle("warn", error);
    const banner = $("toast-banner");
    banner.textContent = s;
    banner.classList.add("visible");
    banner.classList.toggle("error", error);
    clearTimeout(status.timer);
    status.timer = setTimeout(
      () => banner.classList.remove("visible"),
      error ? 6000 : 2500,
    );
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
  function updatePrintHelp() {
    const key =
      {
        open_bin: "printHelpOpen",
        stackable_bin: "printHelpStack",
        snap_latch: "printHelpLatch",
        clamshell_pip: "printHelpClamshell",
      }[p.style] || "printHelp";
    document.querySelector('[data-i18n="printHelp"]').textContent = tr(key);
  }
  function updateClamshellNote() {
    let note = tr("equalHalfNote").replace(
      "{height}",
      (2 * Number(p.height_z) + Number(p.fit_clearance)).toFixed(2),
    );
    if (
      !localDirty &&
      meshParams.style === "clamshell_pip" &&
      INITIAL.print_bounds?.size
    ) {
      note +=
        " " +
        tr("clamshellPrintBounds").replace(
          "{size}",
          INITIAL.print_bounds.size
            .map((value) => Number(value).toFixed(1))
            .join("×"),
        );
    }
    $("clamshell-closed-height").textContent = note;
  }
  function updateClearanceLabels() {
    const clamshell = p.style === "clamshell_pip";
    const label = document.querySelector(
      '[data-slider="fit_clearance"] .ctrl-label',
    );
    label.dataset.pt = clamshell ? "Folga entre metades Z" : "Folga por lado";
    label.dataset.en = clamshell
      ? "Gap between halves Z"
      : "Clearance per side";
    label.textContent = label.dataset[lang];
    document.querySelector('[data-i18n="hud_mouth_hole"]').textContent = tr(
      clamshell ? "hingeClearance" : "clearance",
    );
    $("hud-clearance").textContent =
      Number(clamshell ? p.pip_clearance : p.fit_clearance).toFixed(2) + " mm";
  }
  function updateOpeningCaption() {
    document.querySelector('[data-i18n="open"]').textContent = tr(
      p.style === "snap_latch" ? "releaseAndOpen" : p.style === "rugged_box" ? "releaseClipsAndOpen" : "open",
    );
  }
  function updatePreviewText() {
    if (Number.isFinite(lastInterfaceError)) {
      $("surface").textContent =
        (lang === "pt" ? "Alvo de erro nas interfaces curvas ≤ " : "Curved interface chord-error target ≤ ") +
        lastInterfaceError.toFixed(3) + " mm";
    }
    if (statusTranslationKey === "ready") {
      $("status").textContent = tr("ready");
      $("toast-banner").textContent = tr("ready");
    }
  }
  function translate() {
    p.theme = theme;
    p.lang = lang;
    document.documentElement.lang = lang;
    document.documentElement.dataset.theme = theme;
    $("lang").textContent = lang.toUpperCase();
    $("theme").textContent = theme === "dark" ? "☾" : "☀";
    document
      .querySelectorAll("[data-i18n]")
      .forEach((e) => (e.textContent = tr(e.dataset.i18n)));
    document
      .querySelectorAll("[data-pt]")
      .forEach((e) => (e.textContent = e.dataset[lang]));
    updatePreviewText();
    updateClearanceLabels();
    updateOpeningCaption();
    updatePrintHelp();
    updateClamshellNote();
    if (p.style === "rugged_box") updateRuggedMotionStatus();
    const names = {
      base_and_lid: tr("both"),
      base_only: tr("baseOnly"),
      lid_only: tr("lidOnly"),
      gasket: tr("gasketOnly"),
      fit_test_kit: tr("kit"),
      full_suite: tr("full"),
    };
    for (const option of $("target").options)
      option.textContent = names[option.value] || option.value;
    presets();
    syncPresetSelection();
    features();
    drawPlan();
    render();
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
    updateClearanceLabels();
    updateOpeningCaption();
    updatePrintHelp();
    const openBin = p.style === "open_bin";
    const lidless = openBin || p.style === "stackable_bin";
    const heightLabel = document.querySelector(
      '[data-slider="height_z"] .ctrl-label',
    );
    heightLabel.dataset.pt =
      p.style === "clamshell_pip"
        ? "Altura de cada metade Z"
        : p.style === "stackable_bin"
          ? "Altura total Z"
          : "Altura Z";
    heightLabel.dataset.en =
      p.style === "clamshell_pip"
        ? "Height of each half Z"
        : p.style === "stackable_bin"
          ? "Total height Z"
          : "Height Z";
    heightLabel.textContent = heightLabel.dataset[lang];
    document.querySelector('[data-slider="snap_retention"]').style.display =
      p.style === "lip_snap" ? "grid" : "none";
    $("open-bin-handles").hidden = !openBin;
    $("snap-latch-options").hidden = p.style !== "snap_latch";
    $("stackable-bin-options").hidden = p.style !== "stackable_bin";
    const clamshell = p.style === "clamshell_pip";
    $("clamshell-pip-options").hidden = !clamshell;
    updateClamshellNote();
    $("clamshell-feature-warning").hidden =
      !clamshell ||
      !(
        ["standoffs", "cutouts", "dividers_x", "dividers_y"].some(
          (key) => p[key]?.length,
        ) || p.gasket_enabled
      );
    $("addPost").disabled = clamshell;
    $("addPort").disabled = clamshell;
    const diameterRow = document.querySelector(
      '[data-slider="hinge_pin_diameter"]',
    );
    diameterRow.style.display = ["rugged_box", "clamshell_pip"].includes(
      p.style,
    )
      ? "grid"
      : "none";
    const diameterLabel = diameterRow.querySelector(".ctrl-label");
    diameterLabel.dataset.pt = clamshell
      ? "Diâmetro do eixo integral"
      : "Diâmetro do pino";
    diameterLabel.dataset.en = clamshell
      ? "Integral axle diameter"
      : "Pin diameter";
    diameterLabel.textContent = diameterLabel.dataset[lang];
    $("open").disabled = lidless || INITIAL.preview_mode === "calibration";
    $("play").disabled = lidless || INITIAL.preview_mode === "calibration";
    for (const key of ["lid_height", "lip_depth", "fit_clearance"]) {
      const row = document.querySelector('[data-slider="' + key + '"]');
      row.style.display =
        lidless ||
        (p.style === "sliding_lid" && key !== "fit_clearance") ||
        (p.style === "snap_latch" && key === "lip_depth") ||
        (p.style === "clamshell_pip" && key !== "fit_clearance")
          ? "none"
          : "grid";
    }
    $("gasket_enabled").closest(".switch-row").style.display =
      (lidless || clamshell || p.style === "sliding_lid") && !p.gasket_enabled ? "none" : "flex";
    for (const key of ["gasket_width", "gasket_depth"])
      document.querySelector('[data-slider="' + key + '"]').style.display =
        lidless || ["clamshell_pip", "sliding_lid"].includes(p.style) ? "none" : "grid";
    for (const option of $("target").options) {
      option.disabled =
        (lidless &&
          ["lid_only", "gasket", "fit_test_kit"].includes(option.value)) ||
        (p.style === "snap_latch" && option.value === "fit_test_kit") ||
        (p.style === "clamshell_pip" &&
          !["base_and_lid", "full_suite"].includes(option.value)) ||
        (p.style === "rugged_box" && p.hinge_mode === "print_in_place" &&
          ["base_only", "lid_only"].includes(option.value)) ||
        (option.value === "gasket" && (!p.gasket_enabled || p.style === "sliding_lid"));
      if (option.value === "base_and_lid")
        option.textContent =
          p.style === "clamshell_pip"
            ? tr("hingedAssembly")
            : lidless
              ? tr("baseOnly")
              : tr("both");
    }
    if ([...$("target").options].some(option => option.value === p.export_target && option.disabled))
      p.export_target = "base_and_lid";
    $("name").value = p.name;
    document
      .querySelectorAll("[data-p]")
      .forEach((e) => (e.value = p[e.dataset.p]));
    for (const key of [
      "style",
      "hinge_mode",
      "screw_size",
      "quality",
      "handle_faces",
    ])
      $(key).value = p[key];
    for (const key of [
      "gasket_enabled",
      "auto_configure_slicer",
      "handles_enabled",
    ])
      $(key).checked = p[key];
    $("dividers_x").value = p.dividers_x.join(", ");
    $("dividers_y").value = p.dividers_y.join(", ");
    $("target").value = p.export_target;
    document
      .querySelectorAll(".rugged")
      .forEach(
        (e) => (e.style.display = p.style === "rugged_box" ? "grid" : "none"),
      );
    document
      .querySelectorAll(".screw")
      .forEach(
        (e) => (e.style.display = p.style === "screw_corner" ? "grid" : "none"),
      );
    $("pipNote").textContent =
      p.style === "rugged_box" && p.hinge_mode === "print_in_place"
        ? tr("pip")
        : "";
    document
      .querySelectorAll("[data-param-range]")
      .forEach((e) => (e.value = p[e.dataset.paramRange]));
    syncPresetSelection();
    features();
    drawPlan();
    buttons();
    render();
  }
  function requestPreview(commit = true) {
    clearTimeout(timer);
    localDirty = true;
    const request_id = ++serial;
    latest = request_id;
    if (!commit) return;
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
    if (
      key === "style" &&
      ((["open_bin", "stackable_bin"].includes(value) &&
        ["lid_only", "gasket", "fit_test_kit"].includes(p.export_target)) ||
        (value === "snap_latch" && p.export_target === "fit_test_kit") ||
        (value === "clamshell_pip" &&
          !["base_and_lid", "full_suite"].includes(p.export_target)))
    )
      p.export_target = "base_and_lid";
    sync();
    requestPreview();
  }
  document
    .querySelectorAll("[data-p]")
    .forEach((e) =>
      e.addEventListener("change", () => change(e.dataset.p, Number(e.value))),
    );
  document
    .querySelectorAll("[data-p],#name,#dividers_x,#dividers_y")
    .forEach((element) =>
      element.addEventListener("input", () => requestPreview(false)),
    );
  for (const key of [
    "style",
    "hinge_mode",
    "screw_size",
    "quality",
    "handle_faces",
  ])
    $(key).onchange = () => change(key, $(key).value);
  for (const key of [
    "gasket_enabled",
    "auto_configure_slicer",
    "handles_enabled",
  ])
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
    userOverrodeTheme = true;
    theme = theme === "dark" ? "light" : "dark";
    translate();
  };
  $("sync").onclick = () => send({ type: "sync_printer" });
  $("folder").onclick = () => send({ type: "open_exports_folder" });
  document.addEventListener("keydown", (e) => {
    const tag =
      e.target && e.target.tagName
        ? String(e.target.tagName).toUpperCase()
        : "";
    if (tag === "INPUT" || tag === "TEXTAREA" || e.target?.isContentEditable)
      return;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
      e.preventDefault();
      (e.shiftKey ? $("redo") : $("undo")).click();
    } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
      e.preventDefault();
      $("redo").click();
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
            x.classList.toggle("section-hidden", x.dataset.section !== tab),
          );
        drawPlan();
      }),
  );
  $("savePreset").onclick = () =>
    send({ type: "save_preset", params: p, name: p.name });
  function fieldInput(label, value, onchange, step = ".1") {
    const lab = document.createElement("label");
    lab.className = "ctrl-row";
    const span = document.createElement("span");
    span.textContent = label;
    const inp = document.createElement("input");
    inp.className = "ctrl-num";
    span.className = "ctrl-label";
    inp.type = "number";
    inp.step = step;
    inp.value = value;
    inp.onchange = () => onchange(Number(inp.value));
    lab.append(span, inp);
    return lab;
  }
  function selectInput(label, value, values, onchange) {
    const lab = document.createElement("label");
    lab.className = "ctrl-row";
    const span = document.createElement("span");
    span.textContent = label;
    const sel = document.createElement("select");
    sel.className = "vp-select box-select";
    span.className = "ctrl-label";
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
      card.className = "box-feature";
      const head = document.createElement("div");
      head.className = "box-feature-title";
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
        row.className = "box-pair";
        row.append(
          fieldInput(a, s[ka], (v) => featureChange("standoffs", i, ka, v)),
          fieldInput(b, s[kb], (v) => featureChange("standoffs", i, kb, v)),
        );
        card.append(row);
      });
      const row = document.createElement("div");
      row.className = "box-pair";
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
      card.className = "box-feature";
      const head = document.createElement("div");
      head.className = "box-feature-title";
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
      row.className = "box-pair";
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
        r.className = "box-pair";
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
    const rounded = (x, y, width, height, radius) => {
      c.beginPath();
      if (typeof c.roundRect === "function")
        c.roundRect(x, y, width, height, radius);
      else c.rect(x, y, width, height);
    };
    rounded(
      cx - (p.width_x * s) / 2,
      cy - (p.depth_y * s) / 2,
      p.width_x * s,
      p.depth_y * s,
      p.corner_radius * s,
    );
    c.fillStyle =
      theme === "dark" ? "rgba(0,168,150,.18)" : "rgba(0,137,123,.12)";
    c.fill();
    c.strokeStyle = theme === "dark" ? "#00bfa5" : "#00897b";
    c.lineWidth = 2;
    c.stroke();
    rounded(
      cx - (p.width_x / 2 - p.wall_thickness) * s,
      cy - (p.depth_y / 2 - p.wall_thickness) * s,
      (p.width_x - 2 * p.wall_thickness) * s,
      (p.depth_y - 2 * p.wall_thickness) * s,
      Math.max(0, p.corner_radius - p.wall_thickness) * s,
    );
    c.fillStyle = theme === "dark" ? "#17191e" : "#ffffff";
    c.fill();
    c.lineWidth = 1;
    c.stroke();
    c.strokeStyle = theme === "dark" ? "#36444f" : "#cad5dc";
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
    requestPreview(false);
    const r = $("plan").getBoundingClientRect(),
      s = Math.min(455 / p.width_x, 285 / p.depth_y);
    p.standoffs[drag].x =
      Math.round(((((e.clientX - r.left) * 500) / r.width - 250) / s) * 10) /
      10;
    p.standoffs[drag].y =
      Math.round(((165 - ((e.clientY - r.top) * 330) / r.height) / s) * 10) /
      10;
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
    document.querySelectorAll("[data-action]").forEach((b) => {
      if (b.dataset.action !== "open_folder") b.disabled = on;
    });
  }
  function manufacture(type, format) {
    p.export_target = $("target").value;
    p.lang = lang;
    busy(true);
    status(tr("generating"));
    if (!send({ type, format, params: p, export_target: p.export_target })) {
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
    if (m.type === "randomize_result") {
      if (m.ok) setDesign(m.params);
      else status(m.message, true);
      return;
    }
    if (m.type === "design_changed") {
      if (localDirty) return;
      p = clone(m.params);
      sync();
      requestPreview();
      return;
    }
    if (m.type === "init_state") {
      if (m.host) {
        INITIAL.host = m.host;
        updatePrinter();
      }
      resolveHostTheme(m);
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
      if (
        m.params?.style === "snap_latch" &&
        (!m.latch_motion?.clip_left || !m.latch_motion?.clip_right)
      ) {
        status(tr("latchMotionUnavailable"), true);
        return;
      }
      if (m.params?.style === "snap_latch") {
        try {
          for (const part of ["clip_left", "clip_right", "lid"])
            snapLatchTransform(part, 0, m.latch_motion);
        } catch (_) {
          status(tr("latchMotionUnavailable"), true);
          return;
        }
      }
      localDirty = false;
      p = clone(m.params);
      p.lang = lang;
      p.theme = theme;
      meshParams = clone(m.params);
      INITIAL.hinge = m.hinge;
      INITIAL.print_bounds = m.print_bounds || null;
      INITIAL.latch_motion = m.latch_motion || null;
      INITIAL.preview_mode = m.preview_mode || "assembly";
      if (!m.geometry_key || m.geometry_key !== meshRevisionKey) {
        loadMeshes(m.meshes);
        meshRevisionKey = m.geometry_key || null;
      }
      $("volume").textContent = m.volume_cm3.toFixed(1);
      $("triangles").textContent =
        (m.meshes.reduce((s, x) => s + x.triangle_count, 0) / 1000).toFixed(0) +
        "k";
      lastInterfaceError = Math.max(...m.meshes.map((x) => x.interface_error_mm));
      updatePreviewText();
      status(tr("ready"), false, "ready");
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
  // Canonical material, three-light shader, bed grid and CAD annotation styling
  // adapted from the MIT Orca Studio reference. Geometry always comes from Python.
  let gl = $("gl").getContext("webgl2", {
      antialias: true,
      alpha: false,
      depth: true,
    }),
    program = null,
    lineProg = null,
    bedBuffer = null,
    bedVertCount = 0,
    yaw = -0.75,
    pitch = 0.68,
    zoom = 1,
    orbit = null,
    material = "emerald_silk",
    wire = false,
    calipers = false,
    spin = false,
    cutAxis = "y",
    lastFrame = null;
  const TWO_PI = Math.PI * 2;
  const MATERIAL_PRESETS = {
    emerald_silk: {
      base: [0.02, 0.72, 0.63],
      saucer: [0.14, 0.24, 0.25],
      rough: 0.22,
      metal: 0.3,
    },
    terracotta: {
      base: [0.79, 0.4, 0.28],
      saucer: [0.68, 0.34, 0.24],
      rough: 0.78,
      metal: 0.02,
    },
    matte_ceramic: {
      base: [0.91, 0.9, 0.87],
      saucer: [0.8, 0.78, 0.74],
      rough: 0.66,
      metal: 0.02,
    },
    copper_bronze: {
      base: [0.76, 0.48, 0.31],
      saucer: [0.36, 0.25, 0.2],
      rough: 0.26,
      metal: 0.72,
    },
    xray: {
      base: [0.04, 0.8, 0.72],
      saucer: [0.16, 0.48, 0.52],
      rough: 0.18,
      metal: 0.15,
    },
    heatmap: {
      base: [0.05, 0.76, 0.45],
      saucer: [0.05, 0.76, 0.45],
      rough: 0.55,
      metal: 0.05,
    },
  };
  function shader(type, source) {
    const s = gl.createShader(type);
    gl.shaderSource(s, source);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
      throw Error(gl.getShaderInfoLog(s));
    return s;
  }
  function compileProgram(vs, fs) {
    const p = gl.createProgram();
    gl.attachShader(p, shader(gl.VERTEX_SHADER, vs));
    gl.attachShader(p, shader(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS))
      throw Error(gl.getProgramInfoLog(p));
    return p;
  }
  function initializeGL() {
    if (!gl) {
      status("WebGL2 indisponível / unavailable", true);
      return;
    }
    program = compileProgram(
      `#version 300 es
 precision highp float;layout(location=0)in vec3 a_pos;layout(location=1)in vec3 a_nrm;layout(location=2)in float a_role;
 uniform mat4 u_mvp;uniform mat4 u_model;out vec3 v_pos;out vec3 v_localPos;out vec3 v_nrm;out float v_ovh;out float v_part;out float v_surfaceRole;
 void main(){vec4 w=u_model*vec4(a_pos,1.0);v_pos=w.xyz;v_localPos=a_pos;v_nrm=mat3(u_model)*a_nrm;v_ovh=degrees(asin(clamp(-normalize(v_nrm).z,0.0,1.0)));v_part=0.0;v_surfaceRole=a_role;gl_Position=u_mvp*w;}`,
      `#version 300 es
      precision highp float;
      in vec3 v_pos;
      in vec3 v_localPos;
      in vec3 v_nrm;
      in float v_ovh;
      in float v_part;
      in float v_surfaceRole;
      uniform vec3 u_eye;
      uniform mat4 u_model;
      uniform vec3 u_baseColor;
      uniform vec3 u_saucerColor;
      uniform float u_roughness;
      uniform float u_metallic;
      uniform float u_heatmap;
      uniform float u_xrayMode;
      uniform float u_clipMode;
      uniform float u_clipVal;
      uniform float u_passMode;
      uniform float u_lightTheme;
      out vec4 outColor;

      vec3 heatmapColor(float deg) {
        vec3 safeA = vec3(0.02, 0.76, 0.45);
        vec3 safeB = vec3(0.18, 0.85, 0.42);
        vec3 warn  = vec3(1.00, 0.68, 0.02);
        vec3 crit  = vec3(0.98, 0.20, 0.16);
        if (deg <= 42.0) return mix(safeA, safeB, clamp(deg / 42.0, 0.0, 1.0));
        if (deg <= 46.0) return mix(safeB, warn, (deg - 42.0) / 4.0);
        if (deg <= 55.0) return mix(warn, crit, (deg - 46.0) / 9.0);
        return crit;
      }

      void main() {
        // Derivatives precede clipping/discard so every fragment quad is defined.
        vec3 faceCross = cross(dFdx(v_localPos), dFdy(v_localPos));
        vec3 localFace = faceCross / max(length(faceCross), 1e-12);
        float clipRim = 0.0;
        if (u_clipMode > 0.5 && u_passMode < 0.5) {
          float dist = (u_clipMode < 1.5) ? (v_pos.y - u_clipVal) : (u_clipVal - v_pos.z);
          if (dist < 0.0) {
            discard;
          }
          if (dist < 1.45) {
            clipRim = 1.0 - (dist / 1.45);
          }
        } else if (u_clipMode > 0.5 && u_clipMode < 1.5 && u_passMode > 1.5) {
          if (v_pos.y < u_clipVal) discard;
        }

        // Special Pass 1: Solid Horizontal Z-Slice CAD Cross-Section Cap
        if (u_passMode > 0.5 && u_passMode < 1.5) {
          float hatch = sin((v_pos.x + v_pos.y) * 2.35);
          vec3 capA = vec3(1.00, 0.76, 0.20);
          vec3 capB = vec3(0.08, 0.92, 0.80);
          vec3 cCol = mix(capA, capB, hatch > 0.25 ? 0.65 : 0.12);
          outColor = vec4(cCol, u_xrayMode > 0.5 ? 0.90 : 1.0);
          return;
        }

        // Special Pass 2: Holographic Spiral Mode Top-Cap Indicator Disk
        if (u_passMode > 1.5) {
          float r = length(v_pos.xy);
          float rings = 0.5 + 0.5 * sin(r * 1.45);
          float diag = step(0.35, fract((v_pos.x - v_pos.y) * 0.14));
          vec3 holoCol = mix(vec3(1.00, 0.68, 0.18), vec3(0.10, 0.92, 0.82), rings * 0.65);
          float alpha = 0.18 + 0.20 * diag * rings;
          outColor = vec4(holoCol, alpha);
          return;
        }

        vec3 N = normalize(v_nrm);
        // Large analytic wall/floor triangles must retain their planar normal.
        // Test in the canonical part frame so a rotating lid keeps its creases.
        // Curved triangles retain the interpolated studio normal; no mesh copies.
        float axial = max(max(abs(localFace.x), abs(localFace.y)), abs(localFace.z));
        if (axial > 0.99995) {
          vec3 faceNormal = normalize(mat3(u_model) * localFace);
          if (dot(faceNormal, N) < 0.0) faceNormal = -faceNormal;
          N = faceNormal;
        }
        bool backFace = !gl_FrontFacing;
        if (backFace) N = -N;

        vec3 V = normalize(u_eye - v_pos);
        vec3 L1 = normalize(vec3(-0.52, -0.64, 0.56));
        vec3 L2 = normalize(vec3(0.68, -0.25, 0.42));
        vec3 L3 = normalize(vec3(0.05, 0.82, 0.35));
        float diff1 = max(dot(N, L1), 0.0);
        float diff2 = max(dot(N, L2), 0.0);
        float diff3 = max(dot(N, L3), 0.0);

        // Two-Pass Translucent X-Ray / Wall Caliper Shader
        if (u_xrayMode > 0.5) {
          float ndv = abs(dot(N, V));
          float fresnel = pow(1.0 - clamp(ndv, 0.0, 1.0), 2.15);
          vec3 Hx = normalize(L1 + V);
          float specX = pow(max(dot(N, Hx), 0.0), 54.0) * 0.45;

          vec3 xCol;
          float xAlpha;
          if (v_surfaceRole > 0.5 && v_surfaceRole < 1.5) {
            // Inner cavity wall, inner floor, and drainage holes -> warm glowing amber/coral!
            bool isFloorPlane = abs(N.z) > 0.68;
            vec3 innerBase = isFloorPlane ? vec3(1.00, 0.43, 0.18) : vec3(1.00, 0.58, 0.22);
            if (u_lightTheme > 0.5) innerBase *= 0.88;
            xCol = innerBase * (0.48 + 0.55 * diff1 + 0.25 * diff2)
                 + vec3(1.00, 0.84, 0.46) * (fresnel * 0.65 + specX * 0.5);
            xAlpha = isFloorPlane ? (0.52 + 0.28 * fresnel) : (0.35 + 0.42 * fresnel);
          } else if (v_surfaceRole >= 1.5) {
            // Top mouth lip / rim -> crisp luminous cyan-gold ring
            xCol = vec3(0.28, 0.96, 0.86) * (0.58 + 0.42 * diff1) + vec3(0.85) * specX;
            xAlpha = 0.62 + 0.28 * fresnel;
          } else {
            // Outer wall -> smoky emerald/cyan glass with Fresnel rim glow
            vec3 glassBase = (u_lightTheme > 0.5) ? vec3(0.00, 0.56, 0.52) : vec3(0.05, 0.82, 0.74);
            if (v_part > 0.5) glassBase = (u_lightTheme > 0.5) ? vec3(0.22, 0.42, 0.46) : vec3(0.18, 0.55, 0.58);
            xCol = glassBase * (0.40 + 0.52 * diff1 + 0.22 * diff2)
                 + vec3(0.46, 0.98, 0.92) * (fresnel * 0.78)
                 + vec3(1.0) * specX;
            xAlpha = 0.15 + 0.48 * fresnel + specX * 0.28;
          }

          if (backFace) xAlpha *= 0.76;
          if (clipRim > 0.01) {
            xCol = mix(xCol, vec3(1.00, 0.82, 0.24), clipRim * 0.88);
            xAlpha = max(xAlpha, 0.94 * clipRim);
          }
          outColor = vec4(clamp(xCol, 0.0, 1.0), clamp(xAlpha, 0.08, 0.95));
          return;
        }

        // Standard Opaque PBR-Lite Studio Shading
        vec3 albedo = v_part > 0.5 ? u_saucerColor : u_baseColor;
        if (u_heatmap > 0.5) {
          albedo = heatmapColor(v_ovh);
        } else if (u_clipMode > 0.5 && v_surfaceRole > 0.5 && v_surfaceRole < 1.5) {
          albedo = mix(albedo, vec3(0.98, 0.58, 0.24), 0.42);
        } else if (backFace && u_clipMode > 0.5) {
          albedo = mix(albedo, vec3(1.0, 0.72, 0.28), 0.45);
        }

        float layerWave = 0.985 + 0.015 * sin(v_pos.z * 31.4159);
        albedo *= layerWave;

        vec3 H1 = normalize(L1 + V);
        float shininess = mix(96.0, 14.0, u_roughness);
        float spec1 = pow(max(dot(N, H1), 0.0), shininess) * mix(0.28, 0.85, 1.0 - u_roughness);

        float hemi = 0.5 + 0.5 * N.z;
        vec3 ambient = mix(vec3(0.14, 0.16, 0.20), vec3(0.34, 0.37, 0.42), hemi);
        float rim = pow(1.0 - max(dot(N, V), 0.0), 3.2) * 0.22;

        vec3 specTint = mix(vec3(1.0), albedo, u_metallic);
        vec3 color = albedo * (ambient + 0.78 * diff1 + 0.32 * diff2 + 0.22 * diff3)
                   + specTint * spec1
                   + vec3(0.55, 0.85, 0.80) * rim;

        if (clipRim > 0.01) {
          color = mix(color, vec3(1.00, 0.80, 0.22), clipRim * 0.85);
        }

        color = pow(clamp(color, 0.0, 1.0), vec3(0.92));
        outColor = vec4(color, 1.0);
      }
    `,
    );
    lineProg = compileProgram(
      `#version 300 es
 precision highp float;layout(location=0)in vec3 a_pos;uniform mat4 u_mvp;void main(){gl_Position=u_mvp*vec4(a_pos,1.0);}`,
      `#version 300 es
 precision highp float;uniform vec4 u_color;out vec4 outColor;void main(){outColor=u_color;}`,
    );
    bedBuffer = gl.createBuffer();
    rebuildBedGeometry();
    gl.enable(gl.DEPTH_TEST);
  }
  function currentPrinter() {
    return (
      INITIAL.host || {
        bed_x: 220,
        bed_y: 220,
        max_z: 250,
        nozzle_mm: 0.4,
        line_width_mm: 0.42,
      }
    );
  }
  function rebuildBedGeometry() {
    if (!gl || !bedBuffer) return;
    const bx = Math.max(80, Number(currentPrinter().bed_x) || 220);
    const by = Math.max(80, Number(currentPrinter().bed_y) || 220);
    const hx = 0.5 * bx;
    const hy = 0.5 * by;
    const isCircular =
      String(currentPrinter().bed_shape || "").toLowerCase() === "circular";
    const verts = [];

    const step = bx > 320 || by > 320 ? 30 : 20;
    if (isCircular) {
      const rBed = Math.min(hx, hy);
      const rSq = rBed * rBed;
      for (
        let x = -Math.floor(rBed / step) * step;
        x <= rBed + 0.01;
        x += step
      ) {
        const spanY = Math.sqrt(Math.max(0.0, rSq - x * x));
        if (spanY > 1.0) verts.push(x, -spanY, -0.08, x, spanY, -0.08);
      }
      for (
        let y = -Math.floor(rBed / step) * step;
        y <= rBed + 0.01;
        y += step
      ) {
        const spanX = Math.sqrt(Math.max(0.0, rSq - y * y));
        if (spanX > 1.0) verts.push(-spanX, y, -0.08, spanX, y, -0.08);
      }
      const ringSegs = 72;
      for (let s = 0; s < ringSegs; s++) {
        const a0 = (TWO_PI * s) / ringSegs;
        const a1 = (TWO_PI * (s + 1)) / ringSegs;
        verts.push(
          rBed * Math.cos(a0),
          rBed * Math.sin(a0),
          0.02,
          rBed * Math.cos(a1),
          rBed * Math.sin(a1),
          0.02,
        );
      }
      verts.push(-16, -rBed - 4, 0.02, 16, -rBed - 4, 0.02);
    } else {
      for (let x = -Math.floor(hx / step) * step; x <= hx + 0.01; x += step) {
        verts.push(x, -hy, -0.08, x, hy, -0.08);
      }
      for (let y = -Math.floor(hy / step) * step; y <= hy + 0.01; y += step) {
        verts.push(-hx, y, -0.08, hx, y, -0.08);
      }
      verts.push(
        -hx,
        -hy,
        0.02,
        hx,
        -hy,
        0.02,
        hx,
        -hy,
        0.02,
        hx,
        hy,
        0.02,
        hx,
        hy,
        0.02,
        -hx,
        hy,
        0.02,
        -hx,
        hy,
        0.02,
        -hx,
        -hy,
        0.02,
      );
      verts.push(-18, -hy - 4, 0.02, 18, -hy - 4, 0.02);
    }

    const arr = new Float32Array(verts);
    bedVertCount = arr.length / 3;
    gl.bindBuffer(gl.ARRAY_BUFFER, bedBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, arr, gl.STATIC_DRAW);
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
  function openingFraction(value = Number($("open").value)) {
    const shape = typeof meshParams === "undefined" ? p : meshParams;
    return value / (shape.style === "clamshell_pip" ? 180 : 100);
  }
  function openingLabel() {
    const suffix = meshParams.style === "clamshell_pip" ? "°" : "%";
    $("openValue").textContent = Math.round(Number($("open").value)) + suffix;
    if (meshParams.style === "snap_latch") updateLatchMotionStatus();
    if (meshParams.style === "rugged_box") updateRuggedMotionStatus();
  }
  function configureOpening() {
    const nextStyle = meshParams.style;
    const isClamshell = nextStyle === "clamshell_pip";
    $("open").max = isClamshell ? "180" : "100";
    if (isClamshell && openingStyle !== nextStyle) $("open").value = "180";
    else if (["snap_latch", "rugged_box"].includes(nextStyle) && openingStyle !== nextStyle)
      $("open").value = "0";
    else if (
      !isClamshell &&
      !["snap_latch", "rugged_box"].includes(nextStyle) &&
      ["clamshell_pip", "snap_latch", "rugged_box"].includes(openingStyle)
    )
      $("open").value = "25";
    openingStyle = nextStyle;
    openingLabel();
  }
  function snapLatchTransform(part, opening, motion) {
    if (part !== "lid" && !part.startsWith("clip")) return I();
    const left = motion?.clip_left;
    const right = motion?.clip_right;
    if (!left || !right) throw Error("Missing latch motion metadata");
    for (const info of [left, right]) {
      if (!info.pivot || ![info.pivot.x, info.pivot.y, info.pivot.z, info.release_fraction, info.release_angle, info.lid_lift_mm].every(Number.isFinite) || info.release_fraction <= 0 || info.release_fraction >= 1 || info.release_angle <= 0 || info.lid_lift_mm <= 0)
        throw Error("Invalid latch motion metadata");
    }
    const phase = Math.max(0, Math.min(1, opening));
    const releaseFraction = Math.max(
      left.release_fraction,
      right.release_fraction,
    );
    if (part === "lid") {
      const liftPhase = Math.max(
        0,
        Math.min(1, (phase - releaseFraction) / (1 - releaseFraction)),
      );
      return translateM(0, 0, liftPhase * left.lid_lift_mm);
    }
    const info = motion[part];
    if (!info) throw Error("Unknown latch part: " + part);
    const angle =
      (Math.min(1, phase / info.release_fraction) *
        info.release_angle *
        Math.PI) /
      180;
    const pivot = info.pivot;
    return mult(
      translateM(pivot.x, pivot.y, pivot.z),
      mult(rotateX(angle), translateM(-pivot.x, -pivot.y, -pivot.z)),
    );
  }
  function updateLatchMotionStatus() {
    const label = $("latch-motion-phase");
    const info = INITIAL.latch_motion?.clip_left;
    label.hidden = !info;
    if (!info) return;
    const phase = openingFraction();
    const key =
      phase <= 0
        ? "latchesEngaged"
        : phase < info.release_fraction
          ? "releasingLatches"
          : phase < 1
            ? "liftingLid"
            : "lidRemoved";
    const message = tr(key);
    if (label.textContent !== message) label.textContent = message;
  }
  function updateRuggedMotionStatus() {
    const label = $("rugged-motion-phase");
    if (!label) return;
    const shape = typeof meshParams === "undefined" ? p : meshParams;
    label.hidden = shape.style !== "rugged_box" || INITIAL.preview_mode === "calibration";
    if (label.hidden) return;
    const phase = openingFraction();
    const message = tr(phase <= 0 ? "ruggedClosed" : phase < 0.25 ? "ruggedReleasing" : phase < 1 ? "ruggedOpening" : "ruggedOpen");
    if (label.textContent !== message) label.textContent = message;
  }
  function partTransform(part, opening = openingFraction(), offset = null) {
    const shape = typeof meshParams === "undefined" ? p : meshParams;
    const frame = translateM(...(offset || [0, 0, 0]));
    if (INITIAL.preview_mode === "calibration") return frame;
    if (shape.style === "snap_latch")
      return mult(
        frame,
        snapLatchTransform(part, opening, INITIAL.latch_motion),
      );
    let model = I();
    if (shape.style === "rugged_box") {
      // Remove the spring clips completely before the hinged lid rotates.
      const phase = Math.max(0, Math.min(1, opening));
      const releaseFraction = 0.25;
      if (part.startsWith("clip"))
        model = translateM(0, -15 * Math.min(1, phase / releaseFraction), 0);
      else if (part === "lid") {
        const h = INITIAL.hinge || {y: shape.depth_y / 2 + 5, z: shape.height_z - 4};
        const angle = -Math.PI * Math.max(0, (phase - releaseFraction) / (1 - releaseFraction));
        model = mult(translateM(0, h.y, h.z), mult(rotateX(angle), translateM(0, -h.y, -h.z)));
      }
      return mult(frame, model);
    }
    if (part === "lid") {
      if (shape.style === "clamshell_pip") {
        const h = INITIAL.hinge || {
          y: shape.depth_y / 2 + 5,
          z: shape.height_z - 4,
        };
        model = mult(
          translateM(0, h.y, h.z),
          mult(rotateX(-opening * Math.PI), translateM(0, -h.y, -h.z)),
        );
      } else if (shape.style === "sliding_lid")
        model = translateM(0, -opening * (shape.depth_y + 10), 0);
      else model = translateM(0, 0, opening * 50);
    }
    return mult(frame, model);
  }
  function transformPoint(m, x, y, z) {
    return [
      m[0] * x + m[4] * y + m[8] * z + m[12],
      m[1] * x + m[5] * y + m[9] * z + m[13],
      m[2] * x + m[6] * y + m[10] * z + m[14],
    ];
  }
  function sceneBounds(opening = openingFraction()) {
    if (!meshes.length) return null;
    const lo = [Infinity, Infinity, Infinity],
      hi = [-Infinity, -Infinity, -Infinity];
    for (const mesh of meshes) {
      const m = partTransform(mesh.part, opening, mesh.preview_offset),
        b = mesh.bounds;
      for (const x of [b.min[0], b.max[0]])
        for (const y of [b.min[1], b.max[1]])
          for (const z of [b.min[2], b.max[2]]) {
            const q = transformPoint(m, x, y, z);
            for (let a = 0; a < 3; a++) {
              lo[a] = Math.min(lo[a], q[a]);
              hi[a] = Math.max(hi[a], q[a]);
            }
          }
    }
    return {
      min: lo,
      max: hi,
      size: hi.map((x, i) => x - lo[i]),
      center: hi.map((x, i) => (x + lo[i]) / 2),
    };
  }
  function camera(aspect) {
    const b = sceneBounds() || {
        min: [-0.5, -0.5, -0.5],
        max: [0.5, 0.5, 0.5],
        center: [0, 0, 0],
        size: [1, 1, 1],
      },
      target = b.center;
    const radius = Math.max(0.1, Math.hypot(...b.size) / 2),
      fov = (38 * Math.PI) / 180,
      fitAngle = Math.min(fov, 2 * Math.atan(Math.tan(fov / 2) * aspect)),
      distance = ((radius / Math.sin(fitAngle / 2)) * 1.12) / zoom;
    const eye = [
        target[0] + distance * Math.cos(yaw) * Math.cos(pitch),
        target[1] + distance * Math.sin(yaw) * Math.cos(pitch),
        target[2] + distance * Math.sin(pitch),
      ],
      z = normalize(eye.map((x, i) => x - target[i])),
      x = normalize(cross([0, 0, 1], z)),
      y = cross(z, x),
      view = new Float32Array([
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
      near = Math.max(0.01, distance - radius * 1.7),
      far = Math.max(100, distance + radius * 3),
      f = 1 / Math.tan(fov / 2),
      projection = new Float32Array([
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
    return {
      mvp: mult(projection, view),
      eye,
      bounds: b,
      distance,
      target,
    };
  }
  function decode(s, ctor) {
    const b = atob(s),
      a = new Uint8Array(b.length);
    for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
    return new ctor(a.buffer);
  }
  function loadMeshes(items) {
    configureOpening();
    const calibration = INITIAL.preview_mode === "calibration";
    $("open").disabled =
      calibration || ["open_bin", "stackable_bin"].includes(meshParams.style);
    $("play").disabled =
      calibration || ["open_bin", "stackable_bin"].includes(meshParams.style);
    if (
      calibration ||
      ["open_bin", "stackable_bin"].includes(meshParams.style)
    ) {
      playing = false;
      $("play").textContent = "▶";
    }
    if (!gl) return;
    for (const m of meshes) {
      for (const b of [m.pb, m.nb, m.rb, m.ib, m.wireBuffer])
        if (b) gl.deleteBuffer(b);
      gl.deleteVertexArray(m.vao);
    }
    meshes = items.map((item) => {
      const pos = decode(item.vertices, Float32Array),
        tri = decode(item.triangles, Uint32Array),
        norm = new Float32Array(pos.length),
        roles = new Float32Array(pos.length / 3);
      const lo = [Infinity, Infinity, Infinity],
        hi = [-Infinity, -Infinity, -Infinity];
      let maxOverhang = 0;
      for (let i = 0; i < pos.length; i += 3)
        for (let a = 0; a < 3; a++) {
          lo[a] = Math.min(lo[a], pos[i + a]);
          hi[a] = Math.max(hi[a], pos[i + a]);
        }
      for (let i = 0; i < tri.length; i += 3) {
        const a = tri[i] * 3,
          b = tri[i + 1] * 3,
          c = tri[i + 2] * 3,
          ux = pos[b] - pos[a],
          uy = pos[b + 1] - pos[a + 1],
          uz = pos[b + 2] - pos[a + 2],
          vx = pos[c] - pos[a],
          vy = pos[c + 1] - pos[a + 1],
          vz = pos[c + 2] - pos[a + 2],
          nx = uy * vz - uz * vy,
          ny = uz * vx - ux * vz,
          nz = ux * vy - uy * vx,
          l = Math.hypot(nx, ny, nz) || 1;
        if (Math.max(pos[a + 2], pos[b + 2], pos[c + 2]) > lo[2] + 0.02)
          maxOverhang = Math.max(
            maxOverhang,
            (Math.asin(Math.max(0, Math.min(1, -nz / l))) * 180) / Math.PI,
          );
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
        const inner = norm[i] * pos[i] + norm[i + 1] * pos[i + 1] < 0,
          innerFloor =
            norm[i + 2] > 0.7 &&
            Math.abs(pos[i + 2] - meshParams.floor_thickness) < 0.03;
        roles[i / 3] =
          inner || innerFloor
            ? 1
            : pos[i + 2] > meshParams.height_z - 0.03 && norm[i + 2] > 0.6
              ? 2
              : 0;
      }
      const vao = gl.createVertexArray();
      gl.bindVertexArray(vao);
      const upload = (loc, data, size) => {
        const b = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, b);
        gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, size, gl.FLOAT, false, 0, 0);
        return b;
      };
      const pb = upload(0, pos, 3),
        nb = upload(1, norm, 3),
        rb = upload(2, roles, 1),
        ib = gl.createBuffer();
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, tri, gl.STATIC_DRAW);
      return {
        ...item,
        bounds: { min: lo, max: hi, size: hi.map((x, i) => x - lo[i]) },
        vao,
        pb,
        nb,
        rb,
        ib,
        count: tri.length,
        indices: tri,
        maxOverhang,
        positions: pos,
      };
    });
    zoom = 1;
    render();
  }
  function drawLines(buffer, count, mvp, color) {
    gl.useProgram(lineProg);
    gl.uniformMatrix4fv(gl.getUniformLocation(lineProg, "u_mvp"), false, mvp);
    gl.uniform4fv(gl.getUniformLocation(lineProg, "u_color"), color);
    gl.bindVertexArray(null);
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.LINES, 0, count);
  }
  function updateHud(b) {
    if (!b) return;
    if (meshParams.style === "snap_latch") updateLatchMotionStatus();
    const h = currentPrinter(),
      printSize =
        meshParams.style === "clamshell_pip" && INITIAL.print_bounds?.size
          ? INITIAL.print_bounds.size
          : b.size,
      fits =
        printSize[0] <= h.bed_x &&
        printSize[1] <= h.bed_y &&
        printSize[2] <= h.max_z;
    $("hud-dims").textContent = b.size.map((x) => x.toFixed(1)).join("×");
    $("hud-wall-floor").textContent =
      `${p.wall_thickness.toFixed(1)} / ${p.floor_thickness.toFixed(1)} mm`;
    $("hud-clearance").textContent =
      Number(
        p.style === "clamshell_pip" ? p.pip_clearance : p.fit_clearance,
      ).toFixed(2) + " mm";
    $("hud-overhang").textContent =
      Math.max(0, ...meshes.map((m) => m.maxOverhang)).toFixed(1) + "°";
    $("hud-status-pill").textContent = fits ? "OK" : "⚠";
    $("hud-status-pill").className =
      "hud-status-pill " + (fits ? "ok" : "warn");
    $("bed-alert-banner").classList.toggle("visible", !fits);
    $("wall-perim-hint").textContent =
      `≈ ${Math.ceil(p.wall_thickness / (h.line_width_mm || 0.42))} ${lang === "pt" ? "perímetros de" : "walls of"} ${(h.line_width_mm || 0.42).toFixed(2)} mm`;
  }
  function render() {
    if (!gl || !program) return;
    const cv = $("gl"),
      r = cv.getBoundingClientRect(),
      dpr = Math.min(devicePixelRatio || 1, 2),
      w = Math.max(1, Math.floor(r.width * dpr)),
      h = Math.max(1, Math.floor(r.height * dpr));
    if (cv.width !== w || cv.height !== h) {
      cv.width = w;
      cv.height = h;
    }
    gl.viewport(0, 0, w, h);
    gl.depthMask(true);
    gl.enable(gl.DEPTH_TEST);
    gl.disable(gl.CULL_FACE);
    gl.disable(gl.BLEND);
    if (theme === "light") gl.clearColor(0.84, 0.88, 0.92, 1);
    else gl.clearColor(0.095, 0.11, 0.138, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    const cam = camera(w / h);
    lastFrame = { ...cam, cssW: r.width, cssH: r.height };
    drawLines(
      bedBuffer,
      bedVertCount,
      cam.mvp,
      theme === "light" ? [0.35, 0.45, 0.52, 0.45] : [0, 0.72, 0.62, 0.34],
    );
    const value = Number($("cut").value),
      b = cam.bounds,
      clipMode = value === 0 ? 0 : cutAxis === "y" ? 1 : 2,
      clipValue =
        cutAxis === "y"
          ? b.min[1] + b.size[1] * (1 - value / 100)
          : b.min[2] + b.size[2] * (1 - value / 100);
    const mat =
      MATERIAL_PRESETS[$("xray").checked ? "xray" : material] ||
      MATERIAL_PRESETS.emerald_silk;
    for (const m of meshes) {
      const model = partTransform(m.part, openingFraction(), m.preview_offset);
      gl.useProgram(program);
      gl.uniformMatrix4fv(
        gl.getUniformLocation(program, "u_mvp"),
        false,
        cam.mvp,
      );
      gl.uniformMatrix4fv(
        gl.getUniformLocation(program, "u_model"),
        false,
        model,
      );
      gl.uniform3fv(gl.getUniformLocation(program, "u_eye"), cam.eye);
      gl.uniform3fv(
        gl.getUniformLocation(program, "u_baseColor"),
        m.part === "lid" ? mat.saucer : mat.base,
      );
      gl.uniform3fv(
        gl.getUniformLocation(program, "u_saucerColor"),
        mat.saucer,
      );
      for (const [key, v] of Object.entries({
        u_roughness: mat.rough,
        u_metallic: mat.metal,
        u_heatmap: material === "heatmap" && !$("xray").checked ? 1 : 0,
        u_xrayMode: $("xray").checked ? 1 : 0,
        u_clipMode: clipMode,
        u_clipVal: clipValue,
        u_passMode: 0,
        u_lightTheme: theme === "light" ? 1 : 0,
      }))
        gl.uniform1f(gl.getUniformLocation(program, key), v);
      gl.bindVertexArray(m.vao);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.ib);
      if ($("xray").checked) {
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        gl.depthMask(false);
        gl.enable(gl.CULL_FACE);
        gl.cullFace(gl.FRONT);
        gl.drawElements(gl.TRIANGLES, m.count, gl.UNSIGNED_INT, 0);
        gl.cullFace(gl.BACK);
        gl.drawElements(gl.TRIANGLES, m.count, gl.UNSIGNED_INT, 0);
        gl.disable(gl.CULL_FACE);
        gl.depthMask(true);
        gl.disable(gl.BLEND);
      } else gl.drawElements(gl.TRIANGLES, m.count, gl.UNSIGNED_INT, 0);
      if (wire && clipMode === 0) {
        if (!m.wireBuffer) {
          const edges = new Uint32Array(m.indices.length * 2);
          for (let i = 0, k = 0; i < m.indices.length; i += 3) {
            const a = m.indices[i],
              b = m.indices[i + 1],
              c = m.indices[i + 2];
            for (const e of [a, b, b, c, c, a]) edges[k++] = e;
          }
          m.wireBuffer = gl.createBuffer();
          gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.wireBuffer);
          gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, edges, gl.STATIC_DRAW);
          m.wireCount = edges.length;
        }
        gl.useProgram(lineProg);
        gl.uniformMatrix4fv(
          gl.getUniformLocation(lineProg, "u_mvp"),
          false,
          mult(cam.mvp, model),
        );
        gl.uniform4fv(
          gl.getUniformLocation(lineProg, "u_color"),
          [0, 0, 0, 0.32],
        );
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.wireBuffer);
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        gl.drawElements(gl.LINES, m.wireCount, gl.UNSIGNED_INT, 0);
        gl.disable(gl.BLEND);
      }
    }
    updateHud(sceneBounds());
    renderCalipers();
  }
  function projectWorldToScreen(wx, wy, wz, mvp, cssW, cssH) {
    const cx = mvp[0] * wx + mvp[4] * wy + mvp[8] * wz + mvp[12];
    const cy = mvp[1] * wx + mvp[5] * wy + mvp[9] * wz + mvp[13];
    const cz = mvp[2] * wx + mvp[6] * wy + mvp[10] * wz + mvp[14];
    const cw = mvp[3] * wx + mvp[7] * wy + mvp[11] * wz + mvp[15];
    if (cw <= 0.1) return null;
    const ndcX = cx / cw;
    const ndcY = cy / cw;
    return {
      x: (ndcX * 0.5 + 0.5) * cssW,
      y: (0.5 - ndcY * 0.5) * cssH,
      ndcZ: cz / cw,
    };
  }

  function drawCadArrowHead(ctx, tipX, tipY, dirX, dirY, len) {
    const nx = -dirY;
    const ny = dirX;
    const w = len * 0.44;
    ctx.beginPath();
    ctx.moveTo(tipX, tipY);
    ctx.lineTo(tipX - dirX * len + nx * w, tipY - dirY * len + ny * w);
    ctx.lineTo(tipX - dirX * len - nx * w, tipY - dirY * len - ny * w);
    ctx.closePath();
    ctx.fill();
  }

  function drawCadDoubleArrow(ctx, x1, y1, x2, y2, color, dashed) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const dist = Math.hypot(dx, dy);
    if (dist < 4.0) return;
    const ux = dx / dist;
    const uy = dy / dist;
    const arrowLen = Math.min(7.5, dist * 0.28);

    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 1.65;
    if (dashed) ctx.setLineDash([4, 3]);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.setLineDash([]);
    drawCadArrowHead(ctx, x1, y1, -ux, -uy, arrowLen);
    drawCadArrowHead(ctx, x2, y2, ux, uy, arrowLen);
    ctx.restore();
  }

  function drawCadPill(
    ctx,
    cx,
    cy,
    text,
    borderColor,
    cssW,
    cssH,
    placedBoxes,
  ) {
    ctx.save();
    ctx.font = "700 10.8px 'Cascadia Code', Consolas, 'Segoe UI', monospace";
    const padX = 7;
    const boxH = 20;
    const tw = ctx.measureText(text).width;
    const boxW = tw + padX * 2;

    let x = Math.max(10, Math.min(cssW - boxW - 10, cx - boxW * 0.5));
    let y = Math.max(44, Math.min(cssH - boxH - 46, cy - boxH * 0.5));

    // Gentle vertical collision avoidance so pills never overlap each other
    if (Array.isArray(placedBoxes)) {
      for (let pass = 0; pass < 4; pass++) {
        let hit = false;
        for (let k = 0; k < placedBoxes.length; k++) {
          const b = placedBoxes[k];
          const overlapX = x < b.x + b.w + 4 && x + boxW + 4 > b.x;
          const overlapY = y < b.y + b.h + 3 && y + boxH + 3 > b.y;
          if (overlapX && overlapY) {
            y =
              y >= b.y
                ? Math.min(cssH - boxH - 46, b.y + b.h + 4)
                : Math.max(44, b.y - boxH - 4);
            hit = true;
          }
        }
        if (!hit) break;
      }
      placedBoxes.push({ x: x, y: y, w: boxW, h: boxH });
    }

    const r = 5;
    ctx.beginPath();
    if (typeof ctx.roundRect === "function") {
      ctx.roundRect(x, y, boxW, boxH, r);
    } else {
      ctx.rect(x, y, boxW, boxH);
    }
    ctx.fillStyle =
      theme === "light"
        ? "rgba(250, 252, 255, 0.94)"
        : "rgba(15, 18, 24, 0.90)";
    ctx.fill();
    ctx.lineWidth = 1.4;
    ctx.strokeStyle = borderColor;
    ctx.stroke();

    ctx.fillStyle = theme === "light" ? "#141a22" : "#f3f7fb";
    ctx.textBaseline = "middle";
    ctx.fillText(text, x + padX, y + boxH * 0.5 + 0.5);
    ctx.restore();
    return { cx: x + boxW * 0.5, cy: y + boxH * 0.5 };
  }

  function renderCalipers() {
    const cv = $("vp-caliper-canvas"),
      ctx = cv.getContext("2d"),
      r = cv.getBoundingClientRect(),
      dpr = Math.min(devicePixelRatio || 1, 2);
    cv.width = Math.max(1, r.width * dpr);
    cv.height = Math.max(1, r.height * dpr);
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, r.width, r.height);
    if (!calipers || !lastFrame || !meshes.length) return;
    const b = sceneBounds(),
      lo = b.min,
      hi = b.max,
      placed = [],
      color = theme === "light" ? "#007f74" : "#6cffe8";
    for (const [a, bpoint, text] of [
      [
        [lo[0], lo[1], lo[2]],
        [hi[0], lo[1], lo[2]],
        b.size[0].toFixed(2) + " mm",
      ],
      [
        [hi[0], lo[1], lo[2]],
        [hi[0], hi[1], lo[2]],
        b.size[1].toFixed(2) + " mm",
      ],
      [
        [lo[0], lo[1], lo[2]],
        [lo[0], lo[1], hi[2]],
        b.size[2].toFixed(2) + " mm",
      ],
    ]) {
      const aa = projectWorldToScreen(...a, lastFrame.mvp, r.width, r.height),
        bb = projectWorldToScreen(...bpoint, lastFrame.mvp, r.width, r.height);
      if (aa && bb) {
        drawCadDoubleArrow(ctx, aa.x, aa.y, bb.x, bb.y, color, false);
        drawCadPill(
          ctx,
          (aa.x + bb.x) / 2,
          (aa.y + bb.y) / 2,
          text,
          color,
          r.width,
          r.height,
          placed,
        );
      }
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
    zoom = Math.max(0.35, Math.min(4, zoom * Math.exp(-e.deltaY * 0.001)));
    render();
  };
  $("home").onclick = () => {
    zoom = 1;
    yaw = -0.75;
    pitch = 0.68;
    render();
  };
  $("open").oninput = () => {
    openingLabel();
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
    const extent = Number($("open").max) || 100;
    $("open").value = extent / 2 - (extent / 2) * Math.cos(t * 0.0007);
    openingLabel();
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
  Object.assign(texts.pt, {
    sec_presets: "Galeria de Modelos",
    btn_save_preset: "+ Salvar",
    cat_all: "Todos",
    cat_user: "Meus",
    shape: "Forma",
    features: "Recursos",
    manufacture: "Impressão",
    hud_title: "Inspeção da malha",
    hud_wall_floor: "Parede / Fundo",
    hud_mouth_hole: "Folga por lado",
    hud_dims: "Cena atual (mm)",
    hud_overhang: "Overhang da malha",
    hud_weight: "Volume sólido (cm³)",
    hud_Tris: "Triângulos",
    mat_emerald: "Seda Esmeralda Orca",
    mat_terracotta: "Cerâmica Terracota",
    mat_white: "Porcelana Branca Mate",
    mat_copper: "Bronze Cobre Escovado",
    mat_xray: "🔬 Raio-X / Parede (Translúcido)",
    mat_heatmap: "Mapa de Overhang (°)",
    vp_xray: "🔬 Raio-X / Parede",
    vp_calipers: "📏 Cotas mm",
    vp_heatmap: "🔥 Overhang",
    vp_wire: "⌗ Malha",
    cam_front: "Frente",
    cam_top: "Topo",
    cam_bottom: "Base",
    cam_fit: "Enquadrar",
    vp_cut_y: "✂ Corte Vertical (Perfil Y)",
    vp_cut_z: "💿 Fatia Horizontal Z",
    leg_outer: "Externa",
    leg_inner: "Cavidade & Fundo",
    btn_send_plater: "Enviar para a Mesa do OrcaSlicer",
    btn_exp_3mf: "Exportar .3MF",
    btn_exp_stl: "Exportar .STL",
    btn_surprise: "Surpreenda-me",
  });
  Object.assign(texts.en, {
    sec_presets: "Model Gallery",
    btn_save_preset: "+ Save",
    cat_all: "All",
    cat_user: "Mine",
    shape: "Shape",
    features: "Features",
    manufacture: "Print",
    hud_title: "Mesh inspection",
    hud_wall_floor: "Wall / Floor",
    hud_mouth_hole: "Clearance per side",
    hud_dims: "Current scene (mm)",
    hud_overhang: "Mesh overhang",
    hud_weight: "Solid volume (cm³)",
    hud_Tris: "Triangles",
    mat_emerald: "Orca Emerald Silk",
    mat_terracotta: "Terracotta Ceramic",
    mat_white: "Matte White Porcelain",
    mat_copper: "Brushed Copper Bronze",
    mat_xray: "🔬 X-Ray / Wall (Translucent)",
    mat_heatmap: "Overhang Map (°)",
    vp_xray: "🔬 X-Ray / Wall",
    vp_calipers: "📏 Calipers mm",
    vp_heatmap: "🔥 Overhang",
    vp_wire: "⌗ Mesh",
    cam_front: "Front",
    cam_top: "Top",
    cam_bottom: "Bottom",
    cam_fit: "Fit",
    vp_cut_y: "✂ Vertical Cut Y",
    vp_cut_z: "💿 Horizontal Slice Z",
    leg_outer: "Outer",
    leg_inner: "Cavity & Floor",
    btn_send_plater: "Send to OrcaSlicer Plater",
    btn_exp_3mf: "Export .3MF",
    btn_exp_stl: "Export .STL",
    btn_surprise: "Surprise me",
  });
  let presetFilter = "all",
    activePreset = null;
  function presetSignature(params) {
    const ignored = new Set([
      "name",
      "lang",
      "theme",
      "export_target",
      "auto_configure_slicer",
    ]);
    return JSON.stringify(
      Object.fromEntries(
        Object.keys(params)
          .filter((k) => !ignored.has(k))
          .sort()
          .map((k) => [k, params[k]]),
      ),
    );
  }
  function syncPresetSelection() {
    const all = [...(INITIAL.user_presets || []), ...(INITIAL.presets || [])];
    const selected = all.find((item) => item.id === activePreset);
    const signature = presetSignature(p);
    if (!selected || presetSignature(selected.params) !== signature)
      activePreset =
        all.find((item) => presetSignature(item.params) === signature)?.id ||
        null;
    presets();
  }
  function presetThumb(params) {
    if (params.style === "clamshell_pip") {
      const shell = (x, y) =>
        `<path d="M${x} ${y}l16 -8h44l-16 8Z" fill="#00a896" fill-opacity=".55" stroke="#80ffea"/><path d="M${x} ${y}v14h44v-14M${x + 44} ${y}l16 -8v14l-16 8" fill="#00796b" fill-opacity=".45" stroke="#55cfbb"/>`;
      return `<svg viewBox="0 0 124 92" fill="none" aria-hidden="true">${shell(43, 24)}<path d="M37 44l17 -8M65 44l17 -8" stroke="#ffcf77" stroke-width="3"/>${shell(12, 51)}</svg>`;
    }

    const w = params.width_x || 90,
      d = params.depth_y || 65,
      h = params.height_z || 35,
      sx = Math.min(52 / w, 34 / d, 38 / h),
      ww = w * sx,
      dd = d * sx * 0.48,
      hh = h * sx,
      ox = 62 - ww / 2,
      oy = 70 - hh;
    const lid = ["open_bin", "stackable_bin"].includes(params.style)
      ? ""
      : `<path d="M${ox} ${oy - 8}l${dd} ${-dd * 0.5} ${ww} 0 ${-dd} ${dd * 0.5}Z" fill="#26363e" stroke="#ffcf77"/>`;
    const accessWidth = Math.min(
      ww * 0.85,
      (params.front_access_width || w * 0.6) * sx,
    );
    const accessDrop = Math.min(
      hh * 0.8,
      (params.front_access_drop || h * 0.35) * sx,
    );
    const details =
      params.style === "stackable_bin"
        ? `<path d="M${ox + (ww - accessWidth) / 2} ${oy - 1}v${accessDrop}h${accessWidth}v${-accessDrop}Z" fill="#172126" stroke="#80ffea"/><path d="M${ox + 2} ${oy + hh - 2}h${ww - 4}" stroke="#80ffea"/>`
        : params.style === "open_bin" && params.handles_enabled
          ? params.handle_faces === "front_back"
            ? `<rect x="${ox + ww * 0.28}" y="${oy + hh * 0.3}" width="${ww * 0.44}" height="5" rx="2.5" fill="#172126" stroke="#80ffea"/>`
            : `<path d="M${ox + ww + dd * 0.2} ${oy + hh * 0.25 - dd * 0.1}l${dd * 0.6} ${-dd * 0.3}v5l${-dd * 0.6} ${dd * 0.3}Z" fill="#172126" stroke="#80ffea"/>`
          : params.style === "snap_latch"
            ? [0.2, 0.7]
                .map(
                  (x) =>
                    `<rect x="${ox + ww * x}" y="${oy - 5}" width="${ww * 0.1}" height="12" rx="1" fill="#ffb74d" stroke="#ffe0a3"/>`,
                )
                .join("")
            : "";
    return `<svg viewBox="0 0 124 92" fill="none" aria-hidden="true"><path d="M${ox} ${oy}l${dd} ${-dd * 0.5} ${ww} 0 ${-dd} ${dd * 0.5}Z" fill="#00a896" fill-opacity=".6" stroke="#80ffea"/><path d="M${ox} ${oy}v${hh}h${ww}v${-hh}M${ox + ww} ${oy}l${dd} ${-dd * 0.5}v${hh}l${-dd} ${dd * 0.5}" fill="#00796b" fill-opacity=".4" stroke="#55cfbb"/>${lid}${details}</svg>`;
  }
  function presets() {
    const grid = $("presets");
    grid.replaceChildren();
    const combined = [
      ...(INITIAL.user_presets || []).map((x) => ({ ...x, user: true })),
      ...(INITIAL.presets || []),
    ];
    for (const item of combined) {
      if (presetFilter === "user" && !item.user) continue;
      if (
        !["all", "user"].includes(presetFilter) &&
        item.params.style !== presetFilter
      )
        continue;
      const card = document.createElement("div");
      card.className =
        "preset-card" + (activePreset === item.id ? " active" : "");
      card.dataset.presetId = item.id;
      card.tabIndex = 0;
      card.setAttribute("role", "button");
      card.innerHTML =
        '<div class="preset-thumb">' +
        presetThumb(item.params) +
        '</div><div class="preset-meta"><div class="preset-name"></div><div class="preset-sub"></div></div>';
      card.querySelector(".preset-name").textContent = item.user
        ? item.name
        : lang === "pt"
          ? item.name_pt
          : item.name_en;
      card.querySelector(".preset-sub").textContent =
        `${item.params.width_x}×${item.params.depth_y}×${item.params.height_z} mm`;
      const apply = () => {
        activePreset = item.id;
        setDesign(item.params);
        presets();
      };
      card.onclick = apply;
      card.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          apply();
        }
      };
      if (item.user) {
        const del = document.createElement("button");
        del.className = "preset-del-btn";
        del.textContent = "×";
        del.title = tr("delete");
        del.onclick = (e) => {
          e.stopPropagation();
          send({ type: "delete_preset", preset_id: item.id });
        };
        card.append(del);
      }
      grid.append(card);
    }
  }
  function updatePrinter() {
    const h = currentPrinter();
    $("printer").textContent = h.printer_name || "OrcaSlicer";
    $("printer-pill-specs").textContent =
      `· ${h.bed_x}×${h.bed_y}×${h.max_z} mm · ${h.nozzle_mm}mm`;
    $("sync").classList.remove("syncing");
    if (gl && program) rebuildBedGeometry();
    render();
  }
  document.querySelectorAll("[data-cat]").forEach(
    (button) =>
      (button.onclick = () => {
        presetFilter = button.dataset.cat;
        document
          .querySelectorAll("[data-cat]")
          .forEach((x) => x.classList.toggle("active", x === button));
        presets();
      }),
  );
  $("btn-toggle-save-preset").onclick = () =>
    $("save-preset-bar").classList.toggle("open");
  $("savePreset").onclick = () =>
    send({
      type: "save_preset",
      params: p,
      name: $("inp-save-preset-name").value.trim() || p.name,
    });
  $("btn-randomize").onclick = () => {
    const bytes = new Uint32Array(1);
    if (window.crypto?.getRandomValues) window.crypto.getRandomValues(bytes);
    else bytes[0] = Date.now() >>> 0;
    status(tr("generating"));
    if (!send({ type: "randomize", seed: bytes[0], params: clone(p) }))
      status(tr("noHost"));
  };
  $("sync").onclick = () => {
    $("sync").classList.add("syncing");
    send({ type: "sync_printer" });
    setTimeout(() => $("sync").classList.remove("syncing"), 1200);
  };
  document.querySelectorAll("[data-tab]").forEach(
    (button) =>
      (button.onclick = () => {
        document.body.dataset.dockTab = button.dataset.tab;
        document
          .querySelectorAll("[data-tab]")
          .forEach((x) => x.classList.toggle("active", x === button));
        drawPlan();
        render();
      }),
  );
  document.querySelectorAll("[data-param-range]").forEach((range) => {
    let gesture = false;
    range.onpointerdown = () => {
      snapshot();
      gesture = true;
    };
    range.oninput = () => {
      requestPreview(false);
      if (!gesture) {
        snapshot();
        gesture = true;
      }
      p[range.dataset.paramRange] = Number(range.value);
      document.querySelector(
        '[data-p="' + range.dataset.paramRange + '"]',
      ).value = range.value;
      drawPlan();
    };
    range.onchange = () => {
      if (!gesture) snapshot();
      gesture = false;
      sync();
      requestPreview();
    };
  });
  document
    .querySelectorAll("[data-wall-preset]")
    .forEach(
      (button) =>
        (button.onclick = () =>
          change("wall_thickness", Number(button.dataset.wallPreset))),
    );
  document.querySelectorAll("[data-action]").forEach(
    (button) =>
      (button.onclick = () => {
        const a = button.dataset.action;
        if (a === "open_folder") send({ type: "open_exports_folder" });
        else
          manufacture(
            a === "send_to_plater" ? a : "export_file",
            a === "export_stl" ? "stl" : "3mf",
          );
      }),
  );
  function viewButtons() {
    for (const [id, on] of [
      ["xray", $("xray").checked],
      ["btn-vp-calipers", calipers],
      ["btn-vp-wire", wire],
      ["btn-vp-spin", spin],
      ["btn-vp-heatmap", material === "heatmap"],
    ])
      $(id).classList.toggle("active", !!on);
    $("xray-legend").classList.toggle("visible", !!$("xray").checked);
    $("heatmap-legend").classList.toggle(
      "visible",
      material === "heatmap" && !$("xray").checked,
    );
  }
  $("xray").onclick = () => {
    $("xray").checked = !$("xray").checked;
    viewButtons();
    render();
  };
  $("btn-vp-calipers").onclick = () => {
    calipers = !calipers;
    viewButtons();
    render();
  };
  $("btn-vp-wire").onclick = () => {
    wire = !wire;
    viewButtons();
    render();
  };
  $("sel-material").onchange = () => {
    const choice = $("sel-material").value;
    $("xray").checked = choice === "xray";
    if (choice !== "xray") material = choice;
    viewButtons();
    render();
  };
  $("btn-vp-heatmap").onclick = () => {
    material = material === "heatmap" ? "emerald_silk" : "heatmap";
    $("xray").checked = false;
    $("sel-material").value = material;
    viewButtons();
    render();
  };
  document.querySelectorAll("[data-cam]").forEach(
    (button) =>
      (button.onclick = () => {
        zoom = 1;
        switch (button.dataset.cam) {
          case "front":
            yaw = -Math.PI / 2;
            pitch = 0.02;
            break;
          case "top":
            yaw = -Math.PI / 2;
            pitch = Math.PI / 2 - 0.0001;
            break;
          case "bottom":
            yaw = -Math.PI / 2;
            pitch = -Math.PI / 2 + 0.0001;
            break;
          case "iso":
            yaw = -0.75;
            pitch = 0.68;
            break;
        }
        render();
      }),
  );
  $("btn-cut-mode-y").onclick = () => {
    cutAxis = "y";
    $("btn-cut-mode-y").classList.add("active");
    $("btn-cut-mode-z").classList.remove("active");
    render();
  };
  $("btn-cut-mode-z").onclick = () => {
    cutAxis = "z";
    $("btn-cut-mode-z").classList.add("active");
    $("btn-cut-mode-y").classList.remove("active");
    render();
  };
  $("cut").oninput = () => {
    $("lbl-cross-cut").textContent =
      $("cut").value === "0" ? "Off" : $("cut").value + "%";
    render();
  };
  $("btn-cut-half").onclick = () => {
    $("cut").value = 50;
    $("cut").oninput();
  };
  $("btn-cut-off").onclick = () => {
    $("cut").value = 0;
    $("cut").oninput();
  };
  let scheduledAnimation = 0,
    lastAnimationTime = 0;
  function animate(t) {
    scheduledAnimation = 0;
    if (document.hidden) {
      playing = false;
      spin = false;
      return;
    }
    const dt = lastAnimationTime ? Math.min(t - lastAnimationTime, 50) : 16;
    lastAnimationTime = t;
    if (playing) {
      const extent = Number($("open").max) || 100;
      $("open").value = extent / 2 - (extent / 2) * Math.cos(t * 0.0007);
      openingLabel();
    }
    if (spin) yaw += dt * 0.00025;
    render();
    if (playing || spin) scheduledAnimation = requestAnimationFrame(animate);
  }
  function scheduleAnimation() {
    if (!scheduledAnimation)
      scheduledAnimation = requestAnimationFrame(animate);
  }
  $("play").onclick = () => {
    playing = !playing;
    $("play").textContent = playing ? "Ⅱ" : "▶";
    scheduleAnimation();
  };
  $("btn-vp-spin").onclick = () => {
    spin = !spin;
    viewButtons();
    scheduleAnimation();
  };
  window.OrcaBoxStudio = {
    handleHostMessage: receive,
    getState: () => clone(p),
    getSceneBounds: sceneBounds,
    fitCamera: () => {
      zoom = 1;
      render();
      return lastFrame
        ? {
            distance: lastFrame.distance,
            target: lastFrame.target,
            bounds: lastFrame.bounds,
          }
        : null;
    },
  };
  updatePrinter();
  viewButtons();

  if (INITIAL.mode === "dock") {
    document.body.dataset.mode = "dock";
    document.body.dataset.dockTab = "shape";
  }
  if (hostThemeExplicit === false) {
    const injectedTheme = detectInjectedOrcaTheme();
    if (injectedTheme) theme = injectedTheme;
  }
  configureOpening();
  try {
    initializeGL();
  } catch (e) {
    status(String(e), true);
  }
  translate();
  sync();
  if (INITIAL.host) updatePrinter();
  if (INITIAL.meshes) loadMeshes(INITIAL.meshes);
  else requestPreview();
  watchHostTheme();
})();
</script>
  </body>
</html>
"""


def get_studio_html(
    mode: str = "page", initial_context: dict[str, Any] | None = None
) -> str:
    ctx = copy.deepcopy(initial_context) if isinstance(initial_context, dict) else {}
    ctx["params"] = normalize_params(ctx.get("params"))
    ctx.setdefault("presets", BUILTIN_PRESETS)
    ctx["mode"] = "dock" if str(mode).strip().lower() == "dock" else "page"
    lang = (
        "en"
        if str(ctx.get("lang") or ctx["params"].get("lang", "pt"))
        .lower()
        .startswith("en")
        else "pt"
    )
    theme = (
        "light"
        if str(ctx.get("theme") or ctx["params"].get("theme", "dark")).lower()
        == "light"
        else "dark"
    )
    ctx.update(lang=lang, theme=theme)
    payload = (
        json.dumps(ctx, ensure_ascii=False, separators=(",", ":"))
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return (
        _BOX_HTML.replace("__INITIAL_LANG__", lang)
        .replace("__INITIAL_THEME__", theme)
        .replace("__INITIAL_MODE__", ctx["mode"])
        .replace("__BOX_CONTEXT__", payload)
    )

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
from collections import OrderedDict
import copy, ctypes, json, locale, os, re, sys, threading, time, types, base64, hashlib
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
        self._mesh_cache = OrderedDict()
        self._mesh_cache_bytes = 0
        self._mesh_cache_limit = 128 * 1024 * 1024
        self._encoded_cache = OrderedDict()
        self._encoded_cache_bytes = 0
        self._encoded_cache_limit = 48 * 1024 * 1024
        self._inflight_geometry = {}
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
            "version": "1.2.2",
        }

    @staticmethod
    def _geometry_key(p):
        """Presentation preferences do not change a manufacturing surface."""
        return json.dumps(
            {
                k: v
                for k, v in p.items()
                if k
                not in (
                    "name",
                    "lang",
                    "theme",
                    "export_target",
                    "auto_configure_slicer",
                )
            },
            sort_keys=True,
        )

    @staticmethod
    def _mesh_bytes(value):
        if isinstance(value, list):
            return sum(BoxStudioController._mesh_bytes(mesh) for _, mesh in value)
        return sum(
            array.nbytes
            for array in (value.vertices, value.triangles, value.face_normals)
        )

    @staticmethod
    def _validate_mesh(mesh, name):
        report = topology_report(mesh)
        if not report["closed"] or not report["oriented"]:
            raise ValueError(
                f"{name}: invalid surface topology; choose fine quality or adjust geometry."
            )
        return mesh

    def _cached_geometry(self, key, compute):
        """Byte-bounded LRU with one in-flight computation per immutable key.

        Collection entries conservatively count their arrays again, even when
        shared with a canonical part. The budget therefore bounds retained memory.
        """
        with self._lock:
            if key in self._mesh_cache:
                value, size = self._mesh_cache.pop(key)
                self._mesh_cache[key] = (value, size)
                return value
            slot = self._inflight_geometry.get(key)
            owner = slot is None
            if owner:
                slot = {"ready": threading.Event()}
                self._inflight_geometry[key] = slot
        if not owner:
            slot["ready"].wait()
            if "error" in slot:
                raise slot["error"]
            return slot["result"]
        try:
            result = compute()
            size = self._mesh_bytes(result)
            with self._lock:
                if size <= self._mesh_cache_limit:
                    self._mesh_cache[key] = (result, size)
                    self._mesh_cache_bytes += size
                    while self._mesh_cache_bytes > self._mesh_cache_limit:
                        _, (_, removed_size) = self._mesh_cache.popitem(last=False)
                        self._mesh_cache_bytes -= removed_size
                slot["result"] = result
            return result
        except Exception as exc:
            slot["error"] = exc
            raise
        finally:
            with self._lock:
                self._inflight_geometry.pop(key, None)
                slot["ready"].set()

    def _geometry(self, p, assembled=True, target="full_suite"):
        shape_key = self._geometry_key(p)

        def factory(raw, part, print_orientation=False):
            mesh = self._cached_geometry(
                ("part", shape_key, part),
                lambda: self._validate_mesh(generate_box_mesh(raw, part, False), part),
            )
            return orient_mesh_for_print(mesh, raw, part) if print_orientation else mesh

        def collect():
            items = collect_target_meshes(
                p,
                target=target,
                lang=p["lang"],
                assembled=assembled,
                mesh_factory=factory,
            )
            # The kit uses its own manufacturing primitives, outside the factory.
            if target == "fit_test_kit":
                for name, mesh in items:
                    self._validate_mesh(mesh, name)
            return items

        if assembled or target == "fit_test_kit":
            return self._cached_geometry(
                ("collection", shape_key, target, p["lang"]), collect
            )
        return collect()

    def _preview_payload(self, p):
        target = p["export_target"]
        items = self._geometry(p, assembled=True, target=target)
        latch_motion = None
        if p["style"] == "snap_latch":
            pass  # [bundled] resolved intra-package import

            latch_motion = {
                part: latch_geometry(p, part) for part in ("clip_left", "clip_right")
            }
        calibration = target == "fit_test_kit"
        offsets = [[0.0, 0.0, 0.0] for _ in items]
        if calibration:
            cursor = 0.0
            for index, (_, mesh) in enumerate(items):
                lower, upper = mesh.bounds_mm["min"], mesh.bounds_mm["max"]
                offsets[index] = [
                    cursor - lower[0],
                    -(lower[1] + upper[1]) / 2,
                    -lower[2],
                ]
                cursor += upper[0] - lower[0] + 6.0
            center = (cursor - 6.0) / 2
            for offset in offsets:
                offset[0] -= center
        encoded_key = (self._geometry_key(p), target, p["lang"])
        with self._lock:
            entry = self._encoded_cache.pop(encoded_key, None)
            if entry is not None:
                self._encoded_cache[encoded_key] = entry
        if entry is not None:
            encoded = entry[0]
        else:
            encoded = []
            for (name, mesh), offset in zip(items, offsets):
                encoded.append(
                    {
                        "name": name,
                        "part": mesh.part,
                        "preview_offset": offset,
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
            size = sum(
                len(item["vertices"]) + len(item["triangles"]) for item in encoded
            )
            with self._lock:
                previous = self._encoded_cache.pop(encoded_key, None)
                if previous is not None:
                    self._encoded_cache_bytes -= previous[1]
                if size <= self._encoded_cache_limit:
                    self._encoded_cache[encoded_key] = (encoded, size)
                    self._encoded_cache_bytes += size
                    while self._encoded_cache_bytes > self._encoded_cache_limit:
                        _, (_, removed_size) = self._encoded_cache.popitem(last=False)
                        self._encoded_cache_bytes -= removed_size
        return {
            "type": "preview_result",
            "ok": True,
            "params": p,
            "preview_mode": "calibration" if calibration else "assembly",
            "print_bounds": clamshell_print_bounds(p)
            if p["style"] == "clamshell_pip"
            else None,
            "geometry_key": hashlib.sha256(
                (self._geometry_key(p) + "|" + target).encode("utf-8")
            ).hexdigest(),
            "meshes": encoded,
            "hinge": hinge_geometry(p),
            "latch_motion": latch_motion,
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
        msg = None
        try:
            msg = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            if not isinstance(msg, dict):
                raise ValueError("Invalid plugin message.")
            self._subscriptions[default_mode] = send_fn
            action = msg.get("type", "")
            if action == "randomize":
                previous = normalize_params(msg.get("params") or self.current_params())
                candidate = generate_random_printable_params(
                    previous, msg.get("seed"), self.read_host_context()
                )
                self.set_current_params(candidate)
                for mode, post in list(self._subscriptions.items()):
                    if mode != default_mode:
                        try:
                            post({"type": "design_changed", "params": candidate})
                        except Exception:
                            pass
                send_fn(
                    {
                        "type": "randomize_result",
                        "ok": True,
                        "params": candidate,
                        "seed": msg.get("seed"),
                    }
                )
                return
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
            if isinstance(msg, dict) and msg.get("type") in ("preview", "update_params"):
                send_fn(
                    {
                        "type": "preview_result",
                        "ok": False,
                        "request_id": msg.get("request_id"),
                        "message": str(exc),
                    }
                )
                return
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
