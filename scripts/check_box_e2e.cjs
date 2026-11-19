/* Real UI + real Python geometry/export E2E. Never controls native OrcaSlicer.
 * Run with ORCA_TEST_PYTHON, ORCA_PLAYWRIGHT_MODULE and ORCA_CHROMIUM_PATH.
 * All mutations use Playwright locators: evaluate is observation only.
 */
'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {isDeepStrictEqual} = require('node:util');

const root = path.resolve(__dirname, '..');
const output = process.env.ORCA_E2E_OUTPUT || path.join(os.tmpdir(), 'orca-box-e2e-'+crypto.randomUUID());
const timeout = Number(process.env.ORCA_E2E_TIMEOUT || 240000);
const report = {started: new Date().toISOString(), output, complete:false, checks: [], failures: [], consoleErrors: [], exports: [], randomizations: []};
const presets = ['everyday','screw_corner_standard','tool_rugged','pencil','open_bin_handles','snap_latch_case','stackable_parts_bin','clamshell_pip_short'];
const styles = ['lip_snap','rugged_box','sliding_lid','screw_corner','open_bin','snap_latch','stackable_bin','clamshell_pip'];
const stylePresets = {lip_snap:'everyday',rugged_box:'tool_rugged',sliding_lid:'pencil',screw_corner:'screw_corner_standard',open_bin:'open_bin_handles',snap_latch:'snap_latch_case',stackable_bin:'stackable_parts_bin',clamshell_pip:'clamshell_pip_short'};

function startServer() {
  const child = spawn(process.env.ORCA_TEST_PYTHON || 'python', ['-B', path.join(__dirname, 'ui_test_server.py')], {
    cwd: root, env: {...process.env, ORCA_E2E_BED_X:process.env.ORCA_E2E_BED_X || '260', ORCA_E2E_BED_Y:process.env.ORCA_E2E_BED_Y || '260', ORCA_E2E_BED_Z:process.env.ORCA_E2E_BED_Z || '260'}, stdio:['ignore','pipe','pipe'],
  });
  let logs = '';
  child.stderr.on('data', chunk => { logs += chunk.toString('utf8'); });
  const ready = new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(Error('Backend startup timeout: ' + logs)), 45000);
    let buffer = '';
    child.stdout.on('data', chunk => {
      buffer += chunk.toString('utf8');
      const lines = buffer.split(/\r?\n/); buffer = lines.pop();
      for (const line of lines) {
        try { const value = JSON.parse(line); if (value.url) { clearTimeout(timer); resolve(value); } } catch {}
      }
    });
    child.on('error', reject);
    child.on('exit', code => {clearTimeout(timer); reject(Error('Backend exited ' + code + ': ' + logs));});
  });
  return {child, ready, logs:() => logs};
}

function saveReport() {
  report.updated = new Date().toISOString();
  if(report.complete)report.finished=report.updated;
  report.counts = {};
  for (const check of report.checks) report.counts[check.section] = (report.counts[check.section] || 0) + 1;
  report.ok = report.complete && report.failures.length === 0 && report.consoleErrors.length === 0;
  fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2));
}

async function observeUi(page) {
  return page.evaluate(()=>({
    params:window.OrcaBoxStudio?.getState(),
    sent:window.__sentMessages?.slice(-12),
    replies:window.__hostMessages?.slice(-12),
    controls:{
      style:document.querySelector('#style')?.value,
      gasket:document.querySelector('#gasket_enabled')?.checked,
      target:document.querySelector('#target')?.value,
      options:[...document.querySelectorAll('#target option')].map(o=>({value:o.value,disabled:o.disabled})),
    },
    rendered_models:window.__glModelFrame?.models,
  }));
}

async function withCleanup(run, cleanup) {
  let primaryError = null;
  try {
    return await run();
  } catch (error) {
    primaryError = error;
    throw error;
  } finally {
    try {
      await cleanup();
    } catch (error) {
      if (!primaryError) throw error;
      primaryError.e2eDetails = {...primaryError.e2eDetails, cleanup_error:String(error.stack || error)};
    }
  }
}

