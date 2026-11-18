"""Validated, JSON-compatible parameters for Orca Box Studio (millimetres)."""

from __future__ import annotations
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
