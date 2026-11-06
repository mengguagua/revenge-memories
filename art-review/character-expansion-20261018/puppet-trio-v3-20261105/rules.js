/* Review-only deterministic examples. Does not read or change game saves. */
'use strict';
(function(root){
 const D=root.PUPPET_TRIO_DESIGN||(typeof require==='function'?require('./design.json'):null);
 const copy=x=>JSON.parse(JSON.stringify(x));
 const alive=s=>s.hp>0&&!s.escaped;
 const valid=s=>D.units[s.id];
 const active=(s,key)=>(s.parts[key]||0)>0;
 function fresh(id){const u=D.units[id];return {id,hp:u.stats.hp,parts:Object.fromEntries(u.parts.map(p=>[p.id,p.hp])),target:'body',pos:[8,5],escaped:false,humans:1,canto:0,attacked:false,turn:1,ended:false,revived:false,kill:false,damageXp:0,events:[],friends:Array.from({length:8},(_,i)=>({id:'ally'+i,x:[-1,0,1,-1,1,-1,0,1][i],y:[-1,-1,-1,0,0,1,1,1][i],hp:12,max:24,side:'enemy',hidden:false})),dummyHp:36,playerHp:48};}
 function appearance(s){if(s.id!=='prometheus')return active(s,s.id==='cyclops'?'eye':'engine')?'intact':'broken';return active(s,'fire')?(active(s,'life')?'intact':'life-broken'):(active(s,'life')?'fire-broken':'both-broken');}
 function chance(s,target,base,certain=false){if(!alive(s))return 0;if(certain)return 100;const n=Math.max(0,Math.min(100,Math.floor(Number(base)||0)));return s.id==='cyclops'&&target==='body'&&active(s,'eye')?Math.floor(n/2):n;}
 function defence(s,target,type){const u=valid(s);if(target==='body')return u.stats[type==='magic'?'resistance':'defence'];const p=u.parts.find(p=>p.id===target);return p?p[type==='magic'?'resistance':'defence']:0;}
 function xp(s,damage,killed,coef=8,level=5){if(level>=20)return 0;const u=valid(s),f=[10,10,9,8,7,6,5,4,3,2,2,2,2,2,2,2,2,2,2,1][level-1],full=Math.ceil(coef*f*u.experience.level_value/100);const ordinary=killed?full:damage>0?Math.ceil(full*damage/(u.stats.hp*2)):1;return Math.min(180,Math.ceil(ordinary*1.5));}
 function move(s){return valid(s).stats.move+(s.humans===0&&!s.escaped?3:0);}
 function finishDamage(s){if(s.hp>0)return false;if(s.id==='prometheus'&&active(s,'life')){s.hp=24;s.parts.life=0;s.revived=true;s.canto=0;s.events.push('生命核心消耗：本体立即回复24HP；不计击败，核心不再回复或复苏。');return true;}s.hp=0;s.kill=true;s.canto=0;s.events.push('本体被击败；无需清空其它核心。');return false;}
 function hit(s,{target='body',type='physical',power=18,base=80,roll=60,certain=false}={}){
  if(!alive(s)||target!=='body'&&!active(s,target))return {valid:false,reason:'该目标已不可攻击。'};
  roll=Math.max(0,Math.min(99,Math.floor(Number(roll)||0)));const p=chance(s,target,base,certain),landed=certain||roll<p;let before=target==='body'?s.hp:s.parts[target],damage=landed?Math.min(before,Math.max(1,power-defence(s,target,type))):0;
  if(target==='body')s.hp-=damage;else s.parts[target]-=damage;
  if(target!=='body'&&s.parts[target]===0){s.events.push(valid(s).parts.find(p=>p.id===target).name+'已破坏；无伤害溢出。');if(target==='engine')s.canto=0;}
  const revived=target==='body'&&finishDamage(s),reward=xp(s,damage,s.kill);s.damageXp+=reward;
  const result={valid:true,target,hit:landed,chance:p,roll,damage,before,after:target==='body'?s.hp:s.parts[target],revived,killed:s.kill,reward};s.events.push(`${target==='body'?'本体':valid(s).parts.find(p=>p.id===target).name}：${landed?'命中':'未命中'}（判定${roll}／命中${p}%），伤害${damage}；本次经验示例${reward}。`);return result;
 }
 function begin(s){if(!alive(s))return [];s.turn++;s.ended=false;s.attacked=false;s.canto=0;const changed=[];if(s.id==='cyclops'&&active(s,'eye'))for(const a of s.friends){if(a.side!=='enemy'||a.empty||a.hidden||a.escaped||a.event_object||a.id===s.id||a.hp<=0||Math.max(Math.abs(a.x),Math.abs(a.y))!==1)continue;const before=a.hp;a.hp=Math.min(a.max,a.hp+5);if(a.hp>before)changed.push({id:a.id,before,after:a.hp,amount:a.hp-before});}s.events.push(`本方第${s.turn}回合开始：${changed.length?'周围'+changed.length+'名队友各回复至上限，自己不回血。':'无起始治疗。'}`);return changed;}
 function end(s){if(!alive(s)||s.ended)return 0;s.ended=true;s.canto=0;let n=0;if(s.id==='prometheus'&&active(s,'life')){const before=s.hp;s.hp=Math.min(valid(s).stats.hp,s.hp+6);n=s.hp-before;}s.events.push('本方回合结束：本体回复'+n+'HP。');return n;}
 function ownAttack(s,{mode='physical',roll=60,distance=1,opponent=false}={}){
  const u=valid(s),a=mode==='magic'&&s.id==='prometheus'?u.fire_attack:u.attack;
  if(!alive(s)||!opponent&&(s.humans===0||s.ended||s.attacked))return {valid:false,reason:'当前不能再次主动攻击。'};
  if(mode==='magic'&&s.id==='prometheus'&&!active(s,'fire'))return {valid:false,reason:'火之核心已破坏，魔法停用。'};
  if(distance<a.range[0]||distance>a.range[1])return {valid:false,reason:'超出射程。'};
  const type=a.type,baseDef=type==='magic'?4:6,pierce=s.id==='owl'&&active(s,'engine')&&type==='physical'?2:0,def=Math.max(0,baseDef-pierce),p=a.certain?100:a.hit;
  roll=Math.max(0,Math.min(99,Math.floor(Number(roll)||0)));const landed=!!a.certain||roll<p,damage=landed?Math.min(s.dummyHp,Math.max(1,a.power-def)):0;s.dummyHp-=damage;
  if(!opponent){s.attacked=true;s.canto=s.id==='owl'&&active(s,'engine')?3:0;}
  s.events.push(`${a.name}：${type==='magic'?'魔法':'物理'}威力${a.power}－${def}防御，${landed?'命中':'未命中'}，伤害${damage}。`+(s.canto?'交锋结束，可再移动最多3距离一次。':''));
  return {valid:true,hit:landed,chance:p,damage,defence:def,pierce,canto:s.canto,certain:!!a.certain};
 }
 // Diagram board: solid perimeter except the east exit; no actual stage is authored.
 const size=[17,11],exit=[16,5];
 function wall(x,y){return (x===0||y===0||x===16||y===10)&&!(x===exit[0]&&y===exit[1]) || (x===11&&y>=2&&y<=4);}
 function graph(start,occupied=[]){const q=[start],key=p=>p.join(','),cost={[key(start)]:0},prev={};while(q.length){const p=q.shift();for(const d of [[0,-1],[1,0],[0,1],[-1,0]]){const n=[p[0]+d[0],p[1]+d[1]],k=key(n);if(n[0]<0||n[1]<0||n[0]>=17||n[1]>=11||wall(...n)||occupied.some(p=>key(p)===k)||k in cost)continue;cost[k]=cost[key(p)]+1;prev[k]=p;q.push(n);}}return {cost,prev};}
 function path(start,dest,occupied=[]){const g=graph(start,occupied),key=dest.join(',');if(!(key in g.cost))return [];const out=[dest];while(out[0].join(',')!==start.join(',')){const p=g.prev[out[0].join(',')];if(!p)return [];out.unshift(p);}return out;}
 function cantoMove(s,dest){if(!alive(s)||s.id!=='owl'||!active(s,'engine')||s.humans===0||!s.canto)return false;const p=path(s.pos,dest,s.dummyHp>0?[[9,5]]:[]);if(p.length<2||p.length-1>s.canto)return false;s.pos=dest.slice();s.canto=0;s.events.push('战后移动完成，不能再次攻击。');return true;}
 function onlyPuppets(s){s.humans=0;s.canto=0;s.events.push(`同阵营仅剩机械傀儡：移动${valid(s).stats.move}→${move(s)}，优先撤离。`);}
 function retreat(s){if(!alive(s)||s.humans!==0)return {valid:false};const p=path(s.pos,exit);if(!p.length)return {valid:false};const distance=Math.min(move(s),p.length-1);s.pos=p[distance].slice();s.escaped=s.pos.join(',')===exit.join(',');s.canto=0;s.events.push(s.escaped?'到达最近可达边缘并消失：击败经验0，不触发生命核心。':'沿合法路径移动'+distance+'格，下一本方回合继续撤离。');return {valid:true,path:p.slice(0,distance+1),escaped:s.escaped,distance};}
 const api={fresh,appearance,chance,defence,xp,move,hit,begin,end,ownAttack,onlyPuppets,retreat,cantoMove,path,graph,wall,size,exit,alive,active};root.PuppetTrioRules=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
