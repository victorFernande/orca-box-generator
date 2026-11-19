"""Measure retained caches in an isolated Python process; never opens OrcaSlicer."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def process_memory():
    if os.name != "nt":
        # The reproducible cache byte counts below work on every platform.
        return {"process_memory_measured": False}
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                "PagefileUsage", "PeakPagefileUsage", "PrivateUsage",
            )
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {"working_set_bytes": counters.WorkingSetSize,
            "private_bytes": counters.PrivateUsage,
            "peak_working_set_bytes": counters.PeakWorkingSetSize}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from box_studio import plugin_main as bridge
    from box_studio import rugged_latch_geometry as latch
    from box_studio import rugged_front_mesh as front
    from box_studio.presets_catalog import BUILTIN_PRESETS

    package = ROOT / "src/box_studio"
    files = sorted(package.glob("*.py")) + sorted((package / "preset_meshes").glob("*.npz"))
    report = {"isolated_python_process_only": True, "runtime_representation": "source_package_in_fresh_process",
              "browser_gpu_rss_measured": False,
              "source_hashes": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
              "before": process_memory(), "rows": []}
    with tempfile.TemporaryDirectory(prefix="orca-box-memory-") as directory:
        bridge._resolve_storage_dir = lambda: Path(directory)
        controller = bridge.BoxStudioController()
        for tour in range(1, 4):
            for item in BUILTIN_PRESETS:
                payload = controller._preview_payload(item["params"])
                assert payload["ok"]
                del payload
                gc.collect()
                report["rows"].append({"round": tour, "id": item["id"],
                    "mesh_bytes": controller._mesh_cache_bytes,
                    "encoded_bytes": controller._encoded_cache_bytes, **process_memory()})
        # Exercise the extra local cache used when W/D/H only translate a latch.
        rugged = next(x["params"] for x in BUILTIN_PRESETS if x["id"] == "tool_rugged")
        edited = latch.generate_rugged_latch({**rugged, "width_x": rugged["width_x"] + 2}, "clip_left")
        del edited
        gc.collect()
        with latch._LATCH_CACHE_LOCK:
            retained = sum(sum(a.nbytes for a in (m.vertices, m.triangles, m.face_normals)) for m in latch._LATCH_CACHE.values())
            report["local_latch_cache"] = {"retained_bytes": retained, "limit_bytes": latch._LATCH_CACHE_BYTES,
                                           "entries": len(latch._LATCH_CACHE), "entry_limit": 2}
        for part in ("base", "lid"):
            edited_front = front.generate_front_patch({**rugged, "width_x": rugged["width_x"] + 2}, part, 48.25, 1)
            del edited_front
        gc.collect()
        with front._FRONT_PATCH_LOCK:
            front_retained = sum(front._front_patch_bytes(v) for v in front._FRONT_PATCH_CACHE.values())
            report["local_front_cache"] = {"retained_bytes": front_retained, "limit_bytes": front._FRONT_PATCH_CACHE_BYTES,
                                           "entries": len(front._FRONT_PATCH_CACHE)}
        report["cache_budget_bytes"] = {"controller_mesh": controller._mesh_cache_limit,
                                        "controller_encoded": controller._encoded_cache_limit,
                                        "local_latch": latch._LATCH_CACHE_BYTES,
                                        "local_front": front._FRONT_PATCH_CACHE_BYTES}
        report["after_local_translations"] = process_memory()
        assert front_retained <= front._FRONT_PATCH_CACHE_BYTES
        assert retained <= latch._LATCH_CACHE_BYTES
        assert controller._mesh_cache_bytes <= controller._mesh_cache_limit
        assert controller._encoded_cache_bytes <= controller._encoded_cache_limit
    report["prepared_compressed_bytes"] = sum(p.stat().st_size for p in (package / "preset_meshes").glob("*.npz"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"tours": 3, "selections": len(report["rows"]), "latch_cache": report["local_latch_cache"]}))


if __name__ == "__main__":
    main()
