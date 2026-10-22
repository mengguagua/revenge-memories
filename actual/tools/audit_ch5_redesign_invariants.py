#!/usr/bin/env python3
"""Independent frozen-baseline audit; never writes production maps or source saves."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-redesign-20261022';BASE=O/'baseline';CODES=[c for c in json.loads((O/'codes.json').read_text()) if c!='M41']
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
original=read(BASE/'hashes.json');unchanged=[]
for code,expected in sorted(original.items()):
 if code in CODES:continue
 path=R/f'data/stages/{code}.json';actual=sha(path);check(actual==expected,f'{code} outside scope exact baseline SHA256');unchanged.append({'code':code,'baseline_sha256':expected,'current_sha256':actual,'unchanged':actual==expected})
check(len(unchanged)==33,'exactly 33 out-of-scope maps proven unchanged')
for record in records:check(record['baseline_sha256']==original[record['code']],record['code']+' frozen source file matches baseline manifest')
# One reviewed rendering-only exception: stale target selection after settlement.
# Verify the original snapshot, exact before/after source substitution and final hash;
# every other core file still has to match the frozen baseline byte for byte.
exception=read(O/'ui-preview/core-exception.json');core_records=[]
before_preview="\tif target_ids.is_empty():return\n\tvar attacker=game.find_unit(game.selected_id).duplicate(true)\n\tvar defender=game.find_unit(str(target_ids[target_index]))\n"
after_preview="\tbattle_preview_audit={}\n\tif target_index<0 or target_index>=target_ids.size():return\n\tvar attacker=game.find_unit(game.selected_id)\n\tvar defender=game.find_unit(str(target_ids[target_index]))\n\t# Combat completion can clear either selection before target mode redraws.\n\tif attacker.is_empty() or defender.is_empty():return\n\tattacker=attacker.duplicate(true)\n"
for path,expected in read(BASE/'core-hashes.json').items():
 actual=sha(R/'core'/path)
 if path=='main.gd':
  snapshot=O/'ui-preview/before-main.gd';source=snapshot.read_text();current=(R/'core'/path).read_text()
  check(sha(snapshot)==expected==exception['before_sha256'],'main.gd approved UI guard starts from frozen baseline')
  check(source.count(before_preview)==1 and current==source.replace(before_preview,after_preview,1),'main.gd only exact stale-target drawing guard changed')
  check(actual==exception['after_sha256']=='50a36fa52a31841567ddb48ed92aba2448b4f3b0953abe43204cc2f8578415a3','main.gd exact reviewed final UI-only hash')
  core_records.append({'path':path,'baseline_sha256':expected,'current_sha256':actual,'unchanged':False,'approved_exact_exception':'ui-preview/core-exception.json','scope':'Only target drawing guard; no animation, combat, game-state or map logic changed.'})
 else:
  check(actual==expected,'core unchanged '+path);core_records.append({'path':path,'baseline_sha256':expected,'current_sha256':actual,'unchanged':actual==expected})
report={'passed':not errors,'checks':len(checks),'check_labels':checks,'errors':errors,'maps':records,'outside_scope':unchanged,'outside_scope_count':len(unchanged),'core_files':core_records,'core_exact_exception':exception,'M11_unchanged':next(x['unchanged']for x in unchanged if x['code']=='M11'),'approved_M41_unchanged':next(x['unchanged']for x in unchanged if x['code']=='M41'),'scope':'Every key in every enemy/NPC/reinforcement except position, every narrative/timing/terrain-rule contract, and interaction semantics excluding explicit coordinate/art fields. Unaffected 33 stage files are byte-for-byte unchanged against pre-task SHA256 manifest. All core files unchanged except the exact reviewed main.gd stale-target render guard, checked by reconstructed source and SHA256.'}
(O/'invariants-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':report['checks'],'outside_scope':len(unchanged),'errors':errors},ensure_ascii=False));raise SystemExit(0 if not errors else 1)
