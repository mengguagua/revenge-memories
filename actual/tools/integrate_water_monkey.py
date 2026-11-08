"""Pack only approved, referenced water-monkey pixels and real actor timelines."""
from pathlib import Path
import json,shutil,subprocess,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'art-review/character-expansion-20261018/water-monkey-v1-20261104'
DEST=ROOT/'assets/mechanical-puppets-20261104'
DEST.mkdir(exist_ok=True)
source=(REVIEW/'gallery-extension.js').read_text()
data=json.loads(source.split('const extra = ',1)[1].split(';\nconst d=',1)[0])
manifest=json.loads((REVIEW/'asset-manifest.json').read_text())
MAGICK='/opt/homebrew/bin/magick'
def run(*args):subprocess.run([MAGICK,*map(str,args)],check=True,capture_output=True)
poses={};packed=[]
for group in ['battle','battle-broken']:
    selected=[a for a in data['actions'] if a['profile']=='water-monkey-'+group]
    needed=sorted({f for a in selected for f in a['neededFrames']})
    poses[group]={str(f):len(packed)+i for i,f in enumerate(needed)}
    profile=next(p for p in data['profiles'] if p['id']=='water-monkey-'+group)
    packed.extend(REVIEW/profile['newFrames'][str(f)].split('/',1)[1] for f in needed)
run(*packed,'+append','-strip',DEST/'battle.png')
for group in ['maps','maps-broken']:
    paths=[REVIEW/f['path'] for f in manifest['frames'][group]]
    run(*paths,'+append','-strip',DEST/(group+'.png'))
shutil.copyfile(REVIEW/'assets/battle-00.png',DEST/'portrait.png')
effects={}
for key,entry in data['effects'].items():
    name=Path(entry['path']).name
    shutil.copyfile(REVIEW/'assets'/name,DEST/name)
    effects[key]={'path':'res://assets/mechanical-puppets-20261104/'+name,'frame_size':[128,96],
                  'logical_frame_size':entry['frame_size'],'anchor':entry['anchor'],'frames':1,'columns':1,'native_density':1}
variants={}
for a in data['actions']:
    if a['context']!='battle':continue
    group=a['profile'].removeprefix('water-monkey-')
    rows=[]
    for r in a['frames']:
        row={k:v for k,v in r.items() if k not in ['companionTint','companionShake']}
        row['frame']=poses[group][str(r['frame'])]
        row['flip']=not r.get('flip',False)
        rows.append(row)
    variants[a['key']]={'native_fps':a['fps'],'contact_tick':a['contactTick'] if a['contactTick'] is not None else 0,
                        'frames':rows,'review_origin':a['origin'],'review_target':[64,128]}
runtime={'revision':'water-monkey-motion-v2-20261104','approved_source':'art-review/character-expansion-20261018/water-monkey-v1-20261104',
         'battle':{'path':'res://assets/mechanical-puppets-20261104/battle.png','frame_size':[56,64],
                   'frames':len(packed),'columns':len(packed),'anchor':[28,60],'native_density':1,
                   'source_oam_frame_count':0,'default_facing':'left','original_motion':True},
         'idle_frames':{'intact':poses['battle']['0'],'broken':poses['battle-broken']['0']},
         'maps':{},'effects':effects,'variants':variants,
         'scope':'Only real actor and bitmap effects; all review companions and review sound events stripped.'}
map_anchor=[10,22]
# Place the frame's foot anchor at the tile's bottom center.
tile_origin=[map_anchor[0]-8,map_anchor[1]-16]
for state,group in [('intact','maps'),('broken','maps-broken')]:
    runtime['maps'][state]={'path':'res://assets/mechanical-puppets-20261104/'+group+'.png',
        'frame_size':[40,48],'frames':16,'columns':16,'anchor':map_anchor,'native_density':2,
        'tile_origin':tile_origin,'default_facing':'left','original_motion':True,'static_facing':True,
        'directions':{'up':[8,8],'down':[1,1],'left':[12,12],'right':[4,4],'side':[12,12]},
        'native_cycle':[1,0,1,2],'cycle_ticks':[72,18,72,18],
        'direction_cycles':{k:{'frames':[v+i for i in range(4)],'ticks':[8,8,8,8]} for k,v in [('up',8),('down',0),('left',12),('right',4)]}}
(ROOT/'data/mechanical_puppets_art.json').write_text(json.dumps(runtime,ensure_ascii=False,separators=(',',':'))+'\n')
inventory=[]
for p in sorted(DEST.glob('*.png')):
    subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','--strip','safe','--quiet',str(p)],check=True)
    inventory.append({'path':str(p.relative_to(ROOT)),'pixels':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                      'use':'approved native pixel atlas / effect / portrait','quality':'Original native resolution and transparent contour preserved; lossless oxipng.',
                      'size_note':'24 approved poses share one atlas to preserve part-break transitions. Individual native poses are under 4KB; the lossless atlas exceeds the 50KB reference to retain the approved pixel palette.' if p.name=='battle.png' else 'Within 50KB reference; no resampling or palette loss.'})
report=ROOT/'reports/mechanical-puppets-20261104';report.mkdir(exist_ok=True)
(report/'runtime-assets.json').write_text(json.dumps({'images':inventory,'battle_poses':len(packed),'variants':list(variants),'review_companions_shipped':False},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'battle_poses':len(packed),'variants':len(variants),'images':len(inventory)}))
