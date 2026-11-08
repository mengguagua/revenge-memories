// Directional smears and decaying sparks adapt PixelFX melee/thrust and projectiles/arrow.
// Underlying slash/dash/spark recipes: Sprite Fusion, https://www.spritefusion.com/pixel-art-vfx,
// MIT License, Copyright (c) 2026 Hugo Duprez. Native geometry authored for this game.
import { Particles, P, Rng, fit, sparkle, smooth, clamp, ease, TAU, hex, mix } from '../../core/index.js';
import { beat } from '../projectiles/_lib.js';

export const meta={name:'Profession weapon feedback',tags:['weapon','native','directional'],size:[144,96],origin:[88,64],duration:1,loop:false,fps:60,bg:'none',options:{seed:17,tier:1,style:'soldier',mode:'lance',palette:['#28343e','#4c6572','#79949a','#adc0be','#d5dfd3','#f2edcf']}};

function arc(p,cx,cy,rx,ry,a0,a1,C,k,width=1){
  for(let a=a0;a<=a1;a+=.045){
    const u=(a-a0)/(a1-a0),edge=Math.sin(Math.PI*u);
    if(edge<.04)continue;
    for(let q=0;q<width;q++)p.dot(cx+Math.cos(a)*(rx-q),cy+Math.sin(a)*(ry-q*.45),C[q?3:5],k*Math.min(1,edge*3));
  }
}
function ray(p,x,y,L,C,k,wide=1){
  if(L<.5||k<=0)return;
  p.line(x-L,y,x+L*.5,y,C[5],k);
  p.line(x,y-L*.38,x,y+L*.38,C[4],k);
  if(wide>1){p.line(x-L*.65,y-1,x+L*.22,y-1,C[3],k);p.line(x-L*.55,y+1,x+L*.15,y+1,C[2],k);}
  p.px(x,y,C[7]);p.glow(x,y,L*.8+5,C[4],.13*k);
}
function plume(p,x,y,length,spread,C,k,wing=false,width=1){
  for(const sign of[-1,1]){
    const pts=[];
    for(let n=0;n<=14;n++){
      const u=n/14,xx=x-length*u,yy=y+sign*(Math.sin(u*Math.PI*.8)*spread);
      pts.push([xx,yy]);
    }
    p.polyline(pts,C[5],k);
    if(width>1)for(let px=0;px<length;px++){
      const u=px/length,yy=y+sign*Math.sin(u*Math.PI*.8)*spread,w=width*Math.sin(Math.PI*u);
      for(let q=0;q<w;q++)p.dot(x-px,yy-sign*q,C[q<.75?5:q<1.7?3:1],k>.75?1:k);
    }
    if(wing)for(let j=2;j<6;j++){
      const u=j/7,xx=x-length*u,yy=y+sign*Math.sin(u*Math.PI*.8)*spread;
      p.line(xx,yy,xx-length*.14,yy+sign*3,C[3],k*(1-u));
    }
  }
}
function weaponFlight(p,t,o,C){
  const D=.6,tier=o.tier,hero=o.style.startsWith('hero'),advanced=o.style==='hero-advanced';
  const L=({archer:20,sniper:24,bowknight:25,'hero-base':23,'hero-advanced':27})[o.style]||22;
  const windCount=tier===1?3:tier===2?5:8;
  beat(t,D,windCount,o.seed,r=>r.range(.12,.22),(age,life,r)=>{
    const u=age/life,from=-7-age*(55+tier*12),y=r.sign()*(2+tier+u*2),len=(5+tier*2)*(1-u*.2);
    if(from-len< -61)return;
    p.line(from,y,from-len,y+Math.sin(t*TAU/D)*.4,C[3+Math.floor((1-u)*2)],(1-u)*.7);
  });
  if(tier>=2)plume(p,-2,0,14+tier*4,2+tier,C,.28,hero);
  const W=['#302d27','#65543d','#9d8054','#d0b57d'].map(hex);
  p.line(-L+5,0,-4,0,W[2]);p.line(-L+5,1,-4,1,W[0]);
  for(let x=-L+9;x<-4;x+=7)p.px(x,0,W[3]);
  const flutter=Math.sin(t*TAU/D*2)>0?1:0,feather=hero?C[5]:C[4];
  for(const s of[-1,1]){
    p.line(-L,0,-L+4,-s*(2+flutter),C[1]);p.line(-L+1,0,-L+5,-s*(2+flutter),feather);
    p.line(-L+3,0,-L+7,-s*2,C[3]);
  }
  if(o.style==='sniper'){
    p.poly([[-7,-1],[0,0],[-7,2],[-5,0]],C[4]);p.line(-6,0,0,0,C[7]);
  }else{
    p.poly([[-6,-2],[0,0],[-6,3],[-4,0]],C[2]);p.line(-6,-1,0,0,C[6]);p.line(-4,1,0,0,C[4]);
  }
  if(hero){
    p.px(-8,-1,C[6]);p.px(-8,1,C[3]);
    if(advanced){p.line(-12,-2,-8,-3,C[4]);p.line(-12,2,-8,3,C[4]);p.glow(-3,0,7,C[4],.13);}
  }
}
function wake(p,t,o,C){
  const tier=o.tier,D=.6;
  beat(t,D,3+tier*2,o.seed,r=>r.range(.15,.26),(age,life,r)=>{
    const u=age/life,x=-age*(85+tier*10),y=r.sign()*(2+tier+u*4),L=(7+tier*4)*(1-u*.35);
    if(x-L < -61)return;
    p.line(x,y,x-L,y,C[4],(1-u)*.7);
  });
  const styles=['cavalry','pegasus','falcon','knight','grandknight'];
  if(styles.includes(o.style))plume(p,-2,0,17+tier*5,3+tier,C,.42,o.style==='falcon');
  else if(o.style==='bastion'||o.style==='armored'){
    for(const s of[-1,1])p.line(-3,s*3,-24-tier*3,s*(6+tier),C[3],.45);
  }
}
export function create(o){
  const C=fit(o.palette,8),R=new Rng(o.seed),tier=o.tier,style=o.style;
  const ps=new Particles({rng:R,ground:()=>o.mode==='maphit'?5:14,sparks:[C[7],C[5],C[3],C[1]]});
  let t=0,struck=false;const HIT=.07;
  function burst(){
    const n=o.mode==='maphit'?4:({soldier:3,armored:7,bastion:12,cavalry:4,knight:8,grandknight:14,pegasus:4,falcon:10,archer:3,sniper:7,bowknight:12,'hero-base':8,'hero-advanced':16})[style]||6;
    for(let i=0;i<n;i++){
      const a=R.range(-1.6,1.2)+(R.chance(.18)?Math.PI:0),v=o.mode==='maphit'?R.range(10,25):R.range(22,54+tier*12);
      ps.spawn(P.SPARK,0,0,Math.cos(a)*v,Math.sin(a)*v-22,R.range(.17,.40));
    }
    if(['armored','bastion','grandknight','bowknight'].includes(style)){
      for(let i=0;i<tier+1;i++)ps.spawn(P.DUST,R.range(-7,7),12,R.range(-20,20),-R.range(8,18),R.range(.23,.43),C[1],R.range(1.5,2.6));
    }
  }
  return{
    update(dt){t+=dt;if(!['arrow','wake'].includes(o.mode)&&!struck&&t>=HIT){struck=true;burst();}ps.update(dt);},
    draw(p){
      if(o.mode==='arrow')return weaponFlight(p,t%meta.duration,o,C);
      if(o.mode==='wake')return wake(p,t,o,C);
      if(o.mode==='maphit'){
        const a=t-HIT,k=1-smooth(.035,.30,a);
        if(a>=0&&a<.32){const g=ease.outExpo(clamp(a/.025))*k;ray(p,0,0,6*g,C,k);for(const s of[-1,1])p.polyline([[-11*g,s*4*g],[-5*g,s*2*g],[2*g,0]],C[5],k);}
        ps.draw(p);return;
      }
      const a=t-HIT,q=clamp(a/.42),k=(1-smooth(.055,.43,a)),head=ease.outCubic(clamp(t/HIT));
      if(t<.31){
        const len=(o.mode==='bowhit'?15:22)+tier*8,tail=-len+(len*(smooth(.10,.30,t)));
        p.line(tail,1,-len*(1-head),1,C[1],1-smooth(.15,.31,t));
        p.line(tail,0,-len*(1-head),0,C[6],1-smooth(.15,.31,t));
        if(tier>=2)p.line(tail+4,-1,-len*(1-head),-1,C[3],.7*(1-smooth(.13,.29,t)));
      }
      if(a>=0&&a<.48){
        const L=(o.mode==='bowhit'?7:8)+tier*4,g=ease.outExpo(clamp(a/.035))*k;
        ray(p,0,0,L*g,C,k,tier>=2?2:1);
        switch(style){
          case 'soldier':p.line(-18*q,-3,2,-1,C[3],k*.65);break;
          case 'armored':
            p.poly([[-28*g,-7*g],[4,0],[-28*g,7*g],[-13*g,0]],C[2],k>.75?1:k);
            p.line(-27*g,-7*g,4,0,C[5],k);p.line(-27*g,7*g,4,0,C[3],k);break;
          case 'bastion':
            for(let j=0;j<3;j++){const x=-9-j*14*(.6+q),h=5+j*3;p.poly([[x-10,-h],[x,0],[x-10,h],[x-4,0]],C[2],k>.75?1:k);p.polyline([[x-10,-h],[x,0],[x-10,h]],C[5-j%2],k);}
            arc(p,4+10*q,0,4+6*q,8+5*q,-1.35,1.35,C,k,3);break;
          case 'cavalry':
            plume(p,1,0,30*g,5*g,C,k*.75);p.line(-32*g,5,1,2,C[2],k);break;
          case 'knight':
            for(let j=0;j<2;j++)arc(p,-7-j*12+10*q,0,7+3*q,10,-1.55,1.55,C,k*(1-j*.12),3);
            plume(p,0,0,38*g,7,C,k*.9,false,2);break;
          case 'grandknight':
            for(let j=0;j<3;j++)arc(p,-8-j*15+15*q,0,8+6*q,12+j*.5,-1.5,1.5,C,k*(1-j*.09),4);
            plume(p,0,0,55*g,10,C,k*.92,false,3);break;
          case 'pegasus':plume(p,0,0,29*g,9*g,C,k,true);break;
          case 'falcon':
            plume(p,1,0,48*g,14*g,C,k,true,3);
            for(const s of[-1,1])p.line(-17*g,s*9*g,7*g,s*3*g,C[6],k);break;
          case 'archer':p.line(-13*g,2,6*g,-1,C[3],k*.6);break;
          case 'sniper':
            ray(p,1,0,26*g,C,k,1);arc(p,6+8*q,0,3+q*2,8,-1.5,1.5,C,k*.8);break;
          case 'bowknight':
            plume(p,2,0,38*g,10,C,k,false,3);for(let j=0;j<2;j++)arc(p,-6-j*14+13*q,0,5+6*q,12,-1.4,1.4,C,k*(1-j*.12),2);break;
          case 'hero-base':
            for(const s of[-1,1]){p.polyline([[-28*g,s*8*g],[-8*g,s*3*g],[5*g,0]],C[5],k);p.line(-12*g,s*11*g,0,0,C[3],k*.6);}
            sparkle(p,1,0,8*g,C[6],C[2],.2*k);break;
          case 'hero-advanced':
            for(const s of[-1,1])for(let j=0;j<3;j++){
              const L=(26+j*10)*g,y=(5+j*4)*g;
              p.poly([[-L,s*y],[-L*.45,s*(y*.7)],[(6-j*3)*g,0],[-L*.48,s*(y*.7-2)]],C[3-j%2],k>.75?1:k);
              p.polyline([[-L,s*y],[-L*.45,s*(y*.7)],[(6-j*3)*g,0]],C[5-j%2],k*(1-j*.1));
            }
            arc(p,4+9*q,0,6+5*q,12,-1.45,1.45,C,k,2);break;
        }
        p.glow(0,0,11+tier*5,C[4],.12*k);
      }
      p.place(p.tx,p.ty,false,0);ps.draw(p);
    }
  };
}
