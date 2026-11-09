/* Native-pixel art for the standalone review. Inputs are read-only render layers and map coordinates. */
const TILE = 16;
const PAD = 32;
const colors = {
  cedar: { shadow: "#263745", side: "#3e3029", keel: "#292722", seam: "#625044", rim: "#9f8564", light: "#ccb18a", dark: "#634f40", deck: "#9b755022" },
  navy: { shadow: "#253745", side: "#303033", keel: "#27292b", seam: "#535055", rim: "#7b7271", light: "#a39887", dark: "#4c4648", deck: "#575c6b21" },
  fishing: { shadow: "#273c45", side: "#42382c", keel: "#302923", seam: "#645844", rim: "#9d8968", light: "#c3ae88", dark: "#655746", deck: "#94785020" },
  tender: { shadow: "#283b47", side: "#373332", keel: "#2e2a28", seam: "#63544a", rim: "#8f7665", light: "#b29a81", dark: "#5b4b42", deck: "#83635521" },
  quay: { shadow: "#2c3a43", side: "#41474a", seam: "#596168", rim: "#777b77", light: "#999b91", dark: "#4d5353" }
};

function box(ctx, color, x, y, w, h) {
  if (w <= 0 || h <= 0) return;
  ctx.fillStyle = color;
  ctx.fillRect(x, y, w, h);
}

function pixelBounds([x0, y0, x1, y1]) {
  return { x: PAD + x0 * TILE, y: PAD + y0 * TILE, w: (x1 - x0 + 1) * TILE, h: (y1 - y0 + 1) * TILE };
}

function hullProfile(ground, bounds, style) {
  const [x0, y0, x1, y1] = bounds;
  const rows = [];
  for (let y = y0; y <= y1; y++) {
    const deck = [];
    for (let x = x0; x <= x1; x++) {
      if ("s+".includes(ground[y][x])) deck.push(x);
    }
    if (!deck.length) throw new Error("Blank row in ship deck");
    const left = PAD + deck[0] * TILE;
    const right = PAD + (deck.at(-1) + 1) * TILE;
    for (let n = 0; n < TILE; n++) rows.push({ left, right });
  }
  const origin = PAD + y0 * TILE;
  const last = rows.length - 1;
  const { prow, stern, port, starboard } = style;
  const center = (rows[0].left + rows[0].right) / 2;
  const result = [];

  for (let i = -prow; i < 0; i++) {
    const taper = (i + prow) / prow;
    const left = Math.floor(center - 5 + (rows[0].left - center + 5) * taper);
    const right = Math.ceil(center + 5 + (rows[0].right - center - 5) * taper);
    result.push({ y: origin + i, left, right, end: "bow" });
  }
  for (let i = 0; i <= last; i++) {
    let { left, right } = rows[i];
    for (let offset = -11; offset <= 11; offset++) {
      const adjacent = rows[i + offset];
      if (!adjacent) continue;
      left = Math.min(left, adjacent.left + Math.ceil(Math.abs(offset) * 1.55));
      right = Math.max(right, adjacent.right - Math.ceil(Math.abs(offset) * 1.55));
    }
    result.push({ y: origin + i, left, right, raw: rows[i] });
  }
  for (let i = 1; i <= stern; i++) {
    const inset = Math.floor(i * 0.9);
    result.push({ y: origin + last + i, left: rows[last].left + inset, right: rows[last].right - inset, end: "stern" });
  }

  return result.map(row => ({ ...row, outsideL: row.left - port, outsideR: row.right + starboard }));
}

function nearOpening(x, y, bridges) {
  return bridges.some(({ x: left, y: top, w, h, axis }) =>
    axis === "h"
      ? y >= top + 3 && y < top + h - 3 && x >= left - 9 && x <= left + w + 9
      : x >= left + 3 && x < left + w - 3 && y >= top - 12 && y <= top + h + 6
  );
}

