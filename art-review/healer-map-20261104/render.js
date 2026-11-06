/* Art-only, deterministic renderer. No production rules or save access. */
(()=>{
'use strict';
const D=window.HEAL_MAP_DATA,images=new Map(),tints=new Map(),audit=[];
const GREEN='#a9dfb6',INK='#e9efed',MUTED='#adbfc5';
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const mixes=(a,b,t)=>a+(b-a)*t;
const tex=path=>images.get(path);
async function load(){
 const paths=new Set(['assets/panel.png','assets/font-small.png','assets/font-labels.png','assets/strong-body.png']);
 for(const j of D.jobs){paths.add(`assets/${j.key}-terrain.png`);paths.add(j.effect);paths.add(j.cast.path);for(const role of ['caster','target','friend','enemy'])paths.add(j[role+'_sprite'].path);}
 await Promise.all([...paths].map(path=>new Promise((ok,no)=>{const im=new Image();im.onload=()=>{images.set(path,im);ok()};im.onerror=()=>no(new Error('无法载入 '+path));im.src=path;})));
}
function font(color,path='assets/font-small.png'){
 const key=path+color;if(!tints.has(key)){const im=tex(path),c=document.createElement('canvas');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);x.globalCompositeOperation='source-in';x.fillStyle=color;x.fillRect(0,0,c.width,c.height);tints.set(key,c);}return tints.get(key);
}
function label(ctx,str,x,y){for(const ch of str){const g=D.label_font.glyphs[ch];ctx.drawImage(font(INK,D.label_font.path),g.rect[0],0,12,12,x,y,24,24);x+=24;}}
function width(text,z=2){let w=0;for(const ch of text)w+=(D.font.glyphs[ch]?.advance||8)*z;return w;}
function text(ctx,value,x,y,color=INK,z=2,safe=null){
 const str=String(value),w=width(str,z);
 if(safe&&(x<safe.x||y<safe.y||x+w>safe.x+safe.w+.1||y+8*z>safe.y+safe.h+.1))audit.push({type:'text-safe-area',text:str,bounds:[x,y,w,8*z],safe});
 for(const ch of str){const g=D.font.glyphs[ch];if(!g){audit.push({type:'missing-glyph',text:ch});x+=8*z;continue;}ctx.drawImage(font(color),g.rect[0],g.rect[1],8,8,Math.round(x),Math.round(y),8*z,8*z);x+=g.advance*z;}
}
function sprite(ctx,s,p,frame=0,flip=false){
 const im=tex(s.path),[fw,fh]=s.frame_size,z=2/(s.native_density||4),origin=s.tile_origin||[4,4],cols=s.columns||s.frames;
 const x=p[0]-16-origin[0]*2,y=p[1]-16-origin[1]*2;
 ctx.save();if(flip){ctx.translate(p[0]*2,0);ctx.scale(-1,1);}ctx.drawImage(im,(frame%cols)*fw,Math.floor(frame/cols)*fh,fw,fh,x,y,fw*z,fh*z);ctx.restore();
}
function health(ctx,p,hp,max,enemy=false){ctx.fillStyle='#0c1720';ctx.fillRect(p[0]-15,p[1]+12,30,6);ctx.fillStyle=enemy?'#c88787':'#9bd3b7';ctx.fillRect(p[0]-14,p[1]+13,28*hp/max,4);}
function panel(ctx,r){
 const im=tex('assets/panel.png'),d=16,dx=[r.x,r.x+d,r.x+r.w-d],dy=[r.y,r.y+d,r.y+r.h-d],dw=[d,r.w-d*2,d],dh=[d,r.h-d*2,d],sx=[0,im.width/2,im.width-8],sy=[0,im.height/2,im.height-8];
 for(let y=0;y<3;y++)for(let x=0;x<3;x++)ctx.drawImage(im,sx[x],sy[y],x===1?1:8,y===1?1:8,dx[x],dy[y],dw[x],dh[y]);
}
function badge(ctx,x,y,size,left){
 ctx.drawImage(tex('assets/strong-body.png'),x,y,size,size);
 if(left>0){const cx=x+size-3,cy=y+size-3;ctx.fillStyle='#172a34';ctx.beginPath();ctx.roundRect(cx-8,cy-8,17,17,4);ctx.fill();text(ctx,String(left),cx-width(String(left),1.5)/2,cy-6,INK,1.5);}
}
function effect(ctx,j,frame,p,size,alpha=1){
 if(alpha<=0)return;frame=clamp(frame,0,5);const a=Math.floor(frame),f=frame-a,im=tex(j.effect),cell=192;
 for(const [n,k]of [[a,1-f],[Math.min(5,a+1),f]]){if(k<=0)continue;ctx.save();ctx.globalAlpha=alpha*k;ctx.drawImage(im,(n%3)*cell,Math.floor(n/3)*cell,cell,cell,p[0]-size/2,p[1]-size*161/192,size,size);ctx.restore();}
}
function current(j,targetKey){return targetKey==='friend'?{unit:j.friend,p:j.friend_point,at:j.other_at,sprite:j.friend_sprite}:{unit:j.target,p:j.target_point,at:j.target_at,sprite:j.target_sprite};}
function values(j,tier,targetKey='target',full=false){
 const target=current(j,targetKey),heal=j.caster.strength+j.heal_steps[tier],before=full?target.unit.max_hp:target.unit.hp,cost=Math.ceil(j.caster.max_hp*j.hp_cost[tier]);
 return {target,heal,actual:Math.min(heal,target.unit.max_hp-before),before,after:Math.min(target.unit.max_hp,before+heal),cost,casterAfter:j.caster.max_hp-cost,move:j.caster.move-(tier===2?2:0),distance:Math.abs(j.caster_at[0]-target.at[0])+Math.abs(j.caster_at[1]-target.at[1])};
}
function detail(ctx,j,tier,remaining,targetKey='target',full=false,applied=true,r={x:621,y:287,w:320,h:230}){
 const v=values(j,tier,targetKey,full),u=v.target.unit,left=applied?remaining:0,hp=applied?v.after:v.before,safe={x:r.x+30,y:r.y+24,w:r.w-60,h:r.h-48};
 panel(ctx,r);label(ctx,u.name_zh,r.x+32,r.y+22);text(ctx,`等级${u.level} 经验${u.exp||0}`,r.x+32,r.y+50,MUTED,2,safe);
 text(ctx,`生命${hp}/${u.max_hp}`,r.x+32,r.y+70,INK,2,safe);ctx.fillStyle='#172a35';ctx.fillRect(r.x+32,r.y+91,r.w-64,6);ctx.fillStyle='#9bd3b7';ctx.fillRect(r.x+32,r.y+91,(r.w-64)*hp/u.max_hp,6);
 text(ctx,j.detail_footer[targetKey],r.x+32,r.y+106,'#b9cdae',2,safe);text(ctx,j.detail_tactical[targetKey],r.x+32,r.y+128,INK,2,safe);
 if(left>0){badge(ctx,r.x+27,r.y+155,38,left);label(ctx,'强身',r.x+80,r.y+150);text(ctx,`剩余${left}回合`,r.x+150,r.y+154,MUTED,2,safe);text(ctx,`物防+2  合计${u.defence+2}`,r.x+80,r.y+180,GREEN,2,safe);}
 else{text(ctx,'当前无临时增益',r.x+32,r.y+154,MUTED,2,safe);text(ctx,`物防${u.defence}`,r.x+32,r.y+180,INK,2,safe);}
 return {name:'强身',remaining:left,physical_defence:u.defence+(left>0?2:0),bonus:left>0?2:0,hp,icon_visible:left>0,green_text_visible:left>0,panel:r};
}
function scene(canvas,j,t,tier=0,remaining=2,targetKey='target',showRange=false,full=false,showDetail=true){
 const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,canvas.width,canvas.height);ctx.save();ctx.scale(1.5,1.5);ctx.translate(-321,-39);ctx.drawImage(tex(`assets/${j.key}-terrain.png`),0,0);
 const v=values(j,tier,targetKey,full),selected=v.target,applied=t>=D.impact;
 if(showRange){ctx.fillStyle=j.key==='saint'?'#ddcd9030':'#78bca52e';for(let y=0;y<j.map_size[1];y++)for(let x=0;x<j.map_size[0];x++)if(Math.abs(x-j.caster_at[0])+Math.abs(y-j.caster_at[1])<=j.reach){const px=j.caster_point[0]+(x-j.caster_at[0])*32,py=j.caster_point[1]+(y-j.caster_at[1])*32;ctx.fillRect(px-15,py-15,30,30);}}
 ctx.fillStyle='#a4dac235';ctx.fillRect(selected.p[0]-14,selected.p[1]-14,28,28);
 for(const role of ['target','friend','enemy']){
  const p=j[role+'_point'],unit=j[role],chosen=role===targetKey; sprite(ctx,j[role+'_sprite'],p);health(ctx,p,chosen?(applied?v.after:v.before):unit.hp,unit.max_hp,role==='enemy');
 }
 let pose=0;for(const point of j.cast.timeline)if(t>=point[0])pose=point[1];sprite(ctx,j.cast,j.caster_point,pose,j.cast.flip);health(ctx,j.caster_point,t>=.12?v.casterAfter:j.caster.max_hp,j.caster.max_hp);
 if(t>=.04&&t<.32)effect(ctx,j,Math.min(1.5,(t-.04)*5),[j.caster_point[0]+15,j.caster_point[1]-18],38,.70);
 if(t>=D.release&&t<D.impact){
  const u=clamp((t-D.release)/(D.impact-D.release)),from=[j.caster_point[0]+14,j.caster_point[1]-17],to=[selected.p[0],selected.p[1]-12];
  for(let k=4;k>=0;k--){const z=clamp(u-k*.055),p=[mixes(from[0],to[0],z),mixes(from[1],to[1],z)-Math.sin(z*Math.PI)*24];effect(ctx,j,0,p,25-k*2,.88-k*.14);}
 }
 if(t>=.46&&t<j.duration){const frame=t<.58?mixes(0,2,(t-.46)/.12):t<.78?mixes(2,3,(t-.58)/.2):mixes(3,5,clamp((t-.78)/(j.duration-.78)));effect(ctx,j,frame,[selected.p[0],selected.p[1]+14],j.key==='saint'?108:84,clamp((j.duration-t)/.13));}
 if(applied&&t<D.impact+.44&&v.actual>0){const str='+'+v.actual,x=selected.p[0]-width(str,2)/2,y=selected.p[1]-48-Math.min(9,(t-D.impact)*23);for(const d of [[-1,0],[1,0],[0,-1],[0,1]])text(ctx,str,x+d[0],y+d[1],'#243b31');text(ctx,str,x,y,'#b2e6bc');}
 const status=showDetail?detail(ctx,j,tier,remaining,targetKey,full,applied):null;
 ctx.restore();canvas.dataset.audit=JSON.stringify({case:j.key,tier,time:t,actual_distance:v.distance,selected_targets:1,heal_events:applied?1:0,restored_hp:applied?v.actual:0,neighbor_unchanged:true,status,errors:audit.slice(-15)});return status;
}
function detailOnly(canvas,j,tier,remaining,targetKey='target',full=false){const ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;ctx.save();ctx.scale(1.5,1.5);const d=detail(ctx,j,tier,remaining,targetKey,full,true,{x:0,y:0,w:320,h:230});ctx.restore();canvas.dataset.audit=JSON.stringify(d);}
window.HEAL_RENDER={load,scene,detailOnly,values,audit};
})();
