// Native-pixel additions for the game's original spell animation.
// Uses PixelFX's seeded motion and pixel painter, with no actor artwork.
import { Rng, TAU, clamp, ease, fit, smooth, sparkle } from "../../core/index.js";

export const meta = {
  name: "Spell openings and endings",
  tags: ["magic", "native", "bookends"],
  size: [112, 96],
  origin: [56, 62],
  duration: .65,
  fps: 60,
  loop: false,
  bg: "none",
  options: {
    seed: 23, kind: "holy", phase: "open", duration: .65, size: 1,
    palette: ["#253b3d", "#3a5556", "#5a7673", "#789792",
      "#96b4a7", "#b5c6ac", "#dacd9d", "#ede0b5"],
  },
};

function flake(p, x, y, s, lean, colors, alpha) {
  const points = [
    [x - s * lean, y - s], [x + s, y - s * .13],
    [x + s * lean, y + s], [x - s, y + s * .18],
  ];
  p.poly(points, colors[2], alpha);
  p.line(...points[0], x, y, colors[5], alpha);
  p.line(x, y, ...points[2], colors[4], alpha);
  p.dot(x, y, colors[6], alpha);
}

function arc(p, x, y, rx, ry, a, span, colors, alpha, width = 1) {
  const points = [];
  for (let i = 0; i <= 22; i++) {
    const t = a + span * i / 22;
    points.push([x + Math.cos(t) * rx, y + Math.sin(t) * ry]);
  }
  p.polyline(points.map(([px, py]) => [px, py + width]), colors[2], alpha * .88);
  p.polyline(points, colors[5], alpha);
}

function opening(p, t, o, colors, flecks) {
  const u = clamp(t / o.duration);
  const alpha = smooth(0, .19, u) * (1 - smooth(.48, 1, u));
  const s = o.size;
  if (o.kind === "holy") {
    for (let i = 0; i < 4; i++) {
      const a = i * TAU / 4 + .26 + u * 1.5;
      const r = (16 - 8 * ease.outCubic(u)) * s;
      const x = Math.cos(a) * r, y = Math.sin(a) * r * .64;
      p.poly([[x - 3 * s, y - 2 * s], [x, y + 2 * s],
        [x + 3 * s, y - 3 * s], [x, y + 4 * s]], colors[3], alpha);
      p.line(x - 3 * s, y - 2 * s, x, y + 2 * s, colors[5], alpha);
      p.dot(x, y + 3 * s, colors[7], alpha);
    }
    arc(p, 0, 1 * s, (13 - 5 * u) * s, 6 * s, -1.5 + u, 2.2, colors, alpha * .58);
  } else if (o.kind === "rain") {
    for (let i = 0; i < 4; i++) {
      const x = (-13 + i * 8) * s;
      const y = (-3 + Math.abs(i - 1.5) * 2 - 8 * u) * s;
      flake(p, x, y, 2.4 * s, -.45, colors, alpha * (.75 + i * .05));
      p.line(x - 3 * s, y + 6 * s, x - s, y + s, colors[3], alpha * .70);
    }
  } else {
    for (const side of [-1, 1]) {
      arc(p, side * 2 * s, 0, (18 - 9 * u) * s, (9 - 3 * u) * s,
        u * 1.7 + (side < 0 ? Math.PI : 0), 2.45, colors, alpha * .75);
    }
    for (const fleck of flecks.slice(0, 5)) {
      const r = (17 - 11 * u) * s;
      p.dot(Math.cos(fleck.angle + u) * r, Math.sin(fleck.angle + u) * r * .65,
        colors[4], alpha);
    }
  }
  p.glow(0, 0, 8 * s, colors[3], .09 * alpha);
}

function dispersal(p, t, o, colors, flecks) {
  const u = clamp(t / o.duration);
  const fade = smooth(0, .14, u) * (1 - smooth(.44, 1, u));
  const s = o.size;
  if (o.kind === "holy") {
    for (const fleck of flecks.slice(0, 6)) {
      const span = (7 + 15 * ease.outCubic(u)) * s;
      const x = Math.cos(fleck.angle) * span;
      const y = (-5 - fleck.rise * u + Math.sin(fleck.angle) * 6) * s;
      flake(p, x, y, (2.1 - .7 * u) * s, fleck.lean, colors, fade * fleck.strength);
    }
    if (u < .36) sparkle(p, -3 * s, -6 * s, 3 * s, colors[6], colors[3], fade * .55);
  } else if (o.kind === "rain") {
    for (const fleck of flecks) {
      const x = Math.cos(fleck.angle) * (6 + fleck.rise * ease.outCubic(u)) * s;
      const y = (-2 - Math.sin(u * Math.PI) * (4 + fleck.rise * .55)) * s;
      p.line(x, y, x - fleck.lean * 2 * s, y - 2 * s, colors[3], fade * fleck.strength);
      p.dot(x, y, colors[6], fade * fleck.strength);
    }
  } else {
    const radius = (14 + 6 * ease.outCubic(u)) * s;
    for (const side of [-1, 1]) {
      arc(p, 0, -4 * u * s, radius, radius * .60,
        u * 1.8 + (side < 0 ? Math.PI : 0), 1.95 - u * .65, colors, fade * .67);
    }
    for (const fleck of flecks.slice(0, 5)) {
      const x = Math.cos(fleck.angle) * radius;
      const y = (Math.sin(fleck.angle) * 8 - u * fleck.rise) * s;
      p.dot(x, y, colors[4], fade * fleck.strength);
    }
  }
}

