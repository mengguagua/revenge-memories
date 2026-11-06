extends "res://tests/full_audit_ch1.gd"
const Tactics=preload("res://tests/assessment_tactics.gd")
const Trace=preload("res://tests/assessment_trace.gd")
func _initialize():call_deferred("run")
func snapshot(name:String)->void:Trace.snapshot(self,name)
func write_progress()->void:Trace.write(self)
func run()->void:
 late_label="chain"
 late_folder=Trace.output_root()+"ch1/"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--out="):late_folder=arg.trim_prefix("--out=").trim_suffix("/")+"/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="fresh game via empty journal"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--source="):source_checkpoint=arg.trim_prefix("--source=")
 ui=load("res://scenes/main.tscn").instantiate()
 ui.game.slot_directory=late_folder
 ui.game.save_path=late_folder+"working-journey.json"
 root.add_child(ui);await process_frame;ui.instant_mode=true
 if source_checkpoint!="fresh game via empty journal":
  DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(ui.game.save_path))
  if not ui.game.load_game():record_failure("Continuous first-chapter resume failed")
  if not abort:ui._resume_journey();await settle()
  if not abort and ui.view=="defeat":
   key(KEY_Z);choose("retry");await settle()
   operations.append({"kind":"ordinary retry after recorded defeat","source":source_checkpoint})
   if ui.game.stage_id!=101 and ui.game.treatment_remaining()>0 and ui.game.party.any(func(id):return ui.game.is_dying(ui.game.roster[id])):
    key(KEY_S);choose("new:prepare");await settle()
 elif FileAccess.file_exists(late_folder+"journey-slot-1.json"):
  record_failure("Refusing to overwrite an existing new-game lineage")
 else:
  key(KEY_Z);key(KEY_Z);await settle()
  if ui.game.hub_record!="P00":record_failure("Fresh journal did not open prologue")
 if not abort and ui.game.hub_record=="P00":
  await snapshot("new-game");await hub_action("prologue");await hub_action("grave");await hub_action("otto");await leave_hub()
 for code in ["M11","M12","M13","S11","S12","M14","M15"]:
  if abort:break
  path_cache.clear();risk_cache.clear()
  var stage={"M11":101,"M12":102,"M13":103,"M14":104,"M15":105,"S11":111,"S12":112}[code]
  if ui.game.stage_cleared(stage):continue
  var already_entered=ui.game.mode=="battle" and ui.game.stage_id==stage
  if not already_entered:await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs
  if not already_entered:key(KEY_Z);choose("new:battle");await settle()
  await snapshot(code+"-entry")
  await battle(false)
  if not abort:await post_battle(stage)
  late_records.append({"code":code,"outcome":ui.game.battle_outcome,"inputs":inputs-before,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"failures":failures.duplicate()})
  write_progress();print("ASSESSMENT_CH1 ",code," ",JSON.stringify(failures))
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)

func plan(u:Dictionary)->Dictionary:
 var support=combat_plan(u)
 if support.kind=="heal":return Tactics.safe_plan(self,u,support)
 var choice=super.plan(u)
 if ui.game.stage_id==111:choice=Tactics.escort_priority(self,u,choice)
 return Tactics.safe_plan(self,u,choice)

func tower_plan(u:Dictionary)->Dictionary:
 if str(u.id)=="lance":return super.tower_plan(u)
 return Tactics.intercept(self,u,"M15_boss")

func equip_from_convoy(id:String,item:int)->void:
 await Tactics.equip(self,id,item)
func prepare_current()->void:
 var treatment_due=ui.game.treatment_remaining()>0 and ui.game.party.any(func(id):return ui.game.is_dying(ui.game.roster[id]))
 var promotion_due=ui.game.party.any(func(id):return ui.game.can_deploy(ui.game.roster[id]) and not ui.Progression.promotion_options(ui.game.roster[id]).is_empty())
 if ui.game.chapter==1 and ui.game.flags.get("cooperation_done",false) and (treatment_due or promotion_due):
  var destination=ui.game.world_node
  await go(int(ui.game.stages[103].node));enter_hub();await settle();await hub_action("church")
  await Tactics.treat_priority(self);await Tactics.promotions(self,"shrine")
  for step in range(3):
   if abort or ui.view!="hub":break
   await leave_hub()
  await go(destination)
 await super.prepare_current()
 if not abort:await Tactics.improve_equipment(self)

func post_battle(stage:int)->void:
 if abort:return
 if stage==104:
  await snapshot("after-"+str(stage));return
 enter_hub();await settle()
 match stage:
  101:
   await hub_action("invite")
  102:
   await hub_action("grain");await hub_action("fula")
   if ui.menu_actions.has("hub:recruit_fula"):choose("hub:recruit_fula");await settle()
  103:
   await hub_action("orders");await hub_action("lena")
   if ui.menu_actions.has("hub:recruit_lena"):choose("hub:recruit_lena");await settle()
   await hub_action("church");await hub_action("cooperate");await Tactics.treat_priority(self);await Tactics.promotions(self,"shrine")
  105:
   await hub_action("treat");await hub_action("ceremony")
   if ui.menu_actions.has("hub:ceremony_confirm"):choose("hub:ceremony_confirm");await settle()
   if not ui.game.flags.get("chapter1_complete",false):record_failure("Chapter ceremony did not complete")
   if not abort:await snapshot("chapter-end")
   if not abort:
    key(KEY_Z);choose("new:chapter2");await settle()
    if ui.game.chapter!=2 or ui.view!="hub":record_failure("Chapter1 to Chapter2 transition did not enter eastern hub")
    else:await snapshot("chapter2-start")
   return
  111:
   await hub_action("beck")
   if ui.menu_actions.has("hub:recruit_beck"):choose("hub:recruit_beck");await settle()
  112:
   await hub_action("staff");await hub_action("hervi")
   if ui.menu_actions.has("hub:recruit_hervi"):choose("hub:recruit_hervi");await settle()
 if not abort:await snapshot("after-"+str(stage))
 for i in range(3):
  if abort or ui.view!="hub":break
  await leave_hub()


func risk(u:Dictionary,cell:Vector2i,skip:String="")->float:
 return super.risk(u,cell,skip)*(1.6 if str(u.id) in ["hunapu","eileen"] else 1.4 if int(u.class_id) in [17,18] else 1.2)
