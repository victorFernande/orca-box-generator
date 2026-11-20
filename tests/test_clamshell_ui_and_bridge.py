"""Equal-half clamshell UI poses, printable envelope and assembly cache contract."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio import plugin_main as bridge
from box_studio.exporters import write_orca_3mf
from box_studio.mesh_generator import (
    clamshell_open_transform,
    clamshell_print_bounds,
    hinge_geometry,
    np,
    topology_report,
)
from box_studio.presets_catalog import BUILTIN_PRESETS, generate_random_printable_params
from box_studio.studio_ui import get_studio_html


def preset():
    return next(
        item["params"]
        for item in BUILTIN_PRESETS
        if item["id"] == "clamshell_pip_short"
    )


class ClamshellBridgeTests(unittest.TestCase):
    def test_preview_and_open_export_share_two_validated_shells_and_one_export_object(
        self,
    ):
        params = preset()
        controller = bridge.BoxStudioController()
        with (
            patch.object(
                bridge, "generate_box_mesh", wraps=bridge.generate_box_mesh
            ) as generate,
            patch.object(bridge, "topology_report", wraps=topology_report) as validate,
        ):
            preview = controller._preview_payload(params)
            printed = controller._geometry(
                params, assembled=False, target="base_and_lid"
            )
            repeated = controller._preview_payload(params)
        self.assertEqual([mesh["part"] for mesh in preview["meshes"]], ["base", "lid"])
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(validate.call_count, 2)
        self.assertIs(preview["meshes"], repeated["meshes"])
        self.assertEqual(preview["print_bounds"], clamshell_print_bounds(params))
        self.assertEqual(len(printed), 1)
        assembly = printed[0][1]
        self.assertEqual(assembly.part, "clamshell_pip_assembly")
        self.assertAlmostEqual(assembly.bounds_mm["min"][2], 0, places=5)
        self.assertEqual(
            len(assembly.triangles),
            sum(item["triangle_count"] for item in preview["meshes"]),
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "articulated.3mf"
            write_orca_3mf(
                path,
                printed,
                params=params,
                host_config=dict(bed_x=220, bed_y=220, max_z=250),
            )
            with zipfile.ZipFile(path) as archive:
                document = ET.fromstring(archive.read("3D/3dmodel.model"))
            objects = document.findall(".//{*}resources/{*}object")
            self.assertEqual(
                len(objects),
                1,
                "The packer must keep both articulated halves in one object",
            )

    def test_surprise_uses_the_open_footprint_and_hinge_height(self):
        params = preset()
        for seed in range(12):
            candidate = generate_random_printable_params(
                params, seed, dict(bed_x=160, bed_y=150, max_z=80)
            )
            self.assertEqual(candidate["style"], "clamshell_pip")
            size = clamshell_print_bounds(candidate)["size"]
            self.assertTrue(
                all(value <= limit for value, limit in zip(size, (160, 150, 80)))
            )
        with self.assertRaisesRegex(ValueError, "safe variation|variação"):
            generate_random_printable_params(
                params, 3, dict(bed_x=20, bed_y=50, max_z=80)
            )


@unittest.skipUnless(
    shutil.which("node"), "Node required for embedded camera and hinge poses"
)
class ClamshellUiTests(unittest.TestCase):
    def run_js(self, suffix):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        start = re.search(r"const I\s*=", script).start()
        end = script.index("function decode", start)
        params = preset()
        setup = (
            "const p="
            + json.dumps(params)
            + ";let meshParams=p;const INITIAL={preview_mode:'assembly',hinge:"
            + json.dumps(hinge_geometry(params))
            + "};"
        )
        setup += "let openingStyle=null;const controls={open:{value:'25',max:'100'},openValue:{}};const $=id=>controls[id];const meshes=[];let zoom=1,yaw=0,pitch=.5;"
        result = subprocess.run(
            ["node"],
            input=setup + script[start:end] + suffix,
            text=True, encoding="utf-8",
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_new_style_opens_at_180_degrees_and_keeps_edited_angle_on_refresh(self):
        self.run_js("""
        configureOpening();
        if($('open').max!=='180'||$('open').value!=='180'||openingFraction()!==1||$('openValue').textContent!=='180°')throw Error('initial clamshell not open180');
        $('open').value='90';configureOpening();
        if(openingFraction()!==.5||$('openValue').textContent!=='90°')throw Error('refresh reset the chosen angle');
        meshParams={style:'rugged_box'};configureOpening();
        if($('open').max!=='100'||$('open').value!=='0'||openingFraction()!==0||$('openValue').textContent!=='0%')throw Error('rugged percentage view must start with its clips installed');
        """)

    def test_preview_hinge_transform_matches_the_python_export_pose(self):
        params = preset()
        points = np.array(
            [[-60, -32.5, 28.2], [60, 32.5, 28.2], [-60, -32.5, 14.2], [0, 37.5, 14.1]],
            dtype=float,
        )
        angles = [0, 37, 90, 180]
        expected = [
            clamshell_open_transform(points, params, angle).tolist() for angle in angles
        ]
        script = (
            "const points="
            + json.dumps(points.tolist())
            + ",angles="
            + json.dumps(angles)
            + ";process.stdout.write(JSON.stringify(angles.map(angle=>points.map(q=>transformPoint(partTransform('lid',angle/180),...q)))));"
        )
        actual = np.array(json.loads(self.run_js(script)))
        self.assertTrue(
            np.allclose(actual, expected, atol=4e-6),
            "Rendered and printable hinge poses must be the same transform",
        )

    def test_note_distinguishes_closed_height_from_the_open_print_envelope(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        # These focused DOM stubs expose lang directly; use the production
        # catalog/formatter with that locale instead of a full document root.
        runtime = script[script.index("const OFFLINE_LANGUAGES"):script.index("(() => {")]
        runtime += "const productionLocaleText=localeText;localeText=(en,pt=en,code=lang,context=null)=>productionLocaleText(en,pt,code,context);"
        translations = script[
            script.index("const texts =") : script.index("function send(")
        ]
        helper = script[
            script.index("function updateClamshellNote()") : script.index(
                "function translate()"
            )
        ]
        setup = (
            "const p="
            + json.dumps(preset())
            + ";const meshParams=p,INITIAL={print_bounds:"
            + json.dumps(clamshell_print_bounds(preset()))
            + "};let localDirty=false,lang='pt';const label={};const $=()=>label;"
        )
        checks = """
        updateClamshellNote();
        if(!label.textContent.includes('28.20 mm')||!label.textContent.includes('120.0×140.0×17.3 mm'))throw Error('closed height and open footprint are confused');
        lang='en';updateClamshellNote();
        if(!label.textContent.includes('Open footprint on the bed'))throw Error('open envelope note not translated');
        localDirty=true;updateClamshellNote();
        if(label.textContent.includes('120.0×140.0'))throw Error('stale print envelope shown for an uncommitted edit');
        """
        result = subprocess.run(
            ["node"],
            input=runtime + setup + translations + helper + checks,
            text=True, encoding="utf-8",
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pip_gap_and_hinge_clearance_have_distinct_labels_and_values(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        runtime = script[script.index("const OFFLINE_LANGUAGES"):script.index("(() => {")]
        runtime += "const productionLocaleText=localeText;localeText=(en,pt=en,code=lang,context=null)=>productionLocaleText(en,pt,code,context);"
        translations = script[
            script.index("const texts =") : script.index("function send(")
        ]
        helper = script[
            script.index("function updateClearanceLabels()") : script.index(
                "function translate()"
            )
        ]
        hud = script[
            script.index("function updateHud(") : script.index("function render()")
        ]
        setup = """
        let lang='pt';const p={style:'clamshell_pip',fit_clearance:.2,pip_clearance:.35,wall_thickness:2.4,floor_thickness:2.4};
        const gap={dataset:{}},hudLabel={},hudValue={};
        const nodes={'hud-clearance':hudValue};const $=id=>nodes[id]||(nodes[id]={classList:{toggle(){}}});
        const document={querySelector:selector=>selector.includes('data-slider')?gap:hudLabel};
        const meshParams=p,INITIAL={},meshes=[{maxOverhang:0}],bounds={size:[120,140,17.3]};
        function currentPrinter(){return {bed_x:220,bed_y:220,max_z:250}}
        """
        checks = """
        updateClearanceLabels();
        if(gap.textContent!=='Folga entre metades Z'||hudLabel.textContent!=='Folga da dobradiça'||hudValue.textContent!=='0.35 mm')throw Error('PIP clearances confused');
        updateHud(bounds);if(hudValue.textContent!=='0.35 mm')throw Error('render overwrites hinge clearance with half gap');
        lang='en';updateClearanceLabels();
        if(gap.textContent!=='Gap between halves Z'||hudLabel.textContent!=='Hinge clearance')throw Error('English PIP clearance labels incorrect');
        p.style='rugged_box';updateClearanceLabels();
        if(gap.textContent!=='Joint clearance'||hudLabel.textContent!=='Pivot clearance'||hudValue.textContent!=='0.20 mm')throw Error('SnapLock pivot clearance not explained');
        updateHud(bounds);if(hudValue.textContent!=='0.20 mm')throw Error('render did not restore legacy fit clearance');
        lang='pt';updateClearanceLabels();
        if(gap.textContent!=='Folga nos encaixes'||hudLabel.textContent!=='Folga dos pivôs')throw Error('Portuguese SnapLock pivot labels incorrect');
        p.style='lip_snap';updateClearanceLabels();
        if(gap.textContent!=='Folga por lado'||hudLabel.textContent!=='Folga por lado')throw Error('Original locating gap label not restored');
        """
        result = subprocess.run(
            ["node"],
            input=runtime + setup + translations + helper + hud + checks,
            text=True, encoding="utf-8",
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
