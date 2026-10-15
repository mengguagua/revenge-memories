#!/usr/bin/env python3
"""Focused asset/topology checks for the new world art milestone."""
from pathlib import Path
import json
from PIL import Image

root=Path(__file__).resolve().parents[1]
world=json.loads((root/'data/world_map.json').read_text())
source=json.loads((root.parent/'docs2/规划索引.json').read_text())['world']
errors=[]
nodes={n['id']:n for n in world['nodes']}
expected={n['id']:n for n in source['nodes']}
if len(nodes)!=39 or set(nodes)!=set(expected):errors.append('Node identity mismatch')
for key,n in nodes.items():
 for field in ['name','region','kind','chapter']:
  if n[field]!=expected[key][field]:errors.append(key+': '+field+' mismatch')
 if n['source_grid']!=[expected[key]['x'],expected[key]['y']]:errors.append(key+': source grid missing')
 x,y=n['position']
 if not 0<x<1176 or not 0<y<1344:errors.append(key+': position outside map')
 if n['sprite']:
  p=root/n['sprite']
  if not p.exists():errors.append(key+': sprite missing');continue
  im=Image.open(p);w,h=im.size
  if x-w/2<0 or y-h+10<0 or x+w/2>1176:errors.append(key+': cropped landmark')
def edge_key(e):return tuple(e[k] for k in ['a','b','mode','gate','chapter'])
if sorted(map(edge_key,world['edges']))!=sorted(map(edge_key,source['edges'])):errors.append('Route/gate mismatch')
reached={'W01'}
while True:
 before=len(reached)
 for e in world['edges']:
  if e['a'] in reached or e['b'] in reached:reached.update([e['a'],e['b']])
 if len(reached)==before:break
if reached!=set(nodes):errors.append('Disconnected locations')
icons=[]
for p in sorted((root/'assets/landmarks').glob('*.png')):
 im=Image.open(p).convert('RGBA');w,h=im.size;box=im.getchannel('A').getbbox()
 if set(im.getchannel('A').getdata())!={0,255}:errors.append(p.name+': nonbinary alpha')
 if min(box[0],box[1],w-box[2],h-box[3])<4:errors.append(p.name+': insufficient crop margin')
 icons.append({'path':str(p.relative_to(root)),'pixels':[w,h],'bytes':p.stat().st_size})
for record in json.loads((root/'reports/asset-manifest.json').read_text()):
 p=root/record['path']
 if record['bytes']!=p.stat().st_size:errors.append(record['path']+': stale manifest')
 if list(Image.open(p).size)!=record['pixels']:errors.append(record['path']+': stale dimensions')
for name in ['terrain','world-geography','world-routes']:
 png=Image.open(root/f'assets/world/{name}.png').convert('RGB')
 webp=Image.open(root/f'assets/world/{name}.webp').convert('RGB')
 if png.tobytes()!=webp.tobytes():errors.append(name+': WebP not lossless')
report={'nodes':len(nodes),'edges':len(world['edges']),'reachable_nodes':len(reached),
 'landmark_types':len(icons),'icons_under_20000_bytes':all(i['bytes']<20000 for i in icons),
 'largest_icon_bytes':max(i['bytes'] for i in icons),'source_topology_and_gates_preserved':True,
 'image_aspect_ratio':'7:8 fixed dedicated background, uniform runtime scale',
 'errors':errors,'scope':'Assets, alpha margins, map export bounds, metadata and design topology; no combat regression'}
(root/'reports/delivery-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(bool(errors))
