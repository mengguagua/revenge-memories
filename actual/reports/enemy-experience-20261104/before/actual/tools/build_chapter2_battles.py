#!/usr/bin/env python3
"""Second chapter only: maritime terrain, reusable complete modules and encounter cards.
Never rewrites chapter one or campaign progression. All gameplay anchors keep the
approved story card coordinates; explicit local exceptions are recorded below.
"""
from pathlib import Path
from collections import deque
import json, math, random, copy, subprocess, importlib.util
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[1]; P=R.parent; OUT=R/'assets/chapter2'; REPORT=R/'reports/chapter2-battles'
OUT.mkdir(exist_ok=True); REPORT.mkdir(parents=True,exist_ok=True)
PLAN=json.loads((P/'docs2/规划索引.json').read_text()); PACK=json.loads((R/'assets/battle_tiles/battle-tiles.json').read_text())
NATURE={s['key']:s for s in json.loads((R/'assets/nature/nature.json').read_text())['sprites']}
ORIGINAL=json.loads((P/'data/campaign.json').read_text())['characters']
WORLD=json.loads((R/'data/formal_world.json').read_text())
T=16; COLS=32
OLD={'.':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'s':191,'b':66,'+':218}
IDS={'F21':201,'F22':202,'F23':203,'F24':204,'F25':205,'F26':206,'S21':211,'S22':212}
COUNTS={'F21':[(6,5),(12,2),(15,1)],'F22':[(6,5),(2,2),(12,2)],'F23':[(11,5),(3,3),(2,2)],'F24':[(3,3),(6,4),(12,2),(15,1)],'F25':[(6,4),(2,3),(12,3),(15,2),(3,2)],'F26':[(3,3),(6,4),(12,2),(15,2)],'S21':[(3,3),(11,3)],'S22':[(11,4),(3,2)]}
CHARMAP={'eileen':('celica','艾琳'),'mireille':('genny','米蕾'),'lisa':('mae','莉莎'),'carlo':('saber','卡洛'),'lord':('valbar','洛德'),'roan':('atlas','罗恩'),'shia':('catria','希雅')}
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def opt(path):subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','--quiet',str(path)],check=True)
def line(a,b):
 x,y=a;out=[(x,y)]
 while x!=b[0]:x+=1 if x<b[0] else -1;out.append((x,y))
 while y!=b[1]:y+=1 if y<b[1] else -1;out.append((x,y))
 return out
def route(points):
 out=[]
 for a,b in zip(points,points[1:]):out+=line(a,b)[int(bool(out)):]
 return out

