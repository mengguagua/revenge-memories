#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Native materials only; keep the approved final-chapter spatial and tactical design."""
from pathlib import Path
from PIL import Image
import json,math,hashlib,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-environment-20261023';A=R/'assets/chapter5-environment-20261023/maps'
read=lambda p:json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
notes={'M51':'王都内廷是室外石庭与两间去顶病房；院落、室内床位、医护出口及花园材质关系正确，原图保留。','M52':'登天桥是露天石制桥面，不是室内走廊；中央旧紫色铺面统一为风化大石铺，桥栏、三段控制点、海水和崖岸保持。','F51':'祭所底层是地下水工层，两处装置、室内工作间、检修木桥和贯通人工水渠保留；石砌工作地与主通廊统一室内磨损石板，配合较冷的地下光，区别露天砌石。','F52':'日宫下层已采用去顶室内、神宫大理石地、北门框、设备间和人工蓄水池，空间表达正确，原图保留。','S51':'旧书库已是完整去顶室内，阅读翼木地、中央石廊和真实书架阻挡正确，原图保留；战后记录室单独修正。','J53':'神宫前庭为露天园林石庭，完整正殿属于外部建筑；双侧门阵、同层池桥与室外石铺合理，原图保留。','J54':'神座为露天高台，神宫大理石上庭、园林与三座真实阶口成立；台地挡墙、池岸和退守区已与行动一致，原图保留。'}
reports=[]
for code in read(O/'codes.json'):
 d=read(O/f'baseline/{code}.json');edits=[]
 if code in ['M52','F51']:
  old=Image.open(R/d['art_atlas'][6:]).convert('RGBA');cells=[old.crop((x,y,x+16,y+16))for y in range(0,old.height,16)for x in range(0,old.width,16)];cache={}
  material='assets/chapter5-spatial-20261022/east-finale/courtyard-stone.png'if code=='M52'else'assets/chapter5-spatial-20261022/library/interior-stone.png';im=Image.open(R/material).convert('RGBA')
  for y,row in enumerate(d['visual_ground']):
   for x,mark in enumerate(row):
    if mark not in ('b='if code=='M52'else'bc='):continue
    key=(x%4,y%4)
    if key not in cache:cache[key]=len(cells);cells.append(im.crop((x%4*16,y%4*16,x%4*16+16,y%4*16+16)))
    d['art_layers'][0][y][x]=cache[key];edits.append({'cell':[x,y],'material':'weathered outdoor bridge stone'if code=='M52'else'indoor stone'})
  A.mkdir(parents=True,exist_ok=True);atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
  for i,t in enumerate(cells):atlas.paste(t,(i%32*16,i//32*16))
  p=A/(code+'-terrain.png');atlas.save(p);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True);d['art_atlas']='res://'+str(p.relative_to(R))
  if code=='F51':d['map_tint']=[.88,.90,.94,1.0];edits.append({'ambient':'subdued underground workshop light'})
  d['material_review_version']='0.10.15-environment';d['environment_review']={'version':'0.10.15-environment','conclusion':notes[code],'geometry_and_rules_unchanged':True};write(R/f'data/stages/{code}.json',d)
 reports.append({'code':code,'name':d['name_zh'],'changed':bool(edits),'conclusion':notes[code],'edits':edits,'map_sha256':hashlib.sha256((R/f'data/stages/{code}.json').read_bytes()).hexdigest()})
write(O/'material-review.json',{'passed':True,'maps':reports,'new_generated_art':False,'source':'Existing native floor tiles only. All collision, actors, props, doors, objectives and animation code retained.'})
print({m['code']:len(m['edits'])for m in reports})
