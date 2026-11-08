// The preview uses the installed Skill's isolated PixelFX workspace.
// Keep source imports and geometry adaptations explicit so each image can be traced to a module.
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, rmSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadEffect, renderFrames, renderAct, edgeFade } from './pixelfx-work/tools/lib/fxlib.mjs';
import { createFrame, createFx, clearFrame, composite } from './pixelfx-work/src/core/index.js';
import { encodePNG } from './pixelfx-work/tools/lib/png.mjs';

const here=dirname(fileURLToPath(import.meta.url));
const out=resolve(here,'../../combat-polish-r5-20261107');
const dir=join(out,'assets/r5');
const roots=join(here,'pixelfx-work/src/fx');
mkdirSync(dir,{recursive:true});
const stock={
 damage:'ui/damage-number', life:'shadow/life-steal',
 fireball:'fire/fireball', blast:'explosions/small-explosion', pillar:'fire/flame-pillar', ring:'fire/fire-ring', spiral:'fire/fire-tornado',
 lightning:'lightning/lightning-strike', charge:'lightning/charge-up', double:'melee/double-slash', spin:'melee/spin-slash', reap:'melee/scythe-reap',
};
const sources={};
for (const [key,id] of Object.entries(stock)) {
 const fx=await loadEffect(id);
 sources[key]={fx,sha256:createHash('sha256').update(readFileSync(fx.file)).digest('hex')};
}
async function variant(key,name,changes,parent=null) {
 const id=stock[key], src=readFileSync(parent?join(roots,parent+'.js'):sources[key].fx.file,'utf8');
 let code=src;
 for (const [from,to] of changes) {
  if (!code.includes(from)) throw Error(id+': upstream pattern missing: '+from);
  code=code.replaceAll(from,to);
 }
 const asset=id.split('/')[0]+'/_r5-'+name;
 writeFileSync(join(roots,asset+'.js'),'// Adapted for the R5 preview; original PixelFX source and license retained.\n'+code);
 return loadEffect(asset);
}

// The most luminous step occupies only the core. Red midtones connect to the game's original charge sprite.
const flame=['#39171b','#651d22','#9b2625','#c83026','#e74325','#f76028','#ff903f','#ffc368','#ffefbf'];
const coal=['#271419','#501921','#7c2327','#a02a28','#c63729','#dd492c','#ed6635','#f39746','#ffe0a2'];
const ice=['#191835','#302b61','#4948a0','#5d6ed2','#728ce5','#91c2ee','#b5e9ff','#ecf7ff'];
const levin=['#201832','#34264e','#5e3f8b','#7e61c7','#8e82e7','#a2baff','#c4e7fc','#f3f4ff'];
const sparks=['#ffdd89','#fac16b','#e98251','#cb573d'];
const effects={}, provenance={};

function raster(fx,options,bb,settings={}) {
 const [x0,y0,x1,y1]=bb, fps=settings.fps??60, rate=settings.rate??1, seconds=settings.seconds??fx.meta.duration;
 const f=createFrame(x1-x0,y1-y0,x0,y0), n=Math.max(1,Math.ceil(fps*seconds)), tracks={};
 for (const layer of (settings.layers??['combined'])) tracks[layer]=[];
 const inst=createFx(fx.mod,options);
 if (settings.offset) inst.update(settings.offset);
 for (let i=0;i<n;i++) {
  const sec=i/fps;
  if (i) inst.update(rate/fps);
  for (const [layer,frames] of Object.entries(tracks)) {
   clearFrame(f);
   inst.draw(f,layer==='combined'?undefined:layer);
   edgeFade(f,8);
   const rgba=composite(f,new Uint8ClampedArray(f.w*f.h*4));
   const edge=settings.fade??0;
   if(settings.ink) applyInk(rgba,settings.ink);
   const scale=edge ? Math.min(1,(seconds-sec)/edge) : 1;
   for (let j=3;j<rgba.length;j+=4) {
    rgba[j]=Math.round(rgba[j]*scale);
    if (rgba[j]<4) rgba.fill(0,j-3,j+1);
   }
   frames.push(rgba);
  }
 }
 return {tracks,w:f.w,h:f.h,x0,y0,fps,n};
}

