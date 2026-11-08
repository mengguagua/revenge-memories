// Native 256x128 battle feedback built with PixelFX's painter, particles,
// holy oval and fire-puff recipes. No stock actor, extra hit or status effect.
import {Particles,P,Rng,fit,sparkle,clamp,smooth,ease,TAU} from '../../core/index.js';
import {oval} from '../holy/_lib.js';
import {firePuff,hotFirst,flameBlade,noiseFor,BIG_LAYERS} from '../fire/_lib.js';
export const meta={name:'Native feedback',desc:'One contact, then a quiet, material-specific release.',tags:['combat','native','one-shot'],size:[80,72],origin:[40,64],duration:1.05,fps:60,loop:false,bg:'none',options:{mode:'holy',palette:['#242b33','#45545e','#76868d','#b4c4c4','#e3e5d8'],seed:13}};
export function create(o){
 const C=fit(o.palette,8),R=new Rng(o.seed),mode=o.mode,map=mode.startsWith('map-'),Y=map?-5:-20;
 const ps=new Particles({rng:R,ground:()=>-5,sparks:[C[7],C[6],C[4],C[3]]});
 const motes=Array.from({length:map?5:mode==='wind'?6:9},(_,i)=>({a:i*TAU/(map?5:9)+R.range(-.2,.2),r:R.range(map?3:8,map?8:19),life:R.range(.42,.85),delay:R.range(0,.06),v:R.range(4,15),size:R.range(.7,1.7)}));
 const fire=Array.from({length:5},(_,i)=>({x:(i-2)*1.8,y:-Math.max(0,5-Math.abs(i-2)*2),vx:(i-2)*4,vy:-R.range(15,26),life:R.range(.45,.7),s:i===2?5:R.range(2.2,3.5)}));
 if(['stone','fire','wind','map-hit'].includes(mode))for(let i=0;i<(map?4:8);i++){
  const a=R.range(-2.6,-.5),v=R.range(map?10:20,map?28:57);
  ps.spawn(mode==='stone'?P.GRIT:mode==='wind'?P.MOTE:P.SPARK,0,Y,Math.cos(a)*v,Math.sin(a)*v,R.range(.2,.55),C[3+R.int(0,3)],1);
 }
 const noise=noiseFor(0);let t=0;
 return {update(dt){t+=dt;ps.update(dt);},draw(p){
  const pop=Math.exp(-t/.07),fade=1-smooth(.48,1.,t);
  if(mode==='fire'){
   const H=hotFirst(fit(o.palette,9)),N=(rate,seed,off=0)=>noise(t,rate,seed,off),b=ease.outCubic(clamp(t/.035))*(1-smooth(.1,.38,t));
   for(const[a,len,w]of[[-2.5,11,3],[-1.7,18,4],[-.7,15,4],[.3,9,3]])flameBlade(p,0,Y+2,Math.cos(a),Math.sin(a),len*b,w*(.5+.5*b),2*Math.sin(a*2),N,23+Math.round(a*4),H,BIG_LAYERS,.2,.5);
   for(const q of fire){const u=t/q.life;if(u>=1)continue;firePuff(p,q.x+q.vx*t,Y+q.y+q.vy*t,(1-u)*.72,q.s*(.7+u),.8,H,.04,q.x*.03,-1.2);}
   if(t<.045){p.circle(0,Y,2+3*ease.outCubic(t/.045),C[6],1-t/.045);p.circle(0,Y,1,C[7],pop);}
   p.glow(0,Y,18,C[4],.16*pop);ps.draw(p);
  }else if(mode==='wind'){
   for(let j=0;j<3;j++){
    const u=clamp((t-j*.025)/.58);if(u<=0||u>=1)continue;
    const r=7+13*ease.outCubic(u),a=-1.3+j*2.04+u*1.7;
    p.arc(0,Y,r,1.4*(1-u)+.6,a,a+1.2,C[5+j%2],(1-u)*.85);
    p.arc(0,Y,r-2,.7,a+.24,a+1.05,C[3],(1-u)*.8);
   }ps.draw(p);
  }else if(mode==='void'||mode==='drain'){
   const u=clamp(t/.7),r=4+10*ease.outCubic(Math.min(1,t/.16));
   if(t<.32){p.ring(0,Y,r,2,C[3],1-t/.32);p.arc(0,Y,r+2,1,t*5,t*5+2.6,C[6],1-t/.32);}
   for(const q of motes){if(t>q.life)continue;const k=t/q.life,a=q.a+k*1.6,rr=(3+q.r)*(1-k);p.dot(Math.cos(a)*rr,Y+Math.sin(a)*rr-k*5,C[k<.5?5:3],1-k);}
   if(mode==='drain'&&t<.5)sparkle(p,0,Y,4*(1-t/.5),C[6],C[3],.45);
  }else if(mode==='stone'){
   if(t<.16){const u=t/.16;for(let i=0;i<4;i++){const a=i*TAU/4+.3;const r=3+u*8;p.line(Math.cos(a)*r,Y+Math.sin(a)*r,Math.cos(a)*(r+4),Y+Math.sin(a)*(r+4),C[6],1-u);}}
   for(const q of motes){const u=t/q.life;if(u>=1)continue;const x=Math.cos(q.a)*q.r*u,y=Math.min(-5,Y+Math.sin(q.a)*q.r*u+32*t*t);p.poly([[x-1,y],[x,y-2],[x+2,y],[x+1,y+2]],C[3],1-u);p.dot(x,y-1,C[5],1-u);}
   ps.draw(p);
  }else if(mode==='warp'){
   const u=clamp(t/.85),r=10*Math.sin(Math.PI*u);
   oval(p,0,-3,r,r*.32,C[5],fade);oval(p,0,-3-28*u,r*.65,r*.18,C[6],fade*.8);
   for(const q of motes){const a=q.a+t*4;const rr=8*(1-u*.5);p.dot(Math.cos(a)*rr,-3-u*(19+q.r),C[5],fade);}
  }else if(mode==='wake'){
   for(let j=0;j<3;j++){
    const f=(t*7+j*.29)%1,x=-4-f*19,y=(j-1)*3;
    p.line(x,y,x-3,y,C[4],.45*(1-f));p.dot(x-4,y,C[2],.28*(1-f));
   }
  }else if(mode==='dust'){
   for(let j=0;j<5;j++){const u=t/(.38+j*.035);if(u>=1)continue;const x=(j-2)*(2+u*7),y=-3-Math.sin(u*Math.PI)*(2+j%2);p.ellipse(x,y,2+u,1,C[3],.32*(1-u));}
  }else if(mode==='map-hit'){
   if(t<.14){sparkle(p,0,Y,4*(1-t/.14),C[7],C[4],.18);p.arc(0,Y,3+t*22,1,-2.4,.4,C[5],1-t/.14);}ps.draw(p);
  }else if(mode==='map-heal'||mode==='map-warp'){
   const u=clamp(t/.7),y=-2-u*8,r=5*(1-u*.3);
   for(const[dx,dy]of[[-1,0],[1,0],[0,-1],[0,1]])oval(p,dx,y+dy,r,2,C[1],.75*(1-u));
   oval(p,0,y,r,2,C[6],1-u);
   if(mode==='map-heal'&&u>.2&&u<.65){p.rect(-1,-11-u*3,3,1,C[6],.9);p.rect(0,-12-u*3,1,3,C[6],.9);}
   for(const q of motes){const k=t/q.life;if(k>=1)continue;p.dot(Math.cos(q.a)*4,-3-k*9,C[6],1-k);}
  }else{
   // Holy contact: one narrow cross, then warm fragments leaving the target.
   if(t<.17){const u=t/.17;const len=(3+10*ease.outCubic(Math.min(1,t/.04)))*(1-u);sparkle(p,0,Y,len,C[7],C[4],.25*(1-u));}
   for(const q of motes){const u=(t-q.delay)/q.life;if(u<0||u>=1)continue;const x=Math.cos(q.a)*q.r*u,y=Y+Math.sin(q.a)*q.r*u-u*7;p.dot(x,y,C[u<.4?6:4],1-u);if(q.size>1.4&&u<.45)p.dot(x+1,y,C[4],(1-u)*.5);}
   p.glow(0,Y,18,C[4],.13*pop);
  }
 }};
}
