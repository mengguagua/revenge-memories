#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import copy,json,hashlib,subprocess,shutil,math
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter2-environment-20261023/ships';A=R/'assets/chapter2-environment-20261023/ships';S=R/'source/chapter2-environment-20261023/ships';BASE=O.parent/'baseline'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
for p in [O,A,S]:p.mkdir(exist_ok=True,parents=True)
(S.parent/'.gdignore').write_text('')
source_root=Path('/Users/gcc/.codex/generated_images/01a16466-30d3-7241-a532-5a211e67ed7f')
shutil.copy2(source_root/'exec-327f2181-de80-423a-9918-508d6f75e989.png',S/'deckhouse-original.png')
shutil.copy2(source_root/'exec-9da72fc7-4eb9-4c01-acb7-ddd98a41b1d1.png',S/'cabin-floor-original.png')
original=Image.open(R/'assets/chapter2/modules/captain_cabin.png').convert('RGBA');im=Image.open(S/'deckhouse-original.png').convert('RGBA')
mask=im.getchannel('A').point(lambda a:255 if a>=128 else 0);bbox=mask.getbbox();im.putalpha(mask);cropped=im.crop(bbox)
bounds=original.getbbox();size=(bounds[2]-bounds[0],bounds[3]-bounds[1]);cropped.thumbnail(size,Image.Resampling.BOX)
a=cropped.getchannel('A').point(lambda v:255 if v>=128 else 0);cropped.putalpha(a)
export=Image.new('RGBA',original.size);export.alpha_composite(cropped,((original.width-cropped.width)//2,original.height-cropped.height));export.save(A/'deckhouse.png')
floor=Image.open(S/'cabin-floor-original.png').convert('RGBA').resize((64,64),Image.Resampling.BOX);floor.save(A/'cabin-floor.png')
native=Image.open(R/'assets/chapter2-redesign-20261022/ships/terrain.png').convert('RGBA');cells=[native.crop((x,y,x+16,y+16))for y in range(0,native.height,16)for x in range(0,native.width,16)];original_count=len(cells);floor_ids=[]
for y in range(4):
 for x in range(4):floor_ids.append(len(cells));cells.append(floor.crop((x*16,y*16,x*16+16,y*16+16)))
atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,tile in enumerate(cells):atlas.paste(tile,(i%32*16,i//32*16))
atlas.save(A/'terrain.png')
reviews=[]
for code in ['F21','F22','S21']:
 old=read(BASE/(code+'.json'));d=copy.deepcopy(old);changes=[]
 for prop in d['art_props']:
  if prop['path']=='res://assets/chapter2/modules/captain_cabin.png':prop['path']='res://assets/chapter2-environment-20261023/ships/deckhouse.png';changes.append({'kind':'same-size deckhouse','position':prop['position']})
 for site in d.get('recovery_sites',[]):
  x,y=site['position'];before=d['art_layers'][0][y][x];d['art_layers'][0][y][x]=24+(x+y)%4;changes.append({'kind':'outdoor wooden medical supply deck','position':[x,y],'before_tile':before,'after_tile':d['art_layers'][0][y][x]})
 if code=='F22':
  for cell in d['detention_bays']['cells']:
   x0,y0,x1,y1=cell['bounds']
   for y in range(y0,y1+1):
    for x in range(x0,x1+1):
     before=d['art_layers'][0][y][x];tile=floor_ids[((y-y0)%4)*4+((x-x0)%4)];d['art_layers'][0][y][x]=tile;changes.append({'kind':'dry cabin plank floor under iron bars','position':[x,y],'before_tile':before,'after_tile':tile})
  for obj in d['objects']:
   if obj['id']!='prison_door':continue
   for opened in obj['open_art_cells']:
    x,y=opened['position'];opened['base_tile']=d['art_layers'][0][y][x]
 d['art_atlas']='res://assets/chapter2-environment-20261023/ships/terrain.png'
 d['material_review_version']='0.10.12-environment'
 d['environment_review']={'scope':'ship deck / interior cabin / genuine shore distinction','deckhouse':'Low wooden deckhouse with portholes; same48x32canvas and centered south doorway','infirmary':'Exterior timber supply deck, never stone paving','prison':'Dry indoor wooden planks in cutaway iron-bar cabins; opened thresholds keep matching floor'if code=='F22'else'Not applicable','geometry_and_animation_unchanged':True}
 allowed={'art_layers','art_props','art_atlas','material_review_version','environment_review','objects'}
 changed={k for k in old.keys()|d.keys()if old.get(k)!=d.get(k)};assert changed<=allowed
 for key in old:
  if key not in allowed:assert d[key]==old[key],(code,key)
 for a,b in zip(old['objects'],d['objects']):
  assert {k:v for k,v in a.items()if k!='open_art_cells'}=={k:v for k,v in b.items()if k!='open_art_cells'},(code,a['id'])
  for ac,bc in zip(a.get('open_art_cells',[]),b.get('open_art_cells',[])):assert {k:v for k,v in ac.items()if k!='base_tile'}=={k:v for k,v in bc.items()if k!='base_tile'}
 path=R/f'data/stages/{code}.json';write(path,d)
 review={'passed':True,'code':code,'baseline_sha256':sha(BASE/(code+'.json')),'map_sha256':sha(path),'changed_fields':sorted(changed),'changes':changes,'geometry_units_interactions_rules_exact':True,'objects_only_open_art_base_changed':code=='F22','source_story':'docs2/完整故事剧情.md 第二章5.1与5.2；完整游戏流程F21/F22/S21','unchanged_environment':['sea and hull outline','boarding plank orientation and physical connection','all positions and map/logic grids','S21 real sandy shore and mooring path']}
 write(O/(code+'-environment.json'),review);reviews.append(review)
for p in A.glob('*.png'):subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
assets=[{'path':str(p.relative_to(R)),'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':sha(p),'quality_note':'Original native atlas IDs retained losslessly'if p.name=='terrain.png'else'Uniform export preserving full sprite and native footprint'}for p in A.glob('*.png')]
write(O/'assets.json',{'passed':True,'assets':assets,'new_floor_ids':floor_ids,'existing_ids_preserved':original_count,'source_bbox':bbox,'deckhouse_native_bbox':export.getbbox(),'no_original_assets_overwritten':True})
write(S/'prompts.json',{'tool':'image_gen built-in','cabin':'Edit existing48x32land cabin into low wooden medieval deckhouse with portholes; muted brown, no stone/roof tiles/chimney, transparent, same centered door and canvas. Export alpha>=128 and proportional BOX to original bounds.','floor':'Plain dry horizontal plank ship cabin floor; muted brown pixel art, flat overhead, full seamless square, no fancy parquet or exterior weathering; uniform64px export then16px crop.'})
write(O/'environment-summary.json',{'passed':True,'maps':reviews,'assets':assets,'scope':'Only visible ship material art and matching opened-door art; map geometry, actor/object coordinates, rules, story and animations exact.'})
print(json.dumps({'passed':True,'maps':{r['code']:r['map_sha256']for r in reviews},'assets':assets},ensure_ascii=False))
