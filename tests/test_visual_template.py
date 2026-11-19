"""Frozen Vase visual contract; no sibling checkout or browser dependency in CI.

These declarations are the shared design primitives. Domain controls and copy may
change, while browser screenshots/computed styles remain a separate acceptance
check. The source hash records where the frozen fixture was measured.
"""
from __future__ import annotations

import copy
from html.parser import HTMLParser
import importlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
SCHEMA = importlib.import_module("box_studio.schema")
UI = importlib.import_module("box_studio.studio_ui")
PLUGIN_TITLE = "Orca Box Studio"
CONTROL_KEYS = ('width_x', 'depth_y', 'height_z', 'wall_thickness', 'floor_thickness', 'fit_clearance', 'gasket_width')
FAMILIES = ('lip_snap', 'rugged_box', 'sliding_lid', 'screw_corner')

CANONICAL_SOURCE_SHA256 = '1d644b0dda2754c641ceddad5f3e57c0d85d208a1b2c29f79e03571a599a338d'
DARK_TOKENS = {'--bg-app': '#16181c',
 '--bg-card': '#252830',
 '--bg-card-hover': '#2c303a',
 '--bg-hud': 'rgba(24,27,33,0.86)',
 '--bg-input': '#17191e',
 '--bg-panel': '#1e2026',
 '--bg-viewport-bot': '#121418',
 '--bg-viewport-top': '#232730',
 '--border-strong': '#414856',
 '--border-subtle': '#313640',
 '--font-mono': '"Cascadia Code",Consolas,"SFMono-Regular",monospace',
 '--font-sans': 'var(--orca-font,"Segoe '
                'UI",-apple-system,BlinkMacSystemFont,Roboto,Ubuntu,sans-serif)',
 '--orca-accent': '#00a896',
 '--orca-accent-border': 'rgba(0,191,165,0.48)',
 '--orca-accent-hover': '#00bfa5',
 '--orca-accent-soft': 'rgba(0,191,165,0.15)',
 '--radius-lg': '12px',
 '--radius-md': '9px',
 '--radius-sm': '6px',
 '--shadow-soft': '0 8px 24px rgba(0,0,0,0.35)',
 '--status-crit': '#ff5252',
 '--status-ok': '#00c853',
 '--status-warn': '#ffb300',
 '--text-dim': '#6e7787',
 '--text-main': '#eef2f6',
 '--text-muted': '#9aa3b2'}
LIGHT_TOKENS = {'--bg-app': '#eef2f6',
 '--bg-card': '#f5f7fa',
 '--bg-card-hover': '#eaeff5',
 '--bg-hud': 'rgba(255,255,255,0.90)',
 '--bg-input': '#ffffff',
 '--bg-panel': '#ffffff',
 '--bg-viewport-bot': '#c7d1dc',
 '--bg-viewport-top': '#dde4ec',
 '--border-strong': '#b8c3cf',
 '--border-subtle': '#d5dce4',
 '--orca-accent': '#00897b',
 '--orca-accent-border': 'rgba(0,137,123,0.45)',
 '--orca-accent-hover': '#00796b',
 '--orca-accent-soft': 'rgba(0,137,123,0.12)',
 '--shadow-soft': '0 8px 24px rgba(15,25,40,0.10)',
 '--status-crit': '#d93025',
 '--status-ok': '#1b9e4b',
 '--status-warn': '#d98200',
 '--text-dim': '#7b8696',
 '--text-main': '#1c222b',
 '--text-muted': '#556070'}