class Studio {
  constructor(page, url) { this.page = page; this.url = url; this.mode = 'page'; }
  async messages() { return this.page.evaluate(() => window.__hostMessages || []); }
  async state() { return this.page.evaluate(() => window.OrcaBoxStudio.getState()); }
  async mark() {
    return this.page.evaluate(()=>({host:window.__hostMessages.length,sent:window.__sentMessages.length}));
  }
  async snapshot() {
    return this.page.evaluate(() => window.__hostMessages.filter(m => m.type === 'preview_result' && m.ok && m.meshes).at(-1));
  }
  async check(section, name, run) {
    const started = Date.now();
    report.running={section,name,started:new Date().toISOString()};saveReport();
    console.log('RUN '+section+': '+name);
    try {
      const evidence = await run();
      delete report.running;
      report.checks.push({section, name, milliseconds:Date.now()-started, ...(evidence ? {evidence} : {})});
      console.log('PASS ' + section + ': ' + name);
      saveReport();
      return true;
    } catch (error) {
      delete report.running;
      const failure = {section, name, error:String(error.stack || error), ...(error.e2eDetails ? {diagnostics:error.e2eDetails} : {})};
      report.failures.push(failure);
      try {await this.page.screenshot({path:path.join(output, `failure-${report.failures.length}.png`)});} catch {}
      try {fs.writeFileSync(path.join(output,`failure-${report.failures.length}.json`),JSON.stringify(await observeUi(this.page),null,2));} catch {}
      console.error('FAIL ' + section + ': ' + name + '\n' + error.message);
      saveReport();
      return false;
    }
  }
  async waitPreview(before, expected = {}, success = true) {
    const mark=typeof before==='number' ? {host:before,sent:0} : before;
    await this.page.waitForFunction(({mark, expected, success}) => {
      const stable=value=>Array.isArray(value) ? value.map(stable) : value && typeof value==='object' ? Object.fromEntries(Object.keys(value).sort().map(key=>[key,stable(value[key])])) : value;
      const request=window.__sentMessages.slice(mark.sent).filter(m=>m.type==='preview').at(-1);
      if(!request)return false;
      return window.__hostMessages.slice(mark.host).some(m => m.type === 'preview_result' && m.request_id===request.request_id &&
        (success ? m.ok === false || m.ok && m.meshes > 0 && Object.entries(expected).every(([k,v]) => JSON.stringify(stable(m.params?.[k])) === JSON.stringify(stable(v))) : !m.ok));
    }, {mark, expected, success}, {timeout});
    const request=await this.page.evaluate(mark=>window.__sentMessages.slice(mark.sent).filter(m=>m.type==='preview').at(-1),mark);
    const events = (await this.messages()).slice(mark.host);
    const message = events.filter(m => m.type === 'preview_result' && m.request_id===request.request_id && (success ? m.ok === false || m.ok && m.meshes && Object.entries(expected).every(([key,value])=>isDeepStrictEqual(m.params?.[key],value)) : !m.ok)).at(-1);
    if (success && message?.ok === false) {
      const error = Error('Preview rejected for latest request '+request.request_id+': '+message.message);
      error.e2eDetails = {request,reply:message,expected};
      throw error;
    }
    if (success) {
      const actual = await this.state();
      for (const [key,value] of Object.entries(expected)) assert.deepEqual(actual[key], value, 'UI state differs from accepted mesh ' + key);
    }
    return message;
  }
  async goto(mode = 'page') {
    this.mode = mode;
    await this.page.setViewportSize(mode === 'dock' ? {width:430,height:900} : {width:1580,height:1090});
    await this.page.goto(this.url + '/?theme=dark&lang=pt' + (mode === 'dock' ? '&dock' : ''));
    await this.waitPreview(0);
    await this.page.locator('#gl-canvas').waitFor({state:'visible'});
  }
  async tab(tab) {
    if (this.mode === 'dock') await this.page.locator(`.dock-tab-btn[data-tab="${tab}"]`).click();
  }
  async preset(id) {
    await this.tab('presets');
    await this.page.locator('[data-cat="all"]').click();
    const before = await this.mark();
    await this.page.locator(`.preset-card[data-preset-id="${id}"]`).click();
    return this.waitPreview(before);
  }
  async number(key, value) {
    const input = this.page.locator(`input[type="number"][data-p="${key}"]`);
    if(Number(await input.inputValue())===value)return this.snapshot();
    const before = await this.mark();
    await input.fill(String(value)); await input.press('Tab');
    return this.waitPreview(before, {[key]:value});
  }
  async featureNumbers(card,values) {
    const before=await this.mark();let changed=false;
    for(const [index,value]of values) {
      const input=card.locator('input').nth(index);
      if(Number(await input.inputValue())!==value) {await input.fill(String(value));await input.press('Tab');changed=true;}
    }
    if(changed) {
      const params=await this.state();
      await this.waitPreview(before,{standoffs:params.standoffs,cutouts:params.cutouts});
    }
    for(const [index,value]of values)assert.equal(Number(await card.locator('input').nth(index).inputValue()),value);
  }
  async select(selector, value, key) {
    const before = await this.mark();
    await this.page.locator(selector).selectOption(value);
    return this.waitPreview(before, key ? {[key]:value} : {});
  }
  async optionDisabled(value) {
    // isDisabled() retargets an option inside a label to its enabled select.
    // Observe the browser's native option guard, which governs user selection.
    return this.page.locator(`#target option[value="${value}"]`).evaluate(option=>option.disabled);
  }
  async toggle(id, value, key = id) {
    const before = await this.mark();
    // These custom toggles intentionally hide their input; click its visible track.
    const input = this.page.locator('#' + id);
    if ((await input.isChecked()) !== value) await input.locator('..').click();
    else return this.snapshot();
    return this.waitPreview(before, {[key]:value});
  }
  async range(selector, value) {
    const slider = this.page.locator(selector);
    const min = Number(await slider.getAttribute('min') || 0);
    const max = Number(await slider.getAttribute('max') || 100);
    const step = Number(await slider.getAttribute('step') || 1);
    await slider.focus(); await slider.press('Home');
    if(value===max) await slider.press('End');
    else {
      // Native range keyboard gestures are faster than hundreds of tiny steps.
      const pageStep=Math.max(step,Math.round((max-min)/10/step)*step);
      for(let i=0;i<Math.floor((value-min)/pageStep);i++)await slider.press('PageUp');
      let current=Number(await slider.inputValue()),attempts=0;
      while(Math.abs(current-value)>step/2 && attempts++<1000) {
        await slider.press(current<value ? 'ArrowRight':'ArrowLeft');
        current=Number(await slider.inputValue());
      }
    }
    assert.equal(Number(await slider.inputValue()), value);
    await this.page.waitForFunction(() => window.__glModelFrame?.models.length > 0);
    // Observe a completed browser frame; never produce input via evaluation.
    await this.page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  }
  async models() {
    return this.page.evaluate(() => {
      const snapshot = window.__hostMessages.filter(m => m.type === 'preview_result' && m.ok && m.meshes).at(-1);
      return {parts:snapshot.parts, models:window.__glModelFrame.models, bounds:window.OrcaBoxStudio.getSceneBounds()};
    });
  }
  async gpu() {
    return this.page.evaluate(()=>{
      const gl=document.querySelector('#gl-canvas').getContext('webgl2');
      const program=gl.getParameter(gl.CURRENT_PROGRAM),result={};
      for(const name of ['u_mvp','u_baseColor','u_color','u_xrayMode','u_heatmap','u_clipMode','u_clipVal']) {
        const location=gl.getUniformLocation(program,name);
        if(location!==null) {
          const value=gl.getUniform(program,location);
          result[name]=ArrayBuffer.isView(value) ? Array.from(value) : value;
        }
      }
      const c=document.querySelector('#vp-caliper-canvas'),data=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
      result.caliperPixels=0;for(let i=3;i<data.length;i+=4)if(data[i])result.caliperPixels++;
      return result;
    });
  }
  async action(format, expectedFailure = false) {
    const paramsBefore = await this.state();
    const before = await this.mark();
    const selector = format === 'send' ? 'send_to_plater' : 'export_' + format;
    await this.page.locator(`[data-action="${selector}"]:visible`).click();
    await this.page.waitForFunction(before => window.__hostMessages.slice(before.host).some(m => m.type === 'action_result'), before, {timeout});
    const result = (await this.messages()).slice(before.host).find(m => m.type === 'action_result');
    if (expectedFailure) {
      assert.equal(result.ok, false, 'Expected an explicit export rejection');
      assert.ok(result.message, 'Rejection needs a visible reason');
      assert.deepEqual(await this.state(),paramsBefore,'Rejected export must preserve the design');
      if(result.export_manifest) {
        assert.equal(result.export_manifest.files.length,0,'Rejected geometry cannot produce an accepted file');
        assert.equal(result.export_manifest.verification.ok,false);
      }
      return {rejection:result.message};
    }
    if(format==='send') {
      assert.equal(result.ok,false,'Disabled native transport must never report success');
      assert.match(result.message,/native transport disabled/);
    } else assert.equal(result.ok, true, 'Export rejected: ' + result.message);
    assert.ok(result.export_manifest_url, 'Real export must expose a DEV artifact manifest');
    const response = await this.page.request.get(this.url + result.export_manifest_url);
    assert.equal(response.status(), 200);
    const manifest = await response.json();
    assert.equal(manifest.verification.ok, true, JSON.stringify(manifest.verification));
    assert.ok(manifest.files.length > 0, 'Export did not write a file');
    for (const file of manifest.files) {
      const download = await this.page.request.get(this.url + file.download_url);
      assert.equal(download.status(), 200);
      const bytes = await download.body();
      assert.equal(bytes.length, file.size_bytes);
      assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), file.sha256);
    }
    report.exports.push(manifest);
    return {manifest_id:manifest.id, files:manifest.files.length, checks:manifest.verification.checks};
  }
}

