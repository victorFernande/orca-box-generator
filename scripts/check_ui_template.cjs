/* Development-only browser checks. No network assets or native OrcaSlicer IPC. */
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');
const { chromium } = require(process.env.ORCA_PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const output = process.env.ORCA_UI_OUTPUT || fs.mkdtempSync(path.join(os.tmpdir(), 'orca-ui-evidence-'));
fs.mkdirSync(output, { recursive: true });
const fixture = JSON.parse(fs.readFileSync(path.join(root, 'tests/fixtures/vase_template_metrics.json'), 'utf8'));
const selectors = {header:'.studio-header',workspace:'.studio-workspace',left:'.col-left',right:'.col-right',brand:'.brand-logo',title:'.brand-title',card:'.studio-card',gallery:'.presets-grid',preset:'.preset-card',number:'.ctrl-num',slider:'.orca-slider',toggle:'.toggle-switch',hero:'.col-right .btn-hero',footer:'.col-right .action-footer',view:'.viewport-col',cameraBar:'.vp-cam-bar',cutBar:'.vp-cut-bar'};
function startServer() {
  const child=spawn(process.env.ORCA_TEST_PYTHON || 'python',['-B',path.join(__dirname,'ui_test_server.py')],{cwd:root,stdio:['ignore','pipe','pipe']});
  let logs='';child.stderr.on('data',chunk=>{logs+=chunk.toString();});
  const ready=new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(Error('UI server startup timed out: '+logs)),30000);
    let buffered='';child.stdout.on('data',chunk=>{
      buffered+=chunk.toString();const lines=buffered.split(/\r?\n/);buffered=lines.pop();
      for(const line of lines){try{const value=JSON.parse(line);if(value.url){clearTimeout(timer);resolve(value);}}catch{}}
    });
    child.on('error',error=>{clearTimeout(timer);reject(error);});
    child.on('exit',code=>{clearTimeout(timer);reject(Error('UI server exited '+code+': '+logs));});
  });
  return {child,ready,logs:()=>logs};
}
async function measure(page,reference) {
  return page.evaluate(({selectors,reference})=>{
    const html=getComputedStyle(document.documentElement),body=getComputedStyle(document.body),actual={tokens:{},body:{},components:{},rects:{}};
    for(const key of Object.keys(reference.tokens))actual.tokens[key]=html.getPropertyValue(key).trim();
    for(const key of Object.keys(reference.body))actual.body[key]=body[key];
    for(const [name,selector] of Object.entries(selectors)){
      const el=document.querySelector(selector);if(!el){actual.components[name]=null;continue;}
      const style=getComputedStyle(el),r=el.getBoundingClientRect();
      actual.components[name]=Object.fromEntries(Object.keys(reference.components[name]||{}).map(key=>[key,style[key]]));
      actual.rects[name]={x:r.x,y:r.y,width:r.width,height:r.height,display:style.display};
    }
    actual.overflow=document.documentElement.scrollWidth>innerWidth;
    actual.occludedCameraButtons=[...document.querySelectorAll('.vp-cam-bar button')].filter(button=>{
      const r=button.getBoundingClientRect();return r.width>0&&r.height>0&&!button.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));
    }).map(button=>button.textContent.trim());
    return actual;
  },{selectors,reference});
}
function compare(actual,expected) {
  const issues=[];
  for(const group of ['tokens','body'])for(const [key,value] of Object.entries(expected[group]))if(actual[group][key]!==value)issues.push(`${group}.${key}: ${actual[group][key]} != ${value}`);
  for(const [component,props] of Object.entries(expected.components)){
    if(!props||!Object.keys(props).length)continue;
    if(!actual.components[component]){issues.push(`missing ${component}`);continue;}
    for(const [key,value] of Object.entries(props))if(actual.components[component][key]!==value)issues.push(`${component}.${key}: ${actual.components[component][key]} != ${value}`);
  }
  if(!expected.dock){
    for(const name of ['header','workspace','left','right'])for(const key of ['x','y','width','height'])if(Math.abs((actual.rects[name]?.[key]??Infinity)-expected.rects[name][key])>1)issues.push(`${name}.${key} differs by more than 1px`);
    const camera=actual.rects.cameraBar,cut=actual.rects.cutBar;
    if(camera&&cut&&camera.display!=='none'&&camera.y+camera.height>cut.y+0.5)issues.push('camera controls overlap the section toolbar');
  }else if(Math.abs((actual.rects.view?.height??0)-245)>1)issues.push('dock preview height differs from 245px');
  if(actual.overflow)issues.push('horizontal document overflow');
  if(!expected.dock&&actual.occludedCameraButtons.length)issues.push('camera buttons occluded: '+actual.occludedCameraButtons.join(', '));
  return issues;
}
const geometryCount=page=>page.evaluate(()=>window.__hostMessages.filter(m=>['geometry','preview_result'].includes(m.type)&&m.meshes>0).length);
async function waitGeometry(page,before=0,expected={}) {
  await page.waitForFunction(({before,expected})=>window.__browserErrors?.length||window.__hostMessages.filter(m=>['geometry','preview_result'].includes(m.type)&&m.meshes>0).slice(before).some(m=>Object.entries(expected).every(([key,value])=>m.params?.[key]===value)),{before,expected},{timeout:180000});
  const failures=await page.evaluate(()=>window.__browserErrors||[]);if(failures.length)throw Error(failures.join('\n'));
}
async function clickAction(page,name) {
  const actions={send:'send_to_plater',stl:'export_stl',three:'export_3mf','3mf':'export_3mf',folder:'open_exports'};
  const buttons=page.locator(`[data-action="${actions[name]||name}"]`);const n=await buttons.count();
  for(let i=0;i<n;i++)if(await buttons.nth(i).isVisible()){await buttons.nth(i).click();return;}
  const aliases={send:'#send',stl:'#stl',three:'#three, #mf','3mf':'#three, #mf',folder:'#folder'};
  await page.locator(aliases[name]||'#'+name).first().click();
}
async function waitSuccessfulAction(page,before){
  await page.waitForFunction(before=>window.__hostMessages.slice(before).some(message=>message.type==='action_result'),before,{timeout:180000});
  const result=await page.evaluate(before=>window.__hostMessages.slice(before).find(message=>message.type==='action_result'),before);
  if(result.ok!==true)throw Error('Export failed: '+result.message);
}
function assertLatchSnapshot(snapshot) {
  const p=snapshot.params,motion=snapshot.latch_motion;
  for(const [part,sign] of [['clip_left',-1],['clip_right',1]]){
    const actual=motion?.[part],expected=[sign*p.width_x*.24,-p.depth_y/2-(p.latch_pivot_diameter/2+p.fit_clearance+.4),p.height_z-7.5];
    if(!actual||['x','y','z'].some((key,k)=>!Number.isFinite(actual.pivot?.[key])||Math.abs(actual.pivot[key]-expected[k])>1e-6)||actual.release_fraction!==.35||actual.release_angle!==90||actual.lid_lift_mm!==50)throw Error('Pivot metadata does not match its mesh snapshot: '+part);
  }
}
async function renderedLatchPose(page,value){
  await page.locator('#open').evaluate((input,value)=>{input.value=String(value);input.dispatchEvent(new Event('input',{bubbles:true}));},value);
  await page.waitForFunction(value=>Number(document.querySelector('#open').value)===value&&window.__glModelFrame?.models.length===4,value);
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  return page.evaluate(()=>{
    const snapshot=window.__hostMessages.filter(message=>message.type==='preview_result'&&message.ok).at(-1);
    const gl=document.querySelector('#gl-canvas').getContext('webgl2');
    return {models:Object.fromEntries(snapshot.parts.map((part,index)=>[part,window.__glModelFrame.models[index]])),error:gl.getError()};
  });
}
function assertRenderedLatchPose(pose,snapshot,percent){
  if(pose.error!==0)throw Error('WebGL rejected a pivot-latch pose: '+pose.error);
  const near=(actual,expected,label,tolerance=1e-5)=>{if(!Number.isFinite(actual)||Math.abs(actual-expected)>tolerance)throw Error(`${label}: ${actual} != ${expected}`);};
  const phase=percent/100,releaseFraction=Math.max(...Object.values(snapshot.latch_motion).map(info=>info.release_fraction));
  const lid=pose.models.lid,base=pose.models.base;
  for(const [part,matrix]of [['base',base],['lid',lid]]){
    if(!matrix||matrix.length!==16)throw Error('Missing rendered matrix: '+part);
    for(const index of [0,5,10,15])near(matrix[index],1,part+' orientation');
    for(const index of [1,2,3,4,6,7,8,9,11,12,13])near(matrix[index],0,part+' unexpected motion');
  }
  near(base[14],0,'base stays stationary');
  near(lid[14],Math.max(0,(phase-releaseFraction)/(1-releaseFraction))*snapshot.latch_motion.clip_left.lid_lift_mm,'lid lift waits for both releases');
  for(const part of ['clip_left','clip_right']){
    const matrix=pose.models[part],info=snapshot.latch_motion[part],v=info.pivot;
    if(!matrix||matrix.length!==16)throw Error('Missing latch model matrix: '+part);
    const angle=Math.atan2(matrix[6],matrix[5])*180/Math.PI;
    near(angle,Math.min(phase/info.release_fraction,1)*info.release_angle,part+' actual GL rotation',1e-4);
    const pivot=[matrix[0]*v.x+matrix[4]*v.y+matrix[8]*v.z+matrix[12],matrix[1]*v.x+matrix[5]*v.y+matrix[9]*v.z+matrix[13],matrix[2]*v.x+matrix[6]*v.y+matrix[10]*v.z+matrix[14]];
    for(const [index,key]of ['x','y','z'].entries())near(pivot[index],v[key],part+' remains on its base pivot');
  }
}
async function pivotLatchChecks(page,snapshot,passed){
  if(Number(await page.locator('#open').inputValue())!==0)throw Error('Pivot-latch preview must start closed');
  assertLatchSnapshot(snapshot);
  assertRenderedLatchPose(await renderedLatchPose(page,0),snapshot,0);
  passed.push('Pivot latches start engaged with both pivots matching the mesh snapshot');
  await page.screenshot({path:path.join(output,'box-pivot-latch-closed.png')});
  assertRenderedLatchPose(await renderedLatchPose(page,20),snapshot,20);
  passed.push('Actual WebGL levers rotate while the lid stays closed');
  assertRenderedLatchPose(await renderedLatchPose(page,35),snapshot,35);
  passed.push('Both base-mounted levers release to 90 degrees before lid motion');
  await page.screenshot({path:path.join(output,'box-pivot-latch-released.png')});
  for(const value of [70,100])assertRenderedLatchPose(await renderedLatchPose(page,value),snapshot,value);
  passed.push('The lid lifts only after both levers are released');
  await page.screenshot({path:path.join(output,'box-pivot-latch-open.png')});
  await renderedLatchPose(page,0);
}
async function smoke(page,slug,url,passed) {
  await page.goto(url+'/?theme=dark');await waitGeometry(page);passed.push('Python mesh preview');
  let n=await geometryCount(page);await page.locator('#language, #lang, #btn-lang').first().click();
  await page.waitForFunction(()=>document.documentElement.lang==='en');passed.push('PT/EN');
  if(slug==='thread')await waitGeometry(page,n,{lang:'en'});
  n=await geometryCount(page);await page.locator('#theme, #btn-theme').first().click();
  await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');passed.push('Light/dark');
  if(slug==='thread')await waitGeometry(page,n,{theme:'light'});
  const key=slug==='box'?'width_x':'height';
  const dimension=slug==='box'?page.locator('input[type="number"][data-p="width_x"], input[type="number"][data-key="width_x"]').first():page.locator('input[type="number"][data-key="height"]').first();
  const original=Number(await dimension.inputValue()),before=await geometryCount(page);
  await dimension.fill(String(original+2));await dimension.press('Tab');await waitGeometry(page,before,{[key]:original+2});passed.push('Dimension change');
  n=await geometryCount(page);await page.locator('#undo, #btn-undo').first().click();await waitGeometry(page,n,{[key]:original});
  if(Number(await dimension.inputValue())!==original)throw Error('Undo did not restore dimension');passed.push('Undo');
  n=await geometryCount(page);await page.locator('#redo, #btn-redo').first().click();await waitGeometry(page,n,{[key]:original+2});
  if(Number(await dimension.inputValue())!==original+2)throw Error('Redo did not restore edited dimension');passed.push('Redo');
  if(slug==='thread'){
    n=await geometryCount(page);await dimension.fill(String(original+4));await dimension.press('Tab');await page.locator('#undo, #btn-undo').first().click();
    await waitGeometry(page,n,{[key]:original+2});
    if(Number(await dimension.inputValue())!==original+2)throw Error('Undo lost the pending numeric edit');passed.push('Undo preserves a pending debounced edit');
  }
  const actionBefore=await page.evaluate(()=>window.__hostMessages.length);
  await clickAction(page,'3mf');
  await page.waitForFunction(before=>window.__hostMessages.slice(before).some(m=>m.type==='action_result'&&m.ok===true),actionBefore,{timeout:180000});passed.push('Real isolated 3MF export');
  const sentBefore=await page.evaluate(()=>window.__hostMessages.length);
  await clickAction(page,'send');
  await page.waitForFunction(before=>window.__hostMessages.slice(before).some(m=>m.type==='action_result'&&m.ok===false&&m.message?.includes('native transport disabled')),sentBefore,{timeout:180000});passed.push('No false success when native transport fails');
  n=await geometryCount(page);await page.locator('#randomize, #btn-randomize').first().click();await waitGeometry(page,n);passed.push('Validated Surprise');
  await page.goto(url+'/?theme=dark&dock');await waitGeometry(page);
  for(const tab of ['shape','textures','print','presets']){
    const button=page.locator(`.dock-tab-btn[data-tab="${tab}"]`);await button.click();
    const footer=page.locator('.dock-global-footer');if(!(await footer.isVisible()))throw Error('Dock footer hidden on '+tab);
    if(!(await page.locator('#gl-canvas').isVisible()))throw Error('Dock preview hidden on '+tab);
  }
  passed.push('All dock sections keep preview and export visible');
  const dockBefore=await page.evaluate(()=>window.__hostMessages.length);
  await clickAction(page,'3mf');
  await page.waitForFunction(before=>window.__hostMessages.slice(before).some(m=>m.type==='action_result'&&m.ok===true),dockBefore,{timeout:180000});passed.push('Dock 3MF export binding');
  return passed;
}
async function featureChecks(page,slug,url,passed){
  await page.goto(url+'/?theme=light');await waitGeometry(page);
  if(slug==='thread'){
    let n=await geometryCount(page);await page.locator('.preset-card[data-preset-id="m12"]').click();await waitGeometry(page,n,{module:'bolt_nut_knob',nominal_dia:12});
    await page.locator('[data-cam="fit"]').click();
    await page.screenshot({path:path.join(output,'thread-m12-fit.png')});passed.push('M12 preset and complete camera fit');
    n=await geometryCount(page);await page.locator('select[data-key="starts"]').selectOption('3');await waitGeometry(page,n,{starts:3,lead:5.25});passed.push('Three-start lead');
    n=await geometryCount(page);await page.locator('select[data-key="hand"]').selectOption('left');await waitGeometry(page,n,{hand:'left'});passed.push('Left-hand thread');
    n=await geometryCount(page);await page.locator('#target').selectOption('calibration');await waitGeometry(page,n,{export_target:'calibration'});
    const rings=await page.evaluate(()=>window.__hostMessages.filter(m=>m.type==='geometry').at(-1).meshes);if(rings!==3)throw Error('Expected three calibration rings');passed.push('Three-ring calibration preview');
    await page.screenshot({path:path.join(output,'thread-calibration-fit.png')});
    const before=await page.evaluate(()=>window.__hostMessages.length);
    await page.locator('.preset-card[data-preset-id="mason86"]').click();
    await page.waitForFunction(before=>window.__hostMessages.slice(before).some(m=>m.type==='geometry'&&m.params?.standard==='mason_86'&&m.meshes===0&&m.warning),before,{timeout:30000});
    const beforeRandom=await page.evaluate(()=>window.__hostMessages.length);await page.locator('#randomize, #btn-randomize').first().click();
    await page.waitForFunction(before=>window.__hostMessages.slice(before).some(m=>m.type==='geometry'&&m.params?.standard==='mason_86'&&m.params?.measurements_confirmed===false&&m.meshes===0),beforeRandom,{timeout:30000});passed.push('Experimental Mason 86 stays blocked after Surprise');
  }else{
    let n=await geometryCount(page);await page.locator('.preset-card').filter({hasText:'Mini'}).click();await waitGeometry(page,n,{width_x:45,depth_y:35});passed.push('Preset gallery changes real box geometry');
    n=await geometryCount(page);await page.locator('#target').selectOption('fit_test_kit');await waitGeometry(page,n,{export_target:'fit_test_kit'});
    const parts=await page.evaluate(()=>window.__hostMessages.filter(m=>m.type==='preview_result').at(-1).meshes);if(parts!==3)throw Error('Expected the three-part Box fit kit preview');passed.push('Box fit-kit preview reflects export target');
    await page.screenshot({path:path.join(output,'box-calibration-fit.png')});
    n=await geometryCount(page);await page.locator('.preset-card[data-preset-id="open_bin_handles"]').click();await waitGeometry(page,n,{style:'open_bin',width_x:140,depth_y:100,height_z:60});
    let selected=await page.evaluate(()=>window.__hostMessages.filter(m=>m.type==='preview_result'&&m.ok).at(-1));
    if(selected.meshes!==1||selected.parts.join(',')!=='base')throw Error('Open bin must preview only its base');
    if(!await page.locator('#open').isDisabled()||!await page.locator('#play').isDisabled())throw Error('Open bin exposes lid animation');
    passed.push('Open-bin preset has hand grips and no lid');
    n=await geometryCount(page);await page.locator('input[type="number"][data-p="handle_width"]').fill('48');await page.locator('input[type="number"][data-p="handle_width"]').press('Tab');await waitGeometry(page,n,{handle_width:48});
    n=await geometryCount(page);await page.locator('#handle_faces').selectOption('front_back');await waitGeometry(page,n,{handle_faces:'front_back'});passed.push('Hand-grip size and pair of faces update real geometry');
    n=await geometryCount(page);await page.locator('input[type="number"][data-p="height_z"]').fill('72');await page.locator('input[type="number"][data-p="height_z"]').press('Tab');await waitGeometry(page,n,{height_z:72});passed.push('Open-bin height is resizable');
    await page.locator('[data-cam="fit"]').click();await page.screenshot({path:path.join(output,'box-open-bin-fit.png')});
    n=await geometryCount(page);await page.locator('.preset-card[data-preset-id="snap_latch_case"]').click();await waitGeometry(page,n,{style:'snap_latch'});
    selected=await page.evaluate(()=>window.__hostMessages.filter(m=>m.type==='preview_result'&&m.ok).at(-1));
    if(selected.meshes!==4||[...selected.parts].sort().join(',')!=='base,clip_left,clip_right,lid')throw Error('Snap-latch case must contain base, lid and two independent clips');
    if(!await page.locator('input[type="number"][data-p="lid_height"]').isVisible())throw Error('Lid thickness remains hidden after leaving open-bin mode');
    passed.push('Removable lid and two separate latch meshes');
    await pivotLatchChecks(page,selected,passed);
    n=await geometryCount(page);await page.locator('input[type="number"][data-p="lid_wall_height"]').fill('10');await page.locator('input[type="number"][data-p="lid_wall_height"]').press('Tab');await waitGeometry(page,n,{lid_wall_height:10});
    n=await geometryCount(page);await page.locator('input[type="number"][data-p="latch_retention"]').fill('0.7');await page.locator('input[type="number"][data-p="latch_retention"]').press('Tab');await waitGeometry(page,n,{latch_retention:0.7});passed.push('Lid depth and latch retention update real geometry');
    for(const [key,value]of [['width_x',160],['depth_y',95],['height_z',35]]){
      n=await geometryCount(page);const control=page.locator(`input[type="number"][data-p="${key}"]`);await control.fill(String(value));await control.press('Tab');await waitGeometry(page,n,{[key]:value});
    }
    passed.push('Latching case resizes to 160×95×35 mm');
    selected=await page.evaluate(()=>window.__hostMessages.filter(m=>m.type==='preview_result'&&m.ok).at(-1));
    assertLatchSnapshot(selected);
    assertRenderedLatchPose(await renderedLatchPose(page,0),selected,0);
    passed.push('Resized pivot metadata and rendered levers follow the matching design');
    // The new pivot bodies are wider than the former spring clips. Keep the
    // 160×95 resize check above, then use a four-piece layout that fits the
    // same generic 220×220 bed with the exporter's existing spacing/margins.
    n=await geometryCount(page);const exportDepth=page.locator('input[type="number"][data-p="depth_y"]');
    await exportDepth.fill('90');await exportDepth.press('Tab');await waitGeometry(page,n,{depth_y:90});
    const exportBefore=await page.evaluate(()=>window.__hostMessages.length);await clickAction(page,'3mf');
    await waitSuccessfulAction(page,exportBefore);passed.push('Four-piece snap-latch case exports to real 3MF');
    await page.locator('[data-cam="fit"]').click();await page.screenshot({path:path.join(output,'box-snap-latch-fit.png')});
    n=await geometryCount(page);await page.locator('.preset-card[data-preset-id="stackable_parts_bin"]').click();await waitGeometry(page,n,{style:'stackable_bin'});
    selected=await page.evaluate(()=>window.__hostMessages.filter(m=>m.type==='preview_result'&&m.ok).at(-1));
    if(selected.meshes!==1||selected.parts.join(',')!=='base')throw Error('Stackable container must export only its single connected base');
    if(!await page.locator('#open').isDisabled()||!await page.locator('#play').isDisabled())throw Error('Stackable container exposes lid animation');
    passed.push('Stackable-container preset has one body and no lid');
    for(const [key,value]of [['height_z',100],['front_access_width',85],['front_access_drop',35],['stack_foot_height',3],['stack_clearance',0.35]]){
      n=await geometryCount(page);const control=page.locator(`input[type="number"][data-p="${key}"]`);await control.fill(String(value));await control.press('Tab');await waitGeometry(page,n,{[key]:value});
    }
    passed.push('Stacking foot, clearance and front access update actual geometry');
    const stackExportBefore=await page.evaluate(()=>window.__hostMessages.length);await clickAction(page,'3mf');
    await page.waitForFunction(before=>window.__hostMessages.slice(before).some(m=>m.type==='action_result'&&m.ok===true),stackExportBefore,{timeout:180000});passed.push('Single-piece stackable container exports to real 3MF');
    await page.locator('[data-cam="fit"]').click();await page.screenshot({path:path.join(output,'box-stackable-bin-fit.png')});
    n=await geometryCount(page);await page.locator('.preset-card[data-preset-id="snap_latch_case"]').click();await waitGeometry(page,n,{style:'snap_latch'});
    if(!await page.locator('input[type="number"][data-p="lid_height"]').isVisible())throw Error('Lid controls did not return after the stacking preset');
    passed.push('Returning from a stackable container restores removable-lid controls');
    n=await geometryCount(page);await page.locator('.preset-card[data-preset-id="clamshell_pip_short"]').click();await waitGeometry(page,n,{style:'clamshell_pip'});
    selected=await page.evaluate(()=>window.__hostMessages.filter(m=>m.type==='preview_result'&&m.ok).at(-1));
    if(selected.meshes!==2||[...selected.parts].sort().join(',')!=='base,lid')throw Error('PIP preview must retain its two real moving halves');
    if(Number(await page.locator('#open').getAttribute('max'))!==180||Number(await page.locator('#open').inputValue())!==180)throw Error('New PIP case must open at 180 degrees');
    if(Math.abs(selected.hinge.y-(selected.params.depth_y/2+selected.params.hinge_separation))>1e-5||Math.abs(selected.hinge.z-(selected.params.height_z+selected.params.fit_clearance/2))>1e-5)throw Error('UI hinge disagrees with the equal-half geometry');
    const invalidTargets=await page.locator('#target option').evaluateAll(options=>options.filter(option=>!option.disabled).map(option=>option.value));
    if(invalidTargets.some(target=>!['base_and_lid','full_suite'].includes(target)))throw Error('PIP UI exposes an export that separates its hinge');
    passed.push('Equal-height PIP preset starts fully open with two moving meshes');
    await page.locator('#open').press('Home');await page.waitForFunction(()=>Number(document.querySelector('#open').value)===0);
    await page.locator('[data-cam="fit"]').click();await page.screenshot({path:path.join(output,'box-clamshell-pip-closed.png')});
    await page.locator('#open').press('End');await page.waitForFunction(()=>Number(document.querySelector('#open').value)===180);
    passed.push('PIP hinge closes to zero and opens to 180 degrees');
    for(const[key,value]of [['height_z',18],['pip_clearance',0.35],['hinge_separation',6]]){
      n=await geometryCount(page);const control=page.locator(`input[type="number"][data-p="${key}"]`);await control.fill(String(value));await control.press('Tab');await waitGeometry(page,n,{[key]:value});
    }
    passed.push('Half height and PIP hinge controls regenerate the actual model');
    const pipExportBefore=await page.evaluate(()=>window.__hostMessages.length);await clickAction(page,'3mf');
    await page.waitForFunction(before=>window.__hostMessages.slice(before).some(m=>m.type==='action_result'&&m.ok===true),pipExportBefore,{timeout:180000});passed.push('PIP case exports as a preserved open assembly');
    await page.locator('[data-cam="fit"]').click();await page.screenshot({path:path.join(output,'box-clamshell-pip-open.png')});
    n=await geometryCount(page);const deepHeight=page.locator('input[type="number"][data-p="height_z"]');await deepHeight.fill('25');await deepHeight.press('Tab');await waitGeometry(page,n,{style:'clamshell_pip',height_z:25});
    passed.push('Custom PIP depth keeps equal halves');
    n=await geometryCount(page);await page.locator('.preset-card[data-preset-id="everyday"]').click();await waitGeometry(page,n,{style:'lip_snap'});
    if(Number(await page.locator('#open').getAttribute('max'))!==100||!await page.locator('input[type="number"][data-p="lid_height"]').isVisible())throw Error('Normal lid controls did not return after PIP mode');
    passed.push('Leaving PIP mode restores standard lid and percentage controls');
  }
}
async function nativeStyleChecks(page,slug,url,passed){
  for(const theme of ['light','dark']){
    await page.goto(url+'/?theme='+theme);await waitGeometry(page);
    const toggle=page.locator('#theme, #btn-theme').first();
    // Establish a manual preference before testing a conflicting host theme.
    await toggle.click();await toggle.click();
    await page.waitForFunction(theme=>document.documentElement.dataset.theme===theme,theme);
    await page.addStyleTag({content:':root{--orca-bg:#f0f0f0;--orca-fg:#333;--orca-border:#ddd;--orca-accent:#e00000;--orca-accent-fg:#fff;--orca-font:"Segoe UI",sans-serif;}html,body{background:var(--orca-bg);color:var(--orca-fg);font-family:var(--orca-font);font-size:13px;line-height:normal;}button{font:inherit;color:var(--orca-accent-fg);background:var(--orca-accent);border:1px solid var(--orca-accent);padding:5px 14px;}input,select,textarea{font:inherit;color:var(--orca-fg);background:var(--orca-bg);border:1px solid var(--orca-border);padding:4px 8px;}'});
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    const state=await page.evaluate(()=>{
      const body=getComputedStyle(document.body),title=getComputedStyle(document.querySelector('.brand-title')),slider=getComputedStyle(document.querySelector('.orca-slider'));
      return {theme:document.documentElement.dataset.theme,color:body.color,title:title.color,font:body.fontSize,line:body.lineHeight,accent:getComputedStyle(document.documentElement).getPropertyValue('--orca-accent').trim(),border:slider.borderTopWidth,padding:slider.padding,height:slider.height};
    });
    const color=theme==='light'?'rgb(28, 34, 43)':'rgb(238, 242, 246)',accent=theme==='light'?'#00897b':'#00a896';
    if(state.theme!==theme||state.color!==color||state.title!==color||state.font!=='12.5px'||state.line!=='17.5px'||state.accent!==accent||state.border!=='0px'||state.padding!=='0px'||state.height!=='5px')throw Error('Late native host CSS changed studio '+JSON.stringify(state));
    await page.screenshot({path:path.join(output,`${slug}-native-host-${theme}.png`)});
    passed.push('Late native host defaults preserve '+theme+' template');
  }
}
(async()=>{
  const server=startServer();let browser;const results=[],errors=[];
  try{
    const {url,slug}=await server.ready;
    const options={headless:true,args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']};
    if(process.env.ORCA_CHROMIUM_PATH)options.executablePath=process.env.ORCA_CHROMIUM_PATH;
    browser=await chromium.launch(options);
    for(const sample of (process.argv.includes('--smoke-only')?[]:fixture.samples)){
      const page=await browser.newPage({viewport:{width:sample.width,height:sample.height},deviceScaleFactor:sample.scale});
      await page.addInitScript(()=>{window.__browserErrors=[];window.addEventListener('error',event=>window.__browserErrors.push(event.error?.stack||event.message));});
      const pageErrors=[];page.on('pageerror',error=>pageErrors.push(String(error)));
      page.on('console',message=>{if(message.type()==='error')pageErrors.push(message.text());});
      await page.route('**/*',route=>new URL(route.request().url()).origin===url?route.continue():route.abort());
      await page.goto(`${url}/?theme=${sample.theme}${sample.dock?'&dock':''}`);
      try{await waitGeometry(page);}catch(error){
        await page.screenshot({path:path.join(output,'layout-failure.png')});
        fs.writeFileSync(path.join(output,'layout-failure.json'),JSON.stringify({sample:sample.name,theme:sample.theme,error:String(error),pageErrors,messages:await page.evaluate(()=>window.__hostMessages),body:await page.locator('body').innerText()},null,2));
        throw error;
      }
      await page.evaluate(()=>document.fonts.ready);
      const glState=await page.evaluate(()=>{const gl=document.querySelector('#gl-canvas')?.getContext('webgl2');if(!gl||gl.isContextLost())return false;const program=gl.getParameter(gl.CURRENT_PROGRAM);return !!program&&gl.getProgramParameter(program,gl.LINK_STATUS);});
      if(!glState)pageErrors.push('WebGL2 context/program unavailable or lost');
      const actual=await measure(page,sample),issues=compare(actual,sample);
      await page.screenshot({path:path.join(output,`${slug}-${sample.name}-${sample.theme}.png`),animations:'disabled'});
      results.push({name:sample.name,theme:sample.theme,actual,issues,pageErrors});
      console.log(`${sample.name}/${sample.theme}: ${issues.length+pageErrors.length} issues`);
      await page.close();
    }
    const page=await browser.newPage({viewport:{width:1580,height:1090}});page.on('pageerror',e=>errors.push(String(e)));
    await page.addInitScript(()=>{window.__browserErrors=[];window.addEventListener('error',event=>window.__browserErrors.push(event.error?.stack||event.message));});
    const interactions=[];
    try{await smoke(page,slug,url,interactions);await nativeStyleChecks(page,slug,url,interactions);await featureChecks(page,slug,url,interactions);}catch(error){errors.push(String(error));await page.screenshot({path:path.join(output,'interaction-failure.png')});}
    await page.close();
    const report={reference:fixture.reference,slug,results,interactions,errors,nativeApplicationTest:false};
    fs.writeFileSync(path.join(output,process.argv.includes('--smoke-only')?'interaction-report.json':'report.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({output,interactions,errors,layoutIssues:results.reduce((n,r)=>n+r.issues.length+r.pageErrors.length,0)},null,2));
    if(errors.length||results.some(r=>r.issues.length||r.pageErrors.length))process.exitCode=1;
  }finally{if(browser)await browser.close();server.child.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
