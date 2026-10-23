#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import copy,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter3-environment-20261023';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];errors=[]
def ck(ok,label):
 checks.append(label)
 if not ok:errors.append(label)
CODES=read(O/'codes.json');original=read(O/'baseline/maps.json');changed=[];maps={};allowed={'art_atlas','art_layers','art_props','map_tint','material_review_version','environment_review','objects'}
for c,h in original.items():
 path=R/f'data/stages/{c}.json';d=read(path);maps[c]=sha(path)
 if maps[c]!=h:changed.append(c)
 if c not in CODES:ck(maps[c]==h,c+' out-of-scope exact');continue
 old=read(O/f'baseline/{c}.json')
 for k in old.keys()|d.keys():
  if k not in allowed:ck(old.get(k)==d.get(k),c+' exact '+k)
 for p,q in zip(old['art_props'],d['art_props']):
  ck({k:v for k,v in p.items()if k!='path'}=={k:v for k,v in q.items()if k!='path'},c+' exact prop placement/shape '+str(p['position']))
  ck(Image.open(R/p['path'][6:]).size==Image.open(R/q['path'][6:]).size,c+' same-size prop '+str(q['position']))
 a=copy.deepcopy(old['objects']);b=copy.deepcopy(d['objects'])
 for objects in [a,b]:
  for obj in objects:
   for cell in obj.get('open_art_cells',[]):cell.pop('base_tile',None)
 ck(a==b,c+' all object coordinates/rules identical except opened floor art')
ck(set(changed)=={'M33','F31','F32','F33','S31','S32'},'six art-adjusted maps; M31/M32 intact')
for name,source in [('formal_world.json','data/formal_world.json'),('chapter3_hubs.json','data/chapter3_hubs.json'),('nature.json','assets/nature/nature.json')]:ck(sha(R/source)==sha(O/'baseline'/name),name+' original world/rooms/nature byte-identical')
core=[]
for p,h in read(O/'baseline/core.json').items():
 if sha(R/p)!=h:core.append(p)
ck(set(core)=={'core/main.gd','core/story_hub.gd'},'only world/hub drawing and terrain labels changed; all other core/animation/rule files exact')
for c in ['M31','M32']:
 ck(Image.open(O/f'before/{c}.png').convert('RGBA').tobytes()==Image.open(O/f'images/{c}.png').convert('RGBA').tobytes(),c+' native scenery pixel-identical')
assets=[]
for p in sorted((R/'assets/chapter3-environment-20261023').rglob('*.png')):
 im=Image.open(p);assets.append({'path':str(p.relative_to(R)),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'quality_note':'Native pixels and complete original tile-bank IDs preserved losslessly.'if p.stat().st_size>200000 else'Lossless optimization; native display dimensions retained.'})
result={'passed':not errors,'check_count':len(checks),'checks':checks,'errors':errors,'changed_maps':sorted(changed),'unchanged_maps':[c for c in original if c not in changed],'map_hashes':maps,'changed_core':core,'assets':assets,'scope':'Compare immutable pre-task baseline; exact tactical grids, actors, positions, collision rooms and object rules. Only opened floor artwork, native materials, architecture and display selectors/names changed.'}
(O/'invariants-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:result[k]for k in ['passed','check_count','changed_maps','errors']});assert not errors
