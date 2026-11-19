/* Development-only, real preset click -> complete WebGL frame benchmark.
 * Does not generate a different preview, change parameters through evaluate,
 * install the plugin, or use native Orca IPC. Run only after the source freeze.
 */
'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {spawn}=require('node:child_process');

const ROOT=path.resolve(__dirname,'..');
const PRESETS=['everyday','screw_corner_standard','tool_rugged','pencil','open_bin_handles','snap_latch_case','stackable_parts_bin','clamshell_pip_short'];

function completeIndexSequence(expected,observed) {
  return expected.length>0 && expected.length===observed.length && expected.every((count,index)=>count===observed[index]);
}

function correctFrameBuffers(candidate,bindings,previous) {
  if(bindings.length!==candidate.expected_buffers.length)return false;
  const changed=!previous||previous.geometry_key!==candidate.geometry_key;
  if(changed&&(candidate.first_upload_ms===null||candidate.upload_bytes<=0))return false;
  return bindings.every((pair,index)=>['position','index'].every(kind=>{
    const actual=pair[kind],expected=candidate.expected_buffers[index][kind+'_bytes'];
    if(!actual||!actual.has_data||actual.geometry_key!==candidate.geometry_key||actual.bytes!==expected)return false;
    if(actual.request_id===candidate.request_id)return true;
    const prior=previous?.bindings[index]?.[kind];
    return !changed&&prior?.id===actual.id&&prior.geometry_key===actual.geometry_key;
  }));
}

function sourceHashes() {
  const files=fs.readdirSync(path.join(ROOT,'src','box_studio')).filter(name=>name.endsWith('.py')).sort().map(name=>'src/box_studio/'+name);
  files.push('scripts/ui_test_server.py','scripts/verify_box_e2e_exports.py','scripts/check_box_performance.cjs');
  for(const relative of (process.env.ORCA_PERF_SOURCE_EXTRAS||'').split(',').filter(Boolean)) {
    const absolute=path.resolve(ROOT,relative);
    assert.ok(absolute.startsWith(ROOT+path.sep),'Extra source hashes must stay inside this project');
    files.push(path.relative(ROOT,absolute).replaceAll(path.sep,'/'));
  }
  return Object.fromEntries(files.map(relative=>[relative,crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,relative))).digest('hex')]));
}

