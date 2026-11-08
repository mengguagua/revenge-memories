// Preview-only palette substitution. Source texture alpha and the captured draw rectangle
// identify the original water contribution; game files and the left reference stay intact.
window.WaterPalette = (() => {
 const pixels=new WeakMap();
 function source(image){
  if(!pixels.has(image)){const c=document.createElement('canvas');c.width=image.naturalWidth;c.height=image.naturalHeight;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(image,0,0);pixels.set(image,{w:c.width,h:c.height,p:ctx.getImageData(0,0,c.width,c.height).data});}
  return pixels.get(image);
 }
 function apply(ctx,boxes,palette,images){
  const ramp=palette.map(s=>[1,3,5].map(i=>parseInt(s.slice(i,i+2),16)));let changed=0;
  for(const box of boxes){
   const tex=source(images.get(box.texture));
   const x=Math.max(191,box.x),y=Math.max(0,box.y),w=Math.min(447,box.x+box.w)-x,h=Math.min(128,box.y+box.h)-y;
   if(w<=0||h<=0)continue;
   const region=ctx.getImageData(x,y,w,h),p=region.data,indices=new Int32Array(w*h);let probes=0,matches=0;
   for(let j=0;j<h;j++)for(let i=0;i<w;i++){
    // The Godot capture was 2×, then sampled to logical pixels with nearest-neighbour.
    const u=x+i-box.x+.75,v=y+j-box.y+.75;
    const sx=Math.max(0,Math.min(tex.w-1,Math.floor((box.flip?box.w-u:u)*tex.w/box.w))),sy=Math.max(0,Math.min(tex.h-1,Math.floor(v*tex.h/box.h)));
    const k=(j*w+i)*4,q=(sy*tex.w+sx)*4;indices[j*w+i]=q;
    if(tex.p[q+3]>240&&tex.p[q+2]-tex.p[q]>65&&tex.p[q+2]-tex.p[q+1]>20){
     probes++;if(Math.max(...[0,1,2].map(c=>Math.abs(p[k+c]-tex.p[q+c])))<=12)matches++;
    }
   }
   // During the game's hit reaction the old effect is temporarily absent. Never tint that frame.
   if(probes<4||matches/probes<.55)continue;
   for(let i=0;i<w*h;i++){
    const k=i*4,q=indices[i],alpha=tex.p[q+3]/255;
    if(alpha<.025)continue;
    const r=p[k],g=p[k+1],b=p[k+2];
    if(!(b-r>=8&&g-r>=5)&&!(r>160&&g>170&&b>175&&b>=r-12))continue;
    const luma=(.2126*tex.p[q]+.7152*tex.p[q+1]+.0722*tex.p[q+2])/255;
    const color=ramp[Math.min(ramp.length-1,Math.round(luma*(ramp.length-1)))];
    const difference=Math.max(...[0,1,2].map(c=>Math.abs(p[k+c]-tex.p[q+c])));
    for(let c=0;c<3;c++){
     const value=alpha>.96&&difference>24?ramp[Math.min(ramp.length-1,Math.round((.2126*r+.7152*g+.0722*b)/255*(ramp.length-1)))][c]:p[k+c]+alpha*(color[c]-tex.p[q+c]);
     p[k+c]=Math.max(0,Math.min(255,Math.round(value)));
    }
    changed++;
   }
   ctx.putImageData(region,x,y);
  }
  return changed;
 }
 return {apply};
})();
