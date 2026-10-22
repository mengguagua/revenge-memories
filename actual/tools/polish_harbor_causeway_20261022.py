#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F25 working harbor and F26 inhabited causeway; keep mission rules intact."""
from pathlib import Path
from collections import deque
from PIL import Image
import copy,hashlib,importlib.util,json,math,subprocess
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('camp_fort_polish',R/'tools/polish_camp_fort_20261022.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
lib=base.lib;OUT=base.OUT;ART=R/'assets/map-polish-20261022'
ATLAS=json.loads((ART/'harbor-shore.json').read_text())if(ART/'harbor-shore.json').exists()else copy.deepcopy(base.ATLAS)
image=Image.open(ART/'harbor-shore.png'if(ART/'harbor-shore.png').exists()else R/'assets/battlefield-0.3.0/terrain.png').convert('RGBA')
CELLS=[image.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16))for i in range(ATLAS['tile_count'])]
MOUNTAIN=[CELLS[i] for i in ATLAS['transitions']['mountain_ground']['grass']['255']]
SHORE={'cells':CELLS,'transitions':ATLAS['transitions'],'mountain':MOUNTAIN}
RELOCATIONS={'sailors0':[35,19],'sailors1':[37,19]}

class HarborPlan(base.Plan):
 def direct(self,x,y,ch):
  assert 0<=x<self.w and 0<=y<self.h
  self.grid[y][x]=ch;self.ground[y][x]=ch
 def water(self,x0,y0,x1,y1):
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):
    if self.grid[y][x]in '.p~'and(x,y)not in self.protected:self.direct(x,y,'~')
 def new_island(self,cx,cy,rx,ry):
  water_paths={tuple(p)for boat in self.d.get('event_boats',[])for p in boat['path']}
  for y in range(max(0,math.floor(cy-ry)),min(self.h,math.ceil(cy+ry)+1)):
   for x in range(max(0,math.floor(cx-rx)),min(self.w,math.ceil(cx+rx)+1)):
    if self.grid[y][x]=='~'and(x,y)not in water_paths and ((x-cx)/rx)**2+((y-cy)/ry)**2<1+.05*math.sin(x+y):self.direct(x,y,'.')
 def prison(self):
  # The actual story door is the only opening. Reuse endcaps and repeatable
  # center tiles, without stretching/cropping the approved prison bitmaps.
  x0,y0,x1,y1=34,18,38,21;door=(36,21)
  self.d['art_modules']=[m for m in self.d['art_modules']if not(m['name']=='crates'and m['origin']==[35,18])]
  self.d['art_props']=[m for m in self.d['art_props']if not(m['path'].endswith('/crates.png')and m['position']==[35*16,18*16])]
  walls=[]
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):
    self.ground[y][x]='p'
    if x in[x0,x1]or y in[y0,y1]:
     self.grid[y][x]='#'
     if(x,y)!=door:walls.append([x,y])
    else:self.grid[y][x]='p'
  layer=self.d['art_layers'][1]
  for x in range(x0,x1+1):layer[y0][x]=481 if x==x0 else 483 if x==x1 else 482
  for y in [19,20]:layer[y][x0]=485;layer[y][x1]=485
  for x,tile in [(34,481),(35,483),(37,481),(38,483)]:layer[21][x]=tile
  self.d['art_modules'].append({'name':'harbor_holding_cell','origin':[34,18],'footprint':[5,4],'logic':'#','cells':walls,'walk_through_cells':[[36,21]],'runtime_prop':False,'purpose':'港口引航者囚室，南侧原牢门是唯一可开启出口'})
  for u in self.d['npc_units']:
   u['position']=RELOCATIONS[u['id']]
  self.rect(35,22,37,23,'p')
  self.road([(36,23),(40,23)],2,name='囚室门前接应道')
  self.changes.append({'building':'harbor_holding_cell','origin':[34,18],'footprint':[5,4],'door':[36,21],'relocated_npcs':RELOCATIONS})
 def move_arch(self):
  old=next(m for m in self.d['art_modules']if m['name']=='ancient_arch')
  for x,y in old['cells']:self.grid[y][x]=self.ground[y][x]
  self.d['art_modules'].remove(old)
  self.d['art_props']=[a for a in self.d['art_props']if not(a['path'].endswith('/ancient_arch.png')and a['position']==[23*16,21*16])]
  cells=[];walk=[]
  for y in range(10,14):
   for x in range(20,24):
    assert (x,y)not in self.anchors
    self.ground[y][x]='c'
    if x in[20,23]:self.grid[y][x]='#';cells.append([x,y])
    else:self.grid[y][x]='c';walk.append([x,y])
  self.rect(20,14,23,15,'c')
  self.d['art_modules'].append({'name':'ancient_arch','origin':[20,10],'footprint':[4,4],'logic':'#','cells':cells,'walk_through_cells':walk,'runtime_prop':True,'purpose':'古门遗迹正对原辨认点，门洞保留双列可行石面'})
  self.d['art_props'].append({'path':lib.MODULES['ancient_arch']['path'],'position':[20*16,10*16]})
  self.changes.append({'building':'ancient_arch','from':[23,21],'to':[20,10],'purpose':'使古门辨认点与可见门体对应；原木架仍完整连通'})
 def render(self):
  super().render()
  for y in range(self.h):
   for x in range(self.w):
    if self.ground[y][x]!='~':continue
    v=lib.seed(f'{self.code}:{x}:{y}')%4;neighbours=[]
    for dx,dy in [(0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)]:
     q=self.ground[y+dy][x+dx]if 0<=x+dx<self.w and 0<=y+dy<self.h else '~'
     neighbours.append('w'if q=='~'else'a'if q=='d'else'r'if q=='^'else'p'if q=='p'else'c'if q in'c='else't'if q in's+'else'g')
    self.d['art_layers'][0][y][x]=lib.shore_tile(SHORE,neighbours,v)if any(q!='w'for q in neighbours)else lib.PACK['base']['sea'][v]
  self.d['art_atlas']='res://assets/map-polish-20261022/harbor-shore.png'
 def validate(self):
  ignore=['art_layers','art_props','art_modules','natural_props','logic_grid','visual_ground','map','art_atlas','art_style_version','tactical_review_version','production_anchors','tactical_routes','location_theme','tactical_notes']
  if self.code=='F25':ignore.append('npc_units')
  for key in self.old:
   if key not in ignore:assert self.d[key]==self.old[key],(self.code,'unexpected field drift',key)
  if self.code=='F25':
   for a,b in zip(self.old['npc_units'],self.d['npc_units']):
    assert {k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}
    assert b['position']==RELOCATIONS[b['id']]
  assert self.d['objects']==self.old['objects']
  cats=self.d['terrain']['tile_categories']
  for pos in self.d['player_positions']+[u['position']for key in ['enemies','reinforcements']for u in self.d[key]]:
   i=pos[1]*self.w+pos[0];assert cats[str(self.d['map']['tiles'][i])]==cats[str(self.old['map']['tiles'][i])],(self.code,'actor starting terrain changed',pos)
  seen,dist=base.connected(self.d,self.grid)
  all_walkable={(x,y)for y in range(self.h)for x in range(self.w)if self.grid[y][x]not in '~^#'}
  assert all_walkable<=seen,(self.code,'unconnected walkable island',sorted(all_walkable-seen))
  for pos in self.d['player_positions']+[self.d['exit']]+[u['position']for key in ['enemies','npc_units','reinforcements']for u in self.d[key]]:assert tuple(pos)in seen,(self.code,'unreachable actor',pos)
  for o in self.d['objects']:
   x,y=o['position'];fronts=o.get('approaches',[[x+dx,y+dy]for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]]if o.get('adjacent',False)else[[x,y]])
   assert any(tuple(p)in seen for p in fronts),(self.code,'unreachable object',o['id'])
  for m in self.d['art_modules']:
   if m['logic']=='#':assert all(self.grid[y][x]=='#'for x,y in m['cells']),(self.code,'module collision',m['name'])
  for boat in self.d.get('event_boats',[]):assert all(self.grid[y][x]=='~'for x,y in boat['path']),(self.code,'boat route blocked')
  if self.code=='F25':
   closed=copy.deepcopy(self.d);closed['objects']=[];seen_closed,_=base.connected(closed,self.grid)
   assert all(tuple(u['position'])not in seen_closed for u in self.d['npc_units']),'Closed prison leaks'
   opened=copy.deepcopy(self.grid);opened[21][36]='p';seen_open,_=base.connected(closed,opened)
   assert all(tuple(u['position'])in seen_open for u in self.d['npc_units']),'Opened door fails to connect cell'
  return {'code':self.code,'passed':True,'size':[self.w,self.h],'new_buildings':self.changes,'reachable_after_opening':len(seen),'exit_steps':dist[tuple(self.d['exit'])],'objects_rules_stats_unchanged':True,'actor_start_terrain_unchanged':True,'npc_relocations':RELOCATIONS if self.code=='F25'else{},'closed_open_prison_checked':self.code=='F25','boat_route_water_checked':self.code=='F26','shoreline_changed_cells':sum((self.ground[y][x]=='~')!=(self.old['visual_ground'][y][x]=='~')for y in range(self.h)for x in range(self.w))}

