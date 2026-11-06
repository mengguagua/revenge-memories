const fs=require('fs'),path=require('path');
const {chromium}=require('/Users/gcc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..');
let launched;
async function run(){
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--disable-gpu','--no-sandbox']});
 launched=browser;const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});const problems=[],requests=[];
 page.on('pageerror',e=>problems.push(e.message));page.on('response',r=>{if(r.status()>=400&&!r.url().includes('favicon'))requests.push({url:r.url(),status:r.status()})});
 await page.goto('http://127.0.0.1:8768/art-review/critical-cinema-20261103/',{waitUntil:'networkidle'});await page.waitForFunction(()=>window.cinemaReady);
 await page.evaluate(()=>window.CinemaPreview.seek(1.15,0));await page.screenshot({path:path.join(root,'checks/browser-desktop.png'),fullPage:true});
 const layouts=[];
 for(const [width,height] of [[1440,1100],[1024,900],[390,844]]){
  await page.setViewportSize({width,height});
  const checks=await page.evaluate(()=>{
   const failures=[];
   for(const el of document.querySelectorAll('button,.time-badge,.beat-list span')){
    if(!el.getClientRects().length)continue;const box=el.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(el);const text=range.getBoundingClientRect();
    if(text.width&&((text.left<box.left+2)||(text.right>box.right-2)||(text.top<box.top+1)||(text.bottom>box.bottom-1)))failures.push({text:el.textContent,box:{w:box.width,h:box.height},glyph:{w:text.width,h:text.height}});
   }
   return {viewport:innerWidth,document:document.documentElement.scrollWidth,text_padding:failures};
  });layouts.push(checks);
  if(width===390)await page.screenshot({path:path.join(root,'checks/browser-mobile.png')});
 }
 await page.setViewportSize({width:1440,height:1100});
 const dynamic=[];
 for(let n=0;n<3;n++){
  await page.selectOption('#target',String(n));
  const r=await page.evaluate(n=>{const j=window.CriticalCinema.cases[n];window.CinemaPreview.seek(j.hit-.16,n);return {state:window.CinemaPreview.state,report:window.lastRenderReport}},n);
  dynamic.push({name:r.state.target.name,errors:r.report.errors});await page.locator('#screen').screenshot({path:path.join(root,'checks/dynamic-target-'+n+'.png')});
 }
 await page.locator('#upload').setInputFiles(path.join(root,'assets/target-21_enemy.png'));
 await page.waitForFunction(()=>window.CriticalCinema.getTarget().path==='user-target');
 const uploaded=await page.evaluate(()=>({name:window.CriticalCinema.getTarget().name,path:window.CriticalCinema.getTarget().path}));
 await page.fill('#damage','9999');await page.evaluate(()=>window.CinemaPreview.seek(4.9,0));
 const maxDamage=await page.evaluate(()=>window.lastRenderReport);
 await page.selectOption('#target','0');
 const media=[];
 for(let i=0;i<6;i++){
  const movie=page.locator('video').nth(i);
  const info=await movie.evaluate(async v=>{v.muted=true;await v.play();await new Promise(ok=>{if(v.currentTime>.02)ok();else v.addEventListener('timeupdate',ok,{once:true})});v.pause();return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,ready:v.readyState}});media.push(info);
 }
 await page.locator('.case').nth(5).click();await page.click('#play');const controls=await page.evaluate(()=>({cases:document.querySelectorAll('.case').length,films:document.querySelectorAll('video').length,state:window.CinemaPreview.state}));
 await page.selectOption('#outcome','alive');await page.locator('.case').nth(5).click();await page.click('#sound');await page.waitForTimeout(350);
 const audioOn=await page.evaluate(()=>window.CinemaPreview.audioState);await page.click('#bgm');await page.waitForTimeout(100);const bgmOff=await page.evaluate(()=>window.CinemaPreview.audioState);await page.click('#play');const audioPaused=await page.evaluate(()=>window.CinemaPreview.audioState);
 const themes=await page.locator('#themes audio').count();const soundCues=await page.locator('#sfx-list audio').count();if(themes!==2||soundCues!==34||audioOn.sfxPaused||audioOn.musicPaused||!bgmOff.musicPaused||bgmOff.sfxPaused||!audioPaused.sfxPaused||!audioPaused.musicPaused)throw Error('Audio controls failed '+JSON.stringify({themes,soundCues,audioOn,bgmOff,audioPaused}));
 const report={audio_controls:{themes,soundCues,audioOn,bgmOff,audioPaused},browser:'Headless Chromium; no visible game/editor/window launched',problems,requests,layouts,dynamic,upload:uploaded,max_damage_text_errors:maxDamage.errors,controls,media_playback:media};
 fs.writeFileSync(path.join(root,'checks/browser.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 await browser.close();if(problems.length||requests.length||layouts.some(x=>x.document>x.viewport||x.text_padding.length))process.exitCode=1;
}
run().catch(async e=>{console.error(e);if(launched)await launched.close();process.exitCode=1});