// The wrapper changes only the declared development bootstrap preset and adds
// timing observations around actual controller calls. No target is generated
// before its real GUI click. No production file is edited.
const PYTHON_SERVER=String.raw`
import copy, importlib.util, json, os, sys, threading, time
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'scripts'))
spec = importlib.util.spec_from_file_location('box_performance_server', root / 'scripts' / 'ui_test_server.py')
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)
from box_studio.presets_catalog import BUILTIN_PRESETS
presets = {item['id']: item for item in BUILTIN_PRESETS}
bootstrap = sys.argv[2]
dev.controller.set_current_params(copy.deepcopy(presets[bootstrap]['params']))
local = threading.local()
original_generate = dev.mod.generate_box_mesh
original_validate = dev.controller._validate_mesh
original_geometry = dev.controller._geometry
original_payload = dev.controller._preview_payload
def observed_generate(*args, **kwargs):
    start = time.perf_counter()
    try:
        return original_generate(*args, **kwargs)
    finally:
        metrics = getattr(local, 'metrics', None)
        if metrics is not None:
            metrics['source_generate_ms'] += (time.perf_counter() - start) * 1000
            metrics['source_generate_calls'] += 1
def observed_validate(*args, **kwargs):
    start = time.perf_counter()
    try:
        return original_validate(*args, **kwargs)
    finally:
        metrics = getattr(local, 'metrics', None)
        if metrics is not None:
            metrics['validation_ms'] += (time.perf_counter() - start) * 1000
            metrics['validation_calls'] += 1
def observed_geometry(*args, **kwargs):
    start = time.perf_counter()
    try:
        return original_geometry(*args, **kwargs)
    finally:
        metrics = getattr(local, 'metrics', None)
        if metrics is not None:
            metrics['geometry_total_ms'] += (time.perf_counter() - start) * 1000
def observed_payload(params):
    metrics = {'source_generate_ms': 0.0, 'source_generate_calls': 0,
               'validation_ms': 0.0, 'validation_calls': 0, 'geometry_total_ms': 0.0,
               'mesh_cache_entries_before': len(dev.controller._mesh_cache),
               'encoded_cache_entries_before': len(dev.controller._encoded_cache)}
    local.metrics = metrics
    start = time.perf_counter()
    try:
        result = original_payload(params)
    finally:
        metrics['payload_total_ms'] = (time.perf_counter() - start) * 1000
        local.metrics = None
    metrics['mesh_cache_entries_after'] = len(dev.controller._mesh_cache)
    metrics['encoded_cache_entries_after'] = len(dev.controller._encoded_cache)
    # These intervals nest. Do not add geometry_total to its child stages.
    metrics['payload_outside_geometry_ms'] = metrics['payload_total_ms'] - metrics['geometry_total_ms']
    metrics['geometry_outside_generation_validation_ms'] = metrics['geometry_total_ms'] - metrics['source_generate_ms'] - metrics['validation_ms']
    return {**result, '_performance_backend': metrics}
dev.mod.generate_box_mesh = observed_generate
dev.controller._validate_mesh = observed_validate
dev.controller._geometry = observed_geometry
dev.controller._preview_payload = observed_payload
server = dev.ThreadingHTTPServer(('127.0.0.1', 0), dev.Handler)
print(json.dumps({'url': 'http://127.0.0.1:' + str(server.server_port),
                  'bootstrap_preset': bootstrap,
                  'preset_params': {key: item['params'] for key, item in presets.items()},
                  'ready_cache': {'mesh': len(dev.controller._mesh_cache),
                                  'encoded': len(dev.controller._encoded_cache)}}), flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
    dev.private.cleanup()
`;

