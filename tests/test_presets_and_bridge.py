"""Persistence, offline UI, native bridge contracts and preview concurrency."""

import ast, json, re, sys, tempfile, threading, unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio import plugin_main as bridge
from box_studio.schema import normalize_params
from box_studio.presets_catalog import (
    save_user_preset,
    load_user_presets,
    delete_user_preset,
)
from box_studio.studio_ui import get_studio_html


class PresetBridgeTests(unittest.TestCase):
    def test_01_atomic_presets_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "presets.json"
            p = normalize_params()
            saved = save_user_preset(path, "My enclosure", p)
            self.assertEqual(load_user_presets(path)[0]["params"], p)
            p["width_x"] = 101
            save_user_preset(path, "Updated", p, saved["id"])
            self.assertEqual(len(load_user_presets(path)), 1)
            self.assertEqual(load_user_presets(path)[0]["params"]["width_x"], 101)
            self.assertTrue(delete_user_preset(path, saved["id"]))
            self.assertEqual(load_user_presets(path), [])
            path.write_text("broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_user_presets(path)

    def test_02_offline_page_and_dock(self):
        for mode in ("page", "dock"):
            html = get_studio_html(
                mode,
                {
                    "params": normalize_params(
                        {"name": "</script><script>alert(1)</script>"}
                    )
                },
            )
            self.assertTrue(re.search(r"getContext\(\s*['\"]webgl2['\"]", html))
            self.assertIn("receiveBoxMessage", html)
            self.assertNotIn('src="http', html)
            self.assertNotIn('href="http', html)
            self.assertNotIn("</script><script>alert", html)
            self.assertIn("<\\/script>", html)
            self.assertIn('"mode":"' + mode + '"', html)
        tree = ast.parse(Path(bridge.__file__).read_text(encoding="utf-8"))
        entries = [
            n
            for n in tree.body
            if isinstance(n, ast.ClassDef)
            and any(
                isinstance(d, ast.Attribute) and d.attr == "plugin"
                for d in n.decorator_list
            )
        ]
        self.assertEqual(len(entries), 1)

    def test_03_permissions_capabilities_and_windows_escaping(self):
        with (
            patch.object(bridge.orca, "register_capability") as register,
            patch.object(bridge.orca, "request_permissions") as permissions,
        ):
            bridge.OrcaBoxStudioPlugin().register_capabilities()
            permissions.assert_called_once_with(threading=True)
            self.assertEqual(register.call_count, 2)
        payload = bridge._format_other_instance_payload(
            [r'C:\folder with space\part "quoted".3mf']
        )
        self.assertTrue(payload.startswith('"orca-slicer.exe";'))
        self.assertFalse(payload.endswith(";"))
        self.assertIn('\\"quoted\\"', payload)

    def test_04_preview_one_worker_delivers_to_both_views(self):
        controller = bridge.BoxStudioController()
        started = threading.Event()
        release = threading.Event()
        done = threading.Event()
        output_a = []
        output_b = []
        calls = []

        def payload(params):
            calls.append(params["width_x"])
            started.set()
            self.assertTrue(release.wait(5))
            return {"type": "preview_result", "ok": True, "params": params}

        def post_b(value):
            output_b.append(value)
            done.set()

        with patch.object(controller, "_preview_payload", side_effect=payload):
            controller._enqueue_preview(normalize_params(), output_a.append, 3, "page")
            self.assertTrue(started.wait(5))
            controller._enqueue_preview(normalize_params(), post_b, 9, "dock")
            release.set()
            self.assertTrue(done.wait(5))
            controller._last_worker.join(5)
        self.assertEqual(calls, [90.0])
        self.assertEqual(output_a[0]["request_id"], 3)
        self.assertEqual(output_b[0]["request_id"], 9)

    def test_05_local_preferences_do_not_broadcast_geometry(self):
        c = bridge.BoxStudioController()
        a = []
        b = []
        c.handle_message({"type": "init"}, a.append, "page")
        c.handle_message({"type": "init"}, b.append, "dock")
        a.clear()
        b.clear()
        with patch.object(c, "_enqueue_preview"):
            p = normalize_params({"lang": "en", "theme": "light"})
            c.handle_message({"type": "preview", "params": p}, a.append, "page")
        self.assertEqual(b, [])
        with patch.object(c, "_enqueue_preview"):
            p["width_x"] = 110
            c.handle_message({"type": "preview", "params": p}, a.append, "page")
        self.assertEqual(b[0]["type"], "design_changed")

    def test_06_no_fake_success_on_transport_failure(self):
        c = bridge.BoxStudioController()
        output = []
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(c, "_geometry", return_value=[]),
            patch.object(c, "get_export_dir", return_value=Path(folder)),
            patch.object(bridge, "write_orca_3mf"),
            patch.object(
                bridge,
                "_dispatch_files_to_plater",
                return_value=(False, "Unavailable", None),
            ),
        ):
            c._export_action(
                normalize_params(), {"type": "send_to_plater"}, {}, output.append
            )
        self.assertFalse(output[-1]["ok"])
        self.assertIn("Unavailable", output[-1]["message"])


if __name__ == "__main__":
    unittest.main()
