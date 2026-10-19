"""Faction color correction, without changing any pose or alpha pixel."""
from pathlib import Path
from PIL import Image
import json, shutil, subprocess

V = Path(__file__).resolve().parents[1]; R = V.parent
MAG = '/opt/homebrew/bin/magick'
COLOR_MAP = {
    '#201d27': '#1c2135',  # Restrained cool outline.
    '#343c48': '#343552',  # Dark metal, bracers and boots.
    '#74808c': '#737a9b',  # Muted cool metal, also the spearhead.
    '#c2c9c7': '#bcc0d6',  # Pale cold metal remains distinct from clothing.
    '#4b1f2e': '#343552',  # Three burgundy cloth shades -> faction colors.
    '#893143': '#5c5d95',
    '#b95b64': '#8b86bf'
}
def run(args):
    subprocess.run([MAG, *map(str, args)], check=True)

mapping = json.loads((V / 'reference/mapping-before.json').read_text())
records = []
for k in mapping['canonical_frames']:
    src = V / f'reference/frame-{k:03d}.png'
    dst = V / f'deliverables/enemy/frame-{k:03d}.png'
    cmd = [src]
    for old, new in COLOR_MAP.items():
        cmd += ['-fill', new, '-opaque', old]
    run([*cmd, 'PNG32:' + str(dst)])
    record = next(x for x in mapping['records'] if x['source_frame'] == k)
    records.append({'source_frame': k, 'target_foot_anchor': record['target_foot_anchor'],
                    'foot_measurement_top': record['foot_measurement_top'],
                    'width_factor': record['width_factor'],
                    'previous_bounds': list(Image.open(src).convert('RGBA').getbbox()),
                    'previous_palette': record['shared_character_palette'],
                    'shared_character_palette': list(dict.fromkeys(
                        COLOR_MAP.get(c, c) for c in record['shared_character_palette']))})
out = V / 'deliverables/enemy'
shutil.copyfile(out / 'frame-019.png', out / 'frame-023.png')
run([*[out / f'frame-{k:03d}.png' for k in sorted(mapping['canonical_frames'])],
     '+append', out / 'battle-atlas.png'])
subprocess.run(['/opt/homebrew/bin/oxipng', '-q', '-o', '3',
                *map(str, out.glob('*.png'))], check=True)
(V / 'registration.json').write_text(json.dumps({'revision': V.name,
    'color_map': COLOR_MAP, 'records': records,
    'method': 'Exact color replacement only; RGBA alpha and pixel coordinates are preserved.'},
    ensure_ascii=False, indent=2) + '\n')

for name, bg in [('dark', '#202d35'), ('light', '#dcded8')]:
    cmd = ['-size', '2048x1536', 'xc:' + bg]
    for i, k in enumerate([19, 10, 11, 6, 7, 8, 9]):
        for row, p in enumerate([V / f'reference/frame-{k:03d}.png',
                                 out / f'frame-{k:03d}.png']):
            cmd += ['(', p, '-filter', 'point', '-resize', '480x384!', ')',
                    '-geometry', f'+{16+(i%4)*512}+{(i//4)*768+row*384}', '-composite']
    run([*cmd, V / f'reviews/previous-and-new-{name}.png'])
    # Left: current ally, center: revised spearman, right: accepted enemy archer.
    cmd = ['-size', '1536x432', 'xc:' + bg]
    refs = [R / 'spearman-battle-width-palette-20261019/deliverables/ally/frame-012.png',
            out / 'frame-019.png',
            R / 'archer-battle-light-armor-v3-20261019/deliverables/enemy/frame-001.png']
    for i, p in enumerate(refs):
        x_offset = [-137, -7, -33][i]
        cmd += ['(', p, '-filter', 'point', '-resize', '640x512!', ')',
                '-geometry', f'{i*512+x_offset:+d}-112', '-composite']
    run([*cmd, V / f'reviews/faction-standard-{name}.png'])
    cmd = ['-size', '1024x320', 'xc:' + bg]
    for i, p in enumerate([V / 'reference/frame-019.png', out / 'frame-019.png']):
        cmd += ['(', p, '-filter', 'point', '-resize', '640x512!', ')',
                '-geometry', f'{i*512-7:+d}-208', '-composite']
    run([*cmd, V / f'reviews/idle-before-after-{name}.png'])
print('Seven enemy poses recolored; geometry, alpha and warm skin/hair palette preserved.')
