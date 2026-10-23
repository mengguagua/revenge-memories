#!/usr/bin/env python3
"""Native material selection for second-chapter hubs; all walking masks exact."""
from pathlib import Path
from PIL import Image
import json,copy,hashlib,subprocess,math
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter2-environment-20261023/hubs';A=R/'assets/chapter2-environment-20261023/hubs';BASE=O.parent/'baseline'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
data=read(BASE/'chapter2_hubs.json');before=copy.deepcopy(data);pack=read(R/'assets/battle_tiles/battle-tiles.json');terrain=read(R/'assets/battlefield-0.3.0/terrain.json')
source=Image.open(R/'assets/battlefield-0.3.0/terrain.png').convert('RGBA');cells=[];lookup={}
def tile(original):
 if original not in lookup:
  lookup[original]=len(cells);cells.append(source.crop((original%32*16,original//32*16,original%32*16+16,original//32*16+16)))
 return lookup[original]
rooms={}
for room,d in data['rooms'].items():
 if room=='H27':continue
 floor=d['floor'];visual={'tiles':[],'props':[{'path':'res://assets/chapter2/modules/rowboat.png','position':[88,140],'purpose':'接驳船在南侧短栈末端水面，说明离开据点就是登船'}]}
 for y,row in enumerate(floor):
  output=[]
  for x,m in enumerate(row):
   if m=='~':output.append(None);continue
   variant=((x*73856093)^(y*19349663)^((x+y*17)>>2))%4
   original=pack['base'][data['materials'][m]][variant]
   if room in ['H22','H23']:
    mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<14 and 0<=y+dy<9 and floor[y+dy][x+dx]!='~')
    axis='v'if x in [6,7]else'h'
    original=terrain['transitions']['walkway'][axis+str(mask)][variant]
   if room=='H25'and m in ['.','d']and ((x>=4 and y>=1)or(2<=x<=4 and 3<=y<=6)):
    original=pack['base']['cobble'][variant]
   output.append(tile(original))
  visual['tiles'].append(output)
 rooms[room]=visual
# Art/lighting metadata only: descriptions and every walkable floor row stay exact.
data['rooms']['H24']['environment_tint']=[.82,.86,.94]
for room in ['H22','H23']:
 for prop in data['rooms'][room]['scenery']:
  if prop['name']=='captain_cabin':prop['sprite_path']='res://assets/chapter2-environment-20261023/ships/deckhouse.png'
for prop in data['rooms']['H26']['scenery']:
 if prop['name']=='captain_cabin':prop['sprite_path']='res://assets/battlefield-0.3.0/modules/quay_warehouse.png'
A.mkdir(parents=True,exist_ok=True);atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
atlas.save(A/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','4',str(A/'terrain.png')],check=True)
visual={'version':'0.10.12-environment','applies':'chapter == 2 and room in H21-H26','atlas':'res://assets/chapter2-environment-20261023/hubs/terrain.png','columns':32,'rooms':rooms,'notes':{'H21':'保留草地岛岸与木栈，补南栈接驳船。','H22':'甲板用原生木板边缘与纵向中轴，旧陆地屋顶换为同尺寸船舱上建，出口接驳船连接海上旅行。','H23':'救护甲板采用船板边缘与同尺寸船舱上建，救护队与舱室位置保持。','H24':'保留草地/沙岸，轻冷暗承接初次黑昼。','H25':'航灯院的治疗/训练前场为室外石铺，沙岸植被与现有黑昼保留。','H26':'石铺仓院保持，舰上舱室贴图换同尺寸岸侧仓库。','H27':'海峡城广场室外石地与原自然光均符合剧情，保持。'}}
write(R/'data/chapter2_hub_environment.json',visual);write(R/'data/chapter2_hubs.json',data)
checks=[]
for k,d in data['rooms'].items():
 old=before['rooms'][k];assert d['floor']==old['floor'];assert d['objects']==old['objects'];assert d['spawn']==old['spawn']and d['exit']==old['exit']
 assert [{a:v for a,v in s.items()if a!='sprite_path'}for s in d['scenery']]==[{a:v for a,v in s.items()if a!='sprite_path'}for s in old['scenery']]
 checks.append({'room':k,'floor_objects_scenery_geometry_spawn_exit_exact':True,'note':visual['notes'][k]})
write(O/'assets.json',{'passed':True,'native_source_atlas':'assets/battlefield-0.3.0/terrain.png','native_source_ids':lookup,'atlas':{'path':str((A/'terrain.png').relative_to(R)),'size':list(atlas.size),'bytes':(A/'terrain.png').stat().st_size,'sha256':sha(A/'terrain.png')},'new_artwork_generated':False,'reused_boat':{'path':'assets/chapter2/modules/rowboat.png','size':[32,48]},'reused_warehouse':{'path':'assets/battlefield-0.3.0/modules/quay_warehouse.png','size':[48,32]},'reused_deckhouse':{'path':'assets/chapter2-environment-20261023/ships/deckhouse.png','size':[48,32]},'maps':checks,'no_geometry_changes':True})
print(json.dumps({'passed':True,'native_tiles':len(cells),'atlas_size':list(atlas.size),'bytes':(A/'terrain.png').stat().st_size},ensure_ascii=False))
