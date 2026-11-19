"""Native Page/Dock host integration; infrastructure adapted from Orca Gear Studio (MIT)."""

from __future__ import annotations
from collections.abc import Sequence
from collections import OrderedDict
import copy, ctypes, json, locale, os, re, sys, threading, time, types, base64, hashlib
from pathlib import Path
from typing import Any, Callable
from .schema import DEFAULT_PARAMS, normalize_params, validate_params
from .mesh_generator import (
    collect_target_meshes,
    topology_report,
    hinge_geometry,
    orient_mesh_for_print,
    clamshell_print_bounds,
    generate_box_mesh,
    np,
)
from .exporters import write_binary_stl, write_orca_3mf
from .presets_catalog import (
    BUILTIN_PRESETS,
    load_user_presets,
    save_user_preset,
    delete_user_preset,
    generate_random_printable_params,
)
from .studio_ui import get_studio_html
from .linux_ipc import send_linux_plater_request


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
            "version": "1.2.1",
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
            from .mesh_generator import latch_geometry

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
