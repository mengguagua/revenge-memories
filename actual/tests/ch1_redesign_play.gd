extends "res://tests/map_polish_play.gd"
# Isolated real-input first-chapter review. No live attributes or outcomes changed.

const LATE_OUT="res://reports/chapter1-redesign-20261022/play/"
var late_label="round1"
var late_codes:PackedStringArray=[]
var source_checkpoint=""
var late_folder=""
var late_entry_only=false
var late_records=[]
func _initialize():call_deferred("run")
func snapshot(name:String)->void:
 if abort:return
 var old=ui.game.save_path;var path=late_folder+late_label+"-"+name+".json";ui.game.save_path=path
 if not ui.game.save_game():record_failure("Checkpoint write failed: "+name)
 ui.game.save_path=old;checkpoints.append({"name":name,"path":path,"stage":ui.game.stage_id,"turn":ui.game.turn,"view":ui.view})
func write_progress()->void:
 var f=FileAccess.open(late_folder+late_label+"-play.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":not late_records.is_empty() and late_records.all(func(b):return b.outcome=="victory" and b.failures.is_empty()),"entry_only":late_entry_only,"failures":failures,"total_inputs":inputs,"battles":late_records,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false,"source_saves_modified":false,"route_trace":operations.filter(func(a):return a.get("kind","")=="route trace"),"scope":"Independent genuine deployment checkpoints, ordinary return-to-preparation and current-map reentry, actual input battles and post-battle hub actions; no live attributes, RNG, positions or win conditions edited."},"  "));f.close()
func run()->void:
 if OS.get_cmdline_user_args().has("--continuous"):
  await run_continuous();return
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
  if arg.begins_with("--codes="):late_codes=arg.trim_prefix("--codes=").split(",")
  if arg=="--entry-only":late_entry_only=true
 if late_codes.is_empty():late_codes=["M12","M13","M14","M15","S11","S12"]
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 var sources=State.read_json("res://reports/chapter1-redesign-20261022/sources.json")
 for code in late_codes:
  abort=false;path_cache.clear();risk_cache.clear();var failures_before=failures.size();var inputs_before=inputs
  source_checkpoint=str(sources[code]);var raw=FileAccess.get_file_as_string(source_checkpoint);var source_hash=raw.sha256_text()
  var working=late_folder+"working-"+code+".json";DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
  ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
  if not ui.game.load_game():record_failure("Genuine checkpoint failed: "+code)
  if not abort:
   ui._resume_journey();await settle()
   var target_node=ui.game.world_node
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
   if not abort and ui.game.stage_id!=534:
    await post_battle(ui.game.stage_id)
    b.return_view=ui.view;b.return_node=ui.game.world_node
   elif not abort:
    if ui.view!="ending":record_failure("Final victory did not enter ending")
    for page in range(160):
     if abort or ui.game.flags.get("ending_done",false):break
     key(KEY_Z);await settle()
    if not abort and not ui.game.flags.get("ending_done",false):record_failure("Ending did not complete")
    if not abort:await snapshot("ending-complete")
    b.ending_done=ui.game.flags.get("ending_done",false)
  if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Source evidence changed: "+code)
  b.failures=failures.slice(failures_before);b.key_inputs=inputs-inputs_before;b.final_turn=ui.game.turn
  b.map_sha256=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text();b.map_revision=ui.game.battle_data.get("tactical_review_version","")
  b.final_view=ui.view;late_records.append(b);write_progress()
  print("LATE_MAP_RESULT ",code," ",b.outcome," ",JSON.stringify(b.failures))
  ui.queue_free();await process_frame;await process_frame;ui=null
 write_progress();quit(0 if late_records.all(func(b):return (b.outcome=="victory" or late_entry_only)and b.failures.is_empty())else 1)

func walk_to(at: Vector2i) -> void:
 var start=ui.game.hub_position;var blocked={}
 for o in ui.hub_controller.objects:blocked[Vector2i(o.position[0],o.position[1])]=true
 for d in ui.hub_controller.scenery:
  for y in range(d.rect.position.y,d.rect.end.y):
   for x in range(d.rect.position.x,d.rect.end.x):blocked[Vector2i(x,y)]=true
 var q: Array[Vector2i]=[start];var seen={start:start}
 while not q.is_empty() and not seen.has(at):
  var p=q.pop_front()
  for d in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
   var n=p+d
   if n.x<1 or n.x>12 or n.y<1 or n.y>7 or blocked.has(n) or seen.has(n):continue
   seen[n]=p;q.append(n)
 if not seen.has(at):record_failure("Hub destination blocked: "+str(at));return
 var path: Array=[];var p=at
 while p!=start:path.push_front(p);p=seen[p]
 for n in path:
  var d=n-ui.game.hub_position;key(KEY_RIGHT if d.x>0 else KEY_LEFT if d.x<0 else KEY_DOWN if d.y>0 else KEY_UP)
  if ui.game.hub_position!=n:record_failure("Hub input disagrees with room walk path");return

