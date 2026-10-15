#!/usr/bin/env python3
"""Produce native world tiles from generated material/module art; no scene slicing."""
from pathlib import Path
from collections import Counter, deque
import json, math, subprocess, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/world_tiles'
SRC=ROOT/'source/world-tiles-b'
REPORT=ROOT/'reports/world-tiles-b'
T=16
COLS=32
MATERIALS=['grass','sea','sand','snow','salt','marsh','forest','rock','stone','dirt','timber','sacred']
NAMES=['草地','海水','沙地','雪地','盐原','沼泽','森林','岩地','石路','土路','木桥','神宫石地']
TERRAIN_IDS={k:i for i,k in enumerate(MATERIALS)}
BLENDS=[('coast_grass','grass','sea'),('coast_snow','snow','sea'),
 ('coast_sand','sand','sea'),('coast_salt','salt','sea'),
 ('forest_edge','forest','grass'),('snow_edge','snow','grass'),
 ('sand_edge','sand','grass'),('salt_edge','salt','grass'),
 ('marsh_edge','marsh','grass'),('rock_edge','rock','grass')]
PEERS=[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8),(1,-1,16),(1,1,32),(-1,1,64),(-1,-1,128)]

def canonical(m):
 for diagonal,a,b in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
  if not (m&a and m&b):m&=~diagonal
 return m
MASKS=sorted({canonical(i) for i in range(256)})
assert len(MASKS)==47

def alpha_mask(m):
 """47 canonical corner-and-side masks; shared borders are exact, no AA."""
 im=Image.new('L',(T,T))
 for y in range(T):
  for x in range(T):
   left=x<8;top=y<8
   a=8 if left else 2;b=1 if top else 4
   diag={(True,True):128,(False,True):16,(False,False):32,(True,False):64}[(left,top)]
   u=x if left else 15-x;v=y if top else 15-y
   if m&a and m&b:
    inside=bool(m&diag) or u*u+v*v>=9
   elif m&a:inside=v>=3
   elif m&b:inside=u>=3
   else:inside=(x-7.5)**2+(y-7.5)**2<=25
   if inside:im.putpixel((x,y),255)
 return im

def normalize_border(im, color):
 # Common one-pixel outer border makes arbitrary base texture variants repeat.
 im=im.copy();d=ImageDraw.Draw(im)
 d.rectangle((0,0,15,15),outline=color,width=1)
 return im

