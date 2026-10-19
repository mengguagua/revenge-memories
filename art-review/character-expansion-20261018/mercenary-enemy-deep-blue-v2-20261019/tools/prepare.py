"""Equipment-only color substitution; preserve current pose, head and sword."""
from pathlib import Path
from PIL import Image
import json, subprocess, shutil

V = Path(__file__).resolve().parents[1]; R = V.parent
MAG = '/opt/homebrew/bin/magick'
KEYS = [0, 1, 2, 3, 4, 5, 7, 16]
COLORS = {'#49362c': '#26334f', '#8a6041': '#3e5074', '#b29674': '#5a6b8f',
          '#6d625b': '#26334f', '#737a9b': '#3e5074', '#bcc0d6': '#5a6b8f',
          '#e4dcca': '#5a6b8f'}
BLADES = {0: [128, 242, 173, 198], 1: [129, 243, 174, 199],
          2: [171, 106, 172, 166], 3: [137, 98, 188, 129],
          4: [125, 99, 182, 136], 5: [219, 96, 180, 132],
          7: [131, 241, 174, 198], 16: [107, 24, 107, 137]}
heads = json.loads((V / 'reference/head-regions.json').read_text())
def run(args):
    subprocess.run([MAG, *map(str, args)], check=True)

records = []; out = V / 'deliverables/enemy'
for k in KEYS:
    src = V / f'reference/frame-{k:03d}.png'
    temp = V / f'source/working/recolor-{k}.png'
    head = V / f'source/working/head-mask-{k}.png'
    blade = V / f'source/working/blade-mask-{k}.png'
    mask = V / f'source/working/protection-{k}.png'
    saved = V / f'source/working/protected-{k}.png'
    alpha = V / f'source/working/alpha-{k}.png'
    cmd = [src, '-alpha', 'off']
    for old, new in COLORS.items():
        cmd += ['-fill', new, '-opaque', old]
    run([*cmd, temp])
    a, b, c, d = heads[str(k)]['face_component']
    # Protect the hair above/behind the face while excluding the lower-right
    # shoulder plate. Regions are reviewed per pose, not a shared height band.
    points = [(a-8, b-18), (c+12, b-18), (c+12, b-2), (c+2, d), (a-4, d)]
    polygon = 'polygon ' + ' '.join(f'{x},{y}' for x, y in points)
    run(['-size', '320x256', 'xc:black', '+antialias', '-fill', 'white',
         '-stroke', 'none', '-draw', polygon, head])
    x0, y0, x1, y1 = BLADES[k]
    run(['-size', '320x256', 'xc:black', '+antialias', '-fill', 'none',
         '-stroke', 'white', '-strokewidth', '12', '-draw',
         f'line {x0},{y0} {x1},{y1}', blade])
    run([head, blade, '-compose', 'Lighten', '-composite', mask])
    run([src, '-alpha', 'off', mask, '-compose', 'CopyOpacity', '-composite', saved])
    run([src, '-alpha', 'extract', alpha])
    run([temp, saved, '-compose', 'Over', '-composite', alpha,
         '-compose', 'CopyOpacity', '-composite', '-strip',
         'PNG32:' + str(out / f'frame-{k:03d}.png')])
    records.append({'source_frame': k, 'head_polygon': points, 'blade_segment': BLADES[k],
                    'protection_mask': str(mask.relative_to(V)),
                    'alpha_and_pixel_coordinates_preserved': True})
run(['-size', '320x256', 'xc:none', out / 'frame-007.png', '-geometry', '-4+0',
     '-composite', V / 'reference/slash-006.png', '-geometry', '+0+0',
     '-composite', '-strip', 'PNG32:' + str(out / 'frame-006.png')])
run(['-size', '320x256', 'xc:none', out / 'frame-000.png', '-geometry', '-64+0',
     '-composite', '-strip', 'PNG32:' + str(out / 'frame-008.png')])
shutil.copyfile(out / 'frame-008.png', out / 'frame-015.png')
run([*[out / f'frame-{k:03d}.png' for k in [0, 1, 2, 3, 4, 5, 6, 7, 16]],
     '+append', '-strip', out / 'battle-atlas.png'])
subprocess.run(['/opt/homebrew/bin/oxipng', '-q', '-o', '3',
                *map(str, out.glob('*.png'))], check=True)
(V / 'registration.json').write_text(json.dumps({'revision': V.name, 'color_map': COLORS,
    'equipment_palette': ['#26334f', '#3e5074', '#5a6b8f'], 'records': records,
    'method': 'Exact color mapping outside per-pose head and sword protection. No resampling.'},
    ensure_ascii=False, indent=2) + '\n')

for name, bg in [('dark', '#202d35'), ('light', '#dcded8')]:
    cmd = ['-size', '1024x320', 'xc:' + bg]
    for i, p in enumerate([V / 'reference/frame-000.png', out / 'frame-000.png']):
        cmd += ['(', p, '-filter', 'point', '-resize', '640x512!', ')',
                '-geometry', f'{i*512-148:+d}-208', '-composite']
    run([*cmd, V / f'reviews/idle-before-after-{name}.png'])
    cmd = ['-size', '1536x2304', 'xc:' + bg]
    for i, k in enumerate([0, 1, 2, 3, 4, 5, 6, 7, 16]):
        for row, p in enumerate([V / f'reference/frame-{k:03d}.png', out / f'frame-{k:03d}.png']):
            cmd += ['(', p, '-filter', 'point', '-resize', '480x384!', ')',
                    '-geometry', f'+{16+i%3*512}+{(i//3)*768+row*384}', '-composite']
    run([*cmd, V / f'reviews/previous-and-new-{name}.png'])
print('Deep-blue equipment prepared; face/hair, skin tones, blades and alpha protected.')
