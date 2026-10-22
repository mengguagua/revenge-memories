#!/usr/bin/env python3
"""Chapter-three western route: street rescue, convoy interception, coastal fort."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter3-redesign-20261022/west';BASE=O.parent/'baseline';ART=R/'assets/chapter3-redesign-20261022/west'
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
  self.c=c;self.old=json.loads((BASE/f'{c}.json').read_text());self.d=copy.deepcopy(self.old);self.w=w;self.h=h;self.g=[list('.'*w)for _ in range(h)];self.under={};self.routes=[];self.modules=[];self.props=[];self.layers=[[[None]*w for _ in range(h)]for _ in range(3)];self.solid=set()
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
 def design(self):
  d=self.d;c=self.c
  if c=='M31':
   # Two streets and compact building courts, with a real western wall opening.
   self.rect(2,1,27,22,'.')
   for box in[(4,1,8,5),(9,1,14,5),(16,1,21,5),(22,1,27,5),(4,9,8,13),(9,9,17,13),(19,9,25,15),(3,18,8,22),(18,19,25,22)]:self.rect(*box,'b')
   self.path([(0,7),(26,7),(26,17)],2,'西门横街与东院外街')
   self.path([(5,17),(26,17),(28,17),(28,23)],2,'南侧撤离街与追兵入口')
   self.path([(9,7),(9,17)],2,'医舍旁主巷');self.path([(15,23),(15,17)],2,'南街入场口')
   self.path([(13,8),(13,17)],1,'仓房之间的窄侧街')
   self.path([(22,14),(22,17)],2,'拘押院南门接应短街')
   for pts in[[(6,12),(6,17)],[(7,4),(7,7)],[(12,4),(12,7)],[(18,4),(18,7)],[(24,4),(24,7)],[(5,20),(5,17)],[(20,22),(20,17)],[(25,21),(26,21),(26,17)]]:self.path(pts,1,'住屋门前巷')
   wall=next(m for m in B.PACK['modules']if m['name']=='west_wall')['tiles'][1][0]
   for y in range(0,24,4):self.tiled('west_wall',1,y,[[None if y+i in[6,7,8]else wall]for i in range(4)])
   self.stamp('fishing_cottage',6,2,'b','北街西侧民宅');self.stamp('fishing_cottage',11,2,'b','北街东侧民宅');self.stamp('quay_warehouse',17,2,'b','北街仓房');self.stamp('fishing_cottage',23,2,'b','北街里巷住屋')
   self.stamp('village_clinic',5,10,'b','街边医舍，南门接主巷');self.stamp('quay_warehouse',10,10,'b','窄侧街西仓');self.stamp('quay_warehouse',14,10,'b','窄侧街东仓')
   self.path([(11,12),(9,12)],1);self.path([(15,12),(13,12)],1)
   self.stamp('fishing_cottage',4,18,'b','南街住屋');self.stamp('fishing_cottage',19,20,'b','东南住屋');self.stamp('fishing_cottage',24,19,'b','追兵巷口住屋')
   self.stamp('well',18,17,'b','南街公共井');self.stamp('crates',17,12,'b','东仓侧面装卸物资')
   door=self.jail(20,10);self.g[11][13]='#';self.under[13,11]='p'
   for pts in[[(2,10),(3,10),(3,15),(2,15)],[(16,13),(18,13),(18,15),(16,15)],[(27,9),(29,10),(29,14),(27,14)],[(10,21),(12,21),(13,23),(10,23)]]:self.poly(pts,'f')
   d['player_positions']=[[13,19],[14,19],[15,19],[16,19],[13,20],[14,20],[12,19],[15,20],[16,20],[12,20]]
   self.relocate('npc_units',{'detained0':[21,11],'detained1':[23,11],'street_resident':[11,21]})
   self.relocate('enemies',{'M31_boss':[4,7],'M31_e1':[9,14],'M31_e2':[25,9],'M31_e3':[24,18],'M31_e4':[10,7],'M31_e5':[6,15],'M31_e6':[25,11],'M31_e7':[23,19],'M31_e8':[8,6],'M31_e9':[12,8],'M31_e10':[25,14]})
   self.relocate('reinforcements',{'M31_r0':[28,20],'M31_r1':[28,21]})
   d['exit']=[2,7];d['objects'][0].update(position=door,opens=[door],open_art_cells=[{'position':door,'base_tile':B.PACK['base']['cobble'][0]}])
   d['objects'][1].update(position=[13,11],opens=[[13,11]],open_art_cells=[{'position':[13,11],'base_tile':B.PACK['base']['dirt'][0]}]);d['objects'][2].update(position=[6,11],approach=[6,12])
   d['targets']=[o['position']for o in d['objects']]
   d['tactical_notes']=['西门横街、医舍主巷与南街围出完整住区，民宅、仓房和医舍朝街开门；西城墙在左上方留下真实门道，撤离旗在门内横街（2,7），队长守在门前。','拘押院位于东街，有实体四边围栏和唯一南门；开门后居民经南街转入医舍主巷，再走横街出西门。仓房之间的一格侧街可移开路障后抄近路。','部队在南街集合，未被拘押居民位于队伍后方；第4敌回合追兵仍从东南巷口进入。两名拘押居民必须存活撤离，原开门与胜负条件保持。']
   d['location_theme']='海峡城西街街区、东侧拘押院与真实西门'
  elif c=='M32':
   self.poly([(0,0),(6,0),(8,3),(7,6),(4,8),(1,7)],'f');self.poly([(0,10),(2,9),(3,13),(2,18),(0,20)],'^')
   self.poly([(14,0),(17,0),(18,3),(16,4),(14,3)],'^');self.poly([(25,20),(28,18),(29,19),(29,23),(26,23)],'^')
   self.poly([(14,17),(16,15),(18,17),(18,20),(16,22),(13,21)],'f');self.poly([(25,8),(29,7),(29,15),(27,16),(24,13)],'f')
   self.poly([(3,13),(6,12),(8,14),(8,16),(6,17),(3,16)],'f');self.poly([(8,1),(11,0),(12,3),(11,5),(8,5)],'f')
   self.path([(20,0),(20,23)],2,'两格军需大道与北撤车道')
   self.path([(7,23),(7,20),(13,20),(13,14),(20,14)],2,'西南入口—西运输站')
   self.path([(7,20),(6,20),(6,18),(5,18),(5,11),(7,11),(7,8),(13,8),(13,5),(18,5),(20,5)],1,'西侧林坡截运支路')
   self.rect(11,12,15,15,'b');self.rect(19,6,23,8,'b');self.rect(19,14,23,16,'p')
   self.stamp('hill_granary',10,10,'.','西站粮料仓，南门接站场');self.path([(11,12),(13,12),(13,14)],1)
   self.stamp('quay_warehouse',23,4,'.','北站仓库');self.path([(24,6),(20,6)],1)
   self.stamp('command_pavilion',17,1,'.','北口值守哨');self.path([(18,3),(20,3)],1)
   self.stamp('fishing_cottage',3,19,'.','运输工歇脚屋');self.path([(4,21),(7,21)],1)
   self.stamp('crates',10,13,'b');self.stamp('grain_sacks',10,14,'b');self.stamp('camp_palisade',24,17,'.','东侧车场边缘')
   d['player_positions']=[[7,19],[8,19],[7,20],[8,20],[6,19],[9,19],[6,20],[9,20],[7,21],[8,21]]
   self.relocate('npc_units',{'transport_cart':[20,15],'road_worker':[5,21]})
   self.relocate('enemies',{'M32_boss':[22,3],'M32_e1':[22,7],'M32_e2':[15,9],'M32_e3':[25,16],'M32_e4':[13,5],'M32_e5':[19,6],'M32_e6':[14,12],'M32_e7':[24,18],'M32_e8':[11,12],'M32_e9':[23,7],'M32_e10':[16,11]})
   d['objects'][0]['position']=[13,14];d['objects'][1]['position']=[20,7];d['objects'][2]['position']=[20,15];d['targets']=[o['position']for o in d['objects']];d['exit']=[20,2]
   d['transport_path']=[[20,y]for y in range(15,1,-1)]
   d['tactical_notes']=['两格军需大道贯通南北，运输车完整车体沿路向北口行进；西站粮仓、北站仓库与车场各自围出小型装卸坪。','西南入口先接西运输站，主路可继续截车并夺北站；一格西坡林缘路绕到北站侧面，骑兵有东侧车场与大道可调动。','运输车从南站附近起步，距北口13步；第6己方回合开始每轮一格、控制任一站或打开车锁即停车的规则保持，两站与车锁仍须分别确认。']
   d['location_theme']='贯通南北的军需大道、双运输站与林坡截运支路'
  else:
   self.rect(0,0,31,27,'~');self.poly([(2,0),(27,0),(28,3),(28,7),(25,10),(25,20),(23,23),(20,26),(6,27),(2,24),(0,19),(1,11)],'.')
   self.poly([(1,0),(6,0),(6,3),(4,5),(2,9),(0,10)],'^');self.poly([(2,11),(4,10),(6,12),(5,15),(2,16),(0,15)],'^')
   self.poly([(4,6),(7,5),(9,7),(8,11),(6,13),(4,10)],'f');self.poly([(1,21),(5,20),(7,23),(5,27),(2,25)],'f')
   self.poly([(17,23),(20,23),(22,25),(20,27),(16,27)],'f');self.poly([(15,1),(19,1),(20,3),(18,5),(15,4)],'f')
   self.rect(13,6,25,11,'b');self.rect(16,18,23,22,'b')
   self.path([(8,27),(8,23),(12,23),(12,18),(15,18),(15,8),(24,8),(24,7)],2,'堡前主道—城门—内庭')
   self.path([(8,23),(4,23),(4,18),(7,18),(7,15),(7,9),(12,9),(12,6),(18,6),(21,6)],1,'西崖林缘侧攻路')
   self.path([(15,18),(19,18),(19,21),(23,21),(23,16),(26,16)],2,'工房前庭—投送码头')
   self.path([(24,8),(26,8),(26,1),(25,1)],1,'堡后北侧联络路')
   self.path([(23,11),(23,16)],2,'东南靠港侧门至工房接应路')
   self.rect(25,15,29,17,'s')
   self.stamp('coastal_keep',22,2,'b','北侧石堡主楼，门前是守将内庭')
   # Full native masonry perimeter, with real gaps for the main and harbour gates.
   hwall=459;vwall=463
   key='complete-stone-corner'
   if key not in A.add:
    corner=A.cells[hwall].copy();corner.alpha_composite(A.cells[vwall]);A.add[key]=[len(A.cells)];A.cells.append(corner)
   corner_id=A.add[key][0]
   self.tiled('fort_north_wall',11,1,[[None if x==25 else corner_id if x in[11,27]else hwall for x in range(11,28)]])
   self.tiled('fort_west_wall',11,2,[[None if y in[8,9]else vwall]for y in range(2,12)])
   self.tiled('fort_east_wall',27,2,[[vwall]for y in range(2,9)])
   self.tiled('fort_south_wall',10,12,[[None if x in[14,15,16,23,24]else corner_id if x==11 else hwall for x in range(10,26)]])
   self.stamp('quay_warehouse',18,18,'b','投送工房，记录从南门取');self.stamp('village_clinic',5,17,'.','外院医舍');self.path([(6,19),(6,20),(12,20)],1,'医舍门前外院路')
   # Existing plain cells form the genuine side route around the complete clinic.
   # Paint its east edge, rather than visually asking soldiers to cross the roof.
   self.path([(8,23),(8,15),(7,15)],1,'医舍东侧与林缘通路')
   self.path([(4,19),(6,19)],1,'医舍南门前接应小院')
   for route in self.routes:
    if route['name']=='西崖林缘侧攻路':route['waypoints']=[[8,23],[8,15],[7,15],[7,9],[12,9],[12,6],[18,6],[21,6]]
   self.stamp('command_pavilion',10,21,'.','南院守军值勤处');self.stamp('sea_cliff',26,9,'~','投送栈桥北侧海崖')
   self.stamp('crates',24,16,'b','码头卸货物资');self.stamp('grain_sacks',24,17,'b','码头侧面装卸袋')
   d['player_positions']=[[8,23],[9,23],[8,24],[9,24],[7,23],[10,23],[7,24],[10,24],[8,25],[9,25]]
   self.relocate('npc_units',{'fort_workers':[17,21]})
   self.relocate('enemies',{'M33_boss':[24,7],'M33_e1':[21,8],'M33_e2':[16,11],'M33_e3':[23,20],'M33_e4':[9,9],'M33_e5':[22,10],'M33_e6':[16,14],'M33_e7':[24,18],'M33_e8':[12,7],'M33_e9':[24,9],'M33_e10':[18,10],'M33_e11':[22,21],'german':[20,21]})
   d['objects'][0]['position']=[26,16];d['objects'][1].update(position=[19,19],approach=[19,20]);d['targets']=[o['position']for o in d['objects']];d['exit']=[26,2]
   d['tactical_notes']=['海崖石堡由连续北墙、西墙、东墙及海蚀崖围住旧石内庭，完整主楼位于北端；南侧外院与东侧工房码头分区清楚。','两格主道穿过南墙三格正门，西崖林缘路经西侧门进入内庭；东南两格港门直通工房接应路和真正伸入海面的投送栈桥，东北侧联络出口设在可达的墙内通路（26,2）。','格曼站在工房前庭，工匠偏在院侧，不堵住记录室唯一南门；投送码头、记录和堡主败北后的投降／解除武装／死亡分支均沿用。']
   d['location_theme']='沿海石堡内外院、投送工房与真实海岸栈桥'
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
   if g[y][x]=='f':g[y][x]='.'
  for o in d['objects']:
   for x,y in o.get('approaches',[o['approach']]if'approach'in o else[]):assert g[y][x]not in'#^~',(c,'blocked front',o['id'])
  occupied=[tuple(p)for p in d['player_positions']]+[tuple(u['position'])for u in d['enemies']+d['npc_units']];assert len(occupied)==len(set(occupied)),(c,'overlap')
  ground=[[self.under.get((x,y),'.')if ch=='#'else'.'if ch in'^f'else ch for x,ch in enumerate(row)]for y,row in enumerate(g)]
  # Ground art follows actual building fronts, without changing movement categories.
  if c=='M31':
   for y in range(h):
    for x in range(w):
     if ground[y][x]=='b':ground[y][x]='.'
   # Compact front courts; houses no longer sit on large square stone carpets.
   for x0,y0,x1,y1 in [(6,3,8,4),(11,3,13,4),(17,3,20,4),(23,3,25,4),(5,11,8,12),(10,11,12,12),(14,11,17,12),(4,19,6,20),(19,21,21,22),(24,20,26,21)]:
    for yy in range(y0,y1+1):
     for xx in range(x0,x1+1):
      if ground[yy][xx]=='.':ground[yy][xx]='b'
   for yy in range(10,14):
    for xx in range(20,25):ground[yy][xx]='b'
  elif c=='M33':
   # A unified weathered-stone inner court reads as a fort, not white path strips.
   for yy in range(2,12):
    for xx in range(12,27):
     if ground[yy][xx]in'.pb':ground[yy][xx]='='
   for yy in range(2,6):
    for xx in range(22,26):ground[yy][xx]='='
   for xx in[14,15,16,23,24]:ground[12][xx]='='
   for yy in range(18,23):
    for xx in range(16,24):
     if ground[yy][xx]=='b':ground[yy][xx]='.'
   for yy in range(19,22):
    for xx in range(18,22):
     if ground[yy][xx]in'.b':ground[yy][xx]='p'
  for y,row in enumerate(ground):
   for x,ch in enumerate(row):
    v=B.seed(f'{c}:composition:{x}:{y}')%4;mat=MAT[ch];tile=B.PACK['base'][mat][v]
    if ch in'pb=':tile=A.edge(mat,'grass',B.mask_at(ground,x,y,lambda q:q==ch),v)
    elif ch=='s':
     m=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s');tile=A.trans['walkway']['h'+str(m)][v]
    self.layers[0][y][x]=tile
  nature=[];rng=random.Random(B.seed(c+'-landmass'))
  for ch,large,small in[('f',['pine_tall','pine_broad','pine_pair'],['pine_small_a','pine_small_b','pine_young']),('^',['peak_low','crag_tall','ridge_bent'],['boulder'])]:
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
  d.update(map={'width':w,'height':h,'tiles':[IDS[ch]for row in g for ch in row]},logic_grid=[''.join(row)for row in g],visual_ground=[''.join(row)for row in ground],art_layers=self.layers,art_modules=self.modules,art_props=self.props,natural_props=nature,art_atlas='res://assets/chapter3-redesign-20261022/west/terrain.png',art_columns=32,tactical_routes=self.routes,tactical_review_version='0.10.7-ch3',art_style_version='chapter3-redesign-20261022',landscape_revision='M41 approved composition method; chapter3 west',nature_layout={'biome':'forest','props':[],'excluded':[[0,0,w*16,h*16]]})
  d['visual_notes']=d['tactical_notes'].copy();seen=self.flood(d['player_positions'][0]);opened=self.flood(d['player_positions'][0],True)
  standard={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for k in['enemies','reinforcements']for u in d[k]]};assert standard<=set(seen),(c,'unreachable actors',standard-set(seen));assert anchors<=set(opened),(c,'unreachable NPC',anchors-set(opened))
  distances={}
  for o in d['objects']:
   x,y=o['position'];fronts=o.get('approaches',[o['approach']]if'approach'in o else[[x,y]]+([[x+dx,y+dy]for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]]if o.get('adjacent')else[]));valid=[seen[tuple(p)]for p in fronts if tuple(p)in seen];assert valid,(c,'object unreachable',o['id']);distances[o['id']]=min(valid)
  for group in['enemies','npc_units','reinforcements']:
   assert len(d[group])==len(self.old[group]);assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(self.old[group],d[group])),(c,group)
  for k in['characters','terrain','goal','before','during','after','optional','clear_training_exp','reinforcement_turn','event_boats']:assert d.get(k)==self.old.get(k),(c,k)
  movable={'position','approach','approaches','opens','open_art_cells'}
  for a,b in zip(self.old['objects'],d['objects']):assert{k:v for k,v in a.items()if k not in movable}=={k:v for k,v in b.items()if k not in movable},(c,a['id'])
  report={'passed':True,'code':c,'size':[w,h],'closed_connected':len(seen),'opened_connected':len(opened),'notes':d['tactical_notes'],'units_only_positions_changed':True,'story_timing_rules_preserved':True,'coordinate_changes':{group:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(self.old[group],d[group])]for group in['enemies','npc_units','reinforcements','objects']},'deployment_before':self.old['player_positions'],'deployment_after':d['player_positions'],'exit':d['exit'],'targets':d['targets'],'interaction_front_distances':distances}
  if c=='M31':
   assert 0<d['exit'][0]<w-1 and 0<d['exit'][1]<h-1
   assert(21,11)not in seen and(23,11)not in seen;assert d['objects'][0]['opens']==[d['objects'][0]['position']];report['residents_require_single_gate']=True;report['resident_to_west_gate_steps']={u['id']:self.flood(u['position'],True)[tuple(d['exit'])]for u in d['npc_units']}
  if c=='M32':
   path=d['transport_path'];assert path[0]==d['npc_units'][0]['position']==d['objects'][2]['position'];assert path[-1]==d['exit'];assert all(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(path,path[1:]));assert all(g[y][x]in'pb'and g[y][x+1]in'pb'for x,y in path)
   report.update(transport_steps=len(path)-1,earliest_unopposed_escape_turn=5+len(path)-1,full_cart_footprint_clear=True)
  if c=='M33':
   german=next(u for u in d['enemies']if u['id']=='german');x,y=german['position'];report['german_accessible_sides']=[p for p in[[x+dx,y+dy]for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]]if tuple(p)in seen];assert len(report['german_accessible_sides'])>=3
  write(R/f'data/stages/{c}.json',d);report['map_sha256']=hashlib.sha256((R/f'data/stages/{c}.json').read_bytes()).hexdigest();write(O/f'{c}-design.json',report);return report
if __name__=='__main__':
 reports=[Field('M31',30,24).bake(),Field('M32',30,24).bake(),Field('M33',32,28).bake()];A.save();write(O/'geometry.json',{'passed':True,'maps':reports});print(json.dumps([{'code':r['code'],'size':r['size'],'passed':True}for r in reports]))
