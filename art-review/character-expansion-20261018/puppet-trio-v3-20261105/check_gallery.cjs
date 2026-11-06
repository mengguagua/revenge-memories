'use strict';
// Run the main gallery's actual selector, loader, and draw calls without a browser.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('node:assert/strict');
const base=path.dirname(__dirname),html=fs.readFileSync(path.join(base,'index.html'),'utf8');
const els={},draws=[];let n=0;
class Element {
  constructor(tag,id){
    this.tag=tag;this.id=id;this.dataset={};this.children=[];this.style={};this.attributes={};
    this.classList={toggle(){}};this.value='';this.hidden=false;
    this.nodes={span:{},strong:{}};
  }
  append(...c){this.children.push(...c);}
  replaceChildren(...c){this.children=c;}
  querySelector(k){return this.nodes[k];}
  setAttribute(k,v){this.attributes[k]=v;}
  set innerHTML(html){this.firstElementChild={};this.lastElementChild={};}
  getContext(){
    if(!this.ctx){const ctx={canvas:this,globalAlpha:1,filter:'none',states:[],
      clearRect(){if(this.canvas.id)draws.push({panel:this.canvas.id,clear:true});},
      save(){this.states.push([this.globalAlpha,this.filter]);},
      restore(){[this.globalAlpha,this.filter]=this.states.pop();},
      scale(){},translate(){},
      drawImage(im,...args){if(this.canvas.id)draws.push({panel:this.canvas.id,file:im.src,alpha:this.globalAlpha,filter:this.filter,crop:args.slice(0,4)});}
    };this.ctx=ctx;}return this.ctx;
  }
}
for(const a of html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"[^>]*>/g))els[a[2]]=new Element(a[1],a[2]);
const body=new Element('body');body.dataset.defaultAction=html.match(/data-default-action="([^"]+)"/)[1];
class MockImage{
  set src(v){
    this.file=v;const f=path.resolve(base,decodeURIComponent(v));const b=fs.readFileSync(f);
    if(b.subarray(1,4).toString()==='PNG'){this.width=b.readUInt32BE(16);this.height=b.readUInt32BE(20);}
    else {this.width=256;this.height=160;}
    this.onload();
  }
  get src(){return this.file;}
}
const sandbox={console,Image:MockImage,URLSearchParams,location:{search:''},requestAnimationFrame(){},
  document:{body,createElement:tag=>new Element(tag),getElementById:id=>els[id]||null,addEventListener(){}}};
sandbox.window=sandbox;vm.createContext(sandbox);
for(const match of html.matchAll(/<script src="([^"]+)"/g)){
  const filename=match[1].split('?')[0];
  vm.runInContext(fs.readFileSync(path.join(base,filename),'utf8'),sandbox,{filename});
}
const check=(b,label)=>{assert(b,label);n++;};
const settle=()=>new Promise(res=>setImmediate(res));
const latest=panel=>{
  const i=draws.findLastIndex(e=>e.panel===panel&&e.clear);
  return draws.slice(i+1).filter(e=>e.panel===panel&&!e.clear);
};
const forFile=(panel,s)=>latest(panel).filter(x=>x.file.includes(s));
const ui=sandbox.motionReview;
async function seek(action,tick){draws.length=0;ui.select('puppet-trio-'+action);await settle();ui.seek(tick);}
(async()=>{
 await settle();
 check(ui.getState().action==='puppet-trio-cyclops-intact-aura','Main loads V3 by default');
 check(els['new-missing'].hidden&&els['old-missing'].hidden,'Both panels load');
 ui.seek(30);
 for(const panel of ['original','redrawn']){
  check(forFile(panel,'healing-ground-f25').length===1&&forFile(panel,'ally-map').length===6&&forFile(panel,'fx-heal').length===5,'Actual heal draw targets '+panel);
 }
 await seek('cyclops-intact-aura-empty',30);
 check(forFile('redrawn','healing-ground-f25').length===1&&forFile('redrawn','fx-heal').length===0&&forFile('redrawn','ally-map').length===0,'No healing sprite on empty tiles');
 check(els['contact-info'].textContent==='本回合无治疗特效','Empty timeline label');
 await seek('cyclops-broken-walk-up',13);
 check(forFile('original','maps-reference')[0].crop[0]===8*80,'Original uses back-view atlas cell');
 check(forFile('redrawn','maps-09').length===1,'Redrawn rear gait uses next whole pose');
 await seek('owl-intact-attack',32);
 const owl=latest('redrawn');check(owl.findIndex(x=>x.file.includes('jet-climb'))<owl.findIndex(x=>x.file.includes('owl-intact-battle-03'))&&forFile('redrawn','jet-climb').length===1,'Jet behind flying owl');
 await seek('owl-broken-attack',79);check(forFile('redrawn','jet-').length===0,'Broken engine draws no jet');
 await seek('prometheus-life-broken-fire',68);check(forFile('redrawn','flame-crest').length===1,'Long flame impact loads');
 await seek('prometheus-both-broken-defeat',28);
 check(forFile('redrawn','blast-peak').length===1&&forFile('redrawn','battle-00')[0].alpha===0,'In-place explosion removes standing body at peak');
 check(els['contact-info'].textContent==='原地爆炸：第 29 帧','Explosion does not label damage settlement');
 await seek('prometheus-intact-attack',20);
 check(forFile('redrawn','battle-08').length===1,'Attack preview uses the opposite foot sprint pose');
 await seek('prometheus-life-broken-map-idle',23);
 check(forFile('redrawn','maps-18').length===1,'Map idle uses its own breathing frame');
 await seek('prometheus-fire-broken-walk-left',24);
 check(forFile('redrawn','maps-14').length===1,'Left walk uses far-leg contact');
 for(const state of ['intact','fire-broken','life-broken','both-broken']){
  await seek(`prometheus-${state}-walk-down`,24);
  check(forFile('redrawn','-down-r1-02.png').length===1 && forFile('original','maps-down-r1-reference')[0].crop[0]===0 &&
    els['contact-info'].textContent==='下向步态 · 正面双腿交替','Front-facing down-walk uses revised reference and alternate contact '+state);
  ui.seek(36);check(forFile('redrawn','-down-r1-03.png').length===1,'Opposite passing frame loaded '+state);
 }
 const old=sandbox.GALLERY_DATA.actions.find(a=>a.ready&&a.profile==='professions-class-12-enemy-battle');
 assert(old);ui.select(old.id);await settle();ui.seek(old.contactTick??0);
 check(ui.getState().ready&&latest('redrawn').length>0,'Existing archer player unaffected');
 fs.writeFileSync(path.join(__dirname,'qa/gallery-checks.json'),JSON.stringify({passed:true,count:n,scope:'Main player script and recorded canvas draw calls in a non-rendering DOM mock'},null,2)+'\n');
 console.log('MAIN_GALLERY',n,'passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