async function presetChecks(studio) {
  for (const id of presets) {
    await studio.check('presets', id + ' selects real mesh', async () => {
      const snapshot = await studio.preset(id);
      assert.ok(snapshot.parts.includes('base'));
      const p = await studio.state();
      assert.equal(snapshot.params.style, p.style);
      assert.equal(snapshot.params.width_x, p.width_x);
      return {style:p.style, parts:snapshot.parts};
    });
    if(process.env.ORCA_E2E_PRESET_EXPORTS!=='0') for(const format of ['stl','3mf']) {
      await studio.check('preset-exports',id+' '+format+' real files',()=>studio.action(format));
    }
  }
}

async function motionChecks(studio, style) {
  if (['open_bin','stackable_bin'].includes(style)) {
    assert.equal(await studio.page.locator('#open').isDisabled(), true);
    assert.equal(await studio.page.locator('#play').isDisabled(), true);
    return {lidless:true};
  }
  const end = style === 'clamshell_pip' ? 180 : 100;
  if(['rugged_box','snap_latch','clamshell_pip'].includes(style)) assert.equal(Number(await studio.page.locator('#open').inputValue()),style==='clamshell_pip' ? 180 : 0,'Style starts in its intended pose');
  const frames = style === 'snap_latch' ? [0,20,35,70,100] : style === 'rugged_box' ? [0,1,10,25,70,100] : [0,1,10,end];
  const poses = [];
  for (const value of frames) {
    await studio.range('#open', value);
    const frame = await studio.models();
    assert.equal(frame.models.length, frame.parts.length);
    frame.models.forEach(m => assert.ok(m.length === 16 && m.every(Number.isFinite)));
    if (style === 'snap_latch') {
      const snapshot = await studio.snapshot();
      for (const part of ['clip_left','clip_right']) {
        const m = frame.models[frame.parts.indexOf(part)], info = snapshot.latch_motion[part], v = info.pivot;
        const expected = Math.min(value/100/info.release_fraction,1) * info.release_angle;
        assert.ok(Math.abs(Math.atan2(m[6],m[5])*180/Math.PI-expected)<.001, 'Actual lever rotation');
        ['x','y','z'].forEach((key,i) => assert.ok(Math.abs(m[i]*v.x+m[4+i]*v.y+m[8+i]*v.z+m[12+i]-v[key])<.001, 'Lever stays attached to base pivot'));
      }
      const lid = frame.models[frame.parts.indexOf('lid')];
      assert.ok(Math.abs(lid[14] - Math.max(0,(value/100-.35)/.65)*50)<.001, 'Lid waits for both released levers');
    }
    if (style === 'rugged_box') {
      const snapshot=await studio.snapshot(),lid=frame.models[frame.parts.indexOf('lid')];
      const angle=Math.atan2(lid[6],lid[5]);
      const expected=-Math.PI*Math.max(0,(value/100-.25)/.75);
      assert.ok(Math.abs(angle-expected)<.001 || Math.abs(Math.abs(angle-expected)-2*Math.PI)<.001,'Rugged lid waits for released latches');
      for(const part of ['clip_left','clip_right']) {
        const clip=frame.models[frame.parts.indexOf(part)],info=snapshot.latch_motion[part],v=info.pivot;
        const expectedAngle=expected-info.release_angle*Math.PI/180*Math.min(value/100/info.release_fraction,1);
        assert.ok(Math.abs(Math.sin(Math.atan2(clip[6],clip[5])-expectedAngle))<.001,'Lid-mounted latch release composes with lid rotation');
        for(let i=0;i<3;i++) assert.ok(Math.abs(clip[i]*v.x+clip[4+i]*v.y+clip[8+i]*v.z+clip[12+i]-(lid[i]*v.x+lid[4+i]*v.y+lid[8+i]*v.z+lid[12+i]))<.001,'Latch remains attached to moving lid');
      }
    }
    if(style==='clamshell_pip') {
      const snapshot=await studio.snapshot(),lid=frame.models[frame.parts.indexOf('lid')],v=snapshot.hinge;
      assert.ok(Math.abs(Math.abs(Math.atan2(lid[6],lid[5]))-value*Math.PI/180)<.001,'PIP actual lid rotates through the requested degrees');
      for(const [i,key] of [[1,'y'],[2,'z']]) assert.ok(Math.abs(lid[4+i]*v.y+lid[8+i]*v.z+lid[12+i]-v[key])<.001,'PIP lid remains on its captive hinge axis');
      if(value===180) assert.ok(Math.abs(frame.bounds.min[2])<.001,'Open PIP floors touch the print plane');
    }
    poses.push({value,models:frame.models});
  }
  assert.notDeepEqual(poses[0].models, poses.at(-1).models, 'Opening must transform actual meshes');
  fs.writeFileSync(path.join(output,style+'-rendered-motion.json'),JSON.stringify({snapshot:await studio.snapshot(),poses},null,2));
  await studio.page.locator('#play').click();
  const value = await studio.page.locator('#open').inputValue();
  await studio.page.waitForFunction(value => document.querySelector('#open').value !== value, value);
  await studio.page.locator('#play').click();
  await studio.range('#open', style === 'clamshell_pip' ? 180 : 0);
  return {frames:frames.length};
}

