(async()=>{
const R=window.MapReview,D=R.data,$=s=>document.querySelector(s),canvas=$('#screen'),ctx=canvas.getContext('2d');
let state={index:4,tier:0,t:0,playing:true,speed:1,zoom:false,coverage:true,reference:false},last=performance.now();
const hero=j=>j.hero==='hunapu'?'胡纳普':'艾琳';
$('#cases').innerHTML=D.jobs.map((j,i)=>`<button data-case="${i}" aria-pressed="${i===state.index}"><strong>${hero(j)} · ${j.bow?'持弓':j.name}</strong><small>${j.advanced?'进阶后':'进阶前'} / ${j.profession}${j.bow?' / 同规则演出':''}</small></button>`).join('');
$('#identity-grid').innerHTML=D.jobs.slice(0,4).map(j=>`<article class="identity-card"><h3>${hero(j)} · ${j.profession}<small>${j.advanced?'进阶后':'进阶前'}</small></h3><div class="identity-pair"><figure><img src="assets/identity/${j.key}-approved.png" alt="已确认的${j.profession}地图待机造型"><figcaption>已确认原图</figcaption></figure><figure><img src="assets/identity/${j.key}-preview-idle.png" alt="MAP预览的${j.profession}地图待机，与已确认原图一致"><figcaption>MAP待机</figcaption></figure></div><p>逐像素一致</p></article>`).join('');
$('#posters').innerHTML=D.jobs.slice(0,4).map((j,i)=>`<button class="poster-card" data-poster="${i}"><img src="posters/${j.key}.png?v=map-v6-compact-bow" alt="${hero(j)} ${j.profession} ${j.name} 免费档效果定帧"><div>${hero(j)} · ${j.name}<span>${j.stage_code} ${j.stage_name} / ${j.advanced?'进阶后':'进阶前'}</span></div></button>`).join('');
function update(){
const j=D.jobs[state.index],s=R.stats(j,state.tier),male=j.hero==='hunapu';
$('#case-meta').textContent=`${j.stage_code} / ${j.stage_name} · ${j.advanced?'进阶后':'进阶前'} · ${j.profession}`;$('#case-title').textContent=hero(j)+' · '+j.name+(j.bow?' / 持弓演出':'');
$('#seek').max=j.duration;
document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.case)===state.index));document.querySelectorAll('[data-tier]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.tier)===state.tier));
const area=male?(j.advanced?'3 × 4 / 12格':'3 × 2 / 6格'):(j.advanced?'菱形13格 / 选点4格':'菱形5格 / 选点3格');
const damages=s.damage.map(d=>d.actual),lo=Math.min(...damages),hi=Math.max(...damages);
$('#summary').innerHTML=[['覆盖范围',area],['本次额外威力','＋'+s.power],['场景单目标伤害',lo===hi?lo+'点':lo+'～'+hi+'点'+(!male&&j.advanced?' · 中心＋4':'')],['本次生命代价',s.cost+' HP'+(state.tier===2?' ＋ 虚脱':'')]].map(([a,b])=>`<div><small>${a}</small><strong>${b}</strong></div>`).join('');
}
function select(i){state.index=i;state.t=0;state.reference=false;$('#reference').setAttribute('aria-pressed',false);update()}
$('#cases').onclick=e=>{let b=e.target.closest('[data-case]');if(b)select(+b.dataset.case)};
$('#posters').onclick=e=>{let b=e.target.closest('[data-poster]');if(b){select(+b.dataset.poster);state.t=2.6;state.playing=false;$('#play').textContent='播放';$('.player').scrollIntoView({behavior:'smooth',block:'start'})}};
$('#tiers').onclick=e=>{let b=e.target.closest('[data-tier]');if(b){state.tier=+b.dataset.tier;state.t=0;update()}};
$('#play').onclick=()=>{state.playing=!state.playing;$('#play').textContent=state.playing?'暂停':'播放'};
$('#restart').onclick=()=>{state.t=0;state.playing=true;$('#play').textContent='暂停'};
$('#step').onclick=()=>{state.playing=false;state.t=Math.min(D.jobs[state.index].duration,state.t+1/30);$('#play').textContent='播放'};
$('#seek').oninput=e=>{state.playing=false;state.t=+e.target.value;$('#play').textContent='播放'};
$('#speed').onchange=e=>state.speed=+e.target.value;
for(const k of ['zoom','coverage','reference'])$('#'+k).onclick=()=>{state[k]=!state[k];$('#'+k).setAttribute('aria-pressed',state[k])};
window.MAP_PREVIEW={state,select,render:(index,t,tier,opts={})=>R.render(ctx,index,t,tier,opts),audit:()=>R.render(ctx,state.index,state.t,state.tier,state),ready:false};
try{await R.load();$('#loading').hidden=true;window.MAP_PREVIEW.ready=true;update();requestAnimationFrame(tick)}catch(e){$('#loading').textContent='素材载入失败：'+e.message;console.error(e)}
function tick(now){let dt=Math.min(.1,(now-last)/1000);last=now;if(state.playing&&!state.reference){state.t+=dt*state.speed;if(state.t>D.jobs[state.index].duration+.75)state.t=0}const t=Math.min(state.t,D.jobs[state.index].duration);R.render(ctx,state.index,t,state.tier,state);$('#seek').value=t;$('#clock').textContent=t.toFixed(2)+' / '+D.jobs[state.index].duration.toFixed(2)+' s';$('#phase').textContent=state.reference?'参考底图 · 无MAP效果叠加':R.phase(t);requestAnimationFrame(tick)}
})();
