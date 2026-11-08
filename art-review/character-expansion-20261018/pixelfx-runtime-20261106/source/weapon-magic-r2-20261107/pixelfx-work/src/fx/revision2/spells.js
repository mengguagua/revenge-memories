// Uses PixelFX's native lightning inking, flame tongues, simulated sparks and smoke.
// Lightning/fire recipes: Sprite Fusion https://www.spritefusion.com/pixel-art-vfx,
// MIT License, Copyright (c) 2026 Hugo Duprez. Choreography and geometry are game-specific.
import {Particles, P, Rng, rng, fit, clamp, smooth, ease, sparkle, flare, band, TAU, mix, hex, noise} from '../../core/index.js';
import {zigzag, stroke, crackle, trace} from '../lightning/_lib.js';
import {flameTongue, flameBlade, firePuff, smokePuff, noiseFor, BIG_LAYERS, BACK_LAYERS} from '../fire/_lib.js';

export const meta={name:'Native spell choreography',tags:['magic','native','impact'],size:[128,128],origin:[64,100],duration:2,loop:false,fps:60,bg:'none',options:{seed:23,kind:'thunder',phase:'impact',hit:.25,size:1,palette:['#252a40','#3d4967','#617492','#89a0b4','#b5c8d1','#e0e8df','#f1f0dc','#faf4dc']}};
function ellipse(p,x,y,rx,ry,C,a,spin=0,dashes=false){
  for(let i=0;i<100;i++){
    if(dashes&&i%9>5)continue;
    const g=i/100*TAU+spin,near=Math.sin(g)>=0;
    p.dot(x+Math.cos(g)*rx,y+Math.sin(g)*ry,C[near?5:2],a);
    if(near&&rx>15)p.dot(x+Math.cos(g)*rx,y+Math.sin(g)*ry+1,C[1],a*.6);
  }
}
function crescent(p,x,y,r,spin,C,k,width=2,sy=.65,span=3.8){
  p.shade(x-r-2,y-r-2,x+r+2,y+r+2,(px,py,out)=>{
    const dx=px-x,dy=(py-y)/sy,d=Math.hypot(dx,dy);let a=(Math.atan2(dy,dx)-spin+TAU*3)%TAU;
    if(a>span||d>r||d<r-width*Math.sin(a/span*Math.PI))return;
    const edge=r-d;out.c=C[edge<.7?6:edge<1.4?4:2];out.a=k*Math.min(1,(span-a)*2);
  });
}
function diamond(p,x,y,r,C,k){
  p.polyline([[x,y-r],[x+r*.7,y],[x,y+r],[x-r*.7,y],[x,y-r]],C[5],k);
  p.line(x,y-r*.6,x,y+r*.6,C[2],k*.65);
}
function eye(p,x,y,r,C,k,angle){
  for(const sign of[-1,1]){
    const pts=[];for(let n=0;n<=24;n++){const u=n/24;pts.push([x+(u-.5)*r*2,y+sign*Math.sin(u*Math.PI)*r*.36]);}
    p.polyline(pts,C[4],k);
  }
  diamond(p,x,y,5+Math.sin(angle)*1.2,C,k);p.px(x,y,C[7]);
}
function charge(p,t,o,C){
  const S=o.size,D=1.2,ph=t/D*TAU,n=o.kind,r=(6+1.2*Math.sin(ph))*S;
  const N=(rate,seed,off=0)=>noiseFor(D)(t,rate,seed,off);
  if(n==='fire'||n==='ragnarok'||n==='wisp'){
    for(let i=0;i<3;i++){
      const a=ph+i*TAU/3;
      flameTongue(p,Math.cos(a)*r*.65,Math.sin(a)*r*.35+3*S,(9+i*2)*S,2.2*S,Math.sin(a)*3*S,N,11+i,[...C].reverse(),BACK_LAYERS,.22,.5);
    }
    p.circle(0,0,3*S,C[4]);p.circle(-1,-1,1.6*S,C[6]);
    crescent(p,0,0,14*S,ph,C,.65,1,.65,3.5);
  }else if(n==='thunder'||n==='levin'){
    const frame=Math.floor(t*20)%24,rr=rng(o.seed,frame);
    for(let i=0;i<3;i++){const a=ph+i*TAU/3;crackle(p,zigzag(rr,Math.cos(a)*15*S,Math.sin(a)*11*S,0,0,.19,.2),.65,C,.10,.85);}
    p.circle(0,0,4*S,C[2]);p.circle(0,0,2*S,C[5]);p.px(0,0,C[7]);
    ellipse(p,0,0,10*S,6*S,C,.55,-ph);
  }else if(n==='holy'||n==='halo'||n==='rain'){
    for(let i=0;i<4;i++){const a=ph*.5+i*TAU/4;diamond(p,Math.cos(a)*r,Math.sin(a)*r,3*S,C,.7);}
    ellipse(p,0,0,13*S,8*S,C,.55,ph,true);sparkle(p,0,0,4*S,C[6],C[2],.15);
  }else if(n==='wind'){
    crescent(p,0,0,14*S,ph,C,.8,2,.6);crescent(p,0,0,9*S,ph+Math.PI,C,.65,1,.7);
  }else if(n==='slime'){
    p.ellipse(0,1,7*S,5*S,C[2]);p.ellipse(-1,-1,5*S,3*S,C[4]);p.line(-3*S,-3*S,0,-4*S,C[6]);
    for(let i=0;i<3;i++){const a=ph+i*TAU/3;p.circle(Math.cos(a)*11*S,Math.sin(a)*7*S,1.2*S,C[3]);}
  }else if(n==='medusa'){
    eye(p,0,0,14*S,C,.85,ph);for(let i=0;i<3;i++)crescent(p,0,0,(9+i*4)*S,ph+i*1.8,C,.35,1,.7,1.4);
  }else{
    for(let i=0;i<3;i++)crescent(p,0,0,(8+i*4)*S,ph+i*2.1,C,.7-i*.12,2,.7,3.4);
    p.circle(0,0,3*S,C[0]);p.arc(0,0,3*S,1,.3,2.3,C[5],.8);
  }
  p.glow(0,0,12*S,C[3],.11);
}
function travel(p,t,o,C){
  const S=o.size,n=o.kind,D=.8,N=(rate,seed,off=0)=>noiseFor(D)(t,rate,seed,off),ph=t/D*TAU;
  if(n==='fire'||n==='ragnarok'||n==='wisp'){
    flameBlade(p,0,0,-1,0,26*S,4.5*S,Math.sin(ph)*3*S,N,3,[...C].reverse(),BIG_LAYERS,.25,.5);
    flameBlade(p,-2,-1,-1,-.12,17*S,2.3*S,1,N,5,[...C].reverse(),BACK_LAYERS,.2,.4);
    p.circle(0,0,4*S,C[4]);p.circle(1,-1,2*S,C[6]);
  }else if(n==='wind'){
    crescent(p,-3,0,11*S,-1.8+Math.sin(ph)*.12,C,1,3,.65,3.7);
    for(let j=0;j<3;j++)p.line((-15-j*5)*S,(-5+j*5)*S,(-26-j*5)*S,(-5+j*5)*S,C[3],.6);
  }else if(n==='slime'){
    p.ellipse(-3,0,8*S,6*S,C[1]);p.ellipse(-2,-1,6*S,4*S,C[3]);p.ellipse(0,-2,3*S,2*S,C[5]);
    for(let i=0;i<4;i++){const x=(-16-i*5)*S,y=Math.sin(ph+i)*2*S;p.circle(x,y,(2-i*.3)*S,C[3-i%2]);}
  }else if(n==='medusa'||n==='death'){
    crescent(p,-2,0,10*S,ph,C,.9,3,.8);p.circle(0,0,3*S,C[1]);p.line(-26*S,0,-7*S,0,C[4],.6);
    for(const s of[-1,1])p.polyline([[-33*S,s*5*S],[-20*S,s*3*S],[-9*S,0]],C[2],.6);
  }else if(n==='drain'){
    for(let i=0;i<3;i++){const x=-i*7*S,y=Math.sin(ph+i)*2*S;p.circle(x,y,(3-i*.7)*S,C[4-i]);p.px(x,y-1,C[6-i]);}
  }else{
    p.poly([[3*S,0],[-5*S,-4*S],[-11*S,0],[-5*S,4*S]],C[3]);p.line(-9*S,0,3*S,0,C[7]);
    for(let i=0;i<3;i++)p.line((-12-i*7)*S,(-3+i*3)*S,(-23-i*7)*S,(-3+i*3)*S,C[4-i],.8);
  }
}
export function create(o){
  const C=fit(o.palette,8),R=new Rng(o.seed),S=o.size,H=o.hit,kind=o.kind,F=[...C].reverse(),floor=18*S;
  const ps=new Particles({rng:R,ground:()=>floor,sparks:[C[7],C[5],C[3],C[2]]});
  const start=kind==='levin'?[-32*S,-43*S]:[7*S,-78*S];
  const main=zigzag(new Rng(o.seed+11),...start,0,0,.11,.9);
  if(kind==='thunder'||kind==='levin'){
    const trunk=main.paths[0].pts;
    for(const [part,side] of[[.34,-1],[.55,1],[.71,-1]]){
      const from=trunk[Math.floor((trunk.length-1)*part)];
      const fork=zigzag(new Rng(o.seed+Math.floor(part*100)),...from,from[0]+side*(kind==='levin'?16:23)*S,Math.min(-6*S,from[1]+27*S),.15,.35,.55);
      main.paths.push(...fork.paths);
    }
  }
  main.paths=main.paths.map(q=>({...q,pts:q.pts.filter(([x,y])=>Math.abs(x)<54*S&&y>-88*S&&y<8*S)})).filter(q=>q.pts.length>1);
  const branches=Array.from({length:5},(_,i)=>zigzag(new Rng(o.seed+i+31),0,floor-3,(i-2)*12*S,floor-3+Math.abs(i-2),.14,.35));
  const debris=Array.from({length:kind==='ragnarok'?10:6},()=>({x:R.range(-12,12)*S,vx:R.range(-10,10)*S,vy:R.range(-24,-8)*S,r:R.range(2,4)*S,life:R.range(.6,1.15)}));
  let t=0,hit=false;
  return{
    update(dt){
      t+=dt;
      if(o.phase!=='impact')return;
      if(!hit&&t>=H){
        hit=true;const count=(kind==='ragnarok'?18:kind==='thunder'||kind==='levin'?14:10)*S;
        for(let i=0;i<count;i++){
          const a=R.range(-Math.PI,0.45),v=R.range(24,78)*S;
          ps.spawn(kind==='wind'||kind==='holy'||kind==='halo'?P.MOTE:P.SPARK,0,0,Math.cos(a)*v,Math.sin(a)*v-R.range(2,12),R.range(.25,.6),C[R.int(4,7)],.7);
        }
        if(['fire','ragnarok','wisp'].includes(kind))for(let i=0;i<8*S;i++)ps.spawn(P.EMBER,R.range(-8,8)*S,R.range(-6,2)*S,R.range(-18,18)*S,-R.range(12,38)*S,R.range(.5,1.2),C[3+i%3]);
        if(kind==='slime')for(let i=0;i<9;i++)ps.spawn(P.GRIT,0,0,R.range(-40,40)*S,-R.range(25,70)*S,.7,C[3+i%3],1.2*S);
      }
      ps.update(dt);
    },
    draw(p){
      if(o.phase==='charge')return charge(p,t%1.2,o,C);
      if(o.phase==='travel')return travel(p,t%.8,o,C);
      const a=t-H,q=clamp(a/.65),k=1-smooth(.05,.7,a),N=(rate,seed,off=0)=>noise(t*rate+off,seed);
      if(t<H){
        const u=clamp(t/H);
        if(kind==='thunder'||kind==='levin'){
          ellipse(p,0,floor,9+8*u*S,2.2+u*2,C,.3+.4*u,-t*2,true);
          if(u>.35)stroke(p,main,.25+.2*u,C,.45,{upTo:(u-.35)/.65,light:.07,a:.65});
        }else if(kind==='ragnarok'){
          ellipse(p,0,floor,(10+16*u)*S,(2+3*u)*S,C,.35+.4*u,t);
          for(let i=0;i<3;i++){const g=i*TAU/3+t*4;p.dot(Math.cos(g)*(18-10*u)*S,-30*u*S,C[4],.8);}
        }else if(kind==='death'||kind==='medusa'){
          if(kind==='medusa')eye(p,0,-8*S,(8+13*u)*S,C,u,t*3);
          else for(let i=0;i<3;i++)crescent(p,0,0,(22-10*u+i*2)*S,t*3+i*2,C,u*.7,2,.7);
        }else if(kind==='rain'){
          for(let i=-1;i<=1;i++){
            const x=i*14*S,head=-65*S*(1-ease.inQuad(u));
            p.line(x,head-12*S,x*.4,head,C[5],.4+.5*u);
            p.poly([[x*.4,head+3*S],[x*.4-2*S,head-2*S],[x*.4+2*S,head-2*S]],C[6],.6+.4*u);
          }
        }else{
          ellipse(p,0,0,(16-9*u)*S,(9-4*u)*S,C,.25+.45*u,t);
        }
        return;
      }
      if(a<.045){sparkle(p,0,0,(kind==='ragnarok'?16:9)*S*(1-a/.05),C[7],C[4],.18);p.glow(0,0,20*S,C[4],.2*(1-a/.05));}
      if(kind==='thunder'||kind==='levin'){
        if(a<.30)stroke(p,main,Math.max(.12,Math.pow(1-a/.3,1.4)),C,1.05*S,{hero:a<1/60,light:.16,core:a<.075?.8*S:0,a:1-smooth(.18,.31,a)});
        else if(a<.85){
          for(const branch of main.paths)for(let j=0;j<branch.pts.length-1;j++){
            if((j+o.seed)%6/6 < (a-.3)/.55)continue;
            p.line(...branch.pts[j],...branch.pts[j+1],C[2],1-smooth(.45,.85,a));
          }
        }
        if(a<.55){
          ellipse(p,0,floor,(8+25*ease.outCubic(q))*S,(2+3*q)*S,C,k);
          for(const br of branches)crackle(p,br,.8*(1-q),C,.09,k*.65);
          if(kind==='levin')for(const sign of[-1,1])p.polyline([[-25*S,sign*9*S],[-8*S,sign*3*S],[4*S,0]],C[5],k*.8);
        }
      }else if(['fire','ragnarok','wisp'].includes(kind)){
        const powerful=kind==='ragnarok',life=powerful?.78:.55,heat=1-smooth(.10,life,a);
        if(heat>0){
          const n=powerful?5:4;
          for(let i=0;i<n;i++){
            const ang=-Math.PI*.95+i/(n-1)*Math.PI*.9,reach=(powerful?36:20)*S*ease.outExpo(clamp(a/.08))*heat;
            flameBlade(p,0,2*S,Math.cos(ang),Math.sin(ang),reach,(powerful?5:3.6)*S*heat,Math.sin(i*2)*5*S,N,i+3,F,BIG_LAYERS,.3,.6);
          }
          if(powerful)flameTongue(p,0,floor,58*S*heat,8*S*heat,4*S,N,27,F,BIG_LAYERS,.3,1);
          ellipse(p,0,floor,(8+24*q)*S,(2+4*q)*S,C,heat*.75);
        }
        for(const d of debris){const age=a-.12;if(age>0&&age<d.life)smokePuff(p,d.x+d.vx*age,-4*S+d.vy*age,1-age/d.life,d.r*(1+age),mix(C[1],hex('#4b4852'),.4),false,.55);}
      }else if(kind==='holy'||kind==='halo'||kind==='rain'){
        const big=kind==='halo',end=big?.85:.63,fade=1-smooth(.08,end,a);
        if(fade>0){
          if(kind==='rain'){
            for(let i=-1;i<=1;i++){
              const x=i*13*S,top=-58*S,progress=ease.outExpo(clamp(a/.08));
              p.line(x,top*(1-progress),x*.12,0,C[5],fade);
              p.line(x-2*S,top*(1-progress)-4*S,x*.12,0,C[2],fade*.7);
            }
          }else{
            const height=(big?61:48)*S,half=(big?5:3)*S*fade;
            p.poly([[-half,0],[-half*.7,-height],[half*.7,-height],[half,0]],C[2],fade>.7?1:fade);
            p.line(-1*S,-height,0,5*S,C[4],fade);
            p.glowLine(0,-height*.88,0,2*S,5*S,C[4],.15*fade);
            p.line(0,-height,0,6*S,C[6],fade);
            for(let i=0;i<(big?3:2);i++)ellipse(p,0,-i*14*S,(10+16*q-i*2)*S,(3+4*q)*S,C,fade*.8,0,i===1);
          }
          for(let i=0;i<6;i++){const g=i*TAU/6+.4,x=Math.cos(g)*(10+13*q)*S,y=Math.sin(g)*(8+10*q)*S,r=3*S*fade;p.poly([[x,y-r],[x+r*.55,y],[x,y+r],[x-r*.55,y]],C[3],fade);p.line(x,y-r,x+r*.55,y,C[5],fade);}
          sparkle(p,0,0,(12+4*q)*S*fade,C[6],C[3],.18*fade);
        }
      }else if(kind==='wind'){
        if(a<.7)for(let i=0;i<3;i++){
          const spin=-1.6+i*TAU/3+q*2.2,r=(18+16*q-i*4)*S;
          crescent(p,(i-1)*6*S,Math.sin(i*2.2)*6*S,r,spin,C,k*(1-i*.08),(5-i*.5)*S,.63,2.35);
        }
        ellipse(p,0,floor,(8+25*q)*S,(2+3*q)*S,C,k*.45);
      }else if(kind==='slime'){
        const fade=1-smooth(.25,.95,a),radius=(6+10*ease.outCubic(clamp(a/.16)))*S;
        if(fade>0){
          for(let i=0;i<5;i++){
            const ang=-Math.PI+i*Math.PI/4,x=Math.cos(ang)*radius,y=Math.sin(ang)*radius*.7+Math.min(floor,30*a*a)*S;
            p.ellipse(x,y,(4-i%2)*S*fade,6*S*fade,C[1],fade);p.ellipse(x-1,y-1,3*S*fade,4*S*fade,C[3],fade);p.ellipse(x-1,y-3,1.5*S*fade,2*S*fade,C[5],fade);
            if(a<.25)p.beam(x,y,x*.45,Math.min(floor-2,10*a)*S,1.5*S,C[2],fade);
          }
          ellipse(p,0,floor,(9+14*q)*S,(2+3*q)*S,C,fade*.8);p.glow(0,0,14*S,C[3],.08*fade);
        }
      }else{
        const fade=1-smooth(.14,.85,a),radius=(10+14*ease.outCubic(clamp(a/.3)))*S;
        if(fade>0){
          if(kind==='medusa'){
            eye(p,0,-4*S,23*S*fade,C,fade,a*12);
            for(let i=0;i<6;i++){const g=i*TAU/6+a*2;diamond(p,Math.cos(g)*radius,Math.sin(g)*radius*.7,3*S*fade,C,fade);}
          }else{
            for(let i=0;i<3;i++)crescent(p,0,0,radius-i*3*S,a*4+i*TAU/3,C,fade*(1-i*.16),(kind==='death'?5:3)*S,.68,3.9);
            if(kind==='death')for(let i=0;i<4;i++){
              const g=i*TAU/4+.3,L=(26-14*q)*S;
              p.poly([[0,0],[Math.cos(g-.08)*L,Math.sin(g-.08)*L*.7],[Math.cos(g+.14)*L*.7,Math.sin(g+.14)*L*.7]],C[2],fade*.8);
            }
          }
          ellipse(p,0,floor,(8+22*q)*S,(2+3*q)*S,C,fade*.6);p.glow(0,0,22*S,C[3],.11*fade);
        }
      }
      ps.draw(p);
    }
  };
}
