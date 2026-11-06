'use strict';
(() => {
 const data=window.PSEUDO_TITAN_DATA,$=id=>document.getElementById(id),cache=new Map();
 const audio=new Audio('assets/hit.ogg');audio.volume=.4;let sound=false;
 function load(path){const local=path.startsWith('pseudo-titan-v1-20261105/')?path.split('/').slice(1).join('/'):path;if(!cache.has(local)){const im=new Image();im.src=local;cache.set(local,im);}return cache.get(local);}
 const art={broken:false,action:null,profile:null,tick:0,playing:true,last:0,elapsed:0};
 function soundAt(tick){if(sound&&art.action?.soundEvents?.some(e=>e.tick===tick)){audio.pause();audio.currentTime=0;audio.play().catch(()=>{});}}
 function showArt(){
  const key=$('art-action').value,id='pseudo-titan-'+(art.broken?'broken-':'')+key;
  art.action=data.actions.find(a=>a.id===id);art.profile=data.profiles.find(p=>p.id===art.action?.profile);art.tick=0;art.elapsed=0;
  if(!art.action)return;
  for(const f of art.action.neededFrames)load(art.profile.newFrames[String(f)]);
  for(const c of art.action.reviewCompanions||[])load(c.path);
  $('art-scrub').max=art.action.frames.length-1;$('art-note').textContent=art.action.notes;
 }
 function setBroken(value){art.broken=value;$('art-intact').setAttribute('aria-pressed',String(!value));$('art-broken').setAttribute('aria-pressed',String(value));$('art-state').textContent=value?'核心破坏 · 暗色破口与断管':'核心完整 · 青色核心';
  for(const o of $('art-action').options)o.disabled=value&&['reflection','core-break'].includes(o.value);
  if(value&&['reflection','core-break'].includes($('art-action').value))$('art-action').value='idle';showArt();
 }
 function blit(ctx,im,x,y,w,h,flip=false,tint=1,alpha=1){if(!im.complete||!im.naturalWidth)return;ctx.save();ctx.globalAlpha=alpha;if(tint!==1)ctx.filter=`brightness(${tint})`;ctx.translate(x+(flip?w:0),y);if(flip)ctx.scale(-1,1);ctx.imageSmoothingEnabled=false;ctx.drawImage(im,0,0,w,h);ctx.restore();}
 function native(){
  const group=art.broken?'battle-broken':'battle',p=data.profiles.find(p=>p.id==='pseudo-titan-'+group),im=load(p.newFrames['0']);
  for(const id of ['native-one','native-two']){const c=$(id),ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);blit(ctx,im,0,0,96,88);}
  const c=$('native-map'),ctx=c.getContext('2d');ctx.clearRect(0,0,32,32);const mp=data.profiles.find(p=>p.id==='pseudo-titan-'+(art.broken?'maps-broken':'maps'));blit(ctx,load(mp.newFrames['1']),0,0,32,32);
 }
 function drawArt(){
  const c=$('art-canvas'),ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);if(!art.action||!art.profile)return;
  const row=art.action.frames[art.tick],p=art.profile,scene=!!art.action.reviewCompanions?.length||art.action.key.endsWith('escape');ctx.save();ctx.scale(3,3);ctx.imageSmoothingEnabled=false;
  if(!scene){ctx.translate(128,132);ctx.scale(p.context==='battle'?1.65:1.9,p.context==='battle'?1.65:1.9);ctx.translate(-art.action.origin[0],-art.action.origin[1]);}
  for(const t of art.action.reviewCompanions||[])blit(ctx,load(t.path),t.origin[0]-t.anchor[0]+(row.companionShake||0),t.origin[1]-t.anchor[1],...t.size,t.flip,row.companionTint??1);
  const flip=(p.context==='battle')!==!!row.flip;
  blit(ctx,load(p.newFrames[String(row.frame)]),art.action.origin[0]+row.offset[0]-p.anchor[0]+(row.shake||0),art.action.origin[1]+row.offset[1]-p.anchor[1],...p.sourceFrameSize,flip,row.tint??1,row.alpha??1);ctx.restore();
  $('art-time').textContent=`第${art.tick+1}／${art.action.frames.length}帧 · ${(art.tick/art.action.fps).toFixed(2)}秒`+(art.action.contactTick===null?'':` · 结算第${art.action.contactTick+1}帧`);$('art-scrub').value=art.tick;native();
 }
 function animate(now){if(art.playing&&art.action&&art.last){art.elapsed+=(now-art.last)/1000*art.action.fps;let step=Math.floor(art.elapsed);art.elapsed-=step;while(step-->0){art.tick=(art.tick+1)%art.action.frames.length;soundAt(art.tick);}}art.last=now;drawArt();requestAnimationFrame(animate);}
 function play(value){art.playing=value;$('art-play').textContent=value?'暂停':'播放';$('art-play').setAttribute('aria-pressed',String(value));if(!value)audio.pause();}
 $('art-intact').onclick=()=>setBroken(false);$('art-broken').onclick=()=>setBroken(true);$('art-action').onchange=showArt;
 $('art-play').onclick=()=>play(!art.playing);$('art-step').onclick=()=>{play(false);art.tick=(art.tick+1)%art.action.frames.length;};$('art-reset').onclick=()=>{art.tick=0;art.elapsed=0;};$('art-scrub').oninput=()=>{play(false);art.tick=Number($('art-scrub').value);};
 $('art-sound').onclick=()=>{sound=!sound;$('art-sound').setAttribute('aria-pressed',String(sound));$('art-sound').textContent=sound?'音效：开':'音效：关';if(!sound)audio.pause();};
 $('art-light').onclick=()=>{const on=$('art-stage').classList.toggle('light');$('art-light').setAttribute('aria-pressed',String(on));$('native-review').classList.toggle('light-native',on);};
 let state,route=window.PSEUDO_TITAN_ROUTE||null;
 function log(text){$('combat-log').textContent=text;}
 const ceil=Math.ceil;
 function experience(){const level=Number($('enemy-level').value),value=Math.min(255,70+Math.floor(70*(level-1)/10)),cap=$('exp-profile').value==='cap',coef=8,factor=cap?10:7,ordinary=ceil(coef*factor*value/100),reward=Math.min(180,ceil(ordinary*1.5));$('experience-value').textContent=`基础70＋floor(70×(${level}－1)÷10)＝敌方经验价值${value}`;$('experience-result').textContent=`友方职业系数${coef}×等级系数${factor}：普通击败经验${ordinary} → 机械傀儡${reward}（向上取整，上限180）。`;return {value,ordinary,reward};}
 function forecast(){const defence=state.target==='core'?($('damage-type').value==='magic'?2:3):($('damage-type').value==='magic'?2:4)+(state.core>0?10:0),hit=$('attack-result').value==='hit',damage=hit?Math.min(state[state.target],Math.max(1,14-defence)):0,reflection=state.target==='body'&&state.core>0?2:0;return {defence,damage,reflection,hit};}
 function map(){const x=route?.path[state.pathIndex]?.[0]??18,y=route?.path[state.pathIndex]?.[1]??9;$('map-marker').style.left=(x+2.5)/38*100+'%';$('map-marker').style.top=(y+3)/32*100+'%';$('map-marker').hidden=state.escaped||state.body===0;$('map-unit').src='assets/'+(state.core===0?'maps-broken':'maps')+'-'+(state.humans===0?'08':'01')+'.png';}
 function render(){const over=state.body===0||state.escaped,broken=state.core===0,f=forecast();$('body-number').textContent=state.body+' / 42';$('core-number').textContent=broken?'已破坏 · 0 / 16':state.core+' / 16';$('body-bar').style.width=state.body/42*100+'%';$('core-bar').style.width=state.core/16*100+'%';$('target-body').setAttribute('aria-pressed',String(state.target==='body'));$('target-core').setAttribute('aria-pressed',String(state.target==='core'));$('target-body').disabled=over;$('target-core').disabled=over||broken;$('hit-target').disabled=over||state.friendHp===0||(state.target==='core'&&broken);$('titan-attack').disabled=over||state.friendHp===0||state.humans===0;$('danger-hp').disabled=over||state.friendHp===0;$('friend-hp').textContent=state.friendHp+' / 24';$('reflected').textContent=state.reflected+'HP';$('defence-note').textContent=broken?'核心失效：本体物防4／魔防2，反伤停用。':'核心有效：本体物防14／魔防12；核心自身物防3／魔防2。';$('forecast').textContent=`攻击${state.target==='body'?'本体':'核心'}：${f.hit?'14威力－'+f.defence+'防御':'未命中'}，本次伤害${f.damage}；固定反伤${f.reflection}HP。`;$('machine-state').textContent=state.body===0?'本体被击败':state.escaped?'已逃离':broken?'核心破坏 · 反伤停用':'核心有效 · 本体被攻击后反伤2HP';$('move-number').textContent='移动'+(state.humans===0?7:4);$('remove-human').disabled=state.humans===0||over;$('escape-turn').disabled=state.humans!==0||over||!route;$('escape-reward').textContent=state.escaped?'已到外缘消失：击败经验0，不计击杀；之前的伤害经验保留。':state.body===0?'本体被击败：按机械傀儡倍率发放经验，核心无需清空。':'尚未击败或逃脱。';map();experience();}
 function reset(){state={body:42,core:16,friendHp:24,target:'body',reflected:0,humans:1,pathIndex:0,turns:0,escaped:false};$('damage-type').value='physical';$('attack-result').value='hit';$('escape-note').textContent='同阵营尚有非机械战斗单位，普通移动4。';$('art-action').value='melee';setBroken(false);log('先试直接攻击本体，再试攻击核心：核心可被两次物理攻击击破，本体生命不变；反伤随后停用。');render();}
 $('target-body').onclick=()=>{state.target='body';render();};$('target-core').onclick=()=>{state.target='core';render();};$('damage-type').onchange=render;$('attack-result').onchange=render;$('enemy-level').onchange=experience;$('exp-profile').onchange=experience;
 $('hit-target').onclick=()=>{if(state.body===0||state.escaped||state.friendHp===0)return;const f=forecast(),target=state.target;state[target]-=f.damage;const reflected=Math.min(state.friendHp,f.reflection);state.friendHp=Math.max(0,state.friendHp-f.reflection);state.reflected+=reflected;let text=`${f.hit?'命中':'未命中'}${target==='body'?'本体':'核心'}，伤害${f.damage}。`;
  if(target==='core'){text+=`本体仍为${state.body}；攻击核心不反伤。`;if(state.core===0){text+=' 核心破坏，双防＋10和反伤立即失效；伤害不溢出本体。';setBroken(true);$('art-action').value='idle';showArt();}}
  else{text+=f.reflection?' 按“被攻击后”结算固定2HP反伤。':' 核心失效，无反伤。';if(f.reflection){setBroken(false);$('art-action').value='reflection';showArt();}}
  if(state.friendHp===0)text+=' 友方生命归零；不保底1HP。';if(state.body===0){text+=' 本体被击败，核心无需清空。';setBroken(state.core===0);$('art-action').value='defeat';showArt();}log(text);render();
 };
 $('titan-attack').onclick=()=>{state.friendHp=Math.max(0,state.friendHp-9);setBroken(state.core===0);$('art-action').value='melee';showArt();log('伪泰坦近身单次锤击：威力14－友方物防5＝9伤害。核心破坏不削弱这项攻击。');render();};
 $('danger-hp').onclick=()=>{state.friendHp=2;log('友方设为2HP。攻击完整核心保护的本体，即使未命中，也会因固定反伤归零。');render();};$('reset-example').onclick=reset;
 $('remove-human').onclick=()=>{state.humans=0;$('escape-note').textContent=route?`仅剩机械傀儡，移动4→7；最近合法外缘(${route.destination.join(',')})，路径代价${route.total_cost}，不下水。`:'撤离路径载入中。';render();};
 $('escape-turn').onclick=()=>{if(!route||state.humans!==0||state.escaped||state.body===0)return;let budget=7;while(state.pathIndex<route.path.length-1){const next=state.pathIndex+1,step=route.costs[next]-route.costs[state.pathIndex];if(step>budget)break;budget-=step;state.pathIndex=next;}state.turns++;state.escaped=state.pathIndex===route.path.length-1;setBroken(state.core===0);$('art-action').value='escape';showArt();$('escape-note').textContent=`第${state.turns}个撤离回合，沿合法路径到(${route.path[state.pathIndex].join(',')})。`+(state.escaped?'已到外缘，立即消失。':'本回合最多移动7代价，下一回合继续。');render();};
 reset();requestAnimationFrame(animate);
 window.titanReview={getState:()=>({...state,artBroken:art.broken,artAction:art.action?.id,artTick:art.tick,artPlaying:art.playing,route,forecast:forecast(),experience:experience()}),ready:()=>!!art.action&&art.action.neededFrames.every(f=>load(art.profile.newFrames[String(f)]).complete&&load(art.profile.newFrames[String(f)]).naturalWidth>0),setArtBroken:setBroken,select:(key)=>{$('art-action').value=key;showArt();},seek:(tick)=>{play(false);art.tick=Math.max(0,Math.min(art.action.frames.length-1,tick));drawArt();}};
})();
