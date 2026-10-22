extends "res://tests/chapter3_play.gd"
# Third-chapter isolated real-input review; no live attributes or outcomes edited.

const LATE_OUT="res://reports/chapter3-redesign-20261022/play/"
var late_label="round1"
var late_codes:PackedStringArray=[]
var late_folder=""
var late_entry_only=false
var late_records=[]
var path_cache={}
var risk_cache={}
func _initialize():call_deferred("run")
func distance_map(unit:Dictionary,goals:Array)->Dictionary:
 var k=str(ui.game.stage_id)+":"+str(unit.class_id)+":"+str(unit.get("item_id",0))+":"+JSON.stringify(goals)+":"+JSON.stringify(ui.game.flags.quest.objects)
 if not path_cache.has(k):path_cache[k]=super.distance_map(unit,goals)
 return path_cache[k]
func refresh_threats()->void:
 risk_cache.clear();super.refresh_threats()
func risk(unit:Dictionary,cell:Vector2i,skip:String="")->float:
 var k=str(unit.id)+":"+str(unit.hp)+":"+str(unit.get("weapon_index",-1))+":"+str(cell)+":"+skip
 if not risk_cache.has(k):risk_cache[k]=super.risk(unit,cell,skip)
 return float(risk_cache[k])
func snapshot(name:String)->void:
 if abort:return
 var old=ui.game.save_path;var path=late_folder+late_label+"-"+name+".json";ui.game.save_path=path
 if not ui.game.save_game():record_failure("Checkpoint write failed: "+name)
 ui.game.save_path=old;checkpoints.append({"name":name,"path":path,"stage":ui.game.stage_id,"turn":ui.game.turn,"view":ui.view})
func write_progress()->void:
 var f=FileAccess.open(late_folder+late_label+"-play.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":failures.is_empty() and not late_records.is_empty() and late_records.all(func(b):return b.outcome=="victory" and b.failures.is_empty()),"entry_only":late_entry_only,"failures":failures,"total_inputs":inputs,"battles":late_records,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false,"source_saves_modified":false,"route_trace":operations.filter(func(a):return a.get("kind","")=="route trace"),"scope":"Independent genuine deployment checkpoints, ordinary return-to-preparation and current-map reentry, actual input battles and post-battle hub actions; no live attributes, RNG, positions or win conditions edited."},"  "));f.close()
func run()->void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
  if arg.begins_with("--codes="):late_codes=arg.trim_prefix("--codes=").split(",")
  if arg=="--entry-only":late_entry_only=true
 if OS.get_cmdline_user_args().has("--continuous"):
  await run_continuous();return
 if late_codes.is_empty():late_codes=["M31","M32","M33","F31","F32","F33","S31","S32"]
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 var sources=State.read_json("res://reports/chapter3-redesign-20261022/sources.json")
 for code in late_codes:
  abort=false;path_cache.clear();risk_cache.clear();var failures_before=failures.size();var inputs_before=inputs
  source_checkpoint=str(sources[code]);var raw=FileAccess.get_file_as_string(source_checkpoint);var source_hash=raw.sha256_text()
  var working=late_folder+"working-"+code+".json";DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
  ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
  if not ui.game.load_game():record_failure("Genuine checkpoint failed: "+code)
  if not abort:
   ui._resume_journey();await settle()
   var target_node=ui.game.world_node
   if ui.game.mode=="battle":
    key(KEY_S);choose("new:prepare");await settle()
   await go(target_node)
   if not abort:await prepare_current()
   if not abort:key(KEY_Z);choose("new:battle");await settle()
   if not abort and str(ui.game.battle_data.code)!=code:record_failure("Wrong battle reentered: "+str(ui.game.battle_data.code))
   if not abort:await snapshot(code+"-entry")
  var entry_hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  var b={"entry_map_sha256":entry_hash,"code":code,"source":source_checkpoint,"source_sha256":source_hash,"outcome":"entry_only","failures":[],"key_inputs":0,"final_turn":0}
  if not abort and not late_entry_only:
   var battle_count=battles.size();await battle(false)
   if battles.size()>battle_count:
    b.merge(battles[-1],true);b.quest=ui.game.flags.quest.duplicate(true)
   if not abort:
    await post_battle(ui.game.stage_id)
    b.return_view=ui.view;b.return_node=ui.game.world_node
  if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Source evidence changed: "+code)
  b.failures=failures.slice(failures_before);b.key_inputs=inputs-inputs_before;b.final_turn=ui.game.turn
  b.map_sha256=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text();b.map_revision=ui.game.battle_data.get("tactical_review_version","")
  b.final_view=ui.view;late_records.append(b);write_progress()
  print("LATE_MAP_RESULT ",code," ",b.outcome," ",JSON.stringify(b.failures))
  ui.queue_free();await process_frame;await process_frame;ui=null
 write_progress();quit(0 if late_records.all(func(b):return (b.outcome=="victory" or late_entry_only)and b.failures.is_empty())else 1)