COMMON_RULES = {'#gl-canvas': {'display': 'block', 'height': '100%', 'touch-action': 'none', 'width': '100%'},
 '.action-footer': {'background': 'var(--bg-panel)',
                    'border-top': '1px solid var(--border-subtle)',
                    'display': 'flex',
                    'flex-direction': 'column',
                    'flex-shrink': '0',
                    'gap': '7px',
                    'padding': '10px'},
 '.brand-group': {'display': 'flex', 'flex': '1 1 auto', 'gap': '9px', 'min-width': '0'},
 '.brand-logo': {'background': 'linear-gradient(135deg,#00bfa5 0%,#00796b 100%)',
                 'border-radius': '7px',
                 'box-shadow': '0 2px 8px rgba(0,191,165,0.30)',
                 'height': '26px',
                 'width': '26px'},
 '.brand-title': {'font-size': '13.5px', 'font-weight': '700', 'letter-spacing': '0.2px'},
 '.btn': {'background': 'var(--bg-card)',
          'border': '1px solid var(--border-subtle)',
          'border-radius': 'var(--radius-sm)',
          'display': 'inline-flex',
          'font-size': '11.5px',
          'font-weight': '600',
          'gap': '5px',
          'padding': '5px 10px'},
 '.btn-accent': {'background': 'linear-gradient(135deg,var(--orca-accent)0%,#00897b 100%)',
                 'color': '#ffffff'},
 '.btn-hero': {'background': 'linear-gradient(135deg,#00bfa5 0%,#00897b 100%)',
               'border-radius': 'var(--radius-md)',
               'box-shadow': '0 4px 14px rgba(0,191,165,0.32)',
               'color': '#ffffff',
               'font-size': '13px',
               'font-weight': '700',
               'padding': '10px 14px',
               'width': '100%'},
 '.btn-icon': {'padding': '5px 7px'},
 '.btn-soft': {'background': 'var(--orca-accent-soft)',
               'border-color': 'var(--orca-accent-border)',
               'color': 'var(--orca-accent-hover)'},
 '.card-badge': {'background': 'var(--orca-accent-soft)',
                 'border-radius': '99px',
                 'color': 'var(--orca-accent-hover)',
                 'font-size': '10px',
                 'padding': '1px 6px'},
 '.card-head': {'align-items': 'center',
                'display': 'flex',
                'gap': '6px',
                'justify-content': 'space-between'},
 '.card-title': {'color': 'var(--text-main)',
                 'font-size': '11.5px',
                 'font-weight': '700',
                 'letter-spacing': '0.55px',
                 'text-transform': 'uppercase'},
 '.col-left': {'border-right': '1px solid var(--border-subtle)'},
 '.col-panel': {'background': 'var(--bg-panel)',
                'display': 'flex',
                'flex-direction': 'column',
                'min-height': '0',
                'overflow': 'hidden'},
 '.col-right': {'border-left': '1px solid var(--border-subtle)'},
 '.col-scroll': {'display': 'flex',
                 'flex': '1',
                 'flex-direction': 'column',
                 'gap': '10px',
                 'min-height': '0',
                 'overflow-y': 'auto',
                 'padding': '10px'},
 '.ctrl-label': {'color': 'var(--text-muted)', 'font-size': '11.3px', 'font-weight': '500'},
 '.ctrl-num': {'background': 'var(--bg-input)',
               'border-radius': '4px',
               'font-family': 'var(--font-mono)',
               'font-size': '11px',
               'padding': '2px 5px',
               'width': '58px'},
 '.ctrl-row': {'display': 'flex', 'flex-direction': 'column', 'gap': '3px'},
 '.ctrl-top': {'display': 'flex', 'gap': '6px', 'justify-content': 'space-between'},
 '.ctrl-unit': {'color': 'var(--text-dim)', 'font-size': '10px', 'min-width': '18px'},
 '.design-name-input': {'background': 'var(--bg-input)',
                        'border-radius': 'var(--radius-sm)',
                        'font-size': '12px',
                        'padding': '3px 8px',
                        'width': '165px'},
 '.dock-global-footer': {'display': 'none'},
 '.dock-tab-btn': {'border-radius': 'var(--radius-sm)',
                   'flex': '1',
                   'font-size': '11px',
                   'font-weight': '600',
                   'padding': '6px 4px'},
 '.dock-tab-btn.active': {'background': 'var(--orca-accent-soft)',
                          'border-color': 'var(--orca-accent-border)',
                          'color': 'var(--orca-accent-hover)'},
 '.dock-tabs': {'background': 'var(--bg-panel)',
                'display': 'none',
                'flex-shrink': '0',
                'gap': '4px',
                'padding': '4px 6px'},
 '.export-btn-row': {'display': 'grid', 'gap': '6px', 'grid-template-columns': '1fr 1fr auto'},
 '.header-actions': {'display': 'flex', 'flex-shrink': '0', 'gap': '5px'},
 '.preset-card': {'background': 'var(--bg-panel)',
                  'border': '1px solid var(--border-subtle)',
                  'border-radius': 'var(--radius-sm)',
                  'display': 'flex',
                  'gap': '7px',
                  'padding': '6px 7px'},
 '.presets-grid': {'display': 'grid',
                   'gap': '6px',
                   'grid-template-columns': 'repeat(2,minmax(0,1fr))',
                   'max-height': '205px',
                   'overflow-y': 'auto'},
 '.studio-card': {'background': 'var(--bg-card)',
                  'border': '1px solid var(--border-subtle)',
                  'border-radius': 'var(--radius-md)',
                  'display': 'flex',
                  'gap': '8px',
                  'padding': '10px'},
 '.studio-header': {'align-items': 'center',
                    'background': 'var(--bg-panel)',
                    'border-bottom': '1px solid var(--border-subtle)',
                    'display': 'flex',
                    'flex-shrink': '0',
                    'gap': '10px',
                    'padding': '7px 12px'},
 '.studio-shell': {'display': 'flex',
                   'flex-direction': 'column',
                   'height': '100%',
                   'width': '100%'},
 '.studio-workspace': {'display': 'grid',
                       'flex': '1',
                       'grid-template-columns': '332px minmax(340px,1fr)364px',
                       'min-height': '0',
                       'overflow': 'hidden'},
 '.toggle-switch': {'height': '18px', 'position': 'relative', 'width': '34px'},
 '.toggle-track': {'background': 'var(--border-strong)', 'border-radius': '99px'},
 '.viewport-col': {'background': 'radial-gradient(circle at 50% '
                                 '32%,var(--bg-viewport-top)0%,var(--bg-viewport-bot)100%)',
                   'display': 'flex',
                   'flex-direction': 'column',
                   'min-height': '0',
                   'min-width': '0',
                   'overflow': 'hidden',
                   'position': 'relative'},
 '.vp-glass': {'background': 'var(--bg-hud)',
               'border': '1px solid var(--border-subtle)',
               'border-radius': 'var(--radius-md)',
               'box-shadow': 'var(--shadow-soft)'},
 '[data-theme="light"] .btn-soft': {'color': 'var(--orca-accent)'},
 '[data-theme="light"] .dock-tab-btn.active': {'color': 'var(--orca-accent)'},
 'body[data-mode="dock"] .col-left': {'border': 'none', 'flex': '1', 'min-height': '0'},
 'body[data-mode="dock"] .col-right': {'border': 'none', 'flex': '1', 'min-height': '0'},
 'body[data-mode="dock"] .col-right .action-footer': {'display': 'none'},
 'body[data-mode="dock"] .design-name-input': {'width': '118px'},
 'body[data-mode="dock"] .dock-global-footer': {'display': 'flex'},
 'body[data-mode="dock"] .dock-tabs': {'display': 'flex', 'order': '0'},
 'body[data-mode="dock"] .studio-workspace': {'display': 'flex', 'flex-direction': 'column'},
 'body[data-mode="dock"] .viewport-col': {'border-bottom': '1px solid var(--border-subtle)',
                                          'flex-shrink': '0',
                                          'height': '245px',
                                          'order': '-1'},
 'html': {'background': 'var(--bg-app)',
          'color': 'var(--text-main)',
          'font-family': 'var(--font-sans)',
          'font-size': '12.5px',
          'height': '100%',
          'line-height': '1.4',
          'overflow': 'hidden',
          'width': '100%'},
 'input[type="range"].orca-slider': {'background': 'var(--border-strong)',
                                     'border-radius': '99px',
                                     'height': '5px',
                                     'width': '100%'},
 'input[type="range"].orca-slider::-webkit-slider-thumb': {'background': 'var(--orca-accent-hover)',
                                                           'border': '2px solid #ffffff',
                                                           'border-radius': '50%',
                                                           'height': '13px',
                                                           'width': '13px'}}


