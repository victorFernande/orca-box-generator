"""Language-only updates retain the accepted mesh and action-result messages."""

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.studio_ui import get_studio_html


class QualityOptions(HTMLParser):
    def __init__(self):
        super().__init__()
        self.options = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "option" and attrs.get("value") in ("standard", "fine"):
            self.options.append(
                dict(value=attrs["value"], dataset=dict(i18n=attrs.get("data-i18n")))
            )


@unittest.skipUnless(
    shutil.which("node"), "Node required for the production language handler"
)
class PreviewTranslationTests(unittest.TestCase):
    def test_language_updates_preview_and_quality_without_regeneration_or_losing_results(
        self,
    ):
        html = get_studio_html()
        parser = QualityOptions()
        parser.feed(html)
        self.assertEqual(len(parser.options), 2)
        self.assertTrue(all(option["dataset"]["i18n"] for option in parser.options))
        script = re.search(r"<script>(.*?)</script>", html, re.S)[1]
        locale_helpers = script[script.index("const OFFLINE_LANGUAGES"):script.index("(() => {")]
        translations = script[
            script.index("const texts =") : script.index("function send(")
        ]
        status = script[
            script.index("function status(") : script.index("texts.pt.parameters =")
        ]
        language = script[
            script.index("function updatePreviewText()") : script.index(
                "function snapshot()"
            )
        ]
        setup = (
            "const quality="
            + json.dumps(parser.options)
            + ";"
            + """
        const classList=()=>{const values=new Set();return {add:v=>values.add(v),remove:v=>values.delete(v),contains:v=>values.has(v),toggle:(v,on)=>on?values.add(v):values.delete(v)}};
        const nodes={target:{options:[]}};
        const $=id=>nodes[id]||(nodes[id]={textContent:'',classList:classList(),setAttribute(key,value){this[key]=value}});
        const document={documentElement:{dataset:{}},querySelectorAll:selector=>selector==='[data-i18n]'?quality:[]};
        let lang='en',theme='dark',lastInterfaceError=.018,statusTranslationKey=null,timers=0;
        const p={width_x:120,height_z:14},mesh={sentinel:'same GPU buffers'},meshes=[mesh];
        let serial=12,latest=12,requests=0;
        function send(){requests++;throw Error('language sent an unexpected host request')}
        function requestPreview(){throw Error('language regenerated geometry')}
        function setTimeout(){return ++timers}function clearTimeout(){}
        function updateClearanceLabels(){}function updateOpeningCaption(){}function updatePrintHelp(){}function updateClamshellNote(){}
        function presets(){}function syncPresetSelection(){}function features(){}function drawPlan(){}function render(){}
        """
        )
        checks = """
        status(tr('ready'),false,'ready');translate();
        if(!nodes.surface.textContent.startsWith('Curved interface')||quality[0].textContent!=='Standard'||quality[1].textContent!=='Fine')throw Error('English preview text incorrect');
        const originalTimer=status.timer;lang='pt';translate();
        if(!nodes.surface.textContent.startsWith('Alvo de erro')||!nodes.surface.textContent.endsWith('0.018 mm'))throw Error('accepted interface error was not translated');
        if(nodes.status.textContent!==texts.pt.ready||nodes['toast-banner'].textContent!==texts.pt.ready)throw Error('ready status remained in the previous language');
        if(quality[0].textContent!=='Padrão'||quality[1].textContent!=='Fina')throw Error('quality options not translated');
        if(timers!==1||status.timer!==originalTimer)throw Error('translation restarted the notification timer');
        status('Export completed: part.3mf');lang='en';translate();
        if(nodes.status.textContent!=='Export completed: part.3mf')throw Error('translation erased an export result');
        status('Fit error for the requested design',true);lang='pt';translate();
        if(nodes.status.textContent!=='Fit error for the requested design'||!nodes.status.classList.contains('warn'))throw Error('translation erased an error');
        if(requests||serial!==12||latest!==12||meshes.length!==1||meshes[0]!==mesh||p.width_x!==120||p.height_z!==14||lastInterfaceError!==.018)throw Error('language changed geometry, revisions or the accepted payload');
        """
        result = subprocess.run(
            ["node"],
            input=setup + locale_helpers + translations + status + language + checks,
            text=True, encoding="utf-8",
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
