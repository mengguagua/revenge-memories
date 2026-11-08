(()=>{'use strict';
const D=window.PIXELFX_CATALOG,L=window.PIXELFX_PREVIEW,$=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const sound = window.PIXELFX_SPELL_AUDIO;
const approvedPrefix='assets/base/assets/approved/',approvedPath=p=>approvedPrefix+p.replace(/^assets\//,'');
const effects={...D.effects};for(const[k,v]of Object.entries(L.effects))effects['legacy-'+k]={...v,path:approvedPath(v.path)};
const base=document.createElement('canvas'),candidate=document.createElement('canvas');base.width=candidate.width=592;base.height=candidate.height=240;
const bg=base.getContext('2d'),cg=candidate.getContext('2d',{willReadFrequently:true});
const before=$('#before'),after=$('#after'),bc=before.getContext('2d'),ac=after.getContext('2d');
const hud=$('#native-hud'),hudCtx=hud.getContext('2d'),hudPanel=$('#native-hud-panel');
const images=new Map(),caseCache=new Map(),ghosts=new Map(),tints=new Map();let active=null,layerImages={},effectImages={},reviewImages=new Map(),tintImages=new Map(),ready=false,playing=false,time=0,last=0,speed=1,view=innerWidth<620?'native':'close',loadToken=0,page=0,filtered=[];
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches,reviewKey='revenge-pixelfx-full-review-r5';let changedOnly=true,manualView=false;let reviews={},persistentReviews=true;try{reviews=JSON.parse(localStorage.getItem(reviewKey)||'{}')}catch{persistentReviews=false}
function img(path){if(!images.has(path)){const promise=new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=()=>reject(Error('图片载入失败：'+path));const old=path.startsWith(approvedPrefix)?'assets/'+path.slice(approvedPrefix.length):'';i.src=L.embeddedImages?.[old]||path;});images.set(path,promise);if(images.size>64)images.delete(images.keys().next().value);}return images.get(path);}
function oldCase(key){const c=L.cases.find(c=>'approved-'+c.key===key);return {key,title:c.title,subtitle:c.description,group:'已有对照',family:'approved',duration:c.duration,contact:c.contact,fps:60,size:[592,240],crop:L.crop,field:[L.crop[0],0,256,128],timeline:c.timeline,atlasFrames:c.atlasFrames,atlasCols:c.atlasCols,atlases:{current:c.atlases.map(p=>approvedPath(p)),...(c.cleanAtlases?{clean:c.cleanAtlases.map(p=>approvedPath(p))}:{}),...(c.actorAtlases?{actor:c.actorAtlases.map(p=>approvedPath(p))}:{})},fxPlan:[{effect:'legacy-'+c.effect,start:c.trigger,anchor:c.anchor,flip:c.flip,alpha:c.alpha}],treatment:c.treatment,source:{program:c.variant,contacts:c.contactCalls,engine:'Godot 后台渲染 · 原六项预览'},actionTime:c.waterTint?1.30:c.actionTime||c.contact-.15,impactTime:c.trigger+(['water','core'].includes(c.effect)?.10:1/60),waterTint:c.waterTint,actorPositions:c.actorPositions,legacy:c,...(c.weaponKind==='archery'?{revision:2,legacyArrowEffect:'r2-arrow-archer',fxPlan:[{effect:'r2-bowhit-archer',start:c.contact-.07,anchor:[c.anchor[0],c.anchor[1]-16],flip:c.flip,alpha:1}],treatment:'基础弓手新版：短木杆、轻羽尾与少量风迹。保留原轨迹的一支箭，接触时出现短促银灰亮芒。'}:{})};}
function getCase(meta){if(meta.legacy)return Promise.resolve(oldCase(meta.key));if(caseCache.has(meta.key))return Promise.resolve(caseCache.get(meta.key));return new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='cases/'+encodeURIComponent(meta.key)+'.js';script.onload=()=>{script.remove();const c=window.PIXELFX_CASES?.[meta.key];if(!c)return reject(Error('动画数据为空'));caseCache.set(meta.key,c);if(caseCache.size>6){const old=caseCache.keys().next().value;caseCache.delete(old);delete window.PIXELFX_CASES[old];}resolve(c);};script.onerror=()=>{script.remove();reject(Error('动画数据载入失败'));};document.head.append(script);});}
function recorded(ctx,layer,id){const spec=active.layerSpecs?.[layer],tile=active.layerMap?.[layer]?.[id]??id;const[w,h]=spec?.size||[592,240],[x,y]=spec?.at||[0,0],cell=tile%active.atlasFrames,a=Math.floor(tile/active.atlasFrames);ctx.drawImage(layerImages[layer][a],cell%active.atlasCols*w,Math.floor(cell/active.atlasCols)*h,w,h,x,y,w,h);}
const effectPaths=name=>effects[name].paths||[effects[name].path];
const reviewPaths=c=>[c.cinemaReview?.labelStrip,c.cinemaReview?.normalHud,c.foregroundActor].flatMap(spec=>spec?.paths||[]);
function reviewTile(ctx,spec,n){
 if(!spec)return;
 const id=spec.map[n];
 if(!Number.isInteger(id)||id<0)return;
 const cell=id%spec.cells,image=reviewImages.get(spec.paths[Math.floor(id/spec.cells)]);
 const [w,h]=spec.size,[x,y]=spec.at||[0,0];
 ctx.drawImage(image,cell%spec.cols*w,Math.floor(cell/spec.cols)*h,w,h,x,y,w,h);
}
function effect(name,t,point,flip=false,alpha=1,trailLimit){
 const s=effects[name];if(!s||!point||alpha<=0)return;
 let f=Math.floor(t*s.fps+1e-6);if(f<0)return;
 if(s.loop)f%=s.frames;else if(f>=s.frames)return;
 const cells=s.atlasFrames||s.frames, i=f%cells, a=Math.floor(f/cells);
 const[w,h]=s.frameSize,[px,py]=s.pivot;
 let [left,top,fw,fh]=active.field,right=left+fw;
 if(trailLimit!==undefined) {
  if(flip)right=Math.min(right,trailLimit);
  else left=Math.max(left,trailLimit);
 }
 cg.save();cg.beginPath();cg.rect(left,top,Math.max(0,right-left),fh);cg.clip();cg.globalAlpha=alpha;
 cg.translate(Math.round(point[0]),Math.round(point[1]));if(flip)cg.scale(-1,1);
 cg.drawImage(effectImages[name][a],i%s.columns*w,Math.floor(i/s.columns)*h,w,h,-px,-py,w,h);cg.restore();
}
function effectLayer(n,layer){
 for(const p of active.fxPlan){
  if((p.layer||'front')!==layer||time<p.start||(p.until!==undefined&&time>=p.until))continue;
  let alpha=p.alpha??1;
  if(p.fadeIn)alpha*=Math.max(0,Math.min(1,(time-p.start)/p.fadeIn));
  if(p.fadeOut&&p.until!==undefined)alpha*=Math.max(0,Math.min(1,(p.until-time)/p.fadeOut));
  effect(p.effect,(time-p.start)*(p.rate??1)+(p.offset??0),p.track?p.track[n]:p.anchor,p.flip,alpha,p.trailLimit);
 }
}
function ghost(id){if(!ghosts.has(id)){const c=document.createElement('canvas');c.width=592;c.height=240;const g=c.getContext('2d');g.imageSmoothingEnabled=false;recorded(g,'actor',id);g.globalCompositeOperation='source-in';g.fillStyle='#708e99';g.fillRect(0,0,592,240);ghosts.set(id,c);if(ghosts.size>12)ghosts.delete(ghosts.keys().next().value);}return ghosts.get(id);}
function frame(){const n=Math.max(0,Math.min(active.timeline.length-1,Math.floor(time*60+1e-6)));return{n,id:active.timeline[n]};}
function drawGhosts(n,id){if(!active.actorPositions||!layerImages.actor||time>=active.contact-.04)return;const x=active.actorPositions[n][0];let drew=false;for(const[delay,alpha]of[[.20,.10],[.10,.19]]){const old=Math.max(0,n-Math.round(delay*60));if(Math.abs(active.actorPositions[old][0]-x)>=5){cg.save();cg.beginPath();cg.rect(...active.field);cg.clip();cg.globalAlpha=alpha;cg.drawImage(ghost(active.timeline[old]),0,0);cg.restore();drew=true;}}if(drew)recorded(cg,'actor',id);}
function render(){if(!ready)return;const{n,id}=frame();bg.imageSmoothingEnabled=false;cg.imageSmoothingEnabled=false;bg.clearRect(0,0,592,240);if(layerImages.plate)recorded(bg,'plate',id);recorded(bg,'current',id);cg.clearRect(0,0,592,240);cg.drawImage(base,0,0);
 if(active.waterTint){const boxes=active.waterTint.frames[n]||[],key=id+':'+JSON.stringify(boxes);if(!tints.has(key)){const count=WaterPalette.apply(cg,boxes,active.waterTint.palette,tintImages);const c=document.createElement('canvas');c.width=592;c.height=240;c.getContext('2d').drawImage(candidate,0,0);tints.set(key,{canvas:c,count});if(tints.size>24)tints.delete(tints.keys().next().value);}const v=tints.get(key);cg.drawImage(v.canvas,0,0);$('#viewer').dataset.waterTintPixels=v.count;}
 const endingReplacement = active.replaceEffectsFrom !== undefined && time >= active.replaceEffectsFrom
  && (active.replaceEffectsUntil===undefined || time<active.replaceEffectsUntil);
 if (active.suppressFlash || active.fullReplacement || endingReplacement) recorded(cg, 'clean', id);
 reviewTile(cg,active.cinemaReview?.labelStrip,n);
 const old=active.legacy;
 if(old?.weaponKind==='archery'){recorded(cg,'clean',id);if(old.arrowTips[n])effect(active.legacyArrowEffect||'legacy-arrow',time-old.flightStart,old.arrowTips[n]);}
 else if(active.projectile){const p=active.projectile;if(p.anchors[n]){if(p.kind==='arrow')recorded(cg,'clean',id);effect(p.effect||p.kind,time-p.start,p.anchors[n],p.flip,p.kind==='wake'?.6:1);}}
 drawGhosts(n,id);
 if(old?.weaponKind==='dash-strike')effect('legacy-slash',time-old.slashStart,old.slashAnchor,true,.9);
 effectLayer(n,'back');
 const actor=active.actorPlan, pose=actor?.frames[n-actor.startFrame];
 if(pose)effect(actor.effect,pose[0]/effects[actor.effect].fps,[pose[1],pose[2]],pose[3],pose[4]);
 effectLayer(n,'front');
 if(active.cinemaEffect&&time>=active.contact){if(active.cinemaReplacement)recorded(cg,'clean',id);const p=active.cinemaTargets[n];if(p)effect(active.cinemaEffect,time-active.contact,[p[0],p[1]-4],false,.94);}
 reviewTile(cg,active.foregroundActor,n);
 if(active.cinemaReview){
  hudCtx.imageSmoothingEnabled=false;
  hudCtx.clearRect(0,0,hud.width,hud.height);
  reviewTile(hudCtx,active.cinemaReview.normalHud,n);
  const hp=active.cinemaReview;
  $('#viewer').dataset.targetHp=hp.hpBefore-Math.min(hp.damage,n<hp.firstDropFrame?0:1+Math.floor((n-hp.firstDropFrame)/hp.pointStepFrames));
 }else delete $('#viewer').dataset.targetHp;
 const crop=view==='phone'?[0,0,592,240]:active.crop;
 for(const[ctx,canvas,source]of[[bc,before,base],[ac,after,candidate]]){if(canvas.width!==crop[2]||canvas.height!==crop[3]){canvas.width=crop[2];canvas.height=crop[3];}ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(source,...crop,0,0,crop[2],crop[3]);}
 $('#scrub').value=n;$('#clock').textContent=time.toFixed(2)+' / '+active.duration.toFixed(2)+' 秒';$('#frame-label').textContent='第 '+(n+1)+' / '+active.timeline.length+' 帧';$('#phase').textContent=phaseLabel(active, time);$('#viewer').dataset.case=active.key;$('#viewer').dataset.frame=n;$('#viewer').dataset.time=time.toFixed(3);
}
function phaseLabel(caseData, at) {
 const phase = caseData.spellPhases;
 if(caseData.revision>=4){
  switch(caseData.visualRevision){
   case 'fire':
    return at<phase.charge?'准备':at<phase.release?'原版蓄力':at<phase.arrival?'火球飞行':at<phase.arrival+1.3?'撞击与余焰':'收势与回位';
   case 'ragnarok':
    return at<phase.release?'熔焰蓄势':at<phase.arrival?'贴地火脉':at<caseData.contact?'火环聚焰':'火柱与余烬';
   case 'thunder':
   case 'levin':
    return at<phase.release?'电荷汇聚':at<caseData.contact?'先导电弧':at<caseData.contact+1.15?'回击与地面余电':'收势与回位';
   case 'drain':
    return at<phase.charge?'准备':at<caseData.contact?'目标聚红':at<phase.release?'红珠弹出':at<phase.returnAt+.36?'红珠回流':'收势';
   case 'double':
   case 'spin':
   case 'guard':
    return at<caseData.replaceEffectsFrom?'原演出':at<caseData.actionTime?'蓄势与移步':at<caseData.contact?'挥击':at<caseData.replaceEffectsUntil?'命中与回收':'收势与回位';
  }
 }
 if (caseData.composition) {
  const openingEnd = caseData.composition === 'additive' ? phase.chargeEnd : phase.release;
  if (at < openingEnd) return '开场';
  if (at < caseData.contact) return '原演出';
  if (at >= phase.ending && at < phase.ending + 1.1) return '收尾';
 }
 if (at < caseData.contact) return '动作准备与释放';
 if (at < caseData.contact + 1) return '命中／结果反馈';
 return '收势与回位';
}
function layout(){if(!active)return;const crop=view==='phone'?[0,0,592,240]:active.crop;const hs=view==='close'&&hudPanel.clientWidth>=545?2:1;hud.style.width=256*hs+'px';hud.style.height=112*hs+'px';const stacked=view==='close'&&crop[2]>300;$('.comparison').classList.toggle('stacked',stacked);const available=$('.screen-well').clientWidth;const desired=view==='close'?2:1;let scale=view==='phone'?Math.min(1,available/crop[2]):desired;const pan=view!=='phone'&&crop[2]*scale>available;$('.comparison').classList.toggle('pan-native',pan);$('#native-hint').hidden=!pan;for(const c of[before,after]){c.style.width=crop[2]*scale+'px';c.style.height=crop[3]*scale+'px';}$$('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));$('#scale-label').textContent=Number.isInteger(scale)?scale+'× 整数显示'+(stacked?' · 上下对照':'')+(pan?' · 可横向查看':''):'完整布局适配显示';render();}
function updatePlay(){$('#play').textContent=playing?'暂停':'播放';$('#play').setAttribute('aria-label',(playing?'暂停':'播放')+'两侧动画');}
function pause() {
 playing = false;
 sound.reset();
 updatePlay();
}
function seek(t) {
 if (!active) return;
 sound.reset();
 time = Math.max(0, Math.min(active.duration, t));
 render();
}
function syncReview(){const r=reviews[active?.key]||{};$$('[data-vote]').forEach(b=>b.setAttribute('aria-pressed',String(r.vote===b.dataset.vote)));$('#review-note').value=r.note||'';$('#review-status').textContent=r.vote||r.note?(persistentReviews?'已记录在此浏览器':'本次页面已记录，请导出保存'):'仅记录意见，可导出';}
function saveReview(value){if(!active)return;reviews[active.key]={title:active.title,...reviews[active.key],...value,updated:new Date().toISOString()};try{localStorage.setItem(reviewKey,JSON.stringify(reviews));}catch{persistentReviews=false}syncReview();drawList();}
async function select(key,scroll=false){const meta=D.cases.find(c=>c.key===key);if(!meta)return;const token=++loadToken;ready=false;playing=false;sound.setCase(null);updatePlay();$('#viewer').setAttribute('aria-busy','true');$('#error').hidden=true;$$('.transport button,.phase-controls button,#scrub,.review button,.review input').forEach(e=>e.disabled=true);$('#case-title').textContent=meta.title;$('#case-subtitle').textContent=meta.subtitle+(meta.r5Label?' · '+meta.r5Label:'');$('#group-label').textContent=meta.group;$$('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===key)));if(scroll)$('#viewer').scrollIntoView({behavior:reduced?'auto':'smooth',block:'start'});
 try{const c=await getCase(meta);if(token!==loadToken)return;active=c;ghosts.clear();tints.clear();time=0;if(!manualView)view=innerWidth<620||c.family==='cinema'||c.family==='map'?'native':'close';const peerRow=[...(D.variantRows||[]),...D.progressionRows].find(row=>row.buttons.some(b=>b.case===c.key));$('#tier-peers').replaceChildren();$('#tier-peers').hidden=!peerRow;if(peerRow){const label=document.createElement('span');label.textContent=peerRow.label;$('#tier-peers').append(label);for(const peer of peerRow.buttons){const button=document.createElement('button');button.type='button';button.dataset.case=peer.case;button.textContent=peer.name;button.setAttribute('aria-pressed',String(peer.case===c.key));button.onclick=()=>select(peer.case);$('#tier-peers').append(button);}}const names=new Set(c.fxPlan.map(p=>p.effect));if(c.actorPlan)names.add(c.actorPlan.effect);if(c.projectile)names.add(c.projectile.effect||c.projectile.kind);if(c.cinemaEffect)names.add(c.cinemaEffect);if(c.legacy?.weaponKind==='archery')names.add(c.legacyArrowEffect||'legacy-arrow');if(c.legacy?.weaponKind==='dash-strike')names.add('legacy-slash');const paths=[...Object.values(c.atlases).flat(),...[...names].flatMap(effectPaths),...reviewPaths(c),...(c.waterTint?.textures||[]).map(p=>approvedPath(p))];const loaded=await Promise.all(paths.map(img));if(token!==loadToken)return;const byPath=new Map(paths.map((p,i)=>[p,loaded[i]]));layerImages=Object.fromEntries(Object.entries(c.atlases).map(([k,v])=>[k,v.map(p=>byPath.get(p))]));effectImages=Object.fromEntries([...names].map(k=>[k,effectPaths(k).map(p=>byPath.get(p))]));reviewImages=new Map(reviewPaths(c).map(p=>[p,byPath.get(p)]));hudPanel.hidden=!c.cinemaReview;tintImages=new Map((c.waterTint?.textures||[]).map(p=>[p,byPath.get(approvedPath(p))]));base.width=592;candidate.width=592;
 $('#treatment').textContent=c.treatment;$('#candidate-label').textContent = candidateLabel(c);$('#source-note').textContent='同版 Godot 实机采样基线 · '+c.source.engine.replaceAll('当前','采样时的');$('#source-program').textContent=c.source.program;$('#event-details').replaceChildren();const event=c.source.event;let info=event?[`${c.source.actor} → ${c.source.target}`,`${event.hit?'命中':'未命中'} · 目标生命 ${event.hp_before} → ${event.hp_after}`,...(event.hp_cost?[`施放消耗 ${event.hp_cost} 生命`]:[]),...(event.reflection_damage?[`核心反伤 ${event.reflection_damage} 生命`]:[])]:(c.source.facts||c.source.targets?.map((t,i)=>'目标 '+(i+1)+'：生命 '+t.hp_before+' → '+t.hp_after)||[]);for(const text of info){const span=document.createElement('span');span.textContent=text;$('#event-details').append(span);}$('#contact-label').textContent='原结果时刻 '+c.contact.toFixed(2)+' 秒'+(c.source.contacts===1?' · 一次结算':'');setPhaseControls(c);showSources(c);$('#scrub').max=c.timeline.length-1;$$('.transport button,.phase-controls button,#scrub,.review button,.review input').forEach(e=>e.disabled=false);ready=true;$('#viewer').setAttribute('aria-busy','false');sound.setCase(c);syncReview();playing=!reduced;last=performance.now();updatePlay();layout();try{const url=new URL(location.href);url.searchParams.delete('case');url.hash=key;history.replaceState(null,'',url)}catch{}
 }catch(e){if(token!==loadToken)return;$('#error').textContent=e.message+'。请保留 此文件夹中的 assets、cases 与页面文件。';$('#error').hidden=false;$('#viewer').setAttribute('aria-busy','false');console.error(e);}}
function candidateLabel(c) {
 if (c.waterTint) return '已确认灰青水色 + PixelFX';
 if (c.changeLabel) return c.changeLabel;
 if (c.audioCues) return c.fullReplacement ? 'PixelFX 重制 · 有声' : '原有候选 · 有声';
 return c.revision === 2 ? '职业专属 · R2' : '原有候选';
}
function setPhaseControls(c) {
 $('#charge').hidden = !c.spellPhases && !c.actorPlan;
 $('#charge').textContent = c.composition ? '查看开场' : '查看蓄势';
 $('#action').textContent = c.composition ? '查看原演出'
  : c.waterTint ? '查看水弹颜色' : c.projectile ? '查看飞行' : '查看释放';
 $('#gather').hidden = !c.spellPhases?.gather;
 $('#damage').hidden = !c.cinemaReview;
 $('#hp-stage').hidden = !c.cinemaReview;
 if (c.composition) $('#impact').textContent = '查看收尾';
 else if (c.reaction === 'miss') $('#impact').textContent = '查看闪避';
 else if (c.family === 'support' || c.source.targets?.some(t => t.heal > 0)) $('#impact').textContent = '查看恢复';
 else if (['召唤', '幻影'].includes(c.move)) $('#impact').textContent = '查看入场';
 else if (c.move === '驱邪') $('#impact').textContent = '查看驱邪';
 else $('#impact').textContent = '查看命中';
 if(c.revision>=4){
  if(c.visualRevision==='fire'){$('#charge').textContent='查看原蓄力';$('#action').textContent='查看飞行';}
  if(c.visualRevision==='ragnarok'){$('#action').textContent='查看火脉';$('#impact').textContent='查看火柱';}
  if(['levin','thunder'].includes(c.visualRevision))$('#action').textContent='查看先导';
  if(c.foregroundActor)$('#charge').textContent='查看完整剑身';
  if(c.visualRevision==='drain')$('#action').textContent='查看回流';
  if(c.actorPlan)$('#action').textContent='查看挥击';
 }
}
const upstream='https://github.com/patch-gg/pixelfx/blob/a84159688af3ca37a4be05a0d422b94451b2e24e/src/fx/';
function moduleLink(id){
 const a=document.createElement('a');a.href=upstream+id+'.js';a.textContent=id;
 a.target='_blank';a.rel='noopener';return a;
}
function showSources(c) {
 const links=$('#module-links'),chapters=$('#sound-chapters');
 links.replaceChildren(); links.hidden=!c.pixelFxModules?.length;
 for(const id of c.pixelFxModules||[])links.append(moduleLink(id));
 chapters.replaceChildren();chapters.hidden=!c.audioChapters?.length;
 for(const phase of c.audioChapters||[]){
  const span=document.createElement('span');span.textContent=phase.label+' '+phase.at.toFixed(2)+' 秒';
  chapters.append(span);
 }
}
for(const ref of D.references||[]) {
 const card=document.createElement('article'),name=document.createElement('h3'),video=document.createElement('video');
 name.textContent=ref.name;video.poster=ref.still;video.src=ref.ref;video.preload='none';video.controls=true;video.muted=true;
 video.loop=true;video.playsInline=true;video.width=ref.size[0];video.height=ref.size[1];
 video.setAttribute('aria-label','PixelFX 原库：'+ref.name);
 card.append(name,video,moduleLink(ref.module));$('#stock-list').append(card);
}
const wells=$$('.screen-well');
for(const [i,well] of wells.entries())well.addEventListener('scroll',()=>{
 const peer=wells[1-i];
 if(peer.scrollLeft!==well.scrollLeft)peer.scrollLeft=well.scrollLeft;
});
function caseButton(c,tour=false){const b=document.createElement('button');b.type='button';b.dataset.case=c.key;b.setAttribute('aria-pressed',String(active?.key===c.key));const strong=document.createElement(tour?'span':'strong');strong.textContent=c.title;b.append(strong);const sub=document.createElement(tour?'small':'span');sub.textContent=tour?c.group:c.subtitle;b.append(sub);if(!tour){const tag=document.createElement('small');tag.textContent=c.group+' · '+c.duration.toFixed(1)+' 秒'+(reviews[c.key]?.vote?' · '+reviews[c.key].vote:'');b.append(tag);}b.onclick=()=>select(c.key,true);return b;}
for (const choice of D.revisionRows) {
 const item = D.cases.find(c => c.key === choice.case);
 const button = caseButton(item, true);
 const label = document.createElement('strong');
 label.textContent = choice.name;
 const summary = document.createElement('small');
 summary.textContent = choice.subtitle;
 button.replaceChildren(label, summary);
 $('#revision-list').append(button);
}
for(const row of D.progressionRows){const line=document.createElement('div');line.className='progression-row';const label=document.createElement('h3');label.textContent=row.label;line.append(label);const choices=document.createElement('div');choices.className='progression-choices';for(const choice of row.buttons){const meta=D.cases.find(c=>c.key===choice.case);const button=caseButton(meta,true);button.replaceChildren();const title=document.createElement('strong');title.textContent=choice.name;const sub=document.createElement('small');sub.textContent=choice.subtitle;button.append(title,sub);button.onclick=()=>select(meta.key,true);choices.append(button);}line.append(choices);$('#progression').append(line);}
for(const key of D.featured){const c=D.cases.find(c=>c.key===key);if(c)$('#tour').append(caseButton(c,true));}
const familyOrder=['approved','sword','lance','archery','javelin','lightning-sword','magic','support','monster','mechanical','cinema','map','reaction'];for(const k of familyOrder)if(D.cases.some(c=>c.family===k)){const o=new Option(D.familyNames[k],k);$('#family').add(o);}
const profileNames=new Map();for(const c of D.cases)if(!profileNames.has(c.profile)){let label=c.family==='reaction'?c.title.split(' · ')[0]:c.title.split(' · ')[0];if(c.profile.includes('promoted')||c.profile==='23_ally')label+='（进阶）';profileNames.set(c.profile,D.profileLabels?.[c.profile]||(label+' · '+(c.side==='enemy'?'敌方':c.side==='ally'?'己方':'已完成')));}for(const[k,label]of [...profileNames].sort((a,b)=>a[1].localeCompare(b[1],'zh')))$('#profile').add(new Option(label,k));for(const move of [...new Set(D.cases.map(c=>c.move))].sort((a,b)=>a.localeCompare(b,'zh')))$('#move').add(new Option(move,move));
function filter(){const family=$('#family').value,profile=$('#profile').value,move=$('#move').value,search=$('#search').value.trim().toLowerCase();filtered=D.cases.filter(c=>(!changedOnly||c.revision===D.revision)&&(!family||c.family===family)&&(!profile||c.profile===profile)&&(!move||c.move===move)&&(!search||[c.title,c.subtitle,c.group,c.move,c.profile].join(' ').toLowerCase().includes(search)));page=0;drawList();}
function drawList(){const pages=Math.max(1,Math.ceil(filtered.length/18));page=Math.min(page,pages-1);$('#case-list').replaceChildren(...filtered.slice(page*18,page*18+18).map(c=>caseButton(c)));$('#result-count').textContent='找到 '+filtered.length+' 项 · '+D.cases.length+' 项对照可查看';$('#page-status').textContent=(page+1)+' / '+pages;$('#page-back').disabled=page===0;$('#page-next').disabled=page>=pages-1;}
for(const id of ['family','profile','move'])$('#'+id).addEventListener('change',filter);$('#search').addEventListener('input',filter);$('#changes-only').onclick=()=>{changedOnly=!changedOnly;$('#changes-only').setAttribute('aria-pressed',String(changedOnly));filter()};$('#clear-filters').onclick=()=>{changedOnly=false;$('#changes-only').setAttribute('aria-pressed','false');for(const id of['family','profile','move','search'])$('#'+id).value='';filter();};$('#page-back').onclick=()=>{page--;drawList()};$('#page-next').onclick=()=>{page++;drawList()};filter();
$('#all-critical').onclick=()=>{
 changedOnly=true;$('#changes-only').setAttribute('aria-pressed','true');
 $('#family').value='cinema';for(const id of ['profile','move','search'])$('#'+id).value='';
 filter();$('.library').scrollIntoView({block:'start',behavior:reduced?'auto':'smooth'});
};
for (const label of [
 D.visualUpdates + ' 项画面修订',
 D.cases.length + ' 项实机对照',
 D.criticalCases + ' 段必杀更新飘字'
]) {
 const badge = document.createElement('span');
 badge.textContent = label;
 $('#facts').append(badge);
}
$('#coverage-copy').textContent = '采样目录共 ' + D.cases.length + ' 项。本轮修订 ' + D.visualUpdates
 + ' 项，火球的 ' + D.fireAudioCases + ' 项保留连续音轨，14 段必杀使用普通扣血样式。';
function startPlaying() {
 playing = true;
 last = performance.now();
 updatePlay();
}
$('#play').onclick = () => playing ? pause() : startPlaying();
$('#restart').onclick = () => { seek(0); startPlaying(); };
$('#sound-preview').onclick = async () => {
 const chosen = active;
 if (!ready || !chosen?.audioCues?.length) return;
 if (!await sound.enable() || chosen !== active || !ready) return;
 seek(Math.max(0, chosen.audioCues[0].at - .16));
 startPlaying();
};
$('#previous').onclick=()=>{pause();seek((Math.floor(time*60+1e-6)-1)/60)};$('#next').onclick=()=>{pause();seek((Math.floor(time*60+1e-6)+1)/60)};$('#charge').onclick=()=>{pause();seek(active.chargeTime)};$('#action').onclick=()=>{pause();seek(active.actionTime)};$('#impact').onclick=()=>{pause();seek(active.impactTime)};$('#gather').onclick=()=>{pause();seek(active.spellPhases?.gather||0)};$('#damage').onclick=()=>{pause();seek(active.damageTime)};$('#hp-stage').onclick=()=>{pause();seek(active.hpTime);hudPanel.scrollIntoView({block:'nearest',behavior:reduced?'auto':'smooth'})};$('#scrub').oninput=e=>{pause();seek(Number(e.target.value)/60)};$('#speed').onchange = event => { speed = Number(event.target.value); sound.reset(); };$$('[data-view]').forEach(b=>b.onclick=()=>{manualView=true;view=b.dataset.view;layout()});$$('[data-vote]').forEach(b=>b.onclick=()=>saveReview({vote:reviews[active?.key]?.vote===b.dataset.vote?'':b.dataset.vote}));$('#review-note').addEventListener('change',e=>saveReview({note:e.target.value.trim()}));$('#export-reviews').onclick=()=>{const blob=new Blob([JSON.stringify({revision:D.revision,preview:'combat-polish-r5-20261107',scope:'战斗动作、画面与音效意见',created:new Date().toISOString(),reviews},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='PixelFX-R5-对照意见.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
addEventListener('hashchange',()=>{const key=location.hash.slice(1);if(key!==active?.key)select(key)});addEventListener('resize',layout);document.addEventListener('visibilitychange', () => { last = performance.now(); sound.reset(); });document.addEventListener('keydown',e=>{if(!ready||['INPUT','SELECT','BUTTON','A','SUMMARY'].includes(document.activeElement.tagName))return;if(e.code==='Space'){e.preventDefault();$('#play').click()}else if(e.code==='ArrowRight'){e.preventDefault();$('#next').click()}else if(e.code==='ArrowLeft'){e.preventDefault();$('#previous').click()}});
function tick(now) {
 if (ready && playing && !document.hidden) {
  time += Math.max(0, Math.min(.1, (now - last) / 1000)) * speed;
  if (time > active.duration) time = 0;
  render();
  sound.advance(time, speed);
 }
 last = now;
 requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
select(new URLSearchParams(location.search).get('case') || location.hash.slice(1) || D.defaultCase);
})();
