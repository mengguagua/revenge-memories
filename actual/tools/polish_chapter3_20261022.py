#!/usr/bin/env python3
"""Chapter 3 native-pixel landscape polish from an immutable pre-change snapshot."""
from pathlib import Path
from collections import deque
import copy, hashlib, importlib.util, json, math, random, subprocess
from PIL import Image

R=Path(__file__).resolve().parents[1]
BASE=R/'reports/map-polish-late-20261022/baseline'
OUT=R/'reports/map-polish-late-20261022/chapter3'
spec=importlib.util.spec_from_file_location('landscape',R/'tools/redesign_battlefields.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
PACK=B.PACK; NATURE=B.NATURE
META=json.loads((R/'assets/battlefield-0.3.0/terrain.json').read_text());T=META['transitions']
CAVE=json.loads((R/'assets/map-polish-20261022/side-terrain.json').read_text())
ART=R/'assets/map-polish-late-20261022'
ART.mkdir(exist_ok=True)
source_image=Image.open(R/'assets/map-polish-20261022/side-terrain.png').convert('RGBA')
CELLS=[source_image.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16))for i in range(CAVE['tile_count'])]
ORIGINAL=len(CELLS);EXTRA={'salt_path':{},'salt_rock':{},'shore':{}}
mask_spec=importlib.util.spec_from_file_location('native_masks',R/'tools/build_world_tiles.py');MASK=importlib.util.module_from_spec(mask_spec);mask_spec.loader.exec_module(MASK)
for family,fg in [('salt_path',PACK['base']['dirt']),('salt_rock',CAVE['rock_ids'])]:
 for mask in MASK.MASKS:
  ids=[]
  for v in range(4):
   tile=CELLS[PACK['base']['salt'][v]].copy();front=CELLS[fg[v]].copy();front.putalpha(MASK.alpha_mask(mask));tile.alpha_composite(front);ids.append(len(CELLS));CELLS.append(tile)
  EXTRA[family][str(mask)]=ids
def shore(neighbours,v):
 key=''.join(neighbours)
 if key not in EXTRA['shore']:
  ids=[]
  for variant in range(4):
   tile=CELLS[PACK['base']['sea'][variant]].copy()
   def pixel(px,py,ch):
    material=CAVE['rock_ids'][variant]if ch=='^'else PACK['base'][MATERIAL[ch]][variant]
    tile.putpixel((px,py),CELLS[material].getpixel((px,py)))
   for side,ch in enumerate(neighbours[:4]):
    if ch in'~s':continue
    for a in range(16):
     for depth in range(2):
      px,py=[(a,depth),(15-depth,a),(a,15-depth),(depth,a)][side];pixel(px,py,ch)
   for ch,(cx,cy,sx,sy)in zip(neighbours[4:],[(15,0,-1,1),(15,15,-1,-1),(0,15,1,-1),(0,0,1,1)]):
    if ch in'~s':continue
    for dy in range(3):
     for dx in range(3):
      if dx+dy<=2:pixel(cx+sx*dx,cy+sy*dy,ch)
   ids.append(len(CELLS));CELLS.append(tile)
  EXTRA['shore'][key]=ids
 return EXTRA['shore'][key][v]
def save_atlas():
 im=Image.new('RGBA',(512,math.ceil(len(CELLS)/32)*16))
 for i,tile in enumerate(CELLS):im.alpha_composite(tile,(i%32*16,i//32*16))
 path=ART/'chapter3-terrain.png';im.save(path);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(path)],check=True)
 check=Image.open(path).convert('RGBA')
 assert all(check.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)).tobytes()==CELLS[i].tobytes()for i in range(ORIGINAL))
 write(ART/'chapter3-terrain.json',{'source':'res://assets/map-polish-20261022/side-terrain.png','original_ids_and_pixels_preserved':True,'original_tile_count':ORIGINAL,'tile_count':len(CELLS),'columns':32,'tile_size':16,'transitions':EXTRA,'size':list(im.size),'bytes':path.stat().st_size,'purpose':'第3章独立图集：原生灰岩、盐地土径及与实际陆地对应的窄岸线，保留全部原图集ID；无损压缩保留像素清晰度。'})
IDS={'.':48,',':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'s':191,'b':48,'+':218,'c':208,'a':48}
MATERIAL={'.':'grass',',':'dirt','f':'grass','^':'rock','d':'sand','~':'sea','#':'stone','=':'stone','s':'timber','b':'cobble','+':'sacred','c':'cave','a':'salt'}
CODES=['M31','M32','M33','F31','F32','F33','S31','S32']
LOCK=['characters','player_positions','enemies','npc_units','terrain','enemy_group_ids','objects','reinforcements','reinforcement_turn','exit','boss_id','targets','goal','before','during','after','optional','event_boats','clear_training_exp']
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

