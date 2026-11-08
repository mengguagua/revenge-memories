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
const out=resolve(here,'../../pixel-reference-r4-20261107');
const dir=join(out,'assets/r4');
const roots=join(here,'pixelfx-work/src/fx');
mkdirSync(dir,{recursive:true});
const stock={
 fireball:'fire/fireball', blast:'explosions/small-explosion', pillar:'fire/flame-pillar', ring:'fire/fire-ring', spiral:'fire/fire-tornado',
 lightning:'lightning/lightning-strike', charge:'lightning/charge-up', double:'melee/double-slash', spin:'melee/spin-slash', reap:'melee/scythe-reap',
};
const sources={};
for (const [key,id] of Object.entries(stock)) {
 const fx=await loadEffect(id);
 sources[key]={fx,sha256:createHash('sha256').update(readFileSync(fx.file)).digest('hex')};
}
async function variant(key,name,changes) {
 const id=stock[key], src=readFileSync(sources[key].fx.file,'utf8');
 let code=src;
 for (const [from,to] of changes) {
  if (!code.includes(from)) throw Error(id+': upstream pattern missing: '+from);
  code=code.replaceAll(from,to);
 }
 const asset=id.split('/')[0]+'/_r4-'+name;
 writeFileSync(join(roots,asset+'.js'),'// Adapted for the R4 preview; original PixelFX source and license retained.\n'+code);
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
  const path='assets/r4/'+name+'-'+String(i).padStart(2,'0')+'.png';
  writeFileSync(join(out,path),png);
  return path;
 });
 effects[name]={paths,atlasFrames:cells,frameSize:[w,h],pivot:[-r.x0-minX,-r.y0-minY],columns:cols,fps:r.fps,frames:r.n,loop};
}

function render(name,key,fx,options,bb,settings={}) {
 const r=raster(fx,options,bb,settings);
 for (const layer of Object.keys(r.tracks)) {
  const id='r4-'+name+(layer==='combined'?'':'-'+layer);
  atlas(id,r,layer,settings.loop??false);
  provenance[id]={module:stock[key],sha256:sources[key].sha256,options,render:settings,layer};
 }
 console.log(name+': '+r.n+' frames');
}

const {fireball,ring}=Object.fromEntries(Object.entries(sources).map(([k,v])=>[k,v.fx]));
render('fireball','fireball',fireball,{palette:flame,radius:5.1,speed:91,light:.31,angle:.20},[-114,-48,28,29],{seconds:1.2,loop:true});
render('fireball-cinema','fireball',fireball,{palette:flame,radius:7.4,speed:137,light:.31,angle:.27},[-136,-59,32,32],{seconds:1.2,loop:true});
render('fireball-cinema-advanced','fireball',fireball,{palette:flame,radius:9.25,speed:147,light:.34,angle:.27},[-140,-65,34,34],{seconds:1.2,loop:true});
const explosion=await variant('blast','fireball-impact',[
 ['-180, -100','-116, -65'],
 ['Math.round(80 * POWER)','Math.round(54 * POWER)'],
 ['Math.round(40 * POWER)','Math.round(27 * POWER)'],
 ['rings.push({ r0: RAD * 0.45, r1: RAD * 2.7, life: 0.34, max: 0.34, thick: 3, c: F[5] }, { r0: RAD * 0.3, r1: RAD * 1.6, life: 0.22, max: 0.22, thick: 1.8, c: F[3] });',
  '// The ground shockwave is sufficient; keep the fire and smoke silhouette clear.'],
 ['80 * S * ease.outCubic(k)','52 * S * ease.outCubic(k)'],
 ['R.range(4, 7) + RAD / 6','R.range(2.4, 4.2) + RAD / 9'],
 ['R.range(5, 9) * Math.sqrt(S) + RAD / 7','R.range(3, 5.5) * Math.sqrt(S) + RAD / 9'],
 ['rgb(34, 29, 38)','rgb(39, 29, 35)'],
]);
render('fireball-hit','blast',explosion,{palette:flame,size:.55,stone:'#50404b',light:.32},[-90,-103,91,23],{rate:1.55,seconds:1.12,fade:.35});
render('fireball-cinema-hit','blast',explosion,{palette:flame,size:.82,stone:'#50404b',light:.34},[-122,-129,123,23],{rate:1.48,seconds:1.35,fade:.40});
render('fireball-cinema-advanced-hit','blast',explosion,{palette:flame,size:.97,stone:'#50404b',light:.35},[-129,-137,130,24],{rate:1.48,seconds:1.42,fade:.45});

