'use strict';
(() => {
  const $=id=>document.getElementById(id), data=window.GALLERY_DATA;
  const imageCache=new Map(), ctx=$('art-canvas').getContext('2d');
  const art={broken:false,playing:true,tick:0,action:null,profile:null,last:0,elapsed:0};
  let soundEnabled=false;
  const hitAudio=new Audio('assets/hit.ogg');hitAudio.volume=.45;
  function soundAt(tick){if(soundEnabled&&(art.action?.soundEvents||[]).some(e=>e.tick===tick)){hitAudio.pause();hitAudio.currentTime=0;hitAudio.play().catch(()=>{});}}
  const local=path=>path.replace(/^water-monkey-v1-20261104\//,'');
  function load(path){path=local(path);if(!imageCache.has(path)){const img=new Image();img.src=path;imageCache.set(path,img);}return imageCache.get(path);}
  function showArt(){
    const key=$('art-action').value;
    const id='water-monkey-'+(art.broken?'broken-':'')+key;
    art.action=data.actions.find(a=>a.id===id);
    art.profile=data.profiles.find(p=>p.id===art.action?.profile);
    art.tick=0;art.elapsed=0;
    if(!art.action){$('art-note').textContent='该状态动作尚未生成，请查看其它动作。';return;}
    for(const f of art.action.neededFrames)load(art.profile.newFrames[String(f)]);
    for(const id of art.action.effectIds)load(data.effects[id].path);
    for(const target of art.action.reviewCompanions||[])load(target.path);
    $('art-note').textContent=art.action.notes;
    if(art.playing)soundAt(0);
  }
  function setBroken(value){
    art.broken=value;$('art-intact').setAttribute('aria-pressed',String(!value));$('art-broken').setAttribute('aria-pressed',String(value));
    $('art-state').textContent=value?'背炮已损坏 · 持续保留':'完整背炮';
    for(const option of $('art-action').options)option.disabled=value&&['cannon','part-break'].includes(option.value);
    if(value&&['cannon','part-break'].includes($('art-action').value))$('art-action').value='melee';
    showArt();
  }
  function drawArt(){
    ctx.clearRect(0,0,768,480);if(!art.action||!art.profile)return;
    ctx.save();ctx.scale(3,3);ctx.imageSmoothingEnabled=false;
    // Inspection framing: close views for the body, full scene for a projectile or exit.
    if(!['cannon','escape'].includes($('art-action').value)&&!art.action.reviewCompanions?.length){
      const zoom=art.profile.context==='battle'?2.4:2.5;
      ctx.translate(128,132);ctx.scale(zoom,zoom);ctx.translate(-art.action.origin[0],-art.action.origin[1]);
    }
    const row=art.action.frames[Math.min(art.tick,art.action.frames.length-1)],p=art.profile;
    for(const target of art.action.reviewCompanions||[]){
      const im=load(target.path);if(!im.complete||!im.naturalWidth)continue;
      ctx.save();ctx.imageSmoothingEnabled=false;const tint=row.companionTint??1;if(tint!==1)ctx.filter=`brightness(${tint})`;
      ctx.translate(target.origin[0]-target.anchor[0]+(row.companionShake||0)+(target.flip?target.size[0]:0),target.origin[1]-target.anchor[1]);if(target.flip)ctx.scale(-1,1);
      ctx.drawImage(im,0,0,...target.size);ctx.restore();
    }
    const img=load(p.newFrames[String(row.frame)]);
    if(img.complete&&img.naturalWidth){ctx.save();ctx.globalAlpha=row.alpha??1;const tint=row.tint??1;if(tint!==1)ctx.filter=`brightness(${tint})`;const flip=(p.context==='battle'&&p.side==='enemy')!==!!row.flip;ctx.translate(art.action.origin[0]+(row.offset?.[0]||0)-p.anchor[0]+(row.shake||0)+(flip?p.sourceFrameSize[0]:0),art.action.origin[1]+(row.offset?.[1]||0)-p.anchor[1]);if(flip)ctx.scale(-1,1);ctx.drawImage(img,0,0,...p.sourceFrameSize);ctx.restore();}
    ctx.globalAlpha=1;
    for(const effect of row.effects||[]){const e=data.effects[effect.sprite],im=load(e.path);if(im.complete&&im.naturalWidth)ctx.drawImage(im,effect.position[0]-e.anchor[0],effect.position[1]-e.anchor[1],...e.frame_size);}
    ctx.restore();
  }
  function animate(now){if(art.playing&&art.action&&art.last){art.elapsed+=(now-art.last)/1000*art.action.fps;const step=Math.floor(art.elapsed);if(step){art.elapsed-=step;for(let i=0;i<Math.min(step,art.action.frames.length);i++){art.tick=(art.tick+1)%art.action.frames.length;soundAt(art.tick);}if(step>art.action.frames.length)art.tick=(art.tick+step-art.action.frames.length)%art.action.frames.length;}}art.last=now;drawArt();requestAnimationFrame(animate);}
  $('art-action').onchange=showArt;$('art-intact').onclick=()=>setBroken(false);$('art-broken').onclick=()=>setBroken(true);
  $('art-play').onclick=()=>{art.playing=!art.playing;$('art-play').textContent=art.playing?'暂停':'播放';$('art-play').setAttribute('aria-pressed',String(art.playing));if(art.playing)soundAt(art.tick);else hitAudio.pause();};
  $('art-sound').onclick=()=>{soundEnabled=!soundEnabled;$('art-sound').setAttribute('aria-pressed',String(soundEnabled));$('art-sound').textContent=soundEnabled?'音效：开':'音效：关';if(!soundEnabled)hitAudio.pause();};
  $('art-step').onclick=()=>{art.playing=false;$('art-play').textContent='播放';$('art-play').setAttribute('aria-pressed','false');art.tick=(art.tick+1)%art.action.frames.length;};
  $('art-reset').onclick=()=>{art.tick=0;art.elapsed=0;};
  $('art-light').onclick=()=>{const on=$('art-stage').classList.toggle('light');$('art-light').setAttribute('aria-pressed',String(on));};

  let state;
  function log(text){$('combat-log').textContent=text;}
  function setMap(){
    const x=(state.x+2.5)*16/576*100,y=(14+2.5)*16/480*100;
    $('map-marker').style.left=x+'%';$('map-marker').style.top=y+'%';
    $('map-marker').hidden=state.escaped||state.body===0;
    $('map-unit').src='assets/'+(state.part===0?'maps-broken-05.png':'maps-05.png');
    $('edge-point').style.left=(33.5*16/576*100)+'%';$('edge-point').style.top=y+'%';
    $('edge-point').style.display=state.humans===0&&!state.escaped&&state.body>0?'block':'none';
  }
  function render(){
    const over=state.body===0||state.escaped,broken=state.part===0;
    $('body-number').textContent=state.body+' / 22';$('cannon-number').textContent=broken?'已破坏 · 0 / 10':state.part+' / 10';
    $('body-bar').style.width=(state.body/22*100)+'%';$('cannon-bar').style.width=(state.part/10*100)+'%';
    $('target-body').setAttribute('aria-pressed',String(state.target==='body'));$('target-cannon').setAttribute('aria-pressed',String(state.target==='part'));
    $('target-cannon').disabled=broken||over;$('target-body').disabled=over;
    $('hit-target').disabled=over||(state.target==='part'&&broken);$('hit-target').textContent='攻击'+(state.target==='body'?'本体':'背炮')+' · 6点';
    $('enemy-attack').disabled=over||state.humans===0||state.friendHp===0;$('friend-act').disabled=state.friendHp===0;
    $('friend-hp').textContent=state.friendHp+' / 24';$('friend-speed').textContent=state.slow?'6 → 5':'6';
    $('slow-note').textContent=state.slow?'减速生效：速度－1，持续至该单位下一次行动结束；再次命中仍为5。':'无减速。水炮命中后速度－1；重复命中只刷新持续时间。';
    $('machine-state').textContent=state.body===0?'本体被击败 · 正常发放击败经验':state.escaped?'已逃离 · 无击败经验':state.humans===0?'撤离中 · 移动8 · 不主动攻击':broken?'背炮已损坏 · 仅掌击可用':'战斗中 · 掌击与水炮可用';
    $('humans-number').textContent=state.humans;$('move-number').textContent=state.humans===0?'8':'5';
    $('remove-human').disabled=state.humans===0||over;$('escape-turn').disabled=state.humans!==0||over;
    if(state.body===0)$('experience-result').textContent='击败：同条件普通经验35 → 53（向上取整）。实际按角色与等级修正。';
    else if(state.escaped)$('experience-result').textContent='逃脱：击败经验0，不计击杀；此前已获得的伤害经验保留。';
    else $('experience-result').textContent='尚未击败或逃脱。';
    setMap();
  }
  function reset(){state={body:22,part:10,friendHp:24,slow:false,target:'body',humans:1,x:21,escaped:false};$('escape-note').textContent='条件未满足，按普通AI作战。规则演示独立于F21的即时胜利结算。';$('art-action').value='idle';setBroken(false);log('先攻击背炮两次，可以看到本体仍为22，水炮永久禁用；也可以直接击败本体。');render();}
  $('target-body').onclick=()=>{state.target='body';render();};$('target-cannon').onclick=()=>{state.target='part';render();};
  $('hit-target').onclick=()=>{
    if(state.escaped||state.body===0)return;
    const before=state[state.target],damage=Math.min(6,before);state[state.target]-=damage;
    if(state.target==='part'){
      log(state.part===0?'背炮耐久归零，永久禁用水炮。本体仍为'+state.body+'；溢出不转移，不发击杀经验。':'背炮受到'+damage+'点伤害，剩余'+state.part+'；本体仍为'+state.body+'。');
      if(state.part===0){setBroken(true);$('art-action').value='idle';showArt();}
    }else{log(state.body===0?'本体被击败；副部位无需清空。同条件普通击败经验35时，这里为53。':'本体受到'+damage+'点伤害，剩余'+state.body+'；背炮耐久不变。');if(state.body===0){setBroken(state.part===0);$('art-action').value='defeat';showArt();}}
    if(state.slow){state.slow=false;log($('combat-log').textContent+' 友方这次行动结束，减速解除。');}
    render();
  };
  $('enemy-attack').onclick=()=>{
    if(state.body===0||state.escaped||state.humans===0)return;
    const distance=Number($('enemy-distance').value);
    if(distance>1&&state.part===0){log('背炮已破坏，距离'+distance+'格无可用攻击；不会用掌击越过射程，也不会偷偷恢复水炮。');return;}
    const cannon=distance>1,damage=cannon?5:2;state.friendHp=Math.max(0,state.friendHp-damage);
    if(cannon){const refreshing=state.slow;state.slow=true;log('水炮固定命中示例：8威力－3物防＝5伤害。'+(refreshing?'再次命中只刷新持续时间，速度仍为5。':'友方速度6→5，持续至下一次行动结束。'));}
    else log('近身默认机械掌击：5威力－3物防＝2伤害，无减速。');
    setBroken(state.part===0);$('art-action').value=cannon?'cannon':'melee';showArt();render();
  };
  $('friend-act').onclick=()=>{state.slow=false;log('友方下一次行动结束，速度恢复为6；没有叠加或永久降低。');render();};
  $('remove-human').onclick=()=>{state.humans=0;$('escape-note').textContent='触发撤离：移动5＋3＝8。不主动攻击。示例最近出口为东侧(31,14)，距离10格；两回合可离场。';log('同阵营只剩机械傀儡，转入撤离。仍可在它到达边缘前击败本体。');render();};
  $('escape-turn').onclick=()=>{if(state.escaped||state.body===0||state.humans!==0)return;const before=state.x;state.x=Math.min(31,state.x+8);state.escaped=state.x===31;$('escape-note').textContent=state.escaped?'第2个撤离回合再走2格，到达(31,14)，立即消失。':'第1个撤离回合走8格：(21,14) → (29,14)，还差2格。';log(state.escaped?'水猴已逃离战场，无法再攻击，也不补发击败经验。':'水猴沿最近路线移动'+(state.x-before)+'格，下回合继续撤离。');$('art-action').value='escape';showArt();render();};
  $('reset-example').onclick=reset;
  reset();requestAnimationFrame(animate);
  window.waterMonkeyReview={getState:()=>({...state,artBroken:art.broken,artAction:art.action?.id}),setArtBroken:setBroken,artSeek:value=>{art.playing=false;art.tick=Math.max(0,Math.min(value,art.action.frames.length-1));drawArt();},ready:()=>[...imageCache.values()].every(im=>im.complete&&im.naturalWidth>0)};
})();
