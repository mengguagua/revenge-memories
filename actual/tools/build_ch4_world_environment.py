#!/usr/bin/env python3
"""Fourth-chapter display biomes; never mutate the world navigation data."""
from pathlib import Path
from PIL import Image
import copy,json,hashlib,math,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter4-environment-20261023/world';A=R/'assets/chapter4-environment-20261023/world'
read=lambda p:json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
w=read(R/'data/formal_world.json');v=read(R/'data/chapter3_world_environment.json');ground=copy.deepcopy(v['ground']);layers=copy.deepcopy(v['layers']);props=copy.deepcopy(v['natural_props'])
pack=read(R/'assets/world_tiles/world-tiles.json');families={f['name']:f for f in pack['families']};source=Image.open(R/v['atlas'][6:]).convert('RGBA');cells=[source.crop((x,y,x+16,y+16))for y in range(0,source.height,16)for x in range(0,source.width,16)];width,height=w['width'],w['height'];cache={}
def ellipse(x,y,cx,cy,rx,ry):return ((x-cx)/rx)**2+((y-cy)/ry)**2<=1
for y in range(height):
 for x in range(width):
  if ground[y][x]=='sea':continue
  if ellipse(x,y,12,25,5.8,3.4)or ellipse(x,y,5,26,3.4,3.1)or ellipse(x,y,14,16,3.8,3.2):ground[y][x]='snow'
  elif ellipse(x,y,48,23,3.5,3.2):ground[y][x]='salt'
  elif ellipse(x,y,44,19,3.5,2.6)or ellipse(x,y,35,18,2.7,2.4):ground[y][x]='marsh'
  elif ellipse(x,y,44,15,2.3,1.8):ground[y][x]='stone'
peers=[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8),(1,-1,16),(1,1,32),(-1,1,64),(-1,-1,128)]
def mask(x,y,pred):
 m=sum(bit for dx,dy,bit in peers if 0<=x+dx<width and 0<=y+dy<height and pred(x+dx,y+dy))
 for d,a,b in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
  if not(m&a and m&b):m&=~d
 return m
changes=[]
for y in range(height):
 for x in range(width):
  kind=ground[y][x]
  if kind==v['ground'][y][x]:continue
  coast=mask(x,y,lambda xx,yy:ground[yy][xx]!='sea');edge=mask(x,y,lambda xx,yy:ground[yy][xx]==kind);variant=(x*3+y)%4
  if coast!=255 and 'coast_'+kind in families:t=families['coast_'+kind]['tiles_by_mask'][str(coast)]
  elif edge!=255 and kind+'_edge' in families:
   key=(kind,edge,variant)
   if key not in cache:
    under='sand'if kind=='salt'else'grass';im=cells[pack['base_tiles'][under][variant]].copy();im.alpha_composite(cells[families[kind+'_edge']['tiles_by_mask'][str(edge)]]);cache[key]=len(cells);cells.append(im)
   t=cache[key]
  else:t=pack['base_tiles'][kind][variant]
  layers[0][y][x]=t
  if w['ground'][y][x]in ['forest','rock']:layers[1][y][x]=None
  changes.append({'cell':[x,y],'before':v['ground'][y][x],'after':kind})
road_cells={tuple(p)for route in w['routes']for p in route['cells']};road_art=[]
for x,y in road_cells:
 if ground[y][x]!='snow':continue
 old=layers[3][y][x]
 if not any(old in family.values()for family in pack['roads'].values()):continue
 m=sum(bit for dx,dy,bit in peers[:4]if(x+dx,y+dy)in road_cells);layers[3][y][x]=pack['roads']['snow'][str(m)];road_art.append([x,y])
cat={s['key']:s for s in read(R/'assets/nature/nature.json')['sprites']};winter=read(R/'data/chapter1_hub_climate.json')['nature_keys'];nature=[]
for p in props:
 x,y=[int(n)//16 for n in p['position']]
 if ground[y][x]=='snow' and p['key']in winter:
  k=p['key'];p['key']=winter[k];assert cat[k]['size']==cat[p['key']]['size'];nature.append({'before':k,'after':p['key'],'position':p['position']})
A.mkdir(parents=True,exist_ok=True);atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
atlas.save(A/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(A/'terrain.png')],check=True)
write(R/'data/chapter4_world_environment.json',{'version':'0.10.14-environment','width':width,'height':height,'columns':32,'atlas':'res://assets/chapter4-environment-20261023/world/terrain.png','overview':'res://assets/chapter4-environment-20261023/world/overview.png','layers':layers,'ground':ground,'natural_props':props,'source_world_sha256':hashlib.sha256((R/'data/formal_world.json').read_bytes()).hexdigest(),'note':'Visual-only snow highlands, salt observation plateau, marsh and ruined stone shrine. Nodes, routes and traversal remain formal_world data.'})
write(O/'design.json',{'passed':True,'source_world_unchanged':True,'ground_changes':changes,'snow_road_art':road_art,'winter_nature':nature,'node_materials':{k:{'name':w['nodes'][k]['name_zh'],'position':w['nodes'][k]['position'],'material':ground[w['nodes'][k]['position'][1]][w['nodes'][k]['position'][0]]}for k in ['10','11','12','13','26','27','28','29','37','38']}})
print('world',len(changes),'biome cells,',len(road_art),'snow road tiles,',len(nature),'winter props')
