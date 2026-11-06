(function(global){
'use strict';
const A=global.CinemaAssets,images=new Map(),errors=[];
const targets=global.CinemaTargets;let activeTarget=targets[0],environment='castle';
const cases=[
 {key:'hunapu-sword',hero:'hunapu',name:'胡纳普',className:'战士',weapon:'剑',title:'踏步重斩',advanced:false,duration:7.2,hit:4.10,color:'#9fcbd8',portrait:0,anchor:[190,184,176,160,180,180,190,190],description:'压低重心，贴地突进，以一记斜斩穿过防线。',quote:'就是现在！',beats:['压步蓄势','贴地前冲','斜斩命中','刹步回防']},
 {key:'hunapu-bow',hero:'hunapu',name:'胡纳普',className:'基础造型',weapon:'弓',title:'满弓贯击',advanced:false,duration:7.4,hit:4.38,color:'#b8d0a2',portrait:0,anchor:[176,160,145,135,159,148,150,160],description:'站姿搭箭，屏息拉满；镜头追随一支箭直抵目标。',quote:'这一箭，射穿你！',beats:['搭箭抬弓','站姿满弓','单箭追镜','松弦收弓']},
 {key:'eileen-sword',hero:'eileen',name:'艾琳',className:'女魔剑士',weapon:'剑',title:'跃空落斩',advanced:false,duration:7.4,hit:4.22,color:'#e0acb0',portrait:2,anchor:[180,180,185,178,190,180,180,180],description:'红发与披风随腾跃扬起，空中蓄剑，一次下劈落地。',quote:'让开！',beats:['屈膝起跳','空中蓄剑','落斩命中','低位落地']},
 {key:'hunapu-sword-advanced',hero:'hunapu',name:'胡纳普',className:'破晓勇士',weapon:'剑',title:'破晓 · 断阵',advanced:true,duration:7.6,hit:4.44,color:'#9edfe4',portrait:1,anchor:[175,191,192,211,148,174,145,198],description:'重甲低伏后爆发突入，蓝脊银剑越肩落下，长刃痕短暂停留。',quote:'到此为止！',beats:['沉肩蓄势','重步跃进','长刃落斩','滑步收势']},
 {key:'hunapu-bow-advanced',hero:'hunapu',name:'胡纳普',className:'破晓勇士',weapon:'弓',title:'破晓 · 贯心',advanced:true,duration:7.6,hit:4.66,color:'#c4dca5',portrait:1,anchor:[165,163,170,178,164,157,159,166],description:'单膝落地稳住长弓，特写弦与目光，单箭近镜掠过后贯入。',quote:'躲不开的。',beats:['单膝压稳','长弓拉满','近镜飞矢','贯入收弓']},
 {key:'eileen-sword-advanced',hero:'eileen',name:'艾琳',className:'引光剑使',weapon:'剑',title:'引光 · 回斩',advanced:true,duration:7.6,hit:4.34,color:'#e4c7ae',portrait:3,anchor:[178,167,172,188,181,185,184,188],description:'蓝白长衣随低位穿步展开，转腰上挑，回身一剑完成必杀。',quote:'看清了！',beats:['低位藏剑','穿步切入','回身上挑','长衣收势']}
];
cases[3].actorKey=A['hunapu-sword-fixed']?'hunapu-sword-fixed':cases[3].key;
cases[5].title='引光 · 焰回斩';cases[5].color='#e9b08c';cases[5].description='低位切入，转身上挑，火焰沿剑弧展开，收剑后余烬熄灭。';
const spells=[['fire','火球',23,'#edac91','头顶红色旋涡火团蓄大，飞向目标后爆燃。'],['holy','圣光',26,'#dce4a3','五只萤火虫振翅飞行，汇成散光与光环。'],['thunder','雷电',24,'#cbd5f0','单股落雷先击地，随后压力环扩散，再分叉消散。'],['wind','风刃',27,'#c7e0f1','浅蓝月牙风刃放大后旋转，再单刃发射。'],['ragnarok','诸神黄昏',25,'#efa28d','五枚红色火焰先贴地，再错时斜上飞出，汇成一次爆发。']];
if(A['eileen-cast'])for(const advanced of [false,true])for(const [spell,name,id,color,description] of spells){if(spell==='ragnarok'||!A['spell-'+spell])continue;cases.push({key:'eileen-'+spell+(advanced?'-advanced':''),actorKey:'eileen-cast',hero:'eileen',name:'艾琳',className:advanced?'引光剑使':'女魔剑士',weapon:'魔法',spell,spellId:id,title:name+' · 必杀',advanced,duration:7.2,hit:advanced?4.50:4.32,color,portrait:advanced?3:2,description,quote:advanced?'结束了！':'去吧！',beats:['凝神蓄法','依原法术释放','一次命中结算','原地收势']})}
const actorKey=j=>j.actorKey||j.key;
const endTime=(j,target=activeTarget)=>target.damage>=target.hp?j.hit+1.05:j.duration;
function bodyScale(key,n=0){const d=A[key].frames[n];return 137/(key==='eileen-sword-advanced'?169:(d.body_height||d.height))}
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v)),lerp=(a,b,t)=>a+(b-a)*clamp(t),ease=t=>1-Math.pow(1-clamp(t),3),smooth=t=>{t=clamp(t);return t*t*(3-2*t)},q=v=>Math.round(v/2)*2;
function rect(c,x,y,w,h,color,alpha=1){c.save();c.globalAlpha*=alpha;c.fillStyle=color;c.fillRect(q(x),q(y),q(w),q(h));c.restore()}
function text(c,str,x,y,size,color,box,align='center'){
 c.save();c.font=`${size>=22?600:400} ${size}px "Cinema CJK", "PingFang SC", sans-serif`;c.textAlign=align;c.textBaseline='middle';c.fillStyle=color;
 const m=c.measureText(str),bw=m.actualBoundingBoxLeft+m.actualBoundingBoxRight;
 if(box&&(bw>box[2]-12||size>box[3]-8))errors.push({text:str,width:bw,box});
 c.fillText(str,x,y);c.restore();
}
function bg(c,x,y,w,h,pan=0){const im=images.get(environment==='forest'?'assets/v2/forest.png':'assets/battlefield.png');c.save();c.beginPath();c.rect(x,y,w,h);c.clip();if(im){const s=Math.max(w/im.width,h/im.height)*1.025;c.drawImage(im,x+(w-im.width*s)/2+pan,y+(h-im.height*s)/2,im.width*s,im.height*s)}else rect(c,x,y,w,h,'#25354a');c.restore()}
function pixLine(c,x1,y1,x2,y2,width,color,alpha=1){
 const n=Math.max(1,Math.ceil(Math.hypot(x2-x1,y2-y1)/2));c.save();c.globalAlpha*=alpha;c.fillStyle=color;
 for(let i=0;i<=n;i++){const u=i/n;c.fillRect(q(lerp(x1,x2,u))-width/2,q(lerp(y1,y2,u))-width/2,width,width)}c.restore();
}
function sprite(c,key,n,x,y,scale=1,alpha=1,flip=false,registration=null){
 const d=A[key].frames[n],im=images.get(d.path);if(!im)return;
 c.save();c.globalAlpha*=alpha;c.translate(q(x),q(y));if(flip)c.scale(-1,1);
 const j=cases.find(j=>j.key===key);let ax=d.width/2;
 if(registration?.x!==undefined)ax=registration.x;else if(d.body_anchor!==undefined&&(d.path.includes('/v2/')||d.path.includes('/v3/')||d.path.includes('/v4/')||d.path.includes('/v5/')||d.path.includes('/v6/')))ax=d.body_anchor;else if(j&&j.anchor)ax=(j.anchor[n]-(d.source_box[0]-d.source_cell[0]))/2;
 const ay=registration?.y??d.height;
 c.drawImage(im,Math.round(-ax*scale),Math.round(-ay*scale),Math.round(d.width*scale),Math.round(d.height*scale));c.restore();
}
function dust(c,x,y,t,color='#9da9aa',count=22,spread=1){
 if(t<0||t>1.3)return;
 for(let n=0;n<count;n++){const r=(Math.sin(n*19.431)*.5+.5),v=(Math.cos(n*6.61)*.5+.5);const dx=(r-.5)*110*spread*t,dy=-Math.sin(clamp(t/1.3)*Math.PI)*(8+v*25);rect(c,x+dx,y+dy,2+(n%3)*2,2+(n%2)*2,color,(1-t/1.3)*.65)}
}
function speedlines(c,t,color,strength=1){
 for(let i=0;i<28;i++){const y=57+(i*67)%236,x=((i*139-t*420)%720+720)%720-70;rect(c,x,y,22+(i%5)*14,2,color,.12*strength)}
}
function arrow(c,x,y,size,color='#ebe4d0'){
 pixLine(c,x-size*1.1,y,x+size*.5,y,2,color);
 pixLine(c,x+size*.35,y-4,x+size*.65,y,2,color);pixLine(c,x+size*.35,y+4,x+size*.65,y,2,color);
 pixLine(c,x-size,y-4,x-size*.8,y,2,'#b6c8d2');pixLine(c,x-size,y+4,x-size*.8,y,2,'#b6c8d2');
}
function slash(c,j,t,cx=475,cy=208){
 if(t<0||t>.65)return;
 const k=clamp(t/.20),fade=1-clamp((t-.15)/.5),up=j.hero==='eileen'&&j.advanced;
 const from=up?2.7:-2.15,to=up?-.50:.62,rad=j.advanced?123:91;
 for(let layer=0;layer<3;layer++){
  const col=layer===2?'#fff8df':layer===1?j.color:'#536c81',th=layer===2?2:layer===1?6:12;
  let px=null,py=null;
  for(let n=0;n<38;n++){const p=n/37;if(p>k)break;const a=lerp(from,to,p),r=rad+(layer-1)*3,x=cx+Math.cos(a)*r,y=cy+Math.sin(a)*r*.72;
   if(px!==null)pixLine(c,px,py,x,y,th,col,fade*(.3+.7*p));px=x;py=y;
  }
 }
}
function impact(c,j,dt,x=490,y=207){
 if(dt<0||dt>1.15)return;const burst=clamp(dt/.15),fade=1-clamp(dt/.9),reach=j.weapon==='弓'?25:j.advanced?87:60;
 for(let i=0;i<12;i++){const a=i/12*Math.PI*2+.25,r=(reach+(i%3)*10)*burst;pixLine(c,x+Math.cos(a)*r*.28,y+Math.sin(a)*r*.28,x+Math.cos(a)*r,y+Math.sin(a)*r, i%2?2:4,i%3===0?'#e1ba80':j.color,fade)}
 if(dt<.18){const k=1-dt/.18;pixLine(c,x-20*k,y,x+20*k,y,4,'#fff8e4');pixLine(c,x,y-28*k,x,y+28*k,4,'#fff8e4');rect(c,x-5*k,y-5*k,10*k,10*k,'#fff8e4')}
 for(let i=0;i<27;i++){const a=i*2.399,r=(40+(i%6)*14)*dt,grav=dt*dt*60;rect(c,x+Math.cos(a)*r,y+Math.sin(a)*r+grav,2+(i%2)*2,2,j.color,fade*.9)}
}
function timing(j,t,target=activeTarget){
 const hit=j.hit;let n=0,x=148,y=290;
 if(j.weapon==='魔法'){n=(j.advanced?4:0)+(t<2.05?0:t<3.35?1:t<hit+.7?2:3);if(t>=5.35)n=j.advanced?4:0;return {n,x,y,key:actorKey(j)}}
 if(j.weapon==='弓'){
  if(t<1.85)n=0;else if(t<2.4)n=1;else if(t<2.85)n=2;else if(t<3.40)n=3;else if(t<hit-.65)n=4;else if(t<hit-.44)n=5;else if(t<5.35)n=6;else n=0;
  x=j.advanced?150:162;
 }else if(j.hero==='eileen'&&!j.advanced){
  if(t<2.22)n=0;else if(t<2.70)n=1;else if(t<3.20){n=2;x=lerp(148,235,(t-2.7)/.5);y=lerp(290,230,(t-2.7)/.5)}
  else if(t<3.75){n=3;x=lerp(235,335,(t-3.20)/.55);y=216-Math.sin((t-3.2)/.55*Math.PI)*20}
  else if(t<hit){n=4;x=lerp(335,415,(t-3.75)/(hit-3.75));y=lerp(216,290,(t-3.75)/(hit-3.75))}
  else if(t<4.80){n=5;x=418}else if(t<5.38){n=6;x=420}else if(t<5.9){n=7;x=420}
 }else if(j.hero==='eileen'){
  if(t<2.05)n=0;else if(t<2.65)n=1;else if(t<3.40){n=2;x=lerp(148,270,ease((t-2.65)/.75))}
  else if(t<hit-.15){n=3;x=lerp(270,405,(t-3.4)/(hit-.15-3.4))}
  else if(t<hit+.18){n=4;x=418}else if(t<4.98){n=5;x=421}else if(t<5.45){n=6;x=421}else if(t<5.9){n=7;x=421}
 }else if(j.advanced){
  if(t<2.15)n=0;else if(t<2.75)n=1;else if(t<3.20)n=2;
  else if(t<3.80){n=3;x=lerp(148,295,ease((t-3.2)/.6));y=280}
  else if(t<hit-.15){n=4;x=lerp(295,396,(t-3.8)/(hit-.15-3.8));y=239}
  else if(t<hit+.30){n=5;x=410;y=290}else if(t<5.35){n=6;x=414}else if(t<5.9){n=7;x=415}
 }else{
  if(t<2.18)n=0;else if(t<2.75)n=1;else if(t<hit-.38){n=2;x=lerp(148,354,ease((t-2.75)/(hit-.38-2.75)));y=286}
  else if(t<hit-.10){n=3;x=lerp(354,395,(t-hit+.38)/.28);y=267}
  else if(t<hit+.17){n=4;x=410}else if(t<4.85){n=5;x=416}else if(t<5.4){n=6;x=416}else if(t<5.9){n=7;x=416}
 }
 let key=actorKey(j);
 if(t>=5.38&&j.weapon==='剑'&&target.damage<target.hp){
  const runKey=j.hero+'-return',u=clamp((t-5.53)/1.08);
  if(t>=5.53&&u<1&&A[runKey]){key=runKey;n=(j.advanced?4:0)+Math.floor((t-5.53)*11)%4;x=lerp(416,148,u);y=A[runKey].frames[j.advanced?4:0].return_head_y??153;}
  else if(u>=1){n=0;x=148;y=290}else {n=0;x=416;y=290}
 }else if(t>=5.9&&j.weapon!=='弓'){n=7;x=416;y=290}
 return {n,x,y,key};
}
function cutin(c,j,t){
 const start=.63,end=1.86;if(t<start||t>end)return;
 const enter=ease((t-start)/.22),leave=ease((t-(end-.20))/.20),shift=(1-enter)*150-leave*220;
 c.save();c.beginPath();c.rect(0,59,640,216);c.clip();
 rect(c,0,59,640,216,'#0a1423',.97);speedlines(c,t,j.color,2);
 let p=A.portraits.frames[j.portrait];const step=t<1.16?0:1;
 if(j.weapon==='弓'&&A['bow-cutins'])p=A['bow-cutins'].frames[(j.advanced?2:0)+step];
 if(j.weapon==='魔法'&&A['magic-cutins'])p=A['magic-cutins'].frames[(j.advanced?2:0)+step];
 const im=images.get(p.path),s=Math.min(298/p.width,214/p.height);
 if(im)c.drawImage(im,q(24+shift),q(274-p.height*s),q(p.width*s),q(p.height*s));
 rect(c,332+shift,77,2,178,j.color,.3);
 text(c,j.name,478+shift,110,16,j.color,[358,92,240,35]);
 text(c,j.title,478+shift,157,j.title.length>7?25:30,'#f1ece2',[346,130,264,52]);
 text(c,j.quote,478+shift,215,18,'#cfdae0',[345,190,270,40]);
 c.restore();
}
function targetGeometry(target){const im=images.get(target.path);if(!im)return null;const s=Math.min(139/im.height,166/im.width);return {im,w:im.width*s,h:im.height*s}}
function drawTarget(c,target,x,y,alpha=1){const g=targetGeometry(target);if(!g)return;c.save();c.globalAlpha*=alpha;c.drawImage(g.im,q(x-g.w/2),q(y-g.h),q(g.w),q(g.h));c.restore()}
function targetImpact(c,j,target,dt){
 if(dt<0||dt>.96)return;
 if(j.weapon==='魔法')return;
 const flaming=j.hero==='eileen'&&j.advanced,seq=j.weapon==='弓'?[0,1,7]:flaming?[4,5,6,7]:j.advanced?[0,1,2,3,6,7]:[0,1,2,6,7];
 const key=flaming&&A['spell-fire']?'spell-fire':'impact',n=seq[Math.min(seq.length-1,Math.floor(dt/(.75/seq.length)))],d=A[key].frames[n],im=images.get(d.path);if(!im)return;
 const g=targetGeometry(target),size=j.weapon==='弓'?76:flaming?188:j.advanced?176:126,s=size/Math.max(d.width,d.height);
 c.save();c.globalAlpha=1-clamp((dt-.65)/.31);c.drawImage(im,q(502-d.width*s/2),q(218-d.height*s/2),q(d.width*s),q(d.height*s));c.restore();
}
function effect(c,key,n,x,y,size,alpha=1){const d=A[key]?.frames[Math.max(0,Math.min(7,n))],im=d&&images.get(d.path);if(!im)return;const s=size/Math.max(d.width,d.height);c.save();c.globalAlpha*=alpha;c.translate(q(x),q(y));if(key==='spell-wind'&&n<4)c.scale(-1,1);if(key==='spell-wind'&&n===4){const left=q(-d.width*s/2),top=q(-d.height*s/2),cut=40;c.drawImage(im,0,0,cut,d.height,left,top,cut*s,d.height*s);c.translate(2*(left+(cut+d.width)*s/2),0);c.scale(-1,1);c.drawImage(im,cut,0,d.width-cut,d.height,left+cut*s,top,(d.width-cut)*s,d.height*s);c.restore();return}const ax=d.core_anchor?.[0]??d.width/2,ay=d.core_anchor?.[1]??d.height/2;c.drawImage(im,q(-ax*s),q(-ay*s),q(d.width*s),q(d.height*s));c.restore()}
function spellEffect(c,j,t){
 const key='spell-'+j.spell,dt=t-j.hit,power=j.advanced?1.15:1;
 if(j.spell==='fire'){
  if(t>2.15&&t<3.3)effect(c,key,Math.min(2,Math.floor((t-2.15)*2.6)),154,116,lerp(25,63,(t-2.15)/1.15)*power);
  if(t>=3.3&&dt<0){const u=clamp((t-3.3)/(j.hit-3.3));effect(c,'fire-flight',Math.floor((t-3.3)*12)%4,lerp(174,500,u),lerp(120,213,u),92*power)}
 }else if(j.spell==='holy'){
  if(t>2.35&&dt<0)for(let i=0;i<5;i++){const u=clamp((t-2.35-i*.075)/(j.hit-2.35-i*.075));effect(c,key,Math.floor(t*12+i)%3,lerp(170,500,u)+Math.sin(i*2+t*5)*9,lerp(130+i*11,214,u)+Math.sin(u*Math.PI)*(i-2)*16,26*power)}
 }else if(j.spell==='thunder'){
  if(dt>=-.24&&dt<0)effect(c,key,dt<-.12?0:1,502,166,254*power);
 }else if(j.spell==='wind'){
  if(t>2.2&&t<3.35)effect(c,key,t<2.55?0:1+Math.floor((t-2.55)*6)%3,174,151,lerp(30,76,(t-2.2)/1.15));
  if(t>=3.35&&dt<0){const u=clamp((t-3.35)/(j.hit-3.35));effect(c,key,4,lerp(180,500,u),lerp(151,214,u),87*power)}
 }else if(j.spell==='ragnarok'){
  if(t>2.2&&t<2.9)effect(c,key,t<2.5?0:1,154,117,48*power);
  if(t>=2.9&&dt<0)for(let i=0;i<5;i++){const u=clamp((t-3.18-i*.07)/(j.hit-3.18-i*.07));effect(c,key,u===0?0:1,lerp(204+i*29,500,u),lerp(278,204,u),33*power)}
 }
 if(dt>=0&&dt<1.03){const seq=j.spell==='thunder'?[2,3,4,5,6,7]:j.spell==='holy'?[4,5,6,7]:j.spell==='wind'?[5,6,7]:j.spell==='ragnarok'?[5,6,7]:[4,5,6,7];const n=seq[Math.min(seq.length-1,Math.floor(dt/(.85/seq.length)))];effect(c,key,n,502,j.spell==='thunder'?267:216,(j.spell==='thunder'?207:j.spell==='wind'?157:181)*power,1-clamp((dt-.72)/.31))}
}
function scene(c,j,t,target){
 const dt=t-j.hit,st=timing(j,t,target),dead=target.damage>=target.hp;
 bg(c,0,0,640,360,j.weapon==='弓'&&t>3.8&&t<j.hit?-(t-3.8)*12:0);
 rect(c,0,0,640,360,'#08121d',.12);
 const sh=j.weapon==='剑'&&dt>=0&&dt<.27?(1-dt/.27)*(j.advanced?5:3):0;
 c.save();c.translate(q(Math.sin(t*131)*sh),q(Math.cos(t*103)*sh*.65));
 if(t>2.7&&t<j.hit+.2&&j.weapon==='剑')speedlines(c,t,j.color,.8);
 if(j.weapon==='弓'&&t>3.55&&t<j.hit)speedlines(c,t,j.color,j.advanced?1.3:.6);
 // The current target persists through preparation, contact and recovery.
 // Contact VFX cover the same static image; only a resolved defeat removes it.
 if(!dead||dt<=.35)drawTarget(c,target,502,290);
 const key=st.key||actorKey(j),returning=key.endsWith('-return'),stationary=j.weapon==='弓'||j.weapon==='魔法';let scale=bodyScale(key,(returning||key==='eileen-cast')&&j.advanced?4:0);
 const frame=A[key].frames[st.n],registration=returning?{x:frame.body_anchor??frame.width/2,y:frame.head_top??2}:stationary?{x:frame.body_anchor??frame.width/2}:null;
 // Painted key poses articulate limbs; no body part is rotated or stretched in code.
 sprite(c,key,st.n,st.x,st.y,scale,1,false,registration);
 if(j.weapon==='弓'){
  const release=j.hit-.65;
  if(t>=release&&t<j.hit){const u=(t-release)/.65,ax=lerp(230,484,ease(u));
   if(j.advanced&&u>.25&&u<.62){rect(c,0,95,640,128,'#0b1827',.82);speedlines(c,t,j.color,1.9);arrow(c,lerp(100,550,(u-.25)/.37),155,100);}
   else {pixLine(c,ax-40,210,ax-7,210,2,j.color,.7);arrow(c,ax,210,25)}
  }
  // Crosshair is an editorial camera cue, never an extra projectile or damage tick.
  if(j.advanced&&t>3.1&&t<release){const a=clamp((t-3.1)/.3)*.55;for(const [dx,dy] of [[-1,-1],[1,-1],[-1,1],[1,1]]){pixLine(c,492+dx*20,203+dy*10,492+dx*20,203+dy*19,2,j.color,a);pixLine(c,492+dx*20,203+dy*19,492+dx*30,203+dy*19,2,j.color,a)}}
 }else if(j.weapon==='剑'){
  slash(c,j,dt+.10,468,202);
  if(j.advanced&&dt>0&&dt<.25){const up=j.hero==='eileen';pixLine(c,315,up?288:80,558,up?102:290,dt<.09?6:2,'#ecf3e5',1-dt/.25)}
 }
 if(j.weapon==='魔法')spellEffect(c,j,t);
 if(j.weapon!=='魔法')impact(c,j,dt,495,207);
 if(j.hero==='eileen'&&j.advanced&&j.weapon==='剑'&&A['spell-fire']&&dt>-.14&&dt<.26){for(let i=0;i<3;i++){const a=lerp(2.6,-.5,clamp((dt+.14)/.4))+i*.18;effect(c,'spell-fire',0,468+Math.cos(a)*83,202+Math.sin(a)*62,26-i*4,.9)}}
 targetImpact(c,j,target,dt);
 if(j.weapon==='剑'&&t>2.75)dust(c,st.x,294,t-2.75,'#8499a7',18,j.advanced?1.3:1);
 if(dt>=0&&j.weapon==='剑')dust(c,512,294,dt,'#c4bba7',j.advanced?22:12,j.advanced?1.2:.7);
 if(dt>=0&&dt<.075)rect(c,0,0,640,360,'#f4ead9',dt<.025?.56:.22);
 c.restore();
 if(dt>.15&&dt<1.28){
  const rise=clamp((dt-.15)/.65)*17;
  text(c,'−'+Math.min(target.hp,target.damage),506,152-rise,28,'#ffaf9e',[438,112-rise,136,55]);
 }
 // Letterbox bands separate labels from the moving artwork.
 rect(c,0,0,640,39,'#07101a',.94);rect(c,0,316,640,44,'#07101a',.96);
 text(c,j.name+'  /  '+j.className,320,20,13,'#d2dae0',[18,4,604,31]);
 {
  const shownHp=Math.max(0,target.hp-target.damage*ease((dt-.12)/.55));
  text(c,target.name,498,66,12,'#e0dce1',[396,48,204,31]);
  rect(c,434,86,128,4,'#3b3543');rect(c,434,86,128*shownHp/target.maxHp,4,dt>0?'#d7857d':'#c0a0ab');
  text(c,Math.round(shownHp)+' / '+target.maxHp,498,104,10,'#c8cbd3',[425,91,146,26]);
 }
 text(c,j.title,320,338,19,'#f0e8d8',[20,320,600,35]);
 cutin(c,j,t);
 if(t>.34&&t<.67){const a=Math.sin(clamp((t-.34)/.33)*Math.PI);rect(c,0,115,640,100,'#07101a',a*.85);text(c,'必 杀',320,166,44,'#f5e4c2',[140,120,360,87])}
}
function phase(j,t){
 if(t<.63)return '触发 · 中央弹框';if(t<1.86)return '人物特写';if(t<2.8)return j.beats[0];if(t<j.hit-.15)return j.beats[1];if(t<j.hit+.28)return j.beats[2];if(t<5.9)return '命中余波';if(t<j.duration-.4)return j.beats[3];return '演出结束 · 返回战斗';
}
function render(c,index,t,options={}){
 const j=cases[index];errors.length=0;c.save();c.imageSmoothingEnabled=false;
 const target=options.target||activeTarget;
 const duration=endTime(j,target);t=clamp(t,0,duration);
 bg(c,0,0,1280,800);rect(c,0,0,1280,800,'#091422',.38);
 sprite(c,actorKey(j),j.weapon==='魔法'&&j.advanced?4:0,270,649,bodyScale(actorKey(j),j.weapon==='魔法'&&j.advanced?4:0)*1.8);if(!(target.damage>=target.hp&&t>j.hit+.35)){c.save();c.translate(1003,649);c.scale(1.8,1.8);drawTarget(c,target,0,0);c.restore();}
 rect(c,40,31,382,77,'#0a1724',.94);rect(c,858,31,382,77,'#0a1724',.94);
 text(c,j.name+' · '+j.className,231,56,19,'#e0e8ea',[55,35,350,38]);text(c,target.name,1049,56,19,'#e0e8ea',[873,35,350,38]);
 rect(c,66,86,330,5,'#86b5bb');rect(c,884,86,330,5,'#3b3543');rect(c,884,86,330*Math.max(0,target.hp-target.damage*ease((t-j.hit-.12)/.55))/target.maxHp,5,'#ad8f9b');
 rect(c,0,704,1280,96,'#0a1622',.96);
 text(c,'战斗场景  ·  必杀演出预览',640,745,20,'#b8cbd1',[70,718,1140,54]);
 const open=ease((t-.08)/.29),close=1-ease((t-(duration-.35))/.31),show=open*close;
 if(show>0){
  rect(c,0,0,1280,800,'#02060c',show*.71);
  c.save();c.translate(640,400);const s=.91+.09*show;c.scale(s,s);c.translate(-640,-400);c.globalAlpha=show;
  c.shadowColor='rgba(0,0,0,.8)';c.shadowBlur=45;c.fillStyle='#182a39';c.fillRect(56,68,1168,664);c.shadowBlur=0;
  c.fillStyle='#b9af92';c.fillRect(64,75,1152,2);c.fillStyle='#697581';c.fillRect(64,724,1152,2);
  c.save();c.beginPath();c.rect(64,77,1152,648);c.clip();c.translate(64,77);c.scale(1.8,1.8);scene(c,j,t,target);c.restore();
  c.restore();
 }
 if(options.label!==false){text(c,'ART PREVIEW 06  /  '+String(index+1).padStart(2,'0')+'—'+cases.length,640,777,12,'#8aa4b1',[240,759,800,31])}
 c.restore();return {phase:target.damage>=target.hp&&t>j.hit+.55?'敌人击倒 · 提前结束':phase(j,t),pose:timing(j,t,target).n,errors:errors.slice(),popup:show,duration,targetStatic:true};
}
global.CriticalCinema={cases,images,render,phase,timing,targets,endTime,actorKey,bodyScale,setEnvironment(e){environment=e},setTarget(t){activeTarget=t},getTarget(){return activeTarget},assetPaths:['assets/battlefield.png',...(A['forest']?[]:[]),...targets.map(t=>t.path),...Object.entries(A).filter(([key])=>key!=='spell-ragnarok').flatMap(([,sheet])=>sheet.frames.map(f=>f.path)),...(global.CinemaForest?['assets/v2/forest.png']:[])]};
})(typeof window!=='undefined'?window:globalThis);
