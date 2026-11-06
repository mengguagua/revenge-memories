/* Shared deterministic review renderer. No production gameplay or save access. */
(()=>{
const D=window.MAP_DATA, images=new Map(), audit=[];
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)), mix=(a,b,t)=>a+(b-a)*t;
const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
const FONT='"MAP Review CJK","PingFang SC","Heiti SC","Microsoft YaHei",sans-serif';
async function load(){
 const paths=new Set(['assets/arrow.png']);
 for(const j of D.jobs)for(const p of ['assets/'+(j.bow?'hunapu-advanced':j.key)+'-terrain.png','reference/'+(j.bow?'hunapu-advanced':j.key)+'-runtime.png',j.hero_sprite.path,j.map_action.path,j.enemy_sprite.path,j.friend_sprite.path,j.body.path,j.fx])paths.add(p);
 await Promise.all([...paths].map(p=>new Promise((ok,no)=>{let im=new Image();im.onload=()=>{images.set(p,im);ok()};im.onerror=()=>no(new Error('Missing image '+p));im.src=p})));
}
function round(ctx,x,y,w,h,r,color){ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill()}
function text(ctx,str,x,y,size=18,color='#eaf0ee',weight=400,max=1000,align='left',safe=null){
 ctx.font=`${Math.round(weight/100)*100} ${size}px ${FONT}`;ctx.fillStyle=color;ctx.textAlign=align;ctx.textBaseline='alphabetic';
 const m=ctx.measureText(str),w=m.width;let left=x-(align==='center'?w/2:align==='right'?w:0);
 const bounds=[left,y-(m.actualBoundingBoxAscent||size),w,(m.actualBoundingBoxAscent||size)+(m.actualBoundingBoxDescent||3)];
 if(w>max+.1)audit.push({kind:'text-width',text:str,width:w,max});
 if(safe&&(bounds[0]<safe[0]||bounds[1]<safe[1]||bounds[0]+bounds[2]>safe[0]+safe[2]||bounds[1]+bounds[3]>safe[1]+safe[3]))audit.push({kind:'text-safe-area',text:str,bounds,safe});
 ctx.fillText(str,x,y);
}
function sprite(ctx,s,p,frame=0,opacity=1,flip=false){
 let im=images.get(s.path),[fw,fh]=s.frame_size,cols=s.columns||s.frames;
 const tileOrigin=s.tile_origin||[4,4],density=s.native_density||4;
 const x=p[0]-16-tileOrigin[0]*2,y=p[1]-16-tileOrigin[1]*2;
 ctx.save();ctx.globalAlpha=opacity;
 if(flip){ctx.translate(x+fw/density*2,y);ctx.scale(-1,1);ctx.drawImage(im,(frame%cols)*fw,Math.floor(frame/cols)*fh,fw,fh,0,0,fw/density*2,fh/density*2)}
 else ctx.drawImage(im,(frame%cols)*fw,Math.floor(frame/cols)*fh,fw,fh,x,y,fw/density*2,fh/density*2);
 ctx.restore();
}
function portrait(ctx,j,anchor,scale){
 // The information strip is a standing reference portrait, not a looping run.
 if(j.portrait_from_map){
  // Bow portraits use the same compact MAP sprite as the battlefield.
  const im=images.get(j.map_action.path),z=1.65;
  ctx.drawImage(im,0,0,128,128,anchor[0]-64*z,anchor[1]-96*z,128*z,128*z);return;
 }
 const b=j.body,im=images.get(b.path),pose=j.bow?b.frames[0]:{frame:b.idle,flip:false},f=pose.frame;
 ctx.save();ctx.translate(anchor[0],anchor[1]);ctx.scale(pose.flip?scale:-scale,scale);
 ctx.drawImage(im,(f%b.columns)*160,Math.floor(f/b.columns)*144,160,144,-b.anchor[0],-b.anchor[1],160,144);ctx.restore();
}
function actionFrame(j,t){
 let frame=0;for(const [at,pose] of j.map_action.timeline){if(t<at)break;frame=pose}return frame;
}
function cells(j){
 let result=[];
 if(j.hero==='hunapu'){for(let x=1;x<=(j.advanced?4:2);x++)for(let y=-1;y<=1;y++)result.push([j.hero_point[0]+x*j.tile,j.hero_point[1]+y*j.tile])}
 else{let r=j.advanced?2:1;for(let y=-r;y<=r;y++)for(let x=-r;x<=r;x++)if(Math.abs(x)+Math.abs(y)<=r)result.push([j.center_point[0]+x*j.tile,j.center_point[1]+y*j.tile])}
 return result;
}
function stats(j,tier){
 const power=(j.advanced?D.advanced_steps:D.steps)[tier],hp=j.hero_data.max_hp,cost=Math.ceil(hp*D.hp_cost[tier]);
 return {power,cost,hp,after:hp-cost,damage:j.enemies_data.map((e,i)=>{
 const u=e.unit;let def=j.hero==='hunapu'?u.defence:u.resistance;
 if(j.hero==='hunapu'&&j.advanced)def-=Math.floor(def*.25);
 const center=j.hero==='eileen'&&j.advanced&&e.point[0]===j.center_point[0]&&e.point[1]===j.center_point[1];
 const raw=Math.max(1,Math.min(60,j.hero_data.strength+power-def+(center?4:0)));
 return {raw,actual:Math.min(raw,u.hp),after:Math.max(0,u.hp-raw),center};
 })};
}
function hitTime(j,e){return j.hero==='eileen'?2.42:2.12+(e.point[0]-j.hero_point[0])/j.tile*.09}
function fx(ctx,j,index,p,size,alpha=1){
 if(index<0||index>5)return;
 const im=images.get(j.fx),cw=im.width/3,ch=im.height/2;size*=j.fx_scale||1;
 ctx.save();ctx.globalAlpha=clamp(alpha);ctx.drawImage(im,(index%3)*cw,Math.floor(index/3)*ch,cw,ch,p[0]-size/2,p[1]-size/2,size,size);ctx.restore();
}
function blendFx(ctx,j,phase,p,size,alpha=1){
 phase=clamp(phase,0,5);const n=Math.floor(phase),f=phase-n;
 fx(ctx,j,n,p,size,alpha*(1-f));if(n<5&&f>0)fx(ctx,j,n+1,p,size,alpha*f);
}
function arrow(ctx,from,to,t){
 const im=images.get('assets/arrow.png'),p=[mix(from[0],to[0],t),mix(from[1],to[1],t)];
 ctx.save();ctx.translate(p[0],p[1]-9);ctx.rotate(Math.atan2(to[1]-from[1],to[0]-from[0]));ctx.scale(-1,1);
 ctx.drawImage(im,-14,-4.5,28,9);ctx.restore();
}
function hpBar(ctx,p,hp,max,color){round(ctx,p[0]-13,p[1]+7,26,5,2,'#071019dd');if(hp>0)round(ctx,p[0]-12,p[1]+8,24*hp/max,3,1,color)}
function battle(ctx,j,t,tier,opts){
 const s=stats(j,tier),male=j.hero==='hunapu',key=j.bow?'hunapu-advanced':j.key;
 ctx.save();ctx.beginPath();ctx.rect(0,0,1280,592);ctx.clip();
 if(opts.zoom){
  const z=j.hero==='hunapu'&&!j.advanced?2.8:2.1,g=j.game_rect;
  const p=[(j.hero_point[0]+j.center_point[0])/2+15,j.center_point[1]];
  const tx=clamp(640-p[0]*z,1280-(g[0]+g[2])*z,-g[0]*z),ty=clamp(296-p[1]*z,592-(g[1]+g[3])*z,-g[1]*z);
  ctx.translate(tx,ty);ctx.scale(z,z);ctx.beginPath();ctx.rect(...g);ctx.clip();
 }
 ctx.drawImage(images.get('assets/'+key+'-terrain.png'),0,0);
 if(t>.7&&t<3.8){const dark=.1*smooth((t-.7)/.35)*(1-smooth((t-3.25)/.55));ctx.fillStyle=`rgba(5,14,23,${dark})`;let g=j.game_rect;ctx.fillRect(...g)}
 const covered=cells(j),rangeAlpha=opts.coverage?(t<1.6?.2:t<3?.07:.13):0;
 if(rangeAlpha){for(const p of covered)round(ctx,p[0]-15,p[1]-15,30,30,3,male?`rgba(97,168,206,${rangeAlpha})`:`rgba(215,105,66,${rangeAlpha})`)}
 if(!male&&j.advanced&&opts.coverage)round(ctx,j.center_point[0]-14,j.center_point[1]-14,28,28,4,'#f1bc6438');
 // Grounded preparation, using an authored bitmap rather than geometric VFX.
 if(!j.bow&&t>1.1&&t<2.05){let u=clamp((t-1.1)/.95);blendFx(ctx,j,u*1.3,[j.hero_point[0]+9,j.hero_point[1]-9],male?55:42,.7*smooth(u*2))}
 const actors=[];
 actors.push({p:j.friend_point,s:j.friend_sprite,hp:j.hero_data.max_hp,max:j.hero_data.max_hp,friend:true});
 j.enemies_data.forEach((e,i)=>actors.push({p:e.point,s:j.enemy_sprite,hp:t>=hitTime(j,e)?s.damage[i].after:e.unit.hp,max:e.unit.max_hp,enemy:i}));
 actors.sort((a,b)=>a.p[1]-b.p[1]);
 for(const a of actors){
  const d=a.enemy===undefined?null:s.damage[a.enemy],ht=a.enemy===undefined?999:hitTime(j,j.enemies_data[a.enemy]);
  let shake=t>=ht&&t<ht+.2?Math.round(Math.sin((t-ht)*75)*2):0;
  let opacity=a.hp<=0&&t>ht+.22?1-smooth((t-ht-.22)/.5):1;
  sprite(ctx,a.s,[a.p[0]+shake,a.p[1]],0,opacity);
  if(t>ht&&t<ht+.18){ctx.save();ctx.globalAlpha=(1-(t-ht)/.18)*.18;round(ctx,a.p[0]-10,a.p[1]-27,20,27,8,'#fff2d8');ctx.restore()}
  if(opacity>.01)hpBar(ctx,a.p,a.hp,a.max,a.friend?'#99cdb8':'#cc8e85');
 }
 if(j.bow){
  const muzzleOffset=j.bow_muzzle_offset||[18,4],muzzle=[j.hero_point[0]+muzzleOffset[0],j.hero_point[1]+muzzleOffset[1]];
  for(const e of j.enemies_data){const start=1.94;let u=(t-start)/(hitTime(j,e)-start);if(u>=0&&u<=1)arrow(ctx,muzzle,e.point,u);if(t>hitTime(j,e)&&t<hitTime(j,e)+.22)fx(ctx,j,4,[e.point[0],e.point[1]-10],42,1-(t-hitTime(j,e))/.22)}
 }else if(male&&t>1.94&&t<3.55){
  let u=clamp((t-1.94)/.57),depth=j.advanced?4:2;
  const p=[mix(j.hero_point[0]+10,j.hero_point[0]+depth*j.tile,u),j.hero_point[1]-11];
  const phase=t<2.48?mix(1.4,3,clamp((t-1.94)/.54)):mix(3,5,clamp((t-2.48)/1.07));
  blendFx(ctx,j,phase,p,j.advanced?150:118,t>3.15?1-smooth((t-3.15)/.4):1);
 }else if(!male&&t>1.8&&t<2.42){
  let u=smooth((t-1.8)/.62),p=[mix(j.hero_point[0]+8,j.center_point[0],u),mix(j.hero_point[1]-14,j.center_point[1]-9,u)-Math.sin(u*Math.PI)*20];
  fx(ctx,j,0,p,j.advanced?40:30,1);
 }
 if(!male&&t>=2.24&&t<3.7){
  let phase=t<2.42?mix(1,3,(t-2.24)/.18):mix(3,5,clamp((t-2.42)/1.28));
  let alpha=t>3.28?1-smooth((t-3.28)/.42):1;
  blendFx(ctx,j,phase,[j.center_point[0],j.center_point[1]-(j.advanced?38:16)],j.advanced?185:116,alpha);
 }
 // Keep the caster's hand/weapon action readable in front of the VFX.
 // Foot pixels and the map destination rectangle remain constant.
 sprite(ctx,j.map_action,j.hero_point,actionFrame(j,t));
 hpBar(ctx,j.hero_point,t>.95?s.after:s.hp,s.hp,'#9ad4be');
 // Damage labels appear only once per enemy; they are a review simulation.
 j.enemies_data.forEach((e,i)=>{
  let dt=t-hitTime(j,e);if(dt<0||dt>1.1)return;
  const rise=10*smooth(dt/.55),alpha=dt>.75?1-smooth((dt-.75)/.35):1;
  ctx.save();ctx.globalAlpha=alpha;ctx.shadowColor='#101820';ctx.shadowBlur=5;ctx.shadowOffsetY=2;
  text(ctx,String(s.damage[i].actual),e.point[0],e.point[1]-39-rise,20,s.damage[i].center?'#ffe0a5':'#fff1d5',700,45,'center');ctx.restore();
 });
 ctx.restore();
 // Skill announcement sits within the actual game viewport's safe top area.
 if(t>.6&&t<1.75){const a=smooth((t-.6)/.15)*(1-smooth((t-1.45)/.3));ctx.save();ctx.globalAlpha=a;round(ctx,400,63,480,70,8,'#111d2aee');text(ctx,'MAP  /  '+j.name,640,99,24,male?'#bad9e6':'#eac398',550,440,'center',[420,75,440,50]);text(ctx,j.bow?'持弓 · 穿阵齐射':j.profession,640,119,14,'#9db1be',400,440,'center');ctx.restore()}
}
function ribbon(ctx,j,t,tier){
 const s=stats(j,tier),male=j.hero==='hunapu',color=male?'#bad9e6':'#edc69e';
 ctx.fillStyle='#0d1822';ctx.fillRect(0,592,1280,192);
 const gradient=ctx.createLinearGradient(0,592,1280,784);gradient.addColorStop(0,'#263a4b66');gradient.addColorStop(1,'#0d182200');ctx.fillStyle=gradient;ctx.fillRect(0,592,1280,192);
 ctx.save();ctx.beginPath();ctx.rect(20,604,225,164);ctx.clip();portrait(ctx,j,[133,758],1.45);ctx.restore();
 text(ctx,(male?'胡纳普':'艾琳')+' / '+j.profession+(j.bow?' · 持弓':''),258,625,15,'#9eb5c5',400,510);
 text(ctx,j.name,258,666,32,color,550,500,'left',[248,635,510,50]);
 const range=male?(j.advanced?'宽3 × 深4 · 12格':'宽3 × 深2 · 6格'):(j.advanced?'4格内选点 · 菱形13格':'3格内选点 · 菱形5格');
 text(ctx,range,258,699,18,'#ccd7dc',400,510);
 text(ctx,'力量 '+j.hero_data.strength+' ＋ '+s.power+'  /  '+(male?'物理':'魔法')+(male&&j.advanced?' · 忽略25%物防':!male&&j.advanced?' · 中心格额外＋4':''),258,730,17,color,400,510);
 text(ctx,'范围内每名敌人结算一次 · 友方安全',258,758,14,'#8ca2b1',400,510);
 const safe=[823,610,417,160];
 text(ctx,['第1次 · 无额外代价','第2次 · 支付25%最大HP','第3次 · 支付40%最大HP'][tier],844,631,20,'#e1e9e9',500,380,'left',safe);
 text(ctx,'自身生命',844,668,15,'#9aafbd',400,150);
 text(ctx,t>.95?`${s.hp} → ${s.after}`:`${s.hp} / ${s.hp}`,1220,670,24,tier?'#e4bb9d':'#acd2c0',550,220,'right');
 round(ctx,844,685,376,8,4,'#23333e');round(ctx,844,685,376*((t>.95?s.after:s.hp)/s.hp),8,4,tier?'#d2a47f':'#99c5b2');
 text(ctx,tier===0?'额外威力＋0 · 消耗本次行动':`本次扣${s.cost}HP · 额外威力＋${s.power}`,844,723,17,'#c1cfd6',400,376,'left',safe);
 text(ctx,tier===2?(t>2.75?'虚脱生效 · 至下个己方回合结束':'本次结算后进入虚脱'):'每场独立额度 · 最多3次',844,755,14,tier===2?'#dfb693':'#8fa5b5',400,376,'left',safe);
}
function render(ctx,index,t=0,tier=0,opts={}){
 audit.length=0;const j=D.jobs[index];ctx.save();ctx.clearRect(0,0,1280,784);ctx.imageSmoothingEnabled=false;ctx.fillStyle='#0c151e';ctx.fillRect(0,0,1280,784);
 if(opts.reference){const key=j.bow?'hunapu-advanced':j.key;ctx.drawImage(images.get('reference/'+key+'-runtime.png'),0,0);ribbon(ctx,j,0,tier);text(ctx,'参考：当前Godot后台视口 / 演出摆位',640,562,16,'#a7c1ce',400,700,'center')}
 else{battle(ctx,j,t,tier,{coverage:true,...opts});ribbon(ctx,j,t,tier)}
 ctx.restore();return audit.slice();
}
function phase(t){return t<.85?'范围预览':t<1.95?'蓄势 / 准备':t<2.42?'释放 / 推进':t<2.85?'命中 / 单次结算':t<3.7?'特效消退':t<4.2?'余波消退 / 站定':'结果停留'}
window.MapReview={load,render,stats,cells,phase,actionFrame,images,data:D};
})();
