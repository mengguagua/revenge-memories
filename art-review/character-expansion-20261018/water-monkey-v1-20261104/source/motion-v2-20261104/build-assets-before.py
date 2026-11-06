"""Slice generated atlases with ImageMagick; Pillow only measures source alpha.

All outputs stay inside this art-review folder. No game resources are modified.
"""
from pathlib import Path
import json
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parent
MAGICK = '/opt/homebrew/bin/magick'
inventory = []
frames = {'battle': [], 'maps': [], 'effects': [], 'concept': [], 'battle-broken': [], 'maps-broken': []}

def run(*args):
    subprocess.run([MAGICK, *map(str, args)], check=True, capture_output=True)

def sheet(name, columns, rows, category, factor, canvas, baseline):
    source = ROOT / 'source' / name
    im = Image.open(source)
    for i in range(columns * rows):
        col, row = i % columns, i // columns
        x0, x1 = round(col * im.width / columns), round((col + 1) * im.width / columns)
        y0, y1 = round(row * im.height / rows), round((row + 1) * im.height / rows)
        alpha = im.getchannel('A').crop((x0, y0, x1, y1))
        bbox = alpha.point(lambda v: 255 if v >= 128 else 0).getbbox()
        assert bbox, (name, i)
        l, t, r, b = bbox
        w, h = max(1, round((r-l) * factor)), max(1, round((b-t) * factor))
        kind = 'effects' if category == 'battle' and row == 4 else category
        index = i - 16 if kind == 'effects' else i
        target = ROOT / 'assets' / f'{kind}-{index:02d}.png'
        cw, ch = canvas
        if kind == 'effects':
            cw, ch = 96, 96
            left, top = (cw-w)//2, (ch-h)//2
        else:
            left, top = (cw-w)//2, baseline-h
        assert left >= 2 and top >= 2 and left+w <= cw-2 and top+h <= ch-2, (name, i, bbox, w, h)
        # Remove only very low-alpha generation haze, retaining opaque contour.
        run(source, '-crop', f'{x1-x0}x{y1-y0}+{x0}+{y0}', '+repage',
            '-channel', 'A', '-threshold', '50%', '+channel',
            '-crop', f'{r-l}x{b-t}+{l}+{t}', '+repage',
            '-filter', 'point', '-resize', f'{w}x{h}!',
            '-background', 'none', '-gravity', 'northwest',
            '-splice', f'{left}x{top}', '-gravity', 'northwest', '-extent', f'{cw}x{ch}',
            '-strip', '-define', 'png:compression-level=9', target)
        frames[kind].append({'id': index, 'path': 'assets/'+target.name,
                             'source_cell': i, 'source_bounds': [x0+l,y0+t,r-l,b-t],
                             'size': [cw,ch], 'content': [left,top,w,h]})

sheet('battle-original.png', 4, 5, 'battle', .32, (96,112), 104)
sheet('maps-original.png', 4, 4, 'maps', .125, (40,48), 44)
broken_width = Image.open(ROOT/'source/battle-broken-original.png').width
sheet('battle-broken-original.png', 4, 3, 'battle-broken', .32*1122/broken_width, (96,112), 104)
broken_map_width = Image.open(ROOT/'source/maps-broken-original.png').width
sheet('maps-broken-original.png', 4, 4, 'maps-broken', .125*1254/broken_map_width, (40,48), 44)
sheet('concept-original.png', 2, 2, 'concept', .42, (256,272), 260)
run(ROOT/'source/concept-original.png', '-resize', '1000x1000>', '-strip',
    '-quality', '85', ROOT/'assets/concept.webp')

# Reference atlases are idle design baselines, never claimed to be original-game art.
for category in ['battle','maps','battle-broken','maps-broken']:
    first = ROOT / frames[category][0]['path']
    paths = [str(ROOT/f['path']) for f in frames[category]]
    run(*paths, '+append', '-strip', ROOT/f'assets/{category}-poses.png')
    run(first, '-strip', ROOT/f'assets/{category}-baseline.png')
    run(*([str(first)]*len(paths)), '+append', '-strip', ROOT/f'assets/{category}-reference.png')

for p in sorted((ROOT/'assets').glob('*')):
    im = Image.open(p)
    inventory.append({'path':'assets/'+p.name,'pixels':list(im.size),'bytes':p.stat().st_size,
                      'use':'concept preview' if p.suffix=='.webp' or p.name.startswith('concept-') else 'review-only sprite / atlas',
                      'note':'Original generation preserved in isolated source/. Native review frames retain full contour.'})
(ROOT/'asset-manifest.json').write_text(json.dumps({'frames':frames,'images':inventory},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'frames':{k:len(v) for k,v in frames.items()},'assets':len(inventory),
                  'maximum_bytes':max(a['bytes'] for a in inventory)},ensure_ascii=False))
