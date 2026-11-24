"""Offline locales are preferences, never geometry parameters."""
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
from box_studio.language_packs import canonical_language_code
from box_studio import plugin_main as bridge
from box_studio.studio_ui import get_studio_html


class OfflineLanguageTests(unittest.TestCase):
    def test_locale_normalization(self):
        for raw, code in (("it_IT", "it"), ("es-MX", "es"), ("fr_FR.UTF-8", "fr"),
                          ("de-DE", "de"), ("ja_JP", "ja"), ("PT_br", "pt"),
                          ("en_US", "en"), ("!unsupported!", "en"), (None, "pt")):
            exact = canonical_language_code(raw)
            expected = exact if exact in TRANSLATIONS else code
            self.assertEqual(normalize_language(raw), expected)
            if raw:
                self.assertEqual(bridge._detect_language({"language": raw}), expected)

    def test_catalog_placeholders_and_no_empty_translation(self):
        self.assertEqual(tuple(TRANSLATIONS), SUPPORTED_LANGUAGES)
        for code, catalog in TRANSLATIONS.items():
            for english, text in catalog.items():
                self.assertTrue(text.strip(), (code, english))
                self.assertEqual(sorted(re.findall(r"\{\w+\}", english)), sorted(re.findall(r"\{\w+\}", text)), (code, english))

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
        reference = json.loads((ROOT / "tests/fixtures/1.4.0-translation-digests.json").read_text(encoding="utf-8"))
        for code in reference["catalogs"]:
            catalog = TRANSLATIONS[code]  # New partial catalogs use English fallback.
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
                controller.handle_message({"type": "set_language", "lang": "it"}, page.append, "page")
            self.assertEqual(page, [{"type": "language_changed", "lang": "it", "revision": 1,
                                     "origin": "page", "language_request_id": 0, "language_client_id": ""}])
            self.assertEqual(dock, page)
            self.assertEqual(controller.current_params(), original)
            self.assertEqual(controller._geometry_key(controller.current_params()), key)
            self.assertEqual(controller.build_initial_context()["lang"], "it")
            self.assertEqual(bridge.BoxStudioController().build_initial_context()["lang"], "it")
            self.assertFalse(list(Path(folder).glob("*.tmp")))
            for code in SUPPORTED_LANGUAGES:
                controller.set_language(code)
                self.assertEqual(controller.build_initial_context()["lang"], code)

    def test_all_locales_render_in_page_and_dock_without_external_assets(self):
        for mode in ("page", "dock"):
            for code in SUPPORTED_LANGUAGES:
                html = get_studio_html(mode, {"lang": code})
                self.assertIn(f'<html lang="{code}"', html)
                self.assertIn('id="lang-select"', html)
                self.assertNotRegex(html, r'<(?:script|link)[^>]+(?:src|href)="https?://')
                self.assertNotRegex(html, r"__BOX_(?:LANGUAGES|TRANSLATIONS|LANGUAGE_OPTIONS)__")

    @unittest.skipUnless(shutil.which("node"), "Node needed for production message handler")
    def test_stale_own_ack_and_newer_foreign_update_converge_to_latest_revision(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        helpers = script[script.index("const OFFLINE_LANGUAGES"):script.index("(() => {")]
        select = script[script.index("  function selectLanguage("):script.index('  $("lang-select").onchange')]
        receive = script[script.index("  function receive(raw)"):script.index('  window.addEventListener("message", receive)')]
        setup = """
const INITIAL={mode:'page'};const document={documentElement:{lang:'pt'}};
const languageClientId='unit';
let lang='pt',pendingLanguageRequest=0,languageRequestSerial=0,lastLanguageRevision=0;
const sent=[];function translate(){document.documentElement.lang=lang}function sync(){}function send(m){sent.push(m)}
"""
        checks = """
selectLanguage('it');selectLanguage('fr');
receive({type:'language_changed',lang:'it',origin:'page',language_client_id:'unit',language_request_id:1,revision:1});
if(lang!=='fr')throw Error('old own ack overwrote latest manual choice');
receive({type:'language_changed',lang:'fr',origin:'page',language_client_id:'unit',language_request_id:2,revision:2});
if(lang!=='fr'||pendingLanguageRequest!==0)throw Error('own choice not acknowledged');
// A newer dock change must survive a delayed acknowledgement from this page.
lastLanguageRevision=0;selectLanguage('fr');
receive({type:'language_changed',lang:'de',origin:'dock',language_request_id:9,revision:4});
receive({type:'language_changed',lang:'fr',origin:'page',language_client_id:'unit',language_request_id:3,revision:3});
if(lang!=='de'||pendingLanguageRequest!==0||lastLanguageRevision!==4)throw Error('views did not converge to newer foreign revision');
receive({type:'language_changed',lang:'ja',origin:'dock',language_request_id:1,revision:1});
if(lang!=='de')throw Error('stale foreign revision overwrote latest state');
if(sent.length!==3)throw Error('receiving locale updates sent another request');
"""
        result = subprocess.run(["node"], input=setup+helpers+select+receive+checks,
                                text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reordered_requests_do_not_overwrite_preferences_and_reopened_view_can_choose(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(bridge, "_resolve_storage_dir", return_value=Path(folder)):
            controller = bridge.BoxStudioController()
            responses = []
            for language, request, client in (("fr", 2, "first"), ("it", 1, "first")):
                controller.handle_message({"type": "set_language", "lang": language,
                                           "language_request_id": request, "language_client_id": client}, responses.append)
            self.assertEqual(controller.preferred_language(), "fr")
            self.assertEqual(responses[-1]["revision"], 1)
            controller.handle_message({"type": "set_language", "lang": "it",
                                       "language_request_id": 1, "language_client_id": "reopened"}, responses.append)
            self.assertEqual(controller.preferred_language(), "it")
            for index in range(25):
                controller.handle_message({"type": "set_language", "lang": "it",
                                           "language_request_id": 1, "language_client_id": str(index)}, responses.append)
            self.assertLessEqual(len(controller._language_request_ids), 16)


if __name__ == "__main__":
    unittest.main()
