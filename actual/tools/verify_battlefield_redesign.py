#!/usr/bin/env python3
"""Geometry/resource acceptance for every revised battlefield, no victories set."""
from pathlib import Path
from collections import deque
import hashlib,json,math
from PIL import Image

R=Path(__file__).resolve().parents[1]
OUT=R/'reports/battlefield-0.3.0'
IDS={'.':48,'p':48,'n':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'c':208,'s':191,'b':66,'+':218,'h':208,'t':218}

def main():
 errors=[];records=[];checks=0
 def check(ok,message):
  nonlocal checks
  checks+=1
  if not ok:errors.append(message)
 atlas=json.loads((R/'assets/battlefield-0.3.0/terrain.json').read_text())
 old_rock=set(range(52,56))|{t for values in atlas['transitions']['rock_coast'].values() for t in values}
 mountain={t for family in atlas['transitions']['mountain_ground'].values() for values in family.values() for t in values}
 shore={t:key for key,values in atlas['transitions']['shore_water'].items() for t in values}
 beach={t for values in atlas['transitions']['beach_grass'].values() for t in values}
 walkway={t for values in atlas['transitions']['walkway'].values() for t in values}
 legacy_sand={t for values in atlas['coasts']['sand'].values() for t in values}
 for path in sorted((R/'data/stages').glob('*.json')):
  d=json.loads(path.read_text());code=d['code'];w=d['map']['width'];h=d['map']['height'];grid=d['logic_grid']
  check(len(grid)==h and all(len(row)==w for row in grid),code+' grid dimensions')
  check(d['map']['tiles']==[IDS[q] for row in grid for q in row],code+' terrain semantics')
  ground=d['visual_ground'];check(len(ground)==h and all(len(row)==w for row in ground),code+' visual ground dimensions')
  check(all(q not in '#ht' for row in ground for q in row),code+' collision and building symbols never choose terrain artwork')
  check(not any(t in old_rock for row in d['art_layers'][0] for t in row),code+' no violet rock or legacy coast fragments')
  check(all((d['art_layers'][0][y][x] in mountain)==(ground[y][x]=='^') for y in range(h) for x in range(w)),code+' mountain artwork confined to actual rocky ground')
  check(all(ground[y][x]==grid[y][x] for y in range(h) for x in range(w) if grid[y][x] not in '#ht'),code+' visual fix cannot reclassify normal walkable ground')
  if code not in ['F21','F22','S21']:
   check(not any(t in legacy_sand for row in d['art_layers'][0] for t in row),code+' automatic broken sand border removed')
   check(all((d['art_layers'][0][y][x] in walkway)==(ground[y][x]=='s') for y in range(h) for x in range(w)),code+' boardwalk artwork matches actual wooden terrain only')
   check(all((d['art_layers'][0][y][x] in beach)==(ground[y][x]=='d') for y in range(h) for x in range(w)),code+' sand/grass transition belongs to actual beach terrain')
   check(all(ground[y][x]=='~' for y in range(h) for x in range(w) if d['art_layers'][0][y][x] in shore),code+' bank/water tile never painted over walkable land')
   check(all(any(0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='d' for dx,dy in [(0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)]) for y in range(h) for x in range(w) if 'a' in shore.get(d['art_layers'][0][y][x],'')),code+' wet sand exists only beside a real beach')
  if code=='M15':
   check(all(ground[y][x]=='~' for y in range(12,16) for x in range(39,43)),'M15 offshore cliff transparent areas retain continuous sea')
  for layer in d['art_layers']:
   check(len(layer)==h and all(len(row)==w for row in layer),code+' art dimensions')
   check(all(t is None or 0<=t<atlas['tile_count'] for row in layer for t in row),code+' tile range')
  opened={tuple(p) for o in d['objects'] for p in o.get('opens',[o['position']] if o['kind'] in ['door','rescue'] else [])}
  source=tuple(d['player_positions'][0]);seen={source};queue=deque([source]);dist={source:0}
  while queue:
   x,y=queue.popleft()
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    p=x+dx,y+dy
    if 0<=p[0]<w and 0<=p[1]<h and p not in seen and (grid[p[1]][p[0]] not in '~^#' or p in opened):seen.add(p);dist[p]=dist[x,y]+1;queue.append(p)
  starts=d['player_positions']+[d['exit']]+[u['position'] for u in d['enemies']+d['npc_units']+d['reinforcements']]
  missing=[p for p in starts if tuple(p) not in seen]
  check(not missing,code+' disconnected actor/exit: '+str(missing))
  for o in d['objects']:
   if o['kind']=='visit':
    check(tuple(o['approach']) in seen,code+' inaccessible front door '+o['id'])
    check(o['approach']==[o['position'][0],o['position'][1]+1],code+' ambiguous entrance '+o['id'])
    check(o.get('door_visual')=='native_building_art' and 'sprite_path' not in o and 'sprite' not in o,code+' detached visit-door overlay')
    fronts=o.get('approaches',[o['approach']]);check(1<=len(fronts)<=2 and len(set(map(tuple,fronts)))==len(fronts),code+' ambiguous native doorway fronts')
    for p in fronts:
     check(tuple(p) in seen and grid[p[1]][p[0]] not in '~^#',code+' unreachable native doorway front')
     check(p[1]==o['position'][1]+1 and [p[0],p[1]-1] in o['entrance_cells'],code+' doorway front not aligned with native entrance')
   x,y=o['position'];check(any((x+dx,y+dy) in seen for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]),code+' unreachable object '+o['id'])
  occupied=[]
  for u in d['enemies']+d['npc_units']:
   p=tuple(u['position']);check(p not in occupied and p not in map(tuple,d['player_positions']),code+' overlapping unit '+u['id']);occupied.append(p)
   check(grid[p[1]][p[0]] not in '~^#',code+' unit on blocked ground '+u['id'])
  for site in d.get('building_sites',[]):
   x,y=site['position'];check(grid[y][x] in 'ht',code+' blocked occupation building')
   check((x,y) in seen,code+' occupiable building unreachable by ground units: '+str([x,y]))
   check(any(ground[y+dy][x+dx] in 'ps=c' for dx,dy in [(0,0),(0,-1),(1,0),(0,1),(-1,0)]),code+' occupiable building detached from a functional road/deck: '+str([x,y]))
  for m in d['art_modules']:
   x,y=m['origin'];mw,mh=m['footprint'];check(x>=0 and y>=0 and x+mw<=w and y+mh<=h,code+' cut module '+m['name'])
   if m['logic']=='#':check(all(grid[yy][xx]=='#' for xx,yy in m['cells']),code+' visible solid without collision '+m['name'])
  for p in d.get('art_props',[]):
   f=R/p['path'].removeprefix('res://');check(f.is_file(),code+' missing '+str(f))
   if f.is_file():
    with Image.open(f) as im:sw,sh=im.size
    x,y=p['position'];check(0<=x and 0<=y and x+sw<=w*16 and y+sh<=h*16,code+' partial prop '+f.name)
  contact=min(dist.get(tuple(u['position']),99999) for u in d['enemies'])
  check(contact>=12,code+' no deployment movement interval')
  for boat in d.get('event_boats',[]):
   check(all(grid[y][x]=='~' for x,y in boat['path']),code+' boat route crosses land')
   check(all(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(boat['path'],boat['path'][1:])),code+' discontinuous boat route')
  if code=='M11':
   river=d['river_layout'];channel=set(map(tuple,river['channel']))
   reached={next(iter(channel))};pending=deque(reached)
   while pending:
    x,y=pending.popleft()
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
     q=x+dx,y+dy
     if q in channel and q not in reached:reached.add(q);pending.append(q)
   check(reached==channel and any(x==0 for x,y in channel) and any(x==w-1 for x,y in channel),'M11 river connected between both map edges')
   check(all(grid[y][x] in '~s' for x,y in channel),'M11 road/land cannot cover the channel')
   bridges=[]
   for b in river['bridges']:
    x0,y0,x1,y1=b['bounds'];cells={(x,y) for y in range(y0,y1+1) for x in range(x0,x1+1)};bridges.append(cells)
    check(all(grid[y][x]=='s' for x,y in cells) and bool(cells&channel),'M11 complete bridge over actual water '+b['id'])
   def walk_without(blocked):
    done={source};todo=deque([source])
    while todo:
     x,y=todo.popleft()
     for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
      q=x+dx,y+dy
      if 0<=q[0]<w and 0<=q[1]<h and q not in done and q not in blocked and grid[q[1]][q[0]] not in '~^#':done.add(q);todo.append(q)
    return tuple(d['exit']) in done
   check(not walk_without(set.union(*bridges)),'M11 river is a real movement barrier')
   check(all(walk_without(b) for b in bridges),'M11 either bridge independently leads to the exit')
   water_ids={t for values in atlas['transitions']['winter_river'].values() for t in values}
   check(all((d['art_layers'][0][y][x] in water_ids)==(grid[y][x]=='~') for y in range(h) for x in range(w)),'M11 water art confined to water cells')
  if code=='M14':
   controls=[o for o in d['objects'] if o['kind']=='control']
   check(len(controls)==2 and len(d['camp_checkpoints'])==2,'M14 two authored road checkpoints')
   for gate,obj in zip(d['camp_checkpoints'],controls):
    opening=list(map(tuple,gate['opening']))
    check(tuple(obj['position']) in opening and obj['position'] in d['targets'],'M14 control flag lies inside its actual road opening')
    check(all(grid[y][x]=='p' and (x,y) in seen for x,y in opening),'M14 complete road width passes between palisades')
    check(obj.get('sprite')=='white_flag' and obj.get('persistent_visual',False),'M14 control never masquerades as a detached open gate')
    fences=[]
    for x,y in gate['fences']:
     cells={(x+i,y) for i in range(3)};fences.append(cells)
     check(all(grid[yy][xx]=='#' for xx,yy in cells),'M14 visible palisade has matching collision')
    check(max(x for x,y in fences[0])+1==min(x for x,y in opening) and max(x for x,y in opening)+1==min(x for x,y in fences[1]),'M14 palisades directly frame the road without invisible gap pieces')
   check(not any(m['name']=='north_fence' for m in d['art_modules']),'M14 old isolated grove fence removed')
  records.append({'code':code,'size':[w,h],'ground_reachable':len(seen),'nearest_enemy_path_steps':contact,'map_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'missing':missing})
 for m in json.loads((R/'assets/battlefield-0.3.0/modules.json').read_text())['modules']:
  p=R/m['path'].removeprefix('res://')
  with Image.open(p) as im:
   im=im.convert('RGBA');check(im.getchannel('A').getextrema()==(0,255),'module lacks alpha '+m['name']);box=im.getbbox()
   if m['name'].startswith('tactical_'):
    check(im.size==(16,16) and max(box[2]-box[0],box[3]-box[1])==16 and min(box[2]-box[0],box[3]-box[1])>=12,'undersized tactical architecture '+m['name'])
    check(m.get('whole_source',False),'tactical silhouette must fit from its whole source '+m['name'])
   else:check(box[0]>0 and box[1]>0 and box[2]<im.width and box[3]<im.height,'cut alpha '+m['name'])
 result={'passed':not errors,'checks':checks,'errors':errors,'stages':records}
 (OUT/'geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
 raise SystemExit(0 if not errors else 1)

if __name__=='__main__':main()
