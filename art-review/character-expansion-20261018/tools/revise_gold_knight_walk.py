#!/usr/bin/env python3
"""Register review-only upward gallop; unify map-walk palette and shadow.

Art is generated with image_gen. This script performs native-size registration,
palette normalization and layer compositing. It never writes game resources.
"""
from pathlib import Path
import colorsys
import hashlib
import json
import shutil
from PIL import Image
from revise_gold_knight_idle import ROOT, PALETTE

REVISION = 'gold-knight-walk-v3-20261020'
OUT = ROOT / REVISION
OLD = ROOT / 'professions/class-7-ally/maps/sol-frames'
FLOOR = 92
BOB = 4
BODY_CUT = 70


def quantize(image, old_gold=False):
    image = image.convert('RGBA')
    alpha = image.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    colors = [tuple(bytes.fromhex(c)) for c in PALETTE]
    palette = Image.new('P', (1, 1))
    palette.putpalette([v for c in colors + [colors[0]] * 248 for v in c])
    rgb = image.convert('RGB')
    if old_gold:
        pixels = []
        for color in rgb.getdata():
            h, s, v = colorsys.rgb_to_hsv(*(c/255 for c in color))
            # Keep the old clothing regions and their silhouette, but remove
            # vivid yellow / orange and blue cloth from the previous palette.
            if .095 <= h <= .21 and s > .28:
                color = colors[5] if v >= .57 else colors[6]
            elif .43 <= h <= .75 and s > .25:
                color = colors[1] if v > .42 else colors[0]
            pixels.append(color)
        rgb.putdata(pixels)
    result = rgb.quantize(palette=palette, dither=Image.Dither.NONE).convert('RGBA')
    result.putalpha(alpha)
    return result


def up_frames():
    sheet = Image.open(OUT / 'source/generated-up-v1.png').convert('RGBA')
    assert sheet.size == (2048, 768)
    plates = []
    # Measured helmet/torso centerlines in the two generated cells. Each cell
    # receives the same horizontal transform; no frame-by-frame bbox centering.
    for index, axis in enumerate([627, 399]):
        cell = sheet.crop((1024*index, 0, 1024*(index+1), 768))
        body = cell.crop((axis-160, 112, axis+160, 706))
        body = quantize(body.resize((44, 84), Image.Resampling.NEAREST))
        plate = Image.new('RGBA', (128, 96))
        plate.alpha_composite(body, (42, 9))
        plates.append(plate)
    # Reuse one upper body so the helmet, shoulders, spear, tail and rump have
    # no lateral drift. Frame 1 lowers that body by one original pixel (4 here).
    funnel = plates[0]
    straight = Image.new('RGBA', (128, 96))
    straight.alpha_composite(funnel.crop((0, 0, 128, BODY_CUT)), (0, BOB))
    # Register the upright lower legs to the SAME ground row. This is a planted
    # two-phase gallop, never alternating one raised hoof and one planted hoof.
    legs = plates[1].crop((0, BODY_CUT, 128, FLOOR+1))
    legs = legs.resize((128, FLOOR+1-BODY_CUT-BOB), Image.Resampling.NEAREST)
    straight.alpha_composite(legs, (0, BODY_CUT+BOB))
    return [funnel, straight]


def create():
    (OUT / 'frames').mkdir(exist_ok=True)
    frames = up_frames()
    for index in range(2, 8):
        frames.append(quantize(Image.open(OLD / f'frame-{index:03}.png'), old_gold=True))
    records = []
    atlas = Image.new('RGBA', (128*8, 96))
    for index, image in enumerate(frames):
        path = OUT / 'frames' / f'frame-{index:03}.png'
        image.save(path, optimize=True)
        atlas.alpha_composite(image, (128*index, 0))
        records.append({'source_index': index, 'path': path.relative_to(ROOT).as_posix(),
                        'size': list(image.size), 'bytes': path.stat().st_size,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    atlas.save(OUT / 'walk-atlas.png', optimize=True)
    shutil.copyfile(ROOT / 'hunapu-story-shadow-20261018/story-shadow.png', OUT / 'ground-shadow.png')
    manifest = {'revision': REVISION, 'runtime_integrated': False,
                'generation_mode': 'built-in image_gen edit', 'palette': PALETTE,
                'up_cycle': ['four upper legs converge to overlapping lower legs',
                             'two separated upright planted legs'],
                'body_centerline': 64, 'body_vertical_bob': BOB, 'hoof_floor_row': FLOOR,
                'shared_upper_body_rows': [0, BODY_CUT],
                'other_directions': 'palette only; existing silhouettes and two-pose motion retained',
                'shadow': {'path': (OUT/'ground-shadow.png').relative_to(ROOT).as_posix(),
                           'size': [12, 3], 'offset': [0, -1], 'alpha': .42,
                           'source': 'reused accepted continuous protagonist story shadow'},
                'frames': records}
    (OUT / 'asset-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    return frames


if __name__ == '__main__':
    create()
