"""Exercise the real viewer upload/wire lifecycle without a browser or GPU."""

from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.studio_ui import get_studio_html


class ScriptParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.inside = False
        self.scripts = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.inside = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.scripts.append(data)


@unittest.skipUnless(
    shutil.which("node"), "Node.js is needed for viewer buffer verification"
)
class ViewerBufferLifecycleTests(unittest.TestCase):
    def test_exact_sharing_wire_order_and_complete_release(self):
        source = "\n".join(ScriptParser(get_studio_html("page", {})).scripts)
        harness = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
// Extract complete production blocks, ignoring braces inside comments/strings.
// Geometry, uploads, equality checks and wire edges below run their actual code.
function block(marker) {
  const start = source.indexOf(marker);
  assert(start >= 0, 'Missing viewer boundary: ' + marker);
  const open = source.indexOf('{', start);
  let depth = 1, i = open + 1, quote = null, line = false, comment = false;
  for (; depth && i < source.length; i++) {
    const c = source[i], next = source[i + 1];
    if (line) { if (c === '\n') line = false; continue; }
    if (comment) {
      if (c === '*' && next === '/') { comment = false; i++; }
      continue;
    }
    if (quote) {
      if (c === '\\') { i++; continue; }
      if (c === quote) quote = null;
      continue;
    }
    if (c === '/' && next === '/') { line = true; i++; continue; }
    if (c === '/' && next === '*') { comment = true; i++; continue; }
    if (c === '"' || c === "'" || c === '`') { quote = c; continue; }
    if (c === '{') depth++;
    if (c === '}') depth--;
  }
  assert.equal(depth, 0, 'Unterminated viewer block: ' + marker);
  return source.slice(start, i);
}
function fakeGL() {
  let serial = 0, currentVAO = null, arrayBuffer = null;
  const live = new Map(), vaos = new Set(), draws = [];
  return {
    ARRAY_BUFFER: 1, ELEMENT_ARRAY_BUFFER: 2, STATIC_DRAW: 3,
    FLOAT: 4, UNSIGNED_INT: 5, LINES: 6, BLEND: 7,
    SRC_ALPHA: 8, ONE_MINUS_SRC_ALPHA: 9,
    live, vaos, draws,
    createBuffer() { const b = {id: ++serial}; live.set(b, null); return b; },
    bindBuffer(target, b) {
      if (b) assert(live.has(b), 'Binding a deleted buffer');
      if (target === this.ARRAY_BUFFER) arrayBuffer = b;
      else { assert(currentVAO); currentVAO.element = b; }
    },
    bufferData(target, data) {
      const b = target === this.ARRAY_BUFFER ? arrayBuffer : currentVAO.element;
      assert(live.has(b)); live.set(b, data.slice());
    },
    deleteBuffer(b) {
      assert(live.has(b), 'Double deletion'); live.delete(b);
      if (arrayBuffer === b) arrayBuffer = null;
      for (const vao of vaos) {
        if (vao.element === b) vao.element = null;
        for (const [loc, attr] of vao.attributes)
          if (attr.buffer === b) vao.attributes.delete(loc);
      }
    },
    createVertexArray() {
      const v = {id: ++serial, attributes: new Map(), element: null};
      vaos.add(v); return v;
    },
    bindVertexArray(v) { if (v) assert(vaos.has(v)); currentVAO = v; },
    deleteVertexArray(v) {
      assert(vaos.delete(v), 'Double VAO deletion');
      if (currentVAO === v) currentVAO = null;
    },
    vertexAttribPointer(loc, size) {
      assert(currentVAO && live.has(arrayBuffer));
      currentVAO.attributes.set(loc, {buffer: arrayBuffer, size});
    },
    drawElements(mode, count) {
      assert(currentVAO && live.has(currentVAO.element));
      assert(count * 4 <= live.get(currentVAO.element).byteLength);
      for (const loc of [0, 1, 2])
        assert(live.has(currentVAO.attributes.get(loc).buffer));
      draws.push({mode, count, indices: live.get(currentVAO.element).slice()});
    },
    enableVertexAttribArray() {}, useProgram() {}, uniformMatrix4fv() {},
    uniform4fv() {}, enable() {}, blendFunc() {}, disable() {},
  };
}
const gl = fakeGL();
const context = vm.createContext({
  Float32Array, Uint32Array, Uint8Array, Math, Set, Infinity, gl,
  atob: value => Buffer.from(value, 'base64').toString('binary'),
});
const wireCode = block('if (wire && clipMode === 0)');
const functions = ['function decode(', 'function loadMeshes(',
  'function releaseWireBuffers('].map(block).join('\n');
