extends "res://tests/full_audit_ch4.gd"
func plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id==411 and not ui.game.flags.quest.objects.get("refuge_court",false):
  if unit.id=="lance":
   var graph=ui.game.reachable(unit)
   for cell in graph.costs:
    if not ui.game.can_stop(unit,cell):continue
    var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
    if ui.game.interactions_for(candidate).any(func(o):return o.id=="refuge_court"):
     return {"kind":"interact","cell":cell,"score":300.0,"target":"refuge_court","spell":-1}
   return directed_plan(unit,[Vector2i(6,17)],[],18.0)
  var regular=super.plan(unit)
  if regular.kind=="attack" and regular.target==ui.game.battle_data.boss_id:
   regular.kind="wait";regular.target="";regular.spell=-1
  return regular
 return super.plan(unit)
func run()->void:
 late_label="s41-reward";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint=LATE_OUT+"current/current-S41-turn-8.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text()
 var working=late_folder+"working-S41.json";DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("S41 near-victory checkpoint failed")
 if not abort:ui._resume_journey();await settle();await battle(false)
 if not abort:await post_battle(411);enter_hub();await settle()
 var checks=[]
 if not abort:
  var count_before=ui.game.convoy.alm.count(55);await hub_action("fourth_ring_keeper")
  if not ui.game.Accessories.claimed(ui.game,55) or ui.game.convoy.alm.count(55)!=count_before+1:record_failure("Eligible ring handover failed")
  checks.append({"kind":"eligible handover","facts":ui.game.flags.story_accessory_results,"ring_count":ui.game.convoy.alm.count(55),"passed":not abort})
  await snapshot("ring-received")
  await hub_action("fourth_ring_keeper")
  if ui.game.convoy.alm.count(55)!=count_before+1:record_failure("Repeated handover duplicated ring")
  checks.append({"kind":"already claimed dialogue","ring_count":ui.game.convoy.alm.count(55),"passed":not abort})
  await snapshot("ring-recheck")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("S41 source checkpoint modified")
 var f=FileAccess.open(late_folder+"reward-followup.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"failures":failures,"source":source_checkpoint,"source_sha256":source_hash,"checks":checks,"battles":battles,"checkpoints":checkpoints,"content":observed_content,"inputs":inputs,"scope":"Only resumes genuine turn-8 state to cover optional refuge confirmation and ring delivery. Not counted as a second full-map playthrough; no stats, RNG, positions or win conditions edited."},"  "));f.close()
 print("S41_REWARD_FOLLOWUP ",JSON.stringify({"passed":not abort,"checks":checks.size(),"failures":failures}));ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
