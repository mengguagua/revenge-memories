#!/usr/bin/env python3
"""M12/M13: new landforms and tactical composition, existing rules and actors."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter1-redesign-20261022/grain-prison';BASE=O.parent/'baseline';ART=R/'assets/chapter1-redesign-20261022/grain-prison'
spec=importlib.util.spec_from_file_location('native_atlas',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
L.ART=ART;A=L.Atlas();B=L.B;IDS=B.IDS
MAT={'.':'grass','p':'dirt','f':'grass','^':'grass','~':'sea','#':'grass','c':'cobble','s':'timber','h':'grass','t':'grass','+':'sacred'}
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
class Field:
 def __init__(self,c,w,h):
  self.c=c;self.old=json.loads((BASE/f'{c}.json').read_text());self.d=copy.deepcopy(self.old);self.w=w;self.h=h
  self.g=[list('.'*w)for _ in range(h)];self.under={};self.bridges={};self.routes=[];self.modules=[];self.props=[];self.sites=[];self.layers=[[[None]*w for _ in range(h)]for _ in range(3)]
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):self.g[y][x]=ch
 def poly(self,pts,ch):
  mask=Image.new('1',(self.w,self.h));ImageDraw.Draw(mask).polygon(pts,fill=1)
  for y in range(self.h):
   for x in range(self.w):
    if mask.getpixel((x,y)):self.g[y][x]=ch
 def path(self,pts,width=1,name='',ch='p'):
  for x,y in B.route(pts):self.rect(x-(width-1)//2,y-(width-1)//2,x+width//2,y+width//2,ch)
  if name:self.routes.append({'name':name,'waypoints':pts,'width':width,'surface':ch})
 def bridge(self,x0,y0,x1,y1,axis):
  self.rect(x0,y0,x1,y1,'s')
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):self.bridges[x,y]=axis
 def stamp(self,name,x,y,ground='.',purpose='',occupiable=False):
  m=B.MODULES[name];w,h=m['footprint'];assert 0<=x and 0<=y and x+w<=self.w and y+h<=self.h
  cells=[[xx,yy]for yy in range(y,y+h)for xx in range(x,x+w)]
  for xx,yy in cells:
   assert self.g[yy][xx]!='#',(self.c,name,xx,yy)
   self.under[xx,yy]=ground;self.g[yy][xx]=('t'if name=='tactical_fort'else'h')if occupiable else'#'
  self.modules.append({'name':name,'origin':[x,y],'footprint':[w,h],'cells':cells,'logic':'occupiable'if occupiable else'#','runtime_prop':True,'purpose':purpose})
  self.props.append({'path':m['path'],'position':[x*16,y*16]})
 def jail(self,x,y):
  # A fully enclosed 3x2 room, a single southern door; the door's top sprite stays clear of actors.
  self.rect(x,y,x+4,y+3,'#');self.rect(x+1,y+1,x+3,y+2,'p')
  mh=next(m for m in B.PACK['modules']if m['name']=='jail_bars_h');mv=next(m for m in B.PACK['modules']if m['name']=='jail_bars_v')
  pieces=[('jail_bars_h',x+1,y,[[mh['tiles'][0][1]]*3]),('jail_bars_h',x+1,y+3,[[mh['tiles'][0][1],None,mh['tiles'][0][1]]]),('jail_bars_v',x,y,[mv['tiles'][0],mv['tiles'][1],mv['tiles'][1],mv['tiles'][2]]),('jail_bars_v',x+4,y,[mv['tiles'][0],mv['tiles'][1],mv['tiles'][1],mv['tiles'][2]])]
  for name,ox,oy,tiles in pieces:
   cells=[]
   for dy,row in enumerate(tiles):
    for dx,tile in enumerate(row):
     self.layers[2][oy+dy][ox+dx]=tile
     if tile is not None:cells.append([ox+dx,oy+dy]);self.under[ox+dx,oy+dy]='p'
   self.modules.append({'name':name,'origin':[ox,oy],'footprint':[len(tiles[0]),len(tiles)],'cells':cells,'logic':'#','tiles':tiles})
  self.under[x+2,y+3]='p';return[x+2,y+3]
 def relocate(self,group,positions):
  for u in self.d[group]:u['position']=positions[u['id']]
 def design(self):
  if self.c=='M12':
   # Hill shoulders and an uninterrupted western forest define the grain road.
   self.poly([(0,0),(6,0),(6,3),(4,5),(2,8),(0,9)],'^')
   self.poly([(13,10),(16,9),(18,10),(19,12),(18,13),(18,15),(16,16),(14,14),(12,13)],'^')
   self.poly([(27,0),(29,0),(29,12),(28,11),(27,9),(27,6)],'^')
   self.poly([(0,10),(2,9),(4,10),(4,13),(2,14),(0,15)],'f')
   self.poly([(6,0),(12,0),(14,2),(13,4),(12,6),(9,6),(7,4)],'f')
   self.poly([(8,10),(10,10),(11,12),(10,15),(8,17),(6,16),(6,13)],'f')
   self.poly([(17,20),(19,18),(23,19),(24,21),(26,23),(16,23)],'f')
   self.poly([(28,14),(29,14),(29,23),(27,23),(26,20),(27,17)],'f')
   self.poly([(0,19),(3,20),(4,23),(0,23)],'f')
   self.path([(7,23),(7,18),(13,18),(13,15),(20,15),(20,10),(23,10),(23,7)],2,'折坡粮车主道')
   self.path([(7,18),(5,18),(5,10),(10,10),(10,7),(16,7),(16,5),(18,5),(18,4)],1,'西坡林缘绕仓路')
   self.path([(18,5),(21,5),(21,8),(23,8)],1,'粮台侧门短巷')
   self.path([(23,8),(26,8),(26,3),(26,1),(28,1)],1,'粮台北侧出口')
   self.rect(20,7,26,10,'p');self.rect(18,14,24,16,'p');self.rect(5,18,9,21,'p')
   self.path([(24,16),(24,10)],1,'焚毁兵待命点到仓门')
   self.path([(3,16),(5,16)],1,'医舍前小路');self.path([(4,17),(5,17)],1)
   self.stamp('hill_granary',22,5,'p','目标高地粮仓，南门面向卸货坪')
   self.stamp('hill_granary',17,2,'.','仓吏小屋，南门接西坡小路')
   self.stamp('village_clinic',2,14,'.','西南居民接应医舍')
   self.stamp('grain_wagon',18,17,'p','坡脚车场');self.stamp('grain_sacks',21,7,'p');self.stamp('crates',21,8,'p')
   self.stamp('camp_palisade',25,11,'.','高台东侧矮栅');self.stamp('camp_palisade',17,11,'.','高台西南矮栅')
   self.stamp('tactical_store',20,9,'p','西仓院防守点',True);self.stamp('tactical_store',25,4,'.','北仓院防守点',True)
   self.d['player_positions']=[[7,19],[8,19],[7,20],[6,19],[8,20],[6,20],[9,19],[7,21],[8,21],[5,20]]
   self.relocate('enemies',{'M12_boss':[26,7],'M12_e1':[24,16],'M12_e2':[20,12],'M12_e3':[15,19],'M12_e4':[11,7],'M12_e5':[24,8],'M12_e6':[22,11],'M12_e7':[26,15],'M12_e8':[12,8]})
   self.relocate('npc_units',{'fula':[4,17]});self.d['exit']=[28,1];self.d['targets']=[[23,7],[18,15]]
   self.d['objects'][0]['position']=[23,7]
   self.d['objects'][1].update(position=[18,3],approach=[18,4],approaches=[[18,4]],entrance_cells=[[18,3]])
   for s,p in zip(self.old['building_sites'],[[25,4],[20,9]]):self.sites.append(dict(s,position=p))
   self.d['location_theme']='丘堡粮站：林缘粮车坡路与东北高地仓院'
   self.d['tactical_notes']=['两格粮车道由南侧入场，沿岩肩折向东北高地粮仓；主路只在坡脚车场与仓前卸货坪展开，粮仓南门直接朝向目标格。','西坡一格林缘小路绕过中央岩肩，经过仓吏小屋后接回粮台侧门；树林聚成连续林块，仓院之外保留草地展开面。','焚毁兵在东南待命，第6回合预告、第7回合出发和连续两次点火的规则保持；主路与西坡都能在粮门前截住他，芙拉位于西南医舍安全小院。']
  else:
   self.poly([(0,0),(7,0),(7,2),(5,4),(3,5),(2,8),(0,9)],'^')
   self.poly([(29,0),(31,0),(31,10),(30,9),(29,6)],'^')
   self.poly([(0,16),(3,17),(4,20),(3,23),(0,25)],'^')
   self.poly([(8,0),(12,0),(12,4),(10,6),(7,5),(6,3)],'f')
   self.poly([(0,10),(2,9),(4,11),(4,14),(2,16),(0,16)],'f')
   self.poly([(5,16),(7,15),(9,16),(9,19),(7,20),(4,19)],'f')
   self.poly([(19,10),(21,9),(22,11),(21,13),(19,14)],'f')
   self.poly([(25,17),(29,16),(31,17),(31,23),(28,24),(26,22)],'f')
   self.poly([(10,24),(12,22),(15,22),(16,25),(10,25)],'f')
   # Stream descends through the camp. The short northern bridge and broad southern bridge are both genuine crossings.
   banks=[(13,15)]*6+[(14,16)]*6+[(15,17)]*6+[(16,18)]*8
   for y,(a,b)in enumerate(banks):self.rect(a,y,b,y,'~')
   self.path([(8,25),(8,22),(11,22),(11,18),(23,18),(23,15),(25,15),(25,14)],2,'南门与东囚院押送道')
   self.path([(11,18),(11,11),(6,11)],1,'西囚院救援路')
   self.path([(11,11),(11,8),(20,8),(20,5)],1,'北桥与文书内庭')
   self.path([(20,8),(24,8),(25,8),(25,14)],1,'内庭至东牢巡路')
   self.path([(25,8),(28,8),(28,0)],1,'指挥哨与北口')
   self.path([(23,18),(23,22),(21,22)],1,'南营房支巷')
   self.path([(23,22),(29,22),(29,25)],1,'增援侧路')
   self.rect(5,11,9,12,'p');self.rect(19,5,22,7,'p');self.rect(23,14,28,15,'p');self.rect(7,21,11,23,'p')
   self.bridge(13,8,18,8,'h');self.bridge(15,18,19,19,'h')
   door0=self.jail(4,7);door1=self.jail(23,10)
   self.stamp('command_pavilion',19,3,'.','文书内庭');self.stamp('barracks',10,14,'.','西侧守军营房')
   self.path([(11,16),(11,18)],1,'营房前路')
   self.stamp('command_pavilion',20,20,'.','南侧值守帐');self.stamp('quay_warehouse',25,2,'.','北口军需仓')
   self.stamp('grain_wagon',24,20,'.','东侧车场');self.stamp('crates',22,6,'p');self.stamp('camp_palisade',4,13,'.','西囚院外围矮栅')
   self.stamp('camp_palisade',24,16,'.','东囚院外侧矮栅');self.stamp('camp_palisade',19,23,'.','南营房外栅')
   for p,label in[([9,11],'西囚区岗堡'),([28,14],'东囚区岗堡'),([20,8],'内庭岗堡')]:
    self.stamp('tactical_fort',*p,'p',label,True)
   for s,p in zip(self.old['building_sites'],[[9,11],[28,14],[20,8]]):self.sites.append(dict(s,position=p))
   self.d['player_positions']=[[8,22],[9,22],[8,21],[9,21],[7,22],[10,22],[7,21],[8,23],[9,23],[10,23]]
   self.relocate('enemies',{'M13_boss':[28,5],'M13_e1':[24,15],'M13_e2':[20,17],'M13_e3':[23,21],'M13_e4':[7,12],'M13_e5':[26,7],'M13_e6':[21,14],'M13_e7':[28,21],'M13_e8':[10,13],'M13_e9':[27,15]})
   self.relocate('npc_units',{'M13_workers0':[5,8],'M13_workers1':[24,11],'lena':[7,8]})
   self.relocate('reinforcements',{'M13_r0':[29,24],'M13_r1':[30,24]})
   self.d['exit']=[28,1];self.d['targets']=[door0,door1]
   for o,p in zip(self.d['objects'][:2],[door0,door1]):
    o['position']=p;o['open_art_cells']=[dict(cell,position=p)for cell in o['open_art_cells']]
   self.d['objects'][2].update(position=[20,4],approach=[20,5],approaches=[[20,5],[19,5]],entrance_cells=[[20,4],[19,4]])
   self.d['location_theme']='溪谷押送营：分列两岸的囚院、双桥与北侧文书内庭'
   self.d['tactical_notes']=['押送营沿溪谷分为西囚院、东囚院与北侧内庭；两座桥跨过实际溪水，南桥是两格押送大道，北桥是一格巡守支路。','两间完整牢室只有南侧一格牢门，门前都留出救援小院；西路可先救蕾娜和第一队劳工，南桥支路通往第二囚院，最后在内庭汇合。','营房、文书帐、军需仓和车场围绕道路落位，三处原有岗堡保留地形收益；第5敌回合增援从东南侧路进入，原开门顺序、解锁对应和胜利条件保持。']
 def flood(self,start,opened=False):
  opens={tuple(o['position'])for o in self.d['objects']if o['kind']in['door','rescue']}if opened is True else opened if isinstance(opened,set)else set();seen={tuple(start):0};q=deque([tuple(start)])
  while q:
   x,y=q.popleft()
   for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
    p=(x+dx,y+dy)
    if 0<=p[0]<self.w and 0<=p[1]<self.h and p not in seen and(self.g[p[1]][p[0]]not in'#^~'or opened and p in opens):seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def bake(self):
  self.design();d=self.d;w=self.w;h=self.h;g=self.g
  anchors={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for k in['enemies','npc_units','reinforcements']for u in d[k]]}
  for x,y in anchors:
   assert g[y][x]not in'#^~',(self.c,'blocked actor',x,y)
   if g[y][x]=='f':g[y][x]='.'
  for o in d['objects']:
   for x,y in o.get('approaches',[]):assert g[y][x]not in'#^~',(self.c,'blocked front',o['id'])
  occupied=[tuple(p)for p in d['player_positions']]+[tuple(u['position'])for u in d['enemies']+d['npc_units']]
  assert len(occupied)==len(set(occupied)),(self.c,'duplicate deployment')
  ground=[[self.under.get((x,y),'.')if ch in'#ht'else'.'if ch in'^f'else ch for x,ch in enumerate(row)]for y,row in enumerate(g)]
  for y,row in enumerate(ground):
   for x,ch in enumerate(row):
    v=B.seed(f'{self.c}-composition:{x}:{y}')%4;mat=MAT[ch];tile=B.PACK['base'][mat][v]
    if ch in'pc':tile=A.edge(mat,'grass',B.mask_at(ground,x,y,lambda q:q==ch),v)
    elif ch=='~':tile=A.water([MAT[ground[y+dy][x+dx]]if 0<=x+dx<w and 0<=y+dy<h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
    elif ch=='s':
     mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s');tile=A.trans['walkway'][self.bridges.get((x,y),'h')+str(mask)][v]
    self.layers[0][y][x]=tile
  nature=[];rng=random.Random(B.seed(self.c+'-forest-masses'))
  for ch in['^','f']:
   allowed={(x,y)for y,row in enumerate(g)for x,t in enumerate(row)if t==ch};taken=set();large=['peak_low','crag_tall','ridge_bent','outcrop']if ch=='^'else['pine_tall','pine_broad','pine_pair'];small=['boulder']if ch=='^'else['pine_small_a','pine_small_b','pine_young']
   places=sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0]))
   for x,y in places:
    if(x,y)in taken:continue
    choices=large.copy();rng.shuffle(choices)
    for key in choices:
     sw,sh=B.NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
     if cells<=allowed and not cells&(taken|anchors):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});taken|=cells;break
   for x,y in sorted(allowed-taken):nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.35})
   if ch=='f':
    for x,y in sorted(allowed):
     if(x+y)%2 or rng.random()<.2:continue
     key=rng.choice(['pine_tall','pine_broad']);sw,sh=B.NATURE[key]['size'];px=x*16+rng.randint(-3,3);py=y*16+rng.randint(-2,2);cells={(xx,yy)for yy in range(py//16,math.ceil((py+sh)/16))for xx in range(px//16,math.ceil((px+sw)/16))}
     if cells<=allowed and not cells&anchors:nature.append({'key':key,'position':[px,py],'flip':rng.random()<.35})
   elif self.c=='M12':
    # Join the existing solid hill shoulders into a low cliff silhouette; no collision or path changes.
    for x,y in sorted(allowed):
     if(x+y)%2:continue
     choices=['ridge_bent','outcrop','peak_low'];rng.shuffle(choices)
     for key in choices:
      sw,sh=B.NATURE[key]['size'];px=x*16;py=y*16;cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
      if cells<=allowed and not cells&anchors:nature.append({'key':key,'position':[px,py],'flip':rng.random()<.35});break
  nature.sort(key=lambda p:p['position'][1]+B.NATURE[p['key']]['size'][1])
  d['map'].update(width=w,height=h,tiles=[IDS[c]for row in g for c in row])
  d.update(logic_grid=[''.join(row)for row in g],visual_ground=[''.join(row)for row in ground],art_layers=self.layers,art_modules=self.modules,art_props=self.props,natural_props=nature,building_sites=self.sites,art_atlas='res://assets/chapter1-redesign-20261022/grain-prison/terrain.png',art_columns=32,tactical_routes=self.routes,tactical_review_version='0.10.5-ch1',art_style_version='chapter1-redesign-20261022',landscape_revision='整体地形与战术布局重建',nature_layout={'biome':'forest','props':[],'excluded':[[0,0,w*16,h*16]]})
  d['production_anchors']={'revision':'0.10.5-ch1','deployment':d['player_positions'],'deploy':d['player_positions'],'targets':d['targets'],'exit':d['exit'],'landscape_revision':'chapter1-redesign-20261022'}
  for k in['characters','terrain','enemy_group_ids','boss_id','goal','cause','before','during','after','absent_branch','optional','contract','ai_and_timing','reinforcement_turn','burner_departure_turn','equipment_revision']:assert d.get(k)==self.old.get(k),(self.c,k)
  for k in['enemies','npc_units','reinforcements']:
   assert len(d[k])==len(self.old[k])
   for old,new in zip(self.old[k],d[k]):assert{k:v for k,v in old.items()if k!='position'}=={k:v for k,v in new.items()if k!='position'},(self.c,k,old['id'])
  pos_fields={'position','approach','approaches','entrance_cells','open_art_cells'}
  for old,new in zip(self.old['objects'],d['objects']):assert{k:v for k,v in old.items()if k not in pos_fields}=={k:v for k,v in new.items()if k not in pos_fields},(self.c,old['id'])
  seen=self.flood(d['player_positions'][0]);opened=self.flood(d['player_positions'][0],True)
  unlocked_actors={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for k in['enemies','reinforcements']for u in d[k]]}
  assert unlocked_actors<=set(seen),(self.c,'unreachable',unlocked_actors-set(seen));assert anchors<=set(opened),(self.c,'unreachable NPC',anchors-set(opened))
  for o in d['objects']:
   fronts=o.get('approaches',[o['approach']]if'approach'in o else[])
   if not fronts:
    x,y=o['position'];fronts=[[x,y]]+([[x+dx,y+dy]for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]]if o.get('adjacent')else[])
   assert any(tuple(p)in seen for p in fronts),(self.c,'no front',o['id'])
  report={'passed':True,'code':self.c,'size':[w,h],'closed_connected':len(seen),'opened_connected':len(opened),'notes':d['tactical_notes'],'units_only_positions_changed':True,'object_order_ids_and_rules_preserved':True,'timing_and_story_preserved':True,'positions':{k:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(self.old[k],d[k])]for k in['enemies','npc_units','reinforcements','objects']},'deployment_before':self.old['player_positions'],'deployment_after':d['player_positions'],'target_distances':{o['id']:seen.get(tuple(o['position']))for o in d['objects']}}
  report['interaction_front_distances']={}
  for o in d['objects']:
   x,y=o['position'];fronts=o.get('approaches',[o['approach']]if'approach'in o else[[x,y]]+([[x+dx,y+dy]for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]]if o.get('adjacent')else[]))
   report['interaction_front_distances'][o['id']]=min(seen[tuple(p)]for p in fronts if tuple(p)in seen)
  report['final_map_sha256']=hashlib.sha256((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()
  if self.c=='M12':
   burner=next(u for u in d['enemies']if u.get('burner'));report['burner_to_granary_steps']=self.flood(burner['position']).get(tuple(d['targets'][0]));report['departure_turn']=d['burner_departure_turn'];report['fula_nearest_enemy_distance']=min(abs(u['position'][0]-4)+abs(u['position'][1]-17)for u in d['enemies'])
  else:
   west=self.flood(d['player_positions'][0],{tuple(d['objects'][0]['position'])});east=self.flood(d['player_positions'][0],{tuple(d['objects'][1]['position'])})
   assert(5,8)in west and(7,8)in west and(24,11)not in west
   assert(24,11)in east and(5,8)not in east and(7,8)not in east
   report['single_gate_releases_only_its_room']=True
  write(R/f'data/stages/{self.c}.json',d);write(O/f'{self.c}-design.json',report);return report

if __name__=='__main__':
 reports=[Field('M12',30,24).bake(),Field('M13',32,26).bake()];A.save();write(O/'geometry.json',{'passed':True,'maps':reports})
 print(json.dumps([{'code':r['code'],'passed':True,'size':r['size']}for r in reports],ensure_ascii=False))
