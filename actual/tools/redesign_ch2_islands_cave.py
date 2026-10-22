#!/usr/bin/env python3
"""Chapter-two islands and tidal cave: whole compositions, unchanged game rules."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter2-redesign-20261022/islands-cave';BASE=O.parent/'baseline';ART=R/'assets/chapter2-redesign-20261022/islands-cave'
spec=importlib.util.spec_from_file_location('terrain_helpers',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
L.ART=ART;A=L.Atlas();B=L.B;IDS=B.IDS;MAT=B.MATERIAL
write=lambda p,d:(p.parent.mkdir(parents=True,exist_ok=True),p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'))
def cave_wall(neighbors,v):
 key='tidal-rock:'+''.join('1'if n else'0'for n in neighbors)
 if key not in A.add:
  ids=[]
  for n in range(4):
   im=A.cells[A.trans['mountain_ground']['cave']['255'][n]].copy()
   for y in range(16):
    for x in range(16):
     r,g,b,a=im.getpixel((x,y));shade=.82
     if neighbors[2]and y>=10:shade=.64 if y==10 else .56+(y-10)*.018
     if neighbors[0]and y<2:shade=.60
     if neighbors[1]and x>=13:shade=min(shade,.64)
     if neighbors[3]and x<3:shade=min(shade,.68)
     im.putpixel((x,y),(int(r*shade),int(g*shade),int(b*shade),a))
   ids.append(len(A.cells));A.cells.append(im)
  A.add[key]=ids
 return A.add[key][v]
class Field:
 def __init__(self,c,w,h):
  self.c=c;self.old=json.loads((BASE/f'{c}.json').read_text());self.d=copy.deepcopy(self.old);self.w=w;self.h=h;self.g=[list(('^'if c=='S22'else'~')*w)for _ in range(h)];self.under={};self.routes=[];self.modules=[];self.props=[];self.sites=[];self.bridges={};self.solid=set()
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
 def stamp(self,name,x,y,ground='.',purpose='',occupiable=False,open_arch=False):
  m=B.MODULES[name];fw,fh=m['footprint'];cells=[];walk=[]
  assert 0<=x and 0<=y and x+fw<=self.w and y+fh<=self.h
  for yy in range(y,y+fh):
   for xx in range(x,x+fw):
    if open_arch and xx in[x+1,x+2]:walk.append([xx,yy]);continue
    assert(xx,yy)not in self.solid,(self.c,name,xx,yy)
    self.under[xx,yy]=ground;self.g[yy][xx]='h'if occupiable else'#';cells.append([xx,yy]);self.solid.add((xx,yy))
  self.modules.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'walk_through_cells':walk,'logic':'occupiable'if occupiable else'#','runtime_prop':True,'purpose':purpose})
  self.props.append({'path':m['path'],'position':[x*16,y*16]})
 def relocate(self,group,positions):
  for u in self.d[group]:u['position']=positions[u['id']]
 def design(self):
  d=self.d;c=self.c
  if c=='F23':
   # The beach and small fishing bay form a sheltered rear, with a widening upland to the north-east.
   coast=[(15,1),(24,1),(28,3),(29,7),(28,11),(30,15),(29,20),(26,23),(20,24),(16,25),(6,25),(3,23),(3,19),(5,17),(5,12),(7,7),(11,4)]
   self.poly(coast,'d');self.poly([(15,2),(23,2),(27,4),(27,10),(28,15),(27,20),(24,22),(18,22),(14,23),(9,22),(7,19),(7,13),(9,8),(12,5)],'.')
   self.poly([(20,2),(25,2),(27,4),(28,7),(26,8),(24,6),(21,6)],'^')
   self.poly([(6,8),(8,6),(11,5),(12,8),(11,10),(8,12),(6,12)],'^')
   self.poly([(9,10),(13,9),(15,11),(15,14),(12,15),(9,14)],'f')
   self.poly([(17,4),(20,4),(21,7),(20,9),(17,9),(15,7)],'f')
   self.poly([(23,17),(26,16),(28,18),(27,21),(24,22),(21,21)],'f')
   self.poly([(15,22),(18,21),(20,23),(19,25),(15,25)],'f')
   self.path([(6,24),(9,24),(9,21),(12,21),(12,17),(16,17),(16,11),(23,11),(24,11),(24,7),(26,7),(26,4),(27,3)],2,'登陆湾—渔村—东北草坡')
   self.path([(9,21),(7,21),(7,16),(8,16),(8,13),(12,13),(12,8),(14,8),(14,5),(19,5)],1,'西侧岩坡绕林线')
   self.path([(16,17),(21,17),(21,14),(24,14),(24,11)],1,'东坡清场支路')
   self.rect(7,20,11,23,'p');self.rect(11,17,14,20,'p');self.rect(22,10,25,12,'p')
   self.stamp('fishing_cottage',6,18,'.','渔家小屋，南门面向营地')
   self.stamp('fishing_cottage',10,22,'.','南村住屋');self.path([(11,24),(9,24)],1)
   self.stamp('crates',8,20,'p','营地货箱');self.stamp('grain_sacks',10,20,'p','营地储粮')
   self.stamp('sea_cliff',3,9,'~','西岸完整海蚀崖')
   # This complete lookout stands on the already solid sea-cliff footprint.
   lookout=B.MODULES['ruined_watchtower'];self.props.append({'path':lookout['path'],'position':[4*16,9*16]})
   self.modules.append({'name':'ruined_watchtower','origin':[4,9],'footprint':[2,3],'cells':[[x,y]for y in range(9,12)for x in range(4,6)],'logic':'#','runtime_prop':True,'overlays_existing_module':'sea_cliff','purpose':'西岸旧瞭望台俯瞰登陆湾，复用原不可通行海崖占地'})
   d['player_positions']=[[12,18],[13,18],[12,19],[13,19],[11,18],[11,19],[14,18],[12,20],[13,20],[11,20]]
   self.relocate('npc_units',{'roan':[6,21],'fishers':[8,22]})
   self.relocate('enemies',{'F23_boss':[26,5],'F23_e1':[24,10],'F23_e2':[20,14],'F23_e3':[23,18],'F23_e4':[13,10],'F23_e5':[25,11],'F23_e6':[22,10],'F23_e7':[24,15],'F23_e8':[13,7],'F23_e9':[25,8],'F23_e10':[20,11]})
   d['exit']=[27,3];d['targets']=[[9,21],[5,23]]
   d['objects'][0]['position']=[9,21];d['objects'][1]['position']=[5,23]
   d['objects'][2].update(position=[7,19],approach=[7,20],approaches=[[7,20]],entrance_cells=[[7,19]])
   d['tactical_notes']=['西南沙湾承接登陆，渔家小屋围出营地；部队部署在营地前方，罗恩与渔民留在可防守的后方小院。','西岸旧瞭望台立在完整海蚀崖上，标出湾口；两格村路从沙滩转入东北草坡，西侧一格岩坡支路绕过成片树林，东坡另留短路清场。','飞行魔物集中在北部与东坡，初始距离给护卫留出拦截空间；飞行首领仍固守高地，胜利仍要求清除全部敌军并保住渔民营地。']
   d['location_theme']='礁岛登陆湾、后方渔村和东北林崖高地'
  elif c=='F24':
   self.poly([(12,1),(21,1),(26,2),(29,5),(30,10),(28,13),(30,17),(29,22),(25,25),(18,27),(10,26),(6,23),(4,19),(5,15),(3,12),(5,8),(8,5)],'d')
   self.poly([(12,2),(21,2),(25,3),(28,6),(28,10),(26,13),(28,17),(27,21),(24,23),(18,25),(11,24),(8,22),(6,19),(7,15),(5,12),(7,9),(9,6)],'.')
   self.poly([(6,5),(10,3),(11,5),(9,8),(7,9),(5,8)],'^');self.poly([(24,2),(27,3),(29,6),(28,8),(26,7),(24,5)],'^')
   self.poly([(7,11),(10,10),(12,12),(11,15),(8,16),(6,15)],'f')
   self.poly([(19,2),(21,3),(22,6),(20,8),(18,7),(17,4)],'f')
   self.poly([(23,17),(26,17),(28,19),(26,22),(24,22),(22,20)],'f')
   self.poly([(9,23),(12,22),(14,24),(13,26),(10,26)],'f')
   self.path([(16,26),(16,19),(16,15),(16,12)],2,'南村—航灯庭守卫主路')
   self.rect(13,11,18,14,'c')
   self.path([(12,2),(12,8),(12,9),(14,9),(14,11)],1,'北岸登岛路')
   self.path([(29,19),(25,19),(25,15),(22,15),(22,13),(18,13)],2,'东岸登陆—灯庭侧路')
   self.path([(28,10),(25,10),(25,6),(25,5),(23,5),(23,9),(22,9),(22,13)],1,'东北搜捕队通道')
   self.path([(16,19),(12,19),(12,16),(14,16)],1,'岛民庇护村街')
   self.path([(16,19),(19,19),(19,23),(18,23)],1,'避难所与南村后路')
   self.rect(12,18,19,20,'p');self.rect(24,18,28,20,'p')
   self.stamp('visit_lighthouse',15,7,'.','守灯人塔屋，南门正对灯庭')
   self.path([(16,10),(16,11)],1,'守灯屋正门')
   # The tower's southern steps lead directly onto the defended lamp terrace.
   stairs=B.MODULES['stairs_up'];self.props.append({'path':stairs['path'],'position':[15*16,10*16]})
   self.modules.append({'name':'stairs_up','origin':[15,10],'footprint':[2,2],'cells':[[x,y]for y in range(10,12)for x in range(15,17)],'logic':'inherits_ground','runtime_prop':True,'purpose':'塔屋南门石阶连接塔前航灯石台；完整步行台阶，无新增阻挡'})
   self.stamp('fishing_cottage',11,20,'.','岛民南侧住屋');self.path([(12,22),(16,22)],1)
   self.stamp('fishing_cottage',18,22,'.','南岸住屋');self.path([(19,24),(16,24)],1)
   self.stamp('camp_palisade',10,10,'.','北路外侧旧矮栅');self.stamp('camp_palisade',19,11,'.','东路外侧旧矮栅')
   self.stamp('tactical_house',11,16,'.','西村舍防守格',True);self.stamp('tactical_house',21,20,'.','东渔舍防守格',True)
   for site,p in zip(self.old['building_sites'],[[21,20],[11,16]]):self.sites.append(dict(site,position=p))
   self.stamp('crates',20,19,'p','避难所后勤物资')
   d['player_positions']=[[14,15],[15,15],[16,15],[17,15],[14,16],[15,16],[16,16],[17,16],[13,16],[18,16]]
   self.relocate('npc_units',{'shia':[12,18],'islanders':[15,19]})
   self.relocate('enemies',{'F24_boss':[25,5],'F24_e1':[23,4],'F24_e2':[26,9],'F24_e3':[28,9],'F24_e4':[12,3],'F24_e5':[15,3],'F24_e6':[23,12],'F24_e7':[25,15],'F24_e8':[10,8],'F24_e9':[27,10],'F24_e10':[22,8]})
   self.relocate('reinforcements',{'F24_r0':[29,19],'F24_r1':[28,19]})
   d['exit']=[16,26];d['targets']=[[16,12],[19,19]]
   d['objects'][0]['position']=[16,12];d['objects'][1].update(position=[19,19],approaches=[[19,19],[19,20]],entrance_cells=[[19,19]])
   d['objects'][2].update(position=[16,9],approach=[16,10],approaches=[[16,10],[15,10]],entrance_cells=[[16,9],[15,9]])
   d['tactical_notes']=['航灯石台位于岛中央，北面守灯塔屋经南门石阶直接连接塔前灯座；部队部署在灯台南侧，希雅和岛民位于后方庇护村街。','北岸一格登岛路与东岸两格登陆道汇入灯庭，两路来袭方向从道路和岸形可预判；东南岸接第3敌回合增援。','南村后路可调换两翼守军，完整屋舍和短矮栅收住庭边；第6己方回合、首领败北和灯位安全的条件不变，敌军连续占灯一整回合仍会失败。']
   d['location_theme']='中央航灯石庭、两路登岛口与南侧庇护村'
  else:
   # Carve connected halls from an unbroken rock massif; water only occupies the two tidal basins.
   self.poly([(2,17),(4,15),(9,15),(12,17),(12,22),(9,23),(3,22),(2,20)],'.')
   self.poly([(10,10),(13,8),(16,9),(19,11),(21,13),(21,17),(18,18),(14,17),(10,15)],'.')
   self.poly([(17,2),(22,1),(25,2),(26,6),(24,10),(19,10),(16,8)],'.')
   self.poly([(3,6),(6,5),(8,7),(8,11),(6,13),(3,12)],'~')
   self.poly([(23,13),(27,12),(27,22),(24,21),(22,19)],'~')
   self.path([(6,23),(6,19),(13,19),(13,14),(18,14),(18,8),(23,8),(23,3),(24,3)],2,'南避潮厅—遗迹厅—北洞口')
   self.path([(6,19),(9,19),(9,9),(15,9),(15,6),(18,6)],1,'西潮潭旁检修支巷')
   self.path([(11,10),(13,10),(13,14)],1,'遗物台支路')
   self.path([(13,19),(20,19),(20,14),(18,14)],2,'藏身室救援支巷')
   self.stamp('cave_entry',20,1,'.','洞口避潮室，南门接出口短巷');self.path([(21,3),(24,3)],1,'避潮室门前')
   self.stamp('ancient_arch',17,5,'.','遗迹厅旧拱门，中部两格贯通',open_arch=True)
   self.rect(16,17,18,20,'#');self.rect(17,18,17,19,'.')
   walls=[[x,y]for y in range(17,21)for x in range(16,19)if(x,y)not in[(17,18),(17,19),(18,18)]]
   for x,y in walls:self.under[x,y]='^'
   self.under[18,18]='p';self.rect(19,18,20,18,'p')
   d['sailor_alcove']={'bounds':[16,17,18,20],'walls':walls,'door':[18,18],'approach':[19,18],'interior':[[17,18],[17,19]],'note':'南避潮厅东侧的藏身室，唯一东门接回北向主巷；开门只开放门格。'}
   self.stamp('crates',12,10,'.','遗物台旁行李');self.stamp('brazier',21,10,'.','北厅辨识火盆')
   d['player_positions']=[[6,18],[7,18],[6,19],[7,19],[5,18],[8,18],[5,19],[8,19],[6,20],[7,20]]
   self.relocate('npc_units',{'old_sailor':[17,18],'wounded':[17,19]})
   self.relocate('enemies',{'S22_boss':[24,4],'S22_e1':[22,9],'S22_e2':[19,11],'S22_e3':[20,13],'S22_e4':[13,9],'S22_e5':[21,4],'S22_e6':[24,6]})
   d['exit']=[24,2];d['targets']=[[11,10],[18,18]]
   d['objects'][0]['position']=[11,10];d['objects'][1]['position']=[18,18]
   d['objects'][2].update(position=[21,2],approach=[21,3],approaches=[[21,3]],entrance_cells=[[21,2]])
   d['tactical_notes']=['连续灰岩刻出南避潮厅、中央遗物厅与北侧遗迹厅，两处潮池留在岩室边缘；主巷穿过完整旧拱门中央的两格开口。','西潮潭旁的一格支巷绕回遗物厅，南侧藏身室只有一格东门，门外救援路直接接回北向主巷；遗物箱与避潮室都在清楚的支路尽头。','船员初始锁定在后段藏身室，开门后沿原有安全护送规则撤向北洞口；清场、取得遗物和存活旧船员撤离的判定保持，死亡仍按真实结果记录。']
   d['location_theme']='海洞潮池、避潮分厅与贯通遗迹拱门'
 def flood(self,start,opened=False):
  opens={tuple(p)for o in self.d['objects']for p in o.get('opens',[o['position']]if o['kind']in['door','rescue']else[])};q=deque([tuple(start)]);seen={tuple(start):0}
  while q:
   x,y=q.popleft()
   for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
    p=x+dx,y+dy
    if 0<=p[0]<self.w and 0<=p[1]<self.h and p not in seen and(self.g[p[1]][p[0]]not in'#^~'or opened and p in opens):seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def add_nature(self,anchors):
  g=self.g;w=self.w;h=self.h;rng=random.Random(B.seed(self.c+'-landmass'));nature=[]
  if self.c=='S22':
   # Low neutral rock lips follow existing blocked wall edges; nothing enters walkable floors.
   allowed={(x,y)for y,row in enumerate(g)for x,ch in enumerate(row)if ch=='^'};taken=set()
   candidates=sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)not in allowed for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]),p[1],p[0]))
   for x,y in candidates:
    if(x,y)in taken or(x+y)%3:continue
    if not any(0<=x+dx<w and 0<=y+dy<h and g[y+dy][x+dx]in'.p'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]):continue
    for key in['ridge_bent','outcrop','boulder']:
     sw,sh=B.NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
     if cells<=allowed and not cells&taken:self.props.append({'path':f'res://assets/chapter1-redesign-20261022/side/mine-rims/{key}.png','position':[x*16,y*16],'purpose':'连续岩壁低岩缘'});taken|=cells;break
   return nature
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
  nature.sort(key=lambda p:p['position'][1]+B.NATURE[p['key']]['size'][1]);return nature
 def bake(self):
  self.design();d=self.d;c=self.c;w=self.w;h=self.h;g=self.g
  anchors={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for k in['enemies','npc_units','reinforcements']for u in d[k]]}
  for x,y in anchors:
   assert g[y][x]not in'#^~',(c,'blocked anchor',x,y,g[y][x])
   if g[y][x]=='f':g[y][x]='.'
  for o in d['objects']:
   for x,y in o.get('approaches',[]):assert g[y][x]not in'#^~',(c,'blocked front',o['id'],x,y)
  units=[tuple(p)for p in d['player_positions']]+[tuple(u['position'])for u in d['enemies']+d['npc_units']];assert len(units)==len(set(units)),(c,'overlap')
  ground=[[self.under.get((x,y),'.')if ch in'#ht'else'.'if ch=='f'or(ch=='^'and c!='S22')else ch for x,ch in enumerate(row)]for y,row in enumerate(g)]
  base=[]
  for y,row in enumerate(ground):
   line=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{c}-ch2-redesign:{x}:{y}')%4;mat='marsh'if c=='S22'and ch=='.'else MAT[ch];tile=B.PACK['base'][mat][v]
    if ch=='p':tile=A.edge('dirt','marsh'if c=='S22'else'grass',B.mask_at(ground,x,y,lambda q:q in'ps'),v)
    elif ch=='d':tile=A.edge('sand','sea',B.mask_at(ground,x,y,lambda q:q!='~'),v)
    elif ch=='c':tile=A.edge('cobble','grass',B.mask_at(ground,x,y,lambda q:q in'cp'),v)
    elif ch=='^':tile=cave_wall([0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]not in'^#'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
    elif ch=='~':
     ns=[]
     for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
      q=ground[y+dy][x+dx]if 0<=x+dx<w and 0<=y+dy<h else'~';ns.append('marsh'if c=='S22'and q=='.'else MAT[q])
     tile=A.water(ns,v)
     # Keep the published atlas order, but remove the extra bright water-cell rim.
     # The islands already have real 1–2 tile beaches with native corner masks.
     if c!='S22':tile=B.PACK['base']['sea'][v]
    line.append(tile)
   base.append(line)
  nature=self.add_nature(anchors)
  d.update(map={'width':w,'height':h,'tiles':[IDS[ch]for row in g for ch in row]},logic_grid=[''.join(row)for row in g],visual_ground=[''.join(row)for row in ground],art_layers=[base,[[None]*w for _ in range(h)],[[None]*w for _ in range(h)]],art_modules=self.modules,art_props=self.props,natural_props=nature,building_sites=self.sites,art_atlas='res://assets/chapter2-redesign-20261022/islands-cave/terrain.png',art_columns=32,tactical_routes=self.routes,tactical_review_version='0.10.6-ch2',art_style_version='chapter2-redesign-20261022',landscape_revision='M41 approved composition method; chapter2 islands and cave',nature_layout={'biome':'rock'if c=='S22'else'forest','props':[],'excluded':[[0,0,w*16,h*16]]})
  d['production_anchors']={'revision':'0.10.6-ch2','deployment':d['player_positions'],'deploy':d['player_positions'],'targets':d['targets'],'exit':d['exit']};d['visual_notes']=d['tactical_notes'].copy()
  seen=self.flood(d['player_positions'][0]);opened=self.flood(d['player_positions'][0],True)
  standard={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for k in['enemies','reinforcements']for u in d[k]]};assert standard<=set(seen),(c,'unreachable actors',standard-set(seen));assert anchors<=set(opened),(c,'unreachable NPC',anchors-set(opened))
  for o in d['objects']:
   x,y=o['position'];fronts=o.get('approaches',[o['approach']]if'approach'in o else[[x,y]]+([[x+dx,y+dy]for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]]if o.get('adjacent')else[]));assert any(tuple(p)in seen for p in fronts),(c,'unreachable object',o['id'])
  for group in['enemies','npc_units','reinforcements']:
   assert len(d[group])==len(self.old[group]);assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(self.old[group],d[group])),(c,group)
  for k in['characters','terrain','goal','cause','before','during','after','absent_branch','optional','contract','ai_and_timing','reinforcement_turn','beacon_defense_turn','escort_move','equipment_revision','event_boats','map_tint']:assert d.get(k)==self.old.get(k),(c,k)
  movable=['position','approach','approaches','entrance_cells']
  for a,b in zip(self.old['objects'],d['objects']):assert{k:v for k,v in a.items()if k not in movable}=={k:v for k,v in b.items()if k not in movable},(c,a['id'])
  report={'passed':True,'code':c,'size':[w,h],'closed_connected':len(seen),'opened_connected':len(opened),'notes':d['tactical_notes'],'units_only_positions_changed':True,'story_timing_rules_preserved':True,'coordinate_changes':{group:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(self.old[group],d[group])]for group in['enemies','npc_units','reinforcements','objects']},'deployment_before':self.old['player_positions'],'deployment_after':d['player_positions'],'exit':d['exit'],'targets':d['targets']}
  if c=='F23':
   camp=next(u for u in d['npc_units']if u['id']=='fishers');report['camp_min_flying_distance']=min(abs(u['position'][0]-camp['position'][0])+abs(u['position'][1]-camp['position'][1])for u in d['enemies']if u['class_id']==3);assert report['camp_min_flying_distance']>=19
  if c=='F24':
   assert g[d['targets'][0][1]][d['targets'][0][0]]=='c';report['first_deployment_to_beacon']=seen[tuple(d['targets'][0])];assert report['first_deployment_to_beacon']<=5
  if c=='S22':
   assert tuple(d['npc_units'][0]['position'])not in seen and tuple(d['npc_units'][1]['position'])not in seen;report['locked_room_only_opens_at_rescue_cell']=True;report['old_sailor_to_exit_steps']=self.flood(d['npc_units'][0]['position'],True)[tuple(d['exit'])]
  write(R/f'data/stages/{c}.json',d);report['map_sha256']=hashlib.sha256((R/f'data/stages/{c}.json').read_bytes()).hexdigest();write(O/f'{c}-design.json',report);return report
if __name__=='__main__':
 reports=[Field('F23',32,26).bake(),Field('F24',32,28).bake(),Field('S22',28,24).bake()];A.save();write(O/'geometry.json',{'passed':True,'maps':reports});print(json.dumps([{'code':r['code'],'size':r['size'],'passed':True}for r in reports]))
