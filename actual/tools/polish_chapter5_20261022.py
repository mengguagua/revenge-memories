#!/usr/bin/env python3
"""Chapter V landscape pass: original art, fixed story anchors, reproducible baseline."""
from pathlib import Path
from collections import deque
import copy,hashlib,importlib.util,json,math,random,subprocess
from PIL import Image
R=Path(__file__).resolve().parents[1];BASE=R/'reports/map-polish-late-20261022/baseline';OUT=R/'reports/map-polish-late-20261022/chapter5'
read=lambda p:json.loads(p.read_text())
PACK=read(R/'assets/battle_tiles/battle-tiles.json');SEA=read(R/'assets/chapter2/chapter2-tiles.json');TEMPLE=read(R/'assets/chapter5/terrain.json')['materials']
NATURE={s['key']:s for s in read(R/'assets/nature/nature.json')['sprites']}
MODULES={m['name']:m for m in PACK['modules']}
IDS={'.':48,',':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'s':191,'b':48,'+':218,'c':208,'a':48,'p':208}
MAT={'.':'grass',',':'dirt','f':'grass','^':'cave','d':'sand','~':'sea','#':'plaster','=':'stone','s':'timber','b':'cobble','+':'sacred','c':'cave','a':'salt','p':'plaster'}
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def seed(s):return int(hashlib.sha256(s.encode()).hexdigest()[:12],16)
def route(points):
 for a,b in zip(points,points[1:]):
  x,y=a;yield x,y
  while(x,y)!=tuple(b):
   if x!=b[0]:x+=1 if b[0]>x else -1
   else:y+=1 if b[1]>y else -1
   yield x,y