func hub_action(action: String) -> void:
 var object={}
 for o in ui.hub_controller.objects:
  if str(o.action)==action:object=o;break
 if object.is_empty():
  if action in ui.game.characters and bool(ui.game.roster.get(action,{}).get("dead",false)):
   operations.append({"kind":"dead NPC omitted","id":action});return
  record_failure("Hub object missing: "+action);return
 var at=Vector2i(object.position[0],object.position[1]);var destination=at+Vector2i.DOWN
 walk_to(destination)
 if abort:return
 key(KEY_UP);key(KEY_Z);await settle()
 operations.append({"kind":"facing hub confirmation","room":ui.game.hub_record,"action":action})

func prepare_east()->void:pass
func prepare_current()->void:
 var stage=ui.game.stage_for_node(ui.game.world_node)
 if stage==111:await equip_from_convoy("hunapu",60)
 if stage==105:
  await equip_from_convoy("hunapu",11)
  await equip_from_convoy("otto",2)

func post_battle(stage:int)->void:
 if abort:return
 if stage==104:
  await snapshot("after-"+str(stage));return
 enter_hub();await settle()
 match stage:
  102:
   await hub_action("grain");await hub_action("fula")
   if ui.menu_actions.has("hub:recruit_fula"):choose("hub:recruit_fula");await settle()
  103:
   await hub_action("orders");await hub_action("lena")
   if ui.menu_actions.has("hub:recruit_lena"):choose("hub:recruit_lena");await settle()
   await hub_action("church");await hub_action("cooperate")
  105:
   await hub_action("treat");await hub_action("ceremony")
   if ui.menu_actions.has("hub:ceremony_confirm"):choose("hub:ceremony_confirm");await settle()
   if not ui.game.flags.get("chapter1_complete",false):record_failure("Chapter ceremony did not complete")
   if not abort:await snapshot("chapter-end")
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

func act(id:String)->void:
 var u=ui.game.find_unit(id);var before=State.pos(u)if not u.is_empty()else Vector2i.ZERO
 await super.act(id)
 if abort:return
 u=ui.game.find_unit(id)
 if not u.is_empty():operations.append({"kind":"route trace","stage":ui.game.battle_data.code,"turn":ui.game.turn,"unit":id,"from":[before.x,before.y],"to":u.position.duplicate()})
 if ui.game.turn in [4,6,8,12]and not checkpoints.any(func(c):return c.name==str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn)):
  await snapshot(str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn))

func run_continuous()->void:
 late_label="continuous-main"
 var include_sides=OS.get_cmdline_user_args().has("--include-sides")
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="res://reports/campaign/natural-M11-victory-save.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine M11 completed checkpoint failed")
 if not abort:ui._resume_journey();await settle();key(KEY_Z);choose("continue_world");await settle()
 if include_sides and not abort:
  enter_hub();await hub_action("invite");await leave_hub()
 for code in (["S11","S12","M12","M13","M14","M15"]if include_sides else ["M12","M13","M14","M15"]):
  if abort:break
  var stage={"M12":102,"M13":103,"M14":104,"M15":105,"S11":111,"S12":112}[code]
  await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs;var failures_before=failures.size();var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  key(KEY_Z);choose("new:battle");await settle();await snapshot(code+"-entry")
  var n=battles.size();await battle(false)
  var b={"code":code,"source":source_checkpoint,"source_sha256":source_hash,"scope":"Continuous from genuine M11 completion; all later growth and casualties carried forward","entry_map_sha256":hash,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"outcome":"incomplete"}
  if battles.size()>n:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.slice(failures_before);b.return_view=ui.view;b.final_turn=ui.game.turn;b.chapter_complete=ui.game.flags.get("chapter1_complete",false)
  late_records.append(b);write_progress()
  print("CH1_CONTINUOUS ",code," ",b.outcome," ",JSON.stringify(b.failures))
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Original M11 record changed")
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)

