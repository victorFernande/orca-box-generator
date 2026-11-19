"""Actual preview transforms keep both SnapLock latches attached to the lid."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.schema import normalize_params
from box_studio.rugged_geometry import rugged_hinge_geometry, rugged_latch_geometry
from box_studio.studio_ui import get_studio_html
from box_studio.plugin_main import BoxStudioController


class RuggedPreviewBridgeTests(unittest.TestCase):
    def test_metadata_belongs_to_the_delivered_design_not_the_current_editor(self):
        controller = BoxStudioController()
        rendered = normalize_params({"style": "rugged_box"})
        controller.set_current_params({**rendered, "width_x": 180, "height_z": 45})
        with patch.object(controller, "_geometry", return_value=[]):
            payload = controller._preview_payload(rendered)
        self.assertEqual(payload["hinge"], rugged_hinge_geometry(rendered))
        self.assertEqual(payload["params"], rendered)
        for part in ("clip_left", "clip_right"):
            self.assertEqual(payload["latch_motion"][part], rugged_latch_geometry(rendered, part))
            self.assertEqual(payload["latch_motion"][part]["attachment"], "lid")


@unittest.skipUnless(shutil.which("node"), "Node required for production WebGL transforms")
class RuggedPreviewUiTests(unittest.TestCase):
    def run_js(self, checks):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        start = re.search(r"const I\s*=", script).start()
        end = script.index("function decode", start)
        params = normalize_params({"style": "rugged_box"})
        initial = {"hinge": rugged_hinge_geometry(params), "latch_motion": {
            part: rugged_latch_geometry(params, part) for part in ("clip_left", "clip_right")}}
        setup = ("const assert=require('node:assert/strict');const p=" + json.dumps(params)
                 + ";let meshParams=p;const INITIAL=" + json.dumps(initial)
                 + ";const $=()=>({value:'0'});const meshes=[];let zoom=1,yaw=0,pitch=.5;"
                 + "const near=(a,b)=>assert.ok(Math.abs(a-b)<5e-5,JSON.stringify({a,b}));")
        result = subprocess.run([shutil.which("node")], input=setup + script[start:end] + checks,
                                text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_101_poses_keep_latches_on_the_moving_lid(self):
        self.run_js("""
        validateRuggedMotion(p,INITIAL.hinge,INITIAL.latch_motion);
        for(let step=0;step<=100;step++) {
          const phase=step/100,lid=partTransform('lid',phase),lidAngle=-Math.PI*Math.max(0,(phase-.25)/.75);
          near(Math.sin(Math.atan2(lid[6],lid[5])-lidAngle),0);
          assert.deepEqual(Array.from(partTransform('base',phase)),Array.from(I()));
          if(step<=25)assert.deepEqual(Array.from(lid),Array.from(I()));
          for(const part of ['clip_left','clip_right']) {
            const m=partTransform(part,phase),v=INITIAL.latch_motion[part].pivot;
            const a=transformPoint(m,v.x,v.y,v.z),b=transformPoint(lid,v.x,v.y,v.z);
            a.forEach((value,i)=>near(value,b[i]));
            const expected=lidAngle-Math.PI/2*Math.min(phase/.25,1);
            near(Math.sin(Math.atan2(m[6],m[5])-expected),0);
            if(step===25){const tip=transformPoint(m,v.x,v.y,v.z-10);near(tip[1],v.y-10);near(tip[2],v.z);}
          }
        }
        """)

    def test_missing_stale_and_nonfinite_joint_snapshots_are_rejected(self):
        self.run_js("""
        for(const modify of [
          x=>delete x.latch_motion.clip_right,
          x=>x.latch_motion.clip_left.pivot.x+=1,
          x=>x.latch_motion.clip_right.pivot.z=NaN,
          x=>x.latch_motion.clip_left.attachment='base',
          x=>x.latch_motion.clip_left.release_angle=-90,
          x=>x.hinge.z-=4,
          x=>x.hinge.open_sign=1,
        ]) {
          const x=JSON.parse(JSON.stringify(INITIAL));modify(x);
          assert.throws(()=>validateRuggedMotion(p,x.hinge,x.latch_motion));
        }
        const resized={...p,width_x:180,height_z:45};
        assert.throws(()=>validateRuggedMotion(resized,INITIAL.hinge,INITIAL.latch_motion));
        """)


if __name__ == "__main__":
    unittest.main()