const OBSERVER=String.raw`
(() => {
  const complete = COMPLETE_SEQUENCE;
  const correctBuffers = CORRECT_BUFFERS;
  const state = window.__boxPerformance = {clicks:[],requests:[],replies:[],frames:[],errors:[],bootFrame:null};
  const names = new WeakMap();
  const bufferUploads = new WeakMap(),bufferIds = new WeakMap();
  let activeClick = null, candidate = null, frame = null, bridge,lastVerified = null,nextBufferId=1;
  const now = () => performance.now();
  const clone = value => JSON.parse(JSON.stringify(value));
  const decodedBytes=text=>text.length*3/4-(text.endsWith('==')?2:text.endsWith('=')?1:0);
  document.addEventListener('click', event => {
    const card = event.target.closest?.('.preset-card[data-preset-id]');
    if (!card) return;
    activeClick = {sequence:state.clicks.length+1,preset_id:card.dataset.presetId,
                   click_ms:now(),trusted:event.isTrusted,request_ids:[]};
    state.clicks.push(activeClick);
    candidate = null;
  }, true);
  function observeReply(message, callback) {
    const received = now();
    if (message?.type === 'preview_result') {
      const request = state.requests.findLast(item => item.request_id === message.request_id);
      state.replies.push({request_id:message.request_id,ok:message.ok,received_ms:received,
                         geometry_key:message.geometry_key,params:message.params,
                         message:message.message,backend:message._performance_backend});
      const latest = state.requests.at(-1);
      if (message.ok && request && latest?.request_id === message.request_id) {
        const expected = message.meshes.map(mesh => mesh.triangle_count * 3);
        candidate = {request, received_ms:received, request_id:message.request_id,
          geometry_key:message.geometry_key, params:clone(message.params),
          parts:message.meshes.map(mesh=>mesh.part),expected_indices:expected,
          expected_buffers:message.meshes.map(mesh=>({position_bytes:decodedBytes(mesh.vertices),index_bytes:decodedBytes(mesh.triangles)})),
          base64_characters:message.meshes.reduce((sum,mesh)=>sum+mesh.vertices.length+mesh.triangles.length,0),
          backend:message._performance_backend, first_upload_ms:null,last_upload_ms:null,
          upload_cpu_ms:0,upload_bytes:0,finished:false,click:request.click_sequence ? state.clicks[request.click_sequence-1] : null};
      }
    }
    return callback(message);
  }
  Object.defineProperty(window,'orca',{
    configurable:true,
    get(){return bridge;},
    set(value){
      const originalPost = value.postMessage.bind(value),originalOn=value.onMessage.bind(value);
      value.postMessage = payload => {
        if(payload?.type === 'preview') {
          const request={request_id:payload.request_id,posted_ms:now(),params:clone(payload.params),click_sequence:activeClick?.sequence||null};
          state.requests.push(request);
          if(activeClick)activeClick.request_ids.push(payload.request_id);
        }
        return originalPost(payload);
      };
      value.onMessage = callback => originalOn(message=>observeReply(message,callback));
      bridge=value;
    }
  });
  const proto=window.WebGL2RenderingContext?.prototype;
  if(!proto){state.errors.push('WebGL2 unavailable');return;}
  const originalClear=proto.clear,originalDraw=proto.drawElements,originalBufferData=proto.bufferData;
  const originalLocation=proto.getUniformLocation,originalMatrix=proto.uniformMatrix4fv;
  proto.getUniformLocation=function(program,name){const result=originalLocation.call(this,program,name);if(result)names.set(result,name);return result;};
  proto.uniformMatrix4fv=function(location,transpose,matrix){
    if(frame&&location&&names.get(location)==='u_model')frame.models.push(Array.from(matrix));
    return originalMatrix.call(this,location,transpose,matrix);
  };
  proto.clear=function(mask){
    if(mask&this.COLOR_BUFFER_BIT)frame={started_ms:now(),candidate,indices:[],models:[],bindings:[]};
    return originalClear.apply(this,arguments);
  };
  proto.bufferData=function(target,data,usage){
    const tracked=candidate&&!candidate.finished ? candidate : null,start=now();
    if(tracked&&tracked.first_upload_ms===null)tracked.first_upload_ms=start;
    const result=originalBufferData.apply(this,arguments);
    if(tracked){
      tracked.last_upload_ms=now();tracked.upload_cpu_ms+=tracked.last_upload_ms-start;tracked.upload_bytes+=typeof data==='number'?data:(data?.byteLength||0);
      const buffer=this.getParameter(target===this.ARRAY_BUFFER?this.ARRAY_BUFFER_BINDING:this.ELEMENT_ARRAY_BUFFER_BINDING);
      if(buffer){
        if(!bufferIds.has(buffer))bufferIds.set(buffer,nextBufferId++);
        bufferUploads.set(buffer,{id:bufferIds.get(buffer),geometry_key:tracked.geometry_key,request_id:tracked.request_id,
          bytes:typeof data==='number'?data:(data?.byteLength||0),has_data:typeof data!=='number'&&data!==null});
      }
    }
    return result;
  };
  proto.drawElements=function(mode,count,type,offset){
    const result=originalDraw.apply(this,arguments);
    if(mode!==this.TRIANGLES||!frame?.candidate||frame.candidate.finished)return result;
    frame.indices.push(count);
    const position=this.getVertexAttrib(0,this.VERTEX_ATTRIB_ARRAY_BUFFER_BINDING),index=this.getParameter(this.ELEMENT_ARRAY_BUFFER_BINDING);
    frame.bindings.push({position:position?bufferUploads.get(position):null,index:index?bufferUploads.get(index):null});
    const sample=frame.candidate;
    if(!complete(sample.expected_indices,frame.indices))return result;
    if(type!==this.UNSIGNED_INT||offset!==0){state.errors.push('Unexpected index encoding');return result;}
    if(!correctBuffers(sample,frame.bindings,lastVerified)){
      if(!sample.rejected_frames)sample.rejected_frames=[];
      if(sample.rejected_frames.length<12)sample.rejected_frames.push({indices:[...frame.indices],bindings:frame.bindings});
      return result;
    }
    sample.finished=true;
    const record={request_id:sample.request_id,click_sequence:sample.click?.sequence||null,
      preset_id:sample.click?.preset_id||null,params:sample.params,geometry_key:sample.geometry_key,
      parts:sample.parts,expected_indices:sample.expected_indices,observed_indices:[...frame.indices],models:frame.models,
      buffer_bindings:frame.bindings,rejected_frames:sample.rejected_frames||[],
      click_ms:sample.click?.click_ms??null,posted_ms:sample.request.posted_ms,
      received_ms:sample.received_ms,first_upload_ms:sample.first_upload_ms,last_upload_ms:sample.last_upload_ms,
      upload_cpu_ms:sample.upload_cpu_ms,upload_bytes:sample.upload_bytes,base64_characters:sample.base64_characters,
      first_complete_submit_ms:now(),backend:sample.backend};
    state.frames.push(record);
    const gl=this,sync=gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE,0);
    if(!sync){state.errors.push('GPU fence could not be created');return result;}
    gl.flush();
    const check=()=>{
      const status=gl.clientWaitSync(sync,0,0);
      if(status===gl.WAIT_FAILED){gl.deleteSync(sync);state.errors.push('GPU fence wait failed');return;}
      if(status===gl.TIMEOUT_EXPIRED){requestAnimationFrame(check);return;}
      record.gpu_complete_observed_ms=now();gl.deleteSync(sync);
      lastVerified={geometry_key:record.geometry_key,bindings:record.buffer_bindings};
      requestAnimationFrame(()=>requestAnimationFrame(()=>{
        record.two_raf_after_gpu_ms=now();
        record.complete=true;
        if(!record.click_sequence&&!state.bootFrame)state.bootFrame=record;
      }));
    };
    requestAnimationFrame(check);
    return result;
  };
})();
`.replace('COMPLETE_SEQUENCE',completeIndexSequence.toString()).replace('CORRECT_BUFFERS',correctFrameBuffers.toString());