func act(id:String)->void:
 var u=ui.game.find_unit(id);var before=State.pos(u)if not u.is_empty()else Vector2i.ZERO
 await super.act(id)
 if abort:return
 u=ui.game.find_unit(id)
 if not u.is_empty():operations.append({"kind":"route trace","stage":ui.game.battle_data.code,"turn":ui.game.turn,"unit":id,"from":[before.x,before.y],"to":u.position.duplicate()})
 if ui.game.turn in [4,6,8,12]and not checkpoints.any(func(c):return c.name==str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn)):
  await snapshot(str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn))

func equip_from_convoy(id:String,item:int) -> void:
 var member=ui.game.roster.get(id,{})
 if member.is_empty() or member.get("dead",false) or int(member.get("item_id",0))!=0:return
 var stored=ui.game.convoy[ui.game.route];var index=-1
 for i in range(stored.size()):
  if int(stored[i])==item:index=i;break
 if index<0:return
 key(KEY_S);choose("new:camp");choose("camp:convoy");choose("camp:withdraw");choose("camp:withdraw_item:"+str(index))
 if abort:return
 if ui.view!="equipment_members" or not ui.equipment_screen.members.has(id):record_failure("Current equipment member list absent");return
 for i in range(ui.equipment_screen.members.size()):
  if str(ui.equipment_screen.members[ui.equipment_screen.selected])==id:break
  key(KEY_DOWN)
 key(KEY_Z)
 if ui.view!="equipment_preview" or not ui.equipment_screen.preview().can_equip:record_failure("Equipment comparison rejected "+id);return
 key(KEY_Z);await settle()
 if int(ui.game.roster[id].item_id)!=item:record_failure("Equipment confirmation failed "+id);return
 operations.append({"kind":"actual convoy equipment comparison and confirmation","unit":id,"item":item,"node":ui.game.world_node})
 if not ui.menu_items.is_empty():key(KEY_X)

func prepare_current()->void:
 if ui.game.route=="alm":
  await equip_from_convoy("hunapu",11)
  await equip_from_convoy("hunapu",60)
 else:
  await equip_from_convoy("eileen",16)
  await equip_from_convoy("eileen",60)

func run_continuous()->void:
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="res://reports/chapter2-redesign-20261022/play/continuous-resumed-entry/continuous-resumed-entry-chapter3-start.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine second-chapter completion failed")
 if not abort:ui._resume_journey();await settle();await snapshot("chapter3-start")
 if not abort and not ui.game.flags.get("D31_done",false):await hub_action("third_prologue");await snapshot("D31-finished")
 if not abort and ui.view=="hub":await leave_hub()
 for code in ["M31","F31","F32","S32","F33","M32","S31","M33"]:
  if abort:break
  var stage={"M31":301,"M32":302,"M33":303,"F31":304,"F32":305,"F33":306,"S31":311,"S32":312}[code]
  path_cache.clear();risk_cache.clear()
  if ui.game.route!=ui.game.stages[stage].route:await switch_team()
  if not abort:await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs;var prior_failures=failures.size();var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  key(KEY_Z);choose("new:battle");await settle();await snapshot(code+"-entry")
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
