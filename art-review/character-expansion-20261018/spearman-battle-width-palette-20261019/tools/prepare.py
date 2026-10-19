"""Preserve existing pose pixels; horizontal registration and shared color reduction.

ImageGen supplies the simplification reference, not replacement joints or faces.
Pillow is used only to inspect masks and bounds; ImageMagick performs processing.
"""
from pathlib import Path
from PIL import Image
from collections import deque
import json, subprocess, shutil

V = Path(__file__).resolve().parents[1]
MAG = '/opt/homebrew/bin/magick'
PALS = {
    'ally': ['#18212d', '#2a3b4e', '#51667e', '#96a7b8', '#d8ded8',
             '#493025', '#7d4e2e', '#b17b43', '#cfaa75', '#6a4936',
             '#b87950', '#e4ac77', '#f3d3a0', '#e6d1a9'],
    'enemy': ['#201d27', '#343c48', '#74808c', '#c2c9c7', '#4b1f2e',
              '#893143', '#b95b64', '#422b23', '#7c4a2f', '#b47c46',
              '#c69a64', '#ae6f48', '#e3a672', '#f1cea1']
}
KEYS = {'ally': [12, 4, 5, 0, 1, 2, 3], 'enemy': [19, 10, 11, 6, 7, 8, 9]}

def run(args):
    subprocess.run([MAG, *map(str, args)], check=True)

def pose_bounds(im):
    """Ignore disconnected alpha noise outside all substantial sprite parts."""
    mask = im.convert('RGBA').getchannel('A')
    points = {(x, y) for y in range(im.height) for x in range(im.width)
              if mask.getpixel((x, y)) >= 128}
    all_points = set(points)
    retained = set()
    while points:
        first = points.pop()
        group = {first}
        queue = deque([first])
        while queue:
            x, y = queue.popleft()
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    p = (x + dx, y + dy)
                    if p in points:
                        points.remove(p); group.add(p); queue.append(p)
        if len(group) >= 20:
            retained.update(group)
    xs, ys = zip(*retained)
    box = [min(xs), min(ys), max(xs) + 1, max(ys) + 1]
    outside = sum(not (box[0] <= x < box[2] and box[1] <= y < box[3])
                  for x, y in all_points)
    return box, outside

records = []
for side, keys in KEYS.items():
    out = V / 'deliverables' / side; out.mkdir(exist_ok=True)
    mapping = json.loads((V / f'reference/{side}-mapping-before.json').read_text())
    palette = V / f'source/working/{side}-palette.png'
    run(['-size', '1x1', 'xc:none', *['xc:' + c for c in PALS[side]], '+append', palette])
    for k in keys:
        previous = V / f'reference/{side}-{k}.png'
        im = Image.open(previous).convert('RGBA')
        box, ignored = pose_bounds(im)
        x0, y0, x1, y1 = box
        w, h = round((x1 - x0) * 1.08), y1 - y0
        tmp = V / f'source/working/{side}-{k}.png'
        run([previous, '-channel', 'A', '-threshold', '50%', '+channel',
             '-crop', f'{x1-x0}x{h}+{x0}+{y0}', '+repage',
             '-filter', 'point', '-resize', f'{w}x{h}!', '+dither', '-remap', palette, tmp])
        original = next(x for x in mapping['records'] if int(x['source_frame']) == k)
        target = original.get('target_foot_anchor', original.get('visible_sole_anchor'))
        # Use each original's documented sole ROI; never register by spear extent.
        native_roi = original.get('output_foot_roi')
        if native_roi:
            ry0 = native_roi[1] - y0
        else:
            ry0 = h - 10
        feet = Image.open(tmp).convert('RGBA').getchannel('A').crop((0, ry0, w, h)).getbbox()
        center = (feet[0] + feet[2]) / 2
        offset = [round(target[0] - center), target[1] - h]
        frame = out / f'frame-{k:03d}.png'
        run(['-size', '320x256', 'xc:none', tmp, '-geometry',
             f'+{offset[0]}+{offset[1]}', '-composite', 'PNG32:' + str(frame)])
        records.append({'side': side, 'source_frame': k, 'representative_frame': k,
                        'kind': 'existing_pose_width_and_palette', 'previous_bounds': box,
                        'ignored_disconnected_outer_pixels': ignored,
                        'target_size': [w, h], 'width_factor': w/(x1-x0),
                        'height_preserved': True, 'target_foot_anchor': target,
                        'registered_foot_anchor': [offset[0]+center, target[1]],
                        'foot_measurement_top': ry0 + offset[1],
                        'registration_offset': offset, 'shared_character_palette': PALS[side]})
    alias = 12 if side == 'ally' else 19
    shutil.copyfile(out / f'frame-{alias:03d}.png', out / 'frame-023.png')
    run([*[out / f'frame-{k:03d}.png' for k in sorted(keys)], '+append', out / 'battle-atlas.png'])

subprocess.run(['/opt/homebrew/bin/oxipng', '-q', '-o', '3',
                *map(str, (V / 'deliverables').rglob('*.png'))], check=True)
(V / 'registration.json').write_text(json.dumps({'revision': V.name,
    'records': records, 'palettes': PALS,
    'method': 'Registered horizontal resize and fixed-palette remapping of original pose pixels. Generated sheet retained only as a simplification reference.'},
    ensure_ascii=False, indent=2) + '\n')

for side, keys in KEYS.items():
    for bg_name, bg in [('dark', '#202d35'), ('light', '#dcded8')]:
        cmd = ['-size', '2048x1536', 'xc:' + bg]
        for i, k in enumerate(keys):
            for row, p in enumerate([V / f'reference/{side}-{k}.png',
                                     V / f'deliverables/{side}/frame-{k:03d}.png']):
                cmd += ['(', p, '-filter', 'point', '-resize', '480x384!', ')',
                        '-geometry', f'+{16+(i%4)*512}+{(i//4)*768+row*384}', '-composite']
        run([*cmd, V / f'reviews/{side}-previous-and-new-{bg_name}.png'])
for bg_name, bg in [('dark', '#202d35'), ('light', '#dcded8')]:
    cmd = ['-size', '1024x320', 'xc:' + bg]
    for i, side in enumerate(['ally', 'enemy']):
        k = KEYS[side][0]
        cmd += ['(', V / f'deliverables/{side}/frame-{k:03d}.png',
                '-filter', 'point', '-resize', '640x512!', ')',
                '-geometry', f'+{i*512-80}-208', '-composite']
    run([*cmd, V / f'reviews/factions-{bg_name}.png'])
print('Prepared fourteen poses plus two exact idle aliases, using fixed 14-color faction palettes.')
