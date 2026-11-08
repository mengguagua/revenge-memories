(() => {
'use strict';
const D=window.PIXELFX_PREVIEW, $=s=>document.querySelector(s);
const root=$('#preview'), before=$('#before'), after=$('#after');
const bc=before.getContext('2d'), ac=after.getContext('2d');
const base=document.createElement('canvas'), candidate=document.createElement('canvas');
base.width=candidate.width=592;base.height=candidate.height=240;
const bg=base.getContext('2d'),cg=candidate.getContext('2d',{willReadFrequently:true});
const chosen=new URLSearchParams(location.search).get('case')||location.hash.slice(1)||D.defaultCase;
const cache=new Map(),tintCache=new Map();let current=D.cases.find(c=>c.key===chosen)||D.cases[0],ready=false,playing=false,time=0,last=0,view=window.innerWidth<620?'native':'close',speed=1,loadId=0,raf;
const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function img(url){if(!cache.has(url))cache.set(url,new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=()=>reject(new Error('图片加载失败：'+url));i.src=D.embeddedImages?.[url]||url;}));return cache.get(url);}
let sheets=[],fx,tintImages=new Map();
for(const c of D.cases){const b=document.createElement('button');b.type='button';b.dataset.case=c.key;b.setAttribute('aria-pressed',String(c===current));const title=document.createElement('span');title.textContent=c.title;const sub=document.createElement('small');sub.textContent=c.tag;b.append(title,sub);b.addEventListener('click',()=>select(c));$('#cases').append(b);}
function updatePlay(){const label=playing?'暂停':'播放';$('#play').textContent=label;$('#play').setAttribute('aria-label',label+'两侧动画');}
function pause(){playing=false;updatePlay();}
function seek(v){time=Math.max(0,Math.min(current.duration,v));render();}
function sourceFrame(){const n=Math.max(0,Math.min(current.timeline.length-1,Math.floor(time*D.fps+1e-6)));return {n,id:current.timeline[n]};}
function render(){
 if(!ready)return;
 const {n,id}=sourceFrame(),a=Math.floor(id/current.atlasFrames),cell=id%current.atlasFrames;
 bg.imageSmoothingEnabled=false;bg.clearRect(0,0,592,240);bg.drawImage(sheets[a],(cell%current.atlasCols)*592,Math.floor(cell/current.atlasCols)*240,592,240,0,0,592,240);
 cg.imageSmoothingEnabled=false;cg.clearRect(0,0,592,240);cg.drawImage(base,0,0);
 if(current.waterTint){
  const boxes=current.waterTint.frames[n]||[],key=id+':'+JSON.stringify(boxes);
  if(tintCache.has(key)){const cached=tintCache.get(key);cg.drawImage(cached.canvas,0,0);root.dataset.waterTintPixels=String(cached.changed);}
  else{
   const changed=WaterPalette.apply(cg,boxes,current.waterTint.palette,tintImages),c=document.createElement('canvas');c.width=592;c.height=240;c.getContext('2d').drawImage(candidate,0,0);tintCache.set(key,{canvas:c,changed});root.dataset.waterTintPixels=String(changed);
  }
 }else root.dataset.waterTintPixels='0';
 const effect=D.effects[current.effect],dt=time-current.trigger,ef=Math.floor(dt*effect.fps+1e-6);
 if(dt>=0&&ef<effect.frames){
  const [w,h]=effect.frameSize,[px,py]=effect.pivot;
  cg.save();cg.beginPath();cg.rect(D.crop[0],0,D.crop[2],128);cg.clip();cg.globalAlpha=current.alpha;
  cg.translate(current.anchor[0],current.anchor[1]);if(current.flip)cg.scale(-1,1);
  cg.drawImage(fx,(ef%effect.columns)*w,Math.floor(ef/effect.columns)*h,w,h,-px,-py,w,h);cg.restore();
 }
 const region=view==='phone'?[0,0,592,240]:D.crop;
 for(const [ctx,canvas,source] of [[bc,before,base],[ac,after,candidate]]){
  if(canvas.width!==region[2]){canvas.width=region[2];canvas.height=region[3];}
  ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(source,...region,0,0,region[2],region[3]);
 }
 $('#scrub').value=n;$('#clock').textContent=time.toFixed(2)+' / '+current.duration.toFixed(2)+' 秒';$('#frame-label').textContent='第 '+(n+1)+' / '+current.timeline.length+' 帧';
 $('#phase').textContent=dt>=0&&ef<effect.frames?'特效反馈':time<current.contact?'动作准备与释放':'受击、收势与回位';
 root.dataset.case=current.key;root.dataset.frame=String(n);root.dataset.fxframe=String(dt>=0&&ef<effect.frames?ef:-1);
}
function layout(){const w=view==='phone'?592:256,scale=view==='close'?2:1;for(const c of [before,after]){c.style.width=(w*scale)+'px';c.style.height=(240*scale)+'px';}document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));render();}
async function select(c){
 const id=++loadId;ready=false;playing=false;current=c;time=0;root.classList.add('loading');updatePlay();
 document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===c.key)));
 document.querySelectorAll('.transport button,#scrub').forEach(b=>b.disabled=true);
 $('#case-title').textContent=c.title;$('#case-description').textContent=c.description;$('#treatment').textContent=c.treatment;$('#notice').textContent=c.notice;
 $('#candidate-label').textContent=c.waterTint?'灰青水色 + PixelFX':'同帧叠加 · 原生像素';$('#water-color').hidden=!c.waterTint;
 $('#phase').textContent='正在加载当前样例…';$('#contact-label').textContent='原结算 '+c.contact.toFixed(2)+' 秒 · 一次结算';
 try{
  const loaded=await Promise.all([...c.atlases,D.effects[c.effect].path,...(c.waterTint?.textures||[])].map(img));if(id!==loadId)return;
  sheets=loaded.slice(0,c.atlases.length);fx=loaded[c.atlases.length];tintImages=new Map((c.waterTint?.textures||[]).map((p,i)=>[p,loaded[c.atlases.length+1+i]]));
  base.width=592;candidate.width=592;ready=true;root.classList.remove('loading');$('#error').style.display='none';
  $('#scrub').max=c.timeline.length-1;document.querySelectorAll('.transport button,#scrub').forEach(b=>b.disabled=false);
  playing=!reduced;last=performance.now();updatePlay();layout();
 }catch(e){$('#error').textContent=e.message+'。请保留页面旁的 assets、data.js 和 player.js。';$('#error').style.display='block';root.classList.remove('loading');console.error(e);}
}
$('#play').addEventListener('click',()=>{playing=!playing;last=performance.now();updatePlay();});
$('#restart').addEventListener('click',()=>{seek(0);playing=true;last=performance.now();updatePlay();});
$('#previous').addEventListener('click',()=>{pause();seek((Math.floor(time*D.fps+1e-6)-1)/D.fps);});
$('#next').addEventListener('click',()=>{pause();seek((Math.floor(time*D.fps+1e-6)+1)/D.fps);});
$('#impact').addEventListener('click',()=>{pause();seek(current.trigger+(['water','core'].includes(current.effect)?.1:1/60));});
$('#water-color').addEventListener('click',()=>{pause();seek(1.30);});
$('#scrub').addEventListener('input',e=>{pause();seek(Number(e.target.value)/D.fps);});
$('#speed').addEventListener('change',e=>{speed=Number(e.target.value);});
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;layout();}));
document.addEventListener('keydown',e=>{if(!ready||['INPUT','SELECT','BUTTON','A'].includes(document.activeElement.tagName))return;if(e.code==='Space'){e.preventDefault();$('#play').click();}if(e.code==='ArrowRight'){e.preventDefault();$('#next').click();}if(e.code==='ArrowLeft'){e.preventDefault();$('#previous').click();}});
document.addEventListener('visibilitychange',()=>{last=performance.now();});
function tick(now){if(ready&&playing&&!document.hidden){time+=Math.max(0,Math.min(.1,(now-last)/1000))*speed;if(time>current.duration)time=0;render();}last=now;raf=requestAnimationFrame(tick);}
raf=requestAnimationFrame(tick);select(current);
})();
