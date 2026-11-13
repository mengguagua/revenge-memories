import {spawn} from "node:child_process";
import {writeFileSync} from "node:fs";
import {pathToFileURL} from "node:url";
import assert from "node:assert/strict";
const chrome=spawn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",[
 "--headless","--disable-gpu","--no-first-run","--remote-debugging-pipe",
 "--user-data-dir=/private/tmp/phantom-preview-20261113/phantom-browser-profile"
],{stdio:["ignore","ignore","ignore","pipe","pipe"]});
const pending=new Map();let buffer="",number=0,sessionId;
const exceptions=[];
chrome.stdio[4].setEncoding("utf8");
chrome.stdio[4].on("data",chunk=>{
 buffer+=chunk;const parts=buffer.split("\0");buffer=parts.pop();
 for(const raw of parts){
  const response=JSON.parse(raw);
  if(response.method==="Runtime.exceptionThrown")exceptions.push(response.params);
  const pair=pending.get(response.id);if(!pair)continue;
  pending.delete(response.id);response.error?pair.reject(response.error):pair.resolve(response.result);
 }
});
function send(method,params={},session=sessionId){
 const id=++number;
 chrome.stdio[3].write(JSON.stringify({id,method,params,sessionId:session})+"\0");
 return new Promise((resolve,reject)=>pending.set(id,{resolve,reject}));
}
async function evaluate(expression){
 const r=await send("Runtime.evaluate",{expression,awaitPromise:true,returnByValue:true});
 if(r.exceptionDetails)throw Error(r.exceptionDetails.exception.description);
 return r.result.value;
}
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function ready(){
 for(let i=0;i<120;i++){
  if(await evaluate('film.readyState>=2 && film.duration>3'))return;
  await pause(50);
 }
 throw Error('Video failed to load');
}
async function picture(name){
 const image=await send("Page.captureScreenshot",{format:"png"});
 writeFileSync("/private/tmp/phantom-preview-20261113/"+name+".png",Buffer.from(image.data,"base64"));
}
const timer=setTimeout(()=>{chrome.kill();process.exit(2)},90000);
try{
 const {targetId}=await send('Target.createTarget',{url:'about:blank'});
 ({sessionId}=await send('Target.attachToTarget',{targetId,flatten:true}));
 await send('Runtime.enable');await send('Page.enable');
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1150,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:pathToFileURL(process.argv[2]).href});await ready();
 await picture('preview-desktop');
 let decoded=0;
 for(const code of ['round1','round2','rank2','rank3-capacity']){
  await evaluate(`document.querySelector('[data-case="${code}"]').click()`);
  for(const mode of (code.startsWith('round')?['summon','experience']:['summon'])){
   if(code.startsWith('round'))await evaluate(`document.querySelector('[data-mode="${mode}"]').click()`);
   await ready();
   const data=await evaluate('({width:film.videoWidth,height:film.videoHeight,url:film.currentSrc,paused:film.paused})');
   assert.deepEqual([data.width,data.height],[1334,750]);assert.ok(data.url.endsWith(`${code}-${mode}.mp4`));decoded++;
  }
  if(!code.startsWith('round'))assert.equal(await evaluate('getComputedStyle(document.querySelector("#modes")).display'),'none');
 }
 const at=await evaluate('film.currentTime');await pause(350);assert.ok((await evaluate('film.currentTime'))>at);
 await evaluate('film.pause()');assert.equal(await evaluate('film.paused'),true);
 for(const width of [390,667]){
  await send('Emulation.setDeviceMetricsOverride',{width,height:width===390?1100:750,deviceScaleFactor:1,mobile:true});
  const data=await evaluate(`(()=>{const nodes=[...document.querySelectorAll('button')].filter(n=>n.offsetWidth);return {overflow:document.documentElement.scrollWidth-innerWidth,safe:nodes.every(n=>{const b=n.getBoundingClientRect(),r=document.createRange();r.selectNodeContents(n);return [...r.getClientRects()].every(a=>a.left>=b.left&&a.right<=b.right&&a.top>=b.top&&a.bottom<=b.bottom)})}})()`);
  assert.equal(data.overflow,0);assert.equal(data.safe,true);
  if(width===390){await evaluate('document.querySelector(".screen").scrollIntoView({block:"center"})');await pause(100);await picture('preview-mobile');}
 }
 assert.deepEqual(exceptions,[]);
 console.log(`PASS ${decoded} MP4s decoded; selection/play/pause;390/667mobile;button text safe;no JS errors`);
}finally{clearTimeout(timer);chrome.kill();}
