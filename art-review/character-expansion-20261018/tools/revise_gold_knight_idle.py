#!/usr/bin/env python3
"""Register ImageGen artwork for the review-only allied Golden Knight idle.

The generated standing sprite is the shared registration plate. Only the
foreleg / hind-leg windows are composited from the two generated lift poses.
This prevents generated rider, spear, torso or tail variation from becoming
unwanted whole-character animation. No runtime resources are touched.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'gold-knight-idle-v2-20261020'
OUT = ROOT / REVISION
PALETTE = ['26323b', '4d5559', '7e8584', 'bdc0b9',
           'e0dece', 'b5a273', '817454', 'caac8a']
FRONT = [(31, 62), (46, 62), (46, 64), (55, 64), (55, 84), (31, 84)]
HIND = [(56, 64), (61, 64), (61, 61), (72, 61), (78, 65), (78, 84), (56, 84)]


def mask(points):
    result = Image.new('L', (96, 96))
    ImageDraw.Draw(result).polygon(points, fill=255)
    return result


def registered_plates():
    sheet = Image.open(OUT / 'source/generated-muted-v2.png').convert('RGBA')
    assert sheet.size == (2172, 724)
    colors = [tuple(bytes.fromhex(c)) for c in PALETTE]
    palette = Image.new('P', (1, 1))
    palette.putpalette([v for c in colors + [colors[0]] * 248 for v in c])
    result = []
    for index in range(3):
        cell = sheet.crop((724 * index, 0, 724 * (index + 1), 724))
        cell = cell.resize((90, 90), Image.Resampling.NEAREST)
        alpha = cell.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
        cell = cell.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE).convert('RGBA')
        cell.putalpha(alpha)
        plate = Image.new('RGBA', (96, 96))
        plate.alpha_composite(cell, (3, 2))
        result.append(plate)
    return result


def create():
    (OUT / 'frames').mkdir(exist_ok=True)
    plates = registered_plates()
    front, hind = mask(FRONT), mask(HIND)
    stand = plates[1]
    canonical = [stand.copy(), stand.copy(), stand.copy()]
    canonical[0].paste(plates[0], (0, 0), front)
    canonical[2].paste(plates[2], (0, 0), hind)
    front.save(OUT / 'source/forelegs-mask.png')
    hind.save(OUT / 'source/hindlegs-mask.png')
    # Native aliases are retained; the actual cycle is 0,1,2,1 twice.
    aliases = [0, 1, 2, 1, 0, 1]
    records = []
    for index, pose in enumerate(aliases):
        image = canonical[pose]
        path = OUT / 'frames' / f'idle-{index:03}.png'
        image.save(path, optimize=True)
        records.append({'source_index': index, 'canonical_frame': pose,
                        'path': path.relative_to(ROOT).as_posix(),
                        'size': list(image.size), 'bytes': path.stat().st_size,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    atlas = Image.new('RGBA', (96 * len(aliases), 96))
    for index, pose in enumerate(aliases):
        atlas.alpha_composite(canonical[pose], (96 * index, 0))
    atlas.save(OUT / 'idle-atlas.png', optimize=True)
    (OUT / 'asset-manifest.json').write_text(json.dumps({
        'revision': REVISION, 'generation_mode': 'built-in image_gen edit',
        'runtime_integrated': False, 'palette': PALETTE,
        'fixed_parts': ['rider', 'spear', 'head', 'neck', 'trunk', 'saddle', 'tail'],
        'moving_masks': {'forelegs': FRONT, 'hindlegs': HIND},
        'poses': {'0': 'both forelegs raised; hind legs planted',
                  '1': 'all four legs planted',
                  '2': 'both hind legs raised; forelegs planted'},
        'cycle': [0, 1, 2, 1], 'ticks': [14, 8, 14, 8],
        'frames': records,
    }, ensure_ascii=False, indent=2) + '\n')
    return canonical


if __name__ == '__main__':
    create()
