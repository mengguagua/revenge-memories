const fs=require('fs'),path=require('path'),vm=require('vm');
const {createCanvas,loadImage,GlobalFonts}=require('/Users/gcc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas');
const root=path.resolve(__dirname,'..');GlobalFonts.registerFromPath('/System/Library/Fonts/STHeiti Medium.ttc','Cinema CJK');
const b={window:{},console};vm.createContext(b);for(const f of ['assets.js','targets.js','render.js'])vm.runInContext(fs.readFileSync(path.join(root,f),'utf8'),b);
const R=b.window.CriticalCinema,A=b.window.CinemaAssets,c=createCanvas(1280,800),ctx=c.getContext('2d'),raw=ctx.drawImage.bind(ctx);let calls=[];
ctx.drawImage=(im,...args)=>{const m=ctx.getTransform();calls.push({im,args,m:{a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f}});return raw(im,...args)};
function marker(draw,d,p){const [x,y,w,h]=draw.args,m=draw.m,lx=x+p[0]*w/d.width,ly=y+p[1]*h/d.height;return [m.a*lx+m.c*ly+m.e,m.b*lx+m.d*ly+m.f]}
const spread=a=>Math.max(...a)-Math.min(...a);
async function run(){for(const p of R.assetPaths)R.images.set(p,await loadImage(path.join(root,p)));const results=[],target={...R.targets[0],damage:1};
 for(const [i,j] of R.cases.entries()){if(j.weapon!=='剑')continue;
  const moving=j.weapon==='剑',samples=[],poses=new Set();
  const start=moving?5.54:1.90,end=moving?6.59:5.30;
  for(let t=start;t<end;t+=1/60){const st=R.timing(j,t,target),key=st.key||R.actorKey(j),d=A[key].frames[st.n];calls=[];const report=R.render(ctx,i,t,{target});if(report.errors.length)throw Error('Text outside safe area '+j.key);
   const draw=calls.filter(x=>x.im===R.images.get(d.path)&&Math.abs(x.m.a-1.8)<.001).pop();if(!draw)throw Error('Missing actual rendered actor '+j.key);
   const point=marker(draw,d,[d.body_anchor??d.width/2,d.head_top??2]);samples.push({t,head:point,scale:[draw.args[2]/d.width,draw.args[3]/d.height]});poses.add(key+':'+st.n);
  }
  const xs=samples.map(s=>s.head[0]),ys=samples.map(s=>s.head[1]);const variation=moving?spread(ys):spread(xs),limit=2.1;
  if(variation>limit)throw Error('Visible actor drift '+j.key+' '+variation);
  results.push({key:j.key,check:moving?'Return head height stays fixed; horizontal travel follows timeline':'Stationary head/body X stays fixed including impact; no actor camera shake',measured_world_pixels:variation,limit_world_pixels:limit,painted_poses:[...poses],samples:samples.length,passed:true});
 }
 const sheets=[['returns',R.cases.map((j,i)=>({j,i})).filter(({j})=>j.weapon==='剑'),[5.55,5.65,5.75,5.85]],['archery',R.cases.map((j,i)=>({j,i})).filter(({j})=>j.weapon==='弓'),[2.0,2.7,3.6,4.1]]];
 for(const [name,js,times] of sheets){const out=createCanvas(1280,js.length*240),cx=out.getContext('2d');for(let row=0;row<js.length;row++)for(let n=0;n<times.length;n++){R.render(ctx,js[row].i,times[n],{target});cx.drawImage(c,n*320,row*240,320,200);cx.font='12px Cinema CJK';cx.fillStyle='#d7e1df';cx.fillText(js[row].j.title+' / '+times[n],n*320+12,row*240+224)}fs.writeFileSync(path.join(root,'checks/v5',name+'-registered.png'),out.toBuffer('image/png'))}
 for(const [time,name] of [[4.42,'sword-contact'],[4.78,'sword-followthrough'],[5.42,'sword-recover']]){R.render(ctx,3,time,{target});fs.writeFileSync(path.join(root,'checks/v5',name+'.png'),c.toBuffer('image/png'))}
 fs.writeFileSync(path.join(root,'checks/v5/registration.json'),JSON.stringify({method:'Instrument actual canvas draw calls and full transform; measure marked head point after draw scaling and stage camera, at60Hz. 2.1 output pixels = 1.17 logical pixels maximum rounding tolerance. No per-frame body scaling.',results},null,2));console.log(JSON.stringify(results.map(({key,measured_world_pixels,passed})=>({key,measured_world_pixels,passed}))));
}
run().catch(e=>{console.error(e);process.exitCode=1});
