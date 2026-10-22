#!/usr/bin/env python3
"""Chapter-four western route redesign; native materials and real enclosed architecture."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter4-redesign-20261022/west';BASE=O.parent/'baseline';ART=R/'assets/chapter4-redesign-20261022/west'
spec=importlib.util.spec_from_file_location('native_atlas',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
L.ART=ART;A=L.Atlas();B=L.B;IDS=dict(B.IDS,b=48);MAT=dict(B.MATERIAL,b='cobble')
write=lambda p,d:(p.parent.mkdir(parents=True,exist_ok=True),p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'))
def jail_corner():
 key='complete-jail-corner'
 if key not in A.add:
  tile=A.cells[482].copy();tile.alpha_composite(A.cells[485]);A.add[key]=[len(A.cells)];A.cells.append(tile)
 return A.add[key][0]
class Field:
 def __init__(self,c,w,h):
  self.c=c;self.old=json.loads((BASE/f'{c}.json').read_text());self.d=copy.deepcopy(self.old);self.w=w;self.h=h;self.base='n' if c in ['M43','S41']else'.';self.g=[list(self.base*w)for _ in range(h)];self.under={};self.routes=[];self.modules=[];self.props=[];self.layers=[[[None]*w for _ in range(h)]for _ in range(3)];self.solid=set()
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):self.g[y][x]=ch
 def poly(self,points,ch):
  im=Image.new('1',(self.w,self.h));ImageDraw.Draw(im).polygon(points,fill=1)
  for y in range(self.h):
   for x in range(self.w):
    if im.getpixel((x,y)):self.g[y][x]=ch
 def path(self,points,width=1,name='',ch='p'):
  for x,y in B.route(points):self.rect(x-(width-1)//2,y-(width-1)//2,x+width//2,y+width//2,ch)
  if name:self.routes.append({'name':name,'waypoints':points,'width':width,'surface':ch})
 def stamp(self,name,x,y,ground='.',purpose=''):
  m=B.MODULES[name];fw,fh=m['footprint'];cells=[]
  assert 0<=x and 0<=y and x+fw<=self.w and y+fh<=self.h
  for yy in range(y,y+fh):
   for xx in range(x,x+fw):
    assert(xx,yy)not in self.solid,(self.c,name,xx,yy)
    self.under[xx,yy]=ground;self.g[yy][xx]='#';cells.append([xx,yy]);self.solid.add((xx,yy))
  self.modules.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':'#','runtime_prop':True,'purpose':purpose});self.props.append({'path':m['path'],'position':[x*16,y*16]})
 def tiled(self,name,x,y,tiles):
  cells=[]
  for dy,row in enumerate(tiles):
   for dx,t in enumerate(row):
    if t is None:continue
    xx,yy=x+dx,y+dy;self.g[yy][xx]='#';self.under[xx,yy]='b';self.layers[2][yy][xx]=t;cells.append([xx,yy]);self.solid.add((xx,yy))
  self.modules.append({'name':name,'origin':[x,y],'footprint':[len(tiles[0]),len(tiles)],'cells':cells,'logic':'#','tiles':tiles})
 def jail(self,x,y):
  self.rect(x,y,x+4,y+3,'#');self.rect(x+1,y+1,x+3,y+2,'c')
  mh=next(m for m in B.PACK['modules']if m['name']=='jail_bars_h');mv=next(m for m in B.PACK['modules']if m['name']=='jail_bars_v')
  self.tiled('jail_bars_h',x+1,y,[[mh['tiles'][0][1]]*3]);self.tiled('jail_bars_h',x+1,y+3,[[mh['tiles'][0][1],None,mh['tiles'][0][1]]])
  for xx in[x,x+4]:self.tiled('jail_bars_v',xx,y,[[jail_corner()],mv['tiles'][1],mv['tiles'][1],[jail_corner()]])
  self.under[x+2,y+3]='c';return[x+2,y+3]
 def relocate(self,group,positions):
  for u in self.d[group]:u['position']=positions[u['id']]
 def wall_h(self,x0,x1,y,gaps=(),wood=False):
  tile=475 if wood else 459;self.tiled('palisade_h'if wood else'fort_wall_h',x0,y,[[None if x in gaps else tile for x in range(x0,x1+1)]])
  for x in range(x0,x1+1):
   if x not in gaps:self.under[x,y]=self.base
 def wall_v(self,x,y0,y1,gaps=(),wood=False):
  tile=479 if wood else 463;self.tiled('palisade_v'if wood else'fort_wall_v',x,y0,[[None if y in gaps else tile]for y in range(y0,y1+1)])
  for y in range(y0,y1+1):
   if y not in gaps:self.under[x,y]=self.base
 def corner(self,x,y,wood=False):
  h,v=(475,479)if wood else(459,463);key=f'corner-{h}-{v}'
  if key not in A.add:
   im=A.cells[h].copy();im.alpha_composite(A.cells[v]);A.add[key]=[len(A.cells)];A.cells.append(im)
  self.tiled('complete_wall_corner',x,y,[[A.add[key][0]]]);self.under[x,y]=self.base
 def design(self):
  d=self.d;c=self.c
  if c=='M42':
   self.poly([(0,0),(8,0),(9,4),(7,8),(3,9),(0,7)],'^');self.poly([(28,19),(31,17),(31,27),(25,27),(25,24)],'^')
   self.poly([(0,12),(3,10),(6,13),(5,17),(2,20),(0,20)],'f');self.poly([(8,10),(12,9),(14,12),(14,16),(12,19),(8,18)],'f');self.poly([(27,1),(31,0),(31,12),(29,14),(27,11)],'f');self.poly([(15,2),(18,1),(20,3),(20,5),(17,7),(14,6)],'f')
   self.path([(7,25),(16,25),(16,18),(21,18),(21,7),(24,7),(24,6)],2,'军需大道与骑兵正面')
   self.path([(7,24),(6,24),(6,18),(10,18),(10,9),(20,9),(20,7)],1,'西林旧营交涉与侧攻路')
   self.path([(21,17),(25,17),(25,23),(29,23),(29,25)],2,'骑兵东营及增援通道')
   self.rect(17,11,20,13,'b');self.path([(16,12),(19,12),(23,12)],1,'投送站西门与仓房装卸路')
   self.wall_h(16,26,8,[20,21],True);self.wall_h(16,26,16,[20,21],True);self.wall_v(16,8,16,[12,13],True);self.wall_v(26,8,16,[14],True)
   for p in[(16,8),(26,8),(16,16),(26,16)]:self.corner(*p,True)
   self.stamp('coastal_keep',22,2,'.','北端铁骑关堡，门朝军道');self.stamp('sun_altar',17,9,'b','营内投送装置');self.stamp('quay_warehouse',22,10,'.','投送物资库');self.stamp('barracks',3,20,'.','旧同袍西营后方住舍');self.stamp('command_pavilion',24,19,'.','骑兵东营');self.stamp('crates',24,13,'.','营内货箱')
   self.path([(4,22),(6,22)],1);self.path([(25,21),(25,23)],1);self.path([(24,6),(27,6)],1)
   d['player_positions']=[[7,23],[8,23],[7,24],[8,24],[6,23],[9,23],[6,24],[9,24],[7,25],[8,25]]
   self.relocate('npc_units',{'old_comrade':[6,22],'station_worker':[4,23]})
   self.relocate('enemies',{'M42_boss':[24,6],'M42_e1':[13,8],'M42_e2':[18,13],'M42_e3':[25,22],'M42_e4':[21,19],'M42_e5':[22,7],'M42_e6':[22,14],'M42_e7':[27,18],'M42_e8':[12,7],'M42_e9':[25,7],'M42_e10':[19,9],'M42_e11':[24,23],'M42_e12':[14,8],'M42_e13':[26,6]})
   self.relocate('reinforcements',{'M42_r0':[29,23],'M42_r1':[29,24]})
   d['objects'][0]['position']=[19,12];d['objects'][1]['position']=[25,18];d['exit']=[27,6]
   d['tactical_notes']=['西北岩坡与中央密林夹出骑兵军道，东侧投送营以完整木栅围合，南北主门连大道，西门接林缘旧营。','兰斯的旧同袍退至西营后方住舍旁，部署当轮可到邻格交涉，再沿西路从营侧进入；主道利于骑兵展开，林路更窄且需绕开树丛。','投送装置、库房和东骑兵营各有装卸/巡行通路，第5回合东南来援保持；旧同袍转中立与切断投送规则不变。']
  elif c=='M43':
   self.poly([(0,0),(6,0),(8,4),(7,9),(4,12),(0,10)],'^');self.poly([(27,0),(29,0),(29,27),(26,27),(25,23),(27,18)],'^')
   self.poly([(0,15),(3,13),(5,16),(4,20),(1,22),(0,22)],'f');self.poly([(11,1),(16,0),(18,3),(17,6),(13,7),(10,4)],'f');self.poly([(15,23),(20,22),(24,24),(24,27),(14,27)],'f')
   self.rect(11,6,25,19,'n')
   self.path([(7,25),(15,25),(15,20),(15,12),(22,12),(22,6)],2,'南门外院至日塔主路',ch='=')
   self.path([(6,24),(6,12),(11,12),(13,12),(13,8),(21,8)],1,'雪林西门侧攻路',ch='p')
   self.path([(15,18),(20,18),(20,17)],2,'控制室南面接管通路',ch='=');self.path([(22,10),(24,10)],1,'塔后联络口',ch='=')
   self.wall_h(10,26,5,list(range(20,24)));self.wall_h(10,26,20,[14,15,16]);self.wall_v(10,5,20,[12,13]);self.wall_v(26,5,20)
   for p in[(10,5),(26,5),(10,20),(26,20)]:self.corner(*p)
   self.stamp('coastal_keep',20,2,'n','日塔北侧主楼');self.stamp('tower_entry',23,6,'n','日塔塔身');self.stamp('quay_warehouse',19,15,'n','院内控制室，南面操作');self.stamp('village_clinic',6,17,'n','墙外病人照护所');self.stamp('snow_cottage',11,22,'n','外院守望住舍');self.stamp('ritual_lamp',17,6,'n','路北日塔院内照明装置')
   self.path([(7,19),(7,22),(15,22)],1,'医舍至主门接应路');self.path([(12,24),(15,24)],1)
   d['player_positions']=[[7,23],[8,23],[7,24],[8,24],[6,23],[9,23],[6,24],[9,24],[7,25],[8,25]]
   self.relocate('npc_units',{'tower_worker':[5,21],'tower_patients':[8,20]})
   self.relocate('enemies',{'M43_boss':[22,8],'M43_e1':[21,6],'M43_e2':[16,14],'M43_e3':[22,18],'M43_e4':[12,8],'M43_e5':[20,7],'M43_e6':[16,17],'M43_e7':[23,17],'M43_e8':[13,10],'M43_e9':[21,10],'M43_e10':[18,14],'M43_e11':[24,15],'M43_e12':[13,7],'M43_e13':[25,9]})
   d['objects'][0]['position']=[15,19];d['objects'][1].update(position=[20,16],approach=[20,17]);d['exit']=[24,10]
   d['tactical_notes']=['日塔院墙在北境岩脊间围成完整庭院，主楼和塔身位于北端，控制室位于东南角；院内积雪与石路交错，避免整片铺石。','三格南门承接宽主路，西侧两格小门接雪林侧路；正面更直接，西侧可绕开门前重装但行进空间较窄。','病人与工匠留在西南医舍侧后，避开初始守军射程和唯一门口；夺外院、接管控制室及等待东岸步骤的原流程保持。']
  elif c=='M44':
   self.poly([(0,0),(1,0),(1,27),(0,27)],'^');self.poly([(29,0),(31,0),(31,27),(29,27),(28,23),(30,18)],'^')
   self.poly([(2,18),(5,17),(7,20),(6,23),(3,25),(1,23)],'f');self.poly([(19,23),(23,22),(26,24),(26,27),(18,27)],'f');self.poly([(9,1),(13,1),(14,4),(11,6),(9,4)],'f')
   self.path([(10,25),(15,25),(15,10),(15,7),(26,7)],2,'王都正门主街',ch='=')
   self.path([(10,23),(9,23),(9,17),(5,17),(5,8),(5,6)],1,'医舍后撤门与西侧通道',ch='p')
   self.path([(15,19),(26,19),(26,24),(29,24),(29,23)],2,'南街与东侧援军入口')
   self.path([(5,9),(11,9),(11,7),(15,7)],1,'城墙后侧通道',ch='p');self.path([(5,5),(5,9)],2,'护院门前医舍路',ch='p');self.path([(20,7),(20,4),(23,4)],1,'城内北巷',ch='p')
   self.wall_h(1,30,10,[5,6,14,15,16,17]);self.wall_h(1,8,8,[5,6]);self.wall_h(1,8,1);self.wall_v(8,1,8);self.wall_v(1,1,8)
   for p in[(1,1),(8,1),(1,8),(8,8)]:self.corner(*p)
   self.stamp('coastal_keep',23,2,'.','门内赫兰指挥堡');self.stamp('tower_entry',12,7,'.','主门西塔');self.stamp('tower_entry',18,7,'.','主门东塔');self.stamp('village_clinic',3,3,'.','后撤门内伤兵医舍');self.stamp('quay_warehouse',7,13,'.','城外军需库');self.stamp('fishing_cottage',11,19,'.','南街住屋');self.stamp('fishing_cottage',20,17,'.','东街住屋');self.stamp('command_pavilion',24,21,'.','城外值勤营')
   for pts in[[(4,5),(5,5),(5,7)],[(8,15),(9,15),(9,17)],[(12,21),(15,21)],[(21,19),(23,19)],[(25,23),(26,23)]]:self.path(pts,1)
   d['player_positions']=[[4,14],[5,14],[4,15],[5,15],[3,14],[6,14],[3,15],[6,15],[4,16],[5,16]]
   self.relocate('npc_units',{'church_wounded0':[2,3],'church_wounded1':[3,5]})
   self.relocate('enemies',{'M44_boss':[24,6],'M44_e1':[20,12],'M44_e2':[16,14],'M44_e3':[25,20],'M44_e4':[11,16],'M44_e5':[15,11],'M44_e6':[18,13],'M44_e7':[24,19],'M44_e8':[11,8],'M44_e9':[22,7],'M44_e10':[20,9],'M44_e11':[27,21],'M44_e12':[10,5],'M44_e13':[27,6]})
   self.relocate('reinforcements',{'M44_r0':[29,23],'M44_r1':[29,24]})
   d['objects'][0]['position']=[15,9];d['objects'][1]['position']=[5,10];d['exit']=[27,7]
   d['tactical_notes']=['横贯战场的王都城墙以双塔夹出四格正门，城内指挥堡与医舍街、城外住区与军需库形成清楚前后层次。','主街直攻门楼；西侧窄巷经过两格伤兵后撤门，直接接到墙内医舍，提供较慢但可绕过正门重装的侧通道。','两名伤兵退到完整医舍护院内，院墙只留两格南门；部署靠近后撤门，两人可守住护院入口，其余队员沿墙后通道或正面推进。第4回合东南来援、赫兰半血对白与解除武装分支保持。']
  else:
   self.poly([(0,0),(7,0),(8,3),(6,7),(2,9),(0,7)],'^');self.poly([(23,1),(25,1),(25,11),(22,10),(21,6)],'f');self.poly([(0,17),(3,16),(5,20),(4,23),(0,23)],'f');self.poly([(13,1),(15,0),(17,1),(15,4),(13,5)],'f');self.poly([(20,18),(25,17),(25,23),(20,23)],'^')
   self.path([(9,22),(9,15),(12,15),(12,8),(17,8),(17,5)],2,'山村主街至钟楼')
   self.path([(12,15),(18,15),(18,13)],1,'东侧名册屋南门支路');self.path([(17,8),(22,8),(22,13),(18,13)],1,'焚毁兵东坡进村路');self.path([(9,18),(6,18),(6,16),(5,16)],1,'医舍避难院接应路')
   self.path([(10,6),(12,6),(12,8)],1);self.path([(17,21),(17,22),(9,22)],1);self.path([(17,5),(22,5),(22,8)],1)
   self.stamp('quay_warehouse',17,11,'n','村道东侧名册屋，正门向南');self.stamp('village_clinic',4,14,'n','西南避难院医舍');self.stamp('snow_cottage',9,4,'n','钟楼下村舍');self.stamp('snow_cottage',16,19,'n','村口覆雪住屋');self.stamp('tower_entry',16,2,'n','黑钟村钟楼')
   d['player_positions']=[[9,19],[10,19],[9,20],[10,20],[8,19],[11,19],[8,20],[11,20],[9,21],[10,21]]
   self.relocate('npc_units',{'village_witness':[5,19],'otto_comrade':[6,20]})
   self.relocate('enemies',{'S41_boss':[22,5],'S41_e1':[15,8],'S41_e2':[14,11],'S41_e3':[18,17],'S41_e4':[10,10],'S41_e5':[18,9],'S41_e6':[22,12],'S41_e7':[20,17],'S41_e8':[11,7]})
   d['objects'][0].update(position=[18,12],approach=[18,13],sprite_offset=[0,8]);d['objects'][1]['position']=[6,17];d['burn_target']=[18,13];d['exit']=[18,5]
   d['tactical_notes']=['雪山村落沿钟楼主街展开，东侧名册屋门朝南，西南医舍与避难院在队伍后方；雪林和连片岩坡界定村缘。','主街尽快接近名册屋，东坡小路是焚毁兵实际来路，南侧住屋旁有回村支线；屋门操作格与焚毁目标完全重合。','焚毁兵第5回合出发、前一回合预告、连续两次点火才毁册不变；从东坡到南门有实际路程供拦截，名册损失仍不阻断主线。']
  d['targets']=[o['position']for o in d['objects']]
 def flood(self,start,opened=False):
  opens={tuple(p)for o in self.d['objects']for p in o.get('opens',[o['position']]if o['kind']in['door','rescue']else[])};q=deque([tuple(start)]);seen={tuple(start):0}
  while q:
   x,y=q.popleft()
   for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
    p=x+dx,y+dy
    if 0<p[0]<self.w-1 and 0<p[1]<self.h-1 and p not in seen and(self.g[p[1]][p[0]]not in'#^~'or opened and p in opens):seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def bake(self):
  self.design();c=self.c;d=self.d;w=self.w;h=self.h;g=self.g
  anchors={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for k in['enemies','npc_units','reinforcements']for u in d[k]]}
  for x,y in anchors:
   assert g[y][x]not in'#^~',(c,'blocked actor',x,y,g[y][x])
   if g[y][x]=='f':g[y][x]=self.base
  for o in d['objects']:
   for x,y in o.get('approaches',[o['approach']]if'approach'in o else[]):assert g[y][x]not in'#^~',(c,'blocked front',o['id'])
  occupied=[tuple(p)for p in d['player_positions']]+[tuple(u['position'])for u in d['enemies']+d['npc_units']];assert len(occupied)==len(set(occupied)),(c,'overlap')
  ground=[[self.under.get((x,y),self.base)if ch=='#'else self.base if ch in'^f'else ch for x,ch in enumerate(row)]for y,row in enumerate(g)]
  for y,row in enumerate(ground):
   for x,ch in enumerate(row):
    v=B.seed(f'{c}:composition:{x}:{y}')%4;mat=MAT[ch];tile=B.PACK['base'][mat][v]
    if ch in'pb=':tile=A.edge(mat,'snow'if self.base=='n'else'grass',B.mask_at(ground,x,y,lambda q:q in'pb='),v)
    elif ch=='s':
     m=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s');tile=A.trans['walkway']['h'+str(m)][v]
    self.layers[0][y][x]=tile
  nature=[];rng=random.Random(B.seed(c+'-landmass'))
  for ch,large,small in[('f',['pine_tall','pine_broad','pine_pair'],['pine_small_a','pine_small_b','pine_young']),('^',['peak_low','crag_tall','ridge_bent'],['boulder'])]:
   if self.base=='n' and ch=='f':large=['snow_tall','snow_broad','snow_pair'];small=['snow_small_a','snow_small_b','snow_young']
   if self.base=='n' and ch=='^':small=['snow_boulder']
   allowed={(x,y)for y,row in enumerate(g)for x,t in enumerate(row)if t==ch};used=set();places=sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0]))
   for x,y in places:
    if(x,y)in used:continue
    choices=large.copy();rng.shuffle(choices)
    for key in choices:
     sw,sh=B.NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
     if cells<=allowed and not cells&(used|anchors):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});used|=cells;break
   for x,y in sorted(allowed-used):nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.35})
   if ch=='f':
    for x,y in sorted(allowed):
     if(x+y)%2 or rng.random()<.2:continue
     key=rng.choice(large[:2]);sw,sh=B.NATURE[key]['size'];px=x*16+rng.randint(-2,2);py=y*16+rng.randint(-2,2);cells={(xx,yy)for yy in range(py//16,math.ceil((py+sh)/16))for xx in range(px//16,math.ceil((px+sw)/16))}
     if cells<=allowed and not cells&anchors:nature.append({'key':key,'position':[px,py],'flip':rng.random()<.35})
  nature.sort(key=lambda p:p['position'][1]+B.NATURE[p['key']]['size'][1])
  d.update(map={'width':w,'height':h,'tiles':[IDS[ch]for row in g for ch in row]},logic_grid=[''.join(row)for row in g],visual_ground=[''.join(row)for row in ground],art_layers=self.layers,art_modules=self.modules,art_props=self.props,natural_props=nature,art_atlas='res://assets/chapter4-redesign-20261022/west/terrain.png',art_columns=32,tactical_routes=self.routes,tactical_review_version='0.10.8-ch4',art_style_version='chapter4-redesign-20261022',landscape_revision='M41 approved composition method; chapter4 west',nature_layout={'biome':'snow'if self.base=='n'else'forest','props':[],'excluded':[[0,0,w*16,h*16]]})
  d['visual_notes']=d['tactical_notes'].copy();seen=self.flood(d['player_positions'][0]);opened=self.flood(d['player_positions'][0],True)
  standard={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for k in['enemies','reinforcements']for u in d[k]]};assert standard<=set(seen),(c,'unreachable actors',standard-set(seen));assert anchors<=set(opened),(c,'unreachable NPC',anchors-set(opened))
  distances={}
  for o in d['objects']:
   x,y=o['position'];fronts=o.get('approaches',[o['approach']]if'approach'in o else[[x,y]]+([[x+dx,y+dy]for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]]if o.get('adjacent')else[]));valid=[seen[tuple(p)]for p in fronts if tuple(p)in seen];assert valid,(c,'object unreachable',o['id']);distances[o['id']]=min(valid)
  for group in['enemies','npc_units','reinforcements']:
   assert len(d[group])==len(self.old[group]);assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(self.old[group],d[group])),(c,group)
  for k in['characters','terrain','goal','before','during','after','optional','clear_training_exp','reinforcement_turn','event_boats']:assert d.get(k)==self.old.get(k),(c,k)
  movable={'position','approach','approaches','opens','open_art_cells','sprite_offset'}
  for a,b in zip(self.old['objects'],d['objects']):assert{k:v for k,v in a.items()if k not in movable}=={k:v for k,v in b.items()if k not in movable},(c,a['id'])
  report={'passed':True,'code':c,'size':[w,h],'closed_connected':len(seen),'opened_connected':len(opened),'notes':d['tactical_notes'],'units_only_positions_changed':True,'story_timing_rules_preserved':True,'coordinate_changes':{group:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(self.old[group],d[group])]for group in['enemies','npc_units','reinforcements','objects']},'deployment_before':self.old['player_positions'],'deployment_after':d['player_positions'],'exit':d['exit'],'targets':d['targets'],'interaction_front_distances':distances}
  assert all(0<x<w-1 and 0<y<h-1 for x,y in anchors),(c,'outer-border anchor')
  if c=='M42':
   u=next(u for u in d['npc_units']if u['id']=='old_comrade');x,y=u['position'];report['parley_fronts']=[p for p in [[x+1,y],[x-1,y],[x,y+1],[x,y-1]]if tuple(p)in seen];assert report['parley_fronts']
  if c=='S41':
   assert d['burn_target']==d['objects'][0]['approach'];burner=next(u for u in d['enemies']if u.get('ch4_burner'));steps=self.flood(burner['position'])[tuple(d['burn_target'])];report['burner_steps_to_south_door']=steps;report['earliest_unopposed_first_fire_turn']=int(d['burn_start'])+math.ceil(steps/int(burner['move']))-1;report['two_consecutive_fires_required']=True
  report.update(routes=d['tactical_routes'],structures=[{'name':m['name'],'origin':m['origin'],'footprint':m['footprint']}for m in d['art_modules']],interactions=[{k:v for k,v in z.items()if k in ['id','position','approach','approaches','sprite_offset']}for z in d['objects']])
  write(R/f'data/stages/{c}.json',d);report['map_sha256']=hashlib.sha256((R/f'data/stages/{c}.json').read_bytes()).hexdigest();write(O/f'{c}-design.json',report);return report
if __name__=='__main__':
 reports=[Field('M42',32,28).bake(),Field('M43',30,28).bake(),Field('M44',32,28).bake(),Field('S41',26,24).bake()];A.save();write(O/'geometry.json',{'passed':True,'maps':reports});print(json.dumps([{'code':r['code'],'size':r['size'],'passed':True}for r in reports]))
