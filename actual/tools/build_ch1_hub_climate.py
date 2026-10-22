#!/usr/bin/env python3
"""Pure visual winter variants for first-chapter outdoor story hubs."""
from pathlib import Path
import json,hashlib
from PIL import Image
from climate_ch1_side import mask_at
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter1-climate-20261022/side/hubs'
read=lambda p:json.loads(p.read_text())
pack=read(R/'assets/battle_tiles/battle-tiles.json')
trans=read(R/'assets/battlefield-0.3.0/terrain.json')['transitions']['snow_path']
rooms={}
# Cleared approaches meet the existing interaction anchors and doorway fronts.
cleared={
 'H02':[(5,3,8,8),(2,4,7,6),(6,2,12,4),(9,2,12,3)],
 'H03':[(5,3,8,8),(2,4,7,6),(6,3,12,5),(10,2,12,5)],
 'H05':[(5,3,8,8),(6,2,12,4)],
 'H07':[(5,3,8,8),(6,4,12,6)],
 'H09':[(5,3,8,8),(2,3,7,5),(6,4,11,6)]}
for room in ['H02','H03','H05','H06','H07','H09']:
 grid=[['n']*14 for _ in range(9)]
 if room=='H06':
  # The old tower court is a cleared stone apron; snow begins beyond the court.
  grid=[['c']*14 for _ in range(9)]
 else:
  for x0,y0,x1,y1 in cleared[room]:
   for y in range(y0,y1+1):
    for x in range(x0,x1+1):grid[y][x]='p'
 tiles=[]
 for y,row in enumerate(grid):
  line=[]
  for x,q in enumerate(row):
   v=int(hashlib.sha256(f'{room}:{x}:{y}'.encode()).hexdigest()[:8],16)%4
   line.append(trans[str(mask_at(grid,x,y,lambda z:z=='p'))][v] if q=='p' else pack['base']['cobble' if q=='c' else 'snow'][v])
  tiles.append(line)
 rooms[room]={'atlas':'res://assets/battlefield-0.3.0/terrain.png','tiles':tiles,'ground':'cleared stone courtyard surrounded by snow' if room=='H06' else 'snow with native compacted dirt approaches','logical_floor_unchanged':True}
replacements={
 'grain_store':'res://assets/chapter1-climate-20261022/camp-fort/grain_store-winter.png',
 'barracks':'res://assets/chapter1-climate-20261022/camp-fort/barracks-winter.png',
 'pine_patch':'res://assets/battle_tiles/modules/snow_pine_patch.png',
 'flowers':'res://assets/nature/snow_young.png'}
nature={'pine_tall':'snow_tall','pine_broad':'snow_broad','pine_pair':'snow_pair','pine_young':'snow_young','pine_small_a':'snow_small_a','pine_small_b':'snow_small_b','boulder':'snow_boulder'}
nature.update({key:'climate_snow_'+key for key in ['peak_low','crag_tall','ridge_bent','outcrop']})
assets=[]
for key,new in replacements.items():
 old=R/f'assets/battle_tiles/modules/{key}.png';p=R/new.removeprefix('res://')
 assert Image.open(old).size==Image.open(p).size,(key,Image.open(old).size,Image.open(p).size)
 assets.append({'source':str(old.relative_to(R)),'path':new,'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
nature_defs={x['key']:x for x in read(R/'assets/nature/nature.json')['sprites']}
for old,new in nature.items():assert nature_defs[old]['size']==nature_defs[new]['size'],(old,new)
data={'version':'0.10.11-climate','condition':'chapter == 1 and not flags.chapter1_complete','rooms':rooms,'scenery_paths':replacements,'nature_keys':nature,'notes':['H01 keeps its existing winter art.','H04 church and H08 mine remain dry interior stone/cave.','Only rendering looks up this table; objects, collisions, interactions, scripts and save data are unchanged.','The old tower is a cleared stone court, surrounded by snow; exposed stonework and supplies retain their materials.','After the sun-return ceremony, this table is inactive; later chapters keep their previous renderer.']}
(R/'data/chapter1_hub_climate.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
O.mkdir(parents=True,exist_ok=True)
(O/'assets.json').write_text(json.dumps({'version':data['version'],'assets':assets,'reused_native_atlas':data['rooms']['H02']['atlas'],'native_pixels_unchanged':True,'no_shared_nature_layout_change':True},ensure_ascii=False,indent=2)+'\n')
print('Created six winter visual-only hub variants; all replacement dimensions match.')
