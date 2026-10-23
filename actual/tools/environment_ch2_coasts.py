#!/usr/bin/env python3
"""Interior bedrock and prison stone corrections; approved maps stay mechanically exact."""
from pathlib import Path
from PIL import Image
import copy,hashlib,importlib.util,json,math,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter2-environment-20261023/coasts';BASE=O.parent/'baseline';A=R/'assets/chapter2-environment-20261023/coasts'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('native_masks',R/'tools/build_world_tiles.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
pack=read(R/'assets/battle_tiles/battle-tiles.json');native=Image.open(R/'assets/battle_tiles/battle-tiles.png').convert('RGBA');stone=Image.open(R/'assets/chapter5-spatial-20261022/library/interior-stone.png').convert('RGBA')
def native_tile(n):return native.crop((n%32*16,n//32*16,n%32*16+16,n//32*16+16))
def mask(grid,x,y):
 value=0
 for dx,dy,bit in [(0,-1,1),(1,0,2),(0,1,4),(-1,0,8),(1,-1,16),(1,1,32),(-1,1,64),(-1,-1,128)]:
  if 0<=y+dy<len(grid) and 0<=x+dx<len(grid[0])and grid[y+dy][x+dx]=='p':value|=bit
 for diagonal,a,b in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
  if not(value&a and value&b):value&=~diagonal
 return value
reports=[]
for c in ['F23','F24','F25','F26','S22']:
 old=read(BASE/(c+'.json'));d=copy.deepcopy(old);changed=[]
 if c in ['F25','S22']:
  source=R/d['art_atlas'].removeprefix('res://');im=Image.open(source).convert('RGBA');cols=d.get('art_columns',32)
  cells=[im.crop((x,y,x+16,y+16))for y in range(0,im.height,16)for x in range(0,im.width,16)];initial=len(cells);lookup={}
  for y,row in enumerate(d['visual_ground']):
   for x,q in enumerate(row):
    if c=='S22' and q=='p':
     # Native cave texture and authored terrain mask; no color painting.
     v=(x*3+y)%4;m=mask(d['visual_ground'],x,y);key=('bedrock',v,m)
     if key not in lookup:
      tile=native_tile(pack['base']['marsh'][v]);front=native_tile(pack['base']['cave'][v]);front.putalpha(M.alpha_mask(m));tile.alpha_composite(front);lookup[key]=len(cells);cells.append(tile)
     tile_id=lookup[key]
    elif c=='F25' and 25<=x<=27 and 19<=y<=20 or c=='F25'and(x,y)==(26,21):
     key=('interior-stone',x%4,y%4)
     if key not in lookup:lookup[key]=len(cells);cells.append(stone.crop((x%4*16,y%4*16,x%4*16+16,y%4*16+16)))
     tile_id=lookup[key]
    else:continue
    before=d['art_layers'][0][y][x];d['art_layers'][0][y][x]=tile_id;changed.append({'position':[x,y],'before_tile':before,'after_tile':tile_id})
  if c=='F25':
   door=next(o for o in d['objects']if o['id']=='pilot_prison');door['open_art_cells'][0]['base_tile']=d['art_layers'][0][21][26]
  atlas=Image.new('RGBA',(cols*16,math.ceil(len(cells)/cols)*16))
  for i,t in enumerate(cells):atlas.paste(t,(i%cols*16,i//cols*16))
  target=A/(c+'-terrain.png');target.parent.mkdir(parents=True,exist_ok=True);atlas.save(target);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(target)],check=True)
  d['art_atlas']='res://'+str(target.relative_to(R));d['material_review_version']='0.10.12-environment'
  d['environment_review']={'scope':'Chapter2 room/outdoor material review','note':'海洞主巷改用裸露灰岩，潮湿沉积厅与岩壁保持；不以户外黄土路表达地下空间。'if c=='S22'else'东侧剖面牢室六格及门槛改室内磨损石板，开门后仍是同一石门槛；外部土路/石院/风化木码头保持。','coordinates_and_rules_unchanged':True}
  write(R/f'data/stages/{c}.json',d)
  write(A/(c+'-terrain.json'),{'native_tile_size':16,'tile_count':len(cells),'original_tile_count':initial,'source_atlas':str(source.relative_to(R)),'source_pixels_preserved':True,'size':list(atlas.size),'bytes':target.stat().st_size,'purpose':d['environment_review']['note'],'quality_note':'Lossless independent atlas preserves original IDs and all native art; over200KB retains original pixel data instead of lossy resampling.'})
 if c in ['F23','F25']:
  d['map_tint']=[.82,.86,.94,1.]if c=='F23'else[.75,.8,.9,1.]
  d['material_review_version']='0.10.12-environment'
  d.setdefault('environment_review',{})['light']='黑昼初现，海岸轻冷暗'if c=='F23'else'军港继续黑昼，与战后据点H26的冷暗环境一致'
  write(R/f'data/stages/{c}.json',d)
 # Exact mechanical payload, with only the explicitly visual post-open cell excluded.
 for k in ['map','logic_grid','player_positions','enemies','npc_units','reinforcements','exit','targets','terrain','before','during','after','cause','contract','event_boats','reinforcement_turn']:
  assert old.get(k)==d.get(k),(c,k)
 a=copy.deepcopy(old['objects']);b=copy.deepcopy(d['objects'])
 for items in [a,b]:
  for o in items:o.pop('open_art_cells',None)
 assert a==b,(c,'object behavior mutated')
 if c=='F25':
  a=copy.deepcopy(old['objects']);b=copy.deepcopy(d['objects']);a[1]['open_art_cells'][0]['base_tile']=b[1]['open_art_cells'][0]['base_tile'];assert a==b
 else:assert old['objects']==d['objects']
 reports.append({'code':c,'passed':True,'changed':bool(changed)or c=='F23','source_sha256':sha(BASE/(c+'.json')),'map_sha256':sha(R/f'data/stages/{c}.json'),'material_cells':changed,'gameplay_geometry_coordinates_unchanged':True,'object_change':'pilot_prison open_art_cells[0].base_tile only'if c=='F25'else'none','note':d.get('environment_review',{}).get('note',{'F23':'沙滩、草坡、林崖与登陆湾相符，材质保留；改轻冷暗调与黑昼初现剧情一致。','F24':'黑昼冷暗调、石制灯庭、外景沙岸与草坡已经相符，保持原样。','F26':'古道室外石路、海水、草坡与两条居民船航路相符，保持原样。'}[c]if c in ['F23','F24','F26']else'')})
write(O/'material-review.json',{'passed':True,'maps':reports,'changed':['F23','F25','S22'],'unchanged':['F24','F26'],'source_policy':'All current-story and stage data reviewed; existing bitmap tiles/materials reused. No generated art required.'})
print(json.dumps([{'code':x['code'],'changed':x['changed'],'cells':len(x['material_cells'])}for x in reports]))
