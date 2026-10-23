#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import copy,json,math,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter3-environment-20261023';A=R/'assets/chapter3-environment-20261023/hubs'
read=lambda p:json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
base=read(O/'baseline/chapter3_hubs.json');d=copy.deepcopy(base);pack=read(R/'assets/battle_tiles/battle-tiles.json');native=Image.open(R/'assets/battle_tiles/battle-tiles.png').convert('RGBA');cells=[];lookup={}
def tile(i):
 if i not in lookup:lookup[i]=len(cells);cells.append(native.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)))
 return lookup[i]
rooms={}
notes={'H30':'日返后的庆典广场以室外砌石形成完整前场，边缘保留草地。','H31':'城外旧街与避难前庭使用室外石铺，边缘草地保持。','H32':'转运站压实土道对应军需大道，仓门前保留室外石台。','H33':'沿海工房为砌石作业平台，岸侧仓库替代船舱，南端木踏板接驳船。','H34':'盐路井台采用盐地背景、干土通路与井边石铺；黑昼延续。','H35':'提炼院记录庭的露天砌石、盐土地与冷暗光延续，非室内大厅。','H36':'地牢外安置处以山村土路、洞口石台和草地表达，室内在战场剖面牢室。','H37':'盐原营房安置区用盐地、土路与营房外观，延续冷暗光。','H10':'会合营站按大地图沙岸定位，使用沙地与压实营道，补给仓房替代船舱。'}
for room,source in d['rooms'].items():
 if room in ['H34','H35','H37']:source['biome_override']='salt';source['environment_tint']=[.80,.84,.92]
 if room=='H10':source['biome_override']='sand'
 for p in source['scenery']:
  if room=='H33'and p['name']=='captain_cabin':p['sprite_path']='res://assets/battlefield-0.3.0/modules/quay_warehouse.png'
  if room=='H10'and p['name']=='captain_cabin':p['sprite_path']='res://assets/battlefield-0.3.0/modules/hill_granary.png'
  if room=='H37'and p['name']=='fishing_hut':p['sprite_path']='res://assets/battle_tiles/modules/barracks.png'
 out={'tiles':[],'props':[],'background':source.get('biome_override','sea'),'tint':source.get('environment_tint',[1,1,1]),'scenery_paths':{a['sprite_path']:b['sprite_path']for a,b in zip(base['rooms'][room]['scenery'],source['scenery'])if a.get('sprite_path')!=b.get('sprite_path')}}
 for y,row in enumerate(source['floor']):
  line=[]
  for x,mark in enumerate(row):
   if mark=='~':line.append(None);continue
   material='salt'if mark=='a'else'dirt'if mark=='p'and room in ['H32','H34','H36','H37','H10']else'cobble'if mark=='p'else'sand'if room=='H10'else'grass'
   if room=='H30'and 2<=x<=11 and y<=7:material='cobble'
   if room=='H31'and 3<=x<=10 and 2<=y<=6:material='cobble'
   if room=='H32'and 7<=x<=11 and y<=2:material='cobble'
   if room=='H34'and 9<=x<=11 and 2<=y<=4:material='cobble'
   if room=='H36'and 1<=x<=3 and y<=2:material='cobble'
   if room=='H33'and x==6 and y>=7:material='timber'
   line.append(tile(pack['base'][material][(x*3+y)%4]))
  out['tiles'].append(line)
 if room=='H33':out['props'].append({'path':'res://assets/chapter2/modules/rowboat.png','position':[88,9*16]})
 rooms[room]=out
A.mkdir(parents=True,exist_ok=True);atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
atlas.save(A/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(A/'terrain.png')],check=True)
write(R/'data/chapter3_hub_environment.json',{'version':'0.10.13-environment','atlas':'res://'+str((A/'terrain.png').relative_to(R)),'rooms':rooms,'notes':notes})
(R/'data/chapter3_hubs.json').write_bytes((O/'baseline/chapter3_hubs.json').read_bytes())
for k,v in d['rooms'].items():
 for field in ['floor','objects']:assert v[field]==base['rooms'][k][field]
 assert [{a:b for a,b in p.items()if a!='sprite_path'}for p in v['scenery']]==[{a:b for a,b in p.items()if a!='sprite_path'}for p in base['rooms'][k]['scenery']]
write(O/'hubs/design.json',{'passed':True,'rooms':notes,'floor_objects_and_collision_geometry_exact':True,'atlas_tiles':len(cells),'atlas_bytes':(A/'terrain.png').stat().st_size,'new_generated_art':False})
print('9 hubs,',len(cells),'native tiles,',atlas.size)