async function styleChecks(studio) {
  for (const style of styles) {
    await studio.check(style, 'GUI style and dimension edits', async () => {
      await studio.preset('everyday');
      await studio.select('#style', style, 'style');
      if (style === 'clamshell_pip') await studio.number('height_z',14);
      const p = await studio.state();
      for (const [key,delta] of [['width_x',2],['depth_y',1],['height_z',1]]) await studio.number(key,p[key]+delta);
      const snapshot = await studio.snapshot();
      const expected = ['open_bin','stackable_bin'].includes(style) ? 1 : style==='snap_latch' ? 4 : style==='rugged_box' ? 4 : 2;
      assert.equal(snapshot.meshes, expected);
      return {parts:snapshot.parts, params:await studio.state()};
    });
    await studio.check(style, 'style-specific real controls', async () => {
      if (style==='lip_snap') await studio.number('snap_retention',.15);
      if (style==='rugged_box') {
        assert.equal(await studio.page.locator('#hinge_mode').count(),0,'SnapLock has no loose pin or captive mode');
        assert.equal(await studio.page.locator('[data-slider="hinge_pin_diameter"]').isVisible(),false);
        assert.equal(await studio.page.locator('#addPost').isDisabled(),true);
        assert.equal(await studio.page.locator('#addPort').isDisabled(),true);
        await studio.number('rugged_lid_height',22);
        for(const target of ['base_only','lid_only'])assert.equal(await studio.optionDisabled(target),false,'Snap-assembled shells export separately');
        for(const format of ['stl','3mf']) await studio.action(format);
      }
      if (style==='sliding_lid') await studio.number('fit_clearance',.3);
      if (style==='screw_corner') for(const size of ['M2','M2.5','M3']) await studio.select('#screw_size',size,'screw_size');
      if (style==='open_bin') {await studio.number('handle_width',35);await studio.number('handle_height',10);await studio.number('handle_top_margin',7);await studio.select('#handle_faces','front_back','handle_faces');await studio.toggle('handles_enabled',false);await studio.toggle('handles_enabled',true);}
      if (style==='snap_latch') for(const [k,v] of Object.entries({lid_wall_height:9,latch_width:19,latch_thickness:2.2,latch_retention:.7,latch_pivot_diameter:3.2})) await studio.number(k,v);
      if (style==='stackable_bin') for(const [k,v] of Object.entries({front_access_width:50,front_access_drop:16,stack_foot_height:2.5,stack_clearance:.3})) await studio.number(k,v);
      if (style==='clamshell_pip') for(const [k,v] of Object.entries({pip_clearance:.35,hinge_separation:6,hinge_pin_diameter:3.2,fit_clearance:.3})) await studio.number(k,v);
      return {parts:(await studio.snapshot()).parts};
    });
    await studio.check(style, 'actual rendered opening and animation', () => motionChecks(studio,style));
    let restoredAfterSurprise = false;
    await studio.check(style, 'Surprise keeps a valid style', async () => {
      const previous = await studio.state(), before=await studio.mark();
      const diagnostic = {style,input_params:previous,restoration:{ok:false}};
      report.randomizations.push(diagnostic);saveReport();
      const capture = async () => studio.page.evaluate(mark=>{
        const request=window.__sentMessages.slice(mark.sent).filter(m=>m.type==='randomize').at(-1);
        const result=window.__hostMessages.slice(mark.host).filter(m=>
          (m.type==='randomize_result'||m.type==='action_result'&&m.action==='randomize')&&
          (request?.request_id == null ? m.request_id == null : m.request_id===request.request_id)).at(-1);
        return {seed:request?.seed,request,result};
      },before);
      return withCleanup(async()=>{
        try {
          await studio.page.locator('#btn-randomize').click();
          // Observe the real seed chosen by the UI; never replace it with a
          // favorable fixture. An explicit generation rejection is a failure
          // of this positive check, not a successful "valid style" observation.
          await studio.page.waitForFunction(mark=>{
            const request=window.__sentMessages.slice(mark.sent).filter(m=>m.type==='randomize').at(-1);
            return !!request&&window.__hostMessages.slice(mark.host).some(m=>
              (m.type==='randomize_result'||m.type==='action_result'&&m.action==='randomize')&&
              (request.request_id == null ? m.request_id == null : m.request_id===request.request_id));
          },before,{timeout});
          Object.assign(diagnostic,await capture());saveReport();
          if(diagnostic.result?.ok !== true)throw Error('Surprise rejected seed '+diagnostic.seed+': '+diagnostic.result?.message);
          const next = await studio.waitPreview(before);
          diagnostic.preview_result=next;
          assert.equal(next.params.style,style);
          if (style==='stackable_bin') for(const k of ['width_x','depth_y','corner_radius','wall_thickness','stack_foot_height','stack_clearance']) assert.equal(next.params[k],previous[k], 'Stacking family '+k);
          return {seed:diagnostic.seed,request:diagnostic.request,result:diagnostic.result,preview_result:next};
        } catch(error) {
          diagnostic.error=String(error.stack||error);
          try {diagnostic.failure_state=await observeUi(studio.page);} catch {}
          error.e2eDetails={...error.e2eDetails,randomization:diagnostic};
          throw error;
        } finally {
          try {Object.assign(diagnostic,await capture());} catch {}
          saveReport();
        }
      },async()=>{
        // Even a failed random candidate must not contaminate target/export
        // coverage. A cleanup error must not replace the original failure.
        try {
          await studio.preset('everyday'); await studio.select('#style',style,'style');
          if (style==='clamshell_pip') await studio.number('height_z',14);
          restoredAfterSurprise=true;
          diagnostic.restoration={ok:true,params:await studio.state()};
        } catch(error) {
          diagnostic.restoration={ok:false,error:String(error.stack||error)};
          throw error;
        } finally {saveReport();}
      });
    });
    if(!restoredAfterSurprise) {
      report.blocked_sections ||= [];
      report.blocked_sections.push({style,reason:'Surprise cleanup failed; dependent target/export checks were not run.'});
      report.full_scope=false;saveReport();
      continue;
    }
    await studio.check(style,'gasket export availability follows a supported channel',async()=>{
      assert.equal(await studio.optionDisabled('gasket'),true,'No gasket export without an enabled channel');
      if(['lip_snap','screw_corner','snap_latch'].includes(style)) {
        await studio.number('wall_thickness',3);await studio.toggle('gasket_enabled',true);
        assert.equal(await studio.optionDisabled('gasket'),false);
      }
    });
    const available = await studio.page.locator('#target option').evaluateAll(options => options.map(o=>({value:o.value,disabled:o.disabled})));
    await studio.check(style, 'unavailable targets disabled', async () => {
      const expected = ['open_bin','stackable_bin'].includes(style) ? ['lid_only','gasket','fit_test_kit'] : style==='clamshell_pip' ? ['base_only','lid_only','gasket','fit_test_kit'] : style==='snap_latch' ? ['fit_test_kit'] : style==='sliding_lid' ? ['gasket'] : style==='rugged_box' ? ['gasket','fit_test_kit'] : [];
      assert.deepEqual(available.filter(o=>o.disabled).map(o=>o.value).sort(),expected.sort());
    });
    for (const option of available.filter(o=>!o.disabled)) {
      const target=option.value;
      const rejectGasket = target==='gasket' && style==='sliding_lid';
      await studio.check(style, 'target '+target+' real preview', async () => {
        if (target==='gasket' && !rejectGasket) {
          await studio.number('wall_thickness',3);
          await studio.toggle('gasket_enabled',true);
        }
        const before=await studio.mark();
        await studio.page.locator('#target').selectOption(target);
        if (rejectGasket) return {expected_rejection:(await studio.waitPreview(before,{},false)).message};
        const snapshot=await studio.waitPreview(before,{export_target:target});
        return {parts:snapshot.parts};
      });
      for(const format of ['stl','3mf']) await studio.check(style, target+' '+format+' real file', () => studio.action(format,rejectGasket));
    }
  }
}

