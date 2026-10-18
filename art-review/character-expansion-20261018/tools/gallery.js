'use strict';
(() => {
  const data = window.GALLERY_DATA;
  const $ = id => document.getElementById(id);
  const cache = new Map();
  let active = null, profile = null, tick = 0, playing = false, speed = 1, close = false;
  let last = null, accumulated = 0, selection = 0;
  let mapGround = true;
  const contexts = [$('original').getContext('2d'), $('redrawn').getContext('2d')];
  const option = (value, name) => { const el = document.createElement('option'); el.value = value; el.textContent = name; return el; };
  function loadImage(path) {
    if (!cache.has(path)) {
      const entry = {image:null, promise:null};
      entry.promise = new Promise(resolve => { const image = new Image(); image.onload = () => { entry.image = image; resolve(image); }; image.onerror = () => resolve(null); image.src = path; });
      cache.set(path, entry);
    }
    return cache.get(path).promise;
  }
  const imageFor = path => cache.get(path)?.image || null;
  function setPlaying(value) { playing = value; last = null; accumulated = 0; $('play').textContent = playing ? '暂停' : '播放'; }
  function viewport(row) {
    if (close && active.context==='battle') {
      const camera=active.closeCamera;
      return [active.origin[0]+(row.offset?.[0]||0)+camera.offset[0],active.origin[1]+(row.offset?.[1]||0)+camera.offset[1],...camera.size];
    }
    if (active?.viewport) return active.viewport;
    return data.viewport;
  }
  function blit(ctx, image, crop, at, logicalSize, flip, alpha=1, tint=1) {
    if (!image) return;
    ctx.save(); ctx.globalAlpha = alpha; ctx.imageSmoothingEnabled = false;
    if (tint !== 1) ctx.filter = `brightness(${tint})`;
    if (flip) { ctx.translate(at[0] + logicalSize[0], at[1]); ctx.scale(-1,1); }
    else ctx.translate(at[0], at[1]);
    ctx.drawImage(image, ...crop, 0,0,...logicalSize); ctx.restore();
  }
  function drawRow(ctx, row, revised, view, bodyOnly=false) {
    const scale = 4;
    const width = Math.round(view[2] * scale), height = Math.round(view[3] * scale);
    if (ctx.canvas.width !== width || ctx.canvas.height !== height) { ctx.canvas.width=width; ctx.canvas.height=height; }
    ctx.clearRect(0,0,width,height); ctx.save(); ctx.scale(scale,scale); ctx.translate(-view[0],-view[1]);
    const ground=mapGround && !bodyOnly && profile.mapGround ? imageFor(profile.mapGround) : null;
    if(ground) blit(ctx,ground,[0,0,ground.width,ground.height],[view[0],view[1]],[view[2],view[3]],false);
    const f = row.frame, flip = (profile.context==='battle'&&profile.side==='enemy') !== !!row.flip;
    const at = [active.origin[0]+(row.offset?.[0]||0)-profile.anchor[0]+(row.shake||0), active.origin[1]+(row.offset?.[1]||0)-profile.anchor[1]];
    if (flip && f < profile.sourceOamCutoff) { at[0] += profile.flipOriginOffset[0]; at[1] += profile.flipOriginOffset[1]; }
    if(revised && !bodyOnly && profile.mapShadow){
      const s=profile.mapShadow,im=imageFor(s.path),delta=s.offset||[0,0];
      if(im) blit(ctx,im,[0,0,im.width,im.height],[active.origin[0]+(row.offset?.[0]||0)+delta[0]-s.size[0]/2,active.origin[1]+(row.offset?.[1]||0)+delta[1]-s.size[1]/2],s.size,false,s.alpha??1);
    }
    const sw=profile.sourceFrameSize[0], sh=profile.sourceFrameSize[1];
    if (revised) {
      const im=imageFor(profile.newFrames[String(f)]);
      if(im) blit(ctx, im, [0,0,im.width,im.height], at,[sw,sh],flip,row.alpha ?? 1,row.tint ?? 1);
    } else {
      blit(ctx,imageFor(profile.sourceAtlas),[(f%profile.sourceColumns)*sw,Math.floor(f/profile.sourceColumns)*sh,sw,sh],at,[sw,sh],flip,row.alpha ?? 1,row.tint ?? 1);
    }
    if(!bodyOnly) for(const effect of row.effects || []) {
      const info=data.effects[effect.sprite]; if(!info) continue;
      const eAt=[effect.position[0]-info.anchor[0],effect.position[1]-info.anchor[1]];
      if(effect.flip) {eAt[0]+=(info.flip_origin_offset?.[0]||0);eAt[1]+=(info.flip_origin_offset?.[1]||0);}
      const im=imageFor(info.path); if(im) blit(ctx,im,[0,0,im.width,im.height],eAt,info.frame_size,!!effect.flip);
    }
    ctx.restore();
  }
  function draw() {
    if(!active) return;
    const row=active.frames[tick]; const view=viewport(row);
    drawRow(contexts[0],row,false,view); drawRow(contexts[1],row,true,view);
    $('scrub').value=String(tick);
    $('time-info').textContent=`第 ${tick+1} / ${active.frames.length} 帧 · 源姿势 ${row.frame} · ${(tick/active.fps).toFixed(3)} / ${active.duration.toFixed(3)} 秒`;
    $('contact-info').textContent=active.key==='idle-pose' ? '剧情形象 · 静止展示' : active.contactTick === null ? (active.context==='battle'?'反应演示 · 不新增效果':'地图步态 · 原节奏') : `${tick===active.contactTick?'结算时刻 · ':''}结算：第 ${active.contactTick+1} 帧`;
  }
  function seek(value) { if(!active)return; tick=Math.max(0,Math.min(active.frames.length-1,value)); accumulated=0; draw(); }
  function links() {
    const links=[...(profile.links||[])];
    if(active.video) links.unshift({label:'下载当前动作视频',href:active.video});
    if(active.closeVideo) links.unshift({label:'下载角色近看视频',href:active.closeVideo});
    if(active.still) links.unshift({label:'查看当前动作静帧',href:active.still});
    if(profile.mapping) links.push({label:'帧映射与制作记录',href:profile.mapping});
    if(active.referenceEvidence)links.push({label:'原作参考校正记录',href:active.referenceEvidence});
    $('links').replaceChildren();
    for(const item of links){const a=document.createElement('a');a.textContent=item.label;a.href=item.href;a.target='_blank';a.rel='noopener';$('links').append(a);}
    if(!links.length) $('links').textContent='当前动作尚无导出文件。';
  }
  function poses() {
    $('poses').replaceChildren();
    for(const f of active.neededFrames){
      const card=document.createElement('article');card.className='pose-card';
      const title=document.createElement('div');title.className='pose-title';
      const a=document.createElement('span');a.textContent=`源姿势 ${f}`;
      const b=document.createElement('span');const available=!!imageFor(profile.newFrames[String(f)]);b.textContent=available?'新稿已就绪':'新稿缺失';title.append(a,b);
      const pair=document.createElement('div');pair.className='pose-stage';
      const old=document.createElement('canvas'),redraw=document.createElement('canvas');pair.append(old,redraw);
      const labels=document.createElement('div');labels.className='pose-labels';labels.innerHTML='<span>原作</span><span>四倍重绘</span>';
      labels.firstElementChild.textContent=active.referenceLabel||'原作';
      card.append(title,pair,labels);$('poses').append(card);
      const row={frame:f,offset:[0,0],flip:false,effects:[]};
      const v=[active.origin[0]-profile.anchor[0],active.origin[1]-profile.anchor[1],...profile.sourceFrameSize];
      drawRow(old.getContext('2d'),row,false,v,true);drawRow(redraw.getContext('2d'),row,true,v,true);
    }
  }
  function catalog() {
    $('catalog').replaceChildren();
    for(const item of data.actions.filter(a=>a.profile===profile.id)){
      const button=document.createElement('button');button.setAttribute('aria-pressed',String(item.id===active.id));
      const title=document.createElement('span');title.textContent=item.name;const state=document.createElement('small');state.textContent=item.ready?'素材齐备':item.sourceReviewPending?'参考复核中':'待补 '+item.missingFrames.length+' 帧';
      button.append(title,state);button.onclick=()=>{$('action').value=item.id;chooseAction(item.id);};$('catalog').append(button);
    }
  }
  async function chooseAction(id) {
    const token=++selection;setPlaying(false);active=data.actions.find(a=>a.id===id);if(!active)return;
    profile=data.profiles.find(p=>p.id===active.profile);tick=0;
    $('map-ground').hidden=!profile.mapGround;
    $('map-ground').setAttribute('aria-pressed',String(mapGround && !!profile.mapGround));
    $('scrub').max=String(active.frames.length-1);$('source-size').textContent=profile.sourceFrameSize.join(' × ')+' 像素';
    $('source-label').textContent=active.referenceLabel||'原作';
    $('ready-state').textContent=active.ready?'素材齐备 · 待验收':active.sourceReviewPending?'参考来源复核中':`尚缺 ${active.missingFrames.length} 个源姿势`;
    $('ready-state').className=active.ready?'status-ready':'status-pending';
    $('action-note').textContent=active.notes+' '+(active.ready||active.sourceReviewPending?'':'缺失姿势：'+active.missingFrames.join('、')+'。');
    $('new-missing').hidden=false;$('new-missing').querySelector('strong').textContent=active.ready?'正在载入素材':active.sourceReviewPending?'参考来源复核中':'本动作素材未齐';
    $('new-missing').querySelector('span').textContent=active.ready?'':active.sourceReviewPending?'正在核对原战术移动的动作表与图块银行，旧素材保留待重审。':`尚缺源姿势 ${active.missingFrames.join('、')}；不回退使用旧图。`;
    catalog();links();draw();
    const paths=[profile.sourceAtlas,...active.neededFrames.map(f=>profile.newFrames[String(f)]).filter(Boolean),...active.effectIds.map(id=>data.effects[id]?.path).filter(Boolean)];
    if(profile.mapGround) paths.push(profile.mapGround);
    if(profile.mapShadow) paths.push(profile.mapShadow.path);
    await Promise.all(paths.map(loadImage));if(token!==selection)return;
    const runtimeMissing=active.neededFrames.filter(f=>!imageFor(profile.newFrames[String(f)]));
    const effectMissing=active.effectIds.filter(id=>!imageFor(data.effects[id]?.path));
    $('old-missing').hidden=!!imageFor(profile.sourceAtlas);
    $('new-missing').hidden=active.ready&&!runtimeMissing.length&&!effectMissing.length;
    if(active.ready&&(runtimeMissing.length||effectMissing.length)){
      $('new-missing').querySelector('strong').textContent='资源加载失败';
      $('new-missing').querySelector('span').textContent='请保持完整文件目录。缺失的新稿和效果未用其他素材替代。';
    }
    poses();draw();
  }
  function chooseProfile(id, actionId) {
    profile=data.profiles.find(p=>p.id===id);const list=data.actions.filter(a=>a.profile===id);
    $('action').replaceChildren(...list.map(a=>option(a.id,a.name+(a.ready?'':a.sourceReviewPending?' · 参考复核中':' · 待补帧'))));
    if(list.length){const chosen=list.some(a=>a.id===actionId)?actionId:list[0].id;$('action').value=chosen;chooseAction(chosen);}
  }
  function chooseActor(id, profileId, actionId) {
    const list=data.profiles.filter(p=>p.actor===id);
    $('profile').replaceChildren(...list.map(p=>option(p.id,p.className+' · '+p.contextName)));
    if(list.length){const chosen=list.some(p=>p.id===profileId)?profileId:list[0].id;$('profile').value=chosen;chooseProfile(chosen,actionId);}
  }
  const actorList=[...new Map(data.profiles.map(p=>[p.actor,p.actorName])).entries()];
  $('actor').replaceChildren(...actorList.map(([id,name])=>option(id,name)));
  $('actor').onchange=event=>chooseActor(event.target.value);$('profile').onchange=event=>chooseProfile(event.target.value);$('action').onchange=event=>chooseAction(event.target.value);
  $('stats').innerHTML=`<span><strong>${data.summary.profiles}</strong> 个场景配置</span><span><strong>${data.summary.ready} / ${data.summary.actions}</strong> 个动作素材齐备</span><span><strong>${data.summary.pending}</strong> 个动作待补帧／复核</span><span>源节奏 <strong>60.0988 fps</strong></span>`;
  $('policy').textContent=data.policy;
  $('play').onclick=()=>setPlaying(!playing);$('previous').onclick=()=>{setPlaying(false);seek(tick-1);};$('next').onclick=()=>{setPlaying(false);seek(tick+1);};$('restart').onclick=()=>{setPlaying(false);seek(0);};$('scrub').oninput=event=>{setPlaying(false);seek(Number(event.target.value));};
  function setSpeed(value){speed=value;for(const [id,n] of [['normal-speed',1],['half-speed',.5],['quarter-speed',.25]])$(id).setAttribute('aria-pressed',String(n===value));}
  $('normal-speed').onclick=()=>setSpeed(1);$('half-speed').onclick=()=>setSpeed(.5);$('quarter-speed').onclick=()=>setSpeed(.25);
  function setView(value){close=value;$('scene').setAttribute('aria-pressed',String(!value));$('close').setAttribute('aria-pressed',String(value));draw();}
  $('scene').onclick=()=>setView(false);$('close').onclick=()=>setView(true);
  function setLight(value){document.body.classList.toggle('light-stage',value);$('dark').setAttribute('aria-pressed',String(!value));$('light').setAttribute('aria-pressed',String(value));}
  $('dark').onclick=()=>{mapGround=false;$('map-ground').setAttribute('aria-pressed','false');setLight(false);draw();};
  $('light').onclick=()=>{mapGround=false;$('map-ground').setAttribute('aria-pressed','false');setLight(true);draw();};
  $('map-ground').onclick=()=>{mapGround=true;$('map-ground').setAttribute('aria-pressed','true');$('dark').setAttribute('aria-pressed','false');$('light').setAttribute('aria-pressed','false');draw();};
  document.addEventListener('keydown',event=>{if(event.target.matches('input,button,textarea,select')||event.altKey||event.ctrlKey||event.metaKey)return;if(event.code==='Space'){event.preventDefault();setPlaying(!playing);}if(event.code==='ArrowLeft'||event.code==='ArrowRight'){event.preventDefault();setPlaying(false);seek(tick+(event.code==='ArrowRight'?1:-1));}});
  document.addEventListener('visibilitychange',()=>{last=null;});
  function animate(now){if(playing&&active){if(last!==null){accumulated+=(now-last)/1000*active.fps*speed;const steps=Math.floor(accumulated);if(steps){accumulated-=steps;tick=(tick+steps)%active.frames.length;draw();}}last=now;}requestAnimationFrame(animate);}
  const requestedId=new URLSearchParams(location.search).get('action')||document.body.dataset.defaultAction;
  const requested=data.actions.find(a=>a.id===requestedId);
  const requestedProfile=data.profiles.find(p=>p.id===requested?.profile);
  if(actorList.length){const actor=requestedProfile?.actor||actorList[0][0];$('actor').value=actor;chooseActor(actor,requestedProfile?.id,requested?.id);}requestAnimationFrame(animate);
  window.motionReview={seek:value=>{setPlaying(false);seek(value);},play:()=>setPlaying(true),pause:()=>setPlaying(false),setSpeed,setLight,select:chooseAction,getState:()=>({action:active?.id,tick,playing,speed,ready:active?.ready})};
})();
