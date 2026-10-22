#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F23/F24 authored island villages using existing native sprites and atlas IDs only."""
from pathlib import Path
import importlib.util,json,math,random
spec=importlib.util.spec_from_file_location('grain_prison',Path(__file__).with_name('polish_grain_prison_20261022.py'));P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
R=P.R;OUT=R/'reports/map-polish-20261022/island-villages';B=P.B;IDS=P.IDS;PACK=P.PACK;TRANS=P.TRANS;NATURE=P.NATURE
INVARIANTS=P.INVARIANTS+['beacon_defense_turn','building_sites']
class Island(P.Field):
 def rect(self,x0,y0,x1,y1,ch,only=None):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):
    if self.old['logic_grid'][y][x]=='~':continue
    super().rect(x,y,x,y,ch,only)
 def build(self):
  c=self.code
  for y,row in enumerate(self.g):
   for x,ch in enumerate(row):
    if (x,y)not in self.structures and ch in 'pf':
     sea_near=any(0<=x+dx<self.w and 0<=y+dy<self.h and self.old['logic_grid'][y+dy][x+dx]=='~'for dx,dy in[(0,1),(1,0),(0,-1),(-1,0)])
     self.g[y][x]='d'if ch=='p'and sea_near else'.'
  if c=='F23':
   for p in[(18,5,6,3),(20,10,3,3),(30,16,3,4),(19,26,3,2),(7,19,2,2)]:self.ellipse(*p,'f',only='.')
   self.path([(5,15),(11,15),(15,15),(18,15),(18,20),(24,20),(28,20)],3,'登陆坡至居民营地与东侧渔家')
   self.path([(13,25),(15,25),(15,20),(18,20)],2,'南侧渔村接应路')
   self.path([(18,15),(19,13),(26,13),(28,13),(28,7),(32,7),(32,3)],3,'营地北上草坡主道')
   self.path([(11,15),(15,15),(15,8),(27,8)],2,'西侧岩坡绕行路')
   self.path([(26,17),(26,20),(28,20)],2,'渔家门前院路')
   self.rect(9,12,13,15,'p');self.rect(16,17,20,20,'p')
   self.rect(10,23,16,26,'p')
   self.path([(10,23),(13,23),(13,25)],2,'接应渔舍前院')
   self.stamp('fishing_cottage',9,21,'南侧接应渔舍：罗恩位于门前(10,23)')
   self.stamp('fishing_cottage',14,23,'渔民营地旁的完整渔舍，南向门前接入村路')
   self.stamp('grain_sacks',17,19,'居民营地的补给袋')
   self.stamp('crates',20,19,'营地外围装卸木箱')
   self.rect(24,17,28,20,'p')
   self.d['location_theme']='礁岩登陆滩、南侧渔村和居民营地；草坡主道向东北高地延伸，林带分隔海岸与内陆'
   self.d['tactical_notes']=['西岸登陆集结区通过村路连接南侧渔民营地，完整渔舍的门前留有接应空地；东北草坡主道与西侧岩坡小路可分队清场。','原居民营地、罗恩和所有敌军位置保持不变。飞行首领败退后仍须清除自然魔物；推进时留人保护南侧营地。']
  else:
   for p in[(18,5,6,3),(18,11,2,3),(12,20,4,3),(28,17,3,4),(18,28,3,2),(35,15,2,3)]:self.ellipse(*p,'f',only='.')
   self.path([(22,29),(22,25),(22,20),(23,17)],3,'南村至航灯的守备主道')
   self.path([(15,25),(22,25),(27,25)],2,'岛民住屋与接应路')
   self.path([(22,23),(29,23),(32,23),(32,24)],3,'南村至东侧避难所')
   self.path([(27,24),(27,25)],2,'可占据村舍门前')
   self.path([(23,14),(26,14),(28,14),(28,8),(32,8),(34,8),(34,3)],3,'灯台北侧高地通路')
   self.path([(23,17),(17,17),(13,17),(9,17),(8,16)],2,'西侧渔舍与灯台联络路')
   self.path([(13,17),(15,14),(15,8),(23,8),(23,13)],2,'西坡巡灯支路')
   self.path([(29,23),(32,20),(32,8)],2,'避难所外侧巡行路')
   self.rect(20,23,24,27,'p');self.rect(14,25,17,26,'p');self.rect(30,22,33,24,'p');self.rect(7,16,10,18,'p')
   self.rect(21,13,25,18,'c')
   self.path([(21,13),(22,13)],2,'守灯人小屋门前')
   self.stamp('fishing_cottage',14,23,'希雅接应处的完整渔舍，门前连通南村道路')
   self.stamp('fishing_cottage',25,26,'南村住屋，与原单格村舍形成聚落')
   self.stamp('crates',29,24,'避难所侧边备运物资')
   self.d['location_theme']='黑昼海灯岛：灯塔与航灯共用连续石庭，南村主道上接灯台，东西渔舍与避难所各有独立前院'
   self.d['tactical_notes']=['南侧部署区沿三格宽主道直达航灯石庭；灯塔正门与灯台之间已连成连续步行广场，西坡与东侧避难所保留支路。','第6己方回合与击败首领的胜利条件不变。留意东侧飞兵和海兵，航灯被敌军连续占满一整回合仍会失败；安置岛民从避难所门前操作。']
  # An actor keeps the same movement tile and avoidance as the shipped map.
  for x,y in self.reserved:
   if (x,y)not in self.structures and IDS[self.g[y][x]]!=IDS[self.old['logic_grid'][y][x]]:self.g[y][x]=self.old['logic_grid'][y][x]
  if c=='F23':self.g[20][28]='p' # The landing gateway belongs to its dirt forecourt, not an invisible forest tile.
  ground=[[self.old_ground[y][x]if ch in '#ht'else ch for x,ch in enumerate(row)]for y,row in enumerate(self.g)]
  def shore_key(x,y):
   neighbours=[]
   for dx,dy in[(0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)]:
    q=ground[y+dy][x+dx]if 0<=x+dx<self.w and 0<=y+dy<self.h else'~'
    neighbours.append('w'if q=='~'else'a'if q=='d'else'r'if q=='^'else'p'if q=='p'else'c'if q in 'c='else't'if q in 's+'else'n'if q=='n'else'g')
   return ''.join(neighbours)
  # Reuse a published shoreline with the exact same water/land silhouette.
  # Closely related sand/earth rims are compatible at the two-pixel wet bank;
  # do not restore stranded old road fragments just to obtain a cached key.
  shore_substitutions={};palette={'a':(185,165,120),'p':(162,140,98),'g':(108,123,70),'c':(147,148,138),'r':(100,101,87),'t':(118,99,66),'n':(210,215,232),'v':(105,101,90),'w':(0,0,0)}
  def cached_shore(key):
   if key in TRANS['shore_water']:return key
   candidates=[k for k in TRANS['shore_water']if all((a=='w')==(b=='w')for a,b in zip(k,key))]
   assert candidates,(c,'missing shoreline silhouette',key)
   score=lambda k:sum((4 if i<4 else 1)*sum((palette[a][j]-palette[b][j])**2for j in range(3))for i,(a,b)in enumerate(zip(k,key)))
   match=min(candidates,key=lambda k:(score(k),k));shore_substitutions[key]=match;return match
  base=[]
  for y,row in enumerate(ground):
   out=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{c}:island:{x}:{y}')%4;material=B.MATERIAL[ch]
    if ch=='f':material='grass'
    tile=PACK['base'][material][v]
    if ch=='p':
     key='path_sand'if any(0<=x+dx<self.w and 0<=y+dy<self.h and ground[y+dy][x+dx]=='d'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)])else'path'
     tile=TRANS[key][str(B.mask_at(ground,x,y,lambda q:q in 'ps'))][v]
    elif ch=='d':tile=TRANS['beach_grass'][str(B.mask_at(ground,x,y,lambda q:q not in '.f'))][v]
    elif ch=='~':
     key=shore_key(x,y)
     if key!='wwwwwwww':tile=TRANS['shore_water'][cached_shore(key)][v]
    elif ch=='^':
     next_sea=any(0<=x+dx<self.w and 0<=y+dy<self.h and ground[y+dy][x+dx]=='~'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)])
     family='sea'if next_sea else'grass';mask=B.mask_at(ground,x,y,lambda q:q!='~'if next_sea else q=='^')
     tile=TRANS['mountain_ground'][family][str(mask)][v]
    out.append(tile)
   base.append(out)
  nature=[];rng=random.Random(B.seed(c+'-village-20261022'))
  for terrain,large,small in [('f',['pine_tall','pine_broad','pine_young','pine_pair'],['pine_small_a','pine_small_b']),('^',['peak_low','crag_tall','ridge_bent','outcrop'],[])]:
   allowed={(x,y)for y,row in enumerate(self.g)for x,ch in enumerate(row)if ch==terrain};used=set();positions=sorted(allowed);rng.shuffle(positions)
   for x,y in positions:
    if (x,y)in used or rng.random()<(.3 if terrain=='^'else .1):continue
    key=rng.choice(large);sw,sh=NATURE[key]['size'];foot={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
    if not foot<=allowed or foot&self.protected or foot&used:continue
    nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});used|=foot
   for x,y in sorted(allowed-used-self.protected):
    if not small or rng.random()<.2:continue
    nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.5})
  self.d.update(logic_grid=[''.join(row)for row in self.g],visual_ground=[''.join(row)for row in ground],art_layers=[base,[[None]*self.w for _ in range(self.h)],[[None]*self.w for _ in range(self.h)]],natural_props=nature,tactical_routes=self.routes,landscape_revision='2026-10-22-m11-reference',tactical_review_version='0.10.2',art_style_version='map-polish-20261022')
  self.d['map']['tiles']=[IDS[ch]for row in self.g for ch in row];self.d['production_anchors']['revision']='0.10.2';self.d['production_anchors']['landscape_revision']='2026-10-22-m11-reference'
  for field in INVARIANTS:assert self.d.get(field)==self.old.get(field),(c,field)
  report=self.check();report['native_shore_rim_substitutions']=shore_substitutions;report['water_topology_unchanged']=all((a=='~')==(b=='~')for a,b in zip(''.join(self.old['logic_grid']),''.join(self.d['logic_grid'])))
  actor_cells=[p for p in self.old['player_positions']]+[u['position']for u in self.old['enemies']+self.old['npc_units']+self.old['reinforcements']]
  report['all_actor_cells_same_movement_category']=all(IDS[self.g[y][x]]==IDS[self.old['logic_grid'][y][x]]for x,y in actor_cells)
  report['objective_ground_changes']=[{'id':'landing','position':[28,20],'from':'forest','to':'dirt','reason':'让登陆坡门框与前院同为真实土路，修正隐形林地格；坐标与交互不变'}]if c=='F23'else[]
  P.write(R/f'data/stages/{c}.json',self.d);P.write(OUT/f'{c}-geometry.json',report)
  return report
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 print(json.dumps([Island(c).build()for c in ['F23','F24']],ensure_ascii=False,indent=2))
