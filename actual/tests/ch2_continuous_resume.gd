extends "res://tests/ch2_continuous_play.gd"
## Continue the exact real T91 input-pilot stalemate. No checkpoint reset,
## combat-state edits or reroll: healthy fighters advance and support follows.
const RESUME_SOURCE="res://reports/chapter2-redesign-20261022/play/continuous-final/working-journey.json"
const PRIOR_REPORT="res://reports/chapter2-redesign-20261022/play/continuous-final/continuous-final-play.json"
var resume_trace_turn=-1
var resume_source_hash=""

func act(id:String)->void:
 if resume_trace_turn!=ui.game.turn:
  resume_trace_turn=ui.game.turn
  var summary=[]
  for u in ui.game.units:
   if int(u.hp)>0:summary.append({"id":u.id,"position":u.position.duplicate(),"hp":u.hp})
  print("CONTINUATION_FORMATION ",ui.game.battle_data.code," ",ui.game.turn," ",JSON.stringify(summary))
  operations.append({"kind":"continuation formation","stage":ui.game.battle_data.code,"turn":ui.game.turn,"units":summary})
 await super.act(id)

func plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id!=205:return super.plan(unit)
 var origin=State.pos(unit);var graph=ui.game.reachable(unit)
 var best=combat_plan(unit)
 if best.kind=="heal":return best
 if best.kind=="attack":
  var target=ui.game.find_unit(str(best.target));var candidate=unit.duplicate(true);candidate.position=[best.cell.x,best.cell.y]
  if int(best.spell)>=0:candidate.weapon_index=int(best.spell)
  var reply=Rules.default_counter(target,distance(best.cell,State.pos(target)))
  var attack=Rules.attack_stats(candidate,target,ui.game.terrain_avoid(State.pos(target)))
  var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(best.cell))
  if int(unit.hp)>Items.cost(int(best.spell))+int(response.damage) or int(attack.damage)>=int(target.hp):return best
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  for object in ui.game.interactions_for(candidate):
   if object.get("optional",false):continue
   if risk(candidate,cell)>=int(unit.hp)-3:continue
   return {"kind":"interact","cell":cell,"score":250.0,"target":str(object.id),"spell":-1}
 var front=ui.game.find_unit("lord")
 if front.is_empty() or int(front.hp)<=0:front=ui.game.find_unit("eileen")
 var healer=int(unit.class_id) in [17,18]
 var goals:Array=[]
 if healer and not front.is_empty():
  for d in ui.game.DIRECTIONS:goals.append(State.pos(front)+d)
 else:
  var boss=ui.game.find_unit(str(ui.game.battle_data.boss_id))
  if not boss.is_empty() and int(boss.hp)>0:
   for d in ui.game.DIRECTIONS:goals.append(State.pos(boss)+d)
  else:
   for object in ui.game.battle_data.objects:
    if object.get("optional",false) or ui.game.flags.quest.objects.get(str(object.id),false):continue
    var p=Vector2i(object.position[0],object.position[1])
    if not object.get("adjacent",true):goals.append(p)
    else:
     for d in ui.game.DIRECTIONS:goals.append(p+d)
 if goals.is_empty():return super.plan(unit)
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell) or not field.has(cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell)
  var score=10.0*(before-int(field[cell]))-danger*(3.0 if healer else 2.0)
  if danger>=int(unit.hp)-3:score-=300.0
  # Support catches up with the advancing guard. A wounded rear unit never
  # supplies a global tether that can freeze the healthy assault group.
  if not healer and str(unit.id)!="lord" and not front.is_empty():score-=maxi(0,distance(cell,State.pos(front))-5)*1.5
  if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
 return best