function atlas(name,r,layer,loop) {
 const frames=r.tracks[layer]; let minX=r.w,minY=r.h,maxX=-1,maxY=-1;
 for (const f of frames) for (let y=0;y<r.h;y++) for (let x=0;x<r.w;x++) {
  if (f[(y*r.w+x)*4+3]===0) continue;
  minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);
 }
 if (maxX<0) throw Error('Empty PixelFX render: '+name);
 const w=maxX-minX+1,h=maxY-minY+1;
 const pack=(group,cols)=>{
  const rows=Math.ceil(group.length/cols), stride=w*cols*4, bytes=new Uint8Array(w*cols*h*rows*4);
  for (const [i,f] of group.entries()) for(let y=0;y<h;y++){
   const j=((minY+y)*r.w+minX)*4;
   bytes.set(f.subarray(j,j+w*4),(Math.floor(i/cols)*h+y)*stride+(i%cols)*w*4);
  }
  return encodePNG(w*cols,h*rows,bytes);
 };
 let cells=0, cols=0, packed=[];
 for (const k of [30,20,15,10,8,6,4,2,1]) {
  cells=k; cols=Math.min(k===30||k===20||k===15||k===10?5:k===6?3:4,k);
  packed=[];
  for(let i=0;i<frames.length;i+=cells){
   const png=pack(frames.slice(i,i+cells),cols);
   if (png.length>=193000) {packed=[];break;}
   packed.push(png);
  }
  if (packed.length) break;
 }
 if (!packed.length) throw Error('Unable to pack PNG: '+name);
 rmSync(join(dir,name+'.png'),{force:true});
 for(const file of readdirSync(dir))if(file.startsWith(name+'-')&&/^\d+\.png$/.test(file.slice(name.length+1)))rmSync(join(dir,file));
 const paths=packed.map((png,i)=>{
  const path='assets/r5/'+name+'-'+String(i).padStart(2,'0')+'.png';
  writeFileSync(join(out,path),png);
  return path;
 });
 effects[name]={paths,atlasFrames:cells,frameSize:[w,h],pivot:[-r.x0-minX,-r.y0-minY],columns:cols,fps:r.fps,frames:r.n,loop};
}

function render(name,key,fx,options,bb,settings={}) {
 const r=raster(fx,options,bb,settings);
 for (const layer of Object.keys(r.tracks)) {
  const id='r5-'+name+(layer==='combined'?'':'-'+layer);
  atlas(id,r,layer,settings.loop??false);
  provenance[id]={module:stock[key],sha256:sources[key].sha256,options,render:settings,layer};
 }
 console.log(name+': '+r.n+' frames');
}

const jobs=JSON.parse(readFileSync(join(here,'effect-jobs.json'),'utf8'));
const rgb=c=>c.slice(1).match(/../g).map(n=>parseInt(n,16));
const lum=(r,g,b)=>r*.2126+g*.7152+b*.0722;
const mixHex=(a,b,k)=>'#'+rgb(a).map((v,i)=>Math.round(v+(rgb(b)[i]-v)*k).toString(16).padStart(2,'0')).join('');
function inkRamp([base,accent,white]) {
 return [mixHex(base,'#000000',.66),mixHex(base,'#000000',.40),base,base,base,mixHex(base,accent,.58),accent,accent,white];
}
function applyInk(rgba,{colors,enemy=false}) {
 const [base,bright,white]=colors.map(rgb);
 const b0=lum(...base),b1=lum(...bright),b2=lum(...white);
 for(let i=0;i<rgba.length;i+=4){
  if(!rgba[i+3])continue;
  const r=rgba[i],g=rgba[i+1],b=rgba[i+2],v=lum(r,g,b);
  // Preserve the exact sampled swatches. Particles and additive light from
  // the stock effect are also quantized, so no orange leaks into the result.
  const head=enemy ? (v>b2*.81&&b>=r*.96) : (v>210&&g>174&&b>149);
  const c=head?white:v>(b0+b1)*.51?bright:base;
  if(v<b0)rgba[i+3]*=Math.max(.12,(v/b0)**1.20);
  rgba[i]=c[0];rgba[i+1]=c[1];rgba[i+2]=c[2];
 }
}

