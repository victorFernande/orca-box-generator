/* Deterministic regression for E2E response correlation; no product or browser. */
'use strict';
const assert=require('node:assert/strict');
const {Studio,withCleanup}=require('./check_box_e2e.cjs');

function preview(id,params,ok=true) {
  return {type:'preview_result',request_id:id,ok,meshes:ok ? 2 : 0,params};
}

async function scenario(name,initial,arrive,expected={},success=true,reject=false) {
  const previous=global.window;
  global.window={...initial,OrcaBoxStudio:{getState:()=>({style:'lip_snap',gasket_enabled:false,...expected})}};
  let rejectedStale=false;
  const page={
    async evaluate(fn,arg){return fn(arg);},
    async waitForFunction(fn,arg){
      assert.equal(fn(arg),false,name+': stale response must not satisfy the wait');
      rejectedStale=true;arrive(global.window);
      assert.equal(fn(arg),true,name+': correlated response must satisfy the wait');
    },
  };
  try {
    const studio=new Studio(page,'http://unused.invalid');
    if(reject) {
      await assert.rejects(studio.waitPreview({host:0,sent:0},expected,success),error=>{
        assert.match(error.message,/Preview rejected for latest request 2: rejected geometry/);
        assert.equal(error.e2eDetails.request.request_id,2);
        assert.equal(error.e2eDetails.reply.ok,false);
        return true;
      });
    } else {
      const message=await studio.waitPreview({host:0,sent:0},expected,success);
      assert.equal(message.request_id,2);
    }
    assert.equal(rejectedStale,true);
    console.log('PASS '+name);
  } finally {global.window=previous;}
}

(async()=>{
  const final={style:'lip_snap',gasket_enabled:false};
  const pending=[{type:'preview',request_id:1},{type:'preview',request_id:2}];
  await scenario('same style, older gasket state',{
    __sentMessages:pending,__hostMessages:[preview(1,{style:'lip_snap',gasket_enabled:true})],
  },w=>w.__hostMessages.push(preview(2,final)),{style:'lip_snap'});
  await scenario('identical parameters still require the latest request',{
    __sentMessages:pending,__hostMessages:[preview(1,final)],
  },w=>w.__hostMessages.push(preview(2,final)),final);
  await scenario('old error cannot satisfy a new rejection assertion',{
    __sentMessages:pending,__hostMessages:[preview(1,final,false)],
  },w=>w.__hostMessages.push(preview(2,final,false)),{},false);
  await scenario('a deferred request must actually be sent',{
    __sentMessages:[],__hostMessages:[preview(1,final)],
  },w=>{w.__sentMessages.push({type:'preview',request_id:2});w.__hostMessages.push(preview(2,final));},final);
  await scenario('an old error cannot reject the current successful request',{
    __sentMessages:pending,__hostMessages:[preview(1,final,false)],
  },w=>w.__hostMessages.push(preview(2,final)),final);
  await scenario('a latest correlated error rejects immediately instead of timing out',{
    __sentMessages:pending,__hostMessages:[preview(1,final,false)],
  },w=>w.__hostMessages.push({...preview(2,final,false),message:'rejected geometry'}),final,true,true);
  await scenario('an intermediate success waits for the final debounced parameters',{
    __sentMessages:[{type:'preview',request_id:1}],__hostMessages:[preview(1,{...final,width_x:90})],
  },w=>{w.__sentMessages.push({type:'preview',request_id:2});w.__hostMessages.push(preview(2,{...final,width_x:94}));},{...final,width_x:94});
  let cleaned=false;
  const original=Error('actual rejected random candidate');
  await assert.rejects(withCleanup(async()=>{throw original;},async()=>{cleaned=true;}),error=>error===original);
  assert.equal(cleaned,true);
  console.log('PASS failed random candidate still restores the fixture');
  await assert.rejects(withCleanup(async()=>{throw original;},async()=>{throw Error('restore failed');}),error=>{
    assert.equal(error,original);
    assert.match(error.e2eDetails.cleanup_error,/restore failed/);
    return true;
  });
  console.log('PASS cleanup failure preserves the original candidate failure');
  await assert.rejects(withCleanup(async()=>42,async()=>{throw Error('restore failed');}),/restore failed/);
  console.log('PASS a successful body does not hide failed cleanup');
})().catch(error=>{console.error(error);process.exitCode=1;});
