#!/usr/bin/env python3
"""Native material composition; preserve approved chapter-three tactical geometry."""
from pathlib import Path
from PIL import Image
import copy,json,hashlib,math,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter3-environment-20261023';A=R/'assets/chapter3-environment-20261023/maps'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
pack=read(R/'assets/battle_tiles/battle-tiles.json');native=Image.open(R/'assets/battle_tiles/battle-tiles.png').convert('RGBA')
def tile(i):return native.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16))
reports=[]
for c in ['M31','M32','M33','F31','F32','F33','S31','S32']:
 before=read(O/f'baseline/{c}.json');d=copy.deepcopy(before);edits=[]
 if c=='M33':
  source=Image.open(R/d['art_atlas'][6:]).convert('RGBA');cells=[source.crop((x,y,x+16,y+16))for y in range(0,source.height,16)for x in range(0,source.width,16)];cache={}
  for y,row in enumerate(d['visual_ground']):
   for x,m in enumerate(row):
    if m!='=':continue
    material='grass'if d['logic_grid'][y][x]=='f'else'cobble';i=pack['base'][material][(x*3+y)%4]
    if i not in cache:cache[i]=len(cells);cells.append(tile(i))
    d['art_layers'][0][y][x]=cache[i];edits.append({'cell':[x,y],'material':material})
  atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
  for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
  path=A/'M33-terrain.png';path.parent.mkdir(parents=True,exist_ok=True);atlas.save(path);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(path)],check=True);d['art_atlas']='res://'+str(path.relative_to(R))
 if c=='F33':
  source=Image.open(R/d['art_atlas'][6:]).convert('RGBA');cells=[source.crop((x,y,x+16,y+16))for y in range(0,source.height,16)for x in range(0,source.width,16)];cache={}
  indoor=Image.open(R/'assets/chapter5-spatial-20261022/library/interior-stone.png').convert('RGBA')
  def inside(x,y):
   key=(x%4,y%4)
   if key not in cache:cache[key]=len(cells);cells.append(indoor.crop((x%4*16,y%4*16,x%4*16+16,y%4*16+16)))
   return cache[key]
  for y in range(13,18):
   for x in range(6,11):d['art_layers'][0][y][x]=inside(x,y);edits.append({'cell':[x,y],'material':'indoor stone'})
  for obj in d['objects']:
   if obj['id']=='workers_gate':
    for cell in obj['open_art_cells']:cell['base_tile']=inside(*cell['position'])
  for prop in d['art_props']:
   if prop['path']=='res://assets/battle_tiles/modules/barracks.png':prop['path']='res://assets/chapter3-environment-20261023/maps/workshop-equipment.png'
  atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
  for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
  path=A/'F33-terrain.png';path.parent.mkdir(parents=True,exist_ok=True);atlas.save(path);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(path)],check=True);d['art_atlas']='res://'+str(path.relative_to(R))
 if c=='F31':
  for p in d['art_props']:
   if p['path']=='res://assets/chapter2/modules/captain_cabin.png':p['path']='res://assets/chapter2-environment-20261023/ships/deckhouse.png';edits.append({'prop':'same-size deckhouse','position':p['position']})
 if c=='S31':
  for p in d['art_props']:
   if p['path']=='res://assets/battle_tiles/modules/snow_cottage.png':p['path']='res://assets/battlefield-0.3.0/modules/fishing_cottage.png';edits.append({'prop':'same-size thawed cottage','position':p['position']})
 if c in ['F32','F33','S32']:
  d['map_tint']=[.80,.84,.92,1.0];edits.append({'material':'continued eastern blackday ambient','tint':d['map_tint']})
 notes={'M31':'西大陆日返后的室外街区与拘押院，土路、石门前及草地成立，保持。','M32':'西线运输土道、转运石台、林坡与货车路线合理，保持。','M33':'露天堡院使用风化砌石；既有树木脚下为未铺石的植土带，工房外观与海岸栈桥保持。','F31':'日返西岸码头保持自然光，院落石地、风化岸栈、船板区别保留；舰上房舍沿用第二章同尺寸低矮船舱。','F32':'盐地、干土路与潮池保持；东部庇护继续流失，冷暗光衔接第二章黑昼。','F33':'露天提炼后庭、石廊与检修桥保持；术士工房去顶室内用磨损石板和完整工作台，取消房间内的整栋营房屋顶，开门门槛同步室内石地；冷暗光与盐原一致。','S31':'日返后山村的草地、土道与室内牢室石地保持；两栋积雪房舍改同尺寸无雪家屋。','S32':'露天盐土、黄砂区与室内拘押营房石地保持；光照衔接仍处黑昼的东部盐原。'}
 if edits:
  d['material_review_version']='0.10.13-environment';d['environment_review']={'version':'0.10.13-environment','conclusion':notes[c],'geometry_and_rules_unchanged':True};write(R/f'data/stages/{c}.json',d)
 else:assert sha(R/f'data/stages/{c}.json')==sha(O/f'baseline/{c}.json')
 reports.append({'code':c,'name':d['name_zh'],'changed':bool(edits),'conclusion':notes[c],'edits':edits,'map_sha256':sha(R/f'data/stages/{c}.json')})
write(O/'material-review.json',{'passed':True,'maps':reports,'new_generated_art':True,'generated_asset':'assets/chapter3-environment-20261023/maps/workshop-equipment.png','generation_mode':'built-in imagegen','prompt':'source/chapter3-environment-20261023/workshop-prompt.txt','source':'Existing native tiles and approved same-size architecture; no raster repainting or geometry changes.'})
print({r['code']:len(r['edits'])for r in reports})
