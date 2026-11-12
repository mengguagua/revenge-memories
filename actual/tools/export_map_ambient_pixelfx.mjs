// Native 16 px map effects derived from PixelFX (MIT), commit a841596.
// Flame and ripple recipes adapt Hugo Duprez / Sprite Fusion through PixelFX.
import { writeFile, readFile } from "node:fs/promises";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";

const [toolkitPath, destination] = process.argv.slice(2);
if (!toolkitPath || !destination) throw Error("Pass the PixelFX toolkit and output directory");
const source = path => import(pathToFileURL(join(resolve(toolkitPath), path)).href);
const { createFx, createFrame, clearFrame, composite, fit, rand, TAU, smooth, hex } = await source("src/core/index.js");
const { burn, noiseFor, hotFirst } = await source("src/fx/fire/_lib.js");
const { ring } = await source("src/fx/water/_lib.js");
const { encodePNG } = await source("tools/lib/png.mjs");
const output = resolve(destination);
const frames = 32, fps = 16, duration = frames / fps, columns = 8;
const water = fit(["#2f475a", "#4c6878", "#708c98", "#a7b9bb", "#c1ceca", "#dbe1d5"], 7);

const definitions = {
  sheen: {
    size: [16,16],
    draw(p,t) {
      for (let i=0; i<2; i++) {
        const age=(t/duration+i*.53)%1;
        const center=7+Math.sin(age*TAU+i)*2;
        const y=4+i*7+Math.round(Math.sin(age*TAU)*1.2);
        const width=4+Math.sin(age*Math.PI)*7;
        const power=Math.sin(age*Math.PI)**2*.72;
        const left=Math.max(1,Math.round(center-width/2));
        const right=Math.min(14,Math.round(center+width/2));
        for(let x=left;x<=right;x++) {
          const edge=Math.min(x-left+1,right-x+1)/2;
          p.blend(x,y,water[3],power*Math.min(1,edge));
          p.blend(x+1,y+1,water[0],power*.36);
        }
      }
    }
  },
  ripple: {
    size: [32,16],
    draw(p,t) {
      const age=t/duration;
      ring(p,16,8,2+age*12,.28,Math.sin(age*Math.PI)*.44,water,
        {n:1,gap:4,seed:12,wob:.2,glint:0});
    }
  },
  foam: {
    size: [16,16],
    draw(p,t) {
      const phase=t/duration*TAU;
      const pulse=(Math.sin(phase)+1)/2;
      for(let x=0;x<16;x++) {
        const y=2+Math.round(pulse*3+Math.sin(x*.55+phase)*.7);
        const a=(.28+.32*pulse)*(x%7===0?.4:1);
        p.blend(x,y,water[5],a);
        p.blend(x,y+1,water[3],a*.4);
        if(x%5<2)p.blend(x,y+3,water[2],a*.4);
      }
    }
  },
  flame: {
    size:[16,24],
    draw(p,t) {
      const ramp=fit(["#593c35","#895a3d","#b67c46","#d9a15a","#efc77e","#f4dcac"],9);
      burn(p,t,[[0,0,1,1.1,0],[-1,0,.7,.7,1],[1,0,.65,.7,1]],{
        H:hotFirst(ramp),D:duration,NL:noiseFor(duration),S:33,x:8,y:18,
        height:8,lean:.08,spread:1,puffs:0,licks:2,smoke:0,embers:0,
        glow:0,glowR:0,wind:.3
      });
    }
  },
  torch: {
    size:[16,28],
    draw(p,t) {
      const ramp=fit(["#593c35","#895a3d","#b67c46","#d9a15a","#efc77e","#f4dcac"],9);
      p.rect(5,19,6,8,hex("#34363a"));
      p.rect(5,19,1,7,hex("#727170"));
      p.rect(7,16,3,10,hex("#624d3a"));
      p.rect(7,16,1,9,hex("#a1855c"));
      p.rect(6,17,5,2,hex("#34363a"));
      burn(p,t,[[0,0,1,1.1,0],[-1,0,.7,.7,1],[1,0,.65,.7,1]],{
        H:hotFirst(ramp),D:duration,NL:noiseFor(duration),S:44,x:8,y:17,
        height:9,lean:.1,spread:1,puffs:0,licks:2,smoke:0,embers:0,
        glow:0,glowR:0,wind:.3
      });
    }
  },
  lamplight: {
    size:[16,16],
    draw(p,t) {
      // Small golden oil-lamp light; no flame or magic capability is added.
      const pulse=.5+.5*Math.sin(t/duration*TAU);
      for(let y=2;y<14;y++) for(let x=2;x<14;x++) {
        const distance=Math.hypot(x-7.5,y-7.5);
        const power=Math.max(0,1-distance/6);
        if(power>0)p.blend(x,y,hex("#d9bb79"),Math.floor(power*4)/4*.26*pulse);
      }
      for(let y=7;y<9;y++)for(let x=7;x<9;x++)p.blend(x,y,hex("#ead8a7"),.18+.42*pulse);
    }
  },
  shadow: {
    size:[96,48],
    // Ground projection of clustered puffs, adapted from weather/clouds.
    // No moon, sky painting, luminous rim, or full-screen color wash.
    draw(p) {
      const lobes=[[20,25,15],[38,17,16],[58,18,17],[73,25,14],[48,30,22]];
      for(let y=0;y<48;y++) for(let x=0;x<96;x++) {
        let coverage=0;
        for(const [cx,cy,r] of lobes) coverage=Math.max(coverage,1-Math.hypot((x-cx)*.85,y-cy)/r);
        const a=smooth(0,.28,coverage)*.12;
        if(a>0)p.blend(x,y,hex("#23313e"),a);
      }
    }
  }
};
const entries={};
for(const [name,recipe] of Object.entries(definitions)) {
  const [w,h]=recipe.size, count=name==="shadow"?1:name==="foam"?frames*4:frames;
  const sheetW=w*Math.min(columns,count),sheetH=h*Math.ceil(count/columns);
  const pixels=new Uint8Array(sheetW*sheetH*4);
  const mod={meta:{size:[w,h],origin:[0,0],duration,loop:true,fps,options:{}},draw:recipe.draw};
  const instance=createFx(mod,{seed:33});
  const frame=createFrame(w,h,0,0),rgba=new Uint8ClampedArray(w*h*4);
  for(let i=0;i<count;i++){
    if(i)instance.update(1/fps);
    clearFrame(frame);instance.draw(frame);composite(frame,rgba);
    for(let y=0;y<h;y++) for(let x=0;x<w;x++) {
      const side=name==="foam"?Math.floor(i/frames):0;
      const [rx,ry]=side===1?[h-1-y,x]:side===2?[w-1-x,h-1-y]:side===3?[y,w-1-x]:[x,y];
      const at=((Math.floor(i/columns)*h+ry)*sheetW+(i%columns)*w+rx)*4;
      pixels.set(rgba.subarray((y*w+x)*4,(y*w+x+1)*4),at);
    }
  }
  const png=encodePNG(sheetW,sheetH,pixels);
  await writeFile(join(output,name+".png"),png);
  entries[name]={path:"res://assets/map-ambient-20261112/"+name+".png",size:[w,h],frames:count,columns:Math.min(columns,count),fps,loop:true};
  console.log(name,sheetW,sheetH,png.length);
}
await writeFile(join(output,"effects.json"),JSON.stringify(entries,null,2)+"\n");
const license=await readFile(join(resolve(toolkitPath),"LICENSE"),"utf8");
await writeFile(join(output,"LICENSE"),license);
// JSON is included by both existing Godot export presets, retaining the MIT
// copyright/license in packaged games as well as the repository's LICENSE.
await writeFile(join(output,"attribution.json"),JSON.stringify({source:"https://github.com/patch-gg/pixelfx",commit:"a84159688af3ca37a4be05a0d422b94451b2e24e",license},null,2)+"\n");
await writeFile(join(output,"NOTICE.txt"),"Derived from PixelFX, https://github.com/patch-gg/pixelfx, commit a84159688af3ca37a4be05a0d422b94451b2e24e.\nFlame/ripple/cloud/snow techniques include MIT work by Hugo Duprez / Sprite Fusion. Native map geometry, palette, scale and density adapted for Revenge Memories.\n");
