#!/usr/bin/env python3
"""Author the eastern chapter-three port, salt road and regulating court.
Frozen actors/story/rules; only spatial composition and native pixel art change.
"""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter3-redesign-20261022/east';BASE=O.parent/'baseline';ART=R/'assets/chapter3-redesign-20261022/east'
spec=importlib.util.spec_from_file_location('east_native_land',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
L.ART=ART;A=L.Atlas();B=L.B;IDS=L.IDS;MAT=L.MAT
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
class Field:
 def __init__(self,c,w,h,base):
  self.c=c;self.w=w;self.h=h;self.bg=base;self.old=json.loads((BASE/f'{c}.json').read_text());self.d=copy.deepcopy(self.old)
  self.g=[list(base*w)for _ in range(h)];self.under={};self.top=[[None]*w for _ in range(h)];self.props=[];self.modules=[];self.routes=[];self.bridges={};self.rooms=[];self.notes=[]
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):self.g[y][x]=ch
 def poly(self,points,ch):
  mask=Image.new('1',(self.w,self.h));ImageDraw.Draw(mask).polygon(points,fill=1)
  for y in range(self.h):
   for x in range(self.w):
    if mask.getpixel((x,y)):self.g[y][x]=ch
 def path(self,points,width=2,ch=',',name=''):
  for x,y in B.route(points):self.rect(x-(width-1)//2,y-(width-1)//2,x+width//2,y+width//2,ch)
  if name:self.routes.append({'name':name,'waypoints':points,'width':width,'surface':ch})
 def bridge(self,x0,y0,x1,y1,axis='h'):
  self.rect(x0,y0,x1,y1,'s')
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):self.bridges[x,y]=axis
 def stamp(self,name,x,y,ground=None,solid=True,purpose=''):
  m=B.MODULES[name];fw,fh=m['footprint'];cells=[]
  for yy in range(y,y+fh):
   for xx in range(x,x+fw):
    assert 0<=xx<self.w and 0<=yy<self.h,(self.c,name,'outside')
    if solid:self.under[xx,yy]=ground or self.g[yy][xx];self.g[yy][xx]='#'
    cells.append([xx,yy])
  self.props.append({'path':m['path'],'position':[x*16,y*16]});self.modules.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':'#'if solid else'inherits_ground','runtime_prop':True,'purpose':purpose})
 def wall(self,x0,y0,x1,y1,material='stone',ground='b'):
  horizontal=y0==y1;length=x1-x0+1 if horizontal else y1-y0+1
  name=('jail_bars_h'if horizontal else'jail_bars_v')if material=='bars'else('north_wall'if horizontal else'west_wall')
  native=B.MODULES[name]['tiles'];sequence=native[0]if horizontal else[row[0]for row in native]
  ids=[sequence[0]]+[sequence[1+i%max(1,len(sequence)-2)]for i in range(max(0,length-2))]+[sequence[-1]]if length>1 else[sequence[1]]
  cells=[]
  for i,tile in enumerate(ids):
   x=x0+i if horizontal else x0;y=y0 if horizontal else y0+i
   self.top[y][x]=tile;self.under[x,y]=ground;self.g[y][x]='#';cells.append([x,y])
  self.modules.append({'name':name,'origin':[x0,y0],'footprint':[length,1]if horizontal else[1,length],'cells':cells,'tiles':[ids]if horizontal else[[t]for t in ids],'logic':'#','runtime_prop':False,'composition':'Continuous native middle sections, complete endcaps'})
 def room(self,x,y,w,h,door_x,material='bars'):
  self.rect(x,y,x+w-1,y+h-1,'b')
  self.wall(x,y,x+w-1,y,material);self.wall(x,y+h-1,x+w-1,y+h-1,material)
  self.wall(x,y+1,x,y+h-2,material);self.wall(x+w-1,y+1,x+w-1,y+h-2,material)
  # Native endcaps contain inset margins. Complete corners use the original
  # continuous horizontal and vertical bitmaps, joined on the same cell.
  key='east-corner-'+material
  if key not in A.add:
   htile=482 if material=='bars'else 459;vtile=485 if material=='bars'else 463
   joined=A.cells[htile].copy();joined.alpha_composite(A.cells[vtile]);A.add[key]=len(A.cells);A.cells.append(joined)
  for px,py in[(x,y),(x+w-1,y),(x,y+h-1),(x+w-1,y+h-1)]:self.top[py][px]=A.add[key]
  for py in range(y+1,y+h-1):
   self.top[py][x]=485 if material=='bars'else 463
   self.top[py][x+w-1]=485 if material=='bars'else 463
  dy=y+h-1;self.top[dy-1][door_x]=405;self.top[dy][door_x]=406
  self.rooms.append({'bounds':[x,y,x+w-1,dy],'door':[door_x,dy]})
  return [door_x,dy]
 def door(self,id,p):
  o=next(o for o in self.d['objects']if o['id']==id);o.update(position=p,opens=[p],open_art_cells=[{'position':[p[0],p[1]-1+i],'base_tile':B.PACK['base']['cobble'][0],'clear_layers':[1,2]}for i in [0,1]])
 def units(self,deploy,enemies,npcs):
  self.d['player_positions']=deploy
  for u,p in zip(self.d['enemies'],enemies):u['position']=p
  for u,p in zip(self.d['npc_units'],npcs):u['position']=p
  assert len(enemies)==len(self.d['enemies'])and len(npcs)==len(self.d['npc_units'])
 def design(self):
  if self.c=='F31':
   # The sea takes the west third. A broken wharf edge and two piers explain
   # the port's working frontage; the rescue ship is physically alongside it.
   self.poly([(12,0),(31,0),(31,25),(17,25),(17,23),(11,23),(11,17),(12,17),(12,14),(10,14),(10,9),(12,9)],',')
   self.rect(12,0,13,22,'b');self.rect(10,10,13,12,'s');self.rect(8,20,13,22,'s');self.rect(12,23,17,24,'s')
   self.poly([(3,14),(5,14),(6,15),(7,17),(7,23),(6,24),(2,24),(1,23),(1,17),(2,15)],'s')
   self.bridge(7,20,11,21)
   self.stamp('bow',3,14,solid=False);self.stamp('stern',3,23,solid=False)
   self.stamp('mast',2,16,ground='s');self.stamp('captain_cabin',2,19,ground='s');self.stamp('medicine_wagon',5,22,ground='s');self.rect(4,22,4,22,'+')
   self.path([(14,23),(14,6),(20,6),(20,1)],2,'b','码头仓街主路')
   self.path([(14,12),(29,12),(29,2)],2,'b','北拘留院与海关后街')
   self.path([(14,21),(29,21),(29,12)],2,'b','南拘留院转运路')
   self.path([(24,7),(24,9),(20,9),(20,12)],2,'b','北院门前接驳')
   self.path([(24,19),(24,21)],2,'b','南院门前接驳')
   self.door('ship_lock',self.room(22,2,7,6,25));self.door('mooring',self.room(22,14,7,6,25))
   for name,x,y in [('quay_warehouse',15,2),('quay_warehouse',17,8),('quay_warehouse',16,15),('fishing_cottage',18,18),('grain_sacks',16,10),('crates',17,10),('grain_wagon',17,13),('bollard',10,10),('bollard',11,22),('bollard',16,24)]:self.stamp(name,x,y,ground=',')
   self.rect(24,8,26,9,'b');self.rect(24,20,26,21,'b')
   self.units([[12,19],[13,19],[14,19],[12,20],[13,20],[14,20],[12,21],[13,21],[14,21]],[[29,4],[15,13],[20,6],[28,23],[18,12],[19,17],[30,9],[30,22],[17,5],[20,10],[29,13]],[[24,4],[24,16]])
   for u,p in zip(self.d['reinforcements'],[[30,16],[30,17]]):u['position']=p
   self.d['exit']=[5,23];self.d['targets']=[o['position']for o in self.d['objects']]
   self.notes=['西侧海面、错落码头、仓库街与西南接应船组成实际港口；跳板跨过真实水面，船医区位于己船后甲板。','南北两座拘留院分别围合，南向门直接接入门前广场和仓街；解锁后的伤者沿已推进的街区回撤，不需穿过敌方后街。','守军分布在码头入口、仓街交叉口与东侧巡逻街；两院与弓手至少相隔四格，开局被扣伤者安全。仍须解两门、击败队长并接回全部存活伤者。']
  elif self.c=='F32':
   # Salt pools and two coherent ridges force a real dry crossing; the east
   # open pan is a tempting exposed approach to the same northern gate.
   self.poly([(0,0),(8,0),(7,3),(5,4),(5,7),(2,8),(0,7)],'^')
   self.poly([(0,13),(3,12),(5,14),(5,17),(3,19),(0,19)],'^')
   self.poly([(25,19),(28,17),(29,18),(29,25),(24,25),(23,23)],'^')
   self.poly([(17,8),(19,7),(21,9),(21,12),(20,14),(18,15),(17,13),(16,10)],'~')
   self.poly([(1,10),(3,9),(6,10),(7,12),(6,14),(4,15),(1,14),(0,12)],'~')
   self.poly([(15,19),(17,18),(20,19),(22,21),(21,24),(19,25),(16,24),(15,22)],'~')
   self.path([(7,25),(7,21),(9,21),(9,17),(11,17),(11,14),(14,14),(14,10),(15,10),(15,7),(22,7),(22,3),(27,3)],2,',','盐池西侧干道与北关')
   self.path([(11,18),(23,18),(23,7),(22,7)],1,',','东盐盘直线支路')
   self.path([(15,7),(11,7),(11,4),(20,4),(22,4)],1,',','旧井北侧丘脊旁路')
   self.rect(12,11,15,14,',');self.stamp('well',12,11,ground=',');self.rect(13,12,13,12,'+')
   self.stamp('fishing_cottage',6,17,ground='a');self.path([(7,19),(9,19)],1,',','向导住屋与路线册')
   self.stamp('ruined_watchtower',9,3,ground='a');self.stamp('command_pavilion',24,1,ground='a');self.path([(25,3),(27,3)],2,',')
   self.stamp('camp_palisade',19,1,ground='a');self.stamp('camp_palisade',27,5,ground='a')
   self.rect(23,14,23,14,'#');self.under[23,14]='a'
   self.d['objects'][0].update(position=[23,14],opens=[[23,14]],open_art_cells=[{'position':[23,14],'base_tile':B.PACK['base']['dirt'][0],'clear_layers':[1,2]}])
   self.d['objects'][1]['position']=[8,19]
   self.units([[7,20],[8,20],[9,20],[10,20],[7,21],[8,21],[9,21],[10,21],[7,22],[8,22]],[[26,4],[21,7],[15,7],[22,19],[11,5],[23,5],[20,16],[25,16],[25,11],[25,7],[18,5],[26,17]],[[7,24]])
   self.d['exit']=[27,2];self.d['targets']=[o['position']for o in self.d['objects']]
   self.notes=['盐池和低岩脊围出西侧弯曲干道，中央旧井与休息格形成可辨认的停靠处；14,12附近的既有台词触发区位于干道上。','东侧直行盐盘短而开阔，路障、弓手和术士形成较危险的直线选择；西侧旧井干道与北丘小路提供有层次的接近路线。','向导从护卫后方起步，通过中央井院向北关撤离；路线册就在南侧向导住屋前，向导死亡分支仍可按原规则完成。']
  else:
   # A compound, not a carpet: workshop, archive forecourt and a regulating
   # water court form three rooms linked by a circulation loop.
   self.poly([(0,0),(14,0),(13,2),(10,3),(6,3),(4,6),(3,10),(0,12)],'^')
   self.poly([(26,0),(29,0),(29,7),(28,8),(27,6)],'^')
   self.poly([(0,20),(3,22),(3,25),(0,25)],'^')
   self.rect(4,4,27,22,',');self.wall(4,3,26,3);self.wall(27,4,27,21);self.wall(4,4,4,11)
   self.wall(4,22,6,22);self.wall(10,22,27,22)
   self.path([(8,25),(8,19),(13,19),(13,7),(23,7)],2,'b','后门至调节院主廊')
   self.path([(13,19),(23,19),(23,7)],2,'b','东侧维修环廊')
   self.path([(7,8),(13,8)],2,'b','档案前庭');self.rect(5,7,10,9,'b')
   self.rect(14,10,19,16,'~');self.rect(15,11,18,14,'=');self.bridge(12,12,15,12);self.bridge(18,12,21,12)
   self.path([(21,12),(23,12)],1,'b','阵台东廊');self.rect(15,11,18,14,'=');self.rect(16,12,16,12,'b')
   self.door('workers_gate',self.room(5,12,7,7,8,'stone'))
   self.stamp('barracks',6,13,ground='b',purpose='工房内部设备间');self.stamp('quay_warehouse',6,4,ground=',',purpose='调节档案屋')
   self.stamp('coastal_keep',21,3,ground=',',purpose='北侧控制楼');self.stamp('ritual_lamp',13,8,ground='b');self.stamp('ritual_lamp',20,8,ground=',')
   self.stamp('crates',10,20,ground=',');self.stamp('grain_sacks',11,20,ground=',');self.stamp('well',25,19,ground=',')
   self.poly([(6,10),(8,10),(9,11),(6,11)],'f');self.poly([(24,14),(26,14),(26,17),(25,17),(24,16)],'f')
   self.rect(7,20,7,20,'+')
   record=next(o for o in self.d['objects']if o['id']=='regulation_record');record.update(position=[7,6],approach=[7,7])
   next(o for o in self.d['objects']if o['id']=='control_array')['position']=[16,12]
   self.units([[7,23],[8,23],[9,23],[10,23],[7,24],[8,24],[9,24],[10,24],[11,23],[11,24]],[[23,8],[21,10],[14,7],[17,20],[16,6],[25,11],[22,15],[25,20],[10,7],[26,8],[17,8],[22,18]],[[6,16],[10,16]])
   self.d['exit']=[25,7];self.d['targets']=[o['position']for o in self.d['objects']]
   self.notes=['后门进入工房前庭，西侧工房与档案屋、北侧控制楼和中央调节水院组成围合设施；石廊、裸盐地、种植槽与水面区分用途，避免整图同质铺砖。','中央阵台为水院中的真实石岛，西东两座维修桥都跨越水格、落在可走岸上；外围环廊连接设备、记录与主楼，角色可选择两侧接近守军。','两名设施术士置于南侧完整工房墙内；唯一南门从部署前庭接近，开门后仍留在受护卫控制的后方。门、档案和阵台保持原交互与两人必须存活判定。']
 def flood(self,g,start):
  q=deque([tuple(start)]);seen={tuple(start):0}
  while q:
   x,y=q.popleft()
   for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
    p=x+dx,y+dy
    if 0<=p[0]<self.w and 0<=p[1]<self.h and p not in seen and g[p[1]][p[0]]not in'#^~':seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def build(self):
  self.design();d=self.d;g=self.g;w=self.w;h=self.h
  anchors={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for u in d['enemies']+d['npc_units']+d['reinforcements']]}
  for p in anchors:assert g[p[1]][p[0]]not in'#^~',(self.c,'actor blocked',p,g[p[1]][p[0]])
  ground=[[self.under.get((x,y),self.bg)if q=='#'else self.bg if q=='f'else q for x,q in enumerate(row)]for y,row in enumerate(g)]
  if self.c=='F32':
   # Worn paths are a surface layer on the same 48-ID walkable salt ground;
   # soften their geometry without moving any combat or escort cell.
   for y,row in enumerate(ground):
    for x,q in enumerate(row):
     if q==',':ground[y][x]='a'
   trails=[([(7,25),(7,21),(10,18),(11,16),(11,14),(14,13),(14,11),(15,9),(15,7),(18,6),(22,5),(25,4),(27,3)],2),
           ([(11,14),(10,11),(9,8),(10,6),(14,5),(18,6)],1),
           ([(12,17),(16,17),(19,18),(23,18),(24,15),(23,11),(23,8),(22,5)],1),
           ([(7,19),(9,19)],1)]
   for points,width in trails:
    for x,y in B.route(points):
     for dy in range(width):
      if 0<=x<w and 0<=y+dy<h and g[y+dy][x]not in'#^~+':ground[y+dy][x]=','
  base=[]
  for y,row in enumerate(ground):
   line=[]
   for x,q in enumerate(row):
    v=B.seed(f'{self.c}:ch3-east:{x}:{y}')%4;tile=B.PACK['base'][MAT[q]][v]
    if q in',b=':
     bg='salt'if self.bg=='a'else'dirt';tile=A.edge(MAT[q],bg,B.mask_at(ground,x,y,lambda z:z==q),v)
    if q=='^':tile=A.edge('rock','salt',B.mask_at(ground,x,y,lambda z:z=='^'),v)
    if q=='~':tile=A.water([MAT[ground[y+dy][x+dx]]if 0<=x+dx<w and 0<=y+dy<h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
    if q=='s':
     mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s')
     tile=A.trans['walkway'][self.bridges.get((x,y),'v')+str(mask)][v]
    line.append(tile)
   base.append(line)
  nature=[];rng=random.Random(B.seed(self.c+'-coherent-ridges'))
  for ch in'^f':
   allowed={(x,y)for y,row in enumerate(g)for x,q in enumerate(row)if q==ch};taken=set()
   large=['peak_low','crag_tall','ridge_bent','outcrop']if ch=='^'else['pine_tall','pine_broad','pine_pair']
   small=['boulder','stone_low']if ch=='^'else['pine_young','pine_small_a','pine_small_b']
   places=sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0]))
   for x,y in places:
    if (x,y)in taken:continue
    choices=large.copy();rng.shuffle(choices)
    for key in choices:
     sw,sh=B.NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
     if cells<=allowed and not cells&(taken|anchors):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.3});taken|=cells;break
   for x,y in sorted(allowed-taken):
    key=rng.choice(small);sw,sh=B.NATURE[key]['size']
    if sw>16:key='boulder'
    nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.3})
  nature.sort(key=lambda p:p['position'][1]+B.NATURE[p['key']]['size'][1])
  d.update(map={'width':w,'height':h,'tiles':[IDS[q]for row in g for q in row]},logic_grid=[''.join(r)for r in g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*w for _ in range(h)],self.top],art_modules=self.modules,art_props=self.props,natural_props=nature,nature_layout={'biome':'sea'if self.bg=='~'else'salt','props':[],'excluded':[[0,0,w*16,h*16]]},surroundings='sea'if self.bg=='~'else'',art_atlas='res://assets/chapter3-redesign-20261022/east/terrain.png',art_columns=32,tactical_review_version='0.10.7-ch3',art_style_version='chapter3-redesign-20261022',landscape_revision='Eastern whole-map composition following approved M41 method',visual_notes=self.notes.copy(),tactical_notes=self.notes.copy(),tactical_routes=self.routes)
  self.check();write(R/f'data/stages/{self.c}.json',d)
  digest=hashlib.sha256((R/f'data/stages/{self.c}.json').read_bytes()).hexdigest()
  write(O/f'{self.c}-change.json',{'code':self.c,'map_sha256':digest,'revision':'0.10.7-ch3','notes':self.notes,'dimensions':[w,h]})
 def check(self):
  c=self.c;d=self.d;old=self.old;opened=[r.copy()for r in self.g]
  for o in d['objects']:
   for x,y in o.get('opens',[]):opened[y][x]='='
  closed_seen=self.flood(self.g,d['player_positions'][0]);seen=self.flood(opened,d['player_positions'][0])
  allpos=[tuple(p)for p in d['player_positions']]+[tuple(u['position'])for u in d['enemies']+d['npc_units']+d['reinforcements']]
  assert len(allpos)==len(set(allpos)),(c,'actor overlap')
  assert all(0<x<self.w-1 and 0<y<self.h-1 for x,y in d['player_positions']),(c,'deployment touches outside movement ring')
  for p in allpos+[tuple(d['exit'])]:assert p in seen,(c,'unreachable',p)
  for a,b in zip(old['objects'],d['objects']):
   move={'position','approach','approaches','entrance_cells','opens','open_art_cells','open_art_props'}
   assert{k:v for k,v in a.items()if k not in move}=={k:v for k,v in b.items()if k not in move},(c,'object rules',a['id'])
   x,y=b['position'];fronts=[(x+dx,y+dy)for dx,dy in[(1,0),(0,1),(-1,0),(0,-1)]]if b.get('adjacent')else[(x,y)]
   assert any(p in closed_seen for p in fronts),(c,'closed interaction unreachable',b['id'])
  for group in['enemies','npc_units','reinforcements']:
   assert len(old[group])==len(d[group]);assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(old[group],d[group])),(c,'actor invariant',group)
  for key in['characters','terrain','goal','before','during','after','reinforcement_turn','event_boats','clear_training_exp','equipment_revision']:assert old.get(key)==d.get(key),(c,key)
  escort=[]
  for u in d['npc_units']:
   p=tuple(u['position'])
   if u.get('locked'):assert p not in closed_seen,(c,'room leaks',u['id'])
   route=self.flood(opened,p).get(tuple(d['exit']));assert route is not None
   escort.append({'id':u['id'],'position':u['position'],'opened_exit_steps':route,'initially_enclosed':p not in closed_seen})
  oldspecial={q:sum(r.count(q)for r in old['logic_grid'])for q in'+ht'};newspecial={q:sum(r.count(q)for r in self.g)for q in'+ht'};assert oldspecial==newspecial,(c,'recovery change',oldspecial,newspecial)
  changes={group:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(old[group],d[group])]for group in['enemies','npc_units','reinforcements']}
  changes.update(deploy_before=old['player_positions'],deploy_after=d['player_positions'],objects_before=old['objects'],objects_after=d['objects'],exit_before=old['exit'],exit_after=d['exit'],targets_before=old['targets'],targets_after=d['targets'])
  write(O/f'{c}-geometry.json',{'passed':True,'size':[self.w,self.h],'closed_reachable_cells':len(closed_seen),'opened_reachable_cells':len(seen),'escorts':escort,'rooms':self.rooms,'bridges':[{'position':list(p),'axis':axis}for p,axis in self.bridges.items()],'coordinate_changes':changes,'notes':self.notes})
  write(O/f'{c}-invariants.json',{'passed':True,'actor_identity_order_attributes_equipment_AI_preserved':True,'objective_story_timing_preserved':True,'special_terrain_counts':newspecial,'original_stage_sha256':hashlib.sha256((BASE/f'{c}.json').read_bytes()).hexdigest()})
if __name__=='__main__':
 for args in [('F31',32,26,'~'),('F32',30,26,'a'),('F33',30,26,'a')]:Field(*args).build()
 A.save();meta=json.loads((ART/'terrain.json').read_text());meta['purpose']='Independent native terrain transitions and complete wall corner modules for F31/F32/F33';write(ART/'terrain.json',meta)
 write(O/'asset-review.json',{'atlas':'assets/chapter3-redesign-20261022/east/terrain.png','native_tile_size':16,'size':meta['size'],'bytes':meta['bytes'],'original_ids_preserved':A.original,'compression':'oxipng lossless','quality_note':'Whole native silhouettes and original scale retained; independent atlas preserves shared assets. Native horizontal and vertical middle pieces join enclosed-room corners.'})
 print('F31 F32 F33 authored and verified. Independent atlas saved.')
