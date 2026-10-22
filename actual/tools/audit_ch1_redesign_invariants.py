#!/usr/bin/env python3
"""Independent frozen-baseline audit; never writes production maps or source saves."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter1-redesign-20261022';BASE=O/'baseline';CODES=json.loads((O/'codes.json').read_text())
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
 for key in ['schema_version','id','code','name_zh','chapter','route','node','characters','terrain','enemy_group_ids','reinforcement_turn','burner_departure_turn','escort_move','boss_id','goal','cause','before','during','after','absent_branch','optional','contract','ai_and_timing','equipment_revision','clear_training_exp']:
  check(before.get(key)==after.get(key),f'{code} unchanged contract {key}')
 check(len(before['objects'])==len(after['objects']),f'{code} object count exact')
 check([o['id']for o in before['objects']]==[o['id']for o in after['objects']],f'{code} object identity/order exact including rescue index')
 coordinate_or_art={'position','approach','approaches','entrance_cells','open_art_cells','opens','sprite','sprite_path','sprite_offset','building','door_visual','show_indicator'}
 object_visual_changes=[]
 for a,b in zip(before['objects'],after['objects']):
  for key in sorted(set(a)|set(b)):
   if key in coordinate_or_art:
    if a.get(key)!=b.get(key):object_visual_changes.append({'id':a['id'],'field':key,'before':a.get(key),'after':b.get(key)})
   else:check(a.get(key)==b.get(key),f'{code} object {a["id"]} unchanged {key}')
 records.append({'code':code,'baseline_sha256':sha(before_path),'current_sha256':sha(current_path),'unit_count':unit_count,'unit_changes':changed,'object_coordinate_art_changes':object_visual_changes,'original_story_timing_stats_AI_equipment_retained':True})
original=read(BASE/'hashes.json');unchanged=[]
for code,expected in sorted(original.items()):
 if code in CODES:continue
 path=R/f'data/stages/{code}.json';actual=sha(path);check(actual==expected,f'{code} outside scope exact baseline SHA256');unchanged.append({'code':code,'baseline_sha256':expected,'current_sha256':actual,'unchanged':actual==expected})
check(len(unchanged)==34,'exactly 34 out-of-scope maps proven unchanged')
for record in records:check(record['baseline_sha256']==original[record['code']],record['code']+' frozen source file matches baseline manifest')
report={'passed':not errors,'checks':len(checks),'check_labels':checks,'errors':errors,'maps':records,'outside_scope':unchanged,'outside_scope_count':len(unchanged),'M11_unchanged':next(x['unchanged']for x in unchanged if x['code']=='M11'),'approved_M41_unchanged':next(x['unchanged']for x in unchanged if x['code']=='M41'),'scope':'Every key in every enemy/NPC/reinforcement except position, every narrative/timing/terrain-rule contract, and interaction semantics excluding explicit coordinate/art fields. Unaffected 34 stage files are byte-for-byte unchanged against pre-task SHA256 manifest.'}
(O/'invariants-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':report['checks'],'outside_scope':len(unchanged),'errors':errors},ensure_ascii=False));raise SystemExit(0 if not errors else 1)