def normalized_css_value(value):
    return re.sub(r"\s*([,()])\s*", r"\1", " ".join(value.strip().split()))


def stylesheet_rules(css):
    """Read unconditional rules, retaining the CSS cascade for identical selectors."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules = {}
    cursor = 0
    while True:
        opening = css.find("{", cursor)
        if opening < 0:
            return rules
        selector = css[cursor:opening].strip()
        depth, end = 1, opening + 1
        while depth and end < len(css):
            depth += (css[end] == "{") - (css[end] == "}")
            end += 1
        if depth:
            raise AssertionError("Unbalanced CSS block")
        body = css[opening + 1:end - 1]
        cursor = end
        if selector.startswith("@"):
            continue
        declarations = {
            name: normalized_css_value(value)
            for name, value in re.findall(r"([\w-]+)\s*:\s*([^;]+)", body)
        }
        for item in selector.split(","):
            rules.setdefault(item.strip(), {}).update(declarations)


class Document(HTMLParser):
    void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.nodes, self.stack, self.styles, self.scripts = [], [], [], []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = dict(tag=tag, attrs=dict(attrs), parent=self.stack[-1] if self.stack else None)
        self.nodes.append(node)
        if tag not in self.void:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.nodes.append(dict(tag=tag, attrs=dict(attrs), parent=self.stack[-1] if self.stack else None))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if self.stack and self.stack[-1]["tag"] == "style":
            self.styles.append(data)
        elif self.stack and self.stack[-1]["tag"] == "script":
            self.scripts.append(data)

    def by_class(self, name):
        return [node for node in self.nodes if name in node["attrs"].get("class", "").split()]

    def descendants(self, ancestor):
        result = []
        for node in self.nodes:
            parent = node["parent"]
            while parent is not None:
                if parent is ancestor:
                    result.append(node)
                    break
                parent = parent["parent"]
        return result


def studio_html(mode="page", theme="dark", lang="pt", name="Visual contract"):
    params = copy.deepcopy(SCHEMA.DEFAULT_PARAMS)
    params["name"] = name
    context = dict(params=params, lang=lang, theme=theme, user_presets=[])
    return UI.get_studio_html(mode=mode, initial_context=context)


class VisualTemplateTests(unittest.TestCase):
    def test_shared_design_tokens_and_component_measurements(self):
        document = Document(studio_html())
        rules = stylesheet_rules("\n".join(document.styles))
        for selector, expected in ((":root", DARK_TOKENS), ('[data-theme="dark"]', DARK_TOKENS), ('[data-theme="light"]', LIGHT_TOKENS), *COMMON_RULES.items()):
            with self.subTest(selector=selector):
                self.assertIn(selector, rules)
                for name, value in expected.items():
                    self.assertEqual(rules[selector].get(name), value, f"{selector}: {name}")

    def test_initial_theme_language_and_mode_are_present_before_javascript(self):
        for mode in ("page", "dock"):
            for theme, lang in (("dark", "pt"), ("light", "en")):
                with self.subTest(mode=mode, theme=theme, lang=lang):
                    document = Document(studio_html(mode, theme, lang))
                    root = next(n for n in document.nodes if n["tag"] == "html")
                    body = next(n for n in document.nodes if n["tag"] == "body")
                    self.assertEqual(root["attrs"].get("data-theme"), theme)
                    self.assertEqual(root["attrs"].get("lang"), lang)
                    self.assertEqual(body["attrs"].get("data-mode"), mode)
                    self.assertEqual(body["attrs"].get("data-dock-tab"), "shape")
                    self.assertNotIn("__INITIAL_", "".join(document.scripts))

    def test_shared_shell_tabs_and_both_action_footers(self):
        for mode in ("page", "dock"):
            document = Document(studio_html(mode=mode))
            for cls in ("studio-shell", "studio-header", "brand-group", "brand-logo", "brand-title", "header-actions", "studio-workspace", "col-left", "col-right", "viewport-col", "studio-card", "dock-tabs", "design-name-input"):
                self.assertTrue(document.by_class(cls), cls)
            self.assertEqual(len(document.by_class("studio-header")), 1)
            self.assertEqual(len(document.by_class("viewport-col")), 1)
            ids = [node["attrs"]["id"] for node in document.nodes if node["attrs"].get("id")]
            self.assertEqual(len(ids), len(set(ids)), "DOM IDs must be unique")
            self.assertIn("gl-canvas", ids)
            self.assertTrue(document.by_class("printer-pill"))
            self.assertTrue({"printer-pill", "sync"} & set(ids))
            self.assertIn("presets-grid", ids)
            aliases = ({"btn-undo", "undo"}, {"btn-redo", "redo"}, {"btn-reset", "reset"}, {"btn-randomize", "randomize"}, {"btn-lang", "language", "lang"}, {"btn-theme", "theme"})
            for choices in aliases:
                self.assertTrue(set(ids) & choices, choices)
            tabs = document.by_class("dock-tab-btn")
            values = [node["attrs"].get("data-tab") for node in tabs]
            self.assertEqual(len(values), 4)
            self.assertEqual(len(set(values)), 4)
            self.assertTrue({"shape", "print", "presets"}.issubset(values))
            footers = document.by_class("action-footer")
            self.assertEqual(len(footers), 2)
            self.assertEqual(len(document.by_class("dock-global-footer")), 1)
            for footer in footers:
                actions = {n["attrs"].get("data-action") for n in document.descendants(footer)}
                self.assertTrue({"send_to_plater", "export_3mf", "export_stl", "open_folder"}.issubset(actions))

    def test_resource_controls_remain_in_the_new_template(self):
        html = studio_html()
        document = Document(html)
        source = "\n".join(document.scripts)
        controls = {node["attrs"].get("data-key") or node["attrs"].get("data-slider") for node in document.nodes}
        for key in CONTROL_KEYS:
            with self.subTest(control=key):
                self.assertTrue(key in controls or re.search(r"[\"']" + re.escape(key) + r"[\"']", source), f"Missing resource control {key}")
        for family in FAMILIES:
            self.assertIn(family, html)
        self.assertIn(PLUGIN_TITLE, html)
        self.assertNotIn("Orca Vase Studio", html)

    def test_offline_assets_and_script_safe_design_names(self):
        malicious = '</script><script id="injected">throw 1</script>\u2028\u2029'
        document = Document(studio_html(name=malicious))
        scripts = [n for n in document.nodes if n["tag"] == "script"]
        self.assertEqual(len(scripts), 1)
        self.assertFalse(any(n["attrs"].get("id") == "injected" for n in document.nodes))
        for node in document.nodes:
            if node["tag"] in {"script", "link", "img", "iframe", "source"}:
                for attr in ("src", "href"):
                    self.assertFalse(re.match(r"^(?:https?:)?//", node["attrs"].get(attr, "")), node)
        css = "\n".join(document.styles)
        script = "\n".join(document.scripts)
        self.assertNotRegex(css, r"@import|url\(\s*['\"]?(?:https?:)?//")
        self.assertNotIn("\u2028", script)
        self.assertNotIn("\u2029", script)

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed for JavaScript syntax verification")
    def test_javascript_is_syntactically_valid(self):
        script = "\n".join(Document(studio_html()).scripts)
        result = subprocess.run([shutil.which("node"), "--check"], input=script, text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed for transform verification")
    def test_camera_fits_transformed_lid_and_sliding_poses(self):
        """Exercise the production matrix/bounds/camera functions without a GPU."""
        script = "\n".join(Document(studio_html()).scripts)
        start = re.search(r"\bconst\s+I\s*=", script)
        stop = re.search(r"\bfunction\s+decode\s*\(", script)
        self.assertIsNotNone(start)
        self.assertIsNotNone(stop)
        self.assertLess(start.start(), stop.start())
        production_math = script[start.start():stop.start()]
        prefix = """
