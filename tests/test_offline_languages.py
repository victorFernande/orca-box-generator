"""Seven offline locales are preferences, never geometry parameters."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from box_studio.locale_catalog import TRANSLATIONS, SUPPORTED_LANGUAGES, normalize_language
from box_studio import plugin_main as bridge
from box_studio.studio_ui import get_studio_html


class OfflineLanguageTests(unittest.TestCase):
    def test_locale_normalization(self):
        for raw, code in (("it_IT", "it"), ("es-MX", "es"), ("fr_FR.UTF-8", "fr"),
                          ("de-DE", "de"), ("ja_JP", "ja"), ("PT_br", "pt"),
                          ("en_US", "en"), ("zh_CN", "en"), (None, "pt")):
            self.assertEqual(normalize_language(raw), code)
            if raw:
                self.assertEqual(bridge._detect_language({"language": raw}), code)

    def test_catalog_placeholders_and_no_empty_translation(self):
        self.assertEqual(tuple(TRANSLATIONS), SUPPORTED_LANGUAGES[2:])
        keys = set(TRANSLATIONS["it"])
        for code, catalog in TRANSLATIONS.items():
            self.assertEqual(set(catalog), keys)
            for english, text in catalog.items():
                self.assertTrue(text.strip(), (code, english))
                self.assertEqual(re.findall(r"\{\w+\}", english), re.findall(r"\{\w+\}", text), (code, english))

    @unittest.skipUnless(shutil.which("node"), "Node needed for production dictionary extraction")
    def test_all_ui_dictionary_and_owned_parameter_labels_are_translated(self):
        html = get_studio_html()
        script = re.search(r"<script>(.*?)</script>", html, re.S)[1]
        start = script.index("  const texts =")
        end = script.index("  const tr =", start)
        extra = script[script.index("  Object.assign(texts.en,"):]
        extra = extra[:extra.index("\n  let presetFilter")]
        js = script[start:end] + extra + ";process.stdout.write(JSON.stringify(texts.en))"
        dictionary = json.loads(subprocess.check_output(["node", "-e", js], text=True, encoding="utf-8"))
        labels = re.findall(r'data-en="([^"]+)"', html)
        for code, catalog in TRANSLATIONS.items():
            for text in [*dictionary.values(), *labels, "Parameters", "Export"]:
                self.assertIn(text, catalog, (code, text))

    def test_language_persists_syncs_without_preview_and_preserves_legacy_geometry_key(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(bridge, "_resolve_storage_dir", return_value=Path(folder)):
            controller = bridge.BoxStudioController()
            original = controller.current_params()
            key = controller._geometry_key(original)
            page, dock = [], []
            controller.handle_message({"type": "init"}, page.append, "page")
            controller.handle_message({"type": "init"}, dock.append, "dock")
            page.clear(); dock.clear()
            with patch.object(controller, "_enqueue_preview", side_effect=AssertionError("language generated geometry")):
                controller.handle_message({"type": "set_language", "lang": "it_IT"}, page.append, "page")
            self.assertEqual(page, [{"type": "language_changed", "lang": "it", "revision": 1}])
            self.assertEqual(dock, page)
            self.assertEqual(controller.current_params(), original)
            self.assertEqual(controller._geometry_key(controller.current_params()), key)
            self.assertEqual(controller.build_initial_context()["lang"], "it")
            self.assertEqual(bridge.BoxStudioController().build_initial_context()["lang"], "it")
            self.assertFalse(list(Path(folder).glob("*.tmp")))
            for code in SUPPORTED_LANGUAGES:
                controller.set_language(code)
                self.assertEqual(controller.build_initial_context()["lang"], code)

    def test_seven_locales_render_in_page_and_dock_without_external_assets(self):
        for mode in ("page", "dock"):
            for code in SUPPORTED_LANGUAGES:
                html = get_studio_html(mode, {"lang": code})
                self.assertIn(f'<html lang="{code}"', html)
                self.assertIn('id="lang-select"', html)
                self.assertNotRegex(html, r'<(?:script|link)[^>]+(?:src|href)="https?://')
                self.assertNotRegex(html, r"__BOX_(?:LANGUAGES|TRANSLATIONS|LANGUAGE_OPTIONS)__")


if __name__ == "__main__":
    unittest.main()
