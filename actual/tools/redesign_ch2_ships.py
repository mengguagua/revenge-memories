#!/usr/bin/env python3
"""Compact ship encounters with authored decks, boarding lanes and real cells."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,hashlib,importlib.util,json,math
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter2-redesign-20261022/ships';BASE=O.parent/'baseline';ART=R/'assets/chapter2-redesign-20261022/ships'
spec=importlib.util.spec_from_file_location('ch2_ship_terrain',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
L.ART=ART;A=L.Atlas();B=L.B;IDS=B.IDS;MAT=B.MATERIAL
write=lambda p,d:(p.parent.mkdir(parents=True,exist_ok=True),p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'))
class Field:
 def __init__(self,c,w,h):
  self.c=c;self.old=json.loads((BASE/f'{c}.json').read_text());self.d=copy.deepcopy(self.old);self.w=w;self.h=h;self.g=[list('~'*w)for _ in range(h)];self.under={};self.props=[];self.modules=[];self.top=[[None]*w for _ in range(h)];self.decks=[];self.bridges=[];self.cells=[]
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):self.g[y][x]=ch
 def poly(self,points,ch):
  im=Image.new('1',(self.w,self.h));ImageDraw.Draw(im).polygon(points,fill=1)
  for y in range(self.h):
   for x in range(self.w):
    if im.getpixel((x,y)):self.g[y][x]=ch
 def ship(self,x0,x1,y0,y1,label):
  width=x1-x0+1;mid=(x0+x1)//2
  for y in range(y0,y1+1):
   span=width
   if y-y0<3:span=min(width,[4,6,10][y-y0])
   if y1-y<2:span=min(span,[6,10][y1-y])
   left=mid-(span-1)//2;self.rect(left,y,left+span-1,y,'s')
  self.decks.append({'label':label,'bounds':[x0,y0,x1,y1],'main_aisle':[mid-1,mid+1]})
  self.stamp('bow',mid-1,y0,kind='inherits_ground');self.stamp('stern',mid-1,y1-1,kind='inherits_ground')
 def bridge(self,x0,y0,x1,y1,axis='h',closed=False):
  if not closed:self.rect(x0,y0,x1,y1,'s')
  self.bridges.append({'bounds':[x0,y0,x1,y1],'axis':axis,'initially_closed':closed})
 def stamp(self,name,x,y,kind='#',ground='s',purpose=''):
  m=B.MODULES[name];fw,fh=m['footprint'];cells=[]
  for yy in range(y,y+fh):
   for xx in range(x,x+fw):
    assert 0<=xx<self.w and 0<=yy<self.h,(self.c,name,'outside')
    assert self.g[yy][xx]!='~',(self.c,name,x,y,'prop outside hull',xx,yy)
    if kind=='#':self.under[xx,yy]=ground;self.g[yy][xx]='#'
    elif kind=='occupiable':self.g[yy][xx]='t'
    cells.append([xx,yy])
  self.modules.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':kind,'runtime_prop':True,'purpose':purpose})
  self.props.append({'path':m['path'],'position':[x*16,y*16]})
 def tile_module(self,name,x,y,solid=True):
  m=B.MODULES[name];cells=[]
  for dy,row in enumerate(m['tiles']):
   for dx,t in enumerate(row):
    self.top[y+dy][x+dx]=t;cells.append([x+dx,y+dy])
    if solid:self.under[x+dx,y+dy]='s';self.g[y+dy][x+dx]='#'
  self.modules.append({'name':name,'origin':[x,y],'footprint':m['footprint'],'cells':cells,'tiles':m['tiles'],'logic':'#'if solid else'inherits_ground','runtime_prop':False})
 def cage(self,x,y):
  # Repeat the native middle segments between complete ends; repeating full
  # three-cell endcap modules would leave visible gaps between their caps.
  horizontal=B.MODULES['jail_bars_h']['tiles'][0][1]
  vertical=B.MODULES['jail_bars_v']['tiles']
  pieces=[('jail_bars_h',x+1,y,[[horizontal]*5]),('jail_bars_h',x+1,y+4,[[horizontal]*5]),
          ('jail_bars_v',x,y,[vertical[0],vertical[1],vertical[1],vertical[1],vertical[2]]),
          ('jail_bars_v',x+6,y,[vertical[0],vertical[1],vertical[1],vertical[1],vertical[2]])]
  for name,px,py,tiles in pieces:
   cells=[]
   for dy,row in enumerate(tiles):
    for dx,t in enumerate(row):self.top[py+dy][px+dx]=t;self.g[py+dy][px+dx]='#';self.under[px+dx,py+dy]='s';cells.append([px+dx,py+dy])
   self.modules.append({'name':name,'origin':[px,py],'footprint':[len(tiles[0]),len(tiles)],'cells':cells,'tiles':tiles,'logic':'#','runtime_prop':False,'composition':'Native repeatable middle segment with intact endpoints'})
  door=[x+3,y+4];self.tile_module('jail_door',door[0],door[1]-1,False)
  self.g[door[1]][door[0]]='#'
  self.cells.append({'bounds':[x,y,x+6,y+4],'door':door,'interior':[[xx,yy]for yy in range(y+1,y+4)for xx in range(x+1,x+6)]})
  return door
 def visit(self,position,front):
  o=next(o for o in self.d['objects']if o['kind']=='visit');o.update(position=position,approach=front,approaches=[front],entrance_cells=[position])
 def place_units(self,deploy,enemies,npcs,reinforcements=None):
  self.d['player_positions']=deploy
  for group,positions in [('enemies',enemies),('npc_units',npcs),('reinforcements',reinforcements or{})]:
   for u in self.d[group]:u['position']=positions[u['id']]
 def design(self):
  c=self.c
  if c=='F21':
   self.ship(2,11,5,23,'己方运输船');self.ship(17,28,1,23,'搜捕舰')
   self.bridge(12,10,16,11);self.bridge(12,18,16,19)
   for name,x,y in [('captain_cabin',3,13),('mast',7,8),('hatch',3,7),('crates',3,17),('grain_sacks',3,18),('medicine_wagon',4,16),('mast',21,5),('hatch',24,15),('captain_cabin',23,20),('crates',18,6),('grain_sacks',18,7),('crates',26,15),('crates',26,16),('grain_sacks',27,15)]:self.stamp(name,x,y)
   self.stamp('tactical_deck_post',25,4,'occupiable');self.rect(6,17,7,17,'+')
   self.place_units([[5,18],[6,18],[7,18],[8,18],[5,19],[6,19],[7,19],[8,19],[9,18],[9,19]],{'F21_boss':[24,11],'F21_e1':[24,8],'F21_e2':[18,10],'F21_e3':[22,18],'F21_e4':[10,10],'F21_e5':[26,8],'F21_e6':[25,13],'F21_e7':[26,18],'F21_e8':[10,7]}, {'friendly_ship':[5,22],'injured_passengers':[8,21]})
   self.d['objects'][0]['position']=[14,11];self.d['objects'][1]['position']=[14,19];self.visit([4,14],[4,15]);self.d['exit']=[25,3];self.d['targets']=[[14,11],[14,19]]
   self.d['building_sites']=[{'position':[25,4],'label':'舵楼哨位','occupiable':True,'avoid':40,'phase_heal':5}]
   self.d['recovery_sites']=[{'position':[6,17],'label':'船医补给点'},{'position':[7,17],'label':'船医补给点'}]
   self.notes=['两艘错位舰船形成清楚船艏、作业甲板和船尾，甲板长度收紧；上下两条两格跳板横跨真实海面，分别接入敌舰前后战区。','己方休息舱、医药区与船体旗位位于后甲板，前方桅杆和舷边货物围出通道；守船与登舰可分开部署。','原敌人身份、属性和AI保持，己方船体必须存活；原两格普通恢复地形和一处舵楼哨位均保留。']
  elif c=='F22':
   self.ship(2,10,7,25,'己方接应船');self.ship(16,30,1,25,'押送舰')
   self.bridge(11,12,15,13);self.bridge(11,22,15,22,closed=True)
   for name,x,y in [('captain_cabin',3,16),('mast',7,9),('hatch',3,10),('medicine_wagon',3,20),('crates',9,19),('grain_sacks',9,20),('mast',18,5),('crates',17,18),('grain_sacks',18,18),('hatch',18,21)]:self.stamp(name,x,y)
   doors=[self.cage(23,5),self.cage(23,17)]
   for x,y in [(21,3),(20,10),(17,15),(21,16)]:self.stamp('tactical_deck_post',x,y,'occupiable')
   self.rect(5,20,6,20,'+');self.g[14][18]='#';self.under[18,14]='s'
   o=self.d['objects'][0];o.update(position=[18,14],opens=[[18,14]]+doors,open_art_cells=[{'position':[x,y-1+dy],'base_tile':24,'clear_layers':[1,2]}for x,y in doors for dy in [0,1]],open_art_props=[{'path':B.MODULES['open_jail']['path'],'position':[x*16,(y-1)*16]}for x,y in doors])
   o=self.d['objects'][1];opens=[[x,22]for x in range(11,16)];o.update(position=[20,22],opens=opens,open_art_cells=[{'position':p,'base_tile':A.trans['walkway']['h10'][0],'clear_layers':[1,2]}for p in opens])
   self.visit([4,17],[4,18]);self.d['exit']=[17,13];self.d['targets']=[[18,14],[20,22]]
   self.place_units([[7,14],[8,14],[9,14],[7,15],[8,15],[9,15],[6,14],[6,15],[7,16],[8,16]], {'F22_boss':[22,4],'F22_e1':[21,6],'F22_e2':[20,12],'F22_e3':[28,23],'F22_e4':[9,10],'F22_e5':[29,12],'F22_e6':[22,10],'F22_e7':[22,20],'F22_e8':[13,12],'F22_e9':[29,15]}, {'prisoners_0':[25,6],'prisoners_1':[27,6],'prisoners_2':[25,18],'lord':[27,18]}, {'F22_r0':[23,24],'F22_r1':[24,23]})
   self.d['detention_bays']={'gates':doors,'main_aisle_columns':[20,21,22],'main_aisle_rows':[3,23],'unlock_control':[18,14],'cells':self.cells}
   self.d['building_sites']=[{'position':[x,y],'label':'舵楼哨位','occupiable':True,'avoid':40,'phase_heal':5}for x,y in [(21,3),(20,10),(17,15),(21,16)]]
   self.d['recovery_sites']=[{'position':[5,20],'label':'船医补给点'},{'position':[6,20],'label':'船医补给点'}]
   self.notes=['押送舰以中轴通道连接前后两间真实囚舱，牢墙完整围合；总闸同时打开两处南门，三名普通俘虏与洛德均有连续的撤离通道。','接应旗位放在敌舰中段、已连接己船的跳板落点旁，与总闸相邻；获救者到达旗位即转交接应人员，原故事目标不变。','上跳板初始可通行，下跳板仍由独立绞盘放下；船尾增援、原恢复格和舵楼哨位保留，紧凑甲板减少空走与追逐。']
  else:
   self.ship(2,12,3,20,'载病人渔船');self.ship(18,28,1,21,'漂泊伴船')
   self.bridge(13,10,17,11);self.bridge(13,17,17,18)
   self.poly([(0,21),(2,21),(4,22),(8,23),(12,22),(14,24),(15,25),(0,25)],'d')
   self.rect(0,24,13,25,'.');self.bridge(6,21,7,23,'v');self.rect(3,23,8,24,'p')
   for name,x,y in [('captain_cabin',3,11),('mast',7,6),('hatch',9,15),('crates',3,15),('grain_sacks',3,16),('mast',22,6),('hatch',25,14),('captain_cabin',20,16),('crates',27,11),('grain_sacks',27,12)]:self.stamp(name,x,y)
   self.stamp('tactical_deck_post',22,4,'occupiable');self.stamp('bollard',8,23,ground='p')
   self.place_units([[6,14],[7,14],[8,14],[6,15],[7,15],[8,15],[5,14],[5,15],[6,16],[7,16]], {'S21_boss':[25,5],'S21_e1':[25,8],'S21_e2':[20,11],'S21_e3':[25,18],'S21_e4':[10,7],'S21_e5':[26,5],'S21_e6':[24,12]}, {'patients0':[5,18],'patients1':[8,18]})
   self.d['objects'][0]['position']=[15,11];self.d['objects'][1]['position']=[6,22];self.visit([4,12],[4,13]);self.d['exit']=[3,24];self.d['targets']=[[15,11],[6,22]]
   self.d['building_sites']=[{'position':[22,4],'label':'舵楼哨位','occupiable':True,'avoid':40,'phase_heal':5}]
   self.notes=['两艘漂泊渔船错位相接，前后跳板把作业甲板连成可互援的船队；右船保留飞行魔物的侧面进攻空间。','两组病人位于护卫后方的左船后甲板，南侧短跳板通向真实沙岸停泊口，撤离方向与靠岸画面一致。','桅杆、船员舱和舷边货物划分护卫前线与病人区域；仍须清除全部魔物并至少一组病人存活靠岸，飞行敌人能绕过跳板。']
 def opened_grid(self):
  g=[r.copy()for r in self.g]
  for o in self.d['objects']:
   for x,y in o.get('opens',[]):g[y][x]='s'
  return g
 def flood(self,g,start):
  seen={tuple(start):0};q=deque([tuple(start)])
  while q:
   x,y=q.popleft()
   for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]:
    p=x+dx,y+dy
    if 0<=p[0]<self.w and 0<=p[1]<self.h and p not in seen and g[p[1]][p[0]]not in'#^~':seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def build(self):
  self.design();c=self.c;g=self.g;w=self.w;h=self.h
  ground=[[self.under.get((x,y),'s')if q=='#'else's'if q=='t'else q for x,q in enumerate(row)]for y,row in enumerate(g)]
  base=[]
  for y,row in enumerate(ground):
   out=[]
   for x,q in enumerate(row):
    v=B.seed(f'{c}:compact-ships:{x}:{y}')%4;tile=B.PACK['base'][MAT[q]][v]
    if q=='s':
     bridge=next((br for br in self.bridges if br['bounds'][0]<=x<=br['bounds'][2]and br['bounds'][1]<=y<=br['bounds'][3]),None)
     deck=next((z for z in self.decks if z['bounds'][0]<=x<=z['bounds'][2]and z['bounds'][1]<=y<=z['bounds'][3]),None)
     working=deck and(y<=deck['bounds'][1]+5 or y>=deck['bounds'][3]-4)
     axis=bridge['axis']if bridge else'h'if working else'v'if deck and deck['main_aisle'][0]<=x<=deck['main_aisle'][1]else'h'
     mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]!='~')
     tile=A.trans['walkway'][axis+str(mask)][v]
     if c=='F21'and working and not bridge:
      key='f21-work-deck:'+str(tile)
      if key not in A.add:
       im=A.cells[tile].copy()
       for py in range(16):
        for px in range(16):
         r,g_,b,a=im.getpixel((px,py));im.putpixel((px,py),(int(r*.90),int(g_*.90),int(b*.90),a))
       A.add[key]=len(A.cells);A.cells.append(im)
      tile=A.add[key]
    elif q=='p':tile=A.edge('dirt','sand',B.mask_at(ground,x,y,lambda z:z in'ps'),v)
    elif q=='d':tile=A.edge('sand','sea',B.mask_at(ground,x,y,lambda z:z!='~'),v)
    out.append(tile)
   base.append(out)
  d=self.d;d.update(map={'width':w,'height':h,'tiles':[IDS[q]for row in g for q in row]},logic_grid=[''.join(r)for r in g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*w for _ in range(h)],self.top],art_modules=self.modules,art_props=self.props,natural_props=[],nature_layout={'biome':'sea','props':[],'excluded':[[0,0,w*16,h*16]]},surroundings='sea',art_atlas='res://assets/chapter2-redesign-20261022/ships/terrain.png',art_columns=32,deck_zones=self.decks,boarding_connections=self.bridges,tactical_notes=self.notes,visual_notes=self.notes.copy(),tactical_review_version='0.10.6-ch2',art_style_version='chapter2-redesign-20261022',landscape_revision='Compact ship composition following approved M41/first-chapter design method')
  d['production_anchors']={'revision':'0.10.6-ch2','deployment':d['player_positions'],'deploy':d['player_positions'],'targets':d['targets'],'exit':d['exit']}
  d['tactical_routes']=[{'name':'登船或停泊通路','bounds':b['bounds'],'axis':b['axis'],'initially_closed':b['initially_closed']}for b in self.bridges]
  d['location_theme']={'F21':'错位双舰、双跳板和后甲板守船区','F22':'中段接应、真实双囚舱与两条登舰路线','S21':'漂泊双船、护卫后甲板与真实沙岸停泊口'}[c]
  self.check();write(R/f'data/stages/{c}.json',d)
 def check(self):
  c=self.c;d=self.d;old=self.old;opened=self.opened_grid();closed_seen=self.flood(self.g,d['player_positions'][0]);opened_seen=self.flood(opened,d['player_positions'][0]);actors=d['enemies']+d['npc_units']+d['reinforcements'];spots=[tuple(p)for p in d['player_positions']]+[tuple(u['position'])for u in actors]
  assert len(spots)==len(set(spots)),(c,'overlapping deployment')
  for p in spots:assert self.g[p[1]][p[0]]not in'#^~',(c,'illegal actor',p,self.g[p[1]][p[0]])
  for p in spots+[tuple(d['exit'])]+[tuple(p)for p in d['targets']]:assert p in opened_seen,(c,'unreachable after unlock',p)
  for group in ['enemies','npc_units','reinforcements']:
   assert len(old[group])==len(d[group]);assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(old[group],d[group]))
  for k in ['characters','terrain','goal','cause','before','during','after','absent_branch','contract','ai_and_timing','reinforcement_turn','equipment_revision','clear_training_exp','event_boats']:assert old.get(k)==d.get(k),(c,k)
  for a,b in zip(old['objects'],d['objects']):
   move={'position','approach','approaches','entrance_cells','opens','open_art_cells','open_art_props'}
   assert {k:v for k,v in a.items()if k not in move}=={k:v for k,v in b.items()if k not in move},(c,b['id'],'object rule changed')
   fronts=b.get('approaches')or[[b['position'][0]+dx,b['position'][1]+dy]for dx,dy in[(0,1),(1,0),(0,-1),(-1,0)]]if b.get('adjacent')else[b['position']]
   assert any(tuple(p)in closed_seen for p in fronts),(c,b['id'],'inaccessible closed object')
  escorts=[]
  for u in d['npc_units']:
   if u.get('quest_kind')in['prisoner','patient']:
    if u.get('locked'):assert tuple(u['position'])not in closed_seen,(c,u['id'],'cell not enclosed')
    dist=self.flood(opened,u['position']).get(tuple(d['exit']));assert dist is not None
    escorts.append({'id':u['id'],'position':u['position'],'exit':d['exit'],'opened_path_length':dist,'initial_locked':u.get('locked',False)})
  before_special={q:sum(row.count(q)for row in old['logic_grid'])for q in'+ht'};after_special={q:sum(row.count(q)for row in self.g)for q in'+ht'};assert before_special==after_special,(c,'rest point counts changed',before_special,after_special)
  changes={group:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(old[group],d[group])]for group in['enemies','npc_units','reinforcements']}
  changes.update(deploy_before=old['player_positions'],deploy_after=d['player_positions'],objects_before=old['objects'],objects_after=d['objects'],exit_before=old['exit'],exit_after=d['exit'],targets_before=old['targets'],targets_after=d['targets'])
  write(O/f'{c}-geometry.json',{'passed':True,'code':c,'size':[self.w,self.h],'closed_reachable_cells':len(closed_seen),'opened_reachable_cells':len(opened_seen),'actors':len(actors),'escorts':escorts,'recovery_and_occupiable_counts_preserved':after_special,'notes':self.notes,'coordinate_changes':changes,'invariants':'All actor identity/order/attributes/equipment/AI and chapter story/objective/timing fields preserved; only coordinates and geometry/art changed.'})
if __name__=='__main__':
 for c,w,h in [('F21',32,26),('F22',34,28),('S21',32,26)]:Field(c,w,h).build()
 A.save();atlas_meta=json.loads((ART/'terrain.json').read_text());atlas_meta['purpose']='Independent native ship-deck zones and shore transitions for F21/F22/S21';write(ART/'terrain.json',atlas_meta);write(O/'asset-review.json',{'atlas':'assets/chapter2-redesign-20261022/ships/terrain.png','native_tile_size':16,'size':[512,math.ceil(len(A.cells)/32)*16],'bytes':(ART/'terrain.png').stat().st_size,'original_tiles':A.original,'compression':'oxipng lossless; full native modules retain alpha, size and complete silhouettes.'})
 print('F21/F22/S21 compact deck revision written.')
