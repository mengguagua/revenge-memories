import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { renderFrames, spriteSheet } from "./pixelfx-work/tools/lib/fxlib.mjs";
import * as fireSpell from "./pixelfx-work/src/fx/revision2/spells.js";
import * as bookends from "./pixelfx-work/src/fx/revision3/bookends.js";

const root = dirname(fileURLToPath(import.meta.url));
const base = join(root, "../..");
const output = join(base, basename(root), "assets/fx");
const previous = join(base, "weapon-magic-r2-20261107/assets/fx/manifest.json");
const manifest = JSON.parse(readFileSync(previous, "utf8"));

const fireColors = {
  fire: ["#281923", "#4d202b", "#772b34", "#ab3c38",
    "#ce4b3b", "#e86946", "#f38a57", "#ffb080"],
  ragnarok: ["#27171e", "#4d1f2a", "#792934", "#ae3738",
    "#d44a37", "#ed653f", "#f88b55", "#ffb476"],
};
const edgeColors = {
  holy: ["#253b3d", "#3a5556", "#5a7673", "#789792",
    "#96b4a7", "#b5c6ac", "#dacd9d", "#ede0b5"],
  rain: ["#263242", "#394b67", "#527087", "#7097a8",
    "#a3c2c9", "#c1d5cf", "#e2e0c6", "#f0e9cd"],
  drain: ["#2d1b29", "#532734", "#723a46", "#984b55",
    "#b36462", "#c68174", "#dc9e88", "#eab399"],
  halo: ["#202940", "#354463", "#4c6489", "#6a86a9",
    "#8baac2", "#adc8d1", "#c9d8d1", "#e1e1ce"],
  slime: ["#222a44", "#2e3a5a", "#3e537b", "#526b99",
    "#6886ad", "#83a0c1", "#a5b9cb", "#ccd3d2"],
};

const authored = {};
mkdirSync(output, { recursive: true });

function render(id, module, options, overrides) {
  const meta = { ...module.meta, ...overrides };
  const fx = { id: "revision3/" + id, meta, mod: { ...module, meta } };
  const frames = renderFrames(fx, { fps: 60, actor: false, bg: "none",
    options: { seed: 23, ...options } });
  const sheet = spriteSheet(fx, frames, id);
  writeFileSync(join(output, id + ".png"), sheet.png);
  writeFileSync(join(output, id + ".json"), JSON.stringify(sheet.json, null, 2) + "\n");
  authored[id] = { ...sheet.json.meta.pixelfx, path: "assets/fx/" + id + ".png", options };
  console.log(id, sheet.png.length);
}

for (const [kind, variants] of [["fire", ["", "cinema-"]], ["ragnarok", [""]]]) {
  for (const variant of variants) {
    for (const phase of ["charge", "travel", "impact"]) {
      const suffix = variant + kind + "-" + phase;
      const old = manifest.effects["r2-" + suffix];
      const duration = phase === "charge" ? 1.2 : phase === "travel" ? .8 : 2;
      render("r3-" + suffix, fireSpell, { ...old.options, palette: fireColors[kind], light: .10 },
        { size: old.frameSize, origin: old.pivot, duration, loop: old.loop });
    }
  }
}

const timings = {
  holy: { open: .52, end: .62 }, rain: { open: .49, end: .56 },
  drain: { open: .50, end: .60 }, halo: { end: 1.02 }, slime: { end: 1.10 },
};
for (const [kind, phases] of Object.entries(timings)) {
  const variants = kind === "holy" ? ["", "cinema-"] : [""];
  for (const variant of variants) {
    for (const [phase, duration] of Object.entries(phases)) {
      render("r3-" + variant + kind + "-" + phase, bookends,
        { kind, phase, duration, size: variant ? 1.42 : 1, palette: edgeColors[kind], light: .09 },
        { duration, size: variant ? [156, 120] : [112, 96],
          origin: variant ? [78, 80] : [56, 62] });
    }
  }
}

Object.assign(manifest.effects, authored);
manifest.revision = 3;
manifest.newEffects = Object.keys(authored);
writeFileSync(join(output, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