async function generalChecks(studio) {
  await studio.preset('everyday');
  await studio.check('dimensions','wall, floor, lid, corner and lip edits',async()=>{
    for(const [key,value] of Object.entries({wall_thickness:2.8,floor_thickness:2.8,lid_height:3.2,corner_radius:5,lip_depth:4.5})) await studio.number(key,value);
    await studio.preset('everyday');
  });
  await studio.check('history', 'undo, redo, pending edit undo and reset', async () => {
    await studio.number('width_x',94);
    let before=await studio.mark();await studio.page.locator('#undo').click();await studio.waitPreview(before,{width_x:90});
    before=await studio.mark();await studio.page.locator('#redo').click();await studio.waitPreview(before,{width_x:94});
    const input=studio.page.locator('[data-p="width_x"]');
    await input.fill('96');await input.press('Tab');
    before=await studio.mark();await studio.page.locator('#undo').click();await studio.waitPreview(before,{width_x:94});
    before=await studio.mark();await studio.page.locator('#reset').click();await studio.waitPreview(before,{width_x:90,style:'lip_snap'});
  });
  await studio.check('preferences','PT/EN and light/dark preserve geometry',async()=>{
    const key=(await studio.snapshot()).geometry_key;
    for(const lang of ['en','pt']) {await studio.page.locator('#lang').click();await studio.page.waitForFunction(lang=>document.documentElement.lang===lang,lang);}
    for(const theme of ['light','dark']) {await studio.page.locator('#theme').click();await studio.page.waitForFunction(theme=>document.documentElement.dataset.theme===theme,theme);}
    assert.equal((await studio.snapshot()).geometry_key,key);
    assert.ok(await studio.page.locator('#quality option[value="standard"]').textContent());
  });
  await studio.check('presets-personal','create, reload, edit/save copy, load and delete isolated presets',async()=>{
    const name='E2E temporário '+Date.now();
    await studio.page.locator('#btn-toggle-save-preset').click();
    await studio.page.locator('#inp-save-preset-name').fill(name);
    await studio.page.locator('#savePreset').click();
    await studio.page.locator('[data-cat="user"]').click();
    let card=studio.page.locator('.preset-card').filter({hasText:name});
    await card.waitFor({state:'visible'});
    await studio.goto('page');
    await studio.number('width_x',96);
    await studio.page.locator('[data-cat="user"]').click();
    card=studio.page.locator('.preset-card').filter({hasText:name});
    await card.waitFor({state:'visible'});
    const before=await studio.mark();await card.click();await studio.waitPreview(before);
    assert.equal((await studio.state()).width_x,90,'Persisted preset must restore its saved dimensions');
    const originalId=await card.getAttribute('data-preset-id');
    card=studio.page.locator(`.preset-card[data-preset-id="${originalId}"]`);
    await studio.number('width_x',94);
    await studio.page.locator('#btn-toggle-save-preset').click();
    const copyName=name+' cópia editada';
    await studio.page.locator('#inp-save-preset-name').fill(copyName);
    await studio.page.locator('#savePreset').click();
    const copy=studio.page.locator('.preset-card').filter({hasText:copyName});
    await copy.waitFor({state:'visible'});
    assert.notEqual(await copy.getAttribute('data-preset-id'),originalId,'Save creates a separate copy, not an in-place overwrite');
    await studio.number('width_x',96);
    let start=await studio.mark();await copy.click();await studio.waitPreview(start,{width_x:94});
    await copy.locator('.preset-del-btn').click();await copy.waitFor({state:'detached'});
    start=await studio.mark();await card.click();await studio.waitPreview(start,{width_x:90});
    await card.locator('.preset-del-btn').click();await card.waitFor({state:'detached'});
    await studio.page.locator('[data-cat="all"]').click();
    assert.equal(await studio.page.locator('.preset-card').count(),presets.length);
  });
  await studio.check('view','five camera pills and all materials',async()=>{
    const cameras=[];
    for(const camera of ['iso','front','top','bottom','fit']) {await studio.page.locator(`[data-cam="${camera}"]`).click();cameras.push((await studio.gpu()).u_mvp);}
    assert.equal(new Set(cameras.slice(0,4).map(JSON.stringify)).size,4,'Camera gestures must change actual GPU view matrices');
    const colors=[];
    for(const material of ['terracotta','matte_ceramic','copper_bronze','xray','heatmap','emerald_silk']) {
      await studio.page.locator('#sel-material').selectOption(material);assert.equal(await studio.page.locator('#sel-material').inputValue(),material);
      const gpu=await studio.gpu();
      if(material==='xray')assert.equal(gpu.u_xrayMode,1);
      else if(material==='heatmap')assert.equal(gpu.u_heatmap,1);
      else colors.push(gpu.u_baseColor);
    }
    assert.equal(new Set(colors.map(JSON.stringify)).size,4,'Material choices must reach the actual mesh shader');
  });
  await studio.check('view','xray, calipers, wire, overhang, spin and clipping',async()=>{
    for(const id of ['xray','btn-vp-calipers','btn-vp-wire','btn-vp-heatmap','btn-vp-spin']) {
      const button=studio.page.locator('#'+id);await button.click();assert.match(await button.getAttribute('class'),/active/);
      const gpu=await studio.gpu();
      if(id==='xray')assert.equal(gpu.u_xrayMode,1);
      if(id==='btn-vp-calipers')assert.ok(gpu.caliperPixels>0,'Calipers must draw on the real overlay canvas');
      if(id==='btn-vp-wire')assert.ok(gpu.u_color && !gpu.u_baseColor,'Wire draw uses the actual line shader');
      if(id==='btn-vp-heatmap')assert.equal(gpu.u_heatmap,1);
      if(id==='btn-vp-spin')await studio.page.waitForFunction(previous=>{
        const gl=document.querySelector('#gl-canvas').getContext('webgl2'),program=gl.getParameter(gl.CURRENT_PROGRAM),location=gl.getUniformLocation(program,'u_mvp');
        return JSON.stringify(Array.from(gl.getUniform(program,location)))!==JSON.stringify(previous);
      },gpu.u_mvp);
      await button.click();assert.doesNotMatch(await button.getAttribute('class'),/active/);
      if(id==='btn-vp-calipers')assert.equal((await studio.gpu()).caliperPixels,0);
    }
    await studio.page.locator('#btn-cut-mode-y').click();await studio.range('#cut',40);
    assert.equal((await studio.gpu()).u_clipMode,1);
    await studio.page.locator('#btn-cut-half').click();assert.equal(Number(await studio.page.locator('#cut').inputValue()),50);
    await studio.page.locator('#btn-cut-mode-z').click();await studio.range('#cut',75);
    assert.equal((await studio.gpu()).u_clipMode,2);
    await studio.page.locator('#btn-cut-off').click();assert.equal(Number(await studio.page.locator('#cut').inputValue()),0);
    assert.equal((await studio.gpu()).u_clipMode,0);
  });
  await studio.check('transport','Send writes a real3MF but reports disabled native transport',()=>studio.action('send'));
  await studio.check('printer','sync refreshes host metadata without changing design',async()=>{
    const params=await studio.state(),before=await studio.mark();
    await studio.page.locator('#sync').click();
    await studio.page.waitForFunction(before=>window.__hostMessages.slice(before.host).some(m=>m.type==='init_state'),before,{timeout});
    assert.deepEqual(await studio.state(),params);
  });
}