function startServer(bootstrap) {
  const spawned=performance.now();
  const child=spawn(process.env.ORCA_TEST_PYTHON||'python',['-B','-c',PYTHON_SERVER,ROOT,bootstrap],{
    cwd:ROOT,stdio:['ignore','pipe','pipe'],env:{...process.env,
      ORCA_E2E_BED_X:process.env.ORCA_E2E_BED_X||'260',ORCA_E2E_BED_Y:process.env.ORCA_E2E_BED_Y||'260',ORCA_E2E_BED_Z:process.env.ORCA_E2E_BED_Z||'260'},
  });
  let logs='';child.stderr.on('data',data=>{logs+=data.toString('utf8');});
  const ready=new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(Error('Server startup timeout: '+logs)),45000);
    let text='';child.stdout.on('data',data=>{
      text+=data.toString('utf8');const lines=text.split(/\r?\n/);text=lines.pop();
      for(const line of lines)try{const item=JSON.parse(line);if(item.url){clearTimeout(timer);resolve({...item,process_startup_ms:performance.now()-spawned});}}catch{}
    });
    child.on('error',error=>{clearTimeout(timer);reject(error);});
    child.once('exit',code=>{clearTimeout(timer);reject(Error('Server exited '+code+': '+logs));});
  });
  return {child,ready,logs:()=>logs};
}

async function stopServer(server,url) {
  try{await fetch(url+'/shutdown',{method:'POST',signal:AbortSignal.timeout(3000)});}catch{}
  await new Promise(resolve=>{
    if(server.child.exitCode!==null)return resolve();
    const timer=setTimeout(()=>{server.child.kill();resolve();},5000);
    server.child.once('exit',()=>{clearTimeout(timer);resolve();});
  });
}