function drawHull(ctx, stage, ship, openings) {
  const p = colors[ship.palette];
  const rows = hullProfile(stage.ground, ship.bounds, ship);
  const span = (c, left, right, y, dy = 0) => box(ctx, c, left, y + dy, right - left, 1);

  // The shadow and the down-facing hull sit in the water outside the movement grid.
  for (const { y, outsideL, outsideR } of rows) {
    span("#202d3b47", outsideL - 3, outsideR + 6, y, 5);
    span(p.shadow, outsideL - 1, outsideR + 3, y, 2);
  }
  for (const { y, left, right, end, outsideL, outsideR } of rows) {
    span(p.keel, outsideL, outsideR, y);
    span(p.side, outsideL + 2, outsideR - 2, y);
    span(p.seam, outsideL + 2, outsideL + 3, y);
    span(p.seam, outsideR - 6, outsideR - 5, y);
    span(p.side, right + 2, outsideR - 2, y);
    span(p.seam, right + 4, right + 5, y);
    if (y % 17 === 1) {
      span(p.seam, outsideL + 2, left - 1, y);
      span(p.seam, right + 5, outsideR - 2, y);
    }
    if (end === "bow" && y % 5 === 1) span(p.seam, left + 3, right - 3, y);
  }
  // Recover the unmodified deck between the side hull strips, then tint it by vessel.
  ctx.save();
  ctx.beginPath();
  for (const { y, raw } of rows) {
    if (raw) ctx.rect(raw.left, y, raw.right - raw.left, 1);
  }
  ctx.clip();
  ctx.drawImage(stage.base, 0, 0);
  for (const { y, left, right, raw } of rows) {
    if (!raw) continue;
    span(p.deck, raw.left, raw.right, y);
    if (left === raw.left) span("#34282052", left + 5, left + 8, y);
    if (right === raw.right) span("#34282052", right - 8, right - 5, y);
  }
  ctx.restore();

  // Build the gunwale from the water-facing outline; score timber joints and metal pins.
  for (const [i, row] of rows.entries()) {
    const { y, left, right, end, outsideL, outsideR } = row;
    const endCap = i < 5 || i >= rows.length - 6;
    for (const [a, b] of endCap ? [[left - 2, right + 2]] : [[left - 2, left + 4], [right - 4, right + 2]]) {
      let segment = a;
      for (let x = a; x <= b; x++) {
        if (x !== b && !nearOpening(x, y, openings)) continue;
        span(p.dark, segment, x, y);
        span(p.rim, segment, x, y, -1);
        segment = x + 1;
      }
    }
    if (end && !endCap) {
      const insideLeft = left + 4;
      const insideRight = right - 4;
      for (let x = insideLeft; x < insideRight; x++) {
        if (!nearOpening(x, y, openings)) span(y % 5 === 1 ? p.seam : p.dark, x, x + 1, y);
      }
    }
    if (i % 19 === 7 && !endCap) {
      for (const x of [left, right - 1]) {
        if (nearOpening(x, y, openings)) continue;
        box(ctx, p.dark, x - 2, y + 2, 5, 5);
        box(ctx, p.light, x - 2, y, 5, 2);
        box(ctx, p.rim, x - 1, y + 2, 3, 2);
        box(ctx, p.keel, x, y + 3, 1, 1);
      }
      span(p.dark, outsideL + 3, left - 2, y + 4);
      span(p.dark, right + 2, outsideR - 2, y + 4);
    }
  }
}

