#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scene-authored M14/M15 polish from the preserved 2026-10-22 baseline.

No atlas, actor, objective or combat-rule mutation. Roads keep their original
movement category; new architecture has matching collision and clear fronts.
"""
from pathlib import Path
from collections import deque
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1]
OUT=R/'reports/map-polish-20261022'
BASE=OUT/'baseline'
spec=importlib.util.spec_from_file_location('terrain_library',R/'tools/redesign_battlefields.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
ATLAS=json.loads((R/'assets/battlefield-0.3.0/terrain.json').read_text())
NATURE=lib.NATURE;PACK=lib.PACK

def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def connected(d,grid):
 w,h=d['map']['width'],d['map']['height'];opened={tuple(p)for o in d['objects']for p in o.get('opens',[o['position']]if o['kind']in ['door','rescue']else[])}
 todo=deque([tuple(d['player_positions'][0])]);seen=set(todo);distance={todo[0]:0}
 while todo:
  x,y=todo.popleft()
  for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]:
   p=x+dx,y+dy
   if 0<=p[0]<w and 0<=p[1]<h and p not in seen and (grid[p[1]][p[0]]not in '~^#'or p in opened):seen.add(p);todo.append(p);distance[p]=distance[x,y]+1
 return seen,distance

class Plan:
 def __init__(self,code):
  self.code=code;self.old=read(BASE/f'{code}.json');self.d=copy.deepcopy(self.old);self.w=self.d['map']['width'];self.h=self.d['map']['height']
  self.grid=[list(r)for r in self.d['logic_grid']];self.ground=[list(r)for r in self.d['visual_ground']];self.changes=[]
  self.anchors={tuple(p)for p in self.d['player_positions']+[self.d['exit']]+self.d['targets']+[u['position']for key in ['enemies','npc_units','reinforcements']for u in self.d[key]]}
  for o in self.d['objects']:
   self.anchors.add(tuple(o['position']))
   self.anchors.update(map(tuple,o.get('approaches',[o['approach']]if 'approach'in o else [])))
  self.protected={p for a in self.anchors for p in [(a[0]+dx,a[1]+dy)for dx,dy in [(0,0),(0,-1),(1,0),(0,1),(-1,0)]]}
 def paint(self,x,y,ch):
  if not(0<=x<self.w and 0<=y<self.h):return
  # Solid existing architecture and water retain their original geometry.
  if self.grid[y][x] in '#~^':return
  if self.grid[y][x]not in 'ht':self.grid[y][x]=ch
  self.ground[y][x]=ch
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):self.paint(x,y,ch)
 def road(self,points,width=2,surface='p',name=''):
  for x,y in lib.route(points):self.rect(x-width//2,y-width//2,x+(width-1)//2,y+(width-1)//2,surface)
  if name:self.d['tactical_routes'].append({'name':name,'waypoints':[list(p)for p in points],'width':width,'surface':surface})
 def grove(self,cx,cy,rx,ry):
  for y in range(max(0,math.floor(cy-ry)),min(self.h,math.ceil(cy+ry)+1)):
   for x in range(max(0,math.floor(cx-rx)),min(self.w,math.ceil(cx+rx)+1)):
    if self.grid[y][x]!='.' or (x,y)in self.protected:continue
    if ((x-cx)/rx)**2+((y-cy)/ry)**2<1+.12*math.sin(x*1.3+y*.5):self.paint(x,y,'f')
 def building(self,name,x,y,purpose,front_surface='p'):
  m=lib.MODULES[name];w,h=m['footprint'];cells={(xx,yy)for yy in range(y,y+h)for xx in range(x,x+w)}
  assert not(cells&self.protected),(self.code,name,'protected',cells&self.protected)
  assert all(self.grid[yy][xx]in '.f'for xx,yy in cells),(self.code,name,'only unused ground',[(p,self.grid[p[1]][p[0]])for p in cells])
  for xx,yy in cells:self.grid[yy][xx]='#';self.ground[yy][xx]=front_surface
  self.d['art_modules'].append({'name':name,'origin':[x,y],'footprint':[w,h],'logic':'#','cells':[list(p)for p in sorted(cells)],'walk_through_cells':[],'runtime_prop':True,'purpose':purpose})
  self.d['art_props'].append({'path':m['path'],'position':[x*16,y*16]})
  self.rect(x,y+h,x+w-1,y+h,front_surface)
  self.changes.append({'building':name,'origin':[x,y],'footprint':[w,h],'purpose':purpose})
 def wall(self,x,y):
  cells={(xx,y)for xx in range(x,x+4)}
  assert not(cells&self.protected),(self.code,'wall actors')
  assert all(self.grid[yy][xx]in '.#'for xx,yy in cells),(self.code,'wall road collision')
  for xx,yy in cells:self.grid[yy][xx]='#';self.ground[yy][xx]='.'
  self.d['art_modules'].append({'name':'north_wall','origin':[x,y],'footprint':[4,1],'logic':'#','cells':[list(p)for p in sorted(cells)],'walk_through_cells':[],'runtime_prop':True,'purpose':'相接的旧堡防线，正门与西侧绕行口保留'})
  self.d['art_props'].append({'path':lib.MODULES['north_wall']['path'],'position':[x*16,y*16]})
 def rubble_wall(self,x,y):
  name='breached_wall';m=lib.MODULES[name];w,h=m['footprint'];cells={(xx,yy)for yy in range(y,y+h)for xx in range(x,x+w)}
  assert not cells&self.protected,(self.code,'rubble actors',cells&self.protected)
  assert all(self.grid[yy][xx]in '.#'for xx,yy in cells),(self.code,'rubble does not cover road')
  remove=[a for a in self.d['art_modules']if a['name']=='north_wall'and set(map(tuple,a['cells']))<=cells]
  positions={tuple(a['origin'])for a in remove};self.d['art_modules']=[a for a in self.d['art_modules']if a not in remove]
  self.d['art_props']=[a for a in self.d['art_props']if not (a['path'].endswith('/north_wall.png')and (a['position'][0]//16,a['position'][1]//16)in positions)]
  for xx,yy in cells:self.grid[yy][xx]='#';self.ground[yy][xx]='.'
  self.d['art_modules'].append({'name':name,'origin':[x,y],'footprint':[w,h],'logic':'#','cells':[list(p)for p in sorted(cells)],'walk_through_cells':[],'runtime_prop':True,'purpose':'旧堡残存墙翼，完整废墟轮廓对应不可站立的碎石占地'})
  self.d['art_props'].append({'path':m['path'],'position':[x*16,y*16]})
  self.changes.append({'building':name,'origin':[x,y],'footprint':[w,h],'purpose':'旧堡残墙与其完整阻挡占地'})
 def render(self):
  t=ATLAS['transitions'];base=copy.deepcopy(self.old['art_layers'][0])
  field=lib.Battlefield.__new__(lib.Battlefield);field.w=self.w;field.h=self.h;field.routes=self.d['tactical_routes']
  for y in range(self.h):
   for x in range(self.w):
    ch=self.ground[y][x];v=lib.seed(f'{self.code}:{x}:{y}')%4
    # Coastline is deliberately unchanged. Its approved bank tiles remain exact.
    if ch in '~^':continue
    material='grass'if ch=='f'else lib.MATERIAL[ch];tile=PACK['base'][material][v]
    if ch=='p':tile=t['path'][str(lib.mask_at(self.ground,x,y,lambda q:q in 'ps'))][v]
    elif ch=='s':
     mask=sum(bit for dx,dy,bit in [(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<self.w and 0<=y+dy<self.h and self.ground[y+dy][x+dx]=='s')
     tile=t['walkway'][field.timber_axis(x,y,self.ground)+str(mask)][v]
    base[y][x]=tile
  self.d['art_layers'][0]=base
  # Retain approved rocky outcrops; regenerate whole trees in authored groves.
  natural=[]
  for p in self.old['natural_props']:
   if p['key'].startswith(('peak','crag','ridge','outcrop')):natural.append(p)
  allowed={(x,y)for y in range(self.h)for x in range(self.w)if self.grid[y][x]=='f'}
  rng=random.Random(lib.seed(self.code+'-20261022-groves'));used=set()
  positions=sorted(allowed);rng.shuffle(positions)
  for x,y in positions:
   if (x,y)in used or rng.random()<.19:continue
   key=rng.choice(['pine_tall','pine_broad','pine_pair','pine_young']);sw,sh=NATURE[key]['size'];fw,fh=math.ceil(sw/16),math.ceil(sh/16)
   cells={(xx,yy)for yy in range(y,y+fh)for xx in range(x,x+fw)}
   if not cells<=allowed or cells&self.protected or cells&used:continue
   natural.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});used|=cells
  # Small edge trees make the extent readable while leaving small natural gaps.
  for x,y in sorted(allowed-used-self.protected):
   if rng.random()<.18:continue
   natural.append({'key':rng.choice(['pine_small_a','pine_small_b']),'position':[x*16,y*16],'flip':rng.random()<.5})
  self.d['natural_props']=natural
  self.d['logic_grid']=[''.join(row)for row in self.grid];self.d['visual_ground']=[''.join(row)for row in self.ground]
  self.d['map']['tiles']=[lib.IDS[ch]for row in self.grid for ch in row]
  self.d['tactical_review_version']='0.10.2';self.d['art_style_version']='map-polish-20261022';self.d['production_anchors']['revision']='0.10.2'
 def validate(self):
  for key in ['player_positions','enemies','npc_units','reinforcements','objects','exit','targets','boss_id','goal','before','during','after','terrain','reinforcement_turn']:
   assert self.d[key]==self.old[key],(self.code,key,'gameplay invariant')
  cats=self.d['terrain']['tile_categories']
  for pos in self.d['player_positions']+[u['position']for key in ['enemies','npc_units','reinforcements']for u in self.d[key]]:
   i=pos[1]*self.w+pos[0];assert cats[str(self.d['map']['tiles'][i])]==cats[str(self.old['map']['tiles'][i])],(self.code,'actor starting terrain changed',pos)
  seen,dist=connected(self.d,self.grid);oldseen,olddist=connected(self.old,self.old['logic_grid'])
  missing=[p for p in self.anchors if p not in seen and self.grid[p[1]][p[0]]!='#'];assert not missing,(self.code,'disconnected',missing)
  for o in self.d['objects']:
   p=tuple(o['position']);fronts=o.get('approaches',[o['approach']]if 'approach'in o else [list(p)]if not o.get('adjacent',False)else [[p[0]+dx,p[1]+dy]for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]])
   assert any(tuple(a)in seen for a in fronts),(self.code,'object blocked',o['id'])
  assert all(self.grid[y][x]not in '~^#'for x,y in self.d['player_positions'])
  for m in self.d['art_modules']:
   if m['logic']=='#':assert all(self.grid[y][x]=='#'for x,y in m['cells']),(self.code,'module collision',m)
  # New roads must not break or lengthen the known positional race to the north.
  assert dist[tuple(self.d['exit'])]<=olddist[tuple(self.d['exit'])]+2,(self.code,'exit route detour')
  for y in range(self.h):
   for x in range(self.w):
    assert (self.ground[y][x]=='~')==(self.old['visual_ground'][y][x]=='~'),(self.code,'shore changed')
  return {'code':self.code,'passed':True,'size':[self.w,self.h],'new_buildings':self.changes,'reachable':len(seen),'exit_steps_before':olddist[tuple(self.d['exit'])],'exit_steps_after':dist[tuple(self.d['exit'])],'actors_objectives_stats_unchanged':True,'old_coastline_preserved':True,'new_forest_cells':sum(self.grid[y][x]=='f'and self.old['logic_grid'][y][x]!='f'for y in range(self.h)for x in range(self.w)),'changed_cells':sum(self.grid[y][x]!=self.old['logic_grid'][y][x]for y in range(self.h)for x in range(self.w))}

def main():
 reports=[]
 for code in ['M14','M15']:
  p=Plan(code)
  if code=='M14':
   # Clear headquarters lane, central parade/service strip and south supply court.
   p.road([(25,5),(25,8)],2,name='文书帐门前通道')
   p.road([(20,8),(20,16)],2,name='营帐间勤务道')
   p.rect(18,8,21,10,'p')
   p.building('command_pavilion',22,10,'中营寝帐，门前朝南连接勤务道')
   p.building('command_pavilion',22,13,'南营值守帐，面向南哨卡内侧')
   p.road([(20,12),(24,12)],2,name='中营帐前横道')
   p.rect(27,24,29,25,'p');p.road([(28,23),(28,25)],2,name='东营补给小院')
   for grove in [(11,3,3.5,3),(3,25,2.5,3.5),(15,20,2.6,2.1),(24,29,3.6,2.1),(38,25,1.4,4)]:p.grove(*grove)
   p.d['location_theme']='山口旧哨堡、两道道路军旗哨卡、林带包围的三组营帐与勤务道'
   p.d['tactical_notes']=[p.old['tactical_notes'][0],'文书帐门前路接入北营横道；营帐朝向中间勤务道，南北道路贯通。树林集中在山脚与营盘外围，不遮挡旗点和建筑门前格。']
  else:
   # Readable keep forecourt linked to barracks, inner parade court and the north arch.
   p.building('barracks',12,4,'旧堡守军营房，南面入口连接档案室前路')
   p.road([(13,6),(19,6),(24,6),(24,10)],2,name='营房与档案室前路')
   p.rect(17,5,26,6,'c');p.rect(22,7,26,8,'c')
   p.road([(24,7),(30,7),(30,3)],2,name='中庭通往北闸的石路',surface='c')
   p.road([(29,6),(34,6),(34,5),(38,5)],2,name='北侧沿岸退路')
   p.rect(23,7,25,16,'c')
   # Existing bastions become two connected wall wings; the broad assault gap stays open.
   p.wall(31,18);p.rubble_wall(9,16);p.rubble_wall(30,16)
   p.building('quay_warehouse',30,20,'港侧装卸货仓，南面院地连接木栈廊')
   p.rect(30,22,35,23,'p');p.road([(32,23),(34,23),(36,23)],2,name='港仓装卸短道')
   for grove in [(11,3,1.8,1.5),(16,8,1.4,2),(30,12,2.1,1.6),(12,19,2.2,2.1),(16,23,2.1,1.1),(3,25,1.7,2.2)]:p.grove(*grove)
   p.d['location_theme']='海峡旧塔堡、相接的堡墙与双层中庭、营房档案前路、港仓木栈廊'
   p.d['tactical_notes']=[p.old['tactical_notes'][0],'北堡档案室、守军营房、中庭与北侧退路由明确道路相连。东侧货仓设装卸院并接木栈廊，正面堡墙保留宽阔缺口与西侧绕行通道。']
  p.render();record=p.validate();write(R/f'data/stages/{code}.json',p.d);record['sha256']=hashlib.sha256((R/f'data/stages/{code}.json').read_bytes()).hexdigest();reports.append(record)
 write(OUT/'camp-fort-geometry.json',{'passed':True,'maps':reports,'scope':'地图几何与资源检查；实际按键试玩由主任务统一执行。'})
 print(json.dumps(reports,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
