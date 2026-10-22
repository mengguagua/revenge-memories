extends "res://tests/ch4_redesign_play.gd"
## Exact T91 continuation. No retry, new deployment, reroll or edited live state.
const RESUME_SOURCE="res://reports/chapter4-redesign-20261022/play/continuous-final/working-journey.json"
const PRIOR_REPORT="res://reports/chapter4-redesign-20261022/play/continuous-final/continuous-final-play.json"
var trace_turn=-1
func act(id:String)->void:
 if trace_turn!=ui.game.turn:
  trace_turn=ui.game.turn
  var formation=[]
  for u in ui.game.units:
   if int(u.hp)>0:formation.append({"id":u.id,"position":u.position.duplicate(),"hp":u.hp})
  operations.append({"kind":"continued formation","stage":ui.game.battle_data.code,"turn":ui.game.turn,"units":formation});print("CH4_CONTINUED_FORMATION ",ui.game.battle_data.code," ",ui.game.turn," ",JSON.stringify(formation))
 await super.act(id)
func run()->void:
 late_label="continuous-resumed";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder));source_checkpoint=RESUME_SOURCE
 var source_hash=FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text();var prior_hash=FileAccess.get_file_as_string(PRIOR_REPORT).sha256_text();var prior=State.read_json(PRIOR_REPORT);var original=State.read_json(RESUME_SOURCE);var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(RESUME_SOURCE),ProjectSettings.globalize_path(working));ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Exact T91 checkpoint did not load")
 if not abort and(ui.game.stage_id!=404 or ui.game.turn!=91 or ui.game.battle_outcome!=""):record_failure("Expected genuine live M44 T91 stalemate")
 if not abort:
  var original_units=JSON.parse_string(JSON.stringify(original.units));var loaded_units=JSON.parse_string(JSON.stringify(ui.game.units))
  if original_units!=loaded_units:record_failure("Loaded exact continuation changed units before input")
  ui._resume_journey();await settle();await snapshot("M44-exact-T91-entry")
 for code in ["M44","F44"]:
  if abort:break
  path_cache.clear();risk_cache.clear();var stage=404 if code=="M44"else 408
  if code=="F44":
   if ui.game.route!=ui.game.stages[stage].route:await switch_team()
   if not abort:await go(int(ui.game.stages[stage].node));await prepare_current()
   if not abort:key(KEY_Z);choose("new:battle");await settle();await snapshot("F44-entry")
  if abort:break
  var before=inputs;var starting_turn=ui.game.turn;var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text();var count=battles.size();await battle(false)
  var b={"code":code,"source":RESUME_SOURCE,"source_sha256":source_hash,"entry_map_sha256":hash,"starting_turn":starting_turn,"scope":"Exact continuation from live M44 T91 followed by normal F44 entry; no retry or reset","outcome":"incomplete"}
  if battles.size()>count:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.duplicate();b.final_turn=ui.game.turn;b.return_view=ui.view;b.map_sha256=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text();late_records.append(b);write_progress();print("CH4_CONTINUED_RESULT ",code," ",b.outcome," T",b.final_turn," ",JSON.stringify(b.failures))
 if not abort:
  await go(9);enter_hub();await settle();await hub_action("third_council");await hub_action("third_messenger");choose("hub:fourth_finish");await settle();await snapshot("chapter-end")
  if not ui.game.flags.get("chapter4_closed",false):record_failure("Fourth chapter did not close")
  if not abort:
   key(KEY_Z);choose("new:chapter5");await settle()
   if ui.game.chapter!=5:record_failure("Fifth chapter did not open")
   else:await snapshot("chapter5-start")
 if FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text()!=source_hash:record_failure("Exact T91 source modified")
 if FileAccess.get_file_as_string(PRIOR_REPORT).sha256_text()!=prior_hash:record_failure("Predecessor report modified")
 write_progress();var chain={"passed":not abort,"predecessor_report":PRIOR_REPORT,"predecessor_report_sha256":prior_hash,"inherited_victories":prior.battles.filter(func(b):return b.outcome=="victory"),"retained_pilot_stall":prior.battles.filter(func(b):return b.code=="M44"),"resumed_battles":late_records,"source":RESUME_SOURCE,"source_sha256":source_hash,"source_unchanged":FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text()==source_hash,"chapter":ui.game.chapter,"chapter4_complete":ui.game.flags.get("chapter4_complete",false),"chapter4_closed":ui.game.flags.get("chapter4_closed",false),"D42_done":ui.game.flags.get("D42_done",false),"checkpoints":checkpoints,"operations":operations,"failures":failures,"retry_count":0,"no_state_rng_or_outcome_edits":true,"exact_units_before_first_input":true}
 var f=FileAccess.open(late_folder+"continuous-chain.json",FileAccess.WRITE);f.store_string(JSON.stringify(chain,"  "));f.close();print("CH4_CONTINUED_FINAL ",JSON.stringify({"passed":not abort,"chapter":ui.game.chapter,"D42":ui.game.flags.get("D42_done",false),"failures":failures}));ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
