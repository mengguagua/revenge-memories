#!/usr/bin/env python3
"""Pack approved trio art and apply the runtime-only Prometheus flame palette."""
from bisect import bisect_right
from pathlib import Path
from PIL import Image
import json,copy,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'art-review/character-expansion-20261018/puppet-trio-v3-20261105'
j=json.JSONDecoder().raw_decode((REVIEW/'gallery-extension.js').read_text().split('const extra = ',1)[1])[0]
DEST=ROOT/'assets/story-puppets-20261107';DEST.mkdir(exist_ok=True)
MAGMA_EFFECTS={'trio-flame-ignite','trio-flame-stream'}
MAGMA_RAMP=json.loads(Path(__file__).with_name('prometheus_magma_palette.json').read_text())
MAGMA_STEPS=[value for value,_ in MAGMA_RAMP]
MAGMA_COLORS=[tuple(bytes.fromhex(color[1:])) for _,color in MAGMA_RAMP]

def copy_effect(key, spec):
 src=REVIEW.parent/spec['path'];dst=DEST/src.name
 if key not in MAGMA_EFFECTS:
  shutil.copyfile(src,dst)
  return dst
 with Image.open(src) as source:
  pixels=source.convert('RGBA')
  pixels.putdata([(*MAGMA_COLORS[bisect_right(MAGMA_STEPS,(54*r+183*g+19*b)//256)-1],a)
                  if a else (r,g,b,a) for r,g,b,a in pixels.getdata()])
  pixels.save(dst,optimize=True)
 return dst

if sys.argv[1:]==['--magma-only']:
 for key in sorted(MAGMA_EFFECTS):
  print(copy_effect(key,j['effects'][key]))
 sys.exit(0)

def atlas(paths,name):
 ims=[Image.open(p).convert('RGBA') for p in paths];im=Image.new('RGBA',(ims[0].width*len(ims),ims[0].height))
 for i,p in enumerate(ims):im.paste(p,(i*p.width,0))
 im.save(DEST/name);return list(ims[0].size)
def sprite(path,size,count,anchor):return {'path':'res://assets/story-puppets-20261107/'+path,'frame_size':size,'frames':count,'columns':count,'anchor':anchor,'native_density':1,'source_oam_frame_count':0,'default_facing':'left','original_motion':True}
runtime={'revision':'approved-trio-20261107','approved_source':str(REVIEW.relative_to(ROOT.parent)),'models':{},'effects':{}}
for model in ['cyclops','owl','prometheus']:
 profiles=[p for p in j['profiles'] if p['actor']=='puppet-trio-'+model]
 paths=[];poses={};maps={};portraits={};idle={}
 for p in profiles:
  state=p['id'].removeprefix('puppet-trio-'+model+'-').removesuffix('-battle').removesuffix('-maps')
  if p['context']=='battle':
   poses[state]={}
   for key,path in p['newFrames'].items():
    absolute=REVIEW.parent/path
    if absolute not in paths:paths.append(absolute)
    poses[state][key]=paths.index(absolute)
   idle[state]=poses[state]['0']
   # Trim empty margins only: the full approved silhouette fits the 48px portrait slot.
   name=f'{model}-{state}-portrait.png';im=Image.open(REVIEW.parent/p['newFrames']['0']).convert('RGBA');box=im.getbbox()
   assert box[2]-box[0]<=48 and box[3]-box[1]<=48,(model,state,box)
   cx=(box[0]+box[2])//2;cy=(box[1]+box[3])//2
   im.crop((cx-24,cy-24,cx+24,cy+24)).save(DEST/name);portraits[state]='res://assets/story-puppets-20261107/'+name
  else:
   source=[REVIEW.parent/p['newFrames'][str(i)] for i in range(len(p["newFrames"]))]
   name=f'{model}-{state}-map.png';size=atlas(source,name)
   # The reviewed map frames and anchors are authored at twice the logical size.
   density=2
   anchor=[coordinate/density for coordinate in p['anchor']]
   m=sprite(name,size,len(source),anchor)
   m.update({'native_density':density,'tile_origin':[anchor[0]-8,anchor[1]-16]})
   m.update({'static_facing':True,'directions':{'down':[0,0],'right':[4,4],'up':[8,8],'left':[12,12],'side':[12,12]},'native_cycle':([16,17,18,19] if len(source)>16 else [0,1,2,3]),'cycle_ticks':[14,8,14,8],'direction_cycles':{k:{'frames':[v+i for i in range(4)],'ticks':[12]*4} for k,v in [('down',0),('right',4),('up',8),('left',12)]}})
   maps[state]=m
 size=atlas(paths,model+'-battle.png');base=next(p for p in profiles if p['context']=='battle')
 variants={}
 for action in j['actions']:
  if action.get('unit')!=model or action['context']!='battle':continue
  state=action['state'];frames=[]
  for raw in action['frames']:
   r={k:copy.deepcopy(v) for k,v in raw.items() if k not in ['companionTint','companionShake','sounds']};r['frame']=poses[state][str(raw['frame'])];r['flip']=not raw.get('flip',False);frames.append(r)
  variants[state+':'+action['key']]={'native_fps':action['fps'],'contact_tick':action['contactTick'] or 0,'frames':frames}
 runtime['models'][model]={'battle':sprite(model+'-battle.png',size,len(paths),base['anchor']),'maps':maps,'portraits':portraits,'idle_frames':idle,'variants':variants}
for key,d in j['effects'].items():
 name=copy_effect(key,d).name
 runtime['effects'][key]={**d,'path':'res://assets/story-puppets-20261107/'+name}
(ROOT/'data/story_puppets_art.json').write_text(json.dumps(runtime,ensure_ascii=False,separators=(',',':'))+'\n')
inventory=[]
for p in sorted(DEST.glob('*.png')):
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','--strip','safe','--quiet',str(p)],check=True)
 note='Magma palette; approved native silhouette and alpha preserved.' if p.name in ['fx-flame-ignite.png','fx-flame-stream.png'] else 'Approved native frames, lossless atlas packing; no resampling.'
 inventory.append({'path':str(p.relative_to(ROOT)),'size':list(Image.open(p).size),'bytes':p.stat().st_size,'note':note})
(ROOT/'reports/dialogue-ch2-5-20261107/runtime-art.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(len(inventory),'approved art files packed')