func run()->void:
 if OS.get_cmdline_user_args().has("--finish-entry"):
  await finish_entry();return
 late_label="continuous-resumed"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint=RESUME_SOURCE;resume_source_hash=FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text()
 var prior=State.read_json(PRIOR_REPORT)
 var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(RESUME_SOURCE),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Exact continuous checkpoint failed to load")
 if not abort and (ui.game.stage_id!=205 or ui.game.turn!=91 or ui.game.battle_outcome!=""):record_failure("Resume is not the recorded F25 T91 live battle")
 var west={}
 for id in ui.game.parties.alm:west[id]=ui.game.roster[id].duplicate(true)
 if not abort:ui._resume_journey();await settle();await snapshot("F25-resume-T91")
 for code in ["F25","F26"]:
  if abort:break
  path_cache.clear();risk_cache.clear()
  var stage=205 if code=="F25" else 206
  if stage==206:
   await go(int(ui.game.stages[stage].node));await prepare_current()
   if abort:break
   key(KEY_Z);choose("new:battle");await settle();await snapshot("F26-entry")
  var before=inputs;var starting_turn=ui.game.turn;var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  var b={"code":code,"source":RESUME_SOURCE,"source_sha256":resume_source_hash,"entry_map_sha256":hash,"starting_turn":starting_turn,"scope":"Exact continuation of the six completed chapter-two battles and the live F25 T91 checkpoint; ordinary input only.","outcome":"incomplete"}
  var count=battles.size();await battle(false)
  if battles.size()>count:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.map_sha256=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text();b.key_inputs=inputs-before;b.failures=failures.duplicate();b.return_view=ui.view;b.chapter_complete=ui.game.flags.get("chapter2_complete",false)
  late_records.append(b);write_progress();print("CONTINUOUS_RESUMED_RESULT ",code," ",b.outcome," ",JSON.stringify(b.failures))
 if not abort:
  if not ui.game.flags.get("chapter2_complete",false):record_failure("Chapter two finale did not complete")
  for id in west:
   if JSON.parse_string(JSON.stringify(ui.game.roster[id]))!=JSON.parse_string(JSON.stringify(west[id])):record_failure("Western roster changed during eastern continuation: "+id)
  if not abort:
   key(KEY_Z);choose("new:chapter3");await settle()
   if ui.game.chapter!=3:record_failure("Third chapter did not open")
   else:await snapshot("chapter3-start")
 if FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text()!=resume_source_hash:record_failure("Exact source checkpoint was modified")
 write_progress()
 var chain={"passed":not abort,"predecessor_report":PRIOR_REPORT,"predecessor_report_sha256":FileAccess.get_file_as_string(PRIOR_REPORT).sha256_text(),"inherited_victories":prior.battles.filter(func(b):return b.outcome=="victory"),"retained_pilot_stall":prior.battles.filter(func(b):return b.code=="F25"),"resumed_battles":late_records,"source_sha256":resume_source_hash,"source_unchanged":FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text()==resume_source_hash,"chapter":ui.game.chapter,"chapter2_complete":ui.game.flags.get("chapter2_complete",false),"checkpoints":checkpoints,"operations":operations,"failures":failures,"no_state_rng_or_outcome_edits":true}
 var f=FileAccess.open(late_folder+"continuous-chain.json",FileAccess.WRITE);f.store_string(JSON.stringify(chain,"  "));f.close()
 ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)

func finish_entry()->void:
 late_label="continuous-resumed-entry";late_folder=LATE_OUT+late_label+"/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 var completed=LATE_OUT+"continuous-resumed/working-journey.json"
 var completed_hash=FileAccess.get_file_as_string(completed).sha256_text()
 var original=State.read_json(RESUME_SOURCE);var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(completed),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Completed continuous journey did not load")
 var west_checks=[]
 for id in original.parties.alm:
  # JSON loading yields floats; ordinary preparation sets HP to integer maxHP.
  # Compare normalized persisted values rather than runtime Variant tags.
  var unchanged=JSON.parse_string(JSON.stringify(ui.game.roster[id]))==JSON.parse_string(JSON.stringify(original.roster[id]))
  west_checks.append({"unit":id,"persisted_values_unchanged":unchanged})
  if not unchanged:record_failure("Actual persisted western roster changed: "+id)
 if not abort and (not ui.game.flags.get("chapter2_complete",false) or ui.game.mode!="chapter_end"):record_failure("Expected ordinary completed second chapter")
 if not abort:
  ui._resume_journey();await settle();await snapshot("chapter2-end")
  key(KEY_Z);choose("new:chapter3");await settle()
  if ui.game.chapter!=3:record_failure("Third chapter entry did not complete")
  else:await snapshot("chapter3-start")
 if FileAccess.get_file_as_string(completed).sha256_text()!=completed_hash:record_failure("Completed source modified during entry check")
 var r={"passed":not abort,"source":completed,"source_sha256":completed_hash,"original_T91_source":RESUME_SOURCE,"original_T91_source_sha256":FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text(),"western_persisted_value_checks":west_checks,"prior_assertion_resolution":"Direct Dictionary comparison treated loaded numeric Variants and ordinary integer HP restoration as different; all persisted western fields match the original T91 source after canonical JSON normalization.","chapter":ui.game.chapter,"chapter2_complete":ui.game.flags.get("chapter2_complete",false),"key_inputs":inputs,"checkpoints":checkpoints,"failures":failures,"no_state_rng_or_outcome_edits":true}
 var f=FileAccess.open(late_folder+"chapter3-entry-verification.json",FileAccess.WRITE);f.store_string(JSON.stringify(r,"  "));f.close()
 print("CHAPTER3_ENTRY ",JSON.stringify({"passed":not abort,"chapter":ui.game.chapter,"inputs":inputs,"failures":failures}))
 ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
