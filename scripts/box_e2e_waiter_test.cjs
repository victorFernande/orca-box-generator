/* Deterministic regression for E2E response correlation; no product or browser. */
'use strict';
const assert=require('node:assert/strict');
const {Studio}=require('./check_box_e2e.cjs');

function preview(id,params,ok=true) {
  return {type:'preview_result',request_id:id,ok,meshes:ok ? 2 : 0,params};
}

async function scenario(name,initial,arrive,expected={},success=true) {
  const previous=global.window;
  global.window={...initial,OrcaBoxStudio:{getState:()=>({style:'lip_snap',gasket_enabled:false})}};
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
    const message=await studio.waitPreview({host:0,sent:0},expected,success);
    assert.equal(message.request_id,2);
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
})().catch(error=>{console.error(error);process.exitCode=1;});
