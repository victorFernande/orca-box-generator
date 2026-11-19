"""The accelerated byte decoder and compatibility path preserve mesh arrays."""
import base64
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.studio_ui import get_studio_html


@unittest.skipUnless(shutil.which("node"), "Node required for embedded byte decoder")
class MeshDecodeTests(unittest.TestCase):
    def test_normal_bits_material_roles_and_overhang_match_the_original_viewer(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        start = script.index("const lo =", script.index("meshes = items.map"))
        block = script[start:script.index("const vao =", start)]
        fixture = Path(__file__).resolve().parent / "fixtures/viewer_surface_reference.json"
        cases = json.loads(fixture.read_text(encoding="utf-8"))["cases"]
        source = "const compute=(pos,tri,meshParams)=>{const norm=new Float32Array(pos.length),roles=new Float32Array(pos.length/3);" + block + "return {normal_bits:Array.from(new Uint32Array(norm.buffer)),roles:Array.from(roles),bounds:{min:lo,max:hi},maxOverhang};};"
        source += "const assert=require('node:assert/strict');const cases=" + json.dumps(cases) + ";"
        source += "for(const c of cases)assert.deepEqual(compute(new Float32Array(c.positions),new Uint32Array(c.indices),c.params),c.expected,c.name);"
        result = subprocess.run([shutil.which("node")], input=source, text=True,
                                encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fast_and_compatible_decoders_preserve_every_byte(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S)[1]
        source = script[script.index("function decode("):script.index("function loadMeshes(")]
        encoded = base64.b64encode(bytes(range(256)) * 16).decode("ascii")
        checks = """
        const assert=require('node:assert/strict'),input=Buffer.from(ENCODED,'base64');
        let called=0;
        for(const fast of [false,true]) {
          Uint8Array.fromBase64=fast?s=>{called++;return Uint8Array.from(Buffer.from(s,'base64'))}:undefined;
          for(const ctor of [Uint8Array,Uint32Array,Float32Array]) {
            const output=decode(ENCODED,ctor);
            assert.equal(output.constructor,ctor);
            assert.deepEqual(Buffer.from(output.buffer),input);
          }
          const empty=decode('',Float32Array);assert.equal(empty.length,0);
        }
        assert.equal(called,4);
        """.replace("ENCODED", repr(encoded))
        result = subprocess.run([shutil.which("node")], input=source + checks, text=True,
                                encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
