extends "res://tests/chapter2_play.gd"
# Isolated real-input second-chapter review. No live attributes or outcomes changed.

const LATE_OUT="res://reports/chapter2-redesign-20261022/play/"
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
 f.store_string(JSON.stringify({"passed":failures.is_empty() and not late_records.is_empty() and late_records.all(func(b):return b.outcome=="victory" and b.failures.is_empty()),"entry_only":late_entry_only,"failures":failures,"total_inputs":inputs,"battles":late_records,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false,"source_saves_modified":false,"route_trace":operations.filter(func(a):return a.get("kind","")=="route trace"),"scope":"Independent genuine deployment checkpoints, ordinary return-to-preparation and current-map reentry, actual input battles and post-battle hub actions; no live attributes, RNG, positions or win conditions edited."},"  "));f.close()
func run()->void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
  if arg.begins_with("--codes="):late_codes=arg.trim_prefix("--codes=").split(",")
  if arg=="--entry-only":late_entry_only=true
 if OS.get_cmdline_user_args().has("--continuous"):
  await run_continuous();return
 if late_codes.is_empty():late_codes=["F21","F22","F23","F24","F25","F26","S21","S22"]
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 var sources=State.read_json("res://reports/chapter2-redesign-20261022/sources.json")
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

var path_cache:Dictionary={}
var risk_cache:Dictionary={}

func settle() -> void:
 for i in range(10000):
  if abort:return
  if ui.view in ["plot","reward"]:key(KEY_Z)
  elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
  if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:
   await process_frame
   if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:return
  await process_frame
 record_failure("Current result/dialogue input did not release: "+ui.view)

func distance_map(unit: Dictionary,goals: Array) -> Dictionary:
 var key_=str(ui.game.stage_id)+":"+str(unit.class_id)+":"+str(unit.get("item_id",0))+":"+JSON.stringify(goals)+":"+JSON.stringify(ui.game.flags.quest.objects)
 if not path_cache.has(key_):path_cache[key_]=super.distance_map(unit,goals)
 return path_cache[key_]

func refresh_threats() -> void:
 risk_cache.clear();super.refresh_threats()

func risk(unit: Dictionary,cell: Vector2i,skip: String="") -> float:
 var key_=str(unit.id)+":"+str(unit.hp)+":"+str(unit.get("weapon_index",-1))+":"+str(cell)+":"+skip
 if not risk_cache.has(key_):risk_cache[key_]=super.risk(unit,cell,skip)
 return float(risk_cache[key_])

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
 await equip_from_convoy("eileen",60)
 await prepare_east()

func act(id:String)->void:
 var u=ui.game.find_unit(id);var before=State.pos(u)if not u.is_empty()else Vector2i.ZERO
 await super.act(id)
 if abort:return
 u=ui.game.find_unit(id)
 if not u.is_empty():operations.append({"kind":"route trace","stage":ui.game.battle_data.code,"turn":ui.game.turn,"unit":id,"from":[before.x,before.y],"to":u.position.duplicate()})
 if ui.game.turn in [4,6,8,12]and not checkpoints.any(func(c):return c.name==str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn)):
  await snapshot(str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn))

func run_continuous()->void:
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="res://reports/chapter1-redesign-20261022/play/continuous-main-completion-final/continuous-main-completion-final-chapter2-start.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine first-chapter continuation failed")
 if not abort:ui._resume_journey();await settle()
 var west={}
 for id in ui.game.parties.alm:west[id]=ui.game.roster[id].duplicate(true)
 if not abort:
  await hub_action("east_chart_start");await hub_action("east_mireille");await hub_action("east_lisa");await hub_action("east_departure");await leave_hub()
 for code in ["F21","F22","F23","S21","S22","F24","F25","F26"]:
  if abort:break
  var stage={"F21":201,"F22":202,"F23":203,"F24":204,"F25":205,"F26":206,"S21":211,"S22":212}[code]
  path_cache.clear();risk_cache.clear();await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs;var prior_failures=failures.size();var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  key(KEY_Z);choose("new:battle");await settle();await snapshot(code+"-entry")
  var n=battles.size();await battle(false)
  var b={"code":code,"source":source_checkpoint,"source_sha256":source_hash,"scope":"Continuous from genuine first-chapter completion; normal recruitment, equipment, growth and casualties carried forward","entry_map_sha256":hash,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"outcome":"incomplete"}
  if battles.size()>n:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.slice(prior_failures);b.return_view=ui.view;b.final_turn=ui.game.turn;b.chapter_complete=ui.game.flags.get("chapter2_complete",false)
  late_records.append(b);write_progress();print("CH2_CONTINUOUS ",code," ",b.outcome," ",JSON.stringify(b.failures))
 if not abort:
  if not ui.game.flags.get("chapter2_complete",false):record_failure("Second chapter did not complete")
  for id in west:
   if ui.game.roster[id]!=west[id]:record_failure("West roster modified during eastern chapter: "+id)
  if not abort:
   key(KEY_Z);choose("new:chapter3");await settle()
   if ui.game.chapter!=3:record_failure("Third chapter did not open")
   else:await snapshot("chapter3-start")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Genuine chapter start source changed")
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)

