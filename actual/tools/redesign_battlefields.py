#!/usr/bin/env python3
"""Authored fifteen-map geography revision; idempotent from frozen 0.2.1 cards.

Reuses original terrain rules and unit statistics. Geometry, deployments and
landmarks are designed per location, rather than enlarging a painted backdrop.
"""
from pathlib import Path
from collections import deque, Counter
import copy, hashlib, importlib.util, itertools, json, math, random, subprocess
from PIL import Image

R=Path(__file__).resolve().parents[1]
VERSION='0.3.0'
BACK=R/'data/compat/0.2.1'
OUT=R/'reports/battlefield-0.3.0'
ART=R/'assets/battlefield-0.3.0'
PACK=json.loads((R/'assets/battle_tiles/battle-tiles.json').read_text())
SEA=json.loads((R/'assets/chapter2/chapter2-tiles.json').read_text())
NATURE={s['key']:s for s in json.loads((R/'assets/nature/nature.json').read_text())['sprites']}
MODULES={m['name']:dict(m,path='res://assets/battle_tiles/modules/'+m['name']+'.png') for m in PACK['modules']}
MODULES.update({m['name']:m for m in SEA['modules']})
MODULES.update({m['name']:m for m in json.loads((ART/'modules.json').read_text())['modules']})
IDS={'.':48,'p':48,'n':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'c':208,'s':191,'b':66,'+':218,'h':208,'t':218}
MATERIAL={'.':'grass','p':'dirt','n':'snow','f':'forest','^':'rock','d':'sand','~':'sea','#':'rock','=':'stone','c':'cobble','s':'timber','b':'marsh','+':'sacred','h':'grass','t':'grass'}
SIZES={'M11':(36,28),'M12':(36,28),'M13':(40,30),'M14':(40,32),'M15':(44,34),'S11':(32,26),'S12':(34,26),'F21':(44,30),'F22':(46,32),'F23':(38,30),'F24':(40,32),'F25':(44,34),'F26':(44,32),'S21':(36,28),'S22':(32,28)}
THEMES={
 'M11':'雪原林谷、融雪溪流、林间护送岔路', 'M12':'坡地粮仓、土质车辙、木栅前庭',
 'M13':'南岗崖边押送院、两处囚区和外侧土路', 'M14':'旧瞭望塔、林间军帐和木栅营盘',
 'M15':'扼守海峡的旧塔堡、海蚀断崖、堡门与港侧迂回', 'S11':'支木矿口、运矿岔道和狭窄岩室',
 'S12':'林村诊所、溪桥和绕林药车道', 'F21':'大型双舰、上下登舰口、桅杆与货舱间的集结甲板',
 'F22':'宽舰囚舱、两条登船路线与独立撤离甲板', 'F23':'礁岩登陆滩、渔村营地和草坡',
 'F24':'黑昼灯塔、岛民住屋、海岸高地和守灯岔口', 'F25':'海湾军港、木码头、仓储区和沿岸通路',
 'F26':'断裂海堤、古石拱、木架支路和平行居民航道', 'S21':'漂泊渔船群、病人甲板和两处窄跳板',
 'S22':'潮汐海洞、多岩室、浅滩和绕行岩脊'}

def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def seed(s):return int(hashlib.sha256(str(s).encode()).hexdigest()[:12],16)
def line(a,b):
 x,y=a;result=[(x,y)]
 while (x,y)!=tuple(b):
  if x!=b[0]:x+=1 if b[0]>x else -1
  elif y!=b[1]:y+=1 if b[1]>y else -1
  result.append((x,y))
 return result
def route(points):
 out=[]
 for a,b in zip(points,points[1:]):
  for p in line(a,b):
   if not out or p!=out[-1]:out.append(p)
 return out
def mask_at(grid,x,y,predicate):
 peers=[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8),(1,-1,16),(1,1,32),(-1,1,64),(-1,-1,128)]
 mask=sum(bit for dx,dy,bit in peers if 0<=y+dy<len(grid) and 0<=x+dx<len(grid[0]) and predicate(grid[y+dy][x+dx]))
 for diagonal,a,b in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
  if not (mask&a and mask&b):mask&=~diagonal
 return mask