def extract_materials():
 src=Image.open(SRC/'materials-generated.png').convert('RGB');w,h=src.size
 result={};colors={}
 for i,name in enumerate(MATERIALS):
  box=(round(i%4*w/4),round(i//4*h/3),round((i%4+1)*w/4),round((i//4+1)*h/3))
  tile=src.crop(box).resize((T,T),Image.Resampling.NEAREST)
  tile=tile.quantize(colors=4,dither=Image.Dither.NONE).convert('RGB')
  base=Counter(tile.getdata()).most_common(1)[0][0];colors[name]=base
  result[name]=[]
  for v in range(4):
   variant=ImageChops.offset(tile,(v%2)*5,(v//2)*5)
   result[name].append(normalize_border(variant,base).convert('RGBA'))
 return result,colors

def cut_modules(file,columns,rows,specs):
 src=Image.open(SRC/file).convert('RGBA');w,h=src.size;out=[]
 # Own complete alpha components, including a ridge that crosses the nominal
 # sheet row. Ignore detached single-pixel residues instead of cropping a tip.
 bits=bytearray(a>64 for a in src.getchannel('A').getdata());groups={i:[] for i in range(len(specs))}
 for j in range(w*h):
  if not bits[j]:continue
  q=deque([j]);bits[j]=0;component=[];sx=sy=0
  while q:
   p=q.popleft();x=p%w;y=p//w;component.append(p);sx+=x;sy+=y
   for n in [p-1 if x else -1,p+1 if x<w-1 else -1,p-w if y else -1,p+w if y<h-1 else -1]:
    if n>=0 and bits[n]:bits[n]=0;q.append(n)
  if len(component)<40:continue
  cx=min(columns-1,int((sx/len(component))/w*columns));cy=min(rows-1,int((sy/len(component))/h*rows))
  groups[cy*columns+cx].extend(component)
 for i,(name,gw,gh,kind) in enumerate(specs):
  owned=Image.new('L',src.size)
  for p in groups[i]:owned.putpixel((p%w,p//w),255)
  box=owned.getbbox();cell=src.copy();cell.putalpha(owned)
  assert box, name
  # Native footprint is chosen up front; preserve shape aspect and full silhouette.
  cell=cell.crop(box);target=(gw*T-2,gh*T-2)
  scale=min(target[0]/cell.width,target[1]/cell.height)
  cell=cell.resize((max(1,round(cell.width*scale)),max(1,round(cell.height*scale))),Image.Resampling.NEAREST)
  cell=cell.quantize(colors=32,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
  canvas=Image.new('RGBA',(gw*T,gh*T))
  canvas.alpha_composite(cell,((canvas.width-cell.width)//2,canvas.height-cell.height-1))
  canvas.save(OUT/'modules'/f'{name}.png',optimize=True)
  out.append((name,gw,gh,kind,canvas,box))
 return out

TERRAIN_SPECS=[('tree',1,1,'forest'),('pine',1,1,'forest'),('grove',2,2,'forest'),
 ('pine_grove',2,2,'forest'),('snow_pine',1,1,'forest'),('snow_grove',2,2,'forest'),
 ('rocks',1,1,'rock'),('ridge_small',2,1,'rock'),('snow_ridge_small',2,1,'rock'),
 ('reeds',1,1,'marsh'),('ledge_small',2,1,'rock'),('lilies',1,1,'marsh')]
PATCH_SPECS=[('forest_mass',4,3,'forest'),('woodland_mass',4,3,'forest'),
 ('mountain_north_south',4,4,'rock'),('mountain_east_west',4,2,'rock'),
 ('snow_forest_mass',4,3,'forest'),('snow_mountain_mass',4,3,'rock'),
 ('cliff_edge',4,1,'rock'),('marsh_mass',4,3,'marsh')]
SYMBOL_SPECS=[('village',1,1,'landmark'),('snow_village',1,1,'landmark'),
 ('harbor',2,2,'landmark'),('fort',2,1,'landmark'),('capital',2,2,'landmark'),
 ('temple',2,1,'landmark'),('sun_tower',1,2,'landmark'),('cave',1,1,'landmark'),
 ('lighthouse',1,2,'landmark'),('observatory',2,1,'landmark'),('sand_city',2,1,'landmark'),
 ('stockade',2,1,'landmark'),('camp',1,1,'landmark'),('cutter',1,1,'landmark'),
 ('galleon',2,1,'landmark'),('library',2,1,'landmark')]

def blend_tile(fore,bg,mask,coast,colors,preserve_pattern=False):
 a=alpha_mask(mask);im=fore.copy();im.putalpha(a)
 # Quiet single-pixel shore/biome line uses shades from the generated palette.
 f=colors['fg'];b=colors['bg']
 shadow=tuple(max(0,round(v*.88)) for v in f)
 foam=tuple(round(b[j]*.72+(183,187,194)[j]*.28) for j in range(3))
 data=a.load()
 for y in range(16):
  for x in range(16):
   own=data[x,y]>0
   nearby=[data[max(0,min(15,x+dx)),max(0,min(15,y+dy))]>0 for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]]
   if own and not all(nearby):im.putpixel((x,y),shadow+(255,))
   elif coast and not own and any(nearby):im.putpixel((x,y),foam+(255,))
 if coast:
  result=bg.copy();result.alpha_composite(im);im=result
 # Boundary colors depend only on the shared one-dimensional mask profile.
 # This avoids false strokes from treating a tile frame as a coast boundary.
 for axis in ('x','y'):
  for fixed in (0,15):
   for t in range(16):
    x,y=(fixed,t) if axis=='x' else (t,fixed)
    own=data[x,y]>0
    at=lambda q:data[fixed,q]>0 if axis=='x' else data[q,fixed]>0
    near=any(at(q) for q in (max(0,t-1),min(15,t+1)))
    edge=own and not all(at(q) for q in (max(0,t-1),min(15,t+1)))
    if own:im.putpixel((x,y),(shadow+(255,) if edge else fore.getpixel((x,y)) if preserve_pattern else f+(255,)))
    elif coast:im.putpixel((x,y),(foam if near else b)+(255,))
    else:im.putpixel((x,y),(0,0,0,0))
 return im

def route_alpha(mask):
 im=Image.new('L',(T,T));d=ImageDraw.Draw(im)
 d.ellipse((5,5,10,10),fill=255)
 if mask&1:d.rectangle((5,0,10,8),fill=255)
 if mask&2:d.rectangle((7,5,15,10),fill=255)
 if mask&4:d.rectangle((5,7,10,15),fill=255)
 if mask&8:d.rectangle((0,5,8,10),fill=255)
 return im

def main():
 OUT.mkdir(exist_ok=True,parents=True);(OUT/'modules').mkdir(exist_ok=True)
 REPORT.mkdir(exist_ok=True,parents=True)
 mats,colors=extract_materials();records=[];images={};base={};families=[];roads={};overlays={}
 mods=cut_modules('terrain-modules-generated.png',4,3,TERRAIN_SPECS)
 mods+=cut_modules('biome-metatiles-generated.png',4,2,PATCH_SPECS)
 mods+=cut_modules('world-symbols-generated.png',4,4,SYMBOL_SPECS)
 # Dense interior canopy from the complete generated forest patch. It belongs
 # in repeatable forest tiles, rather than isolated tree icons on every cell.
 forest_mass=next(m[4] for m in mods if m[0]=='forest_mass')
 canopy=forest_mass.crop((24,16,40,32))
 opaque=[rgb[:3] for rgb in canopy.getdata() if rgb[3]==255]
 common=[c for c,n in Counter(opaque).most_common(6)]
 colors['forest']=min(common,key=lambda c:sum(c))
 template=Image.new('RGBA',(16,16),colors['forest']+(255,));template.alpha_composite(canopy)
 for y in range(16):template.putpixel((15,y),template.getpixel((0,y)))
 for x in range(16):template.putpixel((x,15),template.getpixel((x,0)))
 for v in range(4):
  fill=Image.new('RGBA',(16,16),colors['forest']+(255,))
  fill.alpha_composite(ImageChops.offset(canopy,(v%2)*5,(v//2)*5))
  for q in range(16):
   for px,py in [(0,q),(15,q),(q,0),(q,15)]:fill.putpixel((px,py),template.getpixel((px,py)))
  mats['forest'][v]=fill
 def add(im,name,terrain,**extra):
  i=len(records);record={'id':i,'atlas':[i%COLS,i//COLS],'name':name,'terrain':terrain,
    'terrain_id':TERRAIN_IDS.get(terrain,-1),'kind':'ground',**extra}
  records.append(record);images[i]=im;return i
 for name in MATERIALS:
  base[name]=[add(mats[name][v],f'{name}_{v}',name,variant=v) for v in range(4)]
 for set_id,(name,fg,bg) in enumerate(BLENDS):
  coast=name.startswith('coast');ids={}
  for m in MASKS:
   tile=blend_tile(mats[fg][0],mats[bg][0],m,coast,{'fg':colors[fg],'bg':colors[bg]},fg=='forest')
   ids[str(m)]=add(tile,f'{name}_{m:02x}',fg,kind='coast' if coast else 'biome_overlay',
     family=name,mask=m,terrain_set=set_id,terrain_index=1,background=bg)
  empty=mats[bg][0] if coast else Image.new('RGBA',(T,T))
  back=add(empty,f'{name}_background',bg,kind='auto_background',family=name,
           terrain_set=set_id,terrain_index=0,mask=0,background=bg)
  families.append({'name':name,'foreground':fg,'background':bg,'terrain_set':set_id,'tiles_by_mask':ids,'background_tile':back,'opaque_background':coast})
 for name in ['grass','snow','sand','salt','rock']:
  roads[name]={}
  for m in range(16):
   path=mats['dirt'][0].copy();path.putalpha(route_alpha(m))
   tile=mats[name][0].copy();tile.alpha_composite(path)
   roads[name][str(m)]=add(tile,f'road_{name}_{m:x}',name,kind='road',route_mask=m,route='land')
 for route,color in [('sea',(171,184,205)),('sacred',(165,146,99))]:
  overlays[route]={}
  for m in range(16):
   tile=Image.new('RGBA',(T,T));d=ImageDraw.Draw(tile);d.rectangle((7,7,8,8),fill=color+(255,))
   for bit,dx,dy in [(1,0,-1),(2,1,0),(4,0,1),(8,-1,0)]:
    if m&bit:
     for dist in (4,8):
      x=8+dx*dist;y=8+dy*dist
      d.rectangle((max(0,x-1),max(0,y-1),min(15,x),min(15,y)),fill=color+(255,))
   overlays[route][str(m)]=add(tile,f'route_{route}_{m:x}',route,kind='route_overlay',route_mask=m,route=route)
 bridges={}
 for direction in ['horizontal','vertical']:
  tile=mats['sea'][0].copy();wood=mats['timber'][0].copy();a=Image.new('L',(16,16));d=ImageDraw.Draw(a)
  d.rectangle((0,4,15,11) if direction=='horizontal' else (4,0,11,15),fill=255)
  wood.putalpha(a);tile.alpha_composite(wood)
  d=ImageDraw.Draw(tile);dark=tuple(round(c*.6) for c in colors['timber'])+(255,)
  if direction=='horizontal':d.line((0,4,15,4),fill=dark);d.line((0,11,15,11),fill=dark)
  else:d.line((4,0,4,15),fill=dark);d.line((11,0,11,15),fill=dark)
  bridges[direction]=add(tile,f'bridge_{direction}','sea',kind='bridge',route='bridge',route_mask=10 if direction=='horizontal' else 5)
 # Module footprints occupy real rectangular regions in the same atlas.
 while len(records)%COLS:add(Image.new('RGBA',(16,16)),'unused','none',kind='unused')
 module_start=len(records)//COLS
 modules=[]
 for index,(name,gw,gh,kind,canvas,source_box) in enumerate(mods):
  gx=(index%8)*4;gy=module_start+(index//8)*4;ids=[]
  for y in range(gh):
   row=[]
   for x in range(gw):
    i=(gy+y)*COLS+gx+x
    records.append({'id':i,'atlas':[gx+x,gy+y],'name':f'{name}_{x}_{y}','terrain':kind,
      'terrain_id':-1,'kind':'module','module':name,'module_cell':[x,y],'inherits_ground_terrain':True})
    images[i]=canvas.crop((x*T,y*T,(x+1)*T,(y+1)*T));row.append(i)
   ids.append(row)
  modules.append({'name':name,'kind':kind,'footprint':[gw,gh],'tiles':ids,
    'path':f'modules/{name}.png','source_bbox':source_box,'anchor':[gw//2,gh-1],
    'world_symbol_only':kind=='landmark','inherits_ground_terrain':True})
 height=(module_start+math.ceil(len(modules)/8)*4)*T
 atlas=Image.new('RGBA',(COLS*T,height))
 for i,im in images.items():atlas.alpha_composite(im,((i%COLS)*T,(i//COLS)*T))
 atlas.save(OUT/'world-tiles.png',optimize=True)
 records.sort(key=lambda r:r['id'])
 pack={'schema':1,'name':'revenge-memories 世界地图瓦片 B 朴素复古','native_tile_size':T,
   'columns':COLS,'atlas':'world-tiles.png','image_size':list(atlas.size),'style':'B 朴素复古',
   'scale_reference':'外传16px世界地图地理符号，显示采用最近邻整数放大',
   'mask_bits':{'N':1,'E':2,'S':4,'W':8,'NE':16,'SE':32,'SW':64,'NW':128},
   'canonical_masks':MASKS,'terrains':[{'id':i,'key':k,'name':NAMES[i]} for i,k in enumerate(MATERIALS)],
   'base_tiles':base,'families':families,'roads':roads,'route_overlays':overlays,'bridges':bridges,
   'modules':modules,'tiles':records,'materials':{k:list(v) for k,v in colors.items()},
   'scope':'世界地图资源与可重复拼接样图；战术移动费用、毒沼伤害及关卡解锁未接入。'}
 (OUT/'world-tiles.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n')
 # A standard atlas import file for Tiled; per-tile semantic fields are explicit.
 ts=ET.Element('tileset',{'version':'1.10','tiledversion':'1.10','name':'revenge_world_b','tilewidth':'16','tileheight':'16','tilecount':str(atlas.width*atlas.height//256),'columns':str(COLS)})
 ET.SubElement(ts,'image',{'source':'world-tiles.png','width':str(atlas.width),'height':str(atlas.height)})
 for r in records:
  if r['kind']=='unused':continue
  tile=ET.SubElement(ts,'tile',{'id':str(r['id'])});props=ET.SubElement(tile,'properties')
  for key,value in [('name',r['name']),('terrain_id',r['terrain_id']),('terrain_key',r['terrain']),('kind',r['kind']),('family',r.get('family','')),('route_mask',r.get('route_mask',-1)),('module',r.get('module',''))]:
   attrs={'name':key,'value':str(value)}
   if isinstance(value,int):attrs['type']='int'
   ET.SubElement(props,'property',attrs)
 ET.indent(ts);ET.ElementTree(ts).write(OUT/'world-tiles.tsx',encoding='utf-8',xml_declaration=True)
 samples=make_samples(pack,images)
 (OUT/'sample-maps.json').write_text(json.dumps(samples,ensure_ascii=False,indent=2)+'\n')
 lab={'pack':pack,'samples':samples}
 (ROOT/'world-tiles').mkdir(exist_ok=True)
 (ROOT/'world-tiles/data.js').write_text('window.WORLD_TILES_LAB = '+json.dumps(lab,ensure_ascii=False)+';\n')
 atlas.resize((atlas.width*2,atlas.height*2),Image.Resampling.NEAREST).save(REPORT/'atlas-2x.png',optimize=True)
 make_module_board(modules)
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',*map(str,OUT.rglob('*.png'))],check=True,capture_output=True)
 manifest=[]
 for p in sorted([*OUT.rglob('*.png'),*REPORT.glob('*.png')]):
  im=Image.open(p)
  manifest.append({'path':str(p.relative_to(ROOT)),'pixels':list(im.size),'bytes':p.stat().st_size,
    'purpose':'完整地图模块' if p.parent.name=='modules' else ('16px瓦片图集' if p.name=='world-tiles.png' else '实际瓦片拼接/原尺寸对照审阅图'),
    'quality_note':'保持原生像素与完整轮廓，超过参考体积时保留清晰度。' if p.stat().st_size>=200000 else ''})
 (REPORT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'native_tile_size':16,'valid_tiles':len([r for r in records if r['kind']!='unused']),
  'transition_families':len(families),'modules':len(modules),'atlas_size':list(atlas.size)},ensure_ascii=False))

def mask_at(grid,x,y,predicate):
 h=len(grid);w=len(grid[0]);m=0
 for dx,dy,b in PEERS:
  xx,yy=x+dx,y+dy
  if 0<=xx<w and 0<=yy<h and predicate(grid[yy][xx]):m|=b
 return canonical(m)

def make_samples(pack,images):
 """Authored world-scale geography; maps store tile IDs and independent terrain."""
 w,h=48,40
 land=Image.new('L',(w,h));d=ImageDraw.Draw(land)
 for poly in [[(4,7),(9,4),(16,5),(20,9),(19,15),(23,19),(22,25),(18,30),(17,36),(9,38),(4,34),(2,29),(4,23),(2,16)],
              [(33,7),(41,6),(46,10),(45,17),(40,22),(34,20),(30,15)],
              [(32,28),(36,26),(39,29),(38,33),(34,34),(31,31)],
              [(40,23),(44,23),(46,26),(43,28),(40,26)],
              [(40,33),(45,34),(46,37),(43,39),(39,37)],
              [(23,2),(28,1),(31,4),(29,7),(25,7),(22,4)]]:d.polygon(poly,fill=255)
 d.ellipse((9,20,12,23),fill=0)
 # Drop one-cell polygon tips; coast caps remain available for deliberately
 # authored narrow peninsulas, but aren't sprayed along this geography sample.
 for _ in range(2):
  remove=[]
  for yy in range(h):
   for xx in range(w):
    if land.getpixel((xx,yy)) and sum(0<=xx+dx<w and 0<=yy+dy<h and land.getpixel((xx+dx,yy+dy))>0 for dx,dy,_ in PEERS[:4])<2:remove.append((xx,yy))
  for point in remove:land.putpixel(point,0)
 terrain=[['grass' if land.getpixel((x,y)) else 'sea' for x in range(w)] for y in range(h)]
 def paint(poly,key):
  m=Image.new('L',(w,h));ImageDraw.Draw(m).polygon(poly,fill=255)
  for y in range(h):
   for x in range(w):
    if m.getpixel((x,y)) and terrain[y][x]!='sea':terrain[y][x]=key
 paint([(3,28),(9,25),(17,30),(18,38),(5,39)],'snow')
 paint([(7,10),(13,8),(17,14),(14,19),(8,18)],'forest')
 paint([(4,20),(8,19),(9,25),(5,27)],'forest')
 paint([(12,27),(17,25),(19,30),(15,34)],'forest')
 paint([(32,13),(37,12),(44,15),(44,20),(35,22)],'sand')
 paint([(39,9),(45,9),(44,14),(41,14)],'salt')
 paint([(31,8),(38,7),(40,12),(34,14)],'marsh')
 paint([(6,5),(9,6),(8,15),(5,18),(3,15)],'rock')
 paint([(14,18),(18,20),(18,26),(15,28),(13,24)],'rock')
 paint([(23,2),(31,2),(31,7),(23,7)],'sacred')
 family={f['name']:f for f in pack['families']}
 layers=[[[pack['base_tiles']['sea'][(x+2*y)%4] for x in range(w)] for y in range(h)],
         [[-1]*w for _ in range(h)], [[-1]*w for _ in range(h)], [[-1]*w for _ in range(h)]]
 biome_names={'forest':'forest_edge','snow':'snow_edge','sand':'sand_edge','salt':'salt_edge','marsh':'marsh_edge','rock':'rock_edge'}
 for y in range(h):
  for x in range(w):
   key=terrain[y][x]
   if key=='sea':continue
   m=mask_at(terrain,x,y,lambda k:k!='sea')
   # All shoreline types are explicit atlas cells. Inland changes use additive
   # foreground tiles over land, keeping ocean below the exact shared silhouette.
   coast='coast_'+key if key in ['snow','sand','salt'] else 'coast_grass'
   layers[1][y][x]=family[coast]['tiles_by_mask'][str(m)]
   if key in biome_names and key!='rock':
    bm=mask_at(terrain,x,y,lambda k:k==key)
    layers[2][y][x]=family[biome_names[key]]['tiles_by_mask'][str(bm)]
   elif key=='sacred':layers[2][y][x]=pack['base_tiles']['sacred'][0]
 def path(points,sea=False):
  cells=[]
  for (x0,y0),(x1,y1) in zip(points,points[1:]):
   assert x0==x1 or y0==y1
   dx=(x1>x0)-(x1<x0);dy=(y1>y0)-(y1<y0)
   cells += [(x0+dx*t,y0+dy*t) for t in range(abs(x1-x0)+abs(y1-y0)+1)]
  return set(cells)
 roads=set();lanes=set();sacred=set()
 for p in [[(10,35),(10,31),(13,31),(13,28),(12,28),(12,24),(16,24),(16,19),(19,19)],
           [(19,19),(19,17),(15,17),(15,14),(11,14),(11,9),(13,9),(13,6)],
           [(10,31),(7,31)],[(12,24),(7,24)],[(11,14),(8,14)],[(15,17),(18,17)],
           [(33,18),(37,18),(37,14),(42,14),(42,10)],[(37,14),(35,14),(35,9)]]:roads|=path(p)
 for p in [[(19,19),(25,19),(25,18),(33,18)],[(33,18),(33,24),(34,24),(34,30)],
           [(34,30),(43,30),(43,36)],[(43,30),(43,25)]]:lanes|=path(p,True)
 sacred|=path([(13,6),(20,6),(20,4),(26,4)])
 for cells,kind in [(roads,'land'),(lanes,'sea'),(sacred,'sacred')]:
  for x,y in cells:
   m=sum(b for dx,dy,b in PEERS[:4] if (x+dx,y+dy) in cells)
   if kind=='land':
    key=terrain[y][x];key=key if key in pack['roads'] and key!='rock' else 'grass'
    if terrain[y][x]=='sea':layers[3][y][x]=pack['bridges']['horizontal' if m&10 else 'vertical']
    else:layers[3][y][x]=pack['roads'][key][str(m)]
   else:layers[3][y][x]=pack['route_overlays'][kind][str(m)]
 placement=[('snow_village',10,35),('village',7,24),('fort',12,28),('harbor',18,18),
 ('camp',18,16),('capital',12,5),('sun_tower',10,8),('temple',25,3),('cave',7,30),
 ('sand_city',32,17),('observatory',41,9),('temple',34,8),('stockade',41,13),
 ('lighthouse',42,24),('village',34,30),('village',43,36),('cutter',28,21),('galleon',37,25),
 ('library',28,5),('forest_mass',8,10),('woodland_mass',10,15),('forest_mass',5,21),
 ('woodland_mass',14,26),('snow_forest_mass',5,31),('snow_forest_mass',11,32),
 ('mountain_north_south',4,8),('mountain_east_west',8,6),('mountain_north_south',14,20),
 ('snow_mountain_mass',13,29),('marsh_mass',31,10),('cliff_edge',37,20),('pine_grove',33,28)]
 # Dense world-scale tree/crest cells make continuous masses, with road corridors
 # preserved. Complete multi-tile modules stay separate when their bounds overlap.
 placement += [('mountain_north_south',4,10),('mountain_north_south',4,13),
               ('mountain_east_west',7,6),('mountain_north_south',13,22),
               ('mountain_north_south',13,25)]
 module_by={m['name']:m for m in pack['modules']}
 module_layers=[];occupied=[]
 for name,px,py in placement:
  module=module_by[name]
  gw,gh=module['footprint'];foot={(px+x,py+y) for x in range(gw) for y in range(gh)}
  target=next((i for i,o in enumerate(occupied) if not o&foot),len(module_layers))
  if target==len(module_layers):module_layers.append([[-1]*w for _ in range(h)]);occupied.append(set())
  occupied[target]|=foot
  for y,row in enumerate(module['tiles']):
   for x,i in enumerate(row):
    if 0<=px+x<w and 0<=py+y<h:module_layers[target][py+y][px+x]=i
 layers.extend(module_layers)
 scene={'name':'世界地图拼接样图','width':w,'height':h,'terrain':terrain,'layers':layers,
        'placements':[{'module':n,'position':[x,y]} for n,x,y in placement],
        'note':'资源验收样图，展示西大陆/群岛/神宫地形；不是39节点剧情地图的运行接入。'}
 render_map(scene,images,REPORT/'world-sample.png')
 # Opposite aspect ratios, same atlas and same modules: no image stretching.
 cropped=[]
 for name,rect in [('西大陆样图',(0,3,24,40)),('东群岛样图',(29,5,48,40))]:
  x0,y0,x1,y1=rect
  data={'name':name,'width':x1-x0,'height':y1-y0,'terrain':[r[x0:x1] for r in terrain[y0:y1]],
        'layers':[[r[x0:x1] for r in layer[y0:y1]] for layer in layers]}
  cropped.append(data)
 coast_test=[[True]*18 for _ in range(10)]
 for x,y in [(0,0),(1,0),(0,1),(7,3),(8,3),(7,4),(8,4),(15,0),(16,0),(17,0),(17,1),(17,2),(3,8),(3,9),(4,9)]:coast_test[y][x]=False
 testlayers=[[],[]]
 for y,row in enumerate(coast_test):
  a=[];b=[]
  for x,on in enumerate(row):
   a.append(pack['base_tiles']['sea'][0]);b.append(family['coast_grass']['tiles_by_mask'][str(mask_at(coast_test,x,y,bool))] if on else -1)
  testlayers[0].append(a);testlayers[1].append(b)
 test={'name':'海岸凹角、凸角与内湖检查','width':18,'height':10,'terrain':[['grass' if v else 'sea' for v in r] for r in coast_test],'layers':testlayers}
 render_map(test,images,REPORT/'coast-test.png')
 return [scene,*cropped,test]

def render_map(data,images,path):
 im=Image.new('RGBA',(data['width']*T,data['height']*T))
 for layer in data['layers']:
  for y,row in enumerate(layer):
   for x,i in enumerate(row):
    if i>=0:im.alpha_composite(images[i],(x*T,y*T))
 im.save(path,optimize=True)
 if path.name=='world-sample.png':im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST).save(path.with_name('world-sample-2x.png'),optimize=True)

def make_module_board(modules):
 font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',14)
 board=Image.new('RGB',(960,math.ceil(len(modules)/8)*150),'#18262d');d=ImageDraw.Draw(board)
 for i,m in enumerate(modules):
  x=i%8*120;y=i//8*150;im=Image.open(OUT/m['path']).convert('RGBA')
  scale=2 if max(im.size)>32 else 3
  im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
  board.paste(im,(x+(120-im.width)//2,y+12+(100-im.height)//2),im)
  text=f"{m['footprint'][0]}×{m['footprint'][1]}格"
  box=d.textbbox((0,0),text,font=font);d.text((x+(120-(box[2]-box[0]))//2,y+117),text,font=font,fill='#c6c7bc')
 board.save(REPORT/'module-board.png',optimize=True)

if __name__=='__main__':main()