const assert = require('node:assert/strict');
let p = {style:'rugged_box', depth_y:65, height_z:35};
let INITIAL = {hinge:{y:37.5,z:31}};
let opening = 100, yaw = -.75, pitch = .68, zoom = 1;
const $ = () => ({value:opening});
let meshes = [
 {part:'base',bounds:{min:[-45,-32.5,0],max:[45,41.2,35]}},
 {part:'lid',bounds:{min:[-45,-32.5,27.3],max:[45,41.2,38.2]}}
];
"""
        assertions = """
function close(actual, expected) {
 assert.equal(actual.length,expected.length);
 actual.forEach((value,index)=>assert.ok(Math.abs(value-expected[index])<1e-4,
   JSON.stringify({actual,expected})));
}
close(sceneBounds(0).max,[45,41.2,38.2]);
close(sceneBounds(1).min,[-45,-32.5,0]);
close(sceneBounds(1).max,[45,107.5,35]);
for (const aspect of [.6,380/245,1920/960]) {
 const frame=camera(aspect),b=sceneBounds(1),m=frame.mvp;
 for(const x of [b.min[0],b.max[0]])for(const y of [b.min[1],b.max[1]])for(const z of [b.min[2],b.max[2]]) {
  const w=m[3]*x+m[7]*y+m[11]*z+m[15];
  const nx=(m[0]*x+m[4]*y+m[8]*z+m[12])/w;
  const ny=(m[1]*x+m[5]*y+m[9]*z+m[13])/w;
  const nz=(m[2]*x+m[6]*y+m[10]*z+m[14])/w;
  assert.ok(w>0 && Math.abs(nx)<=1 && Math.abs(ny)<=1 && Math.abs(nz)<=1,
   JSON.stringify({aspect,x,y,z,nx,ny,nz}));
 }
}
p.style='sliding_lid';
meshes=[
 {part:'base',bounds:{min:[-45,-32.5,0],max:[45,32.5,35]}},
 {part:'lid',bounds:{min:[-42.3,-30.1,32.2],max:[42.3,30,36.2]}}
];
close(sceneBounds(1).min,[-45,-105.1,0]);
close(sceneBounds(1).max,[45,32.5,36.2]);
p.style='lip_snap';
close(sceneBounds(1).max,[45,32.5,86.2]);
INITIAL.preview_mode='calibration';
meshes=[
 {part:'base',preview_offset:[-26,0,0],bounds:{min:[-14,-12,0],max:[14,12,14]}},
 {part:'lid',preview_offset:[8,0,0],bounds:{min:[-14,-12,0],max:[14,12,8]}},
 {part:'snap_sample',preview_offset:[34,0,0],bounds:{min:[-6,-4,0],max:[6,4,12]}}
];
close(sceneBounds(1).min,[-40,-12,0]);
close(sceneBounds(1).max,[40,12,14]);
console.log('Transform-aware lid, sliding and perspective framing: PASS');
"""
        result = subprocess.run(
            [shutil.which("node")], input=prefix + production_math + assertions,
            text=True, encoding="utf-8", capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_surprise_preserves_features_and_returns_valid_current_style(self):
        catalog = importlib.import_module("box_studio.presets_catalog")
        for style in FAMILIES:
            original = SCHEMA.normalize_params(dict(
                style=style, height_z=40,
                standoffs=[dict(x=-20,y=10,height=8,hole_diameter=4.2,hole_depth=5)],
                dividers_x=[10], dividers_y=[-12],
                cutouts=[dict(kind="usb_c",face="front",u=0,z=15)],
            ))
            before = copy.deepcopy(original)
            for seed in (0, 1, 22, 99):
                with self.subTest(style=style, seed=seed):
                    limits = dict(bed_x=220, bed_y=220, max_z=250)
                    candidate = catalog.generate_random_printable_params(original, seed, limits)
                    self.assertEqual(candidate, catalog.generate_random_printable_params(original, seed, limits))
                    self.assertEqual(candidate["style"], style)
                    self.assertEqual(SCHEMA.validate_params(candidate), [])
                    for key in ("standoffs", "cutouts", "dividers_x", "dividers_y"):
                        self.assertEqual(candidate[key], before[key])
                    self.assertEqual(original, before)

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed for range event verification")
    def test_keyboard_and_pointer_range_changes_save_the_previous_design(self):
        script = "\n".join(Document(studio_html()).scripts)
        starts = list(re.finditer(
            r'document\s*\.\s*querySelectorAll\(\s*"\[data-param-range\]"\s*\)', script,
        ))
        self.assertTrue(starts)
        start = starts[-1].start()
        following = re.search(
            r'document\s*\.\s*querySelectorAll\(\s*"\[data-wall-preset\]"\s*\)',
            script[start:],
        )
        self.assertIsNotNone(following)
        handlers = script[start:start + following.start()]
        fixture = """
