#!/usr/bin/env python3
"""Pure material correction: exposed rock sprites on local sand/salt, no cave carpet."""
from pathlib import Path
import json,hashlib,copy,shutil
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-spatial-20261022/material-audit';ART=R/'assets/material-audit-20261022/chapter4';ART.mkdir(parents=True,exist_ok=True);(O/'baseline').mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
source=R/'assets/chapter4-redesign-20261022/east/terrain.png';target=ART/'terrain.png';shutil.copy2(source,target);records=[]
for code,start in [('F41',36),('F42',40)]:
 path=R/f'data/stages/{code}.json';frozen=O/f'baseline/{code}.json'
 if not frozen.exists():shutil.copy2(path,frozen)
 before=json.loads(frozen.read_text());after=copy.deepcopy(before);changes=[]
 for y,row in enumerate(before['logic_grid']):
  for x,ch in enumerate(row):
   if ch!='^':continue
   old=after['art_layers'][0][y][x];new=start+(x*5+y*3)%4;after['art_layers'][0][y][x]=new;changes.append({'position':[x,y],'before_tile':old,'after_tile':new})
 after['art_atlas']='res://assets/material-audit-20261022/chapter4/terrain.png';after['material_review_version']='0.10.10-material'
 allowed={'art_layers','art_atlas','material_review_version'}
 assert all(before.get(k)==after.get(k)for k in set(before)|set(after)if k not in allowed)
 assert before['art_layers'][1:]==after['art_layers'][1:]
 for y,row in enumerate(before['logic_grid']):
  for x,ch in enumerate(row):
   if ch!='^':assert before['art_layers'][0][y][x]==after['art_layers'][0][y][x]
 write(path,after);records.append({'code':code,'before_sha256':sha(frozen),'after_sha256':sha(path),'changed_ground_cells':changes,'all_geometry_actors_objects_rules_story_natural_props_unchanged':True,'tactical_revision_preserved':before['tactical_review_version'],'material_revision':after['material_review_version']})
write(O/'chapter4-rock-material-changes.json',{'passed':True,'maps':records,'atlas_source':str(source.relative_to(R)),'new_atlas':str(target.relative_to(R)),'atlas_pixels_exact_copy':sha(source)==sha(target),'description':'Source bare_rock was an alias of cave terrain. Render existing full native rocks directly over local sand/salt, as M41 rocks stand over snow. No logical grid, movement cost, collision, scene coordinates, foliage or rules changed.'});print([(r['code'],len(r['changed_ground_cells']),r['after_sha256'])for r in records])
