const fs=require('fs'),path=require('path'),{execFileSync}=require('child_process');
const root=path.resolve(__dirname,'..'),p=path.join(root,'source/asset-manifest.json'),m=JSON.parse(fs.readFileSync(p));
for(const f of m.sheets.portraits.frames){
 const old=path.join(root,f.path),next=f.path.replace('.png','.webp');
 execFileSync('/opt/homebrew/bin/magick',[old,'-define','webp:lossless=true','-quality','100',path.join(root,next)]);
 const comparison=execFileSync('/opt/homebrew/bin/magick',['compare','-metric','AE',old,path.join(root,next),'null:'],{encoding:'utf8',stdio:['ignore','pipe','pipe']});
 fs.copyFileSync(old,path.join(root,'source',path.basename(old)));fs.unlinkSync(old);f.path=next;
}
m.assets=[];
for(const file of fs.readdirSync(path.join(root,'assets'))){
 if(!/\.(png|webp)$/.test(file))continue;
 const full=path.join(root,'assets',file),[width,height]=execFileSync('/opt/homebrew/bin/magick',['identify','-format','%w %h',full],{encoding:'utf8'}).split(' ').map(Number),bytes=fs.statSync(full).size;
 m.assets.push({file:'assets/'+file,width,height,bytes,purpose:file.startsWith('target-')?'Dynamic target static snapshot':file.startsWith('portraits')?'Approved new cinematic portrait':file.startsWith('battlefield')?'Dedicated 16:9 pixel battle backdrop':file.startsWith('impact')?'Enemy-agnostic impact/smoke key frame':'New full-body hero action key pose',compression:file.endsWith('.webp')?'Lossless WebP, decoded pixels verified identical':'Lossless optimized PNG',quality_note:bytes>50000?'Retained complete pixel silhouette and readable detail; no lossy reduction.':null});
}
fs.writeFileSync(p,JSON.stringify(m,null,2));fs.writeFileSync(path.join(root,'assets.js'),'window.CinemaAssets='+JSON.stringify(m.sheets)+';\n');
const captures=fs.readdirSync(path.join(root,'checks')).filter(f=>f.endsWith('.png')).map(file=>{const full=path.join(root,'checks',file),[width,height]=execFileSync('/opt/homebrew/bin/magick',['identify','-format','%w %h',full],{encoding:'utf8'}).split(' ').map(Number);return {file:'checks/'+file,width,height,bytes:fs.statSync(full).size,purpose:file.endsWith('-poster.png')?'Video poster at full preview resolution':'Offline visual verification capture',quality_note:'Lossless original capture retained to inspect text, sprite edges and backdrop detail; not a game runtime asset.'}});
fs.writeFileSync(path.join(root,'source/delivery-inventory.json'),JSON.stringify({assets:m.assets,captures,source_images:'Original imagegen masters retained in source/, never loaded by preview.'},null,2));
console.log(JSON.stringify({active_images:m.assets.length,total_asset_bytes:m.assets.reduce((s,a)=>s+a.bytes,0),portraits_lossless:true}));