const assert=require('node:assert/strict');
let p={width_x:90};const saved=[];
function snapshot(){saved.push({...p});}
function drawPlan(){} function sync(){} function requestPreview(){}
const number={value:90},range={dataset:{paramRange:'width_x'},value:'90'};
const document={querySelectorAll:()=>[range],querySelector:()=>number};
"""
        checks = """
if(range.onfocus)range.onfocus({target:range});
if(range.onkeydown)range.onkeydown({key:'ArrowRight',target:range,preventDefault(){}});
range.value='91';range.oninput();range.onchange();
assert.equal(p.width_x,91);
assert.equal(saved[0].width_x,90,'Keyboard range undo must restore the previous value');
p.width_x=90;saved.length=0;range.value='90';
range.onpointerdown({pointerId:1,target:range});
range.value='91';range.oninput();range.value='92';range.oninput();range.onchange();
assert.equal(p.width_x,92);assert.equal(saved.length,1);assert.equal(saved[0].width_x,90);
"""
        result = subprocess.run(
            [shutil.which("node")], input=fixture + handlers + checks,
            text=True, encoding="utf-8", capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


    @unittest.skipUnless(shutil.which("node"), "Node.js is needed for shortcut verification")
    def test_design_shortcuts_preserve_native_text_undo_and_support_control_y(self):
        script = "\n".join(Document(studio_html()).scripts)
        binding = re.search(
            r'document\s*\.\s*addEventListener\(\s*[\"\x27]keydown[\"\x27]\s*,[\s\S]*?\n\s*\}\s*\);',
            script,
        )
        self.assertIsNotNone(binding)
        fixture = """
