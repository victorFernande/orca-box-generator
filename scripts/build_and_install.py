#!/usr/bin/env python3
"""Single-file PEP 723 bundler and local installer for Orca Box Studio.

Compiles all modules under `src/box_studio/` into a self-contained single-file
OrcaSlicer 2.5.1+ plugin (`dist/orca_box_generator.py`) and deploys ONLY
`orca_box_generator.py` + `icon.svg` into:
`%APPDATA%\\OrcaSlicer\\orca_plugins\\orca_box_generator\\`
"""

from __future__ import annotations

import argparse
import ast
import base64
import importlib.util
import json
import csv
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
import tomllib
import zipfile
import zlib
from pathlib import Path

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PKG_DIR = PROJECT_ROOT / "src" / "box_studio"
DIST_DIR = PROJECT_ROOT / "dist"
DIST_BUNDLE_PATH = DIST_DIR / "orca_box_generator.py"
DIST_ANY_BUNDLE_PATH = DIST_DIR / "orca_box_generator_any.py"
ICON_SRC_PATH = SRC_PKG_DIR / "icon.svg"

MODULE_ORDER: list[str] = [
    "language_packs.py",
    "locale_catalog.py",
    "schema.py",
    "mesh_generator.py",
    "rugged_geometry.py",
    "rugged_latch_geometry.py",
    "rugged_front_geometry.py",
    "rugged_front_mesh.py",
    "exporters.py",
    "presets_catalog.py",
    "preset_mesh_index.py",
    "preset_mesh_cache.py",
    "studio_ui.py",
    "linux_ipc.py",
    "plugin_main.py",
]

DEFAULT_PLUGIN_VERSION = "1.4.3"
PLUGIN_VERSION = (
    os.environ.get("ORCA_PLUGIN_VERSION", "").strip().lstrip("v")
    or DEFAULT_PLUGIN_VERSION
)
if not re.fullmatch(
    r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?(?:\.post\d+)?(?:\.dev\d+)?", PLUGIN_VERSION
):
    raise ValueError("ORCA_PLUGIN_VERSION must be a version such as 1.0.0 or 1.0.0rc1.")
DIST_WHEEL_PATH = DIST_DIR / f"orca_box_generator-{PLUGIN_VERSION}-py3-none-any.whl"

PEP723_HEADER = f"""\
# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=1.26"]
#
# [tool.orcaslicer.plugin]
# id = "orca-box-studio"
# name = "Orca Box Studio"
# description = "Offline parametric boxes, handgrip bins, removable latching lids and calibration parts"
# author = "Orca Box Studio"
# version = "{PLUGIN_VERSION}"
# ///
"""
PRESERVED_SIDE_FILES: frozenset[str] = frozenset(
    {
        "orca_box_generator.py",
        "icon.svg",
        ".install_state.json",
        "install_state.json",
    }
)


def get_orca_base_dir(platform_name: str | None = None) -> Path:
    """Resolve OrcaSlicer user directory across Windows (`win32`), macOS (`darwin`), and Linux."""
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


def get_install_dir(platform_name: str | None = None) -> Path:
    return get_orca_base_dir(platform_name) / "orca_plugins" / "orca_box_generator"


def extract_pep723_toml(source: str) -> dict:
    """Parse and validate PEP 723 `# /// script ... # ///` block using stdlib `tomllib`."""
    in_block = False
    toml_lines: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if not in_block:
            if stripped == "# /// script":
                in_block = True
            continue
        if stripped == "# ///":
            break
        if line.startswith("# "):
            toml_lines.append(line[2:])
        elif line.startswith("#"):
            toml_lines.append(line[1:])
        else:
            raise ValueError(
                f"Invalid non-comment line inside PEP 723 header: {line!r}"
            )
    else:
        raise ValueError("Missing closing `# ///` for PEP 723 script block.")

    return tomllib.loads("\n".join(toml_lines))