function metrics(frame) {
  const subtract=(a,b)=>a===null||a===undefined||b===null||b===undefined ? null : a-b;
  return {...frame,timing:{
    click_to_post_ms:subtract(frame.posted_ms,frame.click_ms),
    post_to_receive_ms:subtract(frame.received_ms,frame.posted_ms),
    backend_payload_ms:frame.backend?.payload_total_ms??null,
    queue_transport_json_poll_ms:frame.backend ? frame.received_ms-frame.posted_ms-frame.backend.payload_total_ms : null,
    receive_to_first_upload_ms:subtract(frame.first_upload_ms,frame.received_ms),
    receive_to_first_complete_submit_ms:frame.first_complete_submit_ms-frame.received_ms,
    upload_cpu_ms:frame.upload_cpu_ms,
    click_to_first_complete_submit_ms:subtract(frame.first_complete_submit_ms,frame.click_ms),
    click_to_gpu_complete_observed_ms:subtract(frame.gpu_complete_observed_ms,frame.click_ms),
    click_to_two_raf_after_gpu_ms:subtract(frame.two_raf_after_gpu_ms,frame.click_ms),
  }};
}

async function runSession(chromium,config,report,mode,target=null) {
  const phase=target?'cold_selection':'after_two_rounds';
  const bootstrap=target==='everyday'?'open_bin_handles':'everyday';
  const server=startServer(bootstrap);let browser,page,url;
  const session={mode,phase,target,bootstrap_preset:bootstrap,measurements:[],errors:[]};
  report.sessions.push(session);
  try {
    const ready=await server.ready;url=ready.url;
    session.process_startup_ms=ready.process_startup_ms;session.ready_cache=ready.ready_cache;
    const launchStart=performance.now();
    browser=await chromium.launch({headless:true,executablePath:process.env.ORCA_CHROMIUM_PATH||undefined,args:config.launch_args});
    session.browser_launch_ms=performance.now()-launchStart;
    const context=await browser.newContext({viewport:mode==='dock'?{width:430,height:900}:{width:1580,height:1090}});
    await context.addInitScript({content:OBSERVER});
    page=await context.newPage();page.setDefaultTimeout(20000);
    page.on('pageerror',error=>session.errors.push(String(error)));
    page.on('console',message=>{if(message.type()==='error')session.errors.push(message.text());});
    const navigateStart=performance.now();
    await page.goto(url+'/?theme=dark&lang=pt'+(mode==='dock'?'&dock':''));
    await page.waitForFunction(()=>window.__boxPerformance?.bootFrame?.complete||window.__boxPerformance?.errors.length,null,{timeout:config.timeout});
    const boot=await page.evaluate(()=>({frame:window.__boxPerformance.bootFrame,errors:window.__boxPerformance.errors,requests:window.__boxPerformance.requests}));
    assert.deepEqual(boot.errors,[]);assert.ok(boot.frame);
    session.open_time_ms=performance.now()-navigateStart;
    session.process_ready_and_open_ms=session.process_startup_ms+session.browser_launch_ms+session.open_time_ms;
    session.boot=metrics(boot.frame);session.bootstrap_requests=boot.requests;
    session.browser_version=browser.version();
    session.gpu=await page.evaluate(()=>{
      const gl=document.querySelector('#gl-canvas').getContext('webgl2'),ext=gl.getExtension('WEBGL_debug_renderer_info');
      const renderer=ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
      return {renderer,vendor:ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):gl.getParameter(gl.VENDOR),
        software_detected:/swiftshader|llvmpipe|softpipe|software|microsoft basic render/i.test(renderer),
        device_pixel_ratio:devicePixelRatio,drawing_buffer:[gl.drawingBufferWidth,gl.drawingBufferHeight]};
    });
    if(target) {
      const expected=ready.preset_params[target];assert.ok(expected,'Preset unavailable: '+target);
      assert.ok(!boot.requests.some(request=>JSON.stringify(request.params)===JSON.stringify(expected)),'Target was requested before its cold selection');
    }
    if(mode==='dock')await page.locator('.dock-tab-btn[data-tab="presets"]').click();
    await page.locator('[data-cat="all"]').click();
    const rounds=target?1:2+config.rounds;
    for(let round=0;round<rounds;round++)for(const id of target?[target]:config.presets) {
      const before=await page.evaluate(()=>window.__boxPerformance.clicks.length);
      await page.locator(`.preset-card[data-preset-id="${id}"]`).click();
      await page.waitForFunction(({before,id})=>{
        const state=window.__boxPerformance,click=state.clicks[before];
        return state.errors.length||(click?.preset_id===id&&state.frames.some(frame=>frame.click_sequence===click.sequence&&frame.complete));
      },{before,id},{timeout:config.timeout});
      const observation=await page.evaluate(before=>{
        const state=window.__boxPerformance,click=state.clicks[before];
        return {click,frame:state.frames.find(frame=>frame.click_sequence===click?.sequence&&frame.complete),errors:state.errors};
      },before);
      assert.deepEqual(observation.errors,[]);assert.ok(observation.frame,'No complete correct-index GPU frame');assert.equal(observation.click.trusted,true);
      const expected=ready.preset_params[id],frame=observation.frame;
      for(const key of Object.keys(expected))assert.deepEqual(frame.params[key],expected[key],'Frame differs from selected preset '+id+' '+key);
      assert.ok(completeIndexSequence(frame.expected_indices,frame.observed_indices));
      const item={mode,phase:target?'cold_selection':round<2?'declared_warmup':'after_two_rounds',round:round+1,preset_id:id,...metrics(frame)};
      session.measurements.push(item);
      console.log(JSON.stringify({mode,preset:id,phase:item.phase,round:round+1,choice_gpu_ms:item.timing.click_to_gpu_complete_observed_ms,backend_ms:item.timing.backend_payload_ms,indices:item.observed_indices}));
      fs.writeFileSync(path.join(config.output,'report.json'),JSON.stringify(report,null,2));
    }
    session.requests=await page.evaluate(()=>window.__boxPerformance.requests);
  } catch(error) {
    session.errors.push(String(error.stack||error));
    if(page) {
      try{session.failure_observation=await page.evaluate(()=>window.__boxPerformance);}catch{}
      try{await page.screenshot({path:path.join(config.output,`failure-${report.sessions.length}.png`)});}catch{}
    }
  } finally {
    if(browser)await browser.close();await stopServer(server,url);
    fs.writeFileSync(path.join(config.output,`backend-${report.sessions.length}.log`),server.logs());
  }
}

