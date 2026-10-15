#!/usr/bin/env python3
"""Directed geography/rule/art verification, complementary to actual play."""
from pathlib import Path
from collections import deque
import json
from PIL import Image, ImageChops
ROOT=Path(__file__).resolve().parents[1]
errors=[];checks=[]
def check(ok,label):
 checks.append(label)
 if not ok:errors.append(label)
def read(p):return json.loads((ROOT/p).read_text())
w=read('data/formal_world.json');pack=read('assets/battle_tiles/battle-tiles.json');campaign=read('data/campaign.json')
check(len(w['nodes'])==39 and len(w['routes'])==40,'approved 39 nodes and 40 routes')
nodes={n['id']:n for n in w['nodes'].values()}
road_cells=set();land_cells=0;steps=0
for r in w['routes']:
 cells=r['cells'];a=nodes[r['a']];b=nodes[r['b']]
 check(cells[0]==[a['x'],a['y']] and cells[-1]==[b['x'],b['y']],r['a']+' route endpoints')
 for p,q in zip(cells,cells[1:]):
  steps+=1;check(abs(p[0]-q[0])+abs(p[1]-q[1])==1,r['a']+' route cardinal continuity')
 for x,y in cells:
  check(0<=x<w['width'] and 0<=y<w['height'],r['a']+' route inside map')
  road_cells.add((x,y))
  check(w['layers'][3][y][x] is not None,r['a']+' every movement cell has route pixels')
  if r['kind']=='land':
   land_cells+=1;check(w['ground'][y][x] not in ['sea','rock','forest','marsh'],r['a']+' land corridor clear')
for m in w['modules']:
 check(not(set(map(tuple,m['cells']))&road_cells),'intact geography module never hides route '+m['name'])
atlas=Image.open(ROOT/'assets/battle_tiles/battle-tiles.png').convert('RGBA')
for m in pack['modules']:
 original=Image.open(ROOT/'assets/battle_tiles'/m['path']).convert('RGBA');mw,mh=m['footprint']
 rebuilt=Image.new('RGBA',(mw*16,mh*16))
 for y,row in enumerate(m['tiles']):
  for x,tid in enumerate(row):
   sx=tid%32*16;sy=tid//32*16;rebuilt.paste(atlas.crop((sx,sy,sx+16,sy+16)),(x*16,y*16))
 check(ImageChops.difference(original,rebuilt).getbbox() is None,'module cuts reassemble '+m['name'])
 check(set(original.getchannel('A').getdata())<={0,255},'binary alpha edges '+m['name'])
 check(original.width==mw*16 and original.height==mh*16,'module has declared native footprint '+m['name'])
stage_checks=[]
for meta in campaign['stages'].values():
 b=read(meta['path'].replace('res://',''));width=b['map']['width'];height=b['map']['height']
 g=[list(r) for r in b['logic_grid']]
 # Directed reachability assumes a player has explicitly opened each labelled door.
 for o in b['objects']:
  if o['kind']=='door':g[o['position'][1]][o['position'][0]]='='
 start=tuple(b['player_positions'][0]);seen={start};q=deque([start])
 while q:
  x,y=q.popleft()
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   p=(x+dx,y+dy)
   if 0<=p[0]<width and 0<=p[1]<height and p not in seen and g[p[1]][p[0]] not in '#^~':seen.add(p);q.append(p)
 points=b['targets']+[b['exit']]+[u['position'] for u in b['enemies']+b['npc_units']]
 check(all(tuple(p) in seen for p in points),b['code']+' deployment reaches every objective, enemy and ally')
 t=b['terrain'];check(all(str(int(u['class_id'])) in t['movement_by_class_and_category'] for u in list(b['characters'].values())+b['enemies']+b['npc_units']),b['code']+' full class movement coverage')
 for tile,cat in {'48':0,'172':1,'94':5,'242':2,'96':7,'196':12,'208':8,'191':6,'66':16,'218':15}.items():
  check(int(t['tile_categories'][tile])==cat,b['code']+' explicit art/rule terrain '+tile)
 check(t['movement_by_class_and_category']['6'][12]>=255 and t['movement_by_class_and_category']['6'][5]>=255,b['code']+' masonry/mountain blocks infantry')
 stage_checks.append({'code':b['code'],'map':[width,height],'reachable_cells':len(seen),'full_class_tables':len(t['movement_by_class_and_category'])})
manifest=[]
for folder in [ROOT/'assets/battle_tiles',ROOT/'reports/campaign']:
 for p in folder.rglob('*.png'):
  im=Image.open(p);manifest.append({'path':str(p.relative_to(ROOT)),'dimensions':list(im.size),'bytes':p.stat().st_size,'use':'tactical reusable asset' if 'battle_tiles' in str(p) else 'map/screenshot review','compression':'lossless PNG; native art and source originals preserved'})
report={'round':2,'checks':len(checks),'errors':errors,'passed':not errors,'route_steps':steps,'land_route_cells':land_cells,'complete_battle_modules':len(pack['modules']),'stages':stage_checks,'scope':'Geometry, full movement/terrain mapping, intact modules; visual checks in round2-visual.json'}
(ROOT/'reports/campaign/round2-geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(ROOT/'reports/campaign/image-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='stages'},ensure_ascii=False));raise SystemExit(0 if not errors else 1)