const fire=await variant('fireball','matched-fireball',[
 ['for (const [sa, x, y, q] of smoke) smokePuff(p, x, y, 1 - sa / q.sl, q.s * 0.9, SMOKE);',
  '// Fire continues into embers. Do not draw the gray smoke puffs.'],
 ['looped(t, D, 130,','looped(t, D, 116,'],
]);
// Intercept the particle simulator on this instance only. This removes both
// explicit smoke/dust and secondary puffs spawned by expired fire particles.
const smokeGate=`
  const spawnInk = ps.spawn.bind(ps);
  ps.spawn = (kind, ...args) => (kind === P.SMOKE || kind === P.DUST) ? undefined : spawnInk(kind, ...args);
  `;
const blast=await variant('blast','matched-explosion',[
 ['const rocks = new Bits',smokeGate+'const rocks = new Bits'],
], 'explosions/_r4-fireball-impact');
for(const [name,bucket,radius,speed,angle,size,tail] of [
 ['fireball','battle',5.1,91,.20,.55,1.12],
 ['fireball-enemy','enemy',5.1,91,.20,.55,1.12],
 ['fireball-cinema','cinema',7.4,137,.27,.82,1.35],
 ['fireball-cinema-advanced','cinema',9.25,147,.27,.97,1.42],
]){
 const ink={colors:jobs.fire[bucket],enemy:bucket==='enemy'};
 const palette=inkRamp(ink.colors);
 render(name,'fireball',fire,{palette,radius,speed,angle,light:.06},[-140,-63,34,31],{seconds:1.2,loop:true,ink});
 render(name+'-hit','blast',blast,{palette,size,stone:'#4a302e',light:.08},[-129,-136,130,24],
  {seconds:tail,rate:size>.6?1.48:1.55,fade:.38,ink});
}

render('ragnarok-fuse','fireball',fire,{palette:coal,radius:2.9,speed:47,light:.20,seed:13},
 [-82,-23,20,16],{seconds:1.2,loop:true,fps:30});
const coil=await variant('spiral','clear-coil',[
 ['smokePuff(p, x, y, 1 - age / q.life, q.s, SMOKE);','// No gray smoke caps.'],
], 'fire/_r4-ragnarok-spiral');
render('ragnarok-coil','spiral',coil,{palette:coal,height:20,seed:11,light:.25},[-47,-55,48,15],{seconds:2,loop:true,fps:30});
const ring=await variant('ring','clear-ring',[
 ['const GLOW =',smokeGate+'const GLOW ='],
]);
render('ragnarok-ring','ring',ring,{palette:coal,reach:29,light:.25,seed:19},[-60,-40,61,14],{rate:.82,seconds:1.75,fade:.32,fps:30});
const column=await variant('pillar','clear-pillar',[
 ['const bits = new Bits',smokeGate+'const bits = new Bits'],
 ['if (R.chance(0.7 * dt * 60)) ps.spawn(P.FIRE, R.range(-w, w), -h + R.range(0, 6), R.range(-20, 20), -R.range(30, 80), R.range(0.35, 0.7), 0, R.range(3, 5.5), 0, R.chance(0.6) ? PF.SMOKES | (t < FALL - 0.3 ? PF.BIG : 0) : 0);',
  'if (t < FALL && R.chance(0.68 * dt * 60)) ps.spawn(P.FIRE, R.range(-w, w), -h + R.range(0, 6), R.range(-20, 20), -R.range(30, 80), R.range(0.24, 0.43), 0, R.range(2.2, 3.7));'],
 ['if (fell && t < GONE - 0.1 && R.chance(1.6 * dt * 60)) ps.spawn(P.FIRE, R.range(-w - 2, w + 2), -h - R.range(0, 8), R.range(-30, 30), -R.range(10, 50), R.range(0.4, 0.75), 0, R.range(3.5, 6.5), 0, PF.SMOKES);',
  'if (fell && t < GONE - 0.1 && R.chance(1.45 * dt * 60)) ps.spawn(P.EMBER, R.range(-w - 2, w + 2), -h - R.range(0, 7), R.range(-30, 30), -R.range(10, 36), R.range(0.25, 0.65), H[4], R.chance(0.18) ? 1.7 : 1);'],
], 'fire/_r4-ragnarok-pillar');
render('ragnarok-pillar','pillar',column,{palette:flame,height:69,stone:'#513b48',seed:11,light:.42},[-105,-126,106,16],
 {seconds:2.43,rate:1.08,fade:.48,layers:['back','front']});

