extends "res://tests/full_audit_ch4.gd"
const Tactics=preload("res://tests/assessment_tactics.gd")
const Trace=preload("res://tests/assessment_trace.gd")
func _initialize():call_deferred("run")
func run()->void:
 late_label="chain"
 await run_continuous()
func snapshot(name:String)->void:Trace.snapshot(self,name)
func write_progress()->void:Trace.write(self)
func run_continuous()->void:
 late_folder=Trace.output_root()+"ch4/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint=Trace.output_root()+"ch3/chain-chapter4-start.json"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--source="):source_checkpoint=arg.trim_prefix("--source=")
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=late_folder;ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine third-chapter completion failed")
 if not abort:ui._resume_journey();await settle();await snapshot("chapter4-start")
 if not abort and ui.view=="defeat":
  key(KEY_Z);choose("retry");await settle()
  operations.append({"kind":"ordinary retry after recorded defeat","source":source_checkpoint})
 # Spend genuinely retained sources at the meeting hub through ordinary choices.
 if not abort and ui.game.mode=="world":
  enter_hub();await settle();await Tactics.treat_priority(self);await Tactics.promotions(self,"third_training");await leave_hub()
  await switch_team();enter_hub();await settle();await Tactics.treat_priority(self);await Tactics.promotions(self,"third_training");await leave_hub()
  await snapshot("after-ordinary-treatment")
 for code in ["M41","S41","M42","M43","F41","F42","F43","S42","M44","F44"]:
  if abort:break
  var stage={"M41":401,"M42":402,"M43":403,"M44":404,"F41":405,"F42":406,"F43":407,"F44":408,"S41":411,"S42":412}[code]
  if ui.game.stage_cleared(stage):continue
  var already_entered=ui.game.mode=="battle" and ui.game.stage_id==stage
  path_cache.clear();risk_cache.clear()
  if not already_entered and ui.game.route!=ui.game.stages[stage].route:await switch_team()
  if stage==404 and not ui.game.flags.get("west_tower_safe",false):
   await go(12);enter_hub();await settle();await hub_action("fourth_tower_shutdown");await leave_hub()
  if not abort and not already_entered:await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs;var prior_failures=failures.size();var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  if not already_entered:key(KEY_Z);choose("new:battle");await settle()
  await snapshot(code+"-entry")
  var count=battles.size();await battle(false)
  var b={"code":code,"source":source_checkpoint,"source_sha256":source_hash,"scope":"Continuous from genuine chapter-three completion, normal treatment, route switching, recruitment and equipment; all growth and casualties carried forward","entry_map_sha256":hash,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"outcome":"incomplete"}
  if battles.size()>count:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.slice(prior_failures);b.final_turn=ui.game.turn;b.return_view=ui.view;b.route=ui.game.route
  late_records.append(b);write_progress();print("CH4_CONTINUOUS ",code," ",b.outcome," ",JSON.stringify(b.failures))
  if OS.get_cmdline_user_args().has("--opening-only"):
   ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1);return
 if not abort:
  await go(9);enter_hub();await settle();await hub_action("third_council");await hub_action("third_messenger");choose("hub:fourth_finish");await settle();await snapshot("chapter-end")
  if not ui.game.flags.get("chapter4_closed",false):record_failure("Fourth chapter did not complete")
  if not abort:
   key(KEY_Z);choose("new:chapter5");await settle()
   if ui.game.chapter!=5:record_failure("Fifth chapter did not open")
   else:await snapshot("chapter5-start")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Original chapter start changed")
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)


func plan(u:Dictionary)->Dictionary:
 return Tactics.safe_plan(self,u,super.plan(u))

func refresh_threats()->void:
 risk_cache.clear();threats.clear()
 for enemy in ui.game.living("enemy"):
  threats.append({"unit":enemy,"cells":ui.game.reachable(enemy).costs.keys()})

func equip_from_convoy(id:String,item:int)->void:
 await Tactics.equip(self,id,item)
func prepare_current()->void:
 await super.prepare_current()
 if not abort:await Tactics.improve_equipment(self)

func risk(u:Dictionary,cell:Vector2i,skip:String="")->float:
 return super.risk(u,cell,skip)*(1.6 if str(u.id) in ["hunapu","eileen"] else 1.4 if int(u.class_id) in [17,18] else 1.2)
