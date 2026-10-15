#!/usr/bin/env python3
"""Targeted integrity and road checks for the organic art layout, no combat simulation."""
from pathlib import Path
import json, math, hashlib
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/natural-0.1.3'
def read(path):return json.loads((ROOT/path).read_text())
checks=0;errors=[]
def check(ok,label):
 global checks
 checks+=1
 if not ok:errors.append(label)
def intersects(a,b):return a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and a[1]<b[1]+b[3] and a[1]+a[3]>b[1]
def contains(a,b):return a[0]<=b[0] and a[1]<=b[1] and a[0]+a[2]>=b[0]+b[2] and a[1]+a[3]>=b[1]+b[3]
cat={s['key']:s for s in read('assets/nature/nature.json')['sprites']}
def rect(p):return [*p['position'],*p.get('size',cat[p['key']]['size'])]
def fingerprint(d,art):return hashlib.sha256(json.dumps({k:v for k,v in d.items() if k not in art},sort_keys=True).encode()).hexdigest()
manifest=[]
for s in cat.values():
 p=ROOT/s['path'].replace('res://','');im=Image.open(p).convert('RGBA');bbox=im.getchannel('A').getbbox()
 check(list(im.size)==s['size'] and s['whole_source'],s['key']+' native complete source')
 check(bbox is not None and bbox[0]>0 and bbox[1]>0 and bbox[2]<im.width and bbox[3]<im.height,s['key']+' silhouette padding')
 check(set(im.getchannel('A').getdata())<={0,255},s['key']+' pixel alpha')
 manifest.append({'path':str(p.relative_to(ROOT)),'use':'complete reusable nature sprite','dimensions':list(im.size),'bytes':p.stat().st_size})
layouts=read('data/nature-layouts.json')
check(len(layouts['hubs'])==10 and len(layouts['battles'])==7,'all current environments covered')
placements=0
for group in ['hubs','battles']:
 for code,layout in layouts[group].items():
  props=layout['props'];placements+=len(props)
  check(len({p['key'] for p in props})>=4,code+' mixed silhouettes')
  check(sum(p['position'][0]%16!=0 or p['position'][1]%16!=0 for p in props)>len(props)*.8,code+' free organic positions')
  for p in props:
   check(p['key'] in cat,code+' resource exists')
   check(not any(intersects(rect(p),e) for e in layout['excluded']),code+' avoids roads/exits/buildings/actors')
  for grove in layout.get('groves',[]):
   for p in grove['props']:check(contains(grove['rect'],rect(p)),code+' complete grove stays in original obstacle')
pack=read('assets/battle_tiles/battle-tiles.json');mods={m['name']:m for m in pack['modules']}
for path in sorted((ROOT/'data/stages').glob('*.json')):
 d=json.loads(path.read_text());old=read('source/natural-0.1.3/baseline/data/stages/'+path.name)
 check(fingerprint(d,['art_layers','art_modules','natural_props','art_style_version'])==fingerprint(old,['art_layers','art_modules','natural_props','art_style_version']),path.stem+' all gameplay fields unchanged')
 reserved=[[*[v*16 for v in m['origin']],*[v*16 for v in m['footprint']]] for m in d['art_modules']]
 points=d['player_positions']+[u['position'] for u in d['enemies']+d['npc_units']+d['reinforcements']]+d['targets']+[d['exit']]+[o['position'] for o in d['objects']]
 reserved += [[x*16-4,y*16-8,24,28] for x,y in points]
 for p in d['natural_props']:
  x,y,w,h=rect(p)
  occupied={(xx,yy) for yy in range(y//16,math.ceil((y+h)/16)) for xx in range(x//16,math.ceil((x+w)/16))}
  chars={d['logic_grid'][yy][xx] for xx,yy in occupied}
  check(len(chars)==1 and next(iter(chars)) in 'f^',path.stem+' whole prop stays in terrain area')
  check(not any(intersects(rect(p),r) for r in reserved),path.stem+' avoids buildings/objectives/deployment')
w=read('data/formal_world.json');old=read('source/natural-0.1.3/baseline/data/formal_world.json');wp=read('assets/world_tiles/world-tiles.json');wm={m['name']:m for m in wp['modules']}
check(fingerprint(w,['layers','modules','natural_props','art_style_version'])==fingerprint(old,['layers','modules','natural_props','art_style_version']),'world routes, ground and node conditions unchanged')
for i in [3,4]:check(w['layers'][i]==old['layers'][i],'world preserved road / node layer '+str(i))
reserved=set();steps=0
for route in w['routes']:
 for a,b in zip(route['cells'],route['cells'][1:]):
  steps+=1;check(abs(a[0]-b[0])+abs(a[1]-b[1])==1,'world cardinal route continuity')
 for x,y in route['cells']:
  check(w['layers'][3][y][x] is not None,'visible road for every movement cell')
  reserved.add((x,y))
for n in w['nodes'].values():
 m=wm[n['symbol']];mw,mh=m['footprint'];ox=n['x']-(mw-1)//2;oy=n['y']-mh+1
 for dy,row in enumerate(m['tiles']):
  for dx,t in enumerate(row):check(w['layers'][4][oy+dy][ox+dx]==t,'full world node icon '+n['id'])
 reserved.update((ox+x,oy+y) for y in range(mh) for x in range(mw))
for m in w['modules']:
 meta=wm[m['name']];ox,oy=m['origin'];cells=set(map(tuple,m['cells']))
 check(not cells&reserved,'world module road/node buffer '+m['name'])
 for dy,row in enumerate(meta['tiles']):
  for dx,t in enumerate(row):check(w['layers'][2][oy+dy][ox+dx]==t,'whole world geography module '+m['name'])
for p in w['natural_props']:
 x,y,sw,sh=rect(p);occupied={(xx,yy) for yy in range(y//16,math.ceil((y+sh)/16)) for xx in range(x//16,math.ceil((x+sw)/16))}
 check(not occupied&reserved,'world natural object avoids road / node buffer')
 check(all(0<=xx<w['width'] and 0<=yy<w['height'] and w['ground'][yy][xx] not in ['sea','marsh','sand','salt'] for xx,yy in occupied),'world complete object stays on land')
report={'passed':not errors,'checks':checks,'errors':errors,'nature_sprites':len(cat),'exterior_placements':placements,'hubs':len(layouts['hubs']),'battle_maps':len(layouts['battles']),'world_nodes':len(w['nodes']),'world_routes':len(w['routes']),'world_modules':len(w['natural_props']),'route_steps':steps,'scope':'Art integrity, complete footprints, road/exit/actor separation and unchanged gameplay data; appearance reviewed in engine captures'}
(REPORT/'geometry-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(REPORT/'image-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if not errors else 1)
