extends "res://tests/ch5_redesign_play.gd"
## Continue the genuine S51 T91 checkpoint. No retry, stage restart, or edited state.
const RESUME_SOURCE="res://reports/chapter5-redesign-20261022/play/continuous-final/working-journey.json"
const PRIOR_REPORT="res://reports/chapter5-redesign-20261022/play/continuous-final/continuous-final-play.json"
var exact_before={}
var resume_maps={}
var trace_turn=-1
func act(id:String)->void:
 if trace_turn!=ui.game.turn:
  trace_turn=ui.game.turn
  var formation=[]
  for u in ui.game.units:
   if int(u.hp)>0:formation.append({"id":u.id,"position":u.position.duplicate(),"hp":u.hp})
  operations.append({"kind":"continued formation","stage":ui.game.battle_data.code,"turn":ui.game.turn,"units":formation});print("CH5_CONTINUED_FORMATION ",ui.game.battle_data.code," T",ui.game.turn," ",JSON.stringify(formation))
 await super.act(id)
func run()->void:
 late_label="continuous-resumed";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder));source_checkpoint=RESUME_SOURCE
 var source_hash=FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text();var prior_hash=FileAccess.get_file_as_string(PRIOR_REPORT).sha256_text();var prior=State.read_json(PRIOR_REPORT);var original=State.read_json(RESUME_SOURCE);var working=late_folder+"working-journey.json"
 for code in ["M51","M52","F51","F52","S51","J53","J54"]:resume_maps[code]=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
 DirAccess.copy_absolute(ProjectSettings.globalize_path(RESUME_SOURCE),ProjectSettings.globalize_path(late_folder+"source-exact-T91.json"));DirAccess.copy_absolute(ProjectSettings.globalize_path(RESUME_SOURCE),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Exact S51 T91 checkpoint did not load")
 if not abort and(ui.game.stage_id!=511 or ui.game.turn!=91 or ui.game.battle_outcome!="" or ui.game.phase!="player"):record_failure("Expected genuine live S51 T91 player phase")
 if not abort:
  for field in State.SAVE_FIELDS:
   var current=ui.game.get(field)
   if current is Vector2i:current=[current.x,current.y]
   exact_before[field]=JSON.parse_string(JSON.stringify(current))==original[field]
   if not exact_before[field]:record_failure("Exact continuation changed persisted field before input: "+field)
  var f=FileAccess.open(late_folder+"exact-before.json",FileAccess.WRITE);f.store_string(JSON.stringify({"source":RESUME_SOURCE,"source_sha256":source_hash,"fields":exact_before,"passed":exact_before.values().all(func(value):return value)},"  "));f.close()
  ui._resume_journey();await settle();await snapshot("S51-exact-T91-entry")
 if not abort:
  path_cache.clear();risk_cache.clear();var before=inputs;var count=battles.size();await battle(false)
  var b={"code":"S51","source":RESUME_SOURCE,"source_sha256":source_hash,"entry_map_sha256":resume_maps.S51,"starting_turn":91,"scope":"Exact T91 continuation using ordinary movement to original records then southern handoff; no retry or reset","outcome":"incomplete"}
  if battles.size()>count:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(511)
  b.key_inputs=inputs-before;b.failures=failures.duplicate();b.final_turn=ui.game.turn;b.return_view=ui.view;b.map_sha256=FileAccess.get_file_as_string("res://data/stages/S51.json").sha256_text();late_records.append(b);write_progress();print("CH5_CONTINUED_RESULT S51 ",b.outcome," T",b.final_turn," ",JSON.stringify(b.failures))
 if not abort:
  for side in ["alm","celica"]:
   if ui.game.route!=side:await switch_team()
   await go(15);enter_hub();await settle()
   if side=="celica":await treat_normally("shia")
   await hub_action("fifth_prepare")
   for member in ui.game.parties[side]:
    if ui.game.can_deploy(ui.game.roster[member]) and not ui.game.ChapterFive.selection(ui.game,side).has(member) and ui.game.ChapterFive.selection(ui.game,side).size()<10:
     choose("hub:fifth_toggle_"+str(member));await settle()
   choose("hub:fifth_ready");await settle();await snapshot("ready-"+side);await leave_hub();await prepare_current()
  enter_hub();await settle();await hub_action("fifth_relationship");await hub_action("fifth_merge");choose("hub:fifth_confirm_merge");await settle();await snapshot("merged");await leave_hub()
 for code in ["J53","J54"]:
  if abort:break
  var stage=533 if code=="J53"else 534
  await go(int(ui.game.stages[stage].node));await prepare_current()
  if not abort:await continuous_battle(code)
 if not abort and(not ui.game.flags.get("campaign_complete",false)or not ui.game.flags.get("ending_done",false)):record_failure("Final campaign or complete ending missing")
 if FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text()!=source_hash:record_failure("Exact S51 T91 source changed")
 if FileAccess.get_file_as_string(PRIOR_REPORT).sha256_text()!=prior_hash:record_failure("Predecessor report changed")
 for code in resume_maps:
  if FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()!=resume_maps[code]:record_failure("Map changed during continuation: "+code)
 write_progress()
 var inherited=prior.battles.filter(func(b):return b.outcome=="victory")
 var chain={"passed":not abort,"predecessor_report":PRIOR_REPORT,"predecessor_report_sha256":prior_hash,"inherited_victories":inherited,"retained_pilot_stall":prior.battles.filter(func(b):return b.code=="S51"),"resumed_battles":late_records,"all_battles":inherited+late_records,"source":RESUME_SOURCE,"source_sha256":source_hash,"source_unchanged":FileAccess.get_file_as_string(RESUME_SOURCE).sha256_text()==source_hash,"map_hashes":resume_maps,"chapter":ui.game.chapter,"campaign_complete":ui.game.flags.get("campaign_complete",false),"chapter5_complete":ui.game.flags.get("chapter5_complete",false),"ending_done":ui.game.flags.get("ending_done",false),"ending_index":ui.game.flags.get("ending_index",-1),"checkpoints":checkpoints,"operations":operations,"failures":failures,"retry_count":0,"no_state_rng_or_outcome_edits":true,"exact_fields_before_first_input":exact_before,"exact_before_passed":exact_before.values().all(func(value):return value)}
 var f=FileAccess.open(late_folder+"continuous-chain.json",FileAccess.WRITE);f.store_string(JSON.stringify(chain,"  "));f.close()
 f=FileAccess.open("res://reports/chapter5-redesign-20261022/flow-continuation.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"report":late_folder+"continuous-chain.json","original_report":PRIOR_REPORT,"source":RESUME_SOURCE,"source_sha256":source_hash,"source_unchanged":chain.source_unchanged,"exact_before_passed":chain.exact_before_passed,"inherited_victories":inherited.size(),"resumed_victories":late_records.filter(func(b):return b.outcome=="victory").size(),"maps":resume_maps,"campaign_complete":chain.campaign_complete,"ending_done":chain.ending_done,"retry_count":0,"scope":"Same genuine fifth-chapter chain: prior four wins, exact S51 T91 continuation after test driver objective-order stall, normal H55 treatment and joint roster menus, J53/J54 and complete ending. Original stall remains preserved; no gameplay attributes, positions, RNG or outcome modified.","failures":failures},"  "));f.close()
 print("CH5_CONTINUED_FINAL ",JSON.stringify({"passed":not abort,"ending_done":chain.ending_done,"failures":failures}));ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