const wireHandler = block('$("btn-vp-wire").onclick =');
vm.runInContext(`
let meshes = [], zoom = 1, wire = false, playing = false;
const INITIAL = {}, meshParams = {style:'rugged_box', floor_thickness:2.5, height_z:35};
const elements = {open:{}, play:{}, 'btn-vp-wire':{}};
function $(id) { return elements[id] || {}; }
function configureOpening() {} function viewButtons() {}
function mult() { return []; } function uniformLocation() { return null; }
const lineProg = {};
${functions}
function renderWire() {
  const clipMode = 0, cam = {mvp:[]};
  for (const m of meshes) {
    const model = [];
    gl.bindVertexArray(m.vao);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.ib);
    ${wireCode}
  }
}
function render() { if (wire) renderWire(); }
${wireHandler};
globalThis.api = {load:loadMeshes, toggle:elements['btn-vp-wire'].onclick,
  scene:()=>meshes};
`, context);
const api = context.api;
const b64 = a => Buffer.from(a.buffer, a.byteOffset, a.byteLength).toString('base64');
function item(part, positions, indices = [0,1,2]) {
  return {part, name:part, vertices:b64(new Float32Array(positions)),
    triangles:b64(new Uint32Array(indices)), volume_cm3:1, triangle_count:indices.length/3};
}
function data(mesh, loc) {
  const b = mesh.vao.attributes.get(loc).buffer;
  return gl.live.get(b);
}
function assertOwnership(scene) {
  const owned = new Set();
  for (const m of scene) {
    for (const b of [m.pb, m.nb, m.rb, m.ib, m.wireBuffer]) if (b) owned.add(b);
    assert.equal(m.vao.attributes.get(0).buffer, m.pb);
    assert.equal(m.vao.attributes.get(1).buffer, m.nb);
    assert.equal(m.vao.attributes.get(2).buffer, m.rb);
    for (const transport of ['vertices','triangles','normals'])
      assert.equal(m[transport], undefined, 'Transport/CPU normal retained');
  }
  assert.equal(gl.live.size, owned.size, 'Orphan GPU buffer');
  for (const b of owned) assert(gl.live.has(b));
  assert.equal(gl.vaos.size, scene.length, 'Orphan VAO');
}
const triangle = (x, z=1) => [x,0,0, x,1,0, x,0,z];
const fixtures = [
  item('a',triangle(-1)), item('b',triangle(1)),
  item('c',triangle(2,-1)), item('d',triangle(-1),[0,2,1]),
];
for (let cycle=0; cycle<3; cycle++) {
  api.load(fixtures,false);
  const [a,b,c,d] = api.scene();
  assertOwnership(api.scene());
  assert.equal(a.nb,b.nb); assert.equal(c.nb,d.nb); assert.notEqual(a.nb,c.nb);
  assert.equal(a.ib,b.ib); assert.equal(a.ib,c.ib); assert.notEqual(a.ib,d.ib);
  assert.equal(a.indices,b.indices); assert.equal(a.indices,c.indices);
  assert.notEqual(a.indices,d.indices);
  assert.notEqual(a.pb,b.pb); assert.notEqual(a.rb,b.rb);
  assert.notEqual(a.positions.buffer,b.positions.buffer);
  assert.deepEqual([...data(a,0)],triangle(-1));
  assert.deepEqual([...data(b,0)],triangle(1));
  assert.notDeepEqual([...data(a,2)],[...data(b,2)], 'Roles must remain individual');
  const solidCount=gl.live.size;
  gl.draws.length=0;
  api.toggle();
  assertOwnership(api.scene());
  assert.equal(a.wireBuffer,b.wireBuffer); assert.equal(a.wireBuffer,c.wireBuffer);
  assert.notEqual(a.wireBuffer,d.wireBuffer);
  assert.equal(gl.live.size,solidCount+2);
  assert.deepEqual([...gl.draws[0].indices],[0,1,1,2,2,0]);
  assert.deepEqual([...gl.draws[3].indices],[0,2,2,1,1,0]);
  assert(gl.draws.every(draw=>draw.mode===gl.LINES && draw.count===6));
  api.toggle();
  assert.equal(gl.live.size,solidCount);
  assert(api.scene().every(m=>m.wireBuffer===null && m.wireCount===0));
  assertOwnership(api.scene());
  // Shared wires also need single deletion when replaced while still enabled.
  api.toggle(); api.load(fixtures,false); api.toggle();
  assertOwnership(api.scene());

  // Actual accumulation underflows a negative normal X component to -0.
  // Both normal streams otherwise have the same words; numeric equality is
  // insufficient. This fixture must keep their normal buffers separate.
  const tiny = 2 ** -149;
  api.load([
    item('negative-zero',[0,0,0, 1,.5,0, 0,1,-tiny]),
    item('positive-zero',[0,0,0, 1,-.5,0, 0,1,-tiny]),
  ],false);
  const [negative,positive]=api.scene();
  const n=new Uint32Array(data(negative,1).buffer);
  const p=new Uint32Array(data(positive,1).buffer);
  assert.equal(n[0],0x80000000); assert.equal(p[0],0);
  assert.equal(n[1],p[1]); assert.equal(n[2],p[2]);
  assert.notEqual(negative.nb,positive.nb, '+0 and -0 are different bits');
  assert.equal(negative.ib,positive.ib);
  assertOwnership(api.scene());

  // One different index word with equal length must not alias either CPU or
  // GPU index storage. Both triangles are nondegenerate independent fixtures.
  const quad=[0,0,0, 0,1,0, 0,0,1, 0,1,1];
  api.load([item('first',quad),item('one-word',quad,[0,1,3])],false);
  const [first,changed]=api.scene();
  assert.notEqual(first.ib,changed.ib);
  assert.notEqual(first.indices,changed.indices);
  assert.deepEqual([...first.indices],[0,1,2]);
  assert.deepEqual([...changed.indices],[0,1,3]);
  assertOwnership(api.scene());
  // Replace a live wired scene, so shared wire buffers also traverse cleanup.
  api.toggle(); api.load(fixtures,false); api.toggle();
  assertOwnership(api.scene());
}
api.load([],false);
assert.equal(gl.live.size,0); assert.equal(gl.vaos.size,0);
console.log('Exact viewer sharing, wire order and three scene cycles: PASS');
"""
        result = subprocess.run(
            [shutil.which("node")],
            input="const source = " + json.dumps(source) + ";\n" + harness,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
