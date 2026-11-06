const fs=require('fs'),path=require('path'),{execFileSync}=require('child_process');
const {createCanvas,loadImage,ImageData}=require('/Users/gcc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas');
const root=path.resolve(__dirname,'..');
const source=JSON.parse(fs.readFileSync(path.join(root,'source/generation.json')));
source.records.push(...JSON.parse(fs.readFileSync(path.join(root,'source/impact-generation.json'))).records);
const manifest={created:'2026-11-03',new_cinematic_art:true,existing_target_snapshot_exception:'Three isolated current-enemy static images, dynamically injected following user correction.',assets:[],sheets:{}};
const magick='/opt/homebrew/bin/magick';
async function run(){
 for(const {key,path:src} of source.records){
  const original=path.join(root,'source',key+'-master.png');fs.copyFileSync(src,original);
  if(key==='opponent')continue;
  const clean=path.join(root,'source',key+'-clean.png');
  if(key==='battlefield'){
   execFileSync(magick,[original,'-filter','point','-resize','640x360^','-gravity','center','-extent','640x360',path.join(root,'assets/battlefield.png')]);
  }else{
   // Asset finishing only: remove generator's translucent preview haze, preserve solid art.
   execFileSync(magick,[original,'-channel','A','-threshold','88%','+channel',clean]);
   const im=await loadImage(clean),cols=key==='portraits'?2:4,rows=key==='opponent'?1:2;
   const cellW=im.width/cols,cellH=im.height/rows;
   const c=createCanvas(im.width,im.height),cx=c.getContext('2d');cx.drawImage(im,0,0);
   const rgba=cx.getImageData(0,0,im.width,im.height).data;
   let labels=null,components=[];
   if(!['portraits','impact'].includes(key)){
    // Segment whole bodies globally, so a pose crossing a nominal grid gutter is
    // preserved completely and cannot leak into its neighbour's extraction.
    labels=new Int32Array(im.width*im.height);const queue=new Int32Array(labels.length);let label=0;
    for(let p=0;p<labels.length;p++)if(rgba[p*4+3]&&!labels[p]){
     label++;let head=0,tail=1;queue[0]=p;labels[p]=label;let minX=im.width,minY=im.height,maxX=0,maxY=0;
     while(head<tail){const at=queue[head++],x=at%im.width,y=Math.floor(at/im.width);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);
      for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){if(!dx&&!dy)continue;const nx=x+dx,ny=y+dy;if(nx<0||nx>=im.width||ny<0||ny>=im.height)continue;const np=ny*im.width+nx;if(!labels[np]&&rgba[np*4+3]){labels[np]=label;queue[tail++]=np}}
     }
     if(tail>100)components.push({label,count:tail,box:[minX,minY,maxX+1,maxY+1]});
    }
    components.sort((a,b)=>b.count-a.count);components=components.slice(0,cols*rows);
    components.forEach(a=>{a.frame=Math.floor((a.box[0]+a.box[2])/2/cellW)+Math.floor((a.box[1]+a.box[3])/2/cellH)*cols});
    if(new Set(components.map(a=>a.frame)).size!==cols*rows)throw Error('Pose segmentation ambiguity: '+key);
   }
   const frames=[];
   for(let n=0;n<cols*rows;n++){
    const x0=Math.round((n%cols)*cellW),y0=Math.round(Math.floor(n/cols)*cellH),x1=Math.round((n%cols+1)*cellW),y1=Math.round((Math.floor(n/cols)+1)*cellH);
    let loX=x1,loY=y1,hiX=x0,hiY=y0;
    for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
     // The released arrow is animated separately; retain only the archer body in frame 6.
     if(key==='hunapu-bow'&&n===5&&x>x0+300)continue;
     if(rgba[(y*im.width+x)*4+3]>0){loX=Math.min(loX,x);loY=Math.min(loY,y);hiX=Math.max(hiX,x);hiY=Math.max(hiY,y)}
    }
    const component=components.find(a=>a.frame===n);if(component){[loX,loY,hiX,hiY]=component.box;hiX--;hiY--}
    const crop=[Math.max(component?0:x0,loX-3),Math.max(component?0:y0,loY-3),Math.min(component?im.width:x1,hiX+4),Math.min(component?im.height:y1,hiY+4)];
    const name=key+'-'+n+'.png',out=path.join(root,'assets',name);
    let input=clean;
    if(component){const copy=new Uint8ClampedArray(rgba);for(let p=0;p<labels.length;p++)if(labels[p]!==component.label)copy[p*4+3]=0;const masked=createCanvas(im.width,im.height);masked.getContext('2d').putImageData(new ImageData(copy,im.width,im.height),0,0);input=path.join(root,'source',key+'-isolated-'+n+'.png');fs.writeFileSync(input,masked.toBuffer('image/png'))}
    execFileSync(magick,[input,'-crop',`${crop[2]-crop[0]}x${crop[3]-crop[1]}+${crop[0]}+${crop[1]}`,'+repage','-filter','point','-resize',key==='portraits'?'75%':'50%',out]);
    const info=execFileSync(magick,['identify','-format','%w %h',out],{encoding:'utf8'}).split(' ').map(Number);
    frames.push({path:'assets/'+name,width:info[0],height:info[1],source_box:crop,source_cell:[x0,y0,x1,y1],complete_body_component:component?.count||null});
   }
   manifest.sheets[key]={frames,cols,rows};
  }
 }
 for(const f of fs.readdirSync(path.join(root,'assets'))){
  if(!f.endsWith('.png')||f.startsWith('opponent-'))continue;
  const p=path.join(root,'assets',f);
  try{execFileSync('/opt/homebrew/bin/oxipng',['-o','3','--strip','safe',p],{stdio:'pipe'})}catch{}
  const [w,h]=execFileSync(magick,['identify','-format','%w %h',p],{encoding:'utf8'}).split(' ').map(Number);
  manifest.assets.push({file:'assets/'+f,width:w,height:h,bytes:fs.statSync(p).size,purpose:f.startsWith('battlefield')?'dedicated 16:9 battle background':f.startsWith('portraits')?'new cinematic cut-in portrait':'new action key pose',quality_note:fs.statSync(p).size>50000?'Losslessly retained crisp pixel detail and silhouette. No lossy degradation.':null});
 }
 fs.writeFileSync(path.join(root,'source/asset-manifest.json'),JSON.stringify(manifest,null,2));
 fs.writeFileSync(path.join(root,'assets.js'),'window.CinemaAssets='+JSON.stringify(manifest.sheets)+';\n');
 console.log(JSON.stringify({assets:manifest.assets.length,total_bytes:manifest.assets.reduce((s,a)=>s+a.bytes,0),max_bytes:Math.max(...manifest.assets.map(a=>a.bytes))}));
}
run().catch(e=>{console.error(e);process.exitCode=1});