function drawBridge(ctx, bridge) {
  ctx.save();
  ctx.translate(bridge.x, bridge.y);
  if (bridge.axis === "v") {
    ctx.translate(bridge.w, 0);
    ctx.rotate(Math.PI / 2);
  }
  const length = bridge.axis === "h" ? bridge.w : bridge.h;
  const width = bridge.axis === "h" ? bridge.h : bridge.w;
  const narrowing = bridge.apron ? 16 : 0;

  // Planks run across the gangway. The drop shadow separates it from the hull and sea.
  box(ctx, "#1c2b374e", 1, 5, length - narrowing + 3, width);
  if (narrowing) box(ctx, "#1c2b374e", length - narrowing + 1, 5, narrowing + 2, width - narrowing);
  for (let x = 0; x < length; x++) {
    const board = Math.floor(x / 7);
    const footWidth = narrowing && x > length - 17 ? width - narrowing : width;
    const color = ["#a58c68", "#9e8564", "#b19a75", "#aa906a"][board % 4];
    box(ctx, x % 7 ? color : "#6d5945", x, 2, 1, footWidth - 3);
    if (x % 7 === 2) box(ctx, "#bea583", x, 4, 1, footWidth - 8);
    if (x % 7 === 4) {
      box(ctx, "#826d53", x, 6 + board * 13 % Math.max(1, footWidth - 12), 2, 1);
    }
  }
  box(ctx, "#4c4137", -2, 0, length + 4, 3);
  box(ctx, "#c0a782", 0, 0, length, 1);
  const foot = width - narrowing;
  box(ctx, "#4c4137", -2, width - 3, length - (narrowing ? 14 : -4), 3);
  box(ctx, "#a38b66", 0, width - 3, length - (narrowing ? 16 : 0), 1);
  if (narrowing) {
    box(ctx, "#4c4137", length - 16, foot - 3, 18, 3);
    box(ctx, "#a38b66", length - 16, foot - 3, 16, 1);
    box(ctx, "#4c4137", length - 16, foot, 3, 14);
  }
  for (const x of [0, 5, length - 7, length - 2]) {
    const atEnd = x >= length - 8;
    const bottom = atEnd ? foot - 2 : width - 2;
    box(ctx, "#665442", x, 2, 2, bottom - 3);
    for (const y of [0, bottom - 1]) {
      box(ctx, "#55483a", x - 1, y, 4, 3);
      box(ctx, "#d0b48a", x - 1, y - 1, 4, 1);
      box(ctx, "#685f55", x, y, 1, 1);
    }
  }
  ctx.restore();
}

function drawFastened(ctx, { x, y, w }) {
  for (const start of [x - 14, x + w + 2]) {
    box(ctx, "#44352c", start - 1, y + 2, 13, 14);
    box(ctx, "#9b7856", start, y + 2, 11, 12);
    for (const yy of [4, 7, 10]) box(ctx, "#c1a27b", start + 1, y + yy, 9, 1);
    box(ctx, "#564c43", start + 4, y + 2, 2, 12);
    box(ctx, "#d5ba92", start + 4, y + 1, 2, 2);
  }
}

function drawQuay(ctx) {
  const p = colors.quay;
  const x = PAD + 12 * TILE;
  const y = PAD + 20 * TILE;
  box(ctx, p.shadow, x - 4, y + 32, 4, 48);
  box(ctx, p.side, x - 2, y + 32, 7, 48);
  box(ctx, p.rim, x + 1, y + 32, 3, 48);
  box(ctx, p.light, x + 1, y + 32, 1, 48);
  for (const yy of [y + 39, y + 55, y + 71]) {
    box(ctx, p.dark, x - 4, yy, 7, 7);
    box(ctx, p.light, x - 3, yy, 5, 2);
  }
}

function drawProposal(ctx, stage, open) {
  const bridges = stage.bridges.map((b) => ({ ...pixelBounds(b.bounds), ...b }));
  const active = bridges.filter(b => !b.initially_closed || open);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(stage.base, 0, 0);
  for (const ship of stage.ships) drawHull(ctx, stage, ship, active);
  if (stage.code === "F31") drawQuay(ctx);
  for (const bridge of bridges) {
    if (!bridge.initially_closed || open) drawBridge(ctx, bridge);
    else drawFastened(ctx, bridge);
  }
  ctx.drawImage(stage.foreground, 0, 0);
}
