#!/usr/bin/env python3
"""Snapshot current package expectations; --freeze only after runtime approval."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter1-climate-20261022'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
prior=read(R/'reports/chapter5-spatial-20261022/package-expected.json')
result={'frozen':'--freeze'in sys.argv,'software_version':'0.10.3','material_revision':'0.10.11-climate','maps':{},'climate_json':{},'climate_textures':{},'winter_nature':[],
 'existing_compat_paths':prior['existing_compat_paths'],'forbidden_new_compat_versions':prior['forbidden_new_compat_versions']+['0.10.11-climate'],
 'excluded_prefixes':['res://source','res://reports','res://tests','res://tools'],
 'new_offline_source_paths':['res://'+str(p.relative_to(R))for p in sorted((R/'source/chapter1-climate-20261022').rglob('*'))if p.is_file()],
 'core_snapshot_hashes':{str(p.relative_to(R)):sha(p)for p in sorted((R/'core').glob('*.gd'))},
 'project_godot_sha256':sha(R/'project.godot'),'export_presets_sha256':sha(R/'export_presets.cfg'),
 'scope':'Exact 40 current maps plus chapter1 climate world/hub JSON and textures. No compatibility copies added.'}
for p in sorted((R/'data/stages').glob('*.json')):
 d=read(p)
 result['maps'][p.stem]={'sha256':sha(p),'revision':d.get('tactical_review_version',''),'material_revision':d.get('material_review_version','')}
assert len(result['maps'])==40
for p in [R/'data/chapter1_world_climate.json',R/'data/chapter1_hub_climate.json',R/'assets/nature/nature.json']+sorted((R/'assets/chapter1-climate-20261022').rglob('*.json')):
 result['climate_json']['res://'+str(p.relative_to(R))]=sha(p)
for p in sorted((R/'assets/chapter1-climate-20261022').rglob('*.png')):
 im=Image.open(p)
 result['climate_textures']['res://'+str(p.relative_to(R))]={'size':list(im.size),'source_png_sha256':sha(p),'bytes':p.stat().st_size}
result['winter_nature']=[a for a in read(R/'assets/nature/nature.json')['sprites']if str(a['key']).startswith('climate_snow_')]
assert len(result['winter_nature'])==4
target=O/('package-expected.json'if result['frozen']else'package-expected-draft.json')
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(target),'frozen':result['frozen'],'maps':len(result['maps']),'json':len(result['climate_json']),'textures':len(result['climate_textures']),'rocks':len(result['winter_nature']),'source_exclusions':len(result['new_offline_source_paths'])}))
