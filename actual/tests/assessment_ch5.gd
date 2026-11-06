extends "res://tests/full_audit_ch5.gd"
const Tactics=preload("res://tests/assessment_tactics.gd")
const Trace=preload("res://tests/assessment_trace.gd")
func _initialize():call_deferred("run")
func run()->void:
 late_label="chain"
 await run_continuous()
func snapshot(name:String)->void:Trace.snapshot(self,name)
func write_progress()->void:Trace.write(self)
func run_continuous()->void:
 late_folder=Trace.output_root()+"ch5/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint=Trace.output_root()+"ch4/chain-chapter5-start.json"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--source="):source_checkpoint=arg.trim_prefix("--source=")
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=late_folder;ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine fourth-chapter completion failed")
 if not abort:ui._resume_journey();await settle();await snapshot("chapter5-start")
 if not abort and ui.view=="defeat":
  key(KEY_Z);choose("retry");await settle()
  operations.append({"kind":"ordinary retry after recorded defeat","source":source_checkpoint})
 for code in ["M51","M52","F51","F52","S51"]:
  if abort:break
  var stage={"M51":501,"M52":502,"F51":503,"F52":504,"S51":511}[code]
  if ui.game.stage_cleared(stage):continue
  var already_entered=ui.game.mode=="battle" and ui.game.stage_id==stage
  if not already_entered and ui.game.route!=ui.game.stages[stage].route:await switch_team()
  if not abort and not already_entered:await go(int(ui.game.stages[stage].node));await prepare_current()
  if not abort:await continuous_battle(code)
 if not abort and not ui.game.flags.get("chapter5_merged",false):
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
  if ui.game.stage_cleared(stage):continue
  var already_entered=ui.game.mode=="battle" and ui.game.stage_id==stage
  if not already_entered:await go(int(ui.game.stages[stage].node));await prepare_current()
  if not abort:await continuous_battle(code)
 if not abort:
  if not ui.game.flags.get("campaign_complete",false)or not ui.game.flags.get("ending_done",false):record_failure("Final campaign or ending incomplete")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Original fifth-chapter source changed")
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)

func continuous_battle(code:String)->void:
 path_cache.clear();risk_cache.clear();var before=inputs
 if not (ui.game.mode=="battle" and str(ui.game.battle_data.code)==code):key(KEY_Z);choose("new:battle");await settle()
 await snapshot(code+"-entry")
 var count=battles.size();await battle(false)
 var record={"code":code,"outcome":"incomplete","source":source_checkpoint}
 if battles.size()>count:record.merge(battles[-1],true)
 if not abort:
  if ui.game.stage_id!=534:await post_battle(ui.game.stage_id)
  else:await finish_ending();record.ending_done=ui.game.flags.get("ending_done",false)
 record.key_inputs=inputs-before;record.failures=failures.duplicate();record.return_view=ui.view
 late_records.append(record);write_progress();print("ASSESSMENT_CH5 ",code," ",record.outcome," ",JSON.stringify(failures))

func plan(u:Dictionary)->Dictionary:
 if ui.game.stage_id==534:
  var attack=combat_plan(u)
  if attack.kind in ["attack","heal"]:return Tactics.safe_plan(self,u,attack)
  if int(u.class_id) not in [17,18]:return Tactics.safe_plan(self,u,Tactics.intercept(self,u,"J54_boss"))
 return Tactics.safe_plan(self,u,super.plan(u))

func post_battle(stage:int)->void:
 if abort or stage==534:return
 enter_hub();await settle()
 match stage:
  501:
   await hub_action("fifth_ward_report");await hub_action("fifth_shield_keeper")
   await Tactics.treat_priority(self)
  502:await hub_action("fifth_west_report")
  503:await hub_action("fifth_repair_report")
  504:await hub_action("fifth_east_report");await hub_action("fifth_archive_invite")
  511:await hub_action("fifth_archive_report")
  533:await hub_action("fifth_merge")
 await snapshot("after-"+str(stage))
 if not abort:await leave_hub()

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
