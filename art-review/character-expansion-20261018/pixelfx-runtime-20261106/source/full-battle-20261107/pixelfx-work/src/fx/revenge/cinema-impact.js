// PixelFX at the cinematic viewport's own logical pixel size, not an enlarged
// close-up sprite. One impact, readable target silhouette, no full-screen flash.
import{Particles,P,Rng,fit,sparkle,smooth,ease,clamp,TAU}from'../../core/index.js';
import{firePuff,hotFirst,flameBlade,noiseFor,BIG_LAYERS}from'../fire/_lib.js';
import{zigzag,stroke}from'../lightning/_lib.js';
export const meta={name:'Cinematic contact',desc:'One native-pixel contact for the actual hero cinematic.',tags:['combat','critical','one-shot'],size:[128,120],origin:[64,108],duration:1.35,fps:60,loop:false,bg:'none',options:{mode:'fire',palette:['#2d3442','#536c7a','#89a7b1','#c6d8d9','#eeefde'],seed:13}};
export function create(o){const C=fit(o.palette,8),R=new Rng(o.seed),Y=-38,mode=o.mode;const ps=new Particles({rng:R,ground:()=>-4,sparks:[C[7],C[6],C[4],C[3]]});
 const fire=Array.from({length:8},(_,i)=>({x:(i-3.5)*3.2,y:-Math.max(0,10-Math.abs(i-3.5)*4),vx:(i-3.5)*6,vy:-R.range(18,34),life:R.range(.65,1.05),s:R.range(5.5,8.5)}));
 const motes=Array.from({length:18},(_,i)=>({a:i/18*TAU+R.range(-.15,.15),r:R.range(18,37),life:R.range(.55,1.05)}));
 for(let i=0;i<12;i++){const a=R.range(-2.7,-.4),v=R.range(25,72);ps.spawn(mode==='fire'?P.SPARK:P.MOTE,0,Y,Math.cos(a)*v,Math.sin(a)*v,R.range(.3,.8),C[4+R.int(0,2)],1);}
 const bolt=zigzag(R,0,-100,0,Y,.22,.35),noise=noiseFor(0);let t=0;
 return{update(dt){t+=dt;ps.update(dt)},draw(p){
  if(mode==='fire'){
   const H=hotFirst(fit(o.palette,9)),N=(rate,seed,off=0)=>noise(t,rate,seed,off),b=ease.outCubic(clamp(t/.045))*(1-smooth(.14,.5,t));
   for(const[a,len,w]of[[-2.8,18,6],[-2.2,29,7],[-1.65,35,8],[-.95,27,7],[-.25,21,6],[.55,12,4]])flameBlade(p,0,Y+2,Math.cos(a),Math.sin(a),len*b,w*(.45+.55*b),4*Math.sin(a*2),N,37+Math.round(a*5),H,BIG_LAYERS,.35,.8);
   for(const q of fire){const u=t/q.life;if(u>=1)continue;firePuff(p,q.x+q.vx*t,Y+q.y+q.vy*t,(1-u)*.67,q.s*(.65+u),.8,H,.035,q.x*.025,-1.2);}
   if(t<.18)p.ring(0,Y,5+19*ease.outCubic(t/.18),1.5,C[4],.6*(1-t/.18));
  }else if(mode==='wind'){
   for(let j=0;j<3;j++){const u=clamp((t-j*.02)/.75);if(u<=0||u>=1)continue;const r=12+22*ease.outCubic(u),a=-1.7+j*2.08+u*2;p.arc(0,Y,r,2.8*(1-u)+.7,a,a+1.45,C[6],.9*(1-u));p.arc(0,Y,r-4,1,a+.25,a+1.4,C[3],1-u);}
  }else if(mode==='lightning'){
   if(t<.21)stroke(p,bolt,1-t/.21,C,.8,{hero:t<.04});
   for(const q of motes){const u=t/q.life;if(u>=1)continue;const r=q.r*u,a=q.a;const x=Math.cos(a)*r,y=Y+Math.sin(a)*r;p.line(x,y,x+Math.cos(a+.8)*4*(1-u),y+Math.sin(a+.8)*4*(1-u),C[u<.3?6:4],1-u);}
   if(t<.08)p.circle(0,Y,3,C[7],1-t/.08);
  }else{
   if(t<.3){const u=t/.3;sparkle(p,0,Y,(7+19*ease.outCubic(Math.min(1,t/.05)))*(1-u),C[7],C[4],.35*(1-u));p.arc(0,Y,8+23*u,1,-2.5,.25,C[5],.6*(1-u));}
   for(const q of motes){const u=t/q.life;if(u>=1)continue;const x=Math.cos(q.a)*q.r*u,y=Y+Math.sin(q.a)*q.r*u-u*10;p.dot(x,y,C[u<.4?6:4],1-u);if(u<.25)p.dot(x+1,y,C[4],.5);}
  }
  ps.draw(p);p.glow(0,Y,32,C[4],.14*Math.exp(-t/.12));
 }};
}
