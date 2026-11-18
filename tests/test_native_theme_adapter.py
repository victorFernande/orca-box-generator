"""Native host CSS cascade and automatic theme regression coverage.

The optional browser case uses the same low-specificity contract as Orca 2.5.1.
Set ORCA_PLAYWRIGHT_MODULE and optionally ORCA_BROWSER_EXECUTABLE to run it.
It opens isolated headless pages and never connects to a running slicer.
"""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.studio_ui import get_studio_html

# Host contract: variables are independent of the selected studio theme, and
# bare element defaults may be appended after the plugin's own style sheets.
HOST_LIGHT_CSS = """
:root{--orca-bg:#f0f0f0;--orca-fg:#333333;--orca-font:"Segoe UI";--orca-accent:#e00000;--orca-accent-fg:#fff;--orca-border:#dddddd}
html,body{background:var(--orca-bg);color:var(--orca-fg);font-family:var(--orca-font);font-size:13px}
body{margin:0}h1,h2,h3,h4,h5,h6{color:var(--orca-fg);font-weight:600}
button{font:inherit;color:var(--orca-accent-fg);background:var(--orca-accent);border:1px solid var(--orca-accent);border-radius:4px;padding:5px 14px;cursor:pointer}
input,select,textarea{font:inherit;color:var(--orca-fg);background:var(--orca-bg);border:1px solid var(--orca-border);border-radius:4px;padding:4px 8px}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--orca-accent)}
"""


class NativeThemeTests(unittest.TestCase):
    @unittest.skipUnless(
        shutil.which("node"), "Node.js required for production theme detector"
    )
    def test_injected_theme_resolution_and_manual_override(self):
        script = re.search(r"<script>(.*?)</script>", get_studio_html(), re.S).group(1)
        begin = script.index("let userOverrodeTheme")
        end = script.index("function watchHostTheme", begin)
        functions = script[begin:end]
        program = (
            """
const INITIAL={host:{theme_explicit:false}};let raw='#fff',theme='dark',updates=0;
const document={documentElement:{}};const window={getComputedStyle:()=>({getPropertyValue:()=>raw})};
function translate(){updates++}
"""
            + functions
            + """
for(const [color,expected] of [['#fff','light'],['#222','dark'],['#f0f0f0','light'],['rgb(25, 30, 35)','dark'],['rgba(240, 240, 240, 1)','light'],['transparent',null]]){
 raw=color;if(detectInjectedOrcaTheme()!==expected)throw Error('wrong CSS theme for '+color);
}
raw='#fff';resolveHostTheme({host:{theme_explicit:false},theme:'dark'});
if(theme!=='light')throw Error('implicit host should use injected light theme');
userOverrodeTheme=true;theme='dark';resolveHostTheme({host:{theme_explicit:false},theme:'light'});
if(theme!=='dark')throw Error('manual theme was overwritten');
userOverrodeTheme=false;theme='light';resolveHostTheme({host:{theme_explicit:true},theme:'dark'});
if(theme!=='dark')throw Error('explicit theme should take precedence over injected CSS');
"""
        )
        result = subprocess.run(
            [shutil.which("node"), "-e", program],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_native_adapter_is_separate_and_more_specific(self):
        html = get_studio_html()
        adapter = re.search(
            r'<style id="orca-box-host-adapter">(.*?)</style>', html, re.S
        ).group(1)
        self.assertIn("html[data-theme] body", adapter)
        self.assertRegex(
            adapter, r'html\[data-theme="dark"\]\s*\{[^}]*--orca-accent:\s*#00a896'
        )
        self.assertRegex(
            adapter, r'html\[data-theme="light"\]\s*\{[^}]*--orca-accent:\s*#00897b'
        )
        self.assertRegex(
            adapter,
            r'input\[type="range"\]\.orca-slider\s*\{[^}]*border:\s*0;[^}]*padding:\s*0;',
        )
        self.assertNotIn("!important", adapter)

    @unittest.skipUnless(
        os.environ.get("ORCA_PLAYWRIGHT_MODULE") and shutil.which("node"),
        "Optional isolated Chromium cascade check",
    )
    def test_host_defaults_before_and_after_studio_css_in_browser(self):
        pages = []
        for theme in ("dark", "light"):
            for order in ("before", "after"):
                html = get_studio_html(
                    "page", {"theme": theme, "host": {"theme_explicit": True}}
                )
                style = (
                    '<style id="orca-host-theme-vars">' + HOST_LIGHT_CSS + "</style>"
                )
                html = (
                    html.replace("<head>", "<head>" + style, 1)
                    if order == "before"
                    else html.replace("</head>", style + "</head>", 1)
                )
                pages.append({"theme": theme, "order": order, "html": html})
        automatic = get_studio_html(
            "page", {"theme": "dark", "host": {"theme_explicit": False}}
        )
        program = r"""
const fs=require('fs'),assert=require('assert'),{chromium}=require(process.env.ORCA_PLAYWRIGHT_MODULE);
const input=JSON.parse(fs.readFileSync(0,'utf8'));
(async()=>{const browser=await chromium.launch({headless:true,...(process.env.ORCA_BROWSER_EXECUTABLE?{executablePath:process.env.ORCA_BROWSER_EXECUTABLE}:{}),args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
try{for(const test of input.pages){const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.setContent(test.html,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>window.OrcaBoxStudio);
const actual=await page.evaluate(()=>{const b=getComputedStyle(document.body),r=document.querySelector('.orca-slider'),s=getComputedStyle(r);return{theme:document.documentElement.dataset.theme,body:b.color,background:b.backgroundColor,font:b.fontSize,brand:getComputedStyle(document.querySelector('.brand-title')).color,resource:getComputedStyle(document.querySelector('.tex-title-wrap')).color,number:getComputedStyle(document.querySelector('.ctrl-num')).color,accent:getComputedStyle(document.documentElement).getPropertyValue('--orca-accent').trim(),rangeHeight:s.height,rangePadding:s.padding,rangeBorder:s.borderTopWidth}});
assert.equal(actual.theme,test.theme);assert.equal(actual.font,'12.5px');const foreground=test.theme==='dark'?'rgb(238, 242, 246)':'rgb(28, 34, 43)';assert.equal(actual.body,foreground);assert.equal(actual.brand,foreground);assert.equal(actual.resource,foreground);assert.equal(actual.number,foreground);assert.equal(actual.accent,test.theme==='dark'?'#00a896':'#00897b');assert.equal(actual.rangeHeight,'5px');assert.equal(actual.rangePadding,'0px');assert.equal(actual.rangeBorder,'0px');assert.deepEqual(errors,[]);await page.close();}
const page=await browser.newPage();await page.setContent(input.automatic,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>window.OrcaBoxStudio);assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
await page.evaluate(css=>{const style=document.createElement('style');style.id='orca-host-theme-vars';style.textContent=css;document.head.append(style)},input.hostCSS);
await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');await page.locator('#theme').click();assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
await page.evaluate(()=>{document.getElementById('orca-host-theme-vars').textContent+=':root{--orca-bg:#ffffff}';document.documentElement.setAttribute('data-orca-theme','light');window.OrcaBoxStudio.handleHostMessage({type:'init_state',theme:'light',host:{theme:'light',theme_explicit:false}})});
assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');await page.close();console.log('native theme cascade PASS');
}finally{await browser.close()}})().catch(error=>{console.error(error);process.exitCode=1});
"""
        result = subprocess.run(
            [shutil.which("node"), "-e", program],
            input=json.dumps(
                {"pages": pages, "automatic": automatic, "hostCSS": HOST_LIGHT_CSS}
            ),
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("native theme cascade PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