def build_atlas():
 src=Image.open(R/'source/chapter2/maritime-source.png').convert('RGBA')
 specs=[('bow',3,2,(60,0,390,278)),('stern',3,2,(430,40,740,276)),('rail_h',4,1,(770,120,1228,250)),('rail_v',1,4,(1285,0,1405,325)),('captain_cabin',3,2,(50,320,420,620)),('mast',2,4,(440,275,735,665)),('hatch',2,2,(800,390,1080,620)),('gangplank',3,1,(1150,410,1495,595)),('lighthouse',3,5,(75,610,380,1024)),('fishing_hut',3,2,(420,700,775,1015)),('bollard',1,1,(840,730,1100,980)),('rowboat',2,3,(1190,640,1490,1024))]
 base=Image.open(R/'assets/battle_tiles/battle-tiles.png').convert('RGBA')
 cells=[base.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)) for i in range(len(PACK['tiles']))]
 mods={m['name']:copy.deepcopy(m) for m in PACK['modules']};records=[]
 for name,gw,gh,box in specs:
  obj=src.crop(box);a=obj.getchannel('A').point(lambda n:255 if n>70 else 0);obj.putalpha(a);bbox=obj.getbbox();obj=obj.crop(bbox)
  # Rail segments join along full horizontal/vertical axes; complete modules
  # use transparent padding so outlines survive source and runtime boundaries.
  nw,nh=gw*16,gh*16
  if name.startswith('rail_') or name=='gangplank':size=(nw,nh)
  else:
   scale=min((nw-2)/obj.width,(nh-2)/obj.height);size=(round(obj.width*scale),round(obj.height*scale))
  obj=obj.resize(size,Image.Resampling.NEAREST);alpha=obj.getchannel('A');obj=obj.convert('RGB').quantize(colors=28,dither=Image.Dither.NONE).convert('RGBA');obj.putalpha(alpha)
  im=Image.new('RGBA',(nw,nh));im.alpha_composite(obj,((nw-size[0])//2,nh-size[1]));path=OUT/'modules'/f'{name}.png';path.parent.mkdir(exist_ok=True);im.save(path);opt(path)
  tids=[]
  for y in range(gh):
   row=[]
   for x in range(gw):row.append(len(cells));cells.append(im.crop((x*16,y*16,x*16+16,y*16+16)))
   tids.append(row)
  m={'name':name,'footprint':[gw,gh],'tiles':tids,'path':'res://assets/chapter2/modules/'+name+'.png','source_bbox':list(box),'opaque_bbox':list(im.getbbox()),'bytes':path.stat().st_size,'kind':'maritime_module','whole_source':True};mods[name]=m;records.append(m)
 # Seamless coast composition from approved materials and blob masks. Reuses
 # generated source textures; only tile masks/connectivity are deterministic.
 sp=importlib.util.spec_from_file_location('world_masks',R/'tools/build_world_tiles.py');wb=importlib.util.module_from_spec(sp);sp.loader.exec_module(wb)
 coasts={}
 for material in ['sand','grass','stone','cave']:
  coasts[material]={}
  for mask in wb.MASKS:
   ids=[]
   for v in range(4):
    im=cells[PACK['base']['sea'][v]].copy();land=cells[PACK['base'][material][v]].copy();land.putalpha(wb.alpha_mask(mask));im.alpha_composite(land);ids.append(len(cells));cells.append(im)
   coasts[material][str(mask)]=ids
 atlas=Image.new('RGBA',(32*16,math.ceil(len(cells)/32)*16))
 for i,im in enumerate(cells):atlas.alpha_composite(im,(i%32*16,i//32*16))
 atlas.save(OUT/'chapter2-tiles.png');opt(OUT/'chapter2-tiles.png')
 data={'schema':1,'native_tile_size':16,'columns':32,'atlas':'res://assets/chapter2/chapter2-tiles.png','base_tile_count':len(PACK['tiles']),'tile_count':len(cells),'modules':records,'coasts':coasts,'palette':'approved humble retro battle palette','source_mode':'built-in imagegen','source':'source/chapter2/maritime-source.png'}
 write(OUT/'chapter2-tiles.json',data)
 board=Image.new('RGB',(320,288),(27,39,43));draw=ImageDraw.Draw(board)
 for i,m in enumerate(records):
  im=Image.open(R/m['path'].removeprefix('res://')).convert('RGBA');x=i%4*80+(80-im.width)//2;y=i//4*96+(80-im.height)//2;board.paste(im,(x,y),im);draw.text((i%4*80+2,i//4*96+82),m['name'],fill=(230,226,207))
 board.save(REPORT/'maritime-modules.png');opt(REPORT/'maritime-modules.png')
 return atlas,mods,coasts,wb

def refine_prison_geometry(data,modules):
 """Visible two-cell detention bays and real gates; preserve captive stats.

 The original production anchors put captives on open deck while a remote
 lever controlled their locked flag. These bays give that state physical form.
 """
 if data['code']!='F22' or data.get('detention_bays'):return
 grid=[list(row) for row in data['logic_grid']];layers=data['art_layers'];w=data['map']['width'];h=data['map']['height']
 prison_cells=set();gates=[]
 for middle in [7,15]:
  # Interior x22..24, y=middle. Keep the exact NPC positions 23/24.
  for name,ox,oy in [('jail_bars_h',22,middle-1),('jail_bars_v',21,middle-1),('jail_bars_v',25,middle-1),('jail_bars_h',22,middle+1)]:
   m=modules[name];mw,mh=m['footprint'];cells=[[x,y] for y in range(oy,oy+mh) for x in range(ox,ox+mw)]
   for dy,row in enumerate(m['tiles']):
    for dx,tid in enumerate(row):layers[2][oy+dy][ox+dx]=tid
   for x,y in cells:grid[y][x]='#';prison_cells.add((x,y))
   data['art_modules'].append({'name':name,'origin':[ox,oy],'footprint':[mw,mh],'logic':'#','cells':cells,'purpose':'Complete detention-bay rails'})
  gates.append([24,middle+1])
 # The lower mast used to occupy the upper cell's front rail. Keep its full
 # silhouette intact by replacing that mast footprint with ordinary timber;
 # the tall ship mast on the player vessel remains the navigation landmark.
 old=next((m for m in data['art_modules'] if m['name']=='mast' and m['origin']==[22,8]),None)
 if old:
  data['art_modules'].remove(old)
  for x,y in old['cells']:
   if (x,y) in prison_cells:continue
   grid[y][x]='s';layers[2][y][x]=None
 # The outer deck is the two-cell-wide main escort aisle. Remove the two
 # earlier decorative bollards which would split it into narrow single files.
 for old in list(data['art_modules']):
  if old['name']=='bollard' and old['origin'] in [[27,6],[27,16]]:
   data['art_modules'].remove(old)
   for x,y in old['cells']:grid[y][x]='s';layers[2][y][x]=None
 # Relocate only guards whose production anchor is now occupied by real bars.
 occupied={tuple(u['position']) for u in data['npc_units']+data['enemies']+data['reinforcements']}|set(map(tuple,data['player_positions']))
 relocations=[]
 for u in data['enemies']:
  start=tuple(u['position'])
  if start not in prison_cells:continue
  occupied.discard(start);queue=deque([start]);seen={start};chosen=None
  while queue:
   x,y=queue.popleft()
   if 0<=x<w and 0<=y<h and grid[y][x] not in '#^~' and (x,y) not in occupied:
    chosen=(x,y);break
   for dx,dy in [(1,0),(0,-1),(0,1),(-1,0)]:
    n=x+dx,y+dy
    if 0<=n[0]<w and 0<=n[1]<h and n not in seen:seen.add(n);queue.append(n)
  assert chosen is not None
  u['position']=list(chosen);occupied.add(chosen);relocations.append({'id':u['id'],'from':list(start),'to':list(chosen),'reason':'Visible detention rail occupied original guard cell'})
 door=next(o for o in data['objects'] if o['id']=='prison_door')
 door.update(label='打开囚舱总闸',sprite_path='res://assets/battle_tiles/modules/jail_door.png',open_sprite_path='res://assets/battle_tiles/modules/open_jail.png',opens=[door['position']]+gates,open_art_cells=[{'position':p,'base_tile':PACK['base']['timber'][p[0]%4],'clear_layers':[1,2]} for p in gates])
 data['logic_grid']=[''.join(row) for row in grid];data['map']['tiles']=[OLD[c] for row in grid for c in row]
 data['detention_bays']={'gates':gates,'captive_positions_unchanged':True,'guard_relocations':relocations,'unlock_control':[16,11],'main_aisle_columns':[26,27],'main_aisle_rows':[3,18]}

def refine_harbor_art(data,modules):
 """F25 visual-only zoning; all rule cells, objectives and unit stats stay exact."""
 if data['code']!='F25':return
 layers=data['art_layers'];grid=data['logic_grid'];w=data['map']['width'];h=data['map']['height']
 for y in range(h):
  for x in range(w):
   if grid[y][x] not in '=#' or x<11:continue
   # Old cobbled loading yards sit beside the dressed-stone processional
   # route. Coherent districts, rather than alternating decorative squares.
   cobbled=(11<=x<=16 and 4<=y<=12) or (17<=x<=28 and 3<=y<=6) or (12<=x<=28 and 11<=y<=20)
   main_route=(21<=x<=23 and 3<=y<=20) or (13<=y<=15 and 12<=x<=28) or (18<=x<=20 and y>=16)
   material='cobble' if cobbled and not main_route else 'stone'
   variant=(x*73856093)^(y*19349663);variant=(variant^(variant>>13))%4
   layers[0][y][x]=PACK['base'][material][variant]
 source=next((m for m in data['art_modules'] if m['name']=='barracks' and m['origin']==[19,8]),None)
 if source:
  for x,y in source['cells']:layers[2][y][x]=None
  data['art_modules'].remove(source)
  for name,ox,oy in [('grain_sacks',19,8),('crates',20,8),('brazier',21,8),('grain_wagon',19,9),('grain_sacks',21,9)]:
   m=modules[name];mw,mh=m['footprint'];cells=[[x,y] for y in range(oy,oy+mh) for x in range(ox,ox+mw)]
   assert all(grid[y][x]=='#' for x,y in cells),'Cargo must inherit the existing blocked footprint'
   for dy,row in enumerate(m['tiles']):
    for dx,tid in enumerate(row):layers[2][oy+dy][ox+dx]=tid
   data['art_modules'].append({'name':name,'origin':[ox,oy],'footprint':[mw,mh],'logic':'#','cells':cells,'visual_replacement':'Existing blocked barracks footprint reused as harbor cargo storage'})
 data['before']='艾琳：引航者关在东侧，箱子在主楼前。先把人救出来。'
 data['art_style_version']='chapter2-harbor-review2'

def main():
 atlas,mods,coasts,wb=build_atlas();templates={};samples=[]
 for path in sorted((P/'data/stages').glob('*.json')):samples+=json.loads(path.read_text()).get('enemies',[])
 for cid in set(c for entries in COUNTS.values() for c,n in entries)|{8}:
  templates[cid]=min([u for u in samples if int(u['class_id'])==cid],key=lambda u:(u['level'],u['max_hp']))
 chars={}
 for key,(source,name) in CHARMAP.items():
  c=copy.deepcopy(ORIGINAL[source]);c.update(id=key,key=key,name_zh=name,source_character=source,side='player',dead=False,acted=False);chars[key]=c
  if key=='roan':c.update(class_id=12,**{'class':'archer'},move=4)
 current_characters=json.loads((R/'data/campaign.json').read_text()).get('characters',{})
 for key in CHARMAP:
  if key in current_characters:chars[key]=copy.deepcopy(current_characters[key])
 dialogue_fixes={'F21': {'during': '莉莎：另一条船的弓手换到右边了。'}, 'F22': {'during': '洛德：我能把右边的跳板放下。后面的人跟我走。'}, 'F23': {'during': '莉莎：那几只硬甲的，我来试。你们看住天上的。'}, 'F24': {'before': '旁白：天早该亮了，海灯岛却仍被黑昼笼罩。岸边术士用自己的生命维持防护。／希雅：我不能现在离开。灯一灭，后面的船就进不来了。／艾琳：那我们先守住它。', 'during': '米蕾：伤者都进屋了。希雅，东边那条船在靠岸。'}, 'F25': {'during': '艾琳：母亲的航图在哪？', 'after': '艾琳：先把牢门边的人带出来。'}, 'F26': {'during': '卡洛：已经能看见西岸了。后面的船跟紧。', 'after': '舵手：西岸到了，居民船已经安全靠岸。／艾琳：让伤者先上岸，我们去海峡城。'}, 'S21': {'before': '米蕾或艾琳：他们船上还有病人，不能就这样走。', 'during': '地方医者：病人的船受伤了，先让护卫站到前面。', 'after': '渔民：北面有个备用停泊点。我把航线告诉船长。'}, 'S22': {'during': '船员：我一直不敢回到家属面前。／卡洛：遗物不能留在这里。我陪你一起送回去。'}}
 reports={}
 for b in [b for b in PLAN['battles'] if b['chapter']==2]:
  code=b['id'];w=b['width'];h=b['height'];rng=random.Random(IDS[code]);naval=code in ['F21','F22','S21'];cave=code=='S22';grid=[['~']*w for _ in range(h)];terrain_notes=[]
  def rect(x0,y0,x1,y1,ch):
   for y in range(max(0,y0),min(h,y1+1)):
    for x in range(max(0,x0),min(w,x1+1)):grid[y][x]=ch
  def path(points,width=1,ch='='):
   for x,y in route(points):rect(x-width//2,y-width//2,x+(width-1)//2,y+(width-1)//2,ch)
  architecture=[];ship_rects=[];rail_cells={}
  if naval:
   right=17 if code=='F21' else 19 if code=='F22' else 15;leftend=11 if code=='F21' else 13 if code=='F22' else 9
   low=h-3
   for x0,x1,y0,y1 in [(2,leftend,3,low),(right,w-3,2,low+1)]:
    rect(x0,y0+1,x1,y1-1,'s');rect(x0+1,y0,x1-1,y0,'s');rect(x0+1,y1,x1-1,y1,'s');ship_rects.append([x0,x1,y0,y1])
   for yy in ([11,13] if code=='F21' else [8,14] if code=='F22' else [10,12]):path([(leftend,yy),(right,yy)],1,'s')
   if code=='F22':path([(16,8),(16,14)],1,'s');path([(3,17),(3,19)],1,'s')
   if code=='S21':path([(3,15),(3,17)],1,'s')
   terrain_notes.append('Two complete timber hulls; ocean never used as a walking shortcut. Boarding lanes are explicit timber cells.')
  elif code=='F26':
   # Broken basalt causeway and parallel sea lane, not a third ship battle.
   path([(4,18),(10,18),(10,15),(16,15),(16,12),(23,12),(23,7),(26,7),(26,4)],3,'=')
   rect(2,16,7,20,'=');rect(21,3,27,8,'=');rect(13,11,18,15,'=');rect(23,12,26,16,'=')
   path([(5,18),(15,18),(15,14)],1,'s');path([(25,14),(25,7)],1,'=')
   rect(2,3,7,6,'=');path([(3,3),(3,17)],1,'s')
   path([(25,18),(29,18),(29,20)],1,'s');path([(25,18),(25,14)],1,'s')
   terrain_notes.append('Ship events use a separate verified water lane; foot units remain on ancient stone and timber causeways.')
  elif cave:
   grid=[['^']*w for _ in range(h)]
   for cx,cy,rx,ry in [(6,15,5.7,3.4),(7,9,4.1,3.2),(14,6,3.7,3.7),(12,12,3.9,3.2)]:
    for y in range(1,h-1):
     for x in range(1,w-1):
      if ((x-cx)/rx)**2+((y-cy)/ry)**2 < 1+.12*math.sin(x*2+y):grid[y][x]='.'
   path([(4,16),(5,10),(10,10),(14,7),(16,3)],2,'.');path([(9,12),(13,12)],2,'.')
   for y in range(11,h):
    for x in range(16 if y<15 else 14,w):grid[y][x]='~'
   terrain_notes.append('Four irregular connected cave chambers and a tidal pool; peaks are whole sprites restricted to impassable rock.')
  else:
   # Organic shore silhouette with broad paths and protected camp clearings.
   cx=w/2;cy=h/2;rx=w/2-2;ry=h/2-2
   for y in range(2,h-2):
    for x in range(2,w-2):
     threshold=1+.05*math.sin(x*.8+y*.4)+.07*math.cos(y*.7)
     if ((x-cx)/rx)**2+((y-cy)/ry)**2<threshold:grid[y][x]='d' if x<7 or x>w-6 or y>h-6 else '.'
   rect(3,3,6,9,'d')
   for cx,cy,rx,ry in [(6,6,2.2,3.1),(w-6,h-7,2.1,1.8),(w/2-4,4,2.4,1.7)]:
    for y in range(2,h-2):
     for x in range(2,w-2):
      if grid[y][x]!='~' and ((x-cx)/rx)**2+((y-cy)/ry)**2<1:grid[y][x]='^'
   if code=='F25':
    rect(11,3,w-4,17,'=');rect(17,18,w-4,20,'=');rect(2,h-6,10,h-3,'s');path([(8,h-5),(13,14)],3,'s')
    # Sea inlet and timber quays distinguish the military harbor.
    rect(7,15,11,18,'~');path([(7,16),(11,16)],1,'s')
   else:path([(4,h-5),(8,h-7),(12,h//2),(w-6,7),(w-5,3)],2,'=')
   terrain_notes.append('Curved shore, sand beaches, irregular basalt and grass clearings; paths are reserved before scenery.')
  # Preserve the production-card anchor coordinates and reach them through
  # meaningful ground lanes; source blueprint marks are not invisible walls.
  deploy=copy.deepcopy(b['deployment_points_by_party'][0]);anchors=deploy+b['targets']+[b['boss'],b['exit']]+b['npc_anchors']+b['reinforcement_anchors']+b['enemy_anchors']
  for x,y in anchors:
   if grid[y][x] in '~^#':
    reachable=[(xx,yy) for yy in range(h) for xx in range(w) if grid[yy][xx] not in '~^#'];nearest=min(reachable,key=lambda p:abs(p[0]-x)+abs(p[1]-y));path([[x,y],nearest],1,'s' if naval or code=='F26' else '.' if cave else 'd')
  reserved=set(tuple(p) for p in anchors)
  # Architectural modules have entire explicit blocked footprints. Buildings
  # stay clear of authored lanes and deploy/goal/NPC cells.
  def stamp(name,at,blocked=True,require=None,force=False):
   mw,mh=mods[name]['footprint'];ox,oy=at;foot={(x,y) for y in range(oy,oy+mh) for x in range(ox,ox+mw)}
   if ox<0 or oy<0 or ox+mw>w or oy+mh>h:return False
   if not force and (foot&reserved or any(grid[y][x] in ('~','=') for x,y in foot)):return False
   if require and any(grid[y][x] not in require for x,y in foot):return False
   if any(foot&set(map(tuple,m['cells'])) for m in architecture):return False
   if blocked:
    for x,y in foot:grid[y][x]='#'
   architecture.append({'name':name,'origin':[ox,oy],'footprint':[mw,mh],'logic':'#' if blocked else 'inherits_ground','cells':[list(p) for p in sorted(foot)]});reserved.update(foot);return True
  if naval:
   for x0,x1,y0,y1 in ship_rects:
    # A complete bow and stern provide silhouette; rails run in true hull cells.
    stamp('bow',[(x0+x1)//2-1,y0-1],False,force=True)
    stamp('stern',[(x0+x1)//2-1,y1-1],False,force=True)
    for yy in range(y0+3,y1-3,4):
     for xx in [x0,x1]:
      foot={(xx,y) for y in range(yy,yy+4)}
      if foot&set(map(tuple,anchors)) or any(grid[y][xx-1 if xx==x0 else xx+1]=='s' for y in range(yy,yy+4) if 0<=xx-1<w and 0<=xx+1<w):continue
      stamp('rail_v',[xx,yy],True,force=True)
    stamp('captain_cabin',[x0+2,y0+2],True,require='s')
    stamp('mast',[x0+3,y0+6],True,require='s')
    for xx,yy in [(x0+1,y1-3),(x1-2,y0+4),(x1-2,y1-4)]:stamp('bollard',[xx,yy],True,require='s')
  elif code=='F24':
   stamp('lighthouse',[14,6],True,force=True);stamp('fishing_hut',[17,17],True);stamp('fishing_hut',[6,14],True)
  elif code=='F25':
   stamp('barracks',[21,1],True,force=True);stamp('captain_cabin',[11,6],True,force=True);stamp('barracks',[19,8],True,force=True)
   stamp('fishing_hut',[4,11],True);stamp('rowboat',[1,14],False,force=True)
   for at in [[3,20],[8,22],[12,19],[27,20]]:stamp('bollard',at,True)
  elif code=='F23':
   stamp('fishing_hut',[9,16],True,force=True);stamp('fishing_hut',[15,7],True);stamp('rowboat',[0,14],False,force=True)
  elif code=='F26':
   stamp('stone_gate',[14,9],True,force=True);stamp('tower_entry',[20,1],True,force=True);stamp('boulders',[11,17],True)
  elif cave:stamp('cave_entry',[1,4],True,force=True)
  # Rails are explicit, continuous hull boundaries with open boarding mouths.
  # Segmented rail art uses edge tiles, while cabins/masts remain whole modules.
  if naval:
   anchor_set=set(map(tuple,anchors))
   for x0,x1,y0,y1 in ship_rects:
    for yy in range(y0,y1+1):
     for xx in range(x0,x1+1):
      if grid[yy][xx]!='s' or (xx,yy) in anchor_set:continue
      sides=[(dx,dy) for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)] if 0<=xx+dx<w and 0<=yy+dy<h and grid[yy+dy][xx+dx]=='~']
      if not sides:continue
      # Do not cut off the protected ship gangways or their approach cells.
      if any(abs(xx-p[0])+abs(yy-p[1])<=1 for p in anchors):continue
      horizontal=any(dy for dx,dy in sides)
      rail_cells[(xx,yy)]=mods['rail_h']['tiles'][0][xx%4] if horizontal else mods['rail_v']['tiles'][yy%4][0]
      grid[yy][xx]='#'
  # Ensure all anchors remain intact after composition; intentional decorative
  # arches sit beside routes rather than being punched through by path repair.
  for p in anchors:
   if grid[p[1]][p[0]] in '#^~':raise AssertionError((code,'covered production anchor',p))
  occupied=set(map(tuple,deploy));enemies=[];npcs=[]
  def free(at):
   q=deque([tuple(at)]);seen=set(q)
   while q:
    x,y=q.popleft()
    if 0<=x<w and 0<=y<h and grid[y][x] not in '#^~' and (x,y) not in occupied:occupied.add((x,y));return [x,y]
    for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
     n=x+dx,y+dy
     if 0<=n[0]<w and 0<=n[1]<h and n not in seen:seen.add(n);q.append(n)
   raise ValueError(code+' no free spawn')
  names={6:'海兵',12:'弓手',15:'术士',2:'重装兵',3:'飞行魔物',11:'腐化魔物',8:'舰长'}
  def enemy(cid,at,i,boss=False):
   u=copy.deepcopy(templates[cid]);hp=34 if boss and code=='F25' else 29 if boss else 26 if cid==2 else 23 if cid==11 else 21
   u.update(id=code+('_boss' if boss else '_e'+str(i)),position=free(at),side='enemy',acted=False,exp=0,item_id=0,group_id=0,raw_ai_flags=0,ai_flags=0,level=5 if boss else 3,hp=hp,max_hp=hp,strength=11 if boss else 9 if cid in [2,11] else 8,skill=6 if boss else 4,speed=6 if cid==3 else 3 if cid in [2,11] else 4,defence=7 if boss else 6 if cid==2 else 3,luck=0,exp_value=50 if boss else 35,magic_flags=1 if cid==15 else 0,raw_magic_flags=1 if cid==15 else 0)
   u['name_zh']='裴萨' if boss and code=='F25' else '封航首领' if boss and code=='F26' else '魔物首领' if boss and code in ['F23','S21','S22'] else '搜捕首领' if boss else names[cid]
   if boss:
    u['objective_boss']=True;u['behavior']='guard';u['item_id']={'F22':49,'F24':4,'S21':4,'S22':49}.get(code,0)
   elif cid in [2,12,15]:u['behavior']='guard'
   if code=='F24' and i in [4,5] and not boss:u['objective_role']='seize_beacon'
   return u
  boss_class=3 if code in ['F23','S21','S22'] else 8 if code in ['F22','F25'] else 6
  enemies.append(enemy(boss_class,b['boss'],0,True))
  for cid,count in COUNTS[code]:
   for i in range(count):enemies.append(enemy(cid,b['enemy_anchors'][(len(enemies)-1)%len(b['enemy_anchors'])],len(enemies)))
  def npc(key,at,name,source='gray',quest='witness',locked=False):
   u=copy.deepcopy(chars.get(key,ORIGINAL[source]));u.update(id=key,name_zh=name,position=free(at),side='player',neutral=True,temporary=True,no_experience=True,controllable=False,acted=False,quest_kind=quest,locked=locked,max_hp=28 if quest in ['ship','camp','patient'] else 24,hp=28 if quest in ['ship','camp','patient'] else 24,defence=6 if quest=='ship' else 4,no_counter=True,move=2)
   if key in chars:
    for field in ['class','class_id','level','hp','max_hp','strength','skill','speed','luck','defence','resistance','move','item_id','magic_flags','magic_level','exp','growths']:u[field]=copy.deepcopy(chars[key][field])
   if key in ['roan','shia']:u.update(battle_guard=True,no_counter=False)
   u['player_slot']=len(deploy)+len(npcs);npcs.append(u);return u
  objects=[]
  def obj(key,kind,at,label,sprite='open_gate',**more):
   o={'id':key,'kind':kind,'position':at,'label':label,'adjacent':True,'sprite':sprite};o.update(more);objects.append(o);return o
  a=b['npc_anchors'];t=b['targets']
  if code=='F21':
   u=npc('friendly_ship',a[0],'己方船','gray','ship');u.update(event_object=True,sprite_path='res://assets/battle_tiles/modules/white_flag.png',sprite_offset=[0,0]);npc('injured_passengers',a[1],'受伤乘客')
   obj('plank_1','inspect',t[0],'检查第一跳板',sprite_path='res://assets/chapter2/modules/gangplank.png',sprite_offset=[-16,0]);obj('plank_2','inspect',t[1],'检查第二跳板',sprite_path='res://assets/chapter2/modules/gangplank.png',sprite_offset=[-16,0])
  elif code=='F22':
   for i,p in enumerate([a[0],[23,7],a[1]]):npc('prisoners_'+str(i),p,'俘虏'+str(i+1),quest='prisoner',locked=True)
   npc('lord',[23,15],'洛德','valbar','prisoner',True)
   obj('prison_door','door',t[0],'打开囚舱','jail_door',unlock_units=['prisoners_0','prisoners_1','prisoners_2','lord']);obj('reserve_bridge','bridge',t[1],'放下备用跳板','open_gate',opens=[[x,13] for x in range(14,20)],sprite_path='res://assets/chapter2/modules/bollard.png',open_art_props=[{'path':'res://assets/chapter2/modules/gangplank.png','position':[224,208]},{'path':'res://assets/chapter2/modules/gangplank.png','position':[272,208]}],open_art_cells=[{'position':[x,13],'base_tile':PACK['base']['timber'][x%4],'clear_layers':[1,2]} for x in range(14,20)])
  elif code=='F23':
   npc('roan',a[0],'罗恩','atlas');npc('fishers',a[1],'渔民营地','gray','camp');obj('camp','inspect',t[0],'查看居民营地','grain_sacks');obj('landing','inspect',t[1],'确认登陆坡')
  elif code=='F24':
   npc('shia',a[0],'希雅','catria');npc('islanders',a[1],'岛民','gray','islanders');obj('beacon','inspect',t[0],'守卫航灯','ritual_lamp',adjacent=False);obj('shelter','shelter',t[1],'安置岛民','clinic_door')
  elif code=='F25':
   npc('sailors0',a[0],'幸存船员','gray','witness',True);npc('sailors1',a[1],'引航者','gray','witness',True);obj('myth_box','story_item',t[0],'取回神教箱','orders_case');obj('pilot_prison','door',t[1],'打开引航者牢门','jail_door',unlock_units=['sailors0','sailors1'])
  elif code=='F26':obj('stone_gate','inspect',t[0],'辨认古石门','aid_plaque');obj('old_beacon','inspect',t[1],'辨认航灯旧座','ritual_lamp')
  elif code=='S21':
   for i,p in enumerate(a):npc('patients'+str(i),p,'病人船组'+str(i+1),'gray','patient')
   obj('ship_guard','inspect',t[0],'查看护船位置');obj('mooring','inspect',t[1],'确认停泊跳板')
  elif code=='S22':
   npc('old_sailor',a[0],'旧船员','gray','sailor',True);npc('wounded',a[1],'同行伤者','gray','sailor',True);obj('relics','story_item',t[0],'取回遗物箱','orders_case');obj('hideout','rescue',t[1],'救出旧船员','open_gate',unlock_units=['old_sailor','wounded'])
  rein=[];rein_turn=4 if code=='F22' else 3 if code=='F24' else 0
  if rein_turn:
   for i in range(2):u=enemy(6,b['reinforcement_anchors'][0],40+i);u['id']=code+'_r'+str(i);rein.append(u)
  protected=set(map(tuple,anchors))|{tuple(u['position']) for u in enemies+npcs+rein}
  for o in objects:
   x,y=o['position'];mw,mh=mods[o['sprite']]['footprint'];protected.update((xx,yy) for yy in range(y-mh+1,y+1) for xx in range(x,x+mw))
  layers=[[[None]*w for _ in range(h)] for _ in range(4)]
  def mask_at(x,y,pred):
   mask=0
   for dx,dy,bit in wb.PEERS:
    if 0<=x+dx<w and 0<=y+dy<h and pred(grid[y+dy][x+dx]):mask|=bit
   return wb.canonical(mask)
  for y in range(h):
   for x in range(w):
    ch=grid[y][x];v=rng.randrange(4);material={'d':'sand','=':'stone','s':'timber','~':'sea','#':'timber' if naval else 'stone','^':'cave' if cave else 'rock'}.get(ch,'cave' if cave else 'grass');layers[0][y][x]=PACK['base'][material][v]
    if ch not in '~s#' and any(0<=x+dx<w and 0<=y+dy<h and grid[y+dy][x+dx]=='~' for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]):
     coast_mat='cave' if cave else 'stone' if ch=='=' else 'sand';layers[0][y][x]=coasts[coast_mat][str(mask_at(x,y,lambda c:c!='~'))][v]
    if ch=='^':layers[0][y][x]=PACK['base']['rock'][v]
  for (xx,yy),tid in rail_cells.items():layers[1][yy][xx]=tid
  for m in architecture:
   ox,oy=m['origin']
   for dy,row in enumerate(mods[m['name']]['tiles']):
    for dx,tid in enumerate(row):layers[2][oy+dy][ox+dx]=tid
  # Sparse irregular complete basalt and trees. No clipped fragments, no
  # repeated 3x3 clumps; every sprite's full footprint excludes all paths.
  nature=[];taken=set();candidates=[(x,y) for y in range(h) for x in range(w) if grid[y][x]=='^'];rng.shuffle(candidates)
  for x,y in candidates:
   if (x,y) in taken:continue
   choice=rng.choice(['crag_tall','peak_low','ridge_bent','outcrop']);m=NATURE[choice];mw=math.ceil(m['size'][0]/16);mh=math.ceil(m['size'][1]/16);foot={(xx,yy) for yy in range(y,y+mh) for xx in range(x,x+mw)}
   if x+mw>w or y+mh>h or foot&protected or foot&taken or any(grid[yy][xx]!='^' for xx,yy in foot):choice='boulder';m=NATURE[choice];mw=mh=1;foot={(x,y)}
   if foot&protected:continue
   if choice=='boulder' and rng.random()>.18:continue
   taken.update(foot);nature.append({'key':choice,'position':[x*16,y*16],'flip':rng.choice([False,True])})
  for _ in range(16 if code in ['F23','F24'] else 0):
   x=rng.randrange(2,w-2);y=rng.randrange(2,h-2);foot={(xx,yy) for yy in range(y,y+2) for xx in range(x,x+2)}
   if foot&protected or foot&taken or any(grid[yy][xx]!='.' for xx,yy in foot):continue
   key=rng.choice(['pine_tall','pine_broad']);taken.update(foot);nature.append({'key':key,'position':[x*16,y*16],'flip':rng.choice([False,True])})
   for xx,yy in foot:grid[yy][xx]='f'
  nature.sort(key=lambda p:p['position'][1]+NATURE[p['key']]['size'][1])
  # Doors are genuine blocked logic cells until interaction opens them.
  for o in objects:
   if o['kind']=='door':grid[o['position'][1]][o['position'][0]]='#'
  event_boats=[]
  if code=='F26':
   boatpath=route([[4,21],[30,21],[30,6]])
   for p in boatpath:
    if grid[p[1]][p[0]]!='~':raise AssertionError(('boat path is not sea',p))
   event_boats=[{'id':'event_boat_'+str(i),'label':'居民船'+str(i+1),'hp':30,'max_hp':30,'path':[list(p) for p in boatpath],'path_index':0,'delay':i*2,'speed':3,'sprite_path':'res://assets/chapter2/modules/rowboat.png'} for i in range(2)]
  data={'schema_version':4,'id':IDS[code],'code':code,'name_zh':b['name'],'chapter':2,'route':'celica','node':next(n['numeric_id'] for n in WORLD['nodes'].values() if n['id']==b['node']),'map':{'width':w,'height':h,'tiles':[OLD[c] for row in grid for c in row]},'logic_grid':[''.join(row) for row in grid],'art_atlas':'res://assets/chapter2/chapter2-tiles.png','art_columns':32,'art_layers':layers,'art_modules':architecture,'natural_props':nature,'art_style_version':'chapter2-1','surroundings_biome':'sea' if not cave else 'rock','surroundings':'cave' if cave else 'sea','nature_layout':{'biome':'rock' if cave else 'sea','props':[]},'event_boat_sprite':'res://assets/chapter2/modules/rowboat.png','characters':chars,'player_positions':deploy,'enemies':enemies,'npc_units':npcs,'terrain':copy.deepcopy(json.loads((R/'data/stages/M11.json').read_text())['terrain']),'enemy_group_ids':[],'objects':objects,'reinforcements':rein,'reinforcement_turn':rein_turn,'exit':b['exit'],'boss_id':code+'_boss','targets':t,'goal':b['goal'],'cause':b['cause'],'before':b['before'],'during':b['during'],'after':b['after'],'absent_branch':b.get('absent_branch',''),'optional':b['optional'],'contract':b['interaction_contract'],'ai_and_timing':b['ai_and_timing'],'event_boats':event_boats,'production_anchors':{'deploy':deploy,'boss':b['boss'],'targets':t,'exit':b['exit'],'npc':a,'reinforcements':b['reinforcement_anchors']},'visual_notes':terrain_notes}
  data.update(dialogue_fixes.get(code,{}))
  refine_prison_geometry(data,mods)
  grid=[list(row) for row in data['logic_grid']]
  refine_harbor_art(data,mods)
  if code=='F24':data['map_tint']=[0.66,0.72,0.84,1.0]
  # Static walk connectivity includes the eventual opened-door state and every
  # enemy/NPC/goal. Adjacent interact cells must be reachable before opening.
  opens={tuple(cell) for o in objects if o['kind']=='door' for cell in o.get('opens',[o['position']])};start=tuple(deploy[0]);q=deque([start]);seen={start}
  while q:
   x,y=q.popleft()
   for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
    n=x+dx,y+dy
    if 0<=n[0]<w and 0<=n[1]<h and n not in seen and (grid[n[1]][n[0]] not in '#^~' or n in opens):seen.add(n);q.append(n)
  goals=deploy+[b['boss'],b['exit']]+t+[u['position'] for u in enemies+npcs+rein]
  disconnected=[p for p in goals if tuple(p) not in seen]
  if disconnected:raise AssertionError((code,'unreachable',disconnected))
  write(R/'data/stages'/f'{code}.json',data)
  # Map review contains only actual atlas tiles and whole runtime sprites.
  rendered=Image.new('RGBA',(w*16,h*16))
  for layer in layers:
   for y,row in enumerate(layer):
    for x,tid in enumerate(row):
     if tid is not None:rendered.alpha_composite(atlas.crop((tid%32*16,tid//32*16,tid%32*16+16,tid//32*16+16)),(x*16,y*16))
  for p in nature:
   im=Image.open(R/NATURE[p['key']]['path'].removeprefix('res://')).convert('RGBA')
   if p['flip']:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
   rendered.alpha_composite(im,tuple(p['position']))
  rendered.convert('RGB').save(REPORT/f'{code}-map.png');opt(REPORT/f'{code}-map.png')
  reports[code]={'dimensions':[w,h],'enemies':len(enemies),'reinforcements':len(rein),'NPCs':len(npcs),'walkable_cells':len(seen),'checked_positions':len(goals),'all_targets_reachable':not disconnected,'modules':len(architecture),'whole_nature_sprites':len(nature),'boats':len(event_boats),'map_bytes':(REPORT/f'{code}-map.png').stat().st_size}
 write(REPORT/'build-report.json',reports);print(json.dumps(reports,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
