"""Canonical workspace behavior: seeded designs, bridge routing and scene framing."""

import copy
import base64
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.schema import normalize_params, validate_params
from box_studio.presets_catalog import generate_random_printable_params
from box_studio.plugin_main import BoxStudioController
from box_studio import plugin_main as bridge
from box_studio.mesh_generator import MeshData, np
from box_studio.studio_ui import get_studio_html


class StudioInteractionTests(unittest.TestCase):
    def test_preview_honors_every_export_target_and_cache_identity(self):
        expected = {
            "base_and_lid": ["base", "lid"],
            "base_only": ["base"],
            "lid_only": ["lid"],
            "gasket": ["gasket"],
            "fit_test_kit": ["base", "lid", "snap_sample"],
            "full_suite": ["base", "lid"],
        }
        fixtures = {}

        def mesh(part, width):
            vertices = np.array(
                [[-2, 5, -0.5], [-2 + width, 5, -0.5], [-2, 8, -0.5], [-2, 5, 2.5]],
                dtype=np.float32,
            )
            triangles = np.array(
                [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]], dtype=np.int32
            )
            t = vertices[triangles]
            normals = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
            normals /= np.linalg.norm(normals, axis=1)[:, None]
            lower, upper = vertices.min(axis=0), vertices.max(axis=0)
            return MeshData(
                vertices,
                triangles,
                normals,
                {
                    "min": lower.tolist(),
                    "max": upper.tolist(),
                    "size": (upper - lower).tolist(),
                },
                0.1,
                part,
                0.01,
            )

        for target, parts in expected.items():
            fixtures[target] = [
                (part, mesh(part, index + 2)) for index, part in enumerate(parts)
            ]

        def collect(params, target, lang, assembled, mesh_factory=None):
            self.assertTrue(assembled)
            return fixtures[target]

        controller = BoxStudioController()
        with patch.object(
            bridge, "collect_target_meshes", side_effect=collect
        ) as collector:
            for target, parts in expected.items():
                params = normalize_params(
                    {"export_target": target, "gasket_enabled": target == "gasket"}
                )
                payload = controller._preview_payload(params)
                self.assertEqual([m["part"] for m in payload["meshes"]], parts)
                self.assertEqual(
                    payload["preview_mode"],
                    "calibration" if target == "fit_test_kit" else "assembly",
                )
                before = collector.call_count
                controller._preview_payload(params)
                self.assertEqual(
                    collector.call_count,
                    before,
                    "same target should use its cache entry",
                )
                for supplied, (_, original) in zip(payload["meshes"], fixtures[target]):
                    actual = np.frombuffer(
                        base64.b64decode(supplied["vertices"]), dtype="<f4"
                    ).reshape(-1, 3)
                    self.assertTrue(
                        np.array_equal(actual, original.vertices),
                        "preview layout must not rewrite manufacturing arrays",
                    )
                if target == "fit_test_kit":
                    previous_right = None
                    for item in payload["meshes"]:
                        offset = item["preview_offset"]
                        bounds = item["bounds"]
                        left = bounds["min"][0] + offset[0]
                        right = bounds["max"][0] + offset[0]
                        if previous_right is not None:
                            self.assertAlmostEqual(left - previous_right, 6)
                        previous_right = right
                        self.assertAlmostEqual(bounds["min"][2] + offset[2], 0)
        self.assertEqual(
            collector.call_count,
            len(expected),
            "changing export target must invalidate a different target's cached item set",
        )

    def test_gasket_preview_without_channel_reports_actionable_error(self):
        with self.assertRaisesRegex(ValueError, "canal TPU|TPU channel"):
            BoxStudioController()._preview_payload(
                normalize_params({"export_target": "gasket", "gasket_enabled": False})
            )

    @unittest.skipUnless(
        shutil.which("node"), "Node.js required for calibration transforms"
    )
    def test_calibration_offsets_disable_box_lid_motion(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S).group(1)
        start = re.search(r"const I\s*=", script).start()
        end = script.index("function decode", start)
        setup = "const meshes=[{part:'lid',preview_offset:[22,-5,1],bounds:{min:[-2,5,-1],max:[8,15,4]}}];const INITIAL={preview_mode:'calibration',hinge:{y:100,z:50}};const p={style:'rugged_box',width_x:90,depth_y:65,height_z:35};const $=()=>({value:'100'});let zoom=1,yaw=-.75,pitch=.68;"
        checks = "const closed=sceneBounds(0),open=sceneBounds(1);if(JSON.stringify(closed)!==JSON.stringify(open))throw Error('kit uses full-box hinge animation');if(JSON.stringify(closed.min)!=='[20,0,0]'||JSON.stringify(closed.max)!=='[30,10,5]')throw Error('actual calibration offsets ignored');if(!camera(.4).mvp.every(Number.isFinite))throw Error('invalid kit camera');"
        result = subprocess.run(
            [shutil.which("node"), "-e", setup + script[start:end] + checks],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(
        shutil.which("node"), "Node.js required for range control events"
    )
    def test_keyboard_range_change_keeps_the_previous_value_for_undo(self):
        html = get_studio_html()
        script = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
        block = re.search(
            r'document\.querySelectorAll\("\[data-param-range\]"\)\.forEach\(\(range\) => \{.*?\n\s*\}\);',
            script,
            re.S,
        ).group(0)
        setup = """
const p={width_x:90},saved=[],range={dataset:{paramRange:'width_x'},value:'90'},number={value:'90'};
const document={querySelectorAll:()=>[range],querySelector:()=>number};
function snapshot(){saved.push(p.width_x)}function drawPlan(){}function sync(){}function requestPreview(){}
"""
        check = """
range.value='91';range.oninput();range.onchange();
if(saved.length!==1||saved[0]!==90||p.width_x!==91)throw Error('keyboard undo lost previous value');
range.onpointerdown();range.value='95';range.oninput();range.value='96';range.oninput();range.onchange();
if(saved.length!==2||saved[1]!==91||p.width_x!==96)throw Error('pointer gesture generated wrong undo snapshot');
"""
        result = subprocess.run(
            [shutil.which("node"), "-e", setup + block + check],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_seeded_surprise_preserves_requested_features_and_style(self):
        original = normalize_params(
            {
                "style": "screw_corner",
                "standoffs": [{"x": -15, "y": 5}],
                "cutouts": [{"kind": "usb_c", "face": "front", "z": 12}],
                "dividers_x": [15],
            }
        )
        before = copy.deepcopy(original)
        for seed in range(20):
            result = generate_random_printable_params(
                original, seed, {"bed_x": 220, "bed_y": 220, "max_z": 250}
            )
            self.assertEqual(
                result,
                generate_random_printable_params(
                    original, seed, {"bed_x": 220, "bed_y": 220, "max_z": 250}
                ),
            )
            self.assertEqual(result["style"], original["style"])
            for key in ("standoffs", "cutouts", "dividers_x", "dividers_y"):
                self.assertEqual(result[key], original[key])
            self.assertEqual(validate_params(result), [])
            self.assertLessEqual(result["width_x"], 212)
            self.assertLessEqual(result["depth_y"], 212)
        self.assertEqual(original, before)

    def test_surprise_rejects_collisions_and_preserves_features_in_fallback(self):
        with self.assertRaises(ValueError):
            generate_random_printable_params({"standoffs": [{"x": 100}]}, 3)
        original = normalize_params(
            {"cutouts": [{"kind": "usb_c", "face": "front", "z": 12}]}
        )
        with patch("random.Random.uniform", return_value=350):
            result = generate_random_printable_params(
                original, 8, {"bed_x": 220, "bed_y": 220, "max_z": 250}
            )
        self.assertEqual(result["cutouts"], original["cutouts"])
        self.assertEqual(result["style"], original["style"])
        self.assertEqual(validate_params(result), [])

    def test_randomize_bridge_updates_shared_design_and_returns_seed(self):
        controller = BoxStudioController()
        page = []
        dock = []
        controller.handle_message({"type": "init"}, page.append, "page")
        controller.handle_message({"type": "init"}, dock.append, "dock")
        page.clear()
        dock.clear()
        controller.handle_message(
            {
                "type": "randomize",
                "seed": 42,
                "params": normalize_params({"style": "sliding_lid"}),
            },
            page.append,
            "page",
        )
        self.assertEqual(page[-1]["type"], "randomize_result")
        self.assertEqual(page[-1]["seed"], 42)
        self.assertEqual(page[-1]["params"], controller.current_params())
        self.assertEqual(page[-1]["params"]["style"], "sliding_lid")
        self.assertEqual(dock[-1]["type"], "design_changed")

    @unittest.skipUnless(
        shutil.which("node"),
        "Node.js required to exercise the actual JavaScript camera",
    )
    def test_camera_fits_all_transformed_real_mesh_bounds(self):
        html = get_studio_html()
        script = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
        start = re.search(r"const I\s*=", script).start()
        end = script.index("function decode", start)
        functions = script[start:end]
        fixture = [
            {"part": "base", "bounds": {"min": [-120, 35, 2], "max": [-80, 60, 20]}},
            {"part": "lid", "bounds": {"min": [10, -50, 40], "max": [30, -30, 50]}},
            {
                "part": "calibration",
                "bounds": {"min": [250, 12, -5], "max": [275, 30, 15]},
            },
        ]
        checks = r"""
for(const aspect of [.38,1,2.4]){
 const b=sceneBounds();if(b.min[0]!==-120||b.max[0]!==275||b.min[2]!==-5||b.max[2]!==100)throw Error('missing transformed/calibration bounds');
 const c=camera(aspect),m=c.mvp;
 for(const mesh of meshes){const t=partTransform(mesh.part);for(const x of [mesh.bounds.min[0],mesh.bounds.max[0]])for(const y of [mesh.bounds.min[1],mesh.bounds.max[1]])for(const z of [mesh.bounds.min[2],mesh.bounds.max[2]]){
  const q=transformPoint(t,x,y,z),w=m[3]*q[0]+m[7]*q[1]+m[11]*q[2]+m[15],xx=(m[0]*q[0]+m[4]*q[1]+m[8]*q[2]+m[12])/w,yy=(m[1]*q[0]+m[5]*q[1]+m[9]*q[2]+m[13])/w;
  if(w<=0||Math.abs(xx)>1||Math.abs(yy)>1)throw Error('camera clips actual model');
 }}
}
meshes.length=0;const emptyCamera=camera(1);if(!emptyCamera.mvp.every(Number.isFinite))throw Error('empty scene camera invalid');
console.log('camera framing PASS');"""
        program = (
            "const meshes="
            + json.dumps(fixture)
            + ";const p={style:'lip_snap',width_x:90,depth_y:65,height_z:35};const INITIAL={};const $=()=>({value:'100'});let zoom=1,yaw=-.75,pitch=.68;"
            + functions
            + checks
        )
        result = subprocess.run(
            [shutil.which("node"), "-e", program],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("camera framing PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