async function main() {
  if(process.argv.includes('--self-check')) {
    assert.equal(completeIndexSequence([12,24],[12]),false);
    assert.equal(completeIndexSequence([12,24],[24,12]),false);
    assert.equal(completeIndexSequence([12,24],[12,24]),true);
    assert.equal(completeIndexSequence([],[]),false);
    const candidate={geometry_key:'new',request_id:2,expected_buffers:[{position_bytes:36,index_bytes:12}],first_upload_ms:null,upload_bytes:0};
    const old={position:{id:1,geometry_key:'old',request_id:1,bytes:36,has_data:true},index:{id:2,geometry_key:'old',request_id:1,bytes:12,has_data:true}};
    assert.equal(correctFrameBuffers(candidate,[old],{geometry_key:'old',bindings:[old]}),false,'Equal counts without new uploaded buffers must fail');
    candidate.first_upload_ms=1;candidate.upload_bytes=48;
    assert.equal(correctFrameBuffers(candidate,[old],{geometry_key:'old',bindings:[old]}),false,'Uploads to unrelated buffers cannot validate old bindings');
    const fresh={position:{...old.position,geometry_key:'new',request_id:2},index:{...old.index,geometry_key:'new',request_id:2}};
    assert.equal(correctFrameBuffers(candidate,[fresh],{geometry_key:'old',bindings:[old]}),true);
    assert.equal(correctFrameBuffers({...candidate,request_id:3,first_upload_ms:null,upload_bytes:0},[fresh],{geometry_key:'new',bindings:[fresh]}),true,'Verified identical geometry may reuse its exact buffers');
    new Function(OBSERVER);console.log('PASS frame-index predicates and observer syntax');return;
  }
  const config={presets:(process.env.ORCA_PERF_PRESETS||PRESETS.join(',')).split(','),modes:(process.env.ORCA_PERF_MODES||'page,dock').split(','),
    phase:process.env.ORCA_PERF_PHASE||'all',rounds:Number(process.env.ORCA_PERF_MEASURED_ROUNDS||1),gpu:process.env.ORCA_PERF_GPU||'auto',
    timeout:Number(process.env.ORCA_PERF_TIMEOUT||180000),budget_ms:Number(process.env.ORCA_PERF_BUDGET_MS||2000),
    output:process.env.ORCA_PERF_OUTPUT||path.join(os.tmpdir(),'orca-box-performance-'+crypto.randomUUID())};
  assert.ok(['all','cold','warm'].includes(config.phase));assert.ok(config.rounds>=1&&Number.isInteger(config.rounds));
  assert.ok(['auto','software'].includes(config.gpu),'ORCA_PERF_GPU must be auto or software');
  config.launch_args=config.gpu==='software'
    ? ['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']
    : ['--enable-webgl','--enable-unsafe-swiftshader'];
  assert.ok(config.modes.every(mode=>['page','dock'].includes(mode)));assert.ok(config.presets.every(id=>PRESETS.includes(id)));
  fs.mkdirSync(config.output,{recursive:true});
  const report={started:new Date().toISOString(),complete:false,config,source_hashes:sourceHashes(),sessions:[],
    runtime:{node:process.version,platform:process.platform},method:{native_application_test:false,
      transport:'real isolated Python controller through development HTTP bridge; existing150ms message polling retained',
      first_frame:'correlated latest preview request + exact TRIANGLES index sequence + real attribute0/element buffer bindings tagged with uploaded request/key/byte lengths, followed by nonblocking GPU fence',
      presentation:'GPU completion is observed at RAF polling; two further RAFs are reported separately, not claimed as physical screen presentation',
      cache:'fresh Python and browser processes per cold target; bootstrap explicitlydifferent only for Lip; OS file cache is not flushed',
      warmup:'two complete preset rounds retained in report before measured rounds; no hidden preset clicks',
      backend_stages:'nested timing observations only; original calls/results preserved; source generation andvalidation are children ofgeometry total'}};
  const {chromium}=require(process.env.ORCA_PLAYWRIGHT_MODULE||'playwright');
  try {
    for(const mode of config.modes) {
      if(config.phase!=='warm')for(const target of config.presets)await runSession(chromium,config,report,mode,target);
      if(config.phase!=='cold')await runSession(chromium,config,report,mode);
    }
  } finally {
    report.complete=true;report.finished=new Date().toISOString();
    const measured=report.sessions.flatMap(session=>session.measurements).filter(item=>item.phase!=='declared_warmup');
    report.errors=report.sessions.flatMap(session=>session.errors);
    report.measurements=measured.length;
    report.over_budget=measured.filter(item=>item.timing.click_to_gpu_complete_observed_ms>=config.budget_ms).map(item=>({mode:item.mode,preset_id:item.preset_id,phase:item.phase,ms:item.timing.click_to_gpu_complete_observed_ms}));
    const expected=config.presets.length*config.modes.length*((config.phase!=='warm'?1:0)+(config.phase!=='cold'?config.rounds:0));
    report.valid=report.errors.length===0&&measured.length===expected;
    report.within_budget=report.valid&&report.over_budget.length===0;
    fs.writeFileSync(path.join(config.output,'report.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify({valid:report.valid,within_budget:report.within_budget,measured:report.measurements,errors:report.errors.length,over_budget:report.over_budget,output:config.output},null,2));
    process.exitCode=report.within_budget?0:1;
  }
}

module.exports={completeIndexSequence,correctFrameBuffers};
if(require.main===module)main().catch(error=>{console.error(error);process.exitCode=1;});
