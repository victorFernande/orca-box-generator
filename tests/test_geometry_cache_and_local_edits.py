"""Canonical mesh reuse and stale-response regressions for Box Studio."""

import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio import plugin_main as bridge
from box_studio.mesh_generator import MeshData, np, topology_report
from box_studio.presets_catalog import BUILTIN_PRESETS, generate_random_printable_params
from box_studio.schema import normalize_params, validate_params
from box_studio.studio_ui import get_studio_html


def tetrahedron(part="base"):
    vertices = np.array([[0, 0, 2], [3, 0, 2], [0, 3, 2], [0, 0, 5]], dtype=np.float32)
    triangles = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]], dtype=np.int32)
    corners = vertices[triangles]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    lower, upper = vertices.min(axis=0), vertices.max(axis=0)
    return MeshData(
        vertices,
        triangles,
        normals,
        dict(min=lower.tolist(), max=upper.tolist(), size=(upper - lower).tolist()),
        0.0045,
        part,
        0.01,
    )


class CanonicalCacheTests(unittest.TestCase):
    def test_preview_export_preview_reuses_validated_canonical_parts_and_encoded_arrays(
        self,
    ):
        controller = bridge.BoxStudioController()
        params = normalize_params()
        with (
            patch.object(
                bridge,
                "generate_box_mesh",
                side_effect=lambda p, part, orientation: tetrahedron(part),
            ) as generate,
            patch.object(bridge, "topology_report", wraps=topology_report) as validate,
        ):
            first = controller._preview_payload(params)
            stored = copy.deepcopy(controller._geometry(params))
            exported = controller._geometry(
                params, assembled=False, target=params["export_target"]
            )
            again = controller._preview_payload(params)
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(validate.call_count, 2)
        self.assertIs(first["meshes"], again["meshes"])
        self.assertTrue(all(mesh.bounds_mm["min"][2] == 0 for _, mesh in exported))
        for (_, before), (_, after) in zip(stored, controller._geometry(params)):
            self.assertTrue(np.array_equal(before.vertices, after.vertices))
            self.assertTrue(np.array_equal(before.triangles, after.triangles))

    def test_metadata_and_language_keep_surfaces_but_localize_names(self):
        controller = bridge.BoxStudioController()
        with patch.object(
            bridge,
            "generate_box_mesh",
            side_effect=lambda p, part, orientation: tetrahedron(part),
        ) as generate:
            pt = controller._preview_payload(normalize_params())
            en = controller._preview_payload(
                normalize_params(dict(name="English", lang="en", theme="light"))
            )
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(pt["geometry_key"], en["geometry_key"])
        self.assertEqual(pt["meshes"][1]["name"], "Tampa")
        self.assertEqual(en["meshes"][1]["name"], "Lid")

    def test_lru_evicts_oldest_and_respects_byte_limit(self):
        controller = bridge.BoxStudioController()
        mesh = tetrahedron()
        size = controller._mesh_bytes(mesh)
        controller._mesh_cache_limit = size * 2
        for key in ("a", "b", "a", "c"):
            controller._cached_geometry(key, lambda: mesh)
        self.assertEqual(list(controller._mesh_cache), ["a", "c"])
        self.assertEqual(controller._mesh_cache_bytes, size * 2)
        controller._mesh_cache_limit = size - 1
        controller._mesh_cache.clear()
        controller._mesh_cache_bytes = 0
        controller._cached_geometry("oversized", lambda: mesh)
        self.assertEqual(controller._mesh_cache_bytes, 0)

    def test_concurrent_consumers_share_one_computation_and_failures_are_retryable(
        self,
    ):
        controller = bridge.BoxStudioController()
        entered, release = threading.Event(), threading.Event()
        calls, results = [], []
        mesh = tetrahedron()

        def compute():
            calls.append(1)
            entered.set()
            self.assertTrue(release.wait(5))
            return mesh

        threads = [
            threading.Thread(
                target=lambda: results.append(
                    controller._cached_geometry("same", compute)
                )
            )
            for _ in range(2)
        ]
        threads[0].start()
        self.assertTrue(entered.wait(5))
        threads[1].start()
        release.set()
        for thread in threads:
            thread.join(5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(calls, [1])
        self.assertEqual(len(results), 2)
        self.assertIs(results[0], results[1])
        with self.assertRaisesRegex(ValueError, "test failure"):
            controller._cached_geometry(
                "retry", lambda: (_ for _ in ()).throw(ValueError("test failure"))
            )
        self.assertIs(controller._cached_geometry("retry", lambda: mesh), mesh)
        self.assertFalse(controller._inflight_geometry)

    def test_seventeen_presets_keep_the_originals_and_add_storage_and_clamshell_styles(
        self,
    ):
        self.assertEqual(len(BUILTIN_PRESETS), 17)
        self.assertEqual(
            [item["id"] for item in BUILTIN_PRESETS[:12]],
            [
                "everyday",
                "esp32",
                "raspberry_pi",
                "arduino",
                "mini_lip",
                "sensor",
                "tool_rugged",
                "rugged_pip",
                "pencil",
                "parts",
                "gasket",
                "vented",
            ],
        )
        self.assertEqual(
            [item["params"]["style"] for item in BUILTIN_PRESETS[12:]],
            [
                "open_bin",
                "snap_latch",
                "stackable_bin",
                "clamshell_pip",
                "clamshell_pip",
            ],
        )
        for item in BUILTIN_PRESETS[12:]:
            self.assertEqual(validate_params(item["params"]), [])

    def test_stackable_surprise_preserves_the_mating_family(self):
        original = next(
            item["params"]
            for item in BUILTIN_PRESETS
            if item["id"] == "stackable_parts_bin"
        )
        self.assertEqual(original["style"], "stackable_bin")
        family = (
            "width_x",
            "depth_y",
            "corner_radius",
            "wall_thickness",
            "stack_foot_height",
            "stack_clearance",
        )
        heights = set()
        for seed in range(10):
            candidate = generate_random_printable_params(original, seed)
            self.assertEqual(candidate["style"], "stackable_bin")
            self.assertEqual(validate_params(candidate), [])
            for key in family:
                self.assertEqual(candidate[key], original[key], key)
            heights.add(candidate["height_z"])
        self.assertGreater(len(heights), 1)
        # Force the fallback branch; it must also retain the same mating family.
        with patch("random.Random.uniform", return_value=999):
            candidate = generate_random_printable_params(original, 11)
        for key in family:
            self.assertEqual(candidate[key], original[key], key)

    def test_stackable_preview_and_print_share_one_real_base(self):
        params = next(
            item["params"]
            for item in BUILTIN_PRESETS
            if item["id"] == "stackable_parts_bin"
        )
        controller = bridge.BoxStudioController()
        with (
            patch.object(
                bridge, "generate_box_mesh", wraps=bridge.generate_box_mesh
            ) as generate,
            patch.object(bridge, "topology_report", wraps=topology_report) as validate,
        ):
            preview = controller._preview_payload(params)
            printed = controller._geometry(params, assembled=False, target="full_suite")
            again = controller._preview_payload(params)
        self.assertEqual([item["part"] for item in preview["meshes"]], ["base"])
        self.assertEqual([mesh.part for _, mesh in printed], ["base"])
        self.assertEqual(printed[0][1].bounds_mm["min"][2], 0)
        self.assertEqual(generate.call_count, 1)
        self.assertEqual(validate.call_count, 1)
        self.assertIs(preview["meshes"], again["meshes"])


@unittest.skipUnless(shutil.which("node"), "Node is needed for embedded UI regressions")
class LocalEditTests(unittest.TestCase):
    def run_js(self, script):
        result = subprocess.run(
            ["node"], input=script, text=True, encoding="utf-8", capture_output=True, timeout=20
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_print_help_tracks_style_and_language_without_unavailable_kit_advice(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        translations = script[
            script.index("const texts =") : script.index("function send(")
        ]
        help_script = script[
            script.index("function updatePrintHelp()") : script.index(
                "function translate()"
            )
        ]
        setup = "let lang='pt',p={style:'open_bin'};const label={};const document={querySelector:()=>label};"
        checks = """
        for(lang of ['pt','en']) {
          for(p.style of ['open_bin','stackable_bin','snap_latch','clamshell_pip']) {
            updatePrintHelp();
            if(/kit/i.test(label.textContent))throw Error('unavailable kit advice: '+p.style);
            if(p.style==='stackable_bin'&&!/pé|foot/.test(label.textContent))throw Error('stacking foot omitted');
            if(p.style==='snap_latch'&&!/duas travas|two latches/.test(label.textContent))throw Error('latches omitted');
            if(p.style==='clamshell_pip'&&(!/180°/.test(label.textContent)||/kit/i.test(label.textContent)))throw Error('clamshell open assembly advice missing');
          }
          p.style='lip_snap';updatePrintHelp();
          if(!/kit/i.test(label.textContent))throw Error('original fit kit advice missing');
        }
        """
        self.run_js(setup + translations + help_script + checks)

    def test_uncommitted_gesture_invalidates_old_results_without_sending_intermediate_geometry(
        self,
    ):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        request = script[
            script.index("function requestPreview(") : script.index("function change(")
        ]
        receive = script[
            script.index("function receive(") : script.index(
                'window.addEventListener("message", receive)'
            )
        ]
        setup = """
        let serial=1,latest=1,timer=null,localDirty=false,p={width_x:90},lang='pt',theme='dark',meshParams={},meshRevisionKey=null;
        const INITIAL={},sent=[],clone=o=>JSON.parse(JSON.stringify(o)),tr=x=>x;
        function clearTimeout(){}function setTimeout(fn){return fn}function status(){}
        function send(m){sent.push(m);return true}function sync(){}function presets(){}
        function updatePrinter(){}function resolveHostTheme(){}function busy(){}
        function loadMeshes(){throw Error('Old geometry replaced the current viewport')}
        """
        checks = """
        requestPreview(false);p.width_x=120;
        if(latest!==2||!localDirty||sent.length)throw Error('gesture did not invalidate old response');
        receive({type:'preview_result',ok:true,request_id:1,params:{width_x:90}});
        receive({type:'design_changed',params:{width_x:80}});
        if(p.width_x!==120)throw Error('in-flight response erased gesture');
        requestPreview();timer();
        if(sent.length!==1||sent[0].params.width_x!==120||sent[0].request_id!==3)throw Error('final gesture was not committed');
        """
        self.run_js(setup + request + receive + checks)

    def test_pending_style_change_does_not_change_displayed_lid_animation(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        start = re.search(r"const I\s*=", script).start()
        end = script.index("function decode", start)
        setup = """
        const p={style:'rugged_box',height_z:90,depth_y:120};
        const meshParams={style:'snap_latch',height_z:40,depth_y:80};
        const latch={pivot:{x:0,y:-45,z:20},release_angle:90,release_fraction:.35,lid_lift_mm:50};
        const INITIAL={preview_mode:'assembly',hinge:{y:65,z:86},latch_motion:{clip_left:latch,clip_right:latch}};
        const $=()=>({value:'100'}),meshes=[];let zoom=1,yaw=0,pitch=.5;
        """
        check = """
        const m=partTransform('lid',1);
        if(m[14]!==50||m[5]!==1)throw Error('draft rugged hinge applied to removable displayed lid');
        """
        self.run_js(setup + script[start:end] + check)

    def test_style_roundtrip_restores_lid_and_fit_controls(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        sync = script[
            script.index("function sync()") : script.index("function requestPreview(")
        ]
        help_script = script[
            script.index("function updatePrintHelp()") : script.index(
                "function translate()"
            )
        ]
        setup = """
        let p={style:'open_bin',name:'Box',dividers_x:[],dividers_y:[]},lang='pt';
        const rows={},nodes={target:{options:['base_and_lid','base_only','lid_only','gasket','fit_test_kit','full_suite'].map(value=>({value}))}};
        const $=id=>nodes[id]||(nodes[id]={style:{},options:[],closest(){return this.container||(this.container={style:{}})}});
        const document={querySelector:selector=>rows[selector]||(rows[selector]={style:{},dataset:{},querySelector(){return this.label||(this.label={dataset:{}})}}),querySelectorAll:()=>[]};
        const tr=x=>x;function syncPresetSelection(){}function features(){}
        const INITIAL={},meshParams={style:'open_bin'},localDirty=false;
        function drawPlan(){}function buttons(){}function render(){}
        """
        checks = """
        const row=k=>rows['[data-slider="'+k+'"]'].style.display;
        sync();if(row('lid_height')!=='none'||row('fit_clearance')!=='none')throw Error('bin shows lid controls');
        if(rows['[data-i18n="printHelp"]'].textContent!=='printHelpOpen')throw Error('open bin print help mentions lid or kit');
        p.style='snap_latch';sync();
        if(rows['[data-i18n="printHelp"]'].textContent!=='printHelpLatch')throw Error('snap print help omits separate latches');
        for(const k of ['lid_height','fit_clearance'])if(row(k)!=='grid')throw Error('control not restored: '+k);
        if(row('lip_depth')!=='none')throw Error('snap shows duplicate skirt controls');
        if($('snap-latch-options').hidden||!$('open-bin-handles').hidden)throw Error('incorrect style panel');
        p.style='sliding_lid';sync();if(row('lid_height')!=='none'||row('fit_clearance')!=='grid')throw Error('sliding controls incorrect');
        p.style='stackable_bin';sync();
        if(rows['[data-i18n="printHelp"]'].textContent!=='printHelpStack')throw Error('stack print help omits foot');
        if(rows['[data-slider="height_z"] .ctrl-label'].textContent!=='Altura total Z')throw Error('stack height omits foot');
        lang='en';sync();if(rows['[data-slider="height_z"] .ctrl-label'].textContent!=='Total height Z')throw Error('stack height not translated');
        if($('stackable-bin-options').hidden||!$('open-bin-handles').hidden||!$('snap-latch-options').hidden)throw Error('incorrect stacking controls');
        if(row('lid_height')!=='none'||row('lip_depth')!=='none'||row('fit_clearance')!=='none'||!$('open').disabled||!$('play').disabled)throw Error('stackable bin offers lid controls');
        for(const option of $('target').options)if(['lid_only','gasket','fit_test_kit'].includes(option.value)&&!option.disabled)throw Error('unsupported stackable target enabled');
        p.style='clamshell_pip';p.height_z=14;p.fit_clearance=.2;sync();
        if($('clamshell-pip-options').hidden||row('lid_height')!=='none'||row('lip_depth')!=='none'||row('fit_clearance')!=='grid')throw Error('clamshell controls incorrect');
        if(rows['[data-slider="height_z"] .ctrl-label'].textContent!=='Height of each half Z')throw Error('clamshell half-height not explained');
        if(!$('addPost').disabled||!$('addPort').disabled)throw Error('unsupported features enabled');
        for(const option of $('target').options)if(!['base_and_lid','full_suite'].includes(option.value)&&!option.disabled)throw Error('clamshell can export detached halves');
        p.gasket_enabled=true;p.standoffs=[{}];sync();
        if($('gasket_enabled').closest().style.display!=='flex'||$('clamshell-feature-warning').hidden)throw Error('incompatible resources cannot be removed');
        p.gasket_enabled=false;p.standoffs=[];sync();
        if($('gasket_enabled').closest().style.display!=='none'||!$('clamshell-feature-warning').hidden)throw Error('unsupported resource controls remain');
        p.style='lip_snap';sync();if(row('lid_height')!=='grid'||row('snap_retention')!=='grid')throw Error('lip controls not restored');
        if(rows['[data-i18n="printHelp"]'].textContent!=='printHelp')throw Error('original print help not restored');
        if($('open').disabled||$('play').disabled||$('target').options.some(option=>option.disabled))throw Error('lid controls not restored');
        INITIAL.preview_mode='calibration';sync();
        if(!$('open').disabled||!$('play').disabled)throw Error('sync reenabled kit opening animation');
        """
        self.run_js(setup + help_script + sync + checks)


if __name__ == "__main__":
    unittest.main()
