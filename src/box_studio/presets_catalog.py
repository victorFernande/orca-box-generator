"""Twelve editable starting designs and atomic user-preset persistence."""

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
