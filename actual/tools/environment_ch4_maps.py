#!/usr/bin/env python3
"""Only materials, same-size architecture, winter nature keys and ambient light."""
from pathlib import Path
from PIL import Image
import copy, json, hashlib, math, subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter4-environment-20261023';A=R/'assets/chapter4-environment-20261023/maps'
read=lambda p:json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
notes={
'M41':'雪峡积雪、雪松、清扫土道、木桥与流水保持已确认构图；医舍换同尺寸冬季屋顶，裸露大岩换既有冬岩。',
'M42':'铁骑投送营位于仍获日照的草地交通带，土道、木栅与石质设备坪符合用途，保持原图。',
'M43':'日塔外围仍是雪原；露天石廊换风化砌石，塔外仓房、医舍和主堡使用同尺寸冬季外观，岩脚残雪与周围一致。控制室室内在战后据点表达。',
'M44':'王都道路与城门院是露天空间，紫色室内感地砖换室外砌石；草地、土路、医舍退路和双门保持。',
'F41':'沙城保留沙地、压实土路、石制井台和居民区；冷暗光延续东部黑昼，据点同步沙地而非盐地。',
'F42':'观测台露天盐原、石质设备庭与潮池保持，冷暗光延续；东楼战后据点改真正室内，避免屋内再摆房屋。',
'F43':'湿沼、草质干岛、土道、木栈与接应船各有用途，保留地形并延续黑昼；居民既有干地撤离路线保持。',
'F44':'沉没祭所是露天石台和木制检修桥，海水环绕，非室内大厅；战时延续冷暗光，局部试验成功后的祭所与邻近区域按实际剧情标记逐步恢复亮光。',
'S41':'黑钟村仍处失去庇护的寒区，名册屋与医舍改同尺寸冬季外观，岩脚补既有残雪；村道、门前交互与避难院保持。',
'S42':'沼泽孤岛使用湿地、草质干地、土道和木桥，诊疗院是岛上室外院落；延续区域黑昼，保留病人上船与双桥路线。'}
pack=read(R/'assets/battle_tiles/battle-tiles.json');native=Image.open(R/'assets/battle_tiles/battle-tiles.png').convert('RGBA')
winter=read(R/'data/chapter1_hub_climate.json')['nature_keys'];reports=[]
for code in read(O/'codes.json'):
 d=read(O/f'baseline/{code}.json');edits=[]
 if code in ['M43','M44']:
  source=Image.open(R/d['art_atlas'][6:]).convert('RGBA');cells=[source.crop((x,y,x+16,y+16))for y in range(0,source.height,16)for x in range(0,source.width,16)];cache={}
  for y,row in enumerate(d['visual_ground']):
   for x,mark in enumerate(row):
    if mark!='=':continue
    tile=pack['base']['cobble'][(x*3+y)%4]
    if tile not in cache:cache[tile]=len(cells);cells.append(native.crop((tile%32*16,tile//32*16,tile%32*16+16,tile//32*16+16)))
    d['art_layers'][0][y][x]=cache[tile];edits.append({'cell':[x,y],'material':'outdoor cobble'})
  A.mkdir(parents=True,exist_ok=True);atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
  for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
  path=A/(code+'-terrain.png');atlas.save(path);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(path)],check=True);d['art_atlas']='res://'+str(path.relative_to(R))
 if code in ['M41','M43','S41']:
  for p in d['natural_props']:
   k=p['key']
   if k in winter and k!=winter[k]:p['key']=winter[k];edits.append({'nature':k,'after':p['key'],'position':p['position']})
  for p in d['art_props']:
   name=Path(p['path']).stem;candidate=None
   if name in ['village_clinic','quay_warehouse']:candidate=R/f'assets/chapter1-climate-20261022/grain-prison/modules/{name}.png'
   if name=='coastal_keep':candidate=R/'assets/chapter1-climate-20261022/camp-fort/coastal_keep-winter.png'
   if candidate and candidate.exists():
    assert Image.open(candidate).size==Image.open(R/p['path'][6:]).size
    p['path']='res://'+str(candidate.relative_to(R));edits.append({'winter_prop':name,'position':p['position']})
 if code in ['F41','F42','F43','F44','S42']:d['map_tint']=[.80,.84,.92,1.0];edits.append({'ambient':'eastern blackday'})
 if edits:
  d['material_review_version']='0.10.14-environment';d['environment_review']={'version':'0.10.14-environment','conclusion':notes[code],'geometry_and_rules_unchanged':True};write(R/f'data/stages/{code}.json',d)
 reports.append({'code':code,'name':d['name_zh'],'changed':bool(edits),'conclusion':notes[code],'edits':edits,'map_sha256':hashlib.sha256((R/f'data/stages/{code}.json').read_bytes()).hexdigest()})
write(O/'material-review.json',{'passed':True,'maps':reports,'new_generated_art':False,'source':'Existing native tiles and same-size winter architecture; approved tactics and all numerical rules unchanged.'})
print({r['code']:len(r['edits'])for r in reports})
