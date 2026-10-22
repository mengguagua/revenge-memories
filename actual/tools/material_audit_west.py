#!/usr/bin/env python3
"""Material-only repairs found by direct native image review and atlas lookup."""
from pathlib import Path
from PIL import Image
import json,hashlib,copy,importlib.util
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-spatial-20261022/material-audit';BASE=O/'west-baseline';ART=R/'assets/chapter5-spatial-20261022/materials-west';BASE.mkdir(parents=True,exist_ok=True);(BASE/'.gdignore').touch()
sp=importlib.util.spec_from_file_location('native_material',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(sp);sp.loader.exec_module(L)
for c in ['S11','M13']:
 source=R/f'data/stages/{c}.json';frozen=BASE/f'{c}.json'
 if not frozen.exists():frozen.write_bytes(source.read_bytes())
 old=json.loads(frozen.read_text());d=copy.deepcopy(old);atlas_path=R/old['art_atlas'].removeprefix('res://');metadata=json.loads(atlas_path.with_suffix('.json').read_text());im=Image.open(atlas_path).convert('RGBA');a=L.Atlas();a.cells=[im.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16))for i in range(metadata['tile_count'])];a.original=len(a.cells);a.add={};a.shores={};L.ART=ART/c
 edits=[]
 if c=='S11':
  mapping={tile:12+i for i,tile in enumerate([44,45,46,47])}
  for name,ids in metadata['additional_transitions'].items():
   if name.startswith('dirt:marsh:'):
    mask=int(name.split(':')[-1])
    for v,tile in enumerate(ids):mapping[tile]=a.edge('dirt','cave',mask,v)
  for y,row in enumerate(d['art_layers'][0]):
   for x,tile in enumerate(row):
    if tile in mapping:d['art_layers'][0][y][x]=mapping[tile];edits.append([x,y,tile,mapping[tile]])
  reason='旧矿道大厅和土路边使用marsh44–47，没有剧情沼泽依据；改为cave12–15岩屑地面，土路只保留压实矿道语义。连续矿岩/全部地形逻辑和坐标不变。'
 else:
  for ox,oy in [(4,7),(23,10)]:
   for y in range(oy,oy+4):
    for x in range(ox,ox+5):
     tile=d['art_layers'][0][y][x];new=16+(x+y)%4;d['art_layers'][0][y][x]=new;edits.append([x,y,tile,new])
  for obj in d['objects']:
   for cell in obj.get('open_art_cells',[]):
    x,y=cell['position'];cell['base_tile']=16+(x+y)%4
  reason='原剧情明确两间牢房；此前牢房地坪与外院同一土路材质。仅囚室内部及墙/门槛下地坪换朴素室内石砖16–19，外院土路、河岸草地、木桥保持。'
 a.save();d['art_atlas']=f'res://assets/chapter5-spatial-20261022/materials-west/{c}/terrain.png';d['material_review_version']='0.10.10-material';source.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 for aobj,bobj in zip(old['objects'],d['objects']):
  assert {k:v for k,v in aobj.items()if k!='open_art_cells'}=={k:v for k,v in bobj.items()if k!='open_art_cells'}
  for ac,bc in zip(aobj.get('open_art_cells',[]),bobj.get('open_art_cells',[])):
   assert {k:v for k,v in ac.items()if k!='base_tile'}=={k:v for k,v in bc.items()if k!='base_tile'}
 allowed={'art_atlas','art_layers','material_review_version','objects'}
 assert all(d[k]==old[k]for k in old if k not in allowed),(c,'nonvisual change')
 (O/f'{c}-material-patch.json').write_text(json.dumps({'code':c,'reason':reason,'permitted_fields':sorted(allowed),'actual_changed_fields':[k for k in d if d[k]!=old.get(k)],'tiles_logic_coords_objects_rules_unchanged':True,'changed_art_cells':edits,'before_sha256':hashlib.sha256(frozen.read_bytes()).hexdigest(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'atlas_source':str(atlas_path),'atlas':d['art_atlas']},ensure_ascii=False,indent=2)+'\n')
 print(c,len(edits),hashlib.sha256(source.read_bytes()).hexdigest())