// Ragnarok has its own silhouette: a low, split ember wake, a floor ring and one upward eruption.
render('ragnarok-fuse','fireball',fireball,{palette:coal,radius:2.9,speed:47,light:.20,seed:13},[-82,-23,20,16],{seconds:1.2,loop:true,fps:30});
render('ragnarok-ring','ring',ring,{palette:coal,reach:29,light:.25,seed:19},[-60,-40,61,14],{rate:.82,seconds:1.75,fade:.32,fps:30});
const spiral=await variant('spiral','ragnarok-spiral',[
 ['3.5 + 15 * Math.pow','2.5 + 7.5 * Math.pow'],
 ['12 + 2 * N(2, n)','7 + 1.5 * N(2, n)'],
 ['30, S + 500','20, S + 500'],['20, S + 300','10, S + 300'],
 ['40, 8, GLOW, 0.4','25, 6, GLOW, 0.3'],
]);
render('ragnarok-coil','spiral',spiral,{palette:coal,height:20,seed:11,light:.25},[-47,-55,48,15],{seconds:2,loop:true,fps:30});
const column=await variant('pillar','ragnarok-pillar',[
 ['FALL = 1.95, GONE = 2.45','FALL = 1.08, GONE = 1.66'],
 ['R.range(20, 40)','R.range(17, 34)'],
 ['GONE - 0.3, meta.duration - 0.6','GONE - 0.22, 2.8'],
 ['* 1.6 * v;','* 5.5 * v;'],
]);
render('ragnarok-pillar','pillar',column,{palette:flame,height:69,stone:'#513b48',seed:11,light:.42},[-105,-126,106,16],
 {seconds:2.43,rate:1.08,fade:.48,fps:60,layers:['back','front']});

async function storm(name,{height,width,reach,rx,lean,seed,palette,power}) {
 const fx=await variant('lightning',name,[
  ['W = 120, TOP = -224, RX = 28, SY = 0.22, REACH = 52, LEAD0 = 0.48, STEPS = 9, MEET = -30',
   `W = ${width}, TOP = -${height}, RX = ${rx}, SY = 0.19, REACH = ${reach}, LEAD0 = 0.46, STEPS = 8, MEET = -${Math.round(height*.18)}`],
  ['[{ t: 0.76, k: 1 }, { t: 1.04, k: 0.8 }, { t: 1.26, k: 0.55 }]','[{ t: 0.76, k: 1 }]'],
  ['R.range(8, 18) * (R.chance(0.5) ? 1 : -1)',`${lean} + R.range(-4, 4)`],
  ['0.17, 0.5)), trunk','0.15, 0.44)), trunk'],
  ['const dark = 0.5 *','const dark = 0.20 *'],
  ['for (let y = -228; y < 36; y++)','for (let y = TOP - 3; y < 18; y++)'],
  ['(y + 96) / 132','(y - TOP * .41) / (-TOP * .62)'],
  ['Math.round(44 * k)',`Math.round(${Math.round(power*33)} * k)`],
  ['R.range(110, 320)','R.range(72, 220)'],
  ['R.range(70, 220)','R.range(48, 162)'],
  ['Math.round(18 * k)','Math.round(10 * k)'],
  ['lights.add(0, -50, 120, C[4], 0.55','lights.add(0, -42, 57, C[4], 0.36'],
  ['p.glow(0, -16, 96, C[3], 0.42','p.glow(0, -16, 58, C[3], 0.30'],
  ['if (hero) p.glow(X0 * 0.5, -110, 170, C[3], 0.3)','if (hero) p.glow(X0 * 0.5, TOP * .55, 64, C[3], 0.18)'],
  ['s.i === 0 ? 1.5 : 1.2',power>1?'1.35':'1.05'],
  ['(hero ? 1.2 : 0.8)',power>1?'(hero ? 1.0 : 0.7)':'(hero ? 0.83 : 0.6)'],
 ]);
 render(name,'lightning',fx,{palette,sparks:['#ebfbff','#aee1ff','#77a3ea','#5670a4'],seed,light:power>1?.43:.33},
  [-width-14,-height-14,width+15,19],{seconds:1.76,rate:1.33,fade:.36,layers:['back','front']});
}
await storm('thunder',{height:109,width:69,reach:36,rx:18,lean:-7,seed:5,palette:ice,power:.86});
await storm('thunder-cinema',{height:143,width:96,reach:50,rx:25,lean:-54,seed:10,palette:ice,power:1.16});
await storm('levin',{height:86,width:68,reach:32,rx:15,lean:-36,seed:12,palette:levin,power:.75});
const charge=await variant('charge','charge-spark',[
 ['const CX = 15, CY = -21','const CX = 0, CY = 0'],
 ['edgeOf(A))','(A ? edgeOf(A) : []))'],
 ['a < 0.07) p.mask','a < 0.07 && A) p.mask'],
 ['(60 + 360 * e)','(33 + 145 * e)'],
 ['R.range(30, 72)','R.range(17, 38)'],
 ['R.range(20, 40)','R.range(12, 24)'],
 ['6.5 * e','3.25 * e'],
 ['4 + 20 * (1 - ease.inQuad(q))','3 + 11 * (1 - ease.inQuad(q))'],
 ['if (t < REL) p.glow(CX * 0.5, -3, 40','if (t < REL) p.glow(CX * 0.5, -3, 28'],
]);
const smallCharge={charge:1.16,actor:false,light:.32};
render('thunder-charge','charge',charge,{...smallCharge,palette:ice},[-43,-44,44,29],{seconds:1.16,fps:30});
render('levin-charge','charge',charge,{...smallCharge,palette:levin,seed:12},[-43,-44,44,29],{seconds:1.16,fps:30});