def build_atlas():
 spec=importlib.util.spec_from_file_location('terrain_masks',R/'tools/build_world_tiles.py');wb=importlib.util.module_from_spec(spec);spec.loader.exec_module(wb)
 im=Image.open(R/'assets/chapter2/chapter2-tiles.png').convert('RGBA')
 cells=[im.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)) for i in range(SEA['tile_count'])]
 transitions={}
 for key,fg,bg in [('path','dirt','grass'),('snow_path','dirt','snow'),('timber_coast','timber','sea'),('rock_coast','rock','sea'),('stone_grass','stone','grass'),('snow_coast','snow','sea'),('dirt_coast','dirt','sea')]:
  transitions[key]={}
  for mask in wb.MASKS:
   ids=[]
   for variant in range(4):
    tile=cells[PACK['base'][bg][variant]].copy();fore=cells[PACK['base'][fg][variant]].copy();fore.putalpha(wb.alpha_mask(mask));tile.alpha_composite(fore)
    ids.append(len(cells));cells.append(tile)
   transitions[key][str(mask)]=ids
 # River banks are drawn inside water cells. The older land-over-water mask
 # leaked blue pixels into walkable roads and left isolated corner fragments.
 # w = water/bridge, n = snowy land, p = earth; N/E/S/W edges are explicit.
 transitions['winter_river']={}
 for edges in itertools.product('wnp',repeat=4):
  key=''.join(edges);ids=[]
  for variant in range(4):
   tile=cells[PACK['base']['sea'][variant]].copy()
   for side,edge in enumerate(edges):
    if edge=='w':continue
    bank=cells[PACK['base']['snow' if edge=='n' else 'dirt'][variant]]
    for span in range(16):
     for depth in range(2):
      px,py=[(span,depth),(15-depth,span),(span,15-depth),(depth,span)][side]
      tile.putpixel((px,py),bank.getpixel((px,py)))
   ids.append(len(cells));cells.append(tile)
  transitions['winter_river'][key]=ids
 # The former rock-face texture was violet and was also selected by collision
 # cells. Reuse native gravel detail in the warm grey of the existing crags;
 # append IDs so old compatible maps still address their original artwork.
 mountain=[]
 for variant in range(4):
  tile=cells[PACK['base']['cave'][variant]].copy()
  for y in range(16):
   for x in range(16):
    r,g,b,a=tile.getpixel((x,y));light=.2126*r+.7152*g+.0722*b
    tile.putpixel((x,y),(round(.88*light+23),round(.86*light+25),round(.74*light+25),a))
  mountain.append(tile)
 transitions['mountain_ground']={}
 for background in ['grass','cave','sea']:
  family={}
  for mask in wb.MASKS:
   ids=[]
   for variant in range(4):
    tile=cells[PACK['base'][background][variant]].copy();fore=mountain[variant].copy()
    fore.putalpha(wb.alpha_mask(mask));tile.alpha_composite(fore)
    ids.append(len(cells));cells.append(tile)
   family[str(mask)]=ids
  transitions['mountain_ground'][background]=family
 # New families append after all shipped IDs. Beaches are authored sand
 # terrain, never an automatic replacement for any land beside water.
 for key,fg,bg in [('beach_grass','sand','grass'),('path_sand','dirt','sand')]:
  transitions[key]={}
  for mask in wb.MASKS:
   ids=[]
   for variant in range(4):
    tile=cells[PACK['base'][bg][variant]].copy();fore=cells[PACK['base'][fg][variant]].copy();alpha=wb.alpha_mask(mask)
    # Pixel stippling softens the biome edge without blurring tile detail.
    original=alpha.copy()
    bayer=[[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]
    for yy in range(16):
     for xx in range(16):
      if not original.getpixel((xx,yy)):continue
      if key=='beach_grass':
       distance=min([abs(dx)+abs(dy) for dy in range(-3,4) for dx in range(-3,4) if abs(dx)+abs(dy)<=3 and 0<=xx+dx<16 and 0<=yy+dy<16 and not original.getpixel((xx+dx,yy+dy))] or [4])
       if bayer[(yy+variant)%4][(xx+variant*2)%4]>=distance*4:alpha.putpixel((xx,yy),0)
      elif 0<xx<15 and 0<yy<15 and any(not original.getpixel((xx+dx,yy+dy)) for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]) and (xx*7+yy*11+variant)%4==0:alpha.putpixel((xx,yy),0)
    fore.putalpha(alpha);tile.alpha_composite(fore);ids.append(len(cells));cells.append(tile)
   transitions[key][str(mask)]=ids
 transitions['walkway']={}
 for axis in ['h','v']:
  for mask in range(16):
   ids=[]
   for variant in range(4):
    tile=cells[PACK['base']['timber'][variant]].copy()
    if axis=='h':tile=tile.transpose(Image.Transpose.ROTATE_90)
    for side,bit in enumerate([1,2,4,8]):
     if mask&bit:continue
     for span in range(16):
      for depth in range(2):
       px,py=[(span,depth),(15-depth,span),(span,15-depth),(depth,span)][side]
       tile.putpixel((px,py),(68,54,40,255) if depth==0 else (145,119,82,255))
    # Low beam ends stay within the walkable tile; these are not railings.
    for a,b,px,py in [(1,8,1,1),(1,2,14,1),(4,2,14,14),(4,8,1,14)]:
     if not mask&a and not mask&b:tile.putpixel((px,py),(49,40,31,255))
    ids.append(len(cells));cells.append(tile)
   transitions['walkway'][axis+str(mask)]=ids
 transitions['shore_water']={}
 atlas={'cells':cells,'transitions':transitions,'mountain':mountain}
 previous=ART/'terrain.json'
 if previous.exists():
  old=json.loads(previous.read_text()).get('transitions',{}).get('shore_water',{})
  if old:
   assert min(t for ids in old.values() for t in ids)==len(cells),'Keep published shore IDs fixed; append future families after the shore catalog'
   for key,ids in sorted(old.items(),key=lambda item:min(item[1])):
    shore_tile(atlas,list(key),0)
    assert transitions['shore_water'][key]==ids,'Published shore ID changed'
 return atlas

