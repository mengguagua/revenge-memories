extends "res://tests/full_audit_ch2.gd"
const Tactics=preload("res://tests/assessment_tactics.gd")
const Trace=preload("res://tests/assessment_trace.gd")
func _initialize():call_deferred("run")
func run()->void:
 late_label="chain"
 await run_continuous()
func snapshot(name:String)->void:Trace.snapshot(self,name)
func write_progress()->void:Trace.write(self)
func run_continuous()->void:
 late_folder=Trace.output_root()+"ch2/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint=Trace.output_root()+"ch1/chain-chapter2-start.json"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--source="):source_checkpoint=arg.trim_prefix("--source=")
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=late_folder;ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine first-chapter continuation failed")
 if not abort:ui._resume_journey();await settle()
 if not abort and ui.view=="defeat":
  key(KEY_Z);choose("retry");await settle()
  operations.append({"kind":"ordinary retry after recorded defeat","source":source_checkpoint})
 var west={}
 for id in ui.game.parties.alm:west[id]=ui.game.roster[id].duplicate(true)
 if not abort and not ui.game.flags.get("east_departure_ready",false):
  await hub_action("east_chart_start");await hub_action("east_mireille");await hub_action("east_lisa");await hub_action("east_departure");await leave_hub()
 for code in ["F21","F22","F23","S21","S22","F24","F25","F26"]:
  if abort:break
  var stage={"F21":201,"F22":202,"F23":203,"F24":204,"F25":205,"F26":206,"S21":211,"S22":212}[code]
  if ui.game.stage_cleared(stage):continue
  var already_entered=ui.game.mode=="battle" and ui.game.stage_id==stage
  path_cache.clear();risk_cache.clear()
  if not already_entered:await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs;var prior_failures=failures.size();var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  if not already_entered:key(KEY_Z);choose("new:battle");await settle()
  await snapshot(code+"-entry")
  var n=battles.size();await battle(false)
  var b={"code":code,"source":source_checkpoint,"source_sha256":source_hash,"scope":"Continuous from genuine first-chapter completion; normal recruitment, equipment, growth and casualties carried forward","entry_map_sha256":hash,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"outcome":"incomplete"}
  if battles.size()>n:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.slice(prior_failures);b.return_view=ui.view;b.post_flow_turn=ui.game.turn;b.chapter_complete=ui.game.flags.get("chapter2_complete",false)
  late_records.append(b);write_progress();print("CH2_CONTINUOUS ",code," ",b.outcome," ",JSON.stringify(b.failures))
 if not abort:
  if not ui.game.flags.get("chapter2_complete",false):record_failure("Second chapter did not complete")
  for id in west:
   if JSON.parse_string(JSON.stringify(ui.game.roster[id]))!=JSON.parse_string(JSON.stringify(west[id])):record_failure("West roster modified during eastern chapter: "+id)
  if not abort:
   if ui.game.chapter==2:key(KEY_Z);choose("new:chapter3");await settle()
   if ui.game.chapter!=3:record_failure("Third chapter did not open")
   else:await snapshot("chapter3-start")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Genuine chapter start source changed")
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)


func plan(u:Dictionary)->Dictionary:
 return Tactics.safe_plan(self,u,super.plan(u))

func deck_recovery_plan(u:Dictionary)->Dictionary:
 if int(u.hp)>int(u.max_hp)*.5:return {}
 return super.deck_recovery_plan(u)

func equip_from_convoy(id:String,item:int)->void:
 await Tactics.equip(self,id,item)
func prepare_current()->void:
 await super.prepare_current()
 if not abort:await Tactics.improve_equipment(self)

func post_battle(stage: int) -> void:
 if abort:return
 enter_hub()
 match stage:
  201:
   await hub_action("sea_route");await hub_action("invite_s21")
  211:await hub_action("s21_report")
  202:
   await hub_action("prisoners_treat");await hub_action("captives_route");await invite("lord")
  203:
   await hub_action("reef_route");await invite("roan");await hub_action("holy_sword");await hub_action("invite_s22")
  212:await hub_action("invite_s22")
  204:
   await hub_action("islanders_settle");await Tactics.treat_priority(self);await invite("shia")
   await hub_action("resistance_spring");choose("hub:east_spring_eileen");await settle()
   await hub_action("east_training");choose("hub:east_magic_info");await settle();await Tactics.promotions(self,"east_training");await hub_action("r05")
  205:
   await hub_action("chart_recover");await hub_action("holy_bow");await hub_action("harbor_patients");await hub_action("r05")
   await hub_action("ancient_departure");choose("hub:east_sail_confirm");await settle()
  206:
   await snapshot("arrival-hub");await hub_action("arrival_captain");await hub_action("east_finale");await snapshot("chapter-end")
 await snapshot("after-"+str(stage))
 if stage!=206 and not abort:await leave_hub()


func risk(u:Dictionary,cell:Vector2i,skip:String="")->float:
 return super.risk(u,cell,skip)*(1.6 if str(u.id) in ["hunapu","eileen"] else 1.4 if int(u.class_id) in [17,18] else 1.2)