// Add separate stepped leader channels in the same return pulse. Side
// channels share the original anchor and do not run the ground-hit emitter.
const aux=`
  const secondary = (o.secondary ?? []).map(([x, end, drop, k, delay],i)=>({
    b:zigzag(rng(o.seed,418,i), x, TOP+drop, end, -1, 0.125, 0.41),end,k,delay
  }));
  function sideChannels(p,t) {
    for(const s of secondary){
      const tr=s.b.paths[0].pts, a=t-(S1+s.delay);
      if(t>=LEAD0+s.delay && a<0){
        const u=clamp((t-LEAD0-s.delay)/(S1-LEAD0));
        const end=Math.max(2,Math.floor(tr.length*u**1.13));
        trace(p,tr,C[3],.86,0,end-1);
        trace(p,tr,C[5],.66,Math.max(0,end-7),end-1);
      } else if(a>=0 && a<.23){
        const v=level(a)*s.k;
        if(v>.13){
          stroke(p,s.b,v,C,0.76,{core:v>.46?.57:0,minY:TOP+4});
          if(a<.062){
            const k=1-a/.062;
            p.glow(s.end,-3,18,C[5],.42*k);
            sparkle(p,s.end,-2,7*k,C[6],C[4],.43);
          }
        }
      } else if(a>=.23 && a<.59){
        const v=1-smooth(.25,.58,a);
        trace(p,tr,C[3],v*.65,Math.floor((1-v)*tr.length*.4),tr.length-1);
      }
    }
  }
`;
const storm=await variant('lightning','critical-multiple-lightning',[
 ['  const tree = cracks(R);','  const tree = cracks(R);\n'+aux],
 ['      // arcs crawl out along the cracks', '      sideChannels(p,t);\n      // arcs crawl out along the cracks'],
], 'lightning/_r4-thunder-cinema');
const pair=[[-131,-26,9,.72,.004],[54,24,20,.78,.016]];
for(const [name,extra] of [['thunder-cinema',pair],['thunder-cinema-advanced',[...pair,[-8,10,2,.69,.022]]]]){
 render(name,'lightning',storm,{palette:ice,sparks:['#ebfbff','#aee1ff','#77a3ea','#5670a4'],seed:10,light:.40,secondary:extra},
  [-151,-159,98,22],{seconds:1.76,rate:1.33,fade:.36,layers:['back','front']});
}

