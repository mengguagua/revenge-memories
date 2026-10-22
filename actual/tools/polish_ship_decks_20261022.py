#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three readable ship battlefields, preserving objectives and dynamic boarding rules."""
from pathlib import Path
from collections import Counter,deque
import copy,importlib.util,json
spec=importlib.util.spec_from_file_location('grain_prison',Path(__file__).with_name('polish_grain_prison_20261022.py'));P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
R=P.R;OUT=R/'reports/map-polish-20261022/ship-decks';B=P.B;IDS=P.IDS;PACK=P.PACK;TRANS=P.TRANS
INVARIANTS=P.INVARIANTS+['building_sites','detention_bays','event_boats','event_boat_sprite']
SHIPS={'F21':[(2,19,1,27),(24,41,1,27)],'F22':[(2,19,1,29),(25,43,1,29)],'S21':[(2,15,3,25),(20,33,1,24)]}
BRIDGES={'F21':[(18,25,10,11),(18,25,19,20)],'F22':[(18,26,11,12),(20,24,22,23)],'S21':[(14,21,12,13),(14,21,20,21)]}
class Deck(P.Field):
 def __init__(self,code):
  super().__init__(code);self.bridge_cells={(x,y)for x0,x1,y0,y1 in BRIDGES[code]for y in range(y0,y1+1)for x in range(x0,x1+1)}
  self.opens={tuple(p)for o in self.d['objects']for p in o.get('opens',[])};self.protected|=self.opens|self.bridge_cells
  self.bow_changes=[];self.cargo_changes=[];self.deck_zones=[]
 def clear_modules(self,predicate):
  removed=[m for m in self.d['art_modules']if predicate(m)];kept=[m for m in self.d['art_modules']if not predicate(m)]
  known=Counter(tuple(p)for m in kept if m.get('logic')=='#'for p in m.get('cells',[]))
  prison=set()
  if self.code=='F22':
   prison={(x,y)for y0 in [7,20]for y in range(y0,y0+4)for x in range(32,39)if self.old['logic_grid'][y][x]=='#'}
  props={(B.MODULES[m['name']]['path'],tuple(v*16 for v in m['origin']))for m in removed}
  self.d['art_props']=[p for p in self.d['art_props']if(p['path'],tuple(p['position']))not in props]
  self.d['art_modules']=kept
  for m in removed:
   for p in m.get('cells',[]):
    x,y=p
    if self.g[y][x]=='#'and not known[(x,y)]and(x,y)not in prison and(x,y)not in self.protected:self.g[y][x]='s';self.old_ground[y][x]='s'
  self.structures={(x,y)for y,row in enumerate(self.g)for x,ch in enumerate(row)if ch in '#ht'}
  self.cargo_changes.extend({'removed':m['name'],'from':m['origin']}for m in removed)
 def add(self,name,x,y,purpose):
  m=B.MODULES[name];w,h=m['footprint'];cells={(xx,yy)for yy in range(y,y+h)for xx in range(x,x+w)}
  assert all(0<=xx<self.w and 0<=yy<self.h and self.g[yy][xx]=='s'for xx,yy in cells),(self.code,name,[x,y],'not clear deck')
  self.stamp(name,x,y,purpose,ground='s')
 def taper_bows(self):
  for x0,x1,y0,y1 in SHIPS[self.code]:
   width=x1-x0+1;middle=(x0+x1)/2
   # Existing square deck footprints become full, shallow ship bows.
   for dy,span in enumerate(([4,8,12,14,16]if width==18 else[3,7,11,15,17]if width==19 else[4,8,10,12])):
    left=int(middle-(span-1)/2);right=left+span-1;y=y0+dy
    for x in range(x0,x1+1):
     if x<left or x>right:
      assert(x,y)not in self.protected,(self.code,'bow anchor overlap',[x,y])
      if self.g[y][x]=='s':self.g[y][x]='~';self.bow_changes.append([x,y])
   self.deck_zones.append({'ship':[x0,x1,y0,y1],'central_aisle':[int(middle)-1,int(middle)+1],'foredeck_end':y0+5,'aftdeck_start':y1-5})
   # Short broadside rail sections follow the widest tapered foredeck step.
   rail_y=y0+2;span=(12 if width==18 else 11 if width==19 else 10);left=int(middle-(span-1)/2);right=left+span-1
   for x in [left,right-3]:self.add('rail_h',x,rail_y,'船艏两舷护栏，中央保留通往前甲板的通道')
 def taper_sterns(self):
  if self.code=='F22':return # The prisoner transport retains its broad rear entry deck and reinforcement landing cells.
  for x0,x1,y0,y1 in SHIPS[self.code]:
   width=x1-x0+1;middle=(x0+x1)/2
   for dy,span in enumerate([8,12,16]if width==18 else[6,10,12]):
    y=y1-dy;left=int(middle-(span-1)/2);right=left+span-1
    for x in range(x0,x1+1):
     if x<left or x>right:
      assert(x,y)not in self.protected,(self.code,'stern anchor overlap',[x,y])
      if self.g[y][x]=='s':self.g[y][x]='~';self.bow_changes.append([x,y])
 def build(self):
  # Loose props are regrouped beside holds rather than scattered across lanes.
  self.clear_modules(lambda m:m['name']in ['grain_sacks','crates','grain_wagon']or(m['name']=='rail_h'and(m['origin'][1]in [s[2]+1 for s in SHIPS[self.code]]or(self.code!='F22'and m['origin'][1]in [s[3]for s in SHIPS[self.code]])))or(self.code=='F22'and m['name']=='hatch'and m['origin']==[34,23]))
  self.taper_bows();self.taper_sterns()
  if self.code in ['F21','F22']:
   for name,x,y in [('crates',4,5),('crates',5,5),('crates',4,6),('grain_sacks',5,6),('crates',3,14),('crates',4,14),('grain_sacks',3,15),('grain_sacks',4,15)]:self.add(name,x,y,'己船靠舷货运区，避开中轴通行与跳板入口')
   if self.code=='F21':
    for name,x,y in [('crates',37,5),('crates',38,5),('grain_sacks',39,5),('crates',38,6),('grain_sacks',25,17),('crates',26,17),('crates',25,18)]:self.add(name,x,y,'敌舰舷边货区，中央和两条登船横道保持畅通')
    self.add('captain_cabin',36,24,'敌舰后甲板船员舱，正门朝向船尾通行空地')
   else:
    for name,x,y in [('crates',35,4),('crates',36,4),('grain_sacks',37,4),('crates',36,5),('crates',26,24),('grain_sacks',27,24),('crates',26,25),('grain_sacks',27,25)]:self.add(name,x,y,'押送舰前货区与后货区，囚室外围及绞盘入口保持空旷')
    self.add('hatch',28,26,'移离下囚室围栏的后货舱口，保留囚门出口正下方通路')
  else:
   for name,x,y in [('crates',4,7),('grain_sacks',5,7),('crates',4,8),('grain_sacks',3,18),('crates',4,18),('crates',30,5),('grain_sacks',31,5),('crates',30,6),('grain_sacks',21,15),('crates',22,15),('crates',21,16),('crates',31,18),('grain_sacks',31,19)]:self.add(name,x,y,'渔船舷边集中货区，病人后甲板与登船横道保持空旷')
   self.add('captain_cabin',29,15,'右船后部船员舱，与货舱口形成独立作业区')
  # A continuous low timber rim follows every sea edge; board direction marks
  # work areas and broad central aisles on one level, never fake raised floors.
  ground=[[self.old_ground[y][x]if ch in '#ht'else ch for x,ch in enumerate(row)]for y,row in enumerate(self.g)]
  base=[]
  for y,row in enumerate(ground):
   out=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{self.code}:deck:{x}:{y}')%4;tile=PACK['base'][B.MATERIAL[ch]][v]
    if ch=='s':
     zone=next((z for z in self.deck_zones if z['ship'][0]<=x<=z['ship'][1]),None)
     vertical=zone and(zone['central_aisle'][0]<=x<=zone['central_aisle'][1]or y<=zone['foredeck_end']or y>=zone['aftdeck_start'])
     axis='v'if vertical else'h'
     if(x,y)in self.bridge_cells:axis='h'
     mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<self.w and 0<=y+dy<self.h and ground[y+dy][x+dx]!='~')
     tile=TRANS['walkway'][axis+str(mask)][v]
    out.append(tile)
   base.append(out)
  self.d.update(logic_grid=[''.join(row)for row in self.g],visual_ground=[''.join(row)for row in ground],art_layers=[base,[[None]*self.w for _ in range(self.h)],[[None]*self.w for _ in range(self.h)]],tactical_review_version='0.10.2',art_style_version='map-polish-20261022',landscape_revision='2026-10-22-m11-reference')
  self.d['map']['tiles']=[IDS[ch]for row in self.g for ch in row];self.d['production_anchors']['revision']='0.10.2';self.d['deck_zones']=self.deck_zones
  self.d['location_theme']={'F21':'双舰登船战：收窄船艏、前后作业甲板、集中货区与两条完整跳板','F22':'押送舰救援：双囚舱独立围合，中段接应走廊、后货舱与可放下的备用跳板','S21':'漂泊渔船群：错位船艏、舷边货区、后部病人甲板与两处互通跳板'}[self.code]
  self.d['tactical_notes']={'F21':['上下两条跳板完整连接两舰，前甲板与中央登船横道留空；货物集中在舷边货舱旁，桅杆两侧均可绕行。','己船后甲板医药区保留原有恢复格，每回合恢复5生命；该地形只能恢复普通伤势，不能救治濒死。保住己方船并击败指挥官。'],
   'F22':['上跳板开战时可通行，下方备用跳板仍为空水面；从原绞盘操作后放下。囚舱总闸同时开启两处真正牢门，囚室与开门字段均保持。','下囚室围栏旁的旧货舱口已移到后货区，囚门前留出撤离通道；同伴接应旗标仍在敌舰中段总闸旁，到旗标即可获救。','己船后甲板的恢复格与船员舱保留。东西向登船走廊与中轴通路贯通，舵楼哨位仍为可占据的单格地形。'],
   'S21':['两船船艏与后甲板清楚分区，货物贴舷集中摆放；上下两条跳板与病人后甲板之间保留宽敞路线。','清出跳板后再护送病人，飞行魔物仍可绕过桥口。普通舵楼哨位保持原有回避与恢复规则。']}[self.code]
  for field in INVARIANTS:assert self.d.get(field)==self.old.get(field),(self.code,field)
  for x,y in self.reserved:assert IDS[self.g[y][x]]==IDS[self.old['logic_grid'][y][x]],(self.code,'actor anchor terrain changed',[x,y])
  for x,y in self.bridge_cells:assert self.g[y][x]==self.old['logic_grid'][y][x],(self.code,'boarding bridge changed',[x,y])
  for x,y in self.opens:assert self.g[y][x]==self.old['logic_grid'][y][x],(self.code,'dynamic opened cell changed',[x,y])
  if self.code=='F22':
   for y0 in [7,20]:
    for y in range(y0,y0+4):
     for x in range(32,39):assert self.g[y][x]==self.old['logic_grid'][y][x],('F22','prison cell changed',[x,y])
  report=self.check();report.update(hull_taper_removed_cells=self.bow_changes,boarding_connections_unchanged=True,dynamic_open_fields_unchanged=True,deck_zones=self.deck_zones,regrouped_props=self.cargo_changes)
  P.write(R/f'data/stages/{self.code}.json',self.d);P.write(OUT/f'{self.code}-geometry.json',report);return report
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 print(json.dumps([Deck(c).build()for c in ['F21','F22','S21']],ensure_ascii=False,indent=2))
