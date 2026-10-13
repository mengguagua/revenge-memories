#!/usr/bin/env python3
"""Build a lossless 12px Chinese atlas from official Fusion Pixel Font BDF.

Download its BDF release ZIP from https://github.com/TakWolf/fusion-pixel-font/releases
and supply --archive. Glyph bitmaps are copied without scaling or antialiasing.
The game keeps the original FE2 8px ASCII font; this atlas supplies non-ASCII
glyphs except Korean-specific blocks. The upstream font licenses are included.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import zipfile

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026.09.25"
BDF_NAME = "fusion-pixel-12px-monospaced-zh_hans.bdf"
SOURCE_URL = f"https://github.com/TakWolf/fusion-pixel-font/releases/download/{VERSION}/fusion-pixel-font-12px-monospaced-bdf-v{VERSION}.zip"


def parse_bdf(text):
    glyphs = []
    glyph = None
    reading_bitmap = False
    for line in text.splitlines():
        if line.startswith("STARTCHAR "):
            glyph = {"rows": []}
            reading_bitmap = False
        elif line == "ENDCHAR":
            if glyph is not None:
                glyphs.append(glyph)
            glyph = None
            reading_bitmap = False
        elif glyph is not None:
            if line.startswith("ENCODING "):
                glyph["code"] = int(line.split()[1])
            elif line.startswith("DWIDTH "):
                glyph["advance"] = int(line.split()[1])
            elif line.startswith("BBX "):
                glyph["box"] = [int(v) for v in line.split()[1:]]
            elif line == "BITMAP":
                reading_bitmap = True
            elif reading_bitmap:
                glyph["rows"].append(line)
    return glyphs


def include_code(code):
    return code >= 128 and not (0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F or 0xA960 <= code <= 0xA97F or 0xAC00 <= code <= 0xD7FF)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    output = ROOT / "assets/fonts"
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.archive) as archive:
        bdf_data = archive.read(BDF_NAME)
        for name in archive.namelist():
            if name == "OFL.txt" or name.startswith("LICENSES/"):
                path = output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(name))
    source = parse_bdf(bdf_data.decode("utf-8"))
    candidates = [g for g in source if include_code(g["code"])]
    oversized = [g for g in candidates if g["box"][2] < 0 or g["box"][2] + g["box"][0] > 12 or 10 - g["box"][3] - g["box"][1] < 0 or 10 - g["box"][3] > 12]
    excluded_codes = {g["code"] for g in oversized}
    selected = sorted((g for g in candidates if g["code"] not in excluded_codes), key=lambda g: g["code"])
    width = 128 * 12
    height = math.ceil(len(selected) / 128) * 12
    atlas = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    metadata = {}
    for index, glyph in enumerate(selected):
        x = index % 128 * 12
        y = index // 128 * 12
        w, h, dx, dy = glyph["box"]
        top = 10 - dy - h  # Upstream ascent=10, descent=2, cell height=12.
        image = Image.new("RGBA", (12, 12), (255, 255, 255, 0))
        for row_y, row in enumerate(glyph["rows"]):
            bits = len(row) * 4
            value = int(row, 16)
            for row_x in range(w):
                if value & (1 << (bits - 1 - row_x)):
                    px, py = dx + row_x, top + row_y
                    if not (0 <= px < 12 and 0 <= py < 12):
                        raise ValueError(f"Glyph {glyph['code']:04X} exceeds 12px cell")
                    image.putpixel((px, py), (255, 255, 255, 255))
        atlas.paste(image, (x, y))
        alpha_bounds = image.getchannel("A").getbbox()
        ink = [0, 0, 0, 0] if alpha_bounds is None else [alpha_bounds[0], alpha_bounds[1], alpha_bounds[2] - alpha_bounds[0], alpha_bounds[3] - alpha_bounds[1]]
        metadata[chr(glyph["code"])] = {"rect": [x, y, 12, 12], "advance": glyph["advance"], "offset": [0, 0], "ink_bounds": ink}
    image_path = output / "fusion-pixel-12px-zh-hans.png"
    # Two palette entries encode exactly transparent/opaque white. A 1-bit PNG
    # reduces byte size without changing a single visible source pixel.
    palette_atlas = atlas.getchannel("A").point(lambda a: 1 if a else 0).convert("P")
    palette_atlas.putpalette([255, 255, 255, 255, 255, 255] + [0] * 762)
    palette_atlas.save(image_path, optimize=True, bits=1, transparency=0)
    optimizer = shutil.which("oxipng") or "/opt/homebrew/bin/oxipng"
    if Path(optimizer).is_file():
        subprocess.run([optimizer, "-o", "4", "--strip", "safe", str(image_path)], check=True, capture_output=True)
    manifest = {
        "path": "res://assets/fonts/fusion-pixel-12px-zh-hans.png",
        "glyphs": metadata,
        "glyph_height": 12,
        "line_height": 16,
        "baseline": 10,
        "fullwidth_advance": 12,
        "halfwidth_advance": 6,
        "source": "Fusion Pixel Font 12px Monospaced zh_Hans",
        "source_version": VERSION,
        "source_url": SOURCE_URL,
        "source_bdf_sha256": hashlib.sha256(bdf_data).hexdigest(),
        "license": "SIL Open Font License 1.1; see res://assets/fonts/OFL.txt and LICENSES/",
        "texture": {"width": width, "height": height, "bytes": image_path.stat().st_size, "filter": "nearest", "alpha_values": [0, 255]},
        "glyph_count": len(selected),
        "excluded_oversized_glyphs": [f"U+{g['code']:04X}" for g in oversized],
        "notes": "Copied source bits at native 12px with no antialiasing or scaling. Original FE2 font continues to draw ASCII at 8px. One atlas keeps glyph addresses stable and preserves readable Chinese strokes; size is a quality-preserving optimization reference rather than a hard limit.",
    }
    (ROOT / "data/font_zh.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    # An enlarged diagnostic sheet is a preview only, not a runtime asset.
    text = ["格雷　我们会在这里等着，你去问问爷爷吧。", "阿尔姆　卢卡斯　克里夫　托宾　麦森", "攻击　等待　结束回合　继续游戏　返回标题", "索菲亚王国　拉姆村　拉姆森林　第一章"]
    preview = Image.new("RGB", (336, 88), "black")
    for row, line in enumerate(text):
        cursor = 12
        for character in line:
            info = metadata[character]
            rect = info["rect"]
            tile = atlas.crop((rect[0], rect[1], rect[0] + 12, rect[1] + 12))
            preview.paste(tile, (cursor, 12 + row * 16), tile)
            cursor += info["advance"]
    preview_path = output / "font-preview.png"
    preview.resize((1008, 264), Image.Resampling.NEAREST).save(preview_path, optimize=True)
    print(json.dumps({"glyph_count": len(selected), "atlas": str(image_path), "size": [width, height], "bytes": image_path.stat().st_size, "metadata_bytes": (ROOT / "data/font_zh.json").stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
