import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const out = dirname(fileURLToPath(import.meta.url));
const repo = resolve(out, "../..");
const capture = resolve(process.argv[2] ?? "/private/tmp/ship-review-capture-20261109");
const chrome = process.env.SHIP_REVIEW_CHROME ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const specifications = {
  F21: [["cedar", 18, 8, 5, 12], ["navy", 22, 10, 6, 15]],
  F22: [["cedar", 17, 8, 5, 11], ["navy", 24, 11, 7, 17]],
  S21: [["fishing", 16, 7, 5, 10], ["tender", 17, 7, 5, 11]],
  F31: [["cedar", 17, 9, 5, 11]]
};
const review = [];
for (const [code, palettes] of Object.entries(specifications)) {
  const source = readFileSync(join(repo, "actual/data/stages", code + ".json"));
  const stage = JSON.parse(source);
  const zones = stage.deck_zones ?? [{ bounds: [1, 14, 7, 24] }];
  const ships = zones.map(({ bounds }, i) => {
    const [palette, prow, stern, port, starboard] = palettes[i];
    return { bounds, palette, prow, stern, port, starboard };
  });
  const connections = stage.boarding_connections ?? [{ bounds: [8, 20, 11, 22], axis: "h", apron: true }];
  const bridges = connections.map((b) => {
    if (b.axis === "v" && stage.visual_ground[b.bounds[3]][b.bounds[0]] === "p") {
      const [x0, y0, x1, y1] = b.bounds;
      return { ...b, bounds: [x0, y0, x1, y1 - 1] };
    }
    return b;
  });
  const variants = code === "F22" ? ["normal", "open"] : ["normal"];
  for (const variant of variants) {
    for (const bridge of bridges) {
      const [x0, y0, x1, y1] = bridge.bounds;
      for (let y = y0; y <= y1; y++) {
        for (let x = x0; x <= x1; x++) {
          if (bridge.apron && x === x1 && y === y1) continue;
          const want = bridge.initially_closed ? "~" : "s";
          if (stage.visual_ground[y][x] !== want) throw new Error(`${code} gangway at ${x},${y} is not ${want}`);
        }
      }
    }
    review.push({
      code, variant, ships, bridges, ground: stage.visual_ground,
      width: stage.map.width * 16 + 64, height: stage.map.height * 16 + 64,
      sourceHash: createHash("sha256").update(source).digest("hex")
    });
  }
}

const sheet = join(capture, "compose.html");
const source = readFileSync(join(out, "draw.js"), "utf8");
writeFileSync(sheet, `<!doctype html><meta charset="utf-8"><pre id="result"></pre><script>
${source}
const jobs = ${JSON.stringify(review)};
function load(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error(src));
    image.src = src;
  });
}
(async () => {
  const results = [];
  for (const stage of jobs) {
    const open = stage.variant === "open";
    [stage.base, stage.foreground] = await Promise.all([
      load(stage.code + "-base.png"),
      load(stage.code + "-foreground" + (open ? "-open" : "") + ".png")
    ]);
    const canvas = document.createElement("canvas");
    canvas.width = stage.width;
    canvas.height = stage.height;
    drawProposal(canvas.getContext("2d"), stage, open);
    results.push(canvas.toDataURL("image/png").split(",")[1]);
  }
  document.querySelector("#result").textContent = JSON.stringify(results);
})().catch(error => { document.querySelector("#result").textContent = "error: " + error; });
</script>`);

const dom = execFileSync(chrome, [
  "--headless", "--no-first-run", "--disable-gpu",
  "--user-data-dir=" + join(capture, "chrome-compose"), "--allow-file-access-from-files",
  "--virtual-time-budget=10000", "--dump-dom", pathToFileURL(sheet).href
], { encoding: "utf8", maxBuffer: 8_000_000, stdio: ["ignore", "pipe", "ignore"] });
const results = JSON.parse(dom.match(/<pre id="result">(.*?)<\/pre>/s)?.[1] ?? "null");
if (!results || results.length !== review.length) throw new Error("Incomplete headless art render");
const images = join(out, "images");
mkdirSync(images, { recursive: true });

const magick = process.env.SHIP_REVIEW_MAGICK ?? "/opt/homebrew/bin/magick";
for (const [i, item] of review.entries()) {
  const { code, variant } = item;
  const suffix = variant === "open" ? "-open" : "";
  const before = join(capture, code + "-full" + suffix + ".png");
  const after = join(capture, code + "-proposal" + suffix + ".png");
  writeFileSync(after, Buffer.from(results[i], "base64"));
  item.images = [];
  for (const [name, png] of [["before", before], ["after", after]]) {
    const file = code + "-" + name + suffix + ".webp";
    const webp = join(images, file);
    execFileSync(magick, [png, "-strip", "-define", "webp:lossless=true", "-quality", "100", webp]);
    const sourcePixels = execFileSync(magick, [png, "-depth", "8", "RGBA:-"], { maxBuffer: 2_000_000 });
    const outputPixels = execFileSync(magick, [webp, "-depth", "8", "RGBA:-"], { maxBuffer: 2_000_000 });
    if (!sourcePixels.equals(outputPixels)) throw new Error("Pixel mismatch " + file);
    item.images.push({ file, bytes: statSync(webp).size });
  }
}
writeFileSync(join(out, "source-manifest.json"), JSON.stringify(review.map(({ ground, ...item }) => item), null, 2) + "\n");
