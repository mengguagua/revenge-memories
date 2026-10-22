#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S11/S12 authored scenery and routes, from the preserved current-map baseline.
No actors, objectives, statistics or gameplay code are rewritten.
"""
from pathlib import Path
from collections import deque
import json,copy,random,math,hashlib,importlib.util,subprocess
from PIL import Image
R=Path(__file__).resolve().parents[1]
BASE=R/'reports/map-polish-20261022/baseline'
OUT=R/'reports/map-polish-20261022/side'
OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('bf',R/'tools/redesign_battlefields.py');bf=importlib.util.module_from_spec(spec);spec.loader.exec_module(bf)
ATLAS=json.loads((R/'assets/battlefield-0.3.0/terrain.json').read_text());TRANS=ATLAS['transitions'];PACK=bf.PACK;NATURE=bf.NATURE
ART=R/'assets/map-polish-20261022';ART.mkdir(parents=True,exist_ok=True)
source_atlas=Image.open(R/'assets/battlefield-0.3.0/terrain.png').convert('RGBA')
CELLS=[source_atlas.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16))for i in range(ATLAS['tile_count'])]
ORIGINAL=len(CELLS)
wspec=importlib.util.spec_from_file_location('masks',R/'tools/build_world_tiles.py');masks=importlib.util.module_from_spec(wspec);wspec.loader.exec_module(masks)
CAVE={'path':{},'rock':{},'shore':{}}
# Reuse the shipped neutral damp-gravel texture and grey mountain material.
# No original tile is recolored, resized, replaced or assigned a different ID.
FLOOR=PACK['base']['marsh'];ROCK=TRANS['mountain_ground']['cave']['255']
for name,foreground in [('path',PACK['base']['dirt']),('rock',ROCK)]:
 for mask in masks.MASKS:
  ids=[]
  for v in range(4):
   tile=CELLS[FLOOR[v]].copy();front=CELLS[foreground[v]].copy();front.putalpha(masks.alpha_mask(mask));tile.alpha_composite(front);ids.append(len(CELLS));CELLS.append(tile)
  CAVE[name][str(mask)]=ids

def native_shore(neighbours,v):
 key=''.join(neighbours)
 if key not in CAVE['shore']:
  ids=[];materials={'g':PACK['base']['grass'],'p':PACK['base']['dirt'],'r':ROCK,'m':FLOOR}
  for variant in range(4):
   tile=CELLS[PACK['base']['sea'][variant]].copy()
   def bank_pixel(px,py,material):tile.putpixel((px,py),CELLS[materials[material][variant]].getpixel((px,py)))
   for side,material in enumerate(neighbours[:4]):
    if material=='w':continue
    for span in range(16):
     for depth in range(2):
      px,py=[(span,depth),(15-depth,span),(span,15-depth),(depth,span)][side];bank_pixel(px,py,material)
   for material,(cx,cy,sx,sy)in zip(neighbours[4:],[(15,0,-1,1),(15,15,-1,-1),(0,15,1,-1),(0,0,1,1)]):
    if material=='w':continue
    for dy in range(3):
     for dx in range(3):
      if dx+dy<=2:bank_pixel(cx+sx*dx,cy+sy*dy,material)
   ids.append(len(CELLS));CELLS.append(tile)
  CAVE['shore'][key]=ids
 return CAVE['shore'][key][v]

def save_atlas():
 image=Image.new('RGBA',(512,math.ceil(len(CELLS)/32)*16))
 for i,tile in enumerate(CELLS):image.alpha_composite(tile,(i%32*16,i//32*16))
 path=ART/'side-terrain.png';image.save(path);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(path)],check=True)
 check=Image.open(path).convert('RGBA')
 assert all(check.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)).tobytes()==CELLS[i].tobytes()for i in range(ORIGINAL))
 write(ART/'side-terrain.json',{'source':'res://assets/battlefield-0.3.0/terrain.png','original_tile_count':ORIGINAL,'original_ids_and_pixels_preserved':True,'tile_count':len(CELLS),'tile_size':16,'columns':32,'transitions':CAVE,'floor_ids':FLOOR,'rock_ids':ROCK,'uses':'S11/S22 neutral gravel and dirt transitions, S12 exact continuous-river bank corners','size':list(image.size),'bytes':path.stat().st_size,'compression':'oxipng lossless; retain full atlas resolution'})
LOCK=['schema_version','id','code','name_zh','chapter','route','node','characters','player_positions','enemies','npc_units','terrain','enemy_group_ids','objects','reinforcements','reinforcement_turn','exit','boss_id','targets','goal','cause','before','during','after','absent_branch','optional','contract','ai_and_timing','escort_move']
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def hsh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def shortest(g,src,dest):
 w=len(g[0]);h=len(g);start=tuple(src);target=tuple(dest);q=deque([start]);seen={start:0}
 while q:
  x,y=q.popleft()
  if (x,y)==target:return seen[x,y]
  for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]:
   a,b=x+dx,y+dy
   if 0<=a<w and 0<=b<h and (a,b)not in seen and g[b][a]not in '^#~':seen[a,b]=seen[x,y]+1;q.append((a,b))
 return None
class Layout:
 def __init__(self,c):
  self.c=c;self.old=read(BASE/f'{c}.json');self.d=copy.deepcopy(self.old);self.w=self.d['map']['width'];self.h=self.d['map']['height'];self.g=[list(r)for r in self.old['logic_grid']];self.routes=[];self.rng=random.Random(bf.seed(c+'20261022'));self.fallbacks=[]
  self.actors={tuple(p)for p in self.d['player_positions']}|{tuple(u['position'])for group in ['enemies','npc_units','reinforcements']for u in self.d[group]}
  self.interactions={tuple(o['position'])for o in self.d['objects']}|{tuple(p)for o in self.d['objects']for p in o.get('approaches',[o['approach']]if'approach'in o else [])}
  self.protect=self.actors|self.interactions|{tuple(self.d['exit'])}|{tuple(p)for p in self.d['targets']}
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):self.g[y][x]=ch
 def ellipse(self,cx,cy,rx,ry,ch):
  for y in range(max(0,math.floor(cy-ry)),min(self.h,math.ceil(cy+ry+1))):
   for x in range(max(0,math.floor(cx-rx)),min(self.w,math.ceil(cx+rx+1))):
    if ((x-cx)/rx)**2+((y-cy)/ry)**2<1+.075*math.sin(x*.92+y*.61):self.g[y][x]=ch
 def path(self,pts,width=3,ch='p',name=''):
  for x,y in bf.route(pts):self.rect(x-width//2,y-width//2,x+(width-1)//2,y+(width-1)//2,ch)
  if name:self.routes.append({'name':name,'waypoints':[list(p)for p in pts],'width':width,'surface':ch})
 def structures(self):
  for m in self.d['art_modules']:
   if m.get('logic')=='#':
    for x,y in m['cells']:self.g[y][x]='#'
   elif m.get('logic')=='occupiable':
    x,y=m['origin'];self.g[y][x]='t'if m['name']=='tactical_fort'else'h'
 def design(self):
  if self.c=='S11':
   # Preserve the full cave walkable footprint. Authored cart tracks now make
   # the rescue route readable across the old unbroken cave-floor texture.
   self.g=[['.'if ch=='p'else ch for ch in row]for row in self.g]
   self.path([(0,12),(8,12),(8,20),(13,20),(13,16),(18,16),(18,8),(26,8),(26,0)],3,'p','救援入口与运矿主巷')
   self.path([(14,18),(22,18),(23,18),(23,12),(18,12)],2,'p','东侧绕岩支巷')
   self.path([(19,3),(26,3)],2,'p','矿口工具间与北侧出口')
   self.path([(17,14),(18,14)],2,'p','工具箱装卸短巷')
   self.path([(23,18),(26,18),(26,20)],2,'p','运矿车装卸口')
   self.path([(10,11),(11,11)],2,'p','工具箱侧廊')
   # Keep the established left lookout pocket accessible from the rescue lane.
   self.path([(8,12),(10,12),(10,9),(12,9),(12,8)],2,'p','西侧塌道岗口')
   self.structures()
   self.d['location_theme']='支木矿口、灰岩分室、运矿土径与北侧撤离巷'
   self.d['tactical_notes']=['西侧土径进入救援区域，暖色运矿主巷串起两组矿工、工具箱和北侧撤离口；工具间南门通过短巷接回出口。','岩脊保留主巷与东侧绕行支巷，两路在北部岩室汇合。矿工仍按现有护送规则等待危险解除后前进。']
  elif self.c=='S22':
   self.g=[['.'if ch=='p'else ch for ch in row]for row in self.g]
   self.path([(9,27),(9,18),(16,18),(16,12),(25,12),(25,5),(27,5),(27,0)],3,'p','避潮主巷与北侧出口')
   self.path([(16,18),(24,18),(24,17)],2,'p','旧船员藏身支室')
   self.path([(16,13),(17,13)],2,'p','遗物短巷')
   self.path([(16,12),(21,12),(21,4),(24,4)],2,'p','遗迹拱门内廊')
   self.path([(24,3),(27,3)],2,'p','避潮室门前路')
   self.path([(10,18),(10,12),(12,12)],2,'p','西潮潭岸路')
   self.path([(25,17),(25,12)],2,'p','藏身室东门接应道')
   self.structures()
   # Retain initial locked hideout cell and the two original tide basins.
   for y,row in enumerate(self.old['logic_grid']):
    for x,ch in enumerate(row):
     if ch=='~':self.g[y][x]='~'
   walls=[[22,y]for y in range(16,20)]+[[23,16],[24,16],[23,19],[24,19],[24,18]]
   for x,y in walls:self.g[y][x]='^'
   self.d['sailor_alcove']={'bounds':[22,16,24,19],'walls':walls,'door':[24,17],'approach':[25,17],'interior':[[23,17],[23,18]],'note':'原藏身处门格保持；开门后船员从东口接回北向主巷'}
   for o in self.d['objects']:
    if o['kind']in['rescue','door']:self.g[o['position'][1]][o['position'][0]]='#'
   self.d['location_theme']='碎石海洞、避潮土径、双潮潭与可穿行遗迹拱门'
   self.d['tactical_notes']=['灰褐洞底与暖色避潮土径区分岩室和主巷；遗物箱、旧船员藏身处、北侧避潮室均由完整道路串联。','遗迹拱门中央两格可以通行，两侧柱脚是实体；旧船员藏身石室从东侧门前救援，开门后接回北向主巷。西潮潭与东南潮水保留边界。']
  else:
   self.g=[['.']*self.w for _ in range(self.h)]
   for p in [(4,4,5,5),(3,8,4,3),(16,3,5,4),(29,20,5,4),(20,23,5,3),(3,21,3,4)]:self.ellipse(*p,'f')
   self.path([(10,25),(10,18),(17,18),(17,7),(24,7),(24,5),(29,5)],3,'p','药车主路与诊所前庭')
   self.path([(10,15),(5,15),(5,8),(13,8),(13,7),(24,7)],2,'p','西桥林间支路')
   self.path([(17,18),(25,18),(25,16)],2,'p','南岸村路')
   self.path([(24,7),(24,11),(22,11),(22,12)],2,'p','北岸渔舍小径')
   self.path([(8,21),(10,21)],2,'p','伤员接应口')
   self.rect(24,3,29,6,'p')
   waterpts=[(0,13),(10,13),(10,10),(21,10),(21,14),(33,14)]
   self.path(waterpts,2,'~')
   channel=[[x,y]for y in range(self.h)for x in range(self.w)if self.g[y][x]=='~']
   bridges=[{'id':'west_village_bridge','bounds':[4,11,5,14],'width':2},{'id':'medicine_bridge','bounds':[16,8,18,11],'width':3}]
   for b in bridges:self.rect(*b['bounds'],'s')
   self.d['river_layout']={'channel':channel,'waypoints':[list(p)for p in waterpts],'bridges':bridges,'shore_rendering':'inside_water_cells','revision':'map-polish-20261022'}
   self.structures()
   self.d['location_theme']='林村诊所、连续弯溪、双木桥与宽阔药车道'
   self.d['tactical_notes']=['药车沿南岸三格宽主路接上中部木桥，桥面真正跨过连续溪流；西侧双格木桥连接林间支路，两岸都有明确桥头。','诊所南门、药车交接前庭与北岸渔舍都接回道路。树林集中在道路外侧，入口和桥头保留布阵空地；南岸村路可接近封路士兵。']
  # No starting actor may be buried by a new forest, river, bridge edge or wall.
  for x,y in self.actors:
   if self.g[y][x]in'^#~f':self.g[y][x]='p'if self.old['logic_grid'][y][x]=='p'else'.'
  for x,y in [self.d['exit']]+self.d['targets']:
   locked=any(o['kind']in['door','rescue']and o['position']==[x,y]for o in self.d['objects'])
   if self.g[y][x]in'^#~'and not locked:self.g[y][x]='p'
  for o in self.d['objects']:
   for x,y in o.get('approaches',[]):self.g[y][x]='p'
 def shore(self,ground,x,y,v):
  neighbours=[]
  for dx,dy in [(0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)]:
   q=ground[y+dy][x+dx]if 0<=x+dx<self.w and 0<=y+dy<self.h else'~'
   neighbours.append('w'if q in '~s'else'p'if q=='p'else'r'if q=='^'else'm'if self.c in['S11','S22']else'g')
  return native_shore(neighbours,v)
 def render(self):
  c=self.c;g=self.g;w=self.w;h=self.h
  ground=[[('p'if c in ['S11','S22']else'.')if q=='#'else('p'if q in'ht'else q)for q in row]for row in g]
  # The mine mouth and crates keep the same ground as their approach.
  base=[]
  for y in range(h):
   row=[]
   for x in range(w):
    q=ground[y][x];v=bf.seed(f'{c}:{x}:{y}')%4
    material=bf.MATERIAL[q]
    if q=='f':material='grass'
    if c in['S11','S22']and q=='.':material='marsh'
    tile=PACK['base'][material][v]
    if q=='p':tile=(CAVE['path']if c in['S11','S22']else TRANS['path'])[str(bf.mask_at(ground,x,y,lambda t:t in'ps'))][v]
    if q=='s':
     mask=sum(bit for dx,dy,bit in [(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s')
     tile=TRANS['walkway']['v'+str(mask)][v]
    if q=='~':tile=self.shore(ground,x,y,v)
    if q=='^':tile=(CAVE['rock']if c in['S11','S22']else TRANS['mountain_ground']['grass'])[str(bf.mask_at(ground,x,y,lambda t:t=='^'))][v]
    row.append(tile)
   base.append(row)
  nature=[];protected=self.protect.copy()
  # Protect entire solid buildings as well as the approach of each entrance.
  for m in self.d['art_modules']:protected.update(tuple(p)for p in m.get('cells',[]))
  for typ,kinds,small in [('f',['pine_tall','pine_broad','pine_young','pine_pair'],['pine_small_a','pine_small_b']),('^',['peak_low','crag_tall','ridge_bent','outcrop'],['boulder'])]:
   allowed={(x,y)for y in range(h)for x in range(w)if g[y][x]==typ};used=set();positions=sorted(allowed);self.rng.shuffle(positions)
   # Broad groups read as woodland/rock walls, with small accents in gaps.
   for x,y in positions:
    if (x,y)in used or self.rng.random()<.20:continue
    key=self.rng.choice(kinds);sw,sh=NATURE[key]['size'];fw=math.ceil(sw/16);fh=math.ceil(sh/16)
    foot={(a,b)for b in range(y,y+fh)for a in range(x,x+fw)}
    if not foot<=allowed or foot&protected or foot&used:continue
    nature.append({'key':key,'position':[x*16,y*16],'flip':self.rng.random()<.5});used|=foot
   for x,y in sorted(allowed-used-protected):
    # Rock accents are sparse inside deep massif, denser on the visible lip.
    lip=any(0<=x+dx<w and 0<=y+dy<h and g[y+dy][x+dx]!=typ for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)])
    if typ=='^'and self.rng.random()>(.70 if lip else .28):continue
    if typ=='f'and self.rng.random()<.12:continue
    nature.append({'key':self.rng.choice(small),'position':[x*16,y*16],'flip':self.rng.random()<.5})
  if c=='S22':
   # Every cell of the narrow alcove rim has a visible full native boulder.
   for x,y in self.d['sailor_alcove']['walls']:
    if not any(p['position']==[x*16,y*16]for p in nature):nature.append({'key':'boulder','position':[x*16,y*16],'flip':False})
  self.d.update(map={'width':w,'height':h,'tiles':[bf.IDS[q]for row in g for q in row]},logic_grid=[''.join(r)for r in g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*w for _ in range(h)],[[None]*w for _ in range(h)]],natural_props=nature,tactical_routes=self.routes,art_style_version='map-polish-20261022',tactical_review_version='0.10.2')
  self.d['production_anchors']['revision']='0.10.2'
  self.d['art_atlas']='res://assets/map-polish-20261022/side-terrain.png'
  if c in['S11','S22']:self.d['nature_layout']['biome']='marsh'
  for k in LOCK:assert self.d.get(k)==self.old.get(k),(c,k,'changed gameplay field')
  before=self.old['logic_grid'];after=self.d['logic_grid'];paths=[]
  before_open=[list(r)for r in before];after_open=[list(r)for r in after]
  for obj in self.d['objects']:
   if obj['kind']in['door','rescue']:
    for x,y in obj.get('opens',[obj['position']]):before_open[y][x]='p';after_open[y][x]='p'
  for u in self.d['npc_units']:
   if u.get('quest_kind')not in ['escort','medicine','sailor']:continue
   goal=self.d['targets'][0]if u.get('quest_kind')=='medicine'else self.d['exit']
   a=shortest(before_open,u['position'],goal);b=shortest(after_open,u['position'],goal);assert b is not None and b<=a,(c,u['id'],a,b)
   paths.append({'unit':u['id'],'before':a,'after':b,'goal':goal})
  source=self.d['player_positions'][0]
  opened=[list(row)for row in after]
  for obj in self.d['objects']:
   if obj['kind']in['door','rescue']:
    for x,y in obj.get('opens',[obj['position']]):opened[y][x]='p'
  anchors=self.d['player_positions']+self.d['targets']+[self.d['exit']]+[u['position']for group in ['enemies','npc_units','reinforcements']for u in self.d[group]]+[p for o in self.d['objects']for p in o.get('approaches',[])]
  unreachable=[p for p in anchors if shortest(opened,source,p)is None];assert not unreachable,(c,unreachable)
  for m in self.d['art_modules']:
   if m.get('logic')=='#':assert all(g[y][x]=='#'for x,y in m['cells']),(c,m['name'],'solid structure mismatch')
  if c=='S22':
   alcove=self.d['sailor_alcove'];assert all(shortest(after,source,p)is None for p in alcove['interior']),'Unopened shelter is not enclosed'
   assert shortest(after,source,alcove['approach'])is not None,'East rescue approach is blocked'
   assert all(shortest(after_open,p,self.d['exit'])is not None for p in alcove['interior']),'Rescued sailor cannot escape'
  if c=='S12':
   channel={tuple(p)for p in self.d['river_layout']['channel']};bridgecells={(x,y)for b in self.d['river_layout']['bridges']for y in range(b['bounds'][1],b['bounds'][3]+1)for x in range(b['bounds'][0],b['bounds'][2]+1)}
   assert all(g[y][x]=='~'or(x,y)in bridgecells for x,y in channel),'River covered by nonbridge land'
   for bridge in self.d['river_layout']['bridges']:
    x0,y0,x1,y1=bridge['bounds'];assert any((x,y)in channel for y in range(y0,y1+1)for x in range(x0,x1+1))
    assert all(g[y0-1][x]not in'^#~'and g[y1+1][x]not in'^#~'for x in range(x0,x1+1)),'Bridge head does not join land'
  return {'code':c,'passed':True,'unchanged_gameplay_fields':LOCK,'escort_paths':paths,'reachable_anchors':len(anchors),'nature_props':len(nature),'terrain_changes':sum(a!=b for rowa,rowb in zip(before,after)for a,b in zip(rowa,rowb)),'shore_fallbacks':self.fallbacks}
records=[];layouts=[]
for c in ['S11','S12','S22']:
 layout=Layout(c);layout.design();records.append(layout.render());layouts.append(layout)
save_atlas()
for layout,record in zip(layouts,records):
 path=R/f'data/stages/{layout.c}.json';write(path,layout.d);record['map_sha256']=hsh(path)
write(OUT/'geometry.json',{'passed':True,'stages':records,'notes':'Source current-map baseline, unchanged all story and actor data. Walkability checks use blocked rock/wall/water; actual gameplay replays performed by parent.'})
print(json.dumps(records,ensure_ascii=False,indent=2))
