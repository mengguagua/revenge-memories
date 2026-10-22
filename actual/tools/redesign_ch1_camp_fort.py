#!/usr/bin/env python3
"""Only M14/M15: native-scale camp and sea-fort compositions from frozen inputs."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,json,math,random,importlib.util
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter1-redesign-20261022/camp-fort';BASE=O.parent/'baseline';ART=R/'assets/chapter1-redesign-20261022/camp-fort'
spec=importlib.util.spec_from_file_location('terrain_native',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L);L.ART=ART;A=L.Atlas();B=L.B;IDS=B.IDS;MAT=B.MATERIAL
write=lambda p,d:(p.parent.mkdir(parents=True,exist_ok=True),p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'))
class Field:
 def __init__(self,c,w,h):
  self.c=c;self.old=json.loads((BASE/(c+'.json')).read_text());self.d=copy.deepcopy(self.old);self.w=w;self.h=h;self.g=[list(('.'if c=='M14'else'~')*w)for _ in range(h)];self.under={};self.mods=[];self.props=[];self.routes=[];self.axes={};self.sites=[]
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):self.g[y][x]=ch
 def poly(self,points,ch):
  m=Image.new('1',(self.w,self.h));ImageDraw.Draw(m).polygon(points,fill=1)
  for y in range(self.h):
   for x in range(self.w):
    if m.getpixel((x,y)):self.g[y][x]=ch
 def path(self,ps,width=2,ch='p',name=''):
  for x,y in B.route(ps):self.rect(x-(width-1)//2,y-(width-1)//2,x+width//2,y+width//2,ch)
  if name:self.routes.append({'name':name,'waypoints':ps,'width':width,'surface':ch})
 def stamp(self,name,x,y,ground='.',walk=None,occupiable=None,purpose=''):
  m=B.MODULES[name];fw,fh=m['footprint'];cells=[];walk=walk or[]
  assert 0<=x and 0<=y and x+fw<=self.w and y+fh<=self.h,(self.c,name,x,y)
  for yy in range(y,y+fh):
   for xx in range(x,x+fw):
    assert self.g[yy][xx]!='#',(self.c,name,'overlap',[xx,yy]);self.under[xx,yy]=ground;self.g[yy][xx]=occupiable or('c'if[xx,yy]in walk else'#');cells.append([xx,yy])
  self.mods.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':'occupiable'if occupiable else'#','walk_through_cells':walk,'runtime_prop':True,'purpose':purpose});self.props.append({'path':m['path'],'position':[x*16,y*16]})
 def tiles(self,name,x,y,tiles=None):
  m=B.MODULES[name];ts=copy.deepcopy(tiles or m['tiles']);fw=max(len(r)for r in ts);fh=len(ts);cells=[]
  for dy,row in enumerate(ts):
   for dx,t in enumerate(row):
    if t is not None:self.under[x+dx,y+dy]=self.g[y+dy][x+dx];self.g[y+dy][x+dx]='#';cells.append([x+dx,y+dy])
  self.mods.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':'#','tiles':ts})
 def jail(self,index,x,y):
  self.rect(x+1,y+1,x+3,y+2,'c');self.tiles('jail_bars_h',x,y,[[481,482,482,482,483]]);self.tiles('jail_bars_v',x,y+1);self.tiles('jail_bars_v',x+4,y+1)
  bottom=[[481,482,None,482,483]];self.tiles('jail_bars_h',x,y+3,bottom)
  gx,gy=x+2,y+3;self.g[gy][gx]='#';self.under[gx,gy]='p';o=self.d['objects'][index];o['position']=[gx,gy];o['sprite']='jail_door';o['open_art_cells']=[{'position':[gx,gy],'base_tile':B.PACK['base']['dirt'][0],'clear_layers':[1,2]}];self.d['npc_units'][index]['position']=[x+2,y+1]
 def update_positions(self,enemy,deploy,exit):
  for u in self.d['enemies']:u['position']=list(enemy[u['id']])
  self.d['player_positions']=deploy;self.d['exit']=exit
 def camp(self):
  self.poly([(0,0),(7,0),(7,2),(5,4),(3,4),(3,8),(0,9)],'^');self.poly([(29,0),(31,0),(31,8),(29,6),(28,3)],'^')
  self.poly([(0,11),(4,9),(7,10),(8,14),(6,17),(6,22),(3,25),(0,25)],'f');self.poly([(8,0),(17,0),(18,3),(16,5),(11,6),(9,4)],'f');self.poly([(28,10),(31,8),(31,25),(25,25),(25,22),(28,20)],'f');self.poly([(15,20),(19,19),(20,22),(18,25),(14,25)],'f')
  # Connected working courts, with tent walls shaping the camp rather than a vast floor.
  self.rect(12,8,15,15,'p');self.rect(19,5,22,8,'p');self.rect(20,12,26,16,'p');self.rect(23,8,26,11,'p')
  self.path([(10,25),(10,21),(14,21),(14,16),(17,16),(17,10),(22,10),(22,5),(25,5),(25,1)],2,name='南营勤务道—指挥帐')
  self.rect(13,16,15,18,'p')
  self.path([(13,22),(23,22),(23,18),(26,18),(26,11),(25,11)],2,name='东营骑兵通道')
  self.path([(9,21),(7,21),(7,15),(8,15),(8,8),(13,8),(13,5),(20,5)],1,name='西林哨堡绕营小路')
  self.path([(14,12),(24,12)],2,name='帐区横向勤务道');self.path([(21,8),(22,8)],1)
  self.stamp('ruined_watchtower',8,3,purpose='西林旧瞭望塔');self.stamp('command_pavilion',20,6,'p',purpose='文书与指挥帐');self.stamp('command_pavilion',13,9,'p');self.stamp('command_pavilion',13,13,'p');self.stamp('command_pavilion',23,9,'p');self.stamp('command_pavilion',20,13,'p')
  self.stamp('grain_store',23,14,'p',purpose='骑兵粮料库');self.stamp('crates',19,9,'p');self.stamp('well',11,11,'p')
  for x,y in [(9,17),(16,17),(20,18),(27,18),(10,6),(26,5),(27,7)]:self.stamp('camp_palisade',x,y,purpose='营盘围合木障')
  self.stamp('tactical_fort',8,10,occupiable='t',purpose='可驻守旧哨堡');self.stamp('tactical_tent',18,12,'p',occupiable='h');self.stamp('tactical_tent',24,20,occupiable='h')
  self.sites=[{'position':[8,10],'label':'旧哨堡','occupiable':True,'avoid':40,'phase_heal':5},{'position':[18,12],'label':'军帐','occupiable':True,'avoid':20,'phase_heal':0},{'position':[24,20],'label':'军帐','occupiable':True,'avoid':20,'phase_heal':0}]
  self.d['objects'][0]['position']=[14,17];self.d['objects'][1]['position']=[26,18]
  v=self.d['objects'][2];v.update(position=[21,7],approach=[21,8],approaches=[[21,8]],entrance_cells=[[21,7]])
  self.d['camp_checkpoints']=[{'id':'south_checkpoint','name':'南营哨卡','row':17,'opening':[[13,17],[14,17],[15,17]],'fences':[[9,17],[16,17]]},{'id':'east_checkpoint','name':'东营哨卡','row':18,'opening':[[25,18],[26,18]],'fences':[[20,18],[27,18]]}]
  self.update_positions({'M14_boss':[25,5],'M14_e1':[26,10],'M14_e2':[26,15],'M14_e3':[25,20],'M14_e4':[13,8],'M14_e5':[23,7],'M14_e6':[17,13],'M14_e7':[25,19],'M14_e8':[15,7],'M14_e9':[22,11],'M14_e10':[16,10],'M14_e11':[23,16]},[[10,21],[11,21],[12,21],[13,21],[10,22],[11,22],[12,22],[13,22],[9,22],[9,23]],[25,1])
  self.d['location_theme']='旧瞭望塔下的围合军营：南营勤务口、西林哨堡路和东侧骑兵粮道'
  self.notes=['旧瞭望塔与林缘为营盘定形，寝帐朝向中间勤务道，右侧粮料库和骑兵营留出独立调动道路。','南营军旗立在三格勤务口，东营军旗立在侧路木障缺口；两处都需站格控制，文书帐的南门可访问。','可以正面进入南营，也能经西林旧哨堡绕到帐区侧后；右路骑兵会压来，指挥官半血投降与邻接接受规则保持。']
 def fort(self):
  self.poly([(6,0),(29,0),(30,3),(32,5),(32,14),(31,18),(32,24),(29,27),(10,27),(8,25),(6,23),(5,18),(3,14),(4,8)],'.')
  self.poly([(4,3),(6,1),(7,4),(6,8),(6,13),(4,15),(3,12)],'^');self.poly([(7,18),(9,19),(10,23),(8,24),(6,22)],'^');self.poly([(11,0),(17,0),(16,3),(12,4),(9,3)],'f');self.poly([(9,24),(12,22),(14,23),(16,27),(10,27)],'f');self.poly([(29,7),(31,7),(31,14),(29,15),(28,12)],'f')
  self.poly([(11,5),(26,5),(27,8),(25,12),(26,16),(23,18),(14,17),(12,14),(10,11)],'c')
  self.path([(18,27),(18,23),(18,18),(19,18),(19,10),(22,10),(22,6),(28,6),(28,2)],3,'p','正门—中庭—北门退路')
  self.path([(18,23),(29,23),(30,23),(30,5),(28,5),(28,2)],2,'s','东侧港栈—北门截退线')
  self.path([(18,22),(11,22),(11,16),(8,16),(8,12),(9,12),(9,10),(13,10)],2,'p','西崖缺口—西牢区')
  self.path([(23,22),(26,22),(26,21)],2,'p','港侧工棚牢区');self.path([(20,10),(24,10),(24,6),(28,6)],2,'c')
  self.path([(18,6),(18,5)],2,'p');self.rect(15,20,21,24,'p')
  for y in range(5,24):
   for x in [30,31]:self.axes[x,y]='v'
  for x in range(18,31):
   for y in [23,24]:self.axes[x,y]='h'
  self.stamp('coastal_keep',16,1,'c',purpose='旧塔与档案室');self.stamp('sea_gate',26,0,'c',walk=[[27,1],[28,1],[27,2],[28,2]],purpose='北门退路')
  self.stamp('sea_cliff',1,17,'~',purpose='西崖断面');self.stamp('sea_cliff',32,10,'~',purpose='港外礁崖')
  self.stamp('breached_wall',9,16,'.',purpose='西崖破墙');self.stamp('breached_wall',23,16,'.',purpose='正门东侧残墙')
  self.stamp('north_wall',14,18,'p',purpose='正门西门墙');self.tiles('north_wall',21,18,[B.MODULES['north_wall']['tiles'][0][:2]])
  self.stamp('barracks',22,7,'c',purpose='中庭营房');self.stamp('quay_warehouse',26,13,'.',purpose='港侧粮仓');self.stamp('crates',26,15,'p')
  self.jail(0,7,6);self.jail(1,25,19)
  self.stamp('tactical_fort',10,13,occupiable='t',purpose='西崖旧哨堡');self.stamp('tactical_store',28,16,'p',occupiable='h',purpose='港仓可驻守格')
  self.sites=[{'position':[10,13],'label':'旧哨堡','occupiable':True,'avoid':40,'phase_heal':5},{'position':[28,16],'label':'港仓','occupiable':True,'avoid':20,'phase_heal':0}]
  self.d['assault_gate']=[19,18]
  v=self.d['objects'][2];v.update(position=[18,4],approach=[18,5],approaches=[[18,5],[19,5]],entrance_cells=[[18,4],[19,4]])
  self.update_positions({'M15_boss':[20,10],'M15_e1':[25,6],'M15_e2':[21,14],'M15_e3':[28,23],'M15_e4':[13,7],'M15_e5':[28,7],'M15_e6':[22,14],'M15_e7':[26,23],'M15_e8':[14,8],'M15_e9':[25,10],'M15_e10':[21,16],'M15_e11':[30,21],'M15_e12':[15,10],'M15_e13':[29,8],'M15_e14':[23,13]},[[17,22],[18,22],[19,22],[20,22],[17,23],[18,23],[19,23],[20,23],[16,23],[16,24]],[28,2])
  for u,p in zip(self.d['reinforcements'],[[30,25],[29,25]]):u['position']=p
  self.d['surroundings']='sea';self.d['location_theme']='双崖之间的三塔旧堡：前场正门、内庭牢区、东侧港栈与北门截退点'
  self.notes=['海崖收束成旧堡半岛，正门两侧残墙分开前场与中庭；西侧牢区、港侧工棚牢区各有实体围栏与南门。','正面由三格门道攻入中庭，也可从西崖缺口进入；东侧连续木栈沿真正海岸通至北门，可以分派骑兵抢占科兰退路。','科兰仍第6回合且低于半血开始撤离、最晚第8回合出发，原9移动保持；北门距其初始驻点至少两个移动回合，骑兵可提前沿侧栈截住。','档案室门前、两扇牢门和可驻守旧哨堡均与道路相接；营房与粮仓完整落地，不将屋顶或城墙当通路。']
 def finish(self):
  if self.c=='M14':self.camp()
  else:self.fort()
  self.d['targets']=[o['position']for o in self.d['objects']if not o.get('optional',False)];self.d['building_sites']=self.sites
  protected={tuple(p)for p in self.d['player_positions']+[self.d['exit']]+[u['position']for u in self.d['enemies']+self.d['npc_units']+self.d['reinforcements']]}
  for o in self.d['objects']:
   if o['kind']=='visit':protected.update(tuple(p)for p in o['approaches'])
   elif o.get('adjacent'):protected.update((o['position'][0]+dx,o['position'][1]+dy)for dx,dy in[(0,1),(1,0),(-1,0),(0,-1)])
   else:protected.add(tuple(o['position']))
  for x,y in protected:
   if self.g[y][x]=='f':self.g[y][x]='.'
  for p in self.d['player_positions']+[self.d['exit']]+[u['position']for u in self.d['enemies']+self.d['npc_units']+self.d['reinforcements']]:assert self.g[p[1]][p[0]]not in '#^~',(self.c,'blocked anchor',p,self.g[p[1]][p[0]])
  ground=[[self.under.get((x,y),'.')if ch=='#'else'.'if ch in '^fht'else ch for x,ch in enumerate(row)]for y,row in enumerate(self.g)];base=[]
  for y,row in enumerate(ground):
   line=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{self.c}:ch1deep:{x}:{y}')%4;mat=MAT[ch];tile=B.PACK['base'][mat][v]
    if ch in 'pc=':tile=A.edge(mat,'grass',B.mask_at(ground,x,y,lambda z:z==ch),v)
    if ch=='~':tile=A.water([MAT[ground[y+dy][x+dx]]if 0<=x+dx<self.w and 0<=y+dy<self.h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
    if ch=='s':
     mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<self.w and 0<=y+dy<self.h and ground[y+dy][x+dx]=='s');tile=A.trans['walkway'][self.axes.get((x,y),'v')+str(mask)][v]
    line.append(tile)
   base.append(line)
  nature=[];rng=random.Random(B.seed(self.c+'deep-ch1'))
  for ch in '^f':
   allowed={(x,y)for y,row in enumerate(self.g)for x,t in enumerate(row)if t==ch};used=set();large=['peak_low','crag_tall','ridge_bent','outcrop']if ch=='^'else['pine_tall','pine_broad','pine_pair'];small=['boulder']if ch=='^'else['pine_small_a','pine_small_b','pine_young']
   places=sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0]))
   for x,y in places:
    if (x,y)in used:continue
    choices=large.copy();rng.shuffle(choices)
    for key in choices:
     sw,sh=B.NATURE[key]['size'];foot={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
     if foot<=allowed and not foot&(used|protected):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});used|=foot;break
   for x,y in sorted(allowed-used-protected):nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.35})
  top=[[None]*self.w for _ in range(self.h)]
  for mod in self.mods:
   if 'tiles'not in mod:continue
   x,y=mod['origin']
   for dy,row in enumerate(mod['tiles']):
    for dx,t in enumerate(row):top[y+dy][x+dx]=t
  self.d.update(map={'width':self.w,'height':self.h,'tiles':[IDS[t]for row in self.g for t in row]},logic_grid=[''.join(r)for r in self.g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*self.w for _ in range(self.h)],top],art_modules=self.mods,art_props=self.props,natural_props=nature,art_atlas='res://assets/chapter1-redesign-20261022/camp-fort/terrain.png',tactical_review_version='0.10.5-ch1',art_style_version='chapter1-redesign-20261022',tactical_routes=self.routes,tactical_notes=self.notes,nature_layout={'biome':'forest'if self.c=='M14'else'grass','props':[],'excluded':[[0,0,self.w*16,self.h*16]]})
  self.d['production_anchors']={'revision':'0.10.5-ch1','deployment':self.d['player_positions'],'deploy':self.d['player_positions'],'targets':self.d['targets'],'exit':self.d['exit']}
  for group in ['enemies','npc_units','reinforcements']:
   assert len(self.old[group])==len(self.d[group])
   for a,b in zip(self.old[group],self.d[group]):assert {k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'},(self.c,'unit rules changed')
  for key in ['goal','before','during','after','absent_branch','contract','ai_and_timing','reinforcement_turn','equipment_revision','terrain','characters']:assert self.old.get(key)==self.d.get(key)
  positions=[tuple(p)for p in self.d['player_positions']]+[tuple(u['position'])for u in self.d['enemies']+self.d['npc_units']];assert len(positions)==len(set(positions)),(self.c,'overlap')
  report=self.check();write(R/f'data/stages/{self.c}.json',self.d);write(O/f'{self.c}-design.json',report);return report
 def flood(self,start,opened=False):
  opens={tuple(o['position'])for o in self.d['objects']if o['kind']=='rescue'};seen={tuple(start):0};q=deque([tuple(start)])
  while q:
   x,y=q.popleft()
   for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
    p=x+dx,y+dy
    if 0<p[0]<self.w-1 and 0<p[1]<self.h-1 and p not in seen and(self.g[p[1]][p[0]]not in '#^~'or(opened and p in opens)):seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def check(self):
  closed=self.flood(self.d['player_positions'][0]);opened=self.flood(self.d['player_positions'][0],True)
  for p in self.d['player_positions']+[self.d['exit']]+[u['position']for u in self.d['enemies']+self.d['reinforcements']]:assert tuple(p)in closed,(self.c,'unreachable ordinary',p)
  for u in self.d['npc_units']:assert tuple(u['position'])in opened,(self.c,'unreachable freed NPC',u['id'])
  for o in self.d['objects']:
   x,y=o['position'];fronts=o.get('approaches',[[x+dx,y+dy]for dx,dy in[(0,1),(1,0),(-1,0),(0,-1)]]if o.get('adjacent')else[[x,y]])
   assert any(tuple(p)in closed for p in fronts),(self.c,'unreachable interaction',o['id'])
  delta={}
  for group in ['player_positions','exit','targets','objects','enemies','npc_units','reinforcements','building_sites']:
   a=self.old.get(group);b=self.d.get(group)
   if group in ['enemies','npc_units','reinforcements']:a={u['id']:u['position']for u in a};b={u['id']:u['position']for u in b}
   delta[group]={'before':a,'after':b}
  result={'code':self.c,'passed':True,'size':[self.w,self.h],'closed_connected':len(closed),'opened_connected':len(opened),'all_stats_ai_timing_identity_unchanged':True,'coordinate_changes':delta,'notes':self.notes}
  if self.c=='M15':
   boss=next(u for u in self.d['enemies']if u['id']=='M15_boss');bossdist=self.flood(boss['position'])[tuple(self.d['exit'])];result['retreat']={'boss_move':boss['move'],'boss_distance_to_exit':bossdist,'minimum_unopposed_turns':math.ceil(bossdist/boss['move']),'deploy_minimum_steps_to_exit':min(self.flood(p)[tuple(self.d['exit'])]for p in self.d['player_positions']),'unchanged_start_condition':'turn>=6 and hp*2<max_hp, or turn>=8'};assert bossdist>boss['move']
  return result
if __name__=='__main__':
 reports=[Field('M14',32,26).finish(),Field('M15',36,28).finish()];A.save();write(O/'design-summary.json',{'passed':True,'maps':reports});print(json.dumps([{'code':r['code'],'passed':r['passed'],'size':r['size'],'retreat':r.get('retreat')}for r in reports],ensure_ascii=False,indent=2))
