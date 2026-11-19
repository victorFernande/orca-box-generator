"""Negative controls for the DEV artifact readers and localhost allowlist."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from box_studio.schema import normalize_params
from box_studio.mesh_generator import MeshData, collect_target_meshes, generate_box_mesh, orient_mesh_for_print, np
from box_studio.exporters import write_binary_stl, write_orca_3mf
from verify_box_e2e_exports import _read_3mf, _read_stl, inspect_mesh, verify_exports


class ArtifactVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private = tempfile.TemporaryDirectory(prefix="orca-e2e-verifier-")
        cls.addClassCleanup(cls.private.cleanup)
        cls.params = normalize_params({"style": "open_bin", "width_x": 90, "depth_y": 60, "height_z": 40})
        cls.host = {"bed_x": 260, "bed_y": 260, "max_z": 260}
        cls.items = collect_target_meshes(cls.params, assembled=False)
        cls.stl = write_binary_stl(Path(cls.private.name) / "actual.stl", cls.items[0][1])
        cls.project = write_orca_3mf(Path(cls.private.name) / "actual.3mf", cls.items, cls.params, cls.host)
        cls.preview = {"ok": True, "params": cls.params, "meshes": [
            {"part": mesh.part,
             "vertices": base64.b64encode(mesh.vertices.astype("<f4").tobytes()).decode(),
             "triangles": base64.b64encode(mesh.triangles.astype("<u4").tobytes()).decode()}
            for _, mesh in collect_target_meshes(cls.params, assembled=True)]}

    def test_real_product_bytes_and_snapshot_pass(self):
        for path in (self.stl, self.project):
            with self.subTest(format=path.suffix):
                report = verify_exports([path], self.items, self.params, self.host, self.preview, self.params["export_target"])
                self.assertTrue(report["ok"], report)
                self.assertTrue(report["preview_identity"]["observed"])
                self.assertEqual(report["parts"][0]["components"], 1)
                self.assertEqual(len(report["print_snapshot"][0]["vertices_sha256"]), 64)

    def test_corrupted_stl_and_wrong_3mf_process_settings_reject(self):
        corrupted = bytearray(self.stl.read_bytes())
        corrupted[96:100] = b"\x00\x00\xc0\x7f"  # NaN in the first facet vertex.
        with self.assertRaisesRegex(ValueError, "facets differ"):
            _read_stl(corrupted, self.items[0][1])
        output = io.BytesIO()
        with zipfile.ZipFile(self.project) as original, zipfile.ZipFile(output, "w") as replacement:
            for name in original.namelist():
                data = original.read(name)
                if name == "Metadata/project_settings.config":
                    settings = json.loads(data)
                    settings["wall_loops"] = "1"
                    data = json.dumps(settings).encode()
                replacement.writestr(name, data)
        with self.assertRaisesRegex(ValueError, "project setting mismatch"):
            _read_3mf(output.getvalue(), self.items, self.params, self.host)

    def test_open_reversed_duplicate_faces_and_bowtie_vertex_reject(self):
        v = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float32)
        t = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]], dtype=np.int32)
        self.assertEqual(inspect_mesh(v, t)["components"], 1)
        for triangles in (t[:-1], t[:, ::-1], np.concatenate([t, t[:1]])):
            with self.subTest(faces=len(triangles)), self.assertRaises(ValueError):
                inspect_mesh(v, triangles)
        # Two outward tetrahedra share only one vertex: all edge incidences are
        # valid, but that vertex has two disconnected link cycles.
        vertices = np.concatenate([v, -v[1:]])
        other = np.where(t == 0, 0, t + 3)[:, ::-1]
        with self.assertRaisesRegex(ValueError, "vertex link"):
            inspect_mesh(vertices, np.concatenate([t, other]))

    def test_delivered_preview_must_correspond_to_export_snapshot(self):
        changed = dict(self.params, width_x=self.params["width_x"] + 1)
        result = verify_exports([self.project], self.items, changed, self.host, self.preview, changed["export_target"])
        self.assertFalse(result["ok"])
        self.assertTrue(any("preview snapshot" in message for message in result["errors"]), result)

    def test_sliding_actual_export_requires_broad_contact_not_only_a_tooth(self):
        params = normalize_params({"style": "sliding_lid", "width_x": 60, "depth_y": 50,
                                   "height_z": 30, "export_target": "lid_only"})
        canonical = generate_box_mesh(params, "lid", False)
        printed = orient_mesh_for_print(canonical, params, "lid")

        def check(mesh, preview_mesh, filename):
            preview = {"ok": True, "params": params, "meshes": [{"part": "lid",
                "vertices": base64.b64encode(preview_mesh.vertices.astype("<f4").tobytes()).decode(),
                "triangles": base64.b64encode(preview_mesh.triangles.astype("<u4").tobytes()).decode()}]}
            path = write_binary_stl(Path(self.private.name) / filename, mesh)
            return verify_exports([path], [("Lid", mesh)], params, self.host, preview, "lid_only")

        good = check(printed, canonical, "sliding-flat.stl")
        self.assertTrue(good["ok"], good)
        self.assertIn("sliding_lid_broad_bed_contact", good["checks"])
        self.assertGreaterEqual(good["parts"][0]["bed_contact_bbox_fraction"], 0.25)
        self.assertEqual(good["parts"][0]["bed_contact_tolerance_mm"], 0.005)

        # Turn the same actual lid upside down: it is still a closed positive
        # solid, with bytes/source/preview parity, but stands on the small tooth.
        v = printed.vertices.copy()
        v[:, 2] *= -1
        v[:, 2] -= v[:, 2].min()
        t = printed.triangles[:, [0, 2, 1]].copy()
        xyz = v[t].astype(float)
        normals = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        low, high = v.min(axis=0), v.max(axis=0)
        inverted = MeshData(v, t, normals.astype(np.float32),
                            {"min": low.tolist(), "max": high.tolist(), "size": (high-low).tolist()},
                            printed.volume_cm3, "lid", printed.interface_error_mm)
        bad = check(inverted, inverted, "sliding-tooth-only.stl")
        self.assertFalse(bad["ok"])
        self.assertTrue(bad["preview_identity"]["ok"], bad)
        self.assertTrue(bad["parts"][0]["closed"] and bad["parts"][0]["oriented"])
        self.assertLess(bad["parts"][0]["bed_contact_bbox_fraction"], 0.25)
        self.assertTrue(any("too little" in message for message in bad["errors"]), bad)

    def test_http_allows_only_registered_temp_bytes_and_failed_ipc_is_honest(self):
        child = subprocess.Popen([sys.executable, "-B", "-W", "error", str(ROOT / "scripts/ui_test_server.py")],
                                 cwd=ROOT, env={**os.environ, "ORCA_E2E_BED_X": "260", "ORCA_E2E_BED_Y": "270", "ORCA_E2E_BED_Z": "280"},
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, encoding="utf-8")
        url = None

        def get(route):
            with urllib.request.urlopen(url + route, timeout=30) as response:
                return response.read()

        def post(payload, route="/message"):
            request = urllib.request.Request(url + route, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read())

        def message(kind):
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                for item in json.loads(get("/messages?mode=page")):
                    if item.get("type") == kind:
                        return item
                time.sleep(0.02)
            self.fail("Timed out waiting for " + kind)

        try:
            line = child.stdout.readline()
            self.assertTrue(line, "DEV server exited before readiness")
            url = json.loads(line)["url"]
            fixture = {"bed_x": 260, "bed_y": 270, "bed_z": 280, "max_z": 280}

            def assert_host(host):
                for key, value in fixture.items():
                    self.assertEqual(host[key], value)
                self.assertEqual(host["printer_name"], "Generic FDM 260x270")

            for route in ("/", "/?dock"):
                html = get(route).decode("utf-8")
                initial = json.JSONDecoder().raw_decode(html.split("const INITIAL = ", 1)[1])[0]
                assert_host(initial["host"])
            for action in ("get_initial_state", "sync_printer"):
                post({"type": action})
                assert_host(message("init_state")["host"])
            post({"type": "update_params", "params": self.params})
            self.assertTrue(message("preview_result")["ok"])
            post({"type": "send_to_plater", "params": self.params})
            result = message("action_result")
            self.assertFalse(result["ok"])
            self.assertIn("native transport disabled", result["message"])
            manifest = json.loads(get(result["export_manifest_url"]))
            self.assertTrue(manifest["verification"]["ok"], manifest)
            self.assertEqual(manifest["host"], fixture)
            self.assertEqual(manifest["verification"]["bed_mm"], [260, 270, 280])
            file = manifest["files"][0]
            data = get(file["download_url"])
            self.assertEqual(len(data), file["size_bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), file["sha256"])
            self.assertNotIn("AppData", json.dumps(manifest))
            for route in ("/export-artifacts/../../README.md", "/export-artifacts/" + "0" * 32,
                          result["export_manifest_url"] + "/files/" + "0" * 32, "/README.md"):
                with self.subTest(route=route), self.assertRaises(urllib.error.HTTPError) as rejected:
                    get(route)
                self.assertEqual(rejected.exception.code, 404)
            count = len(json.loads(get("/export-artifacts")))
            post({"type": "export_file", "format": "3mf", "params": dict(self.params, height_z=8)})
            rejection = message("action_result")
            self.assertFalse(rejection["ok"])
            self.assertNotIn("export_manifest_id", rejection)
            self.assertEqual(len(json.loads(get("/export-artifacts"))), count)
        finally:
            if url:
                try:
                    post({}, "/shutdown")
                    child.wait(timeout=10)
                except (OSError, subprocess.TimeoutExpired):
                    child.kill()
            elif child.poll() is None:
                child.kill()
            child.communicate(timeout=10)


if __name__ == "__main__":
    unittest.main()
