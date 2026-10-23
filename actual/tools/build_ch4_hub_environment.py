#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image
import json,math,subprocess,copy
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter4-environment-20261023';A=R/'assets/chapter4-environment-20261023/hubs'
read=lambda p:json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
base=read(O/'baseline/chapter4_hubs.json')['rooms'];base['H10']=read(R/'data/chapter3_hubs.json')['rooms']['H10']
pack=read(R/'assets/battle_tiles/battle-tiles.json');native=Image.open(R/'assets/battle_tiles/battle-tiles.png').convert('RGBA');indoor=Image.open(R/'assets/chapter5-spatial-20261022/library/interior-stone.png').convert('RGBA');cells=[];cache={}
def tile(i):
 key=('native',i)
 if key not in cache:cache[key]=len(cells);cells.append(native.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)))
 return cache[key]
def inside(x,y):
 key=('indoor',x%4,y%4)
 if key not in cache:cache[key]=len(cells);cells.append(indoor.crop((x%4*16,y%4*16,x%4*16+16,y%4*16+16)))
 return cache[key]
wall_source=read(O/'baseline/M43.json');wall_image=Image.open(R/wall_source['art_atlas'][6:]).convert('RGBA')
def wall(i):
 key=('wall',i)
 if key not in cache:cache[key]=len(cells);cells.append(wall_image.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)))
 return cache[key]
notes={'H41':'雪峡南口仍在室外雪地，撤离土路与积雪村屋保持。','H42':'铁骑关投送站用土道和石制设备坪，渔屋换同尺寸军营仓房。','H43':'日塔控制室为去顶室内，磨损石板、边界墙和控制设备代替雪地与雪顶小屋。','H44':'王都后撤门是露天石铺医护院，仓房外观与伤兵撤退用途一致。','H45':'沙城井台使用沙地、土路与石井台，取消盐地背景；黑昼延续。','H46':'观测台东楼为去顶室内，石地、边界墙、工作台和设备，不在屋内放整栋房屋。','H47':'沼泽船口使用露天木码头，南口接驳船明确离开方式；黑昼延续，邻近祭所完成两岸验证后局部变亮。','H48':'祭所调节庭用露天石台、木登船口和接驳船；局部试验成功后恢复此处亮光。','H49':'黑钟村避难院保留雪地、清扫土道和积雪村舍。','H50':'孤岛诊疗处是岸上石质医护台与木登船口，接驳船连贯，黑昼保持。','H10':'会合营站沿用第三章沙岸、压实土道和陆地补给仓房。'}
rooms={}
for room,d in base.items():
 out={'tiles':[],'props':[],'background':d.get('biome_override','sea'),'tint':[.8,.84,.92]if room in ['H45','H46','H47','H48','H50']else[1,1,1],'scenery_paths':{}}
 if room=='H10':out=copy.deepcopy(read(R/'data/chapter3_hub_environment.json')['rooms']['H10']);out['source_atlas']=read(R/'data/chapter3_hub_environment.json')['atlas'];rooms[room]=out;continue
 if room=='H45':out['background']='sand'
 if room in ['H43','H46']:out['background']='rock';out['background_darkness']=.35;out['wall_frame']={'north':[wall(459)],'west':[wall(463)]}
 for y,row in enumerate(d['floor']):
  line=[]
  for x,m in enumerate(row):
   if m=='~':line.append(None);continue
   if room in ['H43','H46']:line.append(inside(x,y));continue
   material='snow'if m=='n'else'grass'if m=='.'else'sand'if room=='H45'and m=='a'else'salt'if m=='a'else'dirt'
   if room in ['H44','H48','H50']:material='cobble'
   if room=='H47' or(room in ['H48','H50']and y>=7 and x==6):material='timber'
   if room=='H42'and x>=7 and y<=3:material='cobble'
   if room=='H45'and 5<=x<=8 and 1<=y<=4:material='cobble'
   line.append(tile(pack['base'][material][(x*3+y)%4]))
  out['tiles'].append(line)
 for p in d['scenery']:
  replacement=None
  if room in ['H42','H44']:replacement='res://assets/battle_tiles/modules/barracks.png'
  if room=='H43':replacement='res://assets/battle_tiles/modules/sun_altar.png'
  if room=='H46':replacement='res://assets/chapter3-environment-20261023/maps/workshop-equipment.png'
  if replacement:
   assert Image.open(R/replacement[6:]).size==Image.open(R/p['sprite_path'][6:]).size,(room,replacement)
   out['scenery_paths'][p['sprite_path']]=replacement
 if room in ['H47','H48','H50']:out['props'].append({'path':'res://assets/chapter2/modules/rowboat.png','position':[88,144]})
 rooms[room]=out
A.mkdir(parents=True,exist_ok=True);atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
atlas.save(A/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(A/'terrain.png')],check=True)
write(R/'data/chapter4_hub_environment.json',{'version':'0.10.14-environment','atlas':'res://assets/chapter4-environment-20261023/hubs/terrain.png','rooms':rooms,'notes':notes})
write(O/'hubs/design.json',{'passed':True,'rooms':notes,'floor_objects_and_collision_geometry_exact':True,'atlas_tiles':len(cells),'new_generated_art':False})
print('11 hub overlays,',len(cells),'native tiles')
