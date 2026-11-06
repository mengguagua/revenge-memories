const fs=require('fs'),vm=require('vm'),path=require('path'),crypto=require('crypto');
const {createCanvas,loadImage,GlobalFonts}=require('/Users/gcc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas');
const dir=path.resolve(__dirname,'..'),box={window:{},console};vm.createContext(box);
GlobalFonts.registerFromPath('/System/Library/Fonts/STHeiti Medium.ttc','MAP Review CJK');
for(const f of ['data.js','render.js'])vm.runInContext(fs.readFileSync(path.join(dir,f),'utf8'),box);
const R=box.window.MapReview,canvas=createCanvas(1280,784),ctx=canvas.getContext('2d');
async function run(){
 const files=new Set(['assets/arrow.png']);for(const j of R.data.jobs)for(const p of ['assets/'+(j.bow?'hunapu-advanced':j.key)+'-terrain.png',j.hero_sprite.path,j.map_action.path,j.enemy_sprite.path,j.friend_sprite.path,j.body.path,j.fx])files.add(p);
 for(const p of files)R.images.set(p,await loadImage(path.join(dir,p)));
 const rawDraw=ctx.drawImage.bind(ctx);let calls=[];
 ctx.drawImage=(image,...args)=>{calls.push({image,args});return rawDraw(image,...args)};
 const results=[];
 for(let index=0;index<R.data.jobs.length;index++){
  const j=R.data.jobs[index],a=j.map_action,poses=new Set(),dest=new Set();
  const footCanvas=createCanvas(128,44),fc=footCanvas.getContext('2d'),feet=new Set(),upper=new Set();
  for(let i=0;i<a.frames;i++){
   fc.clearRect(0,0,128,44);fc.drawImage(R.images.get(a.path),i*128,84,128,44,0,0,128,44);
   feet.add(crypto.createHash('sha256').update(fc.getImageData(0,0,128,44).data).digest('hex'));
   const c=createCanvas(128,84),cc=c.getContext('2d');cc.drawImage(R.images.get(a.path),i*128,0,128,84,0,0,128,84);
   upper.add(crypto.createHash('sha256').update(cc.getImageData(0,0,128,84).data).digest('hex'));
  }
  for(let t=0;t<=j.duration;t+=1/30){
   calls=[];const errors=R.render(ctx,index,t,0,{coverage:true,zoom:false});if(errors.length)throw Error(JSON.stringify(errors));
   const actor=calls.filter(c=>c.image===R.images.get(a.path));
   if(actor.length!==1)throw Error('Map actor missing/duplicated '+j.key);
   dest.add(JSON.stringify(actor[0].args.slice(4)));poses.add(actor[0].args[0]);
  }
  if(feet.size!==1||upper.size<3||dest.size!==1||poses.size<3)throw Error('Fixed-foot/action acceptance failed '+j.key);
  if(j.hero==='eileen'&&a.rig.sweep_degrees!==102)throw Error('Eileen sweep amplitude');
  if(j.bow&&R.actionFrame(j,1.6)===R.actionFrame(j,2.0))throw Error('Bow draw and release are identical');
  for(const t of [1.20,1.82,2.0,2.58]){
   R.render(ctx,index,t,0,{coverage:true,zoom:true});
   fs.writeFileSync(path.join(dir,'sources',`v5-${j.key}-${t.toFixed(2)}.png`),canvas.toBuffer('image/png'));
  }
  results.push({key:j.key,fixed_foot_hashes:feet.size,upper_body_pose_count:upper.size,rendered_pose_count:poses.size,fixed_destination_rectangles:dest.size,kind:a.kind,sweep_degrees:a.rig?.sweep_degrees||null,passed:true});
 }
 const report={revision:5,scope:'Only MAP art-preview actions: exact lower-leg pixel lock, stationary map draw rectangle, visible upper-body pose changes, distinct bow draw/release, representative rendered screenshots and text-safe-area checks.',results};
 fs.writeFileSync(path.join(dir,'sources/actions-v5-qa.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}
run().catch(e=>{console.error(e);process.exitCode=1});