def _collect_top_level_private_defs(tree: ast.Module) -> tuple[set[str], set[str]]:
    """Return `(private_top_defs, class_attr_names)` for collision analysis."""
    privates: set[str] = set()
    class_attrs: set[str] = set()

    def _record_target(target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            nm = target.id
            if nm.startswith("_") and not (nm.startswith("__") and nm.endswith("__")):
                privates.add(nm)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                _record_target(elt)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nm = node.name
            if nm.startswith("_") and not (nm.startswith("__") and nm.endswith("__")):
                privates.add(nm)
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        class_attrs.add(sub.name)
                    elif isinstance(sub, ast.Assign):
                        for t in sub.targets:
                            if isinstance(t, ast.Name):
                                class_attrs.add(t.id)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                _record_target(t)
        elif isinstance(node, ast.AnnAssign) and node.target is not None:
            _record_target(node.target)

    return privates, class_attrs


def _rename_colliding_privates(source: str, mod_stem: str, to_rename: set[str]) -> str:
    """Token-safely prefix colliding module-private helper names without touching strings/JS."""
    if not to_rename:
        return source

    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    rewritten: list[tokenize.TokenInfo] = []
    prev_significant_str = ""

    for tok in tokens:
        if (
            tok.type == tokenize.NAME
            and tok.string in to_rename
            and prev_significant_str != "."
        ):
            tok = tok._replace(string=f"_{mod_stem}{tok.string}")
        rewritten.append(tok)
        if tok.type not in (
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.COMMENT,
        ):
            prev_significant_str = tok.string

    return tokenize.untokenize(rewritten)


def _strip_internal_imports(source: str) -> tuple[str, set[str]]:
    """Strip `from __future__` and intra-package `box_studio` imports via AST line spans."""
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    future_features: set[str] = set()

    replacements: list[tuple[int, int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod_name = node.module or ""
            is_future = node.level == 0 and mod_name == "__future__"
            is_internal = (
                node.level >= 1
                or mod_name == "box_studio"
                or mod_name.startswith("box_studio.")
            )

            if not (is_future or is_internal):
                continue

            start_line = node.lineno
            end_line = node.end_lineno or node.lineno
            first_line = lines[start_line - 1]
            indent_match = re.match(r"^[ \t]*", first_line)
            indent = indent_match.group(0) if indent_match else ""

            if is_future:
                for alias in node.names:
                    future_features.add(alias.name)
                repl = f"{indent}pass  # [bundled] hoisted __future__ import\n"
                replacements.append((start_line, end_line, repl))
                continue

            stmts: list[str] = []
            if node.level >= 1 and not mod_name:
                stmts.append(f"{indent}import sys as _orca_bundle_sys\n")
                for alias in node.names:
                    bound_name = alias.asname or alias.name
                    stmts.append(
                        f"{indent}{bound_name} = _orca_bundle_sys.modules[__name__]\n"
                    )
            else:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    if alias.asname and alias.asname != alias.name:
                        stmts.append(f"{indent}{alias.asname} = {alias.name}\n")
                if not stmts:
                    stmts.append(
                        f"{indent}pass  # [bundled] resolved intra-package import\n"
                    )

            replacements.append((start_line, end_line, "".join(stmts)))

        elif isinstance(node, ast.Import):
            internal_aliases = [
                a
                for a in node.names
                if a.name == "box_studio" or a.name.startswith("box_studio.")
            ]
            if not internal_aliases:
                continue
            start_line = node.lineno
            end_line = node.end_lineno or node.lineno
            first_line = lines[start_line - 1]
            indent_match = re.match(r"^[ \t]*", first_line)
            indent = indent_match.group(0) if indent_match else ""

            stmts = [f"{indent}import sys as _orca_bundle_sys\n"]
            for alias in node.names:
                if alias.name == "box_studio" or alias.name.startswith("box_studio."):
                    bound = alias.asname or alias.name.split(".")[0]
                    stmts.append(
                        f"{indent}{bound} = _orca_bundle_sys.modules[__name__]\n"
                    )
                else:
                    as_part = f" as {alias.asname}" if alias.asname else ""
                    stmts.append(f"{indent}import {alias.name}{as_part}\n")
            replacements.append((start_line, end_line, "".join(stmts)))

    replacements.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    applied_ranges: list[tuple[int, int]] = []
    for start_line, end_line, repl_text in replacements:
        if any(not (end_line < s or start_line > e) for s, e in applied_ranges):
            continue
        lines[start_line - 1 : end_line] = [repl_text]
        applied_ranges.append((start_line, end_line))

    return "".join(lines), future_features


PRESET_SOURCE_FILES = ("schema.py", "mesh_generator.py", "presets_catalog.py", "rugged_geometry.py", "rugged_latch_geometry.py", "rugged_front_geometry.py", "rugged_front_mesh.py")


def _preset_dependency_digest(parts: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name in PRESET_SOURCE_FILES:
        digest.update(name.encode("ascii") + b"\0")
        digest.update(parts[name].replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def _read_preset_resources() -> tuple[str, dict[str, bytes]]:
    """Reject missing, stale or corrupt package meshes before distribution."""
    tree = ast.parse((SRC_PKG_DIR / "preset_mesh_index.py").read_text(encoding="utf-8"))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            constants[node.targets[0].id] = ast.literal_eval(node.value)
    expected = constants.get("PRESET_MESH_SOURCE_HASH")
    actual = _preset_dependency_digest({n: (SRC_PKG_DIR / n).read_bytes() for n in PRESET_SOURCE_FILES})
    index = constants.get("PRESET_MESH_INDEX", {})
    if expected != actual or len(index) != 3:
        raise RuntimeError("Standard meshes are stale; run scripts/build_preset_meshes.py before packaging.")
    resources = {}
    for design in index.values():
        for entry in design["parts"].values():
            name = entry["file"]
            if not re.fullmatch(r"[a-z0-9_]+-[a-z0-9_]+\.npz", name):
                raise RuntimeError("Invalid standard-mesh resource name.")
            blob = (SRC_PKG_DIR / "preset_meshes" / name).read_bytes()
            if len(blob) != entry["size_bytes"] or hashlib.sha256(blob).hexdigest() != entry["sha256"]:
                raise RuntimeError(f"Standard mesh is corrupt: {name}")
            if name in resources and resources[name] != blob:
                raise RuntimeError(f"Conflicting shared standard-mesh resource: {name}")
            resources[name] = blob
    return actual, resources


def _read_language_resources() -> tuple[dict, dict[str, bytes]]:
    """Validate every catalog without importing the plugin or its host callbacks."""
    spec = importlib.util.spec_from_file_location(
        "_orca_box_language_pack_validator", SRC_PKG_DIR / "language_packs.py"
    )
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    folder = SRC_PKG_DIR / "locales"
    packs, _ = validator.read_language_pack_files(folder, strict=True)
    if "en" not in packs:
        raise ValueError("The language pack directory must contain the English fallback catalog.")
    resources = {path.name: path.read_bytes().replace(b"\r\n", b"\n")
                 for path in sorted(folder.glob("*.json"))}
    return packs, resources


def build_bundle() -> Path:
    """Compile all `src/box_studio/*.py` modules into `dist/orca_box_generator.py`."""
    missing = [m for m in MODULE_ORDER if not (SRC_PKG_DIR / m).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing required source module(s) in {SRC_PKG_DIR}: {missing}"
        )

    raw_sources: dict[str, str] = {}
    private_defs_by_mod: dict[str, set[str]] = {}
    class_attrs_by_mod: dict[str, set[str]] = {}
    def_counts: dict[str, int] = {}

    for mod_file in MODULE_ORDER:
        src = (SRC_PKG_DIR / mod_file).read_text(encoding="utf-8")
        raw_sources[mod_file] = src
        tree = ast.parse(src, filename=mod_file)
        privs, cls_attrs = _collect_top_level_private_defs(tree)
        private_defs_by_mod[mod_file] = privs
        class_attrs_by_mod[mod_file] = cls_attrs
        for nm in privs:
            def_counts[nm] = def_counts.get(nm, 0) + 1

    colliding_privates = {nm for nm, count in def_counts.items() if count > 1}

    preset_source_hash, preset_resources = _read_preset_resources()
    language_packs, _ = _read_language_resources()
    language_data = json.dumps(language_packs, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
    language_data = base64.b85encode(zlib.compress(language_data, 9))
    geometry_sections: dict[str, bytes] = {}
    all_future_features: set[str] = {"annotations"}
    sections: list[str] = []

    for mod_file in MODULE_ORDER:
        mod_stem = Path(mod_file).stem
        src = raw_sources[mod_file]
        if mod_file == "language_packs.py":
            marker = "_BUNDLED_LANGUAGE_PACKS = {}"
            if src.count(marker) != 1:
                raise ValueError("Language pack embedding marker must occur exactly once.")
            src = src.replace(marker, "_BUNDLED_LANGUAGE_PACKS = json.loads(zlib.decompress(base64.b85decode(" +
                              repr(language_data) + ")).decode('utf-8'))")
        if mod_file == "preset_mesh_cache.py":
            src = src.replace("_BUNDLED_PRESET_DATA = {}", "_BUNDLED_PRESET_DATA = " + repr(
                {name: base64.b64encode(data).decode("ascii") for name, data in preset_resources.items()}))
            src = src.replace('_BUNDLED_PRESET_RAW_HASH = ""', '_BUNDLED_PRESET_RAW_HASH = ' + repr(preset_source_hash))
            src = src.replace('_BUNDLED_PRESET_CODE_HASH = ""', '_BUNDLED_PRESET_CODE_HASH = ' + repr(
                _preset_dependency_digest(geometry_sections)))
        rename_set = (
            private_defs_by_mod[mod_file] & colliding_privates
        ) - class_attrs_by_mod[mod_file]
        if rename_set:
            src = _rename_colliding_privates(src, mod_stem, rename_set)

        transformed, fut = _strip_internal_imports(src)
        all_future_features.update(fut)

        banner = f"\n# {'=' * 75}\n# MODULE: box_studio.{mod_stem}\n# {'=' * 75}\n\n"
        body = transformed.rstrip() + "\n"
        if mod_file in PRESET_SOURCE_FILES:
            geometry_sections[mod_file] = body.encode("utf-8")
            body = (f"# BOX_GEOMETRY_SOURCE_BEGIN {mod_file}\n" + body +
                    f"# BOX_GEOMETRY_SOURCE_END {mod_file}\n")
        sections.append(banner + body)

    future_stmt = f"from __future__ import {', '.join(sorted(all_future_features))}\n"
    module_bootstrap = (
        "import sys as _orca_init_sys\n"
        "import types as _orca_init_types\n"
        "if __name__ not in _orca_init_sys.modules:\n"
        "    _orca_init_sys.modules[__name__] = _orca_init_types.ModuleType(__name__)\n"
    )
    license_comments = (
        "\n".join(
            "#" + (" " + line if line else "")
            for line in (PROJECT_ROOT / "LICENSE")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        + "\n"
    )
    bundled_code = (
        PEP723_HEADER
        + "\n"
        + license_comments
        + future_stmt
        + "\n"
        + module_bootstrap
        + "".join(sections)
    )

    meta = extract_pep723_toml(bundled_code)
    plugin_meta = meta.get("tool", {}).get("orcaslicer", {}).get("plugin", {})
    if plugin_meta.get("id") != "orca-box-studio":
        raise RuntimeError(
            "The bundle must declare its own orca-box-studio identifier."
        )
    allowed_plugin_keys = {"id", "name", "description", "author", "version"}
    extra_keys = set(plugin_meta.keys()) - allowed_plugin_keys
    if extra_keys:
        raise RuntimeError(
            f"Non-canonical [tool.orcaslicer.plugin] keys found: {extra_keys}"
        )
    if not plugin_meta.get("name"):
        raise RuntimeError("PEP 723 header is missing [tool.orcaslicer.plugin].name")
    if not meta.get("dependencies"):
        raise RuntimeError("PEP 723 header is missing dependencies")

    if ICON_SRC_PATH.is_file():
        icon_disk = ICON_SRC_PATH.read_text(encoding="utf-8").strip()
        if icon_disk not in raw_sources["plugin_main.py"]:
            raise RuntimeError(
                "Embedded ICON_SVG_CONTENT in plugin_main.py is out of sync with src/box_studio/icon.svg"
            )

    compile(bundled_code, str(DIST_BUNDLE_PATH), "exec")

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    with open(DIST_BUNDLE_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(bundled_code)
    with open(DIST_ANY_BUNDLE_PATH, "w", encoding="utf-8", newline="\n") as fh_any:
        fh_any.write(bundled_code)

    return DIST_BUNDLE_PATH


def _record_digest_and_size(data: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(data).digest()
    b64 = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"sha256={b64}", str(len(data))


def build_wheel() -> Path:
    """Build a standards-compliant pure-Python universal wheel (`py3-none-any.whl`) in `dist/`
    for OrcaCloud / GitHub Releases (`OrcaSlicer.dll` `read_wheel_plugin_metadata` compatible,
    including `Name: Orca Box Studio`, `Import-Name: box_studio`, and `box_studio/icon.svg`).
    """
    pyproj = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    proj_tbl = pyproj.get("project", {})
    plugin_tbl = pyproj.get("tool", {}).get("orcaslicer", {}).get("plugin", {})

    display_name = str(plugin_tbl.get("name") or "Orca Box Studio").strip()
    version = PLUGIN_VERSION
    summary = str(
        plugin_tbl.get("description") or proj_tbl.get("description") or ""
    ).strip()
    author = str(plugin_tbl.get("author") or "Orca Box Studio").strip()
    req_py = str(proj_tbl.get("requires-python") or ">=3.12").strip()
    deps = list(proj_tbl.get("dependencies") or ["numpy>=1.26"])

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    whl_name = f"orca_box_generator-{version}-py3-none-any.whl"
    whl_path = DIST_DIR / whl_name
    dist_info = f"orca_box_generator-{version}.dist-info"
    readme_text = (
        (PROJECT_ROOT / "README.md").read_text(encoding="utf-8").strip()
        if (PROJECT_ROOT / "README.md").is_file()
        else summary
    )

    meta_lines = [
        "Metadata-Version: 2.1",
        f"Name: {display_name}",
        f"Version: {version}",
        f"Summary: {summary}",
        f"Author: {author}",
        "License: MIT",
        f"Requires-Python: {req_py}",
        *[f"Requires-Dist: {dep}" for dep in deps],
        "Import-Name: box_studio",
        "Description-Content-Type: text/markdown",
        "",
        readme_text,
        "",
    ]
    metadata_bytes = "\n".join(meta_lines).encode("utf-8")
    wheel_bytes = (
        "Wheel-Version: 1.0\n"
        f"Generator: orca-box-studio-bundler ({version})\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    ).encode("utf-8")
    top_level_bytes = b"box_studio\n"

    entries: list[tuple[str, bytes]] = []
    pkg_files = ["__init__.py", *MODULE_ORDER, "icon.svg"]
    missing = [f for f in pkg_files if not (SRC_PKG_DIR / f).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing package file(s) in {SRC_PKG_DIR} for wheel build: {missing}"
        )

    for fname in pkg_files:
        raw_bytes = (SRC_PKG_DIR / fname).read_bytes().replace(b"\r\n", b"\n")
        entries.append((f"box_studio/{fname}", raw_bytes))

    _, preset_resources = _read_preset_resources()
    for fname, data in preset_resources.items():
        entries.append((f"box_studio/preset_meshes/{fname}", data))

    _, language_resources = _read_language_resources()
    for fname, data in language_resources.items():
        entries.append((f"box_studio/locales/{fname}", data))

    if (PROJECT_ROOT / "LICENSE").is_file():
        entries.append(
            (
                f"{dist_info}/LICENSE",
                (PROJECT_ROOT / "LICENSE").read_bytes().replace(b"\r\n", b"\n"),
            )
        )
    entries.append((f"{dist_info}/METADATA", metadata_bytes))
    entries.append((f"{dist_info}/WHEEL", wheel_bytes))
    entries.append((f"{dist_info}/top_level.txt", top_level_bytes))

    rec_buf = io.StringIO()
    writer = csv.writer(rec_buf, lineterminator="\n")
    for arc_path, data in entries:
        digest_str, size_str = _record_digest_and_size(data)
        writer.writerow([arc_path, digest_str, size_str])
    writer.writerow([f"{dist_info}/RECORD", "", ""])
    entries.append((f"{dist_info}/RECORD", rec_buf.getvalue().encode("utf-8")))

    fixed_dt = (2026, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(
        whl_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as zf:
        for arc_path, data in entries:
            zi = zipfile.ZipInfo(arc_path, date_time=fixed_dt)
            zi.create_system = 3  # Fixed Unix metadata also when built on Windows.
            zi.external_attr = 0o644 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, data)

    return whl_path


def _replace_install_file(source: Path, destination: Path) -> None:
    """Replace the directory entry atomically instead of following a linked old file."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=".orca_box_",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            with source.open("rb") as input_stream:
                shutil.copyfileobj(input_stream, stream)
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def install_plugin(bundle_path: Path) -> Path:
    """Install `orca_box_generator.py` and `icon.svg` into OrcaSlicer's `orca_plugins`,
    preserving OrcaSlicer's `.install_state.json` / `install_state.json` untouched.
    """
    plugin_root = (get_orca_base_dir() / "orca_plugins").resolve()
    install_dir = get_install_dir().resolve()
    if (
        not install_dir.is_relative_to(plugin_root)
        or install_dir.name != "orca_box_generator"
    ):
        raise RuntimeError(
            "Installation target is outside the dedicated Box plugin directory."
        )
    install_dir.mkdir(parents=True, exist_ok=True)

    # Remove any stale .py, .pyc, .pyo, .whl files or __pycache__ directories while
    # strictly preserving `.install_state.json` / `install_state.json` and `icon.svg`.
    for item in list(install_dir.iterdir()):
        if item.name in PRESERVED_SIDE_FILES:
            continue
        if item.is_dir() and item.name == "__pycache__":
            if not item.resolve().is_relative_to(install_dir):
                raise RuntimeError("Refusing to remove an external cache directory.")
            shutil.rmtree(item, ignore_errors=True)
        elif item.is_file() and item.suffix.lower() in {".py", ".pyc", ".pyo", ".whl"}:
            item.unlink()

    for cache_dir in list(install_dir.rglob("__pycache__")):
        if not cache_dir.resolve().is_relative_to(install_dir):
            raise RuntimeError("Refusing to remove an external cache directory.")
        shutil.rmtree(cache_dir, ignore_errors=True)

    dest_py = install_dir / "orca_box_generator.py"
    _replace_install_file(bundle_path, dest_py)

    if ICON_SRC_PATH.is_file():
        _replace_install_file(ICON_SRC_PATH, install_dir / "icon.svg")

    # Enforce strict OrcaSlicer.dll v2.5.1 directory invariants
    py_files = list(install_dir.glob("*.py"))
    whl_files = list(install_dir.glob("*.whl"))
    pyc_files = [*install_dir.rglob("*.pyc"), *install_dir.rglob("*.pyo")]
    pycache_dirs = list(install_dir.rglob("__pycache__"))

    if len(py_files) != 1 or py_files[0].name != "orca_box_generator.py":
        raise RuntimeError(
            f"Expected strictly 1 .py file in {install_dir}, found: {py_files}"
        )
    if whl_files:
        raise RuntimeError(
            f"Found forbidden .whl file(s) in {install_dir}: {whl_files}"
        )
    if pyc_files:
        raise RuntimeError(
            f"Found forbidden bytecode file(s) in {install_dir}: {pyc_files}"
        )
    if pycache_dirs:
        raise RuntimeError(
            f"Found forbidden __pycache__ in {install_dir}: {pycache_dirs}"
        )

    return install_dir


_ISOLATED_SMOKE = r"""
import importlib
import importlib.util
import pathlib
import sys

target = pathlib.Path(sys.argv[1]).resolve()
if sys.argv[2] == "bundle":
    spec = importlib.util.spec_from_file_location("box_bundle_smoke", target)
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
else:
    sys.path.insert(0, str(target))
    package = importlib.import_module("box_studio")
    assert "box_studio.plugin_main" in sys.modules, "Importing the wheel package must register @orca.plugin"
    bridge = sys.modules["box_studio.plugin_main"]
    assert package.OrcaBoxStudioPlugin is bridge.OrcaBoxStudioPlugin
assert bridge.orca._plugin_cls is bridge.OrcaBoxStudioPlugin
bridge._resolve_storage_dir = lambda: pathlib.Path.cwd() / "storage"
bridge.OrcaBoxStudioPlugin().register_capabilities()
registered = bridge.orca._registered_capabilities
assert bridge.BoxStudioPageCapability in registered
assert bridge.BoxStudioDockCapability in registered
assert bridge.orca._requested_permissions == {"threading": True}
page = bridge.BoxStudioPageCapability()
assert page.get_name() == "Box Studio"
assert "Orca Box Studio" in page.get_ui()
assert pathlib.Path(page.get_icon()).is_file()
if sys.argv[2] == "bundle":
    load_mesh = bridge.load_standard_preset_mesh
else:
    load_mesh = importlib.import_module("box_studio.preset_mesh_cache").load_standard_preset_mesh
for item in bridge.BUILTIN_PRESETS:
    if item["params"]["style"] in ("screw_corner", "rugged_box", "sliding_lid"):
        parts = ("base", "lid", "clip_left", "clip_right") if item["params"]["style"] == "rugged_box" else ("base", "lid")
        for part in parts:
            assert load_mesh(item["params"], part) is not None, "Missing exact standalone preset surface"
# Exercise the generated-code path too: prepared defaults alone would hide a
# broken intra-package import in the flattened reconstruction modules.
generate = bridge.generate_box_mesh
topology = bridge.topology_report if sys.argv[2] == "bundle" else package.topology_report
edited = {"style": "rugged_box", "width_x": 162, "height_z": 35.1,
          "rugged_lid_height": 20.3, "fit_clearance": .2}
for part in ("base", "lid"):
    mesh = generate(edited, part)
    report = topology(mesh)
    assert report["closed"] and report["oriented"] and report["components"] == 1 and report["euler"] == 2
    assert mesh.volume_cm3 > 0
# A translated journal/latch keeps its dimensions while missing the exact
# assembly bank; its canonical shape may still use the verified resource.
mesh = generate({"style": "rugged_box", "width_x": 162}, "clip_right")
assert topology(mesh)["closed"] and mesh.volume_cm3 > 0
print("Isolated registration, page, dock, embedded icon, resources and edited Rugged generation: PASS")
"""


def _run_isolated_smoke(target: Path, kind: str, directory: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-W",
            "error",
            "-I",
            "-c",
            _ISOLATED_SMOKE,
            str(target),
            kind,
        ],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"Isolated {kind} smoke check failed:\n{result.stderr}\n{result.stdout}"
        )


def verify_bundle_smoke(bundle_path: Path) -> None:
    """Import only a copied bundle, without a source directory or PYTHONPATH."""
    with tempfile.TemporaryDirectory(prefix="orca_box_bundle_") as folder:
        directory = Path(folder)
        copied = directory / bundle_path.name
        shutil.copyfile(bundle_path, copied)
        _run_isolated_smoke(copied, "bundle", directory)


def verify_wheel_smoke(wheel_path: Path) -> None:
    """Verify RECORD hashes and load only the unpacked wheel in a separate interpreter."""
    with tempfile.TemporaryDirectory(prefix="orca_box_wheel_") as folder:
        directory = Path(folder)
        with zipfile.ZipFile(wheel_path) as archive:
            names = archive.namelist()
            if any(
                Path(name).is_absolute() or ".." in Path(name).parts for name in names
            ):
                raise RuntimeError("Wheel contains an unsafe archive member.")
            record_name = next(
                name for name in names if name.endswith(".dist-info/RECORD")
            )
            for filename, digest, size in csv.reader(
                io.StringIO(archive.read(record_name).decode("utf-8"))
            ):
                if filename == record_name:
                    continue
                data = archive.read(filename)
                if (digest, size) != _record_digest_and_size(data):
                    raise RuntimeError(f"Invalid wheel RECORD entry: {filename}")
            archive.extractall(directory)
        _run_isolated_smoke(directory, "wheel", directory)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and optionally install Orca Box Studio."
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Build and verify without changing the local OrcaSlicer installation.",
    )
    args = parser.parse_args()
    bundle = build_bundle()
    wheel = build_wheel()
    verify_bundle_smoke(bundle)
    verify_wheel_smoke(wheel)
    print(f"Verified: {bundle.name}, {DIST_ANY_BUNDLE_PATH.name}, {wheel.name}")
    if not args.no_install:
        install_plugin(bundle)
        print("Installed Orca Box Studio in its dedicated local plugin directory.")


if __name__ == "__main__":
    main()
