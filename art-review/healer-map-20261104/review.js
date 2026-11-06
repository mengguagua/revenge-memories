(async()=>{
'use strict';const D=window.HEAL_MAP_DATA,R=window.HEAL_RENDER,$=s=>document.querySelector(s),canvas=$('#scene');let jobIndex=0,tier=0,time=0,left=2,targetKey='target',full=false,playing=false,showRange=false,showDetail=true,last=0;
function job(){return D.jobs[jobIndex];}
function paint(){
 const j=job();R.scene(canvas,j,time,tier,left,targetKey,showRange,full,showDetail);$('#seek').value=time;$('#clock').textContent=`${time.toFixed(2)} / ${j.duration.toFixed(2)}秒`;
 $('#phase').textContent=time<.30?'举杖／抬手':time<.58?'单体引导':time<.90?'治疗＋强身':'收势／恢复操作';$('#turn').textContent='第'+(left===2?3:left===1?4:5)+'回合';
}
function summarize(){
 const j=job(),v=R.values(j,tier,targetKey,full);$('#stage').textContent=`${j.stage_code} / ${j.stage_name} · ${j.profession}`;$('#name').textContent=j.caster.name_zh+' · '+j.name;$('#target-note').textContent=`${v.target.unit.name_zh} · 实际距离${v.distance}格 / 最远${j.reach}格 · 单体`;
 $('#heal').textContent=`${v.before} → ${v.after}（+${v.actual}）`;$('#cost').textContent=`${j.caster.max_hp} → ${v.casterAfter}（扣${v.cost}）`;$('#move').textContent=tier===2?`${j.caster.move} → ${Math.max(1,v.move)}，至下回合结束`:`${j.caster.move}格`;
 $('#single-note').textContent=`另一名友方保持${targetKey==='target'?j.friend.hp+'/'+j.friend.max_hp:j.target.hp+'/'+j.target.max_hp}；敌人不受影响`;
 for(const n of $('#jobs').children)n.setAttribute('aria-pressed',String(Number(n.dataset.job)===jobIndex));for(const n of $('#tiers').children)n.setAttribute('aria-pressed',String(Number(n.dataset.tier)===tier));for(const n of $('#buff-controls').children)n.setAttribute('aria-pressed',String(Number(n.dataset.left)===left));
 $('#buff-summary').textContent=left>0?'强身 · 物防＋2':'强身已到期';$('#buff-summary').classList.toggle('green',left>0);$('#seek').max=j.duration;$('#play').textContent=playing?'暂停':'播放';for(const n of [2,1,0])R.detailOnly($('#detail-'+n),j,tier,n,targetKey,full);paint();
}
function pause(){playing=false;$('#play').textContent='播放';}
function reset(play=false){time=0;left=2;playing=play;last=0;$('#buff-description').textContent='第3回合施放：护甲图标角标为2，人物详情显示绿色“物防＋2”。';summarize();}
for(const n of $('#jobs').children)n.addEventListener('click',()=>{jobIndex=Number(n.dataset.job);reset(true);});for(const n of $('#tiers').children)n.addEventListener('click',()=>{tier=Number(n.dataset.tier);reset(false);});
$('#play').addEventListener('click',()=>{if(playing)pause();else{if(time>=job().duration)time=0;left=2;playing=true;last=0;}summarize();});$('#restart').addEventListener('click',()=>reset(true));$('#impact').addEventListener('click',()=>{pause();time=.68;left=2;summarize();});
$('#seek').addEventListener('input',e=>{pause();time=Number(e.target.value);paint();});$('#range').addEventListener('click',e=>{showRange=!showRange;e.target.setAttribute('aria-pressed',String(showRange));paint();});$('#detail').addEventListener('click',e=>{showDetail=!showDetail;e.target.setAttribute('aria-pressed',String(showDetail));paint();});
$('#target').addEventListener('change',e=>{targetKey=e.target.value;reset(false);});$('#full').addEventListener('change',e=>{full=e.target.checked;reset(false);});
for(const n of $('#buff-controls').children)n.addEventListener('click',()=>{pause();left=Number(n.dataset.left);time=job().duration;$('#buff-description').textContent=left===2?'第3回合施放：护甲图标角标为2，人物详情显示绿色“物防＋2”。':left===1?'第4回合：角标变为1，强身仍生效，物防继续＋2。':'第5回合己方阶段开始：强身到期，图标与绿色加成文案消失，物防恢复原值。';summarize();});
try{await R.load();$('#loading').remove();summarize();if(!matchMedia('(prefers-reduced-motion: reduce)').matches){playing=true;$('#play').textContent='暂停';}requestAnimationFrame(tick);}catch(error){$('#loading').textContent=error.message;$('#loading').setAttribute('role','alert');}
function tick(now){if(playing){if(last){time=Math.min(job().duration,time+(now-last)/1000*Number($('#speed').value));if(time>=job().duration)pause();}paint();}last=now;requestAnimationFrame(tick);}
})();