async function negativeChecks(studio) {
  await studio.preset('everyday');
  await studio.check('rejections','raw STL preserves dimensions; automatic 3MF rejects out-of-bed layout',async()=>{
    const bed=Number(process.env.ORCA_E2E_BED_X || 260);
    assert.ok(bed<=340,'The oversize-negative fixture requires bed X <=340mm so schema permits a genuinely oversized model');
    const oversize=bed+10;
    await studio.select('#target','base_only','export_target');
    await studio.number('width_x',oversize);
    const requested=await studio.state();
    await studio.action('stl');
    const stl=report.exports.at(-1),base=stl.verification.parts.find(part=>part.part==='base');
    assert.ok(stl.verification.checks.includes('binary_stl_exact_facet_source_identity'));
    assert.equal(stl.verification.preview_identity.ok,true);
    const width=base.bounds.max[0]-base.bounds.min[0];
    assert.ok(Math.abs(width-oversize)<.001,'Raw STL must preserve its exact requested X extent');
    assert.deepEqual(await studio.state(),requested,'Raw STL export must preserve the requested design');
    const result=await studio.action('3mf',true);
    assert.match(result.rejection,/bed|mesa|fit|cabe|dimensions|dimens/i,'Expected a bed-size reason');
    assert.equal((await studio.state()).width_x,oversize,'No silent autoscaling');
    return {stl_width_mm:width,stl_manifest_id:stl.id,automatic_3mf_rejection:result.rejection};
  });
  await studio.preset('clamshell_pip_short');
  await studio.check('rejections','PIP unsupported features and partial exports are disabled',async()=>{
    assert.equal(await studio.page.locator('#addPost').isDisabled(),true);
    assert.equal(await studio.page.locator('#addPort').isDisabled(),true);
    const options=await studio.page.locator('#target option').evaluateAll(options=>options.filter(o=>o.disabled).map(o=>o.value));
    assert.deepEqual(options.sort(),['base_only','lid_only','gasket','fit_test_kit'].sort());
  });
  await studio.preset('everyday');
}

