#!/usr/bin/env python3
"""First-chapter winter visuals only; world routes, nodes and movement stay exact."""
from pathlib import Path
import copy,hashlib,json,math,subprocess
from PIL import Image
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter1-climate-20261022/world'
A=R/'assets/chapter1-climate-20261022/world'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
w=read(R/'data/formal_world.json');original_hash=sha(R/'data/formal_world.json')
pack=read(R/'assets/world_tiles/world-tiles.json');families={f['name']:f for f in pack['families']}
native=Image.open(R/'assets/world_tiles/world-tiles.png').convert('RGBA')
cells=[native.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)) for i in range((native.width//16)*(native.height//16))]
edge_cache={}
def snow_margin(mask_value,variant):
 key=(mask_value,variant)
 if key not in edge_cache:
  image=cells[pack['base_tiles']['grass'][variant]].copy()
  image.alpha_composite(cells[families['snow_edge']['tiles_by_mask'][str(mask_value)]])
  edge_cache[key]=len(cells);cells.append(image)
 return edge_cache[key]
cat={s['key']:s for s in read(R/'assets/nature/nature.json')['sprites']}
width,height=w['width'],w['height'];layers=copy.deepcopy(w['layers']);props=copy.deepcopy(w['natural_props'])
# This broad western cold region follows the chapter-one route and coastal edge.
# Its irregular northern margin avoids the old hard y=45 line through adjacent towns.
edge=[44,44,43,43,42,42,42,41,40,40,39,39,39,39,39,39,39,39,38,38,37,36,34,33,32,32,32,32,33,34]
def cold(x,y):return 0<=x<len(edge) and 0<=y<height and y>=edge[x] and w['ground'][y][x]!='sea'
peers=[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8),(1,-1,16),(1,1,32),(-1,1,64),(-1,-1,128)]
def mask(x,y,pred):
 m=sum(bit for dx,dy,bit in peers if 0<=x+dx<width and 0<=y+dy<height and pred(x+dx,y+dy))
 for diagonal,a,b in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
  if not(m&a and m&b):m &= ~diagonal
 return m
changed=[];climate=copy.deepcopy(w['ground'])
for y in range(height):
 for x in range(width):
  if not cold(x,y):continue
  coast=mask(x,y,lambda xx,yy:w['ground'][yy][xx]!='sea')
  snow=mask(x,y,cold);variant=(x*3+y)%4
  tile=(families['coast_snow']['tiles_by_mask'][str(coast)] if coast!=255
        else snow_margin(snow,variant) if snow!=255
        else pack['base_tiles']['snow'][variant])
  if layers[0][y][x]!=tile:changed.append([x,y])
  layers[0][y][x]=tile;climate[y][x]='snow'
  # Residual forest/rock edge tiles belong to the original geography, not roads.
  if w['ground'][y][x] in ['forest','rock']:layers[1][y][x]=None
road_cells={tuple(p) for route in w['routes'] for p in route['cells']}
road_changes=[]
for x,y in road_cells:
 if not cold(x,y):continue
 old=layers[3][y][x]
 # Sacred/sea crossings retain their exact art and meaning.
 ordinary=any(old in family.values() for family in pack['roads'].values())
 if not ordinary:continue
 road_mask=sum(bit for dx,dy,bit in peers[:4] if (x+dx,y+dy)in road_cells)
 layers[3][y][x]=pack['roads']['snow'][str(road_mask)]
 if old!=layers[3][y][x]:road_changes.append([x,y])
nature_changes=[]
for p in props:
 x,y=[int(v)//16 for v in p['position']]
 if not cold(x,y):continue
 key=p['key'];replacement=key.replace('pine_','snow_')
 if replacement in cat and replacement!=key:
  assert cat[key]['size']==cat[replacement]['size']
  p['key']=replacement;nature_changes.append({'position':p['position'],'before':key,'after':replacement})
 elif 'climate_snow_'+key in cat:
  p['key']='climate_snow_'+key;nature_changes.append({'position':p['position'],'before':key,'after':p['key']})
 elif key in ['boulder','peak_low'] and p.get('size',cat[key]['size'])==[16,16]:
  p['key']='snow_boulder';nature_changes.append({'position':p['position'],'before':key,'after':'snow_boulder'})
nodes={}
for key in ['1','2','3','4','5','6','31','32']:
 n=w['nodes'][key];x,y=n['position'];assert cold(x,y),(key,n)
 nodes[n['id']]={'name':n['name_zh'],'position':n['position'],'before':w['ground'][y][x],'first_chapter':'snow',
  'profile':'雪原与积雪村落' if key in ['1','2','3','31','32'] else '残雪泥路与冬营' if key in ['4','5'] else '临海薄雪与裸露石坪'}
variant={'version':'0.10.11-climate','applies':'chapter == 1 and not chapter1_complete',
 'width':width,'height':height,'atlas':'res://assets/chapter1-climate-20261022/world/terrain.png','columns':w['columns'],'layers':layers,
 'natural_props':props,'ground':climate,'node_climates':nodes,
 'overview':'res://assets/chapter1-climate-20261022/world/overview-winter.png',
 'source_world_sha256':original_hash,'note':'Visual-only winter field. All world nodes, road cells, unlocks and movement remain in the unchanged formal_world.json.'}
write(R/'data/chapter1_world_climate.json',variant)
# Compose the overview from the exact same native bitmap tiles and prop records.
A.mkdir(parents=True,exist_ok=True)
atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,t in enumerate(cells):atlas.paste(t,(i%32*16,i//32*16))
atlas.save(A/'terrain.png')
subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(A/'terrain.png')],check=True)
image=Image.new('RGBA',(width*16,height*16))
for layer in layers:
 for y,row in enumerate(layer):
  for x,t in enumerate(row):
   if t is not None and t>=0:image.alpha_composite(cells[t],(x*16,y*16))
for p in props:
 im=Image.open(R/cat[p['key']]['path'].removeprefix('res://')).convert('RGBA')
 if p.get('size'):im=im.resize(tuple(p['size']),Image.Resampling.NEAREST)
 if p.get('flip'):im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 image.alpha_composite(im,tuple(p['position']))
out=A/'overview-winter.png';image.convert('RGB').save(out,optimize=True)
subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(out)],check=True)
assert sha(R/'data/formal_world.json')==original_hash
write(O/'design.json',{'passed':True,'source_world_sha256':original_hash,'formal_world_unchanged':True,
 'road_cells_and_nodes_unchanged':True,'region_edge':edge,'ground_changed_cells':changed,
 'road_art_changed_cells':road_changes,'nature_changes':nature_changes,'node_climates':nodes,
 'overview':{'path':str(out.relative_to(R)),'size':image.size,'bytes':out.stat().st_size,
 'quality':'Lossless native resolution, identical tile/prop composition to world renderer; no resampling of source tiles.'}})
print(json.dumps({'passed':True,'ground_cells':len(changed),'road_cells':len(road_changes),'winter_props':len(nature_changes),'overview_bytes':out.stat().st_size}))
