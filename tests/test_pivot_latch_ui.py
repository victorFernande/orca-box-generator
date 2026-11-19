"""The removable lid waits for both base-mounted pivot latches to release."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.studio_ui import get_studio_html
from box_studio import plugin_main as bridge
from box_studio.mesh_generator import latch_geometry, latch_open_transform, np
from box_studio.schema import normalize_params


class PivotLatchBridgeTests(unittest.TestCase):
    def test_motion_metadata_uses_the_same_design_snapshot_as_the_preview(self):
        controller = bridge.BoxStudioController()
        rendered = normalize_params(dict(style="snap_latch", width_x=110, height_z=40))
        controller.set_current_params(
            dict(style="snap_latch", width_x=150, height_z=60)
        )
        with patch.object(controller, "_geometry", return_value=[]):
            payload = controller._preview_payload(rendered)
        for part in ("clip_left", "clip_right"):
            self.assertEqual(
                payload["latch_motion"][part], latch_geometry(rendered, part)
            )
            self.assertNotEqual(
                payload["latch_motion"][part]["pivot"],
                latch_geometry(controller.current_params(), part)["pivot"],
            )
        self.assertEqual(payload["params"], rendered)


@unittest.skipUnless(
    shutil.which("node"), "Node required for the production pose functions"
)
class PivotLatchUiTests(unittest.TestCase):
    def run_js(self, checks, motion=None):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        start = re.search(r"const I\s*=", script).start()
        end = script.index("function decode", start)
        setup = """
        const p={style:'snap_latch'};let meshParams=p,openingStyle=null;
        const left={pivot:{x:-25,y:-44,z:25},release_angle:90,release_fraction:.35,lid_lift_mm:50};
        const right={...left,pivot:{x:25,y:-44,z:25}};
        const INITIAL={preview_mode:'assembly',latch_motion:{clip_left:left,clip_right:right}};
        const controls={open:{value:'25',max:'100'},openValue:{},'latch-motion-phase':{}};
        const $=id=>controls[id];const tr=key=>key,meshes=[];let zoom=1,yaw=0,pitch=.5;
        """
        if motion is not None:
            setup += "INITIAL.latch_motion=" + json.dumps(motion) + ";"
        result = subprocess.run(
            ["node"],
            input=setup + script[start:end] + checks,
            text=True, encoding="utf-8",
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_pivots_are_fixed_and_both_latches_release_before_the_lid_moves(self):
        self.run_js("""
        for(let i=0;i<=100;i++) {
          const phase=i/100,lid=partTransform('lid',phase);
          if(phase<=.35&&Math.abs(lid[14])>1e-7)throw Error('lid lifted before latch release');
          if(phase>.35&&!(lid[14]>0))throw Error('lid did not move after release');
          for(const [part,info] of Object.entries(INITIAL.latch_motion)) {
            const m=partTransform(part,phase),pivot=info.pivot;
            const q=transformPoint(m,pivot.x,pivot.y,pivot.z);
            if(Math.max(...q.map((value,k)=>Math.abs(value-[pivot.x,pivot.y,pivot.z][k])))>1e-5)throw Error('latch detached from base pivot');
            if(phase>=.35) {
              const full=partTransform(part,1);
              if(m.some((value,k)=>Math.abs(value-full[k])>1e-6))throw Error('latches changed pose while lid lifted');
            }
          }
        }
        for(const [part,info] of Object.entries(INITIAL.latch_motion)) {
          const v=info.pivot,q=transformPoint(partTransform(part,.35),v.x,v.y,v.z+20);
          if(Math.abs(q[1]-(v.y-20))>1e-5)throw Error('positive rotation does not release outwards');
        }
        """)

    def test_motion_is_not_replaced_by_the_old_clip_translation(self):
        self.run_js("""
        for(const part of ['clip_left','clip_right']) {
          const m=partTransform(part,.2);
          if(Math.abs(m[6])<.1)throw Error('clip only translates instead of pivoting');
        }
        let rejected=false;try{snapLatchTransform('lid',.5,null)}catch(error){rejected=true}
        if(!rejected)throw Error('missing motion silently assumed the old mechanism');
        """)

    def test_closed_initial_pose_and_phase_readout_preserve_pip_degrees(self):
        self.run_js("""
        configureOpening();
        if($('open').value!=='0'||$('open').max!=='100'||$('openValue').textContent!=='0%'||$('latch-motion-phase').textContent!=='latchesEngaged')throw Error('initial closed engagement pose incorrect');
        $('open').value='20';openingLabel();
        configureOpening();if($('open').value!=='20')throw Error('mesh refresh reset latch opening');
        if($('latch-motion-phase').textContent!=='releasingLatches')throw Error('release stage not explained');
        $('open').value='70';openingLabel();
        if($('latch-motion-phase').textContent!=='liftingLid')throw Error('lid stage not explained');
        meshParams={style:'clamshell_pip'};configureOpening();
        if($('open').value!=='180'||$('open').max!=='180'||$('openValue').textContent!=='180°')throw Error('PIP view changed');
        """)

    def test_clip_rotations_match_the_python_geometry_helper(self):
        params = normalize_params(
            dict(style="snap_latch", width_x=110, depth_y=80, height_z=40)
        )
        motion = {
            part: latch_geometry(params, part) for part in ("clip_left", "clip_right")
        }
        points = np.array([[-30, -45, 30], [30, -45, 45], [0, -48, 38]], dtype=float)
        phases = [0, 0.05, 0.15, 0.35, 0.5, 1]
        expected = {
            part: [
                latch_open_transform(
                    points,
                    params,
                    part,
                    min(phase / info["release_fraction"], 1) * info["release_angle"],
                ).tolist()
                for phase in phases
            ]
            for part, info in motion.items()
        }
        script = (
            "const points="
            + json.dumps(points.tolist())
            + ",phases="
            + json.dumps(phases)
            + ";const actual={};for(const part of ['clip_left','clip_right'])actual[part]=phases.map(phase=>points.map(q=>transformPoint(partTransform(part,phase),...q)));process.stdout.write(JSON.stringify(actual));"
        )
        actual = json.loads(self.run_js(script, motion))
        for part in motion:
            self.assertTrue(np.allclose(actual[part], expected[part], atol=6e-6), part)


if __name__ == "__main__":
    unittest.main()