async function recoveryChecks(studio) {
  await studio.preset('everyday');
  await studio.number('wall_thickness',3);await studio.toggle('gasket_enabled',true);
  let before=await studio.mark();await studio.page.locator('#addPost').click();await studio.waitPreview(before);
  before=await studio.mark();await studio.page.locator('#addPort').click();await studio.waitPreview(before);
  const saved=await studio.state();
  for(const style of ['open_bin','stackable_bin','sliding_lid']) await studio.check('feature-recovery','gasket to '+style+' keeps editable features',async()=>{
    if((await studio.state()).style!=='lip_snap')await studio.select('#style','lip_snap','style');
    await studio.toggle('gasket_enabled',true);
    const start=await studio.mark();await studio.page.locator('#style').selectOption(style);
    const failure=await studio.waitPreview(start,{},false);assert.ok(failure.message);
    const checkbox=studio.page.locator('#gasket_enabled');
    assert.equal(await checkbox.isChecked(),true,'Requested gasket may not be silently removed');
    assert.equal(await checkbox.locator('..').isVisible(),true,'Incompatible gasket must remain removable');
    let params=await studio.state();
    assert.deepEqual(params.standoffs,saved.standoffs);assert.deepEqual(params.cutouts,saved.cutouts);
    await studio.toggle('gasket_enabled',false);
    params=await studio.state();assert.equal(params.style,style);
    assert.deepEqual(params.standoffs,saved.standoffs);assert.deepEqual(params.cutouts,saved.cutouts);
    return {rejection:failure.message,parts:(await studio.snapshot()).parts};
  });
  await studio.preset('everyday');
}

async function featuresChecks(studio) {
  await studio.preset('everyday');
  for(const [key,value]of [['width_x',70],['depth_y',50],['height_z',30]])await studio.number(key,value);
  await studio.check('features','PCB support add, edit, insert/pilot and remove',async()=>{
    let before=await studio.mark();await studio.page.locator('#addPost').click();await studio.waitPreview(before,{standoffs:[{x:0,y:0,height:8,outer_diameter:7,hole_diameter:4.2,hole_depth:5,insert:'M3',mode:'insert'}]});
    const card=studio.page.locator('#posts .box-feature').first();
    await studio.featureNumbers(card,[[0,10],[1,5],[2,9],[3,8]]);
    for(const [insert,hole,depth] of [['M2',3.2,4],['M2.5',3.8,4],['M3',4.2,5]]) {
      before=await studio.mark();await card.locator('select').nth(0).selectOption(insert);
      await studio.featureNumbers(card,[[4,hole],[5,depth]]);
      await studio.waitPreview(before);
      const post=(await studio.state()).standoffs[0];assert.equal(post.insert,insert);assert.equal(post.hole_diameter,hole);assert.equal(post.hole_depth,depth);
    }
    before=await studio.mark();await card.locator('select').nth(1).selectOption('pilot');await studio.waitPreview(before);
    assert.equal((await studio.state()).standoffs[0].mode,'pilot');
    await studio.action('3mf');
    before=await studio.mark();await card.locator('.box-feature-title button').click();await studio.waitPreview(before,{standoffs:[]});
  });
  await studio.check('features','five cutout kinds, four faces, dimensions and remove',async()=>{
    let before=await studio.mark();await studio.page.locator('#addPort').click();await studio.waitPreview(before);
    let card=studio.page.locator('#ports .box-feature').first();
    for(const kind of ['hdmi','dc','slot','hex','usb_c']) {
      before=await studio.mark();await card.locator('select').nth(1).selectOption(kind);await studio.waitPreview(before);assert.equal((await studio.state()).cutouts[0].kind,kind);
      if(kind==='hex') {
        const fingerprints=[];
        for(const [width,height]of [[6,6],[12,6],[6,12]]) {
          await studio.featureNumbers(card,[[2,width],[3,height]]);
          const cutout=(await studio.snapshot()).params.cutouts[0];assert.equal(cutout.width,width);assert.equal(cutout.height,height);
          await studio.action('stl');
          fingerprints.push(report.exports.at(-1).verification.print_snapshot.find(part=>part.part==='base').vertices_sha256);
        }
        assert.equal(new Set(fingerprints).size,3,'Both independent hex dimensions must change actual exported vertices');
      }
    }
    for(const face of ['back','left','right','front']) {before=await studio.mark();await card.locator('select').nth(0).selectOption(face);await studio.waitPreview(before);assert.equal((await studio.state()).cutouts[0].face,face);}
    await studio.featureNumbers(card,[[0,10],[1,14],[2,11],[3,5]]);
    await studio.action('stl');
    before=await studio.mark();await card.locator('.box-feature-title button').click();await studio.waitPreview(before,{cutouts:[]});
  });
  await studio.check('features','XY dividers, gasket dimensions, quality and slicer option',async()=>{
    for(const [key,value] of [['dividers_x','-15,15'],['dividers_y','0']]) {const before=await studio.mark();await studio.page.locator('#'+key).fill(value);await studio.page.locator('#'+key).press('Tab');await studio.waitPreview(before);}
    await studio.number('wall_thickness',3);await studio.toggle('gasket_enabled',true);
    await studio.number('gasket_width',1.4);await studio.number('gasket_depth',.8);
    await studio.select('#quality','fine','quality');await studio.select('#quality','standard','quality');
    await studio.toggle('auto_configure_slicer',true);await studio.toggle('auto_configure_slicer',false);
    await studio.select('#target','full_suite','export_target');await studio.action('3mf');
  });
  await studio.preset('everyday');
}

