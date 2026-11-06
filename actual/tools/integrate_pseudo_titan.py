"""Pack the approved V2 pixels/timelines; exclude review companions and source studies."""
from pathlib import Path
from PIL import Image
import json, subprocess, hashlib
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'art-review/character-expansion-20261018/pseudo-titan-v1-20261105'
DEST=ROOT/'assets/pseudo-titan-20261105';DEST.mkdir(exist_ok=True)
d=json.loads((REVIEW/'gallery-extension.js').read_text().split('const extra = ',1)[1].split(';\nwindow.PSEUDO_TITAN_DATA',1)[0])
poses={};paths=[]
for group in ['battle','battle-broken']:
 profile=next(p for p in d['profiles'] if p['id']=='pseudo-titan-'+group)
 poses[group]={}
 for frame,path in sorted(profile['newFrames'].items(),key=lambda v:int(v[0])):
  p=REVIEW.parent/path
  if p not in paths:paths.append(p)
  poses[group][str(frame)]=paths.index(p)
def atlas(paths,name):
 images=[Image.open(p).convert('RGBA') for p in paths];out=Image.new('RGBA',(images[0].width*len(images),images[0].height))
 for i,im in enumerate(images):out.paste(im,(i*im.width,0))
 out.save(DEST/name)
atlas(paths,'battle.png')
for group in ['maps','maps-broken']:
 profile=next(p for p in d['profiles'] if p['id']=='pseudo-titan-'+group)
 atlas([REVIEW.parent/profile['newFrames'][str(i)] for i in range(16)],group+'.png')
# A native-resolution status portrait, cropped only to the confirmed full silhouette.
Image.open(paths[0]).crop((20,24,76,88)).save(DEST/'portrait.png')
Image.open(paths[poses['battle-broken']['0']]).crop((20,24,76,88)).save(DEST/'portrait-broken.png')
variants={}
for a in d['actions']:
 if a['context']!='battle':continue
 group=a['profile'].removeprefix('pseudo-titan-');rows=[]
 for r in a['frames']:
  row={k:v for k,v in r.items() if k not in ['companionTint','companionShake','sounds']}
  row['frame']=poses[group][str(r['frame'])];row['flip']=not r.get('flip',False)
  rows.append(row)
 variants[a['key']]={'native_fps':a['fps'],'contact_tick':a['contactTick'] or 0,'frames':rows}
runtime={'revision':'pseudo-titan-side-walk-v2-20261105','approved_source':str(REVIEW.relative_to(ROOT.parent)),
 'battle':{'path':'res://assets/pseudo-titan-20261105/battle.png','frame_size':[96,88],'frames':len(paths),'columns':len(paths),'anchor':[48,80],'native_density':1,'source_oam_frame_count':0,'default_facing':'left','original_motion':True},
 'portrait':'res://assets/pseudo-titan-20261105/portrait.png','portrait_broken':'res://assets/pseudo-titan-20261105/portrait-broken.png','idle_frames':{'intact':poses['battle']['0'],'broken':poses['battle-broken']['0']},'maps':{},'effects':{},'variants':variants}
for state,group in [('intact','maps'),('broken','maps-broken')]:
 runtime['maps'][state]={'path':'res://assets/pseudo-titan-20261105/'+group+'.png','frame_size':[64,64],'frames':16,'columns':16,'anchor':[16,30],'native_density':2,'tile_origin':[8,14],'default_facing':'left','original_motion':True,'static_facing':True,
 'directions':{'up':[8,8],'down':[0,0],'left':[12,12],'right':[4,4],'side':[12,12]},'native_cycle':[0,1,2,1],'cycle_ticks':[14,8,14,8],
 'direction_cycles':{k:{'frames':[v+i for i in range(4)],'ticks':[12]*4} for k,v in [('up',8),('down',0),('left',12),('right',4)]}}
(ROOT/'data/pseudo_titan_art.json').write_text(json.dumps(runtime,ensure_ascii=False,separators=(',',':'))+'\n')
inventory=[]
for p in sorted(DEST.glob('*.png')):
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','--strip','safe','--quiet',str(p)],check=True)
 inventory.append({'path':str(p.relative_to(ROOT)),'pixels':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'use':'approved native pixel atlas / status portrait','quality':'Lossless; approved pixels, silhouette and transparent edges preserved.','size_note':'Lossless multi-pose atlas retains the approved palette.' if p.stat().st_size>=50000 else 'Within 50KB reference.'})
report=ROOT/'reports/pseudo-titan-20261105';report.mkdir(exist_ok=True)
(report/'runtime-assets.json').write_text(json.dumps({'images':inventory,'battle_poses':len(paths),'variants':list(variants),'source_studies_shipped':False,'review_companions_shipped':False},ensure_ascii=False,indent=2)+'\n')
print({'battle_poses':len(paths),'variants':len(variants),'images':len(inventory)})