const assert=require('node:assert/strict'),listeners={},actions=[];
const document={addEventListener:(name,handler)=>listeners[name]=handler};
const send=payload=>actions.push(payload.type);
const sendMutation=send;
const $=id=>({click(){actions.push(id==='redo'?'redo':'undo');}});
"""
        checks = """
function press(tag,key='z',shift=false,ctrl=true,meta=false){
 actions.length=0;let prevented=false;
 listeners.keydown({target:{tagName:tag,isContentEditable:false},key,
  ctrlKey:ctrl,metaKey:meta,shiftKey:shift,preventDefault(){prevented=true;}});
 return {actions:[...actions],prevented};
}
assert.deepEqual(press('INPUT'),{actions:[],prevented:false});
assert.deepEqual(press('TEXTAREA','y'),{actions:[],prevented:false});
assert.deepEqual(press('BODY'),{actions:['undo'],prevented:true});
assert.deepEqual(press('BODY','z',true),{actions:['redo'],prevented:true});
assert.deepEqual(press('BODY','y'),{actions:['redo'],prevented:true});
assert.deepEqual(press('BODY','z',false,false,true),{actions:['undo'],prevented:true});
assert.deepEqual(press('BODY','z',false,false),{actions:[],prevented:false});
"""
        result = subprocess.run(
            [shutil.which("node")], input=fixture + binding.group() + checks,
            text=True, encoding="utf-8", capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
