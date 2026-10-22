#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Polish M12/M13 from the current frozen snapshot; never rewrites shared art or gameplay."""
from pathlib import Path
from collections import deque
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1]
OUT=R/'reports/map-polish-20261022/west-grain-prison'
BASE=R/'reports/map-polish-20261022/baseline'
spec=importlib.util.spec_from_file_location('battlefield_tools',R/'tools/redesign_battlefields.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
TRANS=json.loads((R/'assets/battlefield-0.3.0/terrain.json').read_text())['transitions']
PACK=B.PACK;NATURE=B.NATURE;IDS=B.IDS
INVARIANTS=['characters','player_positions','enemies','npc_units','terrain','enemy_group_ids','objects','reinforcements','reinforcement_turn','exit','boss_id','targets','goal','cause','before','during','after','absent_branch','optional','contract','ai_and_timing','burner_departure_turn','equipment_revision']

def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
class Field:
 def __init__(self,code):
  self.code=code;self.old=json.loads((BASE/f'{code}.json').read_text());self.d=copy.deepcopy(self.old)
  self.w=self.d['map']['width'];self.h=self.d['map']['height'];self.g=[list(r)for r in self.old['logic_grid']]
  self.old_ground=[list(r)for r in self.old['visual_ground']];self.reserved={tuple(p)for p in self.old['player_positions']+[self.old['exit']]+self.old['targets']+[u['position']for u in self.old['enemies']+self.old['npc_units']+self.old['reinforcements']]}
  self.protected=set(self.reserved)
  for o in self.old['objects']:
   self.protected.add(tuple(o['position']))
   self.protected.update(tuple(p)for p in o.get('approaches',[o['approach']]if 'approach'in o else[]))
   if o.get('adjacent'):self.protected.update((o['position'][0]+dx,o['position'][1]+dy)for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)])
  self.structures={(x,y)for y,row in enumerate(self.g)for x,ch in enumerate(row)if ch in '#ht'}
  self.routes=[];self.added=[]
 def rect(self,x0,y0,x1,y1,ch,only=None):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):
    if (x,y)in self.structures:
     if ch in '.pc':self.old_ground[y][x]=ch
     continue
    if ch in '^f#'and(x,y)in self.protected:continue
    if only is None or self.g[y][x]in only:self.g[y][x]=ch
 def ellipse(self,cx,cy,rx,ry,ch,only=None):
  for y in range(max(0,int(cy-ry-1)),min(self.h,int(cy+ry+2))):
   for x in range(max(0,int(cx-rx-1)),min(self.w,int(cx+rx+2))):
    irregular=1+.07*math.sin(x*.9+y*.5)+.05*math.cos(y*1.2-x*.2)
    if ((x-cx)/rx)**2+((y-cy)/ry)**2<irregular:self.rect(x,y,x,y,ch,only)
 def path(self,points,width=2,name=''):
  for x,y in B.route(points):self.rect(x-width//2,y-width//2,x+(width-1)//2,y+(width-1)//2,'p')
  self.routes.append({'name':name,'waypoints':[list(p)for p in points],'width':width,'surface':'p'})
 def stamp(self,name,x,y,purpose,ground='p'):
  m=B.MODULES[name];w,h=m['footprint'];cells={(xx,yy)for yy in range(y,y+h)for xx in range(x,x+w)}
  assert not cells & (self.protected|self.structures),(self.code,name,cells & (self.protected|self.structures))
  for xx,yy in cells:self.g[yy][xx]='#';self.old_ground[yy][xx]=ground
  self.structures.update(cells)
  self.d['art_props'].append({'path':m['path'],'position':[x*16,y*16]})
  self.d['art_modules'].append({'name':name,'origin':[x,y],'footprint':[w,h],'logic':'#','cells':[list(p)for p in sorted(cells)],'walk_through_cells':[],'runtime_prop':True,'purpose':purpose})
  self.added.append({'name':name,'position':[x,y],'purpose':purpose})
 def build(self):
  c=self.code
  # Preserve the original solid structures and all campaign anchors; reshape only the landscape around them.
  for y,row in enumerate(self.g):
   for x,ch in enumerate(row):
    if (x,y)not in self.structures and ch in 'pf^':self.g[y][x]='.'
  if c=='M12':
   for p in [(2,5,4,7),(17,1,5,3),(33,23,4,6)]:self.ellipse(*p,'^')
   for p in [(7,3,3,3),(3,15,4,5),(12,14,3,3),(28,17,5,3),(22,25,4,3),(4,25,4,3),(33,1,3,3)]:self.ellipse(*p,'f',only='.')
   self.path([(15,27),(15,22),(17,22),(17,13),(25,13),(25,8),(28,8)],3,'粮车主坡道：南口到仓门')
   self.path([(15,20),(8,20),(8,11),(15,11),(15,7),(23,7)],2,'西坡绕仓路')
   self.path([(25,13),(31,13),(31,7),(31,0)],2,'东仓装卸侧路')
   self.path([(8,20),(8,21)],2,'居民与芙拉接应处')
   self.rect(13,20,17,23,'p');self.rect(22,5,31,10,'p');self.rect(23,6,28,9,'c')
   self.path([(23,4),(23,6)],2,'仓吏小屋入口');self.path([(18,6),(21,6),(23,6)],2,'西侧粮棚联络路')
   self.path([(29,4),(29,5)],2,'北侧粮棚入口')
   self.stamp('hill_granary',27,6,'目标粮仓：门前占领格(28,8)对应完整粮仓正门','c')
   self.stamp('north_fence',20,11,'西侧木栅限定粮站前庭，保留主路(24–27,11)')
   self.stamp('grain_sacks',22,9,'仓院西侧成组粮袋','p')
   self.stamp('crates',21,9,'粮袋旁的装卸木箱','p')
   self.stamp('grain_wagon',19,17,'主坡道东侧粮车泊位')
   self.rect(18,16,21,18,'p');self.path([(17,17),(19,17)],2,'粮车装卸坪')
   self.d['location_theme']='丘陵林带中的粮站：南侧粮车坡道、西侧绕仓路、木栅前庭与完整目标粮仓'
   self.d['tactical_notes']=['主坡道从南侧部署区直达粮站前庭，西坡小路与东侧装卸路可以分兵；路旁林丛提供掩护，仓门与仓吏入口均有明确接路。','占领格位于完整粮仓正门前(28,8)，木栅在两侧留出通道。焚毁兵第6回合预告、第7回合出发；别让他连续两次在仓门行动。']
  else:
   self.ellipse(1,13,4,18,'^');self.ellipse(38,3,3,6,'^')
   for p in [(14,3,4,3),(25,2,5,3),(10,15,3,4),(27,16,5,2),(16,26,3,3),(34,27,7,4),(26,27,4,3)]:self.ellipse(*p,'f',only='.')
   self.rect(5,4,13,10,'p');self.rect(28,5,36,11,'p');self.rect(18,6,24,10,'c')
   self.path([(10,10),(20,10),(20,8),(26,8),(26,12),(34,12),(35,6)],3,'两囚区与内庭联络道')
   self.path([(20,12),(20,20),(11,20),(11,27),(5,27),(5,29)],3,'南侧押送主道')
   self.path([(11,22),(6,22),(6,12),(10,12),(10,9)],2,'西崖巡行路')
   self.path([(20,23),(35,23),(35,12),(35,0)],2,'东侧外廊与北口')
   self.path([(19,5),(20,5),(20,7)],2,'文书帐正面入口')
   self.rect(11,14,15,17,'p');self.path([(13,16),(13,20)],2,'西营房支路')
   self.stamp('barracks',12,14,'西侧岗房：正门向南接入押送道路')
   self.rect(25,18,31,21,'p');self.path([(29,20),(35,20)],2,'军需车场与东廊联络路')
   self.stamp('command_pavilion',25,18,'车场旁军需哨棚，留出南侧泊车空地')
   self.stamp('north_fence',23,14,'内庭南侧木栅与林带，主路留在西侧')
   self.stamp('crates',30,18,'军需车场边缘货箱')
   self.rect(18,6,24,10,'c')
   self.d['location_theme']='沿崖押送院：西囚区、文书内庭与东囚区由连贯道路串接，南侧营房和车场形成外围营区'
   self.d['tactical_notes']=['西囚区与东囚区之间有连续院路，文书帐、三处岗堡和各牢门都与院路相接；营房与军需车场沿南侧道路布置。','两扇牢门仍须分别邻接确认；获释劳工从开门处出牢，东侧外廊与西崖巡行路均保持连通。第5敌回合的一次增援与原条件相同。']
  # Actor cells retain their old walkability/avoidance; all production locations are invariant.
  for x,y in self.reserved:
   if (x,y)not in self.structures and IDS[self.g[y][x]]!=IDS[self.old['logic_grid'][y][x]]:self.g[y][x]=self.old['logic_grid'][y][x]
  # Paint original ground beneath preserved buildings, and compatible native transitions everywhere else.
  ground=[[self.old_ground[y][x] if ch in '#ht' else ch for x,ch in enumerate(row)]for y,row in enumerate(self.g)]
  base=[]
  for y,row in enumerate(ground):
   out=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{c}:landscape:{x}:{y}')%4;material=B.MATERIAL[ch]
    if ch=='f':material='grass'
    tile=PACK['base'][material][v]
    if ch=='p':tile=TRANS['path'][str(B.mask_at(ground,x,y,lambda q:q in 'ps'))][v]
    elif ch=='^':tile=TRANS['mountain_ground']['grass'][str(B.mask_at(ground,x,y,lambda q:q=='^'))][v]
    out.append(tile)
   base.append(out)
  # Scatter complete sprites inside real forest/rock footprints. Roads, actors and doors remain readable.
  nature=[];rng=random.Random(B.seed(c+'-landscape-20261022'))
  for terrain,large,small in [('f',['pine_tall','pine_broad','pine_young','pine_pair'],['pine_small_a','pine_small_b']),('^',['peak_low','crag_tall','ridge_bent','outcrop'],[])]:
   allowed={(x,y)for y,row in enumerate(self.g)for x,ch in enumerate(row)if ch==terrain};used=set();positions=sorted(allowed);rng.shuffle(positions)
   for x,y in positions:
    if (x,y)in used or rng.random()<(.24 if terrain=='^' else .08):continue
    key=rng.choice(large);sw,sh=NATURE[key]['size'];foot={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
    if not foot<=allowed or foot&self.protected or foot&used:continue
    nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});used|=foot
   for x,y in sorted(allowed-used-self.protected):
    if not small or rng.random()<.18:continue
    nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.5})
  self.d.update(logic_grid=[''.join(row)for row in self.g],visual_ground=[''.join(row)for row in ground],art_layers=[base,[[None]*self.w for _ in range(self.h)],[[None]*self.w for _ in range(self.h)]],natural_props=nature,tactical_routes=self.routes,landscape_revision='2026-10-22-m11-reference',tactical_review_version='0.10.2',art_style_version='map-polish-20261022')
  self.d['map']['tiles']=[IDS[ch]for row in self.g for ch in row]
  self.d['production_anchors']['landscape_revision']='2026-10-22-m11-reference'
  self.d['production_anchors']['revision']='0.10.2'
  for field in INVARIANTS:assert self.d.get(field)==self.old.get(field),(c,field)
  report=self.check()
  write(R/f'data/stages/{c}.json',self.d);write(OUT/f'{c}-geometry.json',report)
  return report
 def check(self):
  opens={tuple(p)for o in self.d['objects']for p in o.get('opens',[o['position']]if o['kind']in ['door','rescue']else[])}
  def flood(opened=False):
   start=tuple(self.d['player_positions'][0]);seen={start};q=deque([start])
   while q:
    x,y=q.popleft()
    for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:
     p=(x+dx,y+dy)
     if 0<=p[0]<self.w and 0<=p[1]<self.h and p not in seen and (self.g[p[1]][p[0]]not in '~^#'or(opened and p in opens)):seen.add(p);q.append(p)
   return seen
  closed=flood();opened=flood(True)
  ordinary=self.d['player_positions']+[self.d['exit']]+[u['position']for u in self.d['enemies']+self.d['reinforcements']]
  assert all(tuple(p)in closed for p in ordinary),(self.code,'unreachable ordinary anchors',[p for p in ordinary if tuple(p)not in closed])
  assert all(tuple(u['position'])in opened for u in self.d['npc_units']),(self.code,'unreachable rescued NPC')
  for o in self.d['objects']:
   fronts=o.get('approaches',[o['approach']]if 'approach'in o else[])
   if not fronts:
    x,y=o['position'];fronts=[[x,y]]+([[x+dx,y+dy]for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]]if o.get('adjacent')else[])
   assert any(tuple(p)in closed for p in fronts),(self.code,o['id'],'unapproachable')
  return {'code':self.code,'passed':True,'closed_connected':len(closed),'opened_connected':len(opened),'actors_objectives_stats_unchanged':True,'all_actor_cells_same_movement_category':all(IDS[self.g[y][x]]==IDS[self.old['logic_grid'][y][x]]for x,y in self.reserved),'new_structures':self.added,'changed_logic_cells':sum(a!=b for a,b in zip(''.join(self.old['logic_grid']),''.join(self.d['logic_grid']))),'natural_props':len(self.d['natural_props']),'routes':self.routes}
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 print(json.dumps([Field(c).build()for c in ['M12','M13']],ensure_ascii=False,indent=2))