async function dockChecks(studio) {
  await studio.goto('dock');
  for(const tab of ['shape','textures','print','presets']) await studio.check('dock','tab '+tab,async()=>{
    await studio.tab(tab);assert.equal(await studio.page.locator('body').getAttribute('data-dock-tab'),tab);
    assert.ok(await studio.page.locator('.dock-global-footer').isVisible());
    assert.ok(await studio.page.locator('#gl-canvas').isVisible());
  });
  for(const id of presets) await studio.check('dock-presets',id+' selects real mesh',async()=>{
    const snapshot=await studio.preset(id);
    assert.ok(snapshot.parts.includes('base'));
    assert.equal(snapshot.params.style,(await studio.state()).style);
    return {parts:snapshot.parts};
  });
  for(const style of styles) await studio.check('dock',style+' preset, dimension and 3MF',async()=>{
    await studio.preset(stylePresets[style]);await studio.tab('shape');
    const p=await studio.state();await studio.number('height_z',p.height_z+1);
    await studio.tab('print');await studio.action('3mf');
    return {parts:(await studio.snapshot()).parts};
  });
  await studio.check('dock','PT/EN and themes',async()=>{
    await studio.page.locator('#lang').click();await studio.page.waitForFunction(()=>document.documentElement.lang==='en');
    await studio.page.locator('#theme').click();await studio.page.waitForFunction(()=>document.documentElement.dataset.theme==='light');
    await studio.page.locator('#lang').click();await studio.page.locator('#theme').click();
  });
}

async function main() {
  const {chromium}=require(process.env.ORCA_PLAYWRIGHT_MODULE || 'playwright');
  fs.mkdirSync(output,{recursive:true});
  const sections=(process.env.ORCA_E2E_SECTIONS || 'presets,general,styles,features,negative,dock').split(',');
  report.scope={sections,preset_exports:process.env.ORCA_E2E_PRESET_EXPORTS!=='0',styles,presets};
  report.full_scope=['presets','general','styles','features','negative','dock'].every(section=>sections.includes(section)) && report.scope.preset_exports;
  report.runtime={node:process.version,platform:process.platform};
  report.source_hashes={};
  const sourceFiles=fs.readdirSync(path.join(root,'src','box_studio')).filter(name=>name.endsWith('.py')).sort().map(name=>'src/box_studio/'+name);
  sourceFiles.push(...fs.readdirSync(path.join(root,'src','box_studio','preset_meshes')).filter(name=>name.endsWith('.npz')).sort().map(name=>'src/box_studio/preset_meshes/'+name));
  sourceFiles.push('scripts/ui_test_server.py','scripts/verify_box_e2e_exports.py','scripts/check_box_e2e.cjs');
  for(const relative of sourceFiles) {
    report.source_hashes[relative]=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,relative))).digest('hex');
  }
  const server=startServer();let browser,page;
  try {
    const {url}=await server.ready;report.backend=url;
    browser=await chromium.launch({headless:true,executablePath:process.env.ORCA_CHROMIUM_PATH || undefined,args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
    const context=await browser.newContext({viewport:{width:1580,height:1090}});
    page=await context.newPage();page.setDefaultTimeout(20000);
    page.on('pageerror',error=>report.consoleErrors.push(String(error)));
    page.on('console',message=>{if(message.type()==='error')report.consoleErrors.push(message.text());});
    const studio=new Studio(page,url);await studio.goto();
    if(sections.includes('witness')) {
      await studio.preset('everyday');await studio.select('#style','rugged_box','style');
      await studio.range('#open',1);
      const witness=await studio.models();fs.writeFileSync(path.join(output,'rugged-one-percent-witness.json'),JSON.stringify(witness,null,2));
      await studio.check('witness','Rugged lid remains closed at1%',async()=>{
        const lid=witness.models[witness.parts.indexOf('lid')];assert.ok(Math.abs(Math.atan2(lid[6],lid[5]))<.001,JSON.stringify(witness));
      });
    }
    if(sections.includes('guard')) {
      await studio.check('guard','fresh default gasket target and DOM native state',async()=>{
        await studio.preset('everyday');
        const option=page.locator('#target option[value="gasket"]');
        const before=await option.evaluate(o=>({disabled:o.disabled,attribute:o.getAttribute('disabled')}));
        const playwright=await option.isDisabled();
        const after=await option.evaluate(o=>({disabled:o.disabled,attribute:o.getAttribute('disabled')}));
        assert.equal(before.disabled,true,JSON.stringify({before,playwright,after,params:await studio.state()}));
        assert.equal(await studio.optionDisabled('gasket'),true);
        assert.equal(after.disabled,true);
        return {before,playwright,after};
      });
    }
    if(sections.includes('presets'))await presetChecks(studio);
    if(sections.includes('general'))await generalChecks(studio);
    if(sections.includes('styles'))await styleChecks(studio);
    if(sections.includes('features')){await featuresChecks(studio);await recoveryChecks(studio);}
    if(sections.includes('negative'))await negativeChecks(studio);
    if(sections.includes('dock'))await dockChecks(studio);
    await page.screenshot({path:path.join(output,'final-dock.png')});
    await context.close();
  } catch(error) {
    report.failures.push({section:'runner',name:'uncaught',error:String(error.stack||error)});
    if(page)try {fs.writeFileSync(path.join(output,'uncaught-ui.json'),JSON.stringify(await observeUi(page),null,2));} catch {}
  }
  finally {
    if(browser)await browser.close();
    if(report.backend) {
      try {await fetch(report.backend+'/shutdown',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal:AbortSignal.timeout(3000)});} catch {}
    }
    await new Promise(resolve=>{
      if(server.child.exitCode!==null)return resolve();
      const timer=setTimeout(()=>{server.child.kill();resolve();},5000);
      server.child.once('exit',()=>{clearTimeout(timer);resolve();});
    });
    fs.writeFileSync(path.join(output,'backend.log'),server.logs());report.complete=true;saveReport();
  }
  console.log(JSON.stringify({ok:report.ok,checks:report.checks.length,failures:report.failures.length,consoleErrors:report.consoleErrors.length,exports:report.exports.length,counts:report.counts,output},null,2));
  process.exitCode=report.ok ? 0 : 1;
}

module.exports={Studio,withCleanup};
if(require.main===module)main();
