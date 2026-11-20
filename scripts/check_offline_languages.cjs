/* Isolated seven-locale acceptance test. Never controls an installed OrcaSlicer. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {chromium} = require(process.env.ORCA_PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const output = process.env.ORCA_LANGUAGE_OUTPUT || path.join(root, 'test-output', 'languages');
const locales = ['pt','en','es','it','fr','de','ja'];
const headings = ['Galeria de Modelos','Model Gallery','Galería de modelos','Galleria modelli','Galerie de modèles','Modellgalerie','モデルギャラリー'];
const server = spawn(process.env.ORCA_TEST_PYTHON || 'python', ['-B','-W','error',path.join(__dirname,'ui_test_server.py')], {cwd:root,stdio:['ignore','pipe','pipe']});
let stderr='',browser;
server.stderr.on('data', data=>{stderr+=data.toString();});
const ready = new Promise((resolve,reject)=>{
  const timeout=setTimeout(()=>reject(Error('Isolated backend startup timed out: '+stderr)),30000);
  let pending='';
  server.stdout.on('data', data=>{
    pending+=data.toString();const lines=pending.split(/\r?\n/);pending=lines.pop();
    for(const line of lines){try{const item=JSON.parse(line);if(item.url){clearTimeout(timeout);resolve(item.url);}}catch{}}
  });
  server.once('exit',code=>{clearTimeout(timeout);reject(Error('Isolated backend exited '+code+': '+stderr));});
  server.once('error',reject);
});
const report={locales,cases:[],errors:[],nativeApplicationTest:false};
async function state(page){
  return page.evaluate(()=>({lang:document.documentElement.lang,selected:document.querySelector('#lang-select').value,
    heading:document.querySelector('[data-i18n="sec_presets"]').textContent,
    width:document.querySelector('[data-p="width_x"]').value,name:document.querySelector('#name').value,
    geometryRequests:window.__sentMessages.filter(m=>['preview','update_params'].includes(m.type)).length,
    overflow:document.documentElement.scrollWidth>innerWidth,
    preset:document.querySelector('.preset-name')?.textContent,
    labels:[...document.querySelectorAll('[data-pt]')].map(e=>e.textContent)}));
}
(async()=>{
  fs.mkdirSync(output,{recursive:true});const url=await ready;
  try{
    browser=await chromium.launch({headless:true,...(process.env.ORCA_BROWSER_EXECUTABLE?{executablePath:process.env.ORCA_BROWSER_EXECUTABLE}:{})});
    const context=await browser.newContext();
    const views=[];
    for(const mode of ['page','dock']){
      const page=await context.newPage();await page.setViewportSize({width:mode==='page'?1600:380,height:960});
      page.on('pageerror',error=>report.errors.push(mode+': '+error.message));
      page.on('console',msg=>{if(msg.type()==='error')report.errors.push(mode+': '+msg.text());});
      await page.goto(url+(mode==='dock'?'?dock=1':''));
      await page.waitForFunction(()=>window.__hostMessages?.some(m=>m.type==='preview_result'&&m.ok),null,{timeout:120000});
      views.push({mode,page});
    }
    // Explicit, user-entered text is deliberately identical to a translated source
    // phrase. It must survive locale changes verbatim.
    const primary=views[0].page;
    await primary.locator('#name').fill('Open bin');
    await primary.locator('#name').press('Tab');
    await primary.waitForFunction(()=>window.__hostMessages.some(m=>m.type==='preview_result'&&m.ok&&m.params?.name==='Open bin'),null,{timeout:120000});
    await views[1].page.waitForFunction(()=>document.querySelector('#name').value==='Open bin');
    await views[1].page.waitForFunction(()=>window.__hostMessages.some(m=>m.type==='preview_result'&&m.ok&&m.params?.name==='Open bin'),null,{timeout:120000});
    await primary.locator('#btn-toggle-save-preset').click();
    await primary.locator('#inp-save-preset-name').fill('Open bin');
    await primary.locator('#savePreset').click();
    for(const {page} of views)await page.waitForFunction(()=>[...document.querySelectorAll('.preset-card')].some(card=>card.querySelector('.preset-del-btn')&&card.querySelector('.preset-name').textContent==='Open bin'));
    const initial=await Promise.all(views.map(v=>state(v.page)));
    for(const theme of ['dark','light']){
      for(let index=0;index<locales.length;index++){
        const code=locales[index];await primary.locator('#lang-select').selectOption(code);
        for(let i=0;i<views.length;i++){
          const {mode,page}=views[i];
          await page.waitForFunction(code=>document.documentElement.lang===code,code);
          const actualTheme=await page.locator('html').getAttribute('data-theme');
          if(actualTheme!==theme)await page.locator('#theme').click();
          const actual=await state(page);
          assert.equal(actual.selected,code);assert.equal(actual.heading,headings[index]);
          assert.equal(actual.name,'Open bin');assert.equal(actual.width,initial[i].width);
          assert.equal(actual.geometryRequests,initial[i].geometryRequests,'locale regenerated geometry');
          assert.equal(actual.overflow,false,'document overflow');
          assert(actual.labels.every(text=>text&&text!=='undefined'),'untranslated empty parameter');
          assert(await page.evaluate(()=>[...document.querySelectorAll('.preset-card')].some(card=>card.querySelector('.preset-del-btn')&&card.querySelector('.preset-name').textContent==='Open bin')),'user preset was translated');
          report.cases.push({mode,theme,code,heading:actual.heading,preset:actual.preset,geometryUnchanged:true});
          if(mode==='page'&&((code==='it'&&theme==='light')||(code==='ja'&&theme==='dark')))
            await page.screenshot({path:path.join(output,code+'-'+theme+'.png')});
        }
      }
    }
    await primary.locator('#lang-select').selectOption('it');
    await views[1].page.waitForFunction(()=>document.documentElement.lang==='it');
    const initCount=await primary.evaluate(()=>window.__hostMessages.filter(m=>m.type==='init_state').length);
    await primary.locator('#sync').click();
    await primary.waitForFunction(before=>window.__hostMessages.filter(m=>m.type==='init_state').length>before,initCount);
    assert.equal((await state(primary)).lang,'it','printer sync overwrote manual locale');
    await primary.reload();
    await primary.waitForFunction(()=>document.documentElement.lang==='it'&&window.__hostMessages.some(m=>m.type==='preview_result'&&m.ok),null,{timeout:120000});
    assert.equal((await state(primary)).selected,'it','reload lost manual locale');
    assert.equal((await state(primary)).name,'Open bin');
    report.exports=[];
    for(const selector of ['#stl','#mf']){
      const before=await primary.evaluate(()=>window.__hostMessages.length);
      await primary.locator(selector).click();
      await primary.waitForFunction(before=>window.__hostMessages.slice(before).some(m=>m.type==='action_result'),before,{timeout:120000});
      const result=await primary.evaluate(before=>window.__hostMessages.slice(before).find(m=>m.type==='action_result'),before);
      assert.equal(result.ok,true,JSON.stringify(result));
      assert.equal(result.export_manifest?.verification?.ok,true,'independent export verification failed');
      report.exports.push({format:selector==='#stl'?'stl':'3mf',ok:true,verified:true,files:result.export_manifest.files.length});
      assert.equal((await state(primary)).lang,'it','export overwrote manual locale');
    }
    report.persistence=true;report.crossViewSync=true;report.manualChoiceSurvivesPrinterSync=true;
    assert.deepEqual(report.errors,[]);report.ok=true;
  }finally{
    if(browser)await browser.close();server.kill();
    fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2)+'\n');
  }
  console.log(JSON.stringify({ok:report.ok,cases:report.cases.length,errors:report.errors,output}));
})().catch(error=>{console.error(error);process.exitCode=1;server.kill();});