const drain=await variant('life','native-life-steal',[
 ['  actor: 2,','  actor: false,'],
 ['const TX = 104, TY = -24, HX = 1, HY = -20, N = 7;',
  '// Native anchors are supplied by the recorded battle fixtures.'],
 ['export function create(o) {',
  'export function create(o) {\n  const TX=o.targetDX??104, TY=o.targetY??-24, HX=o.heartX??1, HY=o.heartY??-20, N=7;'],
 ['let t = 0, hit = false','let t = -(o.windup??0), hit = false'],
 ['      t += dt;\n      if (!hit)', '      t += dt;\n      if (t < 0) return;\n      if (!hit)'],
 ['    drawBack(p) {\n      // the wound',
  '    drawBack(p) {\n      if (t<0) { const k=clamp(1+t/(o.windup||1)); p.glow(TX,TY,16,C[3],.30*k*k); return; }\n      // the wound'],
 ['    draw(p) {\n      // the caster',
  '    draw(p) {\n      if(t<0){const k=clamp(1+t/(o.windup||1)); for(let i=0;i<3;i++){const a=t*7+i*TAU/3, r=4+8*(1-k); p.dot(TX+Math.cos(a)*r, TY+Math.sin(a)*r*.61,C[4+i%2],.30+.58*k);} return;}\n      // the caster'],
 ['      // the hit on the target','      if (!A && fk>.03) p.glow(HX, HY, 27, C[5], 0.58*fk);\n      // the hit on the target'],
 ['for (let i = 0; i < 14; i++) drops.add','for (let i = 0; i < 7; i++) drops.add'],
]);
for(const [token,g] of new Map(Object.values(jobs.drains).map(g=>[g.token,g]))){
 render('life-steal-'+token,'life',drain,{
  actor:false,targetDX:g.targetDX,targetY:g.targetY,heartX:g.heartX,heartY:g.heartY,windup:1.16,
  palette:['#200a16','#42101d','#771b2c','#ae2937','#db4551','#f36568','#ff9e94','#ffe4d9'],seed:11,light:.47},
  [-30,-100,g.targetDX+54,12],{seconds:3.29,fps:60,fade:.24});
}

const reap=await variant('reap','weighted-reap',[
 ['HANG = 0.14, TEAR = 0.55','HANG = 0.10, TEAR = 0.36'],
 ['const W = 13','const W = 16'],
 ['u += 0.022','u += 0.043'],
 ['const wisps = [];','const wisps = [];\n'+smokeGate.replace('kind === P.SMOKE || kind === P.DUST','kind === P.VAPOUR')],
], 'melee/_r4-bastion-reap');
render('bastion-reap','reap',reap,{palette:['#211f28','#332c32','#51434a','#6b584f','#936f59','#b08a67','#c8a884','#e8cdb0'],
 light:.28},[-84,-72,91,14],{seconds:1.34,rate:.88,fade:.25,layers:['back','front']});

const damage=sources.damage.fx;
for(const n of jobs.damage) {
 render('damage-'+n,'damage',damage,{text:'-'+n,light:.42},[-47,-62,64,24],{seconds:1.05});
}

const references=[];
for(const [key,t] of [['damage',.35],['life',.86]]){
 const fx=sources[key].fx,fps=24;
 const r=key==='life'?renderAct(fx,{fps,hold:.48}):renderFrames(fx,{fps});
 const poster=r.frames.reduce((a,b)=>Math.abs(a.t-t)<Math.abs(b.t-t)?a:b);
 writeFileSync(join(dir,'ref-'+key+'-still.png'),encodePNG(r.w,r.h,poster.color));
 const args=['-v','error','-y','-f','rawvideo','-pixel_format','rgba','-video_size',r.w+'x'+r.h,'-framerate',String(fps),'-i','-','-vf',
  'pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-crf','15','-pix_fmt','yuv420p','-movflags','+faststart',join(dir,'ref-'+key+'.mp4')];
 const enc=spawnSync('ffmpeg',args,{input:Buffer.concat(r.frames.map(f=>Buffer.from(f.color))),maxBuffer:3e6});
 if(enc.status!==0)throw Error('Reference encode: '+enc.stderr);
 references.push({module:stock[key],name:fx.meta.name,ref:'assets/r5/ref-'+key+'.mp4',still:'assets/r5/ref-'+key+'-still.png',size:[r.w,r.h],sha256:sources[key].sha256});
}
writeFileSync(join(dir,'effects.json'),JSON.stringify({effects,provenance,references},null,2)+'\n');

