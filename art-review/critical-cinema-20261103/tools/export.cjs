const fs=require('fs'),path=require('path'),vm=require('vm'),{spawn,execFileSync}=require('child_process');
const {createCanvas,loadImage,GlobalFonts}=require('/Users/gcc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas');
const root=path.resolve(__dirname,'..');process.chdir(root);
GlobalFonts.registerFromPath('/System/Library/Fonts/STHeiti Medium.ttc','Cinema CJK');
const sandbox={window:{},console};vm.createContext(sandbox);
for(const file of ['assets.js','targets.js','render.js'])vm.runInContext(fs.readFileSync(file,'utf8'),sandbox,{filename:file});
const R=sandbox.window.CriticalCinema,canvas=createCanvas(1280,800),ctx=canvas.getContext('2d');
function wav(j){
 const file='audio/v5/mixes/'+j.key+'.wav';if(!fs.existsSync(file))throw Error('Missing newly generated mix '+j.key);
 const report=JSON.parse(fs.readFileSync('source/revision5/audio-mixes.json','utf8'));return report.mixes.find(m=>m.key===j.key);
}
async function encode(j,index,target){
 const fps=24,frames=Math.floor(j.duration*fps),dest='videos/'+j.key+'.mp4';
 const ff=spawn('/opt/homebrew/bin/ffmpeg',['-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s','1280x800','-r',String(fps),'-i','pipe:0','-i','audio/v5/mixes/'+j.key+'.wav','-c:v','libx264','-preset','fast','-threads','4','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-shortest',dest]);
 let error='';ff.stderr.on('data',b=>error+=b);const done=new Promise((ok,no)=>{ff.on('error',no);ff.on('close',code=>code===0?ok():no(Error(error)))});
 for(let frame=0;frame<frames;frame++){
  const result=R.render(ctx,index,frame/fps,{target});if(result.errors.length)throw Error(JSON.stringify(result.errors));
  const data=Buffer.from(ctx.getImageData(0,0,1280,800).data.buffer);
  if(!ff.stdin.write(data))await new Promise(ok=>ff.stdin.once('drain',ok));
 }
 ff.stdin.end();await done;console.log('ENCODED',j.key,frames,'frames');return {key:j.key,frames,fps,seconds:frames/fps,file:dest,target:target.name};
}
async function run(){
 for(const p of R.assetPaths)R.images.set(p,await loadImage(p));
 const design={date:'2026-11-03',reference:'https://34.suparobo.jp/system/',reference_use:'Cinematic pacing: character cut-in, anticipation, action, impact hold, recovery. No franchise artwork copied.',scope:'Standalone HTML and video. No game integration.',portrait_status:'All four bust portraits approved by user on 2026-11-03.',enemy_contract:{source:'Dynamic input: a single static current-target image, name, HP, max HP and resolved damage.',first_appearance:'From popup opening, continuously through preparation, attack and recovery; living target is never removed.',poses:1,enemy_motion:'none; no skeletal animation, pose switching, recoil or species-specific design',cover:'Contact effects overlay the continuously present static target. One HP-loss count is shown. Only the resolved-dead branch removes the target after its impact feedback.',number_rule:'Preview values only; future integration must receive the existing resolved result, never calculate or apply additional damage.'},variants:R.cases.map(j=>({...j,character_id:j.hero==='hunapu'?1:2,action_to_effect:{weapon:j.weapon,form:j.className,attack_contract:'One current weapon critical result. Visual motion is not an extra attack or a new unlocked ability.',damage_display_at:j.hit+.15,impact_at:j.hit},storyboard:[{time:[0,.63],shot:'Central popup'},{time:[.63,1.86],shot:'Approved new portrait cut-in'},{time:[1.86,2.8],shot:j.beats[0]},{time:[2.8,j.hit-.15],shot:j.beats[1]},{time:[0,j.duration],shot:'Current static target persists; contact effects overlay it and the single existing damage result is displayed'},{time:[5.95,j.duration],shot:j.beats[3]+' and return'}]}))};
 fs.writeFileSync('source/design.json',JSON.stringify(design,null,2));
 let textErrors=[],poseSets=[],audio=[];
 const contactSheet=createCanvas(1280,800),cs=contactSheet.getContext('2d');
 for(let i=0;i<R.cases.length;i++){
  const j=R.cases[i],target=R.targets[i%3],poses=new Set();audio.push(wav(j));
  for(let f=0;f<Math.round(j.duration*6);f++){const r=R.render(ctx,i,f/6,{target});poses.add(r.pose);textErrors.push(...r.errors)}
  poseSets.push({key:j.key,painted_poses_rendered:[...poses],seconds:j.duration,static_target:target.name});
  R.render(ctx,i,1.13,{target});fs.writeFileSync('checks/'+j.key+'-portrait.png',canvas.toBuffer('image/png'));
  R.render(ctx,i,j.hit-.24,{target});fs.writeFileSync('checks/'+j.key+'-poster.png',canvas.toBuffer('image/png'));cs.drawImage(canvas,(i%3)*426,Math.floor(i/3)*400,426,266);
  R.render(ctx,i,j.hit+.21,{target});fs.writeFileSync('checks/'+j.key+'-impact.png',canvas.toBuffer('image/png'));
 }
 fs.writeFileSync('checks/six-contact-shots.png',contactSheet.toBuffer('image/png'));
 if(textErrors.length)throw Error(JSON.stringify(textErrors.slice(0,15)));
 const contrast=createCanvas(1200,520),cc=contrast.getContext('2d');cc.fillStyle='#ebeee4';cc.fillRect(0,0,600,520);cc.fillStyle='#111d2b';cc.fillRect(600,0,600,520);
 for(let i=0;i<6;i++){const j=R.cases[i],f=sandbox.window.CinemaAssets[R.actorKey(j)].frames[4],im=R.images.get(f.path);for(const x of [0,600])cc.drawImage(im,x+(i%3)*200+15,Math.floor(i/3)*260+30,im.width,im.height)}
 fs.writeFileSync('checks/transparent-edges.png',contrast.toBuffer('image/png'));
 fs.writeFileSync('checks/render.json',JSON.stringify({frames_checked:poseSets.reduce((s,a)=>s+Math.round(a.seconds*6),0),text_safe_area_errors:textErrors,poses:poseSets,alpha_backgrounds:['light','dark'],fixed_enemy_sheet_loaded:R.assetPaths.some(p=>p.includes('opponent')),dynamic_targets:R.targets.map(t=>({name:t.name,poses:1})),audio},null,2));
 console.log('STILLS AND RENDER CHECKS PASS');
 if(process.argv.includes('--stills'))return;
 const videos=[],only=process.argv.find(s=>s.startsWith('--case='))?.slice(7);for(let i=0;i<R.cases.length;i++){const j=R.cases[i];if(!only||j.key===only||(only==='physical'&&i<6)||(only==='wind'&&j.spell==='wind'))videos.push(await encode(j,i,R.targets[i%3]));else {const fps=24;videos.push({key:j.key,frames:Math.floor(j.duration*fps),fps,seconds:Math.floor(j.duration*fps)/fps,file:'videos/'+j.key+'.mp4',target:R.targets[i%3].name})}}
 fs.writeFileSync('videos/concat.txt',videos.map(v=>"file '"+path.basename(v.file)+"'").join('\n'));
 execFileSync('/opt/homebrew/bin/ffmpeg',['-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i','videos/concat.txt','-c','copy','-movflags','+faststart','videos/all-v6.mp4']);
 for(const v of videos){const probe=JSON.parse(execFileSync('/opt/homebrew/bin/ffprobe',['-v','error','-show_streams','-show_format','-of','json',v.file],{encoding:'utf8'}));const s=probe.streams.find(s=>s.codec_type==='video');if(Number(s.nb_frames)!==v.frames)throw Error('Frame count mismatch '+v.key);v.bytes=fs.statSync(v.file).size;v.decoded_frames=Number(s.nb_frames);v.measured_seconds=Number(s.duration)}
 fs.writeFileSync('checks/videos.json',JSON.stringify({videos,total_seconds:videos.reduce((s,v)=>s+v.seconds,0),audio:true,all:'videos/all-v6.mp4'},null,2));console.log('ALL ACTIVE VIDEOS VERIFIED');
}
run().catch(e=>{console.error(e);process.exitCode=1});
