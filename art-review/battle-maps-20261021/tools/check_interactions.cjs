/* Script smoke check only. Minimal local DOM doubles; no browser or layout engine. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),html=fs.readFileSync(path.join(root,'index.html'),'utf8');
class Element {
  constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.attrs={};this.dataset={};this.style={};this.events={};this.value='';this.checked=false;this.disabled=false;this.hidden=false;this._text='';this.clientWidth=640;this.clientHeight=500;}
  set textContent(v){this._text=String(v);this.children=[];}
  get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;this._text='';}
  setAttribute(k,v){this.attrs[k]=v;}
  addEventListener(k,v){this.events[k]=v;}
  click(){if(!this.disabled)this.onclick?.({target:this});}
  scrollIntoView(){}
  scrollTo(){}
  getBoundingClientRect(){return {left:0,top:0,width:this.width || 640,height:this.height || 500};}
  getContext(){return new Proxy({},{get:()=>()=>{},set:()=>true});}
}
const ids={},kinds=['all','main','side'].map(v=>Object.assign(new Element('button'),{dataset:{kind:v}}));
const zooms=['fit','1','2'].map(v=>Object.assign(new Element('button'),{dataset:{zoom:v}}));
const inners=[new Element(),new Element()];
for(const match of html.matchAll(/<([a-z][a-z0-9-]*)\b([^>]*\bid="([^"]+)"[^>]*)>/g)){
 const e=new Element(match[1]);e.checked=/\bchecked\b/.test(match[2]);e.hidden=/\bhidden\b/.test(match[2]);ids[match[3]]=e;
}
ids.chapter.value='all';ids.route.value='all';
const descendants=()=>{const list=[];const visit=e=>{list.push(e);e.children.forEach(visit);};Object.values(ids).forEach(visit);return list;};
const document={events:{},getElementById:id=>ids[id],createElement:t=>new Element(t),createTextNode:t=>Object.assign(new Element('#text'),{textContent:t}),addEventListener(k,v){this.events[k]=v;},querySelectorAll(selector){
 if(selector==='[data-kind]')return kinds;if(selector==='[data-zoom]')return zooms;if(selector==='.stage-inner')return inners;
 if(selector==='.overlay-controls input')return Object.keys(ids).filter(k=>k.startsWith('show-')).map(k=>ids[k]);
 if(selector.startsWith('.'))return descendants().filter(e=>(e.className||'').split(' ').includes(selector.slice(1)));
 throw Error('Unsupported selector '+selector);
}};
let checks=0;const check=(value,message)=>{assert.ok(value,message);checks++;};
const context={window:{},document,URL,URLSearchParams,location:{href:'file:///local/index.html',search:''},history:{replaceState(){}},console,Image:class {set src(v){this._src=v;this.onload?.();}}};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'maps-data.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(root,'gallery.js'),'utf8'),context);
const maps=context.window.MAP_CATALOG.maps,state=()=>context.window.mapGalleryState;
const change=(id,value,event='change')=>{ids[id].value=value;ids[id].events[event]({target:ids[id]});};
check(state().selected==='M11' && state().visible===40 && state().imageReady,'初始页面与图片准备');
check(document.querySelectorAll('.map-card').length===40,'40张目录卡片');
for(const map of maps){
 change('map-select',map.code);check(ids['map-title'].textContent.includes(map.name),map.code+'标题');
 check(ids['conditions'].textContent===map.conditions,map.code+'胜负说明');
 check(ids.tactical.width===map.canvas[0] && ids.tactical.height===map.canvas[1],map.code+'完整画布');
 check(ids.objects.children.length===(map.objects.length || 1),map.code+'对象列表');
 for(const b of document.querySelectorAll('.object-card')){b.click();check(ids.inspection.textContent.includes('操作格'),map.code+'操作位置说明');}
 for(const id of ['enemy-list','ally-list','reinforcement-list','boat-list'])for(const b of ids[id].children)if(b.tagName==='BUTTON'){b.click();check(ids.inspection.textContent.length>20,map.code+'单位定位');}
}
change('chapter','5');check(state().visible===7,'第五章筛选');change('route','joint');check(state().visible===2,'合流筛选');
change('search','不存在的关卡','input');check(state().visible===0 && ids['map-content'].hidden && !ids['no-results'].hidden,'无结果状态');
ids['reset-filters'].click();check(state().visible===40 && !ids['map-content'].hidden,'重置筛选');
kinds[2].click();check(state().visible===9,'9张支线');ids['reset-filters'].click();
change('search','书库','input');check(state().visible===1 && state().selected==='S51','地点搜索');ids['reset-filters'].click();
change('map-select','J53');zooms[2].click();check(inners[0].style.width==='1152px','原图完整2倍缩放');
ids['show-grid'].checked=true;ids['show-grid'].events.change();ids['show-blocked'].checked=true;ids['show-blocked'].events.change();
ids.tactical.events.click({clientX:32+6*16+8,clientY:32+12*16+8});check(ids.inspection.textContent.includes('前庭西阵'),'点击合流门阵');
document.events.keydown({key:'Escape',target:{tagName:'BODY'}});check(ids.inspection.textContent.includes('悬停查看'),'清除选点');
ids.next.click();check(state().selected==='J54','下一张');ids.previous.click();check(state().selected==='J53','上一张');
const report=JSON.parse(fs.readFileSync(path.join(root,'verification.json'),'utf8'));
report.script={passed:true,checks,scope:'本地DOM替身执行脚本，覆盖40图切换与全部对象／单位定位、筛选、空结果、缩放和图层；不验证浏览器布局。'};
report.browser={passed:false,status:'unavailable',reason:'CUA browser URL policy rejected file://. No alternate surface or protocol workaround used.',desktop_layout_reviewed:false,mobile_layout_reviewed:false};
fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,checks,maps:maps.length,layout_verified:false}));
