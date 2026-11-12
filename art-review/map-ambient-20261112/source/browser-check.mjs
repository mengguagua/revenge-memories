import {spawn} from "node:child_process";
import {writeFileSync} from "node:fs";
import {pathToFileURL} from "node:url";
import assert from "node:assert/strict";
const chrome=spawn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",[
 "--headless","--disable-gpu","--no-first-run","--remote-debugging-pipe",
 "--user-data-dir=/private/tmp/map-ambient-20261112/browser-profile"
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
 for(let n=0;n<120;n++){
  if(await evaluate('document.querySelector("#film")?.readyState>=2 && document.querySelector("#film").duration===8'))return;
  await pause(50);
 }
 throw Error("Video did not become ready");
}
async function picture(name){
 const image=await send("Page.captureScreenshot",{format:"png"});
 writeFileSync("/private/tmp/map-ambient-20261112/"+name+".png",Buffer.from(image.data,"base64"));
}
const timer=setTimeout(()=>{chrome.kill();process.exit(2)},180000);
try{
 const {targetId}=await send("Target.createTarget",{url:"about:blank"});
 ({sessionId}=await send("Target.attachToTarget",{targetId,flatten:true}));
 await send("Runtime.enable");await send("Page.enable");
 await send("Emulation.setDeviceMetricsOverride",{width:1440,height:1250,deviceScaleFactor:1,mobile:false});
 await send("Page.navigate",{url:pathToFileURL(process.argv[2]).href});
 await ready();
 await evaluate('document.querySelector("#play").click()');
 assert.equal(await evaluate('document.querySelector("#film").paused'),true);
 await picture("preview-desktop");
 const codes=await evaluate('[...document.querySelectorAll("[data-map]")].map(b=>b.dataset.map)');
 assert.equal(codes.length,40);
 for(const code of codes){
  await evaluate(`document.querySelector("[data-map=${code}]").click()`);
  for(const view of ["phone","map"]){
   await evaluate(`document.querySelector("[data-view=${view}]").click()`);
   await ready();
   const data=await evaluate('({width:film.videoWidth,height:film.videoHeight,url:film.currentSrc,ready:film.readyState})');
   assert.equal(data.ready>=2,true);
   assert.equal(data.url.endsWith(code+"-"+view+".mp4"),true);
   if(view==="phone")assert.deepEqual([data.width,data.height],[2668,750]);
  }
 }
 await evaluate('document.querySelector("[data-map=F23]").click();document.querySelector("[data-view=phone]").click()');
 await ready();
 await evaluate('film.currentTime=1');
 await pause(200);
 const before=await evaluate('film.currentTime');
 await evaluate('document.querySelector("#step").click()');
 assert.ok(Math.abs((await evaluate('film.currentTime'))-before-1/12)<.015);
 await evaluate('document.querySelector("#play").click()');
 await pause(350);
 assert.ok((await evaluate('film.currentTime'))>before+.1);
 await evaluate('document.querySelector("#play").click()');
 for(const width of [390,667]){
  await send("Emulation.setDeviceMetricsOverride",{width,height:width===390?1100:700,deviceScaleFactor:1,mobile:true});
  await evaluate('document.querySelector("button[data-layout=after]").click()');
  const state=await evaluate(`(()=>{
   const nodes=[...document.querySelectorAll("button")];
   const safe=nodes.every(node=>{
    const box=node.getBoundingClientRect();const r=document.createRange();r.selectNodeContents(node);
    return [...r.getClientRects()].every(a=>a.left>=box.left&&a.right<=box.right&&a.top>=box.top&&a.bottom<=box.bottom);
   });
   return {safe,overflow:document.documentElement.scrollWidth-innerWidth,layout:player.dataset.layout};
  })()`);
  assert.equal(state.safe,true);assert.equal(state.overflow,0);assert.equal(state.layout,"after");
  if(width===390){
   await evaluate('player.scrollIntoView({block:"center"})');await pause(150);
   await picture("preview-mobile");
  }
 }
 assert.deepEqual(exceptions,[]);
 console.log("PASS 80 local MP4s decoded, 40 map switches, shared-clock playback, pause and frame-step, mobile390/667, text-safe controls");
}finally{
 clearTimeout(timer);chrome.kill();
}