def main():
 plans=[]
 for code in ['F25','F26']:
  p=HarborPlan(code)
  if code=='F25':
   # The shipping basin follows the existing boardwalk, rather than leaving
   # the entire wooden zigzag stranded on grass.
   p.water(10,9,19,12);p.water(10,13,15,20)
   p.rect(20,8,23,12,'s')
   p.building('quay_warehouse',29,3,'北码头仓库，朝南接码头装卸台')
   p.building('hill_granary',25,20,'神教箱转运区粮库，朝南接主运输道')
   p.building('barracks',34,13,'东侧守备房，与囚室门前接应道相连')
   p.building('fishing_cottage',33,29,'船员候航屋，短路通往港区主道')
   p.road([(27,3),(27,5),(30,5)],2,name='账房与北仓前道')
   p.road([(30,5),(33,5),(33,10)],2,name='北仓出货道')
   p.road([(27,22),(27,25)],2,name='粮库装卸道')
   p.road([(34,31),(31,31),(31,26)],2,name='船员候航短道')
   p.road([(35,15),(39,15)],2,name='守备房前道')
   p.prison()
   for g in [(23,2,1.5,1.5),(16,4,2.2,1.8),(19,29,2.5,1.8),(22,31,2.3,1.4),(34,11,1.2,1.2)]:p.grove(*g)
   p.d['location_theme']='连续港湾与临水木码头、北部账房仓库、中部转运场、东侧实物囚室和船员候航屋'
   p.d['tactical_notes']=['西侧木码头沿真实港湾水面相连，北仓与账房经装卸台接主路；中央转运场通向神教箱。','幸存船员与引航者在东侧囚室内，原牢门是唯一出口。先清理门前接应道，再打开牢门；仓库和囚室墙体均有完整阻挡。']
  else:
   # Separate grass-topped island landings from the continuous stone causeway.
   for y in range(p.h):
    for x in range(p.w):
     if p.grid[y][x]=='p':p.direct(x,y,'.')
   p.move_arch()
   p.new_island(34.8,18.1,2.5,2.4)
   p.building('fishing_cottage',2,23,'居民出航候船屋，门前短道接西侧码头')
   p.road([(3,25),(7,25),(10,25)],2,name='西岛候船短道')
   p.road([(6,26),(6,28)],2,'s','居民船起航小码头')
   p.road([(18,19),(21,19),(21,15)],2,name='古门南侧岛头路')
   p.road([(30,9),(38,9),(38,3),(39,3)],2,name='北岸营地进出路')
   for g in [(5,23,1.2,1),(17.6,17,1.2,1.1),(37.3,4.4,1,1.1),(38.5,11.5,1.1,1)]:p.grove(*g)
   p.d['location_theme']='有候船屋的西岛、古石门岛头、双线古堤与修补木架、航灯落脚台及北岸海崖'
   p.d['tactical_notes']=['古堤与木架是两条连续路线：草地岛头提供集结空间，桥身与桥头材质清楚衔接。居民船从西岛下方水道出航，完整航道仍为水面。','古石门现在正对原辨认点；门洞两列石面可通行。航灯旧座落在木架转角的独立岛台，便于理解旧航路的位置。',p.old['tactical_notes'][-1]]
  p.render();record=p.validate();plans.append((p,record))
 # One private atlas for the two maps: old IDs/pixels are retained exactly,
 # only missing water-bank combinations are appended, leaving shared art intact.
 ART.mkdir(exist_ok=True);sheet=Image.new('RGBA',(512,math.ceil(len(CELLS)/32)*16))
 for i,tile in enumerate(CELLS):sheet.alpha_composite(tile,(i%32*16,i//32*16))
 destination=ART/'harbor-shore.png';sheet.save(destination);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(destination)],check=True)
 ATLAS['tile_count']=len(CELLS);ATLAS['source']='Approved battlefield atlas with appended exact material bank combinations for the two harbor maps; shared atlas unchanged.'
 base.write(ART/'harbor-shore.json',ATLAS)
 reports=[]
 for p,record in plans:
  base.write(R/f'data/stages/{p.code}.json',p.d);record['sha256']=hashlib.sha256((R/f'data/stages/{p.code}.json').read_bytes()).hexdigest();reports.append(record)
 base.write(OUT/'harbor-causeway-geometry.json',{'passed':True,'maps':reports,'atlas':{'path':'res://assets/map-polish-20261022/harbor-shore.png','size':list(sheet.size),'bytes':destination.stat().st_size,'original_cells':base.ATLAS['tile_count'],'appended_cells':len(CELLS)-base.ATLAS['tile_count'],'shared_atlas_unchanged':True,'compression':'lossless; retain full original tile addressing to avoid door/retry regressions'},'scope':'geometry/current-rule checks only; actual play is performed by the root task.'})
 print(json.dumps(reports,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
