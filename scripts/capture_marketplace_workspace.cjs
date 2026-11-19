/* Capture the real offline Box interface with its isolated verification bridge.
 * Copyright (c) 2026 Orca Box Studio (MIT; see LICENSE).
 * No native app control, user project, external assets or Plater IPC is used.
 */
const fs = require('fs');
const path = require('path');
const {spawn} = require('child_process');
const {chromium} = require(process.env.ORCA_PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const output = process.env.ORCA_MARKETPLACE_OUTPUT || path.join(root, 'assets/marketplace');

(async () => {
  fs.mkdirSync(output, {recursive:true});
  const child = spawn(process.env.ORCA_TEST_PYTHON || 'python', ['-B', path.join(__dirname,'ui_test_server.py')], {cwd:root,stdio:['ignore','pipe','pipe']});
  let browser, logs = '';
  child.stderr.on('data', chunk => {logs += chunk.toString();});
  try {
    const {url} = await new Promise((resolve,reject) => {
      const timer = setTimeout(() => reject(Error('Isolated server timed out: '+logs)),30000);
      let buffered = '';
      child.stdout.on('data', chunk => {
        buffered += chunk.toString();
        const lines = buffered.split(/\r?\n/);buffered = lines.pop();
        for(const line of lines){try{const value=JSON.parse(line);if(value.url){clearTimeout(timer);resolve(value);}}catch{}}
      });
      child.on('error',error=>{clearTimeout(timer);reject(error);});
      child.on('exit',code=>{clearTimeout(timer);reject(Error('Isolated server exited '+code+': '+logs));});
    });
    browser = await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'],...(process.env.ORCA_CHROMIUM_PATH?{executablePath:process.env.ORCA_CHROMIUM_PATH}:{})});
    const page = await browser.newPage({viewport:{width:1580,height:1090},deviceScaleFactor:1});
    const errors=[];page.on('pageerror',error=>errors.push(String(error)));
    await page.route('**/*',route=>new URL(route.request().url()).origin===url?route.continue():route.abort());
    for(const [language,code]of [['pt','pt-BR'],['en','en']]){
      await page.goto(url+'/?theme=light&lang='+language);
      const before=await page.evaluate(()=>window.__hostMessages.filter(message=>message.type==='preview_result').length);
      await page.locator('.preset-card[data-preset-id="tool_rugged"]').click();
      await page.waitForFunction(before=>window.__hostMessages.filter(message=>message.type==='preview_result').slice(before).some(message=>message.ok&&message.params?.style==='rugged_box'&&message.params.width_x===160&&message.params.depth_y===95&&message.params.height_z===35&&message.params.rugged_lid_height===20&&message.meshes===4),before,{timeout:180000});
      await page.locator('#open').press('Home');
      for(let step=0;step<4;step++)await page.locator('#open').press('PageUp');
      await page.waitForFunction(()=>document.querySelector('#open').value==='40');
      await page.locator('[data-cam="fit"]').click();
      await page.evaluate(()=>document.fonts.ready);
      await page.waitForFunction(()=>{
        const toast=document.querySelector('#toast-banner');
        return !toast||Number(getComputedStyle(toast).opacity)===0;
      },{},{timeout:10000});
      if(errors.length)throw Error(errors.join('\n'));
      await page.screenshot({path:path.join(output,'source-workspace-'+code+'.png')});
      console.log('Captured source-workspace-'+code+'.png');
    }
  } finally {
    if(browser)await browser.close();
    child.kill();
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
