// Deterministic PNG / silent MP4 export using the exact same review renderer.
const fs=require('fs'),path=require('path'),vm=require('vm'),{spawn}=require('child_process');
const {createCanvas,loadImage,Image,GlobalFonts}=require('/Users/gcc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas');
const out=path.resolve(__dirname,'..');process.chdir(out);
GlobalFonts.registerFromPath('/System/Library/Fonts/STHeiti Medium.ttc','MAP Review CJK');
const context={window:{},Image,console};vm.createContext(context);
vm.runInContext(fs.readFileSync('data.js','utf8'),context);vm.runInContext(fs.readFileSync('render.js','utf8'),context);
const R=context.window.MapReview,D=R.data;
const canvas=createCanvas(1280,784),ctx=canvas.getContext('2d');
async function run(){
 const needed=new Set(['assets/arrow.png']);
 for(const j of D.jobs){const key=j.bow?'hunapu-advanced':j.key;for(const p of ['assets/'+key+'-terrain.png','reference/'+key+'-runtime.png',j.hero_sprite.path,j.map_action.path,j.enemy_sprite.path,j.friend_sprite.path,j.body.path,j.fx])needed.add(p)}
 for(const p of needed)if(fs.existsSync(p))R.images.set(p,await loadImage(p));
 const checks=[];
 for(let i=0;i<4;i++){
  const j=D.jobs[i];if(!fs.existsSync(j.fx))continue;
  const a=R.render(ctx,i,2.58,0,{coverage:true,zoom:true});checks.push({case:j.key,text_errors:a});
  fs.writeFileSync('posters/'+j.key+'.png',canvas.toBuffer('image/png'));
 }
 if(process.argv.includes('--partial')){console.log(JSON.stringify(checks));return}
 let textErrors=[];
 const expected=[[[8,8,8],[10,10,10],[12,12,12]],[[12,12,12,12,12],[15,15,15,15,15],[18,18,18,18,18]],[[8,8,8],[10,10,10],[12,12,12]],[[17,13,13,13,13],[20,16,16,16,16],[23,19,19,19,19]]];
 for(let i=0;i<5;i++)for(let tier=0;tier<3;tier++){
  const j=D.jobs[i],s=R.stats(j,tier),want=expected[i===4?1:i][tier];
  if(JSON.stringify(s.damage.map(x=>x.actual))!==JSON.stringify(want))throw Error('Locked damage mismatch '+j.key+' '+tier);
  if(R.cells(j).length!==(j.hero==='hunapu'?(j.advanced?12:6):(j.advanced?13:5)))throw Error('Coverage mismatch');
  for(let t=0;t<=j.duration;t+=1/30)textErrors.push(...R.render(ctx,i,t,tier,{coverage:true,zoom:false}));
 }
 if(textErrors.length)throw Error(JSON.stringify(textErrors.slice(0,12)));
 fs.writeFileSync('sources/render-qa.json',JSON.stringify({cases:5,tiers:3,all_frames_sampled_fps:30,canvas_text_safe_area_errors:textErrors,damage_and_coverage:'locked values pass',reference_layout_errors:D.jobs.map(j=>({key:j.key,errors:j.layout_errors}))},null,2));
 const design={confirmed:{before:[0,2,4],after:[0,3,6],cost_max_hp:[0,.25,.4],eileen_advanced_center_bonus:4},cases:D.jobs.map(j=>({key:j.key,map:j.stage_code,name:j.name,profession:j.profession,palette:j.palette||null,source_variant:j.body.source_variant,map_actor:{source:j.map_action.path,position:j.hero_point,movement:'fixed tactical-map feet and position; upper-body attack action',kind:j.map_action.kind,timeline:j.map_action.timeline,foot_lock_y:j.map_action.foot_lock_y,rig:j.map_action.rig||null,person_height_native_pixels:j.map_action.person_height_native_pixels||null,leg_layer_native_y:j.map_action.leg_layer_native_y||null},portrait:j.portrait_from_map?'same tactical-map bow sprite':'standing reference only',coverage:R.cells(j).length,seconds:j.duration,hit_rule:j.hero==='hunapu'?'2.12s + 0.09s per tile depth, once per target':'2.42s simultaneous, once per target; advanced center +4',stats:[0,1,2].map(tier=>R.stats(j,tier))})),timeline:[['0–0.85s','范围预览'],['0.85–1.95s','蓄势与动作准备'],['1.95–2.42s','释放与推进'],['2.42–2.85s','单次命中结算'],['2.85–3.70s','特效消退'],['3.70–4.20s','余波消退，原格站定'],['4.20s–结束','结果停留']],scope:D.scope};
 fs.writeFileSync('sources/design.json',JSON.stringify(design,null,2));
 if(process.argv.includes('--stills')){console.log('ALL STILLS AND RENDER QA PASS');return}
 const fps=24,ff=spawn('/opt/homebrew/bin/ffmpeg',['-y','-hide_banner','-loglevel','error','-f','image2pipe','-vcodec','png','-framerate',String(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','map-preview.mp4']);
 let error='';ff.stderr.on('data',d=>error+=d);
 const finished=new Promise((ok,no)=>{ff.on('error',no);ff.on('close',c=>c===0?ok():no(Error(error)))});
 const segments=[];let frames=0;
 for(let i=0;i<5;i++){
  const j=D.jobs[i];segments.push({key:j.key,start:frames/fps,duration:j.duration,tier:1});
  for(let f=0;f<Math.ceil(j.duration*fps);f++){
   const t=f/fps;R.render(ctx,i,t,0,{coverage:true,zoom:t>1.15});
   const buf=canvas.toBuffer('image/png');if(!ff.stdin.write(buf))await new Promise(ok=>ff.stdin.once('drain',ok));frames++;
  }
  console.log('VIDEO_SEGMENT',j.key);
 }
 ff.stdin.end();await finished;
 fs.writeFileSync('sources/video.json',JSON.stringify({fps,frames,seconds:frames/fps,segments,silent:true,scope:D.scope},null,2));console.log('VIDEO_DONE',frames/fps);
}
run().catch(e=>{console.error(e);process.exitCode=1});
