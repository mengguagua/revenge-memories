#!/usr/bin/env python3
"""Copy upstream native 8px glyphs, without scaling the 12px dialogue font."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VERSION = '2026.09.25'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('font_builder', ROOT.parent / 'tools/build_chinese_font.py')
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    with zipfile.ZipFile(args.archive) as archive:
        raw = archive.read('fusion-pixel-8px-monospaced-zh_hans.bdf')
        # This smaller size has additional upstream contributors.
        for name in archive.namelist():
            if name == 'OFL.txt' or name.startswith('LICENSES/'):
                path = ROOT / 'assets/fonts' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(name))
    glyphs = [g for g in source.parse_bdf(raw.decode()) if g['code'] >= 32 and not 0xAC00 <= g['code'] <= 0xD7AF]
    atlas = Image.new('P', (1024, math.ceil(len(glyphs) / 128) * 8), 0)
    atlas.putpalette([255, 255, 255] * 256)
    mapping = {}
    for index, glyph in enumerate(glyphs):
        x, y = index % 128 * 8, index // 128 * 8
        w, h, dx, dy = glyph['box']
        top = 7 - dy - h
        if dx < 0 or dx + w > 8 or top < 0 or top + h > 8:
            continue
        for row_y, row in enumerate(glyph['rows']):
            value, bits = int(row, 16), len(row) * 4
            for row_x in range(w):
                if value & (1 << (bits - 1 - row_x)):
                    atlas.putpixel((x + dx + row_x, y + top + row_y), 1)
        mapping[chr(glyph['code'])] = {'rect': [x, y, 8, 8], 'advance': glyph['advance']}
    output = ROOT / 'assets/fonts/fusion-pixel-8px-zh-hans.png'
    atlas.save(output, bits=1, transparency=0, optimize=True)
    subprocess.run(['/opt/homebrew/bin/oxipng', '-o', '4', '--strip', 'safe', str(output)], check=True, capture_output=True)
    manifest = {'path': 'res://assets/fonts/' + output.name, 'source': 'Fusion Pixel Font 8px monospaced zh_Hans',
                'version': VERSION, 'bdf_sha256': hashlib.sha256(raw).hexdigest(), 'size': list(atlas.size),
                'bytes': output.stat().st_size, 'pixel_policy': 'Native BDF bits; no resampling; binary alpha', 'glyphs': mapping}
    (ROOT / 'data/legacy/font_small_zh.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')))
    print(json.dumps({k: v for k, v in manifest.items() if k != 'glyphs'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
