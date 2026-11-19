/* Capture the real offline Box interface with its isolated verification bridge.
 * Copyright (c) 2026 Orca Box Studio (MIT; see LICENSE).
 * No native app control, user project, external assets or Plater IPC is used.
 */
const fs = require('fs');
const path = require('path');
const {spawn} = require('child_process');
const {chromium} = require(process.env.ORCA_PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'assets/marketplace');

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
      await page.locator('.preset-card[data-preset-id="clamshell_pip_short"]').click();
      await page.waitForFunction(()=>window.__hostMessages.some(message=>message.type==='preview_result'&&message.ok&&message.params?.style==='clamshell_pip'&&message.meshes===2),{},{timeout:180000});
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
