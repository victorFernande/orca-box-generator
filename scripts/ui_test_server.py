"""Isolated backend for browser checks; never imports models into OrcaSlicer."""
from __future__ import annotations
import importlib
import copy
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import sys
import tempfile
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
PACKAGE = next((ROOT / "src").glob("*_studio")).name
SLUG = PACKAGE.split("_", 1)[0]
mod = importlib.import_module(PACKAGE + ".plugin_main")
private = tempfile.TemporaryDirectory(prefix="orca-ui-check-")
mod._resolve_storage_dir = lambda: Path(private.name)
mod._dispatch_files_to_plater = lambda *a, **kw: (False, "Isolated browser test: native transport disabled", None)
mod._open_folder_native = lambda *a, **kw: False
controller = getattr(mod, SLUG.title() + "StudioController")()
outbox = queue.Queue()
outboxes = {"page": outbox, "dock": queue.Queue()}
latest_previews = {}
artifact_manifests = {}
artifact_files = {}
artifact_lock = threading.RLock()
export_lock = threading.Lock()

if SLUG == "box":
    from verify_box_e2e_exports import verify_exports

    # Synthetic printer dimensions are explicit development fixtures, never an
    # update to the running application's profile or native API.
    native_host_context = controller.read_host_context
    native_snapshot = controller.read_full_host_config_snapshot

    def apply_host_fixture(raw):
        host = dict(raw)
        configured = False
        for axis in ("X", "Y", "Z"):
            raw = os.environ.get("ORCA_E2E_BED_" + axis)
            if raw:
                value = float(raw)
                if not 20 <= value <= 2000:
                    raise ValueError("Development bed dimensions must be 20..2000 mm")
                configured = True
                host["bed_" + axis.lower()] = value
                if axis == "Z":
                    host["max_z"] = value
        if configured:
            host["printer_name"] = f"Generic FDM {host['bed_x']:g}x{host['bed_y']:g}"
        return host

    def host_context():
        return apply_host_fixture(native_host_context())

    def host_snapshot(*args, **kwargs):
        return apply_host_fixture(native_snapshot(*args, **kwargs))

    # SSR, init_state, printer sync and exports now share the same fixture.
    controller.read_host_context = host_context
    controller.read_full_host_config_snapshot = host_snapshot
    original_export_action = controller._export_action

    def observed_export_action(params, message, host, send_fn):
        # Serializing only exports lets each real result own exactly its files.
        # Preview/controller workers retain their ordinary product behavior.
        with export_lock:
            p, h = copy.deepcopy(params), copy.deepcopy(host)
            target = message.get("export_target", p["export_target"])
            folder = controller.get_export_dir().resolve()
            folder.relative_to(Path(private.name).resolve())
            before = {path.resolve() for path in folder.iterdir() if path.is_file()}
            with artifact_lock:
                preview = latest_previews.get(getattr(send_fn, "browser_mode", "page"))
            try:
                items = controller._geometry(p, assembled=False, target=target)
                snapshot_error = None
            except Exception as exc:
                items, snapshot_error = [], str(exc)

            def deliver(result):
                if result.get("type") != "action_result":
                    send_fn(result)
                    return
                identity = uuid.uuid4().hex
                # Successful paths preserve writer order. Failed IPC returns no
                # paths, so also discover bytes actually written before failure.
                paths = [Path(value).resolve() for value in result.get("paths", [])]
                if not paths:
                    paths = sorted(path.resolve() for path in folder.iterdir() if path.is_file() and path.resolve() not in before)
                allowed = []
                for path in paths:
                    path.relative_to(folder)
                    path.relative_to(Path(private.name).resolve())
                    if path.is_file() and not path.is_symlink() and path.suffix.lower() in (".stl", ".3mf"):
                        allowed.append(path)
                files = []
                for path in allowed:
                    file_id = uuid.uuid4().hex
                    data = path.read_bytes()
                    files.append({"id": file_id, "name": path.name, "format": path.suffix[1:],
                                  "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                  "download_url": f"/export-artifacts/{identity}/files/{file_id}"})
                    artifact_files[(identity, file_id)] = path
                verification = verify_exports(allowed, items, p, h, preview, target)
                if snapshot_error:
                    verification["errors"].insert(0, snapshot_error)
                    verification["ok"] = False
                manifest = {"id": identity, "action": message["type"], "ok": bool(result.get("ok")),
                            "style": p["style"], "target": target,
                            "format": "3mf" if message["type"] == "send_to_plater" else str(message.get("format", "3mf")).lower(),
                            "params": p, "host": {key: h.get(key) for key in ("bed_x", "bed_y", "bed_z", "max_z")},
                            "files": files, "verification": verification}
                with artifact_lock:
                    artifact_manifests[identity] = manifest
                # Paths from the native product are replaced only in this DEV
                # bridge; public metadata never includes absolute temp paths.
                send_fn({**result, "paths": [item["name"] for item in files],
                         "export_manifest_id": identity,
                         "export_manifest_url": "/export-artifacts/" + identity,
                         "export_manifest": manifest})

            original_export_action(p, message, h, deliver)

    controller._export_action = observed_export_action


def observe_message(message, mode):
    if message.get("type") == "preview_result" and message.get("ok"):
        with artifact_lock:
            latest_previews[mode] = message
    outboxes[mode].put(message)

class Handler(BaseHTTPRequestHandler):
    def reply(self, value, kind="application/json"):
        data = (value if isinstance(value, str) else json.dumps(value)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", kind + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query, keep_blank_values=True)
        if url.path == "/export-artifacts":
            with artifact_lock:
                self.reply(list(artifact_manifests.values()))
            return
        if url.path.startswith("/export-artifacts/"):
            match = re.fullmatch(r"/export-artifacts/([0-9a-f]{32})(?:/files/([0-9a-f]{32}))?", url.path)
            if not match:
                self.send_error(404)
                return
            identity, file_id = match.groups()
            with artifact_lock:
                manifest = artifact_manifests.get(identity)
                path = artifact_files.get((identity, file_id)) if file_id else None
            if not manifest or (file_id and path is None):
                self.send_error(404)
                return
            if file_id:
                resolved = path.resolve()
                try:
                    resolved.relative_to(controller.get_export_dir().resolve())
                    resolved.relative_to(Path(private.name).resolve())
                except ValueError:
                    self.send_error(404)
                    return
                if path.is_symlink() or not path.is_file():
                    self.send_error(404)
                    return
                data = path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", 'attachment; filename="' + path.name.replace('"', "") + '"')
                self.end_headers()
                self.wfile.write(data)
            else:
                self.reply(manifest)
            return
        if url.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if url.path == "/messages":
            mode = "dock" if query.get("mode", ["page"])[0] == "dock" else "page"
            messages = []
            while True:
                try:
                    messages.append(outboxes[mode].get_nowait())
                except queue.Empty:
                    break
            self.reply(messages)
            return
        if url.path != "/":
            self.send_error(404)
            return
        mode = "dock" if "dock" in query else "page"
        # Let the controller initialize host preferences before applying the
        # explicit synthetic theme/language requested by this browser case.
        controller.build_initial_context(mode)
        params = controller.current_params() if SLUG == "box" else controller.current_params
        params.update(theme=query.get("theme", ["dark"])[0], lang=query.get("lang", ["pt"])[0])
        if SLUG == "box":
            controller.set_current_params(params)
        else:
            controller.set_current_params(params, history=False)
        context = controller.build_initial_context(mode)
        context.update(theme=params["theme"], lang=params["lang"])
        html = mod.get_studio_html(mode, context)
        shim = """<script>
window.__hostMessages=[];window.__sentMessages=[];
// Development-only observation of the actual matrices submitted to WebGL.
// Product code receives no additional API and the native host is never used.
window.__glModelFrame={models:[]};
if(window.WebGL2RenderingContext){
const proto=WebGL2RenderingContext.prototype,names=new WeakMap();
const getLocation=proto.getUniformLocation,uniformMatrix=proto.uniformMatrix4fv,clear=proto.clear;
proto.getUniformLocation=function(program,name){const location=getLocation.call(this,program,name);if(location)names.set(location,name);return location;};
proto.clear=function(){window.__glModelFrame={models:[]};return clear.apply(this,arguments);};
proto.uniformMatrix4fv=function(location,transpose,matrix){if(location&&names.get(location)==='u_model')window.__glModelFrame.models.push(Array.from(matrix));return uniformMatrix.apply(this,arguments);};
}
window.orca={onMessage:callback=>window.__hostCallback=callback,postMessage:payload=>{
const body=JSON.stringify(payload);window.__sentMessages.push(JSON.parse(body));return fetch('/message?mode=MODE',{method:'POST',headers:{'Content-Type':'application/json'},body});}};
setInterval(async()=>{try{const response=await fetch('/messages?mode=MODE');for(const m of await response.json()){
window.__hostMessages.push({type:m.type,warning:m.warning,ok:m.ok,meshes:m.meshes?.length,parts:m.meshes?.map(mesh=>mesh.part),request_id:m.request_id,seed:m.seed,candidate_params:m.candidate_params,message:m.message,params:m.params,hinge:m.hinge,latch_motion:m.latch_motion,geometry_key:m.geometry_key,action:m.action,paths:m.paths,transport_only:m.transport_only,export_manifest_id:m.export_manifest_id,export_manifest_url:m.export_manifest_url,export_manifest:m.export_manifest});
if(window.__hostCallback)window.__hostCallback(m);else if(window.handleHostMessage)window.handleHostMessage(m);else window.dispatchEvent(new MessageEvent('message',{data:m}));
}}catch(error){console.error(error);}},150);
</script>""".replace("MODE", mode)
        self.reply(html.replace("<head>", "<head>" + shim, 1), "text/html")

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/shutdown":
            self.reply({"stopping": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if url.path != "/message":
            self.send_error(404)
            return
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        mode = "dock" if parse_qs(url.query).get("mode", ["page"])[0] == "dock" else "page"
        def post(message):
            observe_message(message, mode)
        post.browser_mode = mode
        controller.handle_message(payload, post, mode)
        self.reply({"accepted": True})

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    print(json.dumps({"url": "http://127.0.0.1:" + str(server.server_port), "slug": SLUG}), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        private.cleanup()
