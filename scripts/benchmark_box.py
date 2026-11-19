"""Measure cold preview, print orientation and warm preview without native Orca IPC.

Run with Python 3.12+ and NumPy. Results describe this machine and configuration,
not guaranteed generation times. No plugin installation or files are exported.
"""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
import sys
import tempfile
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--styles", nargs="+", default=["lip_snap", "open_bin", "snap_latch"])
    parser.add_argument("--sizes", nargs="+", default=["90x65x35", "160x95x35"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    from box_studio import plugin_main
    from box_studio.schema import VALID_STYLES, normalize_params, validate_params
    from box_studio.mesh_generator import np

    if any(style not in VALID_STYLES for style in args.styles):
        parser.error("A requested style is unavailable in this checkout.")
    report = {"python": platform.python_version(), "numpy": np.__version__,
              "system": platform.system(), "native_application_test": False, "cases": []}
    with tempfile.TemporaryDirectory(prefix="orca-box-benchmark-") as folder:
        plugin_main._resolve_storage_dir = lambda: Path(folder)
        for size in args.sizes:
            try:
                dimensions = tuple(float(value) for value in size.lower().split("x"))
                if len(dimensions) != 3:
                    raise ValueError()
            except ValueError:
                parser.error("Use sizes such as 160x95x35 (millimeters).")
            for style in args.styles:
                p = normalize_params(dict(zip(("width_x", "depth_y", "height_z"), dimensions)) | {"style": style})
                errors = validate_params(p)
                if errors:
                    raise ValueError("; ".join(errors))
                controller = plugin_main.BoxStudioController()
                started = perf_counter()
                payload = controller._preview_payload(p)
                cold = perf_counter() - started
                started = perf_counter()
                printable = controller._geometry(p, assembled=False, target=p["export_target"])
                export = perf_counter() - started
                started = perf_counter()
                controller._preview_payload(p)
                warm = perf_counter() - started
                case = {"style": style, "size_mm": list(dimensions),
                        "cold_preview_s": round(cold, 6), "print_geometry_s": round(export, 6),
                        "warm_preview_after_export_s": round(warm, 6),
                        "payload_mb": round(len(json.dumps(payload).encode("utf-8")) / 1_000_000, 3),
                        "pieces": [mesh.part for _, mesh in printable],
                        "vertices": sum(len(mesh.vertices) for _, mesh in printable),
                        "triangles": sum(len(mesh.triangles) for _, mesh in printable)}
                report["cases"].append(case)
                print(json.dumps(case, ensure_ascii=False), flush=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
