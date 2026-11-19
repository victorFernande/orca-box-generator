"""Seventeen editable starting designs and atomic user-preset persistence."""

from __future__ import annotations
import copy, json, os, re, tempfile
from pathlib import Path
from typing import Any
from .schema import normalize_params, validate_params


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
        "Estojo articulado · baixo",
        "PIP clamshell · shallow",
        style="clamshell_pip",
        width_x=120,
        depth_y=65,
        height_z=14,
        pip_clearance=0.3,
        hinge_separation=5,
        hinge_pin_diameter=3,
    ),
    _preset(
        "clamshell_pip_deep",
        "Estojo articulado · profundo",
        "PIP clamshell · deep",
        style="clamshell_pip",
        width_x=90,
        depth_y=65,
        height_z=25,
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
            from .mesh_generator import clamshell_print_bounds

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
