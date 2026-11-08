// Extract the original PixelFX Damage number glyph finish and bounce clock.
// The game lays out the resolved damage at runtime, including unseen values.
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [toolkitArg, actualArg] = process.argv.slice(2);
if (!toolkitArg || !actualArg) throw Error('Usage: node export_pixelfx_damage.mjs TOOLKIT ACTUAL');
const toolkit = resolve(toolkitArg);
const actual = resolve(actualArg);
const coreUrl = pathToFileURL(join(toolkit, 'src/core/index.js')).href;
const fontUrl = pathToFileURL(join(toolkit, 'src/fx/ui/_lib.js')).href;
const { createFx, createFrame, composite, painterFor, FONTS } = await import(coreUrl);
const { drawWord } = await import(fontUrl);
const { encodePNG } = await import(pathToFileURL(join(toolkit, 'tools/lib/png.mjs')).href);
const { edgeFade } = await import(pathToFileURL(join(toolkit, 'tools/lib/fxlib.mjs')).href);
const source = await readFile(join(toolkit, 'src/fx/ui/damage-number.js'), 'utf8');
const paintImport = 'import { spell, drawWord } from "./_lib.js";';
if (!source.includes(paintImport)) throw Error('Pinned Damage number interface changed');
const sampler = source.replace('"../../core/index.js"', JSON.stringify(coreUrl)).replace(
  paintImport,
  'import { spell } from '+JSON.stringify(fontUrl)+';\n'+
  'export let sample = null;\nfunction drawWord(_frame, items, style) { sample = {items, style}; }'
);
const effect = await import('data:text/javascript;base64,'+Buffer.from(sampler).toString('base64'));
const instance = createFx(effect, {text:'8', light:.42});
const fps = 60;
const frameCount = Math.ceil(effect.meta.duration * fps);
const symbols = '-0123456789';
const font = FONTS.big;
const cell = [30,36];
const hitSize = [96,72];
const pivot = [40,52];
const tracks = [];
const glyphFrames = [];
const hitFrames = [];
function rgba(frame) {
  return composite(frame, new Uint8ClampedArray(frame.w * frame.h * 4));
}
for (let i=0; i<frameCount; i++) {
  if (i) instance.update(1/fps);
  const hit = createFrame(...hitSize,-pivot[0],-pivot[1]);
  instance.draw(hit);
  edgeFade(hit, 8);
  hitFrames.push(rgba(hit));
  const state = effect.sample;
  const age = i/fps;
  if (state && age < 1.01) {
    const item = state.items[0];
    const center = item.x + item.g.w * item.sx / 2;
    tracks.push([center, item.y, item.sx].map(x=>Math.round(x*10000)/10000));
    for (const symbol of symbols) {
      const frame = createFrame(...cell,-3,-2);
      drawWord(painterFor(frame),[{...item, g:font.glyphs[symbol], x:0, y:0}],state.style);
      glyphFrames.push(rgba(frame));
    }
  } else {
    tracks.push(null);
    for (const _ of symbols) glyphFrames.push(new Uint8Array(cell[0]*cell[1]*4));
  }
}
const dir = join(actual,'assets/battle-fx');
async function pack(stem, size, frames, cols, cells) {
  const [w,h] = size;
  const paths = [];
  for(let start=0;start<frames.length;start+=cells) {
    const length = Math.min(cells,frames.length-start);
    const width = w*cols;
    const height = h*Math.ceil(length/cols);
    const bytes = new Uint8Array(width*height*4);
    for(let i=0;i<length;i++) {
      const f = frames[start+i];
      const ox = i%cols*w;
      const oy = Math.floor(i/cols)*h;
      for(let y=0;y<h;y++) {
        bytes.set(f.subarray(y*w*4,(y+1)*w*4),((oy+y)*width+ox)*4);
      }
    }
    const name = stem+'-'+String(paths.length).padStart(2,'0')+'.png';
    await writeFile(join(dir,name),encodePNG(width,height,bytes));
    paths.push('res://assets/battle-fx/'+name);
  }
  return {paths,size,columns:cols,cells,frames:frames.length,loop:false,fps};
}
const hit = await pack('damage-hit',hitSize,hitFrames,6,30);
hit.pivot = pivot;
const glyphs = await pack('damage-glyph',cell,glyphFrames,symbols.length,symbols.length*16);
glyphs.pivot = [3,2];
await writeFile(join(actual,'data/battle_damage_glyphs.json'),JSON.stringify({
  fps,symbols,widths:[...symbols].map(s=>font.glyphs[s].w),gap:font.gap,tracks,hit,glyphs
})+'\n');