func plan(unit: Dictionary) -> Dictionary:
 if ui.game.stage_id==204 and str(unit.id)=="lord" and ui.game.living("enemy").any(func(e):return e.get("objective_role","")=="seize_beacon"):return beacon_plan(unit)
 var enemies=ui.game.living("enemy");var origin=State.pos(unit);var graph=ui.game.reachable(unit)
 var best=combat_plan(unit)
 # Do not voluntarily accept a lethal counter in the hope of a second strike.
 if best.kind=="attack":
  var target=ui.game.find_unit(str(best.target));var candidate=unit.duplicate(true);candidate.position=[best.cell.x,best.cell.y]
  if int(best.spell)>=0:candidate.weapon_index=int(best.spell)
  var reply=Rules.default_counter(target,distance(best.cell,State.pos(target)))
  var attack=Rules.attack_stats(candidate,target,ui.game.terrain_avoid(State.pos(target)))
  var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(best.cell))
  if int(unit.hp)>Items.cost(int(best.spell))+int(response.damage) or int(attack.damage)>=int(target.hp):return best
 elif best.kind=="heal":return best
 # Resolve necessary interaction through the real action menu after a safe move.
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  for object in ui.game.interactions_for(candidate):
   if object.get("optional",false):continue
   if (object.kind=="inspect" or str(object.id) in ["prison_door","hideout"]) and not enemies.is_empty():continue
   var danger=risk(candidate,cell)
   if danger>=int(unit.hp)-4:continue
   return {"kind":"interact","cell":cell,"score":250.0-danger,"target":str(object.id),"spell":-1}
 # Apply formation penalties to the current cell too. A zero baseline can
 # strand a healthy mage more than one move behind a distant front line.
 best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 var frontline={};var healer={}
 for ally in ui.game.living("player"):
  if ally.get("neutral",false) or not ally.get("controllable",true):continue
  if int(ally.class_id) in [17,18]:healer=ally
  elif frontline.is_empty() or int(ally.defence)>int(frontline.defence) or (int(ally.defence)==int(frontline.defence) and int(ally.max_hp)>int(frontline.max_hp)):frontline=ally
 var goals: Array=[];var healing_role=int(unit.class_id) in [17,18]
 var protect=ui.game.stage_id in [203,204] and not enemies.is_empty()
 var camp=ui.game.find_unit("fishers")
 var defence_point=State.pos(camp) if ui.game.stage_id==203 and not camp.is_empty() else Vector2i(ui.game.battle_data.targets[0][0],ui.game.battle_data.targets[0][1])
 var low_hp=int(unit.hp)<int(unit.max_hp)*.45
 if not healer.is_empty() and low_hp and str(healer.id)!=str(unit.id):
  for d in ui.game.DIRECTIONS:goals.append(State.pos(healer)+d)
 elif healing_role:
  var injured={};var missing=0
  for ally in ui.game.living("player"):
   if str(ally.id)==str(unit.id) or ally.get("event_object",false):continue
   var amount=int(ally.max_hp)-int(ally.hp)
   if amount>missing:missing=amount;injured=ally
  var ally=injured if not injured.is_empty() else ui.game.find_unit("fishers") if ui.game.stage_id==203 else frontline
  if not ally.is_empty():
   for d in ui.game.DIRECTIONS:goals.append(State.pos(ally)+d)
 else:
  var focus={};var near=99999;var anchor=defence_point if protect else State.pos(frontline) if not frontline.is_empty() else origin
  for enemy in enemies:
   var dist=distance(anchor,State.pos(enemy))
   if dist<near:near=dist;focus=enemy
  if not focus.is_empty():
   var p=State.pos(focus)
   for d in ui.game.DIRECTIONS:goals.append(p+d)
  if goals.is_empty():
   for object in ui.game.battle_data.objects:
    if object.get("optional",false):continue
    if ui.game.flags.quest.objects.get(str(object.id),false):continue
    var p=Vector2i(object.position[0],object.position[1])
    if not object.get("adjacent",true):goals.append(p)
    else:
     for d in ui.game.DIRECTIONS:goals.append(p+d)
 if enemies.is_empty() and goals.is_empty():
  var exit=Vector2i(ui.game.battle_data.exit[0],ui.game.battle_data.exit[1])
  for cell in graph.costs:
   if not ui.game.can_stop(unit,cell) or distance(cell,exit)<3:continue
   var nearby=0
   for npc in ui.game.units:
    if npc.get("quest_kind","") in ["prisoner","patient","sailor"] and not npc.get("hidden",false) and distance(cell,State.pos(npc))<2:nearby+=1
   var score=3.0-nearby*10.0-float(graph.costs[cell])*.1
   if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
  return best
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 # Early flying assaults are met as a group; deck edges do not shield healers.
 var hold_line=ui.game.stage_id==211 and ui.game.turn<=3
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var danger=risk(unit,cell);var score=-danger*(3.0 if healing_role or low_hp else 2.0)
  if before<99999 and field.has(cell):score+=(5.0 if protect else 2.0)*(before-int(field[cell]))
  if not protect and not frontline.is_empty() and str(frontline.id)!=str(unit.id):score-=maxi(0,distance(cell,State.pos(frontline))-3)*4.0
  if not protect and not healer.is_empty() and str(healer.id)!=str(unit.id):score-=maxi(0,distance(cell,State.pos(healer))-4)*3.0
  if hold_line:score-=maxi(0,distance(cell,Vector2i(ui.game.battle_data.player_positions[0][0],ui.game.battle_data.player_positions[0][1]))-4)*9.0
  if danger>=int(unit.hp)-3:score-=200.0
  if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
 return best
