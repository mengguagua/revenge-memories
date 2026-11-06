import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
await mkdir(root+'/qa',{recursive:true});
const chrome=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',[
 '--headless=new','--no-sandbox','--disable-gpu','--no-first-run','--no-default-browser-check',
 '--remote-debugging-pipe','--allow-file-access-from-files','--disable-background-networking',
 '--user-data-dir=/private/tmp/water-monkey-review-chrome-20261104'
],{stdio:['ignore','ignore','pipe','pipe','pipe']});
let serial=0,buffer='',stderr='',exited=false;const pending=new Map(),errors=[],checks=[];
chrome.stderr.on('data',b=>{stderr=(stderr+b.toString()).slice(-3000);});
chrome.on('exit',(code,signal)=>{exited=true;for(const p of pending.values()){clearTimeout(p.timeout);p.reject(new Error('Chrome exited '+code+' '+signal+' '+stderr));}pending.clear();});
chrome.stdio[4].on('data',b=>{buffer+=b.toString();let end;while((end=buffer.indexOf('\0'))>=0){const raw=buffer.slice(0,end);buffer=buffer.slice(end+1);if(!raw)continue;const m=JSON.parse(raw);if(m.id){const p=pending.get(m.id);if(p){pending.delete(m.id);clearTimeout(p.timeout);m.error?p.reject(new Error(JSON.stringify(m.error))):p.resolve(m.result);}}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text+' '+(m.params.exceptionDetails.exception?.description||''));}});
function cdp(method,params={},sessionId){return new Promise((resolve,reject)=>{const id=++serial,timeout=setTimeout(()=>{pending.delete(id);reject(new Error('Timeout '+method+' '+stderr));},30000);pending.set(id,{resolve,reject,timeout});chrome.stdio[3].write(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})})+'\0');});}
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const result={checks,errors,screenshots:[],date:'2026-11-04',surface:'headless Chrome only; no Godot or user window activated'};
function check(name,value,detail){checks.push({name,passed:!!value,...(detail===undefined?{}:{detail})});if(!value)throw new Error('Check failed: '+name+' '+JSON.stringify(detail));}
try{
 const {targetId}=await cdp('Target.createTarget',{url:'about:blank'});
 const {sessionId}=await cdp('Target.attachToTarget',{targetId,flatten:true});
 const call=(method,params)=>cdp(method,params,sessionId);
 await call('Runtime.enable');await call('Page.enable');
 const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw new Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;};
 const click=id=>evaluate(`document.getElementById(${JSON.stringify(id)}).click()`);
 const waitFor=async expression=>{for(let i=0;i<80;i++){if(await evaluate(expression))return;await delay(150);}throw new Error('Page not ready: '+expression);};
 const viewport=async(width,height)=>call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
 const screenshot=async name=>{await delay(350);const r=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});const namePath=root+'/source/'+name+'.png';await writeFile(namePath,Buffer.from(r.data,'base64'));result.screenshots.push('source/'+name+'.png');};
 const state=()=>evaluate('waterMonkeyReview.getState()');
 await viewport(1440,1100);await call('Page.navigate',{url:pathToFileURL(root+'/index.html').href});
 await waitFor('!!window.waterMonkeyReview && waterMonkeyReview.ready()');
 check('standalone loaded',true);
 await screenshot('review-desktop');
 await click('enemy-attack');await click('enemy-attack');let s=await state();check('slow never stacks',s.slow&&s.friendHp===14,s);
 await click('friend-act');s=await state();check('slow expires after next action',!s.slow,s);
 await click('reset-example');await click('target-cannon');await click('hit-target');await click('hit-target');s=await state();check('part broken without body damage',s.part===0&&s.body===22&&s.artBroken,s);
 await click('enemy-attack');s=await state();check('broken cannon cannot attack at range',s.friendHp===24,s);
 await evaluate("document.getElementById('enemy-distance').value='1'");await click('enemy-attack');s=await state();check('broken ordinary attack still works',s.friendHp===22&&s.artAction==='water-monkey-broken-melee',s);
 await evaluate("document.getElementById('combat-example').scrollIntoView({block:'start'})");await screenshot('review-broken-combat');
 const states=[];
 for(const broken of [false,true]){
  await evaluate(`waterMonkeyReview.setArtBroken(${broken})`);
  const options=await evaluate("Array.from(document.getElementById('art-action').options).filter(o=>!o.disabled).map(o=>o.value)");
  for(const key of options){await evaluate(`document.getElementById('art-action').value=${JSON.stringify(key)};document.getElementById('art-action').dispatchEvent(new Event('change'))`);await waitFor('waterMonkeyReview.ready()');const a=await state();check('animation '+broken+' '+key,!!a.artAction,a.artAction);states.push(a.artAction);}
 }
 result.animation_states=states;
 await click('reset-example');await click('target-cannon');await click('hit-target');await click('hit-target');await click('remove-human');s=await state();check('escape movement bonus applies once',s.humans===0&&await evaluate("document.getElementById('move-number').textContent==='8'"),s);
 await click('escape-turn');s=await state();check('first escape turn moves eight cells',s.x===29&&!s.escaped&&s.artAction==='water-monkey-broken-escape',s);
 await click('escape-turn');s=await state();check('edge arrival removes unit with zero kill experience',s.x===31&&s.escaped&&await evaluate("document.getElementById('map-marker').hidden&&document.getElementById('experience-result').textContent.includes('经验0')"),s);
 await click('reset-example');for(let i=0;i<4;i++)await click('hit-target');s=await state();check('body kill needs no part destruction and gets 1.5x',s.body===0&&s.part===10&&await evaluate("document.getElementById('experience-result').textContent.includes('53')"),s);
 await click('reset-example');await viewport(390,844);await evaluate('scrollTo(0,0)');await delay(250);await screenshot('review-mobile');
 const layout=await evaluate(`(() => {const bad=[];for(const e of document.querySelectorAll('button,select,.card h2,.health-label,.state-line')){const r=e.getBoundingClientRect(),s=getComputedStyle(e);if(r.width&&r.height&&(e.scrollWidth>e.clientWidth+2||e.scrollHeight>e.clientHeight+2))bad.push({tag:e.tagName,text:e.textContent.slice(0,60),scroll:[e.scrollWidth,e.scrollHeight],client:[e.clientWidth,e.clientHeight]});}return {width:innerWidth,documentWidth:document.documentElement.scrollWidth,bad};})()`);
 check('mobile no viewport overflow',layout.documentWidth<=390,layout);check('mobile text has enough room',layout.bad.length===0,layout);
 await viewport(1440,1100);await call('Page.navigate',{url:pathToFileURL(path.join(root,'..','index.html')).href+'?action=water-monkey-broken-melee#motion-player'});
 await waitFor("!!window.motionReview && motionReview.getState().action==='water-monkey-broken-melee' && document.getElementById('new-missing').hidden");
 check('main gallery loads broken action',true);
 const history=await evaluate("({count:document.querySelectorAll('#revision-history').length,open:document.getElementById('revision-history').open,oldRecordsInside:['runtime-sync-20261102','bow-progression','sniper-progression'].every(id=>document.getElementById('revision-history').contains(document.getElementById(id))),selectorsInPlayer:document.getElementById('motion-player').contains(document.getElementById('actor'))})");
 check('single closed history contains upper and later records',history.count===1&&!history.open&&history.oldRecordsInside&&history.selectorsInPlayer,history);
 await evaluate('motionReview.seek(82)');await screenshot('main-broken-melee');
 const originalPixels=await evaluate("(()=>{const c=document.getElementById('original'),p=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<p.length;i+=4)if(p[i])n++;return n;})()");check('new character design baseline is visibly rendered',originalPixels>100,originalPixels);
 await evaluate('scrollTo(0,0)');await screenshot('main-history-closed');
 await evaluate("document.querySelector('#revision-history>summary').click()");check('history toggle works',await evaluate("document.getElementById('revision-history').open"));
 await evaluate("document.getElementById('revision-history').open=false");
 await viewport(390,844);await evaluate('scrollTo(0,0)');await screenshot('main-mobile');
 const mainLayout=await evaluate("({viewport:innerWidth,width:document.documentElement.scrollWidth})");check('main mobile no horizontal overflow',mainLayout.width<=390,mainLayout);
 const ids=await evaluate("GALLERY_DATA.actions.filter(a=>a.id.startsWith('water-monkey-')).map(a=>a.id)");check('new action IDs unique',new Set(ids).size===ids.length,ids.length);
 for(const id of ids){await evaluate(`motionReview.select(${JSON.stringify(id)})`);await waitFor('document.getElementById("new-missing").hidden');}
 check('all new gallery actions load',true,ids.length);
 await viewport(1440,1100);await evaluate("document.getElementById('motion-player').scrollIntoView({block:'start'})");
 for(const [id,tick,name] of [['water-monkey-melee',0,'v2-melee-start'],['water-monkey-melee',35,'v2-melee-approach'],['water-monkey-melee',82,'v2-melee-contact'],['water-monkey-melee',190,'v2-melee-return'],['water-monkey-melee',218,'v2-melee-home'],['water-monkey-broken-melee',82,'v2-broken-melee-contact'],['water-monkey-cannon',53,'v2-water-flight'],['water-monkey-cannon',68,'v2-water-impact'],['water-monkey-hit',0,'v2-hit-dark'],['water-monkey-hit',3,'v2-hit-normal']]){
  await evaluate(`motionReview.select(${JSON.stringify(id)})`);await waitFor('document.getElementById("new-missing").hidden');await evaluate(`motionReview.seek(${tick})`);await screenshot(name);
 }
 const motion=await evaluate(`(()=>{const find=k=>GALLERY_DATA.actions.find(a=>a.key===k&&a.id.startsWith('water-monkey-'));return {idle:find('map-idle').duration,brokenIdle:find('broken-map-idle').duration,melee:['melee','broken-melee'].map(k=>{const a=find(k);return {frames:a.frames.length,contact:a.contactTick,minX:Math.min(...a.frames.map(r=>r.offset[0])),start:a.frames[0].offset,end:a.frames.at(-1).offset,companion:!!a.reviewCompanions?.length};}),hits:['hit','broken-hit'].map(k=>{const a=find(k);return {poses:new Set(a.frames.map(r=>r.frame)).size,tints:[...new Set(a.frames.map(r=>r.tint))],sound:a.soundEvents?.length};}),water:find('cannon').effectIds.map(id=>GALLERY_DATA.effects[id].frame_size)};})()`);
 check('both idle periods about three seconds',motion.idle>2.9&&motion.idle<3.1&&motion.idle===motion.brokenIdle,motion);
 check('both melees approach hit and return to origin',motion.melee.every(m=>m.frames===219&&m.contact===82&&m.minX===-88&&m.start[0]===0&&m.end[0]===0&&m.companion),motion.melee);
 check('hit feedback uses one pose with flashing and hit sound',motion.hits.every(h=>h.poses===1&&h.tints.includes(.35)&&h.tints.includes(1)&&h.sound===1),motion.hits);
 check('water cannon is broad and visible',motion.water.some(s=>s[0]>=52&&s[1]>=24)&&motion.water.some(s=>s[1]>=44),motion.water);
 await evaluate("motionReview.select('water-monkey-hit')");await waitFor('document.getElementById("new-missing").hidden');check('hit sound opt-in control available',await evaluate("!document.getElementById('review-sound').hidden && document.getElementById('review-sound').getAttribute('aria-pressed')==='false'"));
 await evaluate("document.getElementById('review-sound').click()");check('sound toggle works',await evaluate("document.getElementById('review-sound').getAttribute('aria-pressed')==='true'"));await evaluate("document.getElementById('review-sound').click()");
 await evaluate("motionReview.select('professions-class-6-ally-battle--original_class_6_normal')");await waitFor('document.getElementById("new-missing").hidden');check('existing soldier still loads',await evaluate("motionReview.getState().action==='professions-class-6-ally-battle--original_class_6_normal'"));
 check('no browser exceptions',errors.length===0,errors);
}catch(error){result.failure=error.stack;}
finally{await writeFile(root+'/qa/browser-checks.json',JSON.stringify(result,null,2)+'\n');if(!exited)await cdp('Browser.close').catch(()=>{});chrome.kill();}
console.log(JSON.stringify({passed:checks.filter(c=>c.passed).length,total:checks.length,errors:errors.length,failure:result.failure,screenshots:result.screenshots.length}));
if(result.failure)process.exitCode=1;
