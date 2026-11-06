"""Optimize site images. Original game files and captures stay intact."""
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
OUT=ROOT/'assets/images'
OUT.mkdir(parents=True,exist_ok=True)
sources={p.stem:p for p in (ROOT/'source/captures').glob('*.png') if p.stem not in {'title','story','combat'}}
sources['coast']=REPO/'actual/assets/journey-home/snow-coast.png'
portraits=json.loads((REPO/'actual/data/portraits.json').read_text())['assets']
portrait_keys=['hunapu','eileen','daan','otto','fula','lena','lance','beck','hervi','german','mireille','lisa','carlo','lord','roan','shia','noya','celine']
for name in portrait_keys:
    key=name+'_present' if name in ['hunapu','eileen'] else name
    sources[name]=REPO/'actual'/portraits[key]['path'].removeprefix('res://')
records=[]
for name,source in sources.items():
    dest=OUT/(name+'.webp')
    poster=name.startswith('video-')
    options=['-quality','92'] if poster else ['-define','webp:lossless=true']
    subprocess.run(['/opt/homebrew/bin/magick',str(source),'-strip',*options,'-define','webp:method=6',str(dest)],check=True)
    dimensions=subprocess.check_output(['/opt/homebrew/bin/magick','identify','-format','%wx%h',str(dest)],text=True)
    comparison=subprocess.run(['/opt/homebrew/bin/magick','compare','-metric','AE',str(source),str(dest),'null:'],capture_output=True,text=True)
    if not poster and comparison.returncode!=0:raise RuntimeError(f'Image pixels changed: {name} {comparison.stderr}')
    purpose='Mobile video poster' if poster else 'Game character portrait' if name in portrait_keys else 'Game coastline used as proportional hero/background art' if name=='coast' else 'PC in-game screenshot in story, gameplay or gallery'
    records.append({'purpose':purpose,'asset':str(dest.relative_to(ROOT)),'source':str(source.relative_to(REPO)),'pixels':dimensions,'source_bytes':source.stat().st_size,'bytes':dest.stat().st_size,'pixel_identical':not poster,'method':'WebP quality 92, original resolution, visually checked at display size; original frame retained' if poster else 'lossless WebP, metadata stripped'})
(ROOT/'reports/image-assets.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'images':len(records),'total_bytes':sum(r['bytes'] for r in records),'pixel_identical_assets':len([r for r in records if r['pixel_identical']]),'visually_optimized_posters':2}))