class ShoreAtlas:
 """Append shore cells from existing approved pixels; banks lie inside water cells."""
 def __init__(self):
  self.source=R/'assets/chapter5/temple-tiles.png';im=Image.open(self.source).convert('RGBA')
  self.cells=[im.crop((x,y,x+16,y+16))for y in range(0,im.height,16)for x in range(0,im.width,16)];self.original=len(self.cells);self.families={}
 def tile(self,g,x,y,v):
  w,h=len(g[0]),len(g)
  def material(dx,dy):
   xx,yy=x+dx,y+dy
   if not(0<=xx<w and 0<=yy<h):return'w'
   return {'~':'w','.':'g','f':'g','c':'c','^':'c','=':'s',',':'d'}.get(g[yy][xx],'i')
  key=''.join(material(dx,dy)for dx,dy in [(0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)])
  if key not in self.families:
   ids=[]
   for variant in range(4):
    tile=self.cells[PACK['base']['sea'][variant]].copy()
    def land(k):return self.cells[{'g':PACK['base']['grass'][variant],'c':PACK['base']['cave'][variant],'d':PACK['base']['dirt'][variant],'s':TEMPLE['sandstone'][1],'i':TEMPLE['ivory'][1]}[k]]
    for side,k in enumerate(key[:4]):
     if k=='w':continue
     source=land(k)
     for z in range(16):
      for depth in range(2):
       px,py=[(z,depth),(15-depth,z),(z,15-depth),(depth,z)][side];tile.putpixel((px,py),source.getpixel((px,py)))
    for k,(px,py,sx,sy)in zip(key[4:],[(15,0,-1,1),(15,15,-1,-1),(0,15,1,-1),(0,0,1,1)]):
     if k=='w':continue
     source=land(k)
     for dx in range(2):
      for dy in range(2-dx):tile.putpixel((px+sx*dx,py+sy*dy),source.getpixel((px+sx*dx,py+sy*dy)))
    ids.append(len(self.cells));self.cells.append(tile)
   self.families[key]=ids
  return self.families[key][v]
 def save(self):
  p=R/'assets/map-polish-late-20261022/temple-shores.png';p.parent.mkdir(exist_ok=True)
  im=Image.new('RGBA',(512,math.ceil(len(self.cells)/32)*16))
  for i,t in enumerate(self.cells):im.paste(t,((i%32)*16,(i//32)*16))
  im.save(p);subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(p)],check=True)
  meta={'source':'res://assets/chapter5/temple-tiles.png','original_cells_unchanged':self.original,'appended_cells':len(self.cells)-self.original,'pixel_size':list(im.size),'bytes':p.stat().st_size,'method':'Native 16px source cells preserved byte-for-byte at original indices; narrow existing floor pixels composed inside water cells, no scaling or palette replacement.','shore_families':self.families}
  write(p.with_suffix('.json'),meta)
ATLAS=ShoreAtlas()
class Field:
 def __init__(self,code):
  self.code=code;self.old=read(BASE/f'{code}.json');self.d=copy.deepcopy(self.old);self.w=self.d['map']['width'];self.h=self.d['map']['height']
  self.g=[list(r)for r in self.old['logic_grid']];self.structures={(x,y)for y,r in enumerate(self.g)for x,c in enumerate(r)if c=='#'}
  self.fixed={tuple(p)for p in self.d['player_positions']+[self.d['exit']]+[u['position']for u in self.d['enemies']+self.d['npc_units']+self.d['reinforcements']]}
  for o in self.d['objects']:self.fixed.add(tuple(o.get('approach',o['position'])))
  self.recover={(x,y)for y,r in enumerate(self.g)for x,c in enumerate(r)if c=='+'}
  self.routes=[];self.trees=[];self.added=[];self.accents=set();self.ground={};self.rocks=set()
 def rect(self,x0,y0,x1,y1,ch,strict=False):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):
    if(x,y)in self.structures:continue
    if ch in '~^#f' and(x,y)in self.fixed:continue
    if(x,y)in self.recover:continue
    self.g[y][x]=ch
 def path(self,points,width=3,label=''):
  for x,y in route(points):self.rect(x-width//2,y-width//2,x+(width-1)//2,y+(width-1)//2,'=')
  self.routes.append({'name':label,'waypoints':[list(p)for p in points],'width':width})
 def garden(self,rect,trees):
  self.rect(*rect,'.')
  for x,y,key in trees:self.tree(x,y,key)
 def tree(self,x,y,key='pine_tall'):
  sw,sh=NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
  if not all(0<=xx<self.w and 0<=yy<self.h and self.g[yy][xx]in'.f'for xx,yy in cells)or cells &self.fixed:return
  for xx,yy in cells:self.g[yy][xx]='f'
  self.trees.append({'key':key,'position':[x*16,y*16],'flip':False})
 def module(self,name,x,y):
  m=copy.deepcopy(MODULES[name]);w,h=m['footprint'];cells={(xx,yy)for yy in range(y,y+h)for xx in range(x,x+w)}
  assert not cells&(self.fixed|self.structures|self.recover),(self.code,name,cells&(self.fixed|self.structures|self.recover))
  for xx,yy in cells:self.g[yy][xx]='#'
  self.structures|=cells;m.update(origin=[x,y],cells=[list(p)for p in sorted(cells)],logic='#');self.d['art_modules'].append(m);self.added.append({'name':name,'origin':[x,y]})
 def rocky(self,x0,y0,x1,y1):
  self.rect(x0,y0,x1,y1,'^')
  for y in range(y0,y1+1,2):
   for x in range(x0,x1+1,2):
    cells={(xx,yy)for yy in range(y,y+2)for xx in range(x,x+2)}
    if all(0<=xx<self.w and 0<=yy<self.h and self.g[yy][xx]=='^'for xx,yy in cells):self.trees.append({'key':'peak_low','position':[16*x,16*y],'flip':False})
 def build(self):
  c=self.code
  # Preserve complete architecture footprints, restored ground is explicit and never random clutter.
  self.rect(0,0,self.w-1,self.h-1,'b'if c!='F51'else'c')
  if c=='M51':
   self.garden((2,2,13,6),[(2,2,'pine_tall'),(10,2,'pine_broad'),(12,4,'pine_young')]);self.rect(4,3,7,5,'~')
   self.garden((1,14,4,20),[(1,14,'pine_tall'),(2,18,'pine_broad')]);self.garden((8,19,12,21),[(8,19,'pine_tall'),(11,19,'pine_young')])
   self.garden((24,2,26,6),[(25,2,'pine_tall'),(24,5,'pine_young')]);self.garden((20,20,24,21),[(22,20,'pine_young'),(24,20,'pine_young')])
   self.path([(4,24),(15,24),(15,8),(24,8)],3,'南撤主路与宫门大道');self.path([(5,17),(25,17)],3,'两处病房前的救护横街');self.path([(5,17),(5,11),(5,7),(15,7)],2,'西侧物资院的环行小路');self.path([(10,16),(10,17)],1,'西病房门前');self.path([(22,18),(22,19),(15,19)],2,'东病房回送路')
   self.rect(1,22,6,24,'b');self.rect(1,10,5,12,',')
   self.module('crates',3,11);self.module('grain_sacks',4,12)
   self.d['tactical_notes']=['宫门大道贯通北宫与南侧撤离口，东西病房由连续救护横街连接；两处南门操作格与伤兵出门格保持原位。','西侧仓院以土色卸货地和独立小路连接救护街，药车留在院前；建筑本体仍不可步行。','水池、成组常绿树和庭院草地收住宫墙边缘，南部保留伤兵转送与队伍展开空间。','采用既有低饱和宫殿美术，主路换为较克制的浅砂石铺面，避免大面积青色棋盘抢过角色。']
  elif c=='M52':
   self.rect(0,0,31,23,'~');self.rect(0,6,6,20,'b');self.rect(25,3,31,20,'b');self.rect(6,10,25,15,'=')
   self.rect(0,4,4,5,'b');self.rect(0,21,4,22,'b');self.rect(27,1,31,2,'b');self.rect(27,21,31,22,'b')
   self.garden((0,4,1,6),[(0,4,'pine_tall')]);self.garden((0,18,2,20),[(0,18,'pine_broad')]);self.garden((29,2,31,6),[(29,2,'pine_tall'),(30,5,'pine_young')]);self.garden((28,17,31,21),[(29,18,'pine_broad')])
   self.path([(0,12),(31,12)],3,'西桥台、三道桥锁与东桥台');self.rect(6,10,25,15,'=')
   self.accents={(x,y)for x in range(6,26)for y in [11,14]};self.path([(2,7),(2,10)],2,'西门援军进入桥台的道路');self.path([(28,8),(28,12),(30,12)],2,'东桥头守备回廊')
   self.d['tactical_notes']=['保留完整六格石桥，三个桥锁沿同一横向主路排列；两岸道路确实接上桥面，桥外均为不能步行的水域。','西桥台保留部署与增援通道，东桥台为守卫留出回廊，两端由小片常绿庭园和错落岸线形成落脚点。','六根原有完整石柱与桥边护栏保持原位，桥面以浅石铺装和两条克制的青灰嵌线区分通行层。','三段控制顺序、首领与出口均保持，景观不增加绕行距离。']
  elif c=='F51':
   self.rect(3,4,24,23,'b');self.rect(12,2,15,20,'~');self.rect(12,12,15,14,'=')
   self.rocky(1,2,2,5);self.rocky(1,9,2,17);self.rocky(1,19,1,23);self.rocky(25,2,26,5);self.rocky(25,9,26,20)
   self.path([(4,24),(9,24),(9,13),(22,13),(22,21)],3,'西侧入场、检修桥、东侧工班');self.path([(9,22),(22,22)],2,'渠尾维修绕行通道');self.path([(7,12),(9,12)],2,'西装置操作面');self.path([(22,12),(22,5),(19,5)],2,'东装置与北侧楼梯');self.path([(8,5),(10,5),(10,10)],2,'西侧检修平台')
   self.module('crates',4,13);self.module('crates',18,19);self.module('brazier',17,15)
   self.d['tactical_notes']=['地下水渠从北侧岩口延伸到南部维修廊，中段三格检修桥连接两岸装置，渠尾另留日常维护通道。','两处调节器南面的交接格和工班站位保持原样，操作平台与通往楼梯的石路连续。','外围岩壁与小型检修物资围合地下空间，灯火分布在工作区边缘，不把地下祭所画成露天庭园。','北侧守卫平台、南部增援口和全部部署点仍可步行到达；交接后保护一轮的机制不变。']
  elif c=='F52':
   self.rect(14,8,17,20,'~');self.rect(14,12,17,15,'=')
   self.garden((1,2,4,7),[(1,2,'pine_tall'),(2,5,'pine_broad')]);self.garden((27,2,30,7),[(28,2,'pine_broad'),(29,5,'pine_tall')])
   self.garden((4,16,8,20),[(4,16,'pine_broad'),(6,19,'pine_young')]);self.garden((25,16,29,20),[(27,16,'pine_broad'),(26,19,'pine_young')]);self.garden((12,22,17,24),[(13,23,'pine_young'),(16,23,'pine_young')])
   self.path([(4,24),(10,24),(10,13),(24,13),(24,22)],3,'南廊与中央连桥');self.path([(10,23),(24,23)],2,'南侧回廊');self.path([(7,10),(10,10),(10,7),(20,7),(20,10),(25,10)],2,'两翼操作台与正殿前廊');self.path([(7,10),(7,13),(24,13),(25,13),(25,10)],2,'两岸门阵到中央桥')
   self.accents={(x,13)for x in range(14,18)}
   self.d['tactical_notes']=['中央水渠分开左右门阵，原石桥与南侧绕渠回廊组成闭合路线，主殿南侧另有通向两翼的短廊。','两处装置门前留足操作平台，站位与确认规则保持原样；水面边缘不再用整格伪岸线占用道路。','大树与矮树集中在外围和南部庭园，建筑入口、中央桥和正殿阶前保持清楚留白。','共享神宫的低饱和石材和建筑，与地下维修层通过水渠形制相联系，但用庭园和双翼布局区分场景。']
  elif c=='S51':
   self.garden((2,10,7,13),[(2,10,'pine_broad'),(5,11,'pine_tall')]);self.garden((16,10,21,13),[(19,10,'pine_broad'),(16,11,'pine_tall')]);self.garden((1,1,2,6),[(1,2,'pine_tall')]);self.garden((21,1,22,6),[(21,2,'pine_tall')])
   self.path([(4,18),(12,18),(12,7)],3,'南门交接与书库正门');self.path([(5,8),(18,8)],2,'书库门前阅览庭');self.path([(8,8),(8,14),(20,14),(20,16)],2,'环绕东西小庭的步廊');self.path([(8,14),(4,14),(4,17)],2,'西侧入场接路')
   self.rect(11,6,13,6,'=');self.accents={(12,y)for y in range(7,19)}
   self.d['tactical_notes']=['书库正门与南门交接处沿同一条中轴步道相连，取回记录后能直观看到返回方向。','两侧阅览庭由一圈石路连通，成组常绿树隔出安静的小庭，守卫区与部署区仍有充分展开空间。','原有书箱、石柱和完整书库立面保留；南门不增加假门或不可交互装饰，避免误判。','支线记录、南门交接条件和开放时机均不变，路线可直接走完，也能从侧廊接近守卫。']
  elif c=='J53':
   self.rect(2,15,5,19,'~');self.rect(26,15,29,19,'~')
   self.garden((9,15,12,21),[(10,17,'pine_broad'),(10,20,'pine_young')]);self.garden((19,15,22,21),[(20,17,'pine_broad'),(20,20,'pine_young')]);self.garden((1,1,6,3),[(2,1,'pine_tall'),(5,1,'pine_young')]);self.garden((25,1,30,3),[(27,1,'pine_tall'),(25,1,'pine_young')])
   self.path([(4,25),(28,25)],3,'两军会合南廊');self.path([(16,27),(16,8)],5,'共同进军中轴');self.path([(7,24),(7,13),(6,13),(6,12)],3,'西军侧翼阵门');self.path([(24,24),(24,13),(26,13),(26,12)],3,'东军侧翼阵门');self.path([(6,13),(26,13)],3,'阵门前横向联络廊');self.path([(9,7),(22,7)],2,'正殿阶前平台')
   self.accents={(16,y)for y in range(7,28)}|{(x,25)for x in range(3,30)}
   self.d['tactical_notes']=['两军从西南、东南入口沿南廊会合，五格中轴通向正殿；双方各有直达侧翼阵门的道路。','双池与成组庭树分隔外侧通道和中央推进线，横向联络廊让两翼能互相支援，无需绕入建筑背后。','两处阵门操作格、双方部署名册和前庭统领位置保持，新增景观不会把单方队伍关在支路。','浅石铺路承托低饱和宫殿，只在会师线和中轴保留细青灰嵌线，重点留给建筑、角色和阵门。']
  else:
   # The final arena is wider and calmer than the split-gate forecourt.
   self.rect(2,16,5,22,'~');self.rect(26,16,29,22,'~');self.rect(3,15,4,15,'~');self.rect(27,15,28,15,'~')
   self.garden((8,21,11,24),[(8,22,'pine_broad'),(11,23,'pine_young')]);self.garden((20,21,23,24),[(22,22,'pine_broad'),(20,23,'pine_young')]);self.garden((1,1,3,7),[(1,2,'pine_tall'),(2,5,'pine_young')]);self.garden((28,1,30,7),[(29,2,'pine_tall'),(28,5,'pine_young')])
   self.path([(4,27),(28,27)],3,'两军入场和后撤横廊');self.path([(16,29),(16,8)],5,'神座正面仪道');self.path([(7,26),(7,16),(12,16)],3,'西侧回转廊');self.path([(24,26),(24,16),(20,16)],3,'东侧回转廊');self.path([(8,10),(23,10)],3,'神座前会战平台')
   self.rect(11,12,21,18,'b');self.path([(16,19),(16,7)],3,'中央交战通道');self.accents={(16,y)for y in range(7,30)}|{(x,27)for x in range(3,30)}
   self.d['tactical_notes']=['神座与五格入场轴线一眼可辨，前庭的分路推进在此收束为宽阔的中央会战平台。','两侧柱廊、水池与南部庭园围合场地；西东回转廊保留会师与援护空间，池边不设置隐藏可走格。','神座、首领、双主角部署与半血援军规则不变，平台留空让现有战斗动作和法术表现清楚。','沿用低饱和神宫建筑与浅色石材，用稀疏青灰嵌线和成组植被控制节奏，不以额外发光或高饱和地面遮盖单位。']
  # Existing recovery tiles and anchored units retain their original terrain categories.
  for x,y in self.fixed|self.recover:
   if(x,y)not in self.structures and IDS[self.g[y][x]]!=IDS[self.old['logic_grid'][y][x]]:self.g[y][x]=self.old['logic_grid'][y][x]
  # Never leave a tree drawn over a road painted later in the composition.
  self.trees=[t for t in self.trees if all(self.g[yy][xx]in 'f^' for yy in range(t['position'][1]//16,t['position'][1]//16+math.ceil(NATURE[t['key']]['size'][1]/16))for xx in range(t['position'][0]//16,t['position'][0]//16+math.ceil(NATURE[t['key']]['size'][0]/16)))]
  occupied={(xx,yy)for t in self.trees for yy in range(t['position'][1]//16,t['position'][1]//16+math.ceil(NATURE[t['key']]['size'][1]/16))for xx in range(t['position'][0]//16,t['position'][0]//16+math.ceil(NATURE[t['key']]['size'][0]/16))}
  for y,row in enumerate(self.g):
   for x,ch in enumerate(row):
    if ch=='f' and(x,y)not in occupied:
     if(x,y)in self.fixed:self.trees.append({'key':'pine_young','position':[16*x,16*y],'flip':False})
     else:self.g[y][x]='.'
  layers=[[[None]*self.w for _ in range(self.h)]for _ in range(3)]
  for y,row in enumerate(self.g):
   for x,ch in enumerate(row):
    v=seed(f'{c}:{x}:{y}')%4
    if ch in'bp#':tile=TEMPLE['ivory'][1]
    elif ch=='=':tile=TEMPLE['sandstone'][1]
    else:tile=PACK['base'][MAT[ch]][v]
    if(x,y)in self.accents and ch=='=':tile=TEMPLE['teal'][1]
    if ch=='~':tile=ATLAS.tile(self.g,x,y,v)
    layers[0][y][x]=tile
  for m in self.d['art_modules']:
   if'tiles'in m:
    for dy,row in enumerate(m['tiles']):
     for dx,t in enumerate(row):layers[2][m['origin'][1]+dy][m['origin'][0]+dx]=t
  self.d['art_atlas']='res://assets/map-polish-late-20261022/temple-shores.png'
  self.d.update(logic_grid=[''.join(r)for r in self.g],art_layers=layers,natural_props=self.trees,tactical_routes=self.routes,tactical_review_version='0.10.3',art_style_version='map-polish-late-20261022',landscape_revision='2026-10-22-m11-reference')
  self.d['map']['tiles']=[IDS[ch]for row in self.g for ch in row]
  allowed={'art_atlas','logic_grid','art_layers','natural_props','art_modules','map','tactical_routes','tactical_review_version','art_style_version','landscape_revision','tactical_notes'}
  for k in self.old:
   if k not in allowed:assert self.d[k]==self.old[k],(c,'changed story field',k)
  report=self.check();write(R/f'data/stages/{c}.json',self.d);write(OUT/f'{c}-geometry.json',report);return report
 def check(self):
  start=tuple(self.d['player_positions'][0]);seen={start};q=deque([start])
  while q:
   x,y=q.popleft()
   for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]:
    xx,yy=x+dx,y+dy
    if 0<=xx<self.w and 0<=yy<self.h and(xx,yy)not in seen and self.g[yy][xx]not in'#^~':seen.add((xx,yy));q.append((xx,yy))
  assert self.fixed<=seen,(self.code,'unreachable',sorted(self.fixed-seen))
  assert all(IDS[self.g[y][x]]==IDS[self.old['logic_grid'][y][x]]for x,y in self.fixed),(self.code,'anchor terrain category')
  return {'code':self.code,'passed':True,'connected_cells':len(seen),'checked_anchors':len(self.fixed),'story_and_actor_fields_unchanged':True,'anchor_terrain_categories_unchanged':True,'changed_cells':sum(a!=b for a,b in zip(''.join(self.d['logic_grid']),''.join(self.old['logic_grid']))),'natural_props':len(self.trees),'new_modules':self.added,'routes':self.routes}
if __name__=='__main__':
 reports=[Field(c).build()for c in ['M51','M52','F51','F52','S51','J53','J54']];ATLAS.save();write(OUT/'geometry-summary.json',{'passed':True,'maps':reports});print(json.dumps({'passed':True,'maps':len(reports),'changed_cells':sum(r['changed_cells']for r in reports)},ensure_ascii=False))
