#!/usr/bin/env python3
"""Independent frozen-baseline audit; never writes production maps or source saves."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-spatial-20261022';BASE=O/'baseline';CODES=[c for c in json.loads((O/'codes.json').read_text()) if c!='M41']
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];errors=[];records=[]
def check(value,label):
 checks.append(label)
 if not value:errors.append(label)
for code in CODES:
 before_path=BASE/(code+'.json');current_path=R/f'data/stages/{code}.json';before=read(before_path);after=read(current_path);changed=[];unit_count=0
 for group in ['enemies','npc_units','reinforcements']:
  check(len(before[group])==len(after[group]),f'{code} {group} count exact')
  check([u['id']for u in before[group]]==[u['id']for u in after[group]],f'{code} {group} identity and order exact')
  for a,b in zip(before[group],after[group]):
   unit_count+=1
   for key in sorted(set(a)|set(b)):
    if key=='position':continue
    check(a.get(key)==b.get(key),f'{code} {a["id"]} unchanged {key}')
   if a['position']!=b['position']:changed.append({'group':group,'id':a['id'],'before':a['position'],'after':b['position']})
 for key in ['schema_version','id','code','name_zh','chapter','route','node','characters','terrain','enemy_group_ids','reinforcement_turn','burner_departure_turn','burn_start','summon_template','escort_move','boss_id','goal','cause','before','during','after','absent_branch','optional','contract','ai_and_timing','equipment_revision','clear_training_exp']:
  check(before.get(key)==after.get(key),f'{code} unchanged contract {key}')
 check(len(before['objects'])==len(after['objects']),f'{code} object count exact')
 check([o['id']for o in before['objects']]==[o['id']for o in after['objects']],f'{code} object identity/order exact including rescue index')
 coordinate_or_art={'position','approach','approaches','entrance_cells','open_art_cells','open_art_props','opens','sprite','sprite_path','sprite_offset','building','door_visual','show_indicator'}
 object_visual_changes=[]
 for a,b in zip(before['objects'],after['objects']):
  for key in sorted(set(a)|set(b)):
   if key in coordinate_or_art:
    if a.get(key)!=b.get(key):object_visual_changes.append({'id':a['id'],'field':key,'before':a.get(key),'after':b.get(key)})
   else:check(a.get(key)==b.get(key),f'{code} object {a["id"]} unchanged {key}')
 for a,b in zip(before.get('event_boats',[]),after.get('event_boats',[])):
  for key in sorted(set(a)|set(b)):
   if key not in ['path','position']:check(a.get(key)==b.get(key),f'{code} boat {a["id"]} unchanged {key}')
 check(len(before.get('event_boats',[]))==len(after.get('event_boats',[])),f'{code} exact boat count')
 records.append({'code':code,'baseline_sha256':sha(before_path),'current_sha256':sha(current_path),'unit_count':unit_count,'unit_changes':changed,'object_coordinate_art_changes':object_visual_changes,'original_story_timing_stats_AI_equipment_retained':True})
original=read(BASE/'maps.json');unchanged=[];material_only=[]
art_keys={'art_atlas','art_columns','art_layers','material_review_version'}
for code,expected in sorted(original.items()):
 if code in CODES:continue
 path=R/f'data/stages/{code}.json';actual=sha(path)
 prior=read(BASE/(code+'.json'));current=read(path)
 differences=[k for k in sorted(set(prior)|set(current)) if prior.get(k)!=current.get(k)]
 object_art_only=True
 if 'objects' in differences:
  a,b=prior['objects'],current['objects'];object_art_only=len(a)==len(b)
  for x,y in zip(a,b):
   object_art_only &= {k:v for k,v in x.items()if k!='open_art_cells'}=={k:v for k,v in y.items()if k!='open_art_cells'}
   aa,bb=x.get('open_art_cells',[]),y.get('open_art_cells',[]);object_art_only &= len(aa)==len(bb)
   for xx,yy in zip(aa,bb):object_art_only &= {k:v for k,v in xx.items()if k!='base_tile'}=={k:v for k,v in yy.items()if k!='base_tile'}
 check(all(k in art_keys or k=='objects' and object_art_only for k in differences),f'{code} outside-chapter changes strictly material only')
 if differences:material_only.append(code)
 unchanged.append({'code':code,'baseline_sha256':expected,'current_sha256':actual,'unchanged':actual==expected,'changed_keys':differences,'layout_units_story_rules_unchanged':True})
check(len(unchanged)==33,'all 33 previous-chapter maps checked')
for record in records:check(record['baseline_sha256']==original[record['code']],record['code']+' frozen source file matches baseline manifest')
core_records=[]
for path,expected in read(BASE/'core.json').items():
 actual=sha(R/path);check(actual==expected,'core unchanged '+path)
 core_records.append({'path':path,'baseline_sha256':expected,'current_sha256':actual,'unchanged':actual==expected})
report={'passed':not errors,'checks':len(checks),'check_labels':checks,'errors':errors,'maps':records,'outside_scope':unchanged,'outside_scope_count':len(unchanged),'material_only_maps':material_only,'core_files':core_records,'M11_unchanged':next(x['unchanged']for x in unchanged if x['code']=='M11'),'approved_M41_unchanged':next(x['unchanged']for x in unchanged if x['code']=='M41'),'scope':'Every key in every enemy/NPC/reinforcement except position, every narrative/timing/terrain-rule contract, and interaction semantics excluding explicit coordinate/art fields. For the other 33 stage files only atlas/layer/material revision and door-open base art tile keys may differ; layout, units, objects, story and rules remain exact. All core files including animation and battle resolution unchanged byte for byte.'}
(O/'invariants-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':report['checks'],'outside_scope':len(unchanged),'errors':errors},ensure_ascii=False));raise SystemExit(0 if not errors else 1)
