const fs=require('fs'),path=require('path'),{execFileSync}=require('child_process');
const {createCanvas,loadImage,ImageData}=require('/Users/gcc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas');
const root=path.resolve(__dirname,'..');
async function run(){
 const records=[...JSON.parse(fs.readFileSync(path.join(root,'source/revision2/generation.json'))),...JSON.parse(fs.readFileSync(path.join(root,'source/revision2/extra-generation.json')))],manifest=JSON.parse(fs.readFileSync(path.join(root,'source/v1/asset-manifest.json')));
 for(const spec of records){
  if(!spec.path)continue;const original=path.join(root,'source/revision2',spec.key+'-master.png');fs.copyFileSync(spec.path,original);
  if(spec.kind==='background'){execFileSync('/opt/homebrew/bin/magick',[original,'-filter','point','-resize','640x360^','-gravity','center','-extent','640x360',path.join(root,'assets/v2/'+spec.key+'.png')]);continue}
  const clean=path.join(root,'source/revision2',spec.key+'-clean.png');execFileSync('/opt/homebrew/bin/magick',[original,'-channel','A','-threshold',spec.kind==='fx'?'60%':'88%','+channel',clean]);
  const im=await loadImage(clean),c=createCanvas(im.width,im.height),cx=c.getContext('2d');cx.drawImage(im,0,0);const data=cx.getImageData(0,0,im.width,im.height).data;
  const cols=spec.cols,rows=spec.rows,cw=im.width/cols,ch=im.height/rows,frames=[];let labels=null,components=[];
  if(spec.kind==='actor'){
   labels=new Int32Array(im.width*im.height);const queue=new Int32Array(labels.length);let id=0;
   for(let p=0;p<labels.length;p++)if(data[p*4+3]&&!labels[p]){id++;let head=0,tail=1;queue[0]=p;labels[p]=id;let l=im.width,t=im.height,r=0,b=0;
    while(head<tail){const a=queue[head++],x=a%im.width,y=Math.floor(a/im.width);l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y);for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){if(!dx&&!dy)continue;const xx=x+dx,yy=y+dy;if(xx<0||yy<0||xx>=im.width||yy>=im.height)continue;const z=yy*im.width+xx;if(!labels[z]&&data[z*4+3]){labels[z]=id;queue[tail++]=z}}}
    if(tail>300)components.push({id,count:tail,box:[l,t,r+1,b+1]});
   }
   components.sort((a,b)=>b.count-a.count);components=components.slice(0,cols*rows);components.forEach(a=>a.n=Math.floor((a.box[0]+a.box[2])/2/cw)+Math.floor((a.box[1]+a.box[3])/2/ch)*cols);
   if(new Set(components.map(a=>a.n)).size!==cols*rows)throw Error('Incomplete whole-body extraction '+spec.key);
  }
  for(let n=0;n<cols*rows;n++){
   const cell=[Math.round(n%cols*cw),Math.round(Math.floor(n/cols)*ch),Math.round((n%cols+1)*cw),Math.round((Math.floor(n/cols)+1)*ch)];let box=cell,component=components.find(a=>a.n===n),pixels=null;
   if(component){box=component.box;pixels=new Uint8ClampedArray(data);for(let p=0;p<labels.length;p++)if(labels[p]!==component.id)pixels[p*4+3]=0;}
   else {let l=cell[2],t=cell[3],r=cell[0],b=cell[1];for(let y=cell[1];y<cell[3];y++)for(let x=cell[0];x<cell[2];x++)if(data[(y*im.width+x)*4+3]){l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y)}box=r>=l?[l,t,r+1,b+1]:[cell[0]+1,cell[1]+1,cell[0]+8,cell[1]+8]}
   box=[Math.max(0,box[0]-3),Math.max(0,box[1]-3),Math.min(im.width,box[2]+3),Math.min(im.height,box[3]+3)];
   let input=clean;if(pixels){const mc=createCanvas(im.width,im.height);mc.getContext('2d').putImageData(new ImageData(pixels,im.width,im.height),0,0);input=path.join(root,'source/revision2',spec.key+'-isolated-'+n+'.png');fs.writeFileSync(input,mc.toBuffer('image/png'))}
   const name=spec.key+'-'+n+'.png',out=path.join(root,'assets/v2',name);execFileSync('/opt/homebrew/bin/magick',[input,'-crop',`${box[2]-box[0]}x${box[3]-box[1]}+${box[0]}+${box[1]}`,'+repage','-filter','point','-resize',spec.kind==='portrait'?'65%':'50%',out]);
   const [w,h]=execFileSync('/opt/homebrew/bin/magick',['identify','-format','%w %h',out],{encoding:'utf8'}).split(' ').map(Number);
   frames.push({path:'assets/v2/'+name,width:w,height:h,source_box:box,source_cell:cell,pixel_scale:spec.kind==='portrait'?.65:.5});
  }
  manifest.sheets[spec.key]={frames,cols,rows,kind:spec.kind};
 }
 for(const f of fs.readdirSync(path.join(root,'assets/v2'))){const p=path.join(root,'assets/v2',f);try{execFileSync('/opt/homebrew/bin/oxipng',['-o','2','--strip','safe',p],{stdio:'pipe'})}catch{}}
 for(const [key,sheet] of Object.entries(manifest.sheets)){
  if(!(/^(hunapu|eileen)/.test(key))||sheet.kind==='portrait')continue;
  for(const f of sheet.frames){
   const im=await loadImage(path.join(root,f.path)),c=createCanvas(im.width,im.height),cx=c.getContext('2d');cx.drawImage(im,0,0);const a=cx.getImageData(0,0,im.width,im.height).data,rows=new Array(im.height).fill(0),pts=[];
   for(let y=0;y<im.height*.7;y++)for(let x=0;x<im.width;x++){const z=(y*im.width+x)*4,r=a[z],g=a[z+1],b=a[z+2];if(a[z+3]>200&&(key.startsWith('hunapu')?(r<100&&g>r*1.15&&b>g*1.13):(r>g*1.35&&r>b*1.15))){rows[y]++;pts.push([x,y])}}
   const seen=new Uint8Array(im.width*im.height),skin=p=>{const z=p*4,r=a[z],g=a[z+1],b=a[z+2];return a[z+3]>200&&r>130&&r>g*1.13&&g>b*1.12&&b<185};let face=[];
   for(let p=0;p<seen.length;p++)if(!seen[p]&&skin(p)){const group=[p];seen[p]=1;for(let i=0;i<group.length;i++){const x=group[i]%im.width,y=Math.floor(group[i]/im.width);for(let yy=Math.max(0,y-1);yy<=Math.min(im.height-1,y+1);yy++)for(let xx=Math.max(0,x-1);xx<=Math.min(im.width-1,x+1);xx++){const q=yy*im.width+xx;if(!seen[q]&&skin(q)){seen[q]=1;group.push(q)}}}if(group.length>face.length)face=group}
   if(face.length){const xs=face.map(p=>p%im.width),ys=face.map(p=>Math.floor(p/im.width)),x=(Math.min(...xs)+Math.max(...xs))/2,y=Math.min(...ys),width=Math.max(...xs)-Math.min(...xs)+1,radius=Math.max(18,width*1.7);const hair=pts.filter(([xx,yy])=>Math.abs(xx-x)<radius&&yy>y-width*1.8&&yy<y+width*.8);f.head_top=hair.length?Math.min(...hair.map(p=>p[1])):Math.max(0,y-width);f.body_height=f.height-f.head_top-2;f.body_anchor=x;f.face_width=width;}
  }
 }
 manifest.revision=2;manifest.assets=manifest.assets.filter(a=>!a.file.startsWith('assets/v2/'));
 for(const f of fs.readdirSync(path.join(root,'assets/v2'))){const p=path.join(root,'assets/v2',f),[width,height]=execFileSync('/opt/homebrew/bin/magick',['identify','-format','%w %h',p],{encoding:'utf8'}).split(' ').map(Number);manifest.assets.push({file:'assets/v2/'+f,width,height,bytes:fs.statSync(p).size,purpose:f.replace(/-\d+\.png$/,''),quality_note:'New pixel art, full silhouette retained; lossless PNG optimization.'})}
 fs.writeFileSync(path.join(root,'source/asset-manifest.json'),JSON.stringify(manifest,null,2));fs.writeFileSync(path.join(root,'assets.js'),'window.CinemaForest=true;window.CinemaAssets='+JSON.stringify(manifest.sheets)+';\n');console.log('V2 prepared',Object.keys(manifest.sheets).length,'sheets');
}
run().catch(e=>{console.error(e);process.exitCode=1});
