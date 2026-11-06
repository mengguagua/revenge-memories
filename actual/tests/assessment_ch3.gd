extends "res://tests/full_audit_ch3.gd"
const Tactics=preload("res://tests/assessment_tactics.gd")
const Trace=preload("res://tests/assessment_trace.gd")
func _initialize():call_deferred("run")
func run()->void:
 late_label="chain"
 await run_continuous()
func snapshot(name:String)->void:Trace.snapshot(self,name)
func write_progress()->void:Trace.write(self)
func run_continuous()->void:
 late_folder=Trace.output_root()+"ch3/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint=Trace.output_root()+"ch2/chain-chapter3-start.json"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--source="):source_checkpoint=arg.trim_prefix("--source=")
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=late_folder;ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine second-chapter completion failed")
 if not abort:ui._resume_journey();await settle();await snapshot("chapter3-start")
 if not abort and ui.view=="defeat":
  key(KEY_Z);choose("retry");await settle()
  operations.append({"kind":"ordinary retry after recorded defeat","source":source_checkpoint})
 if not abort and not ui.game.flags.get("D31_done",false):await hub_action("third_prologue");await snapshot("D31-finished")
 if not abort and ui.view=="hub":await leave_hub()
 for code in ["M31","F31","F32","S32","F33","M32","S31","M33"]:
  if abort:break
  var stage={"M31":301,"M32":302,"M33":303,"F31":304,"F32":305,"F33":306,"S31":311,"S32":312}[code]
  if ui.game.stage_cleared(stage):continue
  var already_entered=ui.game.mode=="battle" and ui.game.stage_id==stage
  path_cache.clear();risk_cache.clear()
  if not already_entered and ui.game.route!=ui.game.stages[stage].route:await switch_team()
  if not abort and not already_entered:await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs;var prior_failures=failures.size();var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  if not already_entered:key(KEY_Z);choose("new:battle");await settle()
  await snapshot(code+"-entry")
  var count=battles.size();await battle(false)
  var b={"code":code,"source":source_checkpoint,"source_sha256":source_hash,"scope":"Continuous from genuine chapter-two completion, normal route switching, recruitment and equipment, all growth and casualties carried forward","entry_map_sha256":hash,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"outcome":"incomplete"}
  if battles.size()>count:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.slice(prior_failures);b.final_turn=ui.game.turn;b.return_view=ui.view;b.route=ui.game.route
  late_records.append(b);write_progress();print("CH3_CONTINUOUS ",code," ",b.outcome," ",JSON.stringify(b.failures))
 if not abort:
  await go(9);enter_hub();await settle();await hub_action("third_council");await leave_hub()
  await switch_team();await go(9);enter_hub();await settle();await hub_action("third_council");await snapshot("D33-council")
  await hub_action("third_relations");await hub_action("third_messenger");choose("hub:third_finish");await settle();await snapshot("chapter-end")
  if not ui.game.flags.get("chapter3_complete",false):record_failure("Third chapter did not complete")
  if not abort:
   key(KEY_Z);choose("new:chapter4");await settle()
   if ui.game.chapter!=4:record_failure("Fourth chapter did not open")
   else:await snapshot("chapter4-start")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Original chapter start changed")
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)


func plan(u:Dictionary)->Dictionary:
 return Tactics.safe_plan(self,u,super.plan(u))

func equip_from_convoy(id:String,item:int)->void:
 await Tactics.equip(self,id,item)
func prepare_current()->void:
 await super.prepare_current()
 if not abort:await Tactics.improve_equipment(self)

func risk(u:Dictionary,cell:Vector2i,skip:String="")->float:
 return super.risk(u,cell,skip)*(1.6 if str(u.id) in ["hunapu","eileen"] else 1.4 if int(u.class_id) in [17,18] else 1.2)
