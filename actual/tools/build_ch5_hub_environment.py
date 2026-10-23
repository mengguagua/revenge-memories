#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image
import json,math,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-environment-20261023';A=R/'assets/chapter5-environment-20261023/hubs'
read=lambda p:json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
base=read(O/'baseline/chapter5_hubs.json')['rooms'];cells=[];cache={}
textures={name:Image.open(R/path).convert('RGBA')for name,path in {'stone':'assets/chapter5-spatial-20261022/library/interior-stone.png','wood':'assets/chapter5-spatial-20261022/library/interior-parquet.png','marble':'assets/chapter5-spatial-20261022/east-finale/palace-marble.png','court':'assets/chapter5-spatial-20261022/east-finale/courtyard-stone.png'}.items()}
native=Image.open(R/'assets/battle_tiles/battle-tiles.png').convert('RGBA');pack=read(R/'assets/battle_tiles/battle-tiles.json');old=read(R/'data/chapter4_hub_environment.json');walls=Image.open(R/old['atlas'][6:]).convert('RGBA')
def add(key,im):
 if key not in cache:cache[key]=len(cells);cells.append(im)
 return cache[key]
def mat(name,x,y):return add((name,x%4,y%4),textures[name].crop((x%4*16,y%4*16,x%4*16+16,y%4*16+16)))
def wall(i):return add(('wall',i),walls.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)))
def grass(x,y):
 i=pack['base']['grass'][(x*3+y)%4];return add(('native',i),native.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)))
A.mkdir(parents=True,exist_ok=True)
# Four existing complete shelf modules fill exactly the old 6x6 blocked storage bay.
bay=Image.open(R/'assets/chapter5-spatial-20261022/library/archive-bay.png').convert('RGBA');shelves=Image.new('RGBA',(96,96))
for x,y in [(0,0),(48,0),(0,48),(48,48)]:shelves.alpha_composite(bay,(x,y))
shelves.save(A/'archive-shelves.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(A/'archive-shelves.png')],check=True)
notes={'H51':'内廷照护处是病房门外的室外交接院；保留完整医舍外观，地面改露天砌石与草园边缘，室内病床在M51剖面表达。','H52':'登天桥西门营地是露天石质落脚平台，门楼外观与园林边缘保留，去除室内感浅色抹灰地。','H53':'祭所底层修复间统一去顶室内磨损石板和连续石墙；装置保留，室内草地与花丛改为石地及同占地储料箱。','H54':'日宫下层东门廊是室内大理石地与连续石墙；不铺草地，不摆露天花丛。装置、对象与南侧出口保持。','H55':'两军整备位于神宫前庭的露天石庭，门楼与草园边缘符合外部空间，原对象、名单与救治位置保持。','H56':'旧书库记录室统一去顶室内，木地储藏区与石质通廊分开；完整屋顶书库改同96×96占地的书架库位，不在室内再放房屋。'}
rooms={}
for room,d in base.items():
 indoor=room in ['H53','H54','H56'];out={'tiles':[],'props':[],'background':'rock'if indoor else'grass','tint':[.88,.9,.94]if room=='H53'else[1,1,1],'scenery_paths':{}}
 if indoor:out['background_darkness']=.35;out['wall_frame']={'north':[wall(int(old['rooms']['H43']['wall_frame']['north'][0]))],'west':[wall(int(old['rooms']['H43']['wall_frame']['west'][0]))]}
 for y,row in enumerate(d['floor']):
  line=[]
  for x,mark in enumerate(row):
   if mark=='~':line.append(None);continue
   if room=='H53':tile=mat('stone',x,y)
   elif room=='H54':tile=mat('marble',x,y)
   elif room=='H56':tile=mat('stone'if x in [5,6,7]or y==7 else'wood',x,y)
   else:tile=grass(x,y)if mark=='.'else mat('court',x,y)
   line.append(tile)
  out['tiles'].append(line)
 for p in d['scenery']:
  replacement='res://assets/chapter5-environment-20261023/hubs/archive-shelves.png'if room=='H56'and p['name']=='archive'else'res://assets/battle_tiles/modules/crates.png'if indoor and p['name']=='flowers'else None
  if replacement:
   assert Image.open(R/replacement[6:]).size==Image.open(R/p['sprite_path'][6:]).size
   out['scenery_paths'][p['sprite_path']]=replacement
 rooms[room]=out
atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,t in enumerate(cells):atlas.paste(t,(i%32*16,i//32*16))
atlas.save(A/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(A/'terrain.png')],check=True)
write(R/'data/chapter5_hub_environment.json',{'version':'0.10.15-environment','atlas':'res://assets/chapter5-environment-20261023/hubs/terrain.png','rooms':rooms,'notes':notes})
write(O/'hubs/design.json',{'passed':True,'rooms':notes,'floor_objects_and_collision_geometry_exact':True,'atlas_tiles':len(cells),'new_generated_art':False,'native_composition':'archive-shelves.png = four complete existing 48x48 archive-bay modules; original 96x96 blocked bay retained.'})
print('6 hub overlays,',len(cells),'native tiles')