def save_atlas(atlas):
 cells=atlas['cells'];transitions=atlas['transitions']
 atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
 for i,tile in enumerate(cells):atlas.alpha_composite(tile,(i%32*16,i//32*16))
 atlas.save(ART/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(ART/'terrain.png')],check=True)
 write(ART/'terrain.json',{'tile_size':16,'columns':32,'tile_count':len(cells),'original_ids_preserved':True,'transitions':transitions,'coasts':SEA['coasts'],'source':'Existing approved native tiles and exact matching corner masks; no rescaling.'})

def shore_tile(atlas,neighbours,variant):
 """Draw the bank INSIDE a water cell; never paint sea/sand onto land.

 N/E/S/W and four diagonals carry their actual neighbouring material. Cache
 only combinations used by maps, avoiding thousands of unused atlas cells.
 """
 key=''.join(neighbours);family=atlas['transitions']['shore_water'];cells=atlas['cells']
 if key not in family:
  ids=[];materials={'g':'grass','a':'sand','p':'dirt','c':'cobble','v':'cave','t':'timber','n':'snow'}
  for v in range(4):
   tile=cells[PACK['base']['sea'][v]].copy()
   def bank_pixel(px,py,material,depth):
    land=atlas['mountain'][v] if material=='r' else cells[PACK['base'][materials[material]][v]]
    rgb=land.getpixel((px,py))[:3]
    # A narrow shaded bank/wet-sand rim, rather than a whole fake beach tile.
    shade=.9 if material=='a' else .8 if depth==1 else 1
    tile.putpixel((px,py),tuple(round(c*shade) for c in rgb)+(255,))
   for side,material in enumerate(neighbours[:4]):
    if material=='w':continue
    for span in range(16):
     for depth in range(2):
      px,py=[(span,depth),(15-depth,span),(span,15-depth),(depth,span)][side]
      bank_pixel(px,py,material,depth)
   for material,(cx,cy,sx,sy) in zip(neighbours[4:],[(15,0,-1,1),(15,15,-1,-1),(0,15,1,-1),(0,0,1,1)]):
    if material=='w':continue
    for dy in range(3):
     for dx in range(3):
      if dx+dy<=2:bank_pixel(cx+sx*dx,cy+sy*dy,material,1 if dx+dy==2 else 0)
   ids.append(len(cells));cells.append(tile)
  family[key]=ids
 return family[key][variant]

class Battlefield:
 def __init__(self,code):
  self.code=code;self.old=json.loads((BACK/f'{code}.json').read_text());self.d=copy.deepcopy(self.old);self.w,self.h=SIZES[code];self.rng=random.Random(seed(code))
  self.grid=[['~' if code in ['M15','F21','F22','F23','F24','F25','F26','S21'] else '^' if code in ['S11','S22'] else 'n' if code=='M11' else '.']*self.w for _ in range(self.h)]
  self.modules=[];self.props=[];self.nature=[];self.reserved=set();self.occupied=set();self.routes=[];self.corridors=set();self.underlay={};self.sites=[];self.visits=[];self.visit_types=set()
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):self.grid[y][x]=ch
 def ellipse(self,cx,cy,rx,ry,ch,only=None):
  for y in range(max(0,int(cy-ry-1)),min(self.h,int(cy+ry+2))):
   for x in range(max(0,int(cx-rx-1)),min(self.w,int(cx+rx+2))):
    irregular=1+.065*math.sin(x*.9+y*.5)+.055*math.cos(y*1.2-x*.2)
    if ((x-cx)/rx)**2+((y-cy)/ry)**2<irregular and (only is None or self.grid[y][x] in only):self.grid[y][x]=ch
 def path(self,points,width=2,ch='p',name=None):
  cells=route(points)
  for x,y in cells:self.rect(x-width//2,y-width//2,x+(width-1)//2,y+(width-1)//2,ch)
  if name:
   self.routes.append({'name':name,'waypoints':[list(p) for p in points],'width':width,'surface':ch})
   for x,y in cells:
    self.corridors.update((xx,yy) for yy in range(y-width//2,y+(width-1)//2+1) for xx in range(x-width//2,x+(width-1)//2+1))
 def anchors(self,deploy,exit_,targets,npcs=None):
  self.d['player_positions']=[[deploy[0]+i%4,deploy[1]+i//4] for i in range(10)]
  self.d['exit']=list(exit_);self.d['targets']=[list(p) for p in targets]
  for i,o in enumerate(self.d['objects']):
   o['position']=list(targets[min(i,len(targets)-1)])
   for k in ['opens','open_art_cells','open_art_props']:o.pop(k,None)
  if npcs:
   for u,p in zip(self.d['npc_units'],npcs):u['position']=list(p)
  for key in ['enemies','reinforcements']:
   for u in self.d[key]:
    x,y=u['position'];u['position']=[round(3+(x-2)*(self.w-6)/(self.old['map']['width']-6)),round(3+(y-2)*(self.h-6)/(self.old['map']['height']-6))]
  # The first wave is separated from deployment; stronger/remote defenders
  # still occupy their authored front lines instead of all charging at once.
  points=self.d['player_positions']+[self.d['exit']]+self.d['targets']+[u['position'] for u in self.d['npc_units']]
  self.reserved={tuple(p) for p in points}
 def site(self,name,x,y,label,fort=False):
  if (x,y) in self.reserved or (x,y) in self.occupied or not (1<=x<self.w-1 and 1<=y<self.h-1):return False
  if self.grid[y][x] in '~^#':return False
  m=MODULES[name];self.underlay[x,y]=self.grid[y][x];self.grid[y][x]='t' if fort else 'h'
  self.occupied.add((x,y));self.props.append({'path':m['path'],'position':[x*16,y*16]})
  self.modules.append({'name':name,'origin':[x,y],'footprint':[1,1],'logic':'occupiable','cells':[[x,y]],'runtime_prop':True,'purpose':label})
  self.sites.append({'position':[x,y],'label':label,'occupiable':True,'avoid':40 if fort else 20,'phase_heal':5 if fort else 0})
  return True
 def stamp(self,name,x,y,solid=True,purpose='',force=False):
  # Buildings are tactical single-cell terrain by default. Only the first named
  # landmark at an authored location becomes a modest, front-door visit site.
  ordinary={'snow_cottage':('tactical_snow_house','雪原民居',False),'hill_granary':('tactical_store','粮仓',False),
   'barracks':('tactical_fort','营垒',True),'ruined_watchtower':('tactical_fort','旧哨堡',True),
   'command_pavilion':('tactical_tent','军帐',False),'fishing_cottage':('tactical_house','渔舍',False),
   'village_clinic':('tactical_house','村舍',False),'captain_cabin':('tactical_deck_post','舵楼哨位',True),
   'quay_warehouse':('tactical_store','港仓',False)}
  visit_key={'M11':'snow_cottage','M12':'hill_granary','M13':'command_pavilion','M14':'command_pavilion',
   'M15':'coastal_keep','S11':'mine_adit','S12':'village_clinic','F21':'captain_cabin','F22':'captain_cabin',
   'F23':'fishing_cottage','F24':'lighthouse','F25':'quay_warehouse','S21':'captain_cabin','S22':'cave_entry'}.get(self.code)
  visit=name==visit_key and name not in self.visit_types
  if name in ordinary and not visit:
   icon,label,fort=ordinary[name];return self.site(icon,x,y,label,fort)
  if name=='lighthouse':name='visit_lighthouse'

  m=MODULES[name];w,h=m['footprint'];cells={(xx,yy) for yy in range(y,y+h) for xx in range(x,x+w)}
  passage={(xx,yy) for yy in range(y,y+h) for xx in [x+w//2-1,x+w//2]} if name in ['sea_gate','ancient_arch'] else set()
  if x<1 or y<1 or x+w>=self.w or y+h>=self.h or cells&self.reserved or cells&self.occupied or (solid and (cells-passage)&self.corridors):return False
  if not force and any(self.grid[yy][xx] in '~^' for xx,yy in cells):return False
  if solid:
   for xx,yy in cells-passage:self.underlay[xx,yy]=self.grid[yy][xx];self.grid[yy][xx]='#'
  self.occupied|=cells
  self.modules.append({'name':name,'origin':[x,y],'footprint':[w,h],'logic':'#' if solid else 'inherits_ground','cells':[list(p) for p in sorted(cells-passage)],'walk_through_cells':[list(p) for p in sorted(passage)],'runtime_prop':True,'purpose':purpose})
  self.props.append({'path':m['path'],'position':[x*16,y*16]})
  if visit:
   self.visit_types.add(visit_key)
   door=[x+w//2,y+h-1];approach=[door[0],door[1]+1]
   self.grid[approach[1]][approach[0]]='s' if self.code in ['F21','F22','S21'] else 'p'
   self.reserved.add(tuple(approach))
   # Native art already contains its doorway. Odd-width buildings align with
   # one grid column; an entrance straddling the central seam can use two
   # clear front squares. Do not clear forests or alter movement terrain.
   fronts=[approach]
   if w%2==0:
    other=[x+w//2-1,y+h]
    if self.grid[other[1]][other[0]] in '.npdsch=+' and tuple(other) not in self.occupied:
     fronts.append(other);self.reserved.add(tuple(other))
   entrances=[[p[0],p[1]-1] for p in fronts]
   titles={'snow_cottage':'雪原村舍','hill_granary':'仓吏小屋','command_pavilion':'营地文书帐',
    'coastal_keep':'旧塔堡档案室','mine_adit':'矿口工具间','village_clinic':'林村诊所',
    'captain_cabin':'船员休息舱','fishing_cottage':'渔家小屋','lighthouse':'守灯人小屋',
    'quay_warehouse':'港仓账房','cave_entry':'洞口避潮室'}
   lines={
    'M11':'村民：雪桥两头的树林可以掩护伤员。绕林的小路通向村北，别让护送者落单。',
    'M12':'仓吏：土路是粮车留下的。西坡能绕到仓后，营垒可以占住防守；焚毁兵已经在集结。',
    'M13':'记录员：两处囚门各关着一队劳工。把两处都打开，再替他们清出撤离的路。',
    'M14':'文书：旧哨堡还能守人，军帐只能提供掩护。把两个控制点都拿下，别只追着长官打。',
    'M15':'旧记录：这里原是扼守海峡的三塔要塞。东面栈道通往北门，西崖缺口可绕过中庭。',
    'S11':'矿工：工具留在这里，先救人。东边支巷绕过岩室，伤员走主巷撤离更稳妥。',
    'S12':'医师：药车从溪桥过来。林地能掩护护送者，诊所前的小路通向村北。',
    'F21':'船员：两条跳板都能登舰。舵楼哨位可守可恢复，别把所有人挤在一条跳板上。',
    'F22':'船员：总闸在敌舰中部，备用跳板有独立绞盘。先清出撤离通道，再开囚舱。',
    'F23':'渔民：营地在登陆滩后方。西侧草坡可以绕行，但别让敌人冲到留守者身边。',
    'F24':'守灯人：石台正对航灯，东岸能绕到后方。夺回灯台后，还要防住下一轮争夺。',
    'F25':'账房：仓库之间是土质车道，沿岸木码头可绕行。牢区外侧另有一条窄路。',
    'S21':'船员：先让病人远离跳板。舵楼哨位可轮换伤员，清出甲板后再护送。',
    'S22':'洞民：潮水隔开几间岩室，支巷会绕回主路。别在入口挤作一团。'}
   reward={'M11':48,'M12':48,'S11':2,'S12':48,'F21':48,'F22':48,'F23':11,'F25':20,'S21':48}.get(self.code,0)
   self.visits.append({'id':self.code+'_visit_'+str(len(self.visits)),'kind':'visit','label':'访问'+titles[visit_key],
    'position':door,'approach':approach,'approaches':fronts,'entrance_cells':entrances,'adjacent':True,
    'door_visual':'native_building_art','show_indicator':False,
    'optional':True,'dialogue':lines[self.code],'reward_item':reward,'building':name})
  return True
 def wall(self,points,gaps=(),fence=False):
  for x,y in points:
   name='north_fence' if fence else 'north_wall'
   cells={(x+i,y) for i in range(4)}
   if not any(p in cells for p in gaps):self.stamp(name,x,y,purpose='Continuous defensive wall with authored entrances')
 def terrain(self):
  c=self.code;w=self.w;h=self.h
  if c=='M11':
   for p in [(6,8,7,8),(27,21,8,7),(29,6,6,4),(8,23,5,4),(18,5,4,3)]:self.ellipse(*p,'f')
   self.path([(5,25),(11,25),(11,20),(18,20),(18,13),(25,13),(25,5),(30,5),(30,3)],3,'p','林间护送主路')
   self.path([(11,22),(6,22),(6,17),(16,17),(16,8),(19,8),(19,5),(25,5)],2,'p','溪谷侧路')
   river_points=[(0,14),(12,14),(12,11),(22,11),(22,8),(35,8)]
   # Preserve the full channel first; only authored bridges may cover it.
   self.path(river_points,2,'~')
   channel=[[x,y] for y,row in enumerate(self.grid) for x,ch in enumerate(row) if ch=='~']
   bridges=[{'id':'west_bridge','bounds':[15,9,16,12],'width':2},
            {'id':'east_bridge','bounds':[24,6,26,9],'width':3}]
   for bridge in bridges:self.rect(*bridge['bounds'],'s')
   self.d['river_layout']={'channel':channel,'waypoints':[list(p) for p in river_points],'bridges':bridges,'shore_rendering':'inside_water_cells','revision':'0.3.1'}
   self.anchors((4,23),(30,3),[(18,18),(25,13)],[(8,21),(15,20)])
   self.stamp('snow_cottage',28,2,purpose='Refugee destination village')
   self.stamp('snow_cottage',31,4);self.stamp('snow_cottage',23,2)
  elif c=='M12':
   for p in [(4,6,6,7),(30,23,6,6),(18,3,5,3)]:self.ellipse(*p,'^')
   for p in [(6,15,5,4),(27,16,4,3)]:self.ellipse(*p,'f',only='.')
   self.path([(5,25),(10,25),(10,19),(17,19),(17,13),(25,13),(25,8),(29,8)],3,'p','粮车坡道')
   self.path([(10,20),(8,20),(8,11),(15,11),(15,7),(25,7)],2,'p','西坡包抄路')
   self.ellipse(26,8,7,5,'p',only='.^');self.rect(23,6,28,9,'c')
   self.anchors((4,23),(31,3),[(28,8),(19,14)],[(8,21)])
   for at in [(22,2),(29,4),(18,6)]:self.stamp('hill_granary',*at,force=True,purpose='Grain stores beside the wagon approach')
   self.stamp('grain_wagon',17,16);self.stamp('grain_sacks',24,11);self.stamp('grain_sacks',28,11)
   self.wall([(15,12),(23,12),(28,12)],gaps=[(21,12)],fence=True)
   self.d['burner_departure_turn']=7
   self.d['ai_and_timing']='坡道扩大后第6回合预告、第7回合焚毁兵出发。连续两次在仓门确认焚毁才失败；可提前占门或沿西坡拦截。'
  elif c=='M13':
   self.ellipse(2,13,4,18,'^');self.ellipse(37,4,4,6,'^');self.ellipse(34,27,7,5,'f')
   self.path([(5,27),(11,27),(11,20),(20,20),(20,12),(30,12),(30,7),(35,7)],3,'p','押送院主通道')
   self.path([(11,22),(6,22),(6,12),(10,12),(10,8)],2,'p','西囚区缺口')
   self.path([(20,23),(35,23),(35,12),(35,5)],2,'p','东侧外廊')
   self.rect(5,4,13,9,'p');self.rect(28,5,36,10,'p');self.rect(18,6,24,10,'c')
   self.anchors((4,25),(35,3),[(10,8),(33,10)],[(10,7),(33,9),(12,7)])
   self.wall([(5,11),(12,11),(22,11),(28,11)],gaps=[(10,11),(20,11),(35,11)])
   self.stamp('command_pavilion',19,3)
   for x,y,label in [(7,6,'西囚区岗堡'),(31,6,'东囚区岗堡'),(24,8,'内庭岗堡')]:
    assert self.site('tactical_fort',x,y,label,True)
   self.stamp('crates',14,18);self.stamp('grain_wagon',28,20)
  elif c=='M14':
   self.ellipse(4,8,5,9,'^');self.ellipse(33,4,7,5,'^')
   for p in [(9,16,7,5),(29,24,8,6),(21,4,6,3),(35,14,4,5)]:self.ellipse(*p,'f',only='.')
   self.path([(5,29),(12,29),(12,23),(20,23),(20,16),(28,16),(28,9),(33,9)],3,'p','外营车道')
   self.path([(12,24),(7,24),(7,12),(16,12),(16,8),(28,8)],2,'p','林间绕营路')
   self.path([(22,23),(34,23),(34,8),(35,8),(35,3)],2,'p','东侧哨路')
   self.anchors((4,27),(35,3),[(20,18),(34,20)])
   self.stamp('ruined_watchtower',14,8,force=True,purpose='Old lookout guarding the western loop')
   for at in [(24,3),(19,9),(28,24)]:self.stamp('command_pavilion',*at,purpose='Tents along the camp approach')
   # Each line frames an actual road opening. The former spare fence was
   # isolated in a grove and one control marker did not touch any road.
   gates=[{'id':'south_checkpoint','name':'南营哨卡','row':18,'opening':[[19,18],[20,18],[21,18]],'fences':[[16,18],[22,18]]},
          {'id':'east_checkpoint','name':'东营哨卡','row':20,'opening':[[33,20],[34,20]],'fences':[[30,20],[35,20]]}]
   for gate,obj in zip(gates,self.d['objects']):
    for x,y in gate['fences']:assert self.stamp('camp_palisade',x,y,force=True,purpose=gate['name']+'道路两侧拒止木栅')
    obj.update(name_zh=gate['name'],label='控制'+gate['name'],sprite='white_flag',persistent_visual=True,show_indicator=False)
   self.d['camp_checkpoints']=gates
   self.d['goal']='击败守将或接受其投降，并站到南营、东营两处军旗格，选择控制哨卡。'
   self.stamp('grain_wagon',16,23)
  elif c=='M15':
   self.ellipse(20,18,20,19,'.');self.rect(4,9,37,29,'.');self.ellipse(5,6,5,5,'^',only='.')
   self.rect(8,3,38,9,'.');self.rect(39,2,43,31,'~')
   for p in [(14,11,4,3),(14,29,5,3),(30,29,4,3)]:self.ellipse(*p,'f',only='.')
   self.path([(5,31),(12,31),(12,25),(21,25),(21,18),(24,18),(24,10),(37,10),(37,5)],3,'p','旧堡正面推进路')
   self.path([(12,26),(6,26),(6,15),(10,15),(10,9)],2,'p','西侧崖脚缺口')
   self.path([(22,27),(36,27),(36,18),(37,18),(37,5)],2,'s','港侧迂回栈道')
   self.rect(20,9,29,13,'c');self.rect(19,16,26,19,'c')
   self.anchors((4,29),(38,5),[(9,9),(32,26)],[(9,8),(32,25)])
   assert self.stamp('coastal_keep',17,1,force=True,purpose='Three unequal weathered towers dominate the strait fortress')
   self.stamp('ruined_watchtower',8,11,force=True);self.stamp('sea_gate',28,2,force=True)
   self.wall([(9,18),(14,18),(27,18),(32,18)],gaps=[(21,18)])
   for at in [(1,19),(39,12)]:self.stamp('sea_cliff',*at,force=True,purpose='Strait-facing sea cliffs')
   self.stamp('breached_wall',8,12,force=True);self.stamp('quay_warehouse',34,22)
   self.d['surroundings']='sea';self.d['assault_gate']=[21,20]
  elif c=='S11':
   for p in [(8,20,7,5),(11,13,6,5),(22,8,8,6),(21,19,6,4)]:self.ellipse(*p,'p')
   self.path([(5,23),(10,23),(10,16),(18,16),(18,9),(26,9),(26,4)],3,'p','运矿主巷')
   self.path([(10,19),(23,19),(23,12),(19,12)],2,'p','支巷绕岩路')
   self.anchors((4,21),(26,3),[(17,14),(24,17)],[(8,20),(14,18),(10,20)])
   self.stamp('mine_adit',18,1,force=True,purpose='Timber-braced mine mouth')
   self.stamp('crates',12,11);self.stamp('grain_wagon',25,20)
  elif c=='S12':
   for p in [(5,8,6,8),(20,21,7,5),(29,15,5,5),(16,3,5,4)]:self.ellipse(*p,'f')
   self.path([(0,13),(12,13),(12,10),(23,10),(23,7),(33,7)],2,'~')
   self.path([(5,23),(10,23),(10,18),(17,18),(17,11),(24,11),(24,6),(29,6)],3,'p','药车主路')
   self.path([(10,20),(5,20),(5,15),(14,15),(14,8),(24,8)],2,'p','林地步行支路')
   self.rect(16,9,18,14,'s')
   self.anchors((4,21),(29,3),[(27,6),(21,15)],[(11,18),(8,21)])
   self.stamp('village_clinic',25,1,purpose='Clinic and visible destination forecourt');self.stamp('fishing_cottage',22,12)
  elif c in ['F21','F22','S21']:
   if c=='F21':hulls=[(2,19,2,27),(24,41,2,27)];lanes=[11,20]
   elif c=='F22':hulls=[(2,19,2,29),(25,43,2,29)];lanes=[12,23]
   else:hulls=[(2,15,4,25),(20,33,2,24)];lanes=[13,21]
   for x0,x1,y0,y1 in hulls:
    self.rect(x0+1,y0,x1-1,y1,'s');self.rect(x0,y0+3,x1,y1-2,'s');self.rect(x0+3,y0-1,x1-3,y0,'s')
   for y in lanes:self.path([(hulls[0][1]-1,y),(hulls[1][0]+1,y)],2,'s','上跳板' if y==lanes[0] else '下跳板')
   if c=='F21':self.anchors((5,24),(37,4),[(21,11),(21,20)],[(8,26),(17,22)])
   elif c=='F22':self.anchors((5,26),(18,23),[(29,17),(39,21)],[(34,8),(35,8),(34,21),(35,21)])
   else:self.anchors((5,22),(6,25),[(17,13),(17,21)],[(10,24),(22,23)])
   for i,(x0,x1,y0,y1) in enumerate(hulls):
    self.stamp('bow',(x0+x1)//2-1,y0-1,False,force=True)
    self.stamp('stern',(x0+x1)//2-1,y1-1,False,force=True)
    for y in range(y0+3,y1-3,4):
     if not any(y<=lane<y+4 for lane in lanes):
      for x in [x0,x1]:self.stamp('rail_v',x,y,purpose='Solid hull rails',force=True)
    self.stamp('captain_cabin',x0+3,y1-5 if i==0 else y0+2,purpose='Deck cabin beside the embarkation area',force=True)
    self.stamp('mast',x0+5,y0+7,purpose='Mast divides deck manoeuvring lanes',force=True)
    if c!='S21':
     self.stamp('mast',x0+10,y1-10,purpose='Aft rigging leaves two walk-around lanes',force=True)
     self.stamp('hatch',x0+3,y0+14,purpose='Lower cargo hatch',force=True)
     self.stamp('grain_wagon',x0+9,y0+14,purpose='Secured cargo cluster',force=True)
     self.stamp('grain_sacks',x0+9,y0+16,force=True)
    for x in [x0+1,x0+5,x0+9,x1-4]:
     self.stamp('rail_h',x,y0,force=True,purpose='Foredeck gunwale')
     self.stamp('rail_h',x,y1,force=True,purpose='Stern gunwale')
    self.stamp('hatch',x0+9,y1-6,purpose='Cargo hatch',force=True)
    for x,y in [(x0+2,y0+9),(x1-3,y0+5),(x0+3,y1-5),(x1-2,y1-4)]:self.stamp('crates' if (x+y)%2 else 'grain_sacks',x,y)
   if c=='F22':
    # Two real enclosed holds; the gate lever opens both actual doorway cells.
    gates=[]
    for y in [7,20]:
     self.rect(32,y,38,y+3,'#');self.rect(33,y+1,37,y+2,'s')
     for x,yy,name in [(32,y,'jail_bars_h'),(35,y,'jail_bars_h'),(32,y+3,'jail_bars_h'),(35,y+3,'jail_bars_h'),(32,y,'jail_bars_v'),(38,y,'jail_bars_v')]:
      self.props.append({'path':MODULES[name]['path'],'position':[x*16,yy*16]})
     gates.append([36,y+3])
    door,bridge=self.d['objects'];door.update(opens=[door['position']]+gates,sprite_path=MODULES['jail_door']['path'],open_sprite_path=MODULES['open_jail']['path'],open_tile=191,open_art_cells=[{'position':p,'base_tile':PACK['base']['timber'][0],'clear_layers':[1,2]} for p in gates])
    cells=[[x,23] for x in range(20,25)];self.rect(20,23,24,23,'~');bridge.update(opens=cells,open_tile=191,open_art_cells=[{'position':p,'base_tile':PACK['base']['timber'][0],'clear_layers':[1,2]} for p in cells],sprite_path=MODULES['bollard']['path'])
    # A single upper boarding lane starts open; the lower lane is visibly water.
    self.rect(20,22,24,22,'~')
    self.d['detention_bays']={'gates':gates,'main_aisle_columns':[40,41,42],'main_aisle_rows':[3,28],'unlock_control':door['position']}
   self.d['surroundings']='sea'
   if c in ['F21','F22']:
    self.rect(8,22,9,22,'+')
    self.stamp('medicine_wagon',6,21,purpose='Ship infirmary beside the existing recovery terrain')
    if c=='F22':
     for x,y in [(26,14),(28,12),(37,16)]:self.site('tactical_deck_post',x,y,'甲板掩体',True)
    self.d['tactical_notes']=['大甲板与双登舰口可分队推进。己船医药区的浅色恢复格沿用原地形恢复规则，可轮换伤员后再攻舰长。']
  elif c in ['F23','F24']:
   self.ellipse(w/2,h/2,w/2-2,h/2-2,'.')
   for y in range(h):
    for x in range(w):
     if self.grid[y][x]=='.' and any(not(0<=x+dx<w and 0<=y+dy<h) or self.grid[y+dy][x+dx]=='~' for dx,dy in [(2,0),(-2,0),(0,2),(0,-2)]):self.grid[y][x]='d'
   self.ellipse(7,8,5,7,'^',only='.d');self.ellipse(w-5,h-8,4,4,'^',only='.d')
   for p in [(17,6,6,3),(13,18,4,4),(28,17,4,4)]:self.ellipse(*p,'f',only='.')
   main=[(6,h-4),(12,h-4),(12,20),(19,20),(19,13),(28,13),(28,6),(w-6,6),(w-6,3)] if c=='F23' else [(6,h-4),(12,h-4),(12,20),(19,20),(19,18),(23,18),(23,17)]
   self.path(main,3,'p','海岛主路')
   self.path([(12,22),(6,22),(6,15),(15,15),(15,8),(28,8)],2,'p','西侧草坡支路')
   self.path([(20,23),(32,23),(32,9),(w-6,9),(w-6,3)],2,'p','东岸绕行路')
   if c=='F23':
    self.anchors((5,25),(32,3),[(18,18),(28,20)],[(10,23),(13,25)])
    self.stamp('fishing_cottage',19,20);self.stamp('fishing_cottage',25,15);self.stamp('sea_cliff',3,8,force=True)
   else:
    self.anchors((11,26),(34,3),[(23,17),(32,23)],[(15,25),(22,20)])
    assert self.stamp('lighthouse',21,10,force=True,purpose='Black-day navigation tower')
    self.rect(21,15,25,18,'c');self.stamp('village_clinic',27,24);self.stamp('fishing_cottage',8,16)
    shelter=next(o for o in self.d['objects'] if o['id']=='shelter')
    sx,sy=shelter['position']
    shelter.update(sprite='tactical_house',sprite_path=MODULES['tactical_house']['path'],
     persistent_visual=True,show_indicator=False,door_visual='native_building_art',
     approaches=[[sx,sy],[sx,sy+1]],entrance_cells=[[sx,sy]])
    self.d['beacon_defense_turn']=6
   self.d['surroundings']='sea'
  elif c=='F25':
   self.ellipse(27,16,17,17,'.');self.rect(16,3,40,28,'.');self.rect(2,27,15,31,'s');self.rect(5,18,9,29,'s');self.rect(11,22,17,25,'s')
   self.path([(6,30),(15,30),(15,25),(21,25),(21,18),(29,18),(29,10),(38,10),(38,4)],3,'p','仓储区主路')
   self.path([(21,25),(40,25),(40,14),(39,14),(39,6)],3,'p','牢区外侧通道')
   self.path([(8,28),(8,22),(17,22),(17,14),(23,14),(23,7),(31,7)],2,'s','沿岸木码头')
   self.rect(27,8,32,12,'c');self.rect(22,16,27,18,'c')
   self.anchors((5,29),(39,3),[(24,17),(36,21)],[(10,28),(22,20)])
   for name,x,y in [('quay_warehouse',26,1),('hill_granary',21,10),('quay_warehouse',31,13),('command_pavilion',36,7)]:
    assert self.stamp(name,x,y,force=True,purpose='Functional harbor districts'),(c,name,x,y)
   for x,y in [(19,18),(31,22),(27,25),(16,22),(35,18)]:self.stamp('crates',x,y)
   self.d['surroundings']='sea'
  elif c=='F26':
   self.path([(5,26),(12,26),(12,21),(21,21),(21,15),(30,15),(30,9),(38,9),(38,4)],4,'c','古堤主线')
   self.path([(10,26),(25,26),(25,18),(35,18),(35,10)],2,'s','断堤木架绕行')
   for p in [(5,25,4,3),(20,18,4,4),(36,7,5,5)]:self.ellipse(*p,'p',only='~c')
   self.anchors((4,24),(39,3),[(21,15),(35,18)])
   assert self.stamp('ancient_arch',23,21,force=True,purpose='Walk-through ruin over the alternate causeway')
   self.stamp('breached_wall',10,18,force=True);self.stamp('sea_cliff',32,3,force=True)
   path=route([(5,29),(41,29),(41,5)])
   for x,y in path:self.grid[y][x]='~'
   for i,boat in enumerate(self.d['event_boats']):boat.update(path=[list(p) for p in path],position=list(path[0]),delay=4+i*4)
   self.d['surroundings']='sea'
  elif c=='S22':
   for p in [(8,22,7,5),(10,14,7,5),(22,8,8,6),(23,18,6,5)]:self.ellipse(*p,'p')
   self.path([(5,25),(10,25),(10,18),(16,18),(16,12),(25,12),(25,5)],3,'p','海洞主巷')
   self.path([(10,20),(24,20),(24,14),(18,14)],2,'p','绕岩洞室')
   self.ellipse(28,25,8,6,'~');self.ellipse(6,9,3,3,'~')
   self.anchors((4,23),(27,3),[(17,13),(24,17)],[(8,22),(15,19)])
   self.stamp('cave_entry',23,1,force=True);self.stamp('ancient_arch',19,5,force=True)
  if c in ['M13','M15']:
   for i,o in enumerate(self.d['objects']):
    x,y=o['position'];left=x-1;right=x+3 if c=='M13' and i==0 else x+1
    self.rect(left,y-2,right,y,'#');self.rect(left+1,y-1,right-1,y-1,'p')
    for xx in range(left,right+1):
     self.props.append({'path':MODULES['jail_bars_v']['path'],'position':[xx*16,(y-2)*16]}) if xx in [left,right] else None
    self.props.append({'path':MODULES['jail_bars_h']['path'],'position':[left*16,(y-2)*16]})
    if right-left>2:
     self.props.append({'path':MODULES['jail_bars_h']['path'],'position':[(right-2)*16,(y-2)*16]})
     self.props.append({'path':MODULES['jail_bars_h']['path'],'position':[(right-2)*16,y*16]})
    o.update(open_tile=48,open_art_cells=[{'position':[x,y],'base_tile':PACK['base']['dirt'][0],'clear_layers':[1,2]}])
  # Interior rock islands divide the caves into chambers. Main and side
  # corridors remain reserved, producing real choke points and flanking loops.
  if c in ['S11','S22']:
   islands=[(15,11,3,2),(18,21,3,2),(24,14,2,2)] if c=='S11' else [(16,8,3,3),(18,23,3,2),(6,16,2,3)]
   for cx,cy,rx,ry in islands:
    for yy in range(max(1,cy-ry),min(h-1,cy+ry+1)):
     for xx in range(max(1,cx-rx),min(w-1,cx+rx+1)):
      if ((xx-cx)/rx)**2+((yy-cy)/ry)**2<1.1 and (xx,yy) not in self.corridors|self.reserved|self.occupied and self.grid[yy][xx] in 'p.':self.grid[yy][xx]='^'
  # Explicit ground under production anchors; no random obstacle on a task.
  for p in self.d['player_positions']+self.d['targets']+[self.d['exit']]+[u['position'] for u in self.d['npc_units']]:
   x,y=p
   if self.grid[y][x] in '~^#':self.grid[y][x]='s' if c in ['F21','F22','S21'] else 'p'

 def timber_axis(self,x,y,ground):
  closest=[]
  for track in self.routes:
   if track['surface']!='s':continue
   for i,(a,b) in enumerate(zip(track['waypoints'],track['waypoints'][1:])):
    horizontal=a[1]==b[1]
    px=min(max(x,min(a[0],b[0])),max(a[0],b[0]));py=min(max(y,min(a[1],b[1])),max(a[1],b[1]))
    closest.append((abs(x-px)+abs(y-py),i,'h' if horizontal else 'v'))
  if closest:return min(closest)[2]
  runs=[]
  for dx,dy in [(1,0),(0,1)]:
   span=1
   for sign in [-1,1]:
    xx,yy=x+dx*sign,y+dy*sign
    while 0<=yy<self.h and 0<=xx<self.w and ground[yy][xx]=='s':span+=1;xx+=dx*sign;yy+=dy*sign
   runs.append(span)
  return 'h' if runs[0]>runs[1] else 'v'

 def finalize(self,atlas):
  transitions=atlas['transitions']
  d=self.d;w=self.w;h=self.h;c=self.code
  revision='0.3.5' if c=='M14' else '0.3.4' if c in ['M12','M13','M15','F25','S12'] else '0.3.1' if c=='M11' else VERSION
  d['objects'].extend(self.visits);d['building_sites']=self.sites
  # Place unchanged defenders on connected visible ground, keeping formations
  # away from the initial player group. Never change their stats or identity.
  occupied={tuple(p) for p in d['player_positions']}|{tuple(u['position']) for u in d['npc_units']}|{tuple(o['position']) for o in d['objects']}
  for group in ['enemies','reinforcements']:
   for u in d[group]:
    p=tuple(u['position']);candidates=[]
    for y in range(1,h-1):
     for x in range(1,w-1):
      if self.grid[y][x] in '~^#' or (x,y) in occupied:continue
      separation=min(abs(x-a)+abs(y-b) for a,b in d['player_positions'])
      if group=='enemies' and separation<13:continue
      if c=='F22' and 32<=x<=38 and (7<=y<=10 or 20<=y<=23):continue
      candidates.append((abs(x-p[0])+abs(y-p[1]),seed(f'{c}{u["id"]}:{x}:{y}')%100,x,y))
    assert candidates,(c,u['id']);_,_,x,y=min(candidates);u['position']=[x,y];occupied.add((x,y))
  # Reserve full interaction approaches and actor silhouettes before nature.
  protected=set(occupied)|self.reserved
  for o in d['objects']:
   x,y=o['position']
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:protected.add((x+dx,y+dy))
   if o['kind'] in ['door','rescue']:self.grid[y][x]='#'
  if c=='M15':d['enemies'][0]['position']=[24,10]
  if c=='M12':
   next(u for u in d['enemies'] if u.get('burner'))['position']=[22,15]
  if c=='F24':
   for i,u in enumerate(e for e in d['enemies'] if e.get('objective_role')=='seize_beacon'):u['position']=[28+i,5]
  # Collision describes where actors may stand. It must never choose artwork:
  # a solid keep still stands on grass and a sea cliff still has water behind
  # its transparent silhouette. Coast masks use this restored ground too.
  ground=[[self.underlay.get((x,y),'s' if c in ['F21','F22','S21'] else 'p') if ch=='#'
           else self.underlay.get((x,y),'s' if c in ['F21','F22','S21'] else 'n' if c=='M11' else '.') if ch in 'ht'
           else ch for x,ch in enumerate(row)] for y,row in enumerate(self.grid)]
  base=[[None]*w for _ in range(h)]
  ship=c in ['F21','F22','S21']
  for y in range(h):
   for x in range(w):
    ch=ground[y][x];v=seed(f'{c}:{x}:{y}')%4;material=MATERIAL[ch];surface=ch
    if c in ['S11','S22'] and surface in '.p':material='cave'
    if ch=='f':material='grass'
    if c=='M11' and ch in '.f':material='snow'
    tile=PACK['base'][material][v]
    if ch=='p' and c not in ['S11','S22']:
     key='snow_path' if c=='M11' else 'path_sand' if any(0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='d' for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]) else 'path'
     # The snowy track meets bridge planks directly, without a snow-coloured
     # seam that incorrectly suggests the crossing is disconnected.
     mask=mask_at(ground,x,y,lambda q:q in 'ps');tile=transitions[key][str(mask)][v]
    if ch=='d':tile=transitions['beach_grass'][str(mask_at(ground,x,y,lambda q:q not in '.f'))][v]
    if ch=='s' and not ship:
     mask=sum(bit for dx,dy,bit in [(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)] if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s')
     tile=transitions['walkway'][self.timber_axis(x,y,ground)+str(mask)][v]
    if c=='M11' and ch=='~':
     edges=''
     for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]:
      q=self.grid[y+dy][x+dx] if 0<=x+dx<w and 0<=y+dy<h else '~'
      edges+='w' if q in '~s' else 'p' if q=='p' else 'n'
     tile=transitions['winter_river'][edges][v]
    if ch=='~' and c!='M11' and not ship:
     neighbours=[]
     for dx,dy in [(0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)]:
      q=ground[y+dy][x+dx] if 0<=x+dx<w and 0<=y+dy<h else '~'
      neighbours.append('w' if q=='~' else 'a' if q=='d' else 'r' if q=='^' else 'v' if q=='p' and c in ['S11','S22'] else 'p' if q=='p' else 'c' if q in 'c=' else 't' if q in 's+' else 'n' if q=='n' else 'g')
     if any(q!='w' for q in neighbours):tile=shore_tile(atlas,neighbours,v)
    coast=c!='M11' and ch!='~' and mask_at(ground,x,y,lambda q:q!='~')!=255 and any(0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='~' for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)])
    if coast and (ship or ch=='^'):
     mask=mask_at(ground,x,y,lambda q:q!='~')
     if ch=='s':tile=transitions['timber_coast'][str(mask)][v]
     elif ch=='n' or (c=='M11' and ch in '.fht'):tile=transitions['snow_coast'][str(mask)][v]
     elif c=='M11' and ch=='p':tile=transitions['dirt_coast'][str(mask)][v]
     elif ch=='^':tile=transitions['mountain_ground']['sea'][str(mask)][v]
     else:tile=SEA['coasts']['stone'][str(mask)][v]
    elif ch=='^':
     background='cave' if c in ['S11','S22'] else 'grass'
     tile=transitions['mountain_ground'][background][str(mask_at(ground,x,y,lambda q:q=='^'))][v]
    base[y][x]=tile
  # Whole trees/outcrops occupy matching terrain, with fixed irregular spacing.
  allowed={q:{(x,y) for y in range(h) for x in range(w) if self.grid[y][x]==q} for q in ['f','^']}
  for q,kinds in [('f',['snow_tall','snow_broad','snow_young'] if c=='M11' else ['pine_tall','pine_broad','pine_young','pine_pair']),('^',['peak_low','crag_tall','ridge_bent','outcrop'])]:
   positions=sorted(allowed[q]);self.rng.shuffle(positions);used=set()
   for x,y in positions:
    if (x,y) in used or self.rng.random()<.16:continue
    key=self.rng.choice(kinds);sw,sh=NATURE[key]['size'];fw,fh=math.ceil(sw/16),math.ceil(sh/16)
    foot={(xx,yy) for yy in range(y,y+fh) for xx in range(x,x+fw)}
    if not foot<=allowed[q] or foot&protected or len(foot&used)>len(foot)*.22:continue
    self.nature.append({'key':key,'position':[x*16+self.rng.randrange(0,3),y*16],'flip':self.rng.random()<.35});used|=foot
   if q=='f':
    small=['snow_small_a','snow_small_b'] if c=='M11' else ['pine_small_a','pine_small_b']
    for x,y in sorted(allowed[q]-used-protected):
     key=self.rng.choice(small);xx=x*16;yy=y*16
     for _ in range(4):
      dx=self.rng.randrange(-4,5);dy=self.rng.randrange(-3,4)
      foot={(ax,ay) for ay in range(math.floor((yy+dy)/16),math.ceil((yy+dy+16)/16)) for ax in range(math.floor((xx+dx)/16),math.ceil((xx+dx+16)/16))}
      if foot<=allowed[q] and not foot&protected:xx+=dx;yy+=dy;break
     self.nature.append({'key':key,'position':[xx,yy],'flip':self.rng.random()<.5})
  d.update(map={'width':w,'height':h,'tiles':[IDS[q] for row in self.grid for q in row]},logic_grid=[''.join(row) for row in self.grid],visual_ground=[''.join(row) for row in ground],art_layers=[base,[[None]*w for _ in range(h)],[[None]*w for _ in range(h)]],art_modules=self.modules,art_props=self.props,natural_props=self.nature,art_atlas='res://assets/battlefield-0.3.0/terrain.png',art_columns=32,art_style_version='0.3.6',tactical_review_version=revision,location_theme=THEMES[c],tactical_routes=self.routes)
  d.pop('nature_layout',None)
  # Surroundings stay sparse and scene-authored; they do not dwarf the field.
  biome='snow' if c=='M11' else 'rock' if c in ['S11','S22'] else 'forest'
  d['nature_layout']={'biome':biome,'props':[],'excluded':[[0,0,w*16,h*16]]}
  d['production_anchors']={'revision':revision,'deployment':d['player_positions'],'targets':d['targets'],'exit':d['exit']}
  d['tactical_notes']=[THEMES[c]+'。主路与支路可分队推进；窄口由近战控制，远程可在后方支援。']
  if c=='F24':d['tactical_notes']=['先沿草坡接近航灯。灯前石台可守，东岸飞兵能绕过正面；夺灯后必须在下一轮前赶走。']
  if c=='M15':d['tactical_notes']=['海崖围成三条进堡路线。中路缺口可守，东侧栈道可截北门；科兰第八回合开始撤离，提前派骑兵封路。']
  if c=='M14':d['tactical_notes']=['南营、东营两处军旗立在道路缺口中，站到旗点选择控制，红旗会变为蓝旗。南路三格宽便于布阵，东路两格宽适合卡口；西侧林道可以绕后。']
  if c=='M12':d['tactical_notes']=['土质坡道通往粮仓，西坡可绕过正面木栅。焚毁兵第六回合预告、第七回合出发；拦住仓门，别让他连续两次点火。']
  if c in ['F21','F22','S21']:d['tactical_notes']=['大甲板留出集结空间。两条登舰通道可夹攻；近战守跳板，弓手与法师从后方支援。']
  if c=='F21':d['tactical_notes']=['两条跳板可夹攻舰长。己船医药区的浅色恢复格沿用原地形恢复规则，可轮换伤员后再推进；注意甲板上的远程射线。']
  if c=='F22':d['tactical_notes']=['可先打开囚舱总闸，备用跳板构成另一条撤离路线。己船医药区有恢复格，伤员可轮换；清出跳板后让俘虏回到己船白旗处。']
  # Preserve all combat statistics and narrative triggers from the old cards.
  for group in ['enemies','npc_units','reinforcements']:
   for a,b in zip(self.old[group],d[group]):
    assert {k:v for k,v in a.items() if k!='position'}=={k:v for k,v in b.items() if k!='position'},(c,a['id'],'stat drift')
  write(R/f'data/stages/{c}.json',d)
  return {'code':c,'name':d['name_zh'],'theme':THEMES[c],'before_size':[self.old['map']['width'],self.old['map']['height']],'size':[w,h],'area_growth':round(w*h/(self.old['map']['width']*self.old['map']['height']),2),'stone_ratio':round(sum(q in '=c' for row in self.grid for q in row)/(w*h),3),'ground_cells':sum(q not in '~^#' for row in self.grid for q in row),'modules':len(self.modules),'nature_props':len(self.nature),'routes':len(self.routes),'min_initial_grid_distance':min(abs(x-u['position'][0])+abs(y-u['position'][1]) for x,y in d['player_positions'] for u in d['enemies'])}

def main():
 OUT.mkdir(parents=True,exist_ok=True);atlas=build_atlas();records=[]
 for code in SIZES:
  field=Battlefield(code);field.terrain();records.append(field.finalize(atlas))
 save_atlas(atlas)
 write(OUT/'map-design.json',{'version':VERSION,'stages':records,'combat_stats_unchanged':True,'baseline':'data/compat/0.2.1'})
 print(json.dumps(records,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
