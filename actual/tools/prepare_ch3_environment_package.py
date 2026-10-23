#!/usr/bin/env python3
"""Snapshot current package expectations; --freeze only after runtime approval."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter3-environment-20261023'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def visible_hash(p):
 im=Image.open(p).convert('RGBA');data=bytearray(im.tobytes())
 for i in range(0,len(data),4):
  if data[i+3]==0:data[i:i+3]=b'\0\0\0'
 return hashlib.sha256(data).hexdigest()
prior=read(R/'reports/chapter1-climate-20261022/package-expected.json')
result={'frozen':'--freeze'in sys.argv,'software_version':'0.10.3','material_revision':'0.10.13-environment','maps':{},'environment_json':{},'environment_textures':{},'retained_winter_nature':[],
 'existing_compat_paths':prior['existing_compat_paths'],'forbidden_new_compat_versions':prior['forbidden_new_compat_versions']+['0.10.13-environment'],
 'excluded_prefixes':['res://source','res://reports','res://tests','res://tools'],
 'new_offline_source_paths':['res://'+str(p.relative_to(R))for p in sorted((R/'source/chapter3-environment-20261023').rglob('*'))if p.is_file()],
 'core_snapshot_hashes':{str(p.relative_to(R)):sha(p)for p in sorted((R/'core').glob('*.gd'))},
 'project_godot_sha256':sha(R/'project.godot'),'export_presets_sha256':sha(R/'export_presets.cfg'),
 'scope':'Exact40 current maps plus chapter2 environment hubs/world overview and new textures; first-chapter climate resources retained. No compatibility copies added.'}
for p in sorted((R/'data/stages').glob('*.json')):
 d=read(p)
 result['maps'][p.stem]={'sha256':sha(p),'revision':d.get('tactical_review_version',''),'material_revision':d.get('material_review_version','')}
assert len(result['maps'])==40
for p in [R/'data/formal_world.json',R/'data/chapter2_hubs.json',R/'data/chapter2_hub_environment.json',R/'data/chapter3_hubs.json',R/'data/chapter3_hub_environment.json',R/'data/chapter3_world_environment.json',R/'data/chapter1_world_climate.json',R/'data/chapter1_hub_climate.json',R/'assets/nature/nature.json']+sorted((R/'assets/chapter3-environment-20261023').rglob('*.json')):
 result['environment_json']['res://'+str(p.relative_to(R))]=sha(p)
for p in sorted((R/'assets/chapter3-environment-20261023').rglob('*.png')):
 im=Image.open(p)
 result['environment_textures']['res://'+str(p.relative_to(R))]={'size':list(im.size),'source_png_sha256':sha(p),'visible_rgba_sha256':visible_hash(p),'bytes':p.stat().st_size}
result['retained_winter_nature']=[a for a in read(R/'assets/nature/nature.json')['sprites']if str(a['key']).startswith('climate_snow_')]
assert len(result['retained_winter_nature'])==4
target=O/('package-expected.json'if result['frozen']else'package-expected-draft.json')
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(target),'frozen':result['frozen'],'maps':len(result['maps']),'json':len(result['environment_json']),'textures':len(result['environment_textures']),'rocks':len(result['retained_winter_nature']),'source_exclusions':len(result['new_offline_source_paths'])}))
