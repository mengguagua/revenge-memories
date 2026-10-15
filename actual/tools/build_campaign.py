#!/usr/bin/env python3
"""Build the approved geography and detailed battle art from reusable resources."""
from pathlib import Path
from collections import Counter, deque
import importlib.util, json, math, shutil, subprocess
import re
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT.parent
PLAN=json.loads((PARENT/'docs2/规划索引.json').read_text())
REPORT=ROOT/'reports/campaign'
OUT=ROOT/'assets/battle_tiles'
SRC=ROOT/'source/battle-tiles-b'
COLS=32
T=16
REPORT.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('world_builder',ROOT/'tools/build_world_tiles.py')
wb=importlib.util.module_from_spec(spec);spec.loader.exec_module(wb)

def write(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def optimize(path):
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','--strip','safe',str(path)],capture_output=True,check=True)

BUILDINGS=[('snow_cottage',2,2,'building'),('grain_store',3,2,'building'),('barracks',3,2,'building'),('tower_entry',2,3,'building'),
 ('stone_gate',2,2,'gate'),('closed_gate',2,1,'gate'),('open_gate',2,1,'gate'),('jail_door',1,2,'gate'),
 ('grain_wagon',2,1,'prop'),('medicine_wagon',2,1,'prop'),('crates',1,1,'prop'),('grain_sacks',1,1,'prop'),
 ('brazier',1,1,'prop'),('sun_altar',2,2,'building'),('stairs_up',2,2,'stairs'),('stairs_down',2,2,'stairs')]
DECOR=[('pine_patch',3,3,'forest'),('snow_pine_patch',3,3,'forest'),('rock_face',4,2,'rock'),('cave_entry',3,2,'rock'),
 ('north_wall',4,1,'wall'),('west_wall',1,4,'wall'),('outer_corner',2,2,'wall'),('inner_corner',2,2,'wall'),
 ('north_fence',4,1,'wall'),('west_fence',1,3,'wall'),('jail_bars_h',3,1,'wall'),('jail_bars_v',1,3,'wall'),
 ('breach',3,1,'wall'),('flowers',1,1,'prop'),('boulders',1,1,'prop'),('well',1,1,'prop')]
MATERIALS=['grass','snow','dirt','cave','stone','cobble','timber','sea','shallow','sand','salt','marsh','forest','rock','plaster','sacred']
STORY_PROPS=[('grave',1,1,'prop'),('aid_plaque',1,2,'prop'),('orders_case',1,1,'prop'),('lit_brazier',1,1,'prop'),
 ('white_flag',1,1,'prop'),('clinic_door',1,2,'gate'),('open_jail',1,2,'gate'),('ritual_lamp',1,2,'prop')]
def battle_art():
 wb.SRC=SRC;wb.OUT=OUT;(OUT/'modules').mkdir(exist_ok=True)
 modules=wb.cut_modules('buildings-generated.png',4,4,BUILDINGS)+wb.cut_modules('decor-generated.png',4,4,DECOR)+wb.cut_modules('story-props-generated.png',4,2,STORY_PROPS)
 src=Image.open(SRC/'materials-generated.png').convert('RGB')
 cells=[];metadata=[];base={};textures={};colors={}
 def add(im,name,category,kind='ground',extra=None):
  tid=len(cells);cells.append(im.convert('RGBA'))
  metadata.append(dict(id=tid,atlas=[tid%COLS,tid//COLS],name=name,category=category,kind=kind,**(extra or {})))
  return tid
 categories={'grass':0,'snow':0,'dirt':0,'cave':0,'stone':8,'cobble':8,'timber':6,'sea':7,'shallow':7,'sand':2,'salt':2,'marsh':16,'forest':1,'rock':5,'plaster':8,'sacred':8}
 for i,name in enumerate(MATERIALS):
  x=i%4;y=i//4;box=(round(x*src.width/4),round(y*src.height/4),round((x+1)*src.width/4),round((y+1)*src.height/4))
  tile=src.crop(box).resize((32,32),Image.Resampling.NEAREST).quantize(colors=12,dither=Image.Dither.NONE).convert('RGBA')
  colors[name]=Counter(tile.convert('RGB').getdata()).most_common(1)[0][0];base[name]=[];textures[name]=[]
  for v in range(4):
   im=tile.crop((v%2*16,v//2*16,v%2*16+16,v//2*16+16));textures[name].append(im)
   base[name].append(add(im,name+'_'+str(v),categories[name]))
 # Use a continuous section of generated tree/rock modules for connected masses.
 module_images={m[0]:m[4] for m in modules}
 families={}
 for name,fore,cat in [('forest','forest',1),('snow_forest','forest',1),('rock','rock',5),('wall','stone',12),('water','sea',7),('marsh','marsh',16)]:
  family={}
  texture=textures[fore][0]
  if name in ['forest','snow_forest']:
   patch=module_images['snow_pine_patch' if name=='snow_forest' else 'pine_patch']
   texture=patch.crop((16,16,32,32))
  if name=='rock':texture=module_images['rock_face'].crop((20,6,36,22))
  for m in wb.MASKS:
   im=texture.copy();alpha=wb.alpha_mask(m);im.putalpha(alpha)
   family[str(m)]=add(im,name+'_'+str(m),cat,'edge',{'mask':m})
  families[name]=family
 # Architectural cells come from full AI-painted battlement modules, not boxes.
 walls={}
 for key in ['north_wall','west_wall','outer_corner','inner_corner','jail_bars_h','jail_bars_v','north_fence','west_fence']:
  im=module_images[key];ids=[]
  for y in range(im.height//T):
   row=[]
   for x in range(im.width//T):row.append(add(im.crop((x*T,y*T,(x+1)*T,(y+1)*T)),key+f'_{x}_{y}',12,'wall'))
   ids.append(row)
  walls[key]=ids
 packed=[]
 for name,gw,gh,kind,im,bbox in modules:
  ids=[]
  for y in range(gh):
   row=[]
   for x in range(gw):row.append(add(im.crop((x*T,y*T,(x+1)*T,(y+1)*T)),name+f'_{x}_{y}',-1,'module'))
   ids.append(row)
  packed.append({'name':name,'kind':kind,'footprint':[gw,gh],'tiles':ids,'path':'modules/'+name+'.png','source_bbox':bbox,'logic':'explicit footprint/object record, no inference from decoration'})
 atlas=Image.new('RGBA',(COLS*T,math.ceil(len(cells)/COLS)*T))
 for i,im in enumerate(cells):atlas.alpha_composite(im,(i%COLS*T,i//COLS*T))
 atlas.save(OUT/'battle-tiles.png',optimize=True);optimize(OUT/'battle-tiles.png')
 pack={'schema':1,'native_tile_size':16,'columns':COLS,'atlas':'battle-tiles.png','tiles':metadata,'base':base,'families':families,'walls':walls,'modules':packed,'scope':'Tactical terrain/architecture; art and logic explicitly mapped'}
 write(OUT/'battle-tiles.json',pack)
 board=Image.new('RGB',(640,4*150),(27,38,43))
 for i,m in enumerate(modules):
  im=m[4];im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
  board.paste(im,(i%4*160+(160-im.width)//2,i//4*150+(130-im.height)//2),im)
 # Eight rows to show all modules; separate boards preserve actual native scale.
 for part in range(math.ceil(len(modules)/16)):
  board=Image.new('RGB',(640,600),(27,38,43))
  for j,m in enumerate(modules[part*16:(part+1)*16]):
   im=m[4].resize((m[4].width*2,m[4].height*2),Image.Resampling.NEAREST)
   board.paste(im,(j%4*160+(160-im.width)//2,j//4*150+(130-im.height)//2),im)
  board.save(REPORT/f'battle-modules-{part+1}.png',optimize=True);optimize(REPORT/f'battle-modules-{part+1}.png')
 return pack

def line(a,b):
 x,y=a;out=[(x,y)]
 while x!=b[0]:x+=1 if b[0]>x else -1;out.append((x,y))
 while y!=b[1]:y+=1 if b[1]>y else -1;out.append((x,y))
 return out

def fullpath(points):
 out=[]
 for a,b in zip(points,points[1:]):
  seg=line(a,b);out+=seg if not out else seg[1:]
 return out

def neighbors_mask(grid,x,y,predicate):
 h=len(grid);w=len(grid[0]);m=0
 for dx,dy,bit in wb.PEERS:
  if 0<=x+dx<w and 0<=y+dy<h and predicate(grid[y+dy][x+dx]):m|=bit
 return wb.canonical(m)

def render_layers(layers,w,h,atlas,columns):
 result=Image.new('RGBA',(w*16,h*16))
 for layer in layers:
  for y,row in enumerate(layer):
   for x,tid in enumerate(row):
    if tid is None or tid<0:continue
    sx=tid%columns*16;sy=tid//columns*16
    result.alpha_composite(atlas.crop((sx,sy,sx+16,sy+16)),(x*16,y*16))
 return result

def formal_world():
 w=PLAN['world'];width=w['width'];height=w['height'];old=Image.open(PARENT/'assets/original/graphics/maps/worldtiles.png').convert('RGB')
 wp=json.loads((ROOT/'assets/world_tiles/world-tiles.json').read_text());wa=Image.open(ROOT/'assets/world_tiles/world-tiles.png').convert('RGBA')
 base=wp['base_tiles'];families={f['name']:f for f in wp['families']};mods={m['name']:m for m in wp['modules']}
 def classify(tid):
  if tid>=256:return 'grass'
  im=old.crop((tid%16*16,tid//16*16,tid%16*16+16,tid//16*16+16));p=list(im.getdata())
  sea=sum(b>r*1.12 and b>g*1.08 and b>70 for r,g,b in p)
  green=sum(g>r*1.18 and g>b*1.15 for r,g,b in p)
  dark=sum(g>r*1.3 and g>b*1.3 and g<130 for r,g,b in p)
  gold=sum(r>b*1.5 and g>b*1.5 and r>70 for r,g,b in p)
  if sea>145 and green<65:return 'sea'
  if (64<=tid<=125 or tid in [197,198]) and gold>8:return 'rock'
  if gold>55:return 'sand'
  if dark>80:return 'forest'
  return 'grass'
 ground=[[classify(t) for t in row] for row in w['tiles']]
 for y in range(height):
  for x in range(width):
   if x<28 and y>45 and ground[y][x]=='grass':ground[y][x]='snow'
   if x>34 and 20<y<32 and ground[y][x]=='grass':ground[y][x]='salt' if x<43 else 'sand'
   if x>39 and 16<y<22 and ground[y][x] not in ['sea','rock']:ground[y][x]='marsh'
 routes=[];road_cells={};reserved=set()
 for i,e in enumerate(w['edges']):
  cells=fullpath(e['waypoints']);mode=e['mode'];sacred='通道' in mode or '神宫' in mode
  kind='sacred' if sacred else ('land' if mode in ['陆路','支路'] and e['a'].startswith('W') else 'mixed')
  r=dict(e,index=i,cells=[list(p) for p in cells],kind=kind);routes.append(r)
  for x,y in cells:
   road_cells.setdefault((x,y),[]).append(r)
   for dx in [-1,0,1]:
    for dy in [-1,0,1]:reserved.add((x+dx,y+dy))
   if kind=='land':
    ground[y][x]='snow' if x<28 and y>45 else 'grass'
   elif ground[y][x] in ['forest','rock','marsh']:ground[y][x]='grass'
 for n in w['nodes']:
  x,y=n['x'],n['y']
  if ground[y][x]=='sea' and n['id'] not in ['E02','E03','S03']:ground[y][x]='grass'
 layers=[[[None]*width for _ in range(height)] for _ in range(5)]
 for y in range(height):
  for x in range(width):
   material=ground[y][x];land=material!='sea'
   coast='coast_'+('snow' if material=='snow' else 'sand' if material=='sand' else 'salt' if material=='salt' else 'grass')
   mask=neighbors_mask(ground,x,y,lambda a:a!='sea')
   if not land:layers[0][y][x]=base['sea'][(x+y)%4]
   elif mask!=255:layers[0][y][x]=families[coast]['tiles_by_mask'][str(mask)]
   else:layers[0][y][x]=base[material if material not in ['forest','rock','marsh'] else 'grass'][(x*3+y)%4]
   if material in ['forest','marsh']:
    fam=families[material+'_edge'];bm=neighbors_mask(ground,x,y,lambda a:a==material)
    layers[1][y][x]=fam['tiles_by_mask'][str(bm)]
 # Place intact mountain and forest modules only where they cannot hide roads.
 placed=[]
 for y in range(3,height-4,2):
  for x in range(2,width-4,2):
   kind=ground[y][x]
   if kind not in ['rock','forest']:continue
   name=('snow_mountain_mass' if y>45 and x<28 else 'mountain_north_south' if (x+y)%3==0 else 'mountain_east_west') if kind=='rock' else ('snow_forest_mass' if y>45 and x<28 else 'forest_mass')
   m=mods[name];mw,mh=m['footprint'];foot={(x+dx,y+dy) for dy in range(mh) for dx in range(mw)}
   if foot&reserved or sum(ground[yy][xx]==kind for xx,yy in foot)<mw*mh*.45:continue
   if any(layers[2][yy][xx] is not None for xx,yy in foot):continue
   for dy,row in enumerate(m['tiles']):
    for dx,t in enumerate(row):layers[2][y+dy][x+dx]=t
   placed.append({'name':name,'origin':[x,y],'cells':[list(p) for p in sorted(foot)]})
 # Finish narrow ridges with intact small peaks; all silhouettes avoid routes.
 for y in range(2,height-2):
  for x in range(1,width-2):
   if ground[y][x]!='rock' or (x,y) in reserved or layers[2][y][x] is not None:continue
   m=mods['ridge_small' if ground[y][x+1]=='rock' and (x+1,y) not in reserved and layers[2][y][x+1] is None else 'rocks']
   for dy,row in enumerate(m['tiles']):
    for dx,t in enumerate(row):layers[2][y+dy][x+dx]=t
   placed.append({'name':m['name'],'origin':[x,y],'cells':[[x+dx,y+dy] for dy in range(m['footprint'][1]) for dx in range(m['footprint'][0])]})
 # Route pixels and gameplay movement use these same cardinal cells.
 overlays=wp['route_overlays'];roads=wp['roads'];bridges=wp['bridges']
 for (x,y),rs in road_cells.items():
  mask=0
  for dx,dy,bit in wb.PEERS[:4]:
   if (x+dx,y+dy) in road_cells:mask|=bit
  r=rs[0]
  if any(z['kind']=='sacred' for z in rs):tid=overlays['sacred'][str(mask)]
  elif ground[y][x]=='sea':tid=overlays['sea'][str(mask)]
  else:
   mat=ground[y][x];mat=mat if mat in roads else 'grass';tid=roads[mat][str(mask)]
  layers[3][y][x]=tid
 node_records=[]
 for index,n in enumerate(w['nodes']):
  nid=n['id'];x=n['x'];y=n['y'];kind=n['kind']
  name='fort'
  if '村' in n['name'] or '诊所' in n['name']:name='snow_village' if y>45 and x<28 else 'village'
  elif nid in ['W13']:name='capital'
  elif nid=='W12':name='sun_tower'
  elif nid=='W16':name='temple'
  elif nid=='W15':name='library'
  elif nid in ['W06','E06']:name='harbor'
  elif '洞' in n['name'] or '矿' in n['name'] or '地牢' in n['name']:name='cave'
  elif '观测' in n['name']:name='observatory'
  elif '沙城' in n['name']:name='sand_city'
  elif nid in ['E02','S03']:name='cutter'
  elif nid=='E03':name='galleon'
  elif '岛' in n['name']:name='lighthouse' if nid in ['E01','E05'] else 'village'
  elif '营' in n['name'] or '路' in n['name']:name='camp'
  m=mods[name];mw,mh=m['footprint'];ox=x-(mw-1)//2;oy=y-mh+1
  for dy,row in enumerate(m['tiles']):
   for dx,t in enumerate(row):layers[4][oy+dy][ox+dx]=t
  numeric=index+1
  node_records.append(dict(n,numeric_id=numeric,position=[x,y],name_zh=n['name'],symbol=name,neighbors=[],stages=[b['id'] for b in PLAN['battles'] if b['node']==nid]))
 nd={n['id']:n for n in node_records}
 for r in routes:nd[r['a']]['neighbors'].append(nd[r['b']]['numeric_id']);nd[r['b']]['neighbors'].append(nd[r['a']]['numeric_id'])
 runtime={'schema':2,'campaign_id':'revenge-memories-1','width':width,'height':height,'tile_size':16,'atlas':'res://assets/world_tiles/world-tiles.png','columns':32,'layers':layers,'ground':ground,'nodes':{str(n['numeric_id']):n for n in node_records},'routes':routes,'modules':placed,'source':'docs2/规划索引.json 1.1','movement':'Follow route cells exactly, not node-to-node straight lines'}
 write(ROOT/'data/formal_world.json',runtime)
 result=render_layers(layers,width,height,wa,32);result.convert('RGB').save(REPORT/'formal-world.png',optimize=True);optimize(REPORT/'formal-world.png')
 shutil.copy2(REPORT/'formal-world.png',ROOT/'assets/world_tiles/formal-world-overview.png')
 return runtime

CHARACTER_MAPPING={'hunapu':('alm','胡纳普'),'daan':('leo','达恩'),'otto':('lukas','奥托'),'fula':('silque','芙拉'),
 'lena':('clair','蕾娜'),'lance':('clive','兰斯'),'beck':('python','贝克'),'hervi':('luthier','赫维'),'german':('forsyth','格曼')}
OLD_IDS={'.':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'s':191,'b':66,'+':218}
COUNTS={'M11':[(6,4),(12,2)],'M12':[(6,5),(12,2),(8,1)],'M13':[(6,5),(7,2),(12,2)],
 'M14':[(1,3),(6,5),(12,2),(15,1)],'M15':[(6,5),(7,3),(12,3),(1,2),(15,1)],'S11':[(22,5),(12,1)],'S12':[(6,4),(12,2)]}
STAGE_IDS={'M11':101,'M12':102,'M13':103,'M14':104,'M15':105,'S11':111,'S12':112}
def campaign_data(pack,world):
 original=json.loads((PARENT/'data/campaign.json').read_text())['characters'];chars={}
 for key,(source,name) in CHARACTER_MAPPING.items():
  c=original[source].copy();c.update(key=key,id=key,name_zh=name,source_character=source,side='player',dead=False,acted=False)
  if key in ['daan','hervi','lance']:c['level']=1 if key=='daan' else 3
  chars[key]=c
 terrain=json.loads((PARENT/'data/stages/stage_001.json').read_text())['terrain']
 samples=[]
 for p in sorted((PARENT/'data/stages').glob('*.json')):
  samples+=json.loads(p.read_text()).get('enemies',[])
 templates={}
 for c in [1,6,7,8,12,15,22]:
  options=[u for u in samples if int(u['class_id'])==c];options.sort(key=lambda u:(u['level'],u['max_hp']))
  templates[c]=options[0]
 definitions={};atlas=Image.open(OUT/'battle-tiles.png').convert('RGBA');mods={m['name']:m for m in pack['modules']}
 for b in PLAN['battles']:
  if b['chapter']!=1:continue
  code=b['id'];w=b['width'];h=b['height'];grid=[list(row.ljust(w,'.')[:w]) for row in b['grid']]
  if len(grid)!=h:raise ValueError(code+' height')
  # A blueprint mark is a logical object, not a wall tile. Entries stay walkable.
  points=b['deployment_points_by_party'][0]+b['targets']+[b['boss'],b['exit']]+b['npc_anchors']+b['reinforcement_anchors']
  for x,y in points:
   if grid[y][x] in ['#','^','~']:grid[y][x]='='
  # Assemble complete groves while preserving all blueprint anchors and roads.
  if b['style'] in ['forest_route','forest_clinic'] or code=='M11':
   for y in range(h):
    for x in range(w):
     if grid[y][x]=='f' and sum(0<=x+dx<w and 0<=y+dy<h and grid[y+dy][x+dx]=='f' for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)])<2:grid[y][x]='.'
   for ox,oy in [(1,2),(7,6),(1,9),(w-6,h-8),(w-5,9)]:
    if not(0<=ox<=w-3 and 0<=oy<=h-3):continue
    if any(ox<=p[0]<ox+3 and oy<=p[1]<oy+3 for p in points):continue
    if all(grid[yy][xx] in '.f' for yy in range(oy,oy+3) for xx in range(ox,ox+3)):
     for yy in range(oy,oy+3):
      for xx in range(ox,ox+3):grid[yy][xx]='f'
  occupied=set();enemies=[]
  def free_near(at,avoid=None):
   queue=deque([tuple(at)]);seen={tuple(at)}
   while queue:
    x,y=queue.popleft()
    if 0<=x<w and 0<=y<h and grid[y][x] not in '#^~' and (x,y) not in occupied and (not avoid or (x,y) not in avoid):occupied.add((x,y));return [x,y]
    for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
     p=(x+dx,y+dy)
     if 0<=p[0]<w and 0<=p[1]<h and p not in seen:seen.add(p);queue.append(p)
   raise ValueError('no free location')
  boss_class=7 if code=='M15' else (1 if code=='M14' else 8 if code=='S11' else 6)
  def enemy(cid,at,index,boss=False):
   u=templates[cid].copy();u['id']=code+('_boss' if boss else '_e'+str(index));u['position']=free_near(at)
   u.update(acted=False,exp=0,item_id=0,side='enemy',group_id=0,level=3 if boss else 1,raw_ai_flags=0,ai_flags=0)
   # Original formulas/classes, explicit new-campaign encounter parameters.
   hp=32 if code=='M15' and boss else 27 if boss else 24 if cid==7 else 22
   u.update(hp=hp,max_hp=hp,strength=12 if code=='M15' and boss else 9 if boss else 8 if cid in [1,7,8] else 7,
    defence=8 if code=='M15' and boss else 6 if cid==7 else 4 if boss else 3,skill=5 if boss else 3,speed=5 if cid in [1,8] else 3,luck=0)
   u['name_zh']='科兰' if code=='M15' and boss else ('盗掠首领' if code=='S11' and boss else '指挥官' if boss else {1:'骑兵',6:'士兵',7:'重装兵',8:'佣兵',12:'弓手',15:'魔道士',22:'盗匪'}[cid])
   if cid==15:u['magic_flags']=1;u['raw_magic_flags']=1
   if boss:u['objective_boss']=True
   if (code=='M11' and cid==12) or (boss and code in ['M12','M13','M15']):u['behavior']='guard'
   return u
  # Commander owns enemy slot zero; every reinforcement gets its own identity.
  enemies.append(enemy(boss_class,b['boss'],0,True))
  for cid,count in COUNTS[code]:
   for i in range(count):enemies.append(enemy(cid,b['enemy_anchors'][(len(enemies)-1)%len(b['enemy_anchors'])],len(enemies)))
  if code=='M12':enemies[1]['burner']=True;enemies[1]['name_zh']='焚毁兵'
  if code=='M12':
   occupied.discard(tuple(enemies[1]['position']));enemies[1]['position']=free_near(b['targets'][1])
  deploy=b['deployment_points_by_party'][0]
  objects=[];npcs=[]
  def obj(kind,at,label,adjacent=True):
   objects.append({'id':f'{code}_{kind}_{len(objects)}','kind':kind,'position':at,'label':label,'adjacent':adjacent})
  def npc(key,at,name,source='gray',quest='escort',locked=False):
   c=original[source].copy();c.update(id=key,name_zh=name,position=free_near(at),side='player',neutral=True,temporary=True,no_experience=True,controllable=False,acted=False,quest_kind=quest,locked=locked,max_hp=24,hp=24,defence=4)
   c['player_slot']=len(deploy)+len(npcs);npcs.append(c)
  if code=='M11':
   for i,at in enumerate(b['npc_anchors']):npc(f'{code}_refugees{i}',at,'流民队'+str(i+1))
  if code=='M12':
   obj('occupy',b['targets'][0],'占领粮仓',False);npc('fula',b['npc_anchors'][0],'芙拉','silque','witness')
  if code=='M13':
   for i,at in enumerate(b['targets']):obj('door',at,'打开牢门'+str(i+1));npc(f'{code}_workers{i}',b['npc_anchors'][i],'劳工队'+str(i+1),locked=True)
   npc('lena',[b['npc_anchors'][0][0]+1,b['npc_anchors'][0][1]],'蕾娜','clair','witness',True)
  if code=='M14':
   for i,at in enumerate(b['targets']):obj('control',at,'控制道路'+str(i+1),False)
  if code=='M15':
   for i,at in enumerate(b['targets']):obj('rescue',at,'救出劳工'+str(i+1));npc(f'{code}_workers{i}',b['npc_anchors'][i],'劳工队'+str(i+1),locked=True)
  if code=='S11':
   for i,at in enumerate(b['npc_anchors']):npc(f'{code}_miners{i}',at,'矿工队'+str(i+1))
   npc('beck',[7,12],'贝克','python','witness');obj('tools',b['targets'][0],'取回工具')
  if code=='S12':
   npc('medicine_wagon',b['npc_anchors'][1],'药车','gray','medicine');npc('hervi',b['npc_anchors'][0],'赫维','luthier','witness')
   npcs[-2]['no_counter']=True;npcs[-2]['event_object']=True
  rein=[]
  if code in ['M11','M13','M15']:
   cid=8 if code=='M13' else 6;round_=5 if code=='M13' else 4
   for i in range(2):
    u=enemy(cid,b['reinforcement_anchors'][0],40+i);u['id']=code+'_r'+str(i);rein.append(u)
   for u in rein:occupied.discard(tuple(u['position']))
  else:round_=0
  # Forest edges and architecture are multi-cell art with explicit rule cells.
  layers=[[[None]*w for _ in range(h)] for _ in range(4)]
  wall=pack['walls'];snow=code=='M11';cave=code=='S11'
  for y in range(h):
   for x in range(w):
    ch=grid[y][x];material='snow' if snow else 'cave' if cave else 'grass'
    material={'d':'sand','=':'stone','s':'timber','+':'cobble','b':'marsh','~':'sea'}.get(ch,material)
    layers[0][y][x]=pack['base'][material][(x*17+y*7)%4]
    if ch in ['f','^','~','b']:
     family={'f':'snow_forest' if snow else 'forest','^':'rock','~':'water','b':'marsh'}[ch]
     mask=neighbors_mask(grid,x,y,lambda a:a==ch);layers[1][y][x]=pack['families'][family][str(mask)]
    if ch=='#':
     horizontal=(x>0 and grid[y][x-1]=='#') or (x+1<w and grid[y][x+1]=='#')
     layers[1][y][x]=wall['north_wall'][0][x%4] if horizontal else wall['west_wall'][y%4][0]
  placements=[]
  blocked={tuple(p) for p in points}|{tuple(u['position']) for u in enemies+npcs}
  def stamp(name,at,footprint_logic=None):
   m=mods[name];mw,mh=m['footprint'];ox,oy=at
   if not(0<=ox<=w-mw and 0<=oy<=h-mh):return False
   if any((ox+dx,oy+dy) in blocked for dy in range(mh) for dx in range(mw)):return False
   for dy,row in enumerate(m['tiles']):
    for dx,t in enumerate(row):
     layers[2][oy+dy][ox+dx]=t
     if footprint_logic:grid[oy+dy][ox+dx]=footprint_logic
   placements.append({'name':name,'origin':[ox,oy],'footprint':m['footprint'],'logic':footprint_logic or 'inherits_ground'})
   blocked.update((ox+dx,oy+dy) for dy in range(mh) for dx in range(mw));return True
  # Only complete foliage patches that agree with every rule cell.
  for y in range(1,h-3):
   for x in range(1,w-3):
    if all(grid[yy][xx]=='f' for yy in range(y,y+3) for xx in range(x,x+3)):stamp('snow_pine_patch' if snow else 'pine_patch',[x,y])
  for x,y,name in [(max(0,w-6),1,'tower_entry' if code=='M15' else 'grain_store' if code=='M12' else 'barracks'),(1,1,'snow_cottage' if snow else 'cave_entry' if cave else 'barracks')]:stamp(name,[x,y],'#')
  for y in range(2,h-1,7):
   for x in range(1,w-1,5):
    if grid[y][x] in ['.','f'] and (x,y) not in blocked:stamp('flowers' if grid[y][x]=='.' else 'boulders',[x,y])
  if code in ['M12','M13','M14','M15']:
   for at,name in [([w-8,3],'grain_sacks'),([w-8,8],'crates'),([w-9,h-6],'grain_wagon'),([8,h-8],'medicine_wagon'),([8,3],'brazier')]:
    x,y=at
    if grid[y][x]=='=':stamp(name,at)
  for o in objects:
   x,y=o['position'];name='jail_door' if o['kind']=='door' else 'grain_sacks' if o['kind']=='occupy' else 'crates' if o['kind']=='tools' else 'open_gate'
   o['sprite']=name
   if o['kind']=='door':grid[y][x]='#'
  terrain_copy=json.loads(json.dumps(terrain));logic=[OLD_IDS[ch] for row in grid for ch in row]
  numeric=STAGE_IDS[code];node=next(n for n in world['nodes'].values() if n['id']==b['node'])
  data={'schema_version':4,'id':numeric,'code':code,'name_zh':b['name'],'chapter':1,'route':'alm','node':node['numeric_id'],
   'map':{'width':w,'height':h,'tiles':logic},'art_layers':layers,'art_modules':placements,'logic_grid':[''.join(r) for r in grid],
   'characters':chars,'player_positions':deploy,'enemies':enemies,'npc_units':npcs,'terrain':terrain_copy,'enemy_group_ids':[],
   'objects':objects,'reinforcements':rein,'reinforcement_turn':round_,'exit':b['exit'],'boss_id':code+'_boss','targets':b['targets'],
   'goal':b['goal'],'cause':b['cause'],'before':b['before'],'during':b['during'],'after':b['after'],'absent_branch':b['absent_branch'],
   'optional':b['optional'],'contract':b['interaction_contract'],'ai_and_timing':b['ai_and_timing']}
  mids={'M11':'奥托：前面那条小路能走。别让他们绕回营地。','M12':'芙拉：别把粮全留给军队。村里已经等了几天。',
   'M13':'蕾娜：我能走。先去另一间，他们没有力气再等了。','M14':'兰斯：愿意放下武器的去西门。不要再往内院退。',
   'M15':'胡纳普：凯尔回营的时候，你答应过放人。／科兰：他已经把整支军队的命令都坏掉了。',
   'S11':'矿工：这是征调时留下的工具。先让人出去，再来搬它们。','S12':'管理员：林边的小路是森林，骑兵可以沿主路绕行。'}
  data['during']=mids[code]
  if code=='M12':data['before']+='／战场提示：焚毁兵从集合点出发，第5回合开始行动。连续两次在粮仓门前点火会失败。'
  if code=='M15':data['before']+='／战场提示：科兰第6回合且半血时撤离，最晚第8回合出发。北门是他的撤离点。'
  definitions[str(numeric)]={'code':code,'path':'res://data/stages/'+code+'.json','node':node['numeric_id']}
  write(ROOT/'data/stages'/f'{code}.json',data)
  rendered=render_layers(layers,w,h,atlas,COLS);rendered.convert('RGB').save(REPORT/(code+'-map.png'),optimize=True);optimize(REPORT/(code+'-map.png'))
 story=(PARENT/'docs2/完整故事剧情.md').read_text();scenes={}
 for match in re.finditer(r'^### (D\d+) ([^\n]+)\n([\s\S]*?)(?=^### |\Z)',story,re.M):
  code=match.group(1)
  if code not in ['D00','D11','D12','D13']:continue
  pages=[]
  for ln in match.group(3).splitlines():
   if '：' in ln and not ln.startswith(('#','|')):
    who,text=ln.split('：',1);pages.append({'speaker':who,'text':text})
  scenes[code]=pages
 campaign={'schema':1,'campaign_id':'revenge-memories-1','characters':chars,'stages':definitions,'initial_party':['hunapu','daan','otto'],
  'scenes':scenes,'chapter_limit':1,'asset_reuse':'Original portraits, map/class sprites, near combat animations; new identities and original campaign story',
  'mapping':{k:{'story_name':v[1],'source_character':v[0]} for k,v in CHARACTER_MAPPING.items()},
  'rewards':{'S11_tools':2,'S11_clear':11,'M12_grain':0,'S12_medicine':'event object; no item slot'},
  'balance':'Explicit encounter construction: base enemies L1 HP22/24, STR7/8 DEF3; commanders L3 HP27, Korlan HP32 STR12 DEF8. Original rules and player growth formulas.'}
 write(ROOT/'data/campaign.json',campaign)
 return campaign

if __name__=='__main__':
 pack=battle_art();world=formal_world();campaign=campaign_data(pack,world);print(json.dumps({'battle_cells':len(pack['tiles']),'battle_modules':len(pack['modules']),'world_nodes':len(world['nodes']),'world_routes':len(world['routes']),'chapter_1_stages':len(campaign['stages'])}))