const double=await variant('double','hero-double',[
 ['const R0 = 62','const R0 = 57'],
 ['const X = 34, Y = -23','const X = 0, Y = 0'],
 // The cut is anchored to the target's torso; preserve shards below the crossing until they reach the floor.
 ['ground: () => 0','ground: () => 40'],
 ['W: 10,','W: 10,'],['W: 11,','W: 12,'],
 ['Rg.range(140, 360)','Rg.range(96, 258)'],
]);
render('hero-double','double',double,{palette:['#2b172c','#642947','#9a3b5e','#d0527f','#ec7b9c','#ffbed0','#fff2e7'],sparks,light:.40},[-95,-60,96,62],
 {seconds:.86,rate:.80,fade:.18});
const spin=await variant('spin','hero-spin',[
 ['cy: -17','cy: -29'],['const W = 16, WE = 5','const W = 17, WE = 6'],
 ['th = f < 0.13 ? 9 : Math.max(1, 6','th = f < 0.17 ? 13 : Math.max(1, 7.5'],
 ['q < 0.6 ? WHITE : ramp[5]','q < 0.54 ? C[6] : ramp[5]'],
]);
render('hero-spin','spin',spin,{radius:55,palette:['#36191f','#65232a','#a1322d','#d83c2e','#fa5735','#ff8d53','#ffdc9e'],sparks,light:.45},[-107,-82,108,18],
 {seconds:.90,rate:.70,fade:.18,layers:['back','front']});
const reap=await variant('reap','bastion-reap',[
 ['cx: 8, cy: -33, R: 52, sy: 0.6, k: 0.1, rot: 0.08, a0: -0.5','cx: 9, cy: -25, R: 38, sy: 0.53, k: 0.1, rot: 0.10, a0: -0.61'],
 ['const W = 21','const W = 13'],
]);
render('bastion-reap','reap',reap,{palette:['#1c1a2b','#2d283f','#44415a','#466275','#507d82','#6daca9','#a4dcd3','#e4f1e3'],light:.42},[-84,-72,91,14],
 {seconds:1.58,rate:.88,fade:.27,layers:['back','front']});

const referenceRows=[];
for (const key of ['fireball','pillar','lightning','double','spin','reap']) {
 const {fx}=sources[key], action=key==='double'||key==='spin'||key==='reap', fps=24;
 const r=action?renderAct(fx,{fps,hold:.48}):renderFrames(fx,{fps});
 const posterAt={fireball:.56,pillar:.92,lightning:.8,double:.182,spin:.194,reap:.405}[key];
 const poster=r.frames.reduce((a,b)=>Math.abs(a.t-posterAt)<Math.abs(b.t-posterAt)?a:b);
 const png=encodePNG(r.w,r.h,poster.color);
 writeFileSync(join(dir,'ref-'+key+'-still.png'),png);
 const args=['-v','error','-y','-f','rawvideo','-pixel_format','rgba','-video_size',r.w+'x'+r.h,'-framerate',String(fps),'-i','-','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-crf','15','-pix_fmt','yuv420p','-movflags','+faststart',join(dir,'ref-'+key+'.mp4')];
 const enc=spawnSync('ffmpeg',args,{input:Buffer.concat(r.frames.map(f=>Buffer.from(f.color))),maxBuffer:3e6});
 if(enc.status!==0) throw Error('Reference encode: '+enc.stderr);
 referenceRows.push({module:stock[key],name:fx.meta.name,ref:'assets/r4/ref-'+key+'.mp4',still:'assets/r4/ref-'+key+'-still.png',size:[r.w,r.h],sha256:sources[key].sha256});
}
writeFileSync(join(dir,'effects.json'),JSON.stringify({effects,provenance,references:referenceRows},null,2)+'\n');
