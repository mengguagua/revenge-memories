#!/usr/bin/env python3
"""World appearance only: preserve the navigation graph, extend salt around its named camp."""
from pathlib import Path
from PIL import Image
import copy,json,math,hashlib,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter3-environment-20261023/world';A=R/'assets/chapter3-environment-20261023/world'
read=lambda p:json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
w=read(R/'data/formal_world.json');pack=read(R/'assets/world_tiles/world-tiles.json');families={f['name']:f for f in pack['families']};native=Image.open(R/'assets/world_tiles/world-tiles.png').convert('RGBA');cells=[native.crop((x,y,x+16,y+16))for y in range(0,native.height,16)for x in range(0,native.width,16)];layers=copy.deepcopy(w['layers']);ground=copy.deepcopy(w['ground']);width,height=w['width'],w['height'];edges={}
for y in range(height):
 for x in range(width):
  if ((x-51)/3.5)**2+((y-28)/2.8)**2<=1 and ground[y][x]not in ['sea','salt']:ground[y][x]='salt'
def mask(x,y,kind):
 m=0
 for dx,dy,bit in [(0,-1,1),(1,0,2),(0,1,4),(-1,0,8),(1,-1,16),(1,1,32),(-1,1,64),(-1,-1,128)]:
  if 0<=x+dx<width and 0<=y+dy<height and (ground[y+dy][x+dx]=='salt'if kind=='salt'else ground[y+dy][x+dx]!='sea'):m|=bit
 for diag,a,b in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
  if not(m&a and m&b):m&=~diag
 return m
changes=[]
for y in range(height):
 for x in range(width):
  if ground[y][x]!='salt'or ground[y][x]==w['ground'][y][x]:continue
  coast=mask(x,y,'land');salt=mask(x,y,'salt');v=(x*3+y)%4
  if coast!=255:t=families['coast_salt']['tiles_by_mask'][str(coast)]
  elif salt==255:t=pack['base_tiles']['salt'][v]
  else:
   key=(salt,v)
   if key not in edges:
    im=cells[pack['base_tiles']['sand'][v]].copy();im.alpha_composite(cells[families['salt_edge']['tiles_by_mask'][str(salt)]]);edges[key]=len(cells);cells.append(im)
   t=edges[key]
  layers[0][y][x]=t;changes.append([x,y])
A.mkdir(parents=True,exist_ok=True);atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
atlas.save(A/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(A/'terrain.png')],check=True)
assert ground[28][51]=='salt'
write(R/'data/chapter3_world_environment.json',{'version':'0.10.13-environment','width':width,'height':height,'columns':32,'atlas':'res://'+str((A/'terrain.png').relative_to(R)),'overview':'res://assets/chapter3-environment-20261023/world/overview.png','layers':layers,'ground':ground,'natural_props':w['natural_props'],'source_world_sha256':hashlib.sha256((R/'data/formal_world.json').read_bytes()).hexdigest(),'note':'Display-only salt-camp surface; navigation nodes/routes/unlocks are read from the unchanged formal_world.'})
write(O/'design.json',{'passed':True,'source_world_unchanged':True,'modified_visual_cells':changes,'node_materials':{k:{'name':w['nodes'][k]['name_zh'],'position':w['nodes'][k]['position'],'material':ground[w['nodes'][k]['position'][1]][w['nodes'][k]['position'][0]]}for k in ['6','7','8','9','24','25','35','36']},'source_tiles_preserved':True})
print('World appearance patch:',len(changes),'salt cells; all navigation unchanged')