function ringRibbon(p, x, y, rx, ry, start, span, colors, alpha) {
  p.each(x - rx - 3, y - ry - 2, x + rx + 3, y + ry + 2, (px, py, sx, sy) => {
    const dx = (px - x) / rx, dy = (py - y) / ry;
    const angle = (Math.atan2(dy, dx) - start + TAU * 2) % TAU;
    if (angle > span) return;
    const edge = (Math.hypot(dx, dy) - 1) * ry;
    const thickness = .72 + .55 * Math.sin(angle / span * Math.PI);
    if (Math.abs(edge) > thickness) return;
    const tone = edge > .26 ? colors[2] : edge < -.29 ? colors[3] : colors[5];
    p.blendPx(sx, sy, tone, alpha);
  });
}

function haloEnding(p, t, o, colors, flecks) {
  const s = o.size, u = clamp(t / o.duration);
  const rise = ease.outCubic(u);
  for (let i = 0; i < 3; i++) {
    const decay = 1 - smooth(.12 + .07 * i, .70 + .08 * i, u);
    if (decay <= 0) continue;
    const x = (i - 1) * (2 + rise * 5) * s;
    const y = (-38 + i * 10 + 19 * rise) * s;
    const radius = (15 + i * 2 + rise * 11) * s;
    const start = -.42 - i * 1.13 + u * .9;
    ringRibbon(p, x, y, radius, (4 + rise * 3) * s, start, 3.8 - u * 1.45,
      colors, decay * .88);
    ringRibbon(p, x, y, radius - 3 * s, (3 + rise * 3) * s, start + Math.PI, 1.6,
      colors, decay * .43);
  }
  const opacity = smooth(.08, .24, u) * (1 - smooth(.58, 1, u));
  for (const fleck of flecks) {
    const x = Math.cos(fleck.angle) * (13 + 17 * rise) * s;
    const y = (-18 - fleck.rise * .35 + 15 * u * u + Math.sin(fleck.angle) * 7) * s;
    flake(p, x, y, 2.0 * s, fleck.lean, colors, opacity * fleck.strength);
  }
}

function gelVolume(p, x, y, rx, ry, color, alpha) {
  p.each(x - rx, y - ry, x + rx, y + ry, (px, py, sx, sy) => {
    if (((px - x) / rx) ** 2 + ((py - y) / ry) ** 2 <= 1) {
      p.blendPx(sx, sy, color, alpha);
    }
  });
}

function slimeEnding(p, t, o, colors, flecks) {
  const s = o.size, u = clamp(t / o.duration);
  const fall = ease.inQuad(clamp(u / .38));
  const width = (28 + 4 * fall) * s, height = (34 - 29 * fall) * s;
  const shell = 1 - smooth(.15, .47, u);
  if (shell > 0) {
    p.each(-width - 2, -height - 2, width + 2, 1, (x, y, sx, sy) => {
      const dx = x / width;
      if (Math.abs(dx) > 1 || y > -s) return;
      const surface = -height * Math.sqrt(1 - dx * dx);
      const depth = y - surface;
      if (depth < 0) return;
      const edge = depth < 2 * s || Math.abs(dx) > .90;
      const reflection = depth >= 2 * s && depth < 4 * s && dx > -.67 && dx < .10;
      const tone = reflection ? colors[5] : edge ? colors[3] : colors[2];
      const alpha = shell * (reflection ? .87 : edge ? .80 : .35);
      p.blendPx(sx, sy, tone, alpha);
    });
  }
  const pool = smooth(.10, .30, u) * (1 - smooth(.58, 1, u));
  if (pool > 0) {
    const r = (21 + 8 * fall - 7 * u) * s;
    gelVolume(p, 0, -3 * s, r, 2.5 * s, colors[1], pool);
    gelVolume(p, -3 * s, -3.4 * s, r * .77, 1.3 * s, colors[3], pool * .92);
    gelVolume(p, -r * .29, -4.1 * s, r * .24, .59 * s, colors[5], pool * .72);
  }
  for (const fleck of flecks.slice(0, 7)) {
    const age = u - .10 - fleck.delay * .12;
    if (age <= 0 || age >= .69) continue;
    const opacity = smooth(0, .11, age) * (1 - smooth(.32, .69, age));
    const dir = Math.cos(fleck.angle);
    const x = dir * (12 + age * (20 + fleck.rise)) * s;
    const y = Math.min(-2.1, -13 - 30 * age + 94 * age * age) * s;
    const r = (1.8 + fleck.strength * 1.6) * s * (1 - .38 * age);
    const ry = y > -4 * s ? r * .45 : r;
    gelVolume(p, x, y, r + .5 * s, ry + .5 * s, colors[1], opacity);
    gelVolume(p, x, y, r * .86, ry * .79, colors[3], opacity);
    p.blend(x - .4 * s, y - .6 * s, colors[6], opacity * .92);
  }
}

export function create(o) {
  const colors = fit(o.palette, 8);
  const rng = new Rng(o.seed);
  const flecks = Array.from({ length: 9 }, (_, i) => ({
    angle: (i + rng.range(-.3, .3)) / 9 * TAU,
    rise: rng.range(7, 19),
    lean: rng.range(-.65, .65),
    strength: rng.range(.56, .98),
    delay: rng.next(),
  }));
  let time = 0;
  return {
    update(dt) { time += dt; },
    draw(p) {
      if (time >= o.duration - .0001) return;
      if (o.phase === "open") opening(p, time, o, colors, flecks);
      else if (o.kind === "halo") haloEnding(p, time, o, colors, flecks);
      else if (o.kind === "slime") slimeEnding(p, time, o, colors, flecks);
      else dispersal(p, time, o, colors, flecks);
    },
  };
}
