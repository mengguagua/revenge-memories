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
frames = {'battle': [], 'maps': [], 'effects': [], 'concept': [], 'battle-broken': [], 'maps-broken': [], 'water-v2': []}
# Rejected V1 cells remain only inside mixed source sheets that also contain
# approved poses. Never regenerate them into review or runtime output.
REJECTED = {'battle': {6,8,9,12,13,14,16,17,18,19}, 'battle-broken': {4,5,8,9,10,11}}

def run(*args):
    subprocess.run([MAGICK, *map(str, args)], check=True, capture_output=True)

def sheet(name, columns, rows, category, factor, canvas, baseline):
    source = ROOT / 'source' / name
    im = Image.open(source)
    for i in range(columns * rows):
        if i in REJECTED.get(category, set()):continue
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

sheet('battle-original.png', 4, 5, 'battle', .18, (56,64), 60)
sheet('maps-original.png', 4, 4, 'maps', .125, (40,48), 44)
broken_width = Image.open(ROOT/'source/battle-broken-original.png').width
sheet('battle-broken-original.png', 4, 3, 'battle-broken', .18*1122/broken_width, (56,64), 60)
broken_map_width = Image.open(ROOT/'source/maps-broken-original.png').width
sheet('maps-broken-original.png', 4, 4, 'maps-broken', .125*1254/broken_map_width, (40,48), 44)
sheet('concept-original.png', 2, 2, 'concept', .42, (256,272), 260)

# New genuine running poses: normalize body height against the existing idle,
# not the cannon tip, so a broken barrel cannot shrink the whole character.
run_path=ROOT/'source/motion-v2-20261104/run-original.png'
run_image=Image.open(run_path)
for i in range(8):
    col,row=i%4,i//4
    x0,x1=round(col*run_image.width/4),round((col+1)*run_image.width/4)
    y0,y1=round(row*run_image.height/2),round((row+1)*run_image.height/2)
    alpha=run_image.getchannel('A').crop((x0,y0,x1,y1))
    bbox=alpha.point(lambda v:255 if v>=128 else 0).getbbox()
    l,t,r,b=bbox
    # Head-to-foot landmark measured on the generated source, 270±5 px.
    factor=32/270
    w,h=round((r-l)*factor),round((b-t)*factor)
    group='battle' if row==0 else 'battle-broken'
    index=16+col if row==0 else 12+col
    left,top=(56-w)//2,60-h
    assert left>=2 and top>=2 and left+w<=54
    target=ROOT/'assets'/f'{group}-{index:02d}.png'
    run(run_path,'-crop',f'{x1-x0}x{y1-y0}+{x0}+{y0}','+repage',
        '-channel','A','-threshold','50%','+channel','-crop',f'{r-l}x{b-t}+{l}+{t}','+repage',
        '-filter','point','-resize',f'{w}x{h}!','-background','none','-gravity','northwest',
        '-splice',f'{left}x{top}','-extent','56x64','-strip',target)
    frames[group].append({'id':index,'path':'assets/'+target.name,'source':'source/motion-v2-20261104/run-original.png',
                          'source_cell':i,'source_bounds':[x0+l,y0+t,r-l,b-t],'size':[56,64],'content':[left,top,w,h]})

water=Image.open(ROOT/'source/motion-v2-20261104/water-original.png')
for i in range(4):
    col,row=i%2,i//2
    x0,x1=round(col*water.width/2),round((col+1)*water.width/2)
    y0,y1=round(row*water.height/2),round((row+1)*water.height/2)
    bbox=water.getchannel('A').crop((x0,y0,x1,y1)).point(lambda v:255 if v>=128 else 0).getbbox()
    l,t,r,b=bbox
    assert l>3 and t>3 and r<x1-x0-3 and b<y1-y0-3,('effect crosses source cell',i,bbox)
    target=ROOT/'assets'/f'water-v2-{i:02d}.png'
    run(ROOT/'source/motion-v2-20261104/water-original.png','-crop',f'{x1-x0}x{y1-y0}+{x0}+{y0}','+repage',
        '-channel','A','-threshold','50%','+channel','-crop',f'{r-l}x{b-t}+{l}+{t}','+repage',
        '-filter','point','-resize','112x80','-background','none','-gravity','center','-extent','128x96','-strip',target)
    frames['water-v2'].append({'id':i,'path':'assets/'+target.name,'source':'source/motion-v2-20261104/water-original.png',
                              'source_cell':i,'source_bounds':[x0+l,y0+t,r-l,b-t],'size':[128,96]})
run(ROOT/'source/concept-original.png', '-resize', '1000x1000>', '-strip',
    '-quality', '85', ROOT/'assets/concept.webp')

# Reference atlases are idle design baselines, never claimed to be original-game art.
for category in ['battle','maps','battle-broken','maps-broken']:
    first = ROOT / frames[category][0]['path']
    paths = [str(ROOT/f['path']) for f in frames[category]]
    run(*paths, '+append', '-strip', ROOT/f'assets/{category}-poses.png')
    run(first, '-strip', ROOT/f'assets/{category}-baseline.png')
    reference_columns=max(f['id'] for f in frames[category])+1
    run(*([str(first)]*reference_columns), '+append', '-strip', ROOT/f'assets/{category}-reference.png')

for p in sorted((ROOT/'assets').glob('*')):
    if p.suffix not in ['.png','.webp']:continue
    im = Image.open(p)
    inventory.append({'path':'assets/'+p.name,'pixels':list(im.size),'bytes':p.stat().st_size,
                      'use':'concept preview' if p.suffix=='.webp' or p.name.startswith('concept-') else 'review-only sprite / atlas',
                      'note':'Quality 85 retained for the four-view concept to preserve fine details and transparent edges above the 200KB reference.' if p.name=='concept.webp' else 'Adopted source generation preserved in isolated source/. Native review frames retain full contour.'})
for p in sorted((ROOT/'qa').glob('*.webp')):
    inventory.append({'path':'qa/'+p.name,'pixels':list(Image.open(p).size),'bytes':p.stat().st_size,'use':'review QA screenshot','note':'Current approved artwork; source capture remains isolated.'})
audio=ROOT/'assets/hit.ogg'
(ROOT/'asset-manifest.json').write_text(json.dumps({'frames':frames,'images':inventory,'audio':[{'path':'assets/hit.ogg','bytes':audio.stat().st_size,'use':'Opt-in HTML-only copy of existing rm_sfx_03; runtime reuses existing audio.'}]},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'frames':{k:len(v) for k,v in frames.items()},'assets':len(inventory),
                  'maximum_bytes':max(a['bytes'] for a in inventory)},ensure_ascii=False))