class Field:
 def __init__(self,c):
  self.c=c;self.old=json.loads((BASE/f'{c}.json').read_text());self.d=copy.deepcopy(self.old);self.w=self.d['map']['width'];self.h=self.d['map']['height'];self.g=[list(r)for r in self.old['logic_grid']]
  self.solid={(x,y)for y,row in enumerate(self.g)for x,ch in enumerate(row)if ch=='#'}
  self.anchors={tuple(p)for p in self.d['player_positions']+[self.d['exit']]+self.d['targets']}|{tuple(u['position'])for k in ['enemies','npc_units','reinforcements']for u in self.d[k]}
  self.protect=set(self.anchors)
  for o in self.d['objects']:
   self.protect.add(tuple(o['position']));self.protect.update(tuple(p)for p in o.get('approaches',[o['approach']]if'approach'in o else[]))
   if o.get('adjacent'):
    x,y=o['position'];self.protect.update((x+dx,y+dy)for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)])
  self.reserved_art={tuple(p)for m in self.d['art_modules']for p in m['cells']}
  self.routes=[];self.added=[];self.skipped=[];self.ground={};self.rng=random.Random(B.seed(c+'chapter3-polish'))
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):
    if(x,y)in self.solid:self.ground[x,y]=ch;continue
    if self.g[y][x]=='+'or(ch in'^~#f'and(x,y)in self.protect):continue
    self.g[y][x]=ch
 def ellipse(self,cx,cy,rx,ry,ch,only=None):
  for y in range(max(0,int(cy-ry-1)),min(self.h,int(cy+ry+2))):
   for x in range(max(0,int(cx-rx-1)),min(self.w,int(cx+rx+2))):
    if((x-cx)/rx)**2+((y-cy)/ry)**2<1+.07*math.sin(x*.8+y*.5) and(only is None or self.g[y][x]in only):self.rect(x,y,x,y,ch)
 def path(self,pts,width=2,ch=',',name=''):
  for x,y in B.route(pts):self.rect(x-width//2,y-width//2,x+(width-1)//2,y+(width-1)//2,ch)
  self.routes.append({'name':name,'waypoints':[list(p)for p in pts],'width':width,'surface':ch})
 def stamp(self,name,x,y,ground=','):
  m=B.MODULES[name];w,h=m['footprint'];cells={(xx,yy)for yy in range(y,y+h)for xx in range(x,x+w)}
  if cells&(self.protect|self.solid|self.reserved_art)or x<0 or y<0 or x+w>self.w or y+h>self.h:
   self.skipped.append([name,x,y]);return
  self.rect(x,y,x+w-1,y+h-1,ground)
  for p in cells:self.g[p[1]][p[0]]='#';self.ground[p]=ground
  self.solid|=cells;self.reserved_art|=cells
  self.d['art_props'].append({'path':m['path'],'position':[x*16,y*16]})
  self.d['art_modules'].append({'name':name,'origin':[x,y],'footprint':[w,h],'cells':[list(p)for p in sorted(cells)],'logic':'#','runtime_prop':True,'purpose':'沿通路布置的完整原生场景物件'})
  self.added.append({'name':name,'origin':[x,y]})
 def design(self):
  c=self.c
  if c=='M31':
   self.rect(1,0,27,23,'.')
   self.rect(1,1,26,5,'b');self.rect(1,8,5,15,'b');self.rect(9,9,17,14,'b');self.rect(22,8,26,13,'b');self.rect(9,18,20,22,'b')
   self.path([(3,23),(3,20),(7,20),(7,7),(0,7)],3,'=','西门撤离主街')
   self.path([(7,17),(21,17),(21,7),(7,7)],3,'=','拘押院外侧环街')
   self.path([(14,14),(14,17)],2,'=','拘押院南门')
   for pts in [[(4,4),(4,7)],[(11,4),(11,7)],[(18,4),(18,7)],[(24,11),(24,17),(21,17)],[(11,21),(7,21)],[(18,22),(18,17)],[(3,11),(7,11)],[(3,14),(7,14)]]:self.path(pts,2,'b','住区与仓库门前支巷')
   for e in[(10,11,2,3),(18,11,2,3),(14,2,2,2),(24,21,3,2),(2,17,2,1)]:self.ellipse(*e,'f',only='.')
   self.stamp('well',24,19,'b');self.path([(24,20),(18,20)],2,'b','南住区井前小路')
   self.stamp('crates',25,12,'b');self.stamp('grain_sacks',5,14,'b')
   self.d['tactical_notes']=['西门撤离主街与东侧环街围合拘押院，院门朝南接路；居民获释后可以沿连续宽街抵达真正的西门。','街边医舍、粮仓和民宅各有门前短巷，南住区围绕水井布置，林带与小院分开街道和建筑。','保留两名拘押居民、侧街路障和第四敌回合追兵的原位置与条件；部署到拘押院不增加绕行。']
  elif c=='M32':
   self.rect(0,0,31,23,'.')
   for e in[(2,4,3,6),(16,1,4,3),(31,18,3,7)]:self.ellipse(*e,'^')
   for e in[(6,4,3,5),(5,15,3,2),(17,18,4,2),(12,22,4,2),(21,3,2,3),(29,7,3,4),(2,11,2,2)]:self.ellipse(*e,'f',only='.')
   self.path([(3,23),(3,20),(9,20),(9,12),(16,12),(25,12),(28,12),(28,0)],3,',','车队运输主路')
   self.path([(9,20),(23,20),(23,14),(25,14)],2,',','南林缘绕行路')
   self.path([(9,12),(9,6),(14,6),(14,9),(16,9),(16,12)],2,',','粮仓装卸支路')
   self.rect(13,10,18,14,'b');self.rect(23,10,28,16,'b');self.rect(25,1,29,5,',')
   self.path([(15,14),(28,14),(28,1)],2,',','运输车北撤车辙')
   self.path([(4,13),(9,13)],2,',','道路工棚入口')
   self.stamp('grain_sacks',12,10,'b');self.stamp('crates',12,11,'b');self.stamp('grain_wagon',19,15,',')
   self.stamp('camp_palisade',26,17,',');self.path([(19,16),(23,16)],2,',','备用车场入口')
   self.d['tactical_notes']=['军需大道穿过丘陵林带，两处铺石运输站直接连在车辙上；北口由哨棚守卫，粮仓和工棚都有接路的南向入口。','南侧林缘留出一条宽度两格的迂回道，树林集中在道路两侧，车场与粮袋沿站场边缘放置。','运输车、两站和车锁的位置与原条件保持，既有北撤道路贯通，首个可控制目标不增加路径距离。']
  elif c=='M33':
   self.rect(0,0,27,25,'.');self.rect(24,0,27,25,'~')
   self.ellipse(0,8,3,12,'^');self.ellipse(2,1,4,3,'^')
   for e in[(5,5,3,4),(6,17,2,3),(16,22,6,3),(13,2,3,2)]:self.ellipse(*e,'f',only='.')
   self.rect(10,6,23,19,'b');self.rect(17,1,23,6,'b')
   self.path([(4,25),(4,23),(8,23),(8,16),(14,16),(14,8),(23,8),(23,4),(24,3)],3,'=','堡前车道与正门')
   self.path([(6,13),(23,13)],2,'=','诊所与投送码头横街')
   self.path([(9,8),(9,13)],2,'b','诊所门前坡道');self.path([(18,18),(18,20),(14,20),(14,16)],2,'b','工房记录室前院')
   self.rect(24,11,26,13,'s');self.rect(24,3,24,5,'=')
   self.stamp('crates',22,14,'b');self.stamp('grain_sacks',23,14,'b');self.stamp('camp_palisade',10,20,'.')
   self.d['tactical_notes']=['石堡的铺石内院、南侧工房与东岸投送栈桥形成明确的军港关系；码头控制旗位于上岸通路尽头。','西侧灰岩山脊与林坡框住入堡车道，诊所和工房各有门前支路，南林缘留有平行进退空间。','保留格曼交涉、工房记录和投送码头的实际位置，堡主与增援条件保持；栈桥两端均连接真实陆地。']
  elif c=='F31':
   # Keep both prison courts and the rescue route; shape the quay edge around the port facilities.
   self.rect(10,1,26,19,'b');self.rect(10,1,10,8,'s');self.rect(10,12,13,15,'s')
   self.rect(2,14,7,20,'s');self.rect(3,13,5,13,'s');self.rect(3,20,5,20,'s')
   self.path([(5,17),(12,17)],2,'s','两格登船跳板')
   self.path([(12,17),(24,17),(24,4)],3,'=','仓储码头主通道')
   self.path([(14,5),(14,14),(17,14),(17,17)],2,'b','西仓库装卸巷')
   self.path([(19,10),(19,11),(24,11)],2,'b','北扣船所门前街')
   self.path([(21,16),(21,17)],2,'b','南停泊所门前街')
   self.rect(25,1,26,2,'s');self.rect(25,19,26,19,'s')
   self.stamp('crates',11,6,'s');self.stamp('grain_sacks',12,6,'b');self.stamp('crates',16,12,'b');self.stamp('grain_wagon',14,19,'b')
   self.d['tactical_notes']=['己方船停在西侧港湾，连续的两格跳板连到码头主街；船首、甲板、船尾与上岸口保持同一条船的轮廓。','北扣船所和南停泊所分别朝南开门，门前支街接入环形装卸通道，伤者无需穿越仓库或货箱。','木质靠泊边、石质内街、仓库与货场分层呈现；两处解锁、伤者撤回船只及第三敌回合增援规则保持。']
  elif c in['F32','S32']:
   self.rect(0,0,27,self.h-1,'a')
   self.ellipse(3,6,3.5,4.5,'~');self.ellipse(18,2,4,2.8,'^');self.ellipse(26,self.h-3,2.8,3.5,'^');self.ellipse(1,0,3,2,'^')
   y=20 if c=='F32'else 18
   self.path([(3,self.h-1),(3,y),(10,y),(10,12),(21,12),(21,8),(24,8),(24,3)],3,',','盐原干燥主路')
   self.path([(10,16),(24,16),(24,8)],2,',','营地东侧通路')
   self.path([(8,9 if c=='F32'else 7),(8,12),(10,12)],2,',','盐湖边民宅入口')
   if c=='F32':
    self.rect(12,10,16,14,',');self.rect(13,12,15,13,'=')
    self.path([(8,16),(10,16)],2,',','路线册接应点')
    self.stamp('grain_wagon',16,17,',');self.stamp('fishing_cottage',4,13,',');self.path([(5,15),(10,15)],2,',','盐路歇脚屋')
    self.stamp('crates',15,9,',');self.stamp('grain_sacks',16,9,',')
    self.d['tactical_notes']=['干燥盐路绕开西侧卤湖，经过中央水井歇脚坪再抵达北口；路旁小屋、运输车与补给箱组成有人使用的盐路驿站。','灰色岩台收束北侧和东南边界，主路与东侧短道围出中央开阔战场，避免用密林装饰盐原。','向导、路线册和可移路障位置保持；向导正常撤离与遇难后回收路线册两条路径都可达。']
   else:
    self.rect(10,7,16,12,',');self.rect(17,11,23,16,',')
    self.path([(13,12),(13,16),(20,16)],2,',','两营房南门联络道')
    self.stamp('barracks',17,5,',');self.path([(18,7),(21,7)],2,',','守军营房入口')
    self.stamp('camp_palisade',17,19,'a');self.stamp('camp_palisade',7,2,'a');self.stamp('crates',25,11,',')
    self.d['tactical_notes']=['营地依靠西侧卤湖与北面岩台选址，两间拘押营房都有南向门前空地，并由宽干道连向军帐与守军营房。','外围短木栅、仓箱和东侧巡路表达临时驻军用途；岩台和盐地保留开阔视线，不铺设与盐原不符的树林。','两间营房及诺娅、弟弟、居民的位置和独立生死判定保持；从部署区到任一牢门都有连续通路。']
  elif c=='F33':
   self.rect(0,0,27,23,'a');self.rect(5,4,25,18,'b')
   self.ellipse(1,6,3,7,'^');self.ellipse(25,22,4,3,'^');self.ellipse(11,0,5,2,'^')
   self.path([(4,23),(4,21),(9,21),(9,15),(22,15),(22,4)],3,'=','提炼院运输主廊')
   self.path([(9,15),(9,8),(22,8)],2,'=','记录室外侧回廊')
   self.path([(14,13),(14,15)],2,'b','术士工房南门');self.path([(16,7),(16,8)],2,'b','记录室正面入口')
   self.rect(18,10,21,13,'a');self.path([(21,14),(24,14),(24,12)],2,'b','阵台与祭器平台')
   self.stamp('quay_warehouse',4,13,'b');self.path([(5,15),(9,15)],2,'b','西侧物料仓门前')
   self.stamp('grain_sacks',6,8,'b');self.stamp('crates',6,9,'b');self.stamp('camp_palisade',11,19,'a');self.stamp('camp_palisade',19,19,'a')
   self.d['tactical_notes']=['提炼院用石质主廊连接物料仓、术士工房、记录室和控制阵台，院内保留回廊与中央设备空地，呈现设施后庭而非空白广场。','南侧卸货口接运输路，外侧盐地和灰岩台划定设施边界；祭器平台独立设于东侧，控制旗在玩家能够站立的地面。','两名术士的保护、工房开门、记录复制与阵台稳定各自保留，所有门前操作格与原战斗条件一致。']
  else:
   self.rect(0,0,21,19,'^');self.rect(2,2,19,17,'c')
   for e in[(2,8,1.5,1.6),(18,16,2,2),(11,1,3,2),(20,9,2,3)]:self.ellipse(*e,'^')
   self.path([(4,19),(4,16),(10,16),(10,7),(18,7),(18,3)],3,'=','地牢主廊与守卫岗')
   self.path([(5,7),(10,7)],2,'=','西牢门前横廊');self.path([(15,7),(18,7)],2,'=','东牢门前横廊')
   self.path([(10,13),(16,13),(16,7)],2,'=','东侧巡守回廊');self.path([(4,12),(4,14),(10,14)],2,'=','支木矿口支巷')
   self.stamp('crates',7,12,'c');self.stamp('grain_sacks',8,12,'c');self.stamp('brazier',18,8,'c')
   self.d['tactical_notes']=['灰岩地牢围绕两间独立牢房组织横廊，东西牢门都朝向明亮土质通道，主廊连到东北守卫岗。','矿口工具角与东侧巡守回廊形成可读的内部空间；自然岩壁取代整圈紫色方框，牢室和火盆保留完整原生像素轮廓。','牢门、家属、首领和劝降条件保持，释放家属后不增加撤离要求；两扇门都可从南侧到达。']
  # Keep all source anchors on exactly the same movement/avoidance category.
  for x,y in self.anchors:
   if (x,y)not in self.solid and IDS[self.g[y][x]]!=IDS[self.old['logic_grid'][y][x]]:self.g[y][x]=self.old['logic_grid'][y][x]
  # Original locked rooms remain visually paved and respect the only gate opening.
  for u in self.d['npc_units']:
   if u.get('locked'):
    x,y=u['position']
    if self.old['logic_grid'][y][x]in'=c':
     for yy in range(max(0,y-1),min(self.h,y+2)):
      for xx in range(max(0,x-1),min(self.w,x+2)):
       if self.old['logic_grid'][yy][xx]in'=c':self.g[yy][xx]=self.old['logic_grid'][yy][xx]
 def bake(self):
  self.design();c=self.c
  ground=[[self.ground.get((x,y),'c'if c=='S31'else'b'if c in['M31','M33','F31','F33']else',')if ch=='#'else ch for x,ch in enumerate(row)]for y,row in enumerate(self.g)]
  base=[]
  for y,row in enumerate(ground):
   line=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{c}/{x}/{y}')%4;tile=PACK['base'][MATERIAL[ch]][v]
    if c=='S31':
     if ch=='c':tile=CAVE['floor_ids'][v]
     elif ch=='=':tile=CAVE['transitions']['path'][str(B.mask_at(ground,x,y,lambda q:q=='='))][v]
     elif ch=='^':tile=CAVE['transitions']['rock'][str(B.mask_at(ground,x,y,lambda q:q=='^'))][v]
    elif ch==','and c=='M32':tile=T['path'][str(B.mask_at(ground,x,y,lambda q:q in',b'))][v]
    elif ch==','and c in['F32','F33','S32']:tile=EXTRA['salt_path'][str(B.mask_at(ground,x,y,lambda q:q in',=b'))][v]
    elif ch=='^':
     mask=str(B.mask_at(ground,x,y,lambda q:q=='^'))
     tile=T['mountain_ground']['grass'][mask][v]if c in['M32','M33']else EXTRA['salt_rock'][mask][v]
    elif ch=='='and c!='S31':tile=PACK['base']['dirt'][v]
    elif ch=='~':
     neighbours=[]
     for dx,dy in[(0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)]:
      neighbours.append(ground[y+dy][x+dx]if 0<=x+dx<self.w and 0<=y+dy<self.h else'~')
     tile=shore(neighbours,v)
    elif ch=='s':
     mask=B.mask_at(ground,x,y,lambda q:q=='s')&15;axis='h'if c=='F31'and y in[16,17]and 7<=x<=11 else'v';tile=T['walkway'][axis+str(mask)][v]
    line.append(tile)
   base.append(line)
  # Full native foliage/rock silhouettes only within matching logical footprints.
  nature=[];used=set()
  for ch,large,small in[('f',['pine_broad','pine_tall','pine_pair'],['pine_small_a','pine_small_b']),('^',['peak_low','crag_tall','ridge_bent','outcrop'],['boulder'])]:
   allowed={(x,y)for y,row in enumerate(self.g)for x,t in enumerate(row)if t==ch};positions=sorted(allowed);self.rng.shuffle(positions)
   for x,y in positions:
    if(x,y)in used or self.rng.random()<.16:continue
    key=self.rng.choice(large);sw,sh=NATURE[key]['size'];foot={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
    if not foot<=allowed or foot&(used|self.protect|self.reserved_art):continue
    nature.append({'key':key,'position':[x*16,y*16],'flip':self.rng.random()<.35});used|=foot
   for x,y in sorted(allowed-used-self.protect-self.reserved_art):
    if self.rng.random()<(.12 if ch=='f'else .8):continue
    nature.append({'key':self.rng.choice(small),'position':[x*16,y*16],'flip':self.rng.random()<.5})
  self.d.update(logic_grid=[''.join(row)for row in self.g],visual_ground=[''.join(row)for row in ground],art_atlas='res://assets/map-polish-late-20261022/chapter3-terrain.png',art_layers=[base,copy.deepcopy(self.old['art_layers'][1]),copy.deepcopy(self.old['art_layers'][2])],natural_props=nature,tactical_routes=self.routes,tactical_review_version='0.10.3',art_style_version='map-polish-late-20261022',landscape_revision='2026-10-22-m11-reference')
  self.d['map']['tiles']=[IDS[ch]for row in self.g for ch in row]
  for k in LOCK:assert self.d.get(k)==self.old.get(k),(c,k)
  checks=self.check();write(R/f'data/stages/{c}.json',self.d);write(OUT/f'{c}-geometry.json',checks);return checks
 def check(self):
  opens={tuple(p)for o in self.d['objects']for p in o.get('opens',[])}
  def flood(opened):
   start=tuple(self.d['player_positions'][0]);seen={start};q=deque([start])
   while q:
    x,y=q.popleft()
    for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:
     p=(x+dx,y+dy)
     if 0<=p[0]<self.w and 0<=p[1]<self.h and p not in seen and(self.g[p[1]][p[0]]not in'#^~'or(opened and p in opens)):seen.add(p);q.append(p)
   return seen
  closed=flood(False);opened=flood(True)
  ordinary=self.d['player_positions']+[self.d['exit']]+[u['position']for k in['enemies','reinforcements']for u in self.d[k]]
  assert all(tuple(p)in closed or (((self.c=='S31' and p==[15,5]) or (self.c=='S32' and p==[21,14])) and tuple(p)in opened) for p in ordinary),(self.c,'unreachable actors',[p for p in ordinary if tuple(p)not in closed])
  assert all(tuple(u['position'])in opened for u in self.d['npc_units']),(self.c,'unreachable NPC')
  for o in self.d['objects']:
   fronts=o.get('approaches',[o['approach']]if'approach'in o else[])
   if not fronts:
    x,y=o['position'];fronts=[[x,y]]+([[x+dx,y+dy]for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]]if o.get('adjacent')else[])
   assert any(tuple(p)in closed for p in fronts),(self.c,o['id'],'unapproachable')
  for m in self.d['art_modules']:
   for x,y in m['cells']:
    if m.get('logic')=='#' and (x,y)not in opens and (self.old['logic_grid'][y][x]=='#' or m.get('runtime_prop')):assert self.g[y][x]=='#',(self.c,m['name'],x,y)
  return{'code':self.c,'passed':True,'gameplay_fields_unchanged':LOCK,'closed_connected':len(closed),'opened_connected':len(opened),'changed_logic_cells':sum(a!=b for a,b in zip(''.join(self.old['logic_grid']),''.join(self.d['logic_grid']))),'natural_props':len(self.d['natural_props']),'new_structures':self.added,'skipped_props':self.skipped,'routes':self.routes,'source_sha256':hashlib.sha256((BASE/f'{self.c}.json').read_bytes()).hexdigest()}

if __name__=='__main__':
 # Atlas shores are appended in this fixed map order; always rebuild the complete set.
 results=[Field(c).bake()for c in CODES];save_atlas()
 print(json.dumps(results,ensure_ascii=False,indent=2))
