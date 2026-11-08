// Build battle effect atlases using the installed PixelFX toolkit.
import { readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [toolkitArg, actualArg, swordSource] = process.argv.slice(2);
if (!toolkitArg || !actualArg) throw Error('Usage: node export_puppet_pixelfx.mjs TOOLKIT ACTUAL [SWORD_SOURCE_JSON | --fire-only]');
const fireOnly = swordSource === '--fire-only';
const toolkit = resolve(toolkitArg);
const actual = resolve(actualArg);
const source = path => import(pathToFileURL(join(toolkit, path)).href);
const { createFx, createAct, createFrame, clearFrame, composite, Particles, P, Rng, fit, ease, smooth, band, flare } =
  await source('src/core/index.js');
const { zigzag, stroke } = await source('src/fx/lightning/_lib.js');
const { through, slash } = await source('src/fx/melee/_lib.js');
const { frontCrescent } = await source('src/fx/impacts/_lib.js');
const { encodePNG } = await source('tools/lib/png.mjs');
const fps = 60;
const magmaRamp = JSON.parse(await readFile(new URL('./prometheus_magma_palette.json',import.meta.url),'utf8'));
const magmaColors = Array.from({length:256},(_,luma) => {
  const color = magmaRamp.filter(([level])=>level<=luma).at(-1)[1];
  return [1,3,5].map(offset=>parseInt(color.slice(offset,offset+2),16));
});

// One discharge on contact. The existing projectile still comes from the eye.
function pulse() {
  const ramp = fit(['#251b39','#443563','#664998','#8a64c4','#bd90ea','#e4c6ff','#f7e9ff'], 8);
  const rng = new Rng(1010);
  const particles = new Particles({ rng, sparks: ramp.slice(-4).reverse() });
  const arcs = Array.from({length: 7}, (_, i) => {
    const angle = i*Math.PI*2/7+rng.range(-.2,.2);
    const radius = rng.range(7,19);
    const x = Math.cos(angle), y = Math.sin(angle);
    particles.spawn(P.SPARK, 0, 0, x*radius*4, y*radius*3, rng.range(.14,.36));
    return zigzag(rng, 0, 0, x*radius, y*radius*.86, .44, .25);
  });
  return {
    update: dt => particles.update(dt),
    draw(p, t) {
      const decay = 1-smooth(.025,.27,t);
      if (decay > 0) {
        band(p, 0, 0, 4+16*ease.outQuad(t/.27), .76, 2, .74*decay, ramp.slice(3,7));
        for (const arc of arcs) stroke(p, arc, decay, ramp, .62, { hero:t < .045 });
        flare(p, 0, 0, 8*decay, .86*decay, ramp);
      }
      particles.draw(p);
    },
  };
}

// Claw swipe arcs in a short steel rake. Keep the jets in the body program.
function rake() {
  const ramp = fit(['#192333','#313d54','#586d89','#8299b4','#b7cada','#e8f0ee'],7);
  const rng = new Rng(1011);
  const particles = new Particles({ rng, sparks:['#fff0cb','#d4a766','#ad6947','#744537'] });
  const cuts = Array.from({length:3}, (_, i) => through((i-1)*5, (i-1)*3, .98, 1, 32-i*2, .90, .50, {
    W:4.6-i*.6, t0:i*.012, sweep:.057, hold:.045, trail:.18, ramp, lens:true,
  }));
  for (let i=0; i<11; i++) {
    particles.spawn(P.SPARK, rng.range(-3,3), rng.range(-5,3), rng.range(26,112), rng.range(-49,52),
      rng.range(.15,.34), 0, 1, .025);
  }
  return {
    update: dt => particles.update(dt),
    draw(p, t) {
      for (const cut of cuts) slash(p, cut, t);
      particles.draw(p);
    },
  };
}

function anchor() {
  const ramp = fit(['#402e2a','#73503d','#a57554','#cd9b68','#efc88b','#fff1cb'],7);
  const rng = new Rng(1012);
  const particles = new Particles({ rng, ground:() => 1, sparks:ramp.slice(-4).reverse() });
  for (let i=0; i<24; i++) {
    const x = rng.range(-8,8);
    particles.spawn(P.GRIT, x, -2, rng.range(-78,100), rng.range(-103,-25),
      rng.range(.25,.61), ramp[rng.int(1,4)], rng.int(1,2));
  }
  for (let i=0; i<8; i++) {
    particles.spawn(P.SPARK, -4, -10, rng.range(36,132), rng.range(-84,-12), rng.range(.1,.25));
  }
  return {
    update: dt => particles.update(dt),
    draw(p, t) {
      const fade = 1-smooth(.06,.27,t);
      if (fade > 0) {
        const reach = ease.outQuad(t/.27);
        band(p, 0, -1, 4+28*reach, .15, 2, fade, ramp.slice(2,6));
        frontCrescent(p, 5+22*reach, 1, 14*fade, 9*fade, ramp.slice(3,6).reverse(), fade);
        flare(p, -4, -11, 9*fade, fade*.7, ramp);
      }
      particles.draw(p);
    },
  };
}

// The original fire-core stream stays attached to the caster through release.
function fire() {
  const ramp = fit(['#442024','#7e2826','#ad3527','#d9522b','#ea7a3b','#f8a857','#ffda99'],8);
  const rng = new Rng(1013);
  const particles = new Particles({ rng, ground:() => 22, sparks:ramp.slice(-4).reverse() });
  for (let i=0; i<19; i++) {
    const x = rng.range(-9,5), y = rng.range(-6,6);
    particles.spawn(P.FIRE, x, y, rng.range(9,68), rng.range(-46,15),
      rng.range(.12,.26), 0, rng.range(2,5), rng.range(0,.055));
    particles.spawn(P.EMBER, x, y, rng.range(14,90), rng.range(-62,8),
      rng.range(.22,.54), ramp[rng.int(2,5)], 1);
  }
  return {
    update: dt => particles.update(dt),
    draw(p, t) {
      const heat = 1-smooth(.035,.17,t);
      if (heat > 0) flare(p, 0, 0, 11*heat, .88*heat, ramp);
      particles.draw(p);
    },
  };
}

const effects = {};
async function pack(name, mod, size, pivot, frames, options, layer, draw, colors) {
  const [w,h] = size;
  const columns = 8, width = w*columns, height = h*Math.ceil(frames/columns);
  const pixels = new Uint8Array(width*height*4);
  const frame = createFrame(w,h,-pivot[0],-pivot[1]);
  const rgba = new Uint8ClampedArray(w*h*4);
  const instance = draw ? null : createFx(mod,options);
  for (let i=0; i<frames; i++) {
    clearFrame(frame);
    if (draw) draw(frame,i);
    else {
      if (i) instance.update(1/fps);
      instance.draw(frame,layer);
    }
    composite(frame,rgba);
    const alpha = draw ? 1 : 1-smooth(frames-8,frames-1,i);
    const x = (i%columns)*w, y = Math.floor(i/columns)*h;
    for (let j=0; j<w*h; j++) {
      const dest = ((y+Math.floor(j/w))*width+x+j%w)*4;
      const at = j*4;
      if (colors && rgba[at+3]) {
        // Recolor the baked flame and its glow without changing their alpha.
        const luma = (54*rgba[at]+183*rgba[at+1]+19*rgba[at+2])>>8;
        pixels.set(colors[luma],dest);
      } else pixels.set(rgba.subarray(at,at+3),dest);
      pixels[dest+3] = Math.round(rgba[at+3]*alpha);
    }
  }
  const file = name+'.png';
  const png = encodePNG(width,height,pixels);
  await writeFile(join(actual,'assets/battle-fx',file),png);
  console.log(file,width,height,png.length);
  effects[name] = {paths:['res://assets/battle-fx/'+file],size,pivot,fps,frames,columns,cells:frames,loop:false};
}

if (swordSource && !fireOnly) {
  const double = await source('src/fx/melee/double-slash.js');
  const spin = await source('src/fx/melee/spin-slash.js');
  // Sample the same act clock used by the PixelFX gallery. Both pauses
  // are baked into the blade and pose tracks, with the original shake.
  const instance = createAct(double);
  const samples = [], hits = [];
  instance.onHit = hit => hits.push({frame:samples.length,...hit});
  while (!instance.done()) {
    if (samples.length) instance.update(1/fps);
    samples.push({t:instance.t, pose:instance.pose, shake:instance.shake,
      flash:instance.targets[0].flashT>0, tilt:instance.targets[0].theta, held:instance.frozen});
  }
  const blade = createAct(double);
  await pack('hunapu-double-slash-stock',double,double.meta.size,double.meta.origin,
    samples.length,{},null,(frame,i) => {
      if (i) blade.update(1/fps);
      blade.draw(frame,{body:false,target:false});
    });
  const palette = ['#431920','#771e22','#ae2823','#e13f29','#ff6a3a','#ffa960','#fff0be'];
  for (const layer of ['back','front']) {
    await pack('eileen-fire-spin-'+layer,spin,spin.meta.size,spin.meta.origin,
      Math.round(spin.meta.duration*fps),{palette},layer);
  }
  await writeFile(swordSource,JSON.stringify({effects,double:{samples,hits,target:double.act.target.x},spin:spin.act})+'\n');
  process.exit(0);
}

for (const [name,create,size,pivot,frames] of [
  ['puppet-pulse-refraction',pulse,[88,68],[40,32],29],
  ['puppet-steel-rake',rake,[88,68],[34,32],25],
  ['puppet-anchor-impact',anchor,[98,53],[44,48],38],
  ['puppet-fire-core-crest',fire,[94,76],[28,43],37],
]) {
  const isFire = name === 'puppet-fire-core-crest';
  if (!fireOnly || isFire) {
    await pack(name,{meta:{duration:frames/fps},create},size,pivot,frames,{light:.43},
      undefined,undefined,isFire ? magmaColors : null);
  }
}
if (fireOnly) process.exit(0);

function plan(effect, at, replace_sprites = []) {
  const end = effects[effect].frames/fps;
  return {contact:0,end,left:true,replace_sprites,layers:[{effect,start:0,end,at,hit:true}]};
}
const plans = {
  'cyclops:attack':plan('puppet-pulse-refraction',[1,114],['trio-violet-hit']),
  'owl:attack':plan('puppet-steel-rake',[.982,108],['trio-talon-slash']),
  'prometheus:attack':plan('puppet-anchor-impact',[.99,126],['trio-physical-wave']),
  'prometheus:ranged':plan('puppet-anchor-impact',[.99,126]),
  'prometheus:fire':plan('puppet-fire-core-crest',[.91,106],['trio-flame-crest','trio-flame-embers']),
};
await writeFile(join(actual,'data/puppet_battle_fx.json'),JSON.stringify({effects,plans},null,2)+'\n');
