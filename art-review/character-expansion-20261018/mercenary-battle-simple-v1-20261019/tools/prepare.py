"""Simplify outfit colors while retaining existing pose/alpha and sword effects."""
from pathlib import Path
from PIL import Image
import json, subprocess, shutil

V = Path(__file__).resolve().parents[1]; R = V.parent
MAG = '/opt/homebrew/bin/magick'
PALS = {
    'ally': ['#1b1e2a', '#35333c', '#342331', '#5d3649', '#8b5967',
             '#4b3128', '#885737', '#90754c', '#b3975f', '#e7d4a7',
             '#596776', '#c3cbd0', '#bf825b', '#efbf90'],
    'enemy': ['#1c2135', '#343552', '#5c5d95', '#8b86bf', '#737a9b',
              '#bcc0d6', '#49362c', '#8a6041', '#b29674', '#6d625b',
              '#c08c62', '#efbd8b', '#f2d3a4', '#e4dcca']
}
KEYS = [0, 1, 2, 3, 4, 5, 7, 16]
# Explicit, reviewed sword segments in native output coordinates. The masks
# protect source steel/edges; they are not new art or inferred joints.
BLADES = {
    'ally': {0: [132, 242, 173, 198], 1: [134, 246, 170, 202],
             2: [183, 117, 184, 172], 3: [129, 111, 178, 143],
             4: [120, 99, 164, 131], 5: [216, 96, 177, 133],
             7: [135, 242, 176, 202], 16: [174, 38, 174, 142]},
    'enemy': {0: [128, 240, 173, 198], 1: [134, 246, 170, 202],
              2: [171, 104, 173, 170], 3: [128, 99, 175, 129],
              4: [125, 99, 164, 132], 5: [214, 97, 178, 133],
              7: [135, 242, 176, 202], 16: [174, 26, 174, 142]}
}
def run(args):
    subprocess.run([MAG, *map(str, args)], check=True)

records = []
for side in ['ally', 'enemy']:
    out = V / 'deliverables' / side
    palette = V / f'source/working/{side}-palette.png'
    # Opaque color table; alpha is reattached byte-for-byte after RGB remapping.
    run([*['xc:' + c for c in PALS[side]], '+append', palette])
    for k in KEYS:
        src = V / f'reference/{side}-{k:03d}.png'
        alpha = V / f'source/working/{side}-{k}-alpha.png'
        recolor = V / f'source/working/{side}-{k}-recolor.png'
        mask = V / f'source/working/{side}-{k}-blade-mask.png'
        protected = V / f'source/working/{side}-{k}-protected.png'
        frame = out / f'frame-{k:03d}.png'
        run([src, '-alpha', 'extract', alpha])
        hue = '.08' if side == 'ally' else '.675'
        treatment = []
        if side == 'enemy':
            treatment = ['-channel', 'B', '-fx',
                '((u.r>.13)&&(u.r<.45)&&(u.g>.12)) ? min(.72,.12+u.b*1.1) : (((u.g<.18)&&(u.b>.08)&&(u.b<.4)) ? .08+u.b*.9 : u.b)',
                '+channel']
        run([src, '-alpha', 'off', '-colorspace', 'HSL', *treatment, '-channel', 'R',
             '-fx', f'((u.r>.13)&&(u.r<.45)&&(u.g>.12)) ? {hue} : u.r',
             '+channel', '-colorspace', 'sRGB', '+dither', '-remap', palette,
             alpha, '-compose', 'CopyOpacity', '-composite', 'PNG32:' + str(recolor)])
        x0, y0, x1, y1 = BLADES[side][k]
        run(['-size', '320x256', 'xc:black', '+antialias', '-stroke', 'white',
             '-strokewidth', '12', '-fill', 'none', '-draw',
             f'line {x0},{y0} {x1},{y1}', mask])
        # RGB replacement mask does not touch alpha. Original blade pixels remain
        # original even along partially transparent edges.
        run([src, '-alpha', 'off', mask, '-compose', 'CopyOpacity', '-composite', protected])
        run([recolor, protected, '-compose', 'Over', '-composite', alpha,
             '-compose', 'CopyOpacity', '-composite', 'PNG32:' + str(frame)])
        records.append({'side': side, 'source_frame': k,
                        'kind': 'existing_pose_outfit_palette_simplification',
                        'shared_body_palette': PALS[side],
                        'protected_blade_segment': BLADES[side][k],
                        'blade_mask': str(mask.relative_to(V)),
                        'alpha_preserved': True, 'no_resizing_or_translation': True})

    # Source frame 6 is precisely source7 shifted -4px plus an isolated original
    # slash layer. Retain the same proven composition with the revised body7.
    arc = V / f'reference/{side}-slash-006.png'
    run(['-size', '320x256', 'xc:none', out / 'frame-007.png', '-geometry', '-4+0',
         '-compose', 'Over', '-composite', arc, '-geometry', '+0+0',
         '-compose', 'Over', '-composite', 'PNG32:' + str(out / 'frame-006.png')])
    if side == 'ally':
        for k in [8, 15]:
            shutil.copyfile(out / 'frame-000.png', out / f'frame-{k:03d}.png')
    else:
        run(['-size', '320x256', 'xc:none', out / 'frame-000.png',
             '-geometry', '-64+0', '-composite', 'PNG32:' + str(out / 'frame-008.png')])
        shutil.copyfile(out / 'frame-008.png', out / 'frame-015.png')
    run([*[out / f'frame-{k:03d}.png' for k in [0, 1, 2, 3, 4, 5, 6, 7, 16]],
         '+append', out / 'battle-atlas.png'])

subprocess.run(['/opt/homebrew/bin/oxipng', '-q', '-o', '3',
                *map(str, (V / 'deliverables').rglob('*.png'))], check=True)
(V / 'registration.json').write_text(json.dumps({'revision': V.name, 'palettes': PALS,
    'records': records, 'method': 'Original pixels/alpha retained, fixed clothing palettes; original blade and slash layers protected. No width or height changes.'},
    ensure_ascii=False, indent=2) + '\n')

for side in ['ally', 'enemy']:
    for name, bg in [('dark', '#202d35'), ('light', '#dcded8')]:
        cmd = ['-size', '1536x2304', 'xc:' + bg]
        for i, k in enumerate([0, 1, 2, 3, 4, 5, 6, 7, 16]):
            for row, p in enumerate([V / f'reference/{side}-{k:03d}.png',
                                     V / f'deliverables/{side}/frame-{k:03d}.png']):
                cmd += ['(', p, '-filter', 'point', '-resize', '480x384!', ')',
                        '-geometry', f'+{16+i%3*512}+{(i//3)*768+row*384}', '-composite']
        run([*cmd, V / f'reviews/{side}-previous-and-new-{name}.png'])
for name, bg in [('dark', '#202d35'), ('light', '#dcded8')]:
    cmd = ['-size', '1024x320', 'xc:' + bg]
    for i, side in enumerate(['ally', 'enemy']):
        # Common pose0 placement centers the bodies, including the angled blade.
        cmd += ['(', V / f'deliverables/{side}/frame-000.png',
                '-filter', 'point', '-resize', '640x512!', ')',
                '-geometry', f'{i*512-148:+d}-208', '-composite']
    run([*cmd, V / f'reviews/factions-{name}.png'])
print('Prepared both mercenary palettes, protected swords, original slash layers and aliases.')
